"""Tests for the Phase-1 milestone audit.

The audit is the only place that maps gate steps to roadmap milestones, so the
tests pin both directions: a green gate must produce 10/10, and each class of
degradation (failed step, missing log, missing assertion, stale gate, missing
rollup) must fail the corresponding milestone.
"""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sdcfuzz import phase1_audit
from sdcfuzz.phase1_audit import EXPECTED_STEPS, audit

ROOT = Path(__file__).resolve().parents[1]

LOGS = {
    "pytest": "..................................\n34 passed in 0.15s\n",
    "autousens": (
        "target l1d: chosen=['ldxr', 'ldr'] net_reads=7686\n"
        "target l1d+alu: chosen=['ldxr', 'movz'] l1d_net=3848 alu_net=491968\n"
        "target mult: chosen=['madd'] net_mult=737088\n"
        "target all: alu div fpadd fpmul l1d mult rf vec\n"
        "pareto: size=7 knee=['add_lsl', 'ldxr', 'movz'] l1d_net=967\n"
        "error handling: unknown structure all fail loudly\n"
    ),
    "templates": (
        "static contract: 19 templates, 17 op kinds, 9 metric groups\n"
        "fp-add fpadd=81920\n"
        "fp-mul fpmul=81920\n"
        "all 19 templates cover every mapped instruction form\n"
        "coverage: 9/9 structures observed; gaps={'no_targeting_template': "
        "['rf', 'vec'], 'no_required_metric': [], 'never_observed': []}\n"
    ),
    "sad": ("SAD window, formula, direction, disabled and cycle-mode "
            "checks passed (cycle samples=56)\n"),
    "rf-ace": "RF ACE direction and formula checks passed\n",
    "l1-ace": "L1 ACE direction and formula checks passed\n",
    "fu-ibr": (
        "alu64: intAlu IBR=0.65390920, bits=8322496, cycles=16572\n"
        "mul64: intMult IBR=0.66111605, bits=12288000, cycles=48403\n"
        "div64: intDiv IBR=0.04996947, bits=8192000, cycles=640391\n"
        "IBR width, utilization, formula, disabled, work-ID, cycle-window "
        "and ROI-pairing checks passed\n"
    ),
    "correctness": ("Atomic access, mixed-width and ROI snapshot checks "
                    "passed\n"),
    "coverage-report": "templates=19 structures=9 covered=9\n",
}


def head_commit():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                          capture_output=True, check=True).stdout.strip()


def make_gate(tmp_path, *, age_hours=0.0, step_rc=None):
    gate_dir = tmp_path / "gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    for name, text in LOGS.items():
        (gate_dir / f"{name}.log").write_text(text)
    generated = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    steps = [{"name": name, "returncode": (step_rc or {}).get(name, 0),
              "log": str(gate_dir / f"{name}.log")}
             for name in EXPECTED_STEPS]
    gate = {
        "schema": "sdcfuzz.phase1.gate.v1",
        "generated_utc": generated.isoformat(),
        "commit": head_commit(),
        "gem5": "/nonexistent/gem5.opt",
        "failures": sum(1 for s in steps if s["returncode"]),
        "passed": all(s["returncode"] == 0 for s in steps),
        "steps": steps,
    }
    (gate_dir / "phase1_gate.json").write_text(json.dumps(gate))
    report_dir = gate_dir / "report"
    report_dir.mkdir()
    (report_dir / "coverage_summary.json").write_text(json.dumps({
        "template_count": 19,
        "structure_count": 9,
        "covered_structures": ["rf", "vec", "l1i", "l1d", "alu", "mult",
                               "div", "fpadd", "fpmul"],
        "gaps": {"no_targeting_template": ["rf", "vec"],
                 "no_required_metric": [], "never_observed": []},
        "sad": {"ratio": {"rob": 0.34}, "samples": 25746},
    }))
    return gate_dir


def by_id(report):
    return {milestone["id"]: milestone for milestone in report["milestones"]}


def test_green_gate_passes_every_milestone(tmp_path):
    report = audit(make_gate(tmp_path))
    assert report["passed"], phase1_audit.render(report)
    assert len(report["milestones"]) == 10
    assert all(milestone["passed"] for milestone in report["milestones"])


def test_failed_step_blocks_its_milestone(tmp_path):
    report = audit(make_gate(tmp_path, step_rc={"sad": 1}))
    milestones = by_id(report)
    assert not report["passed"]
    assert not milestones["p1-sad"]["passed"]
    assert milestones["p1-ace"]["passed"]
    details = " ".join(check["detail"] for check in milestones["p1-sad"]["checks"])
    assert "rc=1" in details


def test_missing_log_blocks_its_milestone(tmp_path):
    gate_dir = make_gate(tmp_path)
    (gate_dir / "l1-ace.log").unlink()
    report = audit(gate_dir)
    milestones = by_id(report)
    assert not milestones["p1-ace"]["passed"]
    assert milestones["p1-sad"]["passed"]


def test_missing_needle_blocks_its_milestone(tmp_path):
    gate_dir = make_gate(tmp_path)
    (gate_dir / "autousens.log").write_text("target l1d: chosen=[]\n")
    report = audit(gate_dir)
    assert not by_id(report)["p1-nsga"]["passed"]
    assert not by_id(report)["p1-joint-agg"]["passed"]


def test_stale_gate_fails(tmp_path):
    report = audit(make_gate(tmp_path, age_hours=48.0), max_age_hours=24.0)
    assert not by_id(report)["p1-gate"]["passed"]
    fresh = audit(make_gate(tmp_path / "fresh"), max_age_hours=24.0)
    assert by_id(fresh)["p1-gate"]["passed"]


def test_missing_coverage_rollup_fails(tmp_path):
    gate_dir = make_gate(tmp_path)
    (gate_dir / "report" / "coverage_summary.json").unlink()
    report = audit(gate_dir)
    assert not by_id(report)["p1-coverage"]["passed"]


def test_missing_gate_json_reports_error(tmp_path):
    gate_dir = make_gate(tmp_path)
    (gate_dir / "phase1_gate.json").unlink()
    report = audit(gate_dir)
    assert not report["passed"]
    assert "cannot read" in report["error"]
    assert phase1_audit.render(report).startswith("FAIL:")


def git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.email=test@example.com",
         "-c", "user.name=test", *args],
        cwd=repo, check=True, capture_output=True, text=True)


def test_code_drift_ignores_doc_only_changes(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "code.py").write_text("a\n")
    (repo / "docs").mkdir()
    (repo / "docs" / "note.md").write_text("a\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True,
                          capture_output=True, check=True).stdout.strip()

    (repo / "docs" / "note.md").write_text("b\n")
    (repo / "docs" / "new.md").write_text("new\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "docs only")
    assert phase1_audit._evidence_drift(repo, base) == []

    (repo / "code.py").write_text("b\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "code change")
    assert phase1_audit._evidence_drift(repo, base) == ["code.py"]
    assert phase1_audit._evidence_drift(repo, "0" * 40) is None
