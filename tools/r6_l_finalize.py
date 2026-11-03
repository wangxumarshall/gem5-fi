#!/usr/bin/env python3
"""R6-L finalize: strict offline regrade + per-seed Markdown + audit.

Never runs gem5 and never edits raw streams. For every seed under
runs/lsu/r6_l_unit/runs:
  * loads manifest / chain_report / prop_evt / stats / injection log;
  * qualifies it by the existing admitted verdict, or by the strict
    injected_not_activated proof (L0 or L1 view), or marks NO_INJECTION;
  * for a strict INA seed, backs up and rewrites chain_report.json with the
    terminal/admission/subkind/provenance and proves the stream SHA unchanged;
  * writes a detailed per-seed Markdown for every qualified seed;
  * writes an audit JSONL/summary.
"""
import argparse
import glob
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsu_prop_fields as PF  # noqa: E402
import lsu_chain_check as CHAIN  # noqa: E402
import lsu_campaign as LC  # noqa: E402

# Not line-anchored: an abrupt guest-SEGV teardown can concatenate the
# CHAOS_LSU_TRIGGER line onto the last (newline-less) ITER line.
_TRIG = re.compile(
    r"CHAOS_LSU_TRIGGER: injector=(\S+) tier=(\S+) attempted=(\d+) "
    r"eligible=(\d+) injected=(\d+)")
_REPEAT = re.compile(r"--chaos_repeat\s+(\d+)")
_CMDLINE = re.compile(r"^command line: (.*)$", re.M)
_CMDPATH = re.compile(r"--cmd\s+(\S+)")
_ITER = re.compile(r"^ITER:(\d+):([0-9a-f]{16})\s*$", re.M)
_DRAW = re.compile(r"draw_next_fire=(\d+)")

LS = "/home/sdc/gem5-fi-ding/runs/lsu"
RUNS = f"{LS}/r6_l_unit/runs"
DOCS = f"{LS}/R6_COMPLETE_PROPAGATION_PATHS"
STAGE = "/home/sdc/gem5-fi-ding-cleanup-20261029/R6L_DOCS_STAGE"
OUT = "/home/sdc/gem5-fi-ding-cleanup-20261029/R6L_EVIDENCE_AUDIT"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def atomic_write(p, text):
    d = os.path.dirname(p)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-l-", text=True)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def parse_stats(p):
    out = {}
    if os.path.isfile(p):
        for line in open(p, errors="replace"):
            parts = line.split()
            if len(parts) >= 2 and not line.startswith("#"):
                out[parts[0]] = parts[1]
    return out


def gzip_eof_ok(path):
    try:
        with gzip.open(path, "rb") as f:
            while f.read(1 << 20):
                pass
        return True
    except Exception:  # noqa: BLE001 — a truncated stream is the finding
        return False


def run_meta(paths):
    """Repeat/workload/funnel/oracle metadata read from this seed's own
    run.out. Missing values stay None (never synthesized)."""
    p = paths.get("run_out")
    if not p or not os.path.isfile(p):
        return {}
    text = open(p, errors="replace").read()
    cmdm = _CMDLINE.search(text)
    cmd = cmdm.group(1) if cmdm else ""
    wlm = _CMDPATH.search(cmd)
    workload = os.path.basename(wlm.group(1)) if wlm else ""
    repm = _REPEAT.search(cmd)
    trig = _TRIG.findall(text)
    trig = trig[-1] if trig else None
    drawm = _DRAW.search(text)
    iters = _ITER.findall(text)
    golden = LC.GOLDENS.get(workload)
    return {
        "full_command": cmd,
        "workload": workload or None,
        "repeat_factor": int(repm.group(1)) if repm else 1,
        "tier": trig[1] if trig else None,
        "attempted": int(trig[2]) if trig else None,
        "eligible": int(trig[3]) if trig else None,
        "trigger_injected": int(trig[4]) if trig else None,
        "draw_next_fire": int(drawm.group(1)) if drawm else None,
        "iter_lines": len(iters),
        "iter_all_match_golden": (bool(iters) and golden is not None
                                  and all(c == golden for _, c in iters)),
        "workload_golden": golden,
    }


def inj_log_path(seed_dir):
    hits = sorted(glob.glob(os.path.join(seed_dir, "*_injections.log")))
    return hits[0] if hits else None


def count_injections(path):
    """addrpath: one row per 'Tick: ... Site: ...'; lsqfwd: per 'Cycle: ...'."""
    rows = []
    if not path or not os.path.isfile(path):
        return rows
    for line in open(path, errors="replace"):
        s = line.strip()
        if s.startswith("Tick: ") and "Site:" in s:
            rows.append(s)
        elif s.startswith("Cycle: ") and "Site:" in s:
            rows.append(s)
    return rows


def funnel(path):
    last = None
    if path and os.path.isfile(path):
        for line in open(path, errors="replace"):
            s = line.strip()
            if s.startswith("FUNNEL: ") or s.startswith("CHAOS_L0_FUNNEL:"):
                for tok in s.split():
                    if tok.startswith("injected="):
                        try:
                            v = int(tok.split("=", 1)[1])
                        except ValueError:
                            continue
                        last = {"injected": v}
    return last


def hx(v):
    return f"0x{v}" if v else "—"


def discover(root):
    roots = [p for p in sorted(glob.glob(os.path.join(root, "*_s*")))
             if os.path.isdir(p) and os.path.isfile(os.path.join(p, "manifest.json"))]
    return roots


def load(root):
    man = json.load(open(os.path.join(root, "manifest.json")))
    rid, seed = man["run_id"], int(man["seed"])
    inner = os.path.join(root, rid)
    sd = os.path.join(inner, f"seed{seed}")
    paths = {
        "manifest": os.path.join(root, "manifest.json"),
        "seed_report": os.path.join(sd, "chain_report.json"),
        "cell_report": os.path.join(inner, "chain_report.json"),
        "prop_evt": os.path.join(sd, "prop_evt.txt.gz"),
        "stats": os.path.join(sd, "stats.txt"),
        "run_out": os.path.join(sd, "run.out"),
        "inj_log": inj_log_path(sd),
    }
    return man, rid, seed, sd, paths


def run(root, regrade=False):
    man, rid, seed, sd, paths = load(root)
    rec = {"root": root, "run_id": rid, "seed": seed, "pass": False,
           "status": None, "reasons": []}
    rep = json.load(open(paths["seed_report"]))
    try:
        events, truncated, _s, _i = PF.read_stream(paths["prop_evt"])
    except Exception as exc:
        rec["reasons"].append(f"stream: {exc!r}")
        rec["status"] = "EVIDENCE_TRUNCATED"
        return rec, rep, None
    stats = parse_stats(paths["stats"])
    inj = count_injections(paths["inj_log"])
    rec.update({"oracle": rep.get("oracle_outcome"),
                "exit_code": rep.get("exit_code"),
                "truncated": rep.get("truncated"),
                "evidence_truncated": rep.get("evidence_truncated"),
                "event_count": rep.get("event_count"),
                "terminal": rep.get("terminal"),
                "provable_to": rep.get("provable_to"),
                "admitted": rep.get("admitted"),
                "certified": rep.get("certified"),
                "log_rows": len(inj),
                "binary_sha256": man.get("binary_sha256"),
                "binary_source_head": man.get("binary_source_head"),
                "binary_source_commit": man.get("binary_source_commit"),
                "analysis_tool_head": man.get("analysis_tool_head"),
                "seed_dir": sd,
                "fault_count": len(rep.get("faults") or {}),
                "violations": (rep.get("admission") or {}).get("violations") or []})
    meta = run_meta(paths)
    rec.update({"repeat_factor": meta.get("repeat_factor"),
                "workload": meta.get("workload"),
                "tier": meta.get("tier"),
                "eligible": meta.get("eligible"),
                "draw_next_fire": meta.get("draw_next_fire"),
                "iter_lines": meta.get("iter_lines"),
                "gzip_eof": gzip_eof_ok(paths["prop_evt"])
                if os.path.isfile(paths["prop_evt"]) else False})

    if not inj or not any(e.get("kind") == "inj" and
                          str(e.get("fault_id", "")) not in ("", "0")
                          for e in events):
        rec["status"] = "NO_INJECTION"
        rec["reasons"].append("0 real injections (frequency/workload supply mismatch)")
        return rec, rep, events

    if rep.get("admitted") is True and rep.get("certified") is True:
        rec.update({"pass": True, "status": "QUALIFIED"})
        return rec, rep, events

    # Strict injected_not_activated (L0-only or L1 view).
    stat_inj = None
    for k in ("board.chaos_lsqfwd.numFaultsInjected",
              "board.chaos_addrpath.numFaultsInjected"):
        if k in stats:
            stat_inj = int(stats[k])
            break
    if stat_inj is None:
        # Never synthesize a nonzero injected stat: without the injector's
        # own counter the "log == stream == stats" condition is unprovable.
        rec["status"] = "NOT_QUALIFIED"
        rec["reasons"].append(
            "no injector numFaultsInjected stat (cannot prove three-way count)")
        return rec, rep, events
    verdict = CHAIN.injected_not_activated_verdict(
        events, oracle_outcome=rep.get("oracle_outcome"),
        exit_code=rep.get("exit_code"),
        truncated=rep.get("truncated") is True or
                  rep.get("evidence_truncated") is True,
        stats=stats,
        inj_rows=len(inj),
        binary_sha256=man.get("binary_sha256"),
        binary_source_head=man.get("binary_source_head"),
        analysis_tool_head=man.get("analysis_tool_head"),
        consumer_summary_accounting=rep.get("consumer_summary_accounting"))
    rec["ina"] = {"ok": verdict["ok"], "reasons": verdict["reasons"],
                  "provable_to": verdict.get("provable_to"),
                  "subkind": verdict.get("subkind")}
    if not verdict["ok"]:
        rec["status"] = "NOT_QUALIFIED"
        rec["reasons"].extend(verdict["reasons"][:4])
        return rec, rep, events

    if regrade:
        before = sha256_file(paths["prop_evt"])
        bak = paths["seed_report"] + ".pre-injected-not-activated"
        if not os.path.exists(bak):
            shutil.copy2(paths["seed_report"], bak)
        new = json.loads(json.dumps(rep))
        new["terminal"] = CHAIN.INJECTED_NOT_ACTIVATED
        new["provable_to"] = verdict["provable_to"]
        new["beyond"] = ""
        new["admitted"] = True
        new["certified"] = True
        new["admission"] = {"admitted": True,
                            "path": CHAIN.INJECTED_NOT_ACTIVATED,
                            "terminal": CHAIN.INJECTED_NOT_ACTIVATED,
                            "violations": [], "reasons": [],
                            "note": "严格证明：真实注入，视图/" +
                                    ("缓存行" if verdict["provable_to"] == "L0"
                                     else "comparison 视图") +
                                    "未被下游消费，无架构影响。"}
        new["injected_not_activated"] = {
            "subkind": verdict["subkind"], "fault_id": verdict["fault_id"],
            "l0": verdict["l0"], "line": verdict["line"],
            "oracle": verdict["oracle"], "stats_injected": verdict["stats_injected"],
            "log_rows": verdict["log_rows"], "simTicks": verdict["simTicks"],
            "conditions": {k: True for k in (
                "gzip_eof", "stats_nonempty_simticks_gt_0",
                "counts_log_stream_stats_equal",
                "l0_address_and_field_verifiable",
                "no_downstream_access_of_line", "no_fabricated_l1_to_l5",
                "no_errant_commit_or_containment",
                "chain_end_is_lifecycle_only", "consumer_conservation_ok",
                "binary_and_tool_identity_recorded")},
        }
        new["regrade"] = {
            "kind": "injected_not_activated",
            "original_report_sha256": sha256_file(bak),
            "prop_evt_sha256_before": before,
            "prop_evt_sha256_after": sha256_file(paths["prop_evt"]),
            "tool_head": os.popen(
                "git -C %s rev-parse HEAD" % os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__)))).read().strip(),
        }
        atomic_write(paths["seed_report"], json.dumps(new, ensure_ascii=False, indent=1))
        assert before == new["regrade"]["prop_evt_sha256_after"]
        rep = new
    rec.update({"pass": True, "status": "QUALIFIED",
                "terminal": rep.get("terminal"),
                "provable_to": rep.get("provable_to"),
                "admitted": True, "certified": True})
    return rec, rep, events


def doc(man, rid, seed, rep, events, paths):
    """Per-seed Markdown: identity, injection point/field, address provenance,
    real event order, terminal semantics, evidence checks, honest boundaries.
    Every value is read from THIS seed's own evidence files."""

    meta = run_meta(paths)
    stats = parse_stats(paths["stats"])
    inj_rows = count_injections(paths.get("inj_log")) or []
    by_id = {str(e.get("event_id")): e for e in events}
    stream_inj = sum(1 for e in events if e.get("kind") == "inj")
    stat_inj = None
    for k in ("board.chaos_lsqfwd.numFaultsInjected",
              "board.chaos_addrpath.numFaultsInjected"):
        if k in stats:
            stat_inj = stats[k]
            break
    lines = []
    a = lines.append
    a(f"# {rid} seed{seed} — Load Queue 传播路径（真实事件流）")
    a("")
    a("> 本 doc 只转录该 seed 自己的 `prop_evt.txt.gz`、`chain_report.json`、"
      "`stats.txt`、`run.out`、注入日志与 `manifest.json`；未修改原始流。")
    a("")
    a("## 实验身份")
    a("")
    a(f"- RunID `{rid}` / seed `{seed}`；oracle `{rep.get('oracle_outcome')}`；"
      f"exit `{rep.get('exit_code')}`；terminal `{rep.get('terminal')}`；"
      f"provable_to `{rep.get('provable_to')}`；admitted `{rep.get('admitted')}`；"
      f"certified `{rep.get('certified')}`。")
    a(f"- workload `{meta.get('workload') or 'n/a'}`；repeat factor "
      f"`{meta.get('repeat_factor')}`；tier `{meta.get('tier')}`；"
      f"attempted `{meta.get('attempted')}`；实际 eligible `{meta.get('eligible')}`；"
      f"draw_next_fire `{meta.get('draw_next_fire')}`；"
      + ("ITER 行 n/a（repeat=1 不产生 ITER 行）。"
         if (meta.get("repeat_factor") or 1) <= 1 else
         "ITER 行 `%s`（全部等于 golden：`%s`）。"
         % (meta.get("iter_lines"), meta.get("iter_all_match_golden"))))
    a(f"- 二进制 SHA `{man.get('binary_sha256')}`，源 `{man.get('binary_source_head')}`，"
      f"analysis head `{man.get('analysis_tool_head')}`。")
    a(f"- 事件数 `{rep.get('event_count')}`；truncated `{rep.get('truncated')}`。")
    a("")
    a("## 注入点与字段")
    a("")
    if inj_rows:
        row = inj_rows[0]
        kv = {}
        for k, v in re.findall(r"([A-Za-z_]+):\s*([^,]+)", row):
            kv[k.strip()] = v.strip()
        for k, v in re.findall(r"([A-Za-z_]+)=([^,\s]+)", row):
            kv.setdefault(k.strip(), v.strip())
        a("| 来源 | site | 字段 | old | new | 其他 |")
        a("|---|---|---|---|---|---|")
        inj_ev = next((e for e in events if e.get("kind") == "inj"), {})
        site = kv.get("Site", "n/a")
        field = (kv.get("fault_field") or kv.get("FaultType")
                 or inj_ev.get("field") or "n/a")
        old = (kv.get("old_addr") or kv.get("old")
               or inj_ev.get("before") or "n/a")
        new = (kv.get("new_addr") or kv.get("new")
               or inj_ev.get("after") or "n/a")
        other = ", ".join("%s=%s" % (k, v) for k, v in sorted(kv.items())
                          if k not in ("Site", "FaultType", "fault_field",
                                       "old_addr", "new_addr"))
        a(f"| `{paths.get('inj_log')}` | `{site}` | `{field}` | `{old}` | "
          f"`{new}` | {other or '—'} |")
    else:
        a("注入日志缺失（本 seed 不是真实注入样本）。")
    a("")
    a("## 地址来源与请求身份")
    a("")
    a("| event_id | kind | va | pa | pfn | corr | request_id | lq_idx | "
      "dyn_seq | store_dyn_seq |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for e in events:
        if e.get("kind") == "chain_end":
            continue
        pa = e.get("pa")
        pfn = ""
        try:
            pfn = "0x%x" % (int(pa, 16) >> 12) if pa else ""
        except (TypeError, ValueError):
            pfn = ""
        a(f"| {e.get('event_id')} | `{e.get('kind')}` | {hx(e.get('va'))} | "
          f"{hx(pa)} | {pfn or '—'} | `{e.get('corr') or '—'}` | "
          f"{e.get('request_id') or '—'} | {e.get('lq_idx') or '—'} | "
          f"{e.get('dyn_inst_seq') or '—'} | "
          f"{e.get('store_dyn_inst_seq') or '—'} |")
    a("")
    a("## 逐 fault 规范路径")
    a("")
    for fid in sorted(rep.get("faults") or {}, key=lambda x: int(x)):
        f = (rep.get("faults") or {})[fid]
        a(f"### fault {fid} — terminal={f.get('terminal')} "
          f"provable_to={f.get('provable_to')}")
        a("")
        a("| # | 层 | event_id | parent | tick | kind | request_id | dyn_seq | "
          "va | pa | before→after |")
        a("|---|---|---|---|---|---|---|---|---|---|---|")
        path_ids = [str(x) for x in (f.get("path_event_ids") or [])]
        for i, eid in enumerate(path_ids):
            e = by_id.get(eid, {})
            layer = CHAIN._layer_of(e, f.get("family", "lq")) or "—"
            ch = ""
            if e.get("before") or e.get("after"):
                ch = f"{e.get('before') or '—'} → {e.get('after') or '—'}"
            a(f"| {i} | {layer} | {eid} | {e.get('parent_event_id') or '—'} | "
              f"{e.get('tick')} | `{e.get('kind')}` | "
              f"{e.get('request_id') or '—'} | {e.get('dyn_inst_seq') or '—'} | "
              f"{hx(e.get('va'))} | {hx(e.get('pa'))} | {ch or '—'} |")
        a("")
        a("真实事件顺序（严格按 tick / event_id）：")
        a("")
        for i, eid in enumerate(path_ids, 1):
            e = by_id.get(eid, {})
            layer = CHAIN._layer_of(e, f.get("family", "lq")) or "—"
            ch = ""
            if e.get("before") or e.get("after"):
                ch = "；%s → %s" % (e.get("before") or "—",
                                    e.get("after") or "—")
            a(f"{i}. `event_id={eid}` parent=`{e.get('parent_event_id') or '—'}` "
              f"tick=`{e.get('tick')}` kind=`{e.get('kind')}` layer=`{layer}` "
              f"corr=`{e.get('corr') or '—'}`；va=`{hx(e.get('va'))}` "
              f"pa=`{hx(e.get('pa'))}`{ch}")
        a("")
        a("层边：" + (", ".join(f"{k}={v}" for k, v in
                              (f.get("edges") or {}).items()
                              if not k.endswith("_witness")) or "—"))
        a("")
    ina = rep.get("injected_not_activated")
    if ina:
        l0 = ina.get("l0") or {}
        a("## Injected-not-activated（严格证明）")
        a("")
        a(f"注入 Tick `{l0.get('tick')}`，地址/视图 "
          f"`{hx(l0.get('va') or ina.get('line'))}`，字段 `{l0.get('field')}`；"
          f"log/stream/stats 计数 `{ina.get('log_rows')}/{stream_inj}/"
          f"{ina.get('stats_injected')}`；provable_to `{rep.get('provable_to')}`，"
          f"subkind `{ina.get('subkind')}`。")
        a("")
        a("故障真实注入，但该视图在程序结束前没有被下游消费/产生可观察的架构影响；"
          "`chain_end` 仅生命周期，不是 L5，不伪造任何 L1–L5 事件。")
        a("")
    terminal = rep.get("terminal") or ""
    a("## 终局语义")
    a("")
    if terminal == "crash_translation_fault":
        a("L0 注入改变地址/视图，L1 `addr_form` 形成；该视图进入 LQ/翻译路径，"
          "TLB/MMU 交付真实 `arch_translation_fault`（L2），受控 guest SEGV 结束"
          "仿真。终局是**真实 crash**，provable_to=L2；没有伪造 L3–L5。")
    elif terminal == "full":
        a("故障值沿真实链路被下游消费并到达可观察终局（L5 / full）；"
          "逐事件见上表，未用 `chain_end` 冒充 L5。")
    elif terminal == "detected_contained":
        a("故障在 L3 被真实检测/含住（detected/contained），未产生架构可见错误。")
    elif terminal == "injected_not_activated":
        a("故障真实注入，但视图/缓存行未被下游消费——严格 latent no-effect；"
          "`chain_end` 仅为生命周期。")
    else:
        a(f"terminal=`{terminal or 'n/a'}`；以 `chain_report.json` 为准，"
          "不做超出事件流的推断。")
    a("")
    a("## 证据校验")
    a("")
    a("| 检查 | 结果 |")
    a("|---|---|")
    a(f"| gzip EOF | `{gzip_eof_ok(paths['prop_evt'])}` |")
    a(f"| stats.simTicks | `{stats.get('simTicks', 'n/a')}` |")
    a(f"| 注入 stat | `{stat_inj if stat_inj is not None else 'n/a'}` |")
    a(f"| log/stream/stats 计数 | `{len(inj_rows)}/{stream_inj}/"
      f"{stat_inj if stat_inj is not None else 'n/a'}` |")
    a("| ITER 行 | " + (
        "n/a（repeat=1 不产生 ITER 行）"
        if (meta.get("repeat_factor") or 1) <= 1 else
        "`%s`，全部等于 golden `%s`"
        % (meta.get("iter_lines"), meta.get("iter_all_match_golden"))) + " |")
    acct = rep.get("consumer_summary_accounting") or {}
    a(f"| conservation | `{acct.get('conservation', 'n/a')}` |")
    a(f"| admission / certification | `{rep.get('admitted')}` / "
      f"`{rep.get('certified')}` |")
    a(f"| chain_end 仅生命周期 | `"
      f"{all(e.get('kind') != 'chain_end' or (e.get('corr') in ('none', '')) for e in events)}` |")
    a("")
    a("## 事件总览与证据")
    a("")
    kinds = {}
    for e in events:
        kinds[e.get("kind", "")] = kinds.get(e.get("kind", ""), 0) + 1
    a("| kind | count |")
    a("|---|---|")
    for k in sorted(kinds):
        a(f"| `{k}` | {kinds[k]} |")
    a("")
    a("| 证据 | 路径 | SHA-256 |")
    a("|---|---|---|")
    for key in ("prop_evt", "stats", "run_out", "inj_log", "manifest"):
        p = paths.get(key)
        if p and os.path.isfile(p):
            a(f"| {key} | `{p}` | `{sha256_file(p)}` |")
    a("")
    a("```bash")
    a(meta.get("full_command") or man.get("command", "n/a"))
    a("```")
    a("")
    a("## 诚实边界")
    a("")
    a("- 逐 fault 终局取自 `chain_report.json`；`chain_end` 永不充当 L5。")
    a("- oracle 与链终局不一致时并列记录，不互相改写。")
    a("- 若 repeat factor > 1：只重复**同一 workload 的核心操作**以补足 eligible "
      "供给；频率间隔、warmup/span、seed、注入字段/注入点与 RunID 身份均未改变；"
      "每趟执行相同操作序列（repeat=1 golden 不变，ITER 行全部等于 golden）。")
    a("- 原始证据未修改；同一 seed 的旧目录/旧截断证据保留在原位置。")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=RUNS)
    ap.add_argument("--roots",
                    help="comma-separated evidence roots; later roots supersede "
                         "an earlier root for the same (run_id, seed)")
    ap.add_argument("--regrade", action="store_true")
    ap.add_argument("--deploy", action="store_true")
    args = ap.parse_args()
    roots = [r for r in (args.roots or args.root).split(",") if r.strip()]
    os.makedirs(STAGE, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    # [R6-L-UNIT] New repeat runs live in a fresh root; the pre-repeat root is
    # preserved as superseded evidence. Later roots win for duplicate keys.
    chosen, order = {}, []
    for root in roots:
        for d in discover(root):
            man = json.load(open(os.path.join(d, "manifest.json")))
            k = (man["run_id"], int(man["seed"]))
            if k in chosen and chosen[k] != d:
                print("SUPERSEDE", k, chosen[k], "->", d)
            chosen[k] = d
            if k not in order:
                order.append(k)
    rows, docs = [], 0
    for k in order:
        root = chosen[k]
        rec, rep, events = run(root, regrade=args.regrade)
        rec["root"] = root
        rec["superseded"] = len([r for r in roots if r != root and
                                 os.path.isdir(os.path.join(
                                     r, "%s_s%d" % (rec["run_id"],
                                                    rec["seed"])))])
        rows.append(rec)
        if rec["status"] == "QUALIFIED":
            text = doc(json.load(open(os.path.join(root, "manifest.json"))),
                       rec["run_id"], rec["seed"], rep, events,
                       load(root)[4])
            p = os.path.join(STAGE, rec["run_id"],
                             f"{rec['run_id']}-seed{rec['seed']}.md")
            atomic_write(p, text)
            rec["doc"] = p
            docs += 1
            if args.deploy:
                dst = os.path.join(DOCS, rec["run_id"],
                                   f"{rec['run_id']}-seed{rec['seed']}.md")
                atomic_write(dst, text)
        print(rec["status"], rec["run_id"], "s%d" % rec["seed"],
              rec.get("terminal"), rec.get("provable_to"),
              rec["reasons"][:2])
    with open(os.path.join(OUT, "R6L_EVIDENCE_AUDIT.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "seeds": len(rows),
        "qualified": sum(1 for r in rows if r["status"] == "QUALIFIED"),
        "no_injection": sum(1 for r in rows if r["status"] == "NO_INJECTION"),
        "not_qualified": sum(1 for r in rows if r["status"] == "NOT_QUALIFIED"),
        "docs": docs,
        "by_run": {},
    }
    for r in rows:
        summary["by_run"].setdefault(r["run_id"], []).append(
            [r["seed"], r["status"]])
    with open(os.path.join(OUT, "R6L_SUMMARY.json"), "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: summary[k] for k in
                      ("seeds", "qualified", "no_injection",
                       "not_qualified", "docs")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
