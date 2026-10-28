#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A4] 逐 seed 完整传播文档（65 旧 + 25 新） / 索引 / 状态 / 去重清单生成器。

只读取真实证据（manifest.json / chain_report.json / prop_evt.txt.gz /
stats.txt / run.out / 注入日志），不合成任何事件、不跨 seed 复用数值。
每个 seed 一篇 `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RUNID>/seed<S>.md`，
叙述按真实事件时间顺序；每个字段都来自该 seed 自己的证据。

用法：
  python3 tools/r6_a3_prop_docs.py            # 生成/刷新
  python3 tools/r6_a3_prop_docs.py --check    # 只打印资格汇总
"""
import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# evidence lives in the main checkout (raw runs); the committed docs/status
# live in THIS worktree (same layout as R6-A3).
RUNS = Path("/home/sdc/gem5-fi-ding/runs/lsu")
REPORTS = REPO / "runs/lsu/r6_reports"
TAG = "_r6a4"          # candidate (R6-A4) evidence
OLD_TAG = "_r6a3"      # previous round (65 qualified samples kept as-is)

# [R6-A4] The 25 rerun samples live in _r6a4 dirs; the other 65 stay in
# _r6a3.  Pick per (RunID, seed) so one document never mixes rounds.
NEW_SAMPLES = {
    ("A01-F1-W3", 2), ("A01-F2-W3", 2),
    ("A01-F2-W9", 1), ("A01-F2-W9", 2), ("A01-F2-W9", 3),
    ("A02-F2-W9", 1), ("A02-F2-W9", 2), ("A02-F2-W9", 3),
    ("A04-F2-W3", 1), ("A04-F2-W3", 3), ("A04-F2-W0", 1), ("A04-F2-W0", 3),
    ("A05-F2-W3", 1), ("A05-F2-W3", 2), ("A05-F2-W3", 3),
    ("A06-F2-W3", 3), ("A06-F2-W5", 3),
    ("A08-F2-W3", 1), ("A08-F2-W3", 2), ("A08-F2-W3", 3),
    ("A08-F2-W5", 1), ("A08-F2-W5", 2), ("A08-F2-W5", 3),
    ("A07-F0-W3", 1), ("A07-F0-W3", 2),
}
OUT_ROOT = REPO / "runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"

RUNIDS = """A01-F0-W3 A01-F0-W9 A01-F1-W3 A01-F1-W9 A01-F2-W3 A01-F2-W9
A02-F0-W3 A02-F0-W9 A02-F2-W3 A02-F2-W9
A03-F5-W3 A03-F5-W10
A04-F0-W3 A04-F0-W0 A04-F2-W3 A04-F2-W0
A05-F0-W3 A05-F2-W3
A06-F0-W3 A06-F0-W5 A06-F2-W3 A06-F2-W5
A07-F0-W3 A07-F0-W5 A07-F4-W3 A07-F4-W5
A08-F0-W3 A08-F0-W5 A08-F2-W3 A08-F2-W5""".split()
SEEDS = [1, 2, 3]

LAYER_OF_KIND = {
    "inj": "L0", "addr_form": "L1", "lsq_push": "L1", "mem_req": "L2",
    "lsq_sendfrag": "L2", "tlb_translate": "L2", "tlb_fault": "L2",
    "tlb_hit": "L2", "arch_translation_fault": "L2",
    "sq_execute": "L3", "sq_writeback": "L3", "lq_read": "L3",
    "resp": "L3", "sq_complete": "L3", "lq_complete": "L3",
    "taint_reg": "L4", "squash_discarded": "L4", "store_not_retired": "L4",
    "errant_commit": "L5", "chain_end": "L5",
    # [R6-A4] A07-b ready-delay real lifecycle (timing-only; L1 observation at
    # resume, terminal at L4 squash/discard or L5 transparent retirement).
    "ready_delay_resume": "L1", "ready_delay_squashed": "L4",
    "ready_delay_discarded": "L4", "ready_delay_retired": "L5",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_events(path):
    """流式读取 prop_evt（gz 或纯文本），返回事件字典列表。"""
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
    except EOFError:
        # in-flight / killed sample: keep the flushed prefix (honest, the
        # truncated flag is reported separately)
        pass
    return ev


def chain_events_for(events, fault_id):
    return [e for e in events
            if e.get("fault_id") == fault_id and e.get("event_id") != "0"
            or (e.get("fault_id") == fault_id and e.get("kind") == "inj")]


def fmt(e):
    return ("| {kind} | {eid} | {par} | {tick} | {rid} | {va} | {pa} | "
            "{layer} | {outcome} | {corr} |").format(
        kind=e.get("kind", ""), eid=e.get("event_id", ""),
        par=e.get("parent_event_id", ""), tick=e.get("tick", ""),
        rid=e.get("request_id", ""), va=e.get("va", ""), pa=e.get("pa", ""),
        layer=e.get("detection_layer", ""), outcome=e.get("outcome", ""),
        corr=e.get("corr", ""))


def inj_lines(outdir, rdir):
    """该 seed 目录里的注入日志（按模型名匹配），返回 [(file,line)]。"""
    res = []
    for p in sorted(outdir.rglob("*injections.log")):
        try:
            with open(p, errors="replace") as f:
                for line in f:
                    if line.startswith("Tick: "):
                        res.append((p, line.rstrip("\n")))
        except OSError:
            pass
    return res


def load_sample(outdir, rid, seed):
    rep = outdir / rid / "chain_report.json"
    if not rep.exists():
        return None
    d = json.loads(rep.read_text())
    for s in d.get("samples", []):
        if str(s.get("sample_run_id")) == "s%d" % seed or \
                s.get("seed") == seed:
            return s
    return None


def analyse(rid, seed):
    # [R6-A4] prefer the candidate round for the 25 rerun samples; every other
    # sample keeps its R6-A3 evidence (never rerun, never overwritten).
    tag = TAG if (rid, seed) in NEW_SAMPLES else OLD_TAG
    outdir = RUNS / ("r6_a%s_%s_s%d" % (tag, rid, seed))
    # NEVER fall back to the old round for a rerun sample: its R6-A3 evidence
    # is the known-unqualified NO_FIRE evidence and must not masquerade as
    # this round's result (mixed provenance was the R6-A3 defect class).
    rdir = outdir / rid
    seed_dir = rdir / ("seed%d" % seed)
    man = outdir / "manifest.json"
    rec = {"runid": rid, "seed": seed, "outdir": outdir,
           "seed_dir": seed_dir, "present": outdir.exists()}
    rec["done"] = (outdir / ".done").exists()
    rec["manifest"] = json.loads(man.read_text()) if man.exists() else None
    sample = load_sample(outdir, rid, seed)
    rec["sample"] = sample
    ev_path = seed_dir / "prop_evt.txt.gz"
    if not ev_path.exists():
        ev_path = seed_dir / "prop_evt.txt"
    rec["ev_path"] = ev_path if ev_path.exists() else None
    # never read a cell that is still being written; completed cells only
    rec["events"] = (read_events(ev_path)
                     if (rec["ev_path"] and rec["done"]) else [])
    rec["injections"] = inj_lines(outdir, rdir)
    rec["stats"] = seed_dir / "stats.txt"
    rec["runout"] = seed_dir / "run.out"
    rec["chainrep"] = rdir / "chain_report.json"
    rec["runerr"] = seed_dir / "run.err"

    # 资格判定（工作令第七节）
    s = sample or {}
    faults = (s.get("faults") or {})
    best = None
    for f in faults.values():
        if best is None or f.get("event_count", 0) > best.get("event_count", 0):
            best = f
    rec["fault"] = best or {}
    rec["qualified"] = bool(
        rec["done"] and s and s.get("admitted") and s.get("certified")
        and not s.get("truncated") and not s.get("evidence_truncated")
        and s.get("stream_present", True)
        and s.get("terminal") in ("full", "detected_contained")
        and rec["ev_path"] is not None
        and rec["events"]
        and not (s.get("admission") or {}).get("violations")
    )
    rec["violations"] = (s.get("admission") or {}).get("violations") or []
    return rec


def doc(rec):
    rid, seed = rec["runid"], rec["seed"]
    s = rec["sample"] or {}
    man = rec["manifest"] or {}
    events = rec["events"]
    fault = rec["fault"]
    fid = next(iter((s.get("faults") or {}).keys()), "")
    cev = [e for e in events if e.get("fault_id") == fid]
    cev.sort(key=lambda e: int(e.get("event_id", "0") or 0))
    model, freq, wl = rid.split("-")[0], rid.split("-")[1], rid.split("-")[2]
    model_name = {"A01": "AGU EA 单bit翻转", "A02": "AGU EA 双bit翻转",
                  "A03": "AGU EA bit stuck-at", "A04": "AGU 对象/同页替换",
                  "A05": "AGU 操作数级寻址", "A06": "AGU 访问尺寸/掩码",
                  "A07": "AGU ready 时序", "A08": "AGU 通道/同周期EA互换"
                  }.get(model, model)
    sub = next((l for _p, l in rec["injections"]
                if "submodel=" in l), "")
    inj = next((e for e in cev if e.get("kind") == "inj"), {})
    kinds = [e.get("kind", "") for e in cev]
    last = cev[-1] if cev else {}
    paths = [("prop_evt", rec["ev_path"]), ("stats", rec["stats"]),
             ("run.out", rec["runout"]), ("run.err", rec["runerr"]),
             ("chain_report", rec["chainrep"]),
             ("manifest", rec["outdir"] / "manifest.json")]
    sha_lines = []
    for name, p in paths:
        if p and Path(p).exists():
            sha_lines.append("| %s | `%s` | `%s` |" %
                             (name, p, sha256(p)))
    L = []
    A = L.append
    A("# %s seed%d — 完整传播路径（真实事件时间顺序）\n" % (rid, seed))
    A("## 1. 实验身份与子模型\n")
    A("| 项 | 值 |\n|---|---|")
    A("| RunID | `%s` |" % rid)
    A("| 模型 | %s（%s） |" % (model, model_name))
    A("| 频率档 | %s |" % freq)
    A("| 负载 | %s |" % wl)
    A("| seed | %d（sample_run_id=%s） |" % (seed, s.get("sample_run_id", "")))
    A("| 子模型/注入参数 | %s |" % (sub.replace("|", "/") if sub else "见注入日志"))
    A("| 二进制 | `%s` |" % man.get("binary_path", ""))
    A("| 二进制 SHA-256 | `%s` |" % man.get("binary_sha256", ""))
    A("| 源码 HEAD | `%s` |" % man.get("binary_source_head", ""))
    A("| 命令 | `%s` |" % man.get("cmd", ""))
    A("")
    A("## 2. 故障注入发生在哪里\n")
    if inj:
        A("第一次（也是本样本被选中的）注入事件：`event_id=%s`，tick=%s，"
          "request_id=%s，corr=%s，注入前地址 `before=%s`，注入后地址 "
          "`after=%s`。" % (inj.get("event_id"), inj.get("tick"),
                            inj.get("request_id"), inj.get("corr"),
                            inj.get("before"), inj.get("after")))
    else:
        A("**该样本没有 inj 事件**（流里没有可证注入根）。")
    A("")
    A("注入器日志中该样本的注入行（真实原文，按日志顺序）：\n")
    injlog = [l for _p, l in rec["injections"]]
    if injlog:
        A("```")
        for l in injlog[:4]:
            A(l)
        if len(injlog) > 4:
            A("... (%d more lines in the injection log)" % (len(injlog) - 4))
        A("```")
    else:
        A("（无注入日志行）")
    A("")
    A("## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化\n")
    addrform = next((e for e in cev if e.get("kind") == "addr_form"), {})
    A("- 地址：`%s` → `%s`（来自 inj/addr_form 节点，本 seed 自己的值）。" %
      (addrform.get("before") or inj.get("before"),
       addrform.get("after") or inj.get("after")))
    for _p, l in rec["injections"][:1]:
        for key in ("old_size", "new_size", "old_be", "new_be", "old_ea",
                    "new_ea", "old_base", "new_base", "old_index",
                    "new_index", "old_type", "new_type", "old_shift",
                    "new_shift", "old_cmd", "new_cmd", "expected_channel",
                    "actual_channel", "submodel"):
            i = l.find(key + "=")
            if i >= 0:
                j = l.find(",", i)
                A("- `%s` = `%s`" % (key, l[i + len(key) + 1:j if j > 0 else None]))
    A("")
    A("## 4. 之后依次经过哪些真实部件\n")
    A("事件种类序列（本 seed，fault_id=%s）：`%s`。" %
      (fid, " → ".join(kinds)))
    A("按证据层映射：" + "，".join(
        "%s=%s" % (k, LAYER_OF_KIND.get(k, "?")) for k in kinds) + "。")
    A("")
    A("## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr\n")
    A("| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for e in cev:
        A(fmt(e))
    A("")
    A("## 6. 地址/数据/污点在每层如何变化\n")
    for e in cev:
        if e.get("kind") in ("tlb_translate", "lsq_sendfrag", "mem_req"):
            A("- L2 `%s`：va=%s pa=%s" % (e.get("kind"), e.get("va"),
                                          e.get("pa")))
        elif e.get("kind") == "taint_reg":
            A("- L4 `taint_reg`：%s → %s" % (e.get("before"), e.get("after")))
        elif e.get("kind") == "resp":
            A("- L3 `resp`：va=%s pa=%s（响应回到 LSQ）" %
              (e.get("va"), e.get("pa")))
        elif e.get("kind") in ("sq_complete", "lq_complete"):
            A("- L3 `%s`：state=%s" % (e.get("kind"), e.get("state_after")))
    A("")
    A("## 7. 最终结局\n")
    A("- oracle：`%s`；chain terminal：`%s`；provable_to：`%s`；beyond：`%s`。"
      % (s.get("oracle_outcome"), s.get("terminal"), s.get("provable_to"),
         s.get("beyond") or "—"))
    A("- admitted=%s，certified=%s，violations=%s，truncated=%s，"
      "evidence_truncated=%s，事件数=%s。"
      % (s.get("admitted"), s.get("certified"), rec["violations"] or "[]",
         s.get("truncated"), s.get("evidence_truncated"), s.get("event_count")))
    A("- 事件数：本 seed 流共 %d 条，其中 fault_id=%s 链 %d 条；"
      "最后一条为 `%s`（event_id=%s, tick=%s）。"
      % (len(events), fid, len(cev), last.get("kind"), last.get("event_id"),
         last.get("tick")))
    A("")
    A("## 8. 为什么该结局成立\n")
    edges = fault.get("edges") or {}
    proven = [k for k, v in edges.items() if v == "proven"]
    A("链边证明（本 seed 自己的 fault %s）：已证 `%s`。" %
      (fid, "`, `".join(proven) if proven else "（无）"))
    # [R6-A4] the terminal witness is the real detection/lifecycle event, NOT
    # the exit-callback chain_end.
    wit = None
    for e in reversed(cev):
        if e.get("kind") == "chain_end":
            continue
        if str(e.get("contained", "")).strip() in ("1", "true", "True"):
            wit = e
            break
    if s.get("terminal") in ("full", "detected_contained"):
        A("终局见证事件（本 seed 自己的流）：kind=`%s`，event_id=%s，"
          "parent_event_id=%s，tick=%s，detection_layer=%s，outcome=%s，"
          "contained=%s，corr=%s。"
          % ((wit or last).get("kind"), (wit or last).get("event_id"),
             (wit or last).get("parent_event_id"),
             (wit or last).get("tick"),
             (wit or last).get("detection_layer"),
             (wit or last).get("outcome"),
             (wit or last).get("contained"), (wit or last).get("corr")))
    if s.get("terminal") in ("full", "detected_contained"):
        if wit is not None and str(wit.get("kind", "")).startswith(
                "ready_delay_"):
            A("A07-b 时序生命周期（真实钩子，非 oracle 推断）："
              "`inj`(ready_tick=%s → delayed_tick=%s, delay_cycles=%s) → "
              "`ready_delay_resume`(tick=%s, consumed=%s, squashed=%s) → "
              "`%s`(tick=%s, outcome=%s, containment_layer=%s, reason=%s)。"
              "该终局来自 IEW 延迟重入/Commit 真实提交或 ROB 真实 squash，"
              "watchdog 不参与；故障只改时序、不改数据值。"
              % (inj.get("before"), inj.get("after"),
                 inj.get("delay_cycles"),
                 next((e.get("tick") for e in cev
                       if e.get("kind") == "ready_delay_resume"), ""),
                 next((e.get("consumed") for e in cev
                       if e.get("kind") == "ready_delay_resume"), ""),
                 next((e.get("squashed") for e in cev
                       if e.get("kind") == "ready_delay_resume"), ""),
                 wit.get("kind"), wit.get("tick"), wit.get("outcome"),
                 wit.get("containment_layer"),
                 wit.get("containment_reason")))
        _k = str((wit or {}).get("kind", ""))
        if _k == "squash_discarded":
            A("该 squash 属 A01 翻译 fault 请求的**窄白名单终局**：请求在翻译期"
              "（L2）硬件 fault 后从未进入下游，L3 见证结构性缺失；白名单要求"
              "同一 request（request_id 与 dyn_inst_seq 全等）、严格 ancestry"
              "（inj→addr_form→mem_req→lsq_sendfrag→tlb_translate→tlb_fault→"
              "squash）、tick 单调、squash 后无任何更深观测、流已收口，且"
              "oracle=Masked 与 rc=0（必要条件）。见 "
              "`tools/lsu_chain_check._a01_translation_squash_witness`。")
        elif _k == "arch_translation_fault":
            A("该事件是**真实交付的架构翻译异常**（guest SEGV）：L2 硬件检测 + "
              "contained 字段 + 与注入链的 corr 关联；门禁按既有规则接受为 "
              "`%s`——不是 `chain_end` 推断，也不是 oracle 推断。" % s.get("terminal"))
        elif _k.startswith("ready_delay_"):
            A("该终局来自真实生命周期钩子（见上段），其 parent 链 "
              "resume→inj 逐级可证；门禁据此接受为 `%s`——不是 `chain_end` "
              "推断，也不是 oracle 推断。" % s.get("terminal"))
        else:
            A("该事件带真实 detection_layer/outcome/contained/corr，且其 "
              "parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 "
              "`%s`——它不是 `chain_end` 推断，也不是 oracle 推断。"
              % s.get("terminal"))
    else:
        A("终局不是 full/detected_contained（terminal=%s），该 seed **不合格**，"
          "仅作为真实结局留证。" % s.get("terminal"))
    A("")
    A("## 9. 原始证据位置与 SHA-256\n")
    A("| 证据 | 路径 | SHA-256 |\n|---|---|---|")
    for line in sha_lines:
        A(line)
    A("")
    A("## 10. 诚实边界\n")
    A("- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有"
      "模板替代路径。")
    if not rec["qualified"]:
        A("- 本 seed **未通过验收**（见第 7 节），原因以证据为准。")
    if s.get("truncated"):
        A("- 流被截断（truncated=True）：后续不可证。")
    A("")
    return "\n".join(L) + "\n"


def main():
    check_only = "--check" in sys.argv
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    for rid in RUNIDS:
        for seed in SEEDS:
            rec = analyse(rid, seed)
            q = rec["qualified"]
            s = rec["sample"] or {}
            rows.append({
                "runid": rid, "seed": seed, "present": rec["present"],
                "done": rec["done"], "qualified": q,
                "oracle": s.get("oracle_outcome"),
                "terminal": s.get("terminal"),
                "provable_to": s.get("provable_to"),
                "admitted": s.get("admitted"),
                "certified": s.get("certified"),
                "violations": rec["violations"],
                "events": s.get("event_count"),
                "truncated": s.get("truncated"),
                "evidence_truncated": s.get("evidence_truncated"),
                "stream_present": s.get("stream_present"),
                "outdir": str(rec["outdir"]),
                "binary_sha256": (rec["manifest"] or {}).get("binary_sha256"),
                "binary_source_head": (rec["manifest"] or {}).get(
                    "binary_source_head"),
                "round": ("R6-A4" if (rid, seed) in NEW_SAMPLES else "R6-A3"),
            })
            write_this = ("--all" in sys.argv) or ((rid, seed) in NEW_SAMPLES)
            # A BLOCKED cell has a .done/manifest but no sample; its honest
            # document is hand-written from the resolver + census evidence and
            # must not be replaced by a generic "no inj" template.
            if (not check_only and write_this and rec["present"] and rec["done"]
                    and rec["sample"]):
                d = OUT_ROOT / rid
                d.mkdir(parents=True, exist_ok=True)
                (d / ("seed%d.md" % seed)).write_text(doc(rec))

    nq = sum(1 for r in rows if r["qualified"])
    print("samples=%d qualified=%d" % (len(rows), nq))
    for r in rows:
        if not r["qualified"]:
            print("  UNQUALIFIED %s s%d done=%s oracle=%s terminal=%s "
                  "admitted=%s certified=%s trunc=%s evtrunc=%s stream=%s"
                  % (r["runid"], r["seed"], r["done"], r["oracle"],
                     r["terminal"], r["admitted"], r["certified"],
                     r["truncated"], r["evidence_truncated"],
                     r["stream_present"]))
    if check_only:
        return 0

    # ---- INDEX-A.md ----
    lines = ["# R6 A 单元完整传播路径索引（R6-A4）\n",
             "二进制 SHA-256 冻结值见 `runs/lsu/r6_reports/R6-A4-STATUS.json`。"
             "每个 seed 一篇独立文档，数值只来自该 seed 自己的证据。\n",
             "| RunID | seed1 | seed2 | seed3 |", "|---|---|---|---|"]
    for rid in RUNIDS:
        cells = []
        for seed in SEEDS:
            r = next(x for x in rows if x["runid"] == rid and x["seed"] == seed)
            mark = "✅" if r["qualified"] else ("—" if not r["done"] else "❌")
            cells.append("%s [doc](%s/seed%d.md)" % (mark, rid, seed)
                         if r["present"] and r["done"] else mark)
        lines.append("| %s | %s |" % (rid, " | ".join(cells)))
    lines.append("\n✅ = admitted & certified & terminal ∈ {full, detected_contained}"
                 " & 流完整；❌ = 已跑但不合格（详见该 seed 文档第 7/10 节）；"
                 "— = 未运行。\n")
    (OUT_ROOT / "INDEX-A.md").write_text("\n".join(lines) + "\n")

    # ---- STATUS json + md ----
    man0 = next((x for x in rows if x["present"]), None)
    cand = next((x for x in rows if x["round"] == "R6-A4"
                 and x.get("binary_sha256")), None)
    status = {
        "round": "R6-A4",
        "date": "2026-10-28",
        "binary_sha256": (cand or {}).get("binary_sha256"),
        "source_head": (cand or {}).get("binary_source_head"),
        "previous_round_binary_sha256":
            "c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e",
        "previous_round_source_head":
            "ddc81a7b074d0dae2505dc85c8fec5aef6293f66",
        "target_samples": len(rows),
        "qualified_samples": nq,
        "runids": {},
        "samples": rows,
    }
    by = {}
    for r in rows:
        by.setdefault(r["runid"], []).append(r)
    for rid, rs in by.items():
        status["runids"][rid] = {
            "seeds": {str(x["seed"]): ("qualified" if x["qualified"]
                                       else ("not_run" if not x["done"]
                                             else "unqualified")) for x in rs},
            "qualified": sum(1 for x in rs if x["qualified"]),
        }
    (REPORTS / "R6-A4-STATUS.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=1))

    md = ["# R6-A4 状态（2026-10-28）\n",
          "- 候选二进制（25 格新跑）sha256 `%s`（HEAD `%s`）"
          % ((cand or {}).get("binary_sha256"),
             (cand or {}).get("binary_source_head")),
          "- 上一轮冻结二进制（65 格保留）sha256 "
          "`c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e`"
          "（HEAD `ddc81a7b074d0dae2505dc85c8fec5aef6293f66`）",
          "- 目标样本 %d（30 非 F6 RunID × seed1/2/3），合格 %d。\n"
          % (len(rows), nq),
          "| RunID | s1 | s2 | s3 | 合格 |", "|---|---|---|---|---|"]
    for rid in RUNIDS:
        rs = by[rid]
        cells = []
        for x in rs:
            cells.append("✅" if x["qualified"]
                         else ("—" if not x["done"] else
                               "❌(%s/%s)" % (x["oracle"], x["terminal"])))
        md.append("| %s | %s | %d/3 |" % (rid, " | ".join(cells),
                                          sum(1 for x in rs if x["qualified"])))
    md.append("\n未合格样本的真实原因见 `R6-A4-STATUS.json` 的 samples 与逐 seed 文档。")
    (REPORTS / "R6-A4-STATUS.md").write_text("\n".join(md) + "\n")

    # ---- dedup ----
    seen = {}
    dd = ["# R6-A4 证据去重清单\n",
          "按每条 prop_evt 流的内容 SHA-256 去重；同一内容只计一次。\n",
          "| 内容 SHA-256 | 首次出现 | 重复出现 |", "|---|---|---|"]
    dup = 0
    for r in rows:
        if not r["present"] or not r["done"]:
            continue
        ev = Path(r["outdir"]) / r["runid"] / ("seed%d" % r["seed"]) / "prop_evt.txt.gz"
        if not ev.exists():
            continue
        h = sha256(ev)
        if h in seen:
            dup += 1
            dd.append("| `%s` | %s | %s s%d |" % (h, seen[h], r["runid"],
                                                  r["seed"]))
        else:
            seen[h] = "%s s%d" % (r["runid"], r["seed"])
    dd.append("\n唯一流 %d 条，重复 %d 条。" % (len(seen), dup))
    (REPORTS / "R6-A4-EVIDENCE-DEDUP.md").write_text(
        "\n".join(dd) + "\n")
    print("docs/index/status/dedup written; unique_streams=%d dup=%d"
          % (len(seen), dup))
    return 0


if __name__ == "__main__":
    sys.exit(main())
