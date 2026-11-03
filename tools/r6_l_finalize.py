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
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsu_prop_fields as PF  # noqa: E402
import lsu_chain_check as CHAIN  # noqa: E402

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
                "binary_sha256": man.get("binary_sha256")})

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

    lines = []
    a = lines.append
    a(f"# {rid} seed{seed} — Load Queue 传播路径（真实事件流）")
    a("")
    a("> 本 doc 只转录该 seed 自己的 `prop_evt.txt.gz`、`chain_report.json`、"
      "`stats.txt`、`run.out`、注入日志与 `manifest.json`；未修改原始流。")
    a("")
    a(f"- RunID `{rid}` / seed `{seed}`；oracle `{rep.get('oracle_outcome')}`；"
      f"exit `{rep.get('exit_code')}`；terminal `{rep.get('terminal')}`；"
      f"provable_to `{rep.get('provable_to')}`；admitted `{rep.get('admitted')}`；"
      f"certified `{rep.get('certified')}`。")
    a(f"- 二进制 SHA `{man.get('binary_sha256')}`，源 `{man.get('binary_source_head')}`，"
      f"analysis head `{man.get('analysis_tool_head')}`。")
    a(f"- 事件数 `{rep.get('event_count')}`；truncated `{rep.get('truncated')}`。")
    a("")
    a("## 逐 fault 规范路径")
    a("")
    by_id = {str(e.get("event_id")): e for e in events}
    for fid in sorted(rep.get("faults") or {}, key=lambda x: int(x)):
        f = (rep.get("faults") or {})[fid]
        a(f"### fault {fid} — terminal={f.get('terminal')} provable_to={f.get('provable_to')}")
        a("")
        a("| # | 层 | event_id | parent | tick | kind | request_id | dyn_seq | va | pa | before→after |")
        a("|---|---|---|---|---|---|---|---|---|---|---|")
        for i, eid in enumerate([str(x) for x in (f.get("path_event_ids") or [])]):
            e = by_id.get(eid, {})
            layer = CHAIN._layer_of(e, f.get("family", "lq")) or "—"
            ch = ""
            if e.get("before") or e.get("after"):
                ch = f"{e.get('before') or '—'} → {e.get('after') or '—'}"
            a(f"| {i} | {layer} | {eid} | {e.get('parent_event_id') or '—'} | "
              f"{e.get('tick')} | `{e.get('kind')}` | {e.get('request_id') or '—'} | "
              f"{e.get('dyn_inst_seq') or '—'} | {hx(e.get('va'))} | {hx(e.get('pa'))} | "
              f"{ch or '—'} |")
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
        a(f"注入 Tick `{l0.get('tick')}`，地址/视图 `{hx(l0.get('va') or ina.get('line'))}`，"
          f"字段 `{l0.get('field')}`；log/stream/stats 计数 `{ina.get('log_rows')}/"
          f"{sum(1 for e in events if e.get('kind') == 'inj')}/{ina.get('stats_injected')}`；"
          f"provable_to `{rep.get('provable_to')}`，subkind `{ina.get('subkind')}`。")
        a("")
        a("故障真实注入，但该视图在程序结束前没有被下游消费/产生可观察的架构影响；"
          "`chain_end` 仅生命周期，不是 L5，不伪造任何 L1–L5 事件。")
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
    a(man.get("command", "n/a"))
    a("```")
    a("")
    a("## 诚实边界")
    a("")
    a("- 逐 fault 终局取自 `chain_report.json`；`chain_end` 永不充当 L5。")
    a("- oracle 与链终局不一致时并列记录，不互相改写。")
    a("- 同一 seed 的旧截断证据保留在原目录。")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=RUNS)
    ap.add_argument("--regrade", action="store_true")
    ap.add_argument("--deploy", action="store_true")
    args = ap.parse_args()
    os.makedirs(STAGE, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    rows, docs = [], 0
    for root in discover(args.root):
        rec, rep, events = run(root, regrade=args.regrade)
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
