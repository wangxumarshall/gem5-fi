import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

def test_build_and_lookup():
    from sdc_fingerprint import build_library, lookup
    # 两个单元的合成指纹：lsq 的 mantissa 主导（method3 签名），prf 的 sign/exp 主导
    lsq_masks = [0x00000004, 0x00000100, 0x00000200]     # 低位 = 尾数
    prf_masks = [0x8000000000000000, 0x4000000000000000] # 高位 = 符号/指数
    lib = build_library({"lsq_fwd": lsq_masks, "physreg": prf_masks})
    assert lib["lsq_fwd"]["mantissa_share"] > 0.9
    assert lib["physreg"]["sign_exp_share"] > 0.9
    # lookup: 一个尾数主导的现场 xor -> lsq 排第一
    ranked = lookup(lib, 0x00000100)
    assert ranked[0][0] == "lsq_fwd"

def test_popcount_median():
    from sdc_fingerprint import build_library
    lib = build_library({"u": [0b111, 0b1, 0b11]})  # popcounts 3,1,2
    assert lib["u"]["popcount_median"] == 2
