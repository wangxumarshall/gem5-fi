#!/usr/bin/env python3
"""lsu_r6_status_table.py — [MDSPEC][R6-STATUS][L32] 逐 RunID 权威准入状态表。

权威规格：docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md（§4 状态表 / §5
门禁 / §7 阶段汇报）。本工具产出**唯一权威**的 325 行逐 RunID 表，JSON +
Markdown 双份，并打印 §7.1–3 的状态计数摘要。

诚实纪律（规格红线，逐条对应本工具实现）：
  * 无事件流 ⇒ 一律 `NOT_RUN` / `not measured`——**绝不**"无传播/Masked/Contained"。
  * 有流但无注入 ⇒ `NO_ACTIVATION`（同样绝不算 Masked）。
  * gzip 读不到 EOF 或 `stats.txt` 缺失/空 ⇒ **计 truncated，绝不计 complete**。
  * `PILOT_READY` 仅当：≥1 个 activated 样本形成完整准入链（或严格 containment），
    **且** 全部 activated 样本通过准入，**且** 该 RunID 无截断/Unknown。
  * 链/准入判定**调用真检查器** `tools/lsu_chain_check.py`（check_chain /
    check_admission）——本工具不自写规则。

状态词表（只能用这些）：
  NOT_RUN, RUNNING, NO_ACTIVATION, INFRA_FAILED, CHAIN_INCOMPLETE,
  ORACLE_INCOMPLETE, BLOCKED, PILOT_READY, FORMAL_RUNNING, FORMAL_COMPLETE

用法：
  python3 tools/lsu_r6_status_table.py \
    [--runs-root /home/sdc/gem5-fi-ding/runs/lsu] \
    [--contract docs/gem5-fi/lsu/mdspec/ready_contract.json] \
    [--sha256 <gem5.opt>] [--checkpoint <cpt-dir>] \
    [--out-json docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json] \
    [--out-md   docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import lsu_chain_check as C          # noqa: E402  真检查器（链 + 准入）
import lsu_prop_fields as P          # noqa: E402  真 PROP-EVT 解析器

DEFAULT_RUNS_ROOT = Path("/home/sdc/gem5-fi-ding/runs/lsu")
DEFAULT_CONTRACT = REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json"

STATES = (
    "NOT_RUN", "RUNNING", "NO_ACTIVATION", "INFRA_FAILED", "CHAIN_INCOMPLETE",
    "ORACLE_INCOMPLETE", "BLOCKED", "PILOT_READY", "FORMAL_RUNNING",
    "FORMAL_COMPLETE",
)

_RUNID_RE = re.compile(r"^[A-Z]\d{2}-F\d+-W\d+$")
_STREAM_NAMES = ("prop_evt.txt.gz", "prop_evt.txt")
# 进程在跑的显式标记（RUNNING 判定只认显式标记，绝不猜）
_RUNNING_MARKERS = (".running", "RUNNING", ".claim", "claim.lock")
# 正式 phase 证据落点（contract FORMAL_OUTDIR）
FORMAL_OUTDIR = Path("runs/lsu/formal_325")


# --------------------------------------------------------------------- helpers
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _layer_of(evt, family="generic"):
    """沿用真检查器自身的 kind→layer 映射（tlb 族专用映射亦在内）。"""
    fn = getattr(C, "_layer_of", None)
    if fn is not None:
        return fn(evt, family)
    return P.KIND_LAYER.get(evt.get("kind", ""))


def _is_activated(events) -> bool:
    """真实故障注入 = 存在 fault_id≠0 的 inj 事件（规格二.1）。"""
    for e in events:
        if e.get("kind") == "inj" and e.get("fault_id", "") not in ("", "0"):
            return True
    return False


def _gzip_reaches_eof(path: Path) -> bool:
    """真读整条 gzip 流；EOFError/BadGzipFile 等 = 截断。"""
    try:
        with gzip.open(path, "rt", errors="replace") as f:
            for _ in f:
                pass
        return True
    except (EOFError, gzip.BadGzipFile, OSError, UnicodeDecodeError):
        return False


def _stats_ok(seed_dir: Path) -> bool:
    st = seed_dir / "stats.txt"
    try:
        return st.is_file() and st.stat().st_size > 0
    except OSError:
        return False


# ------------------------------------------------------------ evidence discovery
class Sample:
    """一条 (RunID, seed) 证据样本。"""

    __slots__ = ("path", "seed_dir", "run_id", "seed", "events", "truncated",
                 "stats_ok", "activated", "oracle", "exit_code", "has_unknown",
                 "chain", "admission", "oversized", "max_fault_group")

    def __init__(self, path, seed_dir, run_id, seed, events, truncated,
                 stats_ok):
        self.path = path
        self.seed_dir = seed_dir
        self.run_id = run_id
        self.seed = seed
        self.events = events
        self.truncated = truncated
        self.stats_ok = stats_ok
        self.activated = _is_activated(events)
        self.oracle = None
        self.exit_code = None
        self.has_unknown = any(
            e.get("kind") == "unknown"
            or str(e.get("evidence_status", "")).strip().lower() == "unknown"
            for e in events if e.get("fault_id", "") not in ("", "0"))
        self.chain = None
        self.admission = None
        self.oversized = False
        self.max_fault_group = max(
            (len(v) for v in C._group_by_fault(events).values()), default=0)

    @property
    def complete(self) -> bool:
        """完整流 = gzip 读到 EOF 且 stats.txt 非空。截断/缺 stats 绝不 complete。"""
        return (not self.truncated) and self.stats_ok


def _walk_ancestor_run_ids(d: Path, known: set) -> str | None:
    """在祖先目录名中定位 RunID：精确名，或 `_`/`-` 分隔的 token 命中。"""
    for anc in [d] + list(d.parents):
        name = anc.name
        if name in known:
            return name
        for tok in re.split(r"[_/]", name):
            if _RUNID_RE.fullmatch(tok):
                return tok
    return None


def discover(runs_root: Path, known_runids: set) -> tuple[dict, list]:
    """扫描 runs root，返回 {run_id: [Sample, ...]}, [非 RunID 控制流字典]。"""
    by_run: dict[str, list] = {}
    controls: list = []
    for name in _STREAM_NAMES:
        for p in runs_root.rglob(name):
            # 去重：.gz 与裸文件同名时优先 .gz
            if name == "prop_evt.txt" and (p.parent / "prop_evt.txt.gz").exists():
                continue
            seed_dir = p.parent
            run_id = _walk_ancestor_run_ids(seed_dir, known_runids)
            # 规格布局：<RunID>/seed<N>/prop_evt.txt.gz（也接受结果目录直挂流）。
            # 嵌套的调试产物（如 seed1/dbgrun/prop_evt.txt.gz）不计为样本。
            m = re.fullmatch(r"seed(\d+)", seed_dir.name)
            if m is None:
                if run_id is None:
                    is_run_dir = False
                else:
                    is_run_dir = seed_dir.name == run_id
                if not is_run_dir:
                    continue
            seed = m.group(1) if m else "?"
            events, read_trunc = P.read_events(p)
            # read_events 遇异常会置 truncated；再独立复核 gzip EOF 一次
            truncated = read_trunc or not _gzip_reaches_eof(p)
            samp = Sample(p, seed_dir, run_id or "", seed, events, truncated,
                          _stats_ok(seed_dir))
            if run_id is None:
                controls.append({
                    "stream": str(p.relative_to(runs_root)),
                    "seed": seed,
                    "complete": samp.complete,
                    "activated": samp.activated,
                })
                continue
            by_run.setdefault(run_id, []).append(samp)
    return by_run, controls


# ----------------------------------------------------------------- run results
def _oracle_index(run_dir: Path) -> dict:
    """从 cell_results.json / chain_report.json 汇总 seed→(oracle, exit_code)。"""
    idx: dict = {}
    cr = run_dir / "cell_results.json"
    if cr.is_file():
        try:
            d = json.loads(cr.read_text())
            for r in d.get("runs", []) or []:
                seed = str(r.get("seed", ""))
                chain = r.get("chain") or {}
                idx[f"seed{seed}"] = (r.get("outcome") or chain.get("oracle_outcome"),
                                      chain.get("exit_code"))
        except (json.JSONDecodeError, OSError):
            pass
    crep = run_dir / "chain_report.json"
    if crep.is_file():
        try:
            d = json.loads(crep.read_text())
            for s in d.get("samples", []) or []:
                sid = str(s.get("sample_run_id", ""))
                key = f"seed{sid}" if not sid.startswith("s") else f"seed{sid[1:]}"
                idx.setdefault(key, (s.get("oracle_outcome"), s.get("exit_code")))
        except (json.JSONDecodeError, OSError):
            pass
    return idx


def _find_run_dir(sample: Sample) -> Path:
    """样本所属的 RunID 结果目录（seed 的父目录；若无则向上找）。"""
    return sample.seed_dir.parent


# --------------------------------------------------------------- run-id adjudication
def adjudicate_run(run_id, samples, entry, ctx) -> dict:
    """推导一行权威状态。返回 dict（列名 → 值）。"""
    exec_row = {
        "run_id": run_id,
        "unit": (entry or {}).get("unit", ""),
        "model": (entry or {}).get("model", ""),
        "freq": (entry or {}).get("freq", ""),
        "family": (entry or {}).get("family", ""),
        "contract_status": (entry or {}).get("status", ""),
        "contract_category": (entry or {}).get("category", ""),
        "fix_commit": ctx["fix_commits"].get(run_id, ""),
        "gem5_opt_sha256": ctx["sha256"],
        "gem5_opt_sha256_provisional": ctx["sha256_provisional"],
        "checkpoint": ctx["checkpoint"],
        "checkpoint_provisional": ctx["checkpoint_provisional"],
    }
    executable = (entry or {}).get("status") == "READY"
    exec_row["executable"] = executable

    # 按 seed 排序的样本
    samples = sorted(samples, key=lambda s: s.seed)
    result_dirs = sorted({str(s.seed_dir.parent) for s in samples})
    exec_row["result_dir"] = ";".join(result_dirs)

    n_seeds = len(samples)
    complete = [s for s in samples if s.complete]
    truncated = [s for s in samples if not s.complete]

    # ---- 真检查器：逐样本 check_chain + check_admission -------------------
    cap = ctx["max_chain_events"]
    for s in samples:
        oracle = _oracle_from(ctx, s)
        s.oracle = oracle
        if not s.activated:
            continue                     # 非激活样本无链可证，不跑检查器
        if s.max_fault_group > cap:
            # 诚实上限：真检查器为超线性，超大流不跑——**绝不**据此声称链完整
            s.oversized = True
            continue
        s.chain = C.check_chain(s.events, oracle_outcome=oracle)
        s.admission = C.check_admission({
            "run_id": run_id,
            "activated": 1,
            "events": s.events,
            "rc": s.exit_code if s.exit_code is not None else 0,
            "oracle_outcome": oracle,
        })

    activated = [s for s in samples if s.activated]
    activated_complete = [s for s in activated if s.complete]

    # 最深可证层级 + 覆盖
    deepest = _deepest_layer(activated)
    if activated and deepest is None and any(s.oversized for s in activated):
        coverage = "not measured (fault group > cap)"
    else:
        coverage = _coverage_str(deepest)
    exec_row.update({
        "pilot_seeds": n_seeds,
        "activated_samples": len(activated),
        "complete_streams": len(complete),
        "truncated_streams": len(truncated),
        "L0_L5_coverage": coverage,
        "containment": _containment_evidence(activated),
        "oracle_result": _oracle_summary(activated),
        "run_result": _run_result(samples),
    })

    # ---- 准入结论 --------------------------------------------------------
    verdict, state, reason = _verdict(
        executable=executable, entry=entry, samples=samples, complete=complete,
        truncated=truncated, activated=activated,
        activated_complete=activated_complete, run_id=run_id, deepest=deepest,
        deepest_chain=_deepest_chain(activated), runs_root=ctx["runs_root"],
        max_chain_events=ctx["max_chain_events"])
    exec_row["strict_chain_verdict"] = verdict
    exec_row["state"] = state
    exec_row["failure_reason"] = reason
    if not activated:
        # 红线：无激活 ⇒ 一切"结果"显式标注为未测
        exec_row["oracle_result"] = "not measured" if not samples else exec_row["oracle_result"]
    return exec_row


def _oracle_from(ctx, s: Sample):
    idx = ctx["oracle_idx"].get(s.run_id, {})
    key = f"seed{s.seed}"
    rec = idx.get(key)
    if rec:
        s.exit_code = rec[1]
        return rec[0]
    return None


def _deepest_layer(activated) -> str | None:
    best = None
    for s in activated:
        if not s.chain:
            continue
        for f in s.chain["faults"].values():
            pt = f.get("provable_to")
            if pt and (best is None or C.LAYERS.index(pt) > C.LAYERS.index(best)):
                best = pt
    return best


def _deepest_chain(activated):
    best = None
    for s in activated:
        if s.chain and s.chain["faults"]:
            for f in s.chain["faults"].values():
                if best is None or len(f.get("path_event_ids", [])) > len(
                        best.get("path_event_ids", [])):
                    best = f
    return best


def _coverage_str(deepest) -> str:
    if deepest is None:
        return "none"
    i = C.LAYERS.index(deepest)
    covered = C.LAYERS[:i + 1]
    missing = C.LAYERS[i + 1:]
    out = "L0..%s" % deepest
    if missing:
        out += " (missing %s)" % ",".join(missing)
    return out


def _containment_evidence(activated) -> str:
    """显式 containment 证据（layer + 理由），缺席则空——绝不猜测。"""
    hits = []
    for s in activated:
        if s.admission and s.admission.get("path") == "contained":
            hits.append(f"seed{s.seed}:contained")
    return ";".join(hits)


def _oracle_summary(activated) -> str:
    if not activated:
        return "not measured"
    c = Counter(s.oracle or "MISSING" for s in activated)
    return ", ".join(f"{k}={v}" for k, v in sorted(c.items()))


def _run_result(samples) -> str:
    if not samples:
        return "not measured"
    parts = []
    n_trunc = sum(1 for s in samples if s.truncated)
    n_nostats = sum(1 for s in samples if not s.stats_ok)
    codes = sorted({s.exit_code for s in samples if s.exit_code is not None})
    if n_trunc:
        parts.append(f"{n_trunc} truncated")
    if n_nostats:
        parts.append(f"{n_nostats} no/empty stats.txt")
    if codes:
        parts.append("exit=" + ",".join(str(c) for c in codes))
    return "; ".join(parts) if parts else "streams complete"


def _verdict(*, executable, entry, samples, complete, truncated, activated,
             activated_complete, run_id, deepest, deepest_chain, runs_root,
             max_chain_events):
    """严格序状态派生（规格 §4 词表）。返回 (verdict, state, reason)。"""
    # 0) contract BLOCKED ⇒ BLOCKED（不可执行）
    if not executable:
        cat = (entry or {}).get("category", "")
        why = (entry or {}).get("why", "") or cat
        return (f"n/a (BLOCKED:{cat})", "BLOCKED",
                f"contract BLOCKED [{cat}]: {why}")
    # 0b) 正式 phase 证据（仅认显式标记，绝不猜）
    fdir = Path(runs_root) / "formal_325" / run_id
    if (fdir / ".formal_complete").exists():
        return ("n/a (formal)", "FORMAL_COMPLETE",
                f"formal evidence present at {fdir}")
    if (fdir / ".formal_running").exists():
        return ("n/a (formal)", "FORMAL_RUNNING",
                f"formal in-flight marker at {fdir}")
    # 1) 无任何流 ⇒ NOT_RUN
    if not samples:
        return ("n/a", "NOT_RUN", "not measured: no prop_evt stream found")
    # 2) 显式 running 标记
    for s in samples:
        for m in _RUNNING_MARKERS:
            if (s.seed_dir / m).exists():
                return ("n/a", "RUNNING", f"in-flight marker {m} present")
    # 3) 无完整流 ⇒ INFRA_FAILED（全截断/缺 stats）
    if not complete:
        return ("n/a", "INFRA_FAILED",
                f"{len(truncated)}/{len(samples)} streams truncated or "
                f"stats.txt missing/empty — no usable stream")
    # 4) 完整流中无注入 ⇒ NO_ACTIVATION
    if not activated:
        return ("n/a", "NO_ACTIVATION",
                "no injection (fault_id≠0 inj) in any complete stream — "
                "not measured; NOT Masked/Contained")
    # 5) activated 缺 oracle ⇒ ORACLE_INCOMPLETE
    no_oracle = [s for s in activated if not s.oracle
                 or s.oracle in ("", "None")]
    if no_oracle:
        return ("n/a", "ORACLE_INCOMPLETE",
                f"{len(no_oracle)} activated sample(s) lack oracle outcome")
    # 6) activated 含 Unknown ⇒ CHAIN_INCOMPLETE
    unk = [s for s in activated if s.has_unknown]
    if unk:
        return ("n/a", "CHAIN_INCOMPLETE",
                f"{len(unk)} activated sample(s) carry Unknown evidence "
                f"(mission-forbidden)")
    # 7) 准入失败 ⇒ CHAIN_INCOMPLETE
    oversized = [s for s in activated if s.oversized]
    if oversized and len(oversized) == len(activated):
        return ("NOT ADMITTED (real checker skipped: oversized stream)",
                "CHAIN_INCOMPLETE",
                f"{len(oversized)} activated sample(s) have fault group > "
                f"--max-chain-events={max_chain_events}; real checker not run "
                f"— chain NOT certified (honest: not measured)")
    failures = [s for s in activated if not (s.admission or {}).get("admitted")]
    if failures:
        s0 = failures[0]
        adm = s0.admission or {}
        viol = "; ".join(adm.get("violations", [])[:3])
        note = f" ({len(oversized)} oversized not checker-run)" if oversized else ""
        return (f"NOT ADMITTED (seed{s0.seed}: {adm.get('terminal')}){note}",
                "CHAIN_INCOMPLETE",
                f"{len(failures)}/{len(activated)} activated sample(s) not "
                f"admitted | deepest={deepest} | {viol}")
    # 8) 全部 activated 准入，但存在截断/不可用流 ⇒ 不能认证全流完整
    if truncated:
        return ("ADMITTED on activated, but %d truncated stream(s)" % len(truncated),
                "CHAIN_INCOMPLETE",
                f"{len(truncated)} truncated/unusable stream(s) present — "
                f"full stream integrity not certified (spec §5.3 truncated=0)")
    # 9) 全部准入 + 无截断 + 无 Unknown ⇒ PILOT_READY
    return ("ADMITTED (all activated, full_chain/contained)",
            "PILOT_READY",
            f"{len(activated)} activated sample(s) admitted; deepest={deepest}")


# ------------------------------------------------------------------------ build
def build_table(contract_path: Path, runs_root: Path, sha256_arg, checkpoint_arg,
                fix_commits: dict, registry: dict | None, max_chain_events: int = 20000):
    contract = json.loads(contract_path.read_text())
    entries = {e["run_id"]: e for e in contract.get("entries", [])}
    known = set(entries)
    if registry:
        known |= set(registry)
        for rid, e in registry.items():
            entries.setdefault(rid, e)

    gate = contract.get("gate", {})
    # 二进制 SHA-256：优先 --sha256 实算；否则取 contract gate（provisional）
    if sha256_arg:
        sha = sha256_of(Path(sha256_arg))
        sha_prov = False
        bin_src = str(sha256_arg)
    else:
        sha = gate.get("binary_sha256", "")
        sha_prov = True
        bin_src = gate.get("binary", "")
    if checkpoint_arg:
        ckpt, ckpt_prov = str(checkpoint_arg), False
    else:
        ckpt, ckpt_prov = contract.get("fs_checkpoint", ""), True

    by_run, controls = discover(runs_root, known)
    ctx = {
        "sha256": sha, "sha256_provisional": sha_prov,
        "checkpoint": ckpt, "checkpoint_provisional": ckpt_prov,
        "fix_commits": fix_commits, "oracle_idx": {},
        "runs_root": str(runs_root), "max_chain_events": max_chain_events,
    }
    # oracle 索引（每 RunID 一次）
    for rid, samples in by_run.items():
        if samples:
            run_dir = samples[0].seed_dir.parent
            ctx["oracle_idx"][rid] = _oracle_index(run_dir)

    rows = []
    for rid in sorted(known):
        rows.append(adjudicate_run(rid, by_run.get(rid, []), entries.get(rid), ctx))
    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "spec": "docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md",
        "contract": str(contract_path),
        "runs_root": str(runs_root),
        "total_runids": len(rows),
        "gem5_opt_sha256": sha,
        "gem5_opt_sha256_provisional": sha_prov,
        "gem5_opt_binary_source": bin_src,
        "checkpoint": ckpt,
        "checkpoint_provisional": ckpt_prov,
        "non_runid_control_streams": controls,
    }
    return meta, rows, contract


def summarize(meta, rows, contract):
    """spec §7.1–3 摘要 + 与 contract 类别分歧。"""
    counts = Counter(r["state"] for r in rows)
    summary = {s: counts.get(s, 0) for s in STATES}
    # 完整/截断/缺失分解
    n_streams = sum(r["complete_streams"] + r["truncated_streams"] for r in rows)
    n_complete = sum(r["complete_streams"] for r in rows)
    n_trunc = sum(r["truncated_streams"] for r in rows)
    n_missing = sum(1 for r in rows if r["pilot_seeds"] == 0)
    n_activated = sum(r["activated_samples"] for r in rows)
    # 与 contract 类别分歧
    disagree = []
    contract_status = {e["run_id"]: e.get("status") for e in contract.get("entries", [])}
    for r in rows:
        cs = contract_status.get(r["run_id"])
        if cs == "READY" and r["state"] in ("PILOT_READY",):
            continue
        if cs == "BLOCKED" and r["state"] == "BLOCKED":
            continue
        if cs == "READY" and r["state"] != "PILOT_READY":
            disagree.append((r["run_id"], cs, r["state"]))
        elif cs == "BLOCKED" and r["state"] != "BLOCKED":
            disagree.append((r["run_id"], cs, r["state"]))
    return {
        "states": summary,
        "streams": {"total": n_streams, "complete": n_complete,
                    "truncated": n_trunc, "runids_missing_stream": n_missing},
        "activated_samples_total": n_activated,
        "ready_vs_contract": {
            "ready_by_contract": contract.get("status", {}).get("READY", 0),
            "blocked_by_contract": contract.get("status", {}).get("BLOCKED", 0),
            "pilot_ready_here": summary["PILOT_READY"],
            "disagreements": disagree,
            "disagreement_count": len(disagree),
        },
    }


# ----------------------------------------------------------------------- output
def write_json(path, meta, rows, sumry):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"meta": meta, "summary": sumry, "rows": rows},
        ensure_ascii=False, indent=1) + "\n")


MD_COLS = [
    ("run_id", "RunID"), ("unit", "单元"), ("model", "故障模型"),
    ("executable", "可执行"), ("pilot_seeds", "pilot_seeds"),
    ("activated_samples", "activated"), ("complete_streams", "complete"),
    ("truncated_streams", "trunc"), ("L0_L5_coverage", "L0–L5"),
    ("containment", "containment"), ("oracle_result", "oracle"),
    ("run_result", "run"), ("strict_chain_verdict", "strict-chain"),
    ("state", "state"), ("failure_reason", "失败原因"),
    ("gem5_opt_sha256", "gem5.opt SHA-256"), ("fix_commit", "fix commit"),
]


def write_md(path, meta, rows, sumry):
    lines = []
    lines.append("# R6 逐 RunID 权威准入状态表（L32 背板）\n")
    lines.append(f"- 生成时间：{meta['generated_at']}")
    lines.append(f"- 权威规格：`{meta['spec']}`")
    lines.append(f"- 契约：`{meta['contract']}`")
    lines.append(f"- runs root：`{meta['runs_root']}`")
    sha_tag = "**provisional (contract gate)**" if meta["gem5_opt_sha256_provisional"] \
        else "frozen (hashed)"
    lines.append(f"- gem5.opt SHA-256：`{meta['gem5_opt_sha256']}` — {sha_tag}"
                 f"；来源 `{meta['gem5_opt_binary_source']}`")
    ck_tag = "**provisional**" if meta["checkpoint_provisional"] else "frozen"
    lines.append(f"- checkpoint：`{meta['checkpoint']}` — {ck_tag}")
    lines.append(f"- 总 RunID：{meta['total_runids']}")
    lines.append("")
    lines.append("## §7 状态计数摘要\n")
    for s in STATES:
        lines.append(f"- {s}: {sumry['states'][s]}")
    st = sumry["streams"]
    lines.append(f"\n- 事件流：total={st['total']} complete={st['complete']} "
                 f"truncated={st['truncated']}")
    lines.append(f"- 无任何流的 RunID（never-run）：{st['runids_missing_stream']}")
    lines.append(f"- activated 样本合计：{sumry['activated_samples_total']}")
    rv = sumry["ready_vs_contract"]
    lines.append(f"\n## 与 ready_contract.json 的类别分歧\n")
    lines.append(f"- contract READY={rv['ready_by_contract']} / BLOCKED="
                 f"{rv['blocked_by_contract']}；本表 PILOT_READY={rv['pilot_ready_here']}")
    lines.append(f"- 分歧计数（contract 类别 vs 本表 state）：{rv['disagreement_count']} "
                 f"（READY 但非 PILOT_READY，或 BLOCKED 但非 BLOCKED）")
    lines.append("")
    lines.append("## 权威准入表\n")
    header = "| " + " | ".join(h for _, h in MD_COLS) + " |"
    sep = "|" + "|".join("---" for _ in MD_COLS) + "|"
    lines.append(header)
    lines.append(sep)
    for r in rows:
        cells = []
        for k, _ in MD_COLS:
            v = r.get(k, "")
            if isinstance(v, bool):
                v = "yes" if v else "no"
            v = str(v).replace("|", "\\|").replace("\n", " ")
            cells.append(v)
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def load_fix_commits(path):
    if path and Path(path).is_file():
        return json.loads(Path(path).read_text())
    return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-root", default=str(DEFAULT_RUNS_ROOT))
    ap.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    ap.add_argument("--sha256", help="冻结 gem5.opt 路径（实算 SHA-256）")
    ap.add_argument("--checkpoint", help="checkpoint 身份（目录名）")
    ap.add_argument("--registry", help="可选 RunID 注册表 JSON")
    ap.add_argument("--fix-commits", help="可选 RunID→修复 commit 映射 JSON")
    ap.add_argument("--max-chain-events", type=int, default=20000,
                    help="真检查器超线性(O(n^2))；fault 组事件数超此上限则不跑"
                         "检查器，链标 NOT certified（绝不据此声称完整）")
    ap.add_argument("--out-json",
                    default=str(REPO / "docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json"))
    ap.add_argument("--out-md",
                    default=str(REPO / "docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md"))
    args = ap.parse_args()

    registry = json.loads(Path(args.registry).read_text()) if args.registry else None
    meta, rows, contract = build_table(
        Path(args.contract), Path(args.runs_root), args.sha256, args.checkpoint,
        load_fix_commits(args.fix_commits), registry,
        max_chain_events=args.max_chain_events)
    sumry = summarize(meta, rows, contract)
    write_json(Path(args.out_json), meta, rows, sumry)
    write_md(Path(args.out_md), meta, rows, sumry)

    # §7.1–3 摘要
    print(f"[r6-status] total_runids={meta['total_runids']}")
    for s in STATES:
        print(f"[r6-status]   {s}: {sumry['states'][s]}")
    st = sumry["streams"]
    print(f"[r6-status] streams: total={st['total']} complete={st['complete']} "
          f"truncated={st['truncated']} runids_without_stream={st['runids_missing_stream']}")
    rv = sumry["ready_vs_contract"]
    print(f"[r6-status] gem5.opt sha256={meta['gem5_opt_sha256']} "
          f"(provisional={meta['gem5_opt_sha256_provisional']})")
    print(f"[r6-status] disagreements vs contract: {rv['disagreement_count']} "
          f"(READY={rv['ready_by_contract']} -> PILOT_READY={rv['pilot_ready_here']})")
    print(f"[r6-status] wrote {args.out_json} and {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
