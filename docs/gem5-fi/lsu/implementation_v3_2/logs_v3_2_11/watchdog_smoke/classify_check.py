"""Task 5 Step 5: classification check for the LQ04 watchdog smoke (v3.2.11).

Replays, on the REAL smoke outputs, the exact branch semantics of
``run_pilot.py`` (watchdog_hit -> HANG/INCOMPLETE) and the platform
adjudication (``terminal_rules.adjudicate``), then proves the verdict is
HANG and can never be MASKED -- including the adversarial case where the
oracle would have passed.

Usage: python3 classify_check.py <smoke_outdir> <stdout_log> <stderr_log> <exit_code>
"""
import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[2] / "platform"
sys.path.insert(0, str(PLATFORM))

import run_pilot  # noqa: E402  (for _lq04_events only)
import terminal_rules  # noqa: E402
from tools.prop_trace_to_v31 import convert  # noqa: E402

out_dir = Path(sys.argv[1])
stdout_log = Path(sys.argv[2])
stderr_log = Path(sys.argv[3])
exit_code = int(sys.argv[4])

proc_stdout = stdout_log.read_text(encoding="utf-8", errors="replace")
proc_stderr = stderr_log.read_text(encoding="utf-8", errors="replace")

# --- run_pilot.py branch replay (lines 804-858), verbatim semantics -----
events = run_pilot._lq04_events(out_dir / "lq04_injections.log")
injections = [e for e in events if e.get("kind") == "injection"]
injected = len(injections)

crash_by_fault = False  # LQ04 is not in ("A01", "A03", "FW02")
timed_out = False       # no external wall-clock timeout fired; exit was clean

watchdog_hit = ("CHAOS_SQ03_WATCHDOG_EXPIRED" in (proc_stdout + proc_stderr)
                or "CHAOS_SP05_WATCHDOG_EXPIRED" in (proc_stdout + proc_stderr)
                or "CHAOS_LQ04_WATCHDOG_EXPIRED" in (proc_stdout + proc_stderr))
notimplemented = "NotImplementedError" in (proc_stdout + proc_stderr)

if timed_out:
    run_status, activation, terminal, completeness = (
        "TIMEOUT", "TRIGGERED" if injected else "NOT_TRIGGERED",
        "HANG", "INCOMPLETE")
elif watchdog_hit:
    run_status, activation, terminal, completeness = (
        "SIMULATOR_ERROR", "TRIGGERED" if injected else "NOT_TRIGGERED",
        "HANG", "INCOMPLETE")
elif exit_code != 0 and crash_by_fault:
    run_status, activation, terminal, completeness = (
        "SIMULATOR_ERROR", "TRIGGERED", "CRASH", "COMPLETE")
elif exit_code != 0:
    run_status, activation, terminal, completeness = (
        "SIMULATOR_ERROR", "TRIGGERED" if injected else "NOT_TRIGGERED",
        "CRASH", "INCOMPLETE")
else:
    # run_pilot's tail branch (unreachable here: watchdog_hit is True)
    oracle_pass_tail = False
    run_status, activation, terminal, completeness = (
        "COMPLETED", "TRIGGERED" if injected else "NOT_TRIGGERED",
        "SDC" if not oracle_pass_tail else "MASKED", "COMPLETE")

print("== run_pilot branch replay on the real smoke outputs ==")
print(f"gem5 exit code            : {exit_code}")
print(f"NotImplementedError seen  : {notimplemented}")
print(f"watchdog_hit              : {watchdog_hit}")
print(f"injected (lq04 log)       : {injected}")
print(f"run_status/activation     : {run_status}/{activation}")
print(f"terminal/completeness     : {terminal}/{completeness}")

# --- convert the real trace exactly like run_pilot lines 860-873 --------
csv_path = out_dir / "prop_trace.csv.gz"
jsonl_path = out_dir / "trace_v31.jsonl"
converted = {"rows": 0, "truncated": True, "summary": None}
if csv_path.exists():
    try:
        converted = convert(
            csv_path, jsonl_path,
            sample_run_id="watchdog-smoke-v3211", run_id="watchdog-smoke-v3211",
            sub_task_id="LQ04", fault_id="LQ04", fault_model_id="LQ04",
            run_status=run_status, activation=activation, terminal=terminal,
            completeness=completeness, allow_truncated_complete=crash_by_fault)
    except SystemExit as exc:
        print(f"convert refused: {exc}")

print("\n== trace conversion (real pipeline path) ==")
print(f"rows={converted['rows']} truncated={converted['truncated']}")

# --- platform adjudication (run_pilot lines 884-889) --------------------
trace_events = run_pilot._read_events(jsonl_path)
oracle_pass = False  # the workload never completed: no oracle run is possible
final_terminal, terminal_reason = terminal_rules.adjudicate(
    trace_events, model="LQ04", observed_terminal=terminal,
    oracle_pass=oracle_pass,
    trace_complete=(completeness == "COMPLETE"))

print("\n== terminal_rules.adjudicate(observed_terminal=HANG) ==")
print(f"events read back          : {len(trace_events)}")
print(f"final_terminal            : {final_terminal}")
print(f"terminal_reason           : {terminal_reason}")
print(f"MASKED in verdict         : {'MASKED' == final_terminal}")

# --- adversarial probe: even a passing oracle cannot make it MASKED -----
adv_terminal, adv_reason = terminal_rules.adjudicate(
    trace_events, model="LQ04", observed_terminal=terminal,
    oracle_pass=True, trace_complete=False)
print("\n== adversarial probe (oracle_pass=True) ==")
print(f"final_terminal            : {adv_terminal}")
print(f"terminal_reason           : {adv_reason}")
print(f"MASKED in verdict         : {'MASKED' == adv_terminal}")

ok = (exit_code == 1 and watchdog_hit and not notimplemented
      and final_terminal == "HANG" and adv_terminal == "HANG"
      and "MASKED" not in (final_terminal, adv_terminal))
print("\nCLASSIFICATION_CHECK: " + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
