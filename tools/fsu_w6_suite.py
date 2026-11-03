#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_w6_suite.py — W6 (SVD + FFT + sparse linear system) suite identity.

W6 is a fixed 3-component suite, in this immutable order:

    svd → fft → sparse-cg

Each component is a real program with a fixed, deterministic input, a raw
little-endian live-out array dump, a 16-hex FINAL hash, and a pre-registered
per-element oracle (dtype/layout/shape/count/abs_tol/rel_tol/ulp_tol).
Fault-run results are never part of the identity hash.

`suite_hash` is SHA-256 over canonical JSON of identity fields only:

  * program_id / program_index / source_sha256 / binary_sha256 / scale /
    input_id / golden_array_sha256 / final token;
  * element_oracle.oracle_version and the full pre-registered meta
    (including all three tolerances);
  * compiler version/cflags and oracle version.

Run results, attempts, statuses and paths are excluded.

This module does not run gem5 and does not write runs/.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import fsu_suite as S  # generic program_overrides / seed_plan helpers
import fsu_w6_oracle as WO

W6_PROGRAM_ORDER = ("svd", "fft", "sparse-cg")
W6_PROGRAM_COUNT = len(W6_PROGRAM_ORDER)
DEFAULT_SUITE_ID = "w6-fp-v1"
DEFAULT_SUITE_VERSION = "1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEX16 = re.compile(r"^[0-9a-f]{16}$")


class W6SuiteError(ValueError):
    """W6 suite identity is not established; callers must fail loudly."""


def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _check_hash(value, where: str, allow_pending: bool) -> str:
    text = str(value or "")
    if allow_pending and text == "pending":
        return text
    if not _HEX64.match(text):
        raise W6SuiteError(f"{where}: expected 64-hex SHA-256"
                           + (" or 'pending'" if allow_pending else "")
                           + f", got {value!r}")
    return text


def _normalise_cflags(value) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(x) for x in value)
    return str(value or "")


def _program_map(suite: dict):
    programs = suite.get("programs")
    if not isinstance(programs, list):
        raise W6SuiteError("suite.programs must be a list")
    by_id = {}
    for p in programs:
        if not isinstance(p, dict):
            raise W6SuiteError("suite.programs entries must be objects")
        pid = str(p.get("program_id", "")).strip()
        if pid not in W6_PROGRAM_ORDER:
            raise W6SuiteError(f"unknown W6 program_id {pid!r}; expected "
                               f"{list(W6_PROGRAM_ORDER)}")
        if pid in by_id:
            raise W6SuiteError(f"duplicate W6 program: {pid}")
        by_id[pid] = p
    return by_id


def _validate_order_and_count(suite: dict):
    order = suite.get("program_order")
    if not isinstance(order, list) or tuple(order) != W6_PROGRAM_ORDER:
        raise W6SuiteError("program_order is fixed and must not be "
                           f"reordered: want {list(W6_PROGRAM_ORDER)}, "
                           f"got {order}")
    if int(suite.get("program_count", -1)) != W6_PROGRAM_COUNT:
        raise W6SuiteError(f"program_count must be {W6_PROGRAM_COUNT}")


def _normalise_program_overrides(suite: dict):
    try:
        return S.normalise_program_overrides(suite)
    except S.SuiteError as e:
        raise W6SuiteError(str(e)) from e


def _normalise_seed_plan(suite: dict):
    try:
        return S.normalise_seed_plan(suite)
    except S.SuiteError as e:
        raise W6SuiteError(str(e)) from e


def suite_identity_document(suite: dict, allow_pending: bool = True) -> dict:
    if not isinstance(suite, dict):
        raise W6SuiteError("suite manifest must be an object")
    suite_id = str(suite.get("suite_id", "")).strip()
    suite_version = str(suite.get("suite_version", "")).strip()
    if not suite_id or not suite_version:
        raise W6SuiteError("suite_id and suite_version are required")
    _validate_order_and_count(suite)
    by_id = _program_map(suite)
    missing = [p for p in W6_PROGRAM_ORDER if p not in by_id]
    extra = [p for p in by_id if p not in W6_PROGRAM_ORDER]
    if missing:
        raise W6SuiteError(f"suite missing component(s): {missing}")
    if extra:
        raise W6SuiteError(f"suite has unknown component(s): {extra}")

    programs = []
    for index, pid in enumerate(W6_PROGRAM_ORDER):
        p = by_id[pid]
        if int(p.get("program_index", -1)) != index:
            raise W6SuiteError(f"{pid}.program_index must be {index}")
        scale = p.get("scale")
        if not isinstance(scale, dict) or not scale:
            raise W6SuiteError(f"{pid}.scale must be a non-empty object")
        eo = p.get("element_oracle")
        if not isinstance(eo, dict):
            raise W6SuiteError(f"{pid}.element_oracle is required")
        try:
            meta = WO.validate_meta(eo.get("meta") or {})
        except WO.W6OracleError as e:
            raise W6SuiteError(f"{pid}: invalid element_oracle meta: {e}")
        if meta["program_id"] != pid:
            raise W6SuiteError(f"{pid}: element_oracle meta program_id drift")
        if str(eo.get("oracle_version")) != meta["oracle_version"]:
            raise W6SuiteError(f"{pid}: element_oracle oracle_version drift")
        final = str(p.get("golden", "")).strip()
        if final:
            if not _HEX16.match(final):
                raise W6SuiteError(f"{pid}.golden must be 16 lowercase hex, "
                                   f"got {final!r}")
        elif not allow_pending:
            raise W6SuiteError(f"{pid}.golden is required")
        programs.append({
            "program_id": pid,
            "program_index": index,
            "source_sha256": _check_hash(
                p.get("source_sha256"), f"{pid}.source_sha256", allow_pending),
            "binary_sha256": _check_hash(
                p.get("binary_sha256"), f"{pid}.binary_sha256", allow_pending),
            "golden_array_sha256": _check_hash(
                p.get("golden_array_sha256"),
                f"{pid}.golden_array_sha256", allow_pending),
            "final": final,
            "scale": scale,
            "input_id": str(p.get("input_id", "")),
            "element_oracle": {
                "oracle_version": meta["oracle_version"],
                "meta": meta,
            },
        })

    compiler = suite.get("compiler") or {}
    version = str(compiler.get("version") or "").strip()
    cflags = _normalise_cflags(compiler.get("cflags"))
    if not version or not cflags.strip():
        raise W6SuiteError("suite.compiler.version/cflags are required")
    oracle = suite.get("oracle") or {}
    if not str(oracle.get("version") or "").strip():
        raise W6SuiteError("suite.oracle.version is required")
    doc = {
        "suite_id": suite_id,
        "suite_version": suite_version,
        "program_order": list(W6_PROGRAM_ORDER),
        "program_count": W6_PROGRAM_COUNT,
        "programs": programs,
        "compiler": {"version": version, "cflags": cflags},
        "oracle": {"version": str(oracle["version"])},
    }
    # [FSU][W6] Per-program precision/lane/mask overrides are identity
    # (SVD fp64 vs FFT/sparse-CG fp32) and are covered by suite_hash.
    overrides = _normalise_program_overrides(suite)
    if overrides is not None:
        doc["program_overrides"] = overrides
    # An F5 W6 suite additionally freezes three suite seeds and per-program
    # masks. A suite without a seed_plan keeps the legacy identity shape.
    plan = _normalise_seed_plan(suite)
    if plan is not None:
        doc["seed_plan"] = [S.seed_plan_identity(e) for e in plan]
        defaults = suite.get("run_defaults") or {}
        doc["run_defaults_identity"] = {
            k: str(defaults.get(k, "")) for k in (
                "model_id", "unit", "freq", "load_id", "submodel",
                "config_family", "config_profile")
        }
        injector = suite.get("injector") or {}
        doc["injector_identity"] = {
            "component": str(injector.get("component", "")),
            "max_faults": int(injector.get("max_faults", 0) or 0),
            "first_clock": int(injector.get("first_clock", 0) or 0),
        }
    return doc


def compute_suite_hash(suite: dict) -> str:
    return sha256_bytes(canonical_bytes(suite_identity_document(suite)))


def validate_seed_plan_masks(suite: dict):
    """Every suite seed must yield a mask that fits each program's lane.

    The effective lane width per program comes from suite.injector +
    program_overrides (seed_plan geometry is intentionally omitted for W6).
    A seed's `program_mask[pid]` is authoritative for that program;
    otherwise the seed's global mask is used.
    """
    plan = _normalise_seed_plan(suite)
    if plan is None:
        return
    overrides = _normalise_program_overrides(suite) or {}
    base = suite.get("injector") or {}
    for entry in plan:
        for pid in W6_PROGRAM_ORDER:
            try:
                _, precision, lane_width, _ = S.effective_geometry(
                    base, overrides.get(pid))
            except S.SuiteError as e:
                raise W6SuiteError(f"{pid}: invalid effective geometry: {e}") \
                    from e
            text = (entry.get("program_mask") or {}).get(pid, entry["mask"])
            mask = int(str(text), 0)
            if mask == 0:
                raise W6SuiteError(
                    f"seed{entry['suite_seed']} {pid}: zero mask")
            if mask >> lane_width:
                raise W6SuiteError(
                    f"seed{entry['suite_seed']} {pid}: mask 0x{mask:x} does "
                    f"not fit effective lane_width {lane_width} "
                    f"(precision {precision})")


def validate_suite_manifest(suite: dict, require_hashes: bool = False,
                            require_suite_hash: bool = False) -> dict:
    defaults = suite.get("run_defaults") or {}
    if str(defaults.get("freq", "") or "").strip() == "F5" \
            and "seed_plan" not in suite:
        raise W6SuiteError(
            "an F5 W6 suite must pre-register a seed_plan (3 suite seeds)")
    validate_seed_plan_masks(suite)
    doc = suite_identity_document(suite, allow_pending=not require_hashes)
    if require_hashes:
        for p in doc["programs"]:
            for key in ("source_sha256", "binary_sha256",
                        "golden_array_sha256"):
                _check_hash(p[key], f"{p['program_id']}.{key}",
                            allow_pending=False)
            if not p["final"]:
                raise W6SuiteError(f"{p['program_id']}.golden is required")
    computed = sha256_bytes(canonical_bytes(doc))
    declared = suite.get("suite_hash")
    if declared is not None:
        declared = str(declared)
        _check_hash(declared, "suite.suite_hash", allow_pending=False)
        if declared != computed:
            raise W6SuiteError(f"suite_hash drift: declared {declared}, "
                               f"recomputed {computed}")
    elif require_suite_hash:
        raise W6SuiteError("suite.suite_hash is required before a formal run")
    return {"ok": True, "suite_hash": computed, "identity": doc}


def load_suite(path: Path, root: Path = Path("."),
               require_hashes: bool = True) -> dict:
    """Load + validate a W6 suite and verify on-disk source/binary/golden."""
    suite = json.loads(Path(path).read_text(encoding="utf-8"))
    info = validate_suite_manifest(
        suite, require_hashes=require_hashes, require_suite_hash=True)
    root = Path(root)
    for p in suite["programs"]:
        pid = p["program_id"]
        for kind, want in (("source", p["source_sha256"]),
                           ("binary", p["binary_sha256"])):
            path_obj = Path(p[kind])
            if not path_obj.is_absolute():
                path_obj = root / path_obj
            if not path_obj.exists():
                raise W6SuiteError(f"{pid}: {kind} missing: {path_obj}")
            got = sha256_file(path_obj)
            if got != want:
                raise W6SuiteError(f"{pid}: {kind} SHA drift: {got} != {want}")
        golden = Path(p["element_oracle"]["golden_array"])
        if not golden.is_absolute():
            golden = root / golden
        if not golden.exists():
            raise W6SuiteError(f"{pid}: golden array missing: {golden}")
        got = sha256_file(golden)
        if got != p["golden_array_sha256"]:
            raise W6SuiteError(f"{pid}: golden array SHA drift: {got} != "
                               f"{p['golden_array_sha256']}")
    return {"suite": suite, "suite_hash": info["suite_hash"],
            "identity": info["identity"]}


# ---------------------------------------------------------------------------
# Component seed + injector resolution (W6 program ids differ from W5)
# ---------------------------------------------------------------------------
DEFAULT_COMPONENT_SEED_POLICY = "w5-component-seed-v1"


def derive_component_seed(suite_seed: int, program_id: str,
                          policy_version: str = DEFAULT_COMPONENT_SEED_POLICY,
                          suite_id: str = DEFAULT_SUITE_ID,
                          suite_version: str = DEFAULT_SUITE_VERSION) -> int:
    if program_id not in W6_PROGRAM_ORDER:
        raise W6SuiteError(f"unknown W6 program_id {program_id!r}")
    seed_int = int(suite_seed)
    if seed_int < 0:
        raise W6SuiteError("suite_seed must be >= 0")
    material = "|".join([str(suite_id), str(suite_version), str(seed_int),
                         str(program_id), str(policy_version)]).encode("utf-8")
    digest = hashlib.sha256(material).digest()
    value = int.from_bytes(digest[:8], "big")
    return value if value else 1


def derive_component_seeds(suite_seed: int,
                           policy_version: str = DEFAULT_COMPONENT_SEED_POLICY,
                           suite_id: str = DEFAULT_SUITE_ID,
                           suite_version: str = DEFAULT_SUITE_VERSION):
    seeds = {pid: derive_component_seed(suite_seed, pid, policy_version,
                                        suite_id, suite_version)
             for pid in W6_PROGRAM_ORDER}
    if len(set(seeds.values())) != W6_PROGRAM_COUNT:
        raise W6SuiteError(f"component seed collision: {seeds}")
    return seeds


def resolved_injector(suite: dict, program_id: str, seed_entry=None) -> dict:
    """Resolve one component's injector using the shared W5/W6 rules."""
    overrides = _normalise_program_overrides(suite) or {}
    try:
        return S.resolve_program_injector(
            suite.get("injector") or {}, overrides.get(program_id),
            seed_entry, program_id)
    except S.SuiteError as e:
        raise W6SuiteError(str(e)) from e
