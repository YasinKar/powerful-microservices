from unittest.mock import Mock

from config.authentication import KeycloakAuthentication


def build_request(token=None):
    auth_value = f"Bearer {token}" if token else ""
    return type("Request", (), {"META": {"HTTP_AUTHORIZATION": auth_value}})()


def test_authentication_returns_none_without_token():
    request = build_request()

    result = KeycloakAuthentication().authenticate(request)

    assert result is None


def test_authentication_returns_none_on_decode_error(monkeypatch):
    keycloak_cls = Mock(side_effect=RuntimeError("bad config"))
    monkeypatch.setattr("config.authentication.KeycloakOpenID", keycloak_cls)
    monkeypatch.setattr("config.authentication.logging.error", lambda *args, **kwargs: None)
    request = build_request(token="abc")

    result = KeycloakAuthentication().authenticate(request)

    assert result is None


def test_authentication_returns_mock_user(monkeypatch):
    keycloak_client = Mock()
    keycloak_client.decode_token.return_value = {
        "sub": "subject",
        "preferred_username": "user@example.com",
        "name": "Jane Doe",
        "email": "user@example.com",
        "given_name": "Jane",
        "family_name": "Doe",
        "realm_access": {"roles": ["user"]},
        "groups": ["g1"],
    }
    keycloak_cls = Mock(return_value=keycloak_client)
    monkeypatch.setattr("config.authentication.KeycloakOpenID", keycloak_cls)
    request = build_request(token="abc")

    result = KeycloakAuthentication().authenticate(request)

    assert result is not None
    mock_user, auth = result
    assert auth is None
    assert mock_user.username == "user@example.com"
    assert mock_user.permissions == ["user"]
