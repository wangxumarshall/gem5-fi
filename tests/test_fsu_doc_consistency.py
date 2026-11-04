"""tests/test_fsu_doc_consistency.py — 文档/矩阵/磁盘证据一致性.

只读工作簿、矩阵、磁盘索引与 runs/fsu 审计；不运行 gem5。

覆盖：
  1. 文档/矩阵不得同时声称某能力“未实现/缺 SA0/缺 F5 调度”又存在
     对应 certified 正式 seed（至少 FP06-F5-W3）。
  2. 矩阵每个 RunID 的 seed_completion 必须等于 fsu_index.scan；
     W5 suite 的 15 个 component run 不得变成 15 个 seed。
  3. 双视图数字必须与 INDEX.json 一致；明确标注“本轮前/历史”的段落
     允许保留旧数字。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import fsu_implementation_matrix as M  # noqa: E402
import fsu_index as I  # noqa: E402

FS = ROOT / "docs/gem5-fi/fsu"
RUNIDS = FS / "runids.json"
INDEX = ROOT / "runs/fsu/COMPLETE_PROPAGATION_PATHS/INDEX.json"

DOC_FILES = [
    FS / "F5-READINESS.md",
    FS / "COVERAGE_STATUS.md",
    FS / "ACTIVE_SCOPE.md",
    FS / "IMPLEMENTATION-STATUS-2026-11-03.md",
    FS / "IMPLEMENTATION_AUDIT.md",
]

F5_RUNIDS = [
    "FSU-FP06-F5-W1", "FSU-FP06-F5-W3", "FSU-FP06-F5-W4",
    "FSU-FP06-F5-W5", "FSU-FP06-F5-W6",
    "FSU-FR03-F5-W3", "FSU-FR03-F5-W5", "FSU-FR03-F5-W6",
]

# 已被当前事实推翻的断言。允许出现在明确标注“历史/本轮前/开工时/
# baseline/最初审计”的行里，否则视为过期。
STALE_CAPABILITY_CLAIMS = [
    "缺 F5 调度",
    "没有“warm-up 后第一个 eligible",
    "当前是 XOR",
    "没有 FSU_PROP",
    "无 FSU_PROP",
    "FP06-F5-W3 0/3",
    "SA0/SA1 未实现",
    "F5 调度、SA0/SA1",
]
HISTORICAL_MARKERS = ("历史", "本轮前", "开工时", "取代", "baseline", "最初审计")


def _norm(text: str) -> str:
    """去掉空白与 markdown 强调符，保留表格分隔符/中文/数字。"""
    return re.sub(r"[ \t*`]", "", text)


def _scan():
    runids = I._load_runids(RUNIDS)
    return I.scan(runids, ROOT / "runs/fsu", None)


def _load_index():
    return json.loads(INDEX.read_text(encoding="utf-8"))


def _audit_ok(rid, seed):
    p = ROOT / "runs/fsu" / rid / f"seed{seed}" / "attempt-1" / "audit.json"
    if not p.exists():
        return False
    return json.loads(p.read_text(encoding="utf-8")).get("ok") is True


def test_fp06_w3_certified_evidence_exists():
    assert all(_audit_ok("FSU-FP06-F5-W3", s) for s in (1, 2, 3))
    rows, summary, _ = _scan()
    assert summary["admitted_seeds_total"] >= 24
    row = next(r for r in rows if r["runid"] == "FSU-FP06-F5-W3")
    assert row["admitted_seeds"] == 3
    assert all(s["state"] == "admitted" for s in row["seeds"].values())


def test_docs_do_not_deny_certified_fp06_capability():
    hits = []
    for path in DOC_FILES:
        for line in path.read_text(encoding="utf-8").splitlines():
            for pat in STALE_CAPABILITY_CLAIMS:
                if pat and pat in line:
                    if not any(m in line for m in HISTORICAL_MARKERS):
                        hits.append((path.name, pat, line.strip()))
    assert hits == [], hits

    f5 = (FS / "F5-READINESS.md").read_text(encoding="utf-8")
    assert "FSU-FP06-F5-W3" in f5
    assert "COMPLETE_3_OF_3" in f5
    assert "FP06-d" in f5 and "MISSING" in f5
    assert "FR03-F5-W3" in f5 and "PARTIAL_2_OF_3" in f5
    assert "FR03-F5-W5" in f5 and "COMPLETE_3_OF_3" in f5
    # 分开表述：不能把 FP06-d 的缺失写成 a/b/c 未实现。
    assert "FP06-a" in f5 and "FP06-b" in f5 and "FP06-c" in f5

    audit = (FS / "IMPLEMENTATION_AUDIT.md").read_text(encoding="utf-8")
    fp06_row = next(l for l in audit.splitlines()
                    if l.startswith("| FP06 |"))
    assert "FP06-d" in fp06_row and "MISSING" in fp06_row
    assert "SA0/SA1 极性、全向量宽度" not in fp06_row
    fr03_row = next(l for l in audit.splitlines()
                    if l.startswith("| FR03 |"))
    assert "generation" in fr03_row
    # FR03-W3 now has a real FSU_PROP L0-L5 path; W5/W6 remain blocked.
    assert "FSU_PROP" in fr03_row
    assert "L5" in fr03_row
    assert "W5/W6" in fr03_row and "BLOCKED" in fr03_row
    for stale in ("三 seed 状态一律 0/3", "未运行 gem5",
                  "当前无 FSU PROP 事件", "2mm 缺失"):
        assert stale not in audit, stale


def test_matrix_f5_rows_reflect_disk_truth():
    matrix, summary = M.build()
    by_id = {r["runid"]: r for r in matrix}
    w3 = by_id["FSU-FP06-F5-W3"]
    assert w3["seed_completion"] == "3/3"
    assert w3["f5_readiness"] == "COMPLETE_3_OF_3"
    assert "FP06-d" in w3["coverage_reason"]
    assert "MISSING" in w3["coverage_reason"]
    assert "FP06-a" in w3["coverage_reason"]
    w1 = by_id["FSU-FP06-F5-W1"]
    assert w1["seed_completion"] == "3/3"
    assert w1["f5_readiness"] == "COMPLETE_3_OF_3"
    assert "certified 3/3" in w1["coverage_reason"]
    assert "FP06-d" in w1["coverage_reason"]
    for rid in ("FSU-FP06-F5-W4", "FSU-FP06-F5-W5"):
        assert by_id[rid]["seed_completion"] == "3/3"
        assert by_id[rid]["f5_readiness"] == "COMPLETE_3_OF_3"
    assert by_id["FSU-FP06-F5-W6"]["seed_completion"] == "3/3"
    assert by_id["FSU-FP06-F5-W6"]["f5_readiness"] == "COMPLETE_3_OF_3"
    assert by_id["FSU-FR03-F5-W3"]["seed_completion"] == "2/3"
    assert by_id["FSU-FR03-F5-W3"]["f5_readiness"] == "PARTIAL_2_OF_3"
    for rid in ("FSU-FR03-F5-W5", "FSU-FR03-F5-W6"):
        assert by_id[rid]["seed_completion"] == "3/3"
        assert by_id[rid]["f5_readiness"] == "COMPLETE_3_OF_3"
    assert set(summary["f5_readiness_counts"].keys()) <= {
        "COMPLETE_3_OF_3", "GATE_NOT_COMPLETE", "NOT_RUN", "BLOCKED",
        "PARTIAL_2_OF_3"}

    cap = summary["capability_evidence"]
    fp06 = cap["FP06"]
    for name in ("permanent_stuck", "sa0_sa1_non_xor", "apply_stuck",
                 "fsu_prop_l0_l5", "chain_end"):
        assert fp06[name]["code_present"] is True, name
        assert fp06[name]["certified"] is True, name
        assert fp06[name]["evidence"], name
    assert fp06["partial_product_proxy_fp06d"]["code_present"] is False
    assert fp06["partial_product_proxy_fp06d"]["certified"] is False
    fr03 = cap["FR03"]
    assert fr03["vec_stuck_write_path"]["code_present"] is True
    assert fr03["permanent_cell_across_generations"]["code_present"] is True
    # FR03-W3 has real 3/3 certification; W5/W6 must still not borrow it.
    assert fr03["chaosphysreg_fsu_prop"]["certified"] is True
    assert fr03["runner_chaosphysreg_path"]["certified"] is True
    assert fr03["fr03_formal_seeds"]["certified"] is True
    assert cap["W5_suite"]["five_programs_including_2mm"]["certified"] is True


def test_matrix_seed_completion_matches_authoritative_index():
    matrix, summary = M.build()
    rows, index_summary, index_scope = _scan()
    idx = {r["runid"]: r for r in rows}
    for m in matrix:
        assert m["seed_completion"] == idx[m["runid"]]["seed_completion"]
        assert m["seed_completion_count"] == idx[m["runid"]]["admitted_seeds"]
    assert summary["seed_index"]["admitted_seeds_total"] == \
        index_summary["admitted_seeds_total"]
    assert summary["seed_index"]["active_admitted_seeds"] == \
        index_scope["active_admitted_seeds"]
    assert summary["seed_index"]["active_complete_runids"] == \
        index_scope["active_complete_runids"]

    # W5 suite：15 个 component run 绝不能当成 15 个 seed。
    w5 = next(m for m in matrix if m["runid"] == "FSU-FP04-F0-W5")
    assert w5["seed_completion"] == "3/3"
    assert w5["seed_completion_count"] == 3
    assert sum(1 for s in w5["seed_states"].values()
               if s == "admitted") == 3
    # F0-W5 and F5-W5 each contribute 3 suite seeds (15 components each).
    assert summary["seed_index"]["suite_seed_admitted"] == 18
    assert summary["seed_index"]["component_runs_in_admitted_suites"] == 72
    assert summary["seed_index"]["admitted_seeds_total"] != 15
    assert all(m["seed_completion_count"] <= 3 for m in matrix)

    # W1 is now formally complete; the count must come from the disk audit,
    # never from a hand-written number.
    w1 = next(m for m in matrix if m["runid"] == "FSU-FP06-F5-W1")
    assert w1["seed_completion"] == "3/3"
    assert w1["seed_completion_count"] == 3


def test_doc_dual_view_numbers_match_index_json():
    data = _load_index()
    s = data["summary"]
    a = s["active_scope"]
    hist = (s["complete_3_of_3"], s["admitted_seeds_total"],
            s["total_runids"], s["target_seeds"])
    act = (a["active_complete_runids"], a["active_admitted_seeds"],
           a["active_runids"], a["active_seed_target"])

    active_norm = _norm((FS / "ACTIVE_SCOPE.md").read_text(encoding="utf-8"))
    assert (f"|历史全量（sourceregistry）|{hist[2]}|{hist[3]}|"
            f"{hist[1]}|{hist[0]}|") in active_norm
    assert (f"|当前活跃（F0/F5）|{act[2]}|{act[3]}|"
            f"{act[1]}|{act[0]}|") in active_norm

    cov = _norm((FS / "COVERAGE_STATUS.md").read_text(encoding="utf-8"))
    assert f"{hist[1]}/{hist[3]}" in cov            # 24/519
    assert f"{hist[0]}/{hist[2]}" in cov            # 8/173
    assert f"{act[2]}RunID/{act[3]}seed" in cov     # 80 RunID / 240 seed
    assert f"{act[1]}seed/{act[0]}RunID" in cov     # 15 seed / 5 RunID

    status = _norm((FS / "IMPLEMENTATION-STATUS-2026-11-03.md")
                   .read_text(encoding="utf-8"))
    assert f"{hist[1]}/{hist[3]}seed，{hist[0]}/{hist[2]}RunID" in status
    assert f"{act[1]}/{act[3]}seed，{act[0]}/{act[2]}RunID" in status

    f5 = _norm((FS / "F5-READINESS.md").read_text(encoding="utf-8"))
    assert f"{hist[1]}/{hist[3]}seed、{hist[0]}/{hist[2]}RunID" in f5
    assert f"{act[1]}/{act[3]}seed、{act[0]}/{act[2]}RunID" in f5

    # F5 readiness 表的 seed_completion 必须与磁盘索引一致。
    # 归一化行格式：|RunID|readiness|seed_completion|缺口|
    idx = {r["runid"]: r for r in data["runids"]}
    for rid in F5_RUNIDS:
        line = next((l for l in f5.splitlines()
                     if l.startswith(f"|{rid}|")), None)
        assert line is not None, rid
        cells = line.split("|")
        assert cells[3] == idx[rid]["seed_completion"], (rid, cells)
