# tools/o3_atlas/corpus.py
"""Enumerate the armv8-isa instruction corpus — the single coverage baseline.

All counts are measured (2026-10-16) against docs/cpu/armv8-isa/ and frozen
here; any drift in the corpus makes these tests fail loudly instead of
silently under-covering.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO / "docs" / "cpu" / "armv8-isa"

INDEX_PAGES = {  # 15 个分类索引页（文件名 = 分类名）
    "Arithmetic", "Atomic", "Barrier-Hint", "Bit-Manipulation", "Branch",
    "Compare", "Conditional-Select", "Count", "Cryptographic", "Load-Store",
    "Logical", "Other", "PC-Relative", "Pointer-Authentication", "System",
}

EXPECTED_COUNTS = {  # 372 指令页的实测分账（2026-10-16）
    "Load-Store": 123, "Other": 81, "Arithmetic": 33, "Bit-Manipulation": 25,
    "Logical": 23, "System": 16, "Barrier-Hint": 16, "Branch": 13,
    "Pointer-Authentication": 11, "Compare": 11, "Conditional-Select": 7,
    "Atomic": 7, "PC-Relative": 2, "Cryptographic": 2, "Count": 2,
}


def corpus_files():
    return sorted(p for p in CORPUS_DIR.glob("*.md") if p.is_file())


def index_pages():
    return [p for p in corpus_files() if p.stem in INDEX_PAGES]


def instruction_pages():
    return [p for p in corpus_files() if p.stem not in INDEX_PAGES]


def category_of(path) -> str:
    stem = Path(path).stem
    for cat in sorted(INDEX_PAGES, key=len, reverse=True):  # 长名优先，防前缀误配
        if stem.startswith(cat + "-"):
            return cat
    raise ValueError(f"unknown category for {path}")


def title_of(path) -> str:
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError(f"no title heading in {path}")
