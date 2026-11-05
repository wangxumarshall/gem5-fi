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
          "long chaosSelectWrongEntry(Addr &addr, Addr &pc, "
          "Addr &displaced_addr);" in qhh2
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
          and "chaosSelectWrongEntry(" in pcc2
          and "qaddr, qpc, displaced_addr" in pcc2, "branch missing")
    check("事件 field=queue_select / state_after=wrong_selected",
          '{"field", "queue_select"}' in pcc2
          and "wrong_selected" in pcc2, "events missing")
    check("choices 含 p04_queue_select",
          "p04_queue_select" in src("configs/se/lsu_proxy.py"), "missing")
    import gzip
    import re
    base2 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                 "campaign_p04c_behavior_20261104")
    for rid in ("P04C-F0-W2", "P04C-F0-W8"):
        sd = base2 / rid / "seed1"
        if not (sd / "chain_report.json").is_file() and not (
                sd / "p04c_queue_behavior.log").is_file():
            print(f"  SKIP {rid} 证据不在（{sd}）——源契约已覆盖")
            continue
        inj = (sd / "prefetch_injections.log").read_text().strip()
        check(f"{rid} 注入行 = P04_queue_select", "P04_queue_select" in inj,
              inj)
        beh = (sd / "p04c_queue_behavior.log").read_text()
        m = re.search(r"event=select head=(0x[0-9a-f]+) second=(0x[0-9a-f]+)",
                      beh)
        check(f"{rid} 选择事件记录 head/second 两个不同合法条目",
              m is not None and m.group(1) != m.group(2), beh)
        if m:
            head, second = m.group(1), m.group(2)
            issues = re.findall(
                r"Tick: (\d+) event=issue role=(\w+) va=(0x[0-9a-f]+)", beh)
            check(f"{rid} 错误项先于正确 head 真实发行（顺序反转）",
                  len(issues) == 2
                  and issues[0][1] == "wrong_selected"
                  and issues[0][2] == second
                  and issues[1][1] == "head_issued_late"
                  and issues[1][2] == head
                  and int(issues[0][0]) < int(issues[1][0]), beh)
            check(f"{rid} 两条 live entry 各发行一次（无 drop/dup）",
                  len([i for i in issues if i[1] == "wrong_selected"]) == 1
                  and len([i for i in issues
                           if i[1] == "head_issued_late"]) == 1, beh)
        text = gzip.open(sd / "prop_evt.txt.gz", "rt").read()
        check(f"{rid} 传播事件 queue_select before=<head> after=<second>",
              "field=queue_select" in text
              and "state_after=wrong_selected" in text
              and "state_after=issued" in text, "events missing")

    print("[5] P04-b tail-pointer -1 submodel + behavior")
    check("Mode P04QueuePointer + p04_queue_pointer 映射",
          "P04QueuePointer" in src("CHAOS/gem5/src/mem/cache/prefetch/"
                                   "CHAOSPrefetch/CHAOSPrefetch.hh")
          and 'if (s == "p04_queue_pointer")      return Mode::P04QueuePointer;'
          in pcc2, "mode missing")
    check("Queued 暴露 arm/tail/size 且 addToQueue 插入 tail-1",
          "chaosArmTailPointerBack" in qhh2
          and "chaosTailAddr" in qhh2 and "chaosQueueSize" in qhh2
          and "&queue == &pfq && chaosTailBack" in qcc2
          and "--pos;" in qcc2 and "queue.insert(pos, dpp)" in qcc2,
          "tail-pointer impl missing")
    check("choices 含 p04_queue_pointer",
          "p04_queue_pointer" in src("configs/se/lsu_proxy.py"), "missing")
    base3 = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                 "campaign_p04b_20261104")
    for rid, w in (("P04B-F0-W2", "W2"), ("P04B-F0-W8", "W8")):
        sd = base3 / rid / "seed1"
        if not (sd / "p04b_queue_behavior.log").is_file():
            print(f"  SKIP {rid} 证据不在（{sd}）")
            continue
        inj = (sd / "prefetch_injections.log").read_text().strip()
        check(f"{rid} 注入行 = P04_queue_pointer", "P04_queue_pointer" in inj,
              inj)
        beh = (sd / "p04b_queue_behavior.log").read_text()
        m = re.search(r"event=arm tail=(0x[0-9a-f]+) insert=(0x[0-9a-f]+) "
                      r"size=(\d+)", beh)
        check(f"{rid} arm 记录 tail/insert 不同且 size>=2",
              m is not None and m.group(1) != m.group(2)
              and int(m.group(3)) >= 2, beh)
        if m:
            tail, ins = m.group(1), m.group(2)
            issues = re.findall(
                r"Tick: (\d+) event=issue role=(\w+) va=(0x[0-9a-f]+)", beh)
            check(f"{rid} 新条目先于原 tail 真实发行（顺序反转）",
                  len(issues) == 2
                  and issues[0][1] == "pointer_inserted"
                  and issues[0][2] == ins
                  and issues[1][1] == "pointer_tail_shifted"
                  and issues[1][2] == tail
                  and int(issues[0][0]) < int(issues[1][0]), beh)
            check(f"{rid} 插入项与原 tail 各发行一次（无 drop/dup）",
                  len([i for i in issues if i[1] == "pointer_inserted"]) == 1
                  and len([i for i in issues
                           if i[1] == "pointer_tail_shifted"]) == 1, beh)
        ctl = base3 / f"control_{w}_nofault" / "hwprefetch.log"
        if ctl.is_file() and m:
            order = re.findall(
                r"Generating prefetch for (0x[0-9a-f]+)", ctl.read_text())
            order = [a for a in order if a in (m.group(1), m.group(2))]
            check(f"{rid} 无故障对照为 tail 先、新条目后",
                  order[:2] == [m.group(1), m.group(2)], str(order[:4]))
        text = gzip.open(sd / "prop_evt.txt.gz", "rt").read()
        check(f"{rid} 传播事件 queue_pointer tail_minus_one",
              "field=queue_pointer" in text
              and "state_after=tail_minus_one" in text, "events missing")

    print("[6] P04-a F5 permanent queue-valid stuck (run-long)")
    # F5 is the permanent tier ("warm-up 后第一个 eligible event 起持续到
    # 运行结束").  Source contract: ONE latched physical fault identity, the
    # valid field stuck at invalid for every entry born after the latch, and
    # a real (not log-only) issue-path consequence.
    check("Queued 暴露 fixed-slot latch / stuck-active / slot",
          "size_t chaosLatchQueueValidStuck(" in qhh2
          and "uint64_t pfid," in qhh2
          and "std::vector<std::pair<Addr, Addr>> &invalidated);" in qhh2
          and "bool chaosQueueValidStuckActive() const" in qhh2
          and "uint64_t chaosStuckSlot() const" in qhh2,
          "missing F5 fixed-slot API")
    check("每个 ready-queue entry 获得物理 slot 身份",
          "uint64_t chaosSlot = 0;" in qhh2
          and "dpp.chaosSlot = chaosEnqueueSeq++ % queueSize;" in qcc2,
          "slot identity missing")
    check("latch 只失效所选 slot（不是整个队列）",
          "chaosStuckSlotIdx = chosen->chaosSlot;" in qcc2
          and "d.chaosSlot == chaosStuckSlotIdx" in qcc2
          and "dpp.chaosSlot != chaosStuckSlotIdx" in qcc2
          and qcc2.count("chaosQueueValidStuck = false") == 1
          and "if (chosen == pfq.end()) {" in qcc2,
          "global-field expansion / recovery path present")
    check("addToQueue 对同 slot 的新 entry 施加 stuck valid",
          "chaosApplyStuckValid(queue.back())" in qcc2
          and "chaosApplyStuckValid(*ins)" in qcc2
          and "invalid_stuck_birth" in qcc2, "birth hook missing")
    check("F5 用 peek 不预清（避免两位同时失效）",
          "chaosPeekLiveQueueEntry(qaddr, qpc)" in pcc2
          and "if (trigger.tier == ChaOSLsuTier::F5) {" in pcc2
          and "qidx_long = queue->chaosClearQueueValid(qaddr, qpc);" in pcc2,
          "F5 pre-clear still present")
    check("F5 分支 latch 一次 + 后续 fire 报 no_effect",
          "chaosQueueValidStuckActive()" in pcc2
          and "trigger.noteOutcome(false);" in pcc2
          and "chaosLatchQueueValidStuck(" in pcc2
          and 'logInjection("P04_queue_valid_stuck"' in pcc2,
          "F5 branch missing")
    check("F5 只有一次物理故障身份（injected=1）而非逐次重注入",
          pcc2.count("chaosLatchQueueValidStuck(") == 1
          and "stuck_until_end" in pcc2, "identity contract missing")
    check("F5 行为日志 p04a_queue_stuck.log",
          '"p04a_queue_stuck.log"' in pcc2, "behavior log missing")
    f5_flags = src("tools/lsu_campaign.py").split("if tier == \"F5\":", 1)
    check("campaign F5 = permanent tier (max_faults 0)",
          len(f5_flags) == 2
          and '"--prefetch_max_faults", "0"' in f5_flags[1][:400],
          "F5 flags missing")
    for rid in ("P04-F5-W2", "P04-F5-W8"):
        sd = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/"
                  f"campaign_p04f5_v2_20261105/{rid}/seed1")
        if not (sd / "chain_report.json").is_file():
            print(f"  SKIP {rid} 证据不在（{sd}）——源契约已覆盖")
            continue
        beh = (sd / "p04a_queue_stuck.log").read_text()
        m = re.search(r"event=latch field=queue_valid before=valid "
                      r"after=invalid state=stuck_until_end "
                      r"slot=(\d+) entries=(\d+) latch_invalidated=(\d+)",
                      beh)
        check(f"{rid} latch 记录 fixed slot + 单一失效条目",
              m is not None and int(m.group(2)) == 1
              and int(m.group(3)) == 1, beh)
        inj = (sd / "prefetch_injections.log").read_text()
        check(f"{rid} 注入行 = P04_queue_valid_stuck（一次物理故障）",
              inj.count("P04_queue_valid_stuck") == 1, inj)
        text = gzip.open(sd / "prop_evt.txt.gz", "rt").read()
        check(f"{rid} 真实 stuck 传播实例（birth/skip）",
              "state_after=invalid_stuck" in text
              and "state_after=invalid_skipped" in text, "events missing")
        ids = set(re.findall(r"fault_id=(\d+)", text))
        check(f"{rid} 全部传播实例共享同一物理 fault_id",
              len(ids) == 1, str(ids))
        # Fixed-slot contract: the latch event carries the selected slot,
        # and every stuck birth stays in that slot.
        slots = set(re.findall(r"entry_index=(\d+)", text))
        check(f"{rid} stuck 事件只落在所选 slot",
              m is not None and slots == {m.group(1)}, str(slots))
        rep = json.load(open(sd / "chain_report.json"))
        check(f"{rid} 终局按真实链报告（不伪造 L5）",
              rep.get("terminal") in
              ("provable_to_L2_then_unknown",
               "provable_to_L3_then_unknown",
               "provable_to_L4_then_unknown",
               "full", "detected_contained"),
              str(rep.get("terminal")))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
