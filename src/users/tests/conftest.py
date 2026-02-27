import os
import sys
import importlib
from pathlib import Path

import django
import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.contrib.auth import get_user_model


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.pytest_settings")
django.setup()
sys.modules["config.settings"] = importlib.import_module("config.pytest_settings")


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    call_command("migrate", run_syncdb=True, verbosity=0)


@pytest.fixture(autouse=True)
def clean_test_state():
    call_command("flush", verbosity=0, interactive=False)
    cache.clear()
    yield
    call_command("flush", verbosity=0, interactive=False)
    cache.clear()


@pytest.fixture
def db():
    return None


@pytest.fixture
def api_client(db):
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="user@example.com",
        password="Aa123456!",
    )
