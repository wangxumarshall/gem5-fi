#!/usr/bin/env python3
"""Assemble MMU_Final_Formal_Readiness_Package.zip from REAL artefacts.

The builder never invents evidence:
  * the final binary SHA is read from phase3/final/FINAL_BINARY.sha256
    (written by Main); when that file is absent the package records
    `PENDING_MAIN_FREEZE` explicitly and never guesses a hash;
  * the M07 context text is only copied from a researcher-supplied
    `phase3/final/M07_CONTEXT_CHANGES.json`; no text is invented;
  * every readiness/status value comes from the preflight/evidence index.

Usage:
  python3 tools/make_final_formal_package.py --refresh
  python3 tools/make_final_formal_package.py            # use existing outputs

--refresh re-runs (in order):
  mmu_build_evidence_index.py  (when phase3/formal/final_runs.json exists)
  mmu_formal_preflight.py
  mmu_readiness_matrix.py
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH = os.path.join(ROOT, "phase3", "freeze", "authority")
FORMAL = os.path.join(ROOT, "phase3", "formal")
FREEZE = os.path.join(ROOT, "phase3", "freeze")
FINAL = os.path.join(ROOT, "phase3", "final")
STAGE_NAME = "MMU_Final_Formal_Readiness_Package"

SEED_LITERAL = "N/A_DETERMINISTIC"
SEED_POLICY = "DETERMINISTIC"
SEED_SOURCE = "RESEARCHER_APPROVED"
MODELS = ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08"]
CONTEXTS = ["R01", "R02", "R03", "R04", "R05"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read(path):
    try:
        with open(path, "r", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def _run(cmd):
    print("[package] $ " + " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def refresh():
    final_runs = os.path.join(FORMAL, "final_runs.json")
    manifest = final_runs if os.path.isfile(final_runs) else os.path.join(
        FORMAL, "pilot_runs.json")
    _run([sys.executable, "tools/mmu_build_evidence_index.py",
          "--manifest", manifest,
          "--out", os.path.join(FORMAL, "evidence_index.json")])
    _run([sys.executable, "tools/mmu_formal_preflight.py",
          "--outdir", FORMAL,
          "--summary-json", os.path.join(FORMAL, "preflight_summary.json")])
    _run([sys.executable, "tools/mmu_readiness_matrix.py"])
    if not os.path.isfile(os.path.join(FORMAL, "w10_pfn_map.json")):
        _run([sys.executable, "tools/mmu_collect_w10_pfn.py"])


def final_binary():
    path = os.path.join(FINAL, "FINAL_BINARY.sha256")
    if os.path.isfile(path):
        text = _read(path).strip().split()
        if text:
            return text[0], text[1] if len(text) > 1 else \
                "CHAOS/gem5/build/ARM/gem5.opt", "FROZEN_BY_MAIN"
    return ("PENDING_MAIN_FREEZE", "CHAOS/gem5/build/ARM/gem5.opt",
            "PENDING_MAIN_FREEZE")


def source_commit():
    path = os.path.join(FINAL, "FINAL_SOURCE_COMMIT")
    if os.path.isfile(path):
        text = _read(path).strip().split()
        if text:
            return text[0]
    return "PENDING_MAIN_FREEZE"


def preflight_rows():
    import csv
    path = os.path.join(FORMAL, "MMU_40_Sample_DryRun.csv")
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _model_readiness(rows):
    path = os.path.join(FORMAL, "MMU_Model_Readiness_FINAL.csv")
    if os.path.isfile(path):
        import csv
        with open(path, newline="") as fh:
            return list(csv.DictReader(fh))
    return []


def gen_source_report(bin_sha, bin_path, bin_state):
    commit = source_commit()
    cfg = _json(os.path.join(AUTH, "MMU_Formal_Config.json"))
    lines = ["# MMU Final Source / Binary Version Report", "",
             "Workspace: `%s`" % ROOT,
             "Git HEAD: `%s`" % _git_head(),
             "Final binary declared by Main: `%s`" % bin_sha,
             "Final binary status: **%s**" % bin_state, ""]
    lines += ["## Final binary", "", "| Field | Value |", "|---|---|",
              "| Path | `%s` |" % bin_path,
              "| SHA256 (declared) | `%s` |" % bin_sha,
              "| SHA256 (on disk) | `%s` |" %
              (sha256(os.path.join(ROOT, bin_path))
               if os.path.isfile(os.path.join(ROOT, bin_path)) else
               "<absent>"),
              "| Source commit | `%s` |" % commit, ""]
    lines += ["## Frozen source hashes", "", "| File | SHA256 |",
              "|---|---|"]
    for path, value in sorted((cfg.get("source_sha256") or {}).items()):
        actual = sha256(os.path.join(ROOT, path)) if os.path.isfile(
            os.path.join(ROOT, path)) else "<absent>"
        lines.append("| `%s` | `%s` (on disk `%s`) |" %
                     (path, value, actual))
    lines += ["", "## Workload hashes", "", "| Workload | SHA256 |",
              "|---|---|"]
    for wid, value in sorted((cfg.get("workload_sha256") or {}).items()):
        lines.append("| %s | `%s` |" % (wid, value))
    lines += ["", "If the final binary SHA is `PENDING_MAIN_FREEZE`, Main has "
              "not frozen the post-integration build yet; no hash is "
              "guessed.", ""]
    return "\n".join(lines)


def _git_head():
    try:
        out = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip()
    except Exception:
        return "<unknown>"


def gen_preflight_report(rows):
    from collections import Counter
    primary = Counter(r.get("PrimaryStatus", "") for r in rows)
    blockers = Counter()
    for r in rows:
        for b in (r.get("AllBlockers", "") or "").split(";"):
            if b and b != "READY":
                blockers[b] += 1
    ready = [r["SampleRunID"] for r in rows
             if r.get("PrimaryStatus") == "READY"]
    verdict = "READY" if len(ready) == 40 else "PARTIAL"
    lines = ["# MMU Formal Preflight Report", "",
             "Samples: **%d** (expected 40)" % len(rows),
             "Seed: literal `%s`, SeedPolicy=%s, SeedSource=%s, "
             "seed_used_by_gem5=false." %
             (SEED_LITERAL, SEED_POLICY, SEED_SOURCE), "",
             "**MMU_FORMAL_READINESS = %s**" % verdict, "",
             "## Primary status tally", "", "| Status | Count |",
             "|---|---:|"]
    for status, count in sorted(primary.items()):
        lines.append("| %s | %d |" % (status, count))
    lines += ["", "## All-blocker tally (a sample may have several)", "",
              "| Blocker | Samples |", "|---|---:|"]
    for status, count in sorted(blockers.items()):
        lines.append("| %s | %d |" % (status, count))
    lines += ["", "## READY samples (%d)" % len(ready), ""]
    lines += ["- %s" % s for s in ready] if ready else ["- none"]
    lines += ["", "## Per-sample status", "",
              "| SampleRunID | Model | Workload | Context | Primary | "
              "All blockers |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | **%s** | %s |" %
                     (r.get("SampleRunID"), r.get("ModelID"),
                      r.get("WorkloadID"), r.get("ContextID"),
                      r.get("PrimaryStatus"), r.get("AllBlockers")))
    lines += ["", "Rules: a missing `sample_manifest.json` or a binary/source "
              "mismatch is `BLOCKED_BINARY`/`BLOCKED_SOURCE`, never READY.  "
              "An M02 sample without a per-context no-fault W10 control is "
              "`BLOCKED_MISSING_W10_PFN_MAPPING`.  The W10S variants keep "
              "the authoritative WorkloadID `W10`.", ""]
    return "\n".join(lines)


def gen_trace_report(rows):
    by = {(r.get("ModelID"), r.get("ContextID")): r for r in rows}
    lines = ["# MMU Trace Validation Report", "",
             "All statuses below come from real PROP-EVT verdicts via "
             "`phase3/formal/evidence_index.json`; no run is accepted on "
             "file existence or guest output alone.", "",
             "## Validator rule change this round (M06)", "",
             "`tools/mmu_formal_validate.py` now requires real delivery "
             "evidence for M06 `DETECTED_CONTAINED`: an `exception_delivery` "
             "event, or summary `exception_delivered=1` with "
             "`result_propagated=1`.  A consumed descriptor whose fault "
             "result was never delivered is `TRACE_INCOMPLETE` (or "
             "`SQUASHED`), never `DETECTED_CONTAINED`.", "",
             "| Model/Context | Terminal | Oracle | Trace | Activation | "
             "Consumption |", "|---|---|---|---|---|---|"]
    index = _json(os.path.join(FORMAL, "evidence_index.json"))
    ctxs = index.get("contexts") or {}
    for key, ev in sorted(ctxs.items()):
        lines.append("| %s | %s | %s | %s | %s | %s |" %
                     (key, ev.get("terminal_state", "NOT_RUN"),
                      ev.get("oracle_result", "NOT_RUN"),
                      ev.get("trace_completeness", "NOT_RUN"),
                      ev.get("fault_activation", "NOT_RUN"),
                      ev.get("fault_consumption", "NOT_RUN")))
    lines += ["", "M05 R05 and M07 R03/R05 remain trace/context gaps unless "
              "their final pilots show COMPLETE evidence; the preflight "
              "status is authoritative.", ""]
    return "\n".join(lines)


def gen_control_report():
    import mmu_formal_preflight as pf
    pfn = pf.load_w10_pfn_map(ROOT)
    lines = ["# MMU Golden Control Report", "",
             "Every formal sample needs a separately executed no-fault "
             "control.  A faulted run's own output is never a golden.", "",
             "## Per model/context control", "",
             "| Model | Context | Control path | Line present | "
             "Independent | Detail |", "|---|---|---|---|---|---|"]
    for model in MODELS:
        workload = pf.MODEL_WORKLOAD[model]
        for ctx in CONTEXTS:
            control = pf.control_oracle_for(ROOT, model, workload, ctx)
            sample = {"ModelID": model, "WorkloadID": workload,
                      "ContextID": ctx}
            ok, detail = pf.check_control_independence(ROOT, sample, control)
            lines.append("| %s | %s | `%s` | %s | %s | %s |" %
                         (model, ctx,
                          os.path.relpath(control.get("path", ""), ROOT)
                          if control.get("path") else "-",
                          "YES" if control.get("line") else "NO",
                          "YES" if (ok and control.get("present")) else "NO",
                          (detail or control.get("detail", "")).replace(
                              "|", "/")))
    lines += ["", "## M02 W10 target PFN map", "",
              "Source: `%s` (%s)" % (pfn.get("path"), pfn.get("detail")),
              "", "| Context | target_pfn | Source run | SHA256 |",
              "|---|---|---|---|"]
    for ctx in CONTEXTS:
        rec = (pfn.get("contexts") or {}).get(ctx)
        if rec:
            lines.append("| %s | `0x%x` | %s | `%s` |" %
                         (ctx, rec.get("target_pfn", 0),
                          rec.get("source_run", ""),
                          (rec.get("source_sha256") or "")[:16]))
        else:
            lines.append("| %s | PENDING | - | - |" % ctx)
    lines += ["", "The legacy `--ctx all` W10 control is rejected: it reports "
              "target PFN `0x83480` / sentinel `0x7d`, while a scoped R02 run "
              "reports `0x834b6` / `0x63`.  No reference to `0x83480` is "
              "used as a run parameter.", ""]
    return "\n".join(lines)


def gen_m07_report(rows):
    changes_path = os.path.join(FINAL, "M07_CONTEXT_CHANGES.json")
    changes = _json(changes_path)
    lines = ["# MMU M07 Change Report", "",
             "Researcher-approved context change (not re-litigated):",
             "- R03 = PROT_EXEC + EL0 Load;",
             "- R05 = valid XN mapping + indirect-branch fetch.",
             "ModelID / FaultModel / SampleRunID / counts / seed are "
             "unchanged.  The exact context text is supplied verbatim by "
             "Agent C; it is never invented here.", ""]
    if changes:
        lines += ["## Applied context text", "",
                  "| Sample | Column | Before | After | Reason | "
                  "Approval basis |", "|---|---|---|---|---|---|"]
        for rec in changes.get("changes", []):
            sid = rec.get("sample_run_id", "")
            before = rec.get("before") or {}
            after = rec.get("after") or {}
            for col in sorted(set(before) | set(after)):
                lines.append("| %s | %s | %s | %s | %s | %s |" %
                             (sid, col,
                              str(before.get(col, "")).replace("|", "/"),
                              str(after.get(col, "")).replace("|", "/"),
                              rec.get("reason", "").replace("|", "/"),
                              rec.get("approval_basis", "").replace("|", "/")))
            lines.append("| %s | workload/golden/trace/final | %s | %s | - | "
                         "- |" %
                         (sid, rec.get("workload", ""),
                          "golden=%s; trace=%s; final=%s" %
                          (rec.get("golden", ""), rec.get("trace", ""),
                           rec.get("final_verification", ""))))
        lines += ["", "The workbook also carries the per-column record in "
                  "`17_M07_Context_Change_Record` and two `v2.1-M07` rows in "
                  "`13_Change_Log`; the Markdown history is "
                  "`MMU_Change_Log.md`.", ""]
    else:
        lines += ["## Status", "",
                  "`phase3/final/M07_CONTEXT_CHANGES.json` is absent: the "
                  "exact new context strings have not been delivered yet, so "
                  "no text was applied.  This is an explicit PENDING item, "
                  "not a completed change.", ""]
    lines += ["## Current runtime evidence", "",
              "| Sample | Context | Primary status | Terminal | Oracle |",
              "|---|---|---|---|---|"]
    for r in rows:
        if r.get("ModelID") != "M07":
            continue
        lines.append("| %s | %s | %s | %s | %s |" %
                     (r.get("SampleRunID"), r.get("ContextID"),
                      r.get("PrimaryStatus"), r.get("TerminalState"),
                      r.get("OracleResult")))
    lines.append("")
    return "\n".join(lines)


def gen_blockers(rows):
    lines = ["# MMU Final Blockers", "",
             "Only real, currently observed blockers are listed.  A sample "
             "with no entry here is READY in the preflight.", ""]
    any_block = False
    for r in rows:
        if r.get("PrimaryStatus") == "READY":
            continue
        any_block = True
        lines.append("## %s" % r.get("SampleRunID"))
        lines.append("- Model/Context: %s %s (%s)" %
                     (r.get("ModelID"), r.get("ContextID"),
                      r.get("WorkloadID")))
        lines.append("- Primary: **%s**" % r.get("PrimaryStatus"))
        lines.append("- All blockers: `%s`" % r.get("AllBlockers"))
        lines.append("- Provenance: %s" % r.get("ProvenanceDetail", ""))
        if r.get("M02OldPFNStatus") == "BLOCKED":
            lines.append("- M02 old_pfn: %s" % r.get("M02OldPFNDetail"))
        if r.get("OracleStatus") != "PASS":
            lines.append("- Oracle: %s" % r.get("OracleDetail"))
        if r.get("RuntimeEvidenceStatus") != "PASS":
            lines.append("- Runtime: %s (%s)" %
                         (r.get("RuntimeEvidenceStatus"),
                          r.get("RuntimeGateDetail")))
        lines.append("")
    if not any_block:
        lines += ["No blockers: all 40 samples are READY.", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=ROOT)
    ap.add_argument("--refresh", action="store_true",
                    help="re-run evidence index + preflight + readiness")
    ap.add_argument("--no-zip", action="store_true")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.repo_root)
    if args.refresh:
        refresh()
    rows = preflight_rows()
    if len(rows) != 40:
        print("PACKAGE ERROR: preflight CSV has %d rows, expected 40; run "
              "tools/mmu_formal_preflight.py first" % len(rows),
              file=sys.stderr)
        return 2

    stage = os.path.join(FINAL, STAGE_NAME)
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    os.makedirs(stage)
    artifacts = []
    missing_sources = []

    def add(num, name, src=None, text=None):
        dst = os.path.join(stage, "%02d_%s" % (num, name)
                           if not name.startswith("_") else name)
        if text is not None:
            _write(dst, text)
        else:
            if not src or not os.path.isfile(src):
                missing_sources.append("%02d_%s <- %s" %
                                       (num, name, src or "<none>"))
                return None
            shutil.copy2(src, dst)
        artifacts.append(dst)
        return dst

    add(1, "MMU_40_Sample_Matrix.csv",
        os.path.join(AUTH, "MMU_40_Sample_Matrix.csv"))
    add(2, "MMU_Model_Readiness_FINAL.csv",
        os.path.join(FORMAL, "MMU_Model_Readiness_FINAL.csv"))
    add(3, "MMU_Context_Readiness_FINAL.csv",
        os.path.join(FORMAL, "MMU_Context_Readiness_FINAL.csv"))
    add(4, "MMU_Formal_Config.json",
        os.path.join(AUTH, "MMU_Formal_Config.json"))
    add(5, "MMU_Formal_Config.yaml",
        os.path.join(AUTH, "MMU_Formal_Config.yaml"))
    add(6, "MMU_Seed_Semantics_Audit.md",
        os.path.join(FREEZE, "MMU_Seed_Semantics_Audit.md"))
    bin_sha, bin_path, bin_state = final_binary()
    add(7, "MMU_Source_Version_Report.md",
        text=gen_source_report(bin_sha, bin_path, bin_state))
    add(8, "MMU_Formal_Preflight_Report.md", text=gen_preflight_report(rows))
    add(9, "MMU_Trace_Validation_Report.md", text=gen_trace_report(rows))
    add(10, "MMU_Golden_Control_Report.md", text=gen_control_report())
    add(11, "MMU_M07_Change_Report.md", text=gen_m07_report(rows))
    add(12, "MMU_Final_Blockers.md", text=gen_blockers(rows))
    change_log = _read(os.path.join(FREEZE, "MMU_Change_Log.md"))
    add(13, "MMU_Change_Log.md", text=change_log)
    add(14, "evidence_index.json",
        os.path.join(FORMAL, "evidence_index.json"))
    add(15, "FINAL_BINARY.sha256",
        os.path.join(FINAL, "FINAL_BINARY.sha256"),
        text=(None if bin_state != "PENDING_MAIN_FREEZE" else
              "PENDING_MAIN_FREEZE  %s  (not frozen by Main; never guessed)\n"
              % bin_path))
    add(16, "preflight_summary.json",
        os.path.join(FORMAL, "preflight_summary.json"))
    add(17, "MMU_40_Sample_DryRun.csv",
        os.path.join(FORMAL, "MMU_40_Sample_DryRun.csv"))
    import mmu_formal_preflight as pf
    pfn = pf.load_w10_pfn_map(ROOT)
    pfn_payload = {"present": bool(pfn.get("present")),
                   "path": pfn.get("path"),
                   "detail": pfn.get("detail"),
                   "contexts": pfn.get("contexts") or {},
                   "sources": pfn.get("sources") or [],
                   "rejected": pfn.get("rejected") or []}
    add(18, "W10_PFN_CONTROL_MAP.json",
        text=json.dumps(pfn_payload, indent=2, sort_keys=True,
                        default=str) + "\n")
    add(19, "E_authority.md", os.path.join(FINAL, "E_authority.md"))

    # SHA256 manifest + machine manifest.
    manifest = {"package": STAGE_NAME,
                "artifacts": [], "content_artifact_count": len(artifacts),
                "required_artifact_count": 20,
                "missing_sources": missing_sources,
                "final_binary_sha256": bin_sha,
                "final_binary_status": bin_state,
                "source_commit": source_commit(),
                "seed": SEED_LITERAL, "seed_policy": SEED_POLICY,
                "seed_source": SEED_SOURCE, "seed_used_by_gem5": False,
                "sample_count": len(rows)}
    for path in artifacts:
        manifest["artifacts"].append({
            "file": os.path.basename(path),
            "sha256": sha256(path),
            "bytes": os.path.getsize(path),
        })
    _write(os.path.join(stage, "00_MANIFEST.json"),
           json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    lines = ["%s  %s" % (sha256(p), os.path.basename(p))
             for p in sorted(artifacts)]
    lines.append("%s  00_MANIFEST.json" % sha256(
        os.path.join(stage, "00_MANIFEST.json")))
    _write(os.path.join(stage, "SHA256_MANIFEST.txt"),
           "\n".join(lines) + "\n")

    missing = list(missing_sources)
    missing += [a["file"] for a in manifest["artifacts"]
                if not os.path.isfile(os.path.join(stage, a["file"]))]
    if not args.no_zip:
        zip_path = os.path.join(FINAL, STAGE_NAME + ".zip")
        if os.path.isfile(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, "w",
                             compression=zipfile.ZIP_DEFLATED) as zf:
            for dirpath, _dirs, files in os.walk(stage):
                for name in sorted(files):
                    full = os.path.join(dirpath, name)
                    rel = os.path.relpath(full, os.path.dirname(stage))
                    zf.write(full, rel)
        _write(zip_path + ".sha256", "%s  %s\n" % (sha256(zip_path),
                                                   os.path.basename(zip_path)))
    print(json.dumps({
        "stage": stage,
        "artifact_count": len(artifacts),
        "missing": missing,
        "final_binary_sha256": bin_sha,
        "final_binary_status": bin_state,
        "zip": None if args.no_zip else
        os.path.join(FINAL, STAGE_NAME + ".zip"),
    }, indent=2))
    return 0 if not missing else 5


if __name__ == "__main__":
    sys.exit(main())
