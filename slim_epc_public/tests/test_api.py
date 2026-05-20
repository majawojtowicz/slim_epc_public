
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


class TestAPIResponses:
    def test_get_ues_returns_json_list(self, client):
        r = client.get("/ues")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "ues" in data
        assert isinstance(data["ues"], list)

    def test_get_nonexistent_ue_returns_400(self, client):
        r = client.get("/ues/9999")
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_delete_nonexistent_ue_returns_400(self, client):
        r = client.delete("/ues/8888")
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_attach_invalid_body_returns_422(self, client):
        r = client.post("/ues", json={"wrong_field": 123})
        assert r.status_code == 422
