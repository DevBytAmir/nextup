import pytest
from fastapi import HTTPException

from backend.app.auth import (
    SessionStore,
    bearer_token,
    check_counter_pin,
    check_pin,
    require_counter,
    require_page,
)
from backend.app.models import Settings


def test_check_pin_accepts_numbering_pin_for_number_page():
    settings = Settings()
    assert check_pin("number", settings.numbering_pin, settings) is True


def test_check_pin_accepts_admin_pin_for_admin_page():
    settings = Settings()
    assert check_pin("admin", settings.admin_pin, settings) is True


def test_check_pin_rejects_wrong_pin():
    settings = Settings()
    assert check_pin("admin", "0000", settings) is False


def test_check_pin_rejects_unknown_page():
    settings = Settings()
    assert check_pin("tv", "0000", settings) is False


def test_check_counter_pin_accepts_a_counters_own_pin():
    settings = Settings()
    assert check_counter_pin(1, settings.counter_pins[0], settings) is True
    assert check_counter_pin(2, settings.counter_pins[1], settings) is True


def test_check_counter_pin_rejects_another_counters_pin():
    settings = Settings()
    assert check_counter_pin(1, settings.counter_pins[1], settings) is False
    assert check_counter_pin(2, settings.counter_pins[0], settings) is False


def test_check_counter_pin_rejects_out_of_range_counter():
    settings = Settings()
    assert check_counter_pin(0, settings.counter_pins[0], settings) is False
    assert check_counter_pin(99, settings.counter_pins[0], settings) is False


def test_session_store_create_and_validate_round_trip():
    sessions = SessionStore()
    token = sessions.create("admin")

    assert sessions.page_for(token) == "admin"
    assert sessions.is_valid(token, "admin") is True
    assert sessions.is_valid(token, "number") is False


def test_session_store_binds_a_counter_number():
    sessions = SessionStore()
    token = sessions.create("counter", 2)

    assert sessions.is_valid(token, "counter") is True
    assert sessions.counter_for(token) == 2


def test_session_store_counter_for_returns_none_for_non_counter_sessions():
    sessions = SessionStore()
    token = sessions.create("admin")

    assert sessions.counter_for(token) is None


def test_session_store_rejects_unknown_token():
    sessions = SessionStore()
    assert sessions.is_valid("not-a-real-token", "admin") is False


def test_invalidate_counter_drops_only_sessions_for_that_counter():
    sessions = SessionStore()
    counter1_token = sessions.create("counter", 1)
    counter2_token = sessions.create("counter", 2)
    admin_token = sessions.create("admin")

    sessions.invalidate_counter(1)

    assert sessions.is_valid(counter1_token, "counter") is False
    assert sessions.counter_for(counter2_token) == 2
    assert sessions.is_valid(admin_token, "admin") is True


def test_revoke_drops_the_single_token():
    sessions = SessionStore()
    admin_token = sessions.create("admin")
    other_token = sessions.create("number")

    sessions.revoke(admin_token)

    assert sessions.is_valid(admin_token, "admin") is False
    assert sessions.is_valid(other_token, "number") is True


def test_revoke_unknown_token_does_not_raise():
    sessions = SessionStore()
    sessions.revoke("not-a-real-token")


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


async def test_require_counter_returns_the_bound_counter_number():
    sessions = SessionStore()
    token = sessions.create("counter", 2)

    assert await require_counter(_FakeRequest(sessions, f"Bearer {token}")) == 2


async def test_require_counter_raises_401_with_missing_token():
    sessions = SessionStore()

    with pytest.raises(HTTPException) as exc_info:
        await require_counter(_FakeRequest(sessions, None))
    assert exc_info.value.status_code == 401


async def test_require_counter_raises_401_for_a_non_counter_session():
    sessions = SessionStore()
    token = sessions.create("admin")

    with pytest.raises(HTTPException) as exc_info:
        await require_counter(_FakeRequest(sessions, f"Bearer {token}"))
    assert exc_info.value.status_code == 401


def test_bearer_token_strips_the_prefix():
    sessions = SessionStore()
    assert bearer_token(_FakeRequest(sessions, "Bearer abc123")) == "abc123"


def test_bearer_token_returns_empty_string_when_missing():
    sessions = SessionStore()
    assert bearer_token(_FakeRequest(sessions, None)) == ""
