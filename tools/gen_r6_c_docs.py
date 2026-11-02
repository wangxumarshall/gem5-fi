#!/usr/bin/env python3
"""Generate per-seed R6-C (L1d Cache / CHAOSCache) propagation docs.

Only the seed's own stream/report files are read.  The full event stream is
never transcribed; instead each fault's canonical path is transcribed and the
whole-stream census + SHA are recorded.

Writes into a staging directory; `--deploy` (run only after
audit_r6_c_docs.py reports 0 errors) copies the Markdown atomically.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r6_c_evidence as ev  # noqa: E402

DOCS_ROOT = "/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
DEFAULT_STAGE = "/home/sdc/gem5-fi-ding-cleanup-20261029/R6C_DOCS_STAGE_20261102"
STAGE = DEFAULT_STAGE


def hx(v):
    return f"0x{v}" if v else "—"


def edge_map(fault):
    return {k: v for k, v in (fault.get("edges") or {}).items()
            if not k.endswith("_witness")}


def witnesses(fault):
    return {k: v for k, v in (fault.get("edges") or {}).items()
            if k.endswith("_witness")}


def sample_model(run_id):
    parts = run_id.split("-")
    return (parts[0] if parts else "?"), (parts[1] if len(parts) > 1 else "?")


def parse_hex_addr(text):
    """Event `va`/`pa` are hexadecimal (no 0x prefix)."""
    if text is None or text == "":
        return None
    try:
        return int(text, 16)
    except ValueError:
        return None


def parse_log_addr(text):
    """`cache_injections.log` prints Cache Block Addr in DECIMAL."""
    if text is None or text == "":
        return None
    try:
        return int(text, 10)
    except ValueError:
        return parse_hex_addr(text)


def generate(root):
    s = ev.load_sample(root)
    st = ev.load_streams(s)
    man, cell, chain = s["manifest"], s["cell"], s["chain"]
    run_id, seed = s["run_id"], s["seed"]
    run = (cell.get("runs") or [{}])[0]
    events = st["events"]
    inj_rows = st["inj"]
    funnel = st["runout"]["funnel"] or {}
    faults = chain.get("faults") or {}
    model, freq = sample_model(run_id)
    workload = run_id.split("-")[2] if run_id.count("-") >= 2 else "?"

    # fault id -> injection log row: join by injected tick + block address.
    inj_by_fid = {}
    for fid in sorted(faults, key=lambda x: int(x)):
        ids = st["path_ids"].get(fid) or []
        inj_evt = None
        for eid in ids:
            d = events["captured"].get(eid)
            if d and d.get("kind") == "inj":
                inj_evt = d
                break
        if inj_evt is None:
            for eid, d in events["captured"].items():
                if d.get("kind") == "inj" and d.get("fault_id") == fid:
                    inj_evt = d
                    break
        if inj_evt is None:
            continue
        evt_tick = inj_evt.get("tick")
        evt_addr = parse_hex_addr(inj_evt.get("va"))
        for row in inj_rows:
            if (row.get("Tick") == evt_tick
                    and parse_log_addr(row.get("Cache Block Addr")) == evt_addr):
                inj_by_fid[fid] = row
                break

    L = []
    a = L.append
    a(f"# {run_id} seed{seed} — L1d Cache 传播路径（真实事件流）")
    a("")
    a("> 本 doc 只转录该 seed 自己的 `prop_evt.txt.gz`、`chain_report.json`、"
      "`cell_results.json`、`stats.txt`、`run.out`、`cache_injections.log` 与 "
      "`manifest.json`；未修改原始流，未跨 seed 复用数值，未把推测写成事件事实。")
    a("")
    a("## 1. 样本身份")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    a(f"| RunID | `{run_id}` |")
    a(f"| seed | `{seed}` |")
    a(f"| model | `{model}`（CHAOSCache L1d 数据/标签/状态域） |")
    a(f"| frequency | `{freq}` |")
    a(f"| workload | `{workload}` |")
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
      f"injected=`{funnel.get('injected')}` |")
    a(f"| cell admission_status | `{cell.get('admission_status')}` |")
    a(f"| cell outcome | `{run.get('outcome')}` |")
    a(f"| cell activated / attempted | `{run.get('activated')}` / `{run.get('attempted')}` |")
    a("")
    a("### 逐 fault 判定（全部取自该 seed 的 `chain_report.json`）")
    a("")
    a("| fault | 注入 Tick | Cache Block Addr | 已证明层边 | 缺失层边 | terminal | provable_to |")
    a("|---|---|---|---|---|---|---|")
    for fid in sorted(faults, key=lambda x: int(x)):
        f = faults[fid]
        e = edge_map(f)
        proven = [k for k, v in e.items() if v == "proven"]
        missing = [k for k, v in e.items() if v != "proven"]
        row = inj_by_fid.get(fid, {})
        a(f"| {fid} | `{row.get('Tick', '—')}` | `{row.get('Cache Block Addr', '—')}` | "
          f"{', '.join(proven) or '—'} | {', '.join(missing) or '—'} | "
          f"`{f.get('terminal')}` | `{f.get('provable_to')}` |")
    a("")
    a("说明：整体 `terminal/provable_to` 是 `chain_report.json` 的 run 级汇总；"
      "逐 fault 的层边与终局以上表为准，二者不一致时不改写任何一侧。")
    a("")

    a("## 3. 真实注入清单")
    a("")
    a(f"`cache_injections.log` 共 {len(inj_rows)} 条注入记录；funnel 记录 "
      f"injected={funnel.get('injected')}。下表直接转录日志字段，不做换算。")
    a("")
    a("| fault | Tick | Cache Block Addr | Byte Offset | FaultType | Mask |")
    a("|---|---|---|---|---|---|")
    fid_by_row = {}
    for fid, row in inj_by_fid.items():
        fid_by_row[(row.get("Tick"), parse_log_addr(row.get("Cache Block Addr")))] = fid
    for row in inj_rows:
        fid = fid_by_row.get(
            (row.get("Tick"), parse_log_addr(row.get("Cache Block Addr"))), "—")
        a(f"| {fid} | `{row.get('Tick')}` | `{row.get('Cache Block Addr')}` | "
          f"`{row.get('Byte Offset')}` | `{row.get('FaultType')}` | `{row.get('Mask')}` |")
    a("")

    a("## 4. 传播过程（逐 fault 的规范路径）")
    a("")
    a("规范路径 = `chain_report.json` 的 `faults[<id>].path_event_ids`；"
      "层号由事件 kind 映射给出，并与 `edges` witness 的 from/to 交叉核对。"
      "路径之外的原始事件仍计入第 5 节 census 与哈希，但不被抬升为层边。")
    a("")
    for fid in sorted(faults, key=lambda x: int(x)):
        f = faults[fid]
        ids = st["path_ids"][fid]
        row = inj_by_fid.get(fid, {})
        a(f"### fault {fid}")
        a("")
        a(f"- 注入：Tick `{row.get('Tick', '—')}`，Cache Block Addr "
          f"`{row.get('Cache Block Addr', '—')}`，Byte Offset "
          f"`{row.get('Byte Offset', '—')}`，FaultType `{row.get('FaultType', '—')}`，"
          f"Mask `{row.get('Mask', '—')}`。")
        pas = []
        vas = []
        for eid in ids:
            d = events["captured"].get(eid, {})
            if d.get("pa") and d["pa"] not in pas:
                pas.append(d["pa"])
            if d.get("va") and d["va"] not in vas:
                vas.append(d["va"])
        if pas:
            pa_txt = "、".join(f"`0x{p}`" for p in pas)
            pfn_txt = "、".join(
                f"`0x{int(p, 16) >> 12:x}`（由 PA 推导）" for p in pas)
        else:
            pa_txt = "`n/a`（规范路径事件 `pa=` 为空，未记录物理地址）"
            pfn_txt = "`n/a`（事件域无 pfn 字段，且 PA 为空）"
        va_txt = "、".join(f"`0x{v}`" for v in vas) if vas else "`n/a`"
        a(f"- 地址：VA {va_txt}；PA {pa_txt}；PFN {pfn_txt}。"
          "注意：cache 族以物理 block 地址广播归因，`va` 为访问地址，"
          "注入点的 block 地址即 `cache_injections.log` 的 Cache Block Addr。")
        a(f"- 层边：{', '.join(f'{k}={v}' for k, v in edge_map(f).items()) or '—'}。")
        a("")
        a("| 位置 | 层 | event_id | parent_event_id | tick | cycle | kind | request_id | dyn_inst_seq | va | pa | before → after | state_before → state_after | detection/containment |")
        a("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for i, eid in enumerate(ids):
            d = events["captured"].get(eid, {})
            layer = ev.layer_of(d.get("kind", ""), d)
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
            a(f"| {i} | {layer} | {eid} | {d.get('parent_event_id') or '—'} | {d.get('tick')} | "
              f"{d.get('cycle')} | `{d.get('kind')}` | {d.get('request_id') or '—'} | "
              f"{d.get('dyn_inst_seq') or '—'} | {hx(d.get('va'))} | {hx(d.get('pa'))} | "
              f"{change or '—'} | {state or '—'} | {'；'.join(dc) or '—'} |")
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
              "errant_commit/store_not_retired/squash_discarded/request_fork/chain_end；"
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
    if st["runout"].get("segv"):
        a(f"guest 退出：`{st['runout']['segv']}`。")
        a("")
    if st["runout"].get("detect_lines"):
        a("硬件检测信号（`CHAOS_DETECT`）：")
        a("")
        for line in st["runout"]["detect_lines"]:
            a(f"- `{line}`")
        a("")

    a("## 8. 诚实边界")
    a("")
    a(f"- 整体 `terminal={chain.get('terminal')}` / `provable_to={chain.get('provable_to')}` "
      "取自该 seed 的 `chain_report.json`；逐 fault 的已证明/缺失层边见第 2 节表，"
      "文档不把某个 fault 的 L5 结果外推到其它 fault。")
    a("- `chain_end` 只是生命周期标记，从不作为 L5 证据；路径之外的 errant_commit、"
      "store_not_retired、squash_discarded、request_fork 等事件逐条转录，但不计入 `edges`。")
    a("- oracle 结局来自工作负载/guest 退出判据，链模型终局来自事件流判据；"
      "两者不一致时并列记录、互不改写。")
    a("- cache 族以物理 block 地址广播（`corr=addr_fallback`）归因；"
      "同一被污染 line 的多个访问者由显式 `request_fork` 桥连接。"
      "`va` 与 `pa` 都按原始事件转录，缺失处写 `n/a`，不推导不存在的地址。")
    a("- 被 suppress 的 consumer 只出现在 `CONSUMER-SUMMARY` 计数中（原始流不逐条发出），"
      "本 doc 如实记录 emitted/suppressed/logical total，不把 suppressed 当作已观察事件。")
    a("- 全流未逐行转录；本 doc 以全流 SHA-256 + kind census + 每 fault 规范路径保证可核对性。")
    a("- 同一 RunID/seed 的旧截断证据保留在原目录，未被删除；本 seed 使用独立目录与 manifest。")
    a("")

    text = "\n".join(L) + "\n"
    outdir = os.path.join(STAGE, run_id)
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{run_id}-seed{seed}.md")
    with open(outpath, "w") as fh:
        fh.write(text)
    return outpath, len(text)


def atomic_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dst), prefix=".tmp-cdoc-", text=True)
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
    roots = args.root or [ev.DEFAULT_ROOT]
    only = set(args.only)
    written = []
    for root in roots:
        for seed_root, run_id, seed in ev.discover_seeds(root):
            key = f"{run_id}:{seed}"
            if only and key not in only:
                continue
            try:
                out, size = generate(seed_root)
            except Exception as e:
                print("SKIP", seed_root, repr(e))
                continue
            written.append((key, out, size))
            print(f"WROTE {out} ({size} bytes)")
            if args.deploy:
                dst = os.path.join(DOCS_ROOT, run_id, f"{run_id}-seed{seed}.md")
                atomic_copy(out, dst)
                print("DEPLOYED", dst)
    print(f"generated {len(written)} docs into {STAGE}")


if __name__ == "__main__":
    main()
