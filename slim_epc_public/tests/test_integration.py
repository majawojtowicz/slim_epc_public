import pytest
import time

def test_ue_lifecycle_integration(client):
    r = client.post("/ues", json={"ue_id": 42})
    assert r.status_code == 200
    assert r.json() == {"status": "attached", "ue_id": 42}
    r = client.get("/ues")
    assert r.status_code == 200
    assert 42 in r.json()["ues"]
    r = client.get("/ues/42")
    assert r.status_code == 200
    assert r.json()["ue_id"] == 42
    r = client.delete("/ues/42")
    assert r.status_code == 200
    assert r.json() == {"status": "detached", "ue_id": 42}
    r = client.get("/ues")
    assert r.status_code == 200
    assert 42 not in r.json()["ues"]

def test_single_bearer_transfer_stats(client):
    ue_id = 42
    r = client.post(f"/ues", json={"ue_id": ue_id})
    assert r.status_code == 200
    r = client.post(f"/ues/{ue_id}/bearers", json={"bearer_id": 5})
    assert r.status_code == 200
    r = client.post(f"/ues/{ue_id}/bearers/5/traffic", json={"protocol": "tcp", "Mbps": 1})
    assert r.status_code == 200
    time.sleep(4)
    r = client.get(f"/ues/stats?ue_id={ue_id}&include_details=true")
    assert r.status_code == 200
    stats = r.json()
    assert stats["ue_count"] == 1
    assert stats["bearer_count"] >= 1
    assert "details" in stats
    r = client.delete(f"/ues/{ue_id}/bearers/5/traffic")
    assert r.status_code == 200
