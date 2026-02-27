import os
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
import sqlmodel
from sqlmodel import Session, SQLModel, create_engine


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "postgres"
os.environ["POSTGRES_DB"] = "products"
os.environ["KEYCLOAK_SERVER_URL"] = "http://localhost:8080"
os.environ["KEYCLOAK_CLIENT_ID"] = "products-client"
os.environ["KEYCLOAK_REALM_NAME"] = "products-realm"
os.environ["KEYCLOAK_CLIENT_SECRET_KEY"] = "products-secret"
os.environ["KAFKA_SERVER"] = "localhost:9092"
os.environ["ENVIRONMENT"] = "local"

TEST_DB_PATH = ROOT_DIR / "test_products.sqlite3"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"
(ROOT_DIR / "logs").mkdir(parents=True, exist_ok=True)
_original_create_engine = sqlmodel.create_engine


def _patched_create_engine(url, *args, **kwargs):
    if str(url).startswith("postgresql+psycopg"):
        return _original_create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    return _original_create_engine(url, *args, **kwargs)


sqlmodel.create_engine = _patched_create_engine

try:
    import aiofiles  # noqa: F401
except ModuleNotFoundError:
    class _AsyncFile:
        def __init__(self, path, mode):
            self._path = path
            self._mode = mode
            self._file = None

        async def __aenter__(self):
            self._file = open(self._path, self._mode)
            return self

        async def __aexit__(self, exc_type, exc, tb):
            if self._file:
                self._file.close()

        async def write(self, data):
            self._file.write(data)

    aiofiles_module = types.ModuleType("aiofiles")
    aiofiles_module.open = lambda path, mode: _AsyncFile(path, mode)
    sys.modules["aiofiles"] = aiofiles_module

try:
    import structlog  # noqa: F401
except ModuleNotFoundError:
    import logging

    structlog_module = types.ModuleType("structlog")
    stdlib_module = types.ModuleType("structlog.stdlib")
    processors_module = types.ModuleType("structlog.processors")

    class ProcessorFormatter(logging.Formatter):
        def __init__(self, *args, **kwargs):
            super().__init__("%(message)s")

    class JSONRenderer:
        def __call__(self, logger, name, event_dict):  # noqa: ARG002
            return str(event_dict)

    stdlib_module.ProcessorFormatter = ProcessorFormatter
    processors_module.JSONRenderer = JSONRenderer
    structlog_module.stdlib = stdlib_module
    structlog_module.processors = processors_module

    sys.modules["structlog"] = structlog_module
    sys.modules["structlog.stdlib"] = stdlib_module
    sys.modules["structlog.processors"] = processors_module

from core.authentication import MockUser, StaffOnly  # noqa: E402
from dependencies import get_session  # noqa: E402
from main import app  # noqa: E402
from models import SQLModel as AppSQLModel  # noqa: E402,F401

TEST_ENGINE = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    SQLModel.metadata.create_all(TEST_ENGINE)
    yield
    SQLModel.metadata.drop_all(TEST_ENGINE)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def clean_database():
    with Session(TEST_ENGINE) as session:
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    yield


@pytest.fixture
def session():
    with Session(TEST_ENGINE) as db_session:
        yield db_session


@pytest.fixture
def client(session):
    def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[StaffOnly] = lambda: MockUser(username="staff", permissions=["staff"])

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
