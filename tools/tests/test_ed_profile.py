"""test_ed_profile.py — ed_profile.py 的单元测试（Task 1.1 验证）。

覆盖：全字段解析、null/uncertainty 传播、rho_overrides 优先级、
保护矩阵推导、weights 归一化、退化情形（空 units/零位）、
组合逻辑 1/3 折算、residuals 自动附加。

运行: python3 -m pytest tools/tests/test_ed_profile.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ed_profile import (COMBINATIONAL_WEIGHT, DEFAULT_RHO, UNITS,
                        CpuProfile, load_profile)

# 完整字段样例（与 taishan-v110 计划 schema 一致）
FULL = """
cpu: test-full
units:
  IFU:  {btb: {entries: 2048, width: 64, prot: none},
         ras: {entries: 32, width: 64, prot: none},
         l1i: {size: 64KiB, assoc: 4, prot: ecc_claimed_no_evidence}}
  OoO:  {rob: {entries: 97, prot: none},
         prf_int: {regs: 125, width: 64},
         prf_float: {regs: 96, width: 64},
         prf_vec: {regs: 96, width: 128},
         lq: {entries: 65}, sq: {entries: 47}}
  IEX:  {fus: {int_add: {count: 3, width: 128, op_lat: 1},
               int_mul: {count: 1, width: 128, op_lat: 3}}}
  FSU:  {fus: {fp_add: {count: 2, width: 256, op_lat: 2},
               fp_mul: {count: 2, width: 256, op_lat: 4}}}
  LSU:  {l1d: {size: 64KiB, assoc: 4, blk: 64, prot: none},
         lq: {entries: 65}, sq: {entries: 47}, forwarding: true}
  MMU:  {l2_tlb: {entries: 1024, prot: none}}
  L2C:  {l2: {size: 1MiB, assoc: 8, prot: none}}
"""


def _prof(yaml_text, tmp_path, name="t.yaml"):
    f = tmp_path / name
    f.write_text(yaml_text)
    return load_profile(f)


# --- 1. 全字段：解析 + 7 单元齐全 -----------------------------------------

def test_full_field_parse_all_units(tmp_path):
    p = _prof(FULL, tmp_path)
    assert set(p.weights().keys()) == set(UNITS)
    assert p.cpu == "test-full"


# --- 2. weights 归一化（Σ=1.0）---------------------------------------------

def test_weights_normalized(tmp_path):
    p = _prof(FULL, tmp_path)
    w = p.weights()
    assert sum(w.values()) == pytest.approx(1.0)
    # L2C（1MiB）+ LSU（64KiB L1D）+ IFU（64KiB L1i）主导，FU 组合逻辑最小
    assert w["L2C"] > w["LSU"] > w["IEX"]
    assert w["L2C"] > 0.5  # 1MiB vs ~192KiB SRAM + 小结构


# --- 3. 位容量数值抽查（手算锚）----------------------------------------------

def test_unit_bits_hand_computed(tmp_path):
    p = _prof(FULL, tmp_path)
    ub = p.unit_bits()
    # OoO: ROB 97×260 + PRF 125×64 + 96×64 + 96×128 = 25220+8000+6144+12288=51652
    assert ub["OoO"][0] == 97 * 260 + 125 * 64 + 96 * 64 + 96 * 128
    # MMU: 1024×64
    assert ub["MMU"][0] == 1024 * 64
    # IEX（组合逻辑）: (3×128 + 1×128)×64×(1/3) = 512×64/3 → int
    expect_iex = int((3 * 128 + 1 * 128) * 64 * COMBINATIONAL_WEIGHT)
    assert ub["IEX"][0] == expect_iex
    assert ub["IEX"][1] is True   # is_combinational
    assert ub["OoO"][1] is False


# --- 4. null/undisclosed → uncertainty 传播 ---------------------------------

def test_null_field_uncertainty(tmp_path):
    y = FULL.replace("l2_tlb: {entries: 1024, prot: none}",
                     "l2_tlb: {entries: null, prot: none}")
    p = _prof(y, tmp_path)
    assert any(u == "MMU" for u, _, _ in p.uncertainties)
    assert p.unit_bits()["MMU"][0] == 0  # null → 0 位


# --- 5. rho_overrides 优先级 > 保护矩阵 > 缺省 -------------------------------

def test_rho_override_priority(tmp_path):
    y = FULL + "rho_overrides: {FSU: 0.33}\n"
    p = _prof(y, tmp_path)
    assert p.rho_initial()["FSU"] == 0.33


def test_rho_default_without_protection(tmp_path):
    p = _prof(FULL, tmp_path)
    r = p.rho_initial()
    # IFU 无保护面（btb/ras none）→ DEFAULT_RHO[IFU]=0.0（Phase 16 锚，0×规则）
    assert r["IFU"] == DEFAULT_RHO["IFU"] == 0.0
    # L2C none → PROT 1.0×0.45 = 0.45
    assert r["L2C"] == pytest.approx(0.45)


def test_rho_secded_l2c(tmp_path):
    y = FULL.replace("l2: {size: 1MiB, assoc: 8, prot: none}",
                     "l2: {size: 1MiB, assoc: 8, prot: secded}")
    p = _prof(y, tmp_path)
    # secded：data-face 全修 → tag-face 0.45（DEFAULT，实测线）
    assert p.rho_initial()["L2C"] == pytest.approx(0.45)


# --- 6. ceiling 覆盖与缺省 ---------------------------------------------------

def test_ceiling_default_and_override(tmp_path):
    p = _prof(FULL, tmp_path)
    assert p.ceiling("IFU") == 0.0    # Phase 16 锚
    assert p.ceiling("MMU") == 0.2    # SE 可达
    y = FULL + "ceilings: {MMU: 0.9}\n"
    p2 = _prof(y, tmp_path)
    assert p2.ceiling("MMU") == 0.9


# --- 7. 退化：空 units / 全 null ----------------------------------------------

def test_degenerate_empty_units(tmp_path):
    p = _prof("cpu: empty\nunits: {}\n", tmp_path)
    w = p.weights()
    assert all(v == 0.0 for v in w.values())
    assert sum(w.values()) == 0.0  # 不 NaN


def test_degenerate_all_null_sizes(tmp_path):
    p = _prof("cpu: n\nunits:\n  L2C: {l2: {size: null}}\n", tmp_path)
    assert p.unit_bits()["L2C"][0] == 0


# --- 8. residuals 自动附加 ----------------------------------------------------

def test_residuals_auto_append(tmp_path):
    p = _prof(FULL, tmp_path)
    res = p.residuals()
    assert "combinational_weight_1_3" in res          # 恒附加
    y = FULL.replace("entries: 1024, prot: none", "entries: null, prot: none")
    p2 = _prof(y, tmp_path)
    assert any("w_point_estimate" in r for r in p2.residuals())


# --- 9. 组合逻辑折算系数生效 ---------------------------------------------------

def test_combinational_weight_applied(tmp_path):
    p = _prof(FULL, tmp_path)
    raw_gates = (3 * 128 + 1 * 128) * 64  # 未折算
    assert p.unit_bits()["IEX"][0] < raw_gates
    assert p.unit_bits()["IEX"][0] == int(raw_gates * COMBINATIONAL_WEIGHT)


# --- 10. report 可渲染且含关键行 ------------------------------------------------

def test_report_renders(tmp_path):
    p = _prof(FULL, tmp_path)
    r = p.report()
    assert "test-full" in r
    for u in UNITS:
        assert u in r
    assert "Σw = 1.0000" in r
