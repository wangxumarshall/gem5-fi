# tools/o3_atlas/tests/test_diagrams.py
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.o3_atlas.generate import render_master_dot, render_master_mermaid
from tools.o3_atlas.schema import INJECTORS

PROXY = Path("/home/sdc/gem5-fi-ding/configs/se/ooo_proxy.py")
pytestmark = pytest.mark.skipif(
    not PROXY.is_file(),
    reason="configs/se/ooo_proxy.py 缺失（能力模式全集的数据源；诚实跳过）")

# 上层：流水线站点
STAGES = ("BPU", "FTQ", "FETCH", "DECODE", "RENAME", "DISPATCH", "ISSUE",
          "EXECUTE", "MEMORY", "WRITEBACK", "COMMIT", "REDIRECT")
# 站点标签内嵌的 µarch 结构
STRUCTS = ("ICache", "Decoder", "RAT", "FreeList", "IQ", "LSQ", "FU", "L1D",
           "TLB", "PRF", "ROB")


def test_injector_caps_parsed_from_ooo_proxy():
    # 模式全集实时解析自实验工具面（ooo_proxy.py argparse choices）
    from tools.o3_atlas.generate import INJECTOR_FLAG_MAP, parse_injector_caps
    caps = parse_injector_caps()
    rob = caps[INJECTOR_FLAG_MAP["CHAOSROB"][0]]
    assert len(rob) >= 20 and "pc_bitflip" in rob
    assert "map_bitflip" in caps[INJECTOR_FLAG_MAP["CHAOSRenameMap"][0]]
    assert "opcode_bitflip" in caps[INJECTOR_FLAG_MAP["CHAOSDecode"][0]]
    assert "stxr_force_success" in caps[INJECTOR_FLAG_MAP["CHAOSExMon"][0]]


def test_master_mermaid_pipeline_top_capability_layer_below():
    mmd = render_master_mermaid()
    # 上层：微架构流水线（站点 + 结构单元标签）
    for s in STAGES:
        assert s in mmd, s
    for st in STRUCTS:
        assert st in mmd, st
    # 两层结构：流水线在上、注入能力层在下
    assert "微架构流水线" in mmd and "故障注入能力" in mmd
    # 指令流并集：EXECUTE 分岔（ALU 直通 WB 与访存经 MEMORY）
    assert "EXECUTE --> WRITEBACK" in mmd
    assert "EXECUTE --> MEMORY" in mmd
    assert "MEMORY --> WRITEBACK" in mmd
    assert "REDIRECT -.-> FETCH" in mmd
    # 挂载边：流水线站点 -.-> 下方注入器（19 个全覆盖）
    for inj in INJECTORS:
        assert inj in mmd, inj
    for e in ("BPU -.-> CHAOSBPU", "DECODE -.-> CHAOSDecode",
              "RENAME -.-> CHAOSRenameMap", "RENAME -.-> CHAOSFreeList",
              "ISSUE -.-> CHAOSIQ", "EXECUTE -.-> CHAOSExec",
              "MEMORY -.-> CHAOSLSQFwd", "COMMIT -.-> CHAOSROB"):
        assert e in mmd, e
    # 能力徽标：注入器节点带模式计数（解析自 ooo_proxy.py）
    assert "⚡CHAOSROB(" in mmd and "⚡CHAOSDecode(" in mmd
    # FU 并集入 EXECUTE 站点标签
    for fu in ("IntALU", "IntMult", "IntDiv", "SimdCrcOp"):
        assert fu in mmd, fu


def test_master_dot_pipeline_and_caps_compiles(tmp_path):
    dot_src = render_master_dot()
    assert dot_src.lstrip().startswith("digraph")
    for s in STAGES:
        assert s in dot_src, s
    for inj in INJECTORS:
        assert inj in dot_src, inj
    assert "EXECUTE -> MEMORY" in dot_src
    assert "EXECUTE -> WRITEBACK" in dot_src
    assert "COMMIT -> CHAOSROB" in dot_src
    assert "DECODE -> CHAOSDecode" in dot_src
    assert "⚡CHAOSROB(" in dot_src
    if not shutil.which("dot"):
        pytest.skip("graphviz dot 缺失（诚实跳过）")
    dot_f = tmp_path / "o3.dot"
    svg_f = tmp_path / "o3.svg"
    dot_f.write_text(dot_src, encoding="utf-8")
    r = subprocess.run(["dot", "-Tsvg", str(dot_f), "-o", str(svg_f)],
                       capture_output=True, timeout=120)
    assert r.returncode == 0, r.stderr.decode()[:400]
    assert svg_f.stat().st_size > 1000


def test_injection_capabilities_table_complete():
    from tools.o3_atlas.generate import render_injection_caps
    md = render_injection_caps()
    for inj in INJECTORS:
        assert inj in md, inj
    assert "pc_bitflip" in md and "map_bitflip" in md
    assert "opcode_bitflip" in md and "stxr_force_success" in md
    assert len([l for l in md.splitlines() if l.startswith("|")]) >= 19 + 2
