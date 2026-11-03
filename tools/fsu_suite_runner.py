#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_suite_runner.py — W5 固定 suite seed 运行器。

一个 formal suite seed 固定包含 5 个 component run（每个只跑一个程序、
只注入一次故障），顺序永为 gemm → 2mm → lu → cholesky → jacobi-2d。

路径：
  runs/fsu/<RunID>/seed<N>/components/<program_id>/<RunID>/seed<derived>/attempt-k/

规则：
  - component seed 由 fsu_suite.derive_component_seed 派生，不使用 suite seed；
  - component manifest 由本 runner 生成，绑定 suite_hash / program_id /
    program_index / component attempt / 三类 SHA / 结局；
  - 任一 component 失败 → suite seed 不 admitted、不写 AUTHORITATIVE，
    失败 attempt 保留；重试只新建 attempt，不覆盖旧 attempt；
  - 只有 5/5 component 独立 audit.ok + certified + oracle 非 SimulatorError/
    Inactive 时，才写 suite_manifest.json / suite_report.json / audit.json /
    suite Markdown，最后写 AUTHORITATIVE；
  - component 数绝不进入 seed 正式计数：一个 suite seed = +1。
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_oracle as O  # noqa: E402
import fsu_prop_fields as P  # noqa: E402
import fsu_seed_audit as A  # noqa: E402
import fsu_seed_runner as R  # noqa: E402
import fsu_suite as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = ROOT / "configs/fsu/suites/polybench-fp-v1.json"
DEFAULT_OUT = ROOT / "runs/fsu"
DEFAULT_GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"


def _resolve(path, root: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(root) / p


def _sha(path: Path) -> str:
    return S.sha256_file(path)


def load_suite(path: Path, root: Path = ROOT):
    """Load + validate a suite manifest and verify on-disk identities."""
    suite = json.loads(Path(path).read_text(encoding="utf-8"))
    info = S.validate_suite_manifest(suite, require_hashes=True,
                                     require_suite_hash=True)
    injector = suite.get("injector") or {}
    try:
        max_faults = int(injector.get("max_faults"))
    except (TypeError, ValueError):
        raise S.SuiteError("suite.injector.max_faults must be 1")
    if max_faults != 1:
        raise S.SuiteError("a component run injects exactly one fault "
                           f"(max_faults must be 1, got {max_faults})")
    if not isinstance(injector.get("fpu_mode"), dict):
        raise S.SuiteError("suite.injector.fpu_mode is required")
    defaults = suite.get("run_defaults") or {}
    if str(defaults.get("freq", "") or "").strip() == "F5":
        # [FSU][F5] An F5 suite must carry a frozen 3-seed plan and a
        # permanent-stuck component fault; a suite without them is refused
        # before any attempt directory is created.
        if S.seed_plan_map(suite) is None:
            raise S.SuiteError("an F5 suite must pre-register a seed_plan")
        if str(injector.get("component", "")) != "fsu":
            raise S.SuiteError("an F5 suite component must be 'fsu'")
        fpu = injector.get("fpu_mode") or {}
        if fpu.get("permanent_stuck") is not True:
            raise S.SuiteError(
                "an F5 suite requires fpu_mode.permanent_stuck == true")
        for entry in S.normalise_seed_plan(suite):
            if entry["permanent_stuck"] is not True:
                raise S.SuiteError(
                    f"seed_plan seed{entry['suite_seed']} must set "
                    "permanent_stuck == true")
    for p in suite["programs"]:
        pid = p["program_id"]
        for kind in ("source", "binary"):
            path_obj = _resolve(p.get(kind, ""), root)
            if not path_obj.exists():
                raise S.SuiteError(f"{pid}: {kind} missing: {path_obj}")
            got = _sha(path_obj)
            want = S._check_hash(p.get(f"{kind}_sha256"), f"{pid}.{kind}",
                                 allow_pending=False)
            if got != want:
                raise S.SuiteError(
                    f"{pid}: {kind} SHA drift: {got} != manifest {want}")
        # W5 certification requires the pre-registered element oracle; a
        # missing golden array is a loud refusal, never a silent fallback to
        # the legacy 16-hex FINAL hash.
        eo = p.get("element_oracle")
        if not isinstance(eo, dict):
            raise S.SuiteError(f"{pid}: element_oracle is required for W5")
        try:
            meta = O.validate_meta(eo.get("meta") or {})
        except O.OracleError as e:
            raise S.SuiteError(f"{pid}: invalid element_oracle meta: {e}")
        if meta["program_id"] != pid:
            raise S.SuiteError(
                f"{pid}: element_oracle meta program_id drift: "
                f"{meta['program_id']}")
        if str(eo.get("oracle_version")) != meta["oracle_version"]:
            raise S.SuiteError(
                f"{pid}: element_oracle oracle_version drift")
        golden = _resolve(eo.get("golden_array", ""), root)
        if not golden.exists():
            raise S.SuiteError(
                f"{pid}: golden array missing: {golden} "
                "(element-oracle gate not yet generated; W5 remains BLOCKED)")
    return suite, info


def _component_seed_dir(seed_dir: Path, program_id: str, run_id: str,
                        component_seed: int) -> Path:
    return (Path(seed_dir) / "components" / program_id / run_id /
            f"seed{component_seed}")


def _program_override(suite, program_id):
    overrides = S.normalise_program_overrides(suite)
    if overrides is None:
        return None
    return overrides.get(program_id)


def _component_run_manifest(suite, program, run_id, suite_seed,
                            component_seed, suite_hash, policy_version,
                            plan_entry=None):
    defaults = copy.deepcopy(suite.get("run_defaults") or {})
    override = _program_override(suite, program["program_id"])
    # Application order: suite.injector -> program_overrides[pid] ->
    # seed_plan. Omitted seed_plan geometry fields inherit the per-program
    # override (W6 SVD fp64 vs FFT/sparse fp32).
    injector = S.resolve_program_injector(
        suite.get("injector") or {}, override, plan_entry,
        program["program_id"])
    if plan_entry is not None:
        defaults["submodel"] = plan_entry["submodel"]
    limits = copy.deepcopy(defaults.pop("limits", {}) or {})
    workload = {
        "binary": str(program["binary"]),
        "source": str(program.get("source", "")),
        "identity": f"W5-polybench-{program['program_id']}-v1",
        "golden": program.get("golden", ""),
        "oracle_kind": (suite.get("oracle") or {}).get("kind", "exact_hash"),
        "oracle_tol": int((suite.get("oracle") or {}).get("tol", 0)),
    }
    if program.get("element_oracle") is not None:
        workload["element_oracle"] = copy.deepcopy(program["element_oracle"])
    component = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": suite_hash,
        "suite_seed": suite_seed,
        "program_id": program["program_id"],
        "program_index": program["program_index"],
        "program_count": S.PROGRAM_COUNT,
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
        "notes": ("W5 suite component run: exactly one program and exactly "
                  "one injected fault; not a formal suite seed by itself."),
    }
    out["program_override"] = (
        S.program_override_identity(override) if override else None)
    out["effective_injector"] = copy.deepcopy(injector)
    if plan_entry is not None:
        out["seed_plan_entry"] = S.seed_plan_identity(plan_entry)
        out["pre_registration"] = copy.deepcopy(out["seed_plan_entry"])
    return out


def _activated_count(attempt: Path) -> int:
    """Count distinct fault_ids with a real activated operand_read (L2)."""
    prop = attempt / "inject/prop_evt.txt.gz"
    if not prop.exists():
        return 0
    events, _, _ = P.read_stream(prop)
    return len({str(e.get("fault_id")) for e in events
                if str(e.get("kind")) == "operand_read"
                and str(e.get("activated")).strip() == "1"})


def _primary_terminal(report: dict):
    chain = report.get("chain") or {}
    for fid, f in sorted((chain.get("faults") or {}).items()):
        if f.get("admitted"):
            return f.get("terminal")
    for fid, f in sorted((chain.get("faults") or {}).items()):
        return f.get("terminal")
    return None


def _element_oracle_result(attempt: Path, program: dict, root: Path) -> dict:
    """Run the pre-registered element oracle on inject/array.bin."""
    eo = program.get("element_oracle") or {}
    meta = dict(eo.get("meta") or {})
    golden_path = _resolve(eo.get("golden_array", ""), root)
    fault_path = attempt / "inject/array.bin"
    if not fault_path.exists():
        raise S.SuiteError(
            f"{program['program_id']}: missing {fault_path} "
            "(--array-dump was not produced)")
    if not golden_path.exists():
        raise S.SuiteError(
            f"{program['program_id']}: golden array missing: {golden_path}")
    result = O.compare(
        golden_path.read_bytes(), fault_path.read_bytes(), meta,
        meta.get("abs_tol"), meta.get("rel_tol"), meta.get("ulp_tol"))
    payload = O.json_ready(result)
    payload["golden_array"] = str(golden_path)
    payload["fault_array"] = str(fault_path)
    payload["ok"] = True
    (attempt / "oracle_elements.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _write_oracle_error(attempt: Path, program: dict, root: Path,
                        error: str) -> dict:
    eo = program.get("element_oracle") or {}
    payload = {
        "ok": False,
        "program_id": program["program_id"],
        "error": error,
        "golden_array": str(_resolve(eo.get("golden_array", ""), root)),
        "fault_array": str(attempt / "inject/array.bin"),
        "oracle_version": eo.get("oracle_version"),
    }
    (attempt / "oracle_elements.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _oracle_evidence_ok(attempt: Path) -> bool:
    """oracle_elements.json and inject/array.bin must be in evidence hashes."""
    oracle_path = attempt / "oracle_elements.json"
    array_path = attempt / "inject/array.bin"
    hp = attempt / "evidence_sha256.json"
    if not (oracle_path.exists() and array_path.exists() and hp.exists()):
        return False
    try:
        hashes = json.loads(hp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        hashes.get("oracle_elements.json") == _sha(oracle_path)
        and hashes.get("inject/array.bin") == _sha(array_path))


def _component_manifest(suite, program, suite_hash, suite_seed, component_seed,
                        policy_version, attempt: Path, status: str,
                        audit_ok: bool, certified: bool, root: Path = ROOT,
                        plan_entry=None):
    report_path = attempt / "chain_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    else:
        # Failure before injection (e.g. census eligible=0 or timeout): the
        # component is still recorded honestly with no chain/oracle data.
        report = {}
    oracle = report.get("oracle") or {}
    golden_sha, golden_scheme = S.component_golden_sha256(program)
    manifest_path = attempt / "manifest.json"
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
        "suite_seed": suite_seed,
        "program_id": program["program_id"],
        "program_index": program["program_index"],
        "program_count": S.PROGRAM_COUNT,
        "component_seed_policy_version": policy_version,
        "component_seed": component_seed,
        "component_attempt": attempt_no,
        "component_manifest_sha256": _sha(manifest_path),
        "component_binary_sha256": (
            _sha(_resolve(program["binary"], root))
            if _resolve(program["binary"], root).exists()
            else program.get("binary_sha256", "0" * 64)),
        "component_source_sha256": program["source_sha256"],
        "component_golden_sha256": golden_sha,
        "component_golden_sha256_scheme": golden_scheme,
        "component_golden": program.get("golden"),
        "component_status": status,
        "component_eligible": int(oracle.get("eligible_count", 0) or 0),
        "component_activated": _activated_count(attempt),
        "component_faults": int(report.get("actual_injections",
                                           oracle.get("faults_injected", 0))
                                or 0),
        "component_terminal": _primary_terminal(report),
        # The authoritative W5 outcome is the element oracle; a run that
        # never reached it is explicitly NOT_EVALUATED, never relabelled.
        "component_oracle": "NOT_EVALUATED",
        "component_run_level_oracle": str(oracle.get("category") or "Unknown"),
        "component_audit_ok": bool(audit_ok),
        "component_certified": bool(certified),
        "attempt": str(attempt),
    }
    override = _program_override(suite, program["program_id"])
    out["program_override"] = (
        S.program_override_identity(override) if override else None)
    out["effective_injector"] = S.resolve_program_injector(
        suite.get("injector") or {}, override, plan_entry,
        program["program_id"])
    if plan_entry is not None:
        out["seed_plan_entry"] = S.seed_plan_identity(plan_entry)
    return out


def _write_component_manifest(attempt: Path, manifest: dict):
    (attempt / "component_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    # Evidence hash coverage must include the suite-generated component
    # manifest (audit.json/audit.md stay excluded by run_seed's rule).
    R.write_hashes(attempt)


def _reuse_component(seed_dir: Path, program_id: str, run_id: str,
                     component_seed: int, suite, suite_hash: str,
                     suite_seed: int, policy_version: str, plan_entry=None):
    """Reuse an already-admitted component attempt without re-running gem5."""
    comp_seed_dir = _component_seed_dir(seed_dir, program_id, run_id,
                                        component_seed)
    auth = comp_seed_dir / "AUTHORITATIVE"
    if not auth.exists():
        return None
    attempt = Path(auth.read_text(encoding="utf-8").strip())
    cm_path = attempt / "component_manifest.json"
    audit_path = attempt / "audit.json"
    if not (attempt.is_dir() and cm_path.exists() and audit_path.exists()):
        return None
    try:
        cm = json.loads(cm_path.read_text(encoding="utf-8"))
        S.validate_component_manifest(cm, suite)
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, S.SuiteError):
        return None
    manifest_path = attempt / "manifest.json"
    if not manifest_path.exists() or _sha(manifest_path) != cm.get(
            "component_manifest_sha256"):
        return None
    if not (audit.get("ok") is True and audit.get("certified") is True):
        return None
    if cm.get("component_status") != "admitted":
        return None
    # Element oracle is mandatory for W5: a legacy component without a
    # matching oracle_elements.json must be rerun, never silently reused.
    if cm.get("component_oracle") not in ("SDC", "MASKED"):
        return None
    if not _oracle_evidence_ok(attempt):
        return None
    # Suite/seed/order identity must match this run, not just the program id.
    if (cm.get("suite_hash") != suite_hash
            or int(cm.get("suite_seed", -1)) != int(suite_seed)
            or int(cm.get("component_seed", -1)) != int(component_seed)
            or cm.get("suite_id") != suite.get("suite_id")
            or cm.get("program_id") != program_id
            or int(cm.get("program_index", -1))
            != S.PROGRAM_ORDER.index(program_id)
            or cm.get("component_seed_policy_version") != policy_version):
        return None
    if plan_entry is not None and cm.get("seed_plan_entry") != \
            S.seed_plan_identity(plan_entry):
        return None
    overrides = S.normalise_program_overrides(suite)
    if overrides is not None:
        want = overrides.get(program_id)
        want = S.program_override_identity(want) if want else None
        got = cm.get("program_override")
        if (want is None and got not in (None, {})) or \
                (want is not None and got != want):
            return None
    return cm


def _run_one_component(suite, program, suite_hash, suite_seed, component_seed,
                       policy_version, seed_dir: Path, run_id: str,
                       out_root: Path, gem5: Path, root: Path, runner,
                       timeout_s, allow_rerun: bool, plan_entry=None):
    pid = program["program_id"]
    component_root = Path(seed_dir) / "components" / pid
    component_root.mkdir(parents=True, exist_ok=True)
    comp_seed_dir = _component_seed_dir(seed_dir, pid, run_id, component_seed)

    if not allow_rerun:
        reused = _reuse_component(seed_dir, pid, run_id, component_seed,
                                  suite, suite_hash, suite_seed,
                                  policy_version, plan_entry=plan_entry)
        if reused is not None:
            return {**reused, "reused": True}

    spec = _component_run_manifest(suite, program, run_id, suite_seed,
                                   component_seed, suite_hash, policy_version,
                                   plan_entry=plan_entry)
    spec_path = component_root / f"manifest-seed{component_seed}.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    # If an AUTHORITATIVE exists but its evidence is invalid, a new attempt
    # must be allowed; never overwrite the old attempt.
    rerun = allow_rerun or (comp_seed_dir / "AUTHORITATIVE").exists()
    res = R.run_seed(
        spec_path, component_seed, out_root=out_root, gem5=gem5, root=root,
        runner=runner, timeout_s=timeout_s, allow_rerun=rerun,
        seed_dir=comp_seed_dir,
        component=spec["component"], write_authoritative=False,
        copy_to_complete=False)

    if res.get("status") == "already_admitted":
        attempt = Path(res.get("authoritative", ""))
    else:
        attempt = Path(res.get("attempt", ""))
    if not attempt.is_dir():
        # Hard failure before an attempt existed: nothing to certify.
        return {
            "suite_id": suite["suite_id"], "suite_version": suite["suite_version"],
            "suite_hash": suite_hash, "suite_seed": suite_seed,
            "program_id": pid, "program_index": program["program_index"],
            "program_count": S.PROGRAM_COUNT,
            "component_seed_policy_version": policy_version,
            "component_seed": component_seed, "component_attempt": 0,
            "component_manifest_sha256": "0" * 64,
            "component_binary_sha256": program.get("binary_sha256", "0" * 64),
            "component_source_sha256": program["source_sha256"],
            "component_golden_sha256":
                S.component_golden_sha256(program)[0],
            "component_status": "failed", "component_eligible": 0,
            "component_activated": 0, "component_faults": 0,
            "component_terminal": None, "component_oracle": "NOT_EVALUATED",
            "component_audit_ok": False, "component_certified": False,
            "attempt": str(attempt), "run_status": res.get("status"),
            "reason": res.get("reason", "no attempt created"),
            "program_override": (
                S.program_override_identity(
                    _program_override(suite, pid))
                if _program_override(suite, pid) else None),
            **({"seed_plan_entry": S.seed_plan_identity(plan_entry)}
               if plan_entry is not None else {}),
        }

    if res.get("status") != "admitted":
        audit_ok = certified = False
        status = ("not_activated" if res.get("status") == "not_activated"
                  else "failed")
        cm = _component_manifest(suite, program, suite_hash, suite_seed,
                                 component_seed, policy_version, attempt,
                                 status, audit_ok, certified, root,
                                 plan_entry=plan_entry)
        cm["run_status"] = res.get("status")
        cm["reason"] = res.get("reason")
        _write_component_manifest(attempt, cm)
        return {**cm, "reused": False}

    # 1) Element-wise oracle: compare the golden array against the real
    #    inject/array.bin. Missing dump or oracle failure blocks the suite.
    oracle_result = None
    oracle_error = None
    try:
        oracle_result = _element_oracle_result(attempt, program, root)
    except (S.SuiteError, O.OracleError, OSError, ValueError) as e:
        oracle_error = f"{type(e).__name__}: {e}"
        _write_oracle_error(attempt, program, root, oracle_error)
    oracle_ok = oracle_result is not None and oracle_result.get("ok") is True

    # 2) Independent component audit is mandatory before certification.
    A.write_audit(attempt)
    audit = json.loads((attempt / "audit.json").read_text(encoding="utf-8"))
    audit_ok = audit.get("ok") is True
    certified = audit.get("certified") is True
    status = ("admitted" if (audit_ok and certified and oracle_ok)
              else "failed")
    cm = _component_manifest(suite, program, suite_hash, suite_seed,
                             component_seed, policy_version, attempt,
                             status, audit_ok, certified, root,
                             plan_entry=plan_entry)
    if oracle_ok:
        mismatches = int(oracle_result.get("mismatch_count", 0))
        cm["component_oracle"] = "SDC" if mismatches > 0 else "MASKED"
        cm["component_oracle_category"] = oracle_result.get("category")
        cm["component_oracle_mismatch_count"] = mismatches
        cm["component_oracle_elements"] = "oracle_elements.json"
        cm["component_oracle_elements_sha256"] = _sha(
            attempt / "oracle_elements.json")
    else:
        cm["component_oracle"] = "ORACLE_ERROR"
        cm["component_oracle_error"] = oracle_error
        cm["component_oracle_elements"] = "oracle_elements.json"
    _write_component_manifest(attempt, cm)

    # 3) Certification requires the oracle + array SHA to be part of the
    #    evidence manifest (no out-of-band oracle claims).
    evidence_ok = _oracle_evidence_ok(attempt)
    if status == "admitted" and not evidence_ok:
        status = "failed"
        cm["component_status"] = "failed"
        cm["component_reason"] = "oracle evidence not covered by SHA-256"
        (attempt / "component_manifest.json").write_text(
            json.dumps(cm, ensure_ascii=False, indent=2), encoding="utf-8")
        R.write_hashes(attempt)

    # 4) Re-run the audit so its embedded evidence hash list covers the
    #    suite-generated component manifest and element-oracle evidence.
    A.write_audit(attempt)
    R.write_hashes(attempt)
    audit = json.loads((attempt / "audit.json").read_text(encoding="utf-8"))
    audit_ok = audit.get("ok") is True
    certified = audit.get("certified") is True
    if status == "admitted" and not (audit_ok and certified):
        status = "failed"
        cm["component_reason"] = "component audit failed after oracle evidence"
        (attempt / "component_manifest.json").write_text(
            json.dumps(cm, ensure_ascii=False, indent=2), encoding="utf-8")
        R.write_hashes(attempt)
    cm["component_audit_ok"] = bool(audit_ok)
    cm["component_certified"] = bool(certified and status == "admitted")
    cm["component_status"] = status
    (attempt / "component_manifest.json").write_text(
        json.dumps(cm, ensure_ascii=False, indent=2), encoding="utf-8")
    R.write_hashes(attempt)

    if status == "admitted":
        comp_seed_dir.mkdir(parents=True, exist_ok=True)
        (comp_seed_dir / "AUTHORITATIVE").write_text(str(attempt),
                                                     encoding="utf-8")
    else:
        comp_seed_dir.mkdir(parents=True, exist_ok=True)
        (comp_seed_dir / ".failed").write_text(
            f"component not certified for {pid}: "
            f"oracle_error={oracle_error} evidence_ok={evidence_ok}\n",
            encoding="utf-8")
    return {**cm, "reused": False}


def _suite_markdown(seed_dir: Path, suite_manifest: dict, report: dict):
    comps = suite_manifest["components"]
    lines = [
        f"# {report['run_id']} seed{report['suite_seed']} 正式 suite seed",
        "",
        "> 本文件是 **formal suite seed** 级记录，不是单个 PolyBench 程序。",
        "> 一次 formal suite seed 固定包含 **5 个 component run**；",
        "> 正式计数只 **+1 seed**，绝不把 component 数当 seed 数。",
        "",
        "## 身份",
        "",
        "| 项 | 值 |", "|---|---|",
        f"| suite_id / version | `{report['suite_id']}` / `{report['suite_version']}` |",
        f"| suite_hash | `{report['suite_hash']}` |",
        f"| suite seed | {report['suite_seed']} |",
        f"| program_order | {' → '.join(report['program_order'])} |",
        f"| component seed policy | `{report['component_seed_policy_version']}` |",
        f"| 正式 seed 计数 | +{report['formal_suite_seed_count']}（component run 不算 seed） |",
        "",
        "## Component runs",
        "",
        "| # | program | component seed | attempt | eligible | activated | "
        "fault | terminal | oracle | audit.ok | certified | 链接 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, c in enumerate(comps, 1):
        attempt = Path(c["attempt"])
        try:
            rel = attempt.relative_to(seed_dir)
        except ValueError:
            rel = attempt
        lines.append(
            f"| {i} | {c['program_id']} | {c['component_seed']} | "
            f"{c['component_attempt']} | {c['component_eligible']} | "
            f"{c['component_activated']} | {c.get('component_faults', 0)} | "
            f"{c['component_terminal']} | {c['component_oracle']} | "
            f"{c['component_audit_ok']} | {c['component_certified']} | "
            f"[attempt]({rel}) |")
    lines += [
        "",
        "## 计数规则",
        "",
        "- 本 suite seed：**1** 个 formal suite seed。",
        "- 本 suite seed 含 **5** 个 component run、"
        f"**{report['component_fault_total']}** 次 component fault。",
        "- component run / component fault 数量不进入 `admitted_seeds_total`；",
        "  3 个 suite seed = 15 个 component run，但正式计数只 +3。",
        "",
        "## 认证条件",
        "",
        "- 5/5 component 均 admitted、独立 `audit.ok=true`、"
        "`certified=true`、oracle 非 SimulatorError/Inactive。",
        "- 任一 component 失败 → 整个 suite seed 不认证；失败 attempt 保留，"
        "重试新建 attempt，不覆盖。",
        "",
    ]
    return "\n".join(lines)


def _append_failure_history(seed_dir: Path, payload: dict):
    seed_dir.mkdir(parents=True, exist_ok=True)
    with open(seed_dir / "suite_failures.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def run_suite(suite_path: Path = DEFAULT_SUITE, suite_seed: int = 1,
              run_id: str = "", out_root: Path = DEFAULT_OUT,
              gem5: Path = DEFAULT_GEM5, root: Path = ROOT, runner=None,
              timeout_s=None, allow_rerun: bool = False):
    """Run one formal W5 suite seed (5 fixed component runs)."""
    if not run_id:
        raise S.SuiteError("run_id is required for a formal suite seed")
    suite, info = load_suite(Path(suite_path), Path(root))
    suite_hash = info["suite_hash"]
    policy_version = str(suite.get("component_seed_policy_version")
                         or S.DEFAULT_COMPONENT_SEED_POLICY)
    seed_dir = Path(out_root) / run_id / f"seed{int(suite_seed)}"

    # Drift is checked before any attempt is created.
    if seed_dir.exists():
        sm_path = seed_dir / "suite_manifest.json"
        if sm_path.exists():
            try:
                prev = json.loads(sm_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                raise S.SuiteError(f"unreadable suite_manifest: {e}")
            if str(prev.get("suite_hash")) != suite_hash:
                raise S.SuiteError(
                    "suite_hash drift for existing suite seed: "
                    f"{prev.get('suite_hash')} != {suite_hash}")
            if str(prev.get("run_id")) != run_id:
                raise S.SuiteError("existing suite_manifest run_id drift")
            if int(prev.get("suite_seed", -1)) != int(suite_seed):
                raise S.SuiteError("existing suite_manifest suite_seed drift")
        auth = seed_dir / "AUTHORITATIVE"
        if auth.exists() and not allow_rerun:
            return {"status": "already_admitted",
                    "suite_seed_dir": str(seed_dir),
                    "authoritative": auth.read_text(
                        encoding="utf-8").strip()}

    seed_dir.mkdir(parents=True, exist_ok=True)
    derived = S.derive_component_seeds(
        int(suite_seed), policy_version, suite["suite_id"],
        suite["suite_version"])
    # [FSU][F5] Every component run inside one suite seed is driven by the
    # SAME pre-registered seed_plan entry (identical submodel/mask/polarity/
    # warm-up/sampling for all five programs). A missing seed is refused
    # (seed_plan_entry raises) instead of silently falling back to the base
    # injector.
    plan_entry = S.seed_plan_entry(suite, int(suite_seed))

    results = []
    for pid in S.PROGRAM_ORDER:
        program = next(p for p in suite["programs"]
                       if p["program_id"] == pid)
        results.append(_run_one_component(
            suite, program, suite_hash, int(suite_seed), derived[pid],
            policy_version, seed_dir, run_id, Path(out_root), Path(gem5),
            Path(root), runner, timeout_s, allow_rerun,
            plan_entry=plan_entry))

    admitted = all(c.get("component_status") == "admitted"
                   and c.get("component_audit_ok") is True
                   and c.get("component_certified") is True
                   for c in results) and len(results) == S.PROGRAM_COUNT
    pre_report = {
        "run_id": run_id,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": suite_hash,
        "suite_seed": int(suite_seed),
        "program_order": list(S.PROGRAM_ORDER),
        "program_count": S.PROGRAM_COUNT,
        "component_seed_policy_version": policy_version,
        "suite_status": "admitted" if admitted else "failed",
        "suite_admitted": bool(admitted),
        "formal_suite_seed_count": 1 if admitted else 0,
        "component_run_count": len(results),
        "component_fault_total": sum(int(c.get("component_faults", 0))
                                     for c in results),
        "component_eligible_total": sum(int(c.get("component_eligible", 0))
                                        for c in results),
        "component_activated_total": sum(int(c.get("component_activated", 0))
                                         for c in results),
        "components": results,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "counting_note": ("component runs/faults are never seeds; one suite "
                          "seed counts as exactly one admitted seed"),
    }

    if not admitted:
        (seed_dir / "suite_report.json").write_text(
            json.dumps(pre_report, ensure_ascii=False, indent=2),
            encoding="utf-8")
        failed = [c["program_id"] for c in results
                  if c.get("component_status") != "admitted"]
        (seed_dir / ".failed").write_text(
            "suite not admitted; failed components: "
            + ", ".join(failed) + "\n", encoding="utf-8")
        _append_failure_history(seed_dir, {
            "at": datetime.now().isoformat(timespec="seconds"),
            "run_id": run_id, "suite_seed": int(suite_seed),
            "suite_hash": suite_hash, "failed_components": failed,
        })
        return {"status": "failed", "suite_seed_dir": str(seed_dir),
                "failed_components": failed, "report": pre_report}

    components = [{
        key: c.get(key) for key in (
            "suite_id", "suite_version", "suite_hash", "suite_seed",
            "program_id", "program_index", "program_count",
            "component_seed_policy_version", "component_seed",
            "component_attempt", "component_manifest_sha256",
            "component_binary_sha256", "component_source_sha256",
            "component_golden_sha256", "component_status",
            "component_eligible", "component_activated", "component_faults",
            "component_terminal", "component_oracle",
            "component_audit_ok", "component_certified", "attempt",
            "seed_plan_entry", "program_override")
    } for c in results]
    suite_manifest = {
        "suite": suite,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": suite_hash,
        "suite_seed": int(suite_seed),
        "run_id": run_id,
        "program_order": list(S.PROGRAM_ORDER),
        "program_count": S.PROGRAM_COUNT,
        "component_seed_policy_version": policy_version,
        "components": components,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (seed_dir / "suite_manifest.json").write_text(
        json.dumps(suite_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (seed_dir / "suite_report.json").write_text(
        json.dumps(pre_report, ensure_ascii=False, indent=2), encoding="utf-8")

    audit = A.write_suite_audit(seed_dir)
    md_path = seed_dir / f"{run_id}-seed{int(suite_seed)}.md"
    md_path.write_text(_suite_markdown(seed_dir, suite_manifest, pre_report),
                       encoding="utf-8")
    if audit.get("ok") is not True:
        pre_report["suite_status"] = "failed"
        pre_report["suite_admitted"] = False
        pre_report["formal_suite_seed_count"] = 0
        pre_report["suite_audit_failures"] = audit.get("failures", [])
        (seed_dir / "suite_report.json").write_text(
            json.dumps(pre_report, ensure_ascii=False, indent=2),
            encoding="utf-8")
        (seed_dir / ".failed").write_text(
            "suite audit failed after 5/5 component runs: "
            + "; ".join(audit.get("failures", [])[:5]) + "\n",
            encoding="utf-8")
        _append_failure_history(seed_dir, {
            "at": datetime.now().isoformat(timespec="seconds"),
            "run_id": run_id, "suite_seed": int(suite_seed),
            "suite_hash": suite_hash, "audit_failures": audit.get("failures"),
        })
        return {"status": "failed", "suite_seed_dir": str(seed_dir),
                "reason": "suite audit failed", "audit": audit,
                "report": pre_report}

    (seed_dir / ".done").write_text("admitted\n", encoding="utf-8")
    stale_failed = seed_dir / ".failed"
    if stale_failed.exists():
        stale_failed.unlink()
    # [W5] The authoritative directory carries exactly ONE suite-level
    # Markdown per formal suite seed (the five component runs are linked from
    # it; they are never copied here as if they were formal seeds).
    complete_dir = (Path(out_root) / "COMPLETE_PROPAGATION_PATHS" / run_id)
    complete_dir.mkdir(parents=True, exist_ok=True)
    complete_md = complete_dir / f"{run_id}-seed{int(suite_seed)}.md"
    shutil.copy2(md_path, complete_md)
    # AUTHORITATIVE is written last, only after all evidence exists.
    (seed_dir / "AUTHORITATIVE").write_text(str(seed_dir), encoding="utf-8")
    return {"status": "admitted", "suite_seed_dir": str(seed_dir),
            "suite_hash": suite_hash, "suite_seed": int(suite_seed),
            "component_runs": len(results),
            "formal_suite_seed_increment": 1,
            "markdown": str(md_path), "audit": audit,
            "report": pre_report}


def main(argv=None):
    ap = argparse.ArgumentParser(description="FSU W5 固定 suite seed 运行器")
    ap.add_argument("--suite", default=str(DEFAULT_SUITE))
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--suite-seed", type=int, required=True)
    ap.add_argument("--out-root", default=str(DEFAULT_OUT))
    ap.add_argument("--gem5", default=str(DEFAULT_GEM5))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--timeout", type=int, default=None)
    ap.add_argument("--allow-rerun", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = run_suite(Path(a.suite), a.suite_seed, a.run_id,
                        Path(a.out_root), Path(a.gem5), Path(a.root),
                        timeout_s=a.timeout, allow_rerun=a.allow_rerun)
    except S.SuiteError as e:
        print(json.dumps({"status": "rejected", "reason": str(e)},
                         ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["status"] in ("admitted", "already_admitted") else 1


if __name__ == "__main__":
    sys.exit(main())
