import sys
from collections import Counter
from pathlib import Path

import pytest

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from config_parser import (  # noqa: E402
    ConfigError,
    SAMPLE_SHEET,
    load_config,
    validate_samples,
)

LSUS = PLATFORM.parents[1]
EXCEL = LSUS / "final_paper_audit_v3_1" / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx"


def test_real_excel_has_60_samples_12_models_5_each():
    cfg = load_config(EXCEL, require_complete=False)
    assert len(cfg["samples"]) == 60
    assert len(cfg["models"]) == 12
    counts = Counter(s["model_id"] for s in cfg["samples"])
    assert set(counts.values()) == {5}
    assert len({s["seed"] for s in cfg["samples"]}) == 60


def test_absent_workload_is_reported_not_defaulted():
    cfg = load_config(EXCEL, require_complete=False)
    absent = [s for s in cfg["samples"] if s["workload_path"] == "ABSENT"]
    assert len(absent) == 45
    with pytest.raises(ConfigError) as excinfo:
        load_config(EXCEL, require_complete=True)
    err = excinfo.value
    assert err.errors
    error_ids = {e["sample_run_id"] for e in err.errors if e["field"] == "WorkloadPath"}
    assert {s["sample_run_id"] for s in absent} <= error_ids


def test_duplicate_seed_rejected():
    cfg = load_config(EXCEL, require_complete=False)
    samples = cfg["samples"]
    samples[1]["seed"] = samples[0]["seed"]
    errors = validate_samples(samples, expected_models=cfg["models"], full=False)
    assert any(e["field"] == "Seed" and "duplicate" in e["message"] for e in errors)


def test_parent_mismatch_rejected():
    cfg = load_config(EXCEL, require_complete=False)
    samples = cfg["samples"]
    samples[0]["sub_task_id"] = "A01-F0-W1-S99"
    errors = validate_samples(samples, expected_models=cfg["models"], full=False)
    assert any("parent mismatch" in e["message"] for e in errors)


def test_sample_sheet_name_is_pinned():
    assert SAMPLE_SHEET == "5.60个样本执行矩阵"
