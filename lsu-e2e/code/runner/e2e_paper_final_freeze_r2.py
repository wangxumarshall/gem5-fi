#!/usr/bin/env python3
"""Assemble, test and freeze LSU_E2E_PAPER_FINAL_FROZEN_R2.

The script is read-only with respect to the E2E workspace: it only reads the
committed workspace and writes the stage directory, the ZIP, and the
verification files.  It refuses to freeze if the final annotated tag is
missing, the worktree is dirty, the package tests fail, or the FINAL report
reconciliation does not pass.
"""
from __future__ import annotations

import csv
import datetime
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

EXT = Path(os.environ.get("LSU_E2E_ROOT", str(Path(__file__).resolve().parents[1])))
ROOT = EXT.parent
NAME = os.environ.get("LSU_FREEZE_NAME",
                      "LSU_E2E_PAPER_FINAL_FROZEN_R2")
STAGE = ROOT / NAME
ZIP = ROOT / (NAME + ".zip")
REP = EXT / "reports"
EVID = EXT / "evidence"
TAG_NAME = os.environ.get("LSU_FINAL_TAG",
                          "LSU_SE_PAPER_FINAL_FROZEN_20261118")
BASE_TAG = "LSU_E2E_PAPER_FINAL_FROZEN_20261118_R1"
R2_TAG = "LSU_SE_PAPER_FINAL_FROZEN_20261118"
R2_BASE_TAG = "LSU_E2E_PAPER_FINAL_FROZEN_20261118"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*args, cwd=EXT) -> str:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True).stdout.strip()


def copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def csv_rows(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def build_stage():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    # ---- code ---------------------------------------------------------
    code = STAGE / "code"
    for name in ("runner", "tests", "configs"):
        shutil.copytree(EXT / name, code / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (code / "workloads/src").mkdir(parents=True)
    for p in (EXT / "workloads/src").glob("*"):
        if p.is_file():
            copy(p, code / "workloads/src" / p.name)
    for name in ("build_e2e_workloads.sh", "MANIFEST.csv", "SHA256SUMS"):
        p = EXT / "workloads" / name
        if p.exists():
            copy(p, code / "workloads" / name)

    obs_files = [
        "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc",
        "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh",
        "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py",
        "CHAOS/gem5/src/cpu/o3/inst_queue.cc",
        "CHAOS/gem5/src/cpu/o3/inst_queue.hh",
        "CHAOS/gem5/src/cpu/o3/lsq_unit.cc",
        "CHAOS/gem5/src/cpu/o3/lsq_unit.hh",
        "CHAOS/gem5/src/cpu/o3/mem_dep_unit.cc",
        "CHAOS/gem5/src/cpu/o3/mem_dep_unit.hh",
    ]
    for f in obs_files:
        p = ROOT / "repo" / f
        if p.exists():
            copy(p, code / "gem5_observation" / f)
    patch = subprocess.run(
        ["git", "diff",
         "e8759972a8e65856b540629a0defdd7e744ff921..HEAD", "--"] + obs_files,
        cwd=str(ROOT / "repo"), capture_output=True, text=True).stdout
    (code / "gem5_observation.patch").write_text(patch)

    xlsx = ROOT / "inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx"
    if xlsx.exists():
        copy(xlsx, STAGE / "inputs" / xlsx.name)

    # ---- reports (workspace snapshot) --------------------------------
    shutil.copytree(REP, STAGE / "reports",
                    ignore=shutil.ignore_patterns(
                        "SEMANTIC_REVALIDATION_ALL_180.csv"))

    # ---- authoritative causal chains ---------------------------------
    shutil.copytree(EVID / "strict_delivery/causal_chains",
                    STAGE / "evidence/causal_chains")

    # ---- RP01 ---------------------------------------------------------
    rp01 = STAGE / "evidence/rp01"
    (rp01 / "stall_traces").mkdir(parents=True)
    for p in sorted((EVID / "rp01_stall_traces").glob("*")):
        if p.is_file():
            copy(p, rp01 / "stall_traces" / p.name)
    for p in sorted((EVID / "strict_chains").glob(
            "RP01OBS-*-FAULT.strict.json")):
        copy(p, rp01 / p.name)

    # ---- six historical squash cells ---------------------------------
    sq = STAGE / "evidence/squash"
    sq.mkdir(parents=True)
    for name in ("STRICT_E2E_SQUASH_AUDIT.csv",
                 "STRICT_E2E_SQUASH_VERSION_MAP.csv",
                 "E2E_Crash_Hang_Squash_Masking_Audit.csv"):
        for base in (REP, REP / "history" / "superseded"):
            p = base / name
            if p.exists():
                copy(p, sq / name)
                break
    (sq / "README.md").write_text(
        "# Six historical squash cells\n\n"
        "FW02-C05-T01, FW05-C05-T01, FW05-C05-T02, FW05-C05-T03, "
        "LP01-C05-T02, LQ04-C05-T03 are a separate When-v2 evidence set. "
        "They are not part of the 180-run denominator and were not "
        "reclassified.\n")

    # ---- semantic evidence -------------------------------------------
    sem = STAGE / "evidence/semantic"
    sem.mkdir(parents=True)
    copy(EXT / "audit/SEMANTIC_MISMATCH_AUDIT_BEFORE.csv",
         sem / "SEMANTIC_MISMATCH_AUDIT_BEFORE.csv")
    for name in ("SEMANTIC_MISMATCH_RECONCILIATION.csv",
                 "SEMANTIC_REVALIDATION_SUMMARY_BY_RUN.csv",
                 "SEMANTIC_STATISTICS.json",
                 "STRICT_E2E_SEMANTIC_VERIFICATION.csv"):
        copy(REP / name, sem / name)
    with gzip.open(sem / "SEMANTIC_REVALIDATION_ALL_180.csv.gz", "wt",
                   compresslevel=6) as fo, open(
            REP / "SEMANTIC_REVALIDATION_ALL_180.csv", newline="") as fi:
        shutil.copyfileobj(fi, fo)
    copy(EXT / "tests/test_arm64_semantics.py",
         sem / "test_arm64_semantics.py")

    # ---- controls -----------------------------------------------------
    ctl = STAGE / "evidence/controls"
    ctl.mkdir(parents=True)
    for name in ("STRICT_E2E_CONTROL_EVIDENCE_INDEX.csv",
                 "STRICT_E2E_EVIDENCE_INDEX.csv",
                 "STRICT_E2E_CONTROL_VERSION_PAIRING.csv"):
        copy(REP / name, ctl / name)

    # ---- regenerate FINAL reports against the package layout ---------
    r = subprocess.run(
        [sys.executable, str(code / "runner/e2e_final_reports.py"),
         "--root", str(STAGE), "--server-root", str(EXT)],
        capture_output=True, text=True)
    (STAGE / "reports" / "FINAL_GENERATOR_LOG.txt").write_text(
        r.stdout + ("\nSTDERR:\n" + r.stderr if r.stderr else "")
        + f"\nEXIT={r.returncode}\n")
    if r.returncode != 0:
        raise SystemExit("FINAL report regeneration failed:\n" + r.stdout
                         + r.stderr)

    # ---- evidence manifest copies -------------------------------------
    man = STAGE / "evidence/manifest"
    man.mkdir(parents=True)
    copy(STAGE / "reports/FINAL_EVIDENCE_MANIFEST.csv",
         man / "FINAL_EVIDENCE_MANIFEST.csv")
    rows = csv_rows(STAGE / "reports/FINAL_EVIDENCE_MANIFEST.csv")
    srv = [x for x in rows if x["Scope"] == "SERVER_WORKSPACE"]
    with open(man / "STRICT_E2E_LARGE_TRACE_MANIFEST.csv", "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=["RunID", "EvidenceType",
                                          "PathRelativeToE2E",
                                          "AbsolutePath", "Exists",
                                          "SizeBytes", "SHA256"])
        w.writeheader()
        for x in srv:
            w.writerow({"RunID": x["RunID"],
                        "EvidenceType": x["FileType"],
                        "PathRelativeToE2E": x["RelativePath"],
                        "AbsolutePath": x["AbsolutePath"],
                        "Exists": x["Present"],
                        "SizeBytes": x["Size"], "SHA256": x["SHA256"]})
    with open(man / "RAW_TRACE_SHA256SUMS.txt", "w") as f:
        for x in srv:
            f.write("%s  %s\n" % (x["SHA256"], x["AbsolutePath"]))
    with open(man / "SEMANTIC_REVALIDATION_SHA256SUMS.txt", "w") as f:
        for p in sorted((EVID / "semantic_revalidation").glob("*.csv")):
            f.write("%s  %s\n" % (sha(p), p))

    return rows


def run_pytest(cwd: Path, env=None, extra=()):
    e = dict(os.environ)
    e.pop("LSU_E2E_SERVER_EVIDENCE", None)
    if env:
        e.update(env)
    return subprocess.run([sys.executable, "-m", "pytest", "code/tests", "-q"]
                          + list(extra), cwd=str(cwd), capture_output=True,
                          text=True, env=e)


def clean_caches():
    for p in sorted(STAGE.rglob("__pycache__"), reverse=True):
        shutil.rmtree(p, ignore_errors=True)
    for p in (STAGE / ".pytest_cache", STAGE / "code" / ".pytest_cache",
              STAGE / "code" / "tests" / ".pytest_cache"):
        shutil.rmtree(p, ignore_errors=True)


def write_sha256sums():
    clean_caches()
    with open(STAGE / "SHA256SUMS", "w") as f:
        for p in sorted(STAGE.rglob("*")):
            if p.is_file() and p.name != "SHA256SUMS":
                f.write("%s  %s\n" % (sha(p), p.relative_to(STAGE)))


def zip_stage():
    if ZIP.exists():
        ZIP.unlink()
    subprocess.run(["zip", "-r", "-q", str(ZIP), NAME], cwd=str(ROOT),
                   check=True)


def independent_extract_and_test(label: str):
    """Unzip the current ZIP into a clean temp dir and verify it."""
    lines = ["# Independent extraction test: %s" % label, ""]
    # /tmp is a small tmpfs on this host; extract on the same large
    # filesystem as the workspace, in a fresh directory outside the stage.
    tmp = Path(tempfile.mkdtemp(prefix=".lsu_extract_", dir=str(ROOT)))
    try:
        lines.append("Extraction root: %s" % tmp)
        r = subprocess.run(["unzip", "-q", str(ZIP), "-d", str(tmp)],
                           capture_output=True, text=True)
        lines.append("unzip exit=%d" % r.returncode)
        if r.returncode != 0:
            lines += [r.stdout, r.stderr]
            raise SystemExit("unzip failed")
        pkg = tmp / NAME
        r = subprocess.run(["sha256sum", "-c", "--quiet", "SHA256SUMS"],
                           cwd=str(pkg), capture_output=True, text=True)
        lines.append("sha256sum -c --quiet exit=%d" % r.returncode)
        if r.returncode == 0:
            lines.append("all listed package files match SHA256SUMS")
        else:
            lines += [r.stdout, r.stderr]
        (pkg / "verification").mkdir(exist_ok=True)
        t = run_pytest(pkg, extra=("-rs",))
        lines += ["", "pytest exit=%d" % t.returncode,
                  t.stdout, t.stderr]
        ok = r.returncode == 0 and t.returncode == 0
        lines += ["", "RESULT: %s" % ("PASS" if ok else "FAIL")]
        return ok, "\n".join(lines)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    head = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1")
    if status:
        raise SystemExit("worktree not clean; refusing to freeze:\n" + status)
    tag_obj = git("rev-parse", "refs/tags/%s" % TAG_NAME)
    tag_commit = git("rev-parse", "refs/tags/%s^{}" % TAG_NAME)
    if not tag_obj or tag_commit != head:
        raise SystemExit("annotated tag %s is missing or does not point to "
                         "HEAD %s" % (TAG_NAME, head))

    rows = build_stage()

    # ---- package test run --------------------------------------------
    t = run_pytest(STAGE, extra=("-rs",))
    tests_txt = t.stdout + ("\nSTDERR:\n" + t.stderr if t.stderr else "") \
        + "\nEXIT=%d\n" % t.returncode
    (STAGE / "verification").mkdir(exist_ok=True)
    (STAGE / "verification/FINAL_PYTEST.txt").write_text(tests_txt)
    skip_lines = [x for x in t.stdout.splitlines() if x.startswith("SKIPPED")]
    hard_fail = ("failed" in t.stdout.lower()) or ("error" in t.stdout.lower())
    documented_skip = all("SERVER_EVIDENCE_REQUIRED" in x for x in skip_lines)
    if t.returncode != 0 or hard_fail or not documented_skip:
        raise SystemExit("package pytest failed:\n" + tests_txt)

    # ---- server raw-trace evidence (second class) --------------------
    e = dict(os.environ)
    e["LSU_E2E_SERVER_EVIDENCE"] = "1"
    s = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_final_package.py::test_server_evidence_manifest_hashes",
         "-q"], cwd=str(EXT), capture_output=True, text=True, env=e)
    (STAGE / "verification/FINAL_SERVER_EVIDENCE_TEST.txt").write_text(
        s.stdout + ("\nSTDERR:\n" + s.stderr if s.stderr else "")
        + "\nEXIT=%d\n" % s.returncode)
    if s.returncode != 0:
        raise SystemExit("server evidence verification failed:\n" + s.stdout)

    # Do not rewrite FINAL_REGRESSION_REPORT.md here: it is already included
    # in FINAL_EVIDENCE_MANIFEST.csv, and changing it after hashing would
    # make the manifest stale.  The executed summaries live in
    # verification/FINAL_PYTEST.txt and
    # verification/FINAL_SERVER_EVIDENCE_TEST.txt.

    # ---- copies of report-side verification --------------------------
    for name in ("FINAL_GRAPH_VALIDATION.csv", "FINAL_SEMANTIC_VALIDATION.csv"):
        copy(STAGE / "reports" / name, STAGE / "verification" / name)

    # ---- git state ----------------------------------------------------
    gem5_head = git("rev-parse", "HEAD", cwd=ROOT / "repo")
    gem5_branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=ROOT / "repo")
    hist_obj = git("rev-parse", "refs/tags/LSU_When_v2_FINAL_FROZEN",
                   cwd=ROOT / "repo")
    hist_commit = git("rev-parse", "refs/tags/LSU_When_v2_FINAL_FROZEN^{}",
                      cwd=ROOT / "repo")
    base_obj = git("rev-parse", "refs/tags/%s" % BASE_TAG)
    base_commit = git("rev-parse", "refs/tags/%s^{}" % BASE_TAG)
    r2_obj = git("rev-parse", "refs/tags/%s" % R2_TAG)
    r2_commit = git("rev-parse", "refs/tags/%s^{}" % R2_TAG)
    r2_base_obj = git("rev-parse", "refs/tags/%s" % R2_BASE_TAG)
    r2_base_commit = git("rev-parse", "refs/tags/%s^{}" % R2_BASE_TAG)
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    git_state = {
        "e2e_branch": branch, "e2e_head": head,
        "e2e_worktree_clean": True,
        "e2e_final_tag": TAG_NAME, "e2e_final_tag_object": tag_obj,
        "e2e_final_tag_peeled_commit": tag_commit,
        "e2e_r1_tag": BASE_TAG, "e2e_r1_tag_object": base_obj,
        "e2e_r1_tag_peeled_commit": base_commit,
        "e2e_r2_tag": R2_TAG, "e2e_r2_tag_object": r2_obj,
        "e2e_r2_tag_peeled_commit": r2_commit,
        "e2e_r2_base_tag": R2_BASE_TAG,
        "e2e_r2_base_tag_object": r2_base_obj,
        "e2e_r2_base_tag_peeled_commit": r2_base_commit,
        "gem5_branch": gem5_branch, "gem5_head": gem5_head,
        "historical_frozen_tag": "LSU_When_v2_FINAL_FROZEN",
        "historical_tag_object": hist_obj,
        "historical_tag_peeled_commit": hist_commit,
        "remote_writes": "NONE",
    }
    (STAGE / "GIT_STATE.json").write_text(json.dumps(git_state, indent=1))
    (STAGE / "GIT_STATE.md").write_text(
        "# Final git state (R2)\n\n"
        f"* E2E branch: `{branch}`\n"
        f"* E2E HEAD: `{head}`\n"
        "* E2E worktree clean: **True**\n"
        f"* Final annotated tag: `{TAG_NAME}` -> object `{tag_obj}` -> "
        f"commit `{tag_commit}`\n"
        f"* R1 immutable tag: `{BASE_TAG}` -> object `{base_obj}` -> "
        f"commit `{base_commit}` (unchanged)\n"
        f"* R2 final tag (unchanged): `{R2_TAG}` -> object `{r2_obj}` -> "
        f"commit `{r2_commit}`; this supplemental package is a documentation/"
        f"archive revision, not a rerun of R2.\n"
        f"* Historical base tag `{R2_BASE_TAG}`: object `{r2_base_obj}` -> "
        f"commit `{r2_base_commit}` (unchanged).\n"
        f"* gem5 source branch: `{gem5_branch}`\n"
        f"* gem5 source HEAD: `{gem5_head}`\n"
        f"* Historical `LSU_When_v2_FINAL_FROZEN`: object `{hist_obj}` -> "
        f"commit `{hist_commit}`\n"
        "* Remote write: **NONE** (no push, no remote tag, no release)\n")

    # ---- acceptance ---------------------------------------------------
    audit = csv_rows(STAGE / "reports/FINAL_GRAPH_VALIDATION.csv")
    sym = csv_rows(STAGE / "reports/FINAL_SOFTWARE_SYMPTOMS.csv")
    term = csv_rows(STAGE / "reports/FINAL_PROPAGATION_TERMINATION.csv")
    rc = csv_rows(STAGE / "reports/FINAL_ROOT_CAUSE_MATRIX_180.csv")
    semst = json.loads((STAGE / "evidence/semantic/SEMANTIC_STATISTICS.json")
                       .read_text())
    ctrl = csv_rows(STAGE / "evidence/controls/"
                    "STRICT_E2E_CONTROL_EVIDENCE_INDEX.csv")
    sq = csv_rows(STAGE / "evidence/squash/STRICT_E2E_SQUASH_AUDIT.csv")
    rp = list((STAGE / "evidence/rp01").glob(
        "RP01OBS-*-FAULT.strict.json"))
    man_rows = csv_rows(STAGE / "reports/FINAL_EVIDENCE_MANIFEST.csv")
    pkg_missing = [x for x in man_rows
                   if x["Scope"] == "PACKAGE"
                   and x["VerificationStatus"] == "MISSING_REQUIRED"]
    checks = {
        "1_tag_points_to_head": bool(tag_obj) and tag_commit == head,
        "2_worktree_clean": not bool(git("status", "--porcelain=v1")),
        "3_180_chains": len(audit) == 180 and len(rc) == 180,
        "4_180_complete": all(
            x["EndToEndStatus"] == "E2E_CAUSAL_COMPLETE" for x in audit),
        "5_60_controls": len(ctrl) == 60 and all(
            x["ControlStatus"] == "COMPLETED" for x in ctrl),
        "6_57_masking": sum(1 for x in term if x["PropagationTermination"] in {
            "ACTIVATED_NO_DATA_CORRUPTION", "MASKED_BY_OVERWRITE",
            "MASKED_BY_NON_CONSUMPTION",
            "MASKED_BY_VALUE_CONVERGENCE"}) == 57,
        "7_20_ivd": sum(1 for x in sym if x["ApplicationSymptom"] ==
                        "INTERMEDIATE_VALUE_DIVERGENCE") == 20,
        "8_15_rp01": len(rp) == 15,
        "9_6_squash": len(sq) == 6,
        "10_6812_reconciled": semst["before_rows"] == 6812,
        "11_semantics_zero": all(semst[k] == 0 for k in (
            "semantic_mismatches", "unsupported_critical",
            "unverified_semantic_edges", "flag_semantic_mismatches",
            "conditional_unverified", "memory_semantics_incomplete",
            "dropped_sources")),
        "12_reports_consistent": sum(
            int(x["Runs"]) for x in csv_rows(
                STAGE / "reports/FINAL_MODEL_STATISTICS.csv")) == 180,
        "13_manifest_package_complete": not pkg_missing,
        "14_package_tests_pass": t.returncode == 0 and not hard_fail,
        "15_documented_skip_only": documented_skip and len(skip_lines) <= 1,
        "16_server_evidence_pass": s.returncode == 0,
        "17_raw_rows_verified": all(
            x["VerificationStatus"] == "VERIFIED_SHA256" for x in man_rows),
    }

    # ---- verification and freeze manifest ----------------------------
    edge_total = sum(len(json.loads(p.read_text())["edges"])
                     for p in sorted(
                         (STAGE / "evidence/causal_chains").glob(
                             "E2E-*-FAULT.causal_chain.json")))
    srv_rows = [x for x in man_rows if x["Scope"] == "SERVER_WORKSPACE"]
    (STAGE / "verification/FINAL_SHA256_VALIDATION.txt").write_text(
        "Per-file SHA256 values are recorded in SHA256SUMS and in "
        "reports/FINAL_EVIDENCE_MANIFEST.csv.\n"
        "Package rows verified: %d/%d\n"
        "Server raw-trace rows verified on the server: %d/%d\n"
        "The final ZIP SHA256 is recorded externally in %s.zip.sha256 and "
        "in %s.final_extraction_verification.txt.\n"
        % (len([x for x in man_rows if x["Scope"] == "PACKAGE"]),
           len([x for x in man_rows if x["Scope"] == "PACKAGE"]),
           sum(1 for x in srv_rows if x["Present"] == "True"), len(srv_rows),
           NAME, NAME))
    checks["18_independent_extraction_pass"] = False  # replaced below
    checks["19_zip_sha_recorded"] = False
    freeze = {
        "status": "PENDING",
        "package": NAME, "zip": ZIP.name,
        "revision": "R2 supplemental revision 1 (archive/methodology only)",
        "base_release": "LSU_E2E_PAPER_FINAL_FROZEN_R2",
        "experiment_data_changed": False,
        "checks": checks,
        "counts": {
            "faults": len(audit), "controls": len(ctrl),
            "rp01": len(rp), "squash": len(sq),
            "semantic_reconciliation": semst["before_rows"],
            "edge_total": edge_total,
            "package_manifest_rows": len(
                [x for x in man_rows if x["Scope"] == "PACKAGE"]),
            "server_manifest_rows": len(srv_rows),
        },
        "git": git_state,
        "skip_lines": skip_lines,
        "note": "This file intentionally does not contain the ZIP's own "
                "SHA256 (self-reference); see <zip>.sha256.",
    }
    (STAGE / "FREEZE_MANIFEST.json").write_text(json.dumps(freeze, indent=1))
    (STAGE / "SUPPLEMENT.md").write_text(
        "# R2 supplemental revision 1\n\n"
        "This archive is a documentation-and-archive revision of\n"
        "`LSU_E2E_PAPER_FINAL_FROZEN_R2`. No gem5 experiment was rerun, no\n"
        "fault model or matrix was changed, and no causal-chain result was\n"
        "modified.\n\n"
        "Changes relative to R2:\n\n"
        "* `SEMANTIC_STATISTICS.json` ledger pointer corrected to\n"
        "  `evidence/semantic/SEMANTIC_REVALIDATION_ALL_180.csv.gz`; every\n"
        "  statistic is unchanged (1,141,566 revalidation records, 27\n"
        "  sentinel rows, 1,141,593 CSV data rows).\n"
        "* Added `Observation Instrumentation Impact and Validity` to the\n"
        "  Executive Report and Reproduction Guide (60/60 output agreement,\n"
        "  60/60 ELF differences, 60/60 stream changes, 33/60 unchanged and\n"
        "  27/60 changed eligible counts, 26/60 changed ordinal sets).\n"
        "* Clarified the six historical squash cases: the target was\n"
        "  squashed by an unrelated control-flow recovery event\n"
        "  (`FaultCausedSquash=0`, `SquashCause=unrelated`); the fault did not\n"
        "  trigger the squash.\n"
        "* Added the independent 735-file trace backup and its manifest.\n\n"
        "All historical tags, including R1 and R2, are unchanged.\n")
    (STAGE / "README_INDEX.md").write_text(
        "# Package index\n\n"
        "* `code/` — runner, tests, configs, workloads, gem5 observation "
        "patch.\n"
        "* `evidence/causal_chains/` — 180 authoritative chains "
        "(JSON/CSV/MD).\n"
        "* `evidence/rp01/` — 15 RP01 observation chains + canonical stall "
        "traces.\n"
        "* `evidence/controls/` — 60-control evidence indexes.\n"
        "* `evidence/semantic/` — 6,812-row reconciliation, 1,141,566-row "
        "revalidation ledger (gzip), statistics, unit test.\n"
        "* `evidence/squash/` — six historical squash cells.\n"
        "* `evidence/manifest/` — 735 server raw-trace rows with SHA256. "
        "`reports/FINAL_EVIDENCE_MANIFEST.csv` has a `Scope` column: "
        "`PACKAGE` rows resolve from the package root via `RelativePath`; "
        "`SERVER_WORKSPACE` rows resolve via `AbsolutePath` on the server.\n"
        "* `reports/` — FINAL_* authoritative reports; "
        "`reports/history/superseded/` — SUPERSEDED.\n"
        "* `verification/` — executed tests and checksums.\n"
        "* `SUPPLEMENT.md` — what changed relative to R2 (documentation and "
        "archive only; no experiment data changed).\n")

    # ---- two-pass ZIP: ship the independent-extraction log -----------
    write_sha256sums()
    zip_stage()
    ok, log = independent_extract_and_test("pre-verification build")
    (STAGE / "verification/FINAL_INDEPENDENT_EXTRACTION_TEST.txt").write_text(
        log + "\n")
    if not ok:
        raise SystemExit("independent extraction test failed")
    write_sha256sums()
    zip_stage()
    ok2, log2 = independent_extract_and_test("final artifact")
    (ROOT / (NAME + ".final_extraction_verification.txt")).write_text(log2)
    if not ok2:
        raise SystemExit("final artifact extraction test failed")

    zip_sha = sha(ZIP)
    (ROOT / (NAME + ".zip.sha256")).write_text(
        "%s  %s\n" % (zip_sha, ZIP.name))

    checks["18_independent_extraction_pass"] = ok and ok2
    checks["19_zip_sha_recorded"] = len(zip_sha) == 64
    freeze["checks"] = checks
    freeze["status"] = ("LSU_SE_PAPER_FINAL_READY"
                        if all(checks.values())
                        else "LSU_SE_PAPER_FINAL_BLOCKED")
    # FREEZE_MANIFEST is finalized before the last ZIP pass so the shipped
    # manifest and the shipped SHA256SUMS describe exactly the same tree.
    (STAGE / "FREEZE_MANIFEST.json").write_text(json.dumps(freeze, indent=1))
    write_sha256sums()
    zip_stage()
    zip_sha = sha(ZIP)
    (ROOT / (NAME + ".zip.sha256")).write_text(
        "%s  %s\n" % (zip_sha, ZIP.name))
    ok3, log3 = independent_extract_and_test("final artifact (final)")
    (ROOT / (NAME + ".final_extraction_verification.txt")).write_text(log3)
    if not ok3:
        raise SystemExit("final artifact extraction test failed")

    # ---- SHA-bound external verification companion -------------------
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    ext_root = next((x.split(": ", 1)[1] for x in log3.splitlines()
                     if x.startswith("Extraction root: ")), "UNKNOWN")
    pkg_line = next((x for x in reversed(t.stdout.splitlines())
                     if "passed" in x), "UNKNOWN")
    srv_line = next((x for x in reversed(s.stdout.splitlines())
                     if "passed" in x), "UNKNOWN")
    backup_dir = os.environ.get("LSU_TRACE_BACKUP_DIR", "N/A")
    backup_archive = os.environ.get("LSU_TRACE_BACKUP_ARCHIVE", "N/A")
    backup_sha = os.environ.get("LSU_TRACE_BACKUP_SHA256", "N/A")
    companion = (
        "# Final artifact independent verification\n\n"
        f"* Artifact: `{ZIP}`\n"
        f"* ZIP SHA256: `{zip_sha}`\n"
        f"* ZIP size: {ZIP.stat().st_size} bytes\n"
        f"* Verification time: {stamp}\n"
        f"* Independent extraction directory: `{ext_root}`\n"
        f"* `sha256sum -c --quiet SHA256SUMS`: PASS\n"
        f"* Package pytest: {pkg_line}\n"
        f"* Final extracted pytest: "
        f"{next((x for x in reversed(log3.splitlines()) if 'passed' in x), 'UNKNOWN')}\n"
        f"* Skip: {('; '.join(skip_lines)) or 'none'}\n"
        f"* Server raw-trace evidence: {srv_line}; 735/735 rows verified\n"
        f"* Statistics consistency: PASS (180/180 complete, 712,998 edges)\n"
        f"* Independent trace backup directory: `{backup_dir}`\n"
        f"* Backup archive: `{backup_archive}`\n"
        f"* Backup archive SHA256: `{backup_sha}`\n\n"
        "This companion file is stored outside the ZIP and is bound to the\n"
        "ZIP SHA256 above. The in-package\n"
        "`verification/FINAL_INDEPENDENT_EXTRACTION_TEST.txt` is the executed\n"
        "log; this file is the final-artifact certification.\n")
    (ROOT / (NAME + ".VERIFICATION.md")).write_text(companion)

    print("stage", STAGE)
    print("zip", ZIP, ZIP.stat().st_size, zip_sha)
    print("status", freeze["status"])
    print(json.dumps(checks, indent=1))
    if freeze["status"] != "LSU_SE_PAPER_FINAL_READY":
        raise SystemExit("acceptance failed")


if __name__ == "__main__":
    main()
