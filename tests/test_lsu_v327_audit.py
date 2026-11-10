"""Tests for tools/update_lsu_v327_audit.py (LSU v3.2.12 Task 19 prep).

The derivation rules pinned here (all fixtures synthetic under tmp_path — no
committed verdict file is read, so the suite stays valid when the final
regenerated closure matrix replaces the intermediate one):

- PROPAGATION_VERIFIED=1 requires >=2 COMPLETE_CAUSAL_CHAIN records inside
  ONE binary group (standard §4 distinct-context rule; the closure tool
  adjudicated distinctness at aggregation time);
- one complete record on each of two binaries is NOT verification (verdicts
  are never merged across binaries, standard §6 invariant);
- a uniform single-context group (COMPLETE_CAUSAL_CHAIN, PilotCount=1) is
  NOT verification;
- the frozen prior-audit sidecar carries the v3.2.11 frozen four when the
  matrix does not, and is cross-checked against the frozen v3.2.11 audit
  matrix + frozen status matrix — a sidecar claiming a model the frozen audit
  did NOT verify (FW02 1/5 control-path, LQ04 LIFECYCLE_ONLY) is rejected;
- a template model with no closure-matrix row aborts the derivation unless
  explicitly declared pending (--allow-pending), and pending can only ever
  produce PROPAGATION_VERIFIED=0 — never a hand-set PASS;
- the evidence cell quotes the per-model class (verbatim FinalClassification)
  and terminal (verbatim ObservedTerminal) of the deciding group plus the
  matrix sha256;
- --set may only touch the six workflow flag columns with 0/1; a --set on
  PROPAGATION_VERIFIED is rejected; in-place overwrite of the template is
  refused;
- unparseable FinalClassification cells and mixed counts that do not sum to
  PilotCount are loud rejections.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from update_lsu_v327_audit import (  # noqa: E402
    DerivationError,
    derive_rows,
    load_closure_matrix,
    load_frozen_verdicts,
    main,
    parse_classification,
    parse_set,
)

MATRIX_HEADER = ["ModelID", "SubUnit", "FaultDefinition", "PilotCount",
                 "InjectionVerified", "ActivationVerified", "EarlyAnomalyVerified",
                 "IntermediatePropagationVerified", "RegisterWritebackVerified",
                 "ConsumerVerified", "CommitVerified", "TerminalVerified",
                 "OracleVerified", "RecordIntegrity", "TraceCompleteness",
                 "StructuralChainCompleteness", "FaultEffectPropagationCoverage",
                 "ObservedTerminal", "ApplicationOracle", "FaultCausality",
                 "FinalClassification", "MissingEvidence",
                 "SupplementaryPilotRequired", "EvidencePath"]

STATUS_HEADER = ["model", "unit", "stage", "DESIGNED", "SOURCE_AUDITED",
                 "IMPLEMENTED", "COMPILED", "UNIT_TESTED", "PILOT_RUN",
                 "PROPAGATION_VERIFIED", "evidence"]

MODELS = ["A01", "A03", "DA04", "FW02", "FW05", "LQ04", "LP01", "MD04",
          "RP01", "SP05", "SQ01", "SQ03"]

FROZEN_FOUR = ["DA04", "LP01", "MD04", "FW05"]


def matrix_row(model_id, pilot_count, final, terminal, missing="none"):
    row = {c: "x" for c in MATRIX_HEADER}
    row.update({
        "ModelID": model_id,
        "PilotCount": str(pilot_count),
        "FinalClassification": final,
        "ObservedTerminal": terminal,
        "MissingEvidence": missing,
        "EvidencePath": f"pilots/{model_id}",
    })
    return row


def write_matrix(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MATRIX_HEADER)
        w.writeheader()
        w.writerows(rows)


def write_template(path, models=MODELS):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=STATUS_HEADER)
        w.writeheader()
        for m in models:
            w.writerow({"model": m, "unit": "u", "stage": "s",
                        "DESIGNED": "1", "SOURCE_AUDITED": "1",
                        "IMPLEMENTED": "1", "COMPILED": "1",
                        "UNIT_TESTED": "1", "PILOT_RUN": "1",
                        "PROPAGATION_VERIFIED": "0",
                        "evidence": "v3.2.11-era row"})


def write_frozen_audit(path, models=("DA04", "LP01", "MD04", "FW05", "FW02", "LQ04")):
    finals = {"DA04": "COMPLETE_CAUSAL_CHAIN 2/7; LIFECYCLE_ONLY 2/7; PARTIAL 3/7",
              "LP01": "COMPLETE_CAUSAL_CHAIN 5/5",
              "MD04": "COMPLETE_CAUSAL_CHAIN 3/5; PARTIAL 2/5",
              "FW05": "COMPLETE_CAUSAL_CHAIN 4/5; PARTIAL 1/5",
              "FW02": "COMPLETE_CAUSAL_CHAIN 1/5; PARTIAL 4/5",
              "LQ04": "LIFECYCLE_ONLY 5/5"}
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ModelID", "FinalClassification"])
        for m in models:
            w.writerow([m, finals.get(m, "PARTIAL 5/5")])


def write_frozen_status(path, verified=("DA04", "LP01", "MD04", "FW05")):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "PROPAGATION_VERIFIED", "evidence"])
        w.writeheader()
        for m in MODELS:
            w.writerow({"model": m,
                        "PROPAGATION_VERIFIED": "1" if m in verified else "0",
                        "evidence": "frozen v3.2.11 row"})


def write_sidecar(path, models=FROZEN_FOUR):
    data = {"schema": "test",
            "models": {m: {"propagation_verified": 1,
                           "class": f"frozen class {m}",
                           "terminal": f"frozen terminal {m}",
                           "authority": "frozen summary"} for m in models}}
    Path(path).write_text(json.dumps(data))


def std_paths(tmp_path, matrix_rows):
    """Build the five-file fixture set; returns a kwargs dict for main()."""
    matrix = tmp_path / "matrix.csv"
    template = tmp_path / "template.csv"
    audit = tmp_path / "frozen_audit.csv"
    frozen_status = tmp_path / "frozen_status.csv"
    sidecar = tmp_path / "sidecar.json"
    out = tmp_path / "derived.csv"
    write_matrix(matrix, matrix_rows)
    write_template(template)
    write_frozen_audit(audit)
    write_frozen_status(frozen_status)
    write_sidecar(sidecar)
    return {"--closure-matrix": matrix, "--template": template,
            "--frozen-verdicts": sidecar, "--frozen-audit-matrix": audit,
            "--frozen-status-matrix": frozen_status, "--output": out}, out


def run_main(tmp_path, matrix_rows, extra=None):
    paths, out = std_paths(tmp_path, matrix_rows)
    argv = []
    for k, v in paths.items():
        argv += [k, str(v)]
    for flag, val in (extra or {}).items():
        if isinstance(val, list):
            for v in val:
                argv += [flag, str(v)]
        else:
            argv += [flag, str(val)]
    return main(argv), out


def rows_by_model(out):
    with open(out) as fh:
        return {r["model"]: r for r in csv.DictReader(fh)}


def all_model_rows(matrix_rows):
    """One matrix row per template model so nothing is missing."""
    spec = {
        # uniform single-context COMPLETE group (PilotCount=1): NOT verification
        "A01": (1, "COMPLETE_CAUSAL_CHAIN", "MASKED(1)"),
        "A03": (1, "UNRESOLVED", "CRASH(1)"),
        "DA04": (2, "COMPLETE_CAUSAL_CHAIN", "SDC(2)"),
        "FW02": (7, "mixed(COMPLETE_CAUSAL_CHAIN=2;PARTIAL=3;UNRESOLVED=2)",
                 "mixed(CRASH=1;MASKED=2;NO_INJECTION=1;SQUASHED=3)"),
        "FW05": (4, "LIFECYCLE_ONLY(4/4)", "SDC(4)"),
        "LQ04": (5, "mixed(COMPLETE_CAUSAL_CHAIN=5)", "MASKED(5)"),
        "LP01": (5, "mixed(COMPLETE_CAUSAL_CHAIN=5)", "MASKED(5)"),
        "MD04": (5, "mixed(COMPLETE_CAUSAL_CHAIN=3;PARTIAL=2)", "MASKED(3)"),
        "SP05": (12, "mixed(COMPLETE_CAUSAL_CHAIN=5;LIFECYCLE_ONLY=5;UNRESOLVED=2)",
                 "mixed(MASKED=5;NO_INJECTION=2;SDC=5)"),
        "SQ01": (12, "mixed(COMPLETE_CAUSAL_CHAIN=5;LIFECYCLE_ONLY=5;UNRESOLVED=2)",
                 "mixed(MASKED=5;NO_INJECTION=2;SDC=5)"),
        "SQ03": (12, "mixed(COMPLETE_CAUSAL_CHAIN=5;LIFECYCLE_ONLY=5;UNRESOLVED=2)",
                 "MASKED(10)"),
        "RP01": (10, "mixed(UNRESOLVED=5;PARTIAL=5)", "mixed(NO_INJECTION=5;SQUASHED=2)"),
    }
    return [matrix_row(m, n, f, t) for m, (n, f, t) in spec.items()]


def test_verified_requires_two_complete_contexts_in_one_group(tmp_path):
    rc, out = run_main(tmp_path, all_model_rows([]))
    assert rc == 0
    rows = rows_by_model(out)
    assert rows["SQ01"]["PROPAGATION_VERIFIED"] == "1"
    assert rows["LQ04"]["PROPAGATION_VERIFIED"] == "1"
    # single-context uniform group (PilotCount=1) is NOT verification
    assert rows["A01"]["PROPAGATION_VERIFIED"] == "0"
    # FW05 has rows but no complete context: carried by the frozen prior audit
    assert rows["FW05"]["PROPAGATION_VERIFIED"] == "1"
    assert "frozen prior audit (v3.2.11)" in rows["FW05"]["evidence"]
    # RP01 has rows but nothing complete and no frozen claim
    assert rows["RP01"]["PROPAGATION_VERIFIED"] == "0"


def test_never_merges_complete_contexts_across_binaries(tmp_path):
    rows = all_model_rows([])
    rows = [r for r in rows if r["ModelID"] != "SP05"]
    rows += [matrix_row("SP05@shaA", 1, "COMPLETE_CAUSAL_CHAIN", "MASKED(1)"),
             matrix_row("SP05@shaB", 1, "COMPLETE_CAUSAL_CHAIN", "MASKED(1)")]
    rc, out = run_main(tmp_path, rows)
    assert rc == 0
    assert rows_by_model(out)["SP05"]["PROPAGATION_VERIFIED"] == "0"


def test_missing_model_row_is_rejected_and_pending_is_explicit(tmp_path):
    rows = [r for r in all_model_rows([]) if r["ModelID"] != "RP01"]
    paths, out = std_paths(tmp_path, rows)
    argv = []
    for k, v in paths.items():
        argv += [k, str(v)]
    rc = main(argv)
    assert rc == 2
    assert not out.exists()

    rc2, out2 = run_main(tmp_path, rows, extra={"--allow-pending": ["RP01"]})
    assert rc2 == 0
    rp = rows_by_model(out2)["RP01"]
    assert rp["PROPAGATION_VERIFIED"] == "0"
    assert "PENDING_NO_ROW" in rp["evidence"]


def test_stale_pending_declaration_is_rejected(tmp_path):
    rc, out, = run_main(tmp_path, all_model_rows([]),
                        extra={"--allow-pending": ["LQ04"]})
    assert rc == 2  # LQ04 HAS a row; the pending declaration must be removed


def test_frozen_sidecar_cannot_verify_what_the_frozen_audit_did_not(tmp_path):
    rows = [r for r in all_model_rows([]) if r["ModelID"] != "FW05"]
    paths, out = std_paths(tmp_path, rows)
    sidecar = json.loads(Path(paths["--frozen-verdicts"]).read_text())
    sidecar["models"]["FW02"] = {"propagation_verified": 1, "class": "x",
                                 "terminal": "y", "authority": "z"}
    Path(paths["--frozen-verdicts"]).write_text(json.dumps(sidecar))
    argv = []
    for k, v in paths.items():
        argv += [k, str(v)]
    rc = main(argv)
    assert rc == 2
    assert not out.exists()


def test_sidecar_rejects_model_with_zero_frozen_status(tmp_path):
    rows = [r for r in all_model_rows([]) if r["ModelID"] != "FW05"]
    paths, out = std_paths(tmp_path, rows)
    # LQ04 has v3.2.11 complete?  No: LIFECYCLE_ONLY 5/5 -> must be rejected too
    sidecar = json.loads(Path(paths["--frozen-verdicts"]).read_text())
    sidecar["models"]["LQ04"] = {"propagation_verified": 1, "class": "x",
                                 "terminal": "y", "authority": "z"}
    Path(paths["--frozen-verdicts"]).write_text(json.dumps(sidecar))
    argv = []
    for k, v in paths.items():
        argv += [k, str(v)]
    assert main(argv) == 2


def test_evidence_quotes_class_and_terminal_and_matrix_sha(tmp_path):
    rc, out = run_main(tmp_path, all_model_rows([]))
    assert rc == 0
    rows = rows_by_model(out)
    ev = rows["SQ01"]["evidence"]
    assert "sha256:" in ev
    assert "mixed(COMPLETE_CAUSAL_CHAIN=5;LIFECYCLE_ONLY=5;UNRESOLVED=2)" in ev
    assert "mixed(MASKED=5;NO_INJECTION=2;SDC=5)" in ev
    assert rows["A03"]["evidence"].count("sha256:") == 1
    # every evidence cell names the matrix sha and is non-empty
    for m, r in rows.items():
        assert r["evidence"].strip()
        assert "sha256:" in r["evidence"]


def test_unparseable_and_mismatched_classifications_are_loud(tmp_path):
    with pytest.raises(DerivationError):
        parse_classification("maybe?", 3)
    with pytest.raises(DerivationError):
        parse_classification("mixed(COMPLETE_CAUSAL_CHAIN=5;PARTIAL=2)", 10)
    with pytest.raises(DerivationError):
        parse_classification("COMPLETE_CAUSAL_CHAIN(5/5)", 3)
    with pytest.raises(DerivationError):
        parse_classification("", 1)
    assert parse_classification("mixed(UNRESOLVED=2;PARTIAL=3)", 5)["UNRESOLVED"] == 2
    assert parse_classification("COMPLETE_CAUSAL_CHAIN", 2)["COMPLETE_CAUSAL_CHAIN"] == 2
    assert parse_classification("LIFECYCLE_ONLY(3/3)", 3)["LIFECYCLE_ONLY"] == 3


def test_set_is_restricted_to_workflow_flags(tmp_path):
    rc, out = run_main(tmp_path, all_model_rows([]),
                       extra={"--set": ["RP01:PILOT_RUN=1", "RP01:IMPLEMENTED=1"]})
    assert rc == 0
    rp = rows_by_model(out)["RP01"]
    assert rp["PILOT_RUN"] == "1" and rp["IMPLEMENTED"] == "1"
    assert rp["PROPAGATION_VERIFIED"] == "0"  # still tool-derived, never hand-set

    rc2, _ = run_main(tmp_path, all_model_rows([]),
                      extra={"--set": ["LQ04:PROPAGATION_VERIFIED=1"]})
    assert rc2 == 2  # hand-set PASS rejected

    rc3, _ = run_main(tmp_path, all_model_rows([]),
                      extra={"--set": ["LQ04:evidence=pass"]})
    assert rc3 == 2

    rc4, _ = run_main(tmp_path, all_model_rows([]),
                      extra={"--set": ["LQ04:PILOT_RUN=maybe"]})
    assert rc4 == 2


def test_refuses_in_place_overwrite_and_unknown_matrix_model(tmp_path):
    rows = all_model_rows([]) + [matrix_row("ZZZ", 1, "PARTIAL", "MASKED(1)")]
    rc, out = run_main(tmp_path, rows)
    assert rc == 2  # matrix model absent from the template is a loud rejection

    paths, out = std_paths(tmp_path, all_model_rows([]))
    argv = []
    for k, v in paths.items():
        argv += [k, str(v)]
    argv[argv.index("--output") + 1] = str(paths["--template"])
    assert main(argv) == 2  # in-place overwrite refused


def test_parse_set_shapes():
    assert parse_set("RP01:PILOT_RUN=1") == ("RP01", "PILOT_RUN", "1")
    with pytest.raises(DerivationError):
        parse_set("RP01")
    with pytest.raises(DerivationError):
        parse_set(":PILOT_RUN=1")


def test_frozen_cross_check_helpers(tmp_path):
    matrix = tmp_path / "audit.csv"
    status = tmp_path / "status.csv"
    sidecar = tmp_path / "sidecar.json"
    write_frozen_audit(matrix)
    write_frozen_status(status)
    write_sidecar(sidecar)
    frozen = load_frozen_verdicts(sidecar, matrix, status)
    assert sorted(frozen) == sorted(FROZEN_FOUR)

    bad = tmp_path / "bad_sidecar.json"
    write_sidecar(bad, models=["A01"])
    with pytest.raises(DerivationError):
        load_frozen_verdicts(bad, matrix, status)


def test_load_closure_matrix_groups_and_rejects_blanks(tmp_path):
    p = tmp_path / "m.csv"
    write_matrix(p, all_model_rows([]))
    groups = load_closure_matrix(p)
    assert set(groups) == set(MODELS)
    assert groups["SQ01"][0]["_complete"] == 5
    assert groups["DA04"][0]["_complete"] == 2
    blank = tmp_path / "blank.csv"
    rows = all_model_rows([])
    rows[0]["FinalClassification"] = ""
    write_matrix(blank, rows)
    with pytest.raises(DerivationError):
        load_closure_matrix(blank)
    unknown = tmp_path / "unknown.csv"
    write_matrix(unknown, [matrix_row("RP01", 1, "HANG_COMPLETE", "HANG(1)")])
    with pytest.raises(DerivationError):
        load_closure_matrix(unknown)


def test_derive_rows_report_lines(tmp_path):
    matrix = tmp_path / "m.csv"
    template = tmp_path / "t.csv"
    audit = tmp_path / "a.csv"
    status = tmp_path / "f.csv"
    sidecar = tmp_path / "s.json"
    write_matrix(matrix, all_model_rows([]))
    write_template(template)
    write_frozen_audit(audit)
    write_frozen_status(status)
    write_sidecar(sidecar)
    groups = load_closure_matrix(matrix)
    with open(template) as fh:
        template_rows = list(csv.DictReader(fh))
    frozen = load_frozen_verdicts(sidecar, audit, status)
    rows, report = derive_rows(template_rows, groups, frozen, [], {},
                               "deadbeef" * 8)
    assert len(rows) == len(MODELS)
    assert any("VERIFIED by matrix" in line for line in report)
    assert any("VERIFIED by frozen prior audit" in line for line in report)
    assert any("NOT verified" in line for line in report)
    # workflow flags carried unchanged from the template
    for old, new in zip(template_rows, rows):
        for col in ("unit", "stage", "DESIGNED", "SOURCE_AUDITED",
                    "IMPLEMENTED", "COMPILED", "UNIT_TESTED", "PILOT_RUN"):
            assert new[col] == old[col]
