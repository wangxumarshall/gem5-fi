import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from terminal_rules import adjudicate  # noqa: E402


def ev(kind, seq, ptag=1, value=None, detail="", **kw):
    row = {"event_type": kind, "dyn_inst_seq": seq, "ptag": ptag,
           "new_value": value, "detail": detail}
    row.update(kw)
    return row


def test_squashed_load_is_not_masked():
    """FW02-R01 shape: response + writeback, then squash, no commit."""
    events = [
        ev("injection", 397),
        ev("memory_response", 397, value="0000000000000000"),
        ev("register_writeback", 397, value="0000000000000000"),
        ev("squash", 397, ptag=0),
    ]
    terminal, reason = adjudicate(
        events, model="FW02", observed_terminal="MASKED", oracle_pass=True,
        trace_complete=True)
    assert terminal == "SQUASHED"
    assert reason == "TARGET_SQUASHED_NO_COMMIT"


def test_committed_load_with_data_is_masked():
    events = [
        ev("injection", 50),
        ev("memory_response", 50, value="0000000000000001"),
        ev("register_writeback", 50, value="0000000000000001"),
        ev("commit", 50, ptag=0),
    ]
    terminal, _ = adjudicate(
        events, model="A01", observed_terminal="MASKED", oracle_pass=True,
        trace_complete=True)
    assert terminal == "MASKED"


def test_data_on_another_ptag_does_not_rescue_the_target():
    events = [
        ev("injection", 50),
        ev("memory_response", 99, ptag=2, value="deadbeef"),
        ev("register_writeback", 99, ptag=2, value="deadbeef"),
    ]
    terminal, reason = adjudicate(
        events, model="A01", observed_terminal="MASKED", oracle_pass=True,
        trace_complete=True)
    assert terminal == "UNRESOLVED"
    assert reason == "TARGET_NOT_COMMITTED"


def test_oracle_failure_without_causal_consumer_is_unresolved():
    """v3.2.5: an oracle FAIL alone is not SDC for a store-side fault."""
    events = [ev("injection", 50), ev("commit", 50, ptag=0)]
    terminal, reason = adjudicate(
        events, model="DA04", observed_terminal="MASKED", oracle_pass=False,
        trace_complete=True)
    assert terminal == "UNRESOLVED"
    assert reason == "ORACLE_FAIL_NO_CAUSAL_CONSUMER"


def test_oracle_failure_with_causal_consumer_is_sdc():
    events = [ev("injection", 50), ev("commit", 50, ptag=0),
              ev("consumer_commit", 51)]
    terminal, reason = adjudicate(
        events, model="DA04", observed_terminal="MASKED", oracle_pass=False,
        trace_complete=True)
    assert terminal == "SDC"
    assert reason == "ORACLE_FAIL"


def test_lp01_committed_writeback_oracle_fail_is_sdc():
    events = [
        ev("injection", 50),
        ev("memory_response", 50, value="ad14af81"),
        ev("register_writeback", 50, value="ad14af81"),
        ev("consumer_commit", 51),
        ev("commit", 50, ptag=0),
    ]
    terminal, reason = adjudicate(
        events, model="LP01", observed_terminal="MASKED", oracle_pass=False,
        trace_complete=True)
    assert terminal == "SDC"
    assert reason == "ORACLE_FAIL"


def test_lp01_no_register_writeback_is_unresolved():
    events = [ev("injection", 50), ev("memory_response", 50, value="ad14af81"),
              ev("commit", 50, ptag=0)]
    terminal, reason = adjudicate(
        events, model="LP01", observed_terminal="MASKED", oracle_pass=False,
        trace_complete=True)
    assert terminal == "UNRESOLVED"
    assert reason == "UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE"


def test_store_consumed_and_oracle_pass_is_masked_with_consumer():
    events = [
        ev("injection", 250),
        ev("store_mem_write", 250),
        ev("memory_response", 300, value="aabbccdd"),
        ev("register_writeback", 300, value="aabbccdd"),
        ev("consumer_commit", 301),
        ev("commit", 250, ptag=0),
    ]
    terminal, reason = adjudicate(
        events, model="DA04", observed_terminal="MASKED", oracle_pass=True,
        trace_complete=True)
    assert terminal == "MASKED"
    assert reason == "STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS"


def test_store_committed_lane_not_read_is_masked():
    events = [ev("injection", 250), ev("store_mem_write", 250),
              ev("commit", 250, ptag=0)]
    terminal, reason = adjudicate(
        events, model="DA04", observed_terminal="MASKED", oracle_pass=True,
        trace_complete=True)
    assert terminal == "MASKED"
    assert reason == "STORE_COMMITTED_LANE_NOT_READ"
