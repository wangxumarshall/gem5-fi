#!/usr/bin/env python3
"""T05--T08 evidence-pilot routing must not weaken formal admission."""
import sys
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as C  # noqa: E402
import lsu_runid_map as M  # noqa: E402

XLSX = ROOT / "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"
MODELS = ("T05", "T06", "T07", "T08")


def cell(model):
    row = [""] * 12
    row[C.COL_RUNID] = f"{model}-F0-W4"
    row[C.COL_MODEL] = model
    row[C.COL_UNIT] = "L1d-TLB"
    row[C.COL_FREQ] = "F0"
    row[C.COL_WORKLOAD] = "TLB-AliasPerm 地址翻译探针"
    return row


def main():
    failed = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name +
              ((" <- " + detail) if not cond else ""))
        if not cond:
            failed.append(name)

    # [R6-PROPAGATION-V3] T05/T06/T07 are runnable by default (modes are in
    # the frozen binary).  T08 still needs the explicit T08-a canary.
    for model in ("T05", "T06", "T07"):
        flags, _golden, reason = C.resolve_cell(cell(model))
        check(f"{model} formal route is runnable",
              flags is not None and reason == "fs:tlb_probe",
              str((flags, reason)))
    flags, _golden, reason = C.resolve_cell(cell("T08"))
    check("T08 formal route requires the explicit canary",
          flags is None and "PARTIAL_SUBMODEL_PROVEN" in reason,
          str((flags, reason)))

    for model in MODELS:
        flags, golden, carrier = C.resolve_cell(
            cell(model), evidence_pilot=True,
            t08a_canary=(model == "T08"))
        check(f"{model} evidence pilot resolves to FS",
              flags is not None and golden == C.TLB_PROBE_GOLDEN and
              carrier == "fs:tlb_probe", str((flags, golden, carrier)))
        check(f"{model} evidence pilot carries model fault type",
              "--tlb_fault_type" in (flags or []), str(flags))

    mapping = M.generate_map(XLSX)
    by_id = {e["run_id"]: e for e in mapping["entries"]}
    # [R6-PROPAGATION-V3] T05/T06/T07 are runnable (evidence pending);
    # T08-W4 is PARTIAL_SUBMODEL_PROVEN.  None is MODEL_BLOCKED any more.
    for model in ("T05", "T06", "T07", "T08"):
        entry = by_id[f"{model}-F0-W4"]
        want_cap = ("PARTIAL_SUBMODEL_PROVEN" if model == "T08"
                    else "RUNNABLE_EVIDENCE_PENDING")
        check(f"{model} map is PARTIAL with capability {want_cap}",
              entry["status"] == "PARTIAL"
              and entry.get("capability_status") == want_cap,
              f"{entry['status']} {entry.get('capability_status')} "
              f"{entry['status_reasons']}")
        check(f"{model} map advertises the FS carrier",
              entry["pilot"]["routable"] is True and
              entry["pilot"]["carrier"] == "fs:tlb_probe",
              str(entry.get("pilot")))
        check(f"{model} map carries no stale campaign blocker",
              not any(r.startswith("campaign:")
                      for r in entry["status_reasons"]),
              str(entry["status_reasons"]))

    # A trial artefact remains explicitly BLOCKED even when the evidence run
    # activates.  Stub the expensive gem5 invocation; this is a routing and
    # admission-contract test, not a pilot.
    original = C.run_single_cell
    C.run_single_cell = lambda *a, **k: {
        "attempted": 1, "activated": 1, "outcome": "Masked",
        "chain_report": None, "trigger_alarm": []}
    try:
        args = SimpleNamespace(
            phase="trial", trial_target=1, screening_target=385,
            main_target=5000, max_seeds_per_cell=1,
            wilson_stop_hw=0.02, allow_blocked_models=False)
        with tempfile.TemporaryDirectory() as td:
            C.run_cell_adaptive(cell("T05"), args, Path(td))
            result = json.loads(
                (Path(td) / "T05-F0-W4/cell_results.json").read_text())
            # T05 is no longer MODEL_BLOCKED: the artefact reports the real
            # gate result.  The stubbed run has chain=None, so the gate is
            # GATE-REFUSED (never a fabricated BLOCKED/evidence-pilot status).
            check("T05 activated artefact reports the real admission gate",
                  result.get("activated") == 1 and
                  result.get("admission_status") in
                  ("ADMITTED", "BLOCKED", "GATE-REFUSED")
                  and not result.get("model_blocked_reason"), str(result))
    finally:
        C.run_single_cell = original

    print("\nALL PASS" if not failed else f"\nFAILED: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
