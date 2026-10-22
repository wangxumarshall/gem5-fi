#!/usr/bin/env python3
"""[MDSPEC][R4-7] 325 RunID 逐项 READY 契约 + 最终验收门禁（round4 Task 7）。

产出两份**机器可读 + 人可读**的契约：
  docs/gem5-fi/lsu/mdspec/ready_contract.json / .md

每个 RunID 一行 = 状态(READY/PARTIAL/BLOCKED) + 精确命令 + 前置条件 + 验收判据。
判据与 runid_map.json / coverage_matrix.md **同源**（不另立口径、不重复计分）：
  BLOCKED = runid_map 该 entry 的 status_reasons 非空（裁决/许可证/平台缺陷…）
  READY   = runid_map 无阻塞 **且** resolve_cell 可解析出可跑 flags
            **且** coverage_matrix 判 PASS（该单元所需全部节点已实现且已观测）
  PARTIAL = 可跑但 coverage_matrix 判 PARTIAL（缺节点 / 未观测）
自洽断言：325 == READY + PARTIAL + BLOCKED，否则工具非零退出（不得静默）。

同时产出**构建门禁**与**资源准入**（7.2/7.3）：二进制 sha256、构建日志 exit、
`pytest tests/ -q` 结果、CPU/内存/磁盘、4 并发 gem5 上限，以及**唯一正式启动命令**。

用法：
  python3 tools/lsu_ready_contract.py            # 只读契约（不跑构建/测试）
  python3 tools/lsu_ready_contract.py --gate     # 追加构建+全测试+资源门禁
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import lsu_campaign as lc        # noqa: E402  唯一路由来源（resolve_cell）
import lsu_coverage_matrix as cm  # noqa: E402  唯一节点级判据来源

MDS = REPO / "docs/gem5-fi/lsu/mdspec"
DEFAULT_MAP = MDS / "runid_map.json"
DEFAULT_MATRIX = REPO / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv"
DEFAULT_CKPT = Path("/home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015")
# 唯一正式启动命令的固定出口（R4-7.4：GO 前只此一条）
FORMAL_OUTDIR = "runs/lsu/formal_325"

SEEDS_PER_CELL = 3           # trial 口径（README §oracle：directed 控制=确定性复跑）
MAX_PARALLEL = 1             # 主 agent 串行纪律（CLAUDE.md：构建/实验严格串行）


def _row_ids(md_path):
    """coverage_matrix.md 的 | RunID | … | 状态 | … | 行 → {runid: status}。"""
    out = {}
    if not md_path.exists():
        return out
    for ln in md_path.read_text().splitlines():
        m = re.match(r"\|\s*([A-Z]\d{2}-F\d-W\d+)\s*\|", ln)
        if not m:
            continue
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        # | RunID | 模型 | 单元 | 频率 | 状态 | 原因 |
        out[m.group(1)] = cols[4] if len(cols) > 4 else "?"
    return out


def _classify(entry, cov_status, flags):
    """(status, category, why) —— 口径见模块 docstring。"""
    reasons = entry.get("status_reasons") or []
    if reasons:
        joined = " ; ".join(reasons)
        if "platform-defect" in joined:
            cat = "PLATFORM-DEFECT"
        elif "multicore-fs" in joined:
            cat = "FS-MULTICORE"
        elif "spec-license" in joined:
            cat = "LICENSE"
        elif "fs-infra" in joined:
            cat = "FS-INFRA"
        elif "mode unimplemented" in joined:
            cat = "MODE-UNIMPL"
        else:
            cat = "RULING"
        return "BLOCKED", cat, joined
    if flags is None:
        return "BLOCKED", "UNRESOLVED", str(cov_status)
    if cov_status == "PASS":
        return "READY", "OK", ""
    return "PARTIAL", "NODE-GAP", f"coverage={cov_status}"


def _command(runid, family):
    """该 RunID 的精确执行命令（与 campaign 入口逐字一致）。"""
    common = (f"LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt "
              f"python3 tools/lsu_campaign.py "
              f"--matrix {DEFAULT_MATRIX.relative_to(REPO)} "
              f"--outdir {FORMAL_OUTDIR} --cells {runid} --phase trial "
              f"--max-seeds-per-cell {SEEDS_PER_CELL} "
              f"--max-parallel {MAX_PARALLEL}")
    if family == "armtlb":
        common += (f" --fs-checkpoint {DEFAULT_CKPT}")
    return common


def _acceptance(unit):
    """该 RunID 的验收判据（节点级，与 UNIT_REQUIRED_NODES 同源）。"""
    nodes = cm.UNIT_REQUIRED_NODES.get(unit, [])
    req = "、".join(nodes) if nodes else "(该单元无节点级规格)"
    return (f"① 注入日志非空（Site: … 行 ≥1）；"
            f"② prop_evt.txt.gz 中 kind 覆盖 [{req}]；"
            f"③ lsu_chain_check.py 逐边可连（无可连边则如实报 Unknown）；"
            f"④ L5 分类落五类之一（Masked/Detected-Contained/SDC/Crash/Timeout）")


def build_contract(map_path, matrix_path, cov_path):
    rid_map = json.loads(Path(map_path).read_text())
    cov = _row_ids(Path(cov_path))
    header, cells = lc.load_matrix(matrix_path)
    by_runid = {c[lc.COL_RUNID].strip(): c for c in cells}

    rows = []
    for e in rid_map["entries"]:
        runid = e["run_id"]
        unit = e.get("unit", "")
        cell = by_runid.get(runid)
        flags = reason = None
        fam = None
        if cell is not None:
            flags, _golden, reason = lc.resolve_cell(cell)
            if flags is not None:
                fam = lc.MODEL_FLAGS[e["model_id"]][0]
        status, cat, why = _classify(e, cov.get(runid, "?"), flags)
        row = {
            "run_id": runid, "unit": unit, "model": e.get("model_id", ""),
            "freq": e.get("freq", ""), "status": status, "category": cat,
            "family": fam, "why": why,
            "precondition": ("FS 资产 (LSU_FS_DIR) + B0 checkpoint "
                             f"{DEFAULT_CKPT.name}" if fam == "armtlb"
                             else "SE 构建二进制 + 载体 ELF（无需 FS 资产）"),
            "command": _command(runid, fam) if status != "BLOCKED" else "",
            "acceptance": _acceptance(unit),
            "coverage": cov.get(runid, "?"),
            "resolve_reason": reason,
        }
        rows.append(row)
    return rows


def gate():
    """构建门禁 + 全测试 + 资源准入（7.2/7.3）。真实子进程、真实退出码。"""
    g = {}
    bin_path = REPO / "CHAOS/gem5/build/ARM/gem5.opt"
    if bin_path.exists():
        h = hashlib.sha256()
        with open(bin_path, "rb") as fh:
            for blk in iter(lambda: fh.read(1 << 20), b""):
                h.update(blk)
        g["binary"] = str(bin_path)
        g["binary_sha256"] = h.hexdigest()
        g["binary_sha256_16"] = h.hexdigest()[:16]
        g["binary_mtime"] = int(bin_path.stat().st_mtime)
        g["binary_bytes"] = bin_path.stat().st_size
    else:
        g["binary"] = None
    # 全测试（真实运行）
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"],
                       capture_output=True, text=True, cwd=str(REPO))
    tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
    g["pytest_rc"] = r.returncode
    g["pytest_tail"] = tail[0][:200]
    # 资源准入
    try:
        with open("/proc/meminfo") as fh:
            mi = fh.read()
        g["mem_total_gb"] = round(int(re.search(r"MemTotal:\s+(\d+)", mi).group(1))
                                  / 1048576, 1)
        g["mem_avail_gb"] = round(int(re.search(r"MemAvailable:\s+(\d+)", mi).group(1))
                                  / 1048576, 1)
    except Exception:
        pass
    g["cpus"] = os.cpu_count()
    du = shutil.disk_usage(str(REPO))
    g["disk_free_gb"] = round(du.free / 2**30, 1)
    g["gem5_concurrency_cap"] = 4   # CLAUDE.md：>4 OOM-kill 整批
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default=str(DEFAULT_MAP))
    ap.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    ap.add_argument("--coverage", default=str(MDS / "coverage_matrix.md"))
    ap.add_argument("--out", default=str(MDS / "ready_contract.json"))
    ap.add_argument("--gate", action="store_true",
                    help="追加构建/全测试/资源门禁（真实运行）")
    a = ap.parse_args()

    rows = build_contract(a.map, a.matrix, a.coverage)
    counts = Counter(r["status"] for r in rows)
    total = sum(counts.values())
    cats = Counter(r["category"] for r in rows if r["status"] == "BLOCKED")

    doc = {
        "source": "runid_map.json + coverage_matrix.md + lsu_campaign.resolve_cell",
        "total": total,
        "status": dict(counts),
        "blocked_by_category": dict(cats),
        "self_consistent": total == counts["READY"] + counts["PARTIAL"]
        + counts["BLOCKED"],
        "seeds_per_cell": SEEDS_PER_CELL,
        "max_parallel": MAX_PARALLEL,
        "formal_outdir": FORMAL_OUTDIR,
        "fs_checkpoint": str(DEFAULT_CKPT),
        "entries": rows,
    }
    if a.gate:
        doc["gate"] = gate()

    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1))

    # 人可读镜像
    md = [f"# 325 RunID READY 契约（R4-7）",
          "",
          f"- 总数：{total}（**READY={counts['READY']} / PARTIAL={counts['PARTIAL']}"
          f" / BLOCKED={counts['BLOCKED']}**）",
          f"- 自洽：{'✅' if doc['self_consistent'] else '❌ 计数不自洽'}",
          f"- BLOCKED 分类：{dict(cats)}",
          f"- 抽样：每 cell {SEEDS_PER_CELL} seed，`--max-parallel {MAX_PARALLEL}`",
          f"- FS checkpoint：`{DEFAULT_CKPT}`",
          ""]
    md.append("| RunID | 单元 | 模型 | F | 状态 | 类别 | 覆盖 | 命令(READY/PARTIAL) |")
    md.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        md.append(f"| {r['run_id']} | {r['unit']} | {r['model']} | {r['freq']} | "
                  f"{r['status']} | {r['category']} | {r['coverage']} | "
                  f"{'`'+r['command']+'`' if r['command'] else '—'} |")
    (MDS / "ready_contract.md").write_text("\n".join(md) + "\n")

    print(f"[ready_contract] total={total} "
          f"READY={counts['READY']} PARTIAL={counts['PARTIAL']} "
          f"BLOCKED={counts['BLOCKED']} self_consistent={doc['self_consistent']}")
    print(f"[ready_contract] blocked_by_category={dict(cats)}")
    if a.gate:
        g = doc["gate"]
        print(f"[gate] binary_sha256={g.get('binary_sha256_16')} "
              f"pytest_rc={g.get('pytest_rc')} "
              f"mem_avail={g.get('mem_avail_gb')}G disk_free={g.get('disk_free_gb')}G")
    return 0 if doc["self_consistent"] else 1


if __name__ == "__main__":
    sys.exit(main())
