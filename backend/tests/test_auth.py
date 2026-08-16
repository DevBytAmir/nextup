import pytest
from fastapi import HTTPException

from backend.app.auth import SessionStore, check_pin, require_page
from backend.app.models import Settings


def test_check_pin_accepts_numbering_pin_for_number_page():
    settings = Settings()
    assert check_pin("number", settings.numbering_pin, settings) is True


def test_check_pin_accepts_either_counter_pin_for_counter_page():
    settings = Settings()
    assert check_pin("counter", settings.counter1_pin, settings) is True
    assert check_pin("counter", settings.counter2_pin, settings) is True


def test_check_pin_accepts_admin_pin_for_admin_page():
    settings = Settings()
    assert check_pin("admin", settings.admin_pin, settings) is True


def test_check_pin_rejects_wrong_pin():
    settings = Settings()
    assert check_pin("admin", "0000", settings) is False


def test_check_pin_rejects_unknown_page():
    settings = Settings()
    assert check_pin("tv", "0000", settings) is False


def test_session_store_create_and_validate_round_trip():
    sessions = SessionStore()
    token = sessions.create("admin")

    assert sessions.page_for(token) == "admin"
    assert sessions.is_valid(token, "admin") is True
    assert sessions.is_valid(token, "number") is False


def test_session_store_rejects_unknown_token():
    sessions = SessionStore()
    assert sessions.is_valid("not-a-real-token", "admin") is False


class _FakeApp:
    def __init__(self, sessions: SessionStore) -> None:
        self.state = type("S", (), {"sessions": sessions})()


class _FakeRequest:
    def __init__(self, sessions: SessionStore, header: str | None) -> None:
        self.app = _FakeApp(sessions)
        self.headers = {"Authorization": header} if header else {}


async def test_require_page_passes_with_valid_token():
    sessions = SessionStore()
    token = sessions.create("admin")
    dependency = require_page("admin")

    await dependency(_FakeRequest(sessions, f"Bearer {token}"))  # should not raise


async def test_require_page_raises_401_with_missing_token():
    sessions = SessionStore()
    dependency = require_page("admin")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(_FakeRequest(sessions, None))
    assert exc_info.value.status_code == 401


async def test_require_page_raises_401_with_token_for_wrong_page():
    sessions = SessionStore()
    token = sessions.create("number")
    dependency = require_page("admin")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(_FakeRequest(sessions, f"Bearer {token}"))
    assert exc_info.value.status_code == 401
