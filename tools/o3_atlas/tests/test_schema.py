# tools/o3_atlas/tests/test_schema.py
from tools.o3_atlas import schema

FAM = {"dataproc-imm": {
    "summary": "数据处理立即数",
    "pipeline": ["FETCH", "DECODE", "RENAME", "ISSUE", "EXECUTE", "WRITEBACK", "COMMIT"],
    "queue": "IQ", "fu": "IntALU",
    "default_injectors": ["CHAOSDecode", "CHAOSPhysReg", "CHAOSROB"],
    "anchors": {"FETCH": "CHAOS/gem5/src/cpu/o3/fetch.cc:1059"},
}}
BASE = {"doc": "Arithmetic-ADD_immediate.md", "mnemonic": "ADD (immediate)",
        "tier": "implemented", "family": "dataproc-imm",
        "gem5": {"decode_mnemonic": "add_imm", "static_inst": "AddXImm",
                 "anchors": {"decoder": "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:100"}},
        "injectors": ["CHAOSDecode"],
        "evidence": [{"claim": "解码为 AddXImm",
                      "anchor": "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:100"}]}


def test_valid_record_and_family_pass():
    assert schema.validate_family(FAM["dataproc-imm"], "dataproc-imm", FAM) == []
    assert schema.validate_instruction(BASE, FAM) == []


def test_bad_tier_and_missing_behavior():
    assert schema.validate_instruction({**BASE, "tier": "bogus"}, FAM)
    unimp = {**BASE, "tier": "unimplemented"}
    errs = schema.validate_instruction(unimp, FAM)
    assert any("behavior" in e for e in errs)  # unimplemented 必须记 behavior


def test_unimplemented_valid_with_behavior():
    unimp = {"doc": "Other-CPYP__CPYM_CPYE.md", "mnemonic": "CPYP", "tier": "unimplemented",
             "behavior": "absent",
             "evidence": [{"claim": "MTE 源码零匹配",
                           "anchor": "CHAOS/gem5/src/arch/arm/isa/insts/data64.isa:1"}]}
    assert schema.validate_instruction(unimp, FAM) == []


def test_implemented_requires_gem5_identity_and_family():
    nofam = {k: v for k, v in BASE.items() if k != "family"}
    assert schema.validate_instruction(nofam, FAM)
    nogem5 = {k: v for k, v in BASE.items() if k != "gem5"}
    assert schema.validate_instruction(nogem5, FAM)


def test_unknown_injector_and_node_rejected():
    bad = {**BASE, "injectors": ["CHAOSNope"]}
    assert schema.validate_instruction(bad, FAM)
    badfam = {"f": {**FAM["dataproc-imm"], "pipeline": ["NOT_A_NODE"]}}
    assert schema.validate_family(badfam["f"], "f", badfam)
