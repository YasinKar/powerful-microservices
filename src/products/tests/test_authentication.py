import asyncio

import pytest
from fastapi import HTTPException

from core import authentication


class FakeRequest:
    def __init__(self, auth_header=None):
        self.headers = {}
        if auth_header:
            self.headers["Authorization"] = auth_header


def test_get_keycloak_client_success(monkeypatch):
    class FakeClient:
        def well_known(self):
            return {}

    monkeypatch.setattr(authentication, "KeycloakOpenID", lambda **kwargs: FakeClient())

    client = authentication.get_keycloak_client()

    assert client is not None


def test_get_keycloak_client_failure(monkeypatch):
    monkeypatch.setattr(authentication, "KeycloakOpenID", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("bad")))

    with pytest.raises(HTTPException) as exc:
        authentication.get_keycloak_client()

    assert exc.value.status_code == 500


def test_keycloak_auth_requires_header():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(authentication.keycloak_auth(FakeRequest(), keycloak_openid=object()))

    assert exc.value.status_code == 401


def test_keycloak_auth_success():
    class FakeOpenID:
        def decode_token(self, token):
            return {
                "sub": "id-1",
                "preferred_username": "staff@example.com",
                "name": "Staff User",
                "email": "staff@example.com",
                "given_name": "Staff",
                "family_name": "User",
                "realm_access": {"roles": ["staff"]},
            }

    user = asyncio.run(
        authentication.keycloak_auth(
            FakeRequest("Bearer token"),
            keycloak_openid=FakeOpenID(),
        )
    )

    assert user.username == "staff@example.com"
    assert "staff" in user.permissions


def test_staff_only_blocks_non_staff():
    user = authentication.MockUser(username="a", permissions=["user"])

    with pytest.raises(HTTPException) as exc:
        authentication.StaffOnly(user)

    assert exc.value.status_code == 403
