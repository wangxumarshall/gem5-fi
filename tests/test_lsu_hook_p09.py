#!/usr/bin/env python3
"""test_lsu_hook_p09.py — [MDSPEC][R6-P-P09-a] prefetch-caused dirty
writeback loss.

Contract pinned here:
  * fill-time pure-prefetch classification from the MSHR target sources
    (FromPrefetcher and no FromCPU/FromSnoop) — demand-merged fills are
    NOT marked;
  * the marker lives only across handleFill (never a stale marker);
  * the real dirty-eviction gate suppresses the writeback packet for the
    victim, emitting a unit-side L1 `pf_wb` event and a `cache_evict`
    with state_after=writeback_suppressed;
  * B0 W6/W8 have prefetch fills but ZERO prefetch-caused evictions, so the
    authoritative P09-F0-W6/W8 RunIDs stay blocked by workload coverage;
  * a non-authoritative L2=16KiB diagnostic control proves the model
    end-to-end: suppressed writeback -> stale re-read -> taint -> real
    errant_commit (L5) and a different workload output hash.

Usage: python3 tests/test_lsu_hook_p09.py   (exit 0 = all PASS/SKIP)
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
    print("[1] fill-time pure-prefetch marker (MSHR target sources)")
    mhh = src("CHAOS/gem5/src/mem/cache/mshr.hh")
    bhh = src("CHAOS/gem5/src/mem/cache/base.hh")
    bcc = src("CHAOS/gem5/src/mem/cache/base.cc")
    check("MSHR::hasTargetFrom 检查 targets + deferredTargets",
          "bool hasTargetFrom(Target::Source src) const" in mhh
          and "for (const auto &t : targets)" in mhh
          and "for (const auto &t : deferredTargets)" in mhh, "missing")
    check("BaseCache 有单次 fill 生命期标记 chaosFillFromPrefetch",
          "bool chaosFillFromPrefetch = false;" in bhh, "missing")
    check("fill 点要求 FromPrefetcher 且无 FromCPU/FromSnoop",
          "mshr->hasTargetFrom(MSHR::Target::FromPrefetcher)" in bcc
          and "!mshr->hasTargetFrom(MSHR::Target::FromCPU)" in bcc
          and "!mshr->hasTargetFrom(MSHR::Target::FromSnoop)" in bcc,
          "predicate missing")
    check("标记在 handleFill 后立即清除（不跨 fill 存活）",
          "blk = handleFill(pkt, blk, writebacks, allocate);\n"
          "        chaosFillFromPrefetch = false;" in bcc, "lifetime wrong")

    print("[2] real eviction gate suppresses the writeback packet")
    ccc = src("CHAOS/gem5/src/mem/cache/cache.cc")
    check("evictBlock 仅在 chaosFillFromPrefetch 时询问 P09 钩子",
          "if (chaosFillFromPrefetch && CHAOSPrefetch::wbLossHook)" in ccc,
          "gate missing")
    check("钩子收到 victim 的 dirty 状态",
          "blk->isSet(CacheBlk::DirtyBit));" in ccc, "dirty arg missing")
    check("抑制时跳过 writebackBlk/cleanEvictBlk 并返回空包",
          "if (!chaos_suppress_wb) {" in ccc
          and "PacketPtr pkt = nullptr;" in ccc
          and "writebackBlk(blk) : cleanEvictBlk(blk);" in ccc, "packet not skipped")
    check("schema v1：pf_wb 为单元侧 L1 观察点",
          P.KIND_LAYER.get("pf_wb") == "L1"
          and "fault_id" in P.REQUIRED_FIELDS.get("pf_wb", [])
          and "pf_request_id" in P.REQUIRED_FIELDS.get("pf_wb", []),
          str(P.KIND_LAYER.get("pf_wb")))
    check("campaign P09 不再走 classic cache dirty",
          LC.MODEL_FLAGS.get("P09") ==
          ("prefetch", ["--prefetch_mode", "p09_wb_loss"]),
          str(LC.MODEL_FLAGS.get("P09")))

    print("[3] B0 census: prefetch fills exist, prefetch evictions = 0")
    b0 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
              "census_p09_20261104_v4")
    for w, fills, pure in (("W6", 3489, 50), ("W8", 17913, 28)):
        f = b0 / w / "run.out"
        if not f.is_file():
            print(f"  SKIP B0 {w} 证据不在（{f}）")
            continue
        t = f.read_text()
        m = re.search(r"CHAOS_P09_DIAG: fills=(\d+) pure_pref_fills=(\d+) "
                      r"pref_evictions=(\d+) dirty_pref_evictions=(\d+)", t)
        check(f"B0 {w} pure_pref_fills>0 且 pref_evictions=0",
              m is not None and int(m.group(2)) > 0
              and int(m.group(3)) == 0 and int(m.group(4)) == 0, t[-300:])
        check(f"B0 {w} 触发器 attempted=0 eligible=0（真实零资格）",
              "attempted=0 eligible=0" in t, "trigger mismatch")

    print("[4] diagnostic control (L2=16KiB, NOT a RunID): end-to-end loss")
    d = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
             "p09_diag_l2small_fault_20261104/P09-DIAG-W6-L2_16KiB/seed1")
    ctl = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
               "p09_diag_l2small_20261104b/16KiB")
    if not (d / "prop_evt.txt.gz").is_file():
        print(f"  SKIP diagnostic 证据不在（{d}）")
    else:
        inj = (d / "prefetch_injections.log").read_text()
        check("诊断注入行 P09_wb_loss + victim set/way",
              "P09_wb_loss" in inj and "dirty victim set=13 way=4" in inj,
              inj)
        text = gzip.open(d / "prop_evt.txt.gz", "rt").read()
        check("pf_wb: before=pending after=lost + writeback_suppressed",
              "kind=pf_wb" in text
              and "field=wb_request before=pending after=lost" in text
              and "state_after=writeback_suppressed" in text, "pf_wb missing")
        check("cache_evict 同线 dirty_evict_writeback + suppressed",
              "kind=cache_evict" in text
              and "field=dirty_evict_writeback" in text
              and "cache_line=7e740" in text, "evict missing")
        check("后续真实 demand 重读同线（cache_access/pf_demand）",
              "kind=cache_access" in text and "pa=7e740" in text
              and "kind=pf_demand" in text, "demand missing")
        check("真实 taint_reg + errant_commit L5",
              "kind=taint_reg" in text and "before=clean after=tainted" in text
              and "kind=errant_commit" in text
              and "detection_layer=L5" in text, "L4/L5 missing")
        # The original writeback must be absent at the eviction tick; a
        # later writeback of the STALE re-fill (tick 62665295) is allowed
        # and must be after the errant commit.
        wb_ticks = [int(x) for x in re.findall(
            r"kind=cache_writeback .*?tick=(\d+).*?pa=7e740", text)]
        check("原脏写回在驱逐时点不存在（后续 stale 写回仅在其后）",
              all(t > 53006800 for t in wb_ticks), str(wb_ticks))
        dout = (d / "run.out").read_text()
        m = re.search(r"^([0-9a-f]{16})$", dout, re.M)
        cout = (ctl / "run.out").read_text() \
            if (ctl / "run.out").is_file() else ""
        mc = re.search(r"^([0-9a-f]{16})$", cout, re.M)
        check("诊断故障输出哈希 != 无故障对照（真实 SDC）",
              m is not None and mc is not None and m.group(1) != mc.group(1),
              f"fault={m.group(1) if m else None} "
              f"ctl={mc.group(1) if mc else None}")
        check("无故障对照输出 = B0 golden 062e5124df3667f9",
              mc is not None and mc.group(1) == "062e5124df3667f9",
              mc.group(1) if mc else None)
        gz_ok = subprocess.run(["gzip", "-t", str(d / "prop_evt.txt.gz")],
                               capture_output=True).returncode == 0
        check("诊断证据 gzip EOF + stats 非空",
              gz_ok and (d / "stats.txt").stat().st_size > 0, "gzip/stats")
        rep = subprocess.run(
            [sys.executable, str(ROOT / "tools/lsu_chain_check.py"),
             str(d / "prop_evt.txt.gz"), "--run-id",
             "P09-DIAG-W6-L2_16KiB"],
            capture_output=True, text=True)
        try:
            j = json.loads(rep.stdout)
            f1 = j.get("faults", {}).get("1", {})
            check("链终局 full/L5（真实架构逃逸）",
                  f1.get("terminal") == "full"
                  and f1.get("provable_to") == "L5",
                  str(f1.get("terminal")) + "/" + str(f1.get("provable_to")))
        except Exception as exc:  # noqa: BLE001
            check("链终局 full/L5（真实架构逃逸）", False, f"checker: {exc}")
        check("pilot 未做 campaign oracle 分类（记 n/a，不冒充 Masked）",
              not (d / "cell_results.json").is_file(), "unexpected oracle file")

    print("[5] P09-c dirty premature clear (distinct faulted field)")
    phh2 = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
               "CHAOSPrefetch.hh")
    pcc2 = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
               "CHAOSPrefetch.cc")
    ccc2 = src("CHAOS/gem5/src/mem/cache/cache.cc")
    check("Mode P09DirtyClear + p09_dirty_clear 映射",
          "P09DirtyClear" in phh2
          and 'if (s == "p09_dirty_clear")        return '
          "Mode::P09DirtyClear;" in pcc2, "mode missing")
    check("VictimAction 区分 DropWriteback 与 ClearDirty",
          "enum class VictimAction { None, DropWriteback, ClearDirty };"
          in phh2
          and "maybeHandlePrefetchVictim" in phh2, "action enum missing")
    check("evictBlock 在驱逐决策前真实清除 DirtyBit（非仅日志）",
          "blk->clearCoherenceBits(CacheBlk::DirtyBit);" in ccc2
          and "chaos_premature_clear = true;" in ccc2
          and "chaos_action == CHAOSPrefetch::VictimAction::ClearDirty"
          in ccc2, "dirty-clear missing")
    check("clear 后包类型为 cleanEvict（不生成写回请求）",
          "blk->isSet(CacheBlk::DirtyBit) || writebackClean" in ccc2
          and "writebackBlk(blk) : cleanEvictBlk(blk);" in ccc2,
          "packet decision missing")
    check("单元侧 L1 pf_dirty(dirty->clean) + 注入行 P09_dirty_clear",
          'h5->notePropEvt("pf_dirty"' in pcc2
          and '{"field", "dirty_state"}' in pcc2
          and '{"before", "dirty"}' in pcc2
          and '{"after", "clean"}' in pcc2
          and 'logInjection(dirty_clear ? "P09_dirty_clear"' in pcc2,
          "event/log missing")
    check("choices 含 p09_dirty_clear",
          "p09_dirty_clear" in src("configs/se/lsu_proxy.py"), "missing")
    d2 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
              "p09c_diag_l2small_fault_20261105/"
              "P09C-DIAG-W6-L2_16KiB/seed1")
    ctl2 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                "p09c_diag_l2small_nofault_20261105/16KiB")
    if not (d2 / "prop_evt.txt.gz").is_file():
        print(f"  SKIP P09-c diagnostic 证据不在（{d2}）")
    else:
        inj = (d2 / "prefetch_injections.log").read_text()
        check("P09-c 注入行 = P09_dirty_clear + victim set/way",
              "P09_dirty_clear" in inj
              and "dirty state cleared before eviction" in inj, inj)
        text = gzip.open(d2 / "prop_evt.txt.gz", "rt").read()
        check("pf_dirty: dirty->clean + dirty_premature_clear",
              "kind=pf_dirty" in text
              and "field=dirty_state before=dirty after=clean" in text
              and "state_after=dirty_premature_clear" in text,
              "pf_dirty missing")
        check("cache_evict 为 clean_evict（非 writeback 路径）",
              "kind=cache_evict" in text
              and "field=clean_evict" in text, "evict mismatch")
        check("同线 demand 重读 + taint + errant_commit L5",
              "kind=cache_access" in text and "kind=pf_demand" in text
              and "kind=taint_reg" in text
              and "kind=errant_commit" in text
              and "detection_layer=L5" in text, "L4/L5 missing")
        cout = (ctl2 / "run.out").read_text() \
            if (ctl2 / "run.out").is_file() else ""
        mc2 = re.search(r"^([0-9a-f]{16})$", cout, re.M)
        m2 = re.search(r"^([0-9a-f]{16})$",
                       (d2 / "run.out").read_text(), re.M)
        check("无故障对照 = B0 golden 062e5124df3667f9",
              mc2 is not None and mc2.group(1) == "062e5124df3667f9",
              mc2.group(1) if mc2 else None)
        check("故障输出哈希 != 对照（真实 SDC）",
              m2 is not None and mc2 is not None
              and m2.group(1) != mc2.group(1),
              f"fault={m2.group(1) if m2 else None} "
              f"ctl={mc2.group(1) if mc2 else None}")
        rep2 = subprocess.run(
            [sys.executable, str(ROOT / "tools/lsu_chain_check.py"),
             str(d2 / "prop_evt.txt.gz"), "--run-id",
             "P09C-DIAG-W6-L2_16KiB"],
            capture_output=True, text=True)
        try:
            j2 = json.loads(rep2.stdout)
            f1 = j2.get("faults", {}).get("1", {})
            check("链终局 full/L5（真实架构逃逸）",
                  f1.get("terminal") == "full"
                  and f1.get("provable_to") == "L5",
                  str(f1.get("terminal")) + "/" + str(f1.get("provable_to")))
        except Exception as exc:  # noqa: BLE001
            check("链终局 full/L5（真实架构逃逸）", False, f"checker: {exc}")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
