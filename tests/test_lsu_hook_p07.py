#!/usr/bin/env python3
"""test_lsu_hook_p07.py — [MDSPEC][R6-P-P07-b] prefetch fill tag/way mispair.

Contract:
  * fill-time pure-prefetch marker (same as P09) gates the model;
  * a distinct valid partner in the SAME set is required;
  * the two blocks' TAGS are exchanged while data stays in its own way
    (real tag/data mispair, not a classic cache-tag fault);
  * unit-side L1 `pf_tag` + real demand misses afterwards;
  * B0 census has eligible events (W6=2, W8=5); seed1 pilot only, and the
    output hashes stay at the golden values, so no SDC is claimed.

Usage: python3 tests/test_lsu_hook_p07.py   (exit 0 = all PASS/SKIP)
"""
import gzip
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402
import lsu_prop_fields as P  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def src(path):
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    print("[1] source contract")
    bcc = src("CHAOS/gem5/src/mem/cache/base.cc")
    thh = src("CHAOS/gem5/src/mem/cache/tags/tagged_entry.hh")
    bhh = src("CHAOS/gem5/src/mem/cache/tags/base.hh")
    pcc = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
              "CHAOSPrefetch.cc")
    check("fill 后仅纯预取 fill 触发 tag/way 错配",
          "chaosFillFromPrefetch && CHAOSPrefetch::fillWayHook" in bcc,
          "gate missing")
    check("同 set 找另一个 valid way（不硬编码几何）",
          "getNumWays" in bhh and "findBlockBySetAndWay" in bcc, "partner missing")
    check("交换两个 block 的 tag（data 留原 way）",
          "blk->chaosSetTag(chaos_partner->getTag());" in bcc
          and "chaos_partner->chaosSetTag(chaos_tag);" in bcc, "swap missing")
    check("TaggedEntry 暴露 chaosSetTag（P07 注入用）",
          "void chaosSetTag(Addr tag) { setTag(tag); }" in thh, "accessor missing")
    check("Mode P07FillTagMispair + p07_fill_tag_mispair 映射",
          "P07FillTagMispair" in src("CHAOS/gem5/src/mem/cache/prefetch/"
                                     "CHAOSPrefetch/CHAOSPrefetch.hh")
          and 'if (s == "p07_fill_tag_mispair")   return Mode::P07FillTagMispair;'
          in pcc, "mode missing")
    check("schema v1: pf_tag 单元侧 L1",
          P.KIND_LAYER.get("pf_tag") == "L1"
          and "fault_id" in P.REQUIRED_FIELDS.get("pf_tag", []), "schema")
    check("campaign P07 不再走 classic cache tag",
          LC.MODEL_FLAGS.get("P07") ==
          ("prefetch", ["--prefetch_mode", "p07_fill_tag_mispair"]),
          str(LC.MODEL_FLAGS.get("P07")))

    print("[2] B0 census: real eligible stream")
    cen = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
               "census_p07_20261104")
    for w, n in (("W6", 2), ("W8", 5)):
        f = cen / w / "run.out"
        if not f.is_file():
            print(f"  SKIP B0 {w}")
            continue
        t = f.read_text()
        check(f"B0 {w} attempted={n} eligible={n}",
              f"attempted={n} eligible={n}" in t, "trigger mismatch")

    print("[3] seed1 pilot evidence")
    base = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                "campaign_p07_20261104")
    for rid, fill, partner, golden, term in (
            ("P07-F0-W6", "7ec00", "8ec00", "062e5124df3667f9", "full"),
            ("P07-F0-W8", "76740", "86740", "629727c0ad9ca8ef",
             "provable_to_L1_then_unknown")):
        sd = base / rid / "seed1"
        if not (sd / "prop_evt.txt.gz").is_file():
            print(f"  SKIP {rid}")
            continue
        inj = (sd / "prefetch_injections.log").read_text()
        check(f"{rid} 注入行 P07_fill_tag_mispair + set/way",
              "P07_fill_tag_mispair" in inj and "tags swapped" in inj, inj)
        text = gzip.open(sd / "prop_evt.txt.gz", "rt").read()
        check(f"{rid} pf_tag 记录两条线 + tag_mispair",
              "kind=pf_tag" in text
              and f"before={fill} after={partner}" in text
              and "state_after=tag_mispair" in text, "pf_tag missing")
        dout = (sd / "run.out").read_text()
        m = re.search(r"^([0-9a-f]{16})$", dout, re.M)
        check(f"{rid} 输出哈希未变（不声称 SDC）",
              m is not None and m.group(1) == golden, m.group(1) if m else None)
        rep = subprocess.run(
            [sys.executable, str(ROOT / "tools/lsu_chain_check.py"),
             str(sd / "prop_evt.txt.gz"), "--run-id", rid],
            capture_output=True, text=True)
        try:
            j = json.loads(rep.stdout)
            f1 = j.get("faults", {}).get("1", {})
            check(f"{rid} 链终局={term}",
                  f1.get("terminal") == term, str(f1.get("terminal")))
        except Exception as exc:  # noqa: BLE001
            check(f"{rid} 链终局={term}", False, f"checker: {exc}")
        gz = subprocess.run(["gzip", "-t", str(sd / "prop_evt.txt.gz")],
                            capture_output=True).returncode == 0
        check(f"{rid} gzip EOF + stats 非空",
              gz and (sd / "stats.txt").stat().st_size > 0, "gzip/stats")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
