#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_suite.py — W5 PolyBench-FP 固定 suite 身份、component seed 与门禁。

权威裁决（docs/gem5-fi/fsu/FP04-F0-W5-SUITE-RULING.md）：

  formal suite seed  : FSU-FP04-F0-W5 的正式计数单位，3 个。
  component run      : 一个 suite seed 下跑一个程序的独立运行，5 个。
  component fault    : 一个 component run 内注入的一次故障，1 个。

固定顺序永远为 gemm → 2mm → lu → cholesky → jacobi-2d；3 个 suite seed
= 15 个 component run，但正式计数只 +3，绝不把 component 数当 seed 数。

本模块只做身份/计数/门禁，不运行 gem5。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PROGRAM_ORDER = ("gemm", "2mm", "lu", "cholesky", "jacobi-2d")
PROGRAM_COUNT = len(PROGRAM_ORDER)
DEFAULT_SUITE_ID = "polybench-fp-v1"
DEFAULT_SUITE_VERSION = "1"
DEFAULT_COMPONENT_SEED_POLICY = "w5-component-seed-v1"

COMPONENT_STATUSES = ("admitted", "failed", "not_activated", "invalid")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

# [FSU][F5] Pre-registered per-suite-seed plan. A suite that declares a
# seed_plan freezes exactly three formal suite seeds BEFORE execution:
# each entry fixes the submodel, precision, permanent-fault mask/polarity,
# lane geometry, op/reg filtering, warm-up and bounded sampling window.
# The plan participates in suite_hash, so it cannot be changed after seeing
# results without a loud suite_hash drift error.
SEED_PLAN_COUNT = 3
SEED_PLAN_REQUIRED = (
    "suite_seed", "submodel", "mask", "polarity", "warmup", "sample",
)
SEED_PLAN_OPTIONAL = (
    "precision", "bitseg", "lane_width", "lane_offset", "op_classes",
    "reg_class", "decode_guard", "permanent_stuck", "program_mask",
)
SEED_PLAN_ALLOWED = frozenset(SEED_PLAN_REQUIRED + SEED_PLAN_OPTIONAL)
PRECISIONS = ("fp32", "fp64")
BITSEGS = ("sign", "exp_hi", "exp_lo", "mant_hi", "mant_mid", "mant_lo")
LANE_WIDTHS = (8, 16, 32, 64)
# Keep identical to tools/fsu_seed_runner.py / CHAOSFPU.cc kOpClassNames.
FPU_OP_CLASSES = (
    "FloatAdd", "FloatCmp", "FloatCvt", "FloatMult", "FloatMultAcc",
    "FloatDiv", "FloatMisc", "FloatSqrt",
    "SimdFloatAdd", "SimdFloatAlu", "SimdFloatCmp", "SimdFloatCvt",
    "SimdFloatMult", "SimdFloatMultAcc", "SimdFloatDiv", "SimdFloatSqrt",
    "SimdFloatMisc",
)
FPU_REG_CLASSES = ("any", "vec", "float", "vec_elem")

# [FSU][W6] Per-program injector overrides. W6 mixes SVD (fp64) with FFT /
# sparse-CG (fp32), so one suite-wide precision/lane cannot decode both.
# Application order:
#   suite.injector -> program_overrides[pid] -> seed_plan (F5)
# with two deliberate precedence rules:
#   * a mask in program_overrides is a per-program FINAL mask and wins over
#     the seed_plan's global mask;
#   * seed_plan.program_mask[pid] (if present) is the highest-precedence
#     mask, so each suite seed can pin different masks per precision.
# seed_plan fields that are omitted (e.g. precision for W6) inherit the
# resolved per-program injector instead of being overwritten.
PROGRAM_OVERRIDE_TOP = ("fpu_mode", "fault_mask", "max_faults", "first_clock")
PROGRAM_OVERRIDE_FPU = (
    "bitseg", "precision", "lane_width", "lane_offset", "decode_guard",
    "permanent_stuck", "stuck_polarity", "f5_warmup", "f5_sample_limit",
    "f5_keep_first_last_n", "op_classes", "reg_class",
    # [FSU][FP05] Real result burst (F0): one episode over 2-4 consecutive
    # eligible results. Validated here before it can reach the runner.
    "burst_mode", "burst_length", "burst_lane_step", "burst_lane_mask",
    "burst_id_base",
)
BURST_MODES = ("same_lane", "adjacent_lane", "cross_lane_mbu", "lane_mask")


class SuiteError(ValueError):
    """Suite/component 身份不成立；调用方必须响亮拒绝，不得降级运行。"""


def canonical_bytes(obj) -> bytes:
    """Canonical JSON：排序键、无多余空白、UTF-8。"""
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


def _normalise_cflags(value) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(x) for x in value)
    return str(value or "")


def _check_hash(value, where: str, allow_pending: bool = True):
    text = str(value or "")
    if allow_pending and text == "pending":
        return text
    if not _HEX64.match(text):
        raise SuiteError(f"{where}: expected 64-hex SHA-256"
                         + (" or 'pending'" if allow_pending else "")
                         + f", got {value!r}")
    return text


def _program_map(suite: dict):
    programs = suite.get("programs")
    if not isinstance(programs, list):
        raise SuiteError("suite.programs must be a list")
    by_id = {}
    for p in programs:
        if not isinstance(p, dict):
            raise SuiteError("suite.programs entries must be objects")
        pid = str(p.get("program_id", "")).strip()
        if not pid:
            raise SuiteError("suite.programs entry missing program_id")
        if pid in by_id:
            raise SuiteError(f"duplicate program component: {pid}")
        by_id[pid] = p
    return by_id


def _validate_order_and_count(suite: dict):
    order = suite.get("program_order")
    if not isinstance(order, list):
        raise SuiteError("suite.program_order must be a list")
    if tuple(order) != PROGRAM_ORDER:
        raise SuiteError(
            "program_order is fixed and must not be reordered by results: "
            f"want {list(PROGRAM_ORDER)}, got {order}")
    count = suite.get("program_count")
    try:
        count = int(count)
    except (TypeError, ValueError):
        raise SuiteError(f"suite.program_count must be {PROGRAM_COUNT}")
    if count != PROGRAM_COUNT:
        raise SuiteError(f"suite.program_count must be {PROGRAM_COUNT}, "
                         f"got {count}")


def _int(value, where: str, minimum=None) -> int:
    if isinstance(value, bool):
        raise SuiteError(f"{where} must be an integer, got {value!r}")
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise SuiteError(f"{where} must be an integer, got {value!r}")
    if minimum is not None and value < minimum:
        raise SuiteError(f"{where} must be >= {minimum}, got {value}")
    return value


def _mask_value(value, lane_width: int, where: str) -> int:
    """Parse an int or 0x-hex mask and require it to fit the lane width."""
    if isinstance(value, bool):
        raise SuiteError(f"{where} must be a mask, got {value!r}")
    if isinstance(value, int):
        parsed = value
    else:
        text = str(value or "").strip()
        try:
            parsed = int(text, 0)
        except ValueError:
            raise SuiteError(f"{where} must be an integer or 0x-hex mask, "
                             f"got {value!r}")
    if parsed < 0:
        raise SuiteError(f"{where} must be >= 0, got {value!r}")
    if parsed == 0:
        raise SuiteError(f"{where} must be non-zero (a zero mask is a no-op)")
    if parsed >= (1 << lane_width):
        raise SuiteError(f"{where}=0x{parsed:x} does not fit lane_width="
                         f"{lane_width}")
    return parsed


def _mask_text(value: int, lane_width: int) -> str:
    width = 8 if lane_width <= 32 else 16
    return f"0x{value:0{width}x}"


def _normalise_sample(entry: dict, where: str) -> dict:
    sample = entry.get("sample")
    if not isinstance(sample, dict):
        raise SuiteError(f"{where}.sample must be an object with "
                         "limit/keep_first_last_n")
    missing = [k for k in ("limit", "keep_first_last_n") if k not in sample]
    if missing:
        raise SuiteError(f"{where}.sample missing {missing}")
    limit = _int(sample["limit"], f"{where}.sample.limit", minimum=0)
    keep = _int(sample["keep_first_last_n"],
                f"{where}.sample.keep_first_last_n", minimum=0)
    if limit == 0 and keep != 0:
        raise SuiteError(f"{where}.sample: keep_first_last_n must be 0 when "
                         "limit is 0")
    if limit > 0 and keep > limit:
        raise SuiteError(f"{where}.sample: keep_first_last_n {keep} > limit "
                         f"{limit}")
    return {"limit": limit, "keep_first_last_n": keep}


def _normalise_fpu_patch(patch, where: str) -> dict:
    """Validate one nested fpu_mode override; reject unknown/ill-typed keys."""
    if not isinstance(patch, dict):
        raise SuiteError(f"{where} must be an object")
    unknown = sorted(set(patch) - set(PROGRAM_OVERRIDE_FPU))
    if unknown:
        raise SuiteError(f"{where} has unknown field(s): {unknown}")
    out = {}
    if "precision" in patch:
        precision = str(patch["precision"]).strip()
        if precision not in PRECISIONS:
            raise SuiteError(f"{where}.precision must be one of "
                             f"{list(PRECISIONS)}, got {precision!r}")
        out["precision"] = precision
    if "lane_width" in patch:
        lane_width = _int(patch["lane_width"], f"{where}.lane_width",
                          minimum=8)
        if lane_width not in LANE_WIDTHS:
            raise SuiteError(f"{where}.lane_width must be one of "
                             f"{list(LANE_WIDTHS)}, got {lane_width}")
        out["lane_width"] = lane_width
    if "precision" in out and "lane_width" in out:
        if out["precision"] == "fp64" and out["lane_width"] != 64:
            raise SuiteError(f"{where}: fp64 requires lane_width 64")
        if out["precision"] == "fp32" and out["lane_width"] < 32:
            raise SuiteError(f"{where}: fp32 requires lane_width >= 32")
    if "lane_offset" in patch:
        lane_offset = _int(patch["lane_offset"], f"{where}.lane_offset",
                           minimum=0)
        width = out.get("lane_width", 8)
        if lane_offset >= 128 // width:
            raise SuiteError(f"{where}.lane_offset {lane_offset} >= "
                             f"{128 // width} for lane_width {width}")
        out["lane_offset"] = lane_offset
    if "bitseg" in patch:
        bitseg = str(patch["bitseg"]).strip()
        if bitseg not in BITSEGS:
            raise SuiteError(f"{where}.bitseg must be one of "
                             f"{list(BITSEGS)}, got {bitseg!r}")
        out["bitseg"] = bitseg
    for key in ("decode_guard", "permanent_stuck"):
        if key in patch:
            if not isinstance(patch[key], bool):
                raise SuiteError(f"{where}.{key} must be a boolean")
            out[key] = patch[key]
    if "stuck_polarity" in patch:
        polarity = _int(patch["stuck_polarity"],
                        f"{where}.stuck_polarity", minimum=0)
        if polarity not in (0, 1):
            raise SuiteError(f"{where}.stuck_polarity must be 0 or 1")
        out["stuck_polarity"] = polarity
    for key in ("f5_warmup", "f5_sample_limit", "f5_keep_first_last_n"):
        if key in patch:
            out[key] = _int(patch[key], f"{where}.{key}", minimum=0)
    if "op_classes" in patch:
        raw = patch["op_classes"]
        if not isinstance(raw, (list, tuple)):
            raise SuiteError(f"{where}.op_classes must be an array")
        ops = [str(x) for x in raw]
        bad = [x for x in ops if x not in FPU_OP_CLASSES]
        if bad:
            raise SuiteError(f"{where}.op_classes has unknown name(s): {bad}")
        if len(set(ops)) != len(ops):
            raise SuiteError(f"{where}.op_classes contains duplicates")
        out["op_classes"] = ops
    if "burst_mode" in patch:
        mode = str(patch["burst_mode"] or "").strip()
        if mode and mode not in BURST_MODES:
            raise SuiteError(f"{where}.burst_mode must be one of "
                             f"{list(BURST_MODES)}, got {mode!r}")
        out["burst_mode"] = mode
        if mode:
            length = _int(patch.get("burst_length"), f"{where}.burst_length")
            if length not in (2, 3, 4):
                raise SuiteError(
                    f"{where}.burst_length must be 2/3/4 for burst_mode "
                    f"{mode}, got {length}")
            out["burst_length"] = length
            if "burst_lane_step" in patch:
                out["burst_lane_step"] = _int(
                    patch["burst_lane_step"], f"{where}.burst_lane_step")
            if "burst_lane_mask" in patch:
                out["burst_lane_mask"] = _mask_value(
                    patch["burst_lane_mask"], 64, f"{where}.burst_lane_mask")
            if "burst_id_base" in patch:
                base = _int(patch["burst_id_base"],
                            f"{where}.burst_id_base", minimum=1)
                out["burst_id_base"] = base
    elif any(k in patch for k in ("burst_length", "burst_lane_step",
                                  "burst_lane_mask", "burst_id_base")):
        raise SuiteError(f"{where}: burst_* fields require burst_mode")
    if "reg_class" in patch:
        reg = str(patch["reg_class"]).strip()
        if reg not in FPU_REG_CLASSES:
            raise SuiteError(f"{where}.reg_class must be one of "
                             f"{list(FPU_REG_CLASSES)}, got {reg!r}")
        out["reg_class"] = reg
    return out


def normalise_program_overrides(suite: dict):
    """Return canonical per-program overrides, or None when absent.

    Keys are the suite's real program ids; an unknown program or an unknown
    field is a loud error. The canonical form is part of suite_hash and is
    recorded in each component manifest as `program_override`.
    """
    if "program_overrides" not in suite:
        return None
    raw = suite.get("program_overrides")
    if not isinstance(raw, dict):
        raise SuiteError("suite.program_overrides must be an object keyed by "
                         "program_id")
    if not raw:
        raise SuiteError("suite.program_overrides must not be empty")
    by_id = _program_map(suite)
    out = {}
    for pid, override in raw.items():
        pid = str(pid)
        if pid not in by_id:
            raise SuiteError(f"program_overrides has unknown program_id "
                             f"{pid!r}; suite programs are {sorted(by_id)}")
        where = f"program_overrides[{pid}]"
        if not isinstance(override, dict) or not override:
            raise SuiteError(f"{where} must be a non-empty object")
        unknown = sorted(set(override) - set(PROGRAM_OVERRIDE_TOP))
        if unknown:
            raise SuiteError(f"{where} has unknown field(s): {unknown}")
        canon = {}
        if "fpu_mode" in override:
            canon["fpu_mode"] = _normalise_fpu_patch(
                override["fpu_mode"], f"{where}.fpu_mode")
        if "fault_mask" in override:
            mask = _mask_value(override["fault_mask"], 64,
                               f"{where}.fault_mask")
            canon["fault_mask"] = _mask_text(mask, 64)
        if "max_faults" in override:
            value = _int(override["max_faults"], f"{where}.max_faults",
                         minimum=0)
            if value != 1:
                raise SuiteError(f"{where}.max_faults must be 1 (one "
                                 f"component fault), got {value}")
            canon["max_faults"] = value
        if "first_clock" in override:
            canon["first_clock"] = _int(override["first_clock"],
                                        f"{where}.first_clock", minimum=0)
        out[pid] = canon
    return out


def program_override_identity(override) -> dict:
    """Identity projection for one canonical per-program override."""
    if override is None:
        return {}
    return json.loads(json.dumps(override, sort_keys=True))


def effective_geometry(base_injector: dict, override: dict | None):
    """Resolve (fpu_mode, precision, lane_width, lane_offset) before seed_plan."""
    fpu = dict((base_injector or {}).get("fpu_mode") or {})
    if override:
        fpu.update(override.get("fpu_mode") or {})
    return _finalise_geometry(fpu)


def _finalise_geometry(fpu: dict):
    precision = str(fpu.get("precision", "fp32"))
    if precision not in PRECISIONS:
        raise SuiteError(f"fpu_mode.precision must be one of "
                         f"{list(PRECISIONS)}, got {precision!r}")
    lane_width = _int(fpu.get("lane_width",
                              64 if precision == "fp64" else 32),
                      "fpu_mode.lane_width", minimum=8)
    if lane_width not in LANE_WIDTHS:
        raise SuiteError(f"fpu_mode.lane_width must be one of "
                         f"{list(LANE_WIDTHS)}, got {lane_width}")
    if precision == "fp64" and lane_width != 64:
        raise SuiteError("fpu_mode: fp64 requires lane_width 64")
    if precision == "fp32" and lane_width < 32:
        raise SuiteError("fpu_mode: fp32 requires lane_width >= 32")
    lane_offset = _int(fpu.get("lane_offset", 0), "fpu_mode.lane_offset",
                       minimum=0)
    if lane_offset >= 128 // lane_width:
        raise SuiteError(f"fpu_mode.lane_offset {lane_offset} >= "
                         f"{128 // lane_width} for lane_width {lane_width}")
    fpu["precision"] = precision
    fpu["lane_width"] = lane_width
    fpu["lane_offset"] = lane_offset
    return fpu, precision, lane_width, lane_offset


def resolve_program_injector(base_injector: dict, override: dict | None,
                             seed_entry: dict | None, program_id: str):
    """Resolve ONE component's injector: base -> override -> seed_plan.

    Mask precedence (most specific wins):
      suite base < seed_plan.mask < program_overrides[pid].fault_mask
      < seed_plan.program_mask[pid]
    The seed_plan's geometry fields only override fields it actually
    declares; omitted fields (e.g. precision for W6) keep the per-program
    override, which is what lets SVD be fp64 while FFT/sparse-CG stay fp32.
    """
    injector = json.loads(json.dumps(base_injector or {}))
    override = override or {}
    if "max_faults" in override:
        injector["max_faults"] = override["max_faults"]
    if "first_clock" in override:
        injector["first_clock"] = override["first_clock"]
    fpu = dict(injector.get("fpu_mode") or {})
    if override.get("fpu_mode"):
        fpu.update(override["fpu_mode"])

    if seed_entry is not None:
        for key in ("precision", "lane_width", "lane_offset", "bitseg",
                    "op_classes", "reg_class", "decode_guard",
                    "permanent_stuck"):
            if key in seed_entry:
                fpu[key] = seed_entry[key]
        if "bitseg" in seed_entry:
            fpu["bitseg"] = seed_entry["bitseg"]
        elif seed_entry.get("permanent_stuck", True):
            # Permanent stuck uses the explicit fault_mask; CHAOSFPU
            # forbids a simultaneous bitseg (base or override).
            fpu.pop("bitseg", None)
        fpu["stuck_polarity"] = seed_entry["polarity"]
        fpu["f5_warmup"] = seed_entry["warmup"]
        fpu["f5_sample_limit"] = seed_entry["sample"]["limit"]
        fpu["f5_keep_first_last_n"] = seed_entry["sample"]["keep_first_last_n"]

    fpu, precision, lane_width, lane_offset = _finalise_geometry(fpu)

    base_raw = injector.get(
        "fault_mask", (injector.get("fpu_mode") or {}).get("fault_mask"))
    mask = None
    if base_raw not in (None, ""):
        value = int(str(base_raw), 0)
        mask = value if value else None
    if seed_entry is not None:
        mask = _mask_value(seed_entry["mask"], 64, "seed_plan.mask")
    if override.get("fault_mask") is not None:
        mask = _mask_value(override["fault_mask"], 64,
                           "program_overrides.fault_mask")
    if seed_entry is not None and program_id in \
            (seed_entry.get("program_mask") or {}):
        mask = _mask_value(seed_entry["program_mask"][program_id], 64,
                           f"seed_plan.program_mask[{program_id}]")
    if mask is None:
        # Legacy F0 suites may omit fault_mask entirely (the injector picks
        # its own target); only an F5 seed is required to pin one.
        if seed_entry is not None:
            raise SuiteError(
                f"{program_id}: resolved fault_mask is missing/zero")
    else:
        if mask == 0:
            raise SuiteError(
                f"{program_id}: resolved fault_mask is missing/zero")
        if lane_width < 64 and (mask >> lane_width):
            raise SuiteError(
                f"{program_id}: fault_mask 0x{mask:x} does not fit effective "
                f"lane_width {lane_width} (precision {precision})")
        injector["fault_mask"] = _mask_text(mask, lane_width)
    injector["fpu_mode"] = fpu
    return injector


def normalise_seed_plan_entry(entry: dict, index: int,
                              allowed_programs=None) -> dict:
    """Validate one seed_plan entry and return its canonical identity form.

    Canonical form is what suite_hash binds; it is also what the runner
    writes into the component manifest (`seed_plan_entry`). Numeric masks
    are normalised to a fixed-width 0x string, optional F5 knobs get their
    defaults, and unknown keys are rejected (a typo must never silently
    change a fault).
    """
    where = f"seed_plan[{index}]"
    if not isinstance(entry, dict):
        raise SuiteError(f"{where} must be an object")
    missing = [k for k in SEED_PLAN_REQUIRED if k not in entry]
    if missing:
        raise SuiteError(f"{where} missing required field(s): {missing}")
    unknown = sorted(set(entry) - SEED_PLAN_ALLOWED)
    if unknown:
        raise SuiteError(f"{where} has unknown field(s): {unknown}")

    suite_seed = _int(entry["suite_seed"], f"{where}.suite_seed", minimum=1)
    submodel = str(entry["submodel"] or "").strip()
    if not submodel:
        raise SuiteError(f"{where}.submodel is required")
    # Geometry fields are OPTIONAL: when omitted (W6 F5) the component
    # keeps the per-program override; when present (W5 F5) they are part of
    # the seed and override the program default, as documented.
    precision = entry.get("precision")
    if precision is not None:
        precision = str(precision).strip()
        if precision not in PRECISIONS:
            raise SuiteError(f"{where}.precision must be one of "
                             f"{list(PRECISIONS)}, got {precision!r}")
    lane_width = entry.get("lane_width")
    if lane_width is None:
        if precision is not None:
            lane_width = 64 if precision == "fp64" else 32
    else:
        lane_width = _int(lane_width, f"{where}.lane_width", minimum=8)
        if lane_width not in LANE_WIDTHS:
            raise SuiteError(f"{where}.lane_width must be one of "
                             f"{list(LANE_WIDTHS)}, got {lane_width}")
    if precision is not None and lane_width is not None:
        if precision == "fp64" and lane_width != 64:
            raise SuiteError(f"{where}: fp64 requires lane_width 64")
        if precision == "fp32" and lane_width < 32:
            raise SuiteError(f"{where}: fp32 requires lane_width >= 32")
    lane_offset = entry.get("lane_offset")
    if lane_offset is not None:
        lane_offset = _int(lane_offset, f"{where}.lane_offset", minimum=0)
        if lane_width is not None and lane_offset >= 128 // lane_width:
            raise SuiteError(f"{where}.lane_offset {lane_offset} >= "
                             f"{128 // lane_width} for lane_width {lane_width}")
    polarity = _int(entry["polarity"], f"{where}.polarity", minimum=0)
    if polarity not in (0, 1):
        raise SuiteError(f"{where}.polarity must be 0 or 1, got {polarity}")
    mask = _mask_value(entry["mask"], lane_width or 64, f"{where}.mask")
    warmup = _int(entry["warmup"], f"{where}.warmup", minimum=0)
    sample = _normalise_sample(entry, where)

    bitseg = entry.get("bitseg")
    if bitseg is not None:
        bitseg = str(bitseg).strip()
        if bitseg not in BITSEGS:
            raise SuiteError(f"{where}.bitseg must be one of "
                             f"{list(BITSEGS)}, got {bitseg!r}")
        if bool(entry.get("permanent_stuck", True)):
            # CHAOSFPU panics on permanentStuck + bitseg: the fixed mask is
            # authoritative. Reject it here instead of at gem5 startup.
            raise SuiteError(
                f"{where}: bitseg is not allowed with permanent_stuck "
                "(the explicit fault_mask is authoritative)")

    raw_ops = entry.get("op_classes")
    if raw_ops is None:
        op_classes = []
    elif isinstance(raw_ops, (list, tuple)):
        op_classes = [str(x) for x in raw_ops]
    else:
        raise SuiteError(f"{where}.op_classes must be an array")
    bad_ops = [x for x in op_classes if x not in FPU_OP_CLASSES]
    if bad_ops:
        raise SuiteError(f"{where}.op_classes has unknown name(s): {bad_ops}")
    if len(set(op_classes)) != len(op_classes):
        raise SuiteError(f"{where}.op_classes contains duplicates")

    reg_class = str(entry.get("reg_class", "any") or "any").strip()
    if reg_class not in FPU_REG_CLASSES:
        raise SuiteError(f"{where}.reg_class must be one of "
                         f"{list(FPU_REG_CLASSES)}, got {reg_class!r}")

    program_mask = entry.get("program_mask")
    masks = {}
    if program_mask is not None:
        if not isinstance(program_mask, dict) or not program_mask:
            raise SuiteError(f"{where}.program_mask must be a non-empty "
                             "object keyed by program_id")
        if allowed_programs is not None:
            unknown_pids = sorted(set(program_mask) - set(allowed_programs))
            if unknown_pids:
                raise SuiteError(f"{where}.program_mask unknown program_id(s): "
                                 f"{unknown_pids}")
        for pid, value in program_mask.items():
            parsed = _mask_value(value, 64,
                                 f"{where}.program_mask[{pid}]")
            masks[str(pid)] = _mask_text(parsed, 64)

    out = {
        "suite_seed": suite_seed,
        "submodel": submodel,
        "mask": _mask_text(mask, lane_width or 64),
        "mask_value": mask,
        "polarity": polarity,
        "warmup": warmup,
        "sample": sample,
        "op_classes": op_classes,
        "reg_class": reg_class,
        "decode_guard": bool(entry.get("decode_guard", True)),
        "permanent_stuck": bool(entry.get("permanent_stuck", True)),
    }
    if precision is not None:
        out["precision"] = precision
    if lane_width is not None:
        out["lane_width"] = lane_width
    if lane_offset is not None:
        out["lane_offset"] = lane_offset
    if bitseg is not None:
        out["bitseg"] = bitseg
    if masks:
        out["program_mask"] = masks
    return out


def normalise_seed_plan(suite: dict):
    """Return the normalised seed_plan (sorted by suite_seed) or None."""
    if "seed_plan" not in suite:
        return None
    plan = suite.get("seed_plan")
    if not isinstance(plan, list):
        raise SuiteError("suite.seed_plan must be a list")
    if len(plan) != SEED_PLAN_COUNT:
        raise SuiteError(f"suite.seed_plan must contain exactly "
                         f"{SEED_PLAN_COUNT} entries, got {len(plan)}")
    allowed_programs = tuple(_program_map(suite))
    entries = [normalise_seed_plan_entry(e, i, allowed_programs)
               for i, e in enumerate(plan)]
    seeds = [e["suite_seed"] for e in entries]
    if set(seeds) != set(range(1, SEED_PLAN_COUNT + 1)):
        raise SuiteError(f"seed_plan suite_seed values must be exactly "
                         f"{list(range(1, SEED_PLAN_COUNT + 1))}, got {seeds}")
    if len(set(seeds)) != len(seeds):
        raise SuiteError(f"seed_plan duplicate suite_seed: {seeds}")
    return sorted(entries, key=lambda e: e["suite_seed"])


def seed_plan_map(suite: dict):
    """Map suite_seed -> canonical entry; None for a legacy suite."""
    plan = normalise_seed_plan(suite)
    if plan is None:
        return None
    return {e["suite_seed"]: e for e in plan}


def seed_plan_entry(suite: dict, suite_seed: int):
    """Return the pre-registered entry for one suite seed (loud if missing)."""
    plan = seed_plan_map(suite)
    if plan is None:
        return None
    try:
        seed = int(suite_seed)
    except (TypeError, ValueError):
        raise SuiteError(f"suite_seed must be an integer, got {suite_seed!r}")
    if seed not in plan:
        raise SuiteError(f"suite_seed {seed} is not in the pre-registered "
                         f"seed_plan {sorted(plan)}")
    return plan[seed]


def seed_plan_identity(entry: dict) -> dict:
    """Identity-only projection of a canonical seed_plan entry."""
    out = {k: entry[k] for k in (
        "suite_seed", "submodel", "mask", "polarity", "warmup", "sample",
        "op_classes", "reg_class", "decode_guard", "permanent_stuck")}
    for key in ("precision", "lane_width", "lane_offset", "bitseg",
                "program_mask"):
        if key in entry:
            out[key] = entry[key]
    return out


def suite_identity_document(suite: dict, allow_pending: bool = True) -> dict:
    """构造参与 suite_hash 的严格身份文档。

    只含身份字段：suite_id/suite_version/program_order、每程序
    program_id/program_index/source_sha256/binary_sha256/固定规模、
    compiler 版本与 cflags、oracle 版本。**绝不包含**运行结果、golden、
    attempt、oracle 结局、组件状态或路径。
    """
    if not isinstance(suite, dict):
        raise SuiteError("suite manifest must be an object")
    suite_id = str(suite.get("suite_id", "")).strip()
    suite_version = str(suite.get("suite_version", "")).strip()
    if not suite_id:
        raise SuiteError("suite.suite_id is required")
    if not suite_version:
        raise SuiteError("suite.suite_version is required")
    _validate_order_and_count(suite)
    by_id = _program_map(suite)
    missing = [p for p in PROGRAM_ORDER if p not in by_id]
    extra = [p for p in by_id if p not in PROGRAM_ORDER]
    if missing:
        raise SuiteError(f"suite missing program component(s): {missing}")
    if extra:
        raise SuiteError(f"suite has unknown program component(s): {extra}")

    programs = []
    for index, pid in enumerate(PROGRAM_ORDER):
        p = by_id[pid]
        declared_index = p.get("program_index")
        if declared_index is not None:
            try:
                declared_index = int(declared_index)
            except (TypeError, ValueError):
                raise SuiteError(f"{pid}.program_index must be an integer")
            if declared_index != index:
                raise SuiteError(
                    f"{pid}.program_index must be {index} in fixed order "
                    f"{list(PROGRAM_ORDER)}, got {declared_index}")
        scale = p.get("scale")
        if not isinstance(scale, dict) or not scale:
            raise SuiteError(f"{pid}.scale must be a non-empty object")
        programs.append({
            "program_id": pid,
            "program_index": index,
            "source_sha256": _check_hash(
                p.get("source_sha256"), f"{pid}.source_sha256", allow_pending),
            "binary_sha256": _check_hash(
                p.get("binary_sha256"), f"{pid}.binary_sha256", allow_pending),
            "scale": scale,
        })

    compiler = suite.get("compiler") or {}
    if not isinstance(compiler, dict):
        raise SuiteError("suite.compiler must be an object")
    compiler_version = str(
        compiler.get("version") or suite.get("compiler_version") or "").strip()
    cflags = _normalise_cflags(
        compiler.get("cflags") if "cflags" in compiler else suite.get("cflags"))
    if not compiler_version:
        raise SuiteError("suite.compiler.version is required")
    if not cflags.strip():
        raise SuiteError("suite.compiler.cflags is required")

    oracle = suite.get("oracle") or {}
    if not isinstance(oracle, dict):
        raise SuiteError("suite.oracle must be an object")
    oracle_version = str(
        oracle.get("version") or suite.get("oracle_version") or "").strip()
    if not oracle_version:
        raise SuiteError("suite.oracle.version is required")

    doc = {
        "suite_id": suite_id,
        "suite_version": suite_version,
        "program_order": list(PROGRAM_ORDER),
        "program_count": PROGRAM_COUNT,
        "programs": programs,
        "compiler": {
            "version": compiler_version,
            "cflags": cflags,
        },
        "oracle": {
            "version": oracle_version,
        },
    }

    # [FSU][F5] The pre-registered seed plan is identity: it is frozen
    # BEFORE any run, so it must be covered by suite_hash. Legacy suites
    # without a seed_plan keep their historical hash byte-for-byte.
    plan = normalise_seed_plan(suite)
    if plan is not None:
        doc["seed_plan"] = [seed_plan_identity(e) for e in plan]
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
    # [FSU][W6] Per-program precision/lane/mask overrides are identity and
    # are covered by suite_hash. Legacy suites without program_overrides
    # keep their historical hash byte-for-byte.
    overrides = normalise_program_overrides(suite)
    if overrides is not None:
        doc["program_overrides"] = overrides
    return doc


def compute_suite_hash(suite: dict) -> str:
    return sha256_bytes(canonical_bytes(suite_identity_document(suite)))


def validate_suite_manifest(suite: dict, require_hashes: bool = False,
                            require_suite_hash: bool = False) -> dict:
    """结构 + 固定顺序 + suite_hash 漂移门禁。

    require_hashes=True：正式运行前要求所有 source/binary SHA 已回填。
    require_suite_hash=True：manifest 必须带 suite_hash，且与重算一致。
    返回 {ok, suite_hash, identity}；任何不成立都抛 SuiteError。
    """
    defaults = suite.get("run_defaults") or {}
    freq = str(defaults.get("freq", "") or "").strip()
    if freq == "F5" and "seed_plan" not in suite:
        raise SuiteError(
            "an F5 suite must pre-register a seed_plan (3 suite seeds with "
            "submodel/precision/mask/polarity/warm-up/sample)")
    doc = suite_identity_document(suite, allow_pending=not require_hashes)
    if require_hashes:
        for p in doc["programs"]:
            for key in ("source_sha256", "binary_sha256"):
                _check_hash(p[key], f"{p['program_id']}.{key}",
                            allow_pending=False)
    computed = sha256_bytes(canonical_bytes(doc))
    declared = suite.get("suite_hash")
    if declared is not None:
        declared = str(declared)
        _check_hash(declared, "suite.suite_hash", allow_pending=False)
        if declared != computed:
            raise SuiteError(
                f"suite_hash drift: declared {declared}, recomputed {computed}")
    elif require_suite_hash:
        raise SuiteError("suite.suite_hash is required before a formal run")
    return {"ok": True, "suite_hash": computed, "identity": doc}


def component_seed_from_digest(digest: bytes) -> int:
    """取摘要前 8 字节（大端），0 映射为 1。"""
    if len(digest) < 8:
        raise SuiteError("digest must contain at least 8 bytes")
    value = int.from_bytes(digest[:8], "big")
    return value if value else 1


def derive_component_seed(suite_seed: int, program_id: str,
                          policy_version: str = DEFAULT_COMPONENT_SEED_POLICY,
                          suite_id: str = DEFAULT_SUITE_ID,
                          suite_version: str = DEFAULT_SUITE_VERSION) -> int:
    """SHA-256(suite_id|suite_version|suite_seed|program_id|policy_version)。

    确定性：同一 suite seed + program 永远得到同一 component seed。
    5 个程序必须互不相同；调用方应使用 derive_component_seeds() 做强校验。
    """
    if program_id not in PROGRAM_ORDER:
        raise SuiteError(f"unknown program_id {program_id!r}")
    try:
        seed_int = int(suite_seed)
    except (TypeError, ValueError):
        raise SuiteError(f"suite_seed must be an integer, got {suite_seed!r}")
    if seed_int < 0:
        raise SuiteError("suite_seed must be >= 0")
    if not str(policy_version).strip():
        raise SuiteError("policy_version is required")
    material = "|".join([
        str(suite_id), str(suite_version), str(seed_int),
        str(program_id), str(policy_version),
    ]).encode("utf-8")
    return component_seed_from_digest(hashlib.sha256(material).digest())


def derive_component_seeds(suite_seed: int,
                           policy_version: str = DEFAULT_COMPONENT_SEED_POLICY,
                           suite_id: str = DEFAULT_SUITE_ID,
                           suite_version: str = DEFAULT_SUITE_VERSION):
    """按固定顺序返回 5 个 component seed，并拒绝任何碰撞。"""
    seeds = {pid: derive_component_seed(suite_seed, pid, policy_version,
                                        suite_id, suite_version)
             for pid in PROGRAM_ORDER}
    if len(set(seeds.values())) != PROGRAM_COUNT:
        raise SuiteError(f"component seed collision: {seeds}")
    if any(v == 0 for v in seeds.values()):
        raise SuiteError("component seed 0 must be mapped to 1")
    return seeds


def component_golden_sha256(program: dict) -> tuple:
    """返回 (sha256, scheme)；不伪造 golden artifact 哈希。

    优先级：
      1. `golden_array_sha256` —— 预注册 golden 数组的 canonical 字节 SHA-256
         （W5 逐元素 oracle 的正确绑定；gate 生成 golden 后回填）；
      2. 显式 64-hex `golden_sha256`；
      3. suite config 中 golden token 的 UTF-8 SHA-256（legacy fallback，显式
         记录 scheme，绝不冒充数组哈希）。
    """
    array_sha = program.get("golden_array_sha256")
    if array_sha:
        return _check_hash(array_sha, "golden_array_sha256",
                           allow_pending=False), \
            "sha256-of-canonical-golden-array-v1"
    explicit = program.get("golden_sha256")
    if explicit:
        text = str(explicit)
        if text == "pending":
            raise SuiteError(
                f"{program.get('program_id')}: golden_sha256 is still pending")
        return _check_hash(text, "golden_sha256", allow_pending=False), \
            "explicit-golden-sha256-v1"
    golden = program.get("golden")
    if golden is None or str(golden).strip() == "":
        raise SuiteError(
            f"{program.get('program_id')}: golden token is required for a "
            "certified component")
    token = str(golden).strip()
    return sha256_bytes(token.encode("utf-8")), \
        "sha256-utf8-of-golden-token-v1"


REQUIRED_COMPONENT_FIELDS = (
    "suite_id", "suite_hash", "suite_seed", "program_id", "program_index",
    "program_count", "component_attempt", "component_manifest_sha256",
    "component_binary_sha256", "component_source_sha256",
    "component_golden_sha256", "component_status", "component_eligible",
    "component_activated", "component_terminal", "component_oracle",
)


def validate_component_manifest(component: dict, suite: dict | None = None) -> dict:
    """校验单个 component manifest；缺字段/顺序/哈希漂移全部抛错。"""
    if not isinstance(component, dict):
        raise SuiteError("component manifest must be an object")
    missing = [k for k in REQUIRED_COMPONENT_FIELDS if k not in component]
    if missing:
        raise SuiteError(f"component manifest missing fields: {missing}")
    pid = str(component.get("program_id", "")).strip()
    if pid not in PROGRAM_ORDER:
        raise SuiteError(f"component program_id {pid!r} not in fixed suite")
    want_index = PROGRAM_ORDER.index(pid)
    try:
        index = int(component.get("program_index"))
    except (TypeError, ValueError):
        raise SuiteError(f"{pid}.program_index must be an integer")
    if index != want_index:
        raise SuiteError(f"{pid}.program_index must be {want_index}, "
                         f"got {index}")
    try:
        count = int(component.get("program_count"))
    except (TypeError, ValueError):
        raise SuiteError(f"{pid}.program_count must be {PROGRAM_COUNT}")
    if count != PROGRAM_COUNT:
        raise SuiteError(f"{pid}.program_count must be {PROGRAM_COUNT}, "
                         f"got {count}")
    try:
        suite_seed = int(component.get("suite_seed"))
    except (TypeError, ValueError):
        raise SuiteError(f"{pid}.suite_seed must be an integer")
    if suite_seed < 0:
        raise SuiteError(f"{pid}.suite_seed must be >= 0")
    plan = normalise_seed_plan(suite) if suite is not None else None
    if plan is not None:
        want_entry = seed_plan_entry(suite, suite_seed)
        got_entry = component.get("seed_plan_entry")
        if not isinstance(got_entry, dict):
            raise SuiteError(f"{pid}.seed_plan_entry is required for a suite "
                             "with a pre-registered seed_plan")
        if got_entry != seed_plan_identity(want_entry):
            raise SuiteError(f"{pid}.seed_plan_entry drift for suite_seed "
                             f"{suite_seed}")
    if suite is not None:
        overrides = normalise_program_overrides(suite)
        if overrides is not None:
            want_override = overrides.get(pid)
            got_override = component.get("program_override")
            if want_override is None:
                if got_override not in (None, {}):
                    raise SuiteError(f"{pid}.program_override drift: suite "
                                     "has no override for this program")
            elif got_override != program_override_identity(want_override):
                raise SuiteError(f"{pid}.program_override drift")
    try:
        attempt = int(component.get("component_attempt"))
    except (TypeError, ValueError):
        raise SuiteError(f"{pid}.component_attempt must be an integer")
    if attempt < 1:
        raise SuiteError(f"{pid}.component_attempt must be >= 1")
    status = str(component.get("component_status", ""))
    if status not in COMPONENT_STATUSES:
        raise SuiteError(f"{pid}.component_status {status!r} not in "
                         f"{list(COMPONENT_STATUSES)}")
    _check_hash(component.get("suite_hash"), f"{pid}.suite_hash",
                allow_pending=False)
    for key in ("component_manifest_sha256", "component_binary_sha256",
                "component_source_sha256", "component_golden_sha256"):
        _check_hash(component.get(key), f"{pid}.{key}", allow_pending=False)
    for key in ("component_eligible", "component_activated"):
        try:
            value = int(component.get(key))
        except (TypeError, ValueError):
            raise SuiteError(f"{pid}.{key} must be an integer")
        if value < 0:
            raise SuiteError(f"{pid}.{key} must be >= 0")
    terminal = component.get("component_terminal")
    if terminal is not None and not isinstance(terminal, str):
        raise SuiteError(f"{pid}.component_terminal must be string or null")
    if not str(component.get("component_oracle", "")).strip():
        raise SuiteError(f"{pid}.component_oracle is required")

    if suite is not None:
        suite_id = str(suite.get("suite_id", "")).strip()
        if str(component.get("suite_id")) != suite_id:
            raise SuiteError(f"{pid}.suite_id drift: "
                             f"{component.get('suite_id')!r} != {suite_id!r}")
        suite_hash = compute_suite_hash(suite)
        if str(component.get("suite_hash")) != suite_hash:
            raise SuiteError(f"{pid}.suite_hash drift")
        by_id = _program_map(suite)
        sp = by_id.get(pid)
        if sp is None:
            raise SuiteError(f"{pid}: missing from suite")
        if component.get("component_source_sha256") != sp.get("source_sha256"):
            raise SuiteError(f"{pid}.component_source_sha256 drift")
        if component.get("component_binary_sha256") != sp.get("binary_sha256"):
            raise SuiteError(f"{pid}.component_binary_sha256 drift")
        want_golden, _ = component_golden_sha256(sp)
        if component.get("component_golden_sha256") != want_golden:
            raise SuiteError(f"{pid}.component_golden_sha256 drift")
    return {"ok": True, "program_id": pid, "program_index": index}


def validate_component_manifests(components, suite: dict | None = None) -> dict:
    """5/5、唯一、固定顺序；缺 component / 重复 component 响亮拒绝。"""
    if not isinstance(components, list):
        raise SuiteError("components must be a list")
    if len(components) != PROGRAM_COUNT:
        raise SuiteError(f"suite requires exactly {PROGRAM_COUNT} components, "
                         f"got {len(components)}")
    seen = []
    for c in components:
        info = validate_component_manifest(c, suite)
        seen.append(info["program_id"])
    if len(set(seen)) != len(seen):
        raise SuiteError(f"duplicate component(s): {seen}")
    if seen != list(PROGRAM_ORDER):
        raise SuiteError(
            f"components must be in fixed order {list(PROGRAM_ORDER)}, "
            f"got {seen}")
    return {"ok": True, "program_order": seen}


def suite_seed_state(seed_dir: Path) -> dict:
    """suite seed 的最终状态。

    只有同时满足以下条件才返回 admitted：
      1. seed_dir/suite_manifest.json 存在且身份/suite_hash 自洽；
      2. seed_dir/audit.json.ok is True；
      3. components 恰好 5 个、顺序固定、无缺失/重复；
      4. 每个 component manifest 校验通过，且其 attempt 的 audit.json
         同时 ok=True 与 certified=True，component_status=admitted。
    """
    seed_dir = Path(seed_dir)
    sm_path = seed_dir / "suite_manifest.json"
    if not sm_path.exists():
        attempts = sorted(seed_dir.glob("attempt-*")) if seed_dir.exists() else []
        if any(a.is_dir() for a in attempts) or (seed_dir / ".failed").exists():
            return {"state": "failed", "reason": "no suite_manifest.json"}
        return {"state": "pending", "reason": "no suite_manifest.json"}
    try:
        sm = json.loads(sm_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"state": "invalid", "reason": f"unreadable suite_manifest: {e}"}
    suite = sm.get("suite")
    try:
        v = validate_suite_manifest(suite, require_hashes=True,
                                    require_suite_hash=True)
        suite_hash = v["suite_hash"]
        if str(sm.get("suite_hash")) != suite_hash:
            raise SuiteError("suite_manifest.suite_hash drift")
        suite_seed = int(sm.get("suite_seed"))
        if suite_seed < 0:
            raise SuiteError("suite_manifest.suite_seed must be >= 0")
    except (SuiteError, TypeError, ValueError) as e:
        return {"state": "invalid", "reason": str(e)}

    audit_path = seed_dir / "audit.json"
    suite_audit_ok = False
    if audit_path.exists():
        try:
            suite_audit_ok = json.loads(
                audit_path.read_text(encoding="utf-8")).get("ok") is True
        except (OSError, json.JSONDecodeError):
            suite_audit_ok = False

    components = sm.get("components")
    try:
        validate_component_manifests(components, suite)
    except SuiteError as e:
        return {"state": "invalid", "reason": f"components: {e}",
                "suite_audit_ok": suite_audit_ok, "suite_manifest": str(sm_path)}

    certified = 0
    details = []
    for comp in components:
        pid = comp["program_id"]
        attempt = Path(comp.get("attempt", ""))
        if not attempt.is_absolute():
            attempt = seed_dir / attempt
        detail = {"program_id": pid,
                  "program_index": comp["program_index"],
                  "component_seed": comp.get("component_seed"),
                  "attempt": str(attempt),
                  "status": comp.get("component_status"),
                  "audit_ok": False, "certified": False}
        cm_path = attempt / "component_manifest.json"
        if not attempt.is_dir() or not cm_path.exists():
            detail["reason"] = "component attempt/component_manifest missing"
            details.append(detail)
            continue
        try:
            on_disk = json.loads(cm_path.read_text(encoding="utf-8"))
            validate_component_manifest(on_disk, suite)
        except (OSError, json.JSONDecodeError, SuiteError) as e:
            detail["reason"] = f"component manifest invalid: {e}"
            details.append(detail)
            continue
        # component manifest 必须指向真实 attempt manifest。
        manifest_path = attempt / "manifest.json"
        if not manifest_path.exists():
            detail["reason"] = "attempt manifest.json missing"
            details.append(detail)
            continue
        if sha256_file(manifest_path) != on_disk["component_manifest_sha256"]:
            detail["reason"] = "component_manifest_sha256 drift"
            details.append(detail)
            continue
        # W5 element oracle: the oracle result and the raw fault array must
        # both exist and be covered by the component evidence hashes.
        oracle_path = attempt / "oracle_elements.json"
        array_path = attempt / "inject/array.bin"
        evidence_path = attempt / "evidence_sha256.json"
        oracle_evidence_ok = False
        if (oracle_path.exists() and array_path.exists()
                and evidence_path.exists()):
            try:
                hashes = json.loads(evidence_path.read_text(encoding="utf-8"))
                oracle_evidence_ok = (
                    hashes.get("oracle_elements.json")
                    == sha256_file(oracle_path)
                    and hashes.get("inject/array.bin")
                    == sha256_file(array_path))
            except (OSError, json.JSONDecodeError):
                oracle_evidence_ok = False
        detail["oracle_evidence_ok"] = oracle_evidence_ok
        if not oracle_evidence_ok:
            detail["reason"] = ("element oracle evidence missing or not "
                                "covered by evidence_sha256.json")
            details.append(detail)
            continue
        if on_disk.get("component_oracle") not in ("SDC", "MASKED"):
            detail["reason"] = ("component_oracle is not an element-oracle "
                                f"outcome: {on_disk.get('component_oracle')}")
            details.append(detail)
            continue
        a_path = attempt / "audit.json"
        if not a_path.exists():
            detail["reason"] = "component audit.json missing"
            details.append(detail)
            continue
        try:
            a = json.loads(a_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            detail["reason"] = f"component audit unreadable: {e}"
            details.append(detail)
            continue
        detail["audit_ok"] = a.get("ok") is True
        detail["certified"] = a.get("certified") is True
        if not detail["audit_ok"]:
            detail["reason"] = "component audit.ok != true"
        elif not detail["certified"]:
            detail["reason"] = "component audit.certified != true"
        elif on_disk.get("component_status") != "admitted":
            detail["reason"] = ("component_status != admitted: "
                                f"{on_disk.get('component_status')}")
        else:
            certified += 1
        details.append(detail)

    admitted = (suite_audit_ok and certified == PROGRAM_COUNT
                and len(components) == PROGRAM_COUNT)
    if admitted:
        state = "admitted"
    elif any(d.get("status") == "failed" for d in details) \
            or any("reason" in d for d in details):
        state = "failed"
    else:
        state = "invalid"
    return {
        "state": state,
        "suite_id": suite.get("suite_id"),
        "suite_version": suite.get("suite_version"),
        "suite_hash": suite_hash,
        "suite_seed": sm.get("suite_seed"),
        "suite_audit_ok": suite_audit_ok,
        "component_runs": len(components),
        "component_certified": certified,
        "components": details,
        "suite_manifest": str(sm_path),
    }
