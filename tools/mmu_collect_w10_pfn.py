#!/usr/bin/env python3
"""Collect per-context W10 target PFNs from independent NO-FAULT controls.

Input: a directory containing single-context no-fault W10 controls named
`...W10...R0x` (each with Run_Log/golden_output.txt or board.terminal), or a
single golden file.  Output: `phase3/formal/w10_pfn_map.json`, consumed by
tools/mmu_formal_preflight.py and tools/mmu_formal_runner.py to resolve M02's
`--mmu_m02_old_pfn`.

The loader never invents a PFN: a missing context is simply absent, and the
M02 runner then refuses with `BLOCKED_MISSING_W10_PFN_MAPPING`.  Fault-enabled
runs and the legacy `--ctx all` control are rejected, because their guest
allocation history differs (measured 0x83480/0x7d vs 0x834b6/0x63).

Example (Main, after a real no-fault control run):
  MMU_CTX=R02 phase3/run_scripts/run_mmu_case.sh \
    runs/TEST-CTRL-W10-R02 TEST-CTRL-W10-R02 W10 NONE
  python3 tools/mmu_collect_w10_pfn.py
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmu_formal_preflight as pf


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--control-root", default=None,
                    help="directory with single-context W10 control runs "
                         "(default: <repo>/runs)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    root = os.path.abspath(args.repo_root)
    ctrl = args.control_root or os.path.join(root, "runs")
    out_path = args.out or os.path.join(
        root, "phase3", "formal", "w10_pfn_map.json")
    mapping = pf.load_w10_pfn_map(root, ctrl)
    payload = {
        "generated_from": ctrl,
        "note": ("Per-context target PFN from independent no-fault scoped "
                 "W10 controls.  The legacy --ctx all control is rejected."),
        "contexts": mapping["contexts"],
        "sources": mapping.get("sources", []),
        "rejected": mapping.get("rejected", []),
    }
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, default=str)
    print(json.dumps({
        "out": out_path,
        "contexts": sorted(mapping["contexts"]),
        "map": {c: "0x%x" % r["target_pfn"]
                for c, r in sorted(mapping["contexts"].items())},
        "sources": mapping.get("sources", []),
        "rejected": mapping.get("rejected", []),
        "detail": mapping.get("detail"),
    }, indent=2, sort_keys=True, default=str))
    return 0 if len(mapping["contexts"]) == 5 else 1


if __name__ == "__main__":
    sys.exit(main())
