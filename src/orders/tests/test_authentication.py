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
    assert authentication.get_keycloak_client() is not None


def test_get_keycloak_client_failure(monkeypatch):
    monkeypatch.setattr(authentication, "KeycloakOpenID", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(HTTPException) as exc:
        authentication.get_keycloak_client()
    assert exc.value.status_code == 500


def test_keycloak_auth_requires_bearer_header():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(authentication.keycloak_auth(FakeRequest(), keycloak_openid=object()))
    assert exc.value.status_code == 401


def test_keycloak_auth_success():
    class FakeOpenID:
        def decode_token(self, token):
            return {
                "sub": "user-1",
                "preferred_username": "user@example.com",
                "realm_access": {"roles": ["user"]},
            }

    user = asyncio.run(authentication.keycloak_auth(FakeRequest("Bearer t"), keycloak_openid=FakeOpenID()))
    assert user.sub == "user-1"
    assert user.permissions == ["user"]
