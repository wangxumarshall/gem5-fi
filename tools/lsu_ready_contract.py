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
import lsu_chain_check as chain   # noqa: E402  R6-GATE：链准入门禁（唯一判定源）
import lsu_prop_fields as P       # noqa: E402  PROP-EVT 解析（门禁输入）

MDS = REPO / "docs/gem5-fi/lsu/mdspec"
# [R6-GATE] 链准入门禁（Agent B）：READY 不再仅凭 coverage PASS 得出——须由
# 该 RunID 的 pilot PROP-EVT 证据经 lsu_chain_check.check_admission 准入
# （完整 L0→L5 链，或显式 containment 且后续层全 N/A(contained)）。证据
# 路径以 pilot_evidence.json 记录的仓库相对 path 解析到 LSU_CHAIN_EVIDENCE_ROOT
# （默认 REPO；未跟踪的 runs/ pilot 数据在基础 worktree 中，故运行时可覆盖）。
PILOT_EVIDENCE = MDS / "pilot_evidence.json"
CHAIN_EVENT_CAP = 4000   # 单样本事件上限：超出→响亮不判（绝不默认通过）
DEFAULT_MAP = MDS / "runid_map.json"
DEFAULT_MATRIX = REPO / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv"
DEFAULT_CKPT = Path("/home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015")
# 唯一正式启动命令的固定出口（R4-7.4：GO 前只此一条）
FORMAL_OUTDIR = "runs/lsu/formal_325"

SEEDS_PER_CELL = 3           # pilot/trial 口径（非正式；仅供 pilot 复现）
MAX_PARALLEL = 1             # 主 agent 串行纪律（CLAUDE.md：构建/实验严格串行）

# ---- 正式 campaign 口径（来自 `完整任务执行清单.md` §全局实验口径，2026-10-08 生效）----
# pilot     : 每有效 RunID 先取 30 个独立 activated runs/clusters（检查注入器/负载/oracle）
# 正式筛查  : 每有效 RunID **固定累计 ≥385** 个独立 activated（统一报 Wilson 95% CI）
# 重点扩样  : 仅下列 **21 个固定 RunID** 累计到 **2401**（含前 385，非额外再取）
# 采样数量**在 campaign 开始前固定**；**禁止**按中途点估计或普通 CI 半宽序贯停止
#            ⇒ 正式 phase 用 `screening`（到量即停），**不**用 `main`（Wilson 序贯，违反本政策）。
# 逐 cell F0–F6 注入节律由 07 展开矩阵逐行定义（F0=每 run 1 次均匀抽样；
# F1≈1/1e6 eligible；F2≈1/1e5 eligible），**不在 phase 参数里**。
FORMAL_PHASE = "screening"
SCREENING_TARGET = 385
FOCUS_TARGET = 2401
FOCUS_RUNIDS = frozenset({
    "A01-F0-W3", "A04-F0-W3", "T10-F0-W4", "T04-F0-W4", "S13-F0-W5",
    "S04-F0-W5", "L01-F0-W5", "L03-F0-W5", "C04-F0-W6", "C05-F0-W6",
    "C10-F0-W6", "C12-F0-W6", "O01-F0-W7", "O05-F0-W7", "P03-F0-W8",
    "P07-F0-W8", "P09-F0-W6", "T10-F0-W11", "S13-F0-W12", "O09-F0-W13",
    "P09-F0-W13",
})
FORMAL_SEED_CAP = 100000     # 上限（activated 为停机判据；避免 seed-cap 提前截断）
# 启动门禁资源红线（与 tools/lsu_guard.py 同源）
DISK_MIN_FREE_GIB = 50.0
DISK_MIN_FREE_PCT = 0.20
MEM_MIN_AVAIL_GIB = 10.0     # lsu_guard STOP_DISPATCH_MEM_GIB
GEM5_CONCURRENCY_CAP = 4     # >4 并发 OOM-kill 整批（CLAUDE.md）


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


def _classify(entry, cov_status, flags, reason=None):
    """(status, category, why) —— 口径见模块 docstring。

    [LSU][MDSPEC][R4-8-SPEC] 每个互斥类别**显式**判据 + 兜底报警。此前 A06 与
    T08 都靠 `else: cat = "RULING"` 兜底落到 RULING —— 那是**静默**的：R4-5.9
    把 `MODEL_BLOCKED["T08"]` 文案从 "mode unimplemented: walk pairing" 改成
    "landed compile-unverified, pilot pending" 后，T08-F{0,4,6}-W9 的类别就
    **无声**从 MODE-UNIMPL 变成 RULING（RULING 6→9），而台账（runid_map）与
    分类器都不出声。现改为：A06 的 "ruling" 与 T08 的 "pilot pending"/"mode
    unimplemented" 各自显式匹配；任何落到兜底的理由一律标为 UNCLASSIFIED
    并计数（响亮的未知，绝不冒充某个具体类别）。
    """
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
        elif ("mode unimplemented" in joined or "pilot pending" in joined
              or "sub-model modes" in joined):   # [R4-8-INT] 合并后的 T08 措辞
                                                 # 仍属「子模型模式未实现」类
            cat = "MODE-UNIMPL"
        elif "ruling" in joined:
            cat = "RULING"
        else:
            cat = "UNCLASSIFIED"
        return "BLOCKED", cat, joined
    if flags is None:
        # [R5-U5] 此前返回 cov_status（多为 "PASS"），使被拒绝的行在 why 字段里
        # 自报 "PASS" —— 一条 BLOCKED 行声称通过，属误导性陈述。改为如实引用
        # resolve_cell 的拒绝理由。
        return "BLOCKED", "UNRESOLVED", (reason or "resolve_cell 拒绝（未给出理由）")
    if cov_status == "PASS":
        return "READY", "OK", ""
    return "PARTIAL", "NODE-GAP", f"coverage={cov_status}"


def _command(runid, family):
    """该 RunID 的**正式**执行命令（phase/样本量取自清单 §全局实验口径）。

    默认 RunID：固定累计 ≥385 activated；21 个重点 RunID：累计 2401。
    禁止 trial/3-seed（那是 pilot）与 main/Wilson 序贯（违反固定样本量政策）。
    """
    target = FOCUS_TARGET if runid in FOCUS_RUNIDS else SCREENING_TARGET
    common = (f"LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt "
              f"python3 tools/lsu_campaign.py "
              f"--matrix {DEFAULT_MATRIX.relative_to(REPO)} "
              f"--outdir {FORMAL_OUTDIR} --cells {runid} "
              f"--phase {FORMAL_PHASE} --screening-target {target} "
              f"--max-seeds-per-cell {FORMAL_SEED_CAP} "
              f"--max-parallel {MAX_PARALLEL}")
    if family == "armtlb":
        common += (f" --fs-checkpoint {DEFAULT_CKPT}")
    return common


def verdict(doc):
    """真 GO/NO-GO 判定。BLOCKED>0 / 测试失败 / 资源不足 / 命令仍是 trial → NO-GO。

    仅当**全部**条件满足才 GO：BLOCKED==0 且 self_consistent 且 gate 各项达标。
    """
    reasons = []
    if not doc.get("self_consistent"):
        reasons.append("契约计数不自洽")
    st = doc["status"]
    if st.get("BLOCKED", 0) > 0:
        reasons.append(f"BLOCKED={st['BLOCKED']} > 0（{doc['blocked_by_category']}）")
    if st.get("PARTIAL", 0) > 0:
        reasons.append(f"PARTIAL={st['PARTIAL']} > 0")
    g = doc.get("gate")
    if not g:
        reasons.append("未运行 --gate 资源/测试门禁")
    else:
        if not g.get("binary_sha256"):
            reasons.append("正式二进制缺失")
        if g.get("pytest_rc") != 0:
            reasons.append(f"pytest_rc={g.get('pytest_rc')} != 0（{g.get('pytest_tail','')}）")
        # [R5-U2] 全套件结果（pytest 未收集的独立脚本单列，不得被 pytest_rc 掩盖）
        # [R5-U7] F1：先看运行器自身是否正常。此前只读 tests_fail/tests_env_blocked，
        # 而它们来自"运行器崩溃即回退 {UNKNOWN:1}"的 JSON —— 于是运行器挂掉时
        # tests_fail=0、无任何 NO-GO 理由，门禁静默放行（伪装为"无失败"）。
        if g.get("tests_rc") not in (0, None):
            reasons.append(f"全套件运行器 tests_rc={g.get('tests_rc')} != 0"
                           "（运行器自身失败/超时，其结果不可采信）")
        if "UNKNOWN" in (g.get("tests_counts") or {}):
            reasons.append("全套件计数不可得（tests_counts=UNKNOWN）——"
                           "运行器未产出结果，不得视为『无失败』")
        if g.get("tests_fail", 0) > 0:
            reasons.append(f"全套件 FAIL={g['tests_fail']}"
                           f"（{g.get('tests_counts')}）")
        if g.get("tests_env_blocked", 0) > 0:
            reasons.append(f"全套件 ENV 阻塞={g['tests_env_blocked']} 项未判定"
                           "（缺二进制/资产，不得计入通过）")
        du = shutil.disk_usage(str(REPO))
        tot_gib = du.total / 2 ** 30
        floor = max(DISK_MIN_FREE_GIB, DISK_MIN_FREE_PCT * tot_gib)
        if g.get("disk_free_gb", 0) < floor:
            reasons.append(f"磁盘 free {g.get('disk_free_gb')}G < 红线 {floor:.1f}G")
        if g.get("mem_avail_gb", 0) < MEM_MIN_AVAIL_GIB:
            reasons.append(f"MemAvailable {g.get('mem_avail_gb')}G < {MEM_MIN_AVAIL_GIB}G")
    # 正式命令不得仍是 pilot 口径
    cmds = [r["command"] for r in doc["entries"] if r.get("command")]
    if any("--phase trial" in c for c in cmds):
        reasons.append("正式命令仍为 pilot（--phase trial）")
    if any(f"--phase {FORMAL_PHASE}" not in c for c in cmds):
        reasons.append(f"存在非 {FORMAL_PHASE} phase 的正式命令")
    go = not reasons
    return {"verdict": "GO" if go else "NO-GO",
            "formal_phase": FORMAL_PHASE,
            "screening_target": SCREENING_TARGET,
            "focus_target": FOCUS_TARGET,
            "focus_runids": sorted(FOCUS_RUNIDS),
            "reasons": reasons or ["全部准入条件满足"]}


def _acceptance(unit):
    """该 RunID 的验收判据（节点级，与 UNIT_REQUIRED_NODES 同源）。"""
    nodes = cm.UNIT_REQUIRED_NODES.get(unit, [])
    req = "、".join(nodes) if nodes else "(该单元无节点级规格)"
    return (f"① 注入日志非空（Site: … 行 ≥1）；"
            f"② prop_evt.txt.gz 中 kind 覆盖 [{req}]；"
            f"③ lsu_chain_check.py 逐边可连（无可连边则如实报 Unknown）；"
            f"④ L5 分类落五类之一（Masked/Detected-Contained/SDC/Crash/Timeout）")


def _evidence_root(evidence_root=None):
    if evidence_root:
        return Path(evidence_root)
    return Path(os.environ.get("LSU_CHAIN_EVIDENCE_ROOT") or REPO)


def chain_admission(runid, pilots=None, evidence_root=None):
    """[R6-GATE] 该 RunID 的链准入门禁判定（唯一判定源 = check_admission）。

    取 pilot_evidence.json 中 runid 及其 `<runid>-seed<N>` 全部 pilot 样本，
    逐一读 PROP-EVT 并过 check_admission；**全员 admitted 且至少评估 1 例**
    才准入（任一样本 Unknown/伪链即整体不准入——诚实纪律）。返回
    {admitted, terminal, violations, n_samples, evaluated, note}。
    证据缺失或超事件上限 → 不准入并响亮给因（绝不默认通过）。
    """
    pilots = _load_pilots() if pilots is None else pilots
    root = _evidence_root(evidence_root)
    seed_re = re.compile(rf"^{re.escape(runid)}-seed\d+$")
    samples = [v for k, v in pilots.items()
               if k == runid or seed_re.match(k)]
    out = {"admitted": None, "terminal": None, "violations": [],
           "n_samples": len(samples), "evaluated": 0, "note": ""}
    if not samples:
        out["note"] = (f"无 {runid} 的 pilot 证据（pilot_evidence.json 中无该 "
                       f"RunID 或其 seed 样本）——链不可证")
        return out
    results = []
    for s in samples:
        rel = s.get("path", "")
        p = root / rel if rel else None
        if not rel or not p.exists():
            results.append({"admitted": False, "terminal": None,
                            "violations": [f"chain_evidence_missing: {runid} "
                                           f"证据文件缺 {rel or '(无 path)'}"
                                           f"（root={root}）"]})
            continue
        events, _tr = P.read_events(p)
        if len(events) > CHAIN_EVENT_CAP:
            results.append({"admitted": False, "terminal": None,
                            "violations": [f"chain_evidence_too_large: {runid} "
                                           f"{rel} 事件 {len(events)} > 上限 "
                                           f"{CHAIN_EVENT_CAP}——未评估，绝不"
                                           f"默认通过"]})
            continue
        bundle = {"run_id": runid,
                  "activated": max(1, int(s.get("faults") or 1)),
                  "events": events, "rc": 0}
        results.append(chain.check_admission(bundle))
    out["evaluated"] = sum(1 for r in results if r.get("admitted") is not None)
    out["admitted"] = bool(results) and all(r.get("admitted") for r in results)
    for r in results:
        out["violations"].extend(r.get("violations") or [])
    terms = [r.get("terminal") for r in results if r.get("terminal")]
    out["terminal"] = terms[0] if terms else None
    return out


def _load_pilots(path=None):
    p = Path(path) if path else PILOT_EVIDENCE
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("pilots", {})
    except (OSError, ValueError):
        return {}


def build_contract(map_path, matrix_path, cov_path, pilots=None,
                   evidence_root=None):
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
        status, cat, why = _classify(e, cov.get(runid, "?"), flags, reason)
        # [R6-GATE] 硬门：非 BLOCKED 行必须过链准入门禁，否则降级 BLOCKED。
        # 此前 READY 仅凭 coverage PASS（=节点 kind 曾观测到）即可得——该口径
        # 可无真链（activated=1/RC=0/裸 chain_end）而通过，是本门禁要堵的洞。
        chain_res = None
        if status in ("READY", "PARTIAL"):
            chain_res = chain_admission(runid, pilots, evidence_root)
            if not chain_res["admitted"]:
                if chain_res["n_samples"] == 0:
                    cat = "CHAIN-EVIDENCE-MISSING"
                    why = chain_res["note"]
                else:
                    cat = "CHAIN-UNPROVEN"
                    toks = []
                    for v in chain_res["violations"]:
                        tok = v.split(":", 1)[0].strip()
                        if tok and tok not in toks:
                            toks.append(tok)
                    why = (f"{runid} 链未准入（违规规则 {toks}）: "
                           + " ; ".join(chain_res["violations"][:2]))
                status = "BLOCKED"
        row = {
            "run_id": runid, "unit": unit, "model": e.get("model_id", ""),
            "chain": chain_res,
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
    # [R5-U2] 全部套件（含 pytest 不收集的 ~40 个独立脚本）。这些脚本
    # **无论成败都 exit 0**，故 pytest_rc 与 returncode 都不足以证明通过 ——
    # 必须由 tools/lsu_test_runner.py 解析真实输出判定（该文件头部有动机说明）。
    tj = f"/tmp/lsu_gate_tests_{os.getpid()}.json"
    tr = subprocess.run([sys.executable, "tools/lsu_test_runner.py",
                         "--quiet", "--json", tj],
                        capture_output=True, text=True, cwd=str(REPO))
    ttail = (tr.stdout or "").strip().splitlines()[-1:] or [""]
    g["tests_rc"] = tr.returncode
    g["tests_tail"] = ttail[0][:200]
    try:
        counts = json.loads(Path(tj).read_text())["counts"]
    except Exception:
        counts = {"UNKNOWN": 1}
    g["tests_counts"] = counts
    g["tests_fail"] = counts.get("FAIL", 0)
    g["tests_env_blocked"] = counts.get("ENV", 0)
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
        # [R6-GATE] 链准入门禁记录：证据根 + 判定口径（可复现）
        "chain_gate": {
            "rule": "READY requires lsu_chain_check.check_admission admission "
                    "on this RunID's pilot PROP-EVT (complete family-specific "
                    "L0→L5 chain, or explicit containment with later layers "
                    "N/A(contained))",
            "evidence_root": str(_evidence_root()),
            "event_cap": CHAIN_EVENT_CAP,
            "admitted": sum(1 for r in rows if (r.get("chain") or {})
                            .get("admitted") is True),
            "unproven": sum(1 for r in rows if r.get("category")
                            == "CHAIN-UNPROVEN"),
            "evidence_missing": sum(1 for r in rows if r.get("category")
                                    == "CHAIN-EVIDENCE-MISSING"),
        },
        "seeds_per_cell": SEEDS_PER_CELL,
        "max_parallel": MAX_PARALLEL,
        "formal_outdir": FORMAL_OUTDIR,
        "fs_checkpoint": str(DEFAULT_CKPT),
        "entries": rows,
    }
    if a.gate:
        doc["gate"] = gate()
    doc["verdict"] = verdict(doc)

    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1))

    # 人可读镜像
    md = [f"# 325 RunID READY 契约（R4-7）",
          "",
          f"- 总数：{total}（**READY={counts['READY']} / PARTIAL={counts['PARTIAL']}"
          f" / BLOCKED={counts['BLOCKED']}**）",
          f"- 自洽：{'✅' if doc['self_consistent'] else '❌ 计数不自洽'}",
          f"- BLOCKED 分类：{dict(cats)}",
          f"- **链准入门禁（R6-GATE）**：READY 须经 "
          f"`lsu_chain_check.check_admission` 准入（完整 family-specific "
          f"L0→L5 链，或显式 containment 且后续层全 N/A(contained)）。"
          f"证据根 `{doc['chain_gate']['evidence_root']}`，事件上限 "
          f"{doc['chain_gate']['event_cap']}；admitted={doc['chain_gate']['admitted']}"
          f" / CHAIN-UNPROVEN={doc['chain_gate']['unproven']}"
          f" / CHAIN-EVIDENCE-MISSING={doc['chain_gate']['evidence_missing']}",
          f"- **准入裁决：{doc['verdict']['verdict']}**"
          + ("" if doc['verdict']['verdict'] == "GO"
             else f"（{'；'.join(doc['verdict']['reasons'])}）"),
          f"- 正式口径：`--phase {FORMAL_PHASE}`，默认 RunID 累计 ≥{SCREENING_TARGET} "
          f"activated，{len(FOCUS_RUNIDS)} 个重点 RunID 累计 {FOCUS_TARGET}；"
          f"`--max-parallel {MAX_PARALLEL}`（禁止 trial/3-seed 与 Wilson 序贯）",
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
    cg = doc["chain_gate"]
    print(f"[ready_contract] chain_gate admitted={cg['admitted']} "
          f"unproven={cg['unproven']} evidence_missing="
          f"{cg['evidence_missing']} root={cg['evidence_root']}")
    if a.gate:
        g = doc["gate"]
        print(f"[gate] binary_sha256={g.get('binary_sha256_16')} "
              f"pytest_rc={g.get('pytest_rc')} "
              f"mem_avail={g.get('mem_avail_gb')}G disk_free={g.get('disk_free_gb')}G")
    v = doc["verdict"]
    print(f"[verdict] {v['verdict']} — {'；'.join(v['reasons'])}")
    return 0 if v["verdict"] == "GO" else 1


if __name__ == "__main__":
    sys.exit(main())
