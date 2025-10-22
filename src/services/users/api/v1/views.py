from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from config.authentication import KeycloakAuthentication
from rest_framework.views import APIView
from api.models import ProfileModel
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from .serializers import (
        SignUpSerializer, ProfileSerializer, VerifyUsernameSerializer,
        ChangePasswordSerializer, UsernameSendOTPSerializer,
        PasswordSignInSerializer, OTPSigninSerializer,
    )


class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            return Response({"message": "User registered successfully"}, status=201)
        except ValidationError as exc:
            error_codes = exc.get_codes() or 400
            code = next(iter(error_codes.values())) if error_codes else 400
            print(code)
            print(code)
            return Response(
                exc.detail, 
                status=200
            )


class VerifyUsernameView(APIView):
    serializer_class = VerifyUsernameSerializer

    def post(self, request):
        context = {
            'request':request
        }
        serializer = self.serializer_class(data=request.data, context=context)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'message': 'User verified username successfully'}, 
                status=200
            )
        except ValidationError as exc:
            error_codes = exc.get_codes() or 400
            code = next(iter(error_codes.values()))[0] if error_codes else 400
            print(code)
            return Response(
                exc.detail, 
                status=code
            )


class OTPSigninView(APIView):
    serializer_class = OTPSigninSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request":request})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=200)
        except ValidationError as exc:
            error_codes = exc.get_codes() or 400
            code = next(iter(error_codes.values()))[0] if error_codes else 400
            print(code)
            return Response(
                exc.detail, 
                status=code
            )


class PasswordSigninView(APIView):
    serializer_class = PasswordSignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request":request})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=200)
        except ValidationError as exc:
            error_codes = exc.get_codes() or 400
            code = next(iter(error_codes.values()))[0] if error_codes else 400
            print(code)
            return Response(
                exc.detail, 
                status=code
            )


class UsernameSendOTPView(APIView):
    serializer_class = UsernameSendOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request":request})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message":"send otp for you"}, status=200)
        except ValidationError as exc:
            error_codes = exc.get_codes() or 400
            code = next(iter(error_codes.values())) if error_codes else 400
            print(code)
            return Response(
                exc.detail, 
                status=200 
            )


class ChangePaswordView(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [KeycloakAuthentication]

    def put(self, request):
        context = {
            'request':request
        }
        serializer = self.serializer_class(data=request.data, context=context)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            return Response({'message': 'password change successfully'}, status=status.HTTP_200_OK)
        except ValidationError as exc:
            error_codes = exc.get_codes() or 400
            code = next(iter(error_codes.values()))[0] if error_codes else 400
            print(code)
            return Response(
                exc.detail, 
                status=code  
            )


class ProfileView(APIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [KeycloakAuthentication]

    def get(self, request):
        profile = get_object_or_404(ProfileModel, user=request.user)
        serializer = self.serializer_class(profile, context={"request":request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if ProfileModel.objects.filter(user=request.user).exists():
            return Response({"detail": "Profile already exists."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        profile = get_object_or_404(ProfileModel, user=request.user)
        serializer = self.serializer_class(profile, data=request.data, context={"request":request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.errors, status=200)

    def patch(self, request):
        profile = get_object_or_404(ProfileModel, user=request.user)
        serializer = self.serializer_class(profile, data=request.data, partial=True, context={"request":request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)