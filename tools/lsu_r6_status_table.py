#!/usr/bin/env python3
"""lsu_r6_status_table.py — [MDSPEC][R6-FIXD2] 逐 RunID 权威状态表（两轴表达）。

规格：`docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md`（§4 状态表 / §5 门禁）
    + `docs/gem5-fi/lsu/mdspec/R6-RULINGS-20261023.md`（**裁决 B — 两轴表达**，权威）。
本工具产出**唯一权威**的逐 RunID 表（JSON + Markdown），每行给出**两条正交轴**
（互不覆盖），并打印两轴计数 + `blocker_code` 分类。

**轴 A `evidence_state`（磁盘实际观测进度，仅五值，永不为 BLOCKED）**：

  NOT_RUN           权威根下**没有任何流** —— 未测量。**绝不被契约 BLOCKED 顶掉**
                    （这正是旧表"325 全短路 BLOCKED ⇒ NOT_RUN 永不出现"的修复）。
  EVIDENCE_MISSING  证据被**声称**（pilot_evidence.json 列了该 RunID/seed）但文件
                    在权威根下缺失/不可读（悬空引用）——与"从未运行"不同。
  TRUNCATED         有流，但 gzip 读不到 EOF 或 stats.txt 缺失/0 字节（流不完整）。
  UNPROVEN          全流完整且有激活，但链**未过** `check_admission`（或完整流内
                    根本没有激活）——"测了但证不出来"。
  PILOT_READY       全部激活样本准入 + 无截断 + 无 Unknown + 无 oversized
                    （**纯磁盘/链事实**，与 eligibility 无关；见裁决 B 要求 1）。

**轴 B `eligibility`（是否被规格/基础设施/模式能力阻塞）**：

  RUNNABLE          无上游独立阻塞。
  BLOCKED           有上游独立阻塞（FS-INFRA / RULING / LICENSE / FS-MULTICORE /
                    MODE-UNIMPL / UNRESOLVED …，取自契约的**上游**判定
                    upstream_status/category，而非其链门禁后的收尾 status）。
                    另给出 `blocker_code`（分类）与 `blocker_detail`（说明）。

两轴**并存**（裁决 B 硬性要求）：
  * 有 blocker 的行，`evidence_state` **仍如实显示**其磁盘事实，同时
    `eligibility=BLOCKED` —— 两者并存，不是二选一。
  * **不得**因 contract 有 blocker 就把磁盘事实短路成 BLOCKED。
  * 权威汇总**同时**报告：各 `evidence_state` 数量 · `RUNNABLE`/`BLOCKED` 数量 ·
    `PILOT_READY` 数量 · `blocker_code` 分类数量；并显式声明
    "`BLOCKED=0` 只表示该维度无 blocker，**不代表**全部实验可运行/已通过"。
  * 正式实验准入依据**仍是 `PILOT_READY`**（evidence PILOT_READY ∧ eligibility
    RUNNABLE），不以 `BLOCKED=0` 代替。

遗留字段（**非权威，仅为向后兼容保留**）：`state`（旧一轴六态），其 BLOCKED 仅当
"本可 PILOT_READY 却被上游阻塞"时出现；下游不得再用它做权威汇报。`STATES`
常量（六值）同样为遗留兼容。

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

# 轴 A：磁盘事实（仅五值，永不为 BLOCKED）
EVIDENCE_STATES = ("NOT_RUN", "EVIDENCE_MISSING", "TRUNCATED", "UNPROVEN",
                   "PILOT_READY")
# 轴 B：是否被阻塞（附 blocker_code / blocker_detail）
ELIGIBILITIES = ("RUNNABLE", "BLOCKED")
# 遗留一轴六态常量（非权威，仅向后兼容；BLOCKED 为旧口径的合成值）
STATES = EVIDENCE_STATES + ("BLOCKED",)
BLOCKER_CODE_ZERO_NOTE = (
    "BLOCKED=0 只表示该统计维度中没有 blocker，不代表全部实验可运行或已通过；"
    "正式准入依据仍是 PILOT_READY（evidence_state=PILOT_READY 且 eligibility=RUNNABLE）。"
)

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
    # ---- 轴 A：磁盘事实（五值，**永不为 BLOCKED**）——纯磁盘/链优先级 ----
    if not samples:
        ev_state = "EVIDENCE_MISSING" if cond["evidence_missing"] else "NOT_RUN"
    elif truncated:
        ev_state = "TRUNCATED"
    elif not activated or refused:
        ev_state = "UNPROVEN"
    elif cond["pilot_ready"]:
        ev_state = "PILOT_READY"
    else:
        ev_state = "UNPROVEN"          # oversized / Unknown 等：证不出来
    # ---- 轴 B：是否被上游独立阻塞（与轴 A 正交，绝不覆盖轴 A）----
    eligibility = "BLOCKED" if upstream_blocked else "RUNNABLE"
    blocker_code = (upstream_cat.strip() or "BLOCKED") if upstream_blocked else "NONE"
    if upstream_blocked:
        blocker_detail = (
            f"上游独立阻塞 {blocker_code}（契约 upstream_status="
            f"{contract_up!r} / upstream_category={upstream_cat!r}）；"
            f"磁盘事实仍如实记为 evidence_state={ev_state}（两轴并存，"
            f"不因 blocker 短路）")
    else:
        blocker_detail = "无上游独立阻塞"
    # ---- 遗留单轴（非权威，仅向后兼容）：BLOCKED 仅当旧口径下会压制 PILOT_READY ----
    legacy_blocked = (bool(samples) and not truncated and bool(activated)
                      and not refused and upstream_blocked)
    state = "BLOCKED" if legacy_blocked else ev_state

    row["conditions"] = cond
    row["evidence_state"] = ev_state
    row["eligibility"] = eligibility
    row["blocker_code"] = blocker_code
    row["blocker_detail"] = blocker_detail
    row["state"] = state          # 遗留：非权威
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
        "failure_reason": _reason(ev_state, eligibility, blocker_code, cond,
                                  refused, samples, upstream_cat, missing,
                                  outside),
    })
    return row


def _reason(state, eligibility, blocker_code, cond, refused, samples,
            upstream_cat, missing, outside=()):
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
            base = "完整流内无注入（fault_id≠0 的 inj）——未激活，未测量；非 Masked"
        else:
            base = (f"{len(refused)} 个激活样本未过 check_admission"
                    f"（含 oversized/Unknown）")
    elif state == "PILOT_READY":
        base = "全部激活样本准入，无截断，无 Unknown"
    else:
        base = f"evidence_state={state}"
    # 轴 B 单独表达：无论磁盘事实如何，blocker 都如实附记（两轴并存）
    if eligibility == "BLOCKED":
        base += (f"；且被上游独立阻塞 {blocker_code or upstream_cat or 'BLOCKED'}"
                 f"——规格/基础设施阻塞不可解除，绝不计为可准入 PILOT_READY")
    return base


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
    counts = Counter(r["state"] for r in rows)          # 遗留单轴
    ev_counts = Counter(r["evidence_state"] for r in rows)   # 轴 A
    el_counts = Counter(r["eligibility"] for r in rows)      # 轴 B
    blk_counts = Counter(r["blocker_code"] for r in rows
                         if r["eligibility"] == "BLOCKED")
    # 正式准入依据 = PILOT_READY（evidence PILOT_READY ∧ eligibility RUNNABLE）
    admissible = sorted(r["run_id"] for r in rows
                        if r["evidence_state"] == "PILOT_READY"
                        and r["eligibility"] == "RUNNABLE")
    return {
        "states": {s: counts.get(s, 0) for s in STATES},     # 遗留（非权威）
        "evidence_states": {s: ev_counts.get(s, 0) for s in EVIDENCE_STATES},
        "eligibility": {e: el_counts.get(e, 0) for e in ELIGIBILITIES},
        "pilot_ready": {
            "count": len(admissible),
            "run_ids": admissible,
            "basis": "evidence_state=PILOT_READY ∧ eligibility=RUNNABLE",
        },
        "evidence_pilot_ready_count": ev_counts.get("PILOT_READY", 0),
        "blocker_codes": dict(sorted(blk_counts.items())),
        "blocker_code_zero_note": BLOCKER_CODE_ZERO_NOTE,
        "streams": {
            "total": sum(r["samples"] for r in rows),
            "complete": sum(r["complete_streams"] for r in rows),
            "truncated": sum(r["truncated_streams"] for r in rows),
            "activated": sum(r["activated_samples"] for r in rows),
            "admitted": sum(r["admitted_samples"] for r in rows),
        },
        "runids_without_stream": sum(1 for r in rows if r["samples"] == 0),
        "evidence_root": meta["evidence_root"],
        "pilot_ready_list": admissible,               # 遗留别名（=准入清单）
        "upstream_blocked": sorted(r["run_id"] for r in rows
                                   if r["upstream_blocked"]),
        "extra_evidence_runids": meta.get("extra_evidence_runids", []),
    }


MD_COLS = ["run_id", "unit", "model", "evidence_state", "eligibility",
           "blocker_code", "state", "contract_upstream_status",
           "upstream_block", "samples", "activated_samples", "admitted_samples",
           "failure_reason"]


def write_outputs(out_json, out_md, meta, rows, sumry):
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(
        {"meta": meta, "summary": sumry, "rows": rows},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    L = ["# R6 逐 RunID 权威状态表（两轴：evidence_state × eligibility）", "",
         f"- 生成时间：{meta['generated_at']}",
         f"- 证据根：`{meta['evidence_root']}`（runs 根 `{meta['runs_root']}`）",
         f"- 契约 `chain_gate.evidence_root`：`{meta['contract_chain_gate_evidence_root']}`"
         f" —— 一致：{'是' if meta['evidence_root_matches_contract'] else '否（响亮告警）'}",
         f"- 总 RunID：{meta['total_runids']}", "",
         "## 轴 A — evidence_state 计数（磁盘事实，仅五值，永不为 BLOCKED）", ""]
    for s in EVIDENCE_STATES:
        L.append(f"- {s}: {sumry['evidence_states'][s]}")
    L += ["", "## 轴 B — eligibility 计数（是否被上游独立阻塞）", ""]
    for e in ELIGIBILITIES:
        L.append(f"- {e}: {sumry['eligibility'][e]}")
    L += ["", "## blocker_code 分类计数", ""]
    for code, n in (sumry["blocker_codes"] or {}).items():
        L.append(f"- {code}: {n}")
    if not sumry["blocker_codes"]:
        L.append("- （无，BLOCKED=0）")
    L += ["",
          f"> {sumry['blocker_code_zero_note']}",
          "",
          f"- 正式准入（PILOT_READY ∧ RUNNABLE）：{sumry['pilot_ready']['count']} 个 "
          f"{', '.join(sumry['pilot_ready']['run_ids']) or '（无）'}",
          f"- 其中 evidence_state=PILOT_READY 的行数（纯磁盘事实）："
          f"{sumry['evidence_pilot_ready_count']}",
          f"- 遗留单轴 `state` 计数（**非权威**）："
          + " ".join(f"{s}={sumry['states'][s]}" for s in STATES)]
    st = sumry["streams"]
    L += ["",
          f"- 流：total={st['total']} complete={st['complete']} "
          f"truncated={st['truncated']} activated={st['activated']} "
          f"admitted={st['admitted']}",
          f"- 无任何流的 RunID（从未执行 ⇒ NOT_RUN）："
          f"{sumry['runids_without_stream']}",
          f"- 上游阻塞（eligibility=BLOCKED）：{len(sumry['upstream_blocked'])} 个 "
          f"{', '.join(sumry['upstream_blocked']) or '（无）'}",
          "", "## 权威表（两轴并存）", "",
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
    print("[r6-status] axis A evidence_state（磁盘事实，永不为 BLOCKED）:")
    for s in EVIDENCE_STATES:
        print(f"[r6-status]   {s}: {sumry['evidence_states'][s]}")
    print("[r6-status] axis B eligibility:")
    for e in ELIGIBILITIES:
        print(f"[r6-status]   {e}: {sumry['eligibility'][e]}")
    print("[r6-status] blocker_code 分类:")
    if sumry["blocker_codes"]:
        for code, n in sumry["blocker_codes"].items():
            print(f"[r6-status]   {code}: {n}")
    else:
        print("[r6-status]   （无，BLOCKED=0）")
    print(f"[r6-status] 正式准入 PILOT_READY(∧RUNNABLE): "
          f"{sumry['pilot_ready']['count']} 个 "
          f"{', '.join(sumry['pilot_ready']['run_ids']) or '（无）'}")
    print(f"[r6-status] NOTE: {sumry['blocker_code_zero_note']}")
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
