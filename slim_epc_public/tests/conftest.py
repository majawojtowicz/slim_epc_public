import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from epc.api import router, get_repo
from epc.db import EPCRepository

@pytest.fixture()
def tmp_db(tmp_path):
    return str(tmp_path / "test_epc.db")

@pytest.fixture()
def repo(tmp_db):
    return EPCRepository(tmp_db)

@pytest.fixture()
def client(tmp_db):
    app = FastAPI()
    app.include_router(router)
    repo = EPCRepository(tmp_db)
    app.dependency_overrides[get_repo] = lambda: repo
    return TestClient(app)

@pytest.fixture()
def client_with_mock_tm(tmp_db):
    app = FastAPI()
    app.include_router(router)
    repo = EPCRepository(tmp_db)
    app.dependency_overrides[get_repo] = lambda: repo

    with patch("epc.api.get_traffic_manager") as mock_tm_factory:
        mock_tm = MagicMock()
        mock_tm.is_running.return_value = False
        mock_tm_factory.return_value = mock_tm
        yield TestClient(app), repo, mock_tm

@pytest.fixture()
def client_with_mock_repo():
    app = FastAPI()
    app.include_router(router)
    mock_repo = MagicMock(spec=EPCRepository)
    app.dependency_overrides[get_repo] = lambda: mock_repo

    with patch("epc.api.get_traffic_manager") as mock_tm_factory:
        mock_tm = MagicMock()
        mock_tm.is_running.return_value = False
        mock_tm_factory.return_value = mock_tm
        yield TestClient(app), mock_repo, mock_tm