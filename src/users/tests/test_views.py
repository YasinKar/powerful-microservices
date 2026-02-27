from unittest.mock import Mock

import pytest
from rest_framework import status

from api.models import ProfileModel


class SerializerOK:
    def __init__(self, *args, **kwargs):  # noqa: D401, ANN002, ANN003
        self.data = {"access_token": "token"}

    def is_valid(self, raise_exception=False):  # noqa: FBT002
        return True

    def save(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return Mock()


class SerializerError(SerializerOK):
    def is_valid(self, raise_exception=False):  # noqa: FBT002
        from rest_framework.exceptions import ValidationError

        raise ValidationError({"message": "bad"})


@pytest.mark.django_db
def test_signup_view_success(monkeypatch, api_client):
    monkeypatch.setattr("api.v1.views.SignUpView.serializer_class", SerializerOK)
    response = api_client.post(
        "/api/v1/signup/",
        {"username": "x@y.com", "password": "Aa123456!", "password_confierm": "Aa123456!"},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "User registered successfully"


@pytest.mark.django_db
def test_signup_view_validation_error(monkeypatch, api_client):
    monkeypatch.setattr("api.v1.views.SignUpView.serializer_class", SerializerError)
    response = api_client.post("/api/v1/signup/", {"username": "x@y.com"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_verify_username_view_success(monkeypatch, api_client):
    monkeypatch.setattr("api.v1.views.VerifyUsernameView.serializer_class", SerializerOK)
    response = api_client.post(
        "/api/v1/verify/username/",
        {"username": "x@y.com", "otp": 123456},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_password_signin_view_success(monkeypatch, api_client):
    monkeypatch.setattr("api.v1.views.PasswordSigninView.serializer_class", SerializerOK)
    response = api_client.post(
        "/api/v1/password/signin/",
        {"username": "x@y.com", "password": "Aa123456!"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_otp_signin_view_success(monkeypatch, api_client):
    monkeypatch.setattr("api.v1.views.OTPSigninView.serializer_class", SerializerOK)
    response = api_client.post(
        "/api/v1/otp/signin/",
        {"username": "x@y.com", "otp": 123456},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_username_send_otp_view_success(monkeypatch, api_client):
    monkeypatch.setattr("api.v1.views.UsernameSendOTPView.serializer_class", SerializerOK)
    response = api_client.post("/api/v1/send/OTP/", {"username": "x@y.com"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "send otp for you"


@pytest.mark.django_db
def test_change_password_view_success(monkeypatch, api_client, user):
    monkeypatch.setattr("api.v1.views.ChangePaswordView.serializer_class", SerializerOK)
    api_client.force_authenticate(user=user)

    response = api_client.put(
        "/api/v1/change/password/",
        {"password": "Bb123456!", "password_confierm": "Bb123456!"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_profile_view_create_and_patch(api_client, user):
    api_client.force_authenticate(user=user)

    create = api_client.post(
        "/api/v1/profile/",
        {"first_name": "Jane", "last_name": "Doe"},
        format="json",
    )
    patch = api_client.patch(
        "/api/v1/profile/",
        {"last_name": "D."},
        format="json",
    )

    assert create.status_code == status.HTTP_201_CREATED
    assert patch.status_code == status.HTTP_200_OK
    profile = ProfileModel.objects.get(user=user)
    assert profile.last_name == "D."
