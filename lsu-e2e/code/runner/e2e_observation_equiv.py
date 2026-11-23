#!/usr/bin/env python3
"""Quantify the observation-instrumentation impact (frozen vs E2E stream)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L

ROOT = L.ROOT
EXT = L.EXT
REP = EXT / "reports"
FROZEN_EV = ROOT / "LSU_When_v2_FINAL_FROZEN/FINAL_180_FAULT_EVIDENCE.csv"


def j(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def main():
    old_ctrl = {}
    for p in (ROOT / "results/state").glob("*-CTRL.json"):
        d = j(p)
        old_ctrl[(d.get("model"), d.get("context"))] = d
    new_ctrl = {}
    for p in (EXT / "results/state").glob("E2E-*-CTRL.json"):
        d = j(p)
        new_ctrl[(d.get("model"), d.get("context"))] = d
    frozen = {(r["ModelID"], r["ContextID"], r["TimingID"]): r
              for r in csv.DictReader(open(FROZEN_EV))}

    rows = []
    for (m, c), o in sorted(old_ctrl.items()):
        n = new_ctrl.get((m, c), {})
        same_n = o.get("eligible_n") == n.get("eligible_n")
        same_elf = o.get("elf_sha") == n.get("elf_sha")
        ord_o = o.get("eligible_ordinals") or {}
        ord_n = n.get("eligible_ordinals") or {}
        timing_changes = []
        for t in ("T01", "T02", "T03"):
            if ord_o.get(t) != ord_n.get(t):
                timing_changes.append(f"{t}:{ord_o.get(t)}->{ord_n.get(t)}")
        rows.append({
            "ModelID": m, "ContextID": c,
            "FrozenEligibleN": o.get("eligible_n"),
            "E2EEligibleN": n.get("eligible_n"),
            "EligibleDelta": ((n.get("eligible_n") or 0) -
                              (o.get("eligible_n") or 0)),
            "EligibleCensusSame": same_n,
            "FrozenChecksum": o.get("oracle_got"),
            "E2EChecksum": n.get("oracle_got"),
            "ChecksumSame": o.get("oracle_got") == n.get("oracle_got"),
            "FrozenELFSHA256": o.get("elf_sha"),
            "E2EELFSHA256": n.get("elf_sha"),
            "ELFSame": same_elf,
            "FrozenOrdinals": json.dumps(ord_o, sort_keys=True),
            "E2EOrdinals": json.dumps(ord_n, sort_keys=True),
            "OrdinalChanges": ";".join(timing_changes),
            "OrdinalSetChanged": bool(timing_changes),
            "StreamChanged": (not same_n) or (not same_elf) or
                             bool(timing_changes),
        })
    p = REP / "STRICT_E2E_OBSERVATION_EQUIVALENCE.csv"
    REP.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Per-fault target identity comparison.
    trows = []
    for rid, f in sorted(frozen.items()):
        m, c, t = rid
        new = j(EXT / "evidence/strict_chains" /
                f"E2E-{m}-{c}-{t}-FAULT.strict.json")
        new_tgt = (new.get("target") or {}).get("seq")
        old_tgt = int(f["TARGET_SEQ"]) if f.get("TARGET_SEQ") else None
        new_ord = None
        st = j(EXT / "results/state" / f"E2E-{m}-{c}-{t}-FAULT.json")
        if st:
            new_ord = st.get("observed_ordinal")
        trows.append({
            "ModelID": m, "ContextID": c, "TimingID": t,
            "FrozenTargetSeq": old_tgt, "E2ETargetSeq": new_tgt,
            "TargetSeqSame": old_tgt == new_tgt,
            "FrozenOrdinal": f.get("SelectedOrdinal"),
            "E2EObservedOrdinal": new_ord,
            "OrdinalSame": (str(f.get("SelectedOrdinal")) ==
                            str(new_ord)),
            "FrozenOutcome": f.get("TERMINAL_OUTCOME"),
            "E2EOutcome": new.get("terminal"),
            "OutcomeSame": f.get("TERMINAL_OUTCOME") == new.get("terminal"),
            "ObservationInducedPathChange":
                (old_tgt != new_tgt) or
                (str(f.get("SelectedOrdinal")) != str(new_ord)),
        })
    p2 = REP / "STRICT_E2E_TARGET_IDENTITY_COMPARISON.csv"
    with open(p2, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(trows[0]))
        w.writeheader()
        w.writerows(trows)
    changed = sum(1 for r in trows if r["ObservationInducedPathChange"])
    print(f"wrote {p} and {p2}; target-identity path changes {changed}/180")


if __name__ == "__main__":
    main()
