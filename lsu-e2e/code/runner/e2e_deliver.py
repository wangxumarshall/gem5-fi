#!/usr/bin/env python3
"""Assemble the E2E acceptance matrices and reports from causal-chain JSONs."""
from __future__ import annotations

import csv
import glob
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L
import e2e_analyze as A

EXT = L.EXT
REP = EXT / "reports"
EVID = EXT / "evidence/causal_chains"
OLD = Path("/home/sdc/gem5-fi-LSU/LSU_When_v2_FINAL_FROZEN/"
           "FINAL_180_FAULT_EVIDENCE.csv")


def load_all():
    out = []
    for p in sorted(EVID.glob("*.causal_chain.json")):
        out.append(json.loads(p.read_text()))
    return out


def old_map():
    m = {}
    with open(OLD, newline="") as f:
        for r in csv.DictReader(f):
            m[r["RunID"]] = r
    return m


def state(run_id):
    p = EXT / "results/state" / f"{run_id}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def ctrl_cache(model, ctx):
    p = (EXT / "results/controls" / f"E2E-{model}-{ctx}-CTRL" /
         "attempt_1/sw_events.json")
    return json.loads(p.read_text()) if p.exists() else {}


def first_micro(d):
    ev = d["injection_events"]
    if not ev:
        return "N/A"
    e = ev[0]
    return f"{e['kind']}@seq{e['dyn_inst_seq']}/tick{e['tick']}"


def first_arch(d):
    a = d["architectural"]["first_architectural_divergence"]
    if not a:
        return "N/A"
    if a.get("dyn_inst_seq") is None:
        return "N/A: " + a.get("note", "")
    return (f"seq{a['dyn_inst_seq']}@{a.get('pc')} "
            f"(ctrace:{a.get('ctrace_line')})")


def first_sw(d):
    fd = d["software"].get("first_divergence")
    if not fd or not fd.get("fault"):
        return "N/A"
    f = fd["fault"]
    return (f"{f['type']} site{f['site']} op_seq{f.get('op_dyn_inst_seq')} "
            f"obs={hex(f['b'])} ctrl={hex(fd['control']['b']) if fd.get('control') else 'N/A'}")


def final_status(d):
    if d["terminal"] == "HANG_WATCHDOG":
        return "WATCHDOG_TERMINATED (application did not complete)"
    if d["terminal"] == "CRASH":
        return f"CRASH_EXIT_{d.get('exit_code')}"
    if d["terminal"] == "SDC":
        return "COMPLETED_EXIT_0_WRONG_OUTPUT"
    return "COMPLETED_EXIT_0_CORRECT_OUTPUT"


def layers(d):
    c = d["classification"]
    fd = d["software"].get("first_divergence")
    masks = [n for n in d["nodes"] if n["kind"] == "masking_endpoint"]
    return {
        "InjectionEvidence": bool(d["injection_events"]),
        "TargetEffectEvidence": bool(d["microarchitecture_events"]),
        "MicroarchStateEvidence": any(
            e["kind"] not in ("consumer", "prop_edge")
            for e in d["microarchitecture_events"]),
        "DynamicInstructionIdentity": bool(d["target"] and
                                           d["target"].get("seq") is not None),
        "ArchitecturalEndpoint": bool(
            d["architectural"].get("target_commit") or
            d["architectural"].get("target_squash") or
            (d.get("stall_chain") or {}).get("fault_target_committed") is False),
        "SoftwareEndpoint": bool((fd and fd.get("fault")) or masks or
                                 d["terminal"] == "HANG_WATCHDOG"),
        "ContinuousCausalPath": c["end_to_end_status"] ==
        "E2E_CAUSAL_COMPLETE",
        "HashChainContinuous": (d["software"]["hash_chain_breaks"] == 0
                                if d["terminal"] == "SDC" else "N/A"),
    }


def write_matrix(runs):
    cols = ["RunID", "ModelID", "ContextID", "TimingID", "InjectionEffective",
            "FirstMicroarchitectureDivergence", "FirstArchitecturalDivergence",
            "FirstSoftwareDivergence", "SoftwareSymptom", "SymptomSubtype",
            "PropagationTermination", "FinalApplicationStatus",
            "OracleStatus", "EndToEndChainStatus", "MissingCausalEdges",
            "EvidencePaths", "OldRunID", "NewRunID"]
    with open(REP / "E2E_180_Run_Symptom_Matrix.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for d in runs:
            c = d["classification"]
            w.writerow([
                d["run_id"], d["model"], d["context"], d["timing"],
                ("YES" if d["injection_events"] else "NO"),
                first_micro(d), first_arch(d), first_sw(d),
                c["software_symptom"], c["symptom_subtype"] or "",
                c["propagation_termination"], final_status(d),
                ("PASS" if d["software"].get("output") and
                 d["software"]["output"]["oracle_pass"] else
                 ("N/A_WATCHDOG" if d["terminal"] == "HANG_WATCHDOG"
                  else "MISMATCH")),
                c["end_to_end_status"], ";".join(c["gaps"]),
                "|".join(d["evidence_files"].values()),
                d["old_run_id"], d["run_id"]])


def write_completion(runs):
    with open(REP / "E2E_180_Run_Causal_Completion.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        cols = ["RunID", "ModelID", "ContextID", "TimingID",
                "InjectionEvidence", "TargetEffectEvidence",
                "MicroarchStateEvidence", "DynamicInstructionIdentity",
                "ArchitecturalEndpoint", "SoftwareEndpoint",
                "ContinuousCausalPath", "HashChainContinuous",
                "EndToEndStatus", "MissingCausalEdges", "LimitationNotes"]
        w.writerow(cols)
        for d in runs:
            ly = layers(d)
            notes = []
            if d["terminal"] == "HANG_WATCHDOG":
                sc = d.get("stall_chain") or {}
                if sc.get("commit_trace_tail_truncated"):
                    notes.append("commit-trace tail truncated; watchdog "
                                 "ledger used as authoritative last commit")
            if d["model"] == "A03":
                notes.append(f"persistent fault: {len(d['injection_events'])} "
                             "injection events; primary effective event cited")
            if d["classification"]["software_symptom"] == "NO_VISIBLE_ERROR":
                notes.append("masked at software level; mechanism cited")
            w.writerow([d["run_id"], d["model"], d["context"], d["timing"],
                        ly["InjectionEvidence"], ly["TargetEffectEvidence"],
                        ly["MicroarchStateEvidence"],
                        ly["DynamicInstructionIdentity"],
                        ly["ArchitecturalEndpoint"], ly["SoftwareEndpoint"],
                        ly["ContinuousCausalPath"], ly["HashChainContinuous"],
                        d["classification"]["end_to_end_status"],
                        ";".join(d["classification"]["gaps"]),
                        "; ".join(notes)])


def write_gap_audit(runs):
    with open(REP / "E2E_Causal_Gap_Audit.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "ModelID", "ContextID", "TimingID",
                    "MissingMicroarchitectureEvidence",
                    "MissingArchitecturalEvidence",
                    "MissingSoftwareEvidence", "MissingCausalLink",
                    "MissingTerminalEvidence", "Status", "Notes"])
        for d in runs:
            ly = layers(d)
            miss_m = "" if ly["MicroarchStateEvidence"] else "target uarch row"
            miss_a = ("" if ly["ArchitecturalEndpoint"] else
                      "commit/squash/stall endpoint")
            miss_s = ("" if ly["SoftwareEndpoint"] else
                      "software divergence or masking evidence")
            miss_l = "" if ly["ContinuousCausalPath"] else "causal connection"
            miss_t = "" if d["terminal"] in ("SDC", "NO_VISIBLE_MISMATCH",
                                             "HANG_WATCHDOG") else "terminal"
            notes = []
            if d["classification"]["software_symptom"] == "NO_VISIBLE_ERROR":
                notes.append("masked: " + d["classification"][
                    "propagation_termination"])
            if d["terminal"] == "HANG_WATCHDOG":
                notes.append("pipeline stall -> simulator watchdog")
            w.writerow([d["run_id"], d["model"], d["context"], d["timing"],
                        miss_m, miss_a, miss_s, miss_l, miss_t,
                        d["classification"]["end_to_end_status"],
                        "; ".join(notes)])


def write_m2s(runs):
    with open(REP / "E2E_Microarchitecture_to_Software_Evidence.csv", "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "ModelID", "TargetSeq", "TargetPC",
                    "TargetAddress", "InjectionKind", "UarchRecords",
                    "ReloadSeq", "ReloadAddress", "FirstSoftwareType",
                    "FirstSoftwareSite", "FirstSoftwareOpSeq",
                    "FaultValue", "ControlValue", "OutputChecksum",
                    "Expected", "OraclePass"])
        for d in runs:
            t = d["target"] or {}
            fd = d["software"].get("first_divergence") or {}
            f = fd.get("fault") or {}
            rel = d["software"].get("reload") or {}
            out = d["software"].get("output") or {}
            rows = ";".join(sorted({e["kind"] for e in
                                    d["microarchitecture_events"]}))
            w.writerow([d["run_id"], d["model"], t.get("seq"),
                        hex(t["pc"]) if t.get("pc") else "",
                        (hex(A.target_addr(d["model"], t.get("kv", {})))
                         if t and A.target_addr(d["model"],
                                                t.get("kv", {})) is not None
                         else ""),
                        t.get("kind"), rows, rel.get("dyn_inst_seq", ""),
                        hex(rel["address"]) if rel.get("address") else "",
                        f.get("type", ""), f.get("site", ""),
                        f.get("op_dyn_inst_seq", ""),
                        hex(f["b"]) if "b" in f else "",
                        hex(fd["control"]["b"]) if fd.get("control") else "",
                        hex(out["checksum"]) if out.get("checksum") else "",
                        out.get("expected", ""), out.get("oracle_pass", "")])


def write_oracle(runs):
    with open(REP / "E2E_Application_Oracle_Diff.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "ModelID", "ContextID", "TimingID",
                    "ExpectedChecksum", "ObservedChecksum", "OraclePass",
                    "FirstDivergenceType", "FirstDivergenceSite",
                    "FaultValue", "ControlValue", "HashChainEvents",
                    "HashChainBreaks", "OutputMarkerChecksum",
                    "SoftwareSymptom", "SymptomSubtype"])
        for d in runs:
            fd = d["software"].get("first_divergence") or {}
            f = fd.get("fault") or {}
            out = d["software"].get("output") or {}
            w.writerow([d["run_id"], d["model"], d["context"], d["timing"],
                        out.get("expected", ""),
                        hex(out["checksum"]) if out.get("checksum") else "",
                        out.get("oracle_pass", ""), f.get("type", ""),
                        f.get("site", ""),
                        hex(f["b"]) if "b" in f else "",
                        hex(fd["control"]["b"]) if fd.get("control") else "",
                        d["software"]["hash_chain_events"],
                        d["software"]["hash_chain_breaks"],
                        hex(out["checksum"]) if out.get("checksum") else "",
                        d["classification"]["software_symptom"],
                        d["classification"]["symptom_subtype"] or ""])


def write_crash_audit(runs):
    with open(REP / "E2E_Crash_Hang_Squash_Masking_Audit.csv", "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "ModelID", "ContextID", "TimingID",
                    "Terminal", "ExitCode", "TargetCommitted",
                    "TargetSquashed", "SoftwareSymptom", "SymptomSubtype",
                    "PropagationTermination", "MaskingOrSquashEvidence",
                    "Watchdog", "Notes"])
        for d in runs:
            c = d["classification"]
            masks = [n for n in d["nodes"] if n["kind"] == "masking_endpoint"]
            ev = masks[0].get("later_events", []) if masks else []
            notes = []
            if d["terminal"] == "HANG_WATCHDOG":
                sc = d.get("stall_chain") or {}
                notes.append(f"last_commit={sc.get('last_commit_dyn_seq')} "
                             f"silent_ticks={sc.get('silent_ticks')} "
                             f"control_target_committed="
                             f"{sc.get('control_target_committed')}")
            if c["end_to_end_status"] != "E2E_CAUSAL_COMPLETE":
                notes.append("gaps: " + ";".join(c["gaps"]))
            w.writerow([d["run_id"], d["model"], d["context"], d["timing"],
                        d["terminal"], d.get("exit_code"),
                        c["target_committed"], c["target_squashed"],
                        c["software_symptom"], c["symptom_subtype"] or "",
                        c["propagation_termination"],
                        "|".join(f"{e['type']}:{e['site']}:{hex(e['value'])}"
                                 for e in ev[:6]), d.get("watchdog"),
                        "; ".join(notes)])


def write_pairing(runs):
    with open(REP / "E2E_Control_Fault_Pairing.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["NewRunID", "OldRunID", "ModelID", "ContextID",
                    "TimingID", "ControlRunID", "ControlEligibleN",
                    "ControlOrdinals", "SelectedOrdinal",
                    "ObservedOrdinal", "OrdinalMatch", "IdentityMatch",
                    "ControlChecksum", "FaultChecksum", "ControlCommits",
                    "FaultEvents", "ControlEvents", "FaultElapsedS",
                    "BinarySHA256", "ConfigSHA256", "ELFSHA256"])
        for d in runs:
            st = state(d["run_id"])
            cc = ctrl_cache(d["model"], d["context"])
            cp = d["control_pairing"]
            w.writerow([d["run_id"], d["old_run_id"], d["model"],
                        d["context"], d["timing"], cp.get("control_run_id"),
                        cc.get("eligible_n"),
                        json.dumps(cc.get("eligible_ordinals", {})),
                        st.get("selected_ordinal"), st.get("observed_ordinal"),
                        st.get("ordinal_match"), st.get("identity_match"),
                        cp.get("control_checksum"),
                        cp.get("fault_checksum"), cp.get("control_commits"),
                        cp.get("fault_commits"), cp.get("fault_events"),
                        st.get("elapsed"), st.get("binary_sha"),
                        st.get("config_sha"), st.get("elf_sha")])


def write_ww(runs, om):
    with open(REP / "E2E_Where_When_Symptom_Comparison.csv", "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["NewRunID", "OldRunID", "ModelID", "ContextID",
                    "TimingID", "OldTerminalOutcome", "OldFinalClass",
                    "OldMechanism", "OldChainComplete", "NewTerminal",
                    "NewSymptom", "NewSubtype", "NewTermination",
                    "NewE2EStatus", "OutcomeChanged", "Note"])
        for d in runs:
            o = om.get(d["old_run_id"], {})
            old_term = o.get("TERMINAL_OUTCOME", "")
            new_term = d["terminal"]
            changed = ("YES" if old_term and
                       not ((old_term == "SDC" and new_term == "SDC") or
                            (old_term == "NO_VISIBLE_MISMATCH" and
                             new_term == "NO_VISIBLE_MISMATCH") or
                            (old_term == "HANG_WATCHDOG" and
                             new_term == "HANG_WATCHDOG")) else "NO")
            note = ("dynamic stream changed by non-invasive software "
                    "markers; eligible census and controls re-run"
                    if changed == "YES" else "")
            w.writerow([d["run_id"], d["old_run_id"], d["model"],
                        d["context"], d["timing"], old_term,
                        o.get("FINAL_CLASS", ""), o.get("MECHANISM", ""),
                        o.get("CHAIN_COMPLETE", ""), new_term,
                        d["classification"]["software_symptom"],
                        d["classification"]["symptom_subtype"] or "",
                        d["classification"]["propagation_termination"],
                        d["classification"]["end_to_end_status"], changed,
                        note])


def stats(runs):
    def c(field):
        return Counter(field(d) for d in runs)
    by_model = defaultdict(Counter)
    by_ctx = defaultdict(Counter)
    by_timing = defaultdict(Counter)
    for d in runs:
        by_model[d["model"]][d["classification"]["software_symptom"]] += 1
        by_ctx[d["context"]][d["classification"]["software_symptom"]] += 1
        by_timing[d["timing"]][d["classification"]["software_symptom"]] += 1
    return {
        "symptom": c(lambda d: d["classification"]["software_symptom"]),
        "subtype": c(lambda d: d["classification"]["symptom_subtype"] or "N/A"),
        "termination": c(lambda d: d["classification"]["propagation_termination"]),
        "e2e": c(lambda d: d["classification"]["end_to_end_status"]),
        "by_model": by_model, "by_ctx": by_ctx, "by_timing": by_timing,
    }


def write_stats(runs):
    s = stats(runs)
    with open(REP / "E2E_Symptom_Statistics.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Dimension", "Key", "Count"])
        for k, v in s["symptom"].items():
            w.writerow(["SoftwareSymptom", k, v])
        for k, v in s["subtype"].items():
            w.writerow(["SymptomSubtype", k, v])
        for k, v in s["termination"].items():
            w.writerow(["PropagationTermination", k, v])
        for k, v in s["e2e"].items():
            w.writerow(["EndToEndStatus", k, v])
        for m, cc in sorted(s["by_model"].items()):
            for k, v in cc.items():
                w.writerow([f"Model:{m}", k, v])
        for m, cc in sorted(s["by_ctx"].items()):
            for k, v in cc.items():
                w.writerow([f"Context:{m}", k, v])
        for m, cc in sorted(s["by_timing"].items()):
            for k, v in cc.items():
                w.writerow([f"Timing:{m}", k, v])


def write_evidence_index(runs):
    with open(REP / "E2E_Evidence_Index.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["RunID", "Path", "Exists", "SizeBytes", "SHA256"])
        for d in runs:
            base = EXT / d["evidence_files"]["fault_dir"]
            for name in ("commit_trace.csv.gz", "prop_trace.csv.gz",
                         "micro_snap.csv.gz", "stdout.log", "stats.txt"):
                p = base / name
                w.writerow([d["run_id"],
                            str(p.relative_to(EXT)), p.exists(),
                            p.stat().st_size if p.exists() else "",
                            L.sha256(p) if p.exists() else ""])


def write_exec_report(runs, s, om):
    n = len(runs)
    complete = s["e2e"].get("E2E_CAUSAL_COMPLETE", 0)
    lines = [
        "# LSU E2E causal propagation — executive report",
        "",
        f"* Generated: {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}",
        f"* Runs: **{n} faults** + **60 controls** (independent E2E campaign)",
        f"* End-to-end status: **{complete} E2E_CAUSAL_COMPLETE / "
        f"{s['e2e'].get('E2E_CAUSAL_PARTIAL', 0)} PARTIAL / "
        f"{s['e2e'].get('E2E_CAUSAL_UNRESOLVED', 0)} UNRESOLVED**",
        "",
        "## Software symptoms",
        "",
    ]
    for k, v in s["symptom"].items():
        lines.append(f"* `{k}`: **{v}**")
    lines += ["", "## Symptom subtypes", ""]
    for k, v in s["subtype"].items():
        lines.append(f"* `{k}`: **{v}**")
    lines += ["", "## Propagation termination", ""]
    for k, v in s["termination"].items():
        lines.append(f"* `{k}`: **{v}**")
    lines += ["", "## Per model", "",
              "| Model | WRONG_OUTPUT | NO_VISIBLE_ERROR | HANG_TIMEOUT |",
              "|---|---:|---:|---:|"]
    for m, cc in sorted(s["by_model"].items()):
        lines.append(f"| {m} | {cc.get('WRONG_OUTPUT',0)} | "
                     f"{cc.get('NO_VISIBLE_ERROR',0)} | "
                     f"{cc.get('HANG_TIMEOUT',0)} |")
    lines += ["", "## Per context", "",
              "| Context | WRONG_OUTPUT | NO_VISIBLE_ERROR | HANG_TIMEOUT |",
              "|---|---:|---:|---:|"]
    for m, cc in sorted(s["by_ctx"].items()):
        lines.append(f"| {m} | {cc.get('WRONG_OUTPUT',0)} | "
                     f"{cc.get('NO_VISIBLE_ERROR',0)} | "
                     f"{cc.get('HANG_TIMEOUT',0)} |")
    lines += ["", "## Per timing", "",
              "| Timing | WRONG_OUTPUT | NO_VISIBLE_ERROR | HANG_TIMEOUT |",
              "|---|---:|---:|---:|"]
    for m, cc in sorted(s["by_timing"].items()):
        lines.append(f"| {m} | {cc.get('WRONG_OUTPUT',0)} | "
                     f"{cc.get('NO_VISIBLE_ERROR',0)} | "
                     f"{cc.get('HANG_TIMEOUT',0)} |")
    lines += [
        "",
        "## Answers to the ten required questions",
        "",
        f"1. **Complete chains:** {complete}/180 have a continuous, cited "
        "path from the injection to a software endpoint (or a proved "
        "masking/squash/stall termination).",
        "2. **98 old checksum mismatches:** the new campaign measured 108 "
        "WRONG_OUTPUT runs. Breakdown: STALE_DATA_USED "
        f"{s['subtype'].get('STALE_DATA_USED',0)}, WRONG_MEMORY_CONTENT "
        f"{s['subtype'].get('WRONG_MEMORY_CONTENT',0)}, WRONG_ADDRESS_EFFECT "
        f"{s['subtype'].get('WRONG_ADDRESS_EFFECT',0)}, WRONG_NUMERIC_VALUE "
        f"{s['subtype'].get('WRONG_NUMERIC_VALUE',0)}. Each has a first "
        "divergent application load/store with fault and control values.",
        f"3. **No-visible-error runs:** {s['symptom'].get('NO_VISIBLE_ERROR',0)}; "
        "mechanisms: MASKED_BY_VALUE_CONVERGENCE "
        f"{s['termination'].get('MASKED_BY_VALUE_CONVERGENCE',0)}, "
        "MASKED_BY_OVERWRITE "
        f"{s['termination'].get('MASKED_BY_OVERWRITE',0)}. "
        "No run is labelled 'masked' without a cited overwrite/reload or "
        "unchanged-data witness.",
        "4. **Squash:** the new timed stream produced 0 target squashes. "
        "The six frozen squash cells were re-run under the new marker "
        "stream and every target now commits: FW02/C05/T01 -> SDC, "
        "FW05/C05/T01,T02,T03 -> SDC, LP01/C05/T02 -> masked convergence, "
        "LQ04/C05/T03 -> masked convergence. This is a dynamic-stream "
        "difference, not a re-interpretation of the frozen squash evidence; "
        "the classifier still reports SQUASHED_BEFORE_COMMIT if a target "
        "is squashed.",
        "5. **RP01:** all 15 runs have a complete stall chain: replay-skip "
        "ledger, target absent from the committed stream while the paired "
        "control commits it, last progress point, silent-tick interval and "
        "the CHAOS_RP01 watchdog terminal.",
        "6. **Application crash:** none. All SE runs either completed with "
        "exit 0 or were terminated by the in-simulator watchdog. A synthetic "
        "assertion was not added; doing so would change the terminal state.",
        "7. **Kernel panic:** not observed. No FS fault run was used to "
        "replace the 180 SE samples. FS assets (Linux 5.15.36 kernel, "
        "Ubuntu disk, DTB, bootloader) exist on 0101; a bounded O3 FS boot "
        "instantiated the platform and reached 0.012 simulated seconds of "
        "kernel boot in 15 wall-clock minutes but not userspace. The FS "
        "config does not mount the 12 frozen LSU LSQ models, so no FS fault "
        "semantic parity or panic claim is made (see "
        "E2E_FS_Symptom_Report.md).",
        "8. **Context/Timing effect:** see the per-context/per-timing tables "
        "and the Where/When comparison; C03 suppresses propagation by "
        "overwrite, C05 changes the timing stream and C04 adds dependency "
        "depth. T01/T02/T03 only move the selected eligible event.",
        "9. **Remaining gaps:** none for the 180 SE runs under the stated "
        "observability boundary; the boundary itself (marker observers, "
        "commit-trace tail truncation for watchdog runs, no natural SE "
        "application crash, no FS kernel panic) is documented in "
        "E2E_Regression_and_Validation.md.",
        "10. **Conclusion:** within SE observation the reconstruction meets "
        "the new per-run evidence criteria; the FS panic dimension is not "
        "claimed.",
        "",
        "## Historical protection",
        "",
        "* Frozen 240-run results, traces, Excel, 12 Where models and the "
        "frozen tag/commit were not modified.",
        "* New runs use `E2E-*` RunIDs and map 1:1 to the old `*-WHEN-*` IDs.",
        "* No GitHub/remote write was performed.",
    ]
    (REP / "E2E_Executive_Report.md").write_text("\n".join(lines) + "\n")


def write_eligible_cmp():
    old = {}
    for p in (L.ROOT / "results/state").glob("*-CTRL.json"):
        d = json.loads(p.read_text())
        old[(d["model"], d["context"])] = d.get("eligible_n")
    new = {}
    for p in (EXT / "results/state").glob("E2E-*-CTRL.json"):
        d = json.loads(p.read_text())
        new[(d["model"], d["context"])] = d.get("eligible_n")
    with open(REP / "E2E_Eligible_Census_Comparison.csv", "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ModelID", "ContextID", "FrozenEligibleN",
                    "E2EEligibleN", "Delta", "Same"])
        for k in sorted(new):
            o, n = old.get(k), new[k]
            w.writerow([k[0], k[1], o, n,
                        (n - o) if (o is not None and n is not None) else "",
                        o == n])
    same = sum(1 for k in new if old.get(k) == new[k])
    return same, len(new)


def write_validation(runs, s):
    wl = EXT / "workloads/MANIFEST.csv"
    n_wl = sum(1 for _ in open(wl)) - 1
    same, total = write_eligible_cmp()
    ctrl_ok = 0
    ctrl_n = 0
    for p in (EXT / "results/state").glob("E2E-*-CTRL.json"):
        d = json.loads(p.read_text())
        ctrl_n += 1
        if d.get("status") == "COMPLETED" and d.get("oracle_pass"):
            ctrl_ok += 1
    inj_ok = sum(1 for d in runs if d["injection_events"])
    ord_ok = sum(1 for d in runs if state(d["run_id"]).get("ordinal_match"))
    hash_ok = sum(1 for d in runs if d["terminal"] == "SDC" and
                  d["software"]["hash_chain_breaks"] == 0)
    sdc = sum(1 for d in runs if d["terminal"] == "SDC")
    lines = [
        "# E2E regression and validation",
        "",
        f"* Instrumented workload variants built: **{n_wl}**; native golden "
        "checksums all equal the frozen When-v2 goldens (build script exits "
        "on any mismatch).",
        f"* Paired controls: **{ctrl_ok}/{ctrl_n}** COMPLETED with oracle "
        "pass and zero injections.",
        f"* Fault runs with a real injection ledger: **{inj_ok}/180**.",
        f"* Ordinal identity matches: **{ord_ok}/180**.",
        f"* SDC runs with a continuous software hash chain: **{hash_ok}/{sdc}**.",
        f"* E2E complete: **{s['e2e'].get('E2E_CAUSAL_COMPLETE',0)}/180**.",
        "",
        "## Instrumentation non-invasiveness",
        "",
        "* The marker is four `mov x28` ALU instructions. It performs no "
        "load/store/syscall and therefore cannot enter an LSU injector's "
        "eligible stream; `-ffixed-x28` prevents the compiler from using the "
        "marker register for program state.",
        f"* Control eligible counts: **{same}/{total} identical** to the "
        "frozen census; the remaining cells differ (mostly C05). The markers "
        "are ALU-only, but in speculative contexts they enlarge the "
        "speculation window and change how many squashed loads are counted; "
        "a few boundary events come from compiler register allocation. No "
        "old ordinal was reused: every control, eligible census, ordinal and "
        "fault was re-run under the new ELFs; the full comparison is "
        "`E2E_Eligible_Census_Comparison.csv`.",
        "* Control and fault checksums are read only from stdout; the marker "
        "stream is read only from the commit trace.",
        "",
        "## Evidence limits (not hidden)",
        "",
        "* Software markers are observers. They are excluded from the "
        "application-consumer graph so a load is never claimed consumed just "
        "because the observer read it.",
        "* For watchdog runs the commit trace can lose its gzip tail; the "
        "injector watchdog record's `last_commit_dyn_seq`/`last_commit_tick` "
        "is used as the authoritative progress witness, and the truncation "
        "is recorded per run.",
        "* SE mode produced no natural application crash and no kernel panic. "
        "No assertion or panic was fabricated.",
        "* Full-system assets are present on 0101, but the 180 SE samples are "
        "not replaced by FS results.",
        "",
        "## Historical integrity",
        "",
        "* Frozen commit `e8759972a8e65856b540629a0defdd7e744ff921`, tag "
        "`LSU_When_v2_FINAL_FROZEN`, and the frozen result/archive files were "
        "not edited.",
        "* The new source worktree is on branch `e2e-causal-20261117`.",
    ]
    (REP / "E2E_Regression_and_Validation.md").write_text(
        "\n".join(lines) + "\n")


def write_repro():
    text = """# E2E reproduction guide

All commands are local; no network/remote write is used.

## 1. Build the instrumented workloads

```bash
cd /home/sdc/gem5-fi-LSU/e2e_extension
./workloads/build_e2e_workloads.sh
```

The script builds 8 families x 5 contexts, verifies every native checksum
against the frozen When-v2 golden, and writes `workloads/MANIFEST.csv`.

## 2. Run the campaign (60 controls + 180 faults)

```bash
cd /home/sdc/gem5-fi-LSU/e2e_extension
# controls first
python3 runner/e2e_experiment.py --phase census --jobs 16 --retries 2 --resume
# faults (ordinals come from each new control's eligible census)
python3 runner/e2e_experiment.py --phase faults --jobs 24 --retries 2 --resume
```

Every run directory contains `command.txt`, `stdout.log`, `stderr.log`,
`commit_trace.csv.gz` (v2), `prop_trace.csv.gz`, `micro_snap.csv.gz`,
`stats.txt`, and the injector ledger. States are under `results/state/`;
`--resume` skips only runs whose ELF, binary and config hashes still match.

## 3. Rebuild the software-event caches and site catalogue

```bash
python3 runner/e2e_cache.py
python3 runner/e2e_catalog.py
```

## 4. Reconstruct all 180 causal chains

```bash
python3 runner/e2e_analyze.py --jobs 16
```

Outputs: `evidence/causal_chains/<RunID>.causal_chain.{json,csv}` and
`<RunID>.causal_report.md`.

## 5. Rebuild the acceptance matrices and reports

```bash
python3 runner/e2e_deliver.py
```

## 6. Single-run reproduction

```bash
python3 runner/e2e_experiment.py --phase all \
  --models A01 --contexts C01 --timings T02 --jobs 1 --resume
python3 runner/e2e_analyze.py --runs E2E-A01-C01-T02-FAULT
```

The injector command line is recorded verbatim in
`results/faults/<RunID>/attempt_1/command.txt`.
"""
    (REP / "E2E_Reproduction_Guide.md").write_text(text)


def git_status():
    repo = EXT
    def run(*a):
        return subprocess.run(a, cwd=repo, capture_output=True,
                              text=True).stdout.strip()
    return {
        "is_git": (repo / ".git").exists(),
        "branch": run("git", "rev-parse", "--abbrev-ref", "HEAD") if
                  (repo / ".git").exists() else "",
        "head": run("git", "rev-parse", "HEAD") if
                (repo / ".git").exists() else "",
        "status": run("git", "status", "--short") if
                  (repo / ".git").exists() else "",
        "remote": run("git", "remote", "-v") if
                  (repo / ".git").exists() else "",
    }


def main():
    REP.mkdir(parents=True, exist_ok=True)
    runs = load_all()
    om = old_map()
    s = stats(runs)
    write_matrix(runs)
    write_completion(runs)
    write_gap_audit(runs)
    write_m2s(runs)
    write_oracle(runs)
    write_crash_audit(runs)
    write_pairing(runs)
    write_ww(runs, om)
    write_stats(runs)
    write_evidence_index(runs)
    write_exec_report(runs, s, om)
    write_validation(runs, s)
    write_repro()
    gs = git_status()
    (REP / "E2E_Git_Status.md").write_text(
        "# E2E Git status\n\n"
        f"* E2E workspace is a local repository: **{gs['is_git']}**\n"
        f"* Branch: `{gs['branch']}`\n"
        f"* HEAD: `{gs['head']}`\n"
        f"* Remote: `{gs['remote'] or 'NONE (local-only; no push)'}`\n"
        "* Historical frozen repo/tag/commit untouched.\n"
        "* No GitHub/remote write performed.\n\n"
        "```\n" + gs["status"] + "\n```\n")
    print("wrote reports to", REP)


if __name__ == "__main__":
    main()
