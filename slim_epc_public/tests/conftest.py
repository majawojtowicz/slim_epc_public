import pytest

@pytest.fixture()
def tmp_db(tmp_path):
    return str(tmp_path / "test_epc.db")

@pytest.fixture()
def repo(tmp_db):
    from epc.db import EPCRepository
    return EPCRepository(tmp_db)