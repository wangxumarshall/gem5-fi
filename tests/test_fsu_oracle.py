"""tests/test_fsu_oracle.py — W5 element-wise oracle (task 4).

Covers, with real bytes and a real compiled C dump:
  * strict byte-count / shape / dtype / endianness / garbage rejection;
  * per-element mismatch location;
  * abs / rel / ULP tolerances and their explicit OR semantics;
  * explicit NaN / Inf rules;
  * stable canonical SHA-256 and FNV-1a;
  * the C dump header (little-endian baseline, explicit big-endian input
    path, lower-triangle domain, env-var fallback, no-path no-op);
  * the CLI (--golden/--fault/--meta/--out, pre-registered tolerances).

Run: python3 -m pytest tests/test_fsu_oracle.py -q
"""
import hashlib
import json
import math
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import fsu_oracle as O  # noqa: E402

UTIL_DIR = REPO / "workloads" / "ooo" / "polybench" / "utilities"
UNIT_SRC = REPO / "tests" / "unit" / "fsu_oracle_dump_test.c"
SCHEMA_PATH = REPO / "schemas" / "fsu_oracle.schema.json"
TOOL = REPO / "tools" / "fsu_oracle.py"

ARRAY_DUMP_RE = re.compile(
    r"^ARRAY_DUMP path=(?P<path>.+) count=(?P<count>\d+) "
    r"elem_size=(?P<elem>\d+) fnv1a=(?P<fnv>[0-9a-f]{16})$")

FLAT_BITS = [
    0x01020304, 0xA1B2C3D4, 0x0F0E0D0C,
    0x11223344, 0x55667788, 0x99AABBCC,
    0xDEADBEEF, 0xCAFEBABE, 0x12345678,
]
LOWER_INDICES = (0, 3, 4, 6, 7, 8)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def pack_bits(bits):
    return struct.pack("<%dI" % len(bits), *bits)


def pack_floats(values):
    return struct.pack("<%df" % len(values), *values)


def bits_of(values):
    return [struct.unpack("<I", struct.pack("<f", v))[0] for v in values]


def f32(value):
    """Round a Python float to the nearest fp32 and return it as a float."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def make_meta(program_id="gemm", shape=(2, 2), count=None,
              domain="full", **overrides):
    if count is None:
        if domain == "full":
            count = shape[0] * shape[1]
        else:
            n = shape[0]
            count = n * (n + 1) // 2
    meta = {
        "program_id": program_id,
        "golden_id": "test-golden-v1",
        "dtype": "fp32",
        "layout": "row-major",
        "endianness": "little",
        "count": count,
        "shape": list(shape),
        "domain": domain,
        "abs_tol": 0.0,
        "rel_tol": 0.0,
        "ulp_tol": 0,
        "oracle_version": O.ORACLE_VERSION,
    }
    meta.update(overrides)
    return meta


def write_bytes(path, data):
    path.write_bytes(data)
    return path


def compare_bits(golden_bits, fault_bits, meta=None, abs_tol=0.0,
                 rel_tol=0.0, ulp_tol=0):
    """compare() over raw fp32 bit patterns (bytes path, no temp files)."""
    meta = meta or make_meta(shape=(1, len(golden_bits)))
    return O.compare(pack_bits(golden_bits), pack_bits(fault_bits), meta,
                     abs_tol, rel_tol, ulp_tol)


# ---------------------------------------------------------------------------
# meta validation / schema
# ---------------------------------------------------------------------------
def test_schema_accepts_valid_meta_and_rejects_missing_tolerance():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    meta = make_meta()
    jsonschema.validate(meta, schema)

    bad = dict(meta)
    del bad["ulp_tol"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

    bad = dict(meta, dtype="fp64")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

    bad = dict(meta, count=0)  # schema minimum is 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

    # JSON Schema cannot compute shape products; tools/fsu_oracle.py does.
    with pytest.raises(O.OracleMetaError):
        O.validate_meta(dict(meta, count=3))


def test_validate_meta_rejects_garbage():
    cases = [
        dict(make_meta(), dtype="fp64"),
        dict(make_meta(), layout="column-major"),
        dict(make_meta(), endianness="big"),
        dict(make_meta(), oracle_version=""),
        dict(make_meta(), golden_id=""),
        dict(make_meta(), program_id="not-a-program"),
        dict(make_meta(), count=True),
        dict(make_meta(), count=3),
        dict(make_meta(), shape=[2]),
        dict(make_meta(), shape=[1.0, 4]),
        dict(make_meta(), abs_tol=-1),
        dict(make_meta(), rel_tol=float("nan")),
        dict(make_meta(), ulp_tol=-1),
        dict(make_meta(), ulp_tol=1.5),
        dict(make_meta(), unknown_field=1),
        dict(make_meta(), domain="lower_triangle_incl_diag"),  # non-square
    ]
    for meta in cases:
        with pytest.raises(O.OracleMetaError):
            O.validate_meta(meta)

    for missing in ("program_id", "golden_id", "dtype", "layout",
                    "endianness", "count", "shape", "abs_tol", "rel_tol",
                    "ulp_tol", "oracle_version"):
        meta = make_meta()
        del meta[missing]
        with pytest.raises(O.OracleMetaError):
            O.validate_meta(meta)


def test_validate_meta_lower_triangle_count():
    meta = make_meta(program_id="cholesky", shape=(3, 3),
                     domain="lower_triangle_incl_diag")
    assert meta["count"] == 6
    assert O.validate_meta(meta)["domain"] == "lower_triangle_incl_diag"

    with pytest.raises(O.OracleMetaError):
        O.validate_meta(dict(meta, count=9))


def test_load_meta_rejects_bad_json(tmp_path):
    p = tmp_path / "meta.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(O.OracleMetaError):
        O.load_meta(p)

    p.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(O.OracleMetaError):
        O.load_meta(p)

    p.write_text(json.dumps(make_meta()), encoding="utf-8")
    assert O.load_meta(p)["program_id"] == "gemm"


# ---------------------------------------------------------------------------
# load_array: strict byte checks
# ---------------------------------------------------------------------------
def test_load_array_strict_size_and_metadata(tmp_path):
    meta = make_meta(shape=(1, 4))
    raw = pack_floats([1.0, 2.0, 3.0, 4.0])
    p = write_bytes(tmp_path / "a.bin", raw)

    arr = O.load_array(p, meta)
    assert arr.count == 4
    assert arr.elem_size == 4
    assert arr.sha256 == hashlib.sha256(raw).hexdigest()
    assert arr.values == (1.0, 2.0, 3.0, 4.0)
    assert arr.raw == raw

    with pytest.raises(O.OracleArrayError, match="expected 16"):
        O.load_array(write_bytes(tmp_path / "short.bin", raw[:-1]), meta)
    with pytest.raises(O.OracleArrayError, match="expected 16"):
        O.load_array(write_bytes(tmp_path / "long.bin", raw + b"\x00"), meta)
    with pytest.raises(O.OracleArrayError, match="cannot read"):
        O.load_array(tmp_path / "missing.bin", meta)


def test_load_array_verifies_pregistered_fnv1a(tmp_path):
    meta = make_meta(shape=(1, 2))
    raw = pack_floats([1.5, -2.25])
    good = f"{O.fnv1a64(raw):016x}"
    p = write_bytes(tmp_path / "a.bin", raw)

    assert O.load_array(p, dict(meta, fnv1a=good)).count == 2
    with pytest.raises(O.OracleArrayError, match="FNV-1a mismatch"):
        O.load_array(p, dict(meta, fnv1a="0" * 16))


def test_load_array_rejects_garbage_bytes_and_meta(tmp_path):
    p = write_bytes(tmp_path / "a.bin", b"\x00" * 8)
    for bad_meta in (
        dict(make_meta(shape=(1, 2)), endianness="big"),
        dict(make_meta(shape=(1, 2)), dtype="fp64"),
        dict(make_meta(shape=(1, 2)), layout="column-major"),
    ):
        with pytest.raises(O.OracleMetaError):
            O.load_array(p, bad_meta)
    # any 4-byte pattern is a valid fp32; only length/order metadata is
    # rejectable.  A count/shape mismatch is caught before reading bytes.
    with pytest.raises(O.OracleMetaError):
        O.load_array(p, make_meta(shape=(1, 2), count=3))


# ---------------------------------------------------------------------------
# compare: exact / location / categories
# ---------------------------------------------------------------------------
def test_compare_exact_match():
    bits = bits_of([1.0, -2.5, 3.25, 0.0])
    result = compare_bits(bits, bits)
    assert result["category"] == "EXACT_MATCH"
    assert result["exact_bit_match"] is True
    assert result["mismatch_count"] == 0
    assert result["first_mismatch_index"] == -1
    assert result["first_mismatch"] is None
    assert result["max_abs_error"] == 0.0
    assert result["max_rel_error"] == 0.0
    assert result["max_ulp"] == 0
    assert result["golden_sha256"] == result["fault_sha256"]


def test_compare_first_mismatch_index_and_category():
    golden = [1.0, 2.0, 3.0, 4.0, 5.0]
    fault = list(golden)
    fault[1] = 2.5
    fault[3] = 4.25

    strict = compare_bits(bits_of(golden), bits_of(fault))
    assert strict["category"] == "DIFF"
    assert strict["mismatch_count"] == 2
    assert strict["first_mismatch_index"] == 1
    assert strict["first_mismatch"]["index"] == 1
    assert strict["first_mismatch"]["golden_bits"] == "0x40000000"
    assert abs(strict["first_mismatch"]["abs_error"] - 0.5) < 1e-12
    assert abs(strict["max_abs_error"] - 0.5) < 1e-12

    tolerated = compare_bits(bits_of(golden), bits_of(fault), abs_tol=1.0)
    assert tolerated["category"] == "WITHIN_TOLERANCE"
    assert tolerated["mismatch_count"] == 0
    assert tolerated["first_mismatch_index"] == -1
    assert tolerated["exact_bit_match"] is False


def test_compare_abs_tolerance_boundary():
    # 0.25 diff: pass at exactly 0.25, fail just below.
    g, f = bits_of([1.0]), bits_of([1.25])
    assert compare_bits(g, f, abs_tol=0.25)["category"] == "WITHIN_TOLERANCE"
    assert compare_bits(g, f, abs_tol=0.2499)["category"] == "DIFF"


def test_compare_rel_tolerance_boundary():
    g, f = bits_of([100.0]), bits_of([100.5])
    ok = compare_bits(g, f, rel_tol=0.005)
    assert ok["category"] == "WITHIN_TOLERANCE"
    assert abs(ok["max_rel_error"] - 0.005) < 1e-7
    assert compare_bits(g, f, rel_tol=0.0049)["category"] == "DIFF"

    # rel_error against golden 0: 0 for equal zeros, +Inf otherwise.
    assert compare_bits(bits_of([0.0]), bits_of([0.0]),
                        rel_tol=0.0)["category"] == "EXACT_MATCH"
    zero_vs_nonzero = compare_bits(bits_of([0.0]), bits_of([1.0]))
    assert zero_vs_nonzero["category"] == "DIFF"
    assert zero_vs_nonzero["max_rel_error"] == math.inf


def test_compare_ulp_tolerance_boundary():
    g = [0x3F800000]            # 1.0f
    f = [0x3F800001]            # next fp32 above 1.0
    ok = compare_bits(g, f, ulp_tol=1)
    assert ok["category"] == "WITHIN_TOLERANCE"
    assert ok["max_ulp"] == 1
    assert compare_bits(g, f, ulp_tol=0)["category"] == "DIFF"


def test_compare_tolerance_or_semantics():
    # Only abs passes: 0.25 diff, rel/ulp tolerances too small.
    assert compare_bits(bits_of([1.0]), bits_of([1.25]),
                        abs_tol=0.25, rel_tol=0.0,
                        ulp_tol=0)["category"] == "WITHIN_TOLERANCE"
    # Only rel passes: 0.05 diff on 100.0, abs/ulp tolerances too small.
    assert compare_bits(bits_of([100.0]), bits_of([100.05]),
                        abs_tol=0.0001, rel_tol=0.001,
                        ulp_tol=0)["category"] == "WITHIN_TOLERANCE"
    # Only ULP passes: 1-ULP diff on 1.0, abs/rel tolerances too small.
    assert compare_bits([0x3F800000], [0x3F800001],
                        abs_tol=0.0, rel_tol=1e-9,
                        ulp_tol=1)["category"] == "WITHIN_TOLERANCE"
    # All three fail -> DIFF.
    assert compare_bits(bits_of([1.0]), bits_of([2.0]),
                        abs_tol=0.5, rel_tol=0.4,
                        ulp_tol=10)["category"] == "DIFF"


def test_compare_signed_zero_is_within_tolerance_not_exact():
    result = compare_bits(bits_of([0.0]), bits_of([-0.0]))
    assert result["category"] == "WITHIN_TOLERANCE"
    assert result["exact_bit_match"] is False
    assert result["mismatch_count"] == 0


# ---------------------------------------------------------------------------
# compare: NaN / Inf rules
# ---------------------------------------------------------------------------
def test_compare_nan_same_bits_matches_other_payload_rejected():
    qnan = 0x7FC00000
    assert compare_bits([qnan], [qnan])["category"] == "EXACT_MATCH"

    # Different NaN payloads are NOT equal, even with absurd tolerances.
    result = compare_bits([0x7FC00000], [0x7FC00001],
                          abs_tol=1e9, rel_tol=1e9, ulp_tol=10**9)
    assert result["category"] == "DIFF"
    assert result["nonfinite_mismatch_count"] == 1
    assert result["first_mismatch_index"] == 0

    # NaN never matches a finite value.
    result = compare_bits([0x7FC00000], [0x3F800000],
                          abs_tol=1e9, rel_tol=1e9, ulp_tol=10**9)
    assert result["category"] == "DIFF"

    # Signalling NaN is still a NaN: same pattern matches.
    snan = 0x7F800001
    assert compare_bits([snan], [snan])["category"] == "EXACT_MATCH"


def test_compare_inf_rules():
    pos, neg = 0x7F800000, 0xFF800000
    assert compare_bits([pos], [pos])["category"] == "EXACT_MATCH"
    assert compare_bits([neg], [neg])["category"] == "EXACT_MATCH"

    # Opposite signs and inf-vs-finite are never tolerated.
    for fault in (neg, 0x7F7FFFFF):
        result = compare_bits([pos], [fault],
                              abs_tol=1e9, rel_tol=1e9, ulp_tol=10**9)
        assert result["category"] == "DIFF"
        assert result["max_abs_error"] == math.inf
        assert result["max_rel_error"] == math.inf


# ---------------------------------------------------------------------------
# canonical SHA-256 / FNV
# ---------------------------------------------------------------------------
def test_canonical_sha256_stability_and_array_sha256(tmp_path):
    raw = pack_floats([1.0, 2.0, 3.0])
    expected = hashlib.sha256(raw).hexdigest()
    assert O.canonical_sha256(raw) == expected
    assert O.canonical_sha256(raw) == O.canonical_sha256(bytes(raw))
    assert O.canonical_sha256(raw) != O.canonical_sha256(raw + b"\x00")

    with pytest.raises(TypeError):
        O.canonical_sha256("not bytes")

    meta = make_meta(shape=(1, 3))
    p = write_bytes(tmp_path / "a.bin", raw)
    assert O.array_sha256(p, meta) == expected
    assert O.array_sha256(p, meta) == O.array_sha256(p, meta)

    with pytest.raises(O.OracleArrayError):
        O.array_sha256(write_bytes(tmp_path / "bad.bin", raw[:-1]), meta)


def test_compare_rejects_bytes_with_wrong_length():
    meta = make_meta(shape=(1, 2))
    with pytest.raises(O.OracleArrayError):
        O.compare(b"\x00" * 4, b"\x00" * 8, meta, 0.0, 0.0, 0)


def test_compare_requires_explicit_tolerances():
    meta = make_meta(shape=(1, 1))
    with pytest.raises(TypeError):
        O.compare(pack_bits([0x3F800000]), pack_bits([0x3F800000]), meta)
    with pytest.raises(TypeError):
        O.compare(pack_bits([0x3F800000]), pack_bits([0x3F800000]), meta, 0.0)
    with pytest.raises(O.OracleMetaError):
        O.compare(pack_bits([0x3F800000]), pack_bits([0x3F800000]), meta,
                  -1.0, 0.0, 0)


# ---------------------------------------------------------------------------
# real C dump: compile both byte-order variants, verify bytes / FNV / line
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def dump_bins(tmp_path_factory):
    outdir = tmp_path_factory.mktemp("fsu_oracle_dump_bins")
    normal = outdir / "dump_normal"
    big_input = outdir / "dump_big_input"
    base = ["gcc", "-O0", "-Wall", "-Wextra", "-I", str(UTIL_DIR)]
    for binary, extra in ((normal, []), (big_input,
                                         ["-DGEM5FI_ORACLE_HOST_IS_LITTLE_ENDIAN=0"])):
        cmd = base + extra + ["-o", str(binary), str(UNIT_SRC)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, (
            f"C dump unit test failed to compile: {' '.join(cmd)}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}")
    return normal, big_input


def _run_dump(binary, args, env=None):
    full_env = dict(os.environ)
    full_env.pop("POLYBENCH_ARRAY_DUMP", None)
    if env:
        full_env.update(env)
    return subprocess.run([str(binary)] + list(args), capture_output=True,
                          text=True, env=full_env)


def _expected_le(bits):
    return b"".join(struct.pack("<I", b) for b in bits)


def _parse_dump_line(stdout):
    lines = [ln for ln in stdout.splitlines() if ln.startswith("ARRAY_DUMP")]
    assert len(lines) == 1, f"expected exactly one ARRAY_DUMP line, got: {stdout!r}"
    m = ARRAY_DUMP_RE.match(lines[0])
    assert m, f"ARRAY_DUMP line does not match the documented format: {lines[0]!r}"
    return m


def test_c_dump_argv_little_endian_bytes_and_fnv(dump_bins, tmp_path):
    binary, _ = dump_bins
    path = tmp_path / "flat.bin"
    proc = _run_dump(binary, [f"--array-dump={path}"])
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == ""

    expected = _expected_le(FLAT_BITS)
    assert path.read_bytes() == expected
    assert [struct.unpack("<I", expected[i:i + 4])[0]
            for i in range(0, len(expected), 4)] == FLAT_BITS

    m = _parse_dump_line(proc.stdout)
    assert m.group("path") == str(path)
    assert int(m.group("count")) == 9
    assert int(m.group("elem")) == 4
    assert m.group("fnv") == f"{O.fnv1a64(expected):016x}"

    meta = make_meta(shape=(3, 3), fnv1a=m.group("fnv"))
    arr = O.load_array(path, meta)
    assert arr.count == 9
    assert arr.bits == tuple(FLAT_BITS)


def test_c_dump_env_fallback_and_cli_precedence(dump_bins, tmp_path):
    binary, _ = dump_bins
    env_path = tmp_path / "env.bin"
    cli_path = tmp_path / "cli.bin"

    proc = _run_dump(binary, [], env={"POLYBENCH_ARRAY_DUMP": str(env_path)})
    assert proc.returncode == 0, proc.stderr
    assert env_path.read_bytes() == _expected_le(FLAT_BITS)
    assert _parse_dump_line(proc.stdout).group("path") == str(env_path)

    # argv wins over the environment.
    proc = _run_dump(binary, [f"--array-dump={cli_path}"],
                     env={"POLYBENCH_ARRAY_DUMP": str(env_path)})
    assert proc.returncode == 0, proc.stderr
    assert cli_path.read_bytes() == _expected_le(FLAT_BITS)
    assert _parse_dump_line(proc.stdout).group("path") == str(cli_path)


def test_c_dump_no_path_is_a_true_noop(dump_bins, tmp_path):
    binary, _ = dump_bins
    proc = _run_dump(binary, [])
    assert proc.returncode == 0
    assert proc.stdout == ""
    assert proc.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_c_dump_lower_triangle_domain(dump_bins, tmp_path):
    binary, _ = dump_bins
    path = tmp_path / "lower.bin"
    proc = _run_dump(binary, ["--lower", f"--array-dump={path}"])
    assert proc.returncode == 0, proc.stderr

    expected_bits = [FLAT_BITS[i] for i in LOWER_INDICES]
    expected = _expected_le(expected_bits)
    assert path.read_bytes() == expected
    m = _parse_dump_line(proc.stdout)
    assert int(m.group("count")) == 6
    assert m.group("fnv") == f"{O.fnv1a64(expected):016x}"

    meta = make_meta(program_id="cholesky", shape=(3, 3),
                     domain="lower_triangle_incl_diag", fnv1a=m.group("fnv"))
    arr = O.load_array(path, meta)
    assert arr.count == 6
    assert arr.bits == tuple(expected_bits)


def test_c_dump_explicit_big_endian_input_path(dump_bins, tmp_path):
    _, big_binary = dump_bins
    path = tmp_path / "be.bin"
    proc = _run_dump(big_binary, ["--big-endian-input",
                                  f"--array-dump={path}"])
    assert proc.returncode == 0, proc.stderr
    # The explicit big-endian input is converted to the SAME canonical
    # little-endian file as the little-endian baseline.
    expected = _expected_le(FLAT_BITS)
    assert path.read_bytes() == expected
    assert _parse_dump_line(proc.stdout).group("fnv") == \
        f"{O.fnv1a64(expected):016x}"


# ---------------------------------------------------------------------------
# CLI end-to-end
# ---------------------------------------------------------------------------
def _run_cli(args):
    return subprocess.run([sys.executable, str(TOOL)] + list(args),
                          capture_output=True, text=True)


def _write_case(tmp_path, golden_values, fault_values, meta_overrides=None):
    meta = make_meta(shape=(1, len(golden_values)), **(meta_overrides or {}))
    g = write_bytes(tmp_path / "golden.bin", pack_floats(golden_values))
    f = write_bytes(tmp_path / "fault.bin", pack_floats(fault_values))
    m = tmp_path / "meta.json"
    m.write_text(json.dumps(meta), encoding="utf-8")
    return g, f, m, meta


def test_cli_exact_match_and_output_json(tmp_path):
    g, f, m, _ = _write_case(tmp_path, [1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    out = tmp_path / "out.json"
    proc = _run_cli(["--golden", str(g), "--fault", str(f),
                     "--meta", str(m), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    assert "ORACLE category=EXACT_MATCH" in proc.stdout
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["category"] == "EXACT_MATCH"
    assert result["mismatch_count"] == 0
    assert result["golden_sha256"] == result["fault_sha256"]
    assert result["abs_tol"] == 0.0
    assert result["tolerance_semantics"].startswith("element matches if abs")


def test_cli_diff_exit_code_and_first_index(tmp_path):
    g, f, m, _ = _write_case(tmp_path, [1.0, 2.0, 3.0], [1.0, 9.0, 3.0])
    out = tmp_path / "out.json"
    proc = _run_cli(["--golden", str(g), "--fault", str(f),
                     "--meta", str(m), "--out", str(out)])
    assert proc.returncode == 3, proc.stderr
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["category"] == "DIFF"
    assert result["mismatch_count"] == 1
    assert result["first_mismatch_index"] == 1


def test_cli_meta_tolerance_is_used_without_inference(tmp_path):
    # Pre-register abs_tol=1.0 in meta; the 0.5/2.0 diffs are tolerated.
    g, f, m, _ = _write_case(tmp_path, [1.0, 2.0], [1.5, 4.0],
                             meta_overrides={"abs_tol": 2.0})
    out = tmp_path / "out.json"
    proc = _run_cli(["--golden", str(g), "--fault", str(f),
                     "--meta", str(m), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["category"] == "WITHIN_TOLERANCE"
    assert result["abs_tol"] == 2.0

    # With zero tolerance the same pair is DIFF: tolerance is not inferred.
    _, _, m0, _ = _write_case(tmp_path, [1.0, 2.0], [1.5, 4.0],
                              meta_overrides={"abs_tol": 0.0})
    proc = _run_cli(["--golden", str(g), "--fault", str(f),
                     "--meta", str(m0), "--out", str(out)])
    assert proc.returncode == 3, proc.stderr


def test_cli_requires_complete_tolerance_triple(tmp_path):
    g, f, m, _ = _write_case(tmp_path, [1.0], [1.0])
    out = tmp_path / "out.json"
    proc = _run_cli(["--golden", str(g), "--fault", str(f),
                     "--meta", str(m), "--out", str(out), "--abs-tol", "1.0"])
    assert proc.returncode == 1
    assert "partial tolerance override" in proc.stderr


def test_cli_rejects_entry_size_mismatch(tmp_path):
    g, _, m, _ = _write_case(tmp_path, [1.0, 2.0], [1.0, 2.0])
    bad = write_bytes(tmp_path / "bad.bin", b"\x00" * 4)
    out = tmp_path / "out.json"
    proc = _run_cli(["--golden", str(g), "--fault", str(bad),
                     "--meta", str(m), "--out", str(out)])
    assert proc.returncode == 1
    assert "expected 8" in proc.stderr


def test_cli_serialises_nonfinite_metrics_as_strings(tmp_path):
    inf_bits = 0x7F800000
    meta = make_meta(shape=(1, 1))
    g = write_bytes(tmp_path / "golden.bin", pack_bits([0x3F800000]))
    f = write_bytes(tmp_path / "fault.bin", pack_bits([inf_bits]))
    m = tmp_path / "meta.json"
    m.write_text(json.dumps(meta), encoding="utf-8")
    out = tmp_path / "out.json"
    proc = _run_cli(["--golden", str(g), "--fault", str(f),
                     "--meta", str(m), "--out", str(out)])
    assert proc.returncode == 3, proc.stderr
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["category"] == "DIFF"
    assert result["max_abs_error"] == "inf"
    assert result["max_rel_error"] == "inf"
    assert result["first_mismatch"]["ulp"] is None
