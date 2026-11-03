"""tests/test_fsu_w6_oracle.py — W6 element oracle (fp32 delegation + fp64).

fp32 must delegate to tools/fsu_oracle.py bit-for-bit; fp64 implements the
same OR-rule with 64-bit IEEE patterns. Tolerances are explicit arguments.
"""
import math
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_oracle as O  # noqa: E402
import fsu_w6_oracle as WO  # noqa: E402


def meta(program="fft", dtype="fp32", count=4, shape=(1, 4),
         abs_tol=0.0, rel_tol=0.0, ulp_tol=0):
    return {
        "program_id": program,
        "golden_id": f"test-{program}-v1",
        "dtype": dtype,
        "layout": "row-major",
        "endianness": "little",
        "shape": list(shape),
        "count": count,
        "domain": "full",
        "abs_tol": abs_tol,
        "rel_tol": rel_tol,
        "ulp_tol": ulp_tol,
        "oracle_version": "fsu-w6-oracle-v1",
    }


def f32(values):
    return struct.pack(f"<{len(values)}f", *values)


def f64(values):
    return struct.pack(f"<{len(values)}d", *values)


def test_fp32_is_delegated_to_the_w5_oracle():
    m = meta()
    a = f32([1.0, 2.0, 3.0, 4.0])
    b = f32([1.0, 2.0, 3.0, 4.0])
    w6 = WO.compare(a, b, m, 0.0, 0.0, 0)
    w5 = O.compare(a, b, m, 0.0, 0.0, 0)
    assert w6["category"] == w5["category"] == "EXACT_MATCH"
    assert w6["mismatch_count"] == w5["mismatch_count"] == 0
    assert w6["golden_sha256"] == w5["golden_sha256"]


def test_fp32_tolerance_or_rule():
    m = meta()
    base = f32([1.0, 1.0, 1.0, 1.0])
    one_ulp = struct.unpack("<f", struct.pack("<I",
                                              struct.unpack("<I",
                                                            struct.pack("<f", 1.0))[0] + 1))[0]
    fault = f32([one_ulp, 1.0, 1.0, 1.0])
    assert WO.compare(base, fault, m, 0.0, 0.0, 0)["category"] == "DIFF"
    assert WO.compare(base, fault, m, 0.0, 0.0, 1)["category"] == \
        "WITHIN_TOLERANCE"
    assert WO.compare(base, fault, m, 0.0, 1e-6, 0)["category"] == \
        "WITHIN_TOLERANCE"
    assert WO.compare(base, fault, m, 1e-6, 0.0, 0)["category"] == \
        "WITHIN_TOLERANCE"


def test_fp64_exact_and_one_ulp():
    m = meta(program="svd", dtype="fp64", count=2, shape=(1, 2))
    base = f64([1.0, 2.0])
    assert WO.compare(base, base, m, 0.0, 0.0, 0)["category"] == \
        "EXACT_MATCH"
    bits = struct.unpack("<Q", struct.pack("<d", 1.0))[0]
    next_up = struct.unpack("<d", struct.pack("<Q", bits + 1))[0]
    fault = f64([next_up, 2.0])
    assert WO.compare(base, fault, m, 0.0, 0.0, 0)["mismatch_count"] == 1
    assert WO.compare(base, fault, m, 0.0, 0.0, 1)["mismatch_count"] == 0
    assert WO.compare(base, fault, m, 0.0, 0.0, 1)["category"] == \
        "WITHIN_TOLERANCE"
    # 1 ULP at 1.0 is ~2.22e-16: a smaller abs_tol must not hide it.
    assert WO.compare(base, fault, m, 1e-17, 0.0, 0)["mismatch_count"] == 1
    assert WO.compare(base, fault, m, 1e-15, 0.0, 0)["mismatch_count"] == 0


def test_fp64_nan_and_inf_rules():
    m = meta(program="svd", dtype="fp64", count=2, shape=(1, 2),
             abs_tol=1e30, rel_tol=1.0, ulp_tol=1000)
    nan1 = struct.unpack("<d", struct.pack("<Q", 0x7FF8000000000001))[0]
    nan2 = struct.unpack("<d", struct.pack("<Q", 0x7FF8000000000002))[0]
    inf = math.inf
    neg_inf = -math.inf
    assert WO.compare(f64([nan1, 1.0]), f64([nan1, 1.0]), m, 1e30, 1.0, 1000)[
        "category"] == "EXACT_MATCH"
    # Same NaN with a different payload NEVER matches, even with huge tolerances.
    assert WO.compare(f64([nan1, 1.0]), f64([nan2, 1.0]), m, 1e30, 1.0,
                      1000)["mismatch_count"] == 1
    # NaN vs finite is never rescued by a tolerance.
    assert WO.compare(f64([math.nan, 1.0]), f64([1.0, 1.0]), m, 1e30, 1.0,
                      1000)["mismatch_count"] == 1
    assert WO.compare(f64([inf, 1.0]), f64([inf, 1.0]), m, 0.0, 0.0, 0)[
        "category"] == "EXACT_MATCH"
    assert WO.compare(f64([inf, 1.0]), f64([neg_inf, 1.0]), m, 1e30, 1.0,
                      1000)["mismatch_count"] == 1
    assert WO.compare(f64([inf, 1.0]), f64([1.0, 1.0]), m, 1e30, 1.0,
                      1000)["mismatch_count"] == 1


def test_meta_validation_rejects_garbage():
    good = meta()
    assert WO.validate_meta(good)["count"] == 4
    bads = [
        dict(good, dtype="fp16"),
        dict(good, program_id="not-a-w6-program"),
        dict(good, count=3),
        dict(good, shape=[4]),
        dict(good, layout="column-major"),
        dict(good, endianness="big"),
        dict(good, domain="lower_triangle_incl_diag"),
        dict(good, abs_tol=-1.0),
        dict(good, ulp_tol=-1),
        dict(good, unknown=1),
    ]
    for bad in bads:
        with pytest.raises(WO.W6OracleError):
            WO.validate_meta(bad)
    for missing in ("program_id", "golden_id", "dtype", "layout",
                    "endianness", "count", "shape", "abs_tol", "rel_tol",
                    "ulp_tol", "oracle_version"):
        bad = dict(good)
        del bad[missing]
        with pytest.raises(WO.W6OracleError, match="missing"):
            WO.validate_meta(bad)


def test_load_array_size_mismatch_rejected(tmp_path):
    m = meta(dtype="fp64", program="svd", count=2, shape=(1, 2))
    p = tmp_path / "a.bin"
    p.write_bytes(b"\x00" * 8)  # one fp64 element, count says 2
    with pytest.raises(WO.W6OracleError, match="expected 16"):
        WO.load_array(p, m)

    p.write_bytes(f64([1.0, 2.0]))
    arr = WO.load_array(p, m)
    assert arr.count == 2 and arr.elem_size == 8


def test_fnv1a_pin_is_enforced(tmp_path):
    m = meta(count=2, shape=(1, 2))
    p = tmp_path / "a.bin"
    p.write_bytes(f32([1.0, 2.0]))
    good = f"{O.fnv1a64(p.read_bytes()):016x}"
    assert WO.load_array(p, dict(m, fnv1a=good)).count == 2
    with pytest.raises(WO.W6OracleError, match="FNV-1a mismatch"):
        WO.load_array(p, dict(m, fnv1a="0" * 16))
