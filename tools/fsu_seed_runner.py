#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_seed_runner.py — FSU 单 seed（census → injection → oracle → chain）运行器。

每个 seed 的目录:
  runs/fsu/<RunID>/seed<N>/attempt-<k>/
    manifest.json          本 seed/attempt 的身份与完整命令
    census/                countOnly gem5 outdir + fpu_injections.log
    inject/                injection gem5 outdir + fpu_injections.log + prop_evt.txt.gz
    run.out / run.err      注入运行的 stdout/stderr
    stats.txt              注入运行 stats（从 inject/ 复制；空文件即失败）
    oracle.json            classify.py 的结局与理由
    chain_report.json      fsu_chain_check.check_stream 的完整结果
    ordinals.json          F1/F2/F3 完整 ordinal 序列（canonical JSON）
    not_activated.json     rate 首 ordinal 超出 ROI 时的显式终局
    evidence_sha256.json   本 attempt 全部证据文件的 SHA-256
    <RunID>-seed<N>.md     传播链 Markdown（真实事件生成）
    .done / .failed        原子完成标记（仅 .done 计入 3/3）
    .not_activated         rate 零注入标记（不计入 3/3）

规则:
  - attempt 目录只增不改；失败保留并记录原因，重跑创建 attempt-k+1。
  - 已存在 AUTHORITATIVE 的 seed 默认不再运行。
  - admitted 需要：非 SimulatorError/Inactive、faults>=1、stats 非空、
    所有 injected fault 都出现在事件流且每条链 certified、证据流未截断。
  - F1/F2/F3 必须有 injector.rate；仅改 --fsu_freq 标签会被拒绝。
    rate 模式实际注入数必须等于 ordinal 数；零 ordinal 记 not_activated。
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
import fsu_rate_ordinals as O  # noqa: E402
import fsu_config_profile as CP  # noqa: E402
import fsu_scope as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
DEFAULT_CONFIG = ROOT / "configs/se/ooo_proxy.py"
DEFAULT_OUT = ROOT / "runs/fsu"
COMPLETE_ROOT = DEFAULT_OUT / "COMPLETE_PROPAGATION_PATHS"
MASK64 = (1 << 64) - 1

# [FSU][FP06] Accepted fpu_mode.op_classes names. MUST stay identical to
# CHAOSFPU.cc kOpClassNames (gem5 OpClass names); the C++ constructor panics
# on anything else, so the runner rejects the same set before gem5 starts.
FPU_OP_CLASSES = (
    "FloatAdd", "FloatCmp", "FloatCvt", "FloatMult", "FloatMultAcc",
    "FloatDiv", "FloatMisc", "FloatSqrt",
    "SimdFloatAdd", "SimdFloatAlu", "SimdFloatCmp", "SimdFloatCvt",
    "SimdFloatMult", "SimdFloatMultAcc", "SimdFloatDiv", "SimdFloatSqrt",
    "SimdFloatMisc",
)
FPU_REG_CLASSES = ("any", "vec", "float", "vec_elem")


def _fpu_filter_args(fpu: dict):
    """Translate manifest op_classes/reg_class into CLI flags (fail closed).

    Returns a list of argv fragments. An unknown opClass or register class is
    a hard error: silently ignoring it would make the census/injection stream
    disagree with the manifest.
    """
    args = []
    raw = fpu.get("op_classes")
    if raw is None or raw == "" or raw == []:
        names = []
    elif isinstance(raw, str):
        names = [x.strip() for x in raw.split(",") if x.strip()]
    elif isinstance(raw, list):
        names = raw
    else:
        raise ValueError(
            f"fpu_mode.op_classes must be an array of OpClass names, got "
            f"{type(raw).__name__}")
    for name in names:
        if not isinstance(name, str) or name not in FPU_OP_CLASSES:
            raise ValueError(
                f"unknown fpu_mode.op_classes name {name!r}; expected one of "
                f"{list(FPU_OP_CLASSES)}")
    if len(set(names)) != len(names):
        raise ValueError("fpu_mode.op_classes contains duplicate names")
    if names:
        args += ["--fpu_op_classes", ",".join(names)]

    reg = fpu.get("reg_class")
    if reg is None or reg == "":
        reg = "any"
    if reg not in FPU_REG_CLASSES:
        raise ValueError(
            f"unknown fpu_mode.reg_class {reg!r}; expected one of "
            f"{list(FPU_REG_CLASSES)}")
    if reg != "any":
        args += ["--fpu_reg_class", reg]
    return args


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def chaos_pick_skip(seed: int, n_eligible: int) -> int:
    """Python twin of gem5::chaosPickSkip (cpu/o3/chaos_event_sample.hh)."""
    if n_eligible == 0:
        return 0
    x = (seed ^ 0x9E3779B97F4A7C15) & MASK64
    x = (x * 6364136223846793005 + 1442695040888963407) & MASK64
    return x % n_eligible


def parse_eligible_count(text: str) -> int:
    vals = []
    for line in text.splitlines():
        if "CHAOS_ELIGIBLE_COUNT=" in line:
            try:
                vals.append(int(line.split("CHAOS_ELIGIBLE_COUNT=")[1].split()[0]))
            except (IndexError, ValueError):
                pass
    return vals[-1] if vals else -1


def count_injections(text: str) -> int:
    """Count real injection lines; CHAOS_ELIGIBLE_COUNT/census lines excluded."""
    n = 0
    last_explicit = None
    for line in text.splitlines():
        if "faults_injected:" in line:
            try:
                last_explicit = int(line.split("faults_injected:")[1].split()[0])
            except (IndexError, ValueError):
                pass
        elif "Site: dyn_inst_execute" in line or "Site=" in line:
            n += 1
    return last_explicit if last_explicit is not None else n


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _mask_int(value, default=0):
    """Accept an int or a '0x...' string; never silently truncate."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        raise ValueError(f"fault_mask must be an integer, got {value!r}")
    if isinstance(value, int):
        return value
    return int(str(value), 0)


PHYSREG_INJECTION_MODES = ("phys", "arch_frontend", "arch_commit")
PHYSREG_REG_CLASSES = ("integer", "floating_point", "vector", "both")
PHYSREG_FAULT_TYPES = ("bit_flip", "stuck_at_zero", "stuck_at_one", "random")


def _build_physreg_cmd(manifest, outdir: Path, seed: int, max_faults: int,
                       gem5: Path, config: Path, root: Path):
    """[FR03] Explicit CHAOSPhysReg routing.

    A manifest whose `injector.component` is `physreg` MUST reach
    CHAOSPhysReg. There is no silent fallback to CHAOSFPU: unknown/ambiguous
    routing is rejected before gem5 starts.
    """
    inj = manifest["injector"]
    phys = inj.get("physreg_mode") or {}
    wl = manifest["workload"]
    binary = Path(wl["binary"])
    if not binary.is_absolute():
        binary = root / binary
    fault_mask = _mask_int(inj.get("fault_mask", phys.get("fault_mask", 0)))
    if fault_mask == 0:
        raise ValueError("physreg requires an explicit non-zero fault_mask")
    mode = str(phys.get("injection_mode", "phys"))
    if mode not in PHYSREG_INJECTION_MODES:
        raise ValueError(f"unknown physreg injection_mode {mode!r}")
    reg_class = str(phys.get("reg_class", "vector"))
    if reg_class not in PHYSREG_REG_CLASSES:
        raise ValueError(f"unknown physreg reg_class {reg_class!r}")
    fault_type = str(phys.get("fault_type", "stuck_at_zero"))
    if fault_type not in PHYSREG_FAULT_TYPES:
        raise ValueError(f"unknown physreg fault_type {fault_type!r}")
    lane_width = int(phys.get("vec_lane_width", 32))
    if lane_width not in (8, 16, 32, 64):
        raise ValueError(f"physreg vec_lane_width must be 8/16/32/64, "
                         f"got {lane_width}")
    lane_offset = int(phys.get("vec_lane_offset", -1))
    cmd = [
        str(gem5), "--quiet", "-d", str(outdir), str(config),
        "--cmd", str(binary), "--cpu", "O3",
        "--first_clock", str(inj.get("first_clock", 0)),
        "--max_faults", str(max_faults),
        "--rng_seed", str(seed),
        "--chaos_phys",
        "--phys_mode", mode,
        "--phys_target_idx", str(int(phys.get("target_phys_idx", -1))),
        "--phys_reg_class", reg_class,
        "--vec_lane_width", str(lane_width),
        "--vec_lane_offset", str(lane_offset),
        "--fault_mask", str(fault_mask),
        "--fault_type", fault_type,
    ]
    if phys.get("require_allocated"):
        cmd += ["--phys_require_allocated"]
    if phys.get("target_arch_reg") is not None:
        cmd += ["--phys_target_arch", str(int(phys["target_arch_reg"]))]
    if phys.get("bits_to_change") is not None:
        cmd += ["--bits_to_change", str(int(phys["bits_to_change"]))]
    if phys.get("semantic_role"):
        cmd += ["--phys_semantic_role", str(phys["semantic_role"])]
    profile = str(manifest.get("config_profile", "") or "")
    if profile == "B0":
        cmd += ["--config_profile", "B0"]
    elif profile not in ("", "C3"):
        raise ValueError(f"unknown config_profile {profile!r}")
    if (manifest.get("workload") or {}).get("element_oracle"):
        dump = str(manifest.get("array_dump_path")
                   or (Path(outdir) / "array.bin"))
        cmd += [f"--cmd_arg=--array-dump={dump}"]
    cmd += ["--chaos_propagation",
            "--prop_run_id", manifest["run_id"],
            "--prop_sample_run_id", f"s{seed}"]
    return cmd


def build_cmd(manifest, outdir: Path, seed: int, skip, count_only: bool,
              gem5: Path, config: Path, root: Path, rate_doc=None):
    wl = manifest["workload"]
    binary = Path(wl["binary"])
    if not binary.is_absolute():
        binary = root / binary
    inj = manifest["injector"]
    fpu = inj.get("fpu_mode") or {}
    max_faults = (len(rate_doc["ordinals"]) if rate_doc
                  else inj.get("max_faults", 1))
    fault_mask = _mask_int(inj.get("fault_mask", fpu.get("fault_mask", 0)))
    permanent = bool(fpu.get("permanent_stuck"))
    component = str(inj.get("component", "fsu") or "fsu")
    if component == "physreg":
        if rate_doc is not None:
            raise ValueError("physreg has no F1-F4 rate semantics")
        if count_only:
            raise ValueError("physreg has no eligible-count stream; do not "
                             "run a CHAOSFPU-style census")
        return _build_physreg_cmd(manifest, outdir, seed, max_faults,
                                  gem5, config, root)
    if component != "fsu":
        raise ValueError(f"unknown injector.component {component!r}; "
                         "expected 'fsu' or 'physreg'")
    cmd = [
        str(gem5), "--quiet", "-d", str(outdir), str(config),
        "--cmd", str(binary), "--cpu", "O3",
        "--first_clock", str(inj.get("first_clock", 0)),
        "--max_faults", str(max_faults),
        "--rng_seed", str(seed),
        "--chaos_fpu",
        "--fpu_first_clock", str(inj.get("first_clock", 0)),
        "--fpu_max_faults", str(max_faults),
        "--fpu_fault_mask", str(fault_mask),
        "--fpu_rng_seed", str(seed),
    ]
    if permanent:
        # [FSU][F5] One permanent stuck-at installation, then every eligible
        # event is an exposure of the same fault. Polarity/mask are pinned
        # before the run (formal seeds pre-register them).
        cmd += [
            "--fpu_permanent_stuck",
            "--fpu_stuck_polarity", str(int(fpu.get("stuck_polarity", -1))),
            "--fpu_f5_warmup", str(int(fpu.get("f5_warmup", 0))),
            "--fpu_f5_sample_limit", str(int(fpu.get("f5_sample_limit", 0))),
            "--fpu_f5_keep_first_last_n",
            str(int(fpu.get("f5_keep_first_last_n", 0))),
        ]
    for flag, key in (("--fsu_model", "model_id"), ("--fsu_freq", "freq"),
                      ("--fsu_load", "load_id"),
                      ("--fsu_submodel", "submodel")):
        if manifest.get(key):
            cmd += [flag, str(manifest[key])]
    if fpu.get("bitseg"):
        cmd += ["--fpu_bitseg", str(fpu["bitseg"])]
    if fpu.get("precision"):
        cmd += ["--fpu_precision", str(fpu["precision"])]
    if fpu.get("lane_width") is not None:
        cmd += ["--fpu_lane_width", str(fpu["lane_width"])]
    if fpu.get("lane_offset") is not None:
        cmd += ["--fpu_lane_offset", str(fpu["lane_offset"])]
    if fpu.get("decode_guard"):
        cmd += ["--fpu_decode_guard"]
    # [FSU][FP06] Explicit precision/opClass/regClass filtering. Both census
    # and injection receive the SAME flags so they count/inject one stream.
    cmd += _fpu_filter_args(fpu)
    profile = str(manifest.get("config_profile", "") or "")
    if profile == "B0":
        cmd += ["--config_profile", "B0"]
    elif profile not in ("", "C3"):
        raise ValueError(f"unknown config_profile {profile!r}")
    if fpu.get("fma_weighted"):
        cmd += ["--fpu_fma_weighted"]
    if fpu.get("recurring_stuck"):
        cmd += ["--fpu_recurring_stuck"]
    if fpu.get("rounding_sub"):
        cmd += ["--fpu_rounding_sub"]
    if fpu.get("f3_dependent"):
        cmd += ["--fpu_f3_dependent"]
    if count_only:
        cmd += ["--fpu_count_only"]
    else:
        # [W5 element oracle] The injection run must dump ONE live-out array
        # as raw fp32 bytes for tools/fsu_oracle.py. The census run does not
        # need a dump (and would only add a second, unused artifact).
        if (manifest.get("workload") or {}).get("element_oracle"):
            # argparse needs the value in the SAME token when it starts with
            # "--" (a separate "--array-dump=..." would be parsed as an option
            # and rejected as "expected one argument"). FR03 suites may pin a
            # fixed path so gate/formal guest argv is identical; the file is
            # copied into the evidence dir after the run.
            dump = str(manifest.get("array_dump_path")
                       or (Path(outdir) / "array.bin"))
            cmd += [f"--cmd_arg=--array-dump={dump}"]
        if rate_doc is not None:
            # F1/F2/F3: exact eligible ordinals, no probability/geometric draw.
            cmd += ["--fpu_events_to_skip", "0",
                    "--fpu_rate_ordinals",
                    ",".join(str(x) for x in rate_doc["ordinals"]),
                    "--fpu_rate_warmup", str(rate_doc["warmup"]),
                    "--fsu_rate_divisor", str(rate_doc["rate_divisor"]),
                    "--fsu_jitter_pct", str(rate_doc["jitter_pct"])]
        elif not permanent:
            # F5 uses f5Warmup, not the F0 uniform skip. Passing
            # --fpu_events_to_skip in permanent mode is a constructor panic
            # (the skip would index a different stream than the exposures).
            cmd += ["--fpu_events_to_skip", str(skip)]
        cmd += ["--chaos_propagation",
                "--prop_run_id", manifest["run_id"],
                "--prop_sample_run_id", f"s{seed}"]
    return cmd


def _default_runner(cmd, timeout):
    env = dict(os.environ)
    env.setdefault("PYTHONHASHSEED", "0")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           errors="replace", timeout=timeout, env=env)
        return r.returncode, r.stdout or "", r.stderr or "", False
    except subprocess.TimeoutExpired as e:
        def s(x):
            return x.decode("utf-8", "replace") if isinstance(x, bytes) else (x or "")
        return -1, s(e.stdout), s(e.stderr), True


def new_attempt_dir(seed_dir: Path):
    seed_dir.mkdir(parents=True, exist_ok=True)
    ks = []
    for p in seed_dir.glob("attempt-*"):
        if p.is_dir():
            try:
                ks.append(int(p.name.split("-")[1]))
            except (IndexError, ValueError):
                pass
    k = max(ks, default=0) + 1
    d = seed_dir / f"attempt-{k}"
    d.mkdir()
    return d, k


def _copy_stats(inject_dir: Path, attempt: Path):
    src = inject_dir / "stats.txt"
    dst = attempt / "stats.txt"
    if src.exists():
        shutil.copy2(src, dst)
    return dst


def write_hashes(attempt: Path):
    out = {}
    for p in sorted(attempt.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(attempt))
        if rel in ("evidence_sha256.json", ".done", ".failed",
                   "audit.json", "audit.md"):
            continue
        out[rel] = sha256_file(p)
    (attempt / "evidence_sha256.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def run_seed(manifest_path: Path, seed: int, out_root: Path = DEFAULT_OUT,
             gem5: Path = DEFAULT_GEM5, root: Path = ROOT,
             runner=None, timeout_s=None, allow_rerun=False,
             seed_dir: Path | None = None, component: dict | None = None,
             write_authoritative: bool = True,
             copy_to_complete: bool = True,
             config: Path = DEFAULT_CONFIG):
    """运行一个 seed（或 suite component）。

    [W5 suite] 向后兼容扩展：
      - seed_dir：覆盖默认 <out_root>/<run_id>/seed<N>；
      - component：suite component 身份元数据，写入 manifest["component"]；
      - write_authoritative=False：由 suite runner 在 component audit 通过后
        再写 AUTHORITATIVE；
      - copy_to_complete=False：component Markdown 不得冒充正式 seed 复制到
        COMPLETE_PROPAGATION_PATHS。
    旧调用（不传新参数）行为完全不变。
    """
    from classify import classify_run
    import fsu_chain_check as C

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    run_id = manifest["run_id"]
    # [FSU][D3] Active-scope gate: F1–F4 (and any future frequency outside
    # F0/F5) are DEFERRED_BY_USER. Reject before creating an attempt or
    # starting gem5. Test mode may exercise legacy parsing only with a
    # non-formal out-root.
    scope_test_mode = bool(manifest.get("scope_test_mode"))
    allowed, why = S.formal_out_root_allowed(manifest, out_root)
    if not allowed:
        raise S.ScopeError(why)
    if not scope_test_mode:
        S.enforce_active_freq(manifest.get("freq", ""), run_id)
    # F1/F2/F3 必须在创建任何 attempt 之前证明真实 rate 语义；
    # 只改 --fsu_freq 标签的 manifest 在这里被拒绝。
    rate_cfg = O.validate_rate_for_freq(
        manifest.get("freq", ""), O.rate_config_from_manifest(manifest))
    if seed_dir is None:
        seed_dir = Path(out_root) / run_id / f"seed{seed}"
    else:
        seed_dir = Path(seed_dir)
    auth = seed_dir / "AUTHORITATIVE"
    if auth.exists() and not allow_rerun:
        return {"status": "already_admitted", "authoritative": _read(auth).strip()}

    attempt, k = new_attempt_dir(seed_dir)
    runner = runner or _default_runner
    timeout = timeout_s or int(manifest.get("limits", {}).get("timeout_s", 1800))
    binary = Path(manifest["workload"]["binary"])
    if not binary.is_absolute():
        binary = Path(root) / binary
    gem5 = Path(gem5)

    source_head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    binary_sha = sha256_file(gem5) if gem5.exists() else ""
    tool_head = sha256_file(Path(__file__))

    seed_manifest = {
        **manifest,
        "seed": seed,
        "sample_run_id": f"s{seed}",
        "selection_seed": seed,
        "injection_seed": seed,
        "attempt": k,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_head": source_head,
        "gem5_binary": str(gem5),
        "gem5_sha256": binary_sha,
        "runner_tool_sha256": tool_head,
        "workload_binary": str(binary),
        "workload_sha256": sha256_file(binary) if binary.exists() else "",
    }
    if component is not None:
        seed_manifest["component"] = component
    (attempt / "manifest.json").write_text(
        json.dumps(seed_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def fail(reason, extra=None):
        info = {"status": "failed", "reason": reason, "attempt": str(attempt)}
        if extra:
            info.update(extra)
        (attempt / ".failed").write_text(reason + "\n", encoding="utf-8")
        write_hashes(attempt)
        return info

    if not gem5.exists():
        return fail(f"gem5 missing: {gem5}")
    if not binary.exists():
        return fail(f"workload missing: {binary}")

    # ---- census (countOnly) ----
    # [FR03] CHAOSPhysReg installs one permanent physical-cell fault; there
    # is no CHAOSFPU eligible-event stream to census. The census is skipped
    # EXPLICITLY (recorded on disk), never silently replaced by a zero.
    inj_component = str(
        (seed_manifest.get("injector") or {}).get("component", "fsu") or "fsu")
    physreg = (inj_component == "physreg")
    profile = str(seed_manifest.get("config_profile", "") or "")
    census_profile_check = None
    if physreg:
        eligible = 0
        census_cmd = []
        (attempt / "census_skipped.json").write_text(
            json.dumps({
                "status": "skipped",
                "reason": "physreg permanent-cell target has no "
                          "CHAOSFPU eligible-event census",
                "component": inj_component,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        census_dir = attempt / "census"
        census_cmd = build_cmd(seed_manifest, census_dir, seed, None, True,
                               gem5, Path(config), Path(root))
        rc, out, err, timed_out = runner(census_cmd, timeout)
        (attempt / "census.out").write_text(out, encoding="utf-8")
        (attempt / "census.err").write_text(err, encoding="utf-8")
        census_log = _read(census_dir / "fpu_injections.log")
        eligible = parse_eligible_count(census_log + "\n" + out + "\n" + err)
        if rc != 0 or timed_out or eligible < 0:
            return fail(f"census failed rc={rc} timed_out={timed_out} "
                        f"eligible={eligible}")
        if eligible == 0:
            return fail("eligible=0 (no FSU event in window) — not Masked")
        if profile == "B0":
            census_profile_check = CP.verify_config_profile(
                census_dir / "config.ini", "B0")
            if not census_profile_check["ok"]:
                return fail("config_profile_mismatch(census)",
                            {"config_profile_check": census_profile_check})

    # ---- F1/F2/F3 rate ordinals (deterministic; no probability proxy) ----
    rate_doc = None
    if rate_cfg is not None:
        rate_doc = O.build_rate_ordinals(
            eligible, rate_cfg["rate_divisor"], rate_cfg["jitter_pct"],
            seed, rate_cfg["warmup"])
        ord_path = attempt / "ordinals.json"
        ord_bytes = O.canonical_bytes(rate_doc)
        ord_path.write_bytes(ord_bytes)
        ord_sha = hashlib.sha256(ord_bytes).hexdigest()
        seed_manifest["rate"] = {
            **{k: rate_doc[k] for k in
               ("generator", "version", "rate_divisor", "jitter_pct",
                "seed", "warmup", "interval_bounds", "N",
                "injection_count", "first_ordinal", "last_ordinal")},
            "eligible_total": eligible,
            "ordinals": rate_doc["ordinals"],
            "intervals": rate_doc["intervals"],
            "ordinals_file": "ordinals.json",
            "ordinals_sha256": ord_sha,
        }
        (attempt / "manifest.json").write_text(
            json.dumps(seed_manifest, ensure_ascii=False, indent=2),
            encoding="utf-8")
        if not rate_doc["ordinals"]:
            # 确定性 ordinal 在 ROI 外：保留 attempt，不伪造注入、不计 3/3。
            note = {
                "status": "not_activated",
                "reason": "eligible_below_first_ordinal",
                "eligible_total": eligible,
                "first_interval_upper_bound": rate_doc["interval_bounds"]["hi"],
                "seed": seed,
                "rate_divisor": rate_doc["rate_divisor"],
                "jitter_pct": rate_doc["jitter_pct"],
                "warmup": rate_doc["warmup"],
                "ordinals_sha256": ord_sha,
            }
            (attempt / "not_activated.json").write_text(
                json.dumps(note, ensure_ascii=False, indent=2),
                encoding="utf-8")
            (attempt / ".not_activated").write_text(
                "not_activated/eligible_below_first_ordinal\n",
                encoding="utf-8")
            write_hashes(attempt)
            return {"status": "not_activated",
                    "reason": "eligible_below_first_ordinal",
                    "attempt": str(attempt), "eligible_total": eligible,
                    "first_interval_upper_bound":
                        rate_doc["interval_bounds"]["hi"],
                    "ordinals_sha256": ord_sha}

    skip = None if physreg else chaos_pick_skip(seed, eligible)

    # ---- injection ----
    inject_dir = attempt / "inject"
    inj_cmd = build_cmd(seed_manifest, inject_dir, seed, skip, False,
                        gem5, Path(config), Path(root), rate_doc=rate_doc)
    inj_cmd += ["--fsu_eligible_total", str(eligible)]
    rc, out, err, timed_out = runner(inj_cmd, timeout)
    # Copy a fixed-path array dump into the evidence dir (FR03 determinism:
    # the guest argv must not depend on the gate/formal outdir).
    fixed_dump = manifest.get("array_dump_path")
    if fixed_dump:
        src_dump = Path(str(fixed_dump))
        dst_dump = inject_dir / "array.bin"
        if src_dump.exists():
            shutil.copy2(src_dump, dst_dump)
    (attempt / "run.out").write_text(out, encoding="utf-8")
    (attempt / "run.err").write_text(err, encoding="utf-8")
    stats = _copy_stats(inject_dir, attempt)
    inject_profile_check = None
    if profile == "B0":
        inject_profile_check = CP.verify_config_profile(
            inject_dir / "config.ini", "B0")
        if not inject_profile_check["ok"]:
            return fail("config_profile_mismatch(inject)",
                        {"config_profile_check": inject_profile_check})
    # [FR03] CHAOSPhysReg writes `fault_injections.log` (its historical
    # name); CHAOSFPU writes `fpu_injections.log`. Reading only the FPU name
    # silently turned a real PhysReg injection into "0 faults".
    inj_log_path = inject_dir / "fpu_injections.log"
    if not inj_log_path.exists() and physreg:
        inj_log_path = inject_dir / "fault_injections.log"
    inj_log = _read(inj_log_path)
    faults = count_injections(inj_log)
    golden = manifest["workload"].get("golden") or \
        manifest["workload"].get("golden_id", "")
    oracle_kind = manifest["workload"].get("oracle_kind", "exact_hash")
    oracle_tol = int(manifest["workload"].get("oracle_tol", 0))
    category, reason = classify_run(
        out, err, rc, faults, golden, timed_out,
        oracle_kind=oracle_kind, oracle_tol=oracle_tol)
    oracle = {"category": category, "reason": reason, "faults_injected": faults,
              "eligible_count": eligible, "selection_seed": seed,
              "injection_seed": seed,
              "skip": (None if (rate_doc is not None or physreg)
                       else skip),
              "oracle_kind": oracle_kind, "golden": golden,
              "returncode": rc, "timed_out": timed_out}
    if rate_doc is not None:
        oracle.update({
            "rate_divisor": rate_doc["rate_divisor"],
            "jitter_pct": rate_doc["jitter_pct"],
            "interval_bounds": rate_doc["interval_bounds"],
            "warmup": rate_doc["warmup"],
            "expected_injections": rate_doc["injection_count"],
            "ordinals": rate_doc["ordinals"],
            "ordinals_sha256": seed_manifest["rate"]["ordinals_sha256"],
        })
    (attempt / "oracle.json").write_text(
        json.dumps(oracle, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- chain ----
    prop = inject_dir / "prop_evt.txt.gz"
    if prop.exists():
        chain = C.check_stream(prop, run_id=run_id, sample_run_id=f"s{seed}")
    else:
        chain = {"path": str(prop), "event_count": 0, "truncated": False,
                 "truncation_reason": "missing prop_evt", "identity_violations": [],
                 "faults": {}, "admitted_faults": []}
    # run-level oracle 与每个 fault 的 chain terminal 分开保存，绝不混写。
    fault_terminals = {fid: r.get("terminal")
                       for fid, r in chain.get("faults", {}).items()}
    chain_faults = chain.get("faults", {})
    rate_ok = (rate_doc is None
               or faults == rate_doc["injection_count"])
    # Every injected fault must have its own chain in the stream; an
    # injection log count larger than the stream's fault set is a missing
    # chain, not a pass.
    all_faults_present = len(chain_faults) == faults
    chain_report = {
        "run_id": run_id, "seed": seed, "sample_run_id": f"s{seed}",
        "attempt": k, "oracle": oracle,
        "run_level_oracle": {
            "category": category, "reason": reason,
            "faults_injected": faults,
            "eligible_count": eligible,
        },
        "rate": seed_manifest.get("rate"),
        "rate_ok": rate_ok,
        "expected_injections": (rate_doc["injection_count"]
                                if rate_doc is not None else None),
        "actual_injections": faults,
        "faults_in_stream": len(chain_faults),
        "all_faults_present": all_faults_present,
        "fault_terminals": fault_terminals,
        "chain": chain,
        "admitted": chain.get("admitted"),
        "certified": chain.get("certified"),
        "violations": chain.get("violations", []),
        "source_head": source_head, "gem5_sha256": binary_sha,
        "workload_sha256": seed_manifest["workload_sha256"],
        "config_profile": profile,
        "config_profile_fingerprint": (CP.fingerprint(profile) if profile
                                       else ""),
        "config_profile_check": (inject_profile_check
                                 or census_profile_check),
        "command": {"census": census_cmd, "inject": inj_cmd},
        "stats_nonempty": stats.exists() and stats.stat().st_size > 0,
        "prop_evt_exists": prop.exists(),
    }
    (attempt / "chain_report.json").write_text(
        json.dumps(chain_report, ensure_ascii=False, indent=2), encoding="utf-8")

    admitted = (
        category not in ("SimulatorError", "Inactive")
        and faults >= 1
        and rate_ok
        and all_faults_present
        and chain.get("admitted_faults")
        and chain.get("certified")
        and not chain.get("truncated")
        and chain_report["stats_nonempty"]
        and prop.exists()
    )

    # ---- seed Markdown + hashes ----
    doc_ok = False
    try:
        import fsu_seed_doc
        fsu_seed_doc.write_doc(attempt, seed_manifest, chain_report)
        doc_ok = (attempt / f"{run_id}-seed{seed}.md").exists()
    except Exception as e:  # doc generation must not hide the evidence
        (attempt / "doc_error.txt").write_text(repr(e) + "\n", encoding="utf-8")

    hashes = write_hashes(attempt)
    if admitted and doc_ok:
        (attempt / ".done").write_text("admitted\n", encoding="utf-8")
        if write_authoritative:
            auth.write_text(str(attempt), encoding="utf-8")
        md = attempt / f"{run_id}-seed{seed}.md"
        dst = None
        if copy_to_complete:
            dst = (Path(out_root) / "COMPLETE_PROPAGATION_PATHS" / run_id /
                   f"{run_id}-seed{seed}.md")
            dst.parent.mkdir(parents=True, exist_ok=True)
            if md.exists():
                shutil.copy2(md, dst)
        write_hashes(attempt)
        return {"status": "admitted", "attempt": str(attempt),
                "chain_terminal": _terminal(chain), "oracle": category,
                "md": str(dst) if dst is not None else str(md)}
    (attempt / ".failed").write_text(
        f"not admitted: oracle={category} faults={faults} "
        f"expected={chain_report['expected_injections']} rate_ok={rate_ok} "
        f"faults_in_stream={len(chain_faults)} "
        f"admitted_faults={chain.get('admitted_faults')} "
        f"truncated={chain.get('truncated')} "
        f"stats_nonempty={chain_report['stats_nonempty']} doc_ok={doc_ok}\n",
        encoding="utf-8")
    write_hashes(attempt)
    return {"status": "failed", "attempt": str(attempt), "oracle": category,
            "reason": reason, "faults": faults,
            "rate_ok": rate_ok,
            "expected_injections": chain_report["expected_injections"],
            "admitted_faults": chain.get("admitted_faults"),
            "truncated": chain.get("truncated")}


def _terminal(chain):
    for fid, r in sorted(chain.get("faults", {}).items()):
        if r.get("admitted"):
            return r.get("terminal")
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="FSU 单 seed 运行器")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-root", default=str(DEFAULT_OUT))
    ap.add_argument("--gem5", default=str(DEFAULT_GEM5))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--timeout", type=int, default=None)
    ap.add_argument("--allow-rerun", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = run_seed(Path(a.manifest), a.seed, Path(a.out_root),
                       Path(a.gem5), Path(a.root), timeout_s=a.timeout,
                       allow_rerun=a.allow_rerun)
    except S.ScopeError as e:
        print(json.dumps({"status": "rejected", "reason": str(e)},
                         ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["status"] in ("admitted", "already_admitted") else 1


if __name__ == "__main__":
    sys.exit(main())
