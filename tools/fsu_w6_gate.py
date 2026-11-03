#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_w6_gate.py — W6 (SVD + FFT + sparse-CG) gate, never counted as a seed.

One gate suite seed contains exactly THREE component runs (fixed order
svd → fft → sparse-cg). A suite seed is certified only when 3/3 components
have an independent `audit.ok=true` + `certified=true` AND a real W6
element-oracle result (SDC or MASKED). Any missing/drifting evidence fails
closed; component runs/faults are never added to `admitted_seeds_total`.

W6 mixes precisions, so the injector is resolved per program:
  suite.injector → program_overrides[pid] → seed_plan (+ program_mask).
This is what yields SVD fp64 / lane 64 / 64-bit mask while FFT and sparse-CG
are fp32 / lane 32 / 32-bit masks.

Modes
-----
  --print-commands   print the exact census/injection commands per component
                     (no gem5 execution; F5 --all-seeds prints seeds 1..3)
  --verify-only      re-validate existing gate attempts without gem5
  default            run the three components for one suite seed

Evidence ALWAYS lives under runs/fsu-gates/...; this tool refuses runs/fsu.
It writes no formal suite manifest / AUTHORITATIVE and never touches the
source registry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_prop_fields as P  # noqa: E402
import fsu_seed_audit as A  # noqa: E402
import fsu_seed_runner as R  # noqa: E402
import fsu_suite as S  # noqa: E402
import fsu_suite_runner as SR  # noqa: E402
import fsu_w6_oracle as WO  # noqa: E402
import fsu_w6_suite as WS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE_F0 = ROOT / "configs/fsu/suites/w6-fp-v1.json"
DEFAULT_SUITE_F5 = ROOT / "configs/fsu/suites/w6-fp-v1-f5.json"
DEFAULT_GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
DEFAULT_CONFIG = ROOT / "configs/se/ooo_proxy.py"
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


def _suite_freq(suite) -> str:
    return str((suite.get("run_defaults") or {}).get("freq", "") or "")


def default_gate_id(suite) -> str:
    if _suite_freq(suite) == "F5":
        return "FSU-FP06-F5-W6-GATE"
    return "FSU-FP04-F0-W6-GATE"


def default_outdir(suite) -> Path:
    tag = "F5" if _suite_freq(suite) == "F5" else "F0"
    return ROOT / f"runs/fsu-gates/W6-{tag}-GATE"


def _assert_gate_outdir(outdir: Path, root: Path):
    gate_root = (Path(root) / "runs/fsu-gates").resolve()
    out = Path(outdir).resolve()
    if out != gate_root and gate_root not in out.parents:
        raise WS.W6SuiteError(
            f"gate artifacts must live under {gate_root} (got {out}); "
            "runs/fsu is reserved for formal seeds")


def _component_run_manifest(suite, program, run_id, suite_seed,
                            component_seed, suite_hash, policy_version,
                            plan_entry=None):
    defaults = json.loads(json.dumps(suite.get("run_defaults") or {}))
    limits = defaults.pop("limits", {}) or {}
    program_id = program["program_id"]
    injector = WS.resolved_injector(suite, program_id, plan_entry)
    if plan_entry is not None:
        defaults["submodel"] = plan_entry["submodel"]
    workload = {
        "binary": str(program["binary"]),
        "source": str(program.get("source", "")),
        "identity": f"W6-{program_id}-v1",
        "golden": program.get("golden", ""),
        "oracle_kind": "exact_hash",
        "oracle_tol": 0,
        "element_oracle": json.loads(
            json.dumps(program.get("element_oracle") or {})),
    }
    overrides = S.normalise_program_overrides(suite) or {}
    component = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": suite_hash,
        "suite_seed": int(suite_seed),
        "program_id": program_id,
        "program_index": program["program_index"],
        "program_count": WS.W6_PROGRAM_COUNT,
        "component_seed": component_seed,
        "component_seed_policy_version": policy_version,
    }
    out = {
        "run_id": run_id,
        **defaults,
        "workload": workload,
        "injector": injector,
        "limits": limits,
        "component": component,
        "program_override": S.program_override_identity(
            overrides.get(program_id)),
        "effective_injector": json.loads(json.dumps(injector)),
        "notes": ("W6 gate component run: one real program and exactly one "
                  "fault; never a formal seed by itself."),
    }
    if plan_entry is not None:
        out["seed_plan_entry"] = S.seed_plan_identity(plan_entry)
        out["pre_registration"] = json.loads(
            json.dumps(out["seed_plan_entry"]))
    return out


def _resolve_golden(program: dict, asset_root: Path) -> Path:
    path = Path(program["element_oracle"]["golden_array"])
    return path if path.is_absolute() else Path(asset_root) / path


def _element_oracle(attempt: Path, program: dict, asset_root: Path):
    eo = program.get("element_oracle") or {}
    meta = WO.validate_meta(eo.get("meta") or {})
    golden = _resolve_golden(program, asset_root)
    fault = attempt / "inject/array.bin"
    if not fault.exists():
        raise WS.W6SuiteError(
            f"{program['program_id']}: missing {fault} (--array-dump)")
    result = WO.compare(str(golden), str(fault), meta, meta["abs_tol"],
                        meta["rel_tol"], meta["ulp_tol"])
    payload = WO.json_ready(result)
    payload["golden_array"] = str(golden)
    payload["fault_array"] = str(fault)
    payload["ok"] = True
    (attempt / "oracle_elements.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _write_component_manifest(attempt: Path, manifest: dict):
    (attempt / "component_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    R.write_hashes(attempt)


def _component_manifest(suite, program, suite_hash, suite_seed,
                        component_seed, policy_version, attempt: Path,
                        status: str, audit_ok: bool, certified: bool,
                        plan_entry=None):
    report_path = attempt / "chain_report.json"
    report = (json.loads(report_path.read_text(encoding="utf-8"))
              if report_path.exists() else {})
    oracle = report.get("oracle") or {}
    overrides = S.normalise_program_overrides(suite) or {}
    try:
        attempt_no = int(attempt.name.split("-")[1])
    except (IndexError, ValueError):
        attempt_no = 0
    if status == "admitted" and not (audit_ok and certified):
        status = "failed"
    out = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": suite_hash,
        "suite_seed": int(suite_seed),
        "program_id": program["program_id"],
        "program_index": program["program_index"],
        "program_count": WS.W6_PROGRAM_COUNT,
        "component_seed_policy_version": policy_version,
        "component_seed": component_seed,
        "component_attempt": attempt_no,
        "component_manifest_sha256": sha256_file(attempt / "manifest.json")
        if (attempt / "manifest.json").exists() else "0" * 64,
        "component_binary_sha256": program["binary_sha256"],
        "component_source_sha256": program["source_sha256"],
        "component_golden_sha256": program["golden_array_sha256"],
        "component_golden_sha256_scheme": "sha256-of-canonical-golden-array-v1",
        "component_golden": program.get("golden"),
        "component_status": status,
        "component_eligible": int(oracle.get("eligible_count", 0) or 0),
        "component_activated": SR._activated_count(attempt),
        "component_faults": int(report.get("actual_injections",
                                           oracle.get("faults_injected", 0))
                                or 0),
        "component_terminal": SR._primary_terminal(report),
        "component_oracle": "NOT_EVALUATED",
        "component_run_level_oracle": str(oracle.get("category") or "Unknown"),
        "component_audit_ok": bool(audit_ok),
        "component_certified": bool(certified),
        "program_override": S.program_override_identity(
            overrides.get(program["program_id"])),
        "effective_injector": WS.resolved_injector(
            suite, program["program_id"], plan_entry),
        "attempt": str(attempt),
    }
    if plan_entry is not None:
        out["seed_plan_entry"] = S.seed_plan_identity(plan_entry)
    return out


def _run_one_component(suite, program, suite_hash, suite_seed, component_seed,
                       policy_version, seed_dir: Path, run_id: str,
                       out_root: Path, gem5: Path, root: Path, runner,
                       timeout_s, allow_rerun: bool, plan_entry=None):
    pid = program["program_id"]
    component_root = Path(seed_dir) / "components" / pid
    component_root.mkdir(parents=True, exist_ok=True)
    comp_seed_dir = (component_root / run_id / f"seed{component_seed}")
    spec = _component_run_manifest(
        suite, program, run_id, suite_seed, component_seed, suite_hash,
        policy_version, plan_entry=plan_entry)
    spec_path = component_root / f"manifest-seed{component_seed}.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    rerun = allow_rerun or (comp_seed_dir / "AUTHORITATIVE").exists()
    res = R.run_seed(
        spec_path, component_seed, out_root=out_root, gem5=gem5, root=root,
        runner=runner, timeout_s=timeout_s, allow_rerun=rerun,
        seed_dir=comp_seed_dir, component=spec["component"],
        write_authoritative=False, copy_to_complete=False)
    if res.get("status") == "already_admitted":
        attempt = Path(res.get("authoritative", ""))
    else:
        attempt = Path(res.get("attempt", ""))
    if not attempt.is_dir():
        return {
            "program_id": pid, "program_index": program["program_index"],
            "attempt": str(attempt), "component_status": "failed",
            "component_oracle": "NOT_EVALUATED", "component_audit_ok": False,
            "component_certified": False, "ok": False,
            "run_status": res.get("status"),
            "reason": res.get("reason", "no attempt created"),
        }
    if res.get("status") != "admitted":
        cm = _component_manifest(
            suite, program, suite_hash, suite_seed, component_seed,
            policy_version, attempt,
            "not_activated" if res.get("status") == "not_activated" else
            "failed", False, False, plan_entry)
        cm["run_status"] = res.get("status")
        cm["reason"] = res.get("reason")
        _write_component_manifest(attempt, cm)
        return {**cm, "ok": False}

    oracle_ok = False
    oracle_error = None
    try:
        oracle = _element_oracle(attempt, program, root)
        oracle_ok = oracle.get("ok") is True
    except (WS.W6SuiteError, WO.W6OracleError, OSError, ValueError) as e:
        oracle_error = f"{type(e).__name__}: {e}"
        (attempt / "oracle_elements.json").write_text(
            json.dumps({"ok": False, "program_id": pid,
                        "error": oracle_error}, ensure_ascii=False, indent=2),
            encoding="utf-8")
    A.write_audit(attempt)
    audit = json.loads((attempt / "audit.json").read_text(encoding="utf-8"))
    audit_ok = audit.get("ok") is True
    certified = audit.get("certified") is True
    status = "admitted" if (audit_ok and certified and oracle_ok) else "failed"
    cm = _component_manifest(
        suite, program, suite_hash, suite_seed, component_seed,
        policy_version, attempt, status, audit_ok, certified, plan_entry)
    if oracle_ok:
        mismatches = int(oracle.get("mismatch_count", 0))
        cm["component_oracle"] = "SDC" if mismatches > 0 else "MASKED"
        cm["component_oracle_category"] = oracle.get("category")
        cm["component_oracle_mismatch_count"] = mismatches
        cm["component_oracle_elements"] = "oracle_elements.json"
        cm["component_oracle_elements_sha256"] = sha256_file(
            attempt / "oracle_elements.json")
    else:
        cm["component_oracle"] = "ORACLE_ERROR"
        cm["component_oracle_error"] = oracle_error
    _write_component_manifest(attempt, cm)
    A.write_audit(attempt)
    R.write_hashes(attempt)
    audit = json.loads((attempt / "audit.json").read_text(encoding="utf-8"))
    cm["component_audit_ok"] = audit.get("ok") is True
    cm["component_certified"] = (audit.get("certified") is True
                                 and status == "admitted")
    if status == "admitted" and not cm["component_certified"]:
        status = "failed"
        cm["component_status"] = "failed"
        cm["component_reason"] = "component audit failed after oracle evidence"
    _write_component_manifest(attempt, cm)
    if status == "admitted":
        comp_seed_dir.mkdir(parents=True, exist_ok=True)
        (comp_seed_dir / "AUTHORITATIVE").write_text(str(attempt),
                                                     encoding="utf-8")
    return {**cm, "ok": status == "admitted"}


def verify_component_attempt(attempt: Path, suite, program, plan_entry=None,
                             asset_root=ROOT):
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
        want = WS.resolved_injector(suite, pid, plan_entry)
        check("manifest injector == resolved per-program injector",
              manifest.get("injector") == want)
        check("manifest effective injector recorded",
              manifest.get("effective_injector") == want)
        overrides = S.normalise_program_overrides(suite) or {}
        check("manifest program_override recorded",
              manifest.get("program_override") ==
              S.program_override_identity(overrides.get(pid)))
        check("manifest binary is the registered program binary",
              Path(str((manifest.get("workload") or {}).get("binary", "")))
              .name == Path(program["binary"]).name)
        check("manifest run_id is the gate id",
              str(manifest.get("run_id", "")).endswith("-GATE"))
        if plan_entry is not None:
            check("manifest seed_plan_entry == pre-registration",
                  manifest.get("seed_plan_entry") ==
                  S.seed_plan_identity(plan_entry))

    cm = {}
    if cm_path.exists():
        try:
            cm = json.loads(cm_path.read_text(encoding="utf-8"))
            check("component manifest identity",
                  cm.get("suite_hash") == WS.compute_suite_hash(suite)
                  and cm.get("program_id") == pid
                  and int(cm.get("program_index", -1))
                  == program["program_index"]
                  and cm.get("component_binary_sha256")
                  == program["binary_sha256"]
                  and cm.get("component_source_sha256")
                  == program["source_sha256"]
                  and cm.get("component_golden_sha256")
                  == program["golden_array_sha256"])
        except (OSError, json.JSONDecodeError):
            check("component manifest identity", False)
            cm = {}
    else:
        check("component_manifest.json exists", False)
    check("component_status == admitted",
          cm.get("component_status") == "admitted")
    check("component_oracle is SDC or MASKED",
          cm.get("component_oracle") in DECIDABLE_ORACLE)
    check("component seed_plan_entry recorded",
          plan_entry is None
          or cm.get("seed_plan_entry") == S.seed_plan_identity(plan_entry))
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
    oracle_consistent = False
    if oracle_path.exists() and array_path.exists() and cm:
        try:
            meta = WO.validate_meta(program["element_oracle"]["meta"])
            golden = _resolve_golden(program, asset_root)
            if array_path.stat().st_size != meta["count"] * WO.ELEM_SIZES[
                    meta["dtype"]]:
                raise WO.W6OracleError("array size mismatch")
            res = WO.compare(str(golden), str(array_path), meta,
                             meta["abs_tol"], meta["rel_tol"],
                             meta["ulp_tol"])
            oracle_consistent = (
                (res["mismatch_count"] > 0) ==
                (cm.get("component_oracle") == "SDC"))
        except (OSError, WO.W6OracleError, ValueError):
            oracle_consistent = False
    check("recorded oracle outcome matches the real arrays",
          oracle_consistent)

    failures = [c["check"] for c in checks if not c["ok"]]
    return {
        "program_id": pid, "program_index": program["program_index"],
        "attempt": str(attempt), "status": "PASS" if not failures else "FAIL",
        "failures": failures, "checks": checks,
        "component_oracle": cm.get("component_oracle"),
        "component_eligible": cm.get("component_eligible"),
        "component_activated": cm.get("component_activated"),
        "component_terminal": cm.get("component_terminal"),
        "ok": not failures,
    }


def _latest_attempt(seed_dir: Path, pid: str, gate_id: str):
    root = Path(seed_dir) / "components" / pid / gate_id
    attempts = sorted(root.glob("seed*/attempt-*")) if root.exists() else []
    return attempts[-1] if attempts else None


def _run_seed_components(suite, info, seed_dir, gate_id, plan_entry, gem5,
                         config, root, timeout, allow_rerun, runner):
    policy = str(suite.get("component_seed_policy_version")
                 or WS.DEFAULT_COMPONENT_SEED_POLICY)
    seeds = WS.derive_component_seeds(
        info["suite_seed"], policy, suite["suite_id"],
        suite["suite_version"])
    by_id = {p["program_id"]: p for p in suite["programs"]}
    records = []
    for pid in WS.W6_PROGRAM_ORDER:
        rec = _run_one_component(
            suite, by_id[pid], info["suite_hash"], info["suite_seed"],
            seeds[pid], policy, seed_dir, gate_id, seed_dir, Path(gem5),
            Path(root), runner, timeout, allow_rerun, plan_entry)
        records.append(rec)
    return records


def _verify_seed_components(suite, info, seed_dir, gate_id, plan_entry,
                            asset_root=ROOT):
    by_id = {p["program_id"]: p for p in suite["programs"]}
    records = []
    for pid in WS.W6_PROGRAM_ORDER:
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
            attempt, suite, by_id[pid], plan_entry, asset_root=asset_root))
    return records


def _write_formal(seed_dir: Path, run_id: str, suite, info, plan_entry,
                  records, ok: bool):
    """Write the formal suite-seed records for a passing W6 gate."""
    seed_dir.mkdir(parents=True, exist_ok=True)
    suite_manifest = {
        "run_id": run_id,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": info["suite_hash"],
        "suite_seed": info["suite_seed"],
        "seed_plan_entry": (S.seed_plan_identity(plan_entry)
                            if plan_entry is not None else None),
        "program_order": list(WS.W6_PROGRAM_ORDER),
        "program_count": WS.W6_PROGRAM_COUNT,
        "component_seed_policy_version": str(
            suite.get("component_seed_policy_version")
            or WS.DEFAULT_COMPONENT_SEED_POLICY),
        "components": records,
    }
    (seed_dir / "suite_manifest.json").write_text(
        json.dumps(suite_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    report = {
        "run_id": run_id,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": info["suite_hash"],
        "suite_seed": info["suite_seed"],
        "program_order": list(WS.W6_PROGRAM_ORDER),
        "program_count": WS.W6_PROGRAM_COUNT,
        "suite_status": "admitted" if ok else "failed",
        "suite_admitted": bool(ok),
        "formal_suite_seed_count": 1 if ok else 0,
        "component_run_count": len(records),
        "component_fault_total": sum(int(r.get("component_faults", 0))
                                     for r in records),
        "components": records,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "counting_note": ("component runs/faults are never seeds; one W6 "
                          "suite seed counts as exactly one admitted seed"),
    }
    (seed_dir / "suite_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    failures = [f"{r.get('program_id')}:{x}" for r in records
                for x in r.get("failures", [])]
    audit = {"ok": bool(ok), "certified": bool(ok),
             "checks": [{"check": "3/3 W6 components PASS", "ok": bool(ok)}],
             "failures": failures,
             "run_id": run_id, "suite_seed": info["suite_seed"],
             "suite_hash": info["suite_hash"]}
    (seed_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (seed_dir / "audit.md").write_text(
        f"# {run_id} seed{info['suite_seed']} W6 suite audit\n\n"
        f"- result: **{'PASS' if ok else 'FAIL'}**\n"
        f"- components: {len(records)}/{WS.W6_PROGRAM_COUNT}\n"
        f"- formal suite seeds: {1 if ok else 0}\n",
        encoding="utf-8")
    if ok:
        (seed_dir / "AUTHORITATIVE").write_text(
            str(seed_dir) + "\n", encoding="utf-8")


def _write_report(outdir: Path, gate_id: str, suite, info, plan_entry,
                  records, formal_run_id=None):
    ok = len(records) == WS.W6_PROGRAM_COUNT and all(r["ok"] for r in records)
    formal = formal_run_id is not None
    if formal:
        _write_formal(outdir, formal_run_id, suite, info, plan_entry,
                      records, ok)
    report = {
        "gate": "W6",
        "gate_id": gate_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "non_formal": not formal,
        "counts_toward_519": False,
        "formal_suite_seed_count": 1 if (formal and ok) else 0,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": info["suite_hash"],
        "freq": _suite_freq(suite),
        "suite_seed": info["suite_seed"],
        "seed_plan_entry": (S.seed_plan_identity(plan_entry)
                            if plan_entry is not None else None),
        "program_order": list(WS.W6_PROGRAM_ORDER),
        "program_count": WS.W6_PROGRAM_COUNT,
        "component_run_count": len(records),
        "component_pass_count": sum(1 for r in records if r["ok"]),
        "records": records,
        "ok": ok,
        "outdir": str(outdir),
    }
    (outdir / "gate_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    lines = [
        f"# {gate_id} — W6 gate（非正式，不计 seed）", "",
        f"- suite：`{suite['suite_id']}` v{suite['suite_version']} "
        f"（freq {_suite_freq(suite)}）",
        f"- suite_hash：`{info['suite_hash']}`",
        f"- suite seed：{info['suite_seed']}"
        + (f" / `{plan_entry['submodel']}`" if plan_entry else ""),
        f"- component runs：{len(records)}；PASS："
        f"{report['component_pass_count']}/{WS.W6_PROGRAM_COUNT}",
        "- 正式 seed 计数：**+0**（gate 不计 519/240）",
        f"- 结论：**{'PASS' if ok else 'FAIL'}**", "",
        "| # | program | precision | lane | mask | oracle | 结论 |",
        "|---|---|---|---|---|---|---|",
    ]
    by_id = {p["program_id"]: p for p in suite["programs"]}
    for i, r in enumerate(records, 1):
        inj = WS.resolved_injector(suite, r["program_id"], plan_entry)
        fpu = inj.get("fpu_mode") or {}
        lines.append(
            f"| {i} | {r['program_id']} | {fpu.get('precision')} | "
            f"{fpu.get('lane_width')} | `{inj.get('fault_mask')}` | "
            f"{r.get('component_oracle', '—')} | "
            f"{'PASS' if r.get('ok') else 'FAIL'} |")
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


def print_commands(suite, info, seed, plan_entry, root, gem5, config,
                   gate_id):
    policy = str(suite.get("component_seed_policy_version")
                 or WS.DEFAULT_COMPONENT_SEED_POLICY)
    seeds = WS.derive_component_seeds(
        seed, policy, suite["suite_id"], suite["suite_version"])
    by_id = {p["program_id"]: p for p in suite["programs"]}
    out = {
        "gate_id": gate_id,
        "suite_id": suite["suite_id"],
        "freq": _suite_freq(suite),
        "suite_hash": info["suite_hash"],
        "suite_seed": seed,
        "seed_plan_entry": (S.seed_plan_identity(plan_entry)
                            if plan_entry is not None else None),
        "commands": [],
    }
    for pid in WS.W6_PROGRAM_ORDER:
        program = by_id[pid]
        spec = _component_run_manifest(
            suite, program, gate_id, seed, seeds[pid], info["suite_hash"],
            policy, plan_entry=plan_entry)
        injector = spec["injector"]
        fpu = injector.get("fpu_mode") or {}
        outdir = (Path(root) / "runs/fsu-gates" / gate_id / "commands" /
                  f"seed{seed}" / pid)
        census = R.build_cmd(spec, outdir / "census", seeds[pid], None,
                             True, Path(gem5), Path(config), Path(root))
        inject = R.build_cmd(spec, outdir / "inject", seeds[pid], 0, False,
                             Path(gem5), Path(config), Path(root))
        out["commands"].append({
            "program_id": pid,
            "program_index": program["program_index"],
            "component_seed": seeds[pid],
            "submodel": spec.get("submodel"),
            "program_override": spec.get("program_override"),
            "precision": fpu.get("precision"),
            "lane_width": fpu.get("lane_width"),
            "lane_offset": fpu.get("lane_offset"),
            "bitseg": fpu.get("bitseg"),
            "permanent_stuck": fpu.get("permanent_stuck"),
            "stuck_polarity": fpu.get("stuck_polarity"),
            "fault_mask": injector.get("fault_mask"),
            "fpu_mode": fpu,
            "census": census,
            "inject": inject,
        })
    return out


def run_gate(suite_path=DEFAULT_SUITE_F0, outdir=None, gem5=DEFAULT_GEM5,
             config=DEFAULT_CONFIG, root=ROOT, timeout=3600, suite_seed=1,
             gate_id=None, allow_rerun=False, verify_only=False, runner=None,
             print_only=False, all_seeds=False, formal_run_id=None):
    root = Path(root)
    # Resolve suite-relative assets against `root` when it holds them,
    # otherwise against the repository root (tests pass a tmp out-root).
    probe = json.loads(Path(suite_path).read_text(encoding="utf-8"))
    asset_root = root
    first_binary = probe["programs"][0]["binary"]
    if not (asset_root / first_binary).exists():
        asset_root = ROOT
    loaded = WS.load_suite(Path(suite_path), root=asset_root,
                           require_hashes=True)
    suite = loaded["suite"]
    info = {"suite_hash": loaded["suite_hash"],
            "identity": loaded["identity"],
            "suite_seed": int(suite_seed)}
    if formal_run_id is not None:
        gate_id = str(formal_run_id)
        outdir = Path(root) / "runs/fsu" / gate_id
    elif gate_id is None:
        gate_id = default_gate_id(suite)
    if outdir is None:
        outdir = Path(root) / default_outdir(suite).relative_to(ROOT)
    outdir = Path(outdir)
    if formal_run_id is None:
        _assert_gate_outdir(outdir, root)
    plan_entry = S.seed_plan_entry(suite, suite_seed)
    if plan_entry is None and _suite_freq(suite) == "F5":
        raise WS.W6SuiteError("an F5 W6 gate needs a seed_plan entry")
    if print_only:
        seeds = ([1, 2, 3] if (all_seeds and
                               S.seed_plan_map(suite) is not None)
                 else [suite_seed])
        out = {"gate_id": gate_id,
               "suite_hash": info["suite_hash"],
               "freq": _suite_freq(suite),
               "seeds": []}
        for seed in seeds:
            entry = S.seed_plan_entry(suite, seed)
            sinfo = {**info, "suite_seed": seed}
            out["seeds"].append(print_commands(
                suite, sinfo, seed, entry, root, gem5, config, gate_id))
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    outdir.mkdir(parents=True, exist_ok=True)
    seed_dir = outdir / f"seed{suite_seed}"
    # Suite-relative golden paths are resolved against `root` when it holds
    # the assets, otherwise against the repository root (tests pass a tmp
    # out-root while the real golden arrays stay in the repo).
    asset_root = Path(root)
    first = suite["programs"][0]["element_oracle"]["golden_array"]
    if not (asset_root / first).exists():
        asset_root = ROOT
    if verify_only:
        records = _verify_seed_components(suite, info, seed_dir, gate_id,
                                          plan_entry, asset_root=asset_root)
    else:
        records = _run_seed_components(
            suite, info, seed_dir, gate_id, plan_entry, gem5, config,
            asset_root, timeout, allow_rerun, runner)
    report_dir = (outdir / f"seed{suite_seed}" if formal_run_id is not None
                  else outdir)
    return _write_report(report_dir, gate_id, suite, info, plan_entry,
                         records, formal_run_id=formal_run_id)


def main(argv=None):
    ap = argparse.ArgumentParser(description="W6 (SVD/FFT/sparse) gate")
    ap.add_argument("--suite", default=str(DEFAULT_SUITE_F0))
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--gem5", default=str(DEFAULT_GEM5))
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--suite-seed", type=int, default=1)
    ap.add_argument("--gate-id", default=None)
    ap.add_argument("--allow-rerun", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--print-commands", action="store_true")
    ap.add_argument("--all-seeds", action="store_true")
    ap.add_argument("--formal-run-id", default=None,
                    help="write a formal suite seed under runs/fsu/<RunID>")
    a = ap.parse_args(argv)
    try:
        res = run_gate(Path(a.suite), Path(a.outdir) if a.outdir else None,
                       Path(a.gem5), Path(a.config), Path(a.root), a.timeout,
                       a.suite_seed, a.gate_id, a.allow_rerun, a.verify_only,
                       print_only=a.print_commands, all_seeds=a.all_seeds,
                       formal_run_id=a.formal_run_id)
    except WS.W6SuiteError as e:
        print(json.dumps({"ok": False, "reason": str(e)},
                         ensure_ascii=False, indent=2))
        return 2
    if a.print_commands:
        return res
    print(json.dumps({"ok": res["ok"], "gate_id": res["gate_id"],
                      "component_pass_count": res["component_pass_count"],
                      "outdir": res.get("outdir", "")},
                     ensure_ascii=False, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
