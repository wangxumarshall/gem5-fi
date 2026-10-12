#!/usr/bin/env python3
"""[OOO][P1] ooo_handoff unit test (plan Task 12 prep).

Synthetic campaign fixture (no gem5): 3 samples (Masked with L3-unsupported
gap, Crash, Inactive) + results.jsonl + a mini guard monitor log. Pins:
  * per-class counts and n_valid/n_rows;
  * conservation bookkeeping (activated == five-primary + post-sim);
  * chain histogram incl. the L3-unsupported-only honest bucket;
  * first-divergence summary picks the first non-Masked sample;
  * resource peak windowing;
  * handoff.json + handoff.md are written and machine-parseable.

Run: python3 tools/tests/test_ooo_handoff.py
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "tools"))
import ooo_handoff  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


CAMPAIGN_YAML = """schema_version: arm-chaos-fi/l0l5-campaign/v1
campaign_id: fixture_campaign
runid_row: D01-F0-W6
submodel: c
phase: engineering
injector: decode
config: C3
mode: SE
grid:
  target_index: -1
  field: imm
  width_bits: 32
  sub_field: imm_bitflip
  fault_model: transient_bit_flip
  protection_model: none
n_per_cell: 3
base_seed: 52000000
replay_pct: 100
workload:
  binary: workloads/ooo/smoke/smoke
  binary_sha256: 30cd303815735206e697df0163887bceecec2388a26d22cfc27a4dc8cb98e85d
  golden_id: smoke-golden-v1
  trigger_mode: cycle
  trigger_value: 1000
limits:
  max_faults: 1
hang_timeout: 600
chaos_commit: ffffffff11111111
patchset_sha256: ffffffff11111111
trace:
  enabled: true
  l2_mode: window
  window_pre_seq: 10000
  window_post_seq: 5000000
  msnap_every: 1000
"""


def obs_fixture(run_id, rep, classification, chain_gaps=None):
    complete = not chain_gaps
    return {
        "schema_version": "ooo-observation/v1",
        "identity": {
            "run_id": run_id, "campaign_id": "fixture_campaign",
            "runid_row": "D01-F0-W6", "submodel": "c", "sample_index": rep,
            "phase": "engineering", "seed": 52000000 + rep,
            "manifest_sha256": "00" * 32,
            "gem5_sha256": "1a618953b014514713c0ad98c7f3d69a48171d81f0463d934bccdfcfc0070bf3",
            "config": {"path": "configs/se/ooo_proxy.py",
                       "sha256": "0b" * 32},
            "workload": {"path": "workloads/ooo/smoke/smoke",
                         "sha256": "30" * 32,
                         "golden_id": "smoke-golden-v1"},
            "golden_key": "abc123", "chaos_commit": "ffffffff11111111",
            "patchset_sha256": "ffffffff11111111", "pythonhashseed": 0,
            "host": "localhost", "started": "t", "finished": "t",
            "wall_s": 3.0,
        },
        "l0": {"injected": 1 if classification != "Inactive" else 0,
               "activated": 1 if classification != "Inactive" else 0,
               "events": [{"tick": 423115}], "skip_lines": 0,
               "eligible_count": None, "attempted": None},
        "l1": {"status": "inactive_no_activation"
               if classification == "Inactive" else "ok",
               "first_divergence": None},
        "l2": {"status": "inactive_no_activation"
               if classification == "Inactive"
               else ("not_observed_before_crash"
                     if classification == "Crash" else "ok"),
               "coverage": {"mode": "window", "seq_lo": 0, "seq_hi": 5},
               "first_divergent_commit":
                   ({"seq": 412, "class": "data_corruption",
                     "detail": "dest[0] val differs"}
                    if classification == "Crash" else None)},
        "l3": {"status": "inactive_no_activation"
               if classification == "Inactive" else "unsupported",
               "method": None, "reason": "no source-read association"},
        "l4": {"status": "ok",
               "first_detection": {"kind": "none", "detector": "None"}},
        "l5": {"classification": classification, "reason": "fixture",
               "exit": 0, "timed_out": False,
               "faults_injected": 0 if classification == "Inactive" else 1,
               "checksum_observed": "000000000000cf56",
               "checksum_golden": "000000000000cf56",
               "detector": {"Masked": "None", "Crash": "OS",
                            "Inactive": "n/a"}[classification],
               "conservation": {"ok": True}},
        "violations": [],
        "chain_complete": complete,
        "chain_gaps": chain_gaps or [],
        "files": {}, "coverage_scope": {},
        "audit": {"built_at": "t", "builder_sha256": "00" * 32},
    }


def main():
    with tempfile.TemporaryDirectory(prefix="handoff-test-") as td:
        cdir = os.path.join(td, "fixture_campaign")
        os.makedirs(os.path.join(cdir, "samples"), exist_ok=True)
        cy = os.path.join(td, "fixture_campaign.yaml")
        with open(cy, "w") as f:
            f.write(CAMPAIGN_YAML)

        rows = []
        for rep, cls, gaps in [
                (0, "Masked", ["L3"]), (1, "Crash", ["L3"]),
                (2, "Inactive", None)]:
            rid = f"fixture_campaign-c0000-r{rep:04d}"
            sdir = os.path.join(cdir, "samples", rid)
            os.makedirs(sdir)
            with open(os.path.join(sdir, "observation.json"), "w") as f:
                json.dump(obs_fixture(rid, rep, cls, gaps), f)
            rows.append({"manifest": f"{rid}.yaml", "run_id": rid, "rep": rep,
                         "seed": 52000000 + rep, "classification": cls,
                         "faults_injected": 0 if cls == "Inactive" else 1,
                         "exit": 0, "timed_out": False,
                         "chain_complete": gaps is None,
                         "chain_gaps": gaps or [],
                         "observation": f"samples/{rid}/observation.json",
                         "ts": f"2026-10-12T18:{rep:02d}:00"})
        with open(os.path.join(cdir, "results.jsonl"), "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

        # mini monitor log spanning the campaign window
        gdir = os.path.join(td, "guard")
        os.makedirs(os.path.join(gdir, "monitor"), exist_ok=True)
        with open(os.path.join(gdir, "monitor", "resources.log"), "w") as f:
            f.write("ts,mem_available_kib,swap_free_kib,pswpin_cum,"
                    "pswpout_cum,load1,load5,load15,procs_running,"
                    "procs_blocked,disk_free_bytes,gem5_count,gem5_rss_kib\n")
            f.write("2026-10-12T17:59:00,26000000,12000000,1,1,0,0,0,1,0,"
                    "1,0,0\n")  # outside window (before)
            f.write("2026-10-12T18:00:30,20000000,12000000,1,1,0,0,0,1,0,"
                    "1,2,2097152\n")
            f.write("2026-10-12T18:02:30,24000000,12000000,1,1,0,0,0,1,0,"
                    "1,3,3145728\n")

        h = ooo_handoff.build_campaign_handoff(cdir, cy, gdir)
        check("runid-fields", h["runid_row"] == "D01-F0-W6"
              and h["submodel"] == "c" and h["phase"] == "engineering")
        check("counts", h["counts"]["n_rows"] == 3
              and h["counts"]["n_valid"] == 3
              and h["counts"]["per_class"]["Masked"] == 1
              and h["counts"]["per_class"]["Crash"] == 1
              and h["counts"]["per_class"]["Inactive"] == 1)
        check("conservation", h["conservation"]["activated_total"] == 2
              and h["conservation"]["five_primary_total"] == 2
              and h["conservation"]["post_activation_simulator_failure_total"] == 0
              and h["conservation"]["ok"] is True,
              json.dumps(h["conservation"]))
        check("chain-histogram",
              h["chain"]["n_chain_complete"] == 1
              and h["chain"]["n_chain_incomplete"] == 2
              and h["chain"]["gap_histogram"] == {"L3": 2}
              and h["chain"]["l3_unsupported_only"] == 2,
              json.dumps(h["chain"]))
        check("first-divergence",
              h["first_divergence"]["l2_first_divergent_commit"]["run_id"]
              .endswith("r0001")
              and h["first_divergence"]["l2_first_divergent_commit"]["seq"]
              == 412)
        check("resource-peaks-windowed",
              h["resources"] != "n/a"
              and h["resources"]["min_mem_available_kib"] == 20000000
              and h["resources"]["max_gem5_rss_kib"] == 3145728
              and h["resources"]["max_gem5_processes"] == 3,
              json.dumps(h["resources"]))
        check("wall", h["wall_seconds"] == 120)
        check("status-complete", h["status"] == "COMPLETE")

        jp, mp = ooo_handoff.write_campaign_handoff(cdir, cy, gdir)
        check("files-written", os.path.exists(jp) and os.path.exists(mp))
        with open(jp) as f:
            again = json.load(f)
        check("handoff-json-parseable", again["campaign_id"]
              == "fixture_campaign")
        with open(mp) as f:
            md = f.read()
        check("md-mentions-gaps", "L3" in md and "quarantine" in md)

    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
