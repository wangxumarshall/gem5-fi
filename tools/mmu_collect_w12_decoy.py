#!/usr/bin/env python3
"""Collect per-context decoy PFNs from real scoped W12 control runs.

Inputs: a directory containing `TEST-CTRL-W12-R0x` run directories (each with
Run_Log/golden_output.txt or board.terminal).  Output: the JSON map consumed by
tools/mmu_formal_preflight.py / mmu_formal_runner.py.

This never invents a PFN: a missing context is simply absent, and the M04
runner refuses (`BLOCKED_MISSING_DECOY_MAPPING`).
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
                    help="directory with TEST-CTRL-W12-R0x runs "
                         "(default: <repo>/runs)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    root = os.path.abspath(args.repo_root)
    ctrl = args.control_root or os.path.join(root, "runs")
    out_path = args.out or os.path.join(
        root, "phase3", "formal", "w12_decoy_map.json")
    mapping = pf.load_w12_decoy_map(root, ctrl)
    payload = {
        "generated_from": ctrl,
        "contexts": mapping["contexts"],
        "sources": mapping.get("sources", []),
    }
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, default=str)
    print(json.dumps({
        "out": out_path,
        "contexts": sorted(mapping["contexts"]),
        "map": {c: {"target_pfn": "0x%x" % r["target_pfn"],
                    "decoy_pfn": "0x%x" % r["decoy_pfn"]}
                for c, r in sorted(mapping["contexts"].items())},
    }, indent=2))
    return 0 if len(mapping["contexts"]) == 5 else 1


if __name__ == "__main__":
    sys.exit(main())
