import copy
import os
import sys
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["MONGO_HOST"] = "localhost"
os.environ["MONGO_PORT"] = "27017"
os.environ["MONGO_INITDB_DATABASE"] = "orders"
os.environ["KEYCLOAK_SERVER_URL"] = "http://localhost:8080"
os.environ["KEYCLOAK_CLIENT_ID"] = "orders-client"
os.environ["KEYCLOAK_REALM_NAME"] = "orders-realm"
os.environ["KEYCLOAK_CLIENT_SECRET_KEY"] = "orders-secret"
os.environ["KAFKA_SERVER"] = "localhost:9092"
os.environ["ENVIRONMENT"] = "local"
(ROOT_DIR / "logs").mkdir(parents=True, exist_ok=True)


def _ensure_structlog_stub():
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


def _ensure_keycloak_stub():
    try:
        import keycloak  # noqa: F401
    except ModuleNotFoundError:
        keycloak_module = types.ModuleType("keycloak")

        class KeycloakOpenID:
            def __init__(self, *args, **kwargs):
                pass

            def well_known(self):
                return {}

            def decode_token(self, token):
                return {}

        keycloak_module.KeycloakOpenID = KeycloakOpenID
        sys.modules["keycloak"] = keycloak_module


def _ensure_confluent_stub():
    try:
        import confluent_kafka  # noqa: F401
    except ModuleNotFoundError:
        ck_module = types.ModuleType("confluent_kafka")

        class Producer:
            def __init__(self, *args, **kwargs):
                pass

            def produce(self, *args, **kwargs):
                return None

            def flush(self):
                return None

        class Consumer:
            def __init__(self, *args, **kwargs):
                self._msgs = []

            def subscribe(self, topics):
                return None

            def poll(self, timeout):
                return None

            def commit(self, msg=None):
                return None

            def close(self):
                return None

        ck_module.Producer = Producer
        ck_module.Consumer = Consumer
        sys.modules["confluent_kafka"] = ck_module


def _ensure_pymongo_stub():
    try:
        import pymongo  # noqa: F401
    except ModuleNotFoundError:
        pymongo_module = types.ModuleType("pymongo")

        class _DummyDB(dict):
            def __getitem__(self, item):
                return {}

        class MongoClient:
            def __init__(self, *args, **kwargs):
                pass

            def __getitem__(self, name):
                return _DummyDB()

            def start_session(self):
                class _S:
                    def __enter__(self_inner):
                        return self_inner

                    def __exit__(self_inner, exc_type, exc, tb):
                        return False

                    def with_transaction(self_inner, callback):
                        callback(self_inner)

                return _S()

        pymongo_module.MongoClient = MongoClient
        sys.modules["pymongo"] = pymongo_module


_ensure_structlog_stub()
_ensure_keycloak_stub()
_ensure_confluent_stub()
_ensure_pymongo_stub()

from core.authentication import keycloak_auth, MockUser  # noqa: E402
from events import outbox_events  # noqa: E402
from main import app  # noqa: E402
from services.address_service import AddressService  # noqa: E402
from services.cart_service import CartService  # noqa: E402
from services.order_service import OrderService  # noqa: E402
from services.product_service import ProductService  # noqa: E402


class FakeResult:
    def __init__(self, inserted_id=None, modified_count=0, matched_count=0, deleted_count=0):
        self.inserted_id = inserted_id
        self.modified_count = modified_count
        self.matched_count = matched_count
        self.deleted_count = deleted_count


class FakeCursor(list):
    def sort(self, key, direction):
        reverse = direction == -1
        return FakeCursor(sorted(self, key=lambda x: x.get(key), reverse=reverse))


def _match_condition(value, condition):
    if isinstance(condition, dict):
        if "$lt" in condition:
            return value < condition["$lt"]
        return False
    return value == condition


def _matches(doc, query):
    if not query:
        return True

    for key, value in query.items():
        if key == "$or":
            return any(_matches(doc, subq) for subq in value)
        if not _match_condition(doc.get(key), value):
            return False
    return True


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def with_transaction(self, callback):
        callback(self)


class FakeMongoClient:
    def start_session(self):
        return FakeSession()


class FakeCollection:
    def __init__(self, name, state, client):
        self.name = name
        self._state = state
        self.database = types.SimpleNamespace(client=client)

    @property
    def docs(self):
        return self._state[self.name]

    def find_one(self, query):
        for doc in self.docs:
            if _matches(doc, query):
                return copy.deepcopy(doc)
        return None

    def find(self, query):
        return FakeCursor(copy.deepcopy([doc for doc in self.docs if _matches(doc, query)]))

    def insert_one(self, doc, session=None):  # noqa: ARG002
        new_doc = copy.deepcopy(doc)
        if "_id" not in new_doc:
            new_doc["_id"] = str(uuid.uuid4())
        self.docs.append(new_doc)
        return FakeResult(inserted_id=new_doc.get("id", new_doc["_id"]))

    def update_one(self, query, update, upsert=False, session=None):  # noqa: ARG002
        for idx, doc in enumerate(self.docs):
            if _matches(doc, query):
                updated = copy.deepcopy(doc)
                if "$set" in update:
                    updated.update(update["$set"])
                self.docs[idx] = updated
                return FakeResult(modified_count=1, matched_count=1)

        if upsert:
            new_doc = copy.deepcopy(query)
            if "$set" in update:
                new_doc.update(update["$set"])
            if "_id" not in new_doc:
                new_doc["_id"] = str(uuid.uuid4())
            self.docs.append(new_doc)
            return FakeResult(inserted_id=new_doc["_id"], modified_count=1, matched_count=0)

        return FakeResult(modified_count=0, matched_count=0)

    def delete_one(self, query):
        for idx, doc in enumerate(self.docs):
            if _matches(doc, query):
                self.docs.pop(idx)
                return FakeResult(deleted_count=1)
        return FakeResult(deleted_count=0)

    def find_one_and_update(self, query, update, sort=None):
        candidates = [doc for doc in self.docs if _matches(doc, query)]
        if not candidates:
            return None
        if sort:
            for key, direction in reversed(sort):
                candidates = sorted(candidates, key=lambda d: d.get(key), reverse=direction == -1)
        selected = candidates[0]
        for idx, doc in enumerate(self.docs):
            if doc is selected:
                if "$set" in update:
                    selected = {**doc, **update["$set"]}
                self.docs[idx] = selected
                return copy.deepcopy(selected)
        return None


class FakeDB:
    def __init__(self):
        self.client = FakeMongoClient()
        self._state = {
            "products": [],
            "carts": [],
            "addresses": [],
            "orders": [],
            "outbox": [],
        }

    def __getitem__(self, name):
        return FakeCollection(name, self._state, self.client)


@pytest.fixture
def fake_db():
    return FakeDB()


@pytest.fixture(autouse=True)
def patch_collections(fake_db):
    ProductService.collection = fake_db["products"]
    CartService.collection = fake_db["carts"]
    AddressService.collection = fake_db["addresses"]
    OrderService.collection = fake_db["orders"]
    OrderService.outbox_collection = fake_db["outbox"]
    OrderService.client = fake_db.client
    outbox_events.outbox_collection = fake_db["outbox"]
    yield


@pytest.fixture
def client():
    app.dependency_overrides[keycloak_auth] = lambda: MockUser(sub="user-1", username="user@example.com", permissions=["user"])
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
