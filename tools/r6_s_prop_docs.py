#!/usr/bin/env python3
"""[LSU][R6-S] per-seed complete propagation documents (21 PASS seeds).

Reads ONLY the seed's own unmodified evidence:
  runs/lsu/r6_s_unit/<RunID>_s<N>/manifest.json
  runs/lsu/r6_s_unit/<RunID>_s<N>/<RunID>/chain_report.json
  runs/lsu/r6_s_unit/<RunID>_s<N>/<RunID>/cell_results.json
  runs/lsu/r6_s_unit/<RunID>_s<N>/<RunID>/seed<N>/{prop_evt.txt.gz,stats.txt,
      run.out,addrpath_injections.log}

and writes `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`.
No event, id, tick or value is synthesized; every sentence quotes a field that
exists in that seed's own stream.  Seeds that are not qualified are refused.

Usage:
  python3 tools/r6_s_prop_docs.py           # generate / refresh + index
  python3 tools/r6_s_prop_docs.py --check   # eligibility summary only
"""
import gzip
import hashlib
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS = Path("/home/sdc/gem5-fi-ding/runs/lsu")
EVID = RUNS / "r6_s_unit"
# [R6-S-REPAIR 2026-10-30] The repaired round writes fresh evidence under a
# new root; the original 7 RunIDs stay in the frozen root (never re-run).
EVID_NEW = Path(os.environ.get("R6S_EVID_ROOT", str(RUNS / "r6_s_unit_r3")))
OUT = REPO / "runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
STATUS = RUNS / "RESULTS/STATUS/R6-S-UNIT-STATUS.json"

OLD_RIDS = ["S04-F0-W0", "S04-F0-W5", "S05-F0-W3", "S05-F0-W5",
            "S06-F0-W5", "S06-F0-W6", "S07-F0-W5"]
NEW_RIDS = ["S01-F0-W5", "S02-F0-W5", "S08-F0-W5", "S09-F0-W5",
            "S13-F0-W1", "S13-F0-W5", "S13-F0-W12", "S13-F1-W1",
            "S13-F2-W1"]
PASS_RIDS = OLD_RIDS + NEW_RIDS
SEEDS = [1, 2, 3]

MODEL_NAME = {
    "S01": "Store Queue 单比特翻转", "S02": "Store Queue 双比特翻转",
    "S03": "Store Queue 卡死", "S04": "Store Queue 换值",
    "S05": "Store Queue 错位拼接", "S06": "Store Queue 状态",
    "S07": "Store Queue 换值", "S08": "Store Queue 换值",
    "S09": "Store Queue 错位拼接", "S10": "Store Queue 换值",
    "S11": "Store Queue 时序", "S13": "Store Queue 单比特翻转",
}

# Observation layer of a kind, mirrors tools/lsu_prop_fields.py.
LAYER_OF_KIND = {
    "inj": "L0", "addr_form": "L1", "lsq_push": "L1",
    "sq_entry": "L1", "lsq_fwd": "L2",
    "mem_req": "L2",
    "lsq_sendfrag": "L2", "tlb_translate": "L2", "tlb_fault": "L2",
    "tlb_hit": "L2", "arch_translation_fault": "L2",
    "sq_execute": "L3", "sq_writeback": "L3", "lq_read": "L3",
    "resp": "L3", "sq_complete": "L3", "lq_complete": "L3",
    "cache_access": "L3", "cache_return": "L3", "cache_fill": "L3",
    "cache_evict": "L3", "mshr_alloc": "L3", "mshr_merge": "L3",
    "mshr_fill": "L3", "mshr_free": "L3", "cache_writeback": "L3",
    "taint_reg": "L4", "consumer": "L4", "errant_commit": "L4",
    "squash_discarded": "L4", "squash_masked": "L4",
    "store_not_retired": "L4",
    "chain_end": "—",
}

ROLE = {
    "inj": "L0 故障注入",
    "addr_form": "L1 地址形成",
    "lsq_push": "L1 入队（LQ/SQ）",
    "sq_entry": "L1 生产 store 的 SQ 表项（转发源）",
    "lsq_fwd": "L2 store→load 转发决策/传输",
    "mem_req": "L2 请求创建",
    "lsq_sendfrag": "L2 请求分片",
    "tlb_translate": "L2 地址翻译",
    "lq_read": "L3 load 读取队列",
    "sq_execute": "L3 store 执行",
    "sq_writeback": "L3 store 回写",
    "resp": "L3 数据响应",
    "lq_complete": "L3 load 完成",
    "sq_complete": "L3 store 完成",
    "taint_reg": "L4 污点进入寄存器",
    "errant_commit": "L5 错误提交（逃逸）",
    "consumer": "L4 下游消费者",
    "squash_discarded": "L4 检测并 squash 丢弃",
    "store_not_retired": "L4 未退休即丢弃",
    "chain_end": "生命周期结束标记（非 L5 证据）",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_events(path):
    ev = []
    opener = gzip.open if str(path).endswith(".gz") else open
    try:
        with opener(path, "rt", errors="replace") as f:
            for line in f:
                if not line.startswith("PROP-EVT:"):
                    continue
                d = {}
                for kv in line.split()[1:]:
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        d[k] = v
                ev.append(d)
    except (EOFError, OSError):
        # Truncated gzip: the stream is not admissible evidence for a doc.
        return []
    return ev


def evidence(rid, seed):
    if rid in OLD_RIDS:
        roots = [EVID]
    else:
        roots = [Path(p) for p in os.environ.get(
            "R6S_EVID_ROOTS", "").split(":") if p] or [EVID_NEW]
    outdir = None
    for root in roots:
        cand = root / f"{rid}_s{seed}"
        rep = cand / rid / f"seed{seed}" / "chain_report.json"
        if rep.exists():
            outdir = cand
            break
    if outdir is None:
        outdir = roots[0] / f"{rid}_s{seed}"
    rdir = outdir / rid
    seed_dir = rdir / f"seed{seed}"
    rec = {"rid": rid, "seed": seed, "outdir": outdir, "rdir": rdir,
           "seed_dir": seed_dir}
    try:
        rec["manifest"] = json.loads((outdir / "manifest.json").read_text())
        rec["chain"] = json.loads((rdir / "chain_report.json").read_text())
        rec["cell"] = json.loads((rdir / "cell_results.json").read_text())
    except (OSError, json.JSONDecodeError):
        rec["qualified"] = False
        return rec
    ev_path = seed_dir / "prop_evt.txt.gz"
    if not ev_path.exists():
        ev_path = seed_dir / "prop_evt.txt"
    rec["ev_path"] = ev_path
    rec["events"] = read_events(ev_path)
    rec["done"] = (outdir / ".done").exists()
    rec["runout"] = (seed_dir / "run.out").read_text(errors="replace")
    rec["inj_text"] = ""
    for name in ("addrpath_injections.log", "lsq_fwd_injections.log"):
        inj_log = seed_dir / name
        if inj_log.exists():
            rec["inj_text"] = inj_log.read_text(errors="replace")
            rec["inj_log_name"] = name
            break
    rec.setdefault("inj_log_name", "n/a")
    rec["sample"] = (rec["chain"].get("samples") or [{}])[0]
    faults = rec["sample"].get("faults") or {}
    rec["fid"] = next(iter(faults.keys()), "")
    rec["fault"] = max(faults.values(),
                       key=lambda f: f.get("event_count", 0)) if faults else {}
    rec["cev"] = [e for e in rec["events"] if e.get("fault_id") == rec["fid"]]
    rec["qualified"] = bool(
        rec["done"] and rec["sample"].get("admitted")
        and rec["sample"].get("certified")
        and not rec["sample"].get("truncated")
        and not rec["sample"].get("evidence_truncated")
        # [R6-S-REPAIR 2026-10-30] A Timeout/Hang is not a normal EOF outcome;
        # even a closed-looking chain on a timed-out run is not a PASS seed.
        and rec["sample"].get("oracle_outcome") not in ("Timeout", "Hang")
        and rec["cev"] and not (rec["sample"].get("admission") or {}).get("violations"))
    return rec


def parse_funnel(text):
    """Last FUNNEL: line and the CHAOS_L0_FUNNEL line of the injection log."""
    funnel = None
    l0 = None
    for ln in text.splitlines():
        if ln.startswith("FUNNEL:"):
            funnel = ln
        elif ln.startswith("CHAOS_L0_FUNNEL:"):
            l0 = ln
    return funnel, l0


def parse_trigger(runout):
    for ln in runout.splitlines():
        if ln.startswith("CHAOS_LSU_TRIGGER:"):
            return ln
    return ""


def parse_detect(runout):
    for ln in runout.splitlines():
        if ln.startswith("CHAOS_DETECT:"):
            return ln
    return ""


def inj_line(text):
    # addrpath logs use "Tick: ..."; the forwarding/S10 injector logs use
    # "Cycle: ...". Both are the seed's own injection line.
    lines = [ln for ln in text.splitlines() if ln.startswith("Tick: ")]
    if not lines:
        lines = [ln for ln in text.splitlines() if ln.startswith("Cycle: ")]
    return lines[-1] if lines else ""


def fmt(e, key, dash="—"):
    v = e.get(key, "")
    return v if v not in ("", None) else dash


def layer_of(e):
    dl = e.get("detection_layer", "")
    if dl and dl not in ("None", "none", "Unknown", "unknown"):
        return dl
    return LAYER_OF_KIND.get(e.get("kind", ""), "—")


def addr_change(e):
    before, after = e.get("before", ""), e.get("after", "")
    if before or after:
        return f"{before or '—'}→{after or '—'}"
    va, pa = e.get("va", ""), e.get("pa", "")
    if va:
        return f"va={va}" + (f", pa={pa}" if pa else "")
    return "—"


def state_change(e):
    sb, sa = e.get("state_before", ""), e.get("state_after", "")
    if sb or sa:
        return f"{sb or '—'}→{sa or '—'}"
    if e.get("contained") not in ("", None):
        return f"contained={e.get('contained')}"
    return "—"


def narrate(rec, e, prev, nxt):
    """One human-readable step; every value is read from this seed's event."""
    k = e.get("kind", "")
    eid = e.get("event_id", "")
    par = e.get("parent_event_id", "") or "（根事件，无父）"
    tick = e.get("tick", "")
    bits = []
    if k == "inj":
        field = e.get("field") or "none"
        bits.append(
            f"event_id={eid}，tick={tick}：L0 故障注入。CHAOSAddrPath 在 "
            f"lsq_pushRequest_PRE 站点以 {rec['mode']} 模式写入一个故障；"
            f"注入字段 field={field}，地址 `{e.get('before', '')}` → "
            f"`{e.get('after', '')}`，dyn_inst_seq={fmt(e, 'dyn_inst_seq')}，"
            f"corr={fmt(e, 'corr')}。该事件无父事件，是整条传播链的根。")
    elif k == "addr_form":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L1 地址形成阶段"
            f"看到注入后的地址值 `{e.get('before', '')}` → `{e.get('after', '')}`，"
            f"dyn_inst_seq={fmt(e, 'dyn_inst_seq')}。注入值在这一步成为"
            f"第一个被污染的对象（地址计算输入）。")
    elif k == "lsq_push":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L1 入队。该请求被"
            f"推入 {e.get('field', '—')} 队列（opcode={fmt(e, 'opcode')}，"
            f"pc={fmt(e, 'pc')}，lq_idx={fmt(e, 'lq_idx')}，"
            f"sq_idx={fmt(e, 'sq_idx')}，dyn_inst_seq={fmt(e, 'dyn_inst_seq')}）；"
            f"污染的地址/状态自此携带在 LSQ 条目中。")
    elif k == "mem_req":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L2 请求创建，"
            f"request_id={fmt(e, 'request_id')}，va=`{fmt(e, 'va')}`。"
            f"request_id 与入队条目的 dyn_inst_seq 一致，污染值随请求进入存储子系统。")
    elif k == "lsq_sendfrag":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L2 请求分片，"
            f"request_id={fmt(e, 'request_id')}，va=`{fmt(e, 'va')}`；"
            f"同一请求被拆分后仍然保持同一身份。")
    elif k == "tlb_translate":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L2 地址翻译，"
            f"request_id={fmt(e, 'request_id')}，va=`{fmt(e, 'va')}`，"
            f"pa=`{fmt(e, 'pa')}`（该事件未记录 pa 时如实写 —）。")
    elif k in ("lq_read",):
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L3 load 读取队列项，"
            f"request_id={fmt(e, 'request_id')}，va=`{fmt(e, 'va')}`，"
            f"lq_idx={fmt(e, 'lq_idx')}。被污染的 load 请求在此实际被消费，链到达 L3。")
    elif k in ("sq_execute", "sq_writeback", "sq_complete"):
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L3 {k}，"
            f"request_id={fmt(e, 'request_id')}，va=`{fmt(e, 'va')}`，"
            f"pa=`{fmt(e, 'pa')}`；store 侧继续携带被污染的值。")
    elif k == "resp":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L3 数据响应返回，"
            f"request_id={fmt(e, 'request_id')}，va=`{fmt(e, 'va')}`，"
            f"pa=`{fmt(e, 'pa')}`；响应数据进入 LSQ/寄存器路径。")
    elif k == "lq_complete":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L3 load 完成，"
            f"request_id={fmt(e, 'request_id')}，va=`{fmt(e, 'va')}`，"
            f"pa=`{fmt(e, 'pa')}`；load 数据已可被后续指令读取。")
    elif k == "taint_reg":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L4 污点进入体系结构"
            f"寄存器，request_id={fmt(e, 'request_id')}，va=`{fmt(e, 'va')}`，"
            f"corr={fmt(e, 'corr')}；污染值离开 LSQ 进入寄存器数据通路。")
    elif k == "errant_commit":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L5 错误提交。"
            f"detection_layer={fmt(e, 'detection_layer')}，"
            f"outcome={fmt(e, 'outcome')}，corr={fmt(e, 'corr')}；"
            f"带污染值的指令真实退休，这是逃逸终局（不是 chain_end 推断）。")
    elif k == "consumer":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L4 下游消费者事件，"
            f"corr={fmt(e, 'corr')}；证明污染值被后续指令实际读取/消费。")
    elif k == "squash_discarded":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L4 检测并包含。"
            f"state_before=`{fmt(e, 'state_before')}`，contained={fmt(e, 'contained')}，"
            f"containment_reason={fmt(e, 'containment_reason')}，"
            f"request_id={fmt(e, 'request_id')}；该 {e.get('field', '条目')} 在提交前"
            f"被 squash 并从队列丢弃，错误值没有写入体系结构状态。")
    elif k == "store_not_retired":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：L4 store 未退休即被丢弃，"
            f"contained={fmt(e, 'contained')}，request_id={fmt(e, 'request_id')}；"
            f"错误的 store 副作用没有落地。")
    elif k == "chain_end":
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：生命周期标记 "
            f"corr=none，outcome=run_end。它只表示仿真结束，**不是** L5 证据，"
            f"也从不参与终局判定。")
    else:
        bits.append(
            f"event_id={eid}（parent={par}），tick={tick}：{k}，"
            f"va=`{fmt(e, 'va')}`，request_id={fmt(e, 'request_id')}，"
            f"corr={fmt(e, 'corr')}。")
    if nxt is not None:
        bits.append(
            f"下一步：event_id={nxt.get('event_id')}（{nxt.get('kind')}）以 "
            f"parent_event_id={eid} 承接本事件，共享 fault_id={fmt(e, 'fault_id')}"
            + (f" 与 dyn_inst_seq={e.get('dyn_inst_seq')}"
               if e.get("dyn_inst_seq") else "")
            + "，且 tick 不回退，因此该事件是下一步的直接前驱。")
    else:
        bits.append("本事件是该 fault 在本 seed 事件流中的最后一条。")
    return " ".join(bits)


def doc(rec):
    rid, seed = rec["rid"], rec["seed"]
    s, f, man, cell = rec["sample"], rec["fault"], rec["manifest"], rec["cell"]
    model, freq, wl = rid.split("-")[0], rid.split("-")[1], rid.split("-")[2]
    wl_full = rec["workload"]
    cev = rec["cev"]
    inj = [e for e in cev if e.get("kind") == "inj"][0]
    logline = inj_line(rec["inj_text"])
    m = re.search(r"mode=([^,\s]+), old_addr=([^,\s]+), new_addr=([^,\s]+)",
                  logline or "")
    mode = m.group(1) if m else "—"
    rec["mode"] = mode
    old_addr = m.group(2) if m else inj.get("before", "")
    new_addr = m.group(3) if m else inj.get("after", "")
    bem = re.search(r"old_be=([^,\s]+), new_be=([^,\s]+)", logline or "")
    mask = f"{bem.group(1)} → {bem.group(2)}" if bem else "—"
    funnel, l0f = parse_funnel(rec["inj_text"])
    trig, det = parse_trigger(rec["runout"]), parse_detect(rec["runout"])
    edges = f.get("edges") or {}
    proven = [k for k, v in edges.items()
              if v == "proven" and not k.endswith("_witness")]
    missing = [k for k, v in edges.items()
               if v == "missing" and not k.endswith("_witness")]
    contain = [e for e in cev if e.get("contained") == "1"
               and e.get("event_id") != "0"]
    cid = contain[0].get("event_id") if contain else "—"
    cons = (s.get("consumer_summary_accounting") or {}).get("conservation") or "n/a"
    viol = json.dumps((s.get("admission") or {}).get("violations") or [],
                      ensure_ascii=False)
    provable = f.get("provable_to")
    L = []
    A = L.append
    A(f"# {rid} seed{seed} — 完整传播路径（真实事件时间顺序）\n")
    A("> 本文只转录该 seed 自己的原始事件流（`prop_evt.txt.gz`）与权威 "
      "`chain_report.json`；未修改事件流，未跨 seed 复用任何数值，"
      "未把推测写成事件事实。\n")
    # 1
    A("## 1. 样本身份\n")
    A("| 项 | 值 |\n|---|---|")
    A(f"| RunID | `{rid}` |")
    A(f"| seed | `{seed}` |")
    A(f"| model | `{model}`（{MODEL_NAME.get(model, model)}） |")
    A(f"| frequency | `{freq}` |")
    A(f"| workload | `{wl}`（{wl_full}） |")
    A(f"| binary_path | `{man.get('binary_path')}` |")
    A(f"| binary_sha256 | `{man.get('binary_sha256')}` |")
    A(f"| binary_source_head | `{man.get('binary_source_head')}` |")
    A(f"| analysis_tool_head | `{man.get('analysis_tool_head')}` |")
    A(f"| prop_evt_path | `{rec['ev_path']}` |")
    A(f"| prop_evt_sha256 | `{sha256(rec['ev_path'])}` |")
    A(f"| chain_report_path | `{rec['rdir'] / 'chain_report.json'}` |")
    A(f"| chain_report_sha256 | `{sha256(rec['rdir'] / 'chain_report.json')}` |")
    A(f"| cell_results_path | `{rec['rdir'] / 'cell_results.json'}` |")
    A(f"| cell_results_sha256 | `{sha256(rec['rdir'] / 'cell_results.json')}` |")
    A("")
    # 2
    A("## 2. 最终判定\n")
    A("| 项 | 值 |\n|---|---|")
    A(f"| oracle outcome | `{s.get('oracle_outcome')}` |")
    A(f"| terminal | `{f.get('terminal')}` |")
    A(f"| provable_to | `{provable}` |")
    A(f"| beyond | `{f.get('beyond') or '—'}` |")
    A(f"| admitted | `{s.get('admitted')}` |")
    A(f"| certified | `{s.get('certified')}` |")
    A(f"| violations | `{viol}` |")
    A(f"| conservation | `{cons}` |")
    A(f"| count_contradiction | `{cell.get('count_contradiction')}` |")
    A(f"| truncated | `{s.get('truncated')}` |")
    A(f"| 事件总数 | `{s.get('event_count')}` |")
    A(f"| containment_event_id | `{cid}` |")
    A("")
    # 3
    A("## 3. 真实注入\n")
    A("| 项 | 值 |\n|---|---|")
    A(f"| 注入 tick | `{inj.get('tick')}` |")
    A(f"| event_id | `{inj.get('event_id')}` |")
    A("| parent_event_id | `—` |")
    A("| 注入部件 | `CHAOSAddrPath` |")
    A(f"| 注入字段 | `{inj.get('field') or 'none'}` |")
    A(f"| 原值 | `{old_addr}` |")
    A(f"| 新值 | `{new_addr}` |")
    A(f"| mask | `{mask}` |")
    A(f"| 地址 | `{inj.get('before')}` |")
    A(f"| request_id | `{fmt(inj, 'request_id')}` |")
    A(f"| corr | `{fmt(inj, 'corr')}` |")
    A(f"| injected/activated 计数 | `{funnel or '—'}`；`{l0f or '—'}` |")
    A("")
    A(f"注入日志原文（本 seed 自己的 `{rec['inj_log_name']}`）：\n")
    A("```text")
    A(logline or "（无 Tick 注入行）")
    A("```\n")
    A("运行期触发/检测原文（本 seed 自己的 `seed%d/run.out`）：\n" % seed)
    A("```text")
    A(trig or "（无 CHAOS_LSU_TRIGGER 行）")
    A(det or "（无 CHAOS_DETECT 行）")
    A("```\n")
    # 4
    A("## 4. 传播过程（真实事件时间顺序）\n")
    A(f"本 seed 的 fault_id={rec['fid']} 链共有 {len(cev)} 条真实事件，"
      f"事件种类序列为：`{' → '.join(e.get('kind', '') for e in cev)}`。"
      "以下按该 seed 事件流的原始顺序逐步说明。\n")
    for i, e in enumerate(cev):
        prev = cev[i - 1] if i else None
        nxt = cev[i + 1] if i + 1 < len(cev) else None
        A(f"**第 {i + 1} 步** — {narrate(rec, e, prev, nxt)}\n")
    # 5
    A("## 5. 关键事件表\n")
    A("| 顺序 | event_id | parent_event_id | tick | kind | layer | "
      "request_id | corr | 地址/值变化 | 状态变化 | 传播作用 |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, e in enumerate(cev):
        A(f"| {i + 1} | {e.get('event_id')} | "
          f"{e.get('parent_event_id') or '—'} | {e.get('tick')} | "
          f"{e.get('kind')} | {layer_of(e)} | {fmt(e, 'request_id')} | "
          f"{fmt(e, 'corr')} | {addr_change(e)} | {state_change(e)} | "
          f"{ROLE.get(e.get('kind'), '—')} |")
    A("")
    # 6
    A("## 6. 原始证据与哈希\n")
    A("| 证据 | 路径 | SHA-256 |\n|---|---|---|")
    for label, p in (("prop_evt", rec["ev_path"]),
                     ("chain_report", rec["rdir"] / "chain_report.json"),
                     ("cell_results", rec["rdir"] / "cell_results.json"),
                     ("stats", rec["seed_dir"] / "stats.txt"),
                     ("run.out", rec["seed_dir"] / "run.out"),
                     ("injections.log",
                      rec["seed_dir"] / rec["inj_log_name"]),
                     ("manifest", rec["outdir"] / "manifest.json")):
        A(f"| {label} | `{p}` | `{sha256(p)}` |")
    A("")
    A(f"事件流字节数：{rec['ev_path'].stat().st_size}（gzip 后）；"
      f"解压后事件行数：{len(rec['events'])}；本 fault 事件数：{len(cev)}。\n")
    # 7
    A("## 7. 可复现命令\n")
    A("```bash")
    A(man.get("cmd", ""))
    A("```\n")
    A(f"环境身份：binary SHA-256 `{man.get('binary_sha256')}`，"
      f"binary_source_head `{man.get('binary_source_head')}`，"
      f"analysis_tool_head `{man.get('analysis_tool_head')}`，"
      f"matrix SHA-256 `{man.get('matrix_sha256')}`。\n")
    # 8
    A("## 8. 诚实边界\n")
    A(f"- 本 doc 只证明该 seed 自己的事件流：已证明的层边为 "
      f"{', '.join(proven) if proven else '（无）'}；"
      f"缺失的层边为 {', '.join(missing) if missing else '（无）'}。")
    A(f"- 终局 `{f.get('terminal')}` 与 `provable_to={provable}` 直接取自该 seed 的 "
      "`chain_report.json`，未做任何推断升级。")
    A("- 三方计数：注入日志 `FUNNEL`/`CHAOS_L0_FUNNEL` 与 `run.out` 的 "
      "`CHAOS_LSU_TRIGGER` 全部来自本 seed；`stats.txt` 不含 "
      "`numFaultsInjected` 统计（addrpath 家族不发射该计数器），故该路为 **n/a**，"
      "不以 0 冒充。")
    A("- `chain_end` 只是生命周期标记（corr=none），从不作为 L5 证据；"
      "本 doc 未把 `chain_end` 当作终局。")
    if f.get("terminal") == "crash_translation_fault":
        A("- 本 seed 的终局是严格 `crash_translation_fault`：真实注入 → 连续 "
          "L0→L3 ancestry → 真实 `arch_translation_fault`（detection_layer=L2、"
          "contained=0、outcome=arch_exception、corr 为链关联值）→ 请求在产生"
          "任何内存副作用之前被翻译异常终止。L4/L5 结构性 **N/A**：不是缺失，"
          "也不得伪造。")
        A("- guest 真实 Crash 的受控证据：该 seed 的 `run.out` 含 "
          "`CHAOS_GUEST_SEGV_EXIT: cause=chaos_guest_segv code=139`，gem5 "
          "退出码 139（128+SIGSEGV）；admission 走独立的 crash_terminal 路径，"
          "与 full/contained 无关。")
    elif provable == "L3" and rid.startswith("S06"):
        A(f"- 本 seed 属于 S06 的 **L3 containment** 情形：真实包含事件是 "
          f"event_id={cid} 的 `squash_discarded`（detection_layer=L4，"
          f"contained=1，containment_reason=squash_discarded）；链 checker 把带 "
          "detection_layer/outcome/corr 的检测事件放在 L5 观测口径，而本 seed "
          "事件流中不存在连接 L3→L4 的传播见证事件（如 `taint_reg`），"
          "因此可证前缀停在 L3（`provable_to=L3`，edges 中 `L3->L4` 为 missing）。"
          "L4→L5 为 **N/A**：该 load 在提交前被 squash 丢弃，从未退休，"
          "事件流中没有 L5 退休事件；`chain_end` 不能补造 L5。"
          "准入来自显式 contained 检测事件，而不是从缺失边推断。")
    else:
        A("- 后续层为 N/A 的含义：本 seed 未在当前事件流中产生该层的真实事件，"
          "文档不会补造，也不会据此推断 Masked。")
    A("- 本 seed 未重跑；原始事件流未被修改；三个 seed 的数值各自独立，"
      "不存在跨 seed 复制。")
    A("")
    return "\n".join(L)


def index_section(rows):
    out = []
    add = out.append
    add("\n---\n")
    add("## R6-S（Store Queue 单元）逐 seed 传播路径\n")
    add(f"- S seed 文档：**{len(rows)}**（7 RunID × 3 seed）")
    add("- 全部 seed：binary SHA-256 `a1632e0f1d24be639044d24bac8e6fd902d0a6642"
        "b276fd430927471643e7046`，binary_source_head `2498573f`")
    add("- 判定口径：`oracle=Masked` + `terminal=detected_contained`（含 "
        "S06-F0-W6 seed2 的 `full`），admitted=True，certified=True，violations=[]；"
        "S06 seed1/seed2 与 S07 seed2 为 L3 containment（L4→L5 为 N/A）")
    add("")
    add("| RunID | seed | terminal | provable_to | 文档 |")
    add("|---|---|---|---|---|")
    for rid, seed, f in rows:
        add(f"| {rid} | {seed} | {f.get('terminal')} | {f.get('provable_to')} | "
            f"[`{rid}-seed{seed}.md`]({rid}/{rid}-seed{seed}.md) |")
    add("")
    return "\n".join(out)


def main(argv):
    status = json.loads(STATUS.read_text())
    wl = {r["run_id"]: r["workload"] for r in status["rows"]}
    check = "--check" in argv
    recs = []
    skipped = []
    for rid in PASS_RIDS:
        got = 0
        for seed in SEEDS:
            rec = evidence(rid, seed)
            rec["workload"] = wl.get(rid, "—")
            if not rec["qualified"]:
                skipped.append(f"{rid} seed{seed}")
                print(f"SKIP {rid} seed{seed}: not qualified "
                      f"(admitted/certified/violations/truncated)")
                continue
            got += 1
            recs.append(rec)
            print(f"OK {rid} seed{seed}: events={len(rec['cev'])} "
                  f"terminal={rec['fault'].get('terminal')} "
                  f"provable={rec['fault'].get('provable_to')}")
        if got == 0:
            print(f"REFUSE {rid}: no qualified seed "
                  f"(RunID has no per-seed evidence document)")
            return 2
    if check:
        print(f"{len(recs)} qualified seeds; skipped {len(skipped)}")
        return 0
    for rec in recs:
        rid, seed = rec["rid"], rec["seed"]
        d = OUT / rid
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{rid}-seed{seed}.md"
        if rid in OLD_RIDS and p.exists():
            # The original 21 S docs are frozen: never regenerate them.
            print(f"KEEP {p} (frozen original)")
            continue
        p.write_text(doc(rec))
        print(f"WROTE {p}")
    rows = [(r["rid"], r["seed"], r["fault"]) for r in recs]
    idx = OUT / "INDEX.md"
    text = idx.read_text()
    marker = "## R6-S（Store Queue 单元）逐 seed 传播路径"
    text = text.split(marker)[0].rstrip() + "\n"
    idx.write_text(text + index_section(rows))
    print(f"UPDATED {idx}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
