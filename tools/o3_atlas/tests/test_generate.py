# tools/o3_atlas/tests/test_generate.py
from tools.o3_atlas.generate import render_index, render_page, sanitize_mermaid

FAM = {"dataproc-imm": {
    "summary": "数据处理立即数",
    "pipeline": ["FETCH", "DECODE", "RENAME", "ISSUE", "EXECUTE", "WRITEBACK", "COMMIT"],
    "queue": "IQ", "fu": "IntALU", "default_injectors": ["CHAOSPhysReg"],
    "anchors": {"FETCH": "CHAOS/gem5/src/cpu/o3/fetch.cc:1059"}}}
REC = {"doc": "Arithmetic-ADD_immediate.md", "mnemonic": "ADD (immediate)",
       "tier": "implemented", "family": "dataproc-imm",
       "gem5": {"decode_mnemonic": "add_imm", "static_inst": "AddXImm",
                "anchors": {"decoder": "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:100"}},
       "injectors": ["CHAOSPhysReg", "CHAOSIQ"],
       "evidence": [{"claim": "解码", "anchor": "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:100"}]}
UNIMP = {"doc": "Other-CPYP__CPYM_CPYE.md", "mnemonic": "CPYP", "tier": "unimplemented",
         "behavior": "absent",
         "evidence": [{"claim": "MTE absent", "anchor": "CHAOS/gem5/src/arch/arm/isa/insts/data64.isa:1"}]}


def test_deep_page_sections_and_links():
    md = render_page(REC, FAM["dataproc-imm"])
    for needle in ["# ADD (immediate)", "tier: implemented", "family: dataproc-imm",
                   "../../armv8-isa/Arithmetic-ADD_immediate.md", "AddXImm",
                   "CHAOSPhysReg", "```mermaid", "FETCH", "COMMIT"]:
        assert needle in md, needle


def test_unimplemented_page_is_short_and_honest():
    md = render_page(UNIMP, None)
    assert "unimplemented" in md and "absent" in md and "```mermaid" not in md


def test_mermaid_label_sanitization():
    assert sanitize_mermaid('ADD (immediate)" x') == "ADD _immediate__ x"


def test_index_table_rows():
    md = render_index("Arithmetic", [REC, UNIMP])
    assert "| 372 项中的 2 项" in md  # 覆盖行：语料 372 指令页中本分类索引收录数
    assert "Arithmetic-ADD_immediate.md" in md


def test_render_deterministic():
    assert render_page(REC, FAM["dataproc-imm"]) == render_page(REC, FAM["dataproc-imm"])
