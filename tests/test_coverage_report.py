"""Unit tests for the Phase-1 coverage rollup and SAD parser."""

import json
from pathlib import Path

from sdcfuzz.coverage_report import (
    load_matrix,
    sad_from_stats,
    summarize_matrix,
    write_report,
)


def matrix_document():
    return {
        "schema": "sdcfuzz.phase1.coverage_matrix.v1",
        "template_count": 3,
        "templates": {
            "t-alu": {
                "target": "alu",
                "target_metric": "alu",
                "required": {
                    "rf": ["mov", "add"],
                    "alu": ["mov", "add"],
                },
                "coverage": {"rf": 0.1, "alu": 0.2, "l1i": 0.0},
                "target_activation": 100.0,
            },
            "t-l1i": {
                "target": "l1i",
                "target_metric": "l1i",
                "required": {"rf": ["mov"]},
                "coverage": {"rf": 0.05, "alu": 0.0, "l1i": 0.01},
                "target_activation": 10.0,
            },
            "t-rf": {
                "target": "rf",
                "target_metric": "rf",
                "required": {"rf": ["mov"], "alu": ["add"]},
                "coverage": {"rf": 0.02, "alu": 0.01, "l1i": 0.0},
                "target_activation": 20.0,
            },
        },
    }


def test_summarize_counts_targeting_requiring_and_gaps():
    summary = summarize_matrix(matrix_document())
    rows = {row["structure"]: row for row in summary["structures"]}

    assert summary["template_count"] == 3
    assert summary["structure_count"] == 3
    assert summary["covered_structures"] == ["rf", "l1i", "alu"]
    assert summary["uncovered_structures"] == []

    assert rows["rf"]["targeting_count"] == 1
    assert rows["rf"]["requiring_count"] == 3
    assert rows["rf"]["observing_count"] == 3
    assert rows["rf"]["best_template"] == "t-alu"
    assert rows["rf"]["status"] == "targeted"

    assert rows["l1i"]["targeting_count"] == 1
    assert rows["l1i"]["requiring_count"] == 1
    assert rows["l1i"]["status"] == "targeted"

    assert summary["gaps"]["no_targeting_template"] == []
    assert summary["gaps"]["no_required_metric"] == []
    assert summary["gaps"]["never_observed"] == []


def test_unobserved_structure_is_reported_as_a_gap():
    document = matrix_document()
    for entry in document["templates"].values():
        entry["coverage"]["div"] = 0.0
    summary = summarize_matrix(document)
    rows = {row["structure"]: row for row in summary["structures"]}
    assert rows["div"]["status"] == "unobserved"
    assert rows["div"]["max_ratio"] == 0.0
    assert "div" in summary["uncovered_structures"]
    assert "div" in summary["gaps"]["never_observed"]
    assert "div" in summary["gaps"]["no_targeting_template"]
    assert "div" in summary["gaps"]["no_required_metric"]


def test_sad_from_stats_reads_last_dump(tmp_path):
    stats = tmp_path / "stats.txt"
    stats.write_text(
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.samples 100\n"
        "board.processor.cores.core.sad.ratio::rob 0.10\n"
        "End Simulation Statistics\n"
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.samples 200\n"
        "board.processor.cores.core.sad.ratio::rob 0.50\n"
        "board.processor.cores.core.sad.usedSum::rob 400\n"
        "board.processor.cores.core.sad.capacity::rob 192\n"
        "board.processor.cores.core.sad.ratio::lq 0.25\n"
        "End Simulation Statistics\n")
    sad = sad_from_stats(stats)
    assert sad["samples"] == 200.0
    assert sad["ratio"]["rob"] == 0.5
    assert sad["ratio"]["lq"] == 0.25
    assert sad["used_sum"]["rob"] == 400.0
    assert sad["capacity"]["rob"] == 192.0


def test_sad_from_stats_returns_none_without_sad_counters(tmp_path):
    stats = tmp_path / "stats.txt"
    stats.write_text("system.cpu.numCycles 1\n")
    assert sad_from_stats(stats) is None


def test_write_report_emits_json_csv_and_markdown(tmp_path):
    matrix_path = tmp_path / "coverage_matrix.json"
    matrix_path.write_text(json.dumps(matrix_document()))
    matrix = load_matrix(matrix_path)
    sad = {"samples": 10.0, "ratio": {"rob": 0.5},
           "used_sum": {"rob": 960.0}, "capacity": {"rob": 192.0}}
    out = tmp_path / "report"
    summary = write_report(matrix, out, sad=sad, source=matrix_path)

    assert summary["schema"] == "sdcfuzz.phase1.coverage_summary.v1"
    assert (out / "coverage_summary.json").is_file()
    assert (out / "coverage_summary.md").is_file()
    csv_text = (out / "coverage_matrix.csv").read_text()
    assert csv_text.startswith("template,target,rf,l1i,alu,target_activation")
    assert "t-alu,alu,0.100000000,0.000000000,0.200000000,100.0" in csv_text
    markdown = (out / "coverage_summary.md").read_text()
    assert "SAD 占用" in markdown
    assert "`rob`" in markdown
