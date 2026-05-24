
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

    def test_attach_ue_id_too_high_422(self, client):
        r = client.post("/ues", json={"ue_id": 101})
        assert r.status_code == 422

    def test_attach_ue_id_on_lower_edge_200(self, client):
        r = client.post("/ues", json={"ue_id": 1})
        assert r.status_code == 200

    def test_attach_ue_id_on_higher_edge_200(self, client):
        r = client.post("/ues", json={"ue_id": 100})
        assert r.status_code == 200

class TestAddBearer:

    def test_add_bearer_ok(self, client):
        client.post("/ues", json={"ue_id": 1})

        r = client.post("/ues/1/bearers", json={"bearer_id": 1})
        assert r.status_code == 200

    def test_add_bearer_id_too_low_422(self, client):
        client.post("/ues", json={"ue_id": 1})

        r = client.post("/ues/1/bearers", json={"bearer_id": 0})
        assert r.status_code == 422

    def test_add_bearer_id_too_high_422(self, client):
        client.post("/ues", json={"ue_id": 1})

        r = client.post("/ues/1/bearers", json={"bearer_id": 10})
        assert r.status_code == 422

    def test_add_bearer_default_bearer_400(self, client):
        client.post("/ues", json={"ue_id": 1})

        r = client.post("/ues/1/bearers", json={"bearer_id": 9})
        assert r.status_code == 400

    def test_add_bearer_duplicate_400(self, client):
        client.post("/ues", json={"ue_id": 1})
        client.post("/ues/1/bearers", json={"bearer_id": 2})

        r = client.post("/ues/1/bearers", json={"bearer_id": 2})
        assert r.status_code == 400

class TestStartTraffic:

    def test_start_traffic_ok(self, client):
        client.post("/ues", json={"ue_id": 1})

        r = client.post("/ues/1/bearers/9/traffic", json={"protocol": "udp", "Mbps": 1})
        assert r.status_code == 200

    def test_start_traffic_no_throughput_422(self, client):
        client.post("/ues", json={"ue_id": 1})

        r = client.post("/ues/1/bearers/9/traffic", json={"protocol": "udp"})
        assert r.status_code == 422

    def test_start_traffic_multiple_throughputs_422(self, client):
        client.post("/ues", json={"ue_id": 1})

        r = client.post("/ues/1/bearers/9/traffic", json={"protocol": "udp", "Mbps": 1, "kbps": 1})
        assert r.status_code == 422

class TestAPIBearerLifecycle:
    
    def test_default_bearer_behavior(self, client):
        client.post("/ues", json={"ue_id": 2})

        state = client.get("/ues/2").json()
        assert "9" in state["bearers"]

        resp = client.delete("/ues/2/bearers/9")
        assert resp.status_code == 400
        assert "Cannot remove default bearer" in resp.json()["detail"]

    def test_custom_bearer_lifecycle(self, client):
        client.post("/ues", json={"ue_id": 1})

        resp = client.post("/ues/1/bearers", json={"bearer_id": 2})
        assert resp.status_code == 200
        assert '2' in client.get("/ues/1").json()["bearers"]

        resp = client.post("/ues/1/bearers", json={"bearer_id": 2})
        assert resp.status_code == 400
        assert "exists" in resp.json()["detail"].lower()

        assert client.delete("/ues/1/bearers/2").status_code == 200
        assert '2' not in client.get("/ues/1").json()["bearers"]


class TestAPIIntegration:
    
    def test_full_state_transition_and_reset(self, client):
        client.post("/ues", json={"ue_id": 5}).raise_for_status()
        client.post("/ues/5/bearers", json={"bearer_id": 1}).raise_for_status()
        client.post("/ues/5/bearers/1/traffic", json={
            "protocol": "udp",
            "Mbps": 1
        }).raise_for_status()

        stats_resp = client.get("/ues/5/bearers/1/traffic")
        assert stats_resp.status_code == 200
        assert "tx_bps" in stats_resp.json()

        client.delete("/ues/5/bearers/1/traffic").raise_for_status()
        client.delete("/ues/5").raise_for_status()

        client.post("/ues", json={"ue_id": 10}).raise_for_status()
        client.post("/reset").raise_for_status()
        assert client.get("/ues").json() == {"ues": []}

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


class TestStartTrafficEdgeCases:
    def test_throughput_above_100_mbps_rejected(self, client):
        client.post("/ues", json={"ue_id": 1})
        r = client.post(
            "/ues/1/bearers/9/traffic",
            json={"protocol": "tcp", "Mbps": 500},
        )
        assert r.status_code in (400, 422)

    def test_zero_bps_is_rejected_at_traffic_start(self, client):
        client.post("/ues", json={"ue_id": 1})
        r = client.post(
            "/ues/1/bearers/9/traffic",
            json={"protocol": "tcp", "bps": 0},
        )
        assert r.status_code in (400, 422)


class TestDetachCleanup:
    def test_detach_with_active_traffic_cleans_up(self, client_with_mock_tm):
        client, _repo, mock_tm = client_with_mock_tm

        assert client.post("/ues", json={"ue_id": 1}).status_code == 200
        assert client.post(
            "/ues/1/bearers/9/traffic",
            json={"protocol": "tcp", "Mbps": 1},
        ).status_code == 200
        assert mock_tm.start.called

        assert client.delete("/ues/1").status_code == 200

        mock_tm.stop.assert_called_with(1, 9)
