import pytest
from unittest.mock import MagicMock

from epc.models import BearerConfig
from epc.traffic import TrafficGeneratorManager


class TestTrafficManagerStart:
    def test_traffic_manager_start_twice_raises(self):
        repo = MagicMock()
        tm = TrafficGeneratorManager(repo)
        bearer = BearerConfig(bearer_id=1, protocol="tcp", target_bps=1000)

        try:
            tm.start(1, bearer)
            with pytest.raises(ValueError, match="already running"):
                tm.start(1, bearer)
        finally:
            tm.stop(1, 1)