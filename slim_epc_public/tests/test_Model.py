import pytest
from pydantic import ValidationError

from epc.models import BearerConfig
from epc.models import UEState
from epc.models import StartTrafficRequest

class TestBearerConfig:
    #max=9
    def test_bearer_id_higher(self):
        with pytest.raises(ValidationError):
            BearerConfig(bearer_id=10)

    #min=1
    def test_bearer_id_lower(self):
        with pytest.raises(ValidationError):
            BearerConfig(bearer_id=0)

    #only tcp and udp
    def test_invalid_protocol(self):
        with pytest.raises(ValidationError):
            BearerConfig(bearer_id=1, protocol="http")

class TestUEState:

    def test_ue_id_min(self):
        ue = UEState(ue_id=1)
        assert ue.ue_id == 1

    def test_ue_id_max(self):
        ue = UEState(ue_id=100)
        assert ue.ue_id == 100

    def test_ue_id_too_low(self):
        with pytest.raises(ValidationError):
            UEState(ue_id=0)

    def test_ue_id_too_high(self):
        with pytest.raises(ValidationError):
            UEState(ue_id=101)

    def test_default_empty_bearers(self):
        ue = UEState(ue_id=1)
        assert ue.bearers == {}

    def test_default_empty_stats(self):
        ue = UEState(ue_id=1)
        assert ue.stats == {}

class TestTargetBps:

    def test_mbps_integer(self):
        r = StartTrafficRequest(protocol="tcp", Mbps=10)
        assert r.target_bps() == 10_000_000

    def test_mbps_float(self):
        r = StartTrafficRequest(protocol="tcp", Mbps=1.5)
        assert r.target_bps() == 1_500_000

    def test_mbps_small(self):
        r = StartTrafficRequest(protocol="tcp", Mbps=0.001)
        assert r.target_bps() == 1_000

    def test_kbps_integer(self):
        r = StartTrafficRequest(protocol="tcp", kbps=500)
        assert r.target_bps() == 500_000

    def test_kbps_float(self):
        r = StartTrafficRequest(protocol="tcp", kbps=1.5)
        assert r.target_bps() == 1_500

    def test_bps_integer(self):
        r = StartTrafficRequest(protocol="tcp", bps=1234)
        assert r.target_bps() == 1234

    def test_bps_float_truncated(self):
        r = StartTrafficRequest(protocol="tcp", bps=999.9)
        assert r.target_bps() == 999

    def test_bps_zero(self):
        r = StartTrafficRequest(protocol="tcp", bps=0)
        assert r.target_bps() == 0