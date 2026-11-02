#!/usr/bin/env python3
"""Generate per-seed R6-S W1 (CHAOSLSQFwd) propagation docs from raw evidence.

Only the seed's own stream/report files are read.  The full event stream is
never transcribed (LSQFwd seeds carry 1e5-1e6 events); instead each fault's
canonical path is transcribed and the whole-stream census + SHA are recorded.

Writes into a staging directory; `--deploy` (run only after
audit_r6_w1_docs.py reports 0 errors) copies the Markdown atomically.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r6_w1_evidence as ev  # noqa: E402

DOCS_ROOT = "/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
DEFAULT_STAGE = "/home/sdc/gem5-fi-ding-cleanup-20261029/R6S_W1_DOCS_STAGE_20261102"
STAGE = DEFAULT_STAGE


def hx(v):
    return f"0x{v}" if v else "—"


def edge_map(fault):
    return {k: v for k, v in (fault.get("edges") or {}).items()
            if not k.endswith("_witness")}


def witnesses(fault):
    return {k: v for k, v in (fault.get("edges") or {}).items()
            if k.endswith("_witness")}


def witness_kind(w, side):
    # "L1:sq_entry@t34980760430" -> (layer, kind, tick)
    s = w.get(side, "")
    layer, _, rest = s.partition(":")
    kind, _, tick = rest.partition("@t")
    return layer, kind, tick


def inj_row_for(row):
    return (f"| `{row.get('Cycle')}` | `{row.get('Site')}` | `{row.get('FaultType')}` | "
            f"`{row.get('Vaddr')}` | `{row.get('FwdSize')}` | `{row.get('ByteOffset')}` | "
            f"`{row.get('Mask')}` | `{row.get('StoreSeq')}` | `{row.get('SqIdx')}` | "
            f"`{row.get('LoadSeq')}` | `{row.get('LqIdx')}` |")


def generate(root):
    s = ev.load_sample(root)
    st = ev.load_streams(s)
    man, cell, chain = s["manifest"], s["cell"], s["chain"]
    run_id, seed = s["run_id"], s["seed"]
    run = (cell.get("runs") or [{}])[0]
    events = st["events"]
    inj_rows = st["inj"]
    funnel = st["runout"]["funnel"] or {}
    trigger = st["runout"]["trigger"] or {}
    faults = chain.get("faults") or {}
    freq = run_id.split("-")[1] if "-" in run_id else "?"
    model = run_id.split("-")[0] if "-" in run_id else "?"

    # map fault id -> injection log row (ordered by cycle)
    inj_by_fid = {}
    for fid in sorted(faults, key=lambda x: int(x)):
        d = events["captured"].get(next(iter(st["path_ids"][fid]), None))
        if d is None:
            continue
        key = (d.get("cycle"), "0x" + d.get("va", ""),
               d.get("store_dyn_inst_seq"), d.get("dyn_inst_seq"))
        for row in inj_rows:
            if (row.get("Cycle"), row.get("Vaddr"), row.get("StoreSeq"),
                    row.get("LoadSeq")) == key:
                inj_by_fid[fid] = row
                break

    L = []
    a = L.append
    a(f"# {run_id} seed{seed} — LSQFwd 传播路径（真实事件流）")
    a("")
    a("> 本 doc 只转录该 seed 自己的 `prop_evt.txt.gz`、`chain_report.json`、"
      "`cell_results.json`、`stats.txt`、`run.out`、`lsq_fwd_injections.log` 与 `manifest.json`；"
      "未修改原始流，未跨 seed 复用数值，未把推测写成事件事实。")
    a("")
    a("## 1. 样本身份")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    a(f"| RunID | `{run_id}` |")
    a(f"| seed | `{seed}` |")
    a(f"| model | `{model}`（CHAOSLSQFwd store→load forward 数据域） |")
    a(f"| frequency | `{freq}` |")
    a("| workload | `W1`（mibench/bin/w1_all） |")
    for label, val in [
        ("manifest kind", man.get("kind", "worker")),
        ("manifest status", man.get("status")),
        ("exit_code", man.get("exit_code")),
        ("binary_path", man.get("binary_path")),
        ("binary_sha256", man.get("binary_sha256")),
        ("binary_source_head", man.get("binary_source_head", "n/a")),
        ("analysis_tool_head", man.get("analysis_tool_head")),
        ("start_time", man.get("start_time")),
        ("end_time", man.get("end_time")),
    ]:
        a(f"| {label} | `{val}` |")
    for label, p in [
        ("prop_evt_path", s["paths"]["prop_evt"]),
        ("prop_trace_path", s["paths"]["prop_trace"]),
        ("seed_chain_report_path", s["paths"]["seed_chain_report"]),
        ("cell_chain_report_path", s["paths"]["cell_chain_report"]),
        ("cell_results_path", s["paths"]["cell_results"]),
        ("stats_path", s["paths"]["stats"]),
        ("run_out_path", s["paths"]["run_out"]),
        ("inj_log_path", s["paths"]["inj_log"]),
        ("manifest_path", s["paths"]["manifest"]),
    ]:
        a(f"| {label} | `{p}` |")
    a(f"| evidence_dir | `{root}` |")
    a("")

    a("## 2. 最终判定（run 级 + 逐 fault）")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    a(f"| oracle outcome | `{chain.get('oracle_outcome')}` |")
    a(f"| gem5 guest exit | `{chain.get('exit_code')}` |")
    a(f"| terminal（链模型整体） | `{chain.get('terminal')}` |")
    a(f"| provable_to（链模型整体） | `{chain.get('provable_to')}` |")
    a(f"| beyond | {('`' + chain['beyond'] + '`') if chain.get('beyond') else '—'} |")
    a(f"| admitted | `{chain.get('admitted')}` |")
    a(f"| certified | `{chain.get('certified')}` |")
    a(f"| violations | `{(chain.get('admission') or {}).get('violations')}` |")
    a(f"| admission path | `{(chain.get('admission') or {}).get('path')}` |")
    a(f"| conservation | `{chain.get('consumer_summary_accounting', {}).get('conservation')}` |")
    a(f"| count_contradiction | `{cell.get('count_contradiction')}` |")
    a(f"| truncated | `{chain.get('truncated')}` |")
    a(f"| evidence_truncated | `{chain.get('evidence_truncated')}` |")
    a(f"| chain_valid | `{chain.get('chain_valid')}` |")
    a(f"| 事件总数 | `{events['count']}` |")
    a(f"| fault 数 | `{len(faults)}` |")
    a(f"| L0 funnel | attempted=`{funnel.get('attempted')}` eligible=`{funnel.get('eligible')}` "
      f"injected=`{funnel.get('injected')}` activated=`{funnel.get('activated')}` |")
    a(f"| cell admission_status | `{cell.get('admission_status')}` |")
    a(f"| cell outcome | `{run.get('outcome')}` |")
    a(f"| cell activated / attempted | `{run.get('activated')}` / `{run.get('attempted')}` |")
    a("")
    a("### 逐 fault 判定（全部取自该 seed 的 `chain_report.json`）")
    a("")
    a("| fault | 注入 Cycle | VA | 已证明层边 | 缺失层边 | terminal | provable_to |")
    a("|---|---|---|---|---|---|---|")
    for fid in sorted(faults, key=lambda x: int(x)):
        f = faults[fid]
        e = edge_map(f)
        proven = [k for k, v in e.items() if v == "proven"]
        missing = [k for k, v in e.items() if v != "proven"]
        row = inj_by_fid.get(fid, {})
        a(f"| {fid} | `{row.get('Cycle', '—')}` | `{row.get('Vaddr', '—')}` | "
          f"{', '.join(proven) or '—'} | {', '.join(missing) or '—'} | "
          f"`{f.get('terminal')}` | `{f.get('provable_to')}` |")
    a("")
    a("说明：整体 `terminal/provable_to` 是 `chain_report.json` 的 run 级汇总；"
      "逐 fault 的层边与终局以上表为准，二者不一致时不改写任何一侧。")
    a("")

    a("## 3. 真实注入清单")
    a("")
    a(f"`lsq_fwd_injections.log` 共 {len(inj_rows)} 条注入记录；funnel 记录 "
      f"injected={funnel.get('injected')}、activated={funnel.get('activated')}。"
      "下表直接转录日志字段，不做换算。")
    a("")
    a("| fault | Cycle | Site | FaultType | Vaddr | FwdSize | ByteOffset | Mask | StoreSeq | SqIdx | LoadSeq | LqIdx |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|")
    fid_by_row = {}
    for fid, row in inj_by_fid.items():
        fid_by_row[(row.get("Cycle"), row.get("Vaddr"), row.get("StoreSeq"),
                    row.get("LoadSeq"))] = fid
    for row in inj_rows:
        fid = fid_by_row.get((row.get("Cycle"), row.get("Vaddr"), row.get("StoreSeq"),
                              row.get("LoadSeq")), "—")
        a(f"| {fid} | " + inj_row_for(row).lstrip("| "))
    a("")

    a("## 4. 传播过程（逐 fault 的规范路径）")
    a("")
    a("规范路径 = `chain_report.json` 的 `faults[<id>].path_event_ids`；"
      "层号按路径位置给出（L0 = 注入），并与 `edges` witness 的 from/to 交叉核对。"
      "路径之外的原始事件仍计入第 5 节 census 与哈希，但不被抬升为层边。")
    a("")
    for fid in sorted(faults, key=lambda x: int(x)):
        f = faults[fid]
        ids = st["path_ids"][fid]
        row = inj_by_fid.get(fid, {})
        a(f"### fault {fid}")
        a("")
        a(f"- 注入：Cycle `{row.get('Cycle', '—')}`，Site `{row.get('Site', '—')}`，"
          f"Vaddr `{row.get('Vaddr', '—')}`，FwdSize `{row.get('FwdSize', '—')}`，"
          f"ByteOffset `{row.get('ByteOffset', '—')}`，Mask `{row.get('Mask', '—')}`，"
          f"StoreSeq `{row.get('StoreSeq', '—')}`，LoadSeq `{row.get('LoadSeq', '—')}`。")
        # Honest address provenance: the LSQFwd event domain carries VA and an
        # optional PA; PFN is not emitted.  Never print a blank as if verified.
        pas = []
        for eid in ids:
            p = events["captured"].get(eid, {}).get("pa")
            if p and p not in pas:
                pas.append(p)
        if pas:
            pa_txt = "、".join(f"`0x{p}`" for p in pas)
            pfn_txt = "、".join(f"`0x{int(p, 16) >> 12:x}`（由 PA 推导）" for p in pas)
        else:
            pa_txt = "`n/a`（规范路径事件 `pa=` 为空，未记录物理地址）"
            pfn_txt = "`n/a`（事件域无 pfn 字段，且 PA 为空）"
        a(f"- 地址：VA `{row.get('Vaddr', '—')}`；PA {pa_txt}；PFN {pfn_txt}。")
        a(f"- 层边：{', '.join(f'{k}={v}' for k, v in edge_map(f).items()) or '—'}。")
        a("")
        a("| 位置 | 层 | event_id | parent_event_id | tick | cycle | kind | request_id | dyn_inst_seq | va | before → after | state_before → state_after | detection/containment |")
        a("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for i, eid in enumerate(ids):
            d = events["captured"].get(eid, {})
            change = ""
            if d.get("before") or d.get("after"):
                change = f"{d.get('before') or '—'} → {d.get('after') or '—'}"
            state = ""
            if d.get("state_before") or d.get("state_after"):
                state = f"{d.get('state_before') or '—'} → {d.get('state_after') or '—'}"
            dc = []
            if d.get("detection_layer"):
                dc.append(f"layer={d['detection_layer']}")
            if d.get("contained"):
                dc.append(f"contained={d['contained']}")
            if d.get("outcome"):
                dc.append(f"outcome={d['outcome']}")
            if d.get("containment_layer") or d.get("containment_reason"):
                dc.append(f"{d.get('containment_layer') or '—'}:"
                          f"{d.get('containment_reason') or '—'}")
            a(f"| {i} | L{i} | {eid} | {d.get('parent_event_id') or '—'} | {d.get('tick')} | "
              f"{d.get('cycle')} | `{d.get('kind')}` | {d.get('request_id') or '—'} | "
              f"{d.get('dyn_inst_seq') or '—'} | {hx(d.get('va'))} | {change or '—'} | "
              f"{state or '—'} | {'；'.join(dc) or '—'} |")
        a("")
        w = witnesses(f)
        if w:
            a("| 层边 | witness from | witness to | shared_keys |")
            a("|---|---|---|---|")
            for k in sorted(w):
                ww = w[k]
                a(f"| {k} | `{ww.get('from')}` | `{ww.get('to')}` | "
                  f"{', '.join(ww.get('shared_keys') or [])} |")
            a("")
        extra = []
        for eid, d in events["captured"].items():
            if d.get("fault_id") == fid and eid not in ids and d.get("kind") != "inj":
                extra.append(d)
        extra.sort(key=lambda d: int(d.get("tick") or 0))
        if extra:
            a("该 fault 的路径外生命周期/检测事件（仅转录 kind 白名单 "
              "inj/errant_commit/store_not_retired/squash_discarded/chain_end；"
              "其余 kind 的全量计数见第 5 节；这些事件未计入层边）：")
            a("")
            a("| event_id | parent_event_id | tick | kind | detection | contained | outcome | containment |")
            a("|---|---|---|---|---|---|---|---|")
            for d in extra:
                a(f"| {d.get('event_id')} | {d.get('parent_event_id') or '—'} | "
                  f"{d.get('tick')} | `{d.get('kind')}` | {d.get('detection_layer') or '—'} | "
                  f"{d.get('contained') or '—'} | {d.get('outcome') or '—'} | "
                  f"{d.get('containment_layer') or '—'}:{d.get('containment_reason') or '—'} |")
            a("")
    # consumer summary
    cs = chain.get("consumer_summary") or []
    if isinstance(cs, list) and cs:
        a("### consumer summary（原始 `CONSUMER-SUMMARY` 字段）")
        a("")
        a("| fault | source_id | emitted | suppressed | logical total | by_outcome | by_kind | first_tick | last_tick |")
        a("|---|---|---|---|---|---|---|---|---|")
        for c in cs:
            logical = (int(c.get("emitted_consumer_count", 0)) +
                       int(c.get("suppressed_consumer_count", 0)))
            a(f"| {c.get('fault_id')} | `{c.get('source_id')}` | {c.get('emitted_consumer_count')} | "
              f"{c.get('suppressed_consumer_count')} | {logical} | `{c.get('by_outcome')}` | "
              f"`{c.get('by_kind')}` | {c.get('first_tick')} | {c.get('last_tick')} |")
        a("")
        acc = chain.get("consumer_summary_accounting") or {}
        a(f"accounting：emitted=`{acc.get('emitted')}` suppressed=`{acc.get('suppressed')}` "
          f"logical_total=`{acc.get('logical_total')}` conservation=`{acc.get('conservation')}`。")
        a("")

    a("## 5. 事件总览")
    a("")
    a("全流按 kind 计数（`prop_evt.txt.gz` 解析所得；与 `chain_report.event_count` 对照）：")
    a("")
    a("| kind | count |")
    a("|---|---|")
    for k in sorted(events["kind_counts"], key=lambda x: (-events["kind_counts"][x], x)):
        a(f"| `{k}` | {events['kind_counts'][k]} |")
    a("")
    a(f"合计 `{events['count']}` 条；`chain_report.event_count` = `{chain.get('event_count')}`；"
      f"非单调 tick 计数 = `{events['nonmonotonic_tick']}`（0 表示按流顺序单调不减）。")
    a("")

    a("## 6. 原始证据与哈希")
    a("")
    a("| 证据 | 路径 | SHA-256 |")
    a("|---|---|---|")
    for key, p in s["paths"].items():
        if os.path.isfile(p):
            a(f"| {key} | `{p}` | `{ev.sha256(p)}` |")
    a("")
    a(f"事件流字节数（gzip）：{os.path.getsize(s['paths']['prop_evt'])}；"
      f"prop_trace 字节数：{os.path.getsize(s['paths']['prop_trace'])}。")
    a("")

    a("## 7. 运行规模与可复现命令")
    a("")
    a("| 统计 | 值 |")
    a("|---|---|")
    for k in ("simSeconds", "simTicks", "hostSeconds", "simInsts", "hostInstRate"):
        if k in st["stats"]:
            a(f"| {k} | `{st['stats'][k]}` |")
    if "board.processor.cores.core.numCycles" in st["stats"]:
        a(f"| numCycles | `{st['stats']['board.processor.cores.core.numCycles']}` |")
    a("")
    a("```bash")
    a(man.get("command", "n/a"))
    a("```")
    a("")
    if trigger:
        a(f"触发行：tier=`{trigger['tier']}` attempted=`{trigger['attempted']}` "
          f"eligible=`{trigger['eligible']}` injected=`{trigger['injected']}` "
          f"first_eligible_tick=`{trigger['first_eligible_tick']}` "
          f"last_eligible_tick=`{trigger['last_eligible_tick']}`。")
        a("")
    if st["runout"].get("segv"):
        a(f"guest 退出：`{st['runout']['segv']}`。")
        a("")

    a("## 8. 诚实边界")
    a("")
    a(f"- 整体 `terminal={chain.get('terminal')}` / `provable_to={chain.get('provable_to')}` "
      "取自该 seed 的 `chain_report.json`；逐 fault 的已证明/缺失层边见第 2 节表，"
      "文档不把某个 fault 的 L5 结果外推到其它 fault。")
    a("- `chain_end` 只是生命周期标记，从不作为 L5 证据；路径之外的 errant_commit、"
      "store_not_retired、squash_discarded 等事件逐条转录，但不计入 `edges`。")
    a("- oracle 结局来自工作负载/guest 退出判据，链模型终局来自事件流判据；"
      "两者不一致时并列记录、互不改写。")
    a("- 被 suppress 的 consumer 只出现在 `CONSUMER-SUMMARY` 计数中（原始流不逐条发出），"
      "本 doc 如实记录 emitted/suppressed/logical total，不把 suppressed 当作已观察事件。")
    a("- 全流未逐行转录（LSQFwd 事件量级 1e5–1e6）；本 doc 以全流 SHA-256 + kind census + "
      "每 fault 规范路径保证可核对性。")
    a("- 同一 RunID/seed 的旧截断证据保留在原目录，未被删除；本 seed 使用独立目录与 manifest。")
    a("")

    text = "\n".join(L) + "\n"
    outdir = os.path.join(STAGE, run_id)
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{run_id}-seed{seed}.md")
    with open(outpath, "w") as f:
        f.write(text)
    return outpath, len(text)


def atomic_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dst), prefix=".tmp-w1doc-", text=True)
    os.close(fd)
    try:
        shutil.copyfile(src, tmp)
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", default=[])
    ap.add_argument("--stage", default=DEFAULT_STAGE)
    ap.add_argument("--only", action="append", default=[],
                    help="RUNID:SEED filter (repeatable)")
    ap.add_argument("--deploy", action="store_true")
    args = ap.parse_args()
    global STAGE
    STAGE = args.stage
    roots = args.root or ev.discover_roots()
    only = set(args.only)
    written = []
    for root in roots:
        try:
            man = json.load(open(os.path.join(root, "manifest.json")))
        except Exception as e:
            print("SKIP", root, repr(e))
            continue
        key = f"{man.get('run_id')}:{man.get('seed')}"
        if only and key not in only:
            continue
        out, size = generate(root)
        written.append((key, out, size))
        print(f"WROTE {out} ({size} bytes)")
        if args.deploy:
            dst = os.path.join(DOCS_ROOT, man["run_id"],
                               f"{man['run_id']}-seed{man['seed']}.md")
            atomic_copy(out, dst)
            print("DEPLOYED", dst)
    print(f"generated {len(written)} docs into {STAGE}")


if __name__ == "__main__":
    main()
