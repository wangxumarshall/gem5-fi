#!/usr/bin/env python3
"""Tests for tools/lsu_prop_doc_audit.py (narrative propagation doc audit).

The old half-baked audit used two unreliable heuristics:
  1. any occurrence of "REVIEW_REQUIRED" in the whole file => file is REVIEW
     (T03-F5-W4-seed1 mentions a stale evidence dir in Ch.7 and was
     misjudged), and
  2. the literal heading "原始证据与文件哈希" (12 docs use the equivalent
     "原始证据与哈希" and were counted as structural failures).
These tests pin the correct semantics: the seed verdict is read ONLY from the
explicit verdict field in Chapter 6, and chapter matching is semantic.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import lsu_prop_doc_audit as audit  # noqa: E402

DOCS_DIR = os.environ.get(
    "R6_PROP_DOCS_DIR",
    "/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS",
)
EVIDENCE_JSON = os.environ.get(
    "R6_AUTH_EVIDENCE_JSON",
    "/home/sdc/gem5-fi-ding/runs/lsu/R6-AUTHORITATIVE-EVIDENCE.json",
)
REPO_ROOT = os.environ.get("R6_REPO_ROOT", "/home/sdc/gem5-fi-ding")


# ---------------------------------------------------------------------------
# Pure parser tests (no evidence needed)
# ---------------------------------------------------------------------------
def test_verdict_reads_ch6_only_not_whole_file():
    """A Ch.7 mention of another dir's REVIEW_REQUIRED must not flip the file."""
    text = (
        "# X seed1\n\n## 1. 实验身份与复现信息\n\nx\n\n"
        "## 2. 完整故障传播过程：从注入到最终结局\n\nx\n\n"
        "## 3. SDC 诊断分析\n\nx\n\n"
        "## 4. 完整主链事件表\n\nx\n\n"
        "## 5. 相关旁支与未进入最终主链的事件\n\nx\n\n"
        "## 6. 最终判定与证据完整性\n\n| 判定 | **PASS** |\n\n"
        "## 7. 原始证据与文件哈希\n\n- 另一个目录 — **REVIEW_REQUIRED**\n"
    )
    sections = audit.split_sections(text)
    assert audit.verdict_from_ch6(sections["ch6"]) == "PASS"


def test_verdict_reads_review_required():
    ch6 = "| 判定 | **REVIEW_REQUIRED** |\n\n**REVIEW_REQUIRED 的理由**：多 fault 计数不一致\n"
    assert audit.verdict_from_ch6(ch6) == "REVIEW_REQUIRED"


def test_verdict_accepts_pass_with_parenthetical():
    ch6 = "- 结论：**PASS（附两条证据口径说明）**；L5=N/A\n"
    assert audit.verdict_from_ch6(ch6) == "PASS"


def test_verdict_accepts_verdict_key():
    ch6 = "| verdict | **REVIEW_REQUIRED** |\n"
    assert audit.verdict_from_ch6(ch6) == "REVIEW_REQUIRED"


def test_verdict_ignores_prose_conclusion_line():
    """`样本级结论一致` in another row is not the verdict field."""
    ch6 = (
        "| campaign/checker agreement | **两套口径并列（不是数据矛盾）**；样本级结论一致 |\n"
        "| verdict | **PASS** |\n"
    )
    assert audit.verdict_from_ch6(ch6) == "PASS"


def test_verdict_accepts_not_mibench_result():
    ch6 = "| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS） |\n"
    assert audit.verdict_from_ch6(ch6) == "NOT_MIBENCH_RESULT"


def test_chapter7_variant_is_structurally_complete():
    bases = [
        "## 1. 实验身份与复现信息",
        "## 2. 完整故障传播过程：从注入到最终结局",
        "## 3. SDC 诊断分析",
        "## 4. 完整主链事件表",
        "## 5. 相关旁支与未进入最终主链的事件",
        "## 6. 最终判定与证据完整性",
    ]
    for ch7 in ("## 7. 原始证据与文件哈希", "## 7. 原始证据与哈希"):
        text = "\n\n".join(bases + [ch7]) + "\n"
        sections = audit.split_sections(text)
        assert audit.missing_chapters(sections) == [], ch7


def test_legacy_sections_detected():
    ch2 = "## 2. x\n\n### 2.1 a\n\n### 2.2 b\n\n### 2.3 c\n"
    assert audit.has_legacy_sections("## 30 秒结论\n") is True
    assert audit.has_legacy_sections(ch2) is False


def test_identity_mismatch_requires_mibench_label_and_tlb_probe():
    ch1 = (
        "- workload 矩阵标签：MiBench-TC23 论文负载（blowfish…）\n"
        "- run.out 实际 workload/readfile：`…/configs/fs/tlb_probe.rcS`\n"
    )
    assert audit.identity_status(ch1) == "WORKLOAD_IDENTITY_MISMATCH"
    ch1_ok = (
        "- workload 矩阵标签：TLB-AliasPerm 地址翻译探针\n"
        "- run.out 实际 workload/readfile：`…/configs/fs/tlb_probe.rcS`（与矩阵标签一致）\n"
    )
    assert audit.identity_status(ch1_ok) == "MATCH"


# ---------------------------------------------------------------------------
# Real-document tests (require the on-disk evidence tree)
# ---------------------------------------------------------------------------
pytestmark_real = pytest.mark.skipif(
    not os.path.isdir(DOCS_DIR) or not os.path.isfile(EVIDENCE_JSON),
    reason="real R6 docs/evidence tree not present",
)


@pytestmark_real
def test_real_t03_f5_w4_seed1_is_pass():
    """Regression for the stale-dir false positive."""
    result = audit.audit_one(
        os.path.join(DOCS_DIR, "T03-F5-W4-seed1.md"), REPO_ROOT, EVIDENCE_JSON
    )
    assert result["seed_verdict"] == "PASS"
    assert result["missing_chapters"] == []


@pytestmark_real
def test_real_t01_f1_w4_seed2_is_pass_with_two_calibers():
    """After the recheck the doc reports run-level and per-fault counts apart."""
    result = audit.audit_one(
        os.path.join(DOCS_DIR, "T01-F1-W4-seed2.md"), REPO_ROOT, EVIDENCE_JSON
    )
    assert result["seed_verdict"] == "PASS"
    assert result["chain_evidence_status"] == "PASS"
    assert result["experiment_identity_status"] == "MATCH"
    ch6 = audit.split_sections(open(
        os.path.join(DOCS_DIR, "T01-F1-W4-seed2.md"), encoding="utf-8"
    ).read())["ch6"]
    assert "run 级 outcome" in ch6 and "per-fault 终局" in ch6


@pytestmark_real
def test_real_w1_docs_are_two_axis_not_single_pass():
    result = audit.audit_one(
        os.path.join(DOCS_DIR, "T01-F0-W1-seed1.md"), REPO_ROOT, EVIDENCE_JSON
    )
    assert result["seed_verdict"] == "NOT_MIBENCH_RESULT"
    assert result["chain_evidence_status"] == "PASS"
    assert result["experiment_identity_status"] == "WORKLOAD_IDENTITY_MISMATCH"
    assert result["overall_experiment_status"] == "NOT_MIBENCH_RESULT"


@pytestmark_real
def test_real_w1_identity_mismatch_and_w4_match():
    w1 = audit.audit_one(
        os.path.join(DOCS_DIR, "T01-F0-W1-seed1.md"), REPO_ROOT, EVIDENCE_JSON
    )
    w4 = audit.audit_one(
        os.path.join(DOCS_DIR, "T01-F0-W4-seed1.md"), REPO_ROOT, EVIDENCE_JSON
    )
    assert w1["experiment_identity_status"] == "WORKLOAD_IDENTITY_MISMATCH"
    assert w4["experiment_identity_status"] == "MATCH"


@pytestmark_real
def test_real_t01_f0_w4_seed2_arrow_chain_with_parens():
    """`0(inj) → 1(tlb_lookup) → ...` is a valid ancestry chain."""
    result = audit.audit_one(
        os.path.join(DOCS_DIR, "T01-F0-W4-seed2.md"), REPO_ROOT, EVIDENCE_JSON
    )
    assert result["ancestry"]["chain"] == list(range(0, 9)) + [60, 61, 259]
    assert result["ancestry"]["parent_mismatches"] == []
    assert result["chain_evidence_status"] == "PASS"


@pytestmark_real
def test_real_t04_f0_w4_seeds_use_full_ch4_ancestry():
    """`path_event_ids` is a layer-anchor list, not the chain; Ch.4 is full."""
    for seed in (1, 3):
        result = audit.audit_one(
            os.path.join(DOCS_DIR, f"T04-F0-W4-seed{seed}.md"),
            REPO_ROOT, EVIDENCE_JSON,
        )
        # The full chain has 22 events; ids are not necessarily contiguous.
        assert len(result["ancestry"]["chain"]) == 22, seed
        assert result["ancestry"]["chain"][0] == 0, seed
        assert result["ancestry"]["parent_mismatches"] == [], seed
        assert result["chain_evidence_status"] == "PASS", seed


@pytestmark_real
def test_real_t10_f1_w1_seed2_full_chain():
    result = audit.audit_one(
        os.path.join(DOCS_DIR, "T10-F1-W1-seed2.md"), REPO_ROOT, EVIDENCE_JSON
    )
    assert result["ancestry"]["chain"] == list(range(0, 21))
    assert result["ancestry"]["parent_mismatches"] == []
    assert result["chain_evidence_status"] == "PASS"


@pytestmark_real
def test_real_t02_f2_w4_seed2_regrade_containment():
    """Authoritative regrade has no chain_valid field; event 68 is the witness."""
    result = audit.audit_one(
        os.path.join(DOCS_DIR, "T02-F2-W4-seed2.md"), REPO_ROOT, EVIDENCE_JSON
    )
    assert result["chain_evidence_status"] == "PASS"
    assert result["evidence"]["terminal"] == "detected_contained"
    assert result["witness"]["event_id"] == 68
    assert result["witness"]["contained"] is True
    assert result["witness"]["detection_layer"] == "L4"
    # Ch.7 of this doc lists relative filenames; they must still be hashed.
    assert result["hashes"]["checked_count"] >= 6
    assert result["hashes"]["mismatches"] == []


@pytestmark_real
def test_real_full_audit_counts():
    result = audit.audit_dir(DOCS_DIR, REPO_ROOT, EVIDENCE_JSON)
    summary = result["summary"]
    assert summary["files_total"] == 51
    assert summary["seven_chapters_complete"] == 51
    assert summary["legacy_section_files"] == []
    # The 12 "structural failures" of the old audit were heading variants and
    # must not reappear as failures.
    assert summary["structural_failures"] == []
    assert len(summary["identity_mismatch_files"]) == 24
    # Every seed's propagation chain must verify against its own raw stream.
    assert summary["chain_evidence_fail"] == []
