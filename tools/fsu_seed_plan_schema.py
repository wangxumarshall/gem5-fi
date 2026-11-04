#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_seed_plan_schema.py — versioned adapter for frozen FSU suite plans.

Two plan schemas exist in the frozen suite configs:

* ``f5-v1``   CHAOSFPU permanent/sampling plan:
              ``{suite_seed, submodel, mask, polarity, warmup, sample, ...}``
* ``fr03-v1`` CHAOSPhysReg permanent-cell plan, written before the F5 schema
              was unified:
              ``{suite_seed, submodel, fault_mask, polarity, fault_type,
              vec_lane_offset}``

This adapter is deliberately read-only.  It never Rewrites a frozen config
or a component manifest and it never invents a value:

* every canonical field names its evidence source (frozen config, component
  manifest, the recorded gem5 command, or ``inject/config.ini``);
* the two alias pairs ``fault_mask<->mask`` and
  ``vec_lane_offset<->lane_offset`` are accepted only when they agree;
  a disagreement fails closed;
* decimal and ``0x`` masks normalise to one integer; the canonical text is
  fixed-width;
* masks are **lane-relative** for both injectors (CHAOSPhysReg:
  ``lane_mask = mask & ((1ULL << lane_width) - 1)``; CHAOSFPU takes the same
  ``lane_width``/``lane_offset`` pair), never an absolute 128-bit Vec index;
* ``warmup``/``sample`` are CHAOSFPU F5 concepts (eligible-event ordinals).
  An FR03 permanent-cell plan has no such fields; they are reported
  ``not_applicable`` with the recorded command/config.ini proof, never 0.

The FR03 hash and the FR03 per-component plan are delegated to
``fsu_fr03_suite_gate`` so there is exactly one real implementation.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_fr03_suite_gate as G  # noqa: E402
import fsu_suite as S  # noqa: E402

SCHEMA_F5 = "f5-v1"
SCHEMA_FR03 = "fr03-v1"
SCHEMA_NONE = None

BINDING_KEY = {
    SCHEMA_F5: "seed_plan_entry",
    SCHEMA_FR03: "target_plan_entry",
}

_F5_REQUIRED = frozenset(("mask", "warmup", "sample"))
_FR03_REQUIRED = frozenset(("fault_mask", "vec_lane_offset"))
_ALIAS_FIELDS = (
    ("mask", "fault_mask"),
    ("lane_offset", "vec_lane_offset"),
)


class SeedPlanSchemaError(ValueError):
    """A frozen plan cannot be normalised without guessing."""


def _int0(value, where: str) -> int:
    if isinstance(value, bool):
        raise SeedPlanSchemaError(f"{where} must be an integer, got "
                                  f"{value!r}")
    if isinstance(value, int):
        return value
    text = str(value or "").strip()
    try:
        return int(text, 0)
    except ValueError:
        raise SeedPlanSchemaError(
            f"{where} must be a decimal or 0x-hex integer, got {value!r}")


def _entry_shape(entry, index: int):
    where = f"seed_plan[{index}]"
    if not isinstance(entry, dict):
        raise SeedPlanSchemaError(f"{where} must be an object")
    has_f5 = _F5_REQUIRED <= set(entry)
    has_fr03 = _FR03_REQUIRED <= set(entry)
    if has_f5 and has_fr03:
        # A hybrid entry is only acceptable when every alias agrees; then the
        # presence of warmup/sample decides the model. Otherwise fail closed.
        _check_alias_conflicts(entry, where)
        return SCHEMA_F5 if "warmup" in entry or "sample" in entry \
            else SCHEMA_FR03
    if has_f5:
        _check_alias_conflicts(entry, where)
        return SCHEMA_F5
    if has_fr03:
        _check_alias_conflicts(entry, where)
        return SCHEMA_FR03
    raise SeedPlanSchemaError(
        f"{where} matches neither the f5-v1 schema "
        f"(requires {sorted(_F5_REQUIRED)}) nor the fr03-v1 schema "
        f"(requires {sorted(_FR03_REQUIRED)}); got fields {sorted(entry)}")


def _check_alias_conflicts(entry: dict, where: str):
    for new, old in _ALIAS_FIELDS:
        if new in entry and old in entry:
            a = _int0(entry[new], f"{where}.{new}")
            b = _int0(entry[old], f"{where}.{old}")
            if a != b:
                raise SeedPlanSchemaError(
                    f"{where}: conflicting aliases {old}={entry[old]!r} "
                    f"and {new}={entry[new]!r}")
    if "fault_type" in entry and "polarity" in entry:
        polarity = _int0(entry["polarity"], f"{where}.polarity")
        if polarity not in (0, 1):
            raise SeedPlanSchemaError(
                f"{where}.polarity must be 0 or 1, got {polarity}")
        fault_type = str(entry["fault_type"]).strip()
        want = "stuck_at_one" if polarity else "stuck_at_zero"
        if fault_type != want:
            raise SeedPlanSchemaError(
                f"{where}.fault_type {fault_type!r} conflicts with polarity "
                f"{polarity} (must be {want!r})")


def _canonical_entry(entry: dict, index: int, schema: str) -> dict:
    """Return a copy with agreeing aliases collapsed to the schema spelling."""
    out = copy.deepcopy(entry)
    where = f"seed_plan[{index}]"
    if schema == SCHEMA_FR03:
        # G accepts only fault_mask / vec_lane_offset; collapse the newer
        # spelling after the equality check.
        for new, old in _ALIAS_FIELDS:
            if new in out:
                out.pop(new, None)
    else:
        # S accepts only mask / lane_offset; fault_mask/vec_lane_offset and
        # fault_type are not f5-v1 identity fields.
        for new, old in _ALIAS_FIELDS:
            if old in out:
                out.pop(old, None)
        out.pop("fault_type", None)
    return out


def canonical_suite(suite: dict) -> dict:
    """Copy of the frozen suite with agreeing aliases collapsed.

    The raw frozen config on disk is never modified.  The returned document is
    only used to compute the canonical identity/hash; the caller records the
    raw config path and SHA separately.
    """
    if "seed_plan" not in suite:
        return copy.deepcopy(suite)
    plan = suite.get("seed_plan")
    if not isinstance(plan, list):
        raise SeedPlanSchemaError("suite.seed_plan must be a list")
    out = copy.deepcopy(suite)
    schema = detect_schema(suite)
    out["seed_plan"] = [
        _canonical_entry(entry, i, schema) for i, entry in enumerate(plan)
    ]
    return out


def detect_schema(suite: dict):
    """Return ``f5-v1``, ``fr03-v1`` or ``None`` (legacy F0 suite)."""
    if "seed_plan" not in suite:
        return SCHEMA_NONE
    plan = suite.get("seed_plan")
    if not isinstance(plan, list):
        raise SeedPlanSchemaError("suite.seed_plan must be a list")
    if not plan:
        raise SeedPlanSchemaError("suite.seed_plan must not be empty")
    kinds = {_entry_shape(entry, i) for i, entry in enumerate(plan)}
    if len(kinds) != 1:
        raise SeedPlanSchemaError(
            f"suite.seed_plan mixes schemas {sorted(kinds)}; one frozen plan "
            "must use one schema")
    return kinds.pop()


def normalise_plan(suite: dict) -> list:
    """Canonical plan entries for the detected schema."""
    schema = detect_schema(suite)
    canon = canonical_suite(suite)
    if schema == SCHEMA_F5:
        return S.normalise_seed_plan(canon)
    if schema == SCHEMA_FR03:
        entries = G.normalise_seed_plan(canon)
        targets = G.normalise_target_plan(canon)
        out = []
        for entry in entries:
            out.append({
                "schema_version": SCHEMA_FR03,
                "suite_seed": entry["suite_seed"],
                "submodel": entry["submodel"],
                "mask": entry["fault_mask"],
                "mask_value": entry["fault_mask_value"],
                "mask_domain": "lane",
                "mask_width": 64,
                "polarity": entry["polarity"],
                "fault_type": entry["fault_type"],
                "lane_offset": entry["vec_lane_offset"],
                "program_mask": dict(entry["program_mask"]),
                "targets": {pid: dict(t) for pid, t in targets.items()},
            })
        return out
    raise SeedPlanSchemaError("suite has no seed_plan")


def seed_entry(suite: dict, suite_seed: int):
    schema = detect_schema(suite)
    if schema is None:
        return None, None
    try:
        seed = int(suite_seed)
    except (TypeError, ValueError):
        raise SeedPlanSchemaError(
            f"suite_seed must be an integer, got {suite_seed!r}")
    for entry in normalise_plan(suite):
        if int(entry["suite_seed"]) == seed:
            return schema, entry
    raise SeedPlanSchemaError(
        f"suite_seed {seed} is not in the pre-registered plan "
        f"{[e['suite_seed'] for e in normalise_plan(suite)]}")


def suite_hash(suite: dict, kind: str):
    """Return ``(schema, hash)`` using the one real implementation per model.

    W5 and W6 have separate identity documents even under the f5-v1 plan
    schema; FR03 has a third document that already encodes the lane/mask
    semantics.  The program set decides the W5/W6 document, never the plan
    schema.
    """
    schema = detect_schema(suite)
    canon = canonical_suite(suite)
    if schema == SCHEMA_FR03:
        return schema, G.compute_suite_hash(canon)
    if kind == "w6":
        import fsu_w6_suite as WS
        return schema, WS.compute_suite_hash(canon)
    return schema, S.compute_suite_hash(canon)


def expected_binding(suite: dict, schema: str, entry: dict,
                     program_id: str) -> dict:
    """The exact plan projection a component manifest must record."""
    if schema == SCHEMA_FR03:
        return G.resolve_component_plan(suite, program_id, entry["suite_seed"])
    if schema == SCHEMA_F5:
        return S.seed_plan_identity(entry)
    return {}


def warmup_sample_contract(schema: str, entry: dict) -> dict:
    """Describe warmup/sample values, units and provenance without guessing."""
    if schema == SCHEMA_F5:
        sample = entry["sample"]
        return {
            "model": "CHAOSFPU",
            "warmup": {
                "value": int(entry["warmup"]),
                "unit": "eligible event ordinals skipped before install",
                "status": "declared",
                "source": "frozen config seed_plan[].warmup",
            },
            "sample": {
                "limit": int(sample["limit"]),
                "keep_first_last_n": int(sample["keep_first_last_n"]),
                "unit": "post-warmup ordinary eligible events",
                "status": "declared",
                "source": "frozen config seed_plan[].sample",
            },
        }
    if schema == SCHEMA_FR03:
        proof = (
            "physreg permanent-cell injector: the frozen plan has no "
            "warmup/sample field; the recorded command uses --chaos_phys "
            "with --first_clock/--max_faults and no --chaos_fpu or "
            "--fpu_f5_* flags; inject/config.ini [board.chaos_phys] has "
            "firstClock=0, maxFaults=1, probability=1.0"
        )
        return {
            "model": "CHAOSPhysReg",
            "warmup": {
                "value": None,
                "unit": "n/a",
                "status": "not_applicable",
                "source": proof,
            },
            "sample": {
                "value": None,
                "unit": "n/a",
                "status": "not_applicable",
                "source": proof,
            },
        }
    return {"model": None, "warmup": {"status": "not_applicable"},
            "sample": {"status": "not_applicable"}}


def command_flags(command) -> dict:
    """Parse a recorded gem5 argv list into ``{flag: value-or-True}``."""
    out = {}
    if not isinstance(command, (list, tuple)):
        return out
    i = 0
    while i < len(command):
        item = str(command[i])
        if item.startswith("--"):
            key, sep, value = item.partition("=")
            if sep:
                out[key] = value
            elif i + 1 < len(command) and not str(command[i + 1]).startswith(
                    "--"):
                out[key] = str(command[i + 1])
                i += 1
            else:
                out[key] = True
        i += 1
    return out


def verify_binding(schema: str, entry: dict, program_id: str,
                   recorded: dict) -> list:
    """Compare a recorded plan projection against the frozen plan.

    Returns human-readable mismatch strings.  Missing recorded fields are
    returned as ``missing:<field>`` so the audit can classify them as
    evidence-missing instead of a value drift.
    """
    if schema == SCHEMA_F5:
        expected = S.seed_plan_identity(entry)
    elif schema == SCHEMA_FR03:
        expected = _fr03_expected(entry, program_id)
    else:
        return []
    if not isinstance(recorded, dict):
        return ["missing:binding"]
    issues = []
    for key, want in expected.items():
        if key not in recorded:
            issues.append(f"missing:{key}")
        elif recorded.get(key) != want:
            issues.append(f"{key}={recorded.get(key)!r} != {want!r}")
    return issues


def _fr03_expected(entry: dict, program_id: str) -> dict:
    target = entry["targets"][program_id]
    return {
        "suite_seed": entry["suite_seed"],
        "submodel": entry["submodel"],
        "program_id": program_id,
        "target_phys_idx": target["target_phys_idx"],
        "vec_lane_width": target["vec_lane_width"],
        "vec_lane_offset": entry["lane_offset"],
        "fault_mask": entry["program_mask"][program_id],
        "fault_mask_value": int(entry["program_mask"][program_id], 0),
        "polarity": entry["polarity"],
        "fault_type": entry["fault_type"],
        "require_allocated": True,
        "reg_class": "vector",
        "injection_mode": "phys",
        "semantic_role": "FR03",
        "bits_to_change": 1,
        "precision": target["precision"],
    }


def expected_fr03_target_entry(suite: dict, entry: dict,
                               program_id: str) -> dict:
    """Exact ``target_plan_entry`` written by the FR03 gate/runner."""
    return G.resolve_component_plan(
        canonical_suite(suite), program_id, entry["suite_seed"])


def physical_identity(schema: str, entry: dict, program_id: str,
                      manifest: dict, component_manifest: dict,
                      command, config_ini_text: str) -> dict:
    """Cross-check the physical cell/lane identity from four evidence sources.

    Returns ``{"ok": bool, "sources": {...}, "violations": [...],
    "missing": [...]}``.  Values are only compared when actually present;
    absent sources are reported as missing, never filled in.
    """
    sources = {}
    missing = []
    violations = []

    expected = _fr03_expected(entry, program_id) \
        if schema == SCHEMA_FR03 else None

    def record(name, value):
        if value in (None, {}, ""):
            missing.append(name)
        else:
            sources[name] = value

    inj = (manifest or {}).get("effective_injector") or {}
    phys = (inj.get("physreg_mode") or {}) if isinstance(inj, dict) else {}
    record("manifest.effective_injector.physreg_mode", phys)
    cm_target = (component_manifest or {}).get("target_plan_entry")
    record("component_manifest.target_plan_entry", cm_target)
    flags = command_flags(command)
    if flags:
        record("chain_report.command.inject", {
            k: flags.get(k) for k in (
                "--phys_mode", "--phys_target_idx", "--vec_lane_width",
                "--vec_lane_offset", "--fault_mask", "--fault_type",
                "--phys_reg_class", "--bits_to_change",
            ) if k in flags})
    ini = _parse_config_ini(config_ini_text)
    chaos_phys = ini.get("board.chaos_phys") or {}
    record("inject/config.ini[board.chaos_phys]", chaos_phys)

    if not sources:
        return {"ok": False, "sources": {}, "missing": missing or
                ["all physical-identity sources"], "violations": []}

    if cm_target and expected:
        for key, want in expected.items():
            if key in cm_target and cm_target.get(key) != want:
                violations.append(
                    f"component target_plan_entry {key}={cm_target.get(key)!r}"
                    f" != frozen {want!r}")
    if phys and expected:
        mapping = (
            ("injection_mode", "injection_mode"),
            ("reg_class", "reg_class"),
            ("target_phys_idx", "target_phys_idx"),
            ("require_allocated", "require_allocated"),
            ("vec_lane_width", "vec_lane_width"),
            ("vec_lane_offset", "vec_lane_offset"),
            ("fault_type", "fault_type"),
            ("fault_mask", "fault_mask"),
            ("semantic_role", "semantic_role"),
            ("bits_to_change", "bits_to_change"),
        )
        for mkey, ekey in mapping:
            if mkey in phys and phys.get(mkey) != expected.get(ekey):
                violations.append(
                    f"manifest {mkey}={phys.get(mkey)!r} != frozen "
                    f"{expected.get(ekey)!r}")
    if flags and expected:
        flag_map = (
            ("--phys_mode", "injection_mode"),
            ("--phys_reg_class", "reg_class"),
            ("--vec_lane_width", "vec_lane_width"),
            ("--vec_lane_offset", "vec_lane_offset"),
            ("--fault_type", "fault_type"),
            ("--bits_to_change", "bits_to_change"),
        )
        for flag, ekey in flag_map:
            if flag in flags and str(flags[flag]) != str(expected.get(ekey)):
                violations.append(
                    f"command {flag}={flags[flag]!r} != frozen "
                    f"{expected.get(ekey)!r}")
        if "--phys_target_idx" in flags and int(
                flags["--phys_target_idx"]) != expected["target_phys_idx"]:
            violations.append(
                f"command --phys_target_idx={flags['--phys_target_idx']} != "
                f"frozen {expected['target_phys_idx']}")
        if "--fault_mask" in flags and int(
                str(flags["--fault_mask"]), 0) != expected["fault_mask_value"]:
            violations.append(
                f"command --fault_mask={flags['--fault_mask']} != frozen "
                f"{expected['fault_mask_value']}")
    if chaos_phys and expected:
        ini_map = (
            ("injectionMode", "injection_mode"),
            ("regTargetClass", "reg_class"),
            ("targetPhysRegIdx", "target_phys_idx"),
            ("vecLaneWidth", "vec_lane_width"),
            ("vecLaneOffset", "vec_lane_offset"),
            ("faultType", "fault_type"),
            ("bitsToChange", "bits_to_change"),
        )
        for ikey, ekey in ini_map:
            if ikey in chaos_phys:
                got = _as_scalar(chaos_phys[ikey])
                want = expected.get(ekey)
                if got != want:
                    violations.append(
                        f"config.ini {ikey}={chaos_phys[ikey]!r} != frozen "
                        f"{want!r}")
        if "faultMask" in chaos_phys:
            should = expected["fault_mask_value"]
            got_mask = _as_scalar(chaos_phys["faultMask"])
            if got_mask != should:
                violations.append(
                    f"config.ini faultMask={chaos_phys['faultMask']!r} != "
                    f"frozen {should}")
        if "requireAllocated" in chaos_phys and str(
                chaos_phys["requireAllocated"]).lower() not in (
                    "true", "1"):
            violations.append("config.ini requireAllocated is not true")

    return {"ok": not violations and not missing,
            "sources": sources, "missing": missing,
            "violations": violations}


def _as_scalar(value):
    """Parse a config.ini token as int/bool when unambiguous, else keep text."""
    if isinstance(value, bool):
        return value
    text = str(value).strip()
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        return int(text, 0)
    except ValueError:
        return text


def _parse_config_ini(text: str) -> dict:
    sections, current = {}, None
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, {})
            continue
        if current is not None and "=" in line:
            key, _, value = line.partition("=")
            sections[current][key.strip()] = value.strip()
    return sections


def describe_document(suite: dict) -> dict:
    """Small diagnostic document: schema, aliases and per-field provenance."""
    schema = detect_schema(suite)
    plan = suite.get("seed_plan")
    aliases = []
    if isinstance(plan, list):
        for i, entry in enumerate(plan):
            if not isinstance(entry, dict):
                continue
            for new, old in _ALIAS_FIELDS:
                if new in entry and old in entry:
                    aliases.append({
                        "index": i, "aliases": [new, old],
                        "value": _int0(entry[new], f"seed_plan[{i}].{new}"),
                    })
    return {
        "schema": schema,
        "bindings": BINDING_KEY.get(schema),
        "alias_normalisations": aliases,
        "hash_implementation": (
            "fsu_fr03_suite_gate.compute_suite_hash"
            if schema == SCHEMA_FR03 else
            "fsu_suite.compute_suite_hash" if schema == SCHEMA_F5 else
            "kind-specific legacy hash"),
        "mask_domain": "lane-relative (both injectors)",
        "warmup_sample": (
            "eligible-event ordinals (CHAOSFPU F5)"
            if schema == SCHEMA_F5 else
            "not applicable (CHAOSPhysReg permanent cell)"
            if schema == SCHEMA_FR03 else "no plan"),
        "raw_config_sha256": None,
    }
