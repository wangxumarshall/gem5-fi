import json
import sys
from pathlib import Path

import pytest

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from config_parser import load_config  # noqa: E402
from manifest import ManifestError, build_manifest, canonical_json, write_manifest  # noqa: E402
from oracle import check_oracle, extract_checksum  # noqa: E402

ROOT = Path(__file__).resolve().parents[6]
EXCEL = ROOT / "docs/gem5-fi/lsu/final_paper_audit_v3_1/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx"
CONFIG_SCRIPT = ROOT / "configs/se/lsu_proxy.py"


@pytest.fixture()
def cfg():
    return load_config(EXCEL, require_complete=False)


@pytest.fixture()
def fake_gem5(tmp_path):
    p = tmp_path / "gem5.opt"
    p.write_bytes(b"not a real simulator, manifest hash input only\n")
    return p


def test_manifest_uses_excel_seed_and_hashes_binary(cfg, fake_gem5, tmp_path):
    m = build_manifest(cfg, "A01-F0-W1-S01-R01", fake_gem5, CONFIG_SCRIPT,
                       output_dir=tmp_path / "out")
    assert m["seed"] == 2108120075
    assert m["seed_source"] == "excel:5.60个样本执行矩阵!Seed"
    assert m["sample_run_id"] == "A01-F0-W1-S01-R01"
    assert len(m["gem5"]["binary_sha256"]) == 64
    assert m["workload"]["sha256"] == "90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b"


def test_manifest_rejects_absent_workload(cfg, fake_gem5):
    with pytest.raises(FileNotFoundError):
        build_manifest(cfg, "LQ04-F0-W2-S01-R01", fake_gem5, CONFIG_SCRIPT)


def test_manifest_sha_is_stable(cfg, fake_gem5, tmp_path):
    a = build_manifest(cfg, "FW02-F6-W4-S01-R01", fake_gem5, CONFIG_SCRIPT,
                       output_dir=tmp_path / "out",
                       environment={"captured_at_utc": "fixed", "host": "h",
                                    "kernel": "k", "python": "3"})
    b = build_manifest(cfg, "FW02-F6-W4-S01-R01", fake_gem5, CONFIG_SCRIPT,
                       output_dir=tmp_path / "out",
                       environment={"captured_at_utc": "fixed", "host": "h",
                                    "kernel": "k", "python": "3"})
    assert a["manifest_sha256"] == b["manifest_sha256"]
    path = write_manifest(a, tmp_path / "manifest.json")
    assert json.loads(path.read_text())["manifest_sha256"] == a["manifest_sha256"]


def test_oracle_pass_fail_missing():
    assert check_oracle("728e604ffcec539d", "x checksum=0x728e604ffcec539d\n")["status"] == "PASS"
    assert check_oracle("0x728e604ffcec539d", "x checksum=0x728E604FFCEC539D\n")["status"] == "PASS"
    assert check_oracle("728e604ffcec539d", "x checksum=0x0000000000000000\n")["status"] == "FAIL"
    assert check_oracle("728e604ffcec539d", "no checksum\n")["status"] == "MISSING"
    assert extract_checksum("a checksum=0x1\nb checksum=0x2\n") == "2"
    assert check_oracle("728e604ffcec539d", "728e604ffcec539d\n")["status"] == "PASS"


def test_manifest_rejects_bad_workload_hash(cfg, fake_gem5):
    cfg["samples"][0]["binary_sha256"] = "0" * 64
    with pytest.raises(ManifestError, match="SHA mismatch"):
        build_manifest(cfg, cfg["samples"][0]["sample_run_id"], fake_gem5, CONFIG_SCRIPT)
