#!/usr/bin/env python3
"""Generate M07_C02_T01/T02_COMPLETE_PROPAGATION.md from verified evidence."""
import json
import os

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
ev = json.load(open(os.path.join(ROOT, "work", "obs0222_evidence.json")))

BUILD = "ce80a9c983b31f77c9b4a6626012505fd3484d5c00df5b9399a9d6975ab2b73d"

META = {
    "M07-F0-W14-W5X3-C02-T01": {
        "tidx": "T01", "seq": 24118302, "tid": 4, "asid": 236, "pc": "0x401a54",
        "va": "0x400d200000", "pa": "0x83496000", "episode": 1, "pid": 318,
        "control_contrast": (
            "同一条 load（seq=24118302）在 Control 中 `translation_result(fault_status=Data)`，"
            "无 `lsu_request`（translateMmuOn 仅当 fault==NoFault 才发），随后同样 "
            "`squash_translation_decision=discard_due_to_prior_squash` + "
            "`translation_request_discarded`。证明故障确实把微架构路径从「拒绝」改写为"
            "「NoFault 放行 + 发出请求」，但两条路径都被 squash 丢弃。"),
    },
    "M07-F0-W14-W5X3-C02-T02": {
        "tidx": "T02", "seq": 27030544, "tid": 9, "asid": 242, "pc": "0x401a54",
        "va": "0x400d200000", "pa": "0x83474000", "episode": 2, "pid": 320,
        "control_contrast": (
            "同一条 load（seq=27030544）在 Control 中 `translation_result(fault_status=Data)`，"
            "无 `lsu_request`，随后同样 `squash_translation_decision=discard_due_to_prior_squash`"
            " + `translation_request_discarded`。"),
    },
}

KIND_ORDER = ["translation_start", "squash", "mmu_fault_activate",
              "translation_result", "lsu_request", "translation_response_received",
              "squash_translation_decision", "squash_translation_invoked",
              "translation_request_discarded", "cache_dispatch_decision"]

KIND_MEANING = {
    "translation_start": "翻译开始（MMU::getTE）",
    "squash": "Pre-activation Squash（负载在页表游走期间被 squash，游走仍继续）",
    "mmu_fault_activate": "故障激活：permission grant false → true（M07 one-shot）",
    "translation_result": "翻译结果 NoFault（反转后放行）",
    "lsu_request": "LSU 请求（translateMmuOn，翻译完成、即将移交 LSQ）",
    "translation_response_received": "翻译结果真正返回并被 LSQ 接收",
    "squash_translation_decision": "LSQ 判定动态指令已 Squashed → discard_due_to_prior_squash",
    "squash_translation_invoked": "实际调用 squashTranslation()（released=1 → 置 TranslationSquashed 并 self-destruct）",
    "translation_request_discarded": "请求生命周期终止（prior_squash_before_translation_completion，清理完成）",
    "cache_dispatch_decision": "Cache 派发被阻止（cache_dispatch_blocked_by_squash）",
}


def find(entry, kind):
    return next(e for e in entry["chain"] if e["kind"] == kind)


def gen(sid):
    m = META[sid]
    e = ev[sid]
    chain = e["chain"]
    a = find(e, "mmu_fault_activate")
    t = find(e, "translation_result")
    disc = find(e, "translation_request_discarded")

    lines = []
    lines.append("# %s 完整传播链证据（SQUASHED_BEFORE_MEMORY_ACCESS）" % sid)
    lines.append("")
    lines.append("> 样本 `%s`（模型 M07 / 上下文 C02 / 时机 %s）。  " % (sid, m["tidx"]))
    lines.append("> 本轮（W5X3-OBS-0222）通过纯观测埋点，在运行时直接证明故障请求从激活到")
    lines.append("> squash 丢弃的完整生命周期；终态 **SQUASHED_BEFORE_MEMORY_ACCESS**，")
    lines.append("> Completeness **FULL**（不再标记 PARTIAL / REQUEST_PENDING_AT_ROI_END）。")
    lines.append("")
    lines.append("## 1. 目标动态指令")
    lines.append("")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    lines.append("| DynInstSeq | %d |" % m["seq"])
    lines.append("| TranslationID | %d |" % m["tid"])
    lines.append("| ASID | %d |" % m["asid"])
    lines.append("| PC | %s |" % m["pc"])
    lines.append("| VA | %s |" % m["va"])
    lines.append("| PA | %s |" % m["pa"])
    lines.append("| Episode | %d（PID %d） |" % (m["episode"], m["pid"]))
    lines.append("| Fault | M07 权限 grant 反转（false → true，one-shot），Where=MMU::checkPermissions64 |")
    lines.append("")
    lines.append("## 2. 完整运行时事件链（原始 Trace，含 EventID / Tick / 行号）")
    lines.append("")
    lines.append("Trace：`runs/W5X3_OBS/%s-%s/Trace/prop_evt.txt.gz`（SHA256 ``%s``）" %
                (m["tidx"][0] == "T" and "M07-F0-W14-W5X3-OBS-C02" or "", m["tidx"], e["trace_sha256"]))
    lines.append("")
    lines.append("| EventID | parent | Kind | Tick | 行号 | 说明 |")
    lines.append("|---|---|---|---|---|---|")
    for k in KIND_ORDER:
        c = find(e, k)
        extra = ""
        if k == "translation_result":
            extra = "（fault_status=NoFault）"
        elif k == "squash_translation_decision":
            extra = "（decision=discard_due_to_prior_squash, released=%s）" % c["released"]
        elif k == "squash_translation_invoked":
            extra = "（released=%s，置 TranslationSquashed + self-destruct）" % c["released"]
        elif k == "translation_request_discarded":
            extra = "（terminal_reason=prior_squash_before_translation_completion）"
        elif k == "cache_dispatch_decision":
            extra = "（dispatch_decision=cache_dispatch_blocked_by_squash）"
        lines.append("| %d | %s | %s | %d | %d | %s%s |" %
                     (c["event_id"], c["parent"] or "—", k, c["tick"],
                      c["line"], KIND_MEANING[k], extra))
    lines.append("")
    lines.append("所有事件 fault_id=1（自激活起）、translation_id=%d、dyn_inst_seq=%d、" % (m["tid"], m["seq"]))
    lines.append("request_id=%d，parent_event_id 逐级链式相连（%d→%d→%d→%d→%d→%d→%d→%d）。" %
                (m["seq"], a["event_id"], t["event_id"],
                 find(e, "lsu_request")["event_id"], find(e, "translation_response_received")["event_id"],
                 find(e, "squash_translation_decision")["event_id"], find(e, "squash_translation_invoked")["event_id"],
                 disc["event_id"], find(e, "cache_dispatch_decision")["event_id"]))
    lines.append("")
    lines.append("## 3. Fault → Terminal 因果 DAG")
    lines.append("")
    lines.append("```text")
    lines.append("Translation Start")
    lines.append("      |")
    lines.append("      v")
    lines.append("Pre-activation Squash  (负载在页表游走期间被 squash)")
    lines.append("      |")
    lines.append("      v")
    lines.append("MMU Fault Activation   (permission: false -> true, fault_id=1)")
    lines.append("      |")
    lines.append("      v")
    lines.append("Translation Result     (NoFault, 同 tid/seq/request_id)")
    lines.append("      |")
    lines.append("      v")
    lines.append("LSU Translation Request")
    lines.append("      |")
    lines.append("      v")
    lines.append("Translation Response Received")
    lines.append("      |")
    lines.append("      v")
    lines.append("Squash Status Check    (decision=discard_due_to_prior_squash)")
    lines.append("      |")
    lines.append("      v")
    lines.append("squashTranslation()    (released=1 -> TranslationSquashed + self-destruct)")
    lines.append("      |")
    lines.append("      v")
    lines.append("Request Cleanup / Discard  (prior_squash_before_translation_completion)")
    lines.append("      |")
    lines.append("      v")
    lines.append("CACHE_DISPATCH_BLOCKED_BY_SQUASH")
    lines.append("      |")
    lines.append("      v")
    lines.append("Terminal: SQUASHED_BEFORE_MEMORY_ACCESS")
    lines.append("```")
    lines.append("")
    lines.append("## 4. 七个因果环节的运行时证据")
    lines.append("")
    lines.append("| # | 环节 | 证据（EventID） |")
    lines.append("|---|---|---|")
    lines.append("| 1 | 故障激活修改了该 Translation 的权限状态 | `mmu_fault_activate` event %d，permission_before=false → after=true |" % a["event_id"])
    lines.append("| 2 | Translation Result NoFault 对应同一请求 | `translation_result` event %d（fault_id=1, tid=%d, seq=%d） |" % (t["event_id"], m["tid"], m["seq"]))
    lines.append("| 3 | LSU 接收了该翻译响应 | `translation_response_received` event %d |" % find(e, "translation_response_received")["event_id"])
    lines.append("| 4 | LSU 检查发现 DynInst 已 Squashed | `squash_translation_decision` event %d（discard_due_to_prior_squash, released=1） |" % find(e, "squash_translation_decision")["event_id"])
    lines.append("| 5 | 请求进入 squashTranslation 清理分支 | `squash_translation_invoked` event %d |" % find(e, "squash_translation_invoked")["event_id"])
    lines.append("| 6 | 请求完成 Discard | `translation_request_discarded` event %d（prior_squash_before_translation_completion, released=1） |" % disc["event_id"])
    lines.append("| 7 | 请求未进入 Cache / 架构提交 | `cache_dispatch_decision` event %d（cache_dispatch_blocked_by_squash）；全 Trace 无该 seq 的 cache_request / memory_response / rf_writeback / commit |" % find(e, "cache_dispatch_decision")["event_id"])
    lines.append("")
    lines.append("## 5. 与 Control 的对照")
    lines.append("")
    lines.append(m["control_contrast"])
    lines.append("")
    lines.append("Control：`runs/W5X3_OBS/CTRL-OBS-M07-C02/Trace/prop_evt.txt.gz`（SHA256 ``%s``）。" % e["control_trace_sha256"])
    lines.append("")
    lines.append("## 6. Guest SIGSEGV 独立性说明")
    lines.append("")
    lines.append("Guest 仍报告 `signal=11 si_code=2 fault_addr=%s result=PASS`（架构预期 SIGSEGV）。" % m["va"])
    lines.append("该 SIGSEGV **不是**故障动态指令造成的：故障指令得到 `fault_status=NoFault`（授权被反转放行），")
    lines.append("其请求在翻译完成时因「指令已被预热 squash」被丢弃（本文件 §2/§4）；SIGSEGV 来自未故障的")
    lines.append("架构拒绝路径（execute-only 权限拒绝，one-shot 已被消耗）。因此本样本是**微架构传播+终止链的")
    lines.append("完整观测**，不是软件层面 SDC，也不把 Guest SIGSEGV 错误归因于故障指令。")
    lines.append("")
    lines.append("## 7. 溯源")
    lines.append("")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    lines.append("| 新 Build Hash | `%s` |" % BUILD)
    lines.append("| Fault Trace SHA256 | `%s` |" % e["trace_sha256"])
    lines.append("| Control Trace SHA256 | `%s` |" % e["control_trace_sha256"])
    lines.append("| 新增埋点 Patch | `work/0222_lsq_translation_lifecycle.patch` |")
    lines.append("| 复现命令 | `python3 work/rerun_m07_c02_obs.py`（或见 Run_Log/command.txt） |")
    lines.append("| 终态 | SQUASHED_BEFORE_MEMORY_ACCESS（Completeness=FULL） |")
    lines.append("")

    return "\n".join(lines)


for sid in META:
    out = os.path.join(ROOT, "exports", "MMU_FINAL_FROZEN_DELIVERY",
                       "%s_COMPLETE_PROPAGATION.md" %
                       sid.replace("M07-F0-W14-W5X3-C02-", "M07_C02_"))
    # name mapping: M07-F0-W14-W5X3-C02-T01 -> M07_C02_T01
    fname = "M07_C02_%s_COMPLETE_PROPAGATION.md" % sid.split("-")[-1]
    out = os.path.join(ROOT, "exports", "MMU_FINAL_FROZEN_DELIVERY", fname)
    with open(out, "w") as fh:
        fh.write(gen(sid))
    print("wrote", out)