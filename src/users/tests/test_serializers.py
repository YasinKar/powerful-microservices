import json
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import serializers

from api.models import Outbox
from api.v1.serializers import (
    ChangePasswordSerializer,
    OTPSigninSerializer,
    PasswordSignInSerializer,
    SignUpSerializer,
    UsernameSendOTPSerializer,
    VerifyUsernameSerializer,
    valid_username,
)


class FakeUserKeycloak:
    STATUS_CREATED = 201

    def __init__(self):
        self.username = None
        self.password = None

    def check_connect(self):
        return 200

    def check_enable(self):
        return 200

    def check_email_verify(self):
        return 404

    def create_email(self):
        return self.STATUS_CREATED

    def create_phone(self):
        return self.STATUS_CREATED

    def email_verified(self):
        return 204

    def change_password(self):
        return self.STATUS_CREATED


class FakeTokenKeycloak:
    def __init__(self):
        self.username = None
        self.password = None

    def get_token(self):
        return {"access_token": "access", "refresh_token": "refresh"}

    def get_token_passwordless(self):
        return {"access_token": "access", "token_type": "Bearer", "expires_in": 300}


class VerifiedUserKeycloak(FakeUserKeycloak):
    def check_email_verify(self):
        return 200


def _otp_payload(otp):
    return json.dumps({"otp": otp, "retries": 0, "created_at": "2025-01-01T00:00:00"})


def test_valid_username_accepts_phone_and_email():
    phone, email = valid_username("+1 555-123-4567")
    assert phone is not None
    assert email is None

    phone, email = valid_username("user@example.com")
    assert phone is None
    assert email is not None


@pytest.mark.django_db
def test_signup_serializer_rejects_password_mismatch(monkeypatch):
    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", FakeUserKeycloak)

    serializer = SignUpSerializer(
        data={
            "username": "user@example.com",
            "password": "Aa123456!",
            "password_confierm": "Aa123456?",
        }
    )

    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_signup_serializer_creates_user_and_outbox(monkeypatch):
    cache.clear()
    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", FakeUserKeycloak)
    monkeypatch.setattr("api.v1.serializers.random.randint", lambda *_: 222333)

    serializer = SignUpSerializer(
        data={
            "username": "new@example.com",
            "password": "Aa123456!",
            "password_confierm": "Aa123456!",
        }
    )
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()

    assert user.username == "new@example.com"
    assert Outbox.objects.count() == 1
    cached = json.loads(cache.get("otp_new@example.com"))
    assert cached["otp"] == 222333


@pytest.mark.django_db
def test_verify_username_serializer_increments_retry_for_wrong_otp(monkeypatch):
    User = get_user_model()
    User.objects.create_user(username="user@example.com", password="Aa123456!")
    cache.set("otp_user@example.com", _otp_payload(123456), timeout=300)
    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", FakeUserKeycloak)

    serializer = VerifyUsernameSerializer(
        data={"username": "user@example.com", "otp": 111111}
    )

    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)

    cached = json.loads(cache.get("otp_user@example.com"))
    assert cached["retries"] == 1


@pytest.mark.django_db
def test_verify_username_serializer_publish_event_on_success(monkeypatch):
    User = get_user_model()
    User.objects.create_user(username="user@example.com", password="Aa123456!")
    cache.set("otp_user@example.com", _otp_payload(123456), timeout=300)
    published = []

    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", FakeUserKeycloak)
    monkeypatch.setattr(
        "api.v1.serializers.publish_event",
        lambda topic, value: published.append((topic, value)),
    )

    serializer = VerifyUsernameSerializer(
        data={"username": "user@example.com", "otp": 123456}
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.save() == "user@example.com"
    assert published and published[0][0] == "users"


@pytest.mark.django_db
def test_password_signin_serializer_requires_valid_credentials(monkeypatch):
    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", FakeUserKeycloak)

    serializer = PasswordSignInSerializer(
        data={"username": "missing@example.com", "password": "Aa123456!"}
    )

    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_password_signin_serializer_returns_tokens(monkeypatch):
    User = get_user_model()
    User.objects.create_user(username="user@example.com", password="Aa123456!")
    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", VerifiedUserKeycloak)
    monkeypatch.setattr("api.v1.serializers.TokenKeycloak", FakeTokenKeycloak)

    serializer = PasswordSignInSerializer(
        data={"username": "user@example.com", "password": "Aa123456!"}
    )
    assert serializer.is_valid(), serializer.errors

    payload = serializer.save()
    assert payload["access_token"] == "access"
    assert payload["refresh_token"] == "refresh"


@pytest.mark.django_db
def test_otp_signin_serializer_rejects_unknown_user(monkeypatch):
    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", FakeUserKeycloak)

    serializer = OTPSigninSerializer(data={"username": "unknown@example.com", "otp": 1})
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_otp_signin_serializer_returns_token_on_success(monkeypatch):
    User = get_user_model()
    User.objects.create_user(username="user@example.com", password="Aa123456!")
    cache.set("otp_user@example.com", _otp_payload(123456), timeout=300)

    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", VerifiedUserKeycloak)
    monkeypatch.setattr("api.v1.serializers.TokenKeycloak", FakeTokenKeycloak)

    serializer = OTPSigninSerializer(data={"username": "user@example.com", "otp": 123456})
    assert serializer.is_valid(), serializer.errors
    payload = serializer.save()

    assert payload["access_token"] == "access"
    assert cache.get("otp_user@example.com") is None


@pytest.mark.django_db
def test_change_password_serializer_updates_user_password(monkeypatch, user):
    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", VerifiedUserKeycloak)
    request = SimpleNamespace(user=user)

    serializer = ChangePasswordSerializer(
        data={"password": "Bb123456!", "password_confierm": "Bb123456!"},
        context={"request": request},
    )
    assert serializer.is_valid(), serializer.errors
    updated_user = serializer.save()

    updated_user.refresh_from_db()
    assert updated_user.check_password("Bb123456!")


@pytest.mark.django_db
def test_username_send_otp_serializer_sets_cache(monkeypatch, user):  # noqa: ARG001
    cache.clear()
    monkeypatch.setattr("api.v1.serializers.UserKeyCloak", VerifiedUserKeycloak)
    monkeypatch.setattr("api.v1.serializers.random.randint", lambda *_: 456789)
    get_user_model().objects.filter(username=user.username).update(username="user@example.com")

    serializer = UsernameSendOTPSerializer(data={"username": "user@example.com"})
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    cached = json.loads(cache.get("otp_user@example.com"))
    assert cached["otp"] == 456789
