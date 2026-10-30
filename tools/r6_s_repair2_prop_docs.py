#!/usr/bin/env python3
"""[R6-S-REPAIR2] Eight-chapter propagation documents for the 33 repaired seeds.

Reads ONLY each seed's own evidence under
  /home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2c/<RunID>_s<N>/
and writes
  runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seed<N>.md

It NEVER touches the 39 frozen S documents (the 11 target RunIDs here are
S01-F0-W5, S02-F0-W5, S03-F5-W5, S03-F5-W10, S08-F0-W5, S09-F0-W5,
S10-F0-W5, S10-F0-W9, S10-F5-W5, S10-F5-W9, S11-F0-W5; S01/S02/S08/S09
already have frozen docs from the earlier round and are intentionally
rewritten here because their configuration changed: new F0 span / new
binary / new terminal semantics; the old docs are preserved in git history
and the old evidence root).

Every value is read from that seed's own stream; unqualified seeds are
refused loudly (no fabricated docs).

Usage: python3 tools/r6_s_repair2_prop_docs.py [--check]
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS = Path("/home/sdc/gem5-fi-ding/runs/lsu")
EVID = RUNS / "r6_s_repair2c"
OUT = REPO / "runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
RIDS = [
    "S01-F0-W5", "S02-F0-W5", "S03-F5-W5", "S03-F5-W10",
    "S08-F0-W5", "S09-F0-W5",
    "S10-F0-W5", "S10-F0-W9", "S10-F5-W5", "S10-F5-W9",
    "S11-F0-W5",
]
SEEDS = [1, 2, 3]

ROLE = {
    "inj": "L0 故障注入",
    "addr_form": "L1 地址/尺寸形成",
    "sq_entry": "L1 生产 store 的 SQ 表项（转发源）",
    "lsq_fwd": "L2 store→load 转发决策/传输",
    "mem_req": "L2 请求创建",
    "resp": "L3 数据响应",
    "sq_execute": "L3 store 执行",
    "sq_complete": "L3 store 完成",
    "taint_reg": "L4 污点进入目的寄存器",
    "consumer": "L4 下游消费者",
    "errant_commit": "L5 错误提交（逃逸）",
    "squash_discarded": "L4 检测并 squash 丢弃",
    "arch_translation_fault": "L2 真实交付的翻译异常",
    "ssit_corrupt": "L1 SSIT 字段被替换",
    "ssit_consult": "L2 依赖预测查询读取污染 SSIT",
    "ssit_no_effect": "L2 查询到污染状态但预测未改变（真实含住）",
    "ssit_dep_effective": "L3 错误依赖预测在 issue 时生效",
    "ssit_violation": "L4 真实 memory-order violation",
    "ssit_epoch_clear": "L1 条目在使用前被覆盖/epoch 清除（含住）",
    "request_suppressed": "L2 请求形成被空 byte-enable 抑制",
    "store_lost_contained": "L3 store 完成但无任何内存事务（含住）",
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
    if not path.exists():
        return ev
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
        return []
    return ev


def load(rid, seed):
    outdir = EVID / f"{rid}_s{seed}"
    rdir = outdir / rid
    seed_dir = rdir / f"seed{seed}"
    rec = {"rid": rid, "seed": seed, "outdir": outdir, "rdir": rdir,
           "seed_dir": seed_dir}
    try:
        rec["manifest"] = json.loads((outdir / "manifest.json").read_text())
        rec["chain"] = json.loads((rdir / "chain_report.json").read_text())
        rec["cell"] = json.loads((rdir / "cell_results.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        rec["error"] = str(exc)
        rec["qualified"] = False
        return rec
    ev_path = seed_dir / "prop_evt.txt.gz"
    rec["ev_path"] = ev_path
    rec["events"] = read_events(ev_path)
    rec["done"] = (outdir / ".done").exists()
    rec["runout"] = (seed_dir / "run.out").read_text(errors="replace")
    rec["inj_text"] = ""
    for name in ("lsq_fwd_injections.log", "addrpath_injections.log"):
        p = seed_dir / name
        if p.exists():
            rec["inj_text"] = p.read_text(errors="replace")
            rec["inj_log_name"] = name
            rec["inj_log_path"] = p
            break
    rec.setdefault("inj_log_name", "n/a")
    rec["sample"] = (rec["chain"].get("samples") or [{}])[0]
    faults = rec["sample"].get("faults") or {}
    rec["fid"] = next(iter(faults.keys()), "")
    rec["fault"] = (max(faults.values(), key=lambda f: f.get("event_count", 0))
                    if faults else {})
    rec["cev"] = [e for e in rec["events"] if e.get("fault_id") == rec["fid"]]
    adm = rec["sample"].get("admission") or {}
    rec["qualified"] = bool(
        rec["done"] and rec["sample"].get("admitted")
        and rec["sample"].get("certified")
        and not rec["sample"].get("truncated")
        and not rec["sample"].get("evidence_truncated")
        and rec["sample"].get("oracle_outcome") not in ("Timeout", "Hang")
        and rec["cev"] and not adm.get("violations"))
    return rec


def field(e, key, dash="—"):
    v = e.get(key, "")
    return v if v not in ("", None) else dash


def layer(e):
    dl = e.get("detection_layer", "")
    if dl and dl not in ("None", "none", "Unknown", "unknown"):
        return dl
    try:
        sys.path.insert(0, str(REPO / "tools"))
        import lsu_prop_fields as P
        return P.KIND_LAYER.get(e.get("kind", ""), "—")
    except Exception:
        return "—"


def event_row(e):
    return ("| {eid} | {kind} | {layer} | {parent} | {tick} | {corr} | "
            "{field} | {before} | {after} | {state} | {contained} | "
            "{outcome} |").format(
        eid=field(e, "event_id"), kind=field(e, "kind"),
        layer=layer(e), parent=field(e, "parent_event_id"),
        tick=field(e, "tick"), corr=field(e, "corr"),
        field=field(e, "field"),
        before=field(e, "before"), after=field(e, "after"),
        state=(field(e, "state_before") + "→" + field(e, "state_after")
               if e.get("state_before") or e.get("state_after")
               else field(e, "state_after")),
        contained=field(e, "contained"), outcome=field(e, "outcome"))


def guest_hash(runout):
    for ln in runout.splitlines():
        s = ln.strip()
        if len(s) == 16 and all(c in "0123456789abcdef" for c in s):
            return s
    return "n/a"


def cmdline(runout):
    for ln in runout.splitlines():
        if ln.startswith("command line:"):
            return ln[len("command line:"):].strip()
    return "n/a"


def trigger(runout):
    for ln in runout.splitlines():
        if ln.startswith("CHAOS_LSU_TRIGGER:"):
            return ln
    return "n/a"


def detect(runout):
    for ln in runout.splitlines():
        if ln.startswith("CHAOS_DETECT:"):
            return ln
    return "n/a"


def render(rec):
    rid, seed = rec["rid"], rec["seed"]
    man = rec["manifest"]
    s = rec["sample"]
    f = rec["fault"]
    evs = rec["cev"]
    statsp = rec["seed_dir"] / "stats.txt"
    stats = ""
    if statsp.exists():
        for ln in statsp.read_text(errors="replace").splitlines():
            if ln.strip().startswith(("simTicks", "simInsts",
                                      "board.processor.cores.core.numCycles")):
                stats += "- `" + ln.strip() + "`\n"
    infl = rec.get("inj_log_path")
    inj_event = next((e for e in evs if e.get("kind") == "inj"), {})
    # The chain report stores the admission verdict but not the option-2
    # bundle; derive it from THIS seed's own events with the authoritative
    # checker (same function the gate uses). Never invent a layer.
    cont = {}
    try:
        sys.path.insert(0, str(REPO / "tools"))
        import lsu_chain_check as CC
        cont = CC.containment_from_events(rec["events"], rid) or {}
    except Exception:
        cont = {}
    lines = []
    lines.append(f"# {rid} seed{seed} 传播链（R6-S-REPAIR2）\n")
    lines.append("> 本文由 `tools/r6_s_repair2_prop_docs.py` 从该 seed 自身的 "
                 "`prop_evt.txt.gz` / `chain_report.json` / `stats.txt` / "
                 "注入日志逐字段生成；未合成任何事件、id、tick 或值。\n")
    lines.append("## 1. 单元与实验定义\n")
    lines.append(f"- RunID：`{rid}`；seed：`{seed}`")
    lines.append(f"- oracle：`{s.get('oracle_outcome')}`；exit_code："
                 f"`{s.get('exit_code')}`")
    lines.append(f"- 二进制：`{man.get('binary_path', 'n/a')}`")
    lines.append(f"- 二进制 SHA-256：`{man.get('binary_sha256', 'n/a')}`")
    lines.append(f"- 源码 HEAD：`{man.get('binary_source_head', 'n/a')}`")
    lines.append(f"- 事件数：`{s.get('event_count')}`；terminal："
                 f"`{s.get('terminal')}`；provable_to：`{s.get('provable_to')}`")
    lines.append(f"- admitted：`{s.get('admitted')}`；certified："
                 f"`{s.get('certified')}`；truncated：`{s.get('truncated')}`")
    lines.append(f"- 证据目录：`{rec['outdir']}`\n")

    lines.append("## 2. 注入位置、地址、原值/新值与掩码\n")
    inj_lines = [ln for ln in rec["inj_text"].splitlines()
                 if ln.startswith("Tick: ") or ln.startswith("Cycle: ")]
    if inj_lines:
        lines.append("```")
        lines.extend(inj_lines[-4:])
        lines.append("```")
    lines.append(f"- 注入事件：`event_id={inj_event.get('event_id', 'n/a')}`，"
                 f"tick=`{inj_event.get('tick', 'n/a')}`，"
                 f"va=`{inj_event.get('va', 'n/a')}`，"
                 f"field=`{inj_event.get('field', 'n/a')}`，"
                 f"before=`{inj_event.get('before', 'n/a')}`，"
                 f"after=`{inj_event.get('after', 'n/a')}`，"
                 f"corr=`{inj_event.get('corr', 'n/a')}`")
    lines.append(f"- 触发摘要：`{trigger(rec['runout'])}`")
    lines.append(f"- 检测摘要：`{detect(rec['runout'])}`\n")

    lines.append("## 3. 事件总览（该 fault 的完整事件流）\n")
    lines.append("| event_id | kind | layer | parent | tick | corr | field | "
                 "before | after | state | contained | outcome |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for e in evs:
        lines.append(event_row(e))
    lines.append("")

    lines.append("## 4. 逐步传播语义\n")
    for e in evs:
        k = e.get("kind", "")
        lines.append(
            f"- **event {e.get('event_id')} · {k}（{ROLE.get(k, '家族事件')}）**："
            f"tick={e.get('tick', 'n/a')}，parent="
            f"{e.get('parent_event_id') or '（根）'}，corr={e.get('corr', '—')}，"
            f"field={e.get('field', '—')}，before={e.get('before', '—')}，"
            f"after={e.get('after', '—')}，state="
            f"{e.get('state_before', '—')}→{e.get('state_after', '—')}，"
            f"contained={e.get('contained', '—')}，"
            f"outcome={e.get('outcome', '—')}。")
    lines.append("")

    lines.append("## 5. 终局判定（权威 checker）\n")
    lines.append(f"- 样本级 judge：terminal=`{s.get('terminal')}`，"
                 f"provable_to=`{s.get('provable_to')}`，"
                 f"admitted=`{s.get('admitted')}`，"
                 f"certified=`{s.get('certified')}`")
    faults = s.get("faults") or {}
    if len(faults) > 1:
        lines.append("- 多 fault 样本：准入按 checker 的 escape-first 规则选择"
                     "代表 fault；下表列出全部 fault 的各自终局（不合并、"
                     "不跨 fault 拼接）：")
        for fid, fr in faults.items():
            lines.append(f"  - fault `{fid}`：terminal="
                         f"`{fr.get('terminal')}`，provable_to="
                         f"`{fr.get('provable_to')}`，event_count="
                         f"`{fr.get('event_count')}`")
    lines.append(f"- 叙述 fault `{rec['fid']}`（本 seed 事件数最多者）："
                 f"terminal=`{f.get('terminal')}`，provable_to="
                 f"`{f.get('provable_to')}`，beyond=`{f.get('beyond')}`，"
                 f"event_count=`{f.get('event_count')}`")
    if cont:
        lines.append(f"- containment：layer=`{cont.get('layer')}`，"
                     f"later_layers_N/A=`{cont.get('na_layers')}`，"
                     f"reason=`{cont.get('reason')}`")
        lines.append(f"- containment metrics：`{cont.get('metrics')}`")
    else:
        lines.append("- containment：`n/a`（链路以 full/其他合法终局收口，"
                     "或没有显式含住证据）")
    lines.append(f"- admission violations："
                 f"`{(s.get('admission') or {}).get('violations', [])}`\n")

    lines.append("## 6. 对 guest / 程序的实际表现\n")
    lines.append(f"- run.out 末行：`{rec['runout'].strip().splitlines()[-1] if rec['runout'].strip() else 'n/a'}`")
    lines.append(f"- guest checksum：`{guest_hash(rec['runout'])}`")
    if stats:
        lines.append("- stats：\n" + stats)
    else:
        lines.append("- stats：`n/a`（文件不存在）")
    lines.append("")

    lines.append("## 7. 证据路径与 SHA-256\n")
    files = [rec["ev_path"], rec["rdir"] / "chain_report.json",
             rec["seed_dir"] / "chain_report.json", statsp,
             rec["seed_dir"] / "run.out", rec["outdir"] / "manifest.json"]
    if infl:
        files.append(infl)
    for p in files:
        if p and p.exists():
            lines.append(f"- `{p}`：`{sha256(p)}`")
        else:
            lines.append(f"- `{p}`：`n/a`（不存在）")
    lines.append("")

    lines.append("## 8. 可复现命令与诚实边界\n")
    lines.append("```bash")
    lines.append(f"LSU_GEM5_BIN={man.get('binary_path', '<binary>')} \\")
    lines.append("  python3 tools/lsu_campaign.py --matrix "
                 "/home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \\")
    lines.append(f"  --outdir {rec['outdir']} --cells {rid} --phase trial "
                 f"--seed-start {seed} --max-seeds-per-cell 1 "
                 "--max-parallel 1 --timeout 3600")
    lines.append("```")
    lines.append(f"- 完整 gem5 命令行：`{cmdline(rec['runout'])}`")
    lines.append("- 诚实边界：本链只包含该 seed 自己的事件；L0/L1/L2/... "
                 "的层级由真实 kind/字段映射；不含任何为通过准入而补造的事件。"
                 " `chain_end` 是生命周期标记，从不充当 L5 证据。")
    if rid.startswith("S10"):
        lines.append("- S10 实测路径：污染 SSIT 被真实 consult 读取，"
                     "counterfactual 预测与 actual 预测相等（before==after），"
                     "因此终局是 L2 detected containment；L3/L4/L5 为 N/A，"
                     "没有伪造 violation/replay/commit。")
    if rid == "S11-F0-W5":
        lines.append("- S11-F0-W5 实测路径：PRE hook 把 size 置 0，"
                     "addReq 不创建 Request；request_suppressed 是真实的 "
                     "L2 观测，store_lost_contained 是真实的 L3 含住；"
                     "L4/L5 为 N/A，没有伪造 mem_req/consumer。")
    if rid == "S11-F0-W6":
        lines.append("- S11-F0-W6 不生成文档：下游 0x18 Crash 无真实归因桥，"
                     "admitted=False。")
    if rid.startswith("S03-F5"):
        lines.append("- S03-F5 实测路径：errant commit 后 guest 调用超大 mmap；"
                     "gem5 的 VMA 断言已修为 guest-visible ENOMEM，"
                     "因此 stats/gzip 完整、链路以真实 L5 收口。")
    lines.append("")
    return "\n".join(lines) + "\n"


def main():
    check = "--check" in sys.argv
    bad = []
    written = 0
    for rid in RIDS:
        for seed in SEEDS:
            rec = load(rid, seed)
            if not rec.get("qualified"):
                bad.append(f"{rid} s{seed}: {rec.get('error') or 'not qualified'}")
                continue
            out = OUT / rid / f"{rid}-seed{seed}.md"
            if check:
                print(f"OK {rid} seed{seed}: events={len(rec['cev'])} "
                      f"terminal={rec['fault'].get('terminal')} "
                      f"provable={rec['fault'].get('provable_to')}")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(rec))
            written += 1
            print(f"WROTE {out}")
    if bad:
        print("REFUSED:")
        for b in bad:
            print("  " + b)
        return 1
    print(f"{'CHECK' if check else 'WROTE'} {written} docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
