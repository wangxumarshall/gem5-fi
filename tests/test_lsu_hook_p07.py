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

    print("[4] P07-a data written to wrong way (distinct composition rule)")
    phh = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
              "CHAOSPrefetch.hh")
    check("Mode P07DataWay + p07_data_way 映射",
          "P07DataWay" in phh
          and 'if (s == "p07_data_way")           return Mode::P07DataWay;'
          in pcc, "mode missing")
    check("FillMispair 区分 Tags/Data（一次 attempt，不双计）",
          "enum class FillMispair { None, Tags, Data };" in phh
          and "maybeMispairFill" in phh, "action enum missing")
    check("base.cc 真实交换两个 way 的 data 数组（tag 不动）",
          "chaos_partner->data[ci] = chaos_tmp;" in bcc
          and "FillMispair::Data" in bcc, "data swap missing")
    check("schema v1: pf_data 单元侧 L1",
          P.KIND_LAYER.get("pf_data") == "L1"
          and "fault_id" in P.REQUIRED_FIELDS.get("pf_data", []), "schema")
    check("choices 含 p07_data_way",
          "p07_data_way" in src("configs/se/lsu_proxy.py"), "missing")
    base2 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                 "campaign_p07a_20261105")
    for rid in ("P07A-F0-W6", "P07A-F0-W8"):
        sd = base2 / rid / "seed1"
        if not (sd / "prop_evt.txt.gz").is_file():
            print(f"  SKIP {rid} 证据不在（{sd}）")
            continue
        inj = (sd / "prefetch_injections.log").read_text()
        check(f"{rid} 注入行 P07_data_wrong_way + set/way",
              "P07_data_wrong_way" in inj
              and "data arrays swapped; tags stay in their way" in inj, inj)
        text = gzip.open(sd / "prop_evt.txt.gz", "rt").read()
        check(f"{rid} pf_data 记录 fill/partner way + data_wrong_way",
              "kind=pf_data" in text
              and "field=fill_data_way" in text
              and "state_after=data_wrong_way" in text, "pf_data missing")
        dout = (sd / "run.out").read_text()
        m = re.search(r"^([0-9a-f]{16})$", dout, re.M)
        check(f"{rid} 输出哈希 = 无故障 golden（不声称 SDC）",
              m is not None and m.group(1) in
              ("062e5124df3667f9", "629727c0ad9ca8ef"),
              m.group(1) if m else None)
        rep = subprocess.run(
            [sys.executable, str(ROOT / "tools/lsu_chain_check.py"),
             str(sd / "prop_evt.txt.gz"), "--run-id", rid],
            capture_output=True, text=True)
        try:
            j = json.loads(rep.stdout)
            f1 = j.get("faults", {}).get("1", {})
            check(f"{rid} 链终局按真实链（L1/L2/full 均可，不伪造）",
                  f1.get("terminal") in
                  ("provable_to_L1_then_unknown",
                   "provable_to_L2_then_unknown",
                   "provable_to_L3_then_unknown",
                   "provable_to_L4_then_unknown",
                   "full", "detected_contained"),
                  str(f1.get("terminal")))
        except Exception as exc:  # noqa: BLE001
            check(f"{rid} 链终局按真实链", False, f"checker: {exc}")

    print("[5] P07-c old tag/valid reuse (victim captured before eviction)")
    pcc3 = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
               "CHAOSPrefetch.cc")
    check("Mode P07StaleTag + p07_stale_tag 映射",
          "P07StaleTag" in src("CHAOS/gem5/src/mem/cache/prefetch/"
                               "CHAOSPrefetch/CHAOSPrefetch.hh")
          and 'if (s == "p07_stale_tag")          return Mode::P07StaleTag;'
          in pcc3, "mode missing")
    check("allocateBlock 在 handleEvictions 之前捕获 victim 旧状态",
          "noteVictimForFill(" in bcc
          and (lambda a: a.index("noteVictimForFill(") <
               a.index("handleEvictions(evict_blks, writebacks)"))(
                   bcc[bcc.index("BaseCache::allocateBlock"):]),
          "capture must precede eviction")
    check("handleFill 消费并按 (set,way) 校验，且同 fill 清除捕获",
          "maybeStaleTagFill(" in bcc
          and "clearVictimCapture();" in bcc
          and "blk->chaosSetTag(chaos_stale_tag);" in bcc, "consume/clear missing")
    check("捕获是一次性槽：消费即清空，不跨请求",
          "const VictimCapture cap = pending_victim;" in pcc3
          and "pending_victim = VictimCapture{};" in pcc3
          and "cap.set != set || cap.way != way" in pcc3, "capture lifetime")
    check("仅回填 VALID victim（旧 tag/valid 才有意义）",
          "!cap.victim_valid" in pcc3 and "cap.tag == new_tag" in pcc3,
          "eligibility missing")
    check("schema v1: pf_stale_tag 单元侧 L1",
          P.KIND_LAYER.get("pf_stale_tag") == "L1"
          and "fault_id" in P.REQUIRED_FIELDS.get("pf_stale_tag", []),
          "schema")
    check("choices 含 p07_stale_tag",
          "p07_stale_tag" in src("configs/se/lsu_proxy.py"), "missing")

    cen0 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                "census_p07c_20261105")
    for w in ("W6", "W8"):
        f = cen0 / w / "run.out"
        if not f.is_file():
            print(f"  SKIP B0 census {w}")
            continue
        t = f.read_text()
        m = re.search(r"CHAOS_P07C_DIAG: queries=(\d+) captured=(\d+) "
                      r"setway_ok=(\d+) victim_valid=(\d+) tag_diff=(\d+)", t)
        check(f"B0 {w}: 捕获生效但所有 fill 落在 invalid way（coverage block）",
              m is not None and int(m.group(1)) > 0
              and int(m.group(1)) == int(m.group(3))
              and int(m.group(4)) == 0
              and "attempted=0 eligible=0" in t,
              t[-260:])

    d2 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
              "p07c_diag_l2small_fault_20261105/"
              "P07C-DIAG-W6-L2_16KiB/seed1")
    ctl2 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                "p07c_diag_l2small_20261105/16KiB")
    if not (d2 / "prop_evt.txt.gz").is_file():
        print(f"  SKIP P07-c diagnostic 证据不在（{d2}）")
    else:
        inj = (d2 / "prefetch_injections.log").read_text()
        check("诊断注入行 P07_stale_tag 且复用 victim tag",
              "P07_stale_tag" in inj and "keeps victim tag 0x" in inj, inj)
        text = gzip.open(d2 / "prop_evt.txt.gz", "rt").read()
        m = re.search(r"kind=pf_stale_tag[^\n]*?va=([0-9a-f]+)[^\n]*?"
                      r"before=([0-9a-f]+) after=([0-9a-f]+)[^\n]*?"
                      r"state_after=stale_tag_reused", text)
        check("pf_stale_tag: 新 line 与复用的 victim line 不同",
              m is not None and m.group(2) != m.group(3),
              "event missing" if m is None else str(m.groups()))
        check("单次故障（一个 pf_stale_tag 实例）",
              text.count("kind=pf_stale_tag") == 1,
              str(text.count("kind=pf_stale_tag")))
        check("真实 L5：errant_commit + 链终局 full/L5",
              "kind=errant_commit" in text
              and "detection_layer=L5" in text, "L5 missing")
        rep = subprocess.run(
            [sys.executable, str(ROOT / "tools/lsu_chain_check.py"),
             str(d2 / "prop_evt.txt.gz"), "--run-id",
             "P07C-DIAG-W6-L2_16KiB"], capture_output=True, text=True)
        try:
            j = json.loads(rep.stdout)
            f1 = j.get("faults", {}).get("1", {})
            check("链终局 full/L5（真实架构逃逸）",
                  f1.get("terminal") == "full"
                  and f1.get("provable_to") == "L5",
                  str(f1.get("terminal")))
        except Exception as exc:  # noqa: BLE001
            check("链终局 full/L5（真实架构逃逸）", False, f"checker: {exc}")
        mc = re.search(r"^([0-9a-f]{16})$",
                       (ctl2 / "run.out").read_text(), re.M) \
            if (ctl2 / "run.out").is_file() else None
        mh = re.search(r"^([0-9a-f]{16})$",
                       (d2 / "run.out").read_text(), re.M)
        check("无故障对照 = golden 062e5124df3667f9",
              mc is not None and mc.group(1) == "062e5124df3667f9",
              mc.group(1) if mc else None)
        check("故障输出哈希 != 对照（真实 SDC）",
              mh is not None and mc is not None
              and mh.group(1) != mc.group(1),
              f"fault={mh.group(1) if mh else None} "
              f"ctl={mc.group(1) if mc else None}")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
