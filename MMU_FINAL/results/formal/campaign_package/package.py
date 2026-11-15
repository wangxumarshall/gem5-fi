#!/usr/bin/env python3
"""Assemble MMU_Final_Formal_Campaign_Results_Package.zip.

Never modifies run evidence; hashes and indexes the real files.
"""
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from collections import Counter, OrderedDict

REPO = "/home/sdc/gem5-fi-mmu-impl-v2"
CAMP = os.path.join(REPO, "runs/MMU_FORMAL_CAMPAIGN_20261113")
A = os.path.join(CAMP, "analysis")
AUTH = os.path.join(REPO, "phase3/final/"
                    "MMU_Final_Formal_Readiness_Package_v3.0.2")
PKG = os.path.join(CAMP, "MMU_Final_Formal_Campaign_Results_Package")
SAMPLES = json.load(open(os.path.join(A, "samples.json")))
MODELS = ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08"]
BATCHES = [("Batch1_M01_M02", ["M01", "M02"]),
           ("Batch2_M03_M04", ["M03", "M04"]),
           ("Batch3_M05_M06", ["M05", "M06"]),
           ("Batch4_M07_M08", ["M07", "M08"])]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(path):
    return os.path.relpath(path, REPO)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)


def main():
    if os.path.isdir(PKG):
        shutil.rmtree(PKG)
    os.makedirs(PKG)
    ev_dir = os.path.join(PKG, "evidence_index")
    os.makedirs(ev_dir)

    # ---------- campaign index ----------
    idx_cols = ["CampaignID", "SampleRunID", "ModelID", "ContextID",
                "WorkloadID", "Role", "AttemptID", "RunStatus",
                "ActivationStatus", "FaultConsumptionStatus",
                "PropagationStatus", "TerminalState", "OracleResult",
                "TraceCompleteness", "RecordIntegrity", "FaultID",
                "TargetVA", "AccessMode", "BinarySHA256", "WorkloadSHA256",
                "ConfigSHA256", "StartedUTC", "FinishedUTC", "Gem5ExitCode",
                "RunDir"]
    with open(os.path.join(PKG, "40_Sample_Matrix_Completed.csv"), "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=idx_cols)
        w.writeheader()
        for s in SAMPLES:
            w.writerow({k: s.get(k, "") for k in idx_cols})

    # ---------- evidence index (absolute paths + hashes) ----------
    ev_rows = []
    for s in SAMPLES:
        d = os.path.join(REPO, s["RunDir"]) if not os.path.isabs(s["RunDir"]) \
            else s["RunDir"]
        files = ["sample_manifest.json", "Validation/verdict.json",
                 "Validation/verdict.md", "Run_Log/observed_output.txt",
                 "Run_Log/board.terminal", "Run_Log/command.txt",
                 "Run_Log/stats.txt", "Config/config.ini", "rcS.scoped",
                 "Trace/prop_evt.txt.gz", "Trace/prop_trace.csv.gz",
                 "SHA256/SHA256SUMS.txt"]
        for f in files:
            p = os.path.join(d, f)
            label = f
            if f == "rcS.scoped" and not os.path.exists(p):
                # W10S variants are pre-scoped: the executed rcS is the
                # workload-owned --readfile handed to gem5, not a derived
                # rcS.scoped.  Index the real file.
                cmd = os.path.join(d, "Run_Log", "command.txt")
                m = re.search(r"--readfile\s+(\S+)",
                              open(cmd, errors="replace").read()) \
                    if os.path.exists(cmd) else None
                if m:
                    eff = m.group(1)
                    p = eff if os.path.isabs(eff) else os.path.join(REPO, eff)
                    label = "rcS.effective"
            ev_rows.append({
                "SampleRunID": s["SampleRunID"], "AttemptID": s["AttemptID"],
                "File": label, "AbsolutePath": p,
                "Exists": os.path.exists(p),
                "SHA256": sha(p) if os.path.exists(p) else ""})
    with open(os.path.join(ev_dir, "raw_trace_and_evidence_index.csv"), "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ev_rows[0].keys()))
        w.writeheader()
        w.writerows(ev_rows)
    json.dump(ev_rows, open(os.path.join(
        ev_dir, "raw_trace_and_evidence_index.json"), "w"), indent=1)

    # ---------- fault / control pairing ----------
    pair_cols = ["SampleRunID", "ModelID", "ContextID", "Role",
                 "ControlOraclePath", "ControlOracleSHA256", "ControlRunDir",
                 "InjectionAppliedCount", "ControlGem5ExitCode",
                 "ControlConfigFaultModel", "ZeroProofStatus", "PairingBasis"]
    with open(os.path.join(PKG, "fault_control_pairs.csv"), "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=pair_cols)
        w.writeheader()
        for s in SAMPLES:
            p = s.get("ControlZeroProof") or {}
            co = s.get("ControlOracle") or {}
            w.writerow({
                "SampleRunID": s["SampleRunID"], "ModelID": s["ModelID"],
                "ContextID": s["ContextID"], "Role": "Fault",
                "ControlOraclePath": co.get("path", ""),
                "ControlOracleSHA256": co.get("sha256", ""),
                "ControlRunDir": p.get("control_run_dir", ""),
                "InjectionAppliedCount": p.get("injection_applied_count"),
                "ControlGem5ExitCode": p.get("gem5_exit_code"),
                "ControlConfigFaultModel": p.get("config_mmuFaultModel"),
                "ZeroProofStatus": p.get("status"),
                "PairingBasis": ("frozen approved shareable independent "
                                 "control; no new control SampleRunID"),
            })
    shutil.copy2(os.path.join(A, "control_zero_proof.json"),
                 os.path.join(PKG, "control_zero_proof.json"))

    # ---------- per-context completeness ----------
    with open(os.path.join(PKG, "per_context_completeness.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["SampleRunID", "ModelID", "ContextID", "TraceCompleteness",
                    "PropagationStatus", "TerminalState",
                    "ChainEventCount", "StrictIdentityChainOK",
                    "LegalTerminal"])
        for s in SAMPLES:
            sc = s.get("StrictChain")
            w.writerow([s["SampleRunID"], s["ModelID"], s["ContextID"],
                        s["TraceCompleteness"], s["PropagationStatus"],
                        s["TerminalState"], s["ChainEventCount"],
                        ("" if sc is None else sc.get("ok")),
                        s["TerminalState"] in
                        ("SDC", "SQUASHED", "DETECTED_CONTAINED",
                         "ACTIVATED_MASKED", "CRASH", "HANG/TIMEOUT")])

    # ---------- batch acceptance ----------
    md = ["# Batch acceptance (derived from real run evidence)", ""]
    for name, models in BATCHES:
        sub = [s for s in SAMPLES if s["ModelID"] in models]
        md.append("## %s" % name)
        md.append("")
        md.append("- Samples: %d (completed %d)" % (
            len(sub), sum(1 for s in sub if s["RunStatus"] == "COMPLETED")))
        md.append("- Activation: %s" % dict(Counter(
            s["ActivationStatus"] for s in sub)))
        md.append("- Terminal: %s" % dict(Counter(
            s["TerminalState"] for s in sub)))
        md.append("- Trace: %s" % dict(Counter(
            s["TraceCompleteness"] for s in sub)))
        md.append("- Oracle: %s" % dict(Counter(
            s["OracleResult"] for s in sub)))
        md.append("- Binary hash: %s" % sorted(set(
            s["BinarySHA256"] for s in sub)))
        md.append("- Control zero proof: %s" % dict(Counter(
            (s.get("ControlZeroProof") or {}).get("status") for s in sub)))
        md.append("")
    retried = [s for s in SAMPLES if s["AttemptID"] == "A02"]
    md.append("## Retries / interruptions\n")
    if retried:
        for s in retried:
            md.append("- `%s`: original AttemptID A01 was interrupted by an "
                      "external process kill; A01 directory and partial "
                      "output retained; formal result from AttemptID A02."
                      % s["SampleRunID"])
    else:
        md.append("- none")
    write(os.path.join(PKG, "batch_acceptance.md"), "\n".join(md) + "\n")

    # ---------- provenance ----------
    six = ["CHAOS/gem5/src/arch/arm/mmu.cc",
           "CHAOS/gem5/src/arch/arm/table_walker.cc",
           "CHAOS/gem5/src/arch/arm/table_walker.hh",
           "CHAOS/gem5/src/arch/arm/tlb.cc",
           "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc",
           "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"]
    prov = OrderedDict([
        ("campaign_id", "MMU-FORMAL-20261113"),
        ("repo_root", REPO),
        ("git_head", subprocess.check_output(
            ["git", "-C", REPO, "rev-parse", "HEAD"]).decode().strip()),
        ("source_closure_commit", "60f1a8760410288128061d85582e5395b24c0106"),
        ("binary", {"path": os.path.join(REPO,
         "CHAOS/gem5/build/ARM/gem5.opt"),
         "sha256": sha(os.path.join(REPO,
                                    "CHAOS/gem5/build/ARM/gem5.opt"))}),
        ("source_sha256", {r: sha(os.path.join(REPO, r)) for r in six}),
        ("authority", {f: {"path": os.path.join(AUTH, f), "sha256":
                           sha(os.path.join(AUTH, f))}
                       for f in ["gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx",
                                 "MMU_40_Sample_Matrix.csv",
                                 "MMU_Parameter_Authority_v3.0.2.json"]}),
        ("runner", {"path": os.path.join(REPO,
                                         "tools/mmu_formal_runner.py"),
                    "sha256": sha(os.path.join(
                        REPO, "tools/mmu_formal_runner.py"))}),
        ("workloads", {w: sha(os.path.join(REPO, p)) for w, p in [
            ("W9", "workloads/mmu/W9/mmu_w9"),
            ("W10", "workloads/mmu/W10/mmu_w10"),
            ("W10S", "workloads/mmu/W10S/mmu_w10s"),
            ("W11", "workloads/mmu/W11/mmu_w11"),
            ("W12", "workloads/mmu/W12/mmu_w12"),
            ("W13", "workloads/mmu/W13/mmu_w13"),
            ("W14", "workloads/mmu/W14/mmu_w14")]}),
        ("kernel", {"path": os.path.join(REPO, "gem5-fs/vmlinux"),
                    "sha256": sha(os.path.join(REPO, "gem5-fs/vmlinux"))}),
        ("bootloader", {"path": os.path.join(REPO, "gem5-fs/boot.arm64"),
                        "sha256": sha(os.path.join(
                            REPO, "gem5-fs/boot.arm64"))}),
        ("checkpoint", os.path.join(REPO,
                                    "runs/mmu_bootF1/cpt.244799013609")),
        ("disk_template", {"path": os.path.join(
            REPO, "runs/disks/mmu_template.img"),
            "sha256": sha(os.path.join(REPO,
                                       "runs/disks/mmu_template.img"))}),
        ("started_utc", min(s["StartedUTC"] for s in SAMPLES)),
        ("finished_utc", max(s["FinishedUTC"] for s in SAMPLES)),
    ])
    json.dump(prov, open(os.path.join(PKG, "provenance.json"), "w"), indent=1)
    write(os.path.join(PKG, "provenance.md"),
          "# Provenance\n\n```json\n%s\n```\n" %
          json.dumps(prov, indent=1))

    # ---------- copy analysis artifacts ----------
    copies = ["samples.csv", "samples.json", "final_summary.json",
              "campaign_summary.json", "campaign_summary.md",
              "diagnostic_features.json", "control_zero_proof.json",
              "model_specific_validation.json",
              "model_specific_validation.md",
              "MMU_Final_Formal_Campaign_Results.xlsx",
              "collect.py", "report.py", "validate_models.py", "package.py"]
    for c in copies:
        shutil.copy2(os.path.join(A, c), os.path.join(PKG, c))
    shutil.copytree(os.path.join(A, "propagation_chains"),
                    os.path.join(PKG, "propagation_chains"))
    # structured chain index
    chain_rows = [{"SampleRunID": s["SampleRunID"],
                   "ChainJSON": os.path.join(
                       PKG, "propagation_chains", s["SampleRunID"] + ".json"),
                   "ChainCSV": os.path.join(
                       PKG, "propagation_chains", s["SampleRunID"] + ".csv"),
                   "Events": s["ChainEventCount"]} for s in SAMPLES]
    json.dump(chain_rows, open(os.path.join(PKG, "propagation_chain_index.json"),
                               "w"), indent=1)

    # authority + runner copies
    os.makedirs(os.path.join(PKG, "authority"))
    for f in ["gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx",
              "MMU_40_Sample_Matrix.csv",
              "MMU_Parameter_Authority_v3.0.2.json",
              "MMU_Change_Log_v3.0.2.md"]:
        shutil.copy2(os.path.join(AUTH, f),
                     os.path.join(PKG, "authority", f))
    os.makedirs(os.path.join(PKG, "runner"))
    shutil.copy2(os.path.join(REPO, "tools/mmu_formal_runner.py"),
                 os.path.join(PKG, "runner/mmu_formal_runner.py"))
    shutil.copy2(os.path.join(REPO, "tools/mmu_formal_validate.py"),
                 os.path.join(PKG, "runner/mmu_formal_validate.py"))
    shutil.copy2(os.path.join(REPO, "tools/mmu_evidence_chain.py"),
                 os.path.join(PKG, "runner/mmu_evidence_chain.py"))

    # ---------- failures / limitations ----------
    bad = [s for s in SAMPLES if s["RunStatus"] != "COMPLETED" or
           s["TraceCompleteness"] != "COMPLETE"]
    lim = ["# Failed / Timeout / Incomplete", ""]
    if bad:
        for s in bad:
            lim.append("- `%s`: run=%s trace=%s" % (
                s["SampleRunID"], s["RunStatus"], s["TraceCompleteness"]))
    else:
        lim.append("- No failed, timed-out or trace-incomplete sample.")
    lim.append("")
    lim.append("## Observation limitations (frozen instrumentation scope)")
    lim.append("- The frozen binary does not emit per-instruction IFU fetch "
               "response, decode, or IFU-specific commit events. "
               "Instruction-side samples therefore use MMU translation/"
               "permission -> Execute Request -> Guest Oracle, exactly as "
               "approved; these downstream nodes are marked "
               "NOT_EMITTED_BY_FROZEN_BINARY, not fabricated.")
    lim.append("- M03 R01-R04 terminate SQUASHED with PropagationStatus "
               "PARTIAL by design: the false-hit translation is squashed "
               "before a data-side consumer. TraceCompleteness is COMPLETE "
               "for every one of them.")
    lim.append("- M06 is a detected-and-contained translation fault "
               "(PASS_EXPECTED_DETECTION); this is a legal terminal, not a "
               "run failure.")
    write(os.path.join(PKG, "failed_timeout_incomplete.md"),
          "\n".join(lim) + "\n")

    # ---------- extraction script ----------
    write(os.path.join(PKG, "extract_campaign.sh"), """#!/usr/bin/env bash
# Reproduce the MMU formal campaign dataset from the stable server paths.
# Read-only over run evidence. Adjust REPO if the workspace moves.
set -eu
REPO="${REPO:-/home/sdc/gem5-fi-mmu-impl-v2}"
CAMP="$REPO/runs/MMU_FORMAL_CAMPAIGN_20261113"
python3 "$CAMP/analysis/collect.py"
python3 "$CAMP/analysis/report.py"
python3 "$CAMP/analysis/validate_models.py"
python3 "$CAMP/analysis/package.py"
echo "Artifacts regenerated under $CAMP/analysis and"
echo "$CAMP/MMU_Final_Formal_Campaign_Results_Package"
""")

    # ---------- README ----------
    summ = json.load(open(os.path.join(A, "final_summary.json")))
    write(os.path.join(PKG, "README_RESULTS.md"), """# MMU Final Formal Campaign Results Package

Campaign: `MMU-FORMAL-20261113`
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2`
Binary SHA256: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`
Source closure: `60f1a8760410288128061d85582e5395b24c0106`

## Verdict

`%s`

| Metric | Value |
|---|---|
| Planned samples | 40 |
| Started samples | 40 |
| Completed samples | %d |
| Valid injection evidence | %d |
| Fault state consumed | %d |
| Propagation chain complete (trace) | %d |
| Legal terminal | %d |
| Unfinished samples | %d |
| Control runs referenced | %d |
| Control zero proof | %d / %d |

Terminal distribution: %s

## Why COMPLETE_WITH_LIMITATIONS

%s

## Contents

- `40_Sample_Matrix_Completed.csv` — 40 SampleRunID completion matrix with
  CampaignID, Role, AttemptID and hashes.
- `fault_control_pairs.csv` — Fault -> approved independent control mapping.
- `control_zero_proof.json` — executed-config evidence of zero injection.
- `evidence_index/raw_trace_and_evidence_index.{csv,json}` — absolute paths
  and SHA256 for every manifest, verdict, oracle, config, stats and raw
  PROP-EVT trace.
- `propagation_chains/` — 40 structured chains (JSON + CSV).
- `diagnostic_features.json` — per-sample microarchitectural feature library.
- `model_specific_validation.{json,md}` — §10 gates, 40/40 PASS.
- `batch_acceptance.md`, `per_context_completeness.csv`.
- `MMU_Final_Formal_Campaign_Results.xlsx` — paper experiment workbook.
- `authority/` — frozen Excel, CSV, parameter authority, change log.
- `runner/` — frozen runner + validator + chain library copies.
- `provenance.json`, `failed_timeout_incomplete.md`.
- `extract_campaign.sh` — reproducible regeneration script.
- `SHA256_MANIFEST.txt` — hashes of every packaged file.

Raw traces remain at the absolute paths in
`evidence_index/raw_trace_and_evidence_index.csv` (not duplicated in this ZIP).

## Retries

M06 R04 and M08 R04 were interrupted by an external process kill during
Batch 3/4. The partial A01 directories are retained untouched; their formal
results are from a new AttemptID A02. No completed attempt was overwritten.
""" % (summ["status"], summ["completed_samples"],
       summ["valid_injection_evidence"], summ["fault_state_consumed"],
       summ["chain_complete"], summ["legal_terminal"],
       summ["unfinished_samples"], summ["control_runs_referenced"],
       summ["control_zero_proven"], summ["control_runs_referenced"],
       json.dumps(summ["terminal_distribution"]),
       "\n".join("- " + x for x in summ.get("limitations", []))))

    # ---------- complete experiment configuration ----------
    cmd_lines = []
    plan_rows = []
    for st in SAMPLES:
        d = st["RunDir"]
        cp = os.path.join(d, "Run_Log", "command.txt")
        cmd = open(os.path.join(REPO, cp), errors="replace").read().strip() \
            if os.path.exists(os.path.join(REPO, cp)) else ""
        cmd_lines.append("%s (Attempt %s)\t%s" % (
            st["SampleRunID"], st["AttemptID"], cmd))
        plan_rows.append({"SampleRunID": st["SampleRunID"],
                          "ModelID": st["ModelID"],
                          "ContextID": st["ContextID"],
                          "Role": "Fault", "AttemptID": st["AttemptID"],
                          "Seed": st["Seed"],
                          "SeedPolicy": st["SeedPolicy"],
                          "Command": cmd})
    write(os.path.join(PKG, "experiment_commands.txt"),
          "\n".join(cmd_lines) + "\n")
    json.dump(plan_rows, open(os.path.join(PKG, "campaign_plan.json"), "w"),
              indent=1)

    # ---------- SHA256 manifest ----------
    rows = []
    for root, _dirs, files in os.walk(PKG):
        for f in sorted(files):
            p = os.path.join(root, f)
            rows.append("%s  %s" % (sha(p), os.path.relpath(p, PKG)))
    write(os.path.join(PKG, "SHA256_MANIFEST.txt"), "\n".join(rows) + "\n")

    # ---------- zip ----------
    zpath = os.path.join(CAMP, "MMU_Final_Formal_Campaign_Results_Package.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) \
            as z:
        for root, _dirs, files in os.walk(PKG):
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, CAMP))
    print("ZIP", zpath)
    print("ZIP_SHA256", sha(zpath))
    print("PACKAGE_FILES", len(rows))


if __name__ == "__main__":
    main()
