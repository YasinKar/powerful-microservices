from django.urls import path
from .views import (
        SignUpView, VerifyUsernameView, OTPSigninView,
        ChangePaswordView, ProfileView,
        PasswordSigninView, UsernameSendOTPView
    )


urlpatterns = [
    path('signup/', SignUpView.as_view()),
    path('verify/username/', VerifyUsernameView.as_view()),
    path('otp/signin/', OTPSigninView.as_view()),
    path('password/signin/', PasswordSigninView.as_view()),
    path('change/password/', ChangePaswordView.as_view()),
    path('send/OTP/', UsernameSendOTPView.as_view()),
    path('profile/', ProfileView.as_view()),
]