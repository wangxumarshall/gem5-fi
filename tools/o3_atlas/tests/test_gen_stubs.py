# tools/o3_atlas/tests/test_gen_stubs.py
from pathlib import Path

import pytest

FORMATS = Path("/home/sdc/gem5-fi-ding/CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa")
GEN = Path("/home/sdc/gem5-fi-ding/build/ARM/arch/arm/generated/decoder-ns.hh.inc")

pytestmark = pytest.mark.skipif(
    not FORMATS.is_file() or not GEN.is_file(),
    reason="gem5 源树/生成物缺失（诚实跳过，不静默通过）")


def test_family_for_known_titles():
    from tools.o3_atlas.gen_stubs import family_for
    assert family_for("ADD (immediate)", "Arithmetic") == "dataproc-imm"
    # 别名跟随主定义：MOV (to/from SP) 实为 ADD imm
    assert family_for("MOV (to/from SP)", "Logical") == "dataproc-imm"
    assert family_for("MADD", "Arithmetic") == "mul"
    assert family_for("SDIV", "Arithmetic") == "div"
    assert family_for("LDR (immediate)", "Load-Store") == "load"
    assert family_for("STXR", "Load-Store") == "exclusive"
    assert family_for("LDP", "Load-Store") == "ldst-pair"
    assert family_for("CAS", "Atomic") == "atomic-lse"
    assert family_for("B.cond", "Branch") == "branch-cond"
    assert family_for("RET", "Branch") == "branch-reg"
    assert family_for("DSB", "Barrier-Hint") == "barrier"
    assert family_for("NOP", "Barrier-Hint") == "hint"
    assert family_for("SXTW", "Other") == "extend"
    assert family_for("CRC32B", "Cryptographic") == "dataproc-2src"


def test_generate_all_372_records_all_pass_schema():
    from tools.o3_atlas import schema
    from tools.o3_atlas.gen_stubs import generate_all
    recs, families = generate_all()
    assert len(recs) == 372
    errs = [e for r in recs for e in schema.validate_instruction(r, families)]
    assert errs == []


def test_known_tiers_and_evidence_anchors():
    from tools.o3_atlas.gen_stubs import generate_all
    recs = {r["mnemonic"]: r for r in generate_all()[0]}
    add = recs["ADD (immediate)"]
    assert add["tier"] == "implemented"
    assert add["gem5"]["static_inst"] == "AddXImm"
    assert add["gem5"]["anchors"]["decoder"] == \
        "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:100"
    cpyp = recs["CPYP , CPYM, CPYE"]  # 组合页真实标题（首项 = CPYP）
    assert cpyp["tier"] == "unimplemented" and cpyp["behavior"] == "absent"
    bti = recs["BTI"]
    assert bti["tier"] == "unimplemented" and bti["behavior"] == "warn-nop"
    ldp = recs["LDP"]
    assert ldp["tier"] == "macro-op" and ldp["gem5"]["static_inst"] == "LdpStp"
    tlbi = recs["TLBI"]
    assert tlbi["tier"] == "fs-only"
