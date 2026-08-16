from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


@pytest.fixture
def data_path(tmp_path: Path) -> Path:
    return tmp_path / "state.json"


@pytest.fixture
def app(data_path: Path):
    return create_app(data_path)


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
