# tools/o3_atlas/tests/test_coverage.py
from tools.o3_atlas.corpus import instruction_pages
from tools.o3_atlas.validate import check_coverage

FAM = {"dataproc-imm": {
    "summary": "数据处理立即数",
    "pipeline": ["FETCH", "DECODE", "RENAME", "ISSUE", "EXECUTE", "WRITEBACK", "COMMIT"],
    "queue": "IQ", "fu": "IntALU", "default_injectors": ["CHAOSPhysReg"],
    "anchors": {"FETCH": "CHAOS/gem5/src/cpu/o3/fetch.cc:1059"}}}
REC = {"doc": "Arithmetic-ADD_immediate.md", "mnemonic": "ADD (immediate)",
       "tier": "implemented", "family": "dataproc-imm",
       "gem5": {"decode_mnemonic": "add_imm", "static_inst": "AddXImm",
                "anchors": {"decoder": "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:100"}},
       "injectors": ["CHAOSPhysReg"],
       "evidence": [{"claim": "解码", "anchor": "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa:100"}]}


def test_coverage_reports_missing_and_extra():
    corpus_names = {p.name for p in instruction_pages()}
    one_real = sorted(corpus_names)[0]
    recs = [{"doc": one_real}, {"doc": "Not-A-Real-Page.md"}]
    errs = check_coverage(recs)
    assert any("missing" in e for e in errs)      # corpus 有而 records 没有（缺 371 项）
    assert any("Not-A-Real-Page.md" in e for e in errs)  # records 有而 corpus 没有


def test_coverage_exact_match_passes():
    recs = [{"doc": n} for n in sorted({p.name for p in instruction_pages()})]
    assert check_coverage(recs) == []


def test_check_determinism_passes_on_fixture():
    from tools.o3_atlas.validate import check_determinism
    assert check_determinism(FAM, [REC]) == []


def test_check_determinism_detects_nondeterminism(monkeypatch):
    import tools.o3_atlas.generate as gen
    from tools.o3_atlas.validate import check_determinism
    calls = {"n": 0}
    orig = gen.render_page

    def flaky(rec, fam):
        calls["n"] += 1
        return orig(rec, fam) + ("x" if calls["n"] % 2 else "")

    monkeypatch.setattr(gen, "render_page", flaky)
    errs = check_determinism(FAM, [REC])
    assert errs and "Arithmetic-ADD_immediate.md" in errs[0]
