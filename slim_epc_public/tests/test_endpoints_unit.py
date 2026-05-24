import pytest
from epc.models import UEState, BearerConfig, ThroughputStats


class TestAttachUEHandler:
    def test_attach_success_calls_repo_and_returns_payload(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.attach_ue.return_value = None

        r = client.post("/ues", json={"ue_id": 7})

        assert r.status_code == 200
        assert r.json() == {"status": "attached", "ue_id": 7}
        repo.attach_ue.assert_called_once_with(7)

    def test_attach_repo_value_error_maps_to_400(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.attach_ue.side_effect = ValueError("UE 7 already attached")

        r = client.post("/ues", json={"ue_id": 7})

        assert r.status_code == 400
        assert "already attached" in r.json()["detail"]


class TestGetUEHandler:
    def test_get_ue_returns_state(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.get_ue.return_value = UEState(ue_id=3)

        r = client.get("/ues/3")

        assert r.status_code == 200
        assert r.json()["ue_id"] == 3
        repo.get_ue.assert_called_once_with(3)

    def test_get_ue_not_found_maps_to_400(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.get_ue.side_effect = ValueError("UE 3 not found")

        r = client.get("/ues/3")

        assert r.status_code == 400
        assert "not found" in r.json()["detail"]


class TestDetachUEHandler:
    def test_detach_success(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.detach_ue.return_value = None

        r = client.delete("/ues/4")

        assert r.status_code == 200
        assert r.json() == {"status": "detached", "ue_id": 4}
        repo.detach_ue.assert_called_once_with(4)

    def test_detach_value_error_maps_to_400(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.detach_ue.side_effect = ValueError("UE 4 not found")

        r = client.delete("/ues/4")

        assert r.status_code == 400


class TestAddBearerHandler:
    def test_add_bearer_success(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.add_bearer.return_value = None

        r = client.post("/ues/1/bearers", json={"bearer_id": 2})

        assert r.status_code == 200
        assert r.json() == {"status": "bearer_added", "ue_id": 1, "bearer_id": 2}
        repo.add_bearer.assert_called_once_with(1, 2)

    def test_add_bearer_repo_error_maps_to_400(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.add_bearer.side_effect = ValueError("Bearer 2 already exists")

        r = client.post("/ues/1/bearers", json={"bearer_id": 2})

        assert r.status_code == 400
        assert "exists" in r.json()["detail"].lower()


class TestDeleteBearerHandler:
    def test_delete_bearer_not_in_state_returns_400(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.get_ue.return_value = UEState(ue_id=1)  # bearers puste

        r = client.delete("/ues/1/bearers/5")

        assert r.status_code == 400
        assert "Bearer not found" in r.json()["detail"]
        repo.delete_bearer.assert_not_called()

    def test_delete_bearer_stops_traffic_if_running(self, client_with_mock_repo):
        client, repo, mock_tm = client_with_mock_repo
        state = UEState(ue_id=1, bearers={5: BearerConfig(bearer_id=5)})
        repo.get_ue.return_value = state
        mock_tm.is_running.return_value = True

        r = client.delete("/ues/1/bearers/5")

        assert r.status_code == 200
        mock_tm.stop.assert_called_once_with(1, 5)
        repo.delete_bearer.assert_called_once_with(1, 5)

    def test_delete_bearer_skip_stop_when_not_running(self, client_with_mock_repo):
        client, repo, mock_tm = client_with_mock_repo
        state = UEState(ue_id=1, bearers={5: BearerConfig(bearer_id=5)})
        repo.get_ue.return_value = state
        mock_tm.is_running.return_value = False

        r = client.delete("/ues/1/bearers/5")

        assert r.status_code == 200
        mock_tm.stop.assert_not_called()
        repo.delete_bearer.assert_called_once_with(1, 5)

    def test_delete_default_bearer_400(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        state = UEState(ue_id=1, bearers={9: BearerConfig(bearer_id=9)})
        repo.get_ue.return_value = state
        repo.delete_bearer.side_effect = ValueError("Cannot remove default bearer")

        r = client.delete("/ues/1/bearers/9")

        assert r.status_code == 400
        assert "default bearer" in r.json()["detail"]


class TestStartTrafficHandler:
    def test_start_traffic_bearer_missing_returns_400(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.get_ue.return_value = UEState(ue_id=1)  # brak bearera 5

        r = client.post("/ues/1/bearers/5/traffic", json={"protocol": "tcp", "Mbps": 1})

        assert r.status_code == 400
        assert "Bearer not found" in r.json()["detail"]
        repo.update_bearer.assert_not_called()

    def test_start_traffic_calls_tm_with_updated_bearer(self, client_with_mock_repo):
        client, repo, mock_tm = client_with_mock_repo
        bearer = BearerConfig(bearer_id=9)
        repo.get_ue.return_value = UEState(ue_id=1, bearers={9: bearer})

        r = client.post("/ues/1/bearers/9/traffic", json={"protocol": "udp", "Mbps": 2})

        assert r.status_code == 200
        repo.update_bearer.assert_called_once()
        passed_bearer = repo.update_bearer.call_args.args[1]
        assert passed_bearer.active is True
        assert passed_bearer.protocol == "udp"
        assert passed_bearer.target_bps == 2_000_000
        mock_tm.start.assert_called_once()
        repo.update_stats.assert_called_once()

    def test_start_traffic_skips_initial_stats_if_present(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        bearer = BearerConfig(bearer_id=9)
        existing_stats = ThroughputStats(bearer_id=9, ue_id=1)
        repo.get_ue.return_value = UEState(
            ue_id=1, bearers={9: bearer}, stats={9: existing_stats}
        )

        r = client.post("/ues/1/bearers/9/traffic", json={"protocol": "tcp", "Mbps": 1})

        assert r.status_code == 200
        repo.update_stats.assert_not_called()

    def test_start_traffic_tm_failure_maps_to_400(self, client_with_mock_repo):
        client, repo, mock_tm = client_with_mock_repo
        bearer = BearerConfig(bearer_id=9)
        repo.get_ue.return_value = UEState(ue_id=1, bearers={9: bearer})
        mock_tm.start.side_effect = ValueError("already running")

        r = client.post("/ues/1/bearers/9/traffic", json={"protocol": "tcp", "Mbps": 1})

        assert r.status_code == 400
        assert "already running" in r.json()["detail"]


class TestStopTrafficHandler:
    def test_stop_traffic_marks_bearer_inactive_and_calls_tm(self, client_with_mock_repo):
        client, repo, mock_tm = client_with_mock_repo
        bearer = BearerConfig(bearer_id=9, active=True)
        repo.get_ue.return_value = UEState(ue_id=1, bearers={9: bearer})

        r = client.delete("/ues/1/bearers/9/traffic")

        assert r.status_code == 200
        mock_tm.stop.assert_called_once_with(1, 9)
        repo.update_bearer.assert_called_once()
        assert repo.update_bearer.call_args.args[1].active is False

    def test_stop_traffic_bearer_missing_returns_400(self, client_with_mock_repo):
        client, repo, mock_tm = client_with_mock_repo
        repo.get_ue.return_value = UEState(ue_id=1)

        r = client.delete("/ues/1/bearers/9/traffic")

        assert r.status_code == 400
        mock_tm.stop.assert_not_called()


class TestGetTrafficStatsHandler:
    def test_no_stats_returns_zeros(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.get_ue.return_value = UEState(
            ue_id=1, bearers={9: BearerConfig(bearer_id=9)}
        )

        r = client.get("/ues/1/bearers/9/traffic")

        assert r.status_code == 200
        body = r.json()
        assert body["tx_bps"] == 0
        assert body["rx_bps"] == 0
        assert body["duration"] == 0
        assert body["protocol"] is None

    def test_finished_run_uses_last_update_ts(self, client_with_mock_repo):
        client, repo, mock_tm = client_with_mock_repo
        mock_tm.is_running.return_value = False
        stats = ThroughputStats(
            bearer_id=9, ue_id=1,
            bytes_tx=1250, bytes_rx=625,
            start_ts=1000.0, last_update_ts=1010.0,
            protocol="tcp", target_bps=1000,
        )
        repo.get_ue.return_value = UEState(
            ue_id=1,
            bearers={9: BearerConfig(bearer_id=9)},
            stats={9: stats},
        )

        r = client.get("/ues/1/bearers/9/traffic")

        assert r.status_code == 200
        body = r.json()
        assert body["duration"] == 10
        assert body["tx_bps"] == 1000  # 1250 bytes * 8 / 10 s
        assert body["rx_bps"] == 500


class TestResetHandler:
    def test_reset_stops_all_and_resets_repo(self, client_with_mock_repo):
        client, repo, mock_tm = client_with_mock_repo

        r = client.post("/reset")

        assert r.status_code == 200
        assert r.json() == {"status": "reset"}
        mock_tm.stop_all.assert_called_once()
        repo.reset_all.assert_called_once()


class TestAggregatedStatsHandler:
    def test_aggregated_stats_unknown_ue_returns_400(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.ue_exists.return_value = False

        r = client.get("/ues/stats?ue_id=42")

        assert r.status_code == 400
        assert "UE not found" in r.json()["detail"]

    def test_aggregated_stats_all_empty(self, client_with_mock_repo):
        client, repo, _ = client_with_mock_repo
        repo.list_ues.return_value = []

        r = client.get("/ues/stats")

        assert r.status_code == 200
        body = r.json()
        assert body["scope"] == "all"
        assert body["ue_count"] == 0
        assert body["bearer_count"] == 0
        assert body["total_tx_bps"] == 0