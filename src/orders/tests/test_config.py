from core.config import settings


def test_settings_values():
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MONGO_INITDB_DATABASE
