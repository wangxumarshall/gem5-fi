#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_suite_audit.py — unified, recomputed audit of one FSU suite seed.

Scope
-----
W5 (PolyBench-FP: gemm/2mm/lu/cholesky/jacobi-2d) and W6
(svd/fft/sparse-cg) fixed suites. One suite seed is exactly ONE formal seed;
its component runs/faults never add to the seed count.

This tool does not trust the legacy W5/W6 suite audit.json. It re-derives the
result from the raw component evidence on disk:

  * the frozen suite plan and suite_hash come from
    configs/fsu/suites/<suite_id>.json (or --suite-config);
  * the program set, order and count must match that frozen plan exactly
    (missing, duplicate and unexpected programs are loud violations);
  * every component must belong to the same suite_hash / suite_seed / plan;
  * every component artifact (manifest, audit, chain_report, oracle,
    oracle_elements, array, stats) must exist and every hash listed in the
    component evidence_sha256.json must still match; tampering fails;
  * the component audit is recomputed with fsu_seed_audit.audit_attempt and
    the raw stream is re-checked with fsu_chain_check.check_stream. A stored
    audit.ok/certified that disagrees with the recomputation is a violation,
    so a component failure can never be hidden by a suite-level summary;
  * suite_execution_complete, suite_evidence_valid and suite_certified are
    reported independently;
  * formal_seed_contribution is always 1.

Legacy suite audits are read only. If audit.json has no schema_version it is
reported as legacy: only fields that actually exist are echoed; missing
fields are named, never invented. --migrate-report writes the NEW report to
the requested path only; it never rewrites legacy evidence.

This tool never writes under runs/ (both --out and --migrate-report refuse
known evidence paths inside the seed directory).

Exit code: 0 when suite_certified is true, 1 otherwise, 2 for usage/IO errors
that prevented an audit report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_chain_check as C  # noqa: E402
import fsu_seed_audit as A  # noqa: E402
import fsu_seed_plan_schema as SP  # noqa: E402
import fsu_suite as S  # noqa: E402
import fsu_w6_suite as WS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "fsu-suite-audit/v2"
TOOL_VERSION = "fsu_suite_audit/v2"

# The audit_json itself is not covered by evidence_sha256.json (it is written
# after the evidence manifest), so it is recomputed instead. Everything else
# below must be covered by the component evidence manifest.
REQUIRED_ARTIFACTS = (
    "manifest.json",
    "audit.json",
    "chain_report.json",
    "oracle.json",
    "evidence_sha256.json",
    "component_manifest.json",
    "oracle_elements.json",
    "inject/array.bin",
    "stats.txt",
    "run.out",
)
EVIDENCE_COVERED = (
    "manifest.json",
    "chain_report.json",
    "oracle.json",
    "oracle_elements.json",
    "inject/array.bin",
    "component_manifest.json",
    "stats.txt",
    "run.out",
)
LEGACY_FIELDS = (
    "ok", "certified", "checks", "failures", "run_id", "suite_seed",
    "suite_hash",
)
EVIDENCE_FILENAMES = {
    "audit.json", "audit.md", "suite_manifest.json", "suite_report.json",
    "suite_failures.jsonl",
}


def _sha(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except OSError as e:
        return None, f"missing/unreadable: {e}"
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"


def _resolve_attempt(seed_dir: Path, value) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    p = Path(text)
    return p if p.is_absolute() else seed_dir / p


def _detect_kind(suite_id: str, program_order) -> str:
    if str(suite_id).startswith("w6-"):
        return "w6"
    if tuple(program_order or ()) == tuple(WS.W6_PROGRAM_ORDER):
        return "w6"
    return "w5"


def _expected_and_hash(kind: str):
    if kind == "w6":
        return list(WS.W6_PROGRAM_ORDER), WS.compute_suite_hash, WS.W6_PROGRAM_COUNT
    return list(S.PROGRAM_ORDER), S.compute_suite_hash, S.PROGRAM_COUNT


def _config_path(seed_dir: Path, suite_id: str, override) -> Path | None:
    if override:
        return Path(override)
    if not suite_id:
        return None
    return ROOT / "configs/fsu/suites" / f"{suite_id}.json"


def _attempt_number(attempt: Path) -> int:
    name = attempt.name
    try:
        return int(name.split("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def _guard_output_path(target: Path, seed_dir: Path):
    """Refuse to overwrite legacy evidence inside the audited seed dir."""
    target = target.resolve()
    seed_dir = seed_dir.resolve()
    try:
        target.relative_to(seed_dir)
    except ValueError:
        return
    if target.name in EVIDENCE_FILENAMES or target.parent.name == "components":
        raise ValueError(
            f"refusing to overwrite legacy evidence path: {target}")


def _recompute_chain(attempt: Path, manifest: dict):
    prop = attempt / "inject/prop_evt.txt.gz"
    if not prop.exists():
        return None, "inject/prop_evt.txt.gz missing"
    try:
        result = C.check_stream(prop, run_id=manifest.get("run_id"),
                                sample_run_id=manifest.get("sample_run_id"))
    except Exception as e:  # noqa: BLE001 - evidence failure must be reported
        return None, f"chain recompute failed: {type(e).__name__}: {e}"
    return result, None


def _compare_chain(stored: dict, recomputed: dict):
    issues = []
    pairs = (
        ("event_count", "event_count"),
        ("truncated", "truncated"),
        ("identity_violations", "identity_violations"),
        ("admitted", "admitted"),
        ("certified", "certified"),
        ("fault_terminals", "fault_terminals"),
        ("violations", "violations"),
    )
    for key, rec_key in pairs:
        if key not in stored:
            continue
        if stored.get(key) != recomputed.get(rec_key):
            issues.append(
                f"chain_report.{key}={stored.get(key)!r} != recomputed "
                f"{recomputed.get(rec_key)!r}")
    # Some chain_report writers nest the same fields under "chain".
    return issues


def _audit_component(seed_dir: Path, comp: dict, expected_pid: str,
                     expected_index: int, expected_count: int,
                     suite_id: str, suite_version, suite_hash: str,
                     suite_seed: int, run_id: str, plan_binding,
                     violations: dict):
    pid = str(comp.get("program_id") or expected_pid)
    vlist = []

    def viol(kind: str, message: str):
        text = f"{pid}: {message}"
        vlist.append(text)
        violations[kind].append(text)

    attempt = _resolve_attempt(seed_dir, comp.get("attempt"))
    entry = {
        "program_id": pid,
        "program_index": int(comp.get("program_index", expected_index)),
        "attempt": str(attempt) if attempt else None,
        "manifest_sha256": None,
        "audit_sha256": None,
        "chain_report_sha256": None,
        "oracle_sha256": None,
        "evidence_sha256": None,
        "component_manifest_sha256": None,
        "oracle_elements_sha256": None,
        "audit_ok": False,
        "certified": False,
        "recomputed_audit_ok": False,
        "recomputed_certified": False,
        "oracle_category": None,
        "element_oracle": None,
        "chain_terminal": None,
        "component_status": None,
        "execution_complete": False,
        "evidence_valid": False,
        "plan_binding_key": (plan_binding or {}).get("key"),
        "plan_binding_ok": None,
        "missing_evidence": [],
        "physical_identity": None,
        "violations": vlist,
    }

    def missing(message: str):
        text = f"{pid}: {message}"
        entry["missing_evidence"].append(text)
        violations["missing_evidence"].append(text)
        vlist.append(text)

    def check_binding(recorded, label: str):
        if not plan_binding:
            return
        schema = plan_binding["schema"]
        issues = SP.verify_binding(
            schema, plan_binding["entry"], pid, recorded)
        for issue in issues:
            if issue.startswith("missing:"):
                missing(f"{label} missing {issue.split(':', 1)[1]} "
                        f"(plan binding {plan_binding['key']})")
            else:
                viol("identity", f"{label} {issue}")
        if not issues:
            entry["plan_binding_ok"] = True

    # ---- suite binding declared by the suite manifest component entry ----
    if int(comp.get("program_index", -1)) != expected_index:
        viol("identity", f"program_index {comp.get('program_index')} != "
                         f"{expected_index}")
    if comp.get("program_count") is not None \
            and int(comp.get("program_count")) != expected_count:
        viol("identity", f"program_count {comp.get('program_count')} != "
                         f"{expected_count}")
    if comp.get("suite_hash") is not None \
            and str(comp.get("suite_hash")) != suite_hash:
        viol("identity", "suite_manifest component suite_hash drift")
    if comp.get("suite_seed") is not None \
            and int(comp.get("suite_seed")) != suite_seed:
        viol("identity", "suite_manifest component suite_seed drift")
    if comp.get("suite_id") is not None \
            and str(comp.get("suite_id")) != suite_id:
        viol("identity", "suite_manifest component suite_id drift")

    if attempt is None:
        viol("execution", "component attempt path missing")
        return entry
    if not attempt.is_dir():
        viol("execution", f"attempt directory missing: {attempt}")
        return entry

    # ---- required artifacts + hashes ----
    for rel in REQUIRED_ARTIFACTS:
        if not (attempt / rel).exists():
            viol("evidence", f"required artifact missing: {rel}")

    entry["manifest_sha256"] = _sha(attempt / "manifest.json")
    entry["audit_sha256"] = _sha(attempt / "audit.json")
    entry["chain_report_sha256"] = _sha(attempt / "chain_report.json")
    entry["oracle_sha256"] = _sha(attempt / "oracle.json")
    entry["evidence_sha256"] = _sha(attempt / "evidence_sha256.json")
    entry["component_manifest_sha256"] = _sha(
        attempt / "component_manifest.json")
    entry["oracle_elements_sha256"] = _sha(attempt / "oracle_elements.json")

    evidence, err = _load_json(attempt / "evidence_sha256.json")
    if err:
        viol("evidence", f"evidence_sha256.json {err}")
        evidence = {}
    if not isinstance(evidence, dict):
        viol("evidence", "evidence_sha256.json is not an object")
        evidence = {}

    for rel, want in evidence.items():
        path = attempt / rel
        got = _sha(path)
        if got is None:
            viol("evidence", f"evidence file missing: {rel}")
        elif got != want:
            viol("evidence", f"SHA-256 mismatch: {rel}")
    for rel in EVIDENCE_COVERED:
        if rel not in evidence:
            viol("evidence", f"evidence_sha256.json does not cover {rel}")

    # ---- attempt manifest identity / binding ----
    manifest, err = _load_json(attempt / "manifest.json")
    if err:
        viol("evidence", f"manifest.json {err}")
        manifest = {}
    if manifest:
        if str(manifest.get("run_id")) != str(run_id):
            viol("identity", f"attempt run_id {manifest.get('run_id')!r} != "
                             f"suite run_id {run_id!r}")
        if plan_binding:
            key = plan_binding["key"]
            check_binding(manifest.get(key), f"attempt {key}")
            if key not in manifest:
                missing(f"attempt manifest has no {key}")

    # ---- component manifest identity / binding ----
    cm, err = _load_json(attempt / "component_manifest.json")
    if err:
        viol("evidence", f"component_manifest.json {err}")
        cm = {}
    if cm:
        entry["component_status"] = cm.get("component_status")
        entry["element_oracle"] = cm.get("component_oracle")
        checks = (
            ("suite_id", suite_id),
            ("suite_hash", suite_hash),
            ("program_id", pid),
            ("program_index", expected_index),
            ("program_count", expected_count),
            ("suite_seed", suite_seed),
        )
        for key, want in checks:
            if key not in cm:
                viol("identity", f"component_manifest missing {key}")
            elif str(cm.get(key)) != str(want):
                viol("identity", f"component_manifest {key}="
                                 f"{cm.get(key)!r} != {want!r}")
        if cm.get("suite_version") is not None \
                and suite_version is not None \
                and str(cm.get("suite_version")) != str(suite_version):
            viol("identity", "component_manifest suite_version drift")
        if entry["manifest_sha256"] is not None \
                and cm.get("component_manifest_sha256") \
                != entry["manifest_sha256"]:
            viol("evidence", "component_manifest_sha256 != manifest.json")
        if attempt.name.startswith("attempt-"):
            if int(cm.get("component_attempt", -1)) != _attempt_number(attempt):
                viol("identity", "component_attempt != attempt directory")
        if manifest:
            if cm.get("component_seed") is not None \
                    and str(cm.get("component_seed")) \
                    != str(manifest.get("seed")):
                viol("identity", "component_seed != attempt manifest seed")
            if plan_binding:
                key = plan_binding["key"]
                if key not in cm:
                    missing(f"component_manifest has no {key}")
                else:
                    check_binding(cm.get(key), f"component {key}")
        if cm.get("component_oracle") not in ("SDC", "MASKED"):
            viol("certification",
                 f"element oracle is not SDC/MASKED: "
                 f"{cm.get('component_oracle')!r}")
        if cm.get("component_status") != "admitted":
            viol("certification",
                 f"component_status != admitted: "
                 f"{cm.get('component_status')!r}")

    # ---- execution completed? ----
    oracle, err = _load_json(attempt / "oracle.json")
    if err:
        viol("execution", f"oracle.json {err}")
        oracle = {}
    if oracle:
        entry["oracle_category"] = oracle.get("category")
        rc = oracle.get("returncode")
        timed_out = oracle.get("timed_out")
        if rc != 0:
            viol("execution", f"oracle returncode={rc!r}")
        if timed_out is not False:
            viol("execution", f"oracle timed_out={timed_out!r}")
    if not (attempt / "stats.txt").exists() \
            or (attempt / "stats.txt").stat().st_size == 0:
        viol("execution", "stats.txt missing or empty")
    entry["execution_complete"] = not any(
        x.startswith(f"{pid}: ") and x.split(": ", 1)[1].startswith(
            ("required artifact", "oracle", "stats.txt", "attempt directory"))
        for x in vlist)

    # ---- chain_report vs raw-stream recompute ----
    stored_report, err = _load_json(attempt / "chain_report.json")
    if err:
        viol("evidence", f"chain_report.json {err}")
        stored_report = {}
    stored_chain = (stored_report or {}).get("chain") or {}
    recomputed, err = _recompute_chain(attempt, manifest or {})
    if err:
        viol("evidence", err)
    elif stored_chain:
        for issue in _compare_chain(stored_chain, recomputed):
            viol("evidence", f"stale chain_report: {issue}")
        oracle_cat = (stored_report.get("oracle") or {}).get("category")
        if oracle_cat is not None:
            entry["oracle_category"] = oracle_cat
        entry["chain_terminal"] = (
            next(iter(stored_chain.get("fault_terminals", {}).values()), None))
    else:
        viol("evidence", "chain_report.json has no chain object")

    # ---- plan provenance: warmup/sample units + physical cell identity ----
    command = ((stored_report or {}).get("command") or {}).get("inject")
    ini_text = ""
    ini_path = attempt / "inject/config.ini"
    if ini_path.exists():
        try:
            ini_text = ini_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            missing(f"inject/config.ini unreadable: {e}")
    if plan_binding:
        schema = plan_binding["schema"]
        entry["warmup_sample"] = SP.warmup_sample_contract(
            schema, plan_binding["entry"])
        flags = SP.command_flags(command)
        if not command:
            missing("chain_report command.inject missing (plan provenance)")
        elif schema == SP.SCHEMA_F5 and plan_binding["entry"].get(
                "permanent_stuck"):
            want = {
                "--fpu_f5_warmup": plan_binding["entry"]["warmup"],
                "--fpu_f5_sample_limit":
                    plan_binding["entry"]["sample"]["limit"],
                "--fpu_f5_keep_first_last_n":
                    plan_binding["entry"]["sample"]["keep_first_last_n"],
            }
            for flag, value in want.items():
                if flag not in flags:
                    missing(f"command missing {flag} (F5 warmup/sample)")
                elif int(str(flags[flag]), 0) != int(value):
                    viol("identity", f"command {flag}={flags[flag]!r} != "
                                     f"frozen {value}")
        elif schema == SP.SCHEMA_FR03:
            if "--chaos_phys" not in flags:
                viol("identity", "FR03 command does not select --chaos_phys")
            stray = [f for f in flags if f == "--chaos_fpu"
                     or f.startswith("--fpu_f5_")]
            if stray:
                viol("identity",
                     f"FR03 command carries CHAOSFPU F5 flags: {stray}")
            phys = SP.physical_identity(
                schema, plan_binding["entry"], pid, manifest or {}, cm,
                command, ini_text)
            entry["physical_identity"] = phys
            for item in phys.get("missing", []):
                missing(f"physical identity source missing: {item}")
            for item in phys.get("violations", []):
                viol("identity", f"physical identity: {item}")

    # ---- component audit: stored vs recomputed ----
    stored_audit, err = _load_json(attempt / "audit.json")
    if err:
        viol("evidence", f"audit.json {err}")
        stored_audit = {}
    entry["audit_ok"] = stored_audit.get("ok") is True
    entry["certified"] = stored_audit.get("certified") is True

    try:
        recomputed_audit = A.audit_attempt(attempt)
    except Exception as e:  # noqa: BLE001 - corrupt evidence must be reported
        recomputed_audit = {
            "ok": False,
            "failures": [f"audit recompute raised {type(e).__name__}: {e}"],
        }
    rec_ok = recomputed_audit.get("ok") is True
    rec_cert = False
    if recomputed is not None:
        faults = recomputed.get("faults") or {}
        rec_cert = bool(faults) and all(
            f.get("certified") is True for f in faults.values()) and rec_ok
    entry["recomputed_audit_ok"] = rec_ok
    entry["recomputed_certified"] = rec_cert

    if entry["audit_ok"] != rec_ok:
        viol("evidence", f"stored audit.ok={entry['audit_ok']} != recomputed "
                         f"{rec_ok}")
    if entry["certified"] != rec_cert:
        viol("evidence", f"stored audit.certified={entry['certified']} != "
                         f"recomputed {rec_cert}")
    if cm:
        if "component_audit_ok" in cm \
                and bool(cm.get("component_audit_ok")) != rec_ok:
            viol("certification", "component_manifest component_audit_ok != "
                                  "recomputed")
        if "component_certified" in cm \
                and bool(cm.get("component_certified")) != rec_cert:
            viol("certification", "component_manifest component_certified != "
                                  "recomputed")
    if not rec_ok:
        viol("certification", "recomputed component audit is not ok: "
             + "; ".join(recomputed_audit.get("failures", [])[:3]))
    elif not rec_cert:
        viol("certification", "recomputed component audit is not certified")

    entry["evidence_valid"] = not any(
        x.startswith(f"{pid}: ") and x.split(": ", 1)[1].startswith(
            ("required artifact", "evidence_sha256", "SHA-256", "stale chain",
             "manifest.json", "audit.json", "chain_report.json",
             "component_manifest.json", "stored audit", "missing",
             "physical identity source missing"))
        for x in vlist)
    return entry


def audit_seed(seed_dir: Path, suite_config=None) -> dict:
    seed_dir = Path(seed_dir)
    category_violations = {
        "suite": [], "identity": [], "execution": [], "evidence": [],
        "certification": [], "missing_evidence": [],
    }

    def add(kind: str, message: str):
        category_violations[kind].append(message)

    sm_path = seed_dir / "suite_manifest.json"
    sm, err = _load_json(sm_path)
    if err:
        add("suite", f"suite_manifest.json {err}")
        return _finish(seed_dir, {}, [], [], None, None, None,
                       category_violations)

    suite_id = str(sm.get("suite_id") or "")
    run_id = str(sm.get("run_id") or "")
    suite_version = sm.get("suite_version")
    suite_hash_declared = str(sm.get("suite_hash") or "")
    program_order = sm.get("program_order") or []
    kind = _detect_kind(suite_id, program_order)
    expected, hash_fn, expected_count = _expected_and_hash(kind)

    cfg_path = _config_path(seed_dir, suite_id, suite_config)
    cfg = {}
    frozen_hash = None
    plan_schema = None
    if cfg_path is None or not Path(cfg_path).exists():
        add("suite", f"frozen suite config missing: {cfg_path}")
    else:
        cfg, err = _load_json(Path(cfg_path))
        if err:
            add("suite", f"frozen suite config {err}")
            cfg = {}
        else:
            try:
                plan_schema, frozen_hash = SP.suite_hash(cfg, kind)
            except Exception as e:  # noqa: BLE001
                add("suite", f"frozen suite config invalid: {e}")
            if str(cfg.get("suite_id")) != suite_id:
                add("suite", f"frozen config suite_id "
                             f"{cfg.get('suite_id')!r} != {suite_id!r}")
            if list(cfg.get("program_order") or []) != expected:
                add("suite", "frozen config program_order drift")
            if int(cfg.get("program_count", -1)) != expected_count:
                add("suite", "frozen config program_count drift")

    if not suite_hash_declared:
        add("suite", "suite_manifest.suite_hash missing")
    if frozen_hash is not None and suite_hash_declared != frozen_hash:
        add("suite", f"suite_hash drift: manifest {suite_hash_declared} != "
                     f"recomputed {frozen_hash}")
    suite_hash = frozen_hash or suite_hash_declared

    if list(program_order) != expected:
        add("suite", f"program_order {list(program_order)!r} != frozen "
                     f"{expected!r}")
    if int(sm.get("program_count", -1)) != expected_count:
        add("suite", f"program_count {sm.get('program_count')!r} != "
                     f"{expected_count}")

    # W5 suite manifests embed the whole suite document; it must hash the same
    # under the same model-specific hash implementation.
    if "suite" in sm and isinstance(sm.get("suite"), dict):
        try:
            _, embedded_hash = SP.suite_hash(sm["suite"], kind)
        except Exception as e:  # noqa: BLE001
            add("suite", f"embedded suite invalid: {e}")
        else:
            if embedded_hash != suite_hash:
                add("suite", "embedded suite_hash != frozen config hash")

    try:
        suite_seed = int(sm.get("suite_seed"))
        if suite_seed < 1:
            raise ValueError
    except (TypeError, ValueError):
        add("suite", f"invalid suite_seed {sm.get('suite_seed')!r}")
        suite_seed = 0

    seed_plan_entry = None
    plan_binding = None
    plan_document = None
    if isinstance(cfg.get("seed_plan"), list):
        try:
            plan_schema, plan_entry = SP.seed_entry(cfg, suite_seed)
        except Exception as e:  # noqa: BLE001
            add("suite", f"frozen seed_plan invalid: {e}")
            plan_entry = None
        if plan_entry is not None:
            plan_document = SP.describe_document(cfg)
            plan_document["normalised_entry"] = plan_entry
            plan_document["warmup_sample"] = SP.warmup_sample_contract(
                plan_schema, plan_entry)
            key = SP.BINDING_KEY[plan_schema]
            plan_binding = {"schema": plan_schema, "entry": plan_entry,
                            "key": key}
            if plan_schema == SP.SCHEMA_F5:
                seed_plan_entry = S.seed_plan_identity(plan_entry)
                declared = sm.get("seed_plan_entry")
                if declared is not None and declared != seed_plan_entry:
                    add("suite", "suite_manifest seed_plan_entry drift")
            else:
                declared = sm.get("target_plan_entries")
                if declared is not None and not isinstance(declared, dict):
                    add("suite", "suite_manifest target_plan_entries is not "
                                 "an object")
                if declared:
                    for pid, recorded in declared.items():
                        issues = SP.verify_binding(
                            plan_schema, plan_entry, str(pid), recorded)
                        for issue in issues:
                            if issue.startswith("missing:"):
                                add("missing_evidence",
                                    f"suite_manifest target_plan_entries[{pid}]"
                                    f" missing {issue.split(':', 1)[1]}")
                            else:
                                add("identity",
                                    f"suite_manifest target_plan_entries[{pid}]"
                                    f" {issue}")

    comps = sm.get("components")
    if not isinstance(comps, list):
        add("suite", "suite_manifest.components is not a list")
        comps = []
    actual_programs = [str(c.get("program_id")) for c in comps
                       if isinstance(c, dict)]

    by_pid = {}
    for comp in comps:
        if not isinstance(comp, dict):
            add("identity", "non-object component entry")
            continue
        pid = str(comp.get("program_id") or "")
        by_pid.setdefault(pid, []).append(comp)
        if pid not in expected:
            add("identity", f"unexpected program in suite: {pid!r}")
    for pid in expected:
        n = len(by_pid.get(pid, []))
        if n == 0:
            add("identity", f"missing program: {pid}")
        elif n > 1:
            add("identity", f"duplicate program: {pid} ({n} entries)")

    component_entries = []
    for index, pid in enumerate(expected):
        matches = by_pid.get(pid) or []
        if not matches:
            continue
        if len(matches) > 1:
            # Report the first but keep the duplicate violation.
            pass
        component_entries.append(_audit_component(
            seed_dir, matches[0], pid, index, expected_count, suite_id,
            suite_version, suite_hash, suite_seed, run_id, plan_binding,
            category_violations))

    # ---- suite_report consistency (if present) ----
    rep_path = seed_dir / "suite_report.json"
    if rep_path.exists():
        rep, err = _load_json(rep_path)
        if err:
            add("evidence", f"suite_report.json {err}")
        elif rep:
            if rep.get("suite_hash") is not None \
                    and str(rep.get("suite_hash")) != suite_hash:
                add("evidence", "suite_report suite_hash drift")
            if rep.get("run_id") is not None \
                    and str(rep.get("run_id")) != run_id:
                add("evidence", "suite_report run_id drift")
            if rep.get("suite_seed") is not None \
                    and int(rep.get("suite_seed")) != suite_seed:
                add("evidence", "suite_report suite_seed drift")
            if rep.get("component_run_count") is not None \
                    and int(rep.get("component_run_count")) != len(comps):
                add("evidence", "suite_report component_run_count != "
                                "suite_manifest.components")
            if rep.get("formal_suite_seed_count") is not None \
                    and int(rep.get("formal_suite_seed_count")) != 1:
                add("evidence", "suite_report formal_suite_seed_count != 1")

    legacy = _legacy_audit(seed_dir, add)
    return _finish(seed_dir, sm, component_entries, actual_programs,
                   seed_plan_entry, frozen_hash, cfg_path,
                   category_violations, legacy,
                   plan_schema=plan_schema, plan_document=plan_document)


def _legacy_audit(seed_dir: Path, add):
    path = seed_dir / "audit.json"
    if not path.exists():
        return {"present": False, "path": str(path), "schema_version": None,
                "legacy": True, "fields_present": [], "fields_missing":
                list(LEGACY_FIELDS), "raw": {},
                "ok_matches_recomputed": None,
                "certified_matches_recomputed": None}
    audit, err = _load_json(path)
    if err:
        add("evidence", f"legacy suite audit.json {err}")
        return {"present": True, "path": str(path), "schema_version": None,
                "legacy": True, "fields_present": [],
                "fields_missing": list(LEGACY_FIELDS), "raw": {},
                "ok_matches_recomputed": None,
                "certified_matches_recomputed": None}
    if not isinstance(audit, dict):
        add("evidence", "legacy suite audit.json is not an object")
        audit = {}
    schema_version = audit.get("schema_version")
    present = [k for k in LEGACY_FIELDS if k in audit]
    missing = [k for k in LEGACY_FIELDS if k not in audit]
    return {
        "present": True,
        "path": str(path),
        "schema_version": schema_version,
        "legacy": schema_version is None,
        "fields_present": present,
        "fields_missing": missing,
        "raw": {k: audit.get(k) for k in present},
        "ok_matches_recomputed": None,
        "certified_matches_recomputed": None,
    }


def _finish(seed_dir: Path, sm: dict, components, actual_programs,
            seed_plan_entry, frozen_hash, cfg_path, categories,
            legacy=None, plan_schema=None, plan_document=None):
    expected_order = None
    if sm:
        kind = _detect_kind(str(sm.get("suite_id") or ""),
                            sm.get("program_order") or [])
        expected_order = _expected_and_hash(kind)[0]
    else:
        expected_order = []
    component_ok = bool(components) and all(
        c.get("execution_complete") and c.get("evidence_valid")
        and c.get("audit_ok") and c.get("certified")
        and c.get("recomputed_audit_ok") and c.get("recomputed_certified")
        and c.get("component_status") == "admitted"
        for c in components)
    suite_execution_complete = (
        bool(components) and len(components) == len(expected_order)
        and all(c.get("execution_complete") for c in components))
    suite_evidence_valid = not categories["evidence"]
    suite_certified = (
        suite_execution_complete and suite_evidence_valid and component_ok
        and not categories["suite"] and not categories["identity"]
        and not categories["certification"]
        and not categories.get("missing_evidence"))

    if legacy is not None:
        if legacy.get("fields_present"):
            legacy_ok = legacy.get("raw", {}).get("ok")
            if legacy_ok is not None:
                legacy["ok_matches_recomputed"] = bool(legacy_ok) == suite_certified
                if not legacy["ok_matches_recomputed"]:
                    categories["evidence"].append(
                        "legacy suite audit ok disagrees with recomputed "
                        f"suite_certified={suite_certified}")
                    suite_evidence_valid = False
                    suite_certified = False
            legacy_cert = legacy.get("raw", {}).get("certified")
            if legacy_cert is not None:
                legacy["certified_matches_recomputed"] = (
                    bool(legacy_cert) == suite_certified)
                if not legacy["certified_matches_recomputed"]:
                    categories["evidence"].append(
                        "legacy suite audit certified disagrees with "
                        f"recomputed suite_certified={suite_certified}")
                    suite_evidence_valid = False
                    suite_certified = False

    violations = []
    for kind in ("suite", "identity", "execution", "evidence",
                 "certification", "missing_evidence"):
        violations.extend(f"{kind}: {m}" for m in categories.get(kind, []))

    missing_evidence = list(categories.get("missing_evidence", []))
    if suite_certified:
        recompute_status = "current_verified"
    elif missing_evidence:
        recompute_status = "missing_evidence"
    else:
        recompute_status = "current_verification_failed"

    return {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "suite_id": sm.get("suite_id"),
        "suite_version": sm.get("suite_version"),
        # Prefer the recomputed frozen-plan hash; keep the declared value
        # separately so a drift is visible rather than overwritten.
        "suite_hash": frozen_hash or sm.get("suite_hash"),
        "suite_hash_declared": sm.get("suite_hash"),
        "run_id": sm.get("run_id"),
        "suite_seed": sm.get("suite_seed"),
        "expected_programs": expected_order,
        "actual_programs": actual_programs,
        "component_count": len(components),
        "components": components,
        "suite_execution_complete": bool(suite_execution_complete),
        "suite_evidence_valid": bool(suite_evidence_valid),
        "suite_certified": bool(suite_certified),
        "violations": violations,
        "legacy_audit": legacy,
        "formal_seed_contribution": 1,
        "suite_manifest_sha256": _sha(seed_dir / "suite_manifest.json"),
        "frozen_suite_config": str(cfg_path) if cfg_path else None,
        "frozen_suite_config_sha256": _sha(Path(cfg_path))
        if cfg_path and Path(cfg_path).exists() else None,
        "seed_plan_schema": plan_schema,
        "seed_plan_document": plan_document,
        "seed_plan_entry": seed_plan_entry,
        "missing_evidence": missing_evidence,
        "recompute_status": recompute_status,
    }


def _write_report(report: dict, target: Path, seed_dir: Path):
    target = Path(target)
    _guard_output_path(target, seed_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Recomputed unified audit for one FSU suite seed")
    ap.add_argument("seed_dir", help="runs/fsu/<RunID>/seed<N>")
    ap.add_argument("--suite-config", default=None,
                    help="override frozen suite plan JSON")
    ap.add_argument("--out", default=None,
                    help="write the new report to this path (never legacy)")
    ap.add_argument("--migrate-report", default=None,
                    help="write the new report to this path only; legacy "
                         "evidence is left untouched")
    ap.add_argument("--quiet", action="store_true",
                    help="do not print the report to stdout")
    args = ap.parse_args(argv)

    seed_dir = Path(args.seed_dir)
    if not seed_dir.exists():
        print(f"error: seed dir does not exist: {seed_dir}", file=sys.stderr)
        return 2
    try:
        report = audit_seed(seed_dir, suite_config=args.suite_config)
    except Exception as e:  # noqa: BLE001 - never emit a partial fake report
        print(f"error: audit failed: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 2

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if not args.quiet:
        print(text)

    try:
        if args.out:
            _write_report(report, Path(args.out), seed_dir)
        if args.migrate_report:
            _write_report(report, Path(args.migrate_report), seed_dir)
    except (OSError, ValueError) as e:
        print(f"error: cannot write report: {e}", file=sys.stderr)
        return 2
    return 0 if report["suite_certified"] else 1


if __name__ == "__main__":
    sys.exit(main())
