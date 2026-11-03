#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_w6_golden.py — generate / verify the W6 native golden arrays.

For each of the three fixed components (svd → fft → sparse-cg) the tool runs
the NATIVE binary three times with --array-dump, then requires:

  * rc == 0 for every run;
  * the 16-hex FINAL value identical across the three runs;
  * the dumped bytes byte-identical across the three runs;
  * the dump length exactly count * element_size for the pre-registered meta;
  * the pre-registered element oracle reports EXACT_MATCH against the dump.

Only then is `golden/<program>.bin` written (never overwrite a different
existing golden unless --force-golden). `golden/manifest.json` records the
three native SHAs and FINAL values. `--update-suite` backfills the real
source/binary/golden SHA-256 + FINAL + suite_hash into the suite JSON.

This tool never runs gem5 and never writes runs/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_w6_oracle as WO  # noqa: E402
import fsu_w6_suite as WS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = ROOT / "configs/fsu/suites/w6-fp-v1.json"
# FINAL is either a standalone 16-hex line (svd) or "FINAL=<16hex>" (fft /
# sparse-cg). Anchoring at line start deliberately excludes the ARRAY_DUMP
# line, whose trailing "fnv1a=<16hex>" hashes a DIFFERENT domain for svd.
_FINAL_RE = re.compile(r"^(?:FINAL=)?([0-9a-fA-F]{16})\s*$", re.MULTILINE)
_RESIDUAL_RE = re.compile(r"RESIDUAL=(\S+)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_final(text: str):
    found = _FINAL_RE.findall(text)
    return found[-1].lower() if found else None


def resolve(path, root: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(root) / p


def run_binary(binary: Path, dump: Path, timeout: int, cwd: Path):
    r = subprocess.run([str(binary), f"--array-dump={dump}"],
                       capture_output=True, text=True, errors="replace",
                       timeout=timeout, cwd=str(cwd))
    return r.returncode, r.stdout or "", r.stderr or ""


def generate(suite_path: Path, root: Path, reps: int, timeout: int,
             force_golden: bool, update_suite: bool, keep_reps: bool = False):
    suite_path = Path(suite_path)
    root = Path(root)
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    suite_id = str(suite["suite_id"])
    gold_dir = suite_path.parent / suite_id / "golden"
    gold_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = gold_dir / ".native_reps"
    tmp_dir.mkdir(exist_ok=True)

    by_id = {p["program_id"]: p for p in suite["programs"]}
    records = []
    overall_ok = True
    for pid in WS.W6_PROGRAM_ORDER:
        p = by_id[pid]
        meta = WO.validate_meta(p["element_oracle"]["meta"])
        binary = resolve(p["binary"], root)
        golden = resolve(p["element_oracle"]["golden_array"], root)
        binary_sha = sha256_file(binary) if binary.exists() else None
        source = resolve(p["source"], root)
        source_sha = sha256_file(source) if source.exists() else None
        rec = {
            "program_id": pid,
            "binary": str(binary),
            "binary_sha256": binary_sha,
            "source": str(source),
            "source_sha256": source_sha,
            "meta": meta,
            "golden_array": str(golden),
            "native": [],
            "ok": False,
        }
        if not binary.exists():
            rec["error"] = "native binary missing (build it first)"
            records.append(rec)
            overall_ok = False
            continue
        reps_out = []
        for rep in range(1, reps + 1):
            dump = tmp_dir / f"{pid}.native{rep}.bin"
            try:
                rc, out, err = run_binary(binary, dump, timeout, root)
            except subprocess.TimeoutExpired:
                rc, out, err = -1, "", "timeout"
            reps_out.append({
                "rep": rep, "rc": rc,
                "final": parse_final(out),
                "residual": (lambda m: m.group(1) if m else None)(
                    _RESIDUAL_RE.search(out)),
                "array_sha256": sha256_file(dump) if dump.exists() else None,
                "dump_path": str(dump),
                "stdout_tail": "\n".join(out.splitlines()[-3:]),
                "stderr_tail": "\n".join(err.splitlines()[-3:]),
            })
        rec["native"] = reps_out
        finals = {x["final"] for x in reps_out}
        dumps = {x["array_sha256"] for x in reps_out}
        ok = (len(finals) == 1 and None not in finals
              and len(dumps) == 1 and None not in dumps
              and all(x["rc"] == 0 for x in reps_out))
        if not ok:
            rec["error"] = ("native repeats disagree (rc/final/array SHA); "
                            "refusing to write a golden")
            records.append(rec)
            overall_ok = False
            continue
        # Validate size + pre-registered oracle semantics.
        try:
            arr = WO.load_array(reps_out[0]["dump_path"], meta)
            cmp = WO.compare(arr.raw, arr.raw, meta, meta["abs_tol"],
                             meta["rel_tol"], meta["ulp_tol"])
            rec["array_bytes"] = len(arr.raw)
            rec["oracle_self_check"] = cmp["category"]
            ok = cmp["category"] == "EXACT_MATCH"
        except (WO.W6OracleError, ValueError) as e:
            rec["error"] = f"array/oracle validation failed: {e}"
            ok = False
        if not ok:
            records.append(rec)
            overall_ok = False
            continue
        want_sha = reps_out[0]["array_sha256"]
        if golden.exists():
            if sha256_file(golden) != want_sha:
                if not force_golden:
                    rec["error"] = (f"existing golden differs ({golden}); "
                                    "refusing to overwrite")
                    records.append(rec)
                    overall_ok = False
                    continue
            else:
                rec["golden_action"] = "unchanged"
        if not golden.exists() or sha256_file(golden) != want_sha:
            shutil.copy2(reps_out[0]["dump_path"], golden)
            rec["golden_action"] = "written"
        rec["golden_array_sha256"] = sha256_file(golden)
        rec["final"] = reps_out[0]["final"]
        rec["ok"] = True
        records.append(rec)

    def _rel(path) -> str:
        try:
            return str(Path(path).resolve().relative_to(Path(root).resolve()))
        except ValueError:
            return str(path)

    manifest = {
        "suite_id": suite_id,
        "suite_version": str(suite["suite_version"]),
        "oracle_version": str((suite.get("oracle") or {}).get("version", "")),
        "reps": reps,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "program_order": list(WS.W6_PROGRAM_ORDER),
        "programs": {
            r["program_id"]: {
                "golden_array": _rel(r["golden_array"]),
                "sha256": r.get("golden_array_sha256"),
                "count": r["meta"]["count"],
                "shape": r["meta"]["shape"],
                "domain": r["meta"]["domain"],
                "dtype": r["meta"]["dtype"],
                "layout": r["meta"]["layout"],
                "endianness": r["meta"]["endianness"],
                "native_reps": reps,
                "native_shas": [x["array_sha256"] for x in r["native"]],
                "native_rcs": [x["rc"] for x in r["native"]],
                "native_finals": [x["final"] for x in r["native"]],
                "native_residuals": [x.get("residual") for x in r["native"]],
                "final": r.get("final"),
                "ok": r["ok"],
            } for r in records
        },
        "ok": overall_ok,
    }
    (gold_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    if not keep_reps:
        for f in tmp_dir.glob("*"):
            f.unlink()
        tmp_dir.rmdir()

    if update_suite:
        if not overall_ok:
            raise SystemExit("refusing --update-suite: native golden did not "
                             "pass 3x determinism")
        updated = json.loads(suite_path.read_text(encoding="utf-8"))
        for p in updated["programs"]:
            rec = next(r for r in records
                       if r["program_id"] == p["program_id"])
            p["source_sha256"] = rec["source_sha256"]
            p["binary_sha256"] = rec["binary_sha256"]
            p["golden_array_sha256"] = rec["golden_array_sha256"]
            p["golden"] = rec["final"]
        updated["suite_hash"] = WS.compute_suite_hash(updated)
        suite_path.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        manifest["suite_config_updated"] = str(suite_path)
        manifest["updated_suite_hash"] = updated["suite_hash"]
        (gold_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    return manifest, records


def main(argv=None):
    ap = argparse.ArgumentParser(description="W6 native golden generator")
    ap.add_argument("--suite", default=str(DEFAULT_SUITE))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--force-golden", action="store_true")
    ap.add_argument("--update-suite", action="store_true")
    ap.add_argument("--keep-reps", action="store_true",
                    help="keep the three raw native dumps (default: remove; "
                         "the manifest already records their SHA-256)")
    a = ap.parse_args(argv)
    manifest, records = generate(Path(a.suite), Path(a.root), a.reps,
                                 a.timeout, a.force_golden, a.update_suite,
                                 keep_reps=a.keep_reps)
    for r in records:
        print(json.dumps({
            "program_id": r["program_id"],
            "ok": r["ok"],
            "native_shas": [x["array_sha256"] for x in r["native"]],
            "final": r.get("final"),
            "error": r.get("error"),
        }, ensure_ascii=False))
    print(json.dumps({"ok": manifest["ok"],
                      "suite_hash": manifest.get("updated_suite_hash")},
                     ensure_ascii=False, indent=2))
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
