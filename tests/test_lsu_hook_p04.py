#!/usr/bin/env python3
"""test_lsu_hook_p04.py — [MDSPEC][R6-P-P04] P04-a queue-valid contract.

P04-a is the first FAITHFUL P04 submodel (the old P04->P05 drop/dup routing is
removed).  Contract pinned here:
  * a shadow `chaosQueueValid` bit on Queued::DeferredPacket (default true);
  * Queued::getPacket skips invalid entries at issue (the real queue effect,
    not a drop from the list);
  * CHAOSPrefetch mode `p04_queue_valid` clears one live entry and emits the
    L0 inj + L1 pf_train + L2 pf_queue(queue_valid 1->0) events;
  * campaign routes P04 to `p04_queue_valid` and uses the measured span 2;
  * the pilot evidence (if present) is performance-only: L0->L2, no L3/L5.

Usage: python3 tests/test_lsu_hook_p04.py   (exit 0 = all PASS/SKIP)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

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
    print("[1] queue shadow-valid state + issue-path skip")
    qhh = src("CHAOS/gem5/src/mem/cache/prefetch/queued.hh")
    qcc = src("CHAOS/gem5/src/mem/cache/prefetch/queued.cc")
    check("DeferredPacket 有 shadow chaosQueueValid（默认 true）",
          "bool chaosQueueValid = true;" in qhh, "missing")
    check("Queued 暴露 chaosClearQueueValid / chaosHasLiveQueueEntry",
          "long chaosClearQueueValid(Addr &addr, Addr &pc);" in qhh
          and "bool chaosHasLiveQueueEntry() const" in qhh, "missing API")
    check("getPacket 在发行前跳过/移除 invalid 队列项",
          "!pfq.front().chaosQueueValid" in qcc
          and "invalid_skipped" in qcc, "issue skip missing")
    check("chaosClearQueueValid 只在存在 live entry 时清除并返回 index",
          "Queued::chaosClearQueueValid" in qcc
          and "return -1;" in qcc and "d.chaosQueueValid = false;" in qcc,
          "clear impl missing")

    print("[2] injector mode + hook plumbing")
    phh = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
              "CHAOSPrefetch.hh")
    pcc = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
              "CHAOSPrefetch.cc")
    scc = src("CHAOS/gem5/src/mem/cache/prefetch/stride.cc")
    check("Mode 枚举含 P04QueueValid", "P04QueueValid" in phh, "missing")
    check("stringToMode 映射 p04_queue_valid",
          'if (s == "p04_queue_valid")        return Mode::P04QueueValid;'
          in pcc, "missing")
    check("maybeCorrupt 收 Queued* 且 stride.cc 传 this",
          "prefetch::Queued *queue" in phh
          and "maybeCorrupt(entry, addresses, pf_addr, this)" in scc,
          "hook plumbing missing")
    check("P04 分支用 chaosHasLiveQueueEntry 先判资格再清除",
          "chaosHasLiveQueueEntry()" in pcc
          and "chaosClearQueueValid(qaddr, qpc)" in pcc, "branch missing")
    check("L0 inj + L1 pf_train + L2 pf_queue(queue_valid 1->0)",
          'logInjection("P04_queue_valid"' in pcc
          and '{"field", "queue_valid"}' in pcc
          and '{"before", "1"}' in pcc and '{"after", "0"}' in pcc,
          "events missing")
    check("旧 P04->P05 drop/dup 路由已删除",
          LC.MODEL_FLAGS.get("P04") ==
          ("prefetch", ["--prefetch_mode", "p04_queue_valid"]),
          str(LC.MODEL_FLAGS.get("P04")))
    check("P04 F0 span 为精确绝对命令实测值 2/2",
          LC.PF_F0_SPAN.get(("P04", "beebs_kernels")) == 2
          and LC.PF_F0_SPAN.get(("P04", "prefetch_stride")) == 2,
          str(LC.PF_F0_SPAN))

    print("[3] seed1 pilot evidence (if present)")
    base = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                "campaign_p04_20261104")
    for rid, wl in (("P04-F0-W2", "beebs_kernels"),
                    ("P04-F0-W8", "prefetch_stride")):
        sd = base / rid / "seed1"
        if not (sd / "chain_report.json").is_file():
            print(f"  SKIP {rid} 证据不在（{sd}）——源契约已覆盖")
            continue
        rep = json.load(open(sd / "chain_report.json"))
        f = rep["faults"]["1"]
        check(f"{rid} terminal=provable_to_L2_then_unknown（性能型，无 L3/L5）",
              rep.get("terminal") == "provable_to_L2_then_unknown"
              and f.get("provable_to") == "L2", str(rep.get("terminal")))
        check(f"{rid} 未准入（模型无架构数据效应，不伪造 L5）",
              rep.get("admitted") is False, str(rep.get("admitted")))
        inj = (sd / "prefetch_injections.log").read_text().strip()
        check(f"{rid} 注入行 = P04_queue_valid", "P04_queue_valid" in inj,
              inj)
        import gzip
        text = gzip.open(sd / "prop_evt.txt.gz", "rt").read()
        check(f"{rid} 真实 queue_valid 1->0 + invalid_skipped 事件",
              "field=queue_valid before=1 after=0" in text
              and "state_after=invalid_skipped" in text,
              "events missing")

    print("[4] P04-c entry-selection (queue_select) contract + pilot")
    qhh2 = src("CHAOS/gem5/src/mem/cache/prefetch/queued.hh")
    qcc2 = src("CHAOS/gem5/src/mem/cache/prefetch/queued.cc")
    pcc2 = src("CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/"
               "CHAOSPrefetch.cc")
    check("Queued 暴露 chaosSelectWrongEntry / chaosHasTwoLiveEntries",
          "long chaosSelectWrongEntry(Addr &addr, Addr &pc);" in qhh2
          and "bool chaosHasTwoLiveEntries() const" in qhh2, "missing API")
    check("选择故障交换 head 与第二 live entry（非 drop/dup）",
          "std::iter_swap(first, second);" in qcc2
          and "second = it;" in qcc2, "swap missing")
    check("Mode P04QueueSelect + p04_queue_select 映射",
          "P04QueueSelect" in src("CHAOS/gem5/src/mem/cache/prefetch/"
                                  "CHAOSPrefetch/CHAOSPrefetch.hh")
          and 'if (s == "p04_queue_select")       return Mode::P04QueueSelect;'
          in pcc2, "mode missing")
    check("P04-c 分支用 chaosHasTwoLiveEntries + chaosSelectWrongEntry",
          "chaosHasTwoLiveEntries()" in pcc2
          and "chaosSelectWrongEntry(qaddr, qpc)" in pcc2, "branch missing")
    check("事件 field=queue_select / state_after=wrong_selected",
          '{"field", "queue_select"}' in pcc2
          and "wrong_selected" in pcc2, "events missing")
    check("choices 含 p04_queue_select",
          "p04_queue_select" in src("configs/se/lsu_proxy.py"), "missing")
    base2 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                 "campaign_p04c_20261104")
    for rid in ("P04C-F0-W2", "P04C-F0-W8"):
        sd = base2 / rid / "seed1"
        if not (sd / "chain_report.json").is_file():
            print(f"  SKIP {rid} 证据不在（{sd}）——源契约已覆盖")
            continue
        rep = json.load(open(sd / "chain_report.json"))
        f = rep["faults"]["1"]
        check(f"{rid} terminal=provable_to_L2_then_unknown（无 L3/L5 观测）",
              f.get("terminal") == "provable_to_L2_then_unknown"
              and f.get("provable_to") == "L2", str(f.get("terminal")))
        inj = (sd / "prefetch_injections.log").read_text().strip()
        check(f"{rid} 注入行 = P04_queue_select", "P04_queue_select" in inj,
              inj)
        import gzip
        text = gzip.open(sd / "prop_evt.txt.gz", "rt").read()
        check(f"{rid} 真实 queue_select head->wrong + wrong_selected 事件",
              "field=queue_select before=head after=wrong" in text
              and "state_after=wrong_selected" in text, "events missing")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
