"""Static provenance/completeness checks for the vendored upstream D13.

These tests do not need gem5 or a cross compiler; the real run is
``scripts/test-d13-upstream.sh``.
"""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "sdcfuzz/upstream/d13"

D13_SHA256 = "4143a4bdee3244452ce2747e590d6cbfbbb45117b23a3027d04a0eacc0067263"
RANDOM_SHA256 = (
    "fb461f72675c194b5a93aeeeab55f73f6fba5ad6cf4830146bc935d1c169c1be"
)
LICENSE_SHA256 = (
    "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_vendored_files_match_upstream_hashes():
    assert _sha256(VENDOR / "sdc_probe_workload_d13.c") == D13_SHA256
    assert _sha256(VENDOR / "sdc_probe_workload_random.c") == RANDOM_SHA256
    assert _sha256(VENDOR / "LICENSE") == LICENSE_SHA256


def test_d13_contains_the_documented_algorithm():
    source = (VENDOR / "sdc_probe_workload_d13.c").read_text()
    for symbol in ("rng_u64", "popcount64", "targeted_mutate",
                   "pick_high_toggle", "carry_chain", "toggle_rate",
                   "lsu_cross", "ITERS 200"):
        assert symbol in source, symbol
    # Documented mutation pieces.
    assert "a ^ mask" in source
    assert "a_mut += 1" in source
    assert "(a_mut << 1) | (a_mut >> 63)" in source
    assert "a_mut ^= ~a" in source
    # Documented selection proxy.
    assert "a_mut ^ (a_mut + 1)" in source
    assert "b ^ (b + 1)" in source
    # Pure-random operands retained for coverage breadth.
    assert "volatile uint64_t x5 = rng_u64();" in source
    assert "volatile uint64_t x8 = rng_u64();" in source


def test_d13_readme_points_at_upstream_and_local_heuristic_boundary():
    readme = (VENDOR / "README.md").read_text()
    assert "707db35da507bbe7c086ee3760ea3b3260aaf930" in readme
    assert "gem5_config/workloads/sdc_probe_workload_d13.c" in readme
    assert "operand_heuristic.py" in readme
    assert "不是 D13" in readme
