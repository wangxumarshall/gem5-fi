#!/usr/bin/env python3
"""Replay mechanism pilot.

Runs W7 ``replay_dependency`` with a real A01 F0 injection and
``--prop_replay_all`` so every LSQ replay is recorded, then correlates each
replay with the same dynamic instruction's LQ lifecycle to report its final
commit or squash. A replay hook in the source is not evidence; this script
only reports replays that actually occurred in the run.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import subprocess
import sys
import zlib
from pathlib import Path

PLATFORM = Path(__file__).resolve().parent
IMPL = PLATFORM.parent
sys.path.insert(0, str(PLATFORM))

from tools.prop_trace_to_v31 import convert  # noqa: E402
from trace_validator import validate  # noqa: E402
from trace_completeness import check_completeness  # noqa: E402

ROOT = Path(__file__).resolve().parents[5]
GEM5 = ROOT / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/lsu_proxy.py"
WORKLOAD = IMPL / "workloads/replay_dependency"
ORACLE = IMPL / "workloads/replay_dependency.golden"
SEED = 3135797961  # RW01 seed (deterministic replay_dependency stream)


def build_replay_command(gem5: Path, outdir: Path,
                         probability: float = 1.0) -> list[str]:
    """The exact gem5 argv for the replay pilot.

    The FW02 carrier is ordinal-gated, not probability-gated: CHAOSLSQFwd
    attaches the F6Fw02 mode even with ``probability == 0`` and its
    suppression decision never consults probability.  A matched no-fault
    control (``--probability 0.0``) must therefore omit the injector mount
    or it would still fire (the same rule as run_pilot's FW02/LQ04 controls);
    the replay tracer stays on so the control still records real replays.
    """
    cmd = [str(gem5), f"--outdir={outdir}", str(CONFIG),
           f"--cmd={WORKLOAD}", "--cpu", "O3", "--variant", "B0",
           "--probability", str(probability), "--chaos_propagation",
           "--prop_trace_file", "replay_prop.csv.gz", "--prop_replay_all"]
    if probability == 0.0:
        return cmd
    # FW02 is the fault carrier: one suppressed forwarding keeps the run
    # alive long enough to observe the real partial-forward replays.
    return cmd + ["--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
                  "--max_faults", "1", "--rng_seed", str(SEED),
                  "--lsqfwd_event_ordinal", "1"]


def _rows(path: Path):
    raw = path.read_bytes()
    text = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(raw).decode(
        "utf-8", "replace")
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        row = next(csv.reader([line]))
        if len(row) >= 10:
            yield row


def _detail(text: str) -> dict[str, str]:
    return dict(kv.split("=", 1) for kv in (text or "").split(";") if "=" in kv)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--gem5", type=Path, default=GEM5)
    ap.add_argument("--probability", type=float, default=1.0,
                    help="injection probability (0.0 = matched no-fault control)")
    ap.add_argument("--dry-run", action="store_true",
                    help="build the exact gem5 command, print it (and write "
                         "<outdir>/command.txt), then exit 0 without invoking "
                         "gem5")
    args = ap.parse_args(argv)
    out = args.outdir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    cmd = build_replay_command(args.gem5, out, args.probability)
    (out / "command.txt").write_text("\n".join(cmd) + "\n")
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          timeout=1800)
    (out / "stdout.log").write_text(proc.stdout)
    (out / "stderr.log").write_text(proc.stderr)
    run_status = "COMPLETED" if proc.returncode == 0 else "SIMULATOR_ERROR"

    golden = ORACLE.read_text().strip() if ORACLE.exists() else None
    m = re.search(r"checksum=0x([0-9a-fA-F]+)", proc.stdout)
    oracle_pass = bool(m and golden and m.group(1) == golden)
    terminal = ("MASKED" if oracle_pass else "SDC") if proc.returncode == 0 else "CRASH"

    csv_path = out / "replay_prop.csv.gz"
    jsonl_path = out / "trace_v31.jsonl"
    converted = {"rows": 0, "summary": None}
    if csv_path.exists():
        converted = convert(
            csv_path, jsonl_path, sample_run_id="PILOT-REPLAY-RW01",
            run_id="PILOT-REPLAY", sub_task_id="PILOT-REPLAY-S01",
            fault_id="FW02-CFG01", fault_model_id="FW02",
            run_status=run_status, activation="TRIGGERED", terminal=terminal,
            completeness="COMPLETE" if proc.returncode == 0 else "INCOMPLETE",
            allow_truncated_complete=(proc.returncode != 0))
    errors = validate(jsonl_path) if jsonl_path.exists() else ["trace missing"]
    completeness = (check_completeness(jsonl_path) if jsonl_path.exists()
                    else {"trace_completeness": "INCOMPLETE"})

    replays = []
    fault_applied = False
    if csv_path.exists():
        # Current replay generation per dynamic instruction, and the final LQ
        # free reason (commit/squash) for that same instruction.
        final_state: dict[int, tuple[int, str]] = {}
        raw_replays = []
        for row in _rows(csv_path):
            kind = row[3]
            d = _detail(row[9])
            seq = int(row[4] or 0)
            if kind == "fwd" and d.get("decision") == "suppressed":
                fault_applied = True
            if kind == "replay":
                raw_replays.append((seq, int(row[1] or 0), d))
            elif kind == "lq_lifecycle" and d.get("action") == "free":
                final_state[seq] = (int(row[1] or 0), d.get("reason", "unknown"))
        for seq, tick, d in raw_replays:
            gen = int(d.get("replay_generation", 0))
            attempt = int(d.get("execution_attempt_id", 0))
            post = final_state.get(seq)
            replays.append({
                "reason": d.get("reason"),
                "dyn_inst_seq": seq,
                "tick": tick,
                "pc": d.get("pc"),
                "execution_attempt_id": attempt,
                "replay_generation": gen,
                "pre_replay_generation": max(gen - 1, 0),
                "pre_state": "issued; not yet rescheduled",
                "post_state": (None if post is None else
                               {"tick": post[0], "reason": post[1]}),
                "final_result": ("SQUASHED" if post and "squash" in post[1]
                                 else "COMMITTED" if post and "commit" in post[1]
                                 else "UNRESOLVED"),
                "lq_entry_id": d.get("lq_entry_id"),
                "entry_generation": d.get("entry_generation"),
            })

    summary = {
        "pilot_id": "PILOT-REPLAY-RW01",
        "workload": str(WORKLOAD),
        "seed": SEED,
        "fault": "FW02-CFG01 (F6, one suppressed forwarding)",
        "note": ("replays are real partial_forward_mismatch reschedules of "
                 "replay_dependency; they are observed under a fault run and "
                 "are not claimed to be caused by the injected bit flip"),
        "run_status": run_status,
        "activation": "TRIGGERED" if fault_applied else "NOT_TRIGGERED",
        "terminal_state": terminal,
        "oracle_pass": oracle_pass,
        "trace_completeness": completeness.get("trace_completeness"),
        "record_integrity": completeness.get("record_integrity"),
        "trace_counts": {k: completeness.get(k) for k in
                         ("events", "edges", "injections", "activations")},
        "replay_count": len(replays),
        "replays": replays,
        "validator_errors": errors,
    }
    (out / "replay_pilot_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    ok = (len(replays) > 0 and errors == []
          and completeness.get("trace_completeness") == "COMPLETE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
