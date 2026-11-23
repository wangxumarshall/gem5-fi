#!/usr/bin/env python3
"""Build per-family marker-site -> PC catalogs from the control runs.

The control census is fault-free, so a marker's recorded value can validate
the mapped dynamic instruction.  Only validated site/PC pairs enter the
catalog.  Fault mapping then uses the PC identity (not the possibly corrupted
value) to find the operation.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L


def main():
    catalogs = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for p in sorted((L.EXT / "results/controls").glob(
            "E2E-*-*-CTRL/attempt_1/sw_events.json")):
        d = json.loads(p.read_text())
        fam = L.FAMILY[d["model"]]
        for e in d["events"]:
            if not e.get("op_ok") or not e.get("op_pc") or not e.get("op_seq"):
                continue
            k = f"{e['type']}:{e['site']}"
            pc = e["op_pc"]
            ent = catalogs[fam][k].setdefault(
                str(pc), {"pc": pc, "op": e.get("op_name"),
                          "count": 0, "sites": []})
            ent["count"] += 1
            if e["site"] not in ent["sites"]:
                ent["sites"].append(e["site"])
    out = {}
    for fam, sites in catalogs.items():
        out[fam] = {k: list(v.values()) for k, v in sites.items()}
        n_pc = sum(len(v) for v in out[fam].values())
        print(f"{fam}: {len(out[fam])} marker sites, {n_pc} validated PCs")
    p = L.EXT / "runner/e2e_site_catalog.json"
    p.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("wrote", p)


if __name__ == "__main__":
    main()
