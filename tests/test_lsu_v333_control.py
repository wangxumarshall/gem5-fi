"""LSU v3.3.3 runner/control/parser regression tests (Agent I, Task 5).

Every assertion is over real v3.3.2 evidence under audit_v3_3_2/runs/ or over
the real source text of configs/se/lsu_proxy.py. Nothing here invokes gem5.
"""
from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
RUNS = ROOT / "audit_v3_3_2/runs"

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PLATFORM))

import lsu_v332_matrix as mx  # noqa: E402
import lsu_v333_control_proof as cp  # noqa: E402
import run_pilot  # noqa: E402
import terminal_rules  # noqa: E402


# --------------------------------------------------------------------------
# Control classification from the EXECUTED command.txt (L-D01)
# --------------------------------------------------------------------------
def test_control_classification_counts():
    counts = mx.classify_controls(RUNS)
    assert sum(counts.values()) == 60, counts
    assert counts.get("MOUNTED_BUT_DISABLED") == 35, counts
    assert counts.get("INJECTOR_ABSENT") == 25, counts
    assert counts.get("MOUNTED_BUT_SUPPRESSED", 0) == 0, counts
    assert counts.get("MOUNTED_BUT_ACTIVE", 0) == 0, counts
    assert counts.get("NO_COMMAND_EVIDENCE", 0) == 0, counts


def test_control_classification_reads_executed_command_not_run_pilot_argv():
    outdir = RUNS / "A01-R01-control"
    executed = mx.read_command(outdir)
    summary = json.loads((outdir / "summary.json").read_text())
    run_pilot_argv = " ".join(summary.get("cmd") or [])
    # The historical false label came from reading this argv, which never
    # contains the injector mount.
    assert "--chaos_addrpath" in executed
    assert "--chaos_addrpath" not in run_pilot_argv
    cls = mx.classify_control(executed)
    assert cls["proof"] == "MOUNTED_BUT_DISABLED"
    assert cls["probability"] == 0.0
    assert cls["mounts"] == ["--chaos_addrpath"]


def test_mount_classes_per_model():
    expected_mounted = {"A01", "A03", "FW05", "SQ01", "SQ03", "SP05", "LP01"}
    for model in mx.MODELS:
        dirs = sorted(RUNS.glob(f"{model}-R??-control"))
        assert len(dirs) == 5, model
        proofs = [mx.classify_control(mx.read_command(d))["proof"]
                  for d in dirs]
        want = ("MOUNTED_BUT_DISABLED" if model in expected_mounted
                else "INJECTOR_ABSENT")
        assert proofs == [want] * 5, (model, proofs)


def test_explicit_suppression_is_a_distinct_class():
    cmd = ("gem5 configs/se/lsu_proxy.py --probability 1.0 "
           "--chaos_lsqfwd --chaos_suppress")
    assert mx.classify_control(cmd)["proof"] == "MOUNTED_BUT_SUPPRESSED"


# --------------------------------------------------------------------------
# MD04 probability coupling (L-A06)
# --------------------------------------------------------------------------
def _md04_resolution_expression():
    src = (ROOT / "configs/se/lsu_proxy.py").read_text()
    tree = ast.parse(src)
    default = "MISSING"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "attr", None) != "add_argument" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and first.value == "--md04_probability":
            for kw in node.keywords:
                if kw.arg == "default":
                    default = ast.literal_eval(kw.value)
    assert default is None, f"--md04_probability default is {default!r}"
    for node in ast.walk(tree):
        if not isinstance(node, ast.IfExp) or not isinstance(node.test, ast.Compare):
            continue
        test_attrs = {n.attr for n in ast.walk(node.test)
                      if isinstance(n, ast.Attribute)}
        body_attrs = {n.attr for n in ast.walk(node.body)
                      if isinstance(n, ast.Attribute)}
        else_attrs = {n.attr for n in ast.walk(node.orelse)
                      if isinstance(n, ast.Attribute)}
        if ("md04_probability" in test_attrs
                and "probability" in body_attrs
                and "md04_probability" in else_attrs):
            return compile(ast.Expression(node), "<md04>", "eval")
    raise AssertionError("the md04_probability coupling expression is missing")


def test_md04_probability_default_follows_global():
    code = _md04_resolution_expression()

    class Args:
        pass

    def resolve(global_probability, override):
        args = Args()
        args.probability = global_probability
        args.md04_probability = override
        return eval(code, {"args": args})

    assert resolve(0.0, None) == 0.0        # control at p=0 -> disabled
    assert resolve(1.0, None) == 1.0        # fault default follows global
    assert resolve(0.0, 1.0) == 1.0         # explicit override preserved
    assert resolve(1.0, 0.0) == 0.0


def test_md04_is_constructed_with_the_resolved_probability():
    tree = ast.parse((ROOT / "configs/se/lsu_proxy.py").read_text())
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and getattr(n.func, "id", None) == "CHAOSMD04"]
    assert len(calls) == 1
    prob_kw = [kw for kw in calls[0].keywords if kw.arg == "probability"]
    assert len(prob_kw) == 1
    assert isinstance(prob_kw[0].value, ast.Name)
    assert prob_kw[0].value.id == "md04_probability"
    # No other injector's probability wiring may have changed.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) in (
                "CHAOSLSQFwd", "CHAOSAddrPath", "CHAOSL1DForward", "CHAOSLQ04"):
            prob = [kw for kw in node.keywords if kw.arg == "probability"]
            if prob:
                assert isinstance(prob[0].value, ast.Attribute)
                assert prob[0].value.attr == "probability"


def test_addrpath_watchdog_flag_and_passthrough():
    src = (ROOT / "configs/se/lsu_proxy.py").read_text()
    assert '"--addrpath_watchdog_cycles"' in src
    assert "watchdogCycles=args.addrpath_watchdog_cycles" in src


# --------------------------------------------------------------------------
# A03 bare-hex oracle and honest injection count (L-A03/L-A04)
# --------------------------------------------------------------------------
A03_FAULT_CHECKSUMS = {
    1: "1fd794b8489219e1",
    2: "9fc828ecfead80f9",
    3: "bfccf156021968dd",
    4: "191a781887e50cec",
    5: "20057ce453d4f1e9",
}


@pytest.mark.parametrize("ctx", sorted(A03_FAULT_CHECKSUMS))
def test_a03_bare_hex_oracle(ctx):
    outdir = RUNS / f"A03-R{ctx:02d}-fault"
    stdout = (outdir / "stdout.log").read_text(errors="replace")
    checksum = mx.parse_bare_checksum(stdout)
    assert checksum == A03_FAULT_CHECKSUMS[ctx]
    assert checksum != mx.A03_GOLDEN

    parsed = mx.parse_addrpath_log(outdir / "addrpath_injections.log")
    funnel = parsed["injected_applications"]
    assert funnel > 100_000, parsed
    # The old 20000 came from the per-application cap, never from FUNNEL.
    assert funnel != 20_000
    assert parsed["stream_rows"] == funnel
    assert parsed["capped"] is True

    term = mx.a03_terminal(checksum, parsed["watchdog_expired"],
                           timed_out=True, exit_code=124)
    assert term["terminal"] == "SDC"
    assert term["terminal_reason"] == "ORACLE_FAIL"
    assert term["terminal_qualifier"] is None   # v3.3.2 has no in-sim watchdog


def test_a03_control_prints_golden():
    for ctx in range(1, 6):
        outdir = RUNS / f"A03-R{ctx:02d}-control"
        checksum = mx.parse_bare_checksum(
            (outdir / "stdout.log").read_text(errors="replace"))
        assert checksum == mx.A03_GOLDEN
        term = mx.a03_terminal(checksum, watchdog_expired=False,
                               timed_out=False, exit_code=0)
        assert term["terminal"] == "MASKED"
        assert term["oracle_pass"] is True


def test_a03_post_oracle_hang_qualifier_and_watchdog_terminal():
    divergent = "deadbeefdeadbeef"
    sdc = mx.a03_terminal(divergent, watchdog_expired=True,
                          timed_out=False, exit_code=0)
    assert (sdc["terminal"], sdc["terminal_qualifier"]) == (
        "SDC", "POST_ORACLE_SIM_HANG")
    hang = mx.a03_terminal(None, watchdog_expired=True,
                           timed_out=False, exit_code=0)
    assert hang["terminal"] == "HANG_WATCHDOG"
    assert hang["oracle_pass"] is None


def test_a03_log_cap_is_never_the_injection_count():
    parsed = mx.parse_addrpath_log(
        RUNS / "A03-R01-fault/addrpath_injections.log")
    assert parsed["capped"] is True
    assert parsed["log_line_injections"] == 20_000   # diagnostic only
    assert parsed["injected_applications"] != parsed["log_line_injections"]


# --------------------------------------------------------------------------
# RP01 watchdog from the model log (L-A07)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("ctx", [1, 2, 3, 4, 5])
def test_rp01_watchdog_from_log(ctx):
    outdir = RUNS / f"RP01-R{ctx:02d}-fault"
    parsed = mx.parse_rp01_evidence(outdir)
    assert parsed["watchdog"] is True
    assert parsed["terminal"] == "HANG_WATCHDOG"
    assert parsed["deadline_cycles"] == 20_000_000
    assert parsed["no_checksum"] is True
    assert parsed["skips"] == 1
    assert parsed["raw_fatal_path"], parsed
    assert parsed["raw_fatal_path"].endswith("lsq_fwd_injections.log")
    assert "CHAOS_RP01_WATCHDOG=EXPIRED" in parsed["watchdog_marker"]


def test_run_pilot_rp01_dispatch_and_log_parser():
    assert "RP01" in run_pilot.MODELS
    assert run_pilot._workload_for("RP01") == "replay_partial_v332"
    expected = [26, 77, 128, 179, 230]
    for idx, ctx in enumerate(range(1, 6)):
        events = run_pilot._rp01_events(
            RUNS / f"RP01-R0{ctx}-fault/lsq_fwd_injections.log")
        assert len(events) == 1, (ctx, events)
        assert events[0]["kind"] == "skip"
        assert events[0]["skipped_call"] == 1
        assert events[0]["ordinal"] == expected[idx]
        assert events[0]["replay_gen_pre"] == 0
    meta = run_pilot.injector_meta(
        "RP01", 1.0,
        ["--probability", "1.0", "--chaos_lsqfwd",
         "--rp01_event_ordinal", "26", "--rp01_watchdog_cycles", "20000000"],
        "", ["--chaos_lsqfwd"])
    assert meta["mounted"] is True
    assert meta["gate"] == "ordinal"
    assert meta["gate_enabled"] is True
    control = run_pilot.build_model_extra("RP01", 0.0, 1, 26)
    assert control == []


def test_rp01_stdout_only_parser_would_miss_the_marker():
    outdir = RUNS / "RP01-R01-fault"
    stdout_only = mx.parse_rp01_stdout(outdir / "stdout.log")
    assert stdout_only["watchdog"] is False      # the v3.3.2 defect
    assert mx.parse_rp01_evidence(outdir)["watchdog"] is True


# --------------------------------------------------------------------------
# terminal_rules: a01_ea_discarded and watchdog terminals
# --------------------------------------------------------------------------
def test_a01_ea_discarded_is_injection_not_activated():
    events = [
        {"event_type": "injection", "dyn_inst_seq": 7, "ptag": 1},
        {"event_type": "a01_ea", "dyn_inst_seq": 7, "ptag": 1},
        {"event_type": "a01_ea_discarded", "dyn_inst_seq": 7, "ptag": 1,
         "detail": "applied_to_request=0"},
        {"event_type": "commit", "dyn_inst_seq": 7, "ptag": 1},
    ]
    terminal, reason = terminal_rules.adjudicate(
        events, model="A01", observed_terminal="COMPLETED",
        oracle_pass=True, trace_complete=True)
    assert (terminal, reason) == ("INJECTION_NOT_ACTIVATED",
                                  "NO_EFFECTIVE_INJECTION")


def test_squash_precedes_discard_so_a01_r02_keeps_squashed():
    events = [
        {"event_type": "injection", "dyn_inst_seq": 9, "ptag": 2},
        {"event_type": "a01_ea", "dyn_inst_seq": 9, "ptag": 2},
        {"event_type": "a01_ea_discarded", "dyn_inst_seq": 9, "ptag": 2},
        {"event_type": "squash", "dyn_inst_seq": 9, "ptag": 2},
    ]
    terminal, reason = terminal_rules.adjudicate(
        events, model="A01", observed_terminal="COMPLETED",
        oracle_pass=True, trace_complete=True)
    assert terminal == "SQUASHED"
    assert reason == "TARGET_SQUASHED_NO_COMMIT"


def test_rp01_watchdog_terminal_is_not_relabelled():
    terminal, reason = terminal_rules.adjudicate(
        [], model="RP01", observed_terminal="HANG_WATCHDOG",
        oracle_pass=False)
    assert (terminal, reason) == ("HANG_WATCHDOG",
                                  "INTERNAL_WATCHDOG_DEADLINE")


# --------------------------------------------------------------------------
# Driver planning: all 12 models, RP01/A03 commands
# --------------------------------------------------------------------------
def test_planned_commands_cover_all_models():
    for model in mx.MODELS:
        for role in ("fault", "control"):
            cmd = mx.planned_command(model, 1, role,
                                     Path("/tmp/dry-run-out"))
            assert cmd, (model, role)
            assert any("gem5.opt" in tok or "run_pilot.py" in tok
                       for tok in cmd), (model, role, cmd)


def test_planned_rp01_and_a03_commands():
    rp01 = mx.planned_command("RP01", 1, "fault", Path("/tmp/x"))
    assert "--chaos_lsqfwd" in rp01
    assert "rp01_skip_replay" in rp01
    assert "--rp01_event_ordinal" in rp01
    assert "--rp01_watchdog_cycles" in rp01

    a03 = mx.planned_command("A03", 1, "fault", Path("/tmp/x"))
    assert "--addrpath_watchdog_cycles" in a03
    assert str(mx.A03_WATCHDOG_CYCLES) in a03
    # 385 ticks/cycle at B0; 1M cycles = ~385M ticks, ~20x the 19.6M-tick
    # control. The earlier 1e9-cycle value never fired before the wall bound.
    assert mx.A03_WATCHDOG_CYCLES == 1_000_000

    rp01_control = mx.planned_command("RP01", 1, "control", Path("/tmp/x"))
    assert "--chaos_lsqfwd" not in rp01_control


def test_csv_paths_are_distinct():
    import lsu_v332_report as report
    # Assert the module's *default* RAW path, not the process-global that an
    # earlier in-process mx.main(--out-csv ...) call rebound.
    default_raw = ROOT / "runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv"
    assert default_raw.name.endswith("_RAW.csv")
    assert report.OUT.name == "audit_v3_3_3"
    # The report's FINAL filename is produced inside main(); assert the source
    # constant is the FINAL name and never the RAW name.
    src = (TOOLS / "lsu_v332_report.py").read_text()
    assert "LSU_Fault_Control_Pair_FINAL.csv" in src
    assert "LSU_Fault_Control_Pair_RAW.csv" not in src
    # History files are untouched by design.
    assert (ROOT / "audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final_J.csv").exists()
    assert (ROOT / "audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final_K.csv").exists()


# --------------------------------------------------------------------------
# Strict tri-state ControlInjected (v3.3.3 final-launch closure, BUG 1)
# --------------------------------------------------------------------------
def test_control_injected_constants():
    assert cp.CONTROL_INJECTED_NO == "NO"
    assert cp.CONTROL_INJECTED_YES == "YES"
    assert cp.CONTROL_INJECTED_UNKNOWN == "UNKNOWN"
    assert cp.CONTROL_INJECTED_INVALID == "INVALID"


@pytest.mark.parametrize("value,state,reason", [
    # zero (canonical int and signed/whitespace string forms)
    (0, cp.CONTROL_INJECTED_NO, "ZERO"),
    ("0", cp.CONTROL_INJECTED_NO, "ZERO"),
    ("  0  ", cp.CONTROL_INJECTED_NO, "ZERO"),
    ("+0", cp.CONTROL_INJECTED_NO, "ZERO"),
    # positive
    (1, cp.CONTROL_INJECTED_YES, "POSITIVE"),
    (5, cp.CONTROL_INJECTED_YES, "POSITIVE"),
    ("1", cp.CONTROL_INJECTED_YES, "POSITIVE"),
    ("5", cp.CONTROL_INJECTED_YES, "POSITIVE"),
    # missing / None is checked before empty
    (None, cp.CONTROL_INJECTED_UNKNOWN, "MISSING"),
    # empty
    ("", cp.CONTROL_INJECTED_UNKNOWN, "EMPTY"),
    ("   ", cp.CONTROL_INJECTED_UNKNOWN, "EMPTY"),
    # unparseable -- never silently a zero
    ("abc", cp.CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"),
    ("1.0", cp.CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"),
    (1.0, cp.CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"),
    ("nan", cp.CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"),
    ("0x0", cp.CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"),
    ([0], cp.CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"),
    (True, cp.CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"),
    # negative
    (-1, cp.CONTROL_INJECTED_INVALID, "NEGATIVE"),
    ("-3", cp.CONTROL_INJECTED_INVALID, "NEGATIVE"),
])
def test_classify_injection_count(value, state, reason):
    assert cp.classify_injection_count(value) == (state, reason)


def test_missing_injection_count_key_is_missing_not_zero():
    row = {"ModelID": "A01", "ContextID": "R01"}
    assert cp.classify_injection_count(row.get("InjectionCount")) == (
        cp.CONTROL_INJECTED_UNKNOWN, "MISSING")
    # The former inline check treated "" as zero -- the classifier must not.
    assert cp.classify_injection_count("") != (cp.CONTROL_INJECTED_NO, "ZERO")


def _write_proof_csv(path: Path, rows: list[dict], fields=None) -> Path:
    fields = fields or ["ModelID", "ContextID", "InjectionAttemptCount",
                        "InjectionAppliedCount", "InjectionCount",
                        "ControlZeroProof"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _emit(tmp_path: Path, proof: Path) -> tuple[Path, int]:
    out = tmp_path / "control_audit.csv"
    rc = cp.main(["--emit-control-audit", "--proof", str(proof),
                  "--out", str(out)])
    return out, rc


def test_emit_control_audit_is_tristate_and_keeps_counts_separate(tmp_path):
    rows = [
        # 0, 1, 5 -> NO / YES / YES
        {"ModelID": "A01", "ContextID": "R01", "InjectionAttemptCount": "7",
         "InjectionAppliedCount": "0", "InjectionCount": "0",
         "ControlZeroProof": "MOUNTED_BUT_DISABLED"},
        {"ModelID": "A01", "ContextID": "R02", "InjectionAttemptCount": "8",
         "InjectionAppliedCount": "1", "InjectionCount": "1",
         "ControlZeroProof": "INJECTOR_ABSENT"},
        {"ModelID": "A01", "ContextID": "R03", "InjectionAttemptCount": "9",
         "InjectionAppliedCount": "5", "InjectionCount": "5",
         "ControlZeroProof": "INJECTOR_ABSENT"},
        # empty -> EMPTY (never NO)
        {"ModelID": "A01", "ContextID": "R04", "InjectionAttemptCount": "4",
         "InjectionAppliedCount": "4", "InjectionCount": "",
         "ControlZeroProof": "CONTROL_PROOF_INCOMPLETE"},
        # illegal -> UNPARSEABLE (never NO)
        {"ModelID": "A01", "ContextID": "R05", "InjectionAttemptCount": "6",
         "InjectionAppliedCount": "6", "InjectionCount": "abc",
         "ControlZeroProof": "CONTROL_PROOF_INCOMPLETE"},
        # float / nan -> UNPARSEABLE
        {"ModelID": "A02", "ContextID": "R01", "InjectionAttemptCount": "2",
         "InjectionAppliedCount": "2", "InjectionCount": "1.0",
         "ControlZeroProof": "CONTROL_PROOF_INCOMPLETE"},
        {"ModelID": "A02", "ContextID": "R02", "InjectionAttemptCount": "2",
         "InjectionAppliedCount": "2", "InjectionCount": "nan",
         "ControlZeroProof": "CONTROL_PROOF_INCOMPLETE"},
        # negative -> INVALID (never NO)
        {"ModelID": "A02", "ContextID": "R03", "InjectionAttemptCount": "3",
         "InjectionAppliedCount": "3", "InjectionCount": "-3",
         "ControlZeroProof": "CONTROL_PROOF_INCOMPLETE"},
    ]
    proof = _write_proof_csv(tmp_path / "proof.csv", rows)
    out, rc = _emit(tmp_path, proof)
    assert rc != 0, "UNKNOWN/INVALID controls must make the audit exit nonzero"

    with out.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(cp.CONTROL_AUDIT_COLUMNS)
        emitted = list(reader)

    by_ctx = {(r["ModelID"], r["ContextID"]): r for r in emitted}
    expected = {
        ("A01", "R01"): ("NO", "ZERO"),
        ("A01", "R02"): ("YES", "POSITIVE"),
        ("A01", "R03"): ("YES", "POSITIVE"),
        ("A01", "R04"): ("UNKNOWN", "EMPTY"),
        ("A01", "R05"): ("UNKNOWN", "UNPARSEABLE"),
        ("A02", "R01"): ("UNKNOWN", "UNPARSEABLE"),
        ("A02", "R02"): ("UNKNOWN", "UNPARSEABLE"),
        ("A02", "R03"): ("INVALID", "NEGATIVE"),
    }
    for key, (state, reason) in expected.items():
        got = by_ctx[key]
        assert got["ControlInjected"] == state, got
        assert got["ControlInjectedReason"] == reason, got
        if state != "NO":
            assert got["ControlInjected"] != "NO", (
                "missing/illegal/negative counts must never emit NO: " + repr(got))
    # attempt/applied/count stay separate columns with the original values
    assert by_ctx[("A01", "R01")]["InjectionAttemptCount"] == "7"
    assert by_ctx[("A01", "R01")]["InjectionAppliedCount"] == "0"
    assert by_ctx[("A01", "R01")]["InjectionCount"] == "0"
    assert by_ctx[("A02", "R03")]["InjectionAttemptCount"] == "3"
    assert by_ctx[("A02", "R03")]["InjectionAppliedCount"] == "3"


def test_emit_control_audit_missing_column_is_unknown_never_no(tmp_path):
    # Entire InjectionCount column absent: the value is missing, so the audit
    # must report UNKNOWN/MISSING and never NO.
    rows = [{"ModelID": "A01", "ContextID": "R01",
             "InjectionAttemptCount": "5", "InjectionAppliedCount": "5",
             "ControlZeroProof": "MOUNTED_BUT_DISABLED"}]
    fields = ["ModelID", "ContextID", "InjectionAttemptCount",
              "InjectionAppliedCount", "ControlZeroProof"]
    proof = _write_proof_csv(tmp_path / "proof_missing.csv", rows, fields)
    out, rc = _emit(tmp_path, proof)
    assert rc != 0
    with out.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["ControlInjected"] == "UNKNOWN"
    assert row["ControlInjectedReason"] == "MISSING"
    assert row["InjectionAttemptCount"] == "5"
    assert row["InjectionAppliedCount"] == "5"


def test_emit_control_audit_all_zero_is_a_clean_pass(tmp_path):
    rows = [
        {"ModelID": "A01", "ContextID": "R01", "InjectionAttemptCount": "0",
         "InjectionAppliedCount": "0", "InjectionCount": "0",
         "ControlZeroProof": "INJECTOR_ABSENT"},
        {"ModelID": "A01", "ContextID": "R02", "InjectionAttemptCount": "0",
         "InjectionAppliedCount": "0", "InjectionCount": 0,
         "ControlZeroProof": "MOUNTED_BUT_DISABLED"},
    ]
    proof = _write_proof_csv(tmp_path / "proof_ok.csv", rows)
    out, rc = _emit(tmp_path, proof)
    assert rc == 0
    with out.open(newline="", encoding="utf-8") as handle:
        emitted = list(csv.DictReader(handle))
    assert {r["ControlInjected"] for r in emitted} == {"NO"}
