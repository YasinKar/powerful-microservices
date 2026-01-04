import random
import json
import re
from datetime import datetime

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from rest_framework import serializers

from api.models import ProfileModel
from api.keycloak_service import UserKeyCloak, TokenKeycloak
from events.kafka_producer import publish_event
from events.schemas.user_registered import UserRegisteredEvent, UserRegisteredPayload
from events.schemas.user_verified import UserVerifiedEvent, UserVerifiedPayload


User = get_user_model() 


def valid_username(username):
    phone = re.match(r'^([+]?\d{1,2}[-\s]?|)\d{3}[-\s]?\d{3}[-\s]?\d{4}$', username)
    email = re.match(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', username)
    return phone, email


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    password_confierm = serializers.CharField(required=True)

    def validate_password(self, password):
        """
        Validates that the password meets the following criteria:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 2 digits
        - At least 1 special character
        """
        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.", code=400)
        if not re.search(r"[A-Z]", password):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.", code=400)
        if not re.search(r"[a-z]", password):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.", code=400)
        if len(re.findall(r"\d", password)) < 2:
            raise serializers.ValidationError("Password must contain at least two numbers.", code=400)
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise serializers.ValidationError("Password must contain at least one special character.", code=400)
        return password

    def validate(self, attrs):
        keycloak = UserKeyCloak()
        keycloak.username = attrs['username']

        if keycloak.check_connect() == 500:
            raise serializers.ValidationError({"message": "Server not found"}, code=500)

        phone, email = valid_username(attrs['username'])
        if not phone and not email:
            raise serializers.ValidationError({"username":"phone or email is not correct"}, code=400)
        
        user = User.objects.filter(username=attrs['username'])
        if user.exists():
            if keycloak.check_enable() == 404:
                raise serializers.ValidationError({"message": "user not available calling with admin"}, code=403)
            if keycloak.check_email_verify() == 200:
                raise serializers.ValidationError({"message": "user already exsits"}, code=400)
            
        if attrs['password'] != attrs['password_confierm']:
            raise serializers.ValidationError({"password":"Passwords is not match."}, code=404)
        
        return attrs

    def create(self, validated_data):
        keycloak = UserKeyCloak()
        keycloak.username = validated_data['username']
        keycloak.password = validated_data['password']

        phone, email = valid_username(validated_data['username'])
        user = User.objects.filter(username=validated_data['username']).first()
        if user:
            # Update password for the existing user
            if keycloak.check_enable() == 404:
                raise serializers.ValidationError({"message": "user not available calling with admin"}, code=403)
            if keycloak.check_email_verify() == 200:
                raise serializers.ValidationError({"message": "user already exsits"}, code=400)
            user.set_password(validated_data['password'])
            user.save()
        else:
            user = User.objects.create_user(
                username=validated_data['username'],
                password=validated_data['password'],
            )
            user.save()
            keycloak.username = validated_data["username"]
            keycloak.password = validated_data["password"]
            if phone:
                keycloak.create_phone()
            if email:
                keycloak.create_email()

        otp = random.randint(111111, 999999)
        print("===>", otp)
        cache.set(
            f"otp_{validated_data['username']}",
            json.dumps(
                {"otp": otp, "retries": 0, "created_at": datetime.now().isoformat()}
            ),
            timeout=10 * 60,
        )

        # Publish UserRegistered event in `notifications` topic -> Consumer: Notifications Service
        payload = UserRegisteredPayload(
            user_type="phone" if phone else "email",
            username=validated_data["username"],
            otp=otp,
        )

        event = UserRegisteredEvent.create(payload)
        publish_event(
            topic="users",
            value=event.to_dict()
        )

        return user


class VerifyUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    otp = serializers.IntegerField(required=True, write_only=True)

    def validate(self, attrs):
        keycloak = UserKeyCloak()
        keycloak.username = attrs['username']

        if keycloak.check_connect() == 500:
            raise serializers.ValidationError({"message": "Server not found"}, code=500)

        user = User.objects.filter(username=attrs['username']).first()
        if user:
            if keycloak.check_enable() == 404:
                raise serializers.ValidationError({"message": "user not available calling with admin"}, code=403)
            if keycloak.check_email_verify() == 200:
                raise serializers.ValidationError({"message": "user already exsits"}, code=400)
            
        cached_otp = json.loads(cache.get(f"otp_{attrs['username']}", {}))
        if not cached_otp:
            raise serializers.ValidationError(
                {"message": "otp not found or is expired."}, code=404
            )

        if cached_otp.get("retries") >= 5:
            raise serializers.ValidationError(
                {"message": "you have reached the maximum number of attempts."},
                code=429,
            )

        if cached_otp.get("otp") != attrs["otp"]:
            cached_otp["retries"] += 1
            created_at = datetime.fromisoformat(cached_otp["created_at"])
            time_from_creation = datetime.now() - created_at
            cache.set(
                f"otp_{attrs['username']}",
                json.dumps(cached_otp),
                timeout=time_from_creation.seconds,
            )
            raise serializers.ValidationError(
                {"message": "otp is not correct"}, code=401
            )
        
        return attrs

    def create(self, validated_data):
        keycloak = UserKeyCloak()
        keycloak.username = validated_data["username"]
        keycloak.email_verified()

        phone, email = valid_username(validated_data['username'])

        payload = UserVerifiedPayload(
            user_type="phone" if phone else "email",
            username=validated_data["username"],
        )

        event = UserVerifiedEvent.create(payload)
        publish_event(
            topic="users",
            value=event.to_dict()
        )

        return validated_data['username']
    

class PasswordSignInSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        keycloak = UserKeyCloak()
        keycloak.username = attrs['username']

        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError({"error": "Invalid credentials"}, code=401)

        if keycloak.check_connect() == 500:
            raise serializers.ValidationError({"message": "Server not found"}, code=500)

        if keycloak.check_enable() == 404:
            raise serializers.ValidationError(
                {"message": "user not available calling with admin"}, code=403
            )
        if keycloak.check_email_verify() == 404:
            raise serializers.ValidationError(
                {"message": "please call with admin"}, code=401
            )
        
        return attrs

    def create(self, validated_data):
        tokenkeycloak = TokenKeycloak()
        tokenkeycloak.username = validated_data["username"]
        tokenkeycloak.password = validated_data["password"]
        token_info = tokenkeycloak.get_token()
        if token_info in [404, 500]:
            raise serializers.ValidationError(
                {"message": "service authentications error"}, code=500
            )
        print(token_info)
        return {
            "access_token": token_info['access_token'],
            "refresh_token": token_info['refresh_token'],
        }
    

class OTPSigninSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, write_only=True)
    otp = serializers.IntegerField(required=True, write_only=True)
    access_token = serializers.CharField(read_only=True)
    token_type = serializers.CharField(read_only=True)
    expires_in = serializers.CharField(read_only=True)

    def validate(self, attrs):
        keycloak = UserKeyCloak()
        keycloak.username = attrs['username']

        user = User.objects.filter(username=attrs['username']).first()
        if not user:
            raise serializers.ValidationError({'username': 'User does not exist or is inactive.'}, code=403)

        otp = cache.get(f"otp_{attrs['username']}", {})
        if otp:
            otp = json.loads(otp)
        else:
            raise serializers.ValidationError({"message": "otp not found or is expired."}, code=404)
        if keycloak.check_connect() == 500:
            raise serializers.ValidationError({"message": "server not found"}, code=500)
        if keycloak.check_email_verify() == 404:
            raise serializers.ValidationError({"message": "please first verified username"}, code=401)
        if keycloak.check_enable() == 404:
            raise serializers.ValidationError({"message": "user not available calling with admin"}, code=403)

        if not otp:
            raise serializers.ValidationError(
                {"message": "otp not found or is expired."}, code=404
            )
        if otp.get("retries") >= 5:
            raise serializers.ValidationError(
                {"message": "you have reached the maximum number of attempts."},
                code=429,
            )
        if otp.get("otp") != attrs["otp"]:
            otp["retries"] += 1
            created_at = datetime.fromisoformat(otp["created_at"])
            time_from_creation = datetime.now() - created_at
            cache.set(
                f"otp_{attrs['username']}",
                json.dumps(otp),
                timeout=time_from_creation.seconds,
            )
            raise serializers.ValidationError(
                {"message": "otp is not correct"}, code=401
            )
        cache.delete(f"otp_{attrs['username']}")

        return attrs

    def create(self, validated_data):
        token = TokenKeycloak()
        token.username = validated_data["username"]
        token_info = token.get_token_passwordless()
        if token_info in [404, 500]:
            raise serializers.ValidationError({"message": "service authentications error"}, code=500)
        return {
            "access_token": token_info['access_token'],
            "token_type": token_info['token_type'],
            "expires_in": token_info['expires_in'],
        }


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    password_confierm = serializers.CharField(required=True)

    def validate_password(self, password):
        """
        Validates that the password meets the following criteria:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 2 digits
        - At least 1 special character
        """
        if len(password) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        if not re.search(r"[A-Z]", password):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[a-z]", password):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if len(re.findall(r"\d", password)) < 2:
            raise serializers.ValidationError(
                "Password must contain at least two numbers."
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )
        return password
    
    def validate(self, attrs):
        keycloak = UserKeyCloak()
        user = User.objects.filter(id=self.context['request'].user.id).first()

        if not user:
            raise serializers.ValidationError({"user":"user is not exsits"}, code=401)
        if attrs['password'] != attrs['password_confierm']:
            raise serializers.ValidationError({"password":"Passwords is not match."}, code=400)
        
        if keycloak.check_enable() == 404:
            raise serializers.ValidationError(
                {"message": "user not available calling with admin"}, code=403
            )
        if keycloak.check_email_verify() == 404:
            raise serializers.ValidationError(
                {"message": "please call with admin"}, code=401
            )
        
        return attrs
        
    def create(self, validated_data):
        user = self.context['request'].user 
        user.set_password(validated_data['password'])
        user.save()
        keycloak = UserKeyCloak()
        keycloak.username = user.username 
        keycloak.password = validated_data['password']
        result = keycloak.change_password()
        if result != keycloak.STATUS_CREATED:
            raise serializers.ValidationError({"message": "Keycloak update failed"}, code=500)
        return user


class UsernameSendOTPSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)

    def validate(self, attrs):
        keycloak = UserKeyCloak()
        keycloak.username = attrs['username']
        phone, email = valid_username(attrs['username'])

        if not phone and not email:
            raise serializers.ValidationError({"username":"phone or email is not correct"}, code=400)
        user = get_object_or_404(User, username=attrs['username'])
        
        if keycloak.check_enable() == 404:
            raise serializers.ValidationError({"message": "user not available calling with admin"}, code=403)
        if keycloak.check_email_verify() == 404:
            raise serializers.ValidationError({"message": "please call with admin"}, code=401)
        
        return attrs
    
    def create(self, validated_data):
        phone, email = valid_username(validated_data['username'])
        otp = random.randint(111111, 999999)
        print("===>", otp)
        cache.set(
            f"otp_{validated_data['username']}",
            json.dumps(
                {"otp": otp, "retries": 0, "created_at": datetime.now().isoformat()}
            ),
            timeout=10 * 60,
        )
        if phone:
            # otp_phone_sender(otp, validated_data['username'])
            pass
        if email:
            # otp_email_sender(otp, validated_data['username'])
            pass
        return validated_data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        exclude = ('user', )