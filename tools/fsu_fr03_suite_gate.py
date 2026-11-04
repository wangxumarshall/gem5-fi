#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_fr03_suite_gate.py — FR03-F5-W5 / W6 suite gate (never counted as a seed).

FR03 is the *permanent physical PRF cell* model:

    permanent key = reg_class + phys_index + lane/mask + polarity

`generation` is exposure/provenance IDENTITY only; it is never a clear
condition.  A free/realloc/squash keeps the same physical cell stuck, other
cells/classes/lanes never cross-talk, reads and writes are counted
separately, and a component run is never a formal seed.

This tool is deliberately self-contained for FR03 suites.  The generic
`fsu_suite.py` / `fsu_w6_suite.py` seed_plan contract is the CHAOSFPU
(F5 FP-pipeline) contract: it requires `injector.component == "fsu"` and a
`fpu_mode` geometry.  FR03 injects through CHAOSPhysReg (`component ==
"physreg"`), so reusing that contract would either be rejected or silently
mis-resolve the fault.  The FR03 identity/hash therefore lives here, but the
*execution* path is the existing, unmodified `fsu_seed_runner.run_seed`
physreg route:

    manifest.injector.component == "physreg"
      -> build_cmd -> _build_physreg_cmd -> --chaos_phys ...

Identity that participates in `suite_hash` (and nothing else):

  * suite_id / suite_version / suite_family / fixed program order+count;
  * each program's source/binary/golden-array SHA-256, FINAL token, scale,
    input_id and the full pre-registered element-oracle meta;
  * compiler version/cflags and oracle version;
  * run_defaults identity (FR03 / FSU Pipe / F5 / W5|W6 / B0 / timeout 3600);
  * the injector identity (component=physreg, phys mode, vector class,
    requireAllocated=true, semantic role FR03, max_faults=1, first_clock=0);
  * the per-program physical target plan (target_phys_idx, vec_lane_width,
    precision);
  * the 3-entry pre-registered seed plan (submodel, fault mask, polarity,
    lane offset, fault type).

Run results, attempts, statuses, oracle outcomes and paths are excluded.

Target selection (readiness, no fault-run feedback)
---------------------------------------------------
* `numPhysVecRegs = 48` in the C3/B0 O3 configuration.
* AArch64 VecRegClass exposes `NumVecRegs = 32 (V0-V31) + 8 special + 4
  interleave = 44` architectural registers; the initial rename map consumes
  physical slots 0..43, leaving only slots 44..47 on the dynamic free list
  (W3 gate log evidence: `FreeListSize: 4` at cycle 0).
* Slots 32..43 are the *special/interleave* architectural slots and are
  excluded from the allowed target set.  Slots >= 48 do not exist.
* The target is dynamic-pool slot 47, the highest allocatable Vec physical
  slot (44..47).  Gate v1 used slot 0 (V0/libc memset) and produced a
  truncated crash stream; that design correction is recorded in the gate
  evidence.  Slot 47 is allocated from the dynamic free list for real
  vector dests and `requireAllocated=true` refuses to burn the fault while
  free.  Retry pacing is at least 100 cycles and skip logs are bounded.
  Selection depends only on PRF geometry/no-fault allocation, never on a
  fault-run SDC result.

Modes
-----
  --print-suite-hash  print the recomputed suite_hash and identity digest
  --print-commands    print the exact per-component CHAOSPhysReg command
                      (no gem5 execution; --all-seeds covers 1..3)
  --verify-only       re-validate existing gate attempts without gem5
  default             run every component of one suite seed

Evidence ALWAYS lives under runs/fsu-gates/...; this tool refuses runs/fsu.
It writes no formal suite manifest / AUTHORITATIVE under runs/fsu and never
touches the RunID registry.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_oracle as O  # noqa: E402
import fsu_seed_audit as A  # noqa: E402
import fsu_seed_runner as R  # noqa: E402
import fsu_suite as S  # noqa: E402
import fsu_w6_oracle as WO  # noqa: E402
import fsu_w6_suite as WS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
DEFAULT_CONFIG = ROOT / "configs/se/ooo_proxy.py"

W5_ORDER = tuple(S.PROGRAM_ORDER)          # gemm -> 2mm -> lu -> cholesky -> jacobi-2d
W6_ORDER = tuple(WS.W6_PROGRAM_ORDER)      # svd -> fft -> sparse-cg
SUITE_FAMILIES = {
    "W5": {"order": W5_ORDER, "count": len(W5_ORDER), "load_id": "W5"},
    "W6": {"order": W6_ORDER, "count": len(W6_ORDER), "load_id": "W6"},
}
DEFAULT_COMPONENT_SEED_POLICY = "w5-component-seed-v1"

# O3 C3/B0 vector PRF geometry (configs/se/ooo_proxy.py: phys_vec=48; ARM
# VecRegClass NumVecRegs = 32 + 8 special + 4 interleave).
NUM_PHYS_VEC_REGS = 48
VEC_ARCH_REGS = 44
SPECIAL_VEC_SLOTS = tuple(range(32, VEC_ARCH_REGS))   # 32..43 excluded
ALLOWED_TARGETS = tuple(range(0, 32)) + tuple(
    range(VEC_ARCH_REGS, NUM_PHYS_VEC_REGS))            # 0..31 + 44..47
DYNAMIC_POOL = tuple(range(VEC_ARCH_REGS, NUM_PHYS_VEC_REGS))
# Pre-registered FR03 target for every component (see module docstring).
FR03_TARGET_PHYS_IDX = 47

SEED_PLAN_COUNT = 3
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEX16 = re.compile(r"^[0-9a-f]{16}$")
DECIDABLE_ORACLE = ("SDC", "MASKED")
L5_OK_TERMINALS = ("committed", "squashed")
PROGRAM_FIELDS = (
    "program_id", "program_index", "source_sha256", "binary_sha256",
    "golden_array_sha256", "golden", "scale", "input_id", "element_oracle",
)
SEED_FIELDS = (
    "suite_seed", "submodel", "fault_mask", "polarity", "vec_lane_offset",
    "fault_type",
)
TARGET_FIELDS = ("target_phys_idx", "vec_lane_width", "precision")


class FR03SuiteError(ValueError):
    """FR03 suite identity/target plan is not established: fail loudly."""


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _int(value, where: str, minimum=None) -> int:
    if isinstance(value, bool):
        raise FR03SuiteError(f"{where} must be an integer, got {value!r}")
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise FR03SuiteError(f"{where} must be an integer, got {value!r}")
    if minimum is not None and value < minimum:
        raise FR03SuiteError(f"{where} must be >= {minimum}, got {value}")
    return value


def _hash(value, where: str, allow_pending: bool = False) -> str:
    text = str(value or "")
    if allow_pending and text == "pending":
        return text
    if not _HEX64.match(text):
        raise FR03SuiteError(f"{where}: expected 64-hex SHA-256, got {value!r}")
    return text


def _final(value, where: str, allow_pending: bool = False) -> str:
    text = str(value or "").strip()
    if allow_pending and text in ("", "pending"):
        return text
    if not _HEX16.match(text):
        raise FR03SuiteError(f"{where}: expected 16-hex FINAL token, "
                             f"got {value!r}")
    return text


def _mask_value(value, lane_width: int, where: str) -> int:
    if isinstance(value, bool):
        raise FR03SuiteError(f"{where} must be a mask, got {value!r}")
    if isinstance(value, int):
        parsed = value
    else:
        text = str(value or "").strip()
        try:
            parsed = int(text, 0)
        except ValueError:
            raise FR03SuiteError(f"{where} must be an integer or 0x-hex mask, "
                                 f"got {value!r}")
    if parsed <= 0:
        raise FR03SuiteError(f"{where} must be a non-zero mask")
    if parsed >= (1 << lane_width):
        raise FR03SuiteError(f"{where}=0x{parsed:x} does not fit "
                             f"lane_width={lane_width}")
    return parsed


def _mask_text(value: int, lane_width: int) -> str:
    width = 8 if lane_width <= 32 else 16
    return f"0x{value:0{width}x}"


def _normalise_cflags(value) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(x) for x in value)
    return str(value or "")


def family_of(suite: dict) -> str:
    family = str(suite.get("suite_family", "") or "").strip().upper()
    if family not in SUITE_FAMILIES:
        raise FR03SuiteError(
            f"suite.suite_family must be one of {list(SUITE_FAMILIES)}, "
            f"got {family!r}")
    return family


def program_order(family: str) -> tuple:
    return SUITE_FAMILIES[family]["order"]


def program_count(family: str) -> int:
    return SUITE_FAMILIES[family]["count"]


# ---------------------------------------------------------------------------
# Structure validation
# ---------------------------------------------------------------------------
def _program_map(suite: dict, family: str) -> dict:
    programs = suite.get("programs")
    if not isinstance(programs, list):
        raise FR03SuiteError("suite.programs must be a list")
    by_id = {}
    for p in programs:
        if not isinstance(p, dict):
            raise FR03SuiteError("suite.programs entries must be objects")
        pid = str(p.get("program_id", "")).strip()
        if pid not in program_order(family):
            raise FR03SuiteError(
                f"unknown {family} program_id {pid!r}; expected "
                f"{list(program_order(family))}")
        if pid in by_id:
            raise FR03SuiteError(f"duplicate program component: {pid}")
        by_id[pid] = p
    missing = [p for p in program_order(family) if p not in by_id]
    if missing:
        raise FR03SuiteError(f"suite missing program component(s): {missing}")
    return by_id


def _validate_order_and_count(suite: dict):
    family = family_of(suite)
    order = suite.get("program_order")
    if not isinstance(order, list) or tuple(order) != program_order(family):
        raise FR03SuiteError(
            "program_order is fixed and must not be reordered by results: "
            f"want {list(program_order(family))}, got {order}")
    count = _int(suite.get("program_count"), "suite.program_count",
                 minimum=0)
    if count != program_count(family):
        raise FR03SuiteError(f"suite.program_count must be "
                             f"{program_count(family)}, got {count}")
    by_id = _program_map(suite, family)
    for index, pid in enumerate(program_order(family)):
        declared = _int(by_id[pid].get("program_index", index),
                        f"{pid}.program_index")
        if declared != index:
            raise FR03SuiteError(
                f"{pid}.program_index must be {index} in fixed order "
                f"{list(program_order(family))}, got {declared}")
    return family, by_id


def normalise_injector(suite: dict) -> dict:
    """Validate the FR03 CHAOSPhysReg base injector; reject any FSU/FPU mix."""
    injector = suite.get("injector")
    if not isinstance(injector, dict):
        raise FR03SuiteError("suite.injector must be an object")
    if "fpu_mode" in injector:
        raise FR03SuiteError(
            "an FR03 suite injects through CHAOSPhysReg; "
            "suite.injector.fpu_mode is forbidden")
    component = str(injector.get("component", "") or "")
    if component != "physreg":
        raise FR03SuiteError(
            f"FR03 requires injector.component == 'physreg', got {component!r}")
    max_faults = _int(injector.get("max_faults", 1),
                      "injector.max_faults", minimum=0)
    if max_faults != 1:
        raise FR03SuiteError("an FR03 component injects exactly one "
                             f"permanent fault (max_faults must be 1, got "
                             f"{max_faults})")
    first_clock = _int(injector.get("first_clock", 0),
                       "injector.first_clock", minimum=0)
    probability = injector.get("probability", 1.0)
    if float(probability) != 1.0:
        raise FR03SuiteError("FR03 requires injector.probability == 1.0")
    phys = injector.get("physreg_mode")
    if not isinstance(phys, dict):
        raise FR03SuiteError("injector.physreg_mode must be an object")
    if str(phys.get("injection_mode", "phys")) != "phys":
        raise FR03SuiteError(
            "FR03 requires physreg_mode.injection_mode == 'phys' "
            f"(got {phys.get('injection_mode')!r})")
    if str(phys.get("reg_class", "vector")) != "vector":
        raise FR03SuiteError(
            "FR03 targets VecRegClass; physreg_mode.reg_class must be "
            f"'vector', got {phys.get('reg_class')!r}")
    if phys.get("require_allocated") is not True:
        raise FR03SuiteError(
            "FR03 requires physreg_mode.require_allocated == true")
    if str(phys.get("semantic_role", "")) != "FR03":
        raise FR03SuiteError(
            "FR03 requires physreg_mode.semantic_role == 'FR03'")
    if _int(phys.get("bits_to_change", 1),
            "physreg_mode.bits_to_change", minimum=0) != 1:
        raise FR03SuiteError(
            "FR03 uses the explicit fixed mask; bits_to_change must be 1")
    return {
        "component": "physreg",
        "max_faults": 1,
        "first_clock": first_clock,
        "probability": 1.0,
        "physreg_mode": {
            "injection_mode": "phys",
            "reg_class": "vector",
            "require_allocated": True,
            "semantic_role": "FR03",
            "bits_to_change": 1,
        },
    }


def normalise_target_plan(suite: dict) -> dict:
    """Validate the per-program physical target plan (identity, not results)."""
    family, by_id = _validate_order_and_count(suite)
    raw = suite.get("target_plan")
    if not isinstance(raw, dict) or not raw:
        raise FR03SuiteError("suite.target_plan must be a non-empty object "
                             "keyed by program_id")
    unknown = sorted(set(raw) - set(program_order(family)))
    if unknown:
        raise FR03SuiteError(f"target_plan has unknown program_id(s): "
                             f"{unknown}")
    out = {}
    for pid in program_order(family):
        if pid not in raw:
            raise FR03SuiteError(f"target_plan missing program {pid!r}")
        entry = raw[pid]
        if not isinstance(entry, dict):
            raise FR03SuiteError(f"target_plan[{pid}] must be an object")
        missing = [k for k in TARGET_FIELDS if k not in entry]
        if missing:
            raise FR03SuiteError(f"target_plan[{pid}] missing {missing}")
        unknown = sorted(set(entry) - set(TARGET_FIELDS))
        if unknown:
            raise FR03SuiteError(f"target_plan[{pid}] has unknown field(s): "
                                 f"{unknown}")
        target = _int(entry["target_phys_idx"],
                      f"target_plan[{pid}].target_phys_idx", minimum=0)
        if target in SPECIAL_VEC_SLOTS:
            raise FR03SuiteError(
                f"target_plan[{pid}]: physical Vec slot {target} is a "
                "special/interleave architectural slot (32..43) and is "
                "excluded")
        if target not in ALLOWED_TARGETS:
            raise FR03SuiteError(
                f"target_plan[{pid}]: target_phys_idx {target} outside the "
                f"allocatable Vec PRF range 0..{NUM_PHYS_VEC_REGS - 1} "
                f"(allowed normal {list(ALLOWED_TARGETS)})")
        lane_width = _int(entry["vec_lane_width"],
                          f"target_plan[{pid}].vec_lane_width", minimum=8)
        if lane_width not in (8, 16, 32, 64):
            raise FR03SuiteError(
                f"target_plan[{pid}].vec_lane_width must be 8/16/32/64, "
                f"got {lane_width}")
        precision = str(entry["precision"]).strip()
        if precision not in ("fp32", "fp64"):
            raise FR03SuiteError(
                f"target_plan[{pid}].precision must be fp32/fp64, "
                f"got {precision!r}")
        if precision == "fp64" and lane_width != 64:
            raise FR03SuiteError(f"target_plan[{pid}]: fp64 requires "
                                 "vec_lane_width 64")
        if precision == "fp32" and lane_width < 32:
            raise FR03SuiteError(f"target_plan[{pid}]: fp32 requires "
                                 "vec_lane_width >= 32")
        # The program's element-oracle dtype must agree with the target
        # precision; a silent mismatch would compare the wrong domain.
        eo = by_id[pid].get("element_oracle") or {}
        meta_dtype = str((eo.get("meta") or {}).get("dtype", ""))
        if meta_dtype and meta_dtype != precision:
            raise FR03SuiteError(
                f"target_plan[{pid}].precision {precision} != element_oracle "
                f"dtype {meta_dtype}")
        out[pid] = {
            "target_phys_idx": target,
            "vec_lane_width": lane_width,
            "precision": precision,
        }
    return out


def normalise_seed_plan(suite: dict) -> list:
    """Validate the 3 frozen FR03 suite seeds (mask/polarity/lane)."""
    family, by_id = _validate_order_and_count(suite)
    targets = normalise_target_plan(suite)
    plan = suite.get("seed_plan")
    if not isinstance(plan, list):
        raise FR03SuiteError("suite.seed_plan must be a list")
    if len(plan) != SEED_PLAN_COUNT:
        raise FR03SuiteError(f"suite.seed_plan must contain exactly "
                             f"{SEED_PLAN_COUNT} entries, got {len(plan)}")
    entries = []
    for index, entry in enumerate(plan):
        where = f"seed_plan[{index}]"
        if not isinstance(entry, dict):
            raise FR03SuiteError(f"{where} must be an object")
        missing = [k for k in ("suite_seed", "submodel", "fault_mask",
                               "polarity", "vec_lane_offset")
                   if k not in entry]
        if missing:
            raise FR03SuiteError(f"{where} missing field(s): {missing}")
        unknown = sorted(set(entry) - set(SEED_FIELDS))
        if unknown:
            raise FR03SuiteError(f"{where} has unknown field(s): {unknown}")
        seed = _int(entry["suite_seed"], f"{where}.suite_seed", minimum=1)
        submodel = str(entry.get("submodel", "") or "").strip()
        if not submodel:
            raise FR03SuiteError(f"{where}.submodel is required")
        polarity = _int(entry["polarity"], f"{where}.polarity", minimum=0)
        if polarity not in (0, 1):
            raise FR03SuiteError(f"{where}.polarity must be 0 or 1")
        fault_type = str(entry.get("fault_type")
                         or ("stuck_at_one" if polarity else
                             "stuck_at_zero")).strip()
        want_type = "stuck_at_one" if polarity else "stuck_at_zero"
        if fault_type != want_type:
            raise FR03SuiteError(
                f"{where}.fault_type {fault_type!r} is inconsistent with "
                f"polarity {polarity} (must be {want_type!r})")
        lane_offset = _int(entry["vec_lane_offset"],
                           f"{where}.vec_lane_offset", minimum=0)
        mask_by_program = {}
        for pid in program_order(family):
            lane_width = targets[pid]["vec_lane_width"]
            if lane_offset >= 128 // lane_width:
                raise FR03SuiteError(
                    f"{where}.vec_lane_offset {lane_offset} >= "
                    f"{128 // lane_width} for {pid} lane_width {lane_width}")
            mask = _mask_value(entry["fault_mask"], lane_width,
                               f"{where}.fault_mask")
            mask_by_program[pid] = _mask_text(mask, lane_width)
        entries.append({
            "suite_seed": seed,
            "submodel": submodel,
            "fault_mask": _mask_text(
                _mask_value(entry["fault_mask"], 64, f"{where}.fault_mask"),
                64),
            "fault_mask_value": _mask_value(entry["fault_mask"], 64,
                                            f"{where}.fault_mask"),
            "polarity": polarity,
            "fault_type": fault_type,
            "vec_lane_offset": lane_offset,
            "program_mask": mask_by_program,
        })
    seeds = [e["suite_seed"] for e in entries]
    if sorted(seeds) != list(range(1, SEED_PLAN_COUNT + 1)):
        raise FR03SuiteError("seed_plan suite_seed values must be exactly "
                             f"{list(range(1, SEED_PLAN_COUNT + 1))}, "
                             f"got {seeds}")
    return sorted(entries, key=lambda e: e["suite_seed"])


def seed_plan_map(suite: dict) -> dict:
    return {e["suite_seed"]: e for e in normalise_seed_plan(suite)}


# ---------------------------------------------------------------------------
# Identity + suite_hash
# ---------------------------------------------------------------------------
def _oracle_identity(program: dict, family: str) -> dict:
    eo = program.get("element_oracle")
    if not isinstance(eo, dict):
        raise FR03SuiteError(f"{program.get('program_id')}: element_oracle is "
                             "required (FR03 certification is element-wise)")
    try:
        if family == "W6":
            meta = WO.validate_meta(eo.get("meta") or {})
        else:
            meta = O.validate_meta(eo.get("meta") or {})
    except (O.OracleError, WO.W6OracleError) as e:
        raise FR03SuiteError(
            f"{program.get('program_id')}: invalid element_oracle meta: {e}")
    if meta["program_id"] != program.get("program_id"):
        raise FR03SuiteError(
            f"{program.get('program_id')}: element_oracle meta program_id "
            "drift")
    version = str(eo.get("oracle_version", "") or "")
    if version != meta["oracle_version"]:
        raise FR03SuiteError(
            f"{program.get('program_id')}: element_oracle oracle_version "
            "drift")
    return {"oracle_version": version, "meta": meta}


def suite_identity_document(suite: dict, allow_pending: bool = True) -> dict:
    family, by_id = _validate_order_and_count(suite)
    injector = normalise_injector(suite)
    targets = normalise_target_plan(suite)
    plan = normalise_seed_plan(suite)

    programs = []
    for index, pid in enumerate(program_order(family)):
        p = by_id[pid]
        scale = p.get("scale")
        if not isinstance(scale, dict) or not scale:
            raise FR03SuiteError(f"{pid}.scale must be a non-empty object")
        oracle = _oracle_identity(p, family)
        programs.append({
            "program_id": pid,
            "program_index": index,
            "source_sha256": _hash(p.get("source_sha256"),
                                   f"{pid}.source_sha256", allow_pending),
            "binary_sha256": _hash(p.get("binary_sha256"),
                                   f"{pid}.binary_sha256", allow_pending),
            "golden_array_sha256": _hash(
                p.get("golden_array_sha256"),
                f"{pid}.golden_array_sha256", allow_pending),
            "final": _final(p.get("golden"), f"{pid}.golden", allow_pending),
            "scale": scale,
            "input_id": str(p.get("input_id", "") or ""),
            "element_oracle": oracle,
        })

    compiler = suite.get("compiler") or {}
    if not isinstance(compiler, dict):
        raise FR03SuiteError("suite.compiler must be an object")
    version = str(compiler.get("version") or "").strip()
    cflags = _normalise_cflags(compiler.get("cflags"))
    if not version or not cflags.strip():
        raise FR03SuiteError("suite.compiler.version/cflags are required")
    oracle = suite.get("oracle") or {}
    if not isinstance(oracle, dict) or not str(
            oracle.get("version") or "").strip():
        raise FR03SuiteError("suite.oracle.version is required")

    defaults = suite.get("run_defaults") or {}
    if not isinstance(defaults, dict):
        raise FR03SuiteError("suite.run_defaults must be an object")
    limits = defaults.get("limits") or {}
    doc = {
        "suite_id": str(suite.get("suite_id", "")).strip(),
        "suite_version": str(suite.get("suite_version", "")).strip(),
        "suite_family": family,
        "program_order": list(program_order(family)),
        "program_count": program_count(family),
        "programs": programs,
        "compiler": {"version": version, "cflags": cflags},
        "oracle": {"version": str(oracle["version"])},
        "run_defaults_identity": {
            k: str(defaults.get(k, "")) for k in (
                "model_id", "unit", "freq", "load_id", "config_family",
                "config_profile")
        },
        "limits_identity": {"timeout_s": _int(
            limits.get("timeout_s", 0), "run_defaults.limits.timeout_s",
            minimum=0)},
        "injector_identity": injector,
        "target_plan": {pid: dict(targets[pid])
                        for pid in program_order(family)},
        "seed_plan": [{
            "suite_seed": e["suite_seed"],
            "submodel": e["submodel"],
            "fault_mask": e["fault_mask"],
            "polarity": e["polarity"],
            "fault_type": e["fault_type"],
            "vec_lane_offset": e["vec_lane_offset"],
        } for e in plan],
    }
    if not doc["suite_id"] or not doc["suite_version"]:
        raise FR03SuiteError("suite_id and suite_version are required")
    if doc["run_defaults_identity"]["model_id"] != "FR03":
        raise FR03SuiteError("an FR03 suite must declare model_id=FR03")
    if doc["run_defaults_identity"]["freq"] != "F5":
        raise FR03SuiteError("an FR03 suite gate is F5")
    if doc["run_defaults_identity"]["unit"] != "FSU Pipe":
        raise FR03SuiteError("an FR03 suite must declare unit='FSU Pipe'")
    if doc["run_defaults_identity"]["load_id"] != \
            SUITE_FAMILIES[family]["load_id"]:
        raise FR03SuiteError(
            f"{family} suite must declare load_id="
            f"{SUITE_FAMILIES[family]['load_id']}")
    if doc["run_defaults_identity"]["config_profile"] != "B0":
        raise FR03SuiteError("an FR03 suite gate must run config_profile=B0")
    if doc["limits_identity"]["timeout_s"] != 3600:
        raise FR03SuiteError("an FR03 suite must declare timeout_s=3600")
    return doc


def compute_suite_hash(suite: dict) -> str:
    return hashlib.sha256(canonical_bytes(
        suite_identity_document(suite))).hexdigest()


def validate_suite_manifest(suite: dict, require_hashes: bool = False,
                            require_suite_hash: bool = False) -> dict:
    doc = suite_identity_document(suite, allow_pending=not require_hashes)
    if require_hashes:
        for p in doc["programs"]:
            for key in ("source_sha256", "binary_sha256",
                        "golden_array_sha256"):
                _hash(p[key], f"{p['program_id']}.{key}", allow_pending=False)
            if not p["final"]:
                raise FR03SuiteError(f"{p['program_id']}.golden is required")
    computed = hashlib.sha256(canonical_bytes(doc)).hexdigest()
    declared = suite.get("suite_hash")
    if declared is not None:
        declared = _hash(declared, "suite.suite_hash", allow_pending=False)
        if declared != computed:
            raise FR03SuiteError(
                f"suite_hash drift: declared {declared}, recomputed {computed}")
    elif require_suite_hash:
        raise FR03SuiteError("suite.suite_hash is required before a gate run")
    return {"ok": True, "suite_hash": computed, "identity": doc}


def load_suite(path: Path, root: Path = ROOT,
               require_hashes: bool = True) -> dict:
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
                raise FR03SuiteError(f"{pid}: {kind} missing: {path_obj}")
            got = sha256_file(path_obj)
            if got != want:
                raise FR03SuiteError(
                    f"{pid}: {kind} SHA drift: {got} != {want}")
        golden = Path(p["element_oracle"]["golden_array"])
        if not golden.is_absolute():
            golden = root / golden
        if not golden.exists():
            raise FR03SuiteError(f"{pid}: golden array missing: {golden}")
        got = sha256_file(golden)
        if got != p["golden_array_sha256"]:
            raise FR03SuiteError(
                f"{pid}: golden array SHA drift: {got} != "
                f"{p['golden_array_sha256']}")
    return {"suite": suite, "suite_hash": info["suite_hash"],
            "identity": info["identity"]}


# ---------------------------------------------------------------------------
# Component resolution
# ---------------------------------------------------------------------------
def derive_component_seed(suite: dict, suite_seed: int,
                          program_id: str) -> int:
    family = family_of(suite)
    policy = str(suite.get("component_seed_policy_version")
                 or DEFAULT_COMPONENT_SEED_POLICY)
    if family == "W6":
        return WS.derive_component_seed(
            int(suite_seed), program_id, policy, suite["suite_id"],
            suite["suite_version"])
    return S.derive_component_seed(
        int(suite_seed), program_id, policy, suite["suite_id"],
        suite["suite_version"])


def derive_component_seeds(suite: dict, suite_seed: int) -> dict:
    seeds = {pid: derive_component_seed(suite, suite_seed, pid)
             for pid in program_order(family_of(suite))}
    if len(set(seeds.values())) != len(seeds):
        raise FR03SuiteError(f"component seed collision: {seeds}")
    return seeds


def resolve_component_plan(suite: dict, program_id: str,
                           suite_seed: int) -> dict:
    """Resolve the frozen FR03 target/mask/polarity for one component."""
    family = family_of(suite)
    if program_id not in program_order(family):
        raise FR03SuiteError(f"unknown {family} program {program_id!r}")
    targets = normalise_target_plan(suite)
    plan = seed_plan_map(suite)
    seed = _int(suite_seed, "suite_seed", minimum=1)
    if seed not in plan:
        raise FR03SuiteError(f"suite_seed {seed} is not in the pre-registered "
                             f"seed_plan {sorted(plan)}")
    entry = plan[seed]
    target = targets[program_id]
    lane_width = target["vec_lane_width"]
    mask_text = entry["program_mask"][program_id]
    return {
        "suite_seed": seed,
        "submodel": entry["submodel"],
        "program_id": program_id,
        "target_phys_idx": target["target_phys_idx"],
        "vec_lane_width": lane_width,
        "vec_lane_offset": entry["vec_lane_offset"],
        "fault_mask": mask_text,
        "fault_mask_value": int(mask_text, 0),
        "polarity": entry["polarity"],
        "fault_type": entry["fault_type"],
        "require_allocated": True,
        "reg_class": "vector",
        "injection_mode": "phys",
        "semantic_role": "FR03",
        "bits_to_change": 1,
        "precision": target["precision"],
    }


def component_injector(plan: dict, component_seed: int) -> dict:
    phys = {
        "injection_mode": plan["injection_mode"],
        "reg_class": plan["reg_class"],
        "target_phys_idx": plan["target_phys_idx"],
        "require_allocated": plan["require_allocated"],
        "vec_lane_width": plan["vec_lane_width"],
        "vec_lane_offset": plan["vec_lane_offset"],
        "fault_type": plan["fault_type"],
        "fault_mask": plan["fault_mask"],
        "semantic_role": plan["semantic_role"],
        "bits_to_change": plan["bits_to_change"],
    }
    return {
        "component": "physreg",
        "fault_mask": plan["fault_mask"],
        "max_faults": 1,
        "first_clock": 0,
        "probability": 1.0,
        "rng_seed": int(component_seed),
        "physreg_mode": phys,
    }


def _component_spec(suite: dict, program: dict, suite_seed: int,
                    component_seed: int, run_id: str) -> dict:
    plan = resolve_component_plan(suite, program["program_id"], suite_seed)
    defaults = json.loads(json.dumps(suite.get("run_defaults") or {}))
    limits = defaults.pop("limits", {}) or {}
    family = family_of(suite)
    # CHAOSPhysReg emits model_id="FR03", freq="F5" and submodel=semanticRole
    # ("FR03") on every event; it emits no load_id.  The component manifest
    # must carry exactly the values the independent audit compares against
    # the real stream.  The W5/W6 load_id and the FR03-a/b/c seed label stay
    # in the suite identity and in explicit sibling fields, not in a manifest
    # field that would disagree with every event.
    suite_load_id = str(defaults.pop("load_id", "") or "")
    seed_label = plan["submodel"]
    injector = component_injector(plan, component_seed)
    workload = {
        "binary": str(program["binary"]),
        "source": str(program.get("source", "")),
        "identity": f"FR03-{family}-{program['program_id']}-v1",
        "golden": program.get("golden", ""),
        "oracle_kind": "exact_hash",
        "oracle_tol": 0,
        "element_oracle": json.loads(
            json.dumps(program.get("element_oracle") or {})),
    }
    component = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_family": family,
        "suite_seed": int(suite_seed),
        "program_id": program["program_id"],
        "program_index": program["program_index"],
        "program_count": program_count(family),
        "component_seed": int(component_seed),
        "component_seed_policy_version": str(
            suite.get("component_seed_policy_version")
            or DEFAULT_COMPONENT_SEED_POLICY),
    }
    spec = {
        "run_id": run_id,
        **defaults,
        "submodel": "FR03",
        "suite_load_id": suite_load_id,
        "suite_seed_submodel": seed_label,
        "workload": workload,
        "injector": injector,
        "limits": limits,
        "component": component,
        "target_plan_entry": plan,
        # Fixed guest argv for FR03: identical in gate and formal runs, so
        # the guest stack layout (and the path-dependent fault outcome) is
        # deterministic. The file is copied into attempt/inject/array.bin.
        "array_dump_path": f"/tmp/fsu-fr03-arrays/seed{int(component_seed)}.bin",
        "effective_injector": json.loads(json.dumps(injector)),
        "notes": ("FR03 permanent physical-cell gate component: one real "
                  "program, one fixed Vec phys cell, never a formal seed."),
    }
    return spec


# ---------------------------------------------------------------------------
# Oracle / FR03 evidence
# ---------------------------------------------------------------------------
def _golden_path(program: dict, root: Path) -> Path:
    path = Path(program["element_oracle"]["golden_array"])
    return path if path.is_absolute() else Path(root) / path


def element_oracle(attempt: Path, program: dict, family: str, root: Path,
                   write: bool = False) -> dict:
    eo = program.get("element_oracle") or {}
    golden = _golden_path(program, root)
    fault = Path(attempt) / "inject/array.bin"
    if not golden.exists():
        raise FR03SuiteError(f"{program['program_id']}: golden missing: "
                             f"{golden}")
    if not fault.exists():
        raise FR03SuiteError(f"{program['program_id']}: missing {fault} "
                             "(--array-dump was not produced)")
    if family == "W6":
        meta = WO.validate_meta(eo.get("meta") or {})
        result = WO.compare(str(golden), str(fault), meta, meta["abs_tol"],
                            meta["rel_tol"], meta["ulp_tol"])
    else:
        meta = O.validate_meta(eo.get("meta") or {})
        result = O.compare(golden.read_bytes(), fault.read_bytes(), meta,
                           meta["abs_tol"], meta["rel_tol"], meta["ulp_tol"])
    payload = O.json_ready(result)
    payload["golden_array"] = str(golden)
    payload["fault_array"] = str(fault)
    payload["ok"] = True
    if write:
        (Path(attempt) / "oracle_elements.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _write_oracle_error(attempt: Path, program: dict, root: Path,
                        error: str) -> dict:
    payload = {
        "ok": False,
        "program_id": program["program_id"],
        "error": error,
        "golden_array": str(_golden_path(program, root)),
        "fault_array": str(Path(attempt) / "inject/array.bin"),
        "oracle_version": (program.get("element_oracle") or {}).get(
            "oracle_version"),
    }
    (Path(attempt) / "oracle_elements.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


_FR03_ASSERT_MOD = None


def _fr03_assert_module():
    global _FR03_ASSERT_MOD
    if _FR03_ASSERT_MOD is None:
        path = ROOT / "tests/unit/fr03_gate_assert.py"
        spec = importlib.util.spec_from_file_location("fr03_gate_assert",
                                                      path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _FR03_ASSERT_MOD = mod
    return _FR03_ASSERT_MOD


def fr03_analyze(attempt: Path) -> dict:
    """Re-run the FR03 permanent-cell assertions on the real PROP stream."""
    prop = Path(attempt) / "inject/prop_evt.txt.gz"
    if not prop.exists():
        return {"ok": False, "violations": ["missing_prop_evt"],
                "truncated": True, "target": {}, "counts": {}, "l5": {}}
    ga = _fr03_assert_module()
    events, truncated = ga.read_stream(prop)
    return ga.analyze(events, truncated=truncated)


def _plan_checks(report: dict, plan: dict):
    checks = []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})
        return bool(ok)

    target = report.get("target") or {}

    def as_int(value):
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return int(text, 0)
        except ValueError:
            return None

    check("root reg_class == vec", str(target.get("reg_class")) == "vec")
    check("root phys_reg == planned target",
          as_int(target.get("phys_reg")) == plan["target_phys_idx"])
    check("root fixed_mask == planned fault_mask",
          as_int(target.get("fixed_mask")) == plan["fault_mask_value"])
    check("root stuck_polarity == planned polarity",
          as_int(target.get("stuck_polarity")) == plan["polarity"])
    check("root lane_width == planned vec_lane_width",
          as_int(target.get("lane_width")) == plan["vec_lane_width"])
    check("root lane_offset == planned vec_lane_offset",
          as_int(target.get("lane_offset")) == plan["vec_lane_offset"])
    counts = report.get("counts") or {}
    check("write exposures >= 1",
          (as_int(counts.get("write_exposures_total")) or 0) >= 1)
    check("read exposures >= 1",
          (as_int(counts.get("read_exposures_total")) or 0) >= 1)
    check("a real L5 commit or squash exists",
          (as_int(counts.get("observed_commits")) or 0)
          + (as_int(counts.get("observed_squashes")) or 0) >= 1)
    check("chain_end terminal is real L5",
          str((report.get("l5") or {}).get("terminal")) in L5_OK_TERMINALS)
    return checks


# ---------------------------------------------------------------------------
# Component execution / verification
# ---------------------------------------------------------------------------
def _attempt_number(attempt: Path) -> int:
    try:
        return int(Path(attempt).name.split("-")[1])
    except (IndexError, ValueError):
        return 0


def _component_manifest(suite, program, suite_hash, suite_seed,
                        component_seed, plan: dict, attempt: Path, status: str,
                        audit_ok: bool, certified: bool, fr03_ok: bool,
                        fr03_violations, report: dict | None):
    report = report or {}
    oracle = report.get("oracle") or {}
    out = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_family": family_of(suite),
        "suite_hash": suite_hash,
        "suite_seed": int(suite_seed),
        "program_id": program["program_id"],
        "program_index": program["program_index"],
        "program_count": program_count(family_of(suite)),
        "component_seed_policy_version": str(
            suite.get("component_seed_policy_version")
            or DEFAULT_COMPONENT_SEED_POLICY),
        "component_seed": int(component_seed),
        "component_attempt": _attempt_number(attempt),
        "component_manifest_sha256": (
            sha256_file(Path(attempt) / "manifest.json")
            if (Path(attempt) / "manifest.json").exists() else "0" * 64),
        "component_binary_sha256": program["binary_sha256"],
        "component_source_sha256": program["source_sha256"],
        "component_golden_sha256": program["golden_array_sha256"],
        "component_status": status,
        # A CHAOSPhysReg permanent-cell run has no CHAOSFPU eligible-event
        # census. This is an explicit n/a, never a silent zero.
        "component_eligible": None,
        "component_eligible_note": (
            "n/a: physreg permanent-cell run has no CHAOSFPU census"),
        "component_activated": SR_activated_count(attempt),
        "component_faults": int(report.get("actual_injections",
                                           oracle.get("faults_injected", 0))
                                or 0),
        "component_terminal": _primary_terminal(report),
        "component_oracle": "NOT_EVALUATED",
        "component_run_level_oracle": str(oracle.get("category") or "Unknown"),
        "component_audit_ok": bool(audit_ok),
        "component_certified": bool(certified),
        "component_fr03_ok": bool(fr03_ok),
        "component_fr03_violations": list(fr03_violations or []),
        "target_plan_entry": json.loads(json.dumps(plan)),
        "attempt": str(attempt),
    }
    return out


def SR_activated_count(attempt: Path) -> int:
    # Same counting rule as fsu_suite_runner._activated_count.
    import fsu_prop_fields as P
    prop = Path(attempt) / "inject/prop_evt.txt.gz"
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


def _write_component_manifest(attempt: Path, manifest: dict):
    (Path(attempt) / "component_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    R.write_hashes(attempt)


def _component_results(attempt: Path, suite, program, plan, suite_hash,
                       suite_seed, component_seed, gate_id):
    """Oracle + independent audit + FR03 assertions for one admitted attempt."""
    oracle_result = None
    oracle_error = None
    try:
        oracle_result = element_oracle(attempt, program, family_of(suite),
                                       ROOT, write=True)
    except (FR03SuiteError, O.OracleError, WO.W6OracleError, OSError,
            ValueError) as e:
        oracle_error = f"{type(e).__name__}: {e}"
        _write_oracle_error(attempt, program, ROOT, oracle_error)
    oracle_ok = oracle_result is not None and oracle_result.get("ok") is True

    A.write_audit(attempt)
    audit = json.loads((attempt / "audit.json").read_text(encoding="utf-8"))
    audit_ok = audit.get("ok") is True
    certified = audit.get("certified") is True

    fr03 = fr03_analyze(attempt)
    plan_checks = _plan_checks(fr03, plan)
    fr03_ok = bool(fr03.get("ok")) and all(c["ok"] for c in plan_checks)
    fr03_violations = list(fr03.get("violations") or []) + [
        c["check"] for c in plan_checks if not c["ok"]]

    report_path = attempt / "chain_report.json"
    report = (json.loads(report_path.read_text(encoding="utf-8"))
              if report_path.exists() else {})
    status = ("admitted"
              if (audit_ok and certified and oracle_ok and fr03_ok)
              else "failed")
    cm = _component_manifest(suite, program, suite_hash, suite_seed,
                             component_seed, plan, attempt, status, audit_ok,
                             certified, fr03_ok, fr03_violations, report)
    if oracle_ok:
        mismatches = int(oracle_result.get("mismatch_count", 0))
        cm["component_oracle"] = "SDC" if mismatches > 0 else "MASKED"
        cm["component_oracle_category"] = oracle_result.get("category")
        cm["component_oracle_mismatch_count"] = mismatches
        cm["component_fr03_target"] = fr03.get("target")
        cm["component_fr03_counts"] = fr03.get("counts")
        cm["component_fr03_l5"] = fr03.get("l5")
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
        cm["component_reason"] = "component audit failed after FR03 evidence"
    _write_component_manifest(attempt, cm)
    return {**cm, "ok": status == "admitted"}


def _run_one_component(suite, program, info, suite_seed, component_seed,
                       plan, seed_dir: Path, gate_id: str, out_root: Path,
                       gem5: Path, config: Path, root: Path, runner,
                       timeout_s, allow_rerun) -> dict:
    pid = program["program_id"]
    component_root = Path(seed_dir) / "components" / pid
    component_root.mkdir(parents=True, exist_ok=True)
    comp_seed_dir = component_root / gate_id / f"seed{component_seed}"
    spec = _component_spec(suite, program, suite_seed, component_seed,
                           gate_id)
    spec_path = component_root / f"manifest-seed{component_seed}.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    rerun = allow_rerun or (comp_seed_dir / "AUTHORITATIVE").exists()
    # Reuse an already-admitted component without re-running gem5 unless the
    # caller explicitly asked for a rerun. Existing evidence is re-checked;
    # if it no longer certifies, a fresh attempt is created (never overwrite).
    auth = comp_seed_dir / "AUTHORITATIVE"
    if auth.exists() and not allow_rerun:
        prior = Path(auth.read_text(encoding="utf-8").strip())
        if prior.is_dir():
            out = _component_results(prior, suite, program, plan,
                                     info["suite_hash"], suite_seed,
                                     component_seed, gate_id)
            if out["component_status"] == "admitted":
                out["reused"] = True
                return out
        rerun = True
    res = R.run_seed(spec_path, component_seed, out_root=out_root, gem5=gem5,
                     root=root, runner=runner, timeout_s=timeout_s,
                     allow_rerun=rerun, seed_dir=comp_seed_dir,
                     component=spec["component"], write_authoritative=False,
                     copy_to_complete=False, config=config)
    if res.get("status") == "already_admitted":
        attempt = Path(res.get("authoritative", ""))
    else:
        attempt = Path(res.get("attempt", ""))
    if not attempt.is_dir():
        return {
            "program_id": pid, "program_index": program["program_index"],
            "attempt": str(attempt), "component_status": "failed",
            "component_oracle": "NOT_EVALUATED", "component_audit_ok": False,
            "component_certified": False, "component_fr03_ok": False,
            "ok": False, "run_status": res.get("status"),
            "reason": res.get("reason", "no attempt created"),
            "target_plan_entry": plan,
        }
    if res.get("status") != "admitted":
        report_path = attempt / "chain_report.json"
        report = (json.loads(report_path.read_text(encoding="utf-8"))
                  if report_path.exists() else {})
        status = ("not_activated" if res.get("status") == "not_activated"
                  else "failed")
        cm = _component_manifest(
            suite, program, info["suite_hash"], suite_seed, component_seed,
            plan, attempt, status, False, False, False, [], report)
        cm["run_status"] = res.get("status")
        cm["reason"] = res.get("reason")
        cm["ok"] = False
        _write_component_manifest(attempt, cm)
        return cm
    out = _component_results(attempt, suite, program, plan, info["suite_hash"],
                             suite_seed, component_seed, gate_id)
    if out["component_status"] == "admitted":
        comp_seed_dir.mkdir(parents=True, exist_ok=True)
        (comp_seed_dir / "AUTHORITATIVE").write_text(str(attempt),
                                                     encoding="utf-8")
    return out


def _latest_attempt(seed_dir: Path, pid: str, gate_id: str):
    root = Path(seed_dir) / "components" / pid / gate_id
    attempts = sorted(root.glob("seed*/attempt-*")) if root.exists() else []
    return attempts[-1] if attempts else None


def verify_component_attempt(attempt: Path, suite, program, plan, gate_id):
    attempt = Path(attempt)
    pid = program["program_id"]
    checks, failures = [], []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})
        if not ok:
            failures.append(name)
        return bool(ok)

    man_path = attempt / "manifest.json"
    cm_path = attempt / "component_manifest.json"
    audit_path = attempt / "audit.json"
    check("attempt directory exists", attempt.is_dir())
    check("attempt manifest.json exists", man_path.exists())
    if man_path.exists():
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
        check("manifest run_id is the gate id",
              str(manifest.get("run_id")) == str(gate_id))
        check("manifest injector == frozen FR03 plan",
              manifest.get("injector") == component_injector(
                  plan, int((manifest.get("component") or {}).get(
                      "component_seed", 0))))
        check("manifest target_plan_entry == frozen plan",
              manifest.get("target_plan_entry") == plan)
        check("manifest binary is the registered program binary",
              Path(str((manifest.get("workload") or {}).get("binary", "")))
              .name == Path(program["binary"]).name)
    cm = {}
    if cm_path.exists():
        try:
            cm = json.loads(cm_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cm = {}
    check("component manifest exists/parses", bool(cm))
    check("component status admitted", cm.get("component_status") == "admitted")
    check("component oracle is SDC or MASKED",
          cm.get("component_oracle") in DECIDABLE_ORACLE)
    check("component target plan identity",
          cm.get("target_plan_entry") == plan)
    check("component manifest identity",
          cm.get("suite_hash") == compute_suite_hash(suite)
          and cm.get("program_id") == pid
          and int(cm.get("program_index", -1)) == program["program_index"])
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

    oracle_ok = False
    oracle_error = None
    try:
        oracle = element_oracle(attempt, program, family_of(suite), ROOT,
                                write=False)
        oracle_ok = oracle.get("ok") is True
        if cm:
            check("recorded oracle outcome matches real arrays",
                  (int(oracle.get("mismatch_count", 0)) > 0)
                  == (cm.get("component_oracle") == "SDC"))
    except (FR03SuiteError, O.OracleError, WO.W6OracleError, OSError,
            ValueError) as e:
        oracle_error = f"{type(e).__name__}: {e}"
        check("element oracle re-computation", False)
    fr03 = fr03_analyze(attempt)
    plan_checks = _plan_checks(fr03, plan)
    for c in plan_checks:
        check(c["check"], c["ok"])
    check("FR03 permanent-cell assertions", fr03.get("ok") is True)
    if not fr03.get("ok"):
        failures.extend(fr03.get("violations") or [])
    return {
        "program_id": pid,
        "program_index": program["program_index"],
        "attempt": str(attempt),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "checks": checks,
        "component_oracle": cm.get("component_oracle"),
        "component_activated": cm.get("component_activated"),
        "component_terminal": cm.get("component_terminal"),
        "target_plan_entry": plan,
        "fr03": {"ok": fr03.get("ok"),
                 "violations": fr03.get("violations"),
                 "target": fr03.get("target"),
                 "counts": fr03.get("counts"),
                 "l5": fr03.get("l5")},
        "ok": not failures and oracle_ok,
    }


def _verify_seed_components(suite, info, seed_dir, gate_id, suite_seed):
    by_id = {p["program_id"]: p for p in suite["programs"]}
    records = []
    for pid in program_order(family_of(suite)):
        plan = resolve_component_plan(suite, pid, suite_seed)
        attempt = _latest_attempt(seed_dir, pid, gate_id)
        if attempt is None:
            records.append({
                "program_id": pid,
                "program_index": by_id[pid]["program_index"],
                "attempt": None, "status": "FAIL",
                "failures": ["no gate attempt found"], "checks": [],
                "target_plan_entry": plan, "ok": False,
            })
            continue
        records.append(verify_component_attempt(attempt, suite, by_id[pid],
                                                plan, gate_id))
    return records


def _run_seed_components(suite, info, seed_dir, gate_id, suite_seed, gem5,
                         config, root, timeout, allow_rerun, runner):
    seeds = derive_component_seeds(suite, suite_seed)
    by_id = {p["program_id"]: p for p in suite["programs"]}
    records = []
    for pid in program_order(family_of(suite)):
        plan = resolve_component_plan(suite, pid, suite_seed)
        records.append(_run_one_component(
            suite, by_id[pid], info, suite_seed, seeds[pid], plan, seed_dir,
            gate_id, seed_dir, Path(gem5), Path(config), Path(root), runner,
            timeout, allow_rerun))
    return records


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
def default_gate_id(suite) -> str:
    family = family_of(suite)
    return f"FSU-FR03-F5-{family}-GATE"


def default_outdir(root: Path, suite) -> Path:
    family = family_of(suite)
    return Path(root) / f"runs/fsu-gates/FR03-F5-{family}-GATE"


def _assert_gate_outdir(outdir: Path, root: Path):
    gate_root = (Path(root) / "runs/fsu-gates").resolve()
    formal = (Path(root) / "runs/fsu").resolve()
    out = Path(outdir).resolve()
    if out == formal or formal in out.parents:
        raise FR03SuiteError(
            f"FR03 gate artifacts must never be written under {formal} "
            f"(got {out}); runs/fsu is reserved for formal seeds")
    if out != gate_root and gate_root not in out.parents:
        raise FR03SuiteError(
            f"FR03 gate artifacts must live under {gate_root} (got {out})")


def _sha_or_none(path):
    try:
        return sha256_file(Path(path))
    except OSError:
        return None


def _write_formal(seed_dir: Path, run_id: str, suite, info, suite_seed,
                  records, ok: bool):
    """Write formal FR03 suite-seed evidence (never for gate artifacts)."""
    seed_dir = Path(seed_dir)
    seed_dir.mkdir(parents=True, exist_ok=True)
    order = list(program_order(family_of(suite)))
    comps = []
    violations = []
    for r in records:
        att = Path(str(r.get("attempt", "")))
        hashes = {}
        for name in ("manifest.json", "audit.json", "chain_report.json",
                     "oracle.json", "evidence_sha256.json",
                     "component_manifest.json"):
            p = att / name
            hashes[name] = _sha_or_none(p) if p.exists() else None
            if hashes[name] is None:
                violations.append(f"{r.get('program_id')}: missing {name}")
        c = dict(r)
        c["evidence_hashes"] = hashes
        comps.append(c)
        if not r.get("ok"):
            violations.extend(f"{r.get('program_id')}: {x}"
                              for x in r.get("failures", []))
    actual = [c.get("program_id") for c in comps]
    execution_complete = (actual == order and len(comps) == len(order)
                          and all(c.get("attempt") for c in comps))
    evidence_valid = (execution_complete
                      and all(c.get("component_audit_ok") is True
                              and c.get("component_certified") is True
                              and all(v is not None
                                      for v in c["evidence_hashes"].values())
                              for c in comps))
    certified = bool(ok and execution_complete and evidence_valid
                     and not violations)
    suite_manifest = {
        "run_id": run_id,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_family": family_of(suite),
        "suite_hash": info["suite_hash"],
        "suite_seed": int(suite_seed),
        "program_order": order,
        "program_count": len(order),
        "components": comps,
    }
    (seed_dir / "suite_manifest.json").write_text(
        json.dumps(suite_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    report = {
        "run_id": run_id,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_family": family_of(suite),
        "suite_hash": info["suite_hash"],
        "suite_seed": int(suite_seed),
        "program_order": order,
        "program_count": len(order),
        "suite_status": "admitted" if certified else "failed",
        "suite_admitted": certified,
        "formal_suite_seed_count": 1 if certified else 0,
        "component_run_count": len(comps),
        "component_fault_total": sum(int(c.get("component_faults", 0))
                                     for c in comps),
        "components": comps,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "counting_note": ("component runs/faults are never seeds; one FR03 "
                          "suite seed counts as exactly one admitted seed"),
    }
    (seed_dir / "suite_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    audit_v2 = {
        "schema_version": "fsu-suite-audit/v1",
        "tool_version": "fsu_fr03_suite_gate/v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_family": family_of(suite),
        "suite_hash": info["suite_hash"],
        "run_id": run_id,
        "suite_seed": int(suite_seed),
        "expected_programs": order,
        "actual_programs": actual,
        "component_count": len(comps),
        "components": [
            {"program_id": c.get("program_id"),
             "program_index": c.get("program_index"),
             "attempt": c.get("attempt"),
             "evidence_hashes": c["evidence_hashes"],
             "audit_ok": c.get("component_audit_ok") is True,
             "certified": c.get("component_certified") is True,
             "oracle_category": c.get("component_oracle")}
            for c in comps],
        "suite_execution_complete": execution_complete,
        "suite_evidence_valid": evidence_valid,
        "suite_certified": certified,
        "violations": violations,
        "formal_seed_contribution": 1,
    }
    (seed_dir / "audit_v2.json").write_text(
        json.dumps(audit_v2, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    md = [
        f"# {run_id} seed{suite_seed} — FR03 formal suite seed", "",
        "> 一个 suite seed 固定包含"
        f" {len(order)} 个 component run"
        "（FR03 永久物理 cell）；component 不进入 seed 计数。", "",
        f"- suite_hash: `{info['suite_hash']}`",
        f"- program_order: {' → '.join(order)}",
        f"- result: **{'PASS' if certified else 'FAIL'}**", "",
        "| # | program | phys | lane(w/off) | mask | polarity | oracle | "
        "audit.ok | certified | attempt |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, c in enumerate(comps, 1):
        plan = c.get("target_plan_entry") or {}
        md.append(
            f"| {i} | {c.get('program_id')} | {plan.get('target_phys_idx')} | "
            f"{plan.get('vec_lane_width')}/{plan.get('vec_lane_offset')} | "
            f"`{plan.get('fault_mask')}` | {plan.get('polarity')} | "
            f"{c.get('component_oracle')} | {c.get('component_audit_ok')} | "
            f"{c.get('component_certified')} | `{c.get('attempt')}` |")
    md += ["", "## 计数规则", "",
           "- 本 suite seed = **1** 个正式 seed。",
           f"- {len(order)} 个 component run / fault 不进入 seed 总数。", ""]
    text = "\n".join(md)
    (seed_dir / f"{run_id}-seed{suite_seed}.md").write_text(text,
                                                             encoding="utf-8")
    if certified:
        dst = (seed_dir.parent.parent / "COMPLETE_PROPAGATION_PATHS" /
               run_id / f"{run_id}-seed{suite_seed}.md")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        (seed_dir / "AUTHORITATIVE").write_text(str(seed_dir) + "\n",
                                                encoding="utf-8")


def _write_report(report_dir: Path, gate_id: str, suite, info,
                  suite_seed, records, formal_run_id=None):
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    expected = program_count(family_of(suite))
    ok = len(records) == expected and all(r.get("ok") for r in records)
    formal = formal_run_id is not None
    if formal:
        _write_formal(report_dir, formal_run_id, suite, info, suite_seed,
                      records, ok)
    report = {
        "gate": "FR03",
        "gate_id": gate_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "non_formal": not formal,
        "counts_toward_519": False,
        "formal_suite_seed_count": 1 if (formal and ok) else 0,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_family": family_of(suite),
        "suite_hash": info["suite_hash"],
        "freq": "F5",
        "suite_seed": int(suite_seed),
        "program_order": list(program_order(family_of(suite))),
        "program_count": expected,
        "component_run_count": len(records),
        "component_pass_count": sum(1 for r in records if r.get("ok")),
        "records": records,
        "ok": ok,
        "counting_note": ("component runs/faults are never seeds; an FR03 "
                          "gate is non-formal and contributes +0 seed"),
        "outdir": str(report_dir),
    }
    (report_dir / "gate_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    lines = [
        f"# {gate_id} — FR03 gate（非正式，不计 seed）", "",
        f"- suite：`{suite['suite_id']}` v{suite['suite_version']} "
        f"（{family_of(suite)}，F5）",
        f"- suite_hash：`{info['suite_hash']}`",
        f"- suite seed：{suite_seed}",
        f"- component runs：{len(records)}；PASS："
        f"{report['component_pass_count']}/{expected}",
        "- 正式 seed 计数：**+0**（gate 不计 519/240）",
        f"- 结论：**{'PASS' if ok else 'FAIL'}**", "",
        "| # | program | target phys | lane(w/off) | mask | polarity | "
        "oracle | terminal | 结论 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(records, 1):
        plan = r.get("target_plan_entry") or {}
        lines.append(
            f"| {i} | {r['program_id']} | {plan.get('target_phys_idx')} | "
            f"{plan.get('vec_lane_width')}/{plan.get('vec_lane_offset')} | "
            f"`{plan.get('fault_mask')}` | {plan.get('polarity')} | "
            f"{r.get('component_oracle', '—')} | "
            f"{r.get('component_terminal', '—')} | "
            f"{'PASS' if r.get('ok') else 'FAIL'} |")
    lines += ["", "## 计数与语义", "",
              "- 一个 component run 不是 seed；本 gate 正式计数 **+0**。",
              "- 永久 key = reg_class + phys_index + lane/mask + polarity；"
              "generation 仅是暴露/传播身份，free/realloc/squash 不清除。",
              "- gate 只写 `runs/fsu-gates/`，拒绝 `runs/fsu/`。", ""]
    for r in records:
        lines += [f"### {r['program_id']}", "", "| 检查 | 结果 |",
                  "|---|---|"]
        for c in r.get("checks", []):
            lines.append(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} |")
        if r.get("failures"):
            lines += ["", "失败项：" + "; ".join(str(x) for x in r["failures"])]
        lines.append("")
    (report_dir / "GATE.md").write_text("\n".join(lines) + "\n",
                                        encoding="utf-8")
    sums = []
    for f in sorted(report_dir.rglob("*")):
        if f.is_file() and f.name != "SHA256SUMS":
            sums.append(f"{sha256_file(f)}  {f.relative_to(report_dir)}")
    (report_dir / "SHA256SUMS").write_text("\n".join(sums) + "\n",
                                           encoding="utf-8")
    return report


def print_commands(suite, info, suite_seed, root, gem5, config, gate_id):
    seeds = derive_component_seeds(suite, suite_seed)
    by_id = {p["program_id"]: p for p in suite["programs"]}
    out = {
        "gate_id": gate_id,
        "suite_id": suite["suite_id"],
        "suite_family": family_of(suite),
        "freq": "F5",
        "suite_hash": info["suite_hash"],
        "suite_seed": int(suite_seed),
        "commands": [],
    }
    for pid in program_order(family_of(suite)):
        plan = resolve_component_plan(suite, pid, suite_seed)
        spec = _component_spec(suite, by_id[pid], suite_seed, seeds[pid],
                               gate_id)
        outdir = (Path(root) / "runs/fsu-gates" / gate_id / "commands" /
                  f"seed{suite_seed}" / pid / "inject")
        inject = R.build_cmd(spec, outdir, seeds[pid], 0, False, Path(gem5),
                             Path(config), Path(root))
        out["commands"].append({
            "program_id": pid,
            "program_index": by_id[pid]["program_index"],
            "component_seed": seeds[pid],
            "submodel": plan["submodel"],
            "target_phys_idx": plan["target_phys_idx"],
            "vec_lane_width": plan["vec_lane_width"],
            "vec_lane_offset": plan["vec_lane_offset"],
            "fault_mask": plan["fault_mask"],
            "polarity": plan["polarity"],
            "fault_type": plan["fault_type"],
            "precision": plan["precision"],
            "require_allocated": plan["require_allocated"],
            "inject": inject,
        })
    return out


def run_gate(suite_path, outdir=None, gem5=DEFAULT_GEM5,
             config=DEFAULT_CONFIG, root=ROOT, timeout=3600, suite_seed=1,
             gate_id=None, allow_rerun=False, verify_only=False, runner=None,
             print_only=False, all_seeds=False, print_hash=False,
             formal_run_id=None):
    root = Path(root)
    probe = json.loads(Path(suite_path).read_text(encoding="utf-8"))
    asset_root = root
    first_binary = probe["programs"][0]["binary"]
    if not (asset_root / first_binary).exists():
        asset_root = ROOT
    if print_hash:
        info = validate_suite_manifest(probe, require_hashes=False,
                                       require_suite_hash=False)
        print(json.dumps({
            "suite_id": probe.get("suite_id"),
            "suite_family": family_of(probe),
            "suite_hash": info["suite_hash"],
            "identity": info["identity"],
        }, ensure_ascii=False, indent=2))
        return 0
    loaded = load_suite(Path(suite_path), root=asset_root,
                        require_hashes=True)
    suite = loaded["suite"]
    info = {"suite_hash": loaded["suite_hash"],
            "identity": loaded["identity"]}
    if formal_run_id is not None:
        gate_id = str(formal_run_id)
        outdir = Path(root) / "runs/fsu" / gate_id
    elif gate_id is None:
        gate_id = default_gate_id(suite)
    suite_seed = int(suite_seed)
    if suite_seed not in seed_plan_map(suite):
        raise FR03SuiteError(f"suite_seed {suite_seed} is not pre-registered "
                             f"in seed_plan {sorted(seed_plan_map(suite))}")
    if print_only:
        seeds = ([1, 2, 3] if all_seeds else [suite_seed])
        out = {"gate_id": gate_id, "suite_id": suite["suite_id"],
               "suite_family": family_of(suite),
               "suite_hash": info["suite_hash"], "seeds": []}
        for seed in seeds:
            out["seeds"].append(print_commands(
                suite, info, seed, root, gem5, config, gate_id))
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if outdir is None:
        outdir = default_outdir(root, suite)
    outdir = Path(outdir)
    if formal_run_id is None:
        _assert_gate_outdir(outdir, root)
    seed_dir = outdir / f"seed{suite_seed}"
    if verify_only:
        records = _verify_seed_components(suite, info, seed_dir, gate_id,
                                          suite_seed)
    else:
        records = _run_seed_components(
            suite, info, seed_dir, gate_id, suite_seed, gem5, config, root,
            timeout, allow_rerun, runner)
    return _write_report(seed_dir, gate_id, suite, info, suite_seed, records,
                         formal_run_id=formal_run_id)


def main(argv=None):
    ap = argparse.ArgumentParser(description="FR03-F5-W5/W6 suite gate")
    ap.add_argument("--suite", required=True)
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
    ap.add_argument("--print-suite-hash", action="store_true")
    ap.add_argument("--all-seeds", action="store_true")
    ap.add_argument("--formal-run-id", default=None,
                    help="write formal FR03 suite seed evidence under runs/fsu")
    a = ap.parse_args(argv)
    try:
        res = run_gate(
            Path(a.suite),
            Path(a.outdir) if a.outdir else None,
            Path(a.gem5), Path(a.config), Path(a.root), a.timeout,
            a.suite_seed, a.gate_id, a.allow_rerun, a.verify_only,
            print_only=a.print_commands, all_seeds=a.all_seeds,
            print_hash=a.print_suite_hash, formal_run_id=a.formal_run_id)
    except FR03SuiteError as e:
        print(json.dumps({"ok": False, "reason": str(e)},
                         ensure_ascii=False, indent=2))
        return 2
    if a.print_commands or a.print_suite_hash:
        return res if isinstance(res, int) else 0
    print(json.dumps({"ok": res["ok"], "gate_id": res["gate_id"],
                      "component_pass_count": res["component_pass_count"],
                      "component_run_count": res["component_run_count"],
                      "formal_suite_seed_count":
                          res["formal_suite_seed_count"],
                      "outdir": res.get("outdir", "")},
                     ensure_ascii=False, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
