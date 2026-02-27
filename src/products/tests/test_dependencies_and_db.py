from dependencies import get_session
from core.db import init_db


def test_get_session_yields_session():
    session = next(get_session())
    try:
        assert session is not None
    finally:
        session.close()


def test_init_db_is_noop(session):
    assert init_db(session) is None
