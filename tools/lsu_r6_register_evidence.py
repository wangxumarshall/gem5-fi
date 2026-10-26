#!/usr/bin/env python3
"""[MDSPEC][R6-EVIDENCE] L17：扫盘发现 PROP-EVT 证据 → 重生成 chain-gate 用的
pilot 证据注册表（docs/gem5-fi/lsu/mdspec/pilot_evidence.json）。

动机（为什么需要这个工具）
--------------------------------------------------
tools/lsu_ready_contract.py（R6-GATE 之后的版本）对每个 RunID 调
`chain_admission(runid)`：它从 `docs/gem5-fi/lsu/mdspec/pilot_evidence.json`
取出该 RunID 及其 `<runid>-seed<N>` 的**全部** pilot 样本，把每条样本的
`path` 相对 `LSU_CHAIN_EVIDENCE_ROOT`（默认 = 工具所在仓库）解析后读 PROP-EVT，
逐个过 `lsu_chain_check.check_admission`；**任一**样本不被准入即整行不准入。
只有极少数 RunID 被登记过，于是大量**真实存在**证据的行被归为
CHAIN-EVIDENCE-MISSING —— 不是链有问题，而是证据从未登记。本工具把"磁盘上
真有什么"如实折算成注册表，登记口径与 tools/lsu_pilot_evidence.py **同构**
（同一批字段名），故注册表可直接被契约工具消费，无需改动任何工具。

发现规则（对每个 --runs-root，默认 <evidence-root>/runs/lsu）
--------------------------------------------------
1. 递归找 `prop_evt.txt.gz`；
2. 自路径**最深**向上找第一个匹配矩阵 RunID 的目录段：
     * `^[A-Z]\d{2}-F\d-W\d+$`（如 T04-F0-W4），或
     * `^(<RunID>)-s(?:eed)?(\d+)$`（如 T04-F0-W4-seed1，RunID=前缀）；
3. seed：RunID 段的正下一段若为 `seed<N>` / `s<N>` 则取之；否则为
   `<RunID>-seed<N>` 形式；再否则无 seed；
4. 注册键 = 无 seed 时 `<RunID>`，有 seed 时 `<RunID>-seed<N>`
   —— 这正是 `chain_admission` 的 `k == runid or k == f"{runid}-seed{N}"`
   两种匹配形状；多 seed 全部登记（门禁要求"全员准入"，不得只挑样本）。

诚实纪律（本工具的全部立场）
--------------------------------------------------
* **truncated**：gzip 未读完（`lsu_prop_fields.read_events` 报截断）**或**
  同目录无 `stats.txt` → 置 True。这类证据**照样登记**（存在即事实），但
  打上截断标注，绝不当成完整证据静默使用。
* **重复**（同一 RunID+seed 出现在多个 run 目录）：按 mtime 最新者为主，
  其余**逐条记入** `shadowed_paths`（条目级）与顶层 `duplicates`（汇总）。
  没有静默丢样本。
* **无归属**：路径里找不到 RunID 段的 prop_evt（辅助/机制/探针跑，
  span 目录等）**不静默丢弃** → 全部进顶层 `unmatched` 并计数打印。
* **unit**：复用 tools/lsu_pilot_evidence.unit_of（唯一归属口径，不二次
  硬编码），并把依据写进 `unit_source`；无法归属 → unit=null。
* `faults`：与 lsu_pilot_evidence 同源（`lsu_chain_check._group_by_fault`），
  该私有 API 若被并行车道改名 → 退回本地等价实现并在
  `fault_count_method` 里**如实标注**走了哪条路。
* **不静默丢旧条目**（`--carry-existing`，默认 = 本仓库现有注册表）：旧注册表里
  键不是矩阵 RunID 的**辅助运行**条目（MSHRREF / span / 机制探针等）本工具的
  扫盘规则**不会**重建，直接覆盖就会悄悄丢掉它们贡献的 kind —— 实测会丢
  `exmon_monitor` / `exmon_rmw` / `exmon_stxr` 三个 kind，进而影响
  lsu_coverage_matrix 的"全局 kind 并集"判据。故：旧条目只要其文件在任一扫描
  根下**真实存在**，即原样保留（path 重写为可解析形式，字段取旧值并标
  fields_source="carried-over"）；找不到文件的旧条目**不**保留，但逐条列入
  `dropped_existing` 响亮报出。

用法
--------------------------------------------------
    python3 tools/lsu_r6_register_evidence.py --out /tmp/pilot_evidence.json
    python3 tools/lsu_r6_register_evidence.py --out OUT.json \
        --runs-root /home/sdc/gem5-fi-ding/runs/lsu \
        --runs-root /home/sdc/gem5-fi-ding/.claude/worktrees/<w>/runs/lsu \
        --evidence-root /home/sdc/gem5-fi-ding
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import lsu_prop_fields as P            # noqa: E402  PROP-EVT 解析
import lsu_pilot_evidence as PE        # noqa: E402  唯一 unit 归属口径（unit_of）

try:                                   # 与 lsu_pilot_evidence 同源；被改名则退回本地
    import lsu_chain_check as CC       # noqa: E402
    _HAS_CC = hasattr(CC, "_group_by_fault")
except Exception:                      # pragma: no cover - 仅在并行车道改名时触发
    CC = None
    _HAS_CC = False

DEFAULT_EVIDENCE_ROOT = Path("/home/sdc/gem5-fi-ding")
RUNID_RE = re.compile(r"^[A-Z]\d{2}-F\d-W\d+$")
RUNID_SEED_RE = re.compile(r"^([A-Z]\d{2}-F\d-W\d+)-s(?:eed)?(\d+)$")
SEED_RE = re.compile(r"^(?:seed|s)(\d+)$")


def _fault_count(events):
    """fault_id 取值个数（fault_id 为空或 "0" 的非链事件不计）。

    语义与 lsu_chain_check._group_by_fault 完全一致（那是 pilot_evidence 的
    口径来源）；此处优先调用它，被改名时退回本地等价实现并如实标注。
    """
    if _HAS_CC:
        return len(CC._group_by_fault(events)), "lsu_chain_check._group_by_fault"
    return len({e.get("fault_id") for e in events
                if e.get("fault_id") and e.get("fault_id") != "0"}), "local"


def parse_runid_seed(rel_parts):
    """路径分量 → (run_id, seed) 或 (None, None)。规则见模块 docstring。"""
    for i in range(len(rel_parts) - 1, -1, -1):
        comp = rel_parts[i]
        if RUNID_RE.match(comp):
            seed = None
            if i + 1 < len(rel_parts):
                m = SEED_RE.match(rel_parts[i + 1])
                if m:
                    seed = int(m.group(1))
            return comp, seed
        m = RUNID_SEED_RE.match(comp)
        if m:
            return m.group(1), int(m.group(2))
    return None, None


def key_of(run_id, seed):
    return run_id if seed is None else f"{run_id}-seed{seed}"


def discover(runs_roots, evidence_root):
    """扫盘 → (candidates, unmatched)；candidates 按 (run_id, seed) 分组。"""
    candidates, unmatched = {}, []
    for root in runs_roots:
        if not root.exists():
            unmatched.append({"runs_root": str(root),
                              "path": None,
                              "reason": f"runs root 不存在：{root}"})
            continue
        for f in sorted(root.rglob("prop_evt.txt.gz")):
            rel = f.relative_to(root)
            run_id, seed = parse_runid_seed(rel.parts[:-1])
            if run_id is None:
                unmatched.append({
                    "runs_root": str(root), "path": str(rel),
                    "reason": "路径中无矩阵 RunID 段（<RunID> 或 "
                              "<RunID>-seed<N>）——辅助/机制/探针跑，本工具不"
                              "冒充 RunID 登记"})
                continue
            candidates.setdefault((run_id, seed), []).append(
                {"runs_root": str(root), "abs": f})
    return candidates, unmatched


def build_entry(chosen, run_id, seed, evidence_root, map_entries, faults_method):
    path = chosen["abs"]
    events, read_trunc = P.read_events(path)
    kinds = sorted({e["kind"] for e in events if e.get("kind")})
    faults, method = _fault_count(events)
    faults_method.add(method)
    no_stats = not (path.parent / "stats.txt").exists()
    truncated = bool(read_trunc) or no_stats
    unit, basis = PE.unit_of(run_id, map_entries)
    try:
        rel = path.relative_to(evidence_root)
        out_path, kind = str(rel), "relative"
    except ValueError:
        out_path, kind = str(path), "absolute"
    return {
        "unit": unit,
        "unit_source": basis,
        "path": out_path,
        "path_kind": kind,          # 门禁 root/rel 连接对绝对路径同样成立
        "kinds": kinds,
        "events": len(events),
        "truncated": truncated,
        "truncated_reasons": ([r for r, on in
                               (("gzip_read_incomplete", read_trunc),
                                ("no_sibling_stats_txt", no_stats)) if on]),
        "faults": faults,
        "seed": seed,
        "runs_root": chosen["runs_root"],
    }


def carry_over(existing_path, pilots, runs_roots, evidence_root):
    """保留旧注册表里扫盘规则重建不了的条目（**存在即保留**，否则响亮报出）。

    返回 (carried_keys, dropped)；dropped = [{key, path, reason}]。
    只保留**文件真实存在**的条目；path 重写为可解析形式（相对 evidence-root，
    否则绝对路径）。字段取旧值，`fields_source` 如实标注"未重读、沿用旧值"。
    """
    if not existing_path or not Path(existing_path).exists():
        return [], []
    try:
        old = json.loads(Path(existing_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], []
    bases = [evidence_root] + [r.parent.parent for r in runs_roots]
    carried, dropped = [], []
    for key, v in (old.get("pilots") or {}).items():
        if key in pilots:
            dropped.append({"key": key, "path": v.get("path", ""),
                            "reason": "由本次扫描的同键条目取代（扫盘为真值）"})
            continue
        # 同一个 RunID 的旧条目：本次扫描已按 <RunID>-seed<N> 展开 → 不重复登记
        # （同一 cell 的多个副本只保留最新者，否则 n_samples 会被同一次运行灌水，
        #  门禁判据失真）。仍如实报出，不静默。
        base = key if RUNID_RE.match(key) else (
            RUNID_SEED_RE.match(key).group(1) if RUNID_SEED_RE.match(key) else None)
        if base and any(k == base or RUNID_SEED_RE.match(k) and
                        RUNID_SEED_RE.match(k).group(1) == base for k in pilots):
            dropped.append({"key": key, "path": v.get("path", ""),
                            "reason": f"{base} 已由本次扫描的 seed 样本覆盖"
                                      f"（取较新者，同一 cell 不重复计样本）"})
            continue
        rel = v.get("path", "")
        found = next((b / rel for b in bases
                      if rel and (b / rel).exists()), None)
        if found is None:
            dropped.append({"key": key, "path": rel,
                            "reason": "旧注册表条目文件在任一扫描根下均不存在"})
            continue
        try:
            out_path = str(found.resolve().relative_to(evidence_root))
            kind = "relative"
        except ValueError:
            out_path, kind = str(found.resolve()), "absolute"
        no_stats = not (found.parent / "stats.txt").exists()
        entry = {
            "unit": v.get("unit"), "unit_source": v.get("unit_source"),
            "path": out_path, "path_kind": kind,
            "kinds": sorted(v.get("kinds") or []),
            "events": v.get("events"),
            "truncated": bool(v.get("truncated")) or no_stats,
            "truncated_reasons": ["carried_over_flag"] * bool(v.get("truncated"))
                                 + ["no_sibling_stats_txt"] * no_stats,
            "faults": v.get("faults"),
            "seed": None,
            "runs_root": str(found.parent.parent.parent),
            "fields_source": "carried-over (旧条目沿用，未重读 PROP-EVT)",
        }
        pilots[key] = entry
        carried.append(key)
    return carried, dropped


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT),
                    help="注册表 path 的相对根（= 门禁 LSU_CHAIN_EVIDENCE_ROOT）")
    ap.add_argument("--runs-root", action="append", default=None,
                    help="可重复；默认 <evidence-root>/runs/lsu")
    ap.add_argument("--carry-existing", default=str(
        REPO / "docs/gem5-fi/lsu/mdspec/pilot_evidence.json"),
        help="旧注册表：其中扫盘规则重建不了但文件仍存在的条目原样保留"
             "（避免静默丢 kind）；传空串可关闭")
    a = ap.parse_args()

    evidence_root = Path(a.evidence_root).resolve()
    runs_roots = ([Path(p).resolve() for p in a.runs_root] if a.runs_root
                  else [evidence_root / "runs/lsu"])
    map_entries = PE._map_entries()
    candidates, unmatched = discover(runs_roots, evidence_root)

    pilots, shadows, faults_method = {}, [], set()
    for (run_id, seed), cands in sorted(candidates.items()):
        # 同一 RunID+seed 的多个副本：mtime 最新者为主，其余逐条记录（不静默丢）
        cands = sorted(cands, key=lambda c: (-c["abs"].stat().st_mtime,
                                             str(c["abs"])))
        chosen, others = cands[0], cands[1:]
        key = key_of(run_id, seed)
        entry = build_entry(chosen, run_id, seed, evidence_root, map_entries,
                            faults_method)
        if others:
            entry["shadowed_paths"] = [str(c["abs"].relative_to(c["runs_root"])
                                           if _is_under(c["abs"], c["runs_root"])
                                           else c["abs"]) for c in others]
            shadows.append({"key": key, "chosen": str(chosen["abs"]),
                            "shadowed": entry["shadowed_paths"]})
        pilots[key] = entry

    carried, dropped = carry_over(a.carry_existing, pilots, runs_roots,
                                 evidence_root)

    union, by_unit = set(), {}
    for p in pilots.values():
        union.update(p["kinds"])
        if p["unit"]:
            by_unit.setdefault(p["unit"], set()).update(p["kinds"])

    trunc = sorted(k for k, p in pilots.items() if p["truncated"])
    doc = {
        "generated_by": "tools/lsu_r6_register_evidence.py",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator_repo_head": _head(),
        "evidence_root": str(evidence_root),
        "runs_roots": [{"path": str(r),
                        "volatile": ".claude/worktrees" in str(r),
                        "prop_evt_found": sum(
                            1 for c in candidates.values()
                            for x in c if x["runs_root"] == str(r))}
                       for r in runs_roots],
        "fault_count_method": sorted(faults_method),
        "schema_note": ("字段与 tools/lsu_pilot_evidence.py 同构；额外字段："
                        "path_kind/truncated_reasons/seed/runs_root/"
                        "shadowed_paths 及本文件顶层元数据。门禁只读 pilots。"),
        "pilots": pilots,
        "kinds_observed": sorted(union),
        "kinds_observed_by_unit": {k: sorted(v) for k, v in by_unit.items()},
        "truncated_keys": trunc,
        "duplicate_keys": shadows,
        "unmatched_prop_evt": unmatched,
        "carried_over_keys": sorted(carried),
        "dropped_existing": dropped,
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"[r6-register] roots={len(runs_roots)} pilots={len(pilots)} "
          f"(runids={len({v['seed'] is not None and k.split('-seed')[0] or k for k, v in pilots.items()})}) "
          f"unmatched={len(unmatched)} duplicated_keys={len(shadows)} "
          f"truncated={len(trunc)} kinds={len(union)}")
    print(f"[r6-register] fault_count_method={sorted(faults_method)} → {out}")
    for k in trunc:
        print(f"  TRUNCATED {k:26s} reasons={pilots[k]['truncated_reasons']}")
    for u in unmatched:
        print(f"  UNMATCHED {u['path']} :: {u['reason']}")
    return 0


def _is_under(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _head():
    try:
        import subprocess
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short",
                               "HEAD"], capture_output=True, text=True
                              ).stdout.strip() or None
    except Exception:
        return None


if __name__ == "__main__":
    sys.exit(main())
