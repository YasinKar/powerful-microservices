from unittest.mock import Mock

from api.keycloak_service import BaseKeyCloak, TokenKeycloak, UserKeyCloak


def build_service(monkeypatch, service_cls, admin=None, openid=None):
    monkeypatch.setattr(service_cls, "admin_connect", lambda self: admin)
    monkeypatch.setattr(service_cls, "openid_connect", lambda self: openid)
    return service_cls()


def test_base_keycloak_check_connect_success(monkeypatch):
    admin = Mock()
    admin.get_realms.return_value = []
    service = build_service(monkeypatch, BaseKeyCloak, admin=admin, openid=Mock())

    assert service.check_connect() == service.STATUS_OK


def test_base_keycloak_check_connect_failure(monkeypatch):
    admin = Mock()
    admin.get_realms.side_effect = RuntimeError("boom")
    service = build_service(monkeypatch, BaseKeyCloak, admin=admin, openid=Mock())

    assert service.check_connect() == service.STATUS_SERVER_ERROR


def test_user_keycloak_create_email_creates_user_when_missing(monkeypatch):
    admin = Mock()
    admin.get_user_id.return_value = None
    service = build_service(monkeypatch, UserKeyCloak, admin=admin, openid=Mock())
    service.username = "user@example.com"
    service.password = "Aa123456!"

    assert service.create_email() == service.STATUS_CREATED
    admin.create_user.assert_called_once()


def test_user_keycloak_create_email_resets_password_when_existing(monkeypatch):
    admin = Mock()
    admin.get_user_id.return_value = "user-id-1"
    service = build_service(monkeypatch, UserKeyCloak, admin=admin, openid=Mock())
    service.username = "user@example.com"
    service.password = "Aa123456!"

    assert service.create_email() == service.STATUS_NO_CONTENT
    admin.set_user_password.assert_called_once_with(
        user_id="user-id-1",
        password="Aa123456!",
        temporary=False,
    )


def test_user_keycloak_check_email_verify(monkeypatch):
    admin = Mock()
    admin.get_user_id.return_value = "u1"
    admin.get_user.return_value = {"id": "u1", "emailVerified": True, "enabled": True}
    service = build_service(monkeypatch, UserKeyCloak, admin=admin, openid=Mock())
    service.username = "user@example.com"

    assert service.check_email_verify() == service.STATUS_OK


def test_user_keycloak_enable_updates_user(monkeypatch):
    admin = Mock()
    admin.get_user_id.return_value = "u1"
    admin.get_user.return_value = {"id": "u1", "emailVerified": False, "enabled": False}
    service = build_service(monkeypatch, UserKeyCloak, admin=admin, openid=Mock())
    service.username = "user@example.com"

    assert service.enable() == service.STATUS_OK
    admin.update_user.assert_called_once()


def test_token_keycloak_get_token(monkeypatch):
    openid = Mock()
    openid.token.return_value = {"access_token": "abc"}
    service = build_service(monkeypatch, TokenKeycloak, admin=Mock(), openid=openid)
    service.username = "user@example.com"
    service.password = "Aa123456!"

    assert service.get_token() == {"access_token": "abc"}


def test_token_keycloak_get_token_passwordless(monkeypatch):
    admin = Mock()
    admin.get_user_id.return_value = "u1"
    admin.connection.token = {"access_token": "admin-token"}
    openid = Mock()
    openid.exchange_token.return_value = {"access_token": "user-token", "expires_in": 300}
    service = build_service(monkeypatch, TokenKeycloak, admin=admin, openid=openid)
    service.username = "user@example.com"

    token = service.get_token_passwordless()
    assert token["access_token"] == "user-token"
