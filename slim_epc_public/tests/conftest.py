import pytest

@pytest.fixture()
def tmp_db(tmp_path):
    return str(tmp_path / "test_epc.db")

@pytest.fixture()
def repo(tmp_db):
    from epc.db import EPCRepository
    return EPCRepository(tmp_db)

@pytest.fixture()
def client(tmp_db):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from epc.api import router, get_repo
    from epc.db import EPCRepository

    app = FastAPI()
    app.include_router(router)
    repo = EPCRepository(tmp_db)
    app.dependency_overrides[get_repo] = lambda: repo
    return TestClient(app)