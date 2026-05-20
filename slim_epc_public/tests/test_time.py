import time
import pytest
from epc.models import ThroughputStats

class TestDurationCalculation:
    def test_stats_uses_is_running_for_duration(self, client_with_mock_tm):
        client, repo, mock_tm = client_with_mock_tm
        mock_tm.is_running.return_value = True

        repo.attach_ue(1)
        repo.add_bearer(1, 2)
        stats = ThroughputStats(
            bearer_id=2, ue_id=1,
            bytes_tx=8000, bytes_rx=4000,
            start_ts=time.time() - 10,
            last_update_ts=time.time() - 5,
            protocol="tcp", target_bps=1000,
        )
        repo.update_stats(1, stats)
        r = client.get("/ues/1/bearers/2/traffic")
        assert r.status_code == 200
        assert r.json()["tx_bps"] > 0
        assert r.json()["duration"] >= 9