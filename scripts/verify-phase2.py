#!/usr/bin/env python3
"""Audit the five Phase-2 milestones against their artifacts and assertions.

The audit is deliberately mechanical: every milestone is bound to a JSON
artifact, a small set of success assertions, and the date of the run.  It does
not read the verification prose; it recomputes what it can.

Usage: python3 scripts/verify-phase2.py
Output: m5out/phase2-gate/phase2_milestones.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "m5out"
GATE = OUT / "phase2-gate"


def load(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def main():
    milestones = {}

    # p2-mask: avalanche on all 19 templates, with discriminating penalties.
    avalanche = load(OUT / "phase2-avalanche/avalanche.json")
    if avalanche is None:
        milestones["p2-mask"] = {"status": "FAIL",
                                 "detail": "missing avalanche.json"}
    else:
        templates = avalanche.get("templates", {})
        penalties = [row.get("masking_penalty", -1)
                     for row in templates.values()]
        ok = (len(templates) == 19
              and all(0.0 <= value <= 1.0 for value in penalties)
              and any(value > 0.5 for value in penalties)
              and any(value < 0.5 for value in penalties))
        milestones["p2-mask"] = {
            "status": "PASS" if ok else "FAIL",
            "detail": (f"{len(templates)} templates; penalty range "
                       f"{min(penalties, default=-1):.3f}.."
                       f"{max(penalties, default=-1):.3f}; "
                       f">0.5:{sum(1 for value in penalties if value > 0.5)}, "
                       f"<0.5:{sum(1 for value in penalties if value < 0.5)}"),
            "artifact": "m5out/phase2-avalanche/avalanche.json",
        }

    # p2-rl-pipeline: training history, policy dimensions, baseline.
    training = load(OUT / "phase2-rl/training.json")
    policy = load(OUT / "phase2-rl/policy.json")
    if training is None or policy is None:
        milestones["p2-rl-pipeline"] = {
            "status": "FAIL", "detail": "missing training.json or policy.json"}
    else:
        history = training.get("history", [])
        ok = (len(history) >= 100
              and policy.get("state_dim") == 32
              and policy.get("action_dim") == 10
              and isinstance(history[0].get("reward"), (int, float)))
        milestones["p2-rl-pipeline"] = {
            "status": "PASS" if ok else "FAIL",
            "detail": (f"episodes={len(history)}; "
                       f"state_dim={policy.get('state_dim')}; "
                       f"action_dim={policy.get('action_dim')}; "
                       f"trained_mean={training.get('trained_mean_reward'):.3f}; "
                       f"baseline_mean={training.get('baseline_mean_reward'):.3f}"),
            "artifact": "m5out/phase2-rl/training.json",
        }

    # p2-rl-mutator: four action families exercised, best stream exported.
    best = load(OUT / "phase2-rl/best_stream.json")
    validation = load(OUT / "phase2-rl/validation.json")
    if training is None or best is None:
        milestones["p2-rl-mutator"] = {
            "status": "FAIL", "detail": "missing action_counts or best_stream"}
    else:
        counts = training.get("action_counts", {})
        exercised = sum(1 for key in ("replace", "operand", "power",
                                      "recombine") if counts.get(key, 0) > 0)
        body = best.get("body", [])
        rl_row = (validation or {}).get("streams", {}).get("rl-best-fp", {})
        base_row = (validation or {}).get("streams", {}).get(
            "fp-add-baseline", {})
        ok = (exercised >= 3 and len(body) > 0
              and rl_row.get("n", 0) >= 10 and base_row.get("n", 0) >= 10)
        detail = (f"action families exercised={exercised}/4; "
                  f"counts={counts}; best_body_ops={len(body)}; "
                  f"best_sfi={training.get('trained_best_sfi')}")
        if validation:
            detail += (f"; FI rl={rl_row.get('sdc')}/{rl_row.get('n')} "
                       f"vs fp-add={base_row.get('sdc')}/{base_row.get('n')} "
                       f"fisher={validation.get('fisher_p'):.3g}")
        milestones["p2-rl-mutator"] = {
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
            "artifact": "m5out/phase2-rl/validation.json",
        }

    # p2-power3: nine streams across the three types, McPAT attempted.
    streams = load(OUT / "phase2-power/streams.json")
    measurements = load(OUT / "phase2-power/power_measurements.json")
    if streams is None or measurements is None:
        milestones["p2-power3"] = {
            "status": "FAIL", "detail": "missing streams/measurements"}
    else:
        stream_rows = streams.get("streams", {})
        measured = measurements.get("streams", {})
        patterns = {row.get("pattern") for row in stream_rows.values()}
        mcpat_ok = sum(1 for row in measured.values()
                       if row.get("mcpat", {}).get("status") == "ok")
        ok = (len(stream_rows) == 9 and len(measured) == 9
              and patterns == {"type1", "type2", "type3"} and mcpat_ok >= 3)
        milestones["p2-power3"] = {
            "status": "PASS" if ok else "FAIL",
            "detail": (f"streams={len(stream_rows)}; measured={len(measured)}; "
                       f"patterns={sorted(patterns)}; mcpat_ok={mcpat_ok}"),
            "artifact": "m5out/phase2-power/power_measurements.json",
        }

    # p2-power-corr: correlation records + H1/H2/H3.
    correlation = load(OUT / "phase2-power/correlation.json")
    if correlation is None:
        milestones["p2-power-corr"] = {
            "status": "FAIL", "detail": "missing correlation.json"}
    else:
        records = correlation.get("records", [])
        h1 = correlation.get("h1_power_vs_sdc", {})
        h2 = correlation.get("h2_oscillation_vs_continuous", {})
        h3 = correlation.get("h3_hotspot_vs_global", {})
        ok = (len(records) >= 6 and "average" in h1
              and h2.get("pairs_count", 0) >= 1
              and h3.get("pairs_count", 0) >= 1)
        milestones["p2-power-corr"] = {
            "status": "PASS" if ok else "FAIL",
            "detail": (f"records={len(records)}; "
                       f"h1_features={sorted(h1)}; "
                       f"h2_pairs={h2.get('pairs_count')}; "
                       f"h3_pairs={h3.get('pairs_count')}; "
                       f"h2_fisher={h2.get('fisher_p')}; "
                       f"h3_fisher={h3.get('fisher_p')}"),
            "artifact": "m5out/phase2-power/correlation.json",
        }

    overall = "PASS" if all(row["status"] == "PASS"
                            for row in milestones.values()) else "FAIL"
    payload = {
        "schema": "sdcfuzz.phase2.milestones.v1",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "overall": overall,
        "milestones": milestones,
    }
    GATE.mkdir(parents=True, exist_ok=True)
    (GATE / "phase2_milestones.json").write_text(
        json.dumps(payload, indent=2) + "\n")
    for name, row in milestones.items():
        print(f"{row['status']:4s} {name:16s} {row['detail']}")
    print(f"overall: {overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
