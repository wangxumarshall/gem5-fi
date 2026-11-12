#!/usr/bin/env python3
"""Agent D — static tests for the LSU v3.3.3 ordered shell pipeline.

These tests never start gem5 and never execute a campaign script. They check
syntax (``bash -n``) and the frozen contracts of the five final_config shell
scripts plus the runbook:

* every script pins the frozen binary/config SHA, campaign id and output root;
* 01 refuses a non-empty root and only forwards ``--resume`` explicitly;
* 02/03/04 declare ordered, disjoint stages and fail closed;
* 04 delegates every control state to the strict
  ``lsu_v333_control_proof.py --emit-control-audit`` emitter and rejects
  UNKNOWN/INVALID;
* the runbook documents dry-run / launch / resume / collect / report.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CFG_DIR = ROOT / "audit_v3_3_3/trace_closure/final_config"
RUNBOOK = CFG_DIR / "RUNBOOK_Final_Formal_Campaign.md"

SCRIPTS = {
    "01_launch_campaign.sh": CFG_DIR / "01_launch_campaign.sh",
    "02_manifest_only.sh": CFG_DIR / "02_manifest_only.sh",
    "03_full_collector.sh": CFG_DIR / "03_full_collector.sh",
    "04_final_reports.sh": CFG_DIR / "04_final_reports.sh",
    "launch_commands_final.sh": CFG_DIR / "launch_commands_final.sh",
}

BIN = ("62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b758"
       "1467a6cd")
CFG = ("8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b8199"
       "2cb225")
CAMPAIGN_ID = "LSU-V333-FINAL-20261112"
RUNS = "runs/lsu/formal_v333_final_20261112"

MANIFEST_DIR = "collector_manifest"
FULL_DIR = "collector_full"


def text(name: str) -> str:
    return SCRIPTS[name].read_text(encoding="utf-8")


def test_all_scripts_exist():
    missing = [name for name, path in SCRIPTS.items() if not path.is_file()]
    assert not missing, f"missing shell scripts: {missing}"
    assert RUNBOOK.is_file(), "runbook is missing"


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_script_bash_syntax(name):
    proc = subprocess.run(["bash", "-n", str(SCRIPTS[name])],
                          capture_output=True, text=True)
    assert proc.returncode == 0, f"bash -n {name} failed:\n{proc.stderr}"


def test_runbook_bash_blocks_syntax(tmp_path):
    """The runbook's command blocks are executable bash, not prose."""
    body = RUNBOOK.read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)```", body, flags=re.S)
    assert blocks, "runbook has no ```bash command blocks"
    for index, block in enumerate(blocks):
        path = tmp_path / f"runbook_block_{index}.sh"
        path.write_text(block, encoding="utf-8")
        proc = subprocess.run(["bash", "-n", str(path)],
                              capture_output=True, text=True)
        assert proc.returncode == 0, (
            f"runbook bash block #{index} is not valid bash:\n{proc.stderr}")


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_script_pins_frozen_identity(name):
    body = text(name)
    assert BIN in body, f"{name} does not pin the frozen binary SHA"
    assert CFG in body, f"{name} does not pin the frozen config SHA"
    assert CAMPAIGN_ID in body, f"{name} does not pin the campaign id"
    assert RUNS in body, f"{name} does not pin the campaign root"


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_script_fails_closed(name):
    body = text(name)
    assert "set -euo pipefail" in body, f"{name} lacks set -euo pipefail"


# ---------------------------------------------------------------------------
# 01 — launch / resume
# ---------------------------------------------------------------------------
def test_01_supports_resume_and_refuses_nonempty_root():
    body = text("01_launch_campaign.sh")
    assert "RESUME" in body and "--resume" in body
    assert "RESUME=1" in body
    # explicit forwarding of --resume to the matrix runner
    assert re.search(r"if \[ \"\$RESUME\" = \"1\" \]; then\s*\n\s*"
                     r"runner_args\+=\(--resume\)", body), \
        "01 does not forward --resume to the runner"
    # refuses a non-empty root unless resume was requested
    assert "refusing to reuse a non-empty formal output dir" in body
    assert "ls -A" in body
    assert "exit 2" in body


def test_01_dry_run_does_not_create_root_or_force():
    body = text("01_launch_campaign.sh")
    assert "--dry-run" in body
    assert "runner_args+=(--dry-run)" in body
    assert 'if [ "$DRY_RUN" != "1" ]; then' in body
    # the runner must never be given --force
    assert "--force" not in body


def test_01_rejects_unknown_arguments():
    body = text("01_launch_campaign.sh")
    assert "unknown argument" in body


# ---------------------------------------------------------------------------
# 02 / 03 / 04 — ordered, disjoint stages
# ---------------------------------------------------------------------------
def test_02_writes_manifest_dir_only():
    body = text("02_manifest_only.sh")
    assert f'OUT="$RUNS/{MANIFEST_DIR}"' in body
    assert f'--out "$OUT"' in body
    assert "--manifest-only" in body
    # disjoint from the full collector, asserted in-script
    assert f'FULL="$RUNS/{FULL_DIR}"' in body
    assert re.search(r'if \[ "\$OUT" = "\$FULL" \]', body)
    assert "collector_full" in body  # only as the collision target
    assert f'--out {RUNS}/{FULL_DIR}' not in body


def test_02_requires_complete_campaign_root():
    body = text("02_manifest_only.sh")
    assert "campaign_identity.json" in body
    assert "campaign root is incomplete" in body
    assert "summary.json" in body and "campaign.json" in body
    assert re.search(r"12 models|MODELS=", body)
    assert "exit 3" in body


def test_03_requires_stage1_and_stage2_inputs():
    body = text("03_full_collector.sh")
    assert f'FULL="$RUNS/{FULL_DIR}"' in body
    assert f'MAN="$RUNS/{MANIFEST_DIR}"' in body
    # disjointness assertion
    assert re.search(r'if \[ "\$FULL" = "\$MAN" \]', body)
    # campaign root completeness (stage 1)
    assert "campaign root is incomplete" in body
    assert "summary.json" in body and "campaign.json" in body
    # stage-2 artifacts are ordered inputs
    assert "LSU_120Run_Campaign_Manifest.csv" in body
    assert "LSU_60Fault_60Control_Pair_Map.csv" in body
    assert "LSU_Control_Zero_Proof_Final.csv" in body
    assert "STEP 2 output missing" in body
    assert "exit 4" in body


def test_04_requires_collector_full_outputs():
    body = text("04_final_reports.sh")
    assert f'COLL="$RUNS/{FULL_DIR}"' in body
    for required in (
        "LSU_120Run_Campaign_Manifest.csv",
        "LSU_60Fault_60Control_Pair_Map.csv",
        "LSU_Control_Zero_Proof_Final.csv",
        "LSU_Formal_Experiment_Config_Final.xlsx",
        "LSU_60Context_Final_Readiness.csv",
    ):
        assert required in body, f"04 does not require {required}"
    assert "STEP 3 collector_full output missing" in body


def test_stage_outputs_are_disjoint():
    manifest = text("02_manifest_only.sh")
    full = text("03_full_collector.sh")
    reports = text("04_final_reports.sh")
    # 02 writes collector_manifest, 03 writes collector_full, 04 writes root reports.
    assert f'OUT="$RUNS/{MANIFEST_DIR}"' in manifest
    assert f'FULL="$RUNS/{FULL_DIR}"' in full
    assert "LSU_60Context_Causal_Propagation_Final.csv" in reports
    assert "LSU_Final_Experiment_Config.xlsx" in reports
    # 03 never writes into collector_manifest
    assert f'--out {RUNS}/{MANIFEST_DIR}' not in full
    # 04 never writes into either collector directory
    assert f'--out {RUNS}/{MANIFEST_DIR}' not in reports
    assert f'--out {RUNS}/{FULL_DIR}' not in reports


def test_stages_reject_historical_evidence_roots():
    for name in ("02_manifest_only.sh", "03_full_collector.sh",
                 "04_final_reports.sh"):
        body = text(name)
        assert "refusing historical pilot/pre-formal evidence root" in body, \
            f"{name} does not reject historical roots"
        assert "audit_v3_3_3/runs" in body
        assert "formal_v333" in body


# ---------------------------------------------------------------------------
# 04 — strict tri-state control audit and FORCE semantics
# ---------------------------------------------------------------------------
def test_04_has_no_inline_injection_count_logic():
    body = text("04_final_reports.sh")
    assert 'in ("0", "")' not in body
    assert "InjectionCount" not in body


def test_04_uses_strict_control_audit_emitter():
    body = text("04_final_reports.sh")
    assert "tools/lsu_v333_control_proof.py" in body
    assert "--emit-control-audit" in body
    assert "--proof" in body
    assert 'LSU_Control_Zero_Proof_Final.csv' in body
    assert 'LSU_Control_Audit_Formal.csv' in body


def test_04_fails_on_unknown_or_invalid_control_state():
    body = text("04_final_reports.sh")
    assert "UNKNOWN" in body and "INVALID" in body
    assert "ControlInjected" in body
    assert "exit 5" in body or "SystemExit(5)" in body


def test_04_requires_force_to_overwrite_reports():
    body = text("04_final_reports.sh")
    assert "FORCE" in body
    assert "--force" in body
    assert "refusing to overwrite an existing report" in body
    for guard in ("$PROP", "$READY", "$VALID", "$CTL", "$BOOK"):
        assert f'refuse_overwrite "{guard}"' in body, \
            f"04 does not guard overwrite of {guard}"


def test_04_runs_workbook_and_trace_closure():
    body = text("04_final_reports.sh")
    assert "tools/lsu_v333_workbook.py" in body
    assert "tools/lsu_v333_propagation.py" in body
    assert "tools/lsu_v333_trace_closure.py" in body


# ---------------------------------------------------------------------------
# launch commands + runbook
# ---------------------------------------------------------------------------
def test_launch_commands_covers_full_sequence():
    body = text("launch_commands_final.sh")
    for stage in ("preflight", "dry-run", "launch", "resume", "collect",
                  "report"):
        assert stage in body, f"launch_commands_final.sh lacks {stage} stage"
    for script in ("01_launch_campaign.sh", "02_manifest_only.sh",
                   "03_full_collector.sh", "04_final_reports.sh"):
        assert script in body, f"launch_commands_final.sh never calls {script}"
    assert "sha256sum -c" in body
    assert CURATED_ORDER_OK(body), \
        "collect must run 02 before 03"


def CURATED_ORDER_OK(body: str) -> bool:
    return body.index("02_manifest_only.sh") < body.index("03_full_collector.sh")


def test_runbook_documents_dry_run_launch_resume_collect_report():
    body = RUNBOOK.read_text(encoding="utf-8")
    lowered = body.lower()
    for keyword in ("dry run", "dry-run", "launch", "resume", "collect",
                    "report"):
        assert keyword in lowered, f"runbook does not document {keyword!r}"
    for script in ("01_launch_campaign.sh", "02_manifest_only.sh",
                   "03_full_collector.sh", "04_final_reports.sh",
                   "launch_commands_final.sh"):
        assert script in body, f"runbook does not reference {script}"
    assert "--resume" in body
    assert "--dry-run" in body
    assert "FORCE=1" in body
    assert BIN in body and CFG in body and CAMPAIGN_ID in body
    assert RUNS in body
    # ordered pipeline: stage 2 command precedes stage 3 command
    assert body.index("02_manifest_only.sh") < body.index("03_full_collector.sh")
    assert body.index("03_full_collector.sh") < body.index("04_final_reports.sh")


def test_runbook_documents_recovery_and_disjoint_outputs():
    body = RUNBOOK.read_text(encoding="utf-8")
    assert "Failure and recovery" in body
    assert MANIFEST_DIR in body and FULL_DIR in body
    assert "distinct" in body or "disjoint" in body
