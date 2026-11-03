#!/usr/bin/env python3
"""fsu_oracle.py — FSU W5 element-wise oracle for PolyBench output arrays.

The fp32 comparison path is also the single implementation reused by
``tools/fsu_w6_oracle.py`` for the W6 FFT / sparse-cg components (the W6
module only adds an fp64 path for SVD). ``schemas/fsu_oracle.schema.json``
stays W5-specific; W6 has its own meta contract.

The C side (``workloads/ooo/polybench/utilities/gem5fi_oracle.h``) optionally
writes ONE live-out array as raw little-endian bytes and prints::

    ARRAY_DUMP path=<p> count=<n> elem_size=<s> fnv1a=<16hex>

This module loads the pre-registered meta file plus the golden and fault
dumps, validates every byte, compares element by element and reports::

    category = EXACT_MATCH | WITHIN_TOLERANCE | DIFF

Honesty rules enforced here
---------------------------
* The byte stream is canonical: fp32, row-major, explicitly little-endian.
  File length MUST equal ``count * 4``; nothing is truncated or padded.
* Tolerances are REQUIRED arguments to :func:`compare` (no defaults) and
  come either from the pre-registered meta file or from an explicit CLI
  triple.  This tool never derives a tolerance from the observed result.
* NaN: two NaNs match iff their 32-bit patterns are identical; NaN never
  matches a non-NaN, and no tolerance rescues a NaN mismatch.
* Inf: +Inf matches +Inf, -Inf matches -Inf; a finite/infinite mismatch is
  never rescued by a tolerance.
* A finite element matches iff::

      abs_error <= abs_tol  OR  rel_error <= rel_tol  OR  ulp <= ulp_tol

  i.e. the three tolerance classes are OR-ed per element (a single
  tolerance passing is enough).  ``rel_error`` is ``abs_error / |golden|``;
  if ``golden == 0`` it is 0 for ``fault == 0`` and +Inf otherwise.
  ULP distance is the distance between the two fp32 bit patterns under the
  standard order-preserving integer mapping (it is only defined for two
  finite values; non-finite pairs are handled by the explicit rules above).
* The category is ``EXACT_MATCH`` when every raw 32-bit pattern is equal,
  ``DIFF`` when at least one element fails the OR rule, and
  ``WITHIN_TOLERANCE`` when the bytes differ but every element passes.

CLI
---
::

    python3 tools/fsu_oracle.py --golden G.bin --fault F.bin --meta M.json \
        --out result.json [--abs-tol X --rel-tol Y --ulp-tol N]

Exit codes: 0 = EXACT_MATCH or WITHIN_TOLERANCE, 3 = DIFF, 1 = usage /
validation error.  If any tolerance flag is given, all three must be given
(partial overrides would mix pre-registration sources).  Non-finite result
metrics are serialised as the strings "inf"/"-inf"/"nan" so the output
stays valid JSON.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union

ORACLE_VERSION = "fsu-oracle-v1"
RESULT_SCHEMA = "fsu-oracle-result-v1"

# W5 PolyBench programs plus the W6 artifact components. The fp32 path of
# tools/fsu_w6_oracle.py delegates to this module, so W6 fp32 comparisons
# share exactly the same implementation as W5.
PROGRAMS = ("gemm", "2mm", "lu", "cholesky", "jacobi-2d",
            "svd", "fft", "sparse-cg")
DTYPE_FP32 = "fp32"
LAYOUT_ROW_MAJOR = "row-major"
ENDIANNESS_LITTLE = "little"
DOMAIN_FULL = "full"
DOMAIN_LOWER_TRIANGLE = "lower_triangle_incl_diag"
DOMAINS = (DOMAIN_FULL, DOMAIN_LOWER_TRIANGLE)

_FP32_BYTES = 4
_META_REQUIRED = (
    "program_id",
    "golden_id",
    "dtype",
    "layout",
    "endianness",
    "count",
    "shape",
    "abs_tol",
    "rel_tol",
    "ulp_tol",
    "oracle_version",
)
_META_OPTIONAL = ("domain", "fnv1a")
_META_ALLOWED = frozenset(_META_REQUIRED + _META_OPTIONAL)

FNV1A64_OFFSET = 0xCBF29CE484222325
FNV1A64_PRIME = 0x100000001B3
_U32_MASK = 0xFFFFFFFF


class OracleError(Exception):
    """Base class for honest, loud oracle failures."""


class OracleMetaError(OracleError):
    """Invalid or unregistered meta file."""


class OracleArrayError(OracleError):
    """Invalid array dump (size, hash, missing file, ...)."""


@dataclasses.dataclass(frozen=True)
class ArrayDump:
    """One validated canonical dump."""

    path: str
    raw: bytes
    bits: Tuple[int, ...]
    values: Tuple[float, ...]
    count: int
    elem_size: int
    sha256: str

    def __len__(self) -> int:
        return self.count


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def fnv1a64(data: bytes) -> int:
    """FNV-1a 64 over raw bytes (same definition as the C dump)."""
    h = FNV1A64_OFFSET
    for byte in data:
        h ^= byte
        h = (h * FNV1A64_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def canonical_sha256(data: Union[bytes, bytearray, memoryview]) -> str:
    """SHA-256 of the canonical (already little-endian, packed) bytes.

    The dumps written by ``gem5fi_oracle.h`` ARE canonical, so this is
    simply SHA-256 over the file bytes.  It is exposed as its own function
    so callers never re-serialise the array differently before hashing.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("canonical_sha256 expects bytes-like data")
    return hashlib.sha256(bytes(data)).hexdigest()


def _require_int(value: Any, name: str, minimum: Optional[int] = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OracleMetaError(f"{name} must be an integer, got {value!r}")
    if minimum is not None and value < minimum:
        raise OracleMetaError(f"{name} must be >= {minimum}, got {value}")
    return value


def _require_tol(value: Any, name: str, *, integer: bool) -> Union[int, float]:
    if integer:
        return _require_int(value, name, minimum=0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OracleMetaError(f"{name} must be a number, got {value!r}")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise OracleMetaError(f"{name} must be a finite number >= 0, got {value!r}")
    return value


def _require_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise OracleMetaError(f"{name} must be a non-empty string, got {value!r}")
    return value


def validate_meta(meta: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate and normalise a meta mapping; return a plain dict.

    This is the pre-registration check: dtype/layout/endianness/shape/count
    and all three tolerances must already be fixed.  Unknown keys are
    rejected (the JSON schema is strict too).
    """
    if not isinstance(meta, Mapping):
        raise OracleMetaError(f"meta must be a JSON object, got {type(meta).__name__}")

    missing = [k for k in _META_REQUIRED if k not in meta]
    if missing:
        raise OracleMetaError(f"meta missing required field(s): {', '.join(missing)}")
    unknown = sorted(set(meta) - _META_ALLOWED)
    if unknown:
        raise OracleMetaError(f"meta has unknown field(s): {', '.join(unknown)}")

    out: Dict[str, Any] = {}
    out["program_id"] = _require_str(meta["program_id"], "program_id")
    if out["program_id"] not in PROGRAMS:
        raise OracleMetaError(
            f"program_id must be one of {PROGRAMS}, got {out['program_id']!r}")
    out["golden_id"] = _require_str(meta["golden_id"], "golden_id")
    out["oracle_version"] = _require_str(meta["oracle_version"], "oracle_version")

    if meta["dtype"] != DTYPE_FP32:
        raise OracleMetaError(f"dtype must be {DTYPE_FP32!r}, got {meta['dtype']!r}")
    if meta["layout"] != LAYOUT_ROW_MAJOR:
        raise OracleMetaError(
            f"layout must be {LAYOUT_ROW_MAJOR!r}, got {meta['layout']!r}")
    if meta["endianness"] != ENDIANNESS_LITTLE:
        raise OracleMetaError(
            f"endianness must be {ENDIANNESS_LITTLE!r}, got {meta['endianness']!r}")
    out["dtype"] = DTYPE_FP32
    out["layout"] = LAYOUT_ROW_MAJOR
    out["endianness"] = ENDIANNESS_LITTLE

    shape = meta["shape"]
    if (not isinstance(shape, (list, tuple)) or len(shape) != 2
            or any(isinstance(v, bool) or not isinstance(v, int) for v in shape)):
        raise OracleMetaError(f"shape must be a 2-element integer array, got {shape!r}")
    shape = [_require_int(v, "shape[]", minimum=1) for v in shape]
    out["shape"] = shape

    count = _require_int(meta["count"], "count", minimum=1)
    out["count"] = count

    domain = meta.get("domain", DOMAIN_FULL)
    if domain not in DOMAINS:
        raise OracleMetaError(f"domain must be one of {DOMAINS}, got {domain!r}")
    out["domain"] = domain

    if domain == DOMAIN_FULL:
        expected = shape[0] * shape[1]
        if count != expected:
            raise OracleMetaError(
                f"count={count} != shape product {shape[0]}*{shape[1]}={expected} "
                f"for domain={DOMAIN_FULL}")
    else:
        if shape[0] != shape[1]:
            raise OracleMetaError(
                f"domain={DOMAIN_LOWER_TRIANGLE} requires a square shape, got {shape}")
        n = shape[0]
        expected = n * (n + 1) // 2
        if count != expected:
            raise OracleMetaError(
                f"count={count} != n*(n+1)/2={expected} for n={n} "
                f"domain={DOMAIN_LOWER_TRIANGLE}")

    out["abs_tol"] = _require_tol(meta["abs_tol"], "abs_tol", integer=False)
    out["rel_tol"] = _require_tol(meta["rel_tol"], "rel_tol", integer=False)
    out["ulp_tol"] = _require_tol(meta["ulp_tol"], "ulp_tol", integer=True)

    if "fnv1a" in meta:
        fnv = meta["fnv1a"]
        if not isinstance(fnv, str) or len(fnv) != 16:
            raise OracleMetaError(f"fnv1a must be a 16-hex string, got {fnv!r}")
        try:
            int(fnv, 16)
        except ValueError as exc:
            raise OracleMetaError(f"fnv1a must be a 16-hex string, got {fnv!r}") from exc
        out["fnv1a"] = fnv.lower()

    return out


def load_meta(source: Union[str, Path, Mapping[str, Any]]) -> Dict[str, Any]:
    """Load meta from a JSON file (or validate an already-parsed mapping)."""
    if isinstance(source, Mapping):
        return validate_meta(source)

    path = Path(source)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OracleMetaError(f"cannot read meta file {path}: {exc}") from exc
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise OracleMetaError(f"meta file {path} is not valid JSON: {exc}") from exc
    return validate_meta(parsed)


def load_array(path: Union[str, Path], meta: Mapping[str, Any]) -> ArrayDump:
    """Read and strictly validate one canonical fp32 little-endian dump.

    Checks, in order: file readable; byte length exactly ``count * 4``;
    optional pre-registered FNV-1a matches.  Returns raw bytes, fp32 bit
    patterns and float values (bit patterns are authoritative for NaN/Inf
    and exact-match decisions).
    """
    meta = validate_meta(meta)
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError as exc:
        raise OracleArrayError(f"cannot read array dump {p}: {exc}") from exc

    count = meta["count"]
    expected = count * _FP32_BYTES
    if len(raw) != expected:
        raise OracleArrayError(
            f"array dump {p} has {len(raw)} bytes, expected {expected} "
            f"(count={count} * 4); refusing truncated/padded data")

    if "fnv1a" in meta:
        actual = f"{fnv1a64(raw):016x}"
        if actual != meta["fnv1a"]:
            raise OracleArrayError(
                f"array dump {p} FNV-1a mismatch: file {actual} != "
                f"meta {meta['fnv1a']}")

    bits = tuple(struct.unpack(f"<{count}I", raw))
    values = struct.unpack(f"<{count}f", raw)
    return ArrayDump(
        path=str(p),
        raw=raw,
        bits=bits,
        values=values,
        count=count,
        elem_size=_FP32_BYTES,
        sha256=canonical_sha256(raw),
    )


def array_sha256(path: Union[str, Path], meta: Mapping[str, Any]) -> str:
    """SHA-256 of a validated dump (validates size/order/endianness first)."""
    return load_array(path, meta).sha256


# ---------------------------------------------------------------------------
# fp32 classification / ULP
# ---------------------------------------------------------------------------
def _is_nan(bits: int) -> bool:
    return (bits & 0x7F800000) == 0x7F800000 and (bits & 0x007FFFFF) != 0


def _is_inf(bits: int) -> bool:
    return (bits & 0x7FFFFFFF) == 0x7F800000


def _f32_order_key(bits: int) -> int:
    """Order-preserving monotonic integer key for an fp32 bit pattern.

    Negative values (sign bit set) are bitwise-inverted, non-negative
    values get the sign bit set.  The distance between two keys is the ULP
    distance for two finite values.  (+0.0 and -0.0 have distance 1 in this
    mapping; numeric equality is still covered by the abs/rel tolerances.)
    """
    bits &= _U32_MASK
    if bits & 0x80000000:
        return (~bits) & _U32_MASK
    return bits | 0x80000000


def _as_dump(obj: Any, meta: Mapping[str, Any], name: str) -> ArrayDump:
    if isinstance(obj, ArrayDump):
        return obj
    if isinstance(obj, (bytes, bytearray, memoryview)):
        raw = bytes(obj)
        expected = meta["count"] * _FP32_BYTES
        if len(raw) != expected:
            raise OracleArrayError(
                f"{name} has {len(raw)} bytes, expected {expected} "
                f"(count={meta['count']} * 4)")
        count = meta["count"]
        return ArrayDump(
            path=f"<{name}>",
            raw=raw,
            bits=tuple(struct.unpack(f"<{count}I", raw)),
            values=struct.unpack(f"<{count}f", raw),
            count=count,
            elem_size=_FP32_BYTES,
            sha256=canonical_sha256(raw),
        )
    raise TypeError(f"{name} must be an ArrayDump or bytes, got {type(obj).__name__}")


def _json_float(value: float) -> Union[float, str]:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare(golden: Union[ArrayDump, bytes],
            fault: Union[ArrayDump, bytes],
            meta: Mapping[str, Any],
            abs_tol: Union[int, float],
            rel_tol: Union[int, float],
            ulp_tol: int) -> Dict[str, Any]:
    """Compare two validated arrays element by element.

    ``abs_tol``/``rel_tol``/``ulp_tol`` are REQUIRED (no defaults): they
    must be pre-registered before the fault run and must never be inferred
    from the result.  Per-element match rule::

        abs_error <= abs_tol  OR  rel_error <= rel_tol  OR  ulp <= ulp_tol

    with the explicit NaN/Inf rules documented at module level.
    """
    meta = validate_meta(meta)
    abs_tol = _require_tol(abs_tol, "abs_tol", integer=False)
    rel_tol = _require_tol(rel_tol, "rel_tol", integer=False)
    ulp_tol = _require_int(ulp_tol, "ulp_tol", minimum=0)

    g = _as_dump(golden, meta, "golden")
    f = _as_dump(fault, meta, "fault")
    if g.count != meta["count"] or f.count != meta["count"]:
        raise OracleArrayError(
            f"array count mismatch: golden={g.count} fault={f.count} "
            f"meta={meta['count']}")

    mismatch_count = 0
    first_mismatch_index = -1
    first_mismatch: Optional[Dict[str, Any]] = None
    nonfinite_mismatch_count = 0
    max_abs_error = 0.0
    max_rel_error = 0.0
    max_ulp = 0
    exact_bit_match = True

    for idx, (gb, fb, gv, fv) in enumerate(zip(g.bits, f.bits, g.values, f.values)):
        if gb != fb:
            exact_bit_match = False

        g_nan, f_nan = _is_nan(gb), _is_nan(fb)
        if g_nan or f_nan:
            # NaN == NaN only for an identical bit pattern; never tolerated.
            matched = g_nan and f_nan and gb == fb
            if not matched:
                mismatch_count += 1
                nonfinite_mismatch_count += 1
                max_abs_error = math.inf
                max_rel_error = math.inf
                if first_mismatch_index < 0:
                    first_mismatch_index = idx
                    first_mismatch = _mismatch_detail(
                        idx, gb, fb, gv, fv, math.inf, math.inf, None)
            continue

        g_inf, f_inf = _is_inf(gb), _is_inf(fb)
        if g_inf or f_inf:
            # Same-sign infinity matches; finite/inf or opposite signs never do.
            matched = g_inf and f_inf and gb == fb
            if not matched:
                mismatch_count += 1
                nonfinite_mismatch_count += 1
                max_abs_error = math.inf
                max_rel_error = math.inf
                if first_mismatch_index < 0:
                    first_mismatch_index = idx
                    first_mismatch = _mismatch_detail(
                        idx, gb, fb, gv, fv, math.inf, math.inf, None)
            continue

        abs_err = abs(gv - fv)
        if gv == 0.0:
            rel_err = 0.0 if fv == 0.0 else math.inf
        else:
            rel_err = abs_err / abs(gv)
        ulp = abs(_f32_order_key(gb) - _f32_order_key(fb))

        if abs_err > max_abs_error:
            max_abs_error = abs_err
        if rel_err > max_rel_error:
            max_rel_error = rel_err
        if ulp > max_ulp:
            max_ulp = ulp

        matched = (abs_err <= abs_tol) or (rel_err <= rel_tol) or (ulp <= ulp_tol)
        if not matched:
            mismatch_count += 1
            if first_mismatch_index < 0:
                first_mismatch_index = idx
                first_mismatch = _mismatch_detail(
                    idx, gb, fb, gv, fv, abs_err, rel_err, ulp)

    if exact_bit_match:
        category = "EXACT_MATCH"
    elif mismatch_count == 0:
        category = "WITHIN_TOLERANCE"
    else:
        category = "DIFF"

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
        "abs_tol": abs_tol,
        "rel_tol": rel_tol,
        "ulp_tol": ulp_tol,
        "tolerance_semantics": (
            "element matches if abs<=abs_tol OR rel<=rel_tol OR ulp<=ulp_tol; "
            "NaN matches only the same bit pattern; Inf matches only the same sign"
        ),
        "golden_path": g.path,
        "fault_path": f.path,
        "golden_sha256": g.sha256,
        "fault_sha256": f.sha256,
        "category": category,
        "exact_bit_match": exact_bit_match,
        "mismatch_count": mismatch_count,
        "nonfinite_mismatch_count": nonfinite_mismatch_count,
        "first_mismatch_index": first_mismatch_index,
        "first_mismatch": first_mismatch,
        "max_abs_error": max_abs_error,
        "max_rel_error": max_rel_error,
        "max_ulp": max_ulp,
    }


def _mismatch_detail(index: int, gb: int, fb: int,
                     gv: float, fv: float,
                     abs_err: float, rel_err: float,
                     ulp: Optional[int]) -> Dict[str, Any]:
    return {
        "index": index,
        "golden_bits": f"0x{gb:08x}",
        "fault_bits": f"0x{fb:08x}",
        "golden": repr(gv),
        "fault": repr(fv),
        "abs_error": _json_float(abs_err),
        "rel_error": _json_float(rel_err),
        "ulp": ulp,
    }


def json_ready(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert non-finite floats in the result to JSON-safe strings."""
    def conv(value: Any) -> Any:
        if isinstance(value, float):
            return _json_float(value)
        if isinstance(value, dict):
            return {k: conv(v) for k, v in value.items()}
        if isinstance(value, list):
            return [conv(v) for v in value]
        return value

    return conv(dict(result))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Element-wise FSU oracle for PolyBench fp32 array dumps.")
    parser.add_argument("--golden", required=True, help="golden array dump (raw LE fp32)")
    parser.add_argument("--fault", required=True, help="fault-run array dump (raw LE fp32)")
    parser.add_argument("--meta", required=True, help="pre-registered meta JSON")
    parser.add_argument("--out", required=True, help="result JSON output path")
    parser.add_argument("--abs-tol", type=float, default=None,
                        help="absolute tolerance (must be given with rel/ulp overrides)")
    parser.add_argument("--rel-tol", type=float, default=None,
                        help="relative tolerance (must be given with abs/ulp overrides)")
    parser.add_argument("--ulp-tol", type=int, default=None,
                        help="ULP tolerance (must be given with abs/rel overrides)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    overrides = (args.abs_tol is not None, args.rel_tol is not None,
                 args.ulp_tol is not None)
    try:
        meta = load_meta(args.meta)
        if any(overrides) and not all(overrides):
            raise OracleError(
                "partial tolerance override: give all of --abs-tol/--rel-tol/"
                "--ulp-tol or none (tolerances are pre-registered as a triple)")
        if all(overrides):
            meta = validate_meta(dict(meta, abs_tol=args.abs_tol,
                                      rel_tol=args.rel_tol,
                                      ulp_tol=args.ulp_tol))
        golden = load_array(args.golden, meta)
        fault = load_array(args.fault, meta)
        result = compare(golden, fault, meta,
                         meta["abs_tol"], meta["rel_tol"], meta["ulp_tol"])
        out = Path(args.out)
        out.write_text(
            json.dumps(json_ready(result), indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
    except OracleError as exc:
        print(f"fsu_oracle: error: {exc}", file=sys.stderr)
        return 1

    print(f"ORACLE category={result['category']} "
          f"mismatch_count={result['mismatch_count']} "
          f"first_mismatch_index={result['first_mismatch_index']} "
          f"golden_sha256={result['golden_sha256']} "
          f"fault_sha256={result['fault_sha256']}")
    return 0 if result["category"] != "DIFF" else 3


if __name__ == "__main__":
    sys.exit(main())
