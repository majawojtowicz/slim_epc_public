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