# tools/o3_atlas/tests/test_diagrams.py
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.o3_atlas.generate import render_master_dot, render_master_mermaid
from tools.o3_atlas.schema import INJECTORS

STAGES = ("BPU", "FTQ", "FETCH", "DECODE", "RENAME", "DISPATCH", "ISSUE",
          "EXECUTE", "MEMORY", "WRITEBACK", "COMMIT", "REDIRECT")


def test_master_mermaid_contains_all_injectors_and_stages():
    mmd = render_master_mermaid()
    for inj in INJECTORS:
        assert inj in mmd, inj
    for stage in STAGES:
        assert stage in mmd, stage


def test_master_dot_compiles_to_svg(tmp_path):
    if not shutil.which("dot"):
        pytest.skip("graphviz dot 缺失（诚实跳过；本机应有 dot 8.1.0）")
    dot_src = render_master_dot()
    assert dot_src.lstrip().startswith("digraph")
    for inj in INJECTORS:
        assert inj in dot_src, inj
    dot_f = tmp_path / "o3.dot"
    svg_f = tmp_path / "o3.svg"
    dot_f.write_text(dot_src, encoding="utf-8")
    r = subprocess.run(["dot", "-Tsvg", str(dot_f), "-o", str(svg_f)],
                       capture_output=True, timeout=120)
    assert r.returncode == 0, r.stderr.decode()[:400]
    assert svg_f.stat().st_size > 1000
