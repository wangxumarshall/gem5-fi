#!/usr/bin/env python3
"""lsu_r6_status_table.py — [MDSPEC][R6-FIXD] 逐 RunID 权威准入状态表（六态）。

规格：`docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md`（§4 状态表 / §5 门禁）。
本工具产出**唯一权威**的逐 RunID 表（JSON + Markdown），每行同时给出
`state`（六态之一）与 `conditions`（六态各自独立布尔），并打印状态计数。

六态（**互不覆盖**，六者都必须可独立出现）：

  NOT_RUN           权威根下**没有任何流** —— 未测量。**绝不被契约 BLOCKED 顶掉**
                    （这正是旧表"325 全短路 BLOCKED ⇒ NOT_RUN 永不出现"的修复）。
  EVIDENCE_MISSING  证据被**声称**（pilot_evidence.json 列了该 RunID/seed）但文件
                    在权威根下缺失/不可读（悬空引用）——与"从未运行"不同。
  TRUNCATED         有流，但 gzip 读不到 EOF 或 stats.txt 缺失/0 字节（流不完整）。
  UNPROVEN          全流完整且有激活，但链**未过** `check_admission`（或完整流内
                    根本没有激活）——"测了但证不出来"。
  PILOT_READY       全部激活样本准入 + 无截断 + 无 Unknown + **无上游阻塞**。
  BLOCKED           有**上游独立阻塞**（FS-INFRA / RULING / LICENSE …，取自契约的
                    **上游**判定 upstream_status/category，而非其链门禁后的收尾
                    status）。仅当该行"本可 PILOT_READY"时才记 BLOCKED
                    （规格红线：规格/基础设施阻塞**绝不可**计为 PILOT_READY）；
                    上游阻塞另在 `upstream_block` 列单独表达，绝不吞掉
                    NOT_RUN / TRUNCATED / UNPROVEN。

诚实纪律（逐条实现）：
  * 磁盘上没有流 ⇒ NOT_RUN，**不等于** BLOCKED，也**不得**解释成"无传播/Masked"。
  * 截断流上**不得**认证（与 Lane B 的 containment 口径一致）。
  * 链判定**调用真检查器** `lsu_chain_check.check_admission`（本工具不自写规则）。

evidence root（**与契约同一个、且被明确记录**）：`--evidence-root`，缺省
`$LSU_CHAIN_EVIDENCE_ROOT`，再缺省仓库根；流自 `<root>/runs/lsu` 读取。
若与 `ready_contract.json` 的 `chain_gate.evidence_root` 不一致，**响亮**告警并记录。

用法：
  LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding \
    python3 tools/lsu_r6_status_table.py [--out-json ...] [--out-md ...]
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import lsu_chain_check as C            # noqa: E402  真检查器（唯一链/准入判定源）
import lsu_prop_fields as P            # noqa: E402  真 PROP-EVT 解析器

STATES = ("NOT_RUN", "EVIDENCE_MISSING", "TRUNCATED", "UNPROVEN",
          "PILOT_READY", "BLOCKED")

DEFAULT_CONTRACT = REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json"
DEFAULT_PILOTS = REPO / "docs/gem5-fi/lsu/mdspec/pilot_evidence.json"
_RUNID_RE = re.compile(r"^[A-Z]\d{2}-F\d+-W\d+$")
_STREAM_NAMES = ("prop_evt.txt.gz", "prop_evt.txt")
EVENT_CAP = 200000        # 真检查器超线性；超大流不跑检查器 ⇒ 记 UNPROVEN（响亮）


def resolve_evidence_root(arg=None):
    """(root, source) —— 明确记录证据根来源，绝不隐式。"""
    if arg:
        return Path(arg), "--evidence-root"
    env = os.environ.get("LSU_CHAIN_EVIDENCE_ROOT")
    if env:
        return Path(env), "$LSU_CHAIN_EVIDENCE_ROOT"
    return REPO, "default(repo root)"


# ------------------------------------------------------------------ discovery
class Sample:
    __slots__ = ("path", "seed_dir", "seed", "run_id", "events", "truncated",
                 "stats_ok", "activated", "has_unknown", "admission", "oversized")

    def __init__(self, path, seed_dir, seed, run_id):
        self.path = path
        self.seed_dir = seed_dir
        self.seed = seed
        self.run_id = run_id
        self.events = []
        self.truncated = True
        self.stats_ok = False
        self.activated = False
        self.has_unknown = False
        self.admission = None
        self.oversized = False

    @property
    def complete(self):
        return (not self.truncated) and self.stats_ok

    def read(self):
        try:
            self.events, trunc = P.read_events(self.path)
            self.truncated = bool(trunc) or not _gzip_eof(self.path)
        except Exception:
            self.events, self.truncated = [], True
        self.stats_ok = _stats_ok(self.seed_dir)
        self.activated = any(e.get("kind") == "inj"
                             and str(e.get("fault_id", "")) not in ("", "0")
                             for e in self.events)
        self.has_unknown = any(
            str(e.get("evidence_status", "")).strip().lower() == "unknown"
            or e.get("kind") == "unknown"
            for e in self.events if str(e.get("fault_id", "")) not in ("", "0"))
        return self


def _gzip_eof(path: Path) -> bool:
    if path.suffix != ".gz":
        return True
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


def _runid_of(path_dir: Path, known: set) -> str | None:
    for anc in [path_dir] + list(path_dir.parents):
        name = anc.name
        if name in known:
            return name
        if _RUNID_RE.fullmatch(name):
            return name
        for tok in re.split(r"[_]", name):
            if _RUNID_RE.fullmatch(tok):
                return tok
    return None


def discover(runs_root: Path, known: set) -> dict:
    by_run: dict = {}
    if not runs_root.is_dir():
        return by_run
    for name in _STREAM_NAMES:
        for p in runs_root.rglob(name):
            if name == "prop_evt.txt" and (p.parent / "prop_evt.txt.gz").exists():
                continue
            seed_dir = p.parent
            rid = _runid_of(seed_dir, known)
            if rid is None:
                continue
            m = re.fullmatch(r"seed(\d+)", seed_dir.name)
            if m is None and seed_dir.name != rid:
                continue                      # 嵌套调试产物不计为样本
            seed = m.group(1) if m else "?"
            by_run.setdefault(rid, []).append(
                Sample(p, seed_dir, seed, rid).read())
    return by_run


# ------------------------------------------------------------------ adjudication
def _claim_paths(pilots: dict, runid: str, root: Path, runs_root: Path):
    """registry 中该 RunID 及其 seed 样本**声称**的证据路径。

    返回 (claimed, missing, outside)：
      missing = 权威根下**不存在**者（悬空引用 ⇒ EVIDENCE_MISSING）；
      outside = 存在但**不在权威 runs 根之内**者（草稿/他处 worktree 的产物，
                不构成权威证据 ⇒ 该行仍按磁盘事实记 NOT_RUN，但如实披露）。
    """
    seed_re = re.compile(rf"^{re.escape(runid)}-seed\d+$")
    claimed, missing, outside = 0, [], []
    rr = Path(runs_root).resolve()
    for k, v in pilots.items():
        if k != runid and not seed_re.match(k):
            continue
        for rel in (v.get("paths") or ([v["path"]] if v.get("path") else [])):
            claimed += 1
            p = (root / rel)
            if not p.exists():
                missing.append(rel)
            else:
                try:
                    p.resolve().relative_to(rr)
                except ValueError:
                    outside.append(rel)
    return claimed, missing, outside


def _unknown_present(samples) -> bool:
    return any(s.has_unknown for s in samples if s.activated)


def adjudicate(runid, samples, entry, pilots, root, runs_root):
    contract_up = (entry or {}).get("upstream_status")
    upstream_cat = (entry or {}).get("upstream_category") or ""
    # [R6-FIXD] 上游阻塞取自契约的**上游**判定（链门禁之前），绝不取它的收尾
    # status —— 否则"契约判 325 全 BLOCKED（实为链门禁降级）"会把每一行短路。
    upstream_blocked = (contract_up == "BLOCKED")
    row = {
        "run_id": runid,
        "unit": (entry or {}).get("unit", ""),
        "model": (entry or {}).get("model", ""),
        "freq": (entry or {}).get("freq", ""),
        "contract_status": (entry or {}).get("status", ""),
        "contract_upstream_status": contract_up,
        "upstream_block": upstream_cat if upstream_blocked else "NONE",
        "upstream_blocked": upstream_blocked,
    }
    samples = sorted(samples, key=lambda s: s.seed)
    complete = [s for s in samples if s.complete]
    truncated = [s for s in samples if not s.complete]
    activated = [s for s in samples if s.activated]

    # 真检查器：逐激活样本 check_admission（超大流不跑，记 oversized）
    for s in activated:
        if len(s.events) > EVENT_CAP:
            s.oversized = True
            continue
        s.admission = C.check_admission({
            "run_id": runid, "activated": 1, "events": s.events, "rc": 0,
            "containment": C.containment_from_events(s.events, runid),
        })

    admitted = [s for s in activated
                if (s.admission or {}).get("admitted") is True]
    refused = [s for s in activated if s not in admitted]
    claimed, missing, outside = _claim_paths(pilots, runid, root, runs_root)

    cond = {
        "not_run": len(samples) == 0,
        "evidence_missing": (len(samples) == 0 and claimed > 0 and missing),
        "truncated": bool(truncated) and bool(samples),
        "unproven": (bool(complete) and (not activated or bool(refused))),
        "pilot_ready": (bool(activated) and not refused and not truncated
                        and not _unknown_present(activated)
                        and not any(s.oversized for s in activated)),
        "blocked": upstream_blocked,
    }
    # ---- disk-first 优先级；BLOCKED 只在"本可 PILOT_READY"时生效 ----
    if not samples:
        state = "EVIDENCE_MISSING" if cond["evidence_missing"] else "NOT_RUN"
    elif truncated:
        state = "TRUNCATED"
    elif not activated or refused:
        state = "UNPROVEN"
    elif upstream_blocked:
        state = "BLOCKED"
    elif cond["pilot_ready"]:
        state = "PILOT_READY"
    else:
        state = "UNPROVEN"          # oversized / Unknown 等：证不出来

    row["conditions"] = cond
    row["state"] = state
    row.update({
        "samples": len(samples),
        "complete_streams": len(complete),
        "truncated_streams": len(truncated),
        "activated_samples": len(activated),
        "admitted_samples": len(admitted),
        "unknown_samples": sum(1 for s in activated if s.has_unknown),
        "claimed_evidence": claimed,
        "missing_evidence": missing,
        "claimed_outside_runs_root": outside,
        "result_dir": ";".join(sorted({str(s.seed_dir.parent) for s in samples})),
        "failure_reason": _reason(state, cond, refused, samples, upstream_cat,
                                  missing, outside),
    })
    return row


def _reason(state, cond, refused, samples, upstream_cat, missing, outside=()):
    if state == "NOT_RUN":
        base = "not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED"
        if outside:
            base += (f"；另有 {len(outside)} 条 pilot 路径存在但**不在权威 runs 根内**"
                     f"（草稿/他处产物，不构成权威证据，如 {outside[0]}）")
        return base
    if state == "EVIDENCE_MISSING":
        return ("证据被声称但文件在权威根下缺失：%s（悬空引用）"
                % ", ".join(missing[:3]))
    if state == "TRUNCATED":
        n = sum(1 for s in samples if not s.complete)
        return f"{n}/{len(samples)} 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF）"
    if state == "UNPROVEN":
        if not any(s.activated for s in samples):
            return "完整流内无注入（fault_id≠0 的 inj）——未激活，未测量；非 Masked"
        return (f"{len(refused)} 个激活样本未过 check_admission"
                f"（含 oversized/Unknown）")
    if state == "BLOCKED":
        return (f"上游独立阻塞 {upstream_cat or 'BLOCKED'}："
                f"证据已准入但规格/基础设施阻塞不可解除——绝不计为 PILOT_READY")
    return "全部激活样本准入，无截断，无 Unknown"


# ---------------------------------------------------------------------- build
def build(contract_path, pilots_path, root, runs_root):
    contract = {}
    if contract_path and Path(contract_path).is_file():
        contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    entries = {e["run_id"]: e for e in contract.get("entries", [])}
    pilots = {}
    if pilots_path and Path(pilots_path).is_file():
        pilots = json.loads(Path(pilots_path).read_text(encoding="utf-8")).get(
            "pilots", {}) or {}
    # 权威集合 = 契约的 RunID（矩阵口径，325 项）；证据里出现的**非矩阵**
    # RunID 单独披露（extra_evidence_runids），不混进权威表。
    known = set(entries)
    by_run = discover(Path(runs_root), known)
    extra = sorted(set(by_run) - known)
    rows = [adjudicate(rid, by_run.get(rid, []), entries.get(rid), pilots,
                       Path(root), Path(runs_root)) for rid in sorted(known)]
    gate_root = ((contract.get("chain_gate") or {}).get("evidence_root"))
    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "spec": "docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md",
        "contract": str(contract_path),
        "evidence_root": str(root),
        "evidence_root_source": "unspecified(build)",
        "runs_root": str(runs_root),
        "contract_chain_gate_evidence_root": gate_root,
        "evidence_root_matches_contract": (
            gate_root is None or
            Path(gate_root).resolve() == Path(root).resolve()),
        "total_runids": len(rows),
        "extra_evidence_runids": extra,
    }
    return meta, rows, contract


def summarize(meta, rows, contract):
    counts = Counter(r["state"] for r in rows)
    return {
        "states": {s: counts.get(s, 0) for s in STATES},
        "streams": {
            "total": sum(r["samples"] for r in rows),
            "complete": sum(r["complete_streams"] for r in rows),
            "truncated": sum(r["truncated_streams"] for r in rows),
            "activated": sum(r["activated_samples"] for r in rows),
            "admitted": sum(r["admitted_samples"] for r in rows),
        },
        "runids_without_stream": sum(1 for r in rows if r["samples"] == 0),
        "evidence_root": meta["evidence_root"],
        "pilot_ready_list": sorted(r["run_id"] for r in rows
                                   if r["state"] == "PILOT_READY"),
        "upstream_blocked": sorted(r["run_id"] for r in rows
                                   if r["upstream_blocked"]),
        "extra_evidence_runids": meta.get("extra_evidence_runids", []),
    }


MD_COLS = ["run_id", "unit", "model", "state", "contract_upstream_status",
           "upstream_block", "samples", "activated_samples", "admitted_samples",
           "failure_reason"]


def write_outputs(out_json, out_md, meta, rows, sumry):
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(
        {"meta": meta, "summary": sumry, "rows": rows},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    L = ["# R6 逐 RunID 权威准入状态表（六态）", "",
         f"- 生成时间：{meta['generated_at']}",
         f"- 证据根：`{meta['evidence_root']}`（runs 根 `{meta['runs_root']}`）",
         f"- 契约 `chain_gate.evidence_root`：`{meta['contract_chain_gate_evidence_root']}`"
         f" —— 一致：{'是' if meta['evidence_root_matches_contract'] else '否（响亮告警）'}",
         f"- 总 RunID：{meta['total_runids']}", "",
         "## 状态计数", ""]
    for s in STATES:
        L.append(f"- {s}: {sumry['states'][s]}")
    st = sumry["streams"]
    L += ["",
          f"- 流：total={st['total']} complete={st['complete']} "
          f"truncated={st['truncated']} activated={st['activated']} "
          f"admitted={st['admitted']}",
          f"- 无任何流的 RunID（从未执行 ⇒ NOT_RUN）："
          f"{sumry['runids_without_stream']}",
          f"- 上游阻塞（单独表达）：{len(sumry['upstream_blocked'])} 个 "
          f"{', '.join(sumry['upstream_blocked']) or '（无）'}",
          "", "## 权威准入表", "",
          "| " + " | ".join(MD_COLS) + " |",
          "|" + "|".join("---" for _ in MD_COLS) + "|"]
    for r in rows:
        cells = []
        for k in MD_COLS:
            v = r.get(k, "")
            if isinstance(v, bool):
                v = "yes" if v else "no"
            cells.append(str(v).replace("|", "\\|").replace("\n", " ")[:200])
        L.append("| " + " | ".join(cells) + " |")
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence-root", default=None,
                    help="证据根（默认 $LSU_CHAIN_EVIDENCE_ROOT 或仓库根）")
    ap.add_argument("--runs-root", default=None,
                    help="流根（默认 <evidence-root>/runs/lsu）")
    ap.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    ap.add_argument("--pilots", default=str(DEFAULT_PILOTS))
    ap.add_argument("--out-json", default=str(
        REPO / "docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json"))
    ap.add_argument("--out-md", default=str(
        REPO / "docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md"))
    a = ap.parse_args()

    root, src = resolve_evidence_root(a.evidence_root)
    runs_root = Path(a.runs_root) if a.runs_root else Path(root) / "runs/lsu"
    meta, rows, contract = build(a.contract, a.pilots, root, runs_root)
    meta["evidence_root_source"] = src
    sumry = summarize(meta, rows, contract)
    write_outputs(a.out_json, a.out_md, meta, rows, sumry)

    print(f"[r6-status] evidence_root={meta['evidence_root']} (source={src}) "
          f"matches_contract={meta['evidence_root_matches_contract']}")
    print(f"[r6-status] total_runids={meta['total_runids']}")
    for s in STATES:
        print(f"[r6-status]   {s}: {sumry['states'][s]}")
    st = sumry["streams"]
    print(f"[r6-status] streams total={st['total']} complete={st['complete']} "
          f"truncated={st['truncated']} activated={st['activated']} "
          f"admitted={st['admitted']} runids_without_stream="
          f"{sumry['runids_without_stream']}")
    if not meta["evidence_root_matches_contract"]:
        print("[r6-status] WARNING: 状态表证据根与契约 chain_gate.evidence_root "
              "不一致 —— 两者必须同源（否则两张表描述不同证据）")
    print(f"[r6-status] wrote {a.out_json} and {a.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
