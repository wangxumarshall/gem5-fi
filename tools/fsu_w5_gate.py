#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_w5_gate.py — W5 逐元素 oracle 的无故障 gate（native 3× + gem5 B0 3×）。

对固定 suite 的五个程序逐一验证：
  * 数组形状/元素总数与 meta 一致；
  * canonical array SHA-256 在 3 次 native 与 3 次 gem5 B0 中稳定；
  * 与预注册 golden 数组逐元素 mismatch_count == 0（abs/rel/ULP 容差固定）；
  * FINAL=<16hex> 辅助校验与 golden token 一致；
  * suite_hash 在真实 binary SHA 下稳定。

本工具不是正式 seed，不写 runs/fsu/<RunID>/seed*；证据只写 gate 目录。
高负载期间禁止运行；真实执行前必须重建五个 PolyBench 二进制。

用法（负载安全后）：
  python3 tools/fsu_w5_gate.py --create-golden \
      --outdir runs/fsu-gates/W5-ELEMENT-ORACLE-GATE
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_config_profile as CP  # noqa: E402
import fsu_oracle as O  # noqa: E402
import fsu_suite as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = ROOT / "configs/fsu/suites/polybench-fp-v1.json"
DEFAULT_GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
DEFAULT_CONFIG = ROOT / "configs/se/ooo_proxy.py"
DEFAULT_OUT = ROOT / "runs/fsu-gates/W5-ELEMENT-ORACLE-GATE"

FINALS = "FINAL="
ARRAY_DUMP = "ARRAY_DUMP "


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_final(text: str):
    val = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(FINALS):
            val = line[len(FINALS):].strip()
    return val


def parse_array_dump(text: str):
    rec = None
    for line in text.splitlines():
        if ARRAY_DUMP in line:
            body = line.split(ARRAY_DUMP, 1)[1]
            kv = {}
            for tok in body.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    kv[k] = v
            rec = kv
    return rec


def run(cmd, timeout, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           errors="replace", timeout=timeout, cwd=cwd)
        return r.returncode, r.stdout or "", r.stderr or "", False
    except subprocess.TimeoutExpired as e:
        def s(x):
            return x.decode("utf-8", "replace") if isinstance(x, bytes) else (x or "")
        return -1, s(e.stdout), s(e.stderr), True


def suite_hash_with_real_binaries(suite, root: Path):
    resolved = json.loads(json.dumps(suite))
    for p in resolved["programs"]:
        binary = Path(p["binary"])
        if not binary.is_absolute():
            binary = root / binary
        if not binary.exists():
            raise SystemExit(f"binary missing: {binary} (rebuild polybench first)")
        p["binary_sha256"] = sha256_file(binary)
        source = Path(p["source"])
        if not source.is_absolute():
            source = root / source
        p["source_sha256"] = sha256_file(source)
    info = S.validate_suite_manifest(resolved, require_hashes=True,
                                     require_suite_hash=False)
    return info["suite_hash"]


def meta_for(program: dict):
    eo = program.get("element_oracle") or {}
    meta = dict(eo.get("meta") or {})
    if not meta:
        raise SystemExit(f"{program['program_id']}: element_oracle.meta missing")
    return O.validate_meta(meta)


def resolve(path: str, root: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else root / p


def main(argv=None):
    ap = argparse.ArgumentParser(description="W5 element-oracle no-fault gate")
    ap.add_argument("--suite", default=str(DEFAULT_SUITE))
    ap.add_argument("--gem5", default=str(DEFAULT_GEM5))
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--outdir", default=str(DEFAULT_OUT))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--create-golden", action="store_true",
                    help="write golden arrays after 3 native reps agree")
    ap.add_argument("--force-golden", action="store_true",
                    help="overwrite an existing golden array (never a failed attempt)")
    ap.add_argument("--update-suite", action="store_true",
                    help="after a PASS, write real binary SHA + golden array "
                         "SHA + suite_hash back into the suite config")
    a = ap.parse_args(argv)

    root = Path(a.root)
    suite_path = Path(a.suite)
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    order = S.validate_suite_manifest(suite, require_hashes=False,
                                      require_suite_hash=False)["identity"]
    # Fail closed on a declared suite_hash drift; the gate recomputes with the
    # REAL binary hashes below (the config may legitimately be 'pending').
    declared = suite.get("suite_hash")
    if declared and declared != "pending":
        try:
            S.validate_suite_manifest(suite, require_hashes=False,
                                      require_suite_hash=True)
        except S.SuiteError as e:
            raise SystemExit(f"suite_hash drift before gate: {e}")

    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    arts = outdir / "artifacts"
    arts.mkdir(exist_ok=True)
    gold_dir = suite_path.parent / suite["suite_id"] / "golden"
    gold_dir.mkdir(parents=True, exist_ok=True)

    suite_hash = suite_hash_with_real_binaries(suite, root)
    report = {
        "gate": "W5-ELEMENT-ORACLE-GATE",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": suite_hash,
        "reps_native": a.reps,
        "reps_gem5": a.reps,
        "config_profile": "B0",
        "programs": [],
        "ok": True,
    }

    by_id = {p["program_id"]: p for p in suite["programs"]}
    for pid in S.PROGRAM_ORDER:
        p = by_id[pid]
        meta = meta_for(p)
        binary = resolve(p["binary"], root)
        row = {"program_id": pid, "binary": str(binary),
               "binary_sha256": sha256_file(binary),
               "source_sha256": sha256_file(resolve(p["source"], root)),
               "meta": meta, "native": [], "gem5": [], "ok": True}
        progs = []
        for rep in range(1, a.reps + 1):
            dump = arts / f"{pid}.native{rep}.bin"
            rc, out, err, timed = run(
                [str(binary), f"--array-dump={dump}"], a.timeout, cwd=str(root))
            progs.append({
                "rep": rep, "rc": rc, "timed_out": timed,
                "final": parse_final(out), "dump": parse_array_dump(out),
                "array_sha256": sha256_file(dump) if dump.exists() else None,
                "dump_path": str(dump),
                "stdout_tail": "\n".join(out.splitlines()[-4:]),
                "stderr_tail": "\n".join(err.splitlines()[-4:]),
            })
        row["native"] = progs
        ok = (len({x["final"] for x in progs}) == 1
              and len({x["array_sha256"] for x in progs}) == 1
              and all(x["rc"] == 0 and not x["timed_out"]
                      and x["array_sha256"] for x in progs))
        golden_path = gold_dir / f"{pid}.bin"
        if a.create_golden:
            if golden_path.exists() and not a.force_golden:
                raise SystemExit(
                    f"{pid}: golden exists ({golden_path}); refusing to "
                    "overwrite (use --force-golden only for a new, complete gate)")
            if not ok:
                raise SystemExit(f"{pid}: native reps disagree; no golden written")
            shutil.copy2(progs[0]["dump_path"], golden_path)
        if not golden_path.exists():
            row["ok"] = False
            row["error"] = f"golden missing: {golden_path} (run --create-golden)"
            report["programs"].append(row)
            report["ok"] = False
            continue
        golden_bytes = golden_path.read_bytes()
        row["golden_array"] = str(golden_path)
        row["golden_sha256"] = hashlib.sha256(golden_bytes).hexdigest()
        # Native vs golden must be exactly identical.
        for x in progs:
            if x["array_sha256"] != row["golden_sha256"]:
                ok = False
        # gem5 B0 no-fault reps.
        gem = []
        for rep in range(1, a.reps + 1):
            dump = arts / f"{pid}.gem5-{rep}.bin"
            cmd = [str(Path(a.gem5)), "--quiet", "-d",
                   str(arts / f"{pid}.gem5-{rep}.outdir"),
                   str(Path(a.config)), "--cmd", str(binary), "--cpu", "O3",
                   "--config_profile", "B0", "--rng_seed", str(rep),
                   "--chaos_fpu", "--fpu_count_only",
                   f"--cmd_arg=--array-dump={dump}"]
            rc, out, err, timed = run(cmd, a.timeout, cwd=str(root))
            prof = CP.verify_config_profile(
                arts / f"{pid}.gem5-{rep}.outdir" / "config.ini", "B0")
            gem.append({
                "rep": rep, "rc": rc, "timed_out": timed,
                "final": parse_final(out), "dump": parse_array_dump(out),
                "array_sha256": sha256_file(dump) if dump.exists() else None,
                "dump_path": str(dump),
                "config_profile_check": prof,
                "stdout_tail": "\n".join(out.splitlines()[-4:]),
                "stderr_tail": "\n".join(err.splitlines()[-4:]),
            })
        row["gem5"] = gem
        for x in gem:
            if (x["rc"] != 0 or x["timed_out"] or not x["array_sha256"]
                    or x["array_sha256"] != row["golden_sha256"]
                    or not (x.get("config_profile_check") or {}).get("ok")):
                ok = False
        # FINAL must match the registered 16-hex golden token (auxiliary).
        want_final = str(p.get("golden") or "")
        for x in progs + gem:
            if x["final"] != want_final:
                ok = False
        # Per-element comparison (must be exact at the pre-registered tol).
        for x in gem:
            if not x["array_sha256"]:
                continue
            cmp = O.compare(golden_bytes, Path(x["dump_path"]).read_bytes(),
                            meta, meta["abs_tol"], meta["rel_tol"],
                            meta["ulp_tol"])
            x["mismatch_count"] = cmp.get("mismatch_count")
            x["max_abs_error"] = cmp.get("max_abs_error")
            x["max_rel_error"] = cmp.get("max_rel_error")
            x["max_ulp"] = cmp.get("max_ulp")
            if cmp.get("mismatch_count") != 0:
                ok = False
        row["ok"] = ok
        report["programs"].append(row)
        report["ok"] = report["ok"] and ok

    (outdir / "gate_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# W5 element-oracle no-fault gate", "",
             f"- suite：`{report['suite_id']}` v{report['suite_version']}",
             f"- suite_hash：`{report['suite_hash']}`",
             f"- native reps：{a.reps}；gem5 B0 reps：{a.reps}",
             f"- 结论：{'PASS' if report['ok'] else 'FAIL'}", "",
             "| program | native SHA-256 | gem5 SHA-256 | mismatch | FINAL | ok |",
             "|---|---|---|---|---|---|"]
    for r in report["programs"]:
        ns = (r["native"][0].get("array_sha256") or "—")[:16]
        gs = (r["gem5"][0].get("array_sha256") or "—")[:16]
        mm = r["gem5"][0].get("mismatch_count", "—") if r["gem5"] else "—"
        lines.append(f"| {r['program_id']} | `{ns}…` | `{gs}…` | {mm} | "
                     f"{r['native'][0].get('final') if r['native'] else '—'} | "
                     f"{'PASS' if r['ok'] else 'FAIL'} |")
    (outdir / "GATE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sums = []
    for f in sorted(outdir.rglob("*")):
        if f.is_file() and f.name != "SHA256SUMS":
            sums.append(f"{sha256_file(f)}  {f.relative_to(outdir)}")
    (outdir / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    if a.update_suite:
        if not report["ok"]:
            raise SystemExit("refusing --update-suite: gate did not PASS")
        updated = json.loads(suite_path.read_text(encoding="utf-8"))
        for p in updated["programs"]:
            row = next(r for r in report["programs"]
                       if r["program_id"] == p["program_id"])
            p["binary_sha256"] = row["binary_sha256"]
            p["source_sha256"] = row["source_sha256"]
            p["golden_array_sha256"] = row["golden_sha256"]
            p["binary_hash_state"] = "gated"
        resolved = json.loads(json.dumps(updated))
        for p in resolved["programs"]:
            p["binary_sha256"] = row_sha = report["programs"][
                S.PROGRAM_ORDER.index(p["program_id"])]["binary_sha256"]
        updated["suite_hash"] = S.compute_suite_hash(resolved)
        suite_path.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        report["suite_config_updated"] = str(suite_path)
        report["updated_suite_hash"] = updated["suite_hash"]
    print(json.dumps({"ok": report["ok"], "suite_hash": suite_hash,
                      "outdir": str(outdir)}, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
