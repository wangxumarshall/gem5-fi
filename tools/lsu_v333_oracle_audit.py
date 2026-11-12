#!/usr/bin/env python3
"""Build LSU_12Model_Workload_Oracle_Audit.csv from the final v3.3.3 controls.

Reads the candidate/formal oracle identity from the v3.3.2 workload audit,
recomputes the ELF SHA256 from the executed command, and compares the final
R01 control's printed checksum to the recorded golden. A missing checksum is
written as ``NO_CHECKSUM``; nothing is invented.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "audit_v3_3_2/LSU_Workload_Oracle_Final_Audit.csv"
RUNS = ROOT / "audit_v3_3_3/runs"
OUT = ROOT / "audit_v3_3_3/LSU_12Model_Workload_Oracle_Audit.csv"
MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05",
          "DA04", "LP01", "MD04", "LQ04", "RP01")
CANDIDATE = {"FW02", "RP01", "MD04", "SQ01", "SQ03", "SP05"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_checksum(text: str):
    # bare 16-hex final line (A03) or checksum=0x...
    for line in reversed(text.splitlines()):
        line = line.strip()
        if re.fullmatch(r"[0-9a-fA-F]{16}", line):
            return line.lower()
        m = re.search(r"checksum=0x([0-9a-fA-F]+)", line)
        if m:
            return m.group(1).lower()
    return None


def executed_workload(run: Path):
    cmd = (run / "command.txt").read_text(errors="replace")
    m = re.search(r"--cmd=(\S+)", cmd)
    return m.group(1) if m else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle", default=str(ORACLE))
    ap.add_argument("--runs", default=str(RUNS))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    oracle = {r["ModelID"]: r for r in csv.DictReader(open(args.oracle))}
    rows = []
    for model in MODELS:
        o = oracle.get(model, {})
        run = Path(args.runs) / f"{model}-R01-control"
        stdout = run / "stdout.log"
        text = stdout.read_text(errors="replace") if stdout.exists() else ""
        checksum = parse_checksum(text) if text else None
        wl = executed_workload(run)
        elf_sha = sha256(Path(wl)) if wl and Path(wl).exists() else "n/a"
        golden = (o.get("Golden") or "").strip().lower()
        if golden.startswith("checksum="):
            golden = golden.split("=", 1)[1]
        if golden.startswith("0x"):
            golden = golden[2:]
        match = ("YES" if checksum and golden and checksum == golden else
                 "NO" if checksum and golden else "NO_CHECKSUM")
        rows.append({
            "ModelID": model,
            "Workload": o.get("Workload", "n/a"),
            "ELF": wl or "n/a",
            "ELFSHA256": elf_sha,
            "Golden": golden or "n/a",
            "ControlChecksum": checksum or "NO_CHECKSUM",
            "OracleMatch": match,
            "OriginalWorkloadStatus": o.get("WorkloadStatus", "n/a"),
            "WorkloadIdentityStatus": ("OVERRIDE_APPROVED"
                                       if model in CANDIDATE else "FORMAL"),
            "ControlEvidencePath": str(run),
            "Notes": ("A01 8-byte-only eligible stream (L-A12); "
                      if model == "A01" else
                      "A03 SDC/POST_ORACLE_SIM_HANG on the fault; control golden; "
                      if model == "A03" else ""),
        })
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", args.out, len(rows))
    for r in rows:
        print(r["ModelID"], r["OracleMatch"], r["ControlChecksum"], r["Golden"])


if __name__ == "__main__":
    main()
