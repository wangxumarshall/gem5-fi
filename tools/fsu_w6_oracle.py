#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_w6_oracle.py — element-wise oracle for the W6 SVD/FFT/sparse suite.

W6 has three fixed artifacts:

  svd        full 8x8 Jacobi live-out matrix, fp64, count 64
  fft        N=1024 power spectrum, fp32, count 1024
  sparse-cg  16x16 five-point Laplacian CG solution, fp32, count 256

Honesty rules
-------------
* The dump format is the SAME canonical raw little-endian format written by
  the shared ``workloads/ooo/polybench/utilities/gem5fi_oracle.h`` header.
* fp32 comparisons delegate to :func:`fsu_oracle.compare` — the exact W5
  implementation, so the two artifacts cannot drift apart.
* fp64 support lives here because the W5 oracle is fp32-only. It applies the
  identical per-element rule::

      abs_error <= abs_tol  OR  rel_error <= rel_tol  OR  ulp <= ulp_tol

  NaN matches only an identical 64-bit pattern; +Inf/-Inf match only the
  same sign; no tolerance rescues a non-finite mismatch.
* Tolerances are required arguments (no defaults); they come from the
  pre-registered suite JSON and are never inferred from the result.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple, Union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_oracle as O  # noqa: E402

W6_PROGRAMS = ("svd", "fft", "sparse-cg")
DTYPES = {4: "fp32", 8: "fp64"}
ELEM_SIZES = {"fp32": 4, "fp64": 8}
ORACLE_VERSION = "fsu-w6-oracle-v1"
RESULT_SCHEMA = "fsu-w6-oracle-result-v1"

_REQUIRED = (
    "program_id", "golden_id", "dtype", "layout", "endianness", "count",
    "shape", "abs_tol", "rel_tol", "ulp_tol", "oracle_version",
)
_OPTIONAL = ("domain", "fnv1a")
_ALLOWED = frozenset(_REQUIRED + _OPTIONAL)

_M64 = (1 << 64) - 1


class W6OracleError(ValueError):
    """Loud, honest W6 oracle failure."""


@dataclasses.dataclass(frozen=True)
class ArrayDump:
    path: str
    raw: bytes
    bits: Tuple[int, ...]
    values: Tuple[float, ...]
    count: int
    elem_size: int
    sha256: str


def _int(value, name: str, minimum=None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise W6OracleError(f"{name} must be an integer, got {value!r}")
    if minimum is not None and value < minimum:
        raise W6OracleError(f"{name} must be >= {minimum}, got {value}")
    return value


def _tol(value, name: str, integer: bool):
    if integer:
        return _int(value, name, minimum=0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise W6OracleError(f"{name} must be a number, got {value!r}")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise W6OracleError(f"{name} must be finite and >= 0, got {value!r}")
    return value


def validate_meta(meta: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(meta, Mapping):
        raise W6OracleError("meta must be a JSON object")
    missing = [k for k in _REQUIRED if k not in meta]
    if missing:
        raise W6OracleError(f"meta missing required field(s): {missing}")
    unknown = sorted(set(meta) - _ALLOWED)
    if unknown:
        raise W6OracleError(f"meta has unknown field(s): {unknown}")

    pid = str(meta["program_id"])
    if pid not in W6_PROGRAMS:
        raise W6OracleError(f"program_id must be one of {W6_PROGRAMS}, "
                            f"got {pid!r}")
    dtype = str(meta["dtype"])
    if dtype not in ELEM_SIZES:
        raise W6OracleError(f"dtype must be one of {list(ELEM_SIZES)}, "
                            f"got {dtype!r}")
    if meta["layout"] != O.LAYOUT_ROW_MAJOR:
        raise W6OracleError("layout must be 'row-major'")
    if meta["endianness"] != O.ENDIANNESS_LITTLE:
        raise W6OracleError("endianness must be 'little'")
    shape = meta["shape"]
    if (not isinstance(shape, (list, tuple)) or len(shape) != 2
            or any(isinstance(v, bool) or not isinstance(v, int) for v in shape)):
        raise W6OracleError(f"shape must be a 2-element integer array, "
                            f"got {shape!r}")
    shape = [_int(v, "shape[]", minimum=1) for v in shape]
    count = _int(meta["count"], "count", minimum=1)
    if count != shape[0] * shape[1]:
        raise W6OracleError(f"count={count} != shape product "
                            f"{shape[0]}*{shape[1]}")
    domain = str(meta.get("domain", O.DOMAIN_FULL))
    if domain != O.DOMAIN_FULL:
        raise W6OracleError(f"W6 arrays use domain='full', got {domain!r}")
    out = {
        "program_id": pid,
        "golden_id": str(meta["golden_id"]),
        "oracle_version": str(meta["oracle_version"]),
        "dtype": dtype,
        "layout": O.LAYOUT_ROW_MAJOR,
        "endianness": O.ENDIANNESS_LITTLE,
        "shape": shape,
        "count": count,
        "domain": O.DOMAIN_FULL,
        "abs_tol": _tol(meta["abs_tol"], "abs_tol", integer=False),
        "rel_tol": _tol(meta["rel_tol"], "rel_tol", integer=False),
        "ulp_tol": _tol(meta["ulp_tol"], "ulp_tol", integer=True),
    }
    if "fnv1a" in meta:
        fnv = meta["fnv1a"]
        if not isinstance(fnv, str) or len(fnv) != 16:
            raise W6OracleError(f"fnv1a must be a 16-hex string, got {fnv!r}")
        int(fnv, 16)
        out["fnv1a"] = fnv.lower()
    return out


def load_meta(source) -> Dict[str, Any]:
    if isinstance(source, Mapping):
        return validate_meta(source)
    try:
        return validate_meta(json.loads(Path(source).read_text(
            encoding="utf-8")))
    except OSError as exc:
        raise W6OracleError(f"cannot read meta file {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise W6OracleError(f"meta file {source} is not valid JSON: {exc}") from exc


def load_array(path: Union[str, Path], meta: Mapping[str, Any]) -> ArrayDump:
    meta = validate_meta(meta)
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError as exc:
        raise W6OracleError(f"cannot read array dump {p}: {exc}") from exc
    size = ELEM_SIZES[meta["dtype"]]
    expected = meta["count"] * size
    if len(raw) != expected:
        raise W6OracleError(
            f"array dump {p} has {len(raw)} bytes, expected {expected} "
            f"(count={meta['count']} * {size}); refusing truncated/padded data")
    if "fnv1a" in meta:
        actual = f"{O.fnv1a64(raw):016x}"
        if actual != meta["fnv1a"]:
            raise W6OracleError(f"array dump {p} FNV-1a mismatch: {actual} != "
                                f"{meta['fnv1a']}")
    if size == 4:
        bits = tuple(struct.unpack(f"<{meta['count']}I", raw))
        values = struct.unpack(f"<{meta['count']}f", raw)
    else:
        bits = tuple(struct.unpack(f"<{meta['count']}Q", raw))
        values = struct.unpack(f"<{meta['count']}d", raw)
    return ArrayDump(str(p), raw, bits, values, meta["count"], size,
                     O.canonical_sha256(raw))


def _is_nan64(bits: int) -> bool:
    return ((bits & 0x7FF0000000000000) == 0x7FF0000000000000
            and (bits & 0x000FFFFFFFFFFFFF) != 0)


def _is_inf64(bits: int) -> bool:
    return (bits & 0x7FFFFFFFFFFFFFFF) == 0x7FF0000000000000


def _order_key64(bits: int) -> int:
    bits &= _M64
    if bits & 0x8000000000000000:
        return (~bits) & _M64
    return bits | 0x8000000000000000


def _compare_fp64(golden: ArrayDump, fault: ArrayDump, meta,
                  abs_tol: float, rel_tol: float, ulp_tol: int):
    mismatch_count = 0
    first_index = -1
    first = None
    max_abs = 0.0
    max_rel = 0.0
    max_ulp = 0
    exact = True
    for idx, (gb, fb, gv, fv) in enumerate(
            zip(golden.bits, fault.bits, golden.values, fault.values)):
        if gb != fb:
            exact = False
        if _is_nan64(gb) or _is_nan64(fb):
            matched = _is_nan64(gb) and _is_nan64(fb) and gb == fb
            if not matched:
                mismatch_count += 1
                max_abs = max_rel = math.inf
                if first_index < 0:
                    first_index = idx
                    first = _detail(idx, gb, fb, gv, fv, math.inf,
                                    math.inf, None)
            continue
        if _is_inf64(gb) or _is_inf64(fb):
            matched = _is_inf64(gb) and _is_inf64(fb) and gb == fb
            if not matched:
                mismatch_count += 1
                max_abs = max_rel = math.inf
                if first_index < 0:
                    first_index = idx
                    first = _detail(idx, gb, fb, gv, fv, math.inf,
                                    math.inf, None)
            continue
        abs_err = abs(gv - fv)
        rel_err = (0.0 if fv == 0.0 else math.inf) if gv == 0.0 \
            else abs_err / abs(gv)
        ulp = abs(_order_key64(gb) - _order_key64(fb))
        max_abs = max(max_abs, abs_err)
        max_rel = max(max_rel, rel_err)
        max_ulp = max(max_ulp, ulp)
        matched = (abs_err <= abs_tol or rel_err <= rel_tol
                   or ulp <= ulp_tol)
        if not matched:
            mismatch_count += 1
            if first_index < 0:
                first_index = idx
                first = _detail(idx, gb, fb, gv, fv, abs_err, rel_err, ulp)
    category = ("EXACT_MATCH" if exact
                else "WITHIN_TOLERANCE" if mismatch_count == 0 else "DIFF")
    return {
        "schema": RESULT_SCHEMA,
        "program_id": meta["program_id"],
        "golden_id": meta["golden_id"],
        "oracle_version": meta["oracle_version"],
        "dtype": meta["dtype"],
        "layout": meta["layout"],
        "endianness": meta["endianness"],
        "shape": list(meta["shape"]),
        "domain": meta["domain"],
        "count": meta["count"],
        "abs_tol": meta["abs_tol"],
        "rel_tol": meta["rel_tol"],
        "ulp_tol": meta["ulp_tol"],
        "tolerance_semantics": (
            "element matches if abs<=abs_tol OR rel<=rel_tol OR ulp<=ulp_tol; "
            "NaN matches only the same bit pattern; Inf matches only the same sign"),
        "golden_path": golden.path,
        "fault_path": fault.path,
        "golden_sha256": golden.sha256,
        "fault_sha256": fault.sha256,
        "category": category,
        "exact_bit_match": exact,
        "mismatch_count": mismatch_count,
        "nonfinite_mismatch_count": 0,
        "first_mismatch_index": first_index,
        "first_mismatch": first,
        "max_abs_error": max_abs,
        "max_rel_error": max_rel,
        "max_ulp": max_ulp,
    }


def _detail(index, gb, fb, gv, fv, abs_err, rel_err, ulp):
    return {
        "index": index,
        "golden_bits": f"0x{gb:016x}",
        "fault_bits": f"0x{fb:016x}",
        "golden": repr(gv),
        "fault": repr(fv),
        "abs_error": O._json_float(abs_err),
        "rel_error": O._json_float(rel_err),
        "ulp": ulp,
    }


def _raw_or_dump(obj, meta, name):
    if isinstance(obj, ArrayDump):
        return obj
    if isinstance(obj, (str, Path)):
        return load_array(obj, meta)
    if isinstance(obj, (bytes, bytearray, memoryview)):
        raw = bytes(obj)
        expected = meta["count"] * ELEM_SIZES[meta["dtype"]]
        if len(raw) != expected:
            raise W6OracleError(f"{name} has {len(raw)} bytes, expected "
                                f"{expected}")
        fmt = "I" if meta["dtype"] == "fp32" else "Q"
        vfmt = "f" if meta["dtype"] == "fp32" else "d"
        bits = tuple(struct.unpack(f"<{meta['count']}{fmt}", raw))
        values = struct.unpack(f"<{meta['count']}{vfmt}", raw)
        return ArrayDump(f"<{name}>", raw, bits, values, meta["count"],
                         ELEM_SIZES[meta["dtype"]], O.canonical_sha256(raw))
    raise TypeError(f"{name} must be bytes, a path or an ArrayDump, "
                    f"got {type(obj).__name__}")


def compare(golden, fault, meta: Mapping[str, Any], abs_tol, rel_tol,
            ulp_tol) -> Dict[str, Any]:
    """Compare two dumps with the pre-registered OR-rule tolerances."""
    meta = validate_meta(meta)
    abs_tol = _tol(abs_tol, "abs_tol", integer=False)
    rel_tol = _tol(rel_tol, "rel_tol", integer=False)
    ulp_tol = _tol(ulp_tol, "ulp_tol", integer=True)
    g = _raw_or_dump(golden, meta, "golden")
    f = _raw_or_dump(fault, meta, "fault")
    if meta["dtype"] == "fp32":
        # Same implementation as W5 (no second fp32 tolerance code path).
        result = O.compare(g.raw, f.raw, meta, abs_tol, rel_tol, ulp_tol)
        result["golden_path"] = g.path
        result["fault_path"] = f.path
        result["golden_sha256"] = g.sha256
        result["fault_sha256"] = f.sha256
        return result
    result = _compare_fp64(g, f, meta, abs_tol, rel_tol, ulp_tol)
    result["abs_tol"] = abs_tol
    result["rel_tol"] = rel_tol
    result["ulp_tol"] = ulp_tol
    result["golden_path"] = g.path
    result["fault_path"] = f.path
    result["golden_sha256"] = g.sha256
    result["fault_sha256"] = f.sha256
    result["nonfinite_mismatch_count"] = sum(
        1 for gb, fb in zip(g.bits, f.bits)
        if (_is_nan64(gb) or _is_nan64(fb) or _is_inf64(gb) or _is_inf64(fb))
        and not ((_is_nan64(gb) and _is_nan64(fb) and gb == fb)
                 or (_is_inf64(gb) and _is_inf64(fb) and gb == fb)))
    return result


def json_ready(result: Mapping[str, Any]) -> Dict[str, Any]:
    return O.json_ready(result)


def main(argv: Sequence[str] = None) -> int:
    ap = argparse.ArgumentParser(description="W6 element oracle")
    ap.add_argument("--golden", required=True)
    ap.add_argument("--fault", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        meta = load_meta(a.meta)
        result = compare(a.golden, a.fault, meta, meta["abs_tol"],
                         meta["rel_tol"], meta["ulp_tol"])
        Path(a.out).write_text(
            json.dumps(json_ready(result), indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
    except (W6OracleError, O.OracleError) as exc:
        print(f"fsu_w6_oracle: error: {exc}", file=sys.stderr)
        return 1
    print(f"W6_ORACLE category={result['category']} "
          f"mismatch_count={result['mismatch_count']}")
    return 0 if result["category"] != "DIFF" else 3


if __name__ == "__main__":
    sys.exit(main())
