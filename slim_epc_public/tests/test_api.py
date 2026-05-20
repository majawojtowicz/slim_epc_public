
import pytest
from pydantic import ValidationError
from fastapi import FastAPI

from epc.api import router, get_repo
from epc.db import EPCRepository

class TestAttachUE:

    def test_attach_ok(self, client):
        r = client.post("/ues", json={"ue_id": 1})
        assert r.status_code == 200
        assert r.json() == {"status": "attached", "ue_id": 1}

    def test_attach_duplicate_400(self, client):
        client.post("/ues", json={"ue_id": 1})
        r = client.post("/ues", json={"ue_id": 1})
        assert r.status_code == 400
        assert "already" in r.json()["detail"].lower()

    def test_attach_ue_id_too_low_422(self, client):
        r = client.post("/ues", json={"ue_id": 0})
        assert r.status_code == 422