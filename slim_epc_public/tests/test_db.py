import pytest

from epc.models import ThroughputStats

class TestAttachDetach:
    def test_attach_adds(self, repo):
        repo.attach_ue(1)
        assert 1 in list(repo.list_ues())

    def test_attach_duplicate_raises(self, repo):
        repo.attach_ue(1)
        with pytest.raises(ValueError, match="already attached"):
            repo.attach_ue(1)

    def test_detach_removes(self, repo):
        repo.attach_ue(1)
        repo.detach_ue(1)
        assert 1 not in list(repo.list_ues())

    def test_detach_nonexistent_raises(self, repo):
        with pytest.raises(ValueError, match="not found"):
            repo.detach_ue(99)

class TestRepositoryPersistedUpdates:
    def test_update_bearer_persists_changes(self, repo):
        repo.attach_ue(1)
        
        bearer = repo.get_ue(1).bearers[9]
        bearer.active = True
        bearer.protocol = "udp"
        bearer.target_bps = 5000
        repo.update_bearer(1, bearer)
    
        fresh_state = repo.get_ue(1)
        assert fresh_state.bearers[9].active is True
        assert fresh_state.bearers[9].protocol == "udp"
        assert fresh_state.bearers[9].target_bps == 5000

    def test_update_stats_persists_changes(self, repo):
        repo.attach_ue(1)
        stats = ThroughputStats(
            bearer_id=9, 
            ue_id=1, 
            bytes_tx=1024, 
            bytes_rx=2048,
        )
        repo.update_stats(1, stats)
        
        fresh_state = repo.get_ue(1)
        assert 9 in fresh_state.stats
        assert fresh_state.stats[9].bytes_tx == 1024
        assert fresh_state.stats[9].bytes_rx == 2048

    def test_reset_all_clears_entire_database(self, repo):
        repo.attach_ue(1)
        repo.add_bearer(1, 2)
        repo.attach_ue(2)
        repo.attach_ue(3)
        assert len(list(repo.list_ues())) == 3
        
        repo.reset_all()
        assert len(list(repo.list_ues())) == 0
        
        repo.attach_ue(1)
        assert repo.ue_exists(1) is True