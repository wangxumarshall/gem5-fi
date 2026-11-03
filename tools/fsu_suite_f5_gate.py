#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_suite_f5_gate.py — FP06-F5-W5 suite gate (never counted as a seed).

The gate runs the five fixed PolyBench programs ONCE each, as F5 component
runs driven by the SAME pre-registered `seed_plan` entry (default suite seed
1 = FP06-a FP32 sign SA0). PASS requires 5/5 components to be admitted with
an independent `audit.ok=true` + `certified=true` and a real element-oracle
result (SDC or MASKED). Any missing/drifting artifact fails closed.

This tool NEVER writes `runs/fsu`: evidence must live under
`runs/fsu-gates/...`. It writes no suite-level manifest / AUTHORITATIVE, so
a gate PASS is not a formal suite seed (formal count stays +0).

Modes
-----
* default            run the five components (the main agent invokes this
                     after building gem5; component failures are reported,
                     never hidden).
* --verify-only      re-validate already-produced gate attempts without
                     running gem5.
* --print-commands   print the exact census/injection commands for each
                     program (no execution at all).

Usage:
  python3 tools/fsu_suite_f5_gate.py \
      --outdir runs/fsu-gates/F5-FP06-W5-GATE
  python3 tools/fsu_suite_f5_gate.py --print-commands
  python3 tools/fsu_suite_f5_gate.py --verify-only \
      --outdir runs/fsu-gates/F5-FP06-W5-GATE
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_seed_runner as R  # noqa: E402
import fsu_suite as S  # noqa: E402
import fsu_suite_runner as SR  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = ROOT / "configs/fsu/suites/polybench-fp-v1-f5.json"
DEFAULT_GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
DEFAULT_CONFIG = ROOT / "configs/se/ooo_proxy.py"
DEFAULT_OUT = ROOT / "runs/fsu-gates/F5-FP06-W5-GATE"
DEFAULT_GATE_ID = "FSU-FP06-F5-W5-GATE"
DECIDABLE_ORACLE = ("SDC", "MASKED")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _checker():
    checks = []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})
        return bool(ok)

    return checks, check


def _gate_root(root: Path) -> Path:
    return (Path(root) / "runs/fsu-gates").resolve()


def _assert_gate_outdir(outdir: Path, root: Path):
    gate_root = _gate_root(root)
    out = Path(outdir).resolve()
    if out != gate_root and gate_root not in out.parents:
        raise S.SuiteError(
            f"gate artifacts must live under {gate_root} (got {out}); "
            "runs/fsu is reserved for formal seeds")


def _attempt_injector_checks(manifest: dict, plan_entry: dict):
    """The attempt's manifest must carry EXACTLY the pre-registered fault."""
    checks, check = _checker()
    inj = manifest.get("injector") or {}
    fpu = inj.get("fpu_mode") or {}
    check("attempt freq is F5", str(manifest.get("freq")) == "F5")
    check("attempt model_id is FP06",
          str(manifest.get("model_id")) == "FP06")
    check("attempt load_id is W5", str(manifest.get("load_id")) == "W5")
    check("attempt submodel == seed_plan submodel",
          str(manifest.get("submodel")) == plan_entry["submodel"])
    check("injector component is fsu", str(inj.get("component")) == "fsu")
    check("exactly one component fault (max_faults=1)",
          int(inj.get("max_faults", 0)) == 1)
    check("permanent_stuck enabled", fpu.get("permanent_stuck") is True)
    check("fault_mask == seed_plan mask",
          str(inj.get("fault_mask", "")).lower() == plan_entry["mask"].lower())
    check("precision == seed_plan precision",
          str(fpu.get("precision")) == plan_entry["precision"])
    check("stuck_polarity == seed_plan polarity",
          int(fpu.get("stuck_polarity", -1)) == plan_entry["polarity"])
    check("lane_width == seed_plan lane_width",
          int(fpu.get("lane_width", -1)) == plan_entry["lane_width"])
    check("lane_offset == seed_plan lane_offset",
          int(fpu.get("lane_offset", -1)) == plan_entry["lane_offset"])
    check("f5_warmup == seed_plan warmup",
          int(fpu.get("f5_warmup", -1)) == plan_entry["warmup"])
    check("f5_sample_limit == seed_plan sample.limit",
          int(fpu.get("f5_sample_limit", -1))
          == plan_entry["sample"]["limit"])
    check("f5_keep_first_last_n == seed_plan sample.keep_first_last_n",
          int(fpu.get("f5_keep_first_last_n", -1))
          == plan_entry["sample"]["keep_first_last_n"])
    check("op_classes == seed_plan op_classes",
          list(fpu.get("op_classes") or []) == plan_entry["op_classes"])
    check("reg_class == seed_plan reg_class",
          str(fpu.get("reg_class", "any")) == plan_entry["reg_class"])
    check("decode_guard == seed_plan decode_guard",
          bool(fpu.get("decode_guard")) == bool(plan_entry["decode_guard"]))
    check("attempt seed_plan_entry == suite seed_plan entry",
          manifest.get("seed_plan_entry") == S.seed_plan_identity(plan_entry))
    return checks


def verify_component_attempt(attempt: Path, program: dict, plan_entry: dict,
                             suite: dict):
    """Validate one gate component attempt from real on-disk evidence."""
    attempt = Path(attempt)
    pid = program["program_id"]
    checks, check = _checker()
    man_path = attempt / "manifest.json"
    cm_path = attempt / "component_manifest.json"
    audit_path = attempt / "audit.json"
    oracle_path = attempt / "oracle_elements.json"
    array_path = attempt / "inject/array.bin"
    ev_path = attempt / "evidence_sha256.json"

    check("attempt directory exists", attempt.is_dir())
    check("attempt manifest.json exists", man_path.exists())
    if man_path.exists():
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
        checks.extend(_attempt_injector_checks(manifest, plan_entry))
        check("binary is the registered program binary",
              Path(str((manifest.get("workload") or {}).get("binary", "")))
              .name == Path(program["binary"]).name)
        check("run_id is the gate id, not a formal RunID",
              str(manifest.get("run_id", "")).endswith("-GATE"))
    else:
        manifest = {}

    cm = {}
    if cm_path.exists():
        try:
            cm = json.loads(cm_path.read_text(encoding="utf-8"))
            S.validate_component_manifest(cm, suite)
            check("component manifest structure/identity", True)
        except (OSError, json.JSONDecodeError, S.SuiteError) as e:
            check("component manifest structure/identity", False)
            cm = {}
    else:
        check("component_manifest.json exists", False)
    check("component_status == admitted",
          cm.get("component_status") == "admitted")
    check("component_oracle is SDC or MASKED",
          cm.get("component_oracle") in DECIDABLE_ORACLE)
    check("component seed_plan_entry == pre-registration",
          cm.get("seed_plan_entry") == S.seed_plan_identity(plan_entry))
    if man_path.exists() and cm:
        check("component_manifest_sha256 == attempt manifest.json",
              cm.get("component_manifest_sha256") == sha256_file(man_path))

    audit = {}
    if audit_path.exists():
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            audit = {}
    check("independent audit.ok", audit.get("ok") is True)
    check("independent audit.certified", audit.get("certified") is True)

    check("oracle_elements.json exists", oracle_path.exists())
    check("inject/array.bin exists", array_path.exists())
    covered = False
    if oracle_path.exists() and array_path.exists() and ev_path.exists():
        try:
            hashes = json.loads(ev_path.read_text(encoding="utf-8"))
            covered = (
                hashes.get("oracle_elements.json") == sha256_file(oracle_path)
                and hashes.get("inject/array.bin") == sha256_file(array_path))
        except (OSError, json.JSONDecodeError):
            covered = False
    check("oracle/array covered by evidence_sha256.json", covered)

    failures = [c["check"] for c in checks if not c["ok"]]
    return {
        "program_id": pid,
        "program_index": program["program_index"],
        "attempt": str(attempt),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "checks": checks,
        "component_oracle": cm.get("component_oracle"),
        "component_eligible": cm.get("component_eligible"),
        "component_activated": cm.get("component_activated"),
        "component_terminal": cm.get("component_terminal"),
        "ok": not failures,
    }


def _latest_attempt(seed_dir: Path, pid: str, gate_id: str) -> Path | None:
    root = Path(seed_dir) / "components" / pid / gate_id
    attempts = sorted(root.glob("seed*/attempt-*")) if root.exists() else []
    return attempts[-1] if attempts else None


def _verify_all(suite, info, seed_dir, gate_id, plan_entry):
    by_id = {p["program_id"]: p for p in suite["programs"]}
    records = []
    for pid in S.PROGRAM_ORDER:
        attempt = _latest_attempt(seed_dir, pid, gate_id)
        if attempt is None:
            records.append({
                "program_id": pid,
                "program_index": by_id[pid]["program_index"],
                "attempt": None, "status": "FAIL",
                "failures": ["no gate attempt found"], "checks": [],
                "ok": False,
            })
            continue
        records.append(verify_component_attempt(
            attempt, by_id[pid], plan_entry, suite))
    return records


def _run_all(suite, info, seed_dir, gate_id, plan_entry, gem5, config, root,
             timeout, allow_rerun, runner):
    suite_hash = info["suite_hash"]
    policy = str(suite.get("component_seed_policy_version")
                 or S.DEFAULT_COMPONENT_SEED_POLICY)
    derived = S.derive_component_seeds(
        1, policy, suite["suite_id"], suite["suite_version"])
    records = []
    for pid in S.PROGRAM_ORDER:
        program = next(p for p in suite["programs"]
                       if p["program_id"] == pid)
        # The five F5 components all run the SAME suite-seed 1 plan entry.
        res = SR._run_one_component(
            suite, program, suite_hash, 1, derived[pid], policy, seed_dir,
            gate_id, seed_dir, gem5, root, runner, timeout, allow_rerun,
            plan_entry=plan_entry)
        attempt = Path(str(res.get("attempt", "")))
        if attempt.is_dir() and (attempt / "manifest.json").exists():
            rec = verify_component_attempt(attempt, program, plan_entry, suite)
        else:
            rec = {
                "program_id": pid,
                "program_index": program["program_index"],
                "attempt": str(attempt), "status": "FAIL",
                "failures": [f"component run not admitted: "
                             f"{res.get('reason', res.get('status'))}"],
                "checks": [], "ok": False,
            }
        rec["run_status"] = res.get("status")
        records.append(rec)
    return records


def _write_report(outdir: Path, gate_id: str, suite, info, plan_entry,
                  records):
    ok = len(records) == S.PROGRAM_COUNT and all(r["ok"] for r in records)
    report = {
        "gate": "FP06-F5-W5",
        "gate_id": gate_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "non_formal": True,
        "counts_toward_519": False,
        "formal_suite_seed_count": 0,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": info["suite_hash"],
        "suite_seed": 1,
        "seed_plan_entry": S.seed_plan_identity(plan_entry),
        "program_order": list(S.PROGRAM_ORDER),
        "program_count": S.PROGRAM_COUNT,
        "component_run_count": len(records),
        "component_pass_count": sum(1 for r in records if r["ok"]),
        "records": records,
        "ok": ok,
    }
    (outdir / "gate_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    lines = [
        f"# {gate_id} — FP06-F5-W5 suite gate（非正式，不计 seed）", "",
        f"- suite：`{suite['suite_id']}` v{suite['suite_version']}",
        f"- suite_hash：`{info['suite_hash']}`",
        f"- seed_plan：suite seed 1 / `{plan_entry['submodel']}` / "
        f"{plan_entry['precision']} / mask `{plan_entry['mask']}` / "
        f"polarity {plan_entry['polarity']}",
        f"- component runs：{len(records)}；PASS："
        f"{report['component_pass_count']}/{S.PROGRAM_COUNT}",
        f"- 正式 seed 计数：**+0**（gate 不计 519/240）",
        f"- 结论：**{'PASS' if ok else 'FAIL'}**", "",
        "| # | program | eligible | activated | terminal | oracle | "
        "audit | 结论 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(records, 1):
        lines.append(
            f"| {i} | {r['program_id']} | {r.get('component_eligible', '—')} "
            f"| {r.get('component_activated', '—')} | "
            f"{r.get('component_terminal', '—')} | "
            f"{r.get('component_oracle', '—')} | "
            f"{'ok' if r['ok'] else '; '.join(r['failures'][:2])} | "
            f"{r['status']} |")
    lines += ["", "## 逐 component 检查", ""]
    for r in records:
        lines += [f"### {r['program_id']}", "", "| 检查 | 结果 |", "|---|---|"]
        for c in r.get("checks", []):
            lines.append(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} |")
        if r.get("failures"):
            lines += ["", "失败项：" + "; ".join(r["failures"])]
        lines.append("")
    (outdir / "GATE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sums = []
    for f in sorted(outdir.rglob("*")):
        if f.is_file() and f.name != "SHA256SUMS":
            sums.append(f"{sha256_file(f)}  {f.relative_to(outdir)}")
    (outdir / "SHA256SUMS").write_text("\n".join(sums) + "\n",
                                       encoding="utf-8")
    return report


def print_commands(suite, info, root, gem5, config, gate_id, plan_entry):
    """Print the exact census + injection commands (never executes them)."""
    policy = str(suite.get("component_seed_policy_version")
                 or S.DEFAULT_COMPONENT_SEED_POLICY)
    derived = S.derive_component_seeds(
        1, policy, suite["suite_id"], suite["suite_version"])
    out = {"gate_id": gate_id, "suite_hash": info["suite_hash"],
           "seed_plan": S.seed_plan_identity(plan_entry), "commands": []}
    for pid in S.PROGRAM_ORDER:
        program = next(p for p in suite["programs"]
                       if p["program_id"] == pid)
        spec = SR._component_run_manifest(
            suite, program, gate_id, 1, derived[pid], info["suite_hash"],
            policy, plan_entry=plan_entry)
        outdir = Path(root) / "runs/fsu-gates" / gate_id / "commands" / pid
        census = R.build_cmd(spec, outdir / "census", derived[pid], None,
                             True, Path(gem5), Path(config), Path(root))
        inject = R.build_cmd(spec, outdir / "inject", derived[pid], 0, False,
                             Path(gem5), Path(config), Path(root))
        out["commands"].append({
            "program_id": pid,
            "component_seed": derived[pid],
            "injector": spec["injector"],
            "submodel": spec["submodel"],
            "census": census,
            "inject": inject,
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def run_gate(suite_path=DEFAULT_SUITE, outdir=DEFAULT_OUT,
             gem5=DEFAULT_GEM5, config=DEFAULT_CONFIG, root=ROOT,
             timeout=3600, gate_id=DEFAULT_GATE_ID, allow_rerun=False,
             verify_only=False, runner=None, print_only=False):
    root = Path(root)
    outdir = Path(outdir)
    _assert_gate_outdir(outdir, root)
    suite, info = SR.load_suite(Path(suite_path), root)
    plan_entry = S.seed_plan_entry(suite, 1)
    if plan_entry is None:
        raise S.SuiteError("the F5 gate suite must pre-register a seed_plan")
    if print_only:
        return print_commands(suite, info, root, gem5, config, gate_id,
                              plan_entry)
    outdir.mkdir(parents=True, exist_ok=True)
    seed_dir = outdir / "gate-seed1"
    if verify_only:
        records = _verify_all(suite, info, seed_dir, gate_id, plan_entry)
    else:
        records = _run_all(suite, info, seed_dir, gate_id, plan_entry,
                           Path(gem5), Path(config), root, timeout,
                           allow_rerun, runner)
    return _write_report(outdir, gate_id, suite, info, plan_entry, records)


def main(argv=None):
    ap = argparse.ArgumentParser(description="FP06-F5-W5 non-formal gate")
    ap.add_argument("--suite", default=str(DEFAULT_SUITE))
    ap.add_argument("--outdir", default=str(DEFAULT_OUT))
    ap.add_argument("--gem5", default=str(DEFAULT_GEM5))
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--gate-id", default=DEFAULT_GATE_ID)
    ap.add_argument("--allow-rerun", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--print-commands", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = run_gate(Path(a.suite), Path(a.outdir), Path(a.gem5),
                       Path(a.config), Path(a.root), a.timeout, a.gate_id,
                       a.allow_rerun, a.verify_only, print_only=a.print_commands)
    except S.SuiteError as e:
        print(json.dumps({"ok": False, "reason": str(e)},
                         ensure_ascii=False, indent=2))
        return 2
    if a.print_commands:
        return res
    print(json.dumps({"ok": res["ok"], "gate_id": res["gate_id"],
                      "component_pass_count": res["component_pass_count"],
                      "outdir": str(a.outdir)},
                     ensure_ascii=False, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
