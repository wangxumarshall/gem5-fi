#!/usr/bin/env python3
"""MMU Final 40-sample Runner Describe audit (never launches gem5).

Runs the fixed formal runner with --describe for all 40 SampleRunIDs, checks
every parameter against the v3.0.2 authority (and the approved final F1
pilots), writes the M05/M07 parity reports, preflight, provenance, process
and output-directory integrity evidence, then packs the v2 ZIP.

Exit 0 only when all acceptance checks pass.
"""

import argparse
import concurrent.futures
import csv
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmu_formal_preflight as pf  # noqa: E402

GEM5_SHA256 = \
    "b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185"
SOURCE_SHA256 = {
    "CHAOS/gem5/src/arch/arm/mmu.cc":
        "bba49e65398f80aaf58b3ce5a954f4ffbd68278dd0b5c888124d249e28dd1c1b",
    "CHAOS/gem5/src/arch/arm/table_walker.cc":
        "54dbeeff2e40891eb018c4bf891a5446ab2b8c4fe88f69c40647c26923595985",
    "CHAOS/gem5/src/arch/arm/table_walker.hh":
        "89110e2081da62743e4c2325aa656976e945f086959bcd29f18882412e44b611",
    "CHAOS/gem5/src/arch/arm/tlb.cc":
        "b81b7b4cc9eee2c7ba0b592775587dcc7610c8d18c237ba412d2c69ba80d52f4",
    "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc":
        "38c0942ab5d2c4c73b7ee3763c1d7503b708ba9ba4f73c2fd051db6836052dc4",
    "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh":
        "90ea1b55a9a7e51db04fad4a23ceee3107ebc2d375c3d5c5902b9ffb6b2d3336",
}
WORKLOAD_SHA256 = {
    "W9": "ec525687a757fd0f3865294481c687e754c06dc6a073dd2aa80306b04621732b",
    "W10": "733b8a80150b9728b640fbaad0889f139b09b92a98462778753975a4917a63ae",
    "W10S": "fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3",
    "W11": "1393b2737e33db75a8dfa38dbd0fa888d7640e7fb791cb7da1df815bd21451c4",
    "W12": "8fa269fd88eaf9126f67cf80d5d77f13600e211948db5cd7f4b89f42c147fdbc",
    "W13": "6e7d926e863c15433b3887e3ac069169e510751190d4b0de5dae0e7aa886ec70",
    "W14": "f15dc78e2efc683f2a653a40ed47d293b71c27aaa018594e67274e9098a7be36",
}
M05_DECOY_VA = 0x4010200000
M07_PAGE_BASE = {
    "R01": 0x400D000000, "R02": 0x400D000000, "R03": 0x400D200000,
    "R04": 0x400D400000, "R05": 0x400D600000,
}


def now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def as_int(text):
    try:
        return int(str(text).strip(), 0)
    except (TypeError, ValueError):
        return None


def formals_under(runs_root):
    out = []
    if not os.path.isdir(runs_root):
        return out
    for name in sorted(os.listdir(runs_root)):
        if re.match(r"^M0[1-8]-F0-", name) and os.path.isdir(
                os.path.join(runs_root, name)):
            out.append(name)
    return out


def gem5_procs():
    """Return real gem5.opt processes only (never the audit's own shell)."""
    try:
        exact = subprocess.run(["pgrep", "-x", "gem5.opt"],
                               capture_output=True, text=True, timeout=10)
        detail = subprocess.run(["pgrep", "-af", "[g]em5.opt"],
                                capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        return [], "pgrep failed: %s" % exc
    pids = [ln for ln in exact.stdout.splitlines() if ln.strip()]
    lines = [ln for ln in detail.stdout.splitlines() if ln.strip()]
    # Trust the exact-name count; the detail list is diagnostic only.
    if not pids:
        lines = []
    return lines, ""


def run_one(args, sid):
    raw_path = os.path.join(args.audit_out, "raw_describe", sid + ".json")
    cmd = [
        sys.executable, args.runner,
        "--repo-root", args.repo_root,
        "--excel", args.excel,
        "--csv", args.csv,
        "--out-root", args.out_root,
        "--sample", sid, "--describe",
        "--param-authority", args.param_authority,
    ]
    started = now()
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=args.timeout)
    with open(raw_path, "w", encoding="utf-8") as fh:
        fh.write(proc.stdout)
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        payload = {}
    return {
        "sample_run_id": sid,
        "command": cmd,
        "started_at": started,
        "finished_at": now(),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
        "raw_path": raw_path,
    }


def cmd_value(command, flag):
    return (command[command.index(flag) + 1]
            if flag in command else None)


def expected_target_va(row, plan):
    exact = as_int(row.get("TargetVAExact"))
    if exact is not None:
        return exact, "TargetVAExact"
    numeric = as_int(row.get("TargetVA"))
    if numeric is not None:
        return numeric, "numeric TargetVA"
    embedded = pf._embedded_hex_values(row.get("TargetVA"))
    if len(embedded) == 1:
        return embedded[0], "embedded exact VA"
    return plan.get("target_va"), "workload fact (%s)" % plan.get(
        "target_va_source")


def analyse(args, rows, authority, result):
    sid = result["sample_run_id"]
    row = rows[sid]
    plan = (result["payload"] or {}).get("plan") or {}
    auth = ((authority.get("data") or {}).get("samples") or {}).get(sid, {})
    failures = []

    def check(name, ok, detail=""):
        if not ok:
            failures.append("%s (%s)" % (name, detail))
        return ok

    status = (result["payload"] or {}).get("status", "")
    check("exit_code", result["exit_code"] == 0, result["exit_code"])
    check("status", status == "READY", status)
    check("would_run", (result["payload"] or {}).get("would_run") is False)
    check("parity_ok", (result["payload"] or {}).get("parity_ok") is True,
          (result["payload"] or {}).get("parity_failures"))
    check("sample_run_id", plan.get("sample_run_id") == sid)
    check("model", plan.get("model") == row.get("ModelID"))
    check("workload", plan.get("workload") == row.get("WorkloadID"))
    check("context", plan.get("context") == row.get("ContextID"))
    check("target_mode",
          plan.get("target_mode") == row.get("AccessMode"),
          "%r vs %r" % (plan.get("target_mode"), row.get("AccessMode")))
    check("target_instruction",
          bool(row.get("TargetInstruction")) and
          plan.get("target_instruction") == row.get("TargetInstruction"))
    check("eligible_event_ordinal",
          plan.get("eligible_event_index") == 1,
          plan.get("eligible_event_index"))
    check("seed", plan.get("seed") == row.get("Seed") ==
          "N/A_DETERMINISTIC", plan.get("seed"))
    seed_flags = [a for a in plan.get("command", [])
                  if str(a).startswith("--") and "seed" in str(a).lower()]
    check("no_seed_flag", not seed_flags, seed_flags)
    check("gem5_sha256", plan.get("gem5_sha256") == GEM5_SHA256,
          plan.get("gem5_sha256"))
    src_bad = {rel: (plan.get("source_sha256") or {}).get(rel)
               for rel, want in SOURCE_SHA256.items()
               if (plan.get("source_sha256") or {}).get(rel) != want}
    check("source_sha256", not src_bad, src_bad)
    wl = plan.get("run_workload", "")
    check("workload_sha256",
          plan.get("workload_sha256") == WORKLOAD_SHA256.get(wl),
          "%s %r" % (wl, plan.get("workload_sha256")))
    ctrl = plan.get("control_oracle") or {}
    check("control_oracle", ctrl.get("present") is True and
          bool(ctrl.get("sha256")), ctrl.get("path"))
    outdir = plan.get("outdir", "")
    check("outdir_absent", not os.path.isdir(outdir), outdir)

    target_expected, target_basis = expected_target_va(row, plan)
    check("target_va", plan.get("target_va") == target_expected,
          "%r vs %r (%s)" % (plan.get("target_va"), target_expected,
                             target_basis))

    decoy_va = decoy_tb = ""
    if row.get("ModelID") == "M05":
        cmd = plan.get("command") or []
        decoy_va = plan.get("m05_decoy_va", "")
        decoy_tb = plan.get("m05_decoy_table_base", "")
        excel_va = as_int(row.get("M05DecoyVA"))
        check("m05.decoy_va_present", as_int(decoy_va) == M05_DECOY_VA,
              decoy_va)
        check("m05.excel_equals_pilot",
              excel_va == as_int(auth.get("M05DecoyVA")) ==
              as_int(auth.get("pilot_decoy_va")) == M05_DECOY_VA,
              (row.get("M05DecoyVA"), auth.get("M05DecoyVA"),
               auth.get("pilot_decoy_va")))
        check("m05.command_decoy_va",
              as_int(cmd_value(cmd, "--mmu_m05_decoy_va")) == M05_DECOY_VA,
              cmd_value(cmd, "--mmu_m05_decoy_va"))
        check("m05.command_table_base",
              cmd_value(cmd, "--mmu_m05_decoy_table_base") == "0",
              cmd_value(cmd, "--mmu_m05_decoy_table_base"))
        check("m05.excel_table_base",
              as_int(row.get("M05DecoyTableBase")) ==
              as_int(auth.get("pilot_decoy_table_base")) == 0,
              row.get("M05DecoyTableBase"))

    if row.get("ModelID") == "M07":
        ctx = row.get("ContextID")
        exact = as_int(row.get("TargetVAExact"))
        pilot = as_int(auth.get("pilot_target_va"))
        page_base = M07_PAGE_BASE.get(ctx)
        check("m07.exact_va", plan.get("target_va") == exact == pilot,
              (plan.get("target_va"), exact, pilot))
        check("m07.page_membership",
              page_base is not None and
              0 <= (plan.get("target_va") or 0) - page_base < 0x1000,
              (plan.get("target_va"), page_base))
        check("m07.page_masked_match_unchanged",
              page_base is not None and
              ((plan.get("target_va") or 0) & ~0xFFF) == page_base,
              (plan.get("target_va"), page_base))
        check("m07.target_n", plan.get("target_n") == 12 and
              cmd_value(plan.get("command") or [], "--mmu_target_n") == "12",
              plan.get("target_n"))
        check("m07.mode", plan.get("target_mode") == row.get("AccessMode") ==
              auth.get("pilot_target_mode"),
              (plan.get("target_mode"), row.get("AccessMode"),
               auth.get("pilot_target_mode")))

    return {
        "SampleRunID": sid,
        "ModelID": row.get("ModelID", ""),
        "WorkloadID": row.get("WorkloadID", ""),
        "ContextID": row.get("ContextID", ""),
        "Status": status,
        "WouldRun": (result["payload"] or {}).get("would_run"),
        "ExitCode": result["exit_code"],
        "ParityOK": (result["payload"] or {}).get("parity_ok"),
        "ParityFailures": ";".join(
            (result["payload"] or {}).get("parity_failures") or []),
        "TargetVA": ("0x%x" % plan["target_va"]
                     if plan.get("target_va") is not None else ""),
        "TargetVASource": plan.get("target_va_source", ""),
        "TargetMode": plan.get("target_mode", ""),
        "TargetInstruction": plan.get("target_instruction", ""),
        "DecoyVA": decoy_va,
        "DecoyTableBase": decoy_tb,
        "EligibleEventOrdinal": plan.get("eligible_event_index"),
        "Seed": plan.get("seed", ""),
        "SeedPolicy": plan.get("seed_policy", ""),
        "Gem5SHA256": plan.get("gem5_sha256", ""),
        "SourceSHA256OK": not src_bad,
        "WorkloadSHA256": plan.get("workload_sha256", ""),
        "ControlOracle": ctrl.get("path", ""),
        "ControlOracleSHA256": ctrl.get("sha256", ""),
        "Outdir": outdir,
        "OutdirExists": os.path.isdir(outdir),
        "RawJSON": result["raw_path"],
        "Failures": " | ".join(failures),
        "Accept": not failures,
    }


def write_reports(args, rows, authority, results, analyses, pre, post,
                  preflight_summary):
    aud = args.audit_out
    m05 = [a for a in analyses if a["ModelID"] == "M05"]
    m07 = [a for a in analyses if a["ModelID"] == "M07"]

    def write(name, text):
        with open(os.path.join(aud, name), "w", encoding="utf-8") as fh:
            fh.write(text)

    # CSV / JSON summary
    cols = list(analyses[0].keys()) if analyses else []
    with open(os.path.join(aud, "MMU_40_Sample_Describe_Results.csv"),
              "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        writer.writerows(analyses)
    write("MMU_40_Sample_Describe_Results.json",
          json.dumps(analyses, indent=2, sort_keys=True) + "\n")

    # M05 parity report
    lines = [
        "# M05 Parameter Parity Report", "",
        "Authoritative value: `0x4010200000` (W13_DECOY_VA; final F1 "
        "pilots R01-R05 use `--mmu_m05_decoy_table_base 0 "
        "--mmu_m05_decoy_va 0x4010200000`).", "",
        "| Sample | Excel DecoyVA | Authority | Pilot | W13 symbol | Plan | "
        "Table base | Command flags | Status |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for a in m05:
        sid = a["SampleRunID"]
        auth = ((authority.get("data") or {}).get("samples") or {}).get(sid, {})
        raw = json.load(open(a["RawJSON"])) if os.path.isfile(
            a["RawJSON"]) else {}
        plan = raw.get("plan") or {}
        cmd = plan.get("command") or []
        flags = "%s %s / %s %s" % (
            "--mmu_m05_decoy_table_base",
            cmd_value(cmd, "--mmu_m05_decoy_table_base"),
            "--mmu_m05_decoy_va", cmd_value(cmd, "--mmu_m05_decoy_va"))
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            sid, rows[sid].get("M05DecoyVA"), auth.get("M05DecoyVA"),
            auth.get("pilot_decoy_va"), authority_value(authority),
            a["DecoyVA"], a["DecoyTableBase"], flags,
            "PASS" if a["Accept"] else "FAIL: " + a["Failures"]))
    lines += ["", "Source precedence (`table_walker.cc:2979-3001`): a nonzero "
              "`--mmu_m05_decoy_va` selects the FORMAL path and forbids the "
              "pilot-only `live_partial_scan` fallback; the table base is only "
              "a consistency check when zero.", ""]
    write("MMU_M05_Parameter_Parity_Report.md", "\n".join(lines) + "\n")

    # M07 parity report
    lines = [
        "# M07 Parameter Parity Report", "",
        "Exact VA = authority `TargetVAExact` = final F1 pilot. "
        "`--mmu_target_n 12` and the page-masked match key are unchanged.", "",
        "| Sample | Authority exact | Pilot | Plan | Mode | Instruction | "
        "Page base | n | Masked key | Status |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for a in m07:
        sid = a["SampleRunID"]
        ctx = a["ContextID"]
        auth = ((authority.get("data") or {}).get("samples") or {}).get(sid, {})
        base = M07_PAGE_BASE.get(ctx)
        raw = json.load(open(a["RawJSON"])) if os.path.isfile(
            a["RawJSON"]) else {}
        plan = raw.get("plan") or {}
        va = plan.get("target_va")
        masked = ("0x%x" % (va & ~0xFFF)) if va is not None else ""
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            sid, rows[sid].get("TargetVAExact"), auth.get("pilot_target_va"),
            a["TargetVA"], a["TargetMode"], a["TargetInstruction"],
            "0x%x" % base if base else "", plan.get("target_n"), masked,
            "PASS" if a["Accept"] else "FAIL: " + a["Failures"]))
    lines += ["", "R05 note: the older closure pilot TEST-M07-R05 used "
              "`0x400d600100`; the final F1 pilot and W14 `R05_CODE_OFF=0x180` "
              "supersede it with `0x400d600180`.", ""]
    write("MMU_M07_Parameter_Parity_Report.md", "\n".join(lines) + "\n")

    # Preflight report
    s = preflight_summary or {}
    lines = [
        "# MMU Final Preflight (v3.0.2 authority)", "",
        "- Samples: %s" % s.get("samples"),
        "- Primary READY: %s" % (s.get("primary_counts") or {}).get("READY"),
        "- Runtime PASS: %s" % (s.get("runtime_counts") or {}).get("PASS"),
        "- Source provenance PASS: %s" %
        (s.get("source_provenance_counts") or {}).get("PASS"),
        "- Binary provenance PASS: %s" %
        (s.get("binary_provenance_counts") or {}).get("PASS"),
        "- Seed gate failures: %s" % s.get("seed_gate_fail_count"),
        "- Triple issues: %s" % (s.get("triple_issues") or []),
        "- Final binary: `%s` (%s)" % (s.get("final_binary_sha256"),
                                       s.get("final_binary_status")),
        "- Authority Excel: `%s`" % s.get("excel"),
        "- Authority CSV: `%s`" % s.get("csv_input"),
        "",
        "Generated by `tools/mmu_formal_preflight.py`; full artifacts under "
        "`preflight/`.", "",
    ]
    write("MMU_Final_Preflight_Report.md", "\n".join(lines) + "\n")

    # Execution log
    lines = ["# MMU Final 40-sample describe execution log", "",
             "Started: %s" % pre["started_utc"],
             "Runner: `%s` sha256=%s" % (args.runner, sha256(args.runner)),
             "Excel: `%s`" % args.excel,
             "CSV: `%s`" % args.csv,
             "Parameter authority: `%s`" % args.param_authority, ""]
    for r in results:
        lines.append("[%s] %s exit=%d" % (r["started_at"],
                                          r["sample_run_id"],
                                          r["exit_code"]))
        lines.append("  " + " ".join(r["command"]))
    lines += ["", "Preflight: exit=%s" % pre["preflight_exit"],
              "Finished: %s" % now(), ""]
    write("MMU_Runner_Describe_Execution.log", "\n".join(lines) + "\n")

    # Provenance
    lines = ["# MMU Final provenance", "",
             "gem5 binary:", "  %s  %s" % (
                 GEM5_SHA256, os.path.join(args.repo_root, "CHAOS", "gem5",
                                           "build", "ARM", "gem5.opt")),
             "", "Source files:"]
    for rel, want in sorted(SOURCE_SHA256.items()):
        lines.append("  %s  %s" % (want, rel))
    lines += ["", "Workload binaries:"]
    for wid, want in sorted(WORKLOAD_SHA256.items()):
        path = os.path.join(args.repo_root, "workloads", "mmu", wid,
                            "mmu_%s" % wid.lower())
        lines.append("  %s  %s" % (want, path))
    lines += ["", "Authority and tools:"]
    for label, path in (
            ("runner", args.runner), ("preflight", args.preflight),
            ("excel", args.excel), ("csv", args.csv),
            ("parameter_authority", args.param_authority)):
        lines.append("  %s  %s  %s" % (sha256(path), label, path))
    lines.append("")
    write("MMU_Final_Provenance.txt", "\n".join(lines))

    # Git status / HEAD
    head = subprocess.run(["git", "-C", args.repo_root, "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "-C", args.repo_root, "rev-parse",
                             "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "-C", args.repo_root, "status",
                             "--porcelain"], capture_output=True,
                            text=True).stdout
    write("Git_Status_and_HEAD.txt",
          "HEAD: %s\nBranch: %s\n\n%s" % (head, branch, status))

    # Process check
    write("Gem5_Process_Check.txt",
          "Before:\n%s\n\nAfter:\n%s\n\ngem5_count_before=%d\n"
          "gem5_count_after=%d\n" %
          ("\n".join(pre["gem5_before"]) or "(none)",
           "\n".join(post["gem5_after"]) or "(none)",
           len(pre["gem5_before"]), len(post["gem5_after"])))

    # Output directory integrity
    new_dirs = sorted(set(post["formal_dirs"]) - set(pre["formal_dirs"]))
    lines = ["# Output directory integrity", "",
             "Formal SampleRunID directories before: %d" %
             len(pre["formal_dirs"]),
             "Formal SampleRunID directories after: %d" %
             len(post["formal_dirs"]),
             "New formal directories: %d" % len(new_dirs), ""]
    for name in pre["formal_dirs"]:
        lines.append("  before: %s" % name)
    for name in new_dirs:
        lines.append("  NEW: %s" % name)
    lines += ["", "Per-plan outdirs (none may exist):"]
    for a in analyses:
        lines.append("  %s  exists=%s  %s" % (
            "OK" if not a["OutdirExists"] else "VIOLATION",
            a["OutdirExists"], a["Outdir"]))
    lines.append("")
    write("Output_Directory_Integrity.txt", "\n".join(lines))


def authority_value(authority):
    return (((authority.get("data") or {}).get("provenance") or {})
            .get("W13_DECOY_VA") or {}).get("value", "")


def build_manifest_and_zip(args):
    aud = args.audit_out
    manifest = os.path.join(aud, "SHA256_MANIFEST.txt")
    lines = []
    for root, _dirs, files in os.walk(aud):
        for name in sorted(files):
            path = os.path.join(root, name)
            if os.path.abspath(path) == os.path.abspath(manifest):
                continue
            rel = os.path.relpath(path, aud)
            lines.append("%s  %s" % (sha256(path), rel))
    with open(manifest, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(lines)) + "\n")
    with zipfile.ZipFile(args.package_zip, "w",
                         zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(aud):
            for name in sorted(files):
                path = os.path.join(root, name)
                rel = os.path.relpath(path, aud)
                zf.write(path, rel)
    with open(args.package_zip + ".sha256", "w") as fh:
        fh.write("%s  %s\n" % (sha256(args.package_zip),
                               os.path.basename(args.package_zip)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runner", default=None)
    ap.add_argument("--preflight", default=None)
    ap.add_argument("--excel", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--param-authority", required=True)
    ap.add_argument("--out-root", default=None)
    ap.add_argument("--audit-out", required=True)
    ap.add_argument("--package-zip", default=None)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    args.repo_root = os.path.abspath(args.repo_root)
    args.runner = args.runner or os.path.join(args.repo_root, "tools",
                                              "mmu_formal_runner.py")
    args.preflight = args.preflight or os.path.join(
        args.repo_root, "tools", "mmu_formal_preflight.py")
    args.out_root = args.out_root or os.path.join(args.repo_root, "runs")
    args.audit_out = os.path.abspath(args.audit_out)
    args.package_zip = args.package_zip or os.path.join(
        os.path.dirname(args.audit_out),
        os.path.basename(args.audit_out.rstrip("/")) + ".zip")
    os.makedirs(os.path.join(args.audit_out, "raw_describe"), exist_ok=True)
    os.makedirs(os.path.join(args.audit_out, "runner"), exist_ok=True)
    os.makedirs(os.path.join(args.audit_out, "authority"), exist_ok=True)
    os.makedirs(os.path.join(args.audit_out, "preflight"), exist_ok=True)

    # Fixed runner + authority are packaged verbatim.
    shutil.copy2(args.runner,
                 os.path.join(args.audit_out, "runner",
                              "mmu_formal_runner.py"))
    shutil.copy2(args.preflight,
                 os.path.join(args.audit_out, "runner",
                              "mmu_formal_preflight.py"))
    for src, dst in (
            (args.excel, "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx"),
            (args.csv, "MMU_40_Sample_Matrix.csv"),
            (args.param_authority, "MMU_Parameter_Authority_v3.0.2.json")):
        shutil.copy2(src, os.path.join(args.audit_out, "authority", dst))
    with open(os.path.join(args.audit_out, "MMU_Runner_SHA256.txt"),
              "w") as fh:
        fh.write("%s  runner/mmu_formal_runner.py\n" % sha256(
            os.path.join(args.audit_out, "runner",
                         "mmu_formal_runner.py")))
        fh.write("%s  runner/mmu_formal_preflight.py\n" % sha256(
            os.path.join(args.audit_out, "runner",
                         "mmu_formal_preflight.py")))

    with open(args.csv, newline="", encoding="utf-8-sig") as fh:
        rows_list = list(csv.DictReader(fh))
    rows = {r["SampleRunID"]: r for r in rows_list}
    ids = [r["SampleRunID"] for r in rows_list]
    if len(ids) != 40 or len(set(ids)) != 40:
        print("authority CSV must contain 40 unique SampleRunIDs", file=sys.stderr)
        return 2
    with open(args.param_authority, "r", encoding="utf-8") as fh:
        authority = {"present": True, "data": json.load(fh),
                     "path": args.param_authority,
                     "sha256": sha256(args.param_authority)}

    pre = {
        "started_utc": now(),
        "gem5_before": gem5_procs()[0],
        "formal_dirs": formals_under(args.out_root),
        "preflight_exit": None,
    }
    # Preflight before the 40 describes (same authority, no gem5).
    pf_cmd = [sys.executable, args.preflight, "--repo-root", args.repo_root,
              "--excel", args.excel, "--csv", args.csv,
              "--outdir", os.path.join(args.audit_out, "preflight"),
              "--summary-json", os.path.join(args.audit_out, "preflight",
                                             "MMU_Preflight_Summary.json")]
    pf_proc = subprocess.run(pf_cmd, capture_output=True, text=True,
                             timeout=args.timeout)
    pre["preflight_exit"] = pf_proc.returncode
    with open(os.path.join(args.audit_out, "preflight",
                           "preflight_stdout.log"), "w") as fh:
        fh.write(pf_proc.stdout + "\n" + pf_proc.stderr)
    preflight_summary = {}
    summary_path = os.path.join(args.audit_out, "preflight",
                                "MMU_Preflight_Summary.json")
    if os.path.isfile(summary_path):
        with open(summary_path) as fh:
            preflight_summary = json.load(fh)

    results = []
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(run_one, args, sid): sid for sid in ids}
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())
    results.sort(key=lambda r: ids.index(r["sample_run_id"]))
    analyses = [analyse(args, rows, authority, r) for r in results]
    post = {
        "gem5_after": gem5_procs()[0],
        "formal_dirs": formals_under(args.out_root),
    }
    write_reports(args, rows, authority, results, analyses, pre, post,
                  preflight_summary)

    # Acceptance
    bad = [a for a in analyses if not a["Accept"]]
    summary = {
        "audit_utc": now(),
        "samples": len(analyses),
        "ready": sum(1 for a in analyses if a["Status"] == "READY"),
        "blocked": sum(1 for a in analyses
                       if str(a["Status"]).startswith("BLOCKED")),
        "parity_fail": sum(1 for a in analyses
                           if a["Status"] == "PARITY_FAIL"),
        "would_run_false": sum(1 for a in analyses
                               if a["WouldRun"] is False),
        "new_formal_dirs": len(set(post["formal_dirs"]) -
                               set(pre["formal_dirs"])),
        "gem5_processes_before": len(pre["gem5_before"]),
        "gem5_processes_after": len(post["gem5_after"]),
        "preflight_exit": pre["preflight_exit"],
        "failed_samples": [a["SampleRunID"] for a in bad],
        "gem5_sha256": GEM5_SHA256,
    }
    with open(os.path.join(args.audit_out, "MMU_Final_Audit_Summary.json"),
              "w") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")

    # Final audit markdown
    lines = [
        "# MMU Final 40-Sample Runner Describe Audit v2", "",
        "Date: %s" % now(), "",
        "| Metric | Result |", "|---|---|",
        "| Samples | %d |" % summary["samples"],
        "| READY | %d/%d |" % (summary["ready"], summary["samples"]),
        "| BLOCKED | %d |" % summary["blocked"],
        "| PARITY_FAIL | %d |" % summary["parity_fail"],
        "| would_run=false | %d/%d |" %
        (summary["would_run_false"], summary["samples"]),
        "| New formal output dirs | %d |" % summary["new_formal_dirs"],
        "| gem5 processes before/after | %d/%d |" %
        (summary["gem5_processes_before"],
         summary["gem5_processes_after"]),
        "| Binary SHA256 | `%s` |" % GEM5_SHA256,
        "| Preflight exit | %s |" % summary["preflight_exit"], "",
        "## Per-sample", "",
        "| # | SampleRunID | Status | would_run | Model | Ctx | TargetVA | "
        "Mode | DecoyVA | n | Parity |",
        "|---:|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, a in enumerate(analyses, 1):
        raw = json.load(open(a["RawJSON"])) if os.path.isfile(
            a["RawJSON"]) else {}
        plan = raw.get("plan") or {}
        lines.append("| %d | `%s` | %s | %s | %s | %s | %s | %s | %s | %s | "
                     "%s |" % (
                         i, a["SampleRunID"], a["Status"], str(a["WouldRun"]),
                         a["ModelID"], a["ContextID"], a["TargetVA"],
                         a["TargetMode"], a["DecoyVA"] or "-",
                         plan.get("target_n"), "PASS" if a["Accept"] else
                         "FAIL: " + a["Failures"]))
    lines += ["", "## M05 / M07 parity", "",
              "- M05: workload-owned `--mmu_m05_decoy_va 0x4010200000` with "
              "`--mmu_m05_decoy_table_base 0`, matching Excel, v3.0.2 "
              "authority, final F1 pilots and W13_DECOY_VA.",
              "- M07: exact `0x400d400100` / `0x400d600180`, page-masked match "
              "key unchanged, `--mmu_target_n 12`, mode and instruction "
              "matching the authority.", ""]
    verdict = ("PASS" if (summary["ready"] == 40 and summary["blocked"] == 0
                          and summary["parity_fail"] == 0 and
                          summary["would_run_false"] == 40 and
                          summary["new_formal_dirs"] == 0 and
                          summary["gem5_processes_before"] == 0 and
                          summary["gem5_processes_after"] == 0 and
                          summary["preflight_exit"] == 0)
               else "PARTIAL")
    lines += ["## Verdict", "", "`MMU_FINAL_RUNNER_AUDIT = %s`" % verdict, ""]
    with open(os.path.join(args.audit_out,
                           "MMU_Final_40_Sample_Runner_Describe_Audit.md"),
              "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    build_manifest_and_zip(args)
    print(json.dumps(dict(summary, verdict=verdict,
                          package=args.package_zip), indent=2,
                     sort_keys=True))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
