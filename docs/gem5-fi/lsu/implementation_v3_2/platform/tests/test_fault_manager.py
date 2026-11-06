import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fault_manager import FaultManager  # noqa: E402


def test_f0_fires_exactly_once():
    fm = FaultManager("F0", max_faults=1, rng_seed=7)
    assert sum(fm.on_eligible() for _ in range(100)) == 1
    assert fm.summary()["injected"] == 1
    assert fm.summary()["fired"] is True


def test_f0_honours_warmup_and_ordinal():
    fm = FaultManager("F0", warmup_events=5, event_ordinal=3, max_faults=1)
    hits = [i for i in range(1, 12) if fm.on_eligible()]
    assert hits == [8]
    assert fm.summary()["attempted"] == 11


def test_f5_applies_to_every_post_warmup_eligible():
    fm = FaultManager("F5", warmup_events=2, max_faults=0)
    assert [fm.on_eligible() for _ in range(6)] == [False, False, True, True, True, True]


def test_f5_counts_nochange_as_applied():
    fm = FaultManager("F5", max_faults=0)
    assert fm.on_eligible(value_changed=False) is True
    s = fm.summary()
    assert s["injected"] == 1
    assert s["nochange"] == 1
    assert s["value_changed"] == 0


def test_f6_requires_named_trigger_then_once():
    fm = FaultManager("F6", target_event="store_load_forward")
    assert fm.on_eligible() is False
    assert fm.on_f6_event("tlb_hit") is False
    assert fm.on_f6_event("store_load_forward") is True
    assert fm.on_f6_event("store_load_forward") is False
    s = fm.summary()
    assert s["injected"] == 1
    assert s["trigger_events"] == 3


def test_f6_never_fires_without_trigger_event():
    fm = FaultManager("F6", target_event="missing_event")
    assert all(fm.on_eligible() is False for _ in range(10))
    assert fm.summary()["injected"] == 0


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        FaultManager("F2")
