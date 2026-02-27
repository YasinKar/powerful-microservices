from core.config import settings


def test_settings_has_required_defaults():
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MAX_FILE_SIZE == 5 * 1024 * 1024
    assert "image/jpeg" in settings.ALLOWED_UPLOAD_TYPES


def test_sqlalchemy_database_uri_is_computed():
    uri = str(settings.SQLALCHEMY_DATABASE_URI)
    assert uri.startswith("postgresql+psycopg://")
