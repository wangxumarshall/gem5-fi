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


def test_sad_from_stats_returns_none_when_disabled(tmp_path):
    stats = tmp_path / "stats.txt"
    stats.write_text(
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.enabled 0\n"
        "board.processor.cores.core.sad.samples 0\n"
        "board.processor.cores.core.sad.roiCycles 0\n"
        "board.processor.cores.core.sad.idleCycles 0\n"
        "board.processor.cores.core.sad.windowBegins 0\n"
        "board.processor.cores.core.sad.ratio::rob 0.00000000\n"
        "board.processor.cores.core.sad.capacity::rob 128\n"
        "End Simulation Statistics\n")
    assert sad_from_stats(stats) is None


def test_sad_from_stats_reads_roi_window(tmp_path):
    stats = tmp_path / "stats.txt"
    stats.write_text(
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.enabled 1\n"
        "board.processor.cores.core.sad.samples 90\n"
        "board.processor.cores.core.sad.activeCycles 90\n"
        "board.processor.cores.core.sad.roiCycles 100\n"
        "board.processor.cores.core.sad.idleCycles 10\n"
        "board.processor.cores.core.sad.windowBegins 1\n"
        "board.processor.cores.core.sad.windowEnds 1\n"
        "board.processor.cores.core.sad.ratio::rob 0.50000000\n"
        "End Simulation Statistics\n")
    sad = sad_from_stats(stats)
    assert sad["enabled"] == 1.0
    assert sad["samples"] == 90.0
    assert sad["active_cycles"] == 90.0
    assert sad["roi_cycles"] == 100.0
    assert sad["idle_cycles"] == 10.0
    assert sad["window_begins"] == 1.0


def test_sad_from_stats_returns_none_when_roi_never_started(tmp_path):
    stats = tmp_path / "stats.txt"
    stats.write_text(
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.enabled 1\n"
        "board.processor.cores.core.sad.samples 0\n"
        "board.processor.cores.core.sad.roiCycles 0\n"
        "board.processor.cores.core.sad.idleCycles 0\n"
        "board.processor.cores.core.sad.windowBegins 0\n"
        "board.processor.cores.core.sad.ratio::rob 0.00000000\n"
        "End Simulation Statistics\n")
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


def test_sad_issue_scalars_are_parsed_from_last_dump(tmp_path):
    stats = tmp_path / "stats.txt"
    stats.write_text(
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.issueRatio 0.900000\n"
        "board.processor.cores.core.sad.samples 100\n"
        "End Simulation Statistics\n"
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.samples 200\n"
        "board.processor.cores.core.sad.ratio::rob 0.5\n"
        "board.processor.cores.core.sad.issueRatio 0.25\n"
        "board.processor.cores.core.sad.issuedOps 400\n"
        "board.processor.cores.core.sad.issueWidth 4\n"
        "End Simulation Statistics\n")
    sad = sad_from_stats(stats)
    assert sad["samples"] == 200.0
    assert sad["ratio"] == {"rob": 0.5}
    assert sad["issue"] == {"ratio": 0.25, "issued_ops": 400.0, "width": 4.0}


def test_sad_last_dump_missing_field_does_not_inherit_earlier_value(tmp_path):
    stats = tmp_path / "stats.txt"
    stats.write_text(
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.ratio::rob 0.9\n"
        "End Simulation Statistics\n"
        "Begin Simulation Statistics\n"
        "board.processor.cores.core.sad.samples 10\n"
        "End Simulation Statistics\n")
    sad = sad_from_stats(stats)
    assert sad["samples"] == 10.0
    assert sad["ratio"] == {}


def test_markdown_reports_issue_utilisation_separately(tmp_path):
    matrix_path = tmp_path / "coverage_matrix.json"
    matrix_path.write_text(json.dumps(matrix_document()))
    sad = {"samples": 10.0, "ratio": {"rob": 0.5}, "used_sum": {"rob": 5.0},
           "capacity": {"rob": 10.0},
           "issue": {"ratio": 0.25, "issued_ops": 40.0, "width": 4.0}}
    write_report(load_matrix(matrix_path), tmp_path / "report", sad=sad,
                 source=matrix_path)
    markdown = (tmp_path / "report/coverage_summary.md").read_text()
    assert "| `issue` | 0.250000 | 40.0 | 4.0 |" in markdown
    assert "不是结构功能覆盖率" in markdown
