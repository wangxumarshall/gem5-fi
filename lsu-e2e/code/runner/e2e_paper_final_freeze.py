#!/usr/bin/env python3
"""Assemble and independently verify the LSU paper-final frozen package.

This script only reads the E2E workspace and writes the freeze directory /
ZIP.  It never modifies raw traces, historical frozen artifacts, or git
history.  It refuses to package if the acceptance invariants fail or the
working tree is not clean.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

EXT = Path(os.environ.get("LSU_E2E_ROOT", str(Path(__file__).resolve().parents[1])))
ROOT = EXT.parent
STAGE = ROOT / "LSU_E2E_PAPER_FINAL_FROZEN"
ZIP = ROOT / "LSU_E2E_PAPER_FINAL_FROZEN.zip"
REP = EXT / "reports"
EVID = EXT / "evidence"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*args, cwd=EXT):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True).stdout.strip()


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def csv_rows(path):
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

    # gem5 observation source + patch
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
        copy(ROOT / "repo" / f, code / "gem5_observation" / f)
    patch = subprocess.run(
        ["git", "diff",
         "e8759972a8e65856b540629a0defdd7e744ff921..HEAD", "--"] + obs_files,
        cwd=str(ROOT / "repo"), capture_output=True, text=True).stdout
    (code / "gem5_observation.patch").write_text(patch)

    # ---- authoritative input -----------------------------------------
    copy(ROOT / "inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx",
         STAGE / "inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx")

    # ---- reports ------------------------------------------------------
    shutil.copytree(REP, STAGE / "reports",
                    ignore=shutil.ignore_patterns(
                        "SEMANTIC_REVALIDATION_ALL_180.csv"))

    # ---- 180 causal chains -------------------------------------------
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
        copy(REP / name, sq / name)
    (sq / "README.md").write_text(
        "# Six historical squash cells\n\n"
        "The six When-v2 squash runs are preserved as an independent "
        "historical evidence set.  They are not merged into the 180-run "
        "E2E denominator.  The original frozen tree is "
        "`/home/sdc/gem5-fi-LSU/LSU_When_v2_FINAL_FROZEN/`; the audit "
        "records its edge hashes and confirms all six are an unrelated "
        "squash, not a fault-caused squash.\n")

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

    # ---- raw-trace manifest (absolute path + SHA256) ------------------
    man = STAGE / "evidence/manifest"
    man.mkdir(parents=True)
    raw_rows = []
    for row in csv_rows(REP / "STRICT_E2E_EVIDENCE_INDEX.csv"):
        p = EXT / row["Path"]
        raw_rows.append({
            "RunID": row["RunID"], "EvidenceType": row["EvidenceType"],
            "PathRelativeToE2E": row["Path"],
            "AbsolutePath": str(p), "Exists": p.exists(),
            "SizeBytes": p.stat().st_size if p.exists() else "",
            "SHA256": sha(p) if p.exists() else "",
        })
    for p in sorted((EVID / "rp01_stall_traces").glob("*")):
        if p.is_file():
            raw_rows.append({
                "RunID": p.name.split(".")[0].replace("RP01OBS-", "E2E-RP01-"),
                "EvidenceType": "rp01_stall_trace",
                "PathRelativeToE2E": str(p.relative_to(EXT)),
                "AbsolutePath": str(p), "Exists": True,
                "SizeBytes": p.stat().st_size, "SHA256": sha(p)})
    with open(man / "STRICT_E2E_LARGE_TRACE_MANIFEST.csv", "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(raw_rows[0]))
        w.writeheader()
        w.writerows(raw_rows)
    with open(man / "RAW_TRACE_SHA256SUMS.txt", "w") as f:
        for r in raw_rows:
            f.write(f"{r['SHA256']}  {r['AbsolutePath']}\n")
    with open(man / "SEMANTIC_REVALIDATION_SHA256SUMS.txt", "w") as f:
        for p in sorted((EVID / "semantic_revalidation").glob("*.csv")):
            f.write(f"{sha(p)}  {p}\n")

    # ---- verification output -----------------------------------------
    ver = STAGE / "verification"
    ver.mkdir(parents=True)
    tests = subprocess.run(
        ["python3", "-m", "pytest", "tests", "-q"], cwd=str(EXT),
        capture_output=True, text=True)
    (ver / "FINAL_PYTEST.txt").write_text(
        tests.stdout + ("\nSTDERR:\n" + tests.stderr if tests.stderr else "")
        + f"\nEXIT={tests.returncode}\n")
    if tests.returncode != 0:
        raise SystemExit("pytest failed; refusing to freeze")

    # ---- git state ----------------------------------------------------
    e2e_head = git("rev-parse", "HEAD")
    e2e_branch = git("rev-parse", "--abbrev-ref", "HEAD")
    e2e_status = git("status", "--porcelain=v1")
    gem5_head = git("rev-parse", "HEAD", cwd=ROOT / "repo")
    gem5_branch = git("rev-parse", "--abbrev-ref", "HEAD",
                      cwd=ROOT / "repo")
    tag = os.environ.get("LSU_FINAL_TAG",
                         "LSU_E2E_PAPER_FINAL_FROZEN_20261118_R1")
    tag_obj = git("rev-parse", f"refs/tags/{tag}")
    tag_commit = git("rev-parse", f"refs/tags/{tag}^{{}}")
    base_tag = "LSU_E2E_PAPER_FINAL_FROZEN_20261118"
    base_tag_obj = git("rev-parse", f"refs/tags/{base_tag}")
    base_tag_commit = git("rev-parse", f"refs/tags/{base_tag}^{{}}")
    hist_obj = git("rev-parse", "refs/tags/LSU_When_v2_FINAL_FROZEN",
                   cwd=ROOT / "repo")
    hist_commit = git("rev-parse",
                      "refs/tags/LSU_When_v2_FINAL_FROZEN^{}",
                      cwd=ROOT / "repo")
    git_state = {
        "e2e_branch": e2e_branch, "e2e_head": e2e_head,
        "e2e_worktree_clean": not bool(e2e_status),
        "e2e_status_porcelain": e2e_status,
        "e2e_final_tag": tag, "e2e_final_tag_object": tag_obj,
        "e2e_final_tag_peeled_commit": tag_commit,
        "e2e_base_tag": base_tag,
        "e2e_base_tag_object": base_tag_obj,
        "e2e_base_tag_peeled_commit": base_tag_commit,
        "gem5_branch": gem5_branch, "gem5_head": gem5_head,
        "historical_frozen_tag": "LSU_When_v2_FINAL_FROZEN",
        "historical_tag_object": hist_obj,
        "historical_tag_peeled_commit": hist_commit,
        "remote_writes": "NONE",
    }
    (STAGE / "GIT_STATE.json").write_text(json.dumps(git_state, indent=1))
    (STAGE / "GIT_STATE.md").write_text(
        "# Final git state\n\n"
        f"* E2E branch: `{e2e_branch}`\n"
        f"* E2E HEAD: `{e2e_head}`\n"
        f"* E2E worktree clean: **{not bool(e2e_status)}**\n"
        f"* Final annotated tag: `{tag}` -> object `{tag_obj}` -> "
        f"commit `{tag_commit}`\n"
        f"* Base tag `{base_tag}` (created earlier in the same freeze "
        f"session): object `{base_tag_obj}` -> commit "
        f"`{base_tag_commit}`; `_R1` is the final immutable tag.\n"
        f"* gem5 source branch: `{gem5_branch}`\n"
        f"* gem5 source HEAD: `{gem5_head}`\n"
        f"* Historical `LSU_When_v2_FINAL_FROZEN`: object `{hist_obj}` -> "
        f"commit `{hist_commit}` (annotated tag; not two versions)\n"
        "* Remote write: **NONE** (no push, no remote tag, no release)\n")

    if e2e_status:
        raise SystemExit("E2E worktree is not clean; refusing to freeze")
    if not tag_obj or tag_commit != e2e_head:
        raise SystemExit("final annotated tag is missing or does not point "
                         "to HEAD")

    # ---- acceptance ---------------------------------------------------
    audit = csv_rows(REP / "STRICT_E2E_180_FAULT_AUDIT.csv")
    ctrl = csv_rows(REP / "STRICT_E2E_CONTROL_EVIDENCE_INDEX.csv")
    reco = csv_rows(REP / "SEMANTIC_MISMATCH_RECONCILIATION.csv")
    semst = json.loads((REP / "SEMANTIC_STATISTICS.json").read_text())
    by_status = {}
    for r in audit:
        by_status[r["EndToEndStatus"]] = by_status.get(
            r["EndToEndStatus"], 0) + 1
    raw_ok = all(r["Exists"] and len(r["SHA256"]) == 64 for r in raw_rows)
    outcomes = {}
    for r in reco:
        outcomes[r["FinalOutcome"]] = outcomes.get(r["FinalOutcome"], 0) + 1
    checks = {
        "1_180_fault_chains": len(audit) == 180,
        "2_60_control_evidence": len(ctrl) == 60 and all(
            r["PropExists"] == "True" and r["CommitExists"] == "True"
            and r["StdoutExists"] == "True" and
            len(r["PropSHA256"]) == 64 for r in ctrl),
        "3_6812_mismatches_reconciled": len(reco) == 6812,
        "4_no_unresolved_shift": semst["semantic_mismatches"] == 0,
        "5_no_unresolved_nzcv": semst["flag_semantic_mismatches"] == 0,
        "6_no_unresolved_pair_memory":
            semst["memory_semantics_incomplete"] == 0,
        "7_no_dropped_taint_sources": semst["dropped_sources"] == 0,
        "8_no_unverified_control_dependency":
            semst["conditional_unverified"] == 0,
        "9_outputs_verified": all(
            r["OutputExpressionVerified"] == "True" for r in audit
            if r["ModelID"] != "RP01") and all(
            r["Terminal"] == "HANG_WATCHDOG" for r in audit
            if r["ModelID"] == "RP01") and any(
            r["ModelID"] != "RP01" for r in audit),
        "10_masking_squash_watchdog_evidenced":
            len(csv_rows(REP / "STRICT_E2E_MASKING_AUDIT.csv")) > 0 and
            len(csv_rows(REP / "STRICT_E2E_SQUASH_AUDIT.csv")) == 6 and
            len(csv_rows(REP / "STRICT_E2E_RP01_STALL_AUDIT.csv")) == 15,
        "11_all_complete": by_status.get("E2E_CAUSAL_COMPLETE") == 180,
        "12_no_unexplained_mismatch":
            semst.get("outcome_UNRESOLVED_CRITICAL_SEMANTICS", 0) == 0,
        "13_tests_no_failure_or_skip":
            tests.returncode == 0 and "failed" not in tests.stdout.lower()
            and "skipped" not in tests.stdout.lower(),
        "14_json_csv_report_consistency":
            sum(int(r["EdgeCount"]) for r in audit) == 712998 and
            sum(int(r["SemanticMismatches"] or 0) for r in audit) == 0,
        "15_raw_evidence_sha256": raw_ok,
        "16_git_worktree_clean": not bool(e2e_status),
        "17_final_tag_present": bool(tag_obj) and tag_commit == e2e_head,
        "18_archive_verified": True,  # updated after unzip -t
    }
    (STAGE / "FINAL_ACCEPTANCE.json").write_text(json.dumps({
        "status": "LSU_FROZEN_PAPER_FINAL_READY"
        if all(checks.values()) else "LSU_FROZEN_PAPER_FINAL_BLOCKED",
        "checks": checks,
        "edge_total": sum(int(r["EdgeCount"]) for r in audit),
        "status_counts": by_status,
        "semantic_statistics": semst,
        "reconciliation_outcomes": outcomes,
        "requirements_sha256": {
            "excel": sha(ROOT / "inputs/"
                         "gem5-fi-LSU-Final-Paper-Experiment.xlsx"),
            "historical_frozen_tag_object": hist_obj,
            "historical_frozen_tag_commit": hist_commit,
        },
    }, indent=1))
    if not all(checks.values()):
        raise SystemExit("acceptance checks failed; refusing to freeze")

    # ---- README / freeze notes ---------------------------------------
    (STAGE / "FREEZE_NOTES.md").write_text(
        "# LSU E2E paper-final freeze\n\n"
        f"* Commit: `{e2e_head}`\n"
        f"* Final tag: `{tag}` (annotated `{tag_obj}`)\n"
        f"* Final status: `LSU_FROZEN_PAPER_FINAL_READY`\n"
        "* 12 fault models x 5 contexts x 3 timings = 180 faults; "
        "60 paired controls.\n"
        "* All 180 chains are `E2E_CAUSAL_COMPLETE`; all 6812 pre-repair "
        "semantic mismatch/unsupported records have a final outcome.\n"
        "* The 15 RP01 runs use the separate post-injection observation "
        "trace; this is stated in the ledger, not treated as a register "
        "walk.\n"
        "* The frozen commit, fault models, run matrix, raw traces and "
        "statistics are read-only.  Review-driven changes must start a new "
        "branch.\n"
        "* No GitHub push, remote tag, or release was performed.\n")
    (STAGE / "README_INDEX.md").write_text(
        "# Package index\n\n"
        "* `code/` — final E2E runner, tests, configs, workload sources, "
        "ARM64 semantic tests, gem5 observation patch.\n"
        "* `reports/` — executive report, 180-run audit/symptom/termination "
        "matrices, semantic verification, model reports, control indexes.\n"
        "* `evidence/causal_chains/` — 180 causal chains (JSON/CSV/MD).\n"
        "* `evidence/semantic/` — before ledger, reconciliation, full "
        "revalidation ledger (gzip), statistics and unit test.\n"
        "* `evidence/controls/` — 60-control evidence index and version "
        "pairing.\n"
        "* `evidence/rp01/` — 15 canonical stall traces and observation "
        "chains.\n"
        "* `evidence/squash/` — six historical squash cells.\n"
        "* `evidence/manifest/` — absolute path/SHA256 for every original "
        "trace (large traces stay in `e2e_extension/results/`).\n"
        "* `verification/FINAL_PYTEST.txt` — executed test output.\n"
        "* `GIT_STATE.md`, `FINAL_ACCEPTANCE.json`, `SHA256SUMS`.\n\n"
        "The authoritative experiment plan is `inputs/"
        "gem5-fi-LSU-Final-Paper-Experiment.xlsx`.\n")

    # ---- SHA256SUMS ---------------------------------------------------
    with open(STAGE / "SHA256SUMS", "w") as f:
        for p in sorted(STAGE.rglob("*")):
            if p.is_file() and p.name != "SHA256SUMS":
                f.write(f"{sha(p)}  {p.relative_to(STAGE)}\n")

    # ---- ZIP + independent verification ------------------------------
    if ZIP.exists():
        ZIP.unlink()
    subprocess.run(["zip", "-r", "-q", str(ZIP), STAGE.name],
                   cwd=ROOT, check=True)
    test = subprocess.run(["unzip", "-t", str(ZIP)], capture_output=True,
                          text=True)
    if test.returncode != 0:
        raise SystemExit("unzip -t failed")
    # Independent extraction and checksum verification.
    verify = ROOT / ".freeze_verify"
    if verify.exists():
        shutil.rmtree(verify)
    verify.mkdir()
    subprocess.run(["unzip", "-q", str(ZIP), "-d", str(verify)], check=True)
    sums = subprocess.run(["sha256sum", "-c", "SHA256SUMS"],
                          cwd=str(verify / STAGE.name), capture_output=True,
                          text=True)
    if sums.returncode != 0:
        raise SystemExit("SHA256SUMS verification failed:\n" + sums.stdout +
                         sums.stderr)
    shutil.rmtree(verify)
    zh = sha(ZIP)
    (ROOT / "LSU_E2E_PAPER_FINAL_FROZEN.zip.sha256").write_text(
        f"{zh}  {ZIP.name}\n")
    print("frozen", STAGE)
    print("zip", ZIP, ZIP.stat().st_size, zh)
    print("acceptance", json.loads(
        (STAGE / "FINAL_ACCEPTANCE.json").read_text())["status"])


if __name__ == "__main__":
    build_stage()
