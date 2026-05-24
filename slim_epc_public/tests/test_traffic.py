import pytest
from unittest.mock import MagicMock

from epc.models import BearerConfig
from epc.traffic import TrafficGeneratorManager


def _make_bearer(bearer_id=1, protocol="tcp", target_bps=1000):
    return BearerConfig(bearer_id=bearer_id, protocol=protocol, target_bps=target_bps, active=True)


class TestTrafficManagerStart:

    def test_traffic_manager_start_twice_raises(self):
        tm = TrafficGeneratorManager(MagicMock())
        bearer = _make_bearer()
        try:
            tm.start(1, bearer)
            with pytest.raises(ValueError, match="already running"):
                tm.start(1, bearer)
        finally:
            tm.stop(1, 1)

    def test_start_registers_task(self):
        tm = TrafficGeneratorManager(MagicMock())
        try:
            tm.start(1, _make_bearer())
            assert (1, 1) in tm.tasks
        finally:
            tm.stop(1, 1)

    def test_start_without_target_bps_raises(self):
        tm = TrafficGeneratorManager(MagicMock())
        bearer = BearerConfig(bearer_id=1, protocol="tcp")
        with pytest.raises(ValueError, match="not configured"):
            tm.start(1, bearer)

    def test_start_without_protocol_raises(self):
        tm = TrafficGeneratorManager(MagicMock())
        bearer = BearerConfig(bearer_id=1, target_bps=1000)
        with pytest.raises(ValueError, match="not configured"):
            tm.start(1, bearer)


class TestTrafficManagerStop:

    def test_stop_removes_task(self):
        tm = TrafficGeneratorManager(MagicMock())
        tm.start(1, _make_bearer())
        tm.stop(1, 1)
        assert (1, 1) not in tm.tasks

    def test_stop_nonexistent_is_noop(self):
        tm = TrafficGeneratorManager(MagicMock())
        tm.stop(99, 99)

    def test_stop_all_clears_tasks(self):
        tm = TrafficGeneratorManager(MagicMock())
        try:
            tm.start(1, _make_bearer(bearer_id=1))
            tm.start(1, _make_bearer(bearer_id=2))
            tm.start(2, _make_bearer(bearer_id=9))
            assert len(tm.tasks) == 3

            tm.stop_all()
            assert len(tm.tasks) == 0
        finally:
            tm.stop_all()


class TestTrafficManagerIsRunning:

    def test_is_running_false_initially(self):
        tm = TrafficGeneratorManager(MagicMock())
        assert tm.is_running(1, 1) is False

    def test_is_running_true_after_start(self):
        tm = TrafficGeneratorManager(MagicMock())
        try:
            tm.start(1, _make_bearer())
            assert tm.is_running(1, 1) is True
        finally:
            tm.stop(1, 1)

    def test_is_running_false_after_stop(self):
        tm = TrafficGeneratorManager(MagicMock())
        tm.start(1, _make_bearer())
        tm.stop(1, 1)
        assert tm.is_running(1, 1) is False