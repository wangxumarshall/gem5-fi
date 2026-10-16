# tools/o3_atlas/tests/test_corpus.py
from pathlib import Path

from tools.o3_atlas.corpus import (EXPECTED_COUNTS, corpus_files, category_of,
                                   index_pages, instruction_pages, title_of)


def test_counts():
    assert len(corpus_files()) == 387
    assert len(index_pages()) == 15
    assert len(instruction_pages()) == 372


def test_category_counts_match_measured_table():
    got = {}
    for p in instruction_pages():
        got[category_of(p)] = got.get(category_of(p), 0) + 1
    assert got == EXPECTED_COUNTS
    assert sum(got.values()) == 372


def test_category_of_hyphenated_category_names():
    assert category_of(Path("Load-Store-LDNP.md")) == "Load-Store"
    assert category_of(Path("Barrier-Hint-ESB.md")) == "Barrier-Hint"
    assert category_of(Path("Arithmetic-ADD_immediate.md")) == "Arithmetic"


def test_titles_present_and_nonempty():
    for p in instruction_pages():
        assert title_of(p).strip(), p.name
