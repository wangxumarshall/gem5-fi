#!/usr/bin/env python3
"""Shared result classifier for the ARM64 CHAOS SDC campaign (plan §9.1).

Mutually-exclusive, ORDERED classification. The order matters: a
SimulatorError (gem5 itself crashed) must be caught BEFORE looking at the
program output, and a Hang (timeout, no completion) before SDC/Masked.

Report issue #4 (docs/gem5-fi_branch_next_step.md §三.4): the old runner
and the p0_* scripts NEVER checked the program exit code — a run that
crashed (exit!=0) with empty stdout but 1 logged injection was silently
labeled SDC. Also no Hang-vs-Crash split (no timeout distinction). This
module is the honest, shared fix.

Categories (plan §9.1, in evaluation order):
  SimulatorError : gem5 itself failed (panic/assert/SIGSEGV/abort in
                   stderr, OR gem5 exited non-zero WITHOUT producing a
                   valid program checksum = the tool/sim broke, not the
                   program). NOT a valid FI outcome.
  Crash          : the WORKLOAD crashed/trapped under the fault — gem5
                   reported an arch trap (illegal instruction, SError,
                   data/prefetch abort, etc.) OR the program exit code
                   is non-zero (e.g. killed by signal). A real DUE.
  Hang           : the simulation exceeded the Hang timeout (frozen ROI *
                   multiplier, plan §13.2) with NO program checksum —
                   the fault corrupted control flow so the program never
                   completed. Distinguished from Crash by exit/timeout
                   (Hang = timeout with no trap; Crash = trap/exit!=0).
  Inactive       : 0 valid injections (target absent/invalid at trigger,
                   or XZR discard). The fault did not land.
  Masked         : program completed normally (exit 0) AND its checksum
                   == golden — the fault landed but did not propagate.
  SDC            : program completed normally (exit 0) AND checksum !=
                   golden — silent data corruption (no detection).

Usage:
  from classify import classify_run
  cls = classify_run(stdout, stderr, returncode, faults_injected,
                      golden_checksum, timed_out=False)
"""
import re

# Workload checksum = a 16-hex value, either a standalone line (reg_chain
# style) or FINAL=<16-hex> prefixed (the v1.1 Phase 10/11 kernels:
# spec_leak_probe / stencil_5pt / stream_triad print "FINAL=<hex>"; found
# when the stream_triad DRAM pilot classified a REAL SDC run as
# SimulatorError 'no program checksum' — the regex never matched the
# prefixed form). Match the LAST occurrence in the combined output.
_CHECKSUM_RE = re.compile(r"^(?:FINAL=)?([0-9a-fA-F]{16})$", re.MULTILINE)

# gem5-side fatal markers (SimulatorError). These appear in stderr when gem5
# itself panics/asserts/segs fault — distinct from the workload trapping.
_SIMERR_MARKERS = ("panic", "Assertion", "SIGSEGV", "abort",
                   "fatal: ", "RuntimeError", "std::out_of_range",
                   "gem5 has encountered a segmentation fault")


def extract_checksum(text):
    """Return the last 16-hex value (standalone or FINAL=-prefixed line),
    or '' if none."""
    if not text:
        return ""
    m = _CHECKSUM_RE.findall(text)
    return m[-1] if m else ""


# ---------------------------------------------------------------------------
# v1.1 Phase 8.1 non-hash oracles (task_plan §Phase 8.1 / design doc §1.7).
# The exact_hash oracle (16-hex FINAL checksum) folds the whole workload
# output into ONE word — a reduction kernel hides WHERE the fault landed and
# an FP kernel's last-bit rounding differences are indistinguishable from
# real SDC. The per-element kernels print richer self-describing lines:
#
#   ARRAYHASH=<64hex>   — hash over the full output array (array_hash oracle;
#                         compares to the golden run's array hash)
#   ELEMDIFF n=<count> first=<idx> maxulp=<n>
#                       — per-element diff against a golden array
#                         (per_element_diff oracle; count>0 -> SDC, and
#                         first/maxulp are carried into the reason)
#   ULP=<max_ulp_error> — max ULP error over the output array (fp_ulp oracle;
#                         > tol -> SDC, <= tol -> Masked even if the bits are
#                         not exactly equal — a rounding-level difference
#                         within tolerance is NOT corruption)
#
# Regexes match the LAST such line in the combined output (kernels may print
# progress lines; the final one is the oracle line).
_ARRAYHASH_RE = re.compile(r"ARRAYHASH=([0-9a-fA-F]{64})")
_ELEMDIFF_RE = re.compile(
    r"ELEMDIFF n=(\d+) first=(-?\d+) maxulp=(\d+)")
_ULP_RE = re.compile(r"ULP=(\d+)")


def extract_arrayhash(text):
    """Return the last ARRAYHASH=<64hex> value in text, or '' if none."""
    if not text:
        return ""
    m = _ARRAYHASH_RE.findall(text)
    return m[-1] if m else ""


def extract_elemdiff(text):
    """Return the last ELEMDIFF triple (n, first, maxulp) as ints, or None."""
    if not text:
        return None
    m = _ELEMDIFF_RE.findall(text)
    if not m:
        return None
    n, first, maxulp = m[-1]
    return (int(n), int(first), int(maxulp))


def extract_ulp(text):
    """Return the last ULP=<n> value in text as int, or None if none."""
    if not text:
        return None
    m = _ULP_RE.findall(text)
    return int(m[-1]) if m else None


def _is_simerr(stderr):
    if not stderr:
        return False
    low = stderr
    return any(mk in low for mk in _SIMERR_MARKERS)


def classify_run(stdout, stderr, returncode, faults_injected,
                 golden_checksum, timed_out=False, fs_mode=False,
                 oracle_kind="exact_hash", oracle_tol=0):
    """Classify one run per plan §9.1 (ordered). Returns the category string
    plus a short reason (for the evidence log).

    fs_mode (§3.2 Phase 5.4): the FS pipeline has NO workload checksum — the
    oracle is kernel survival. Ordered rules: kernel-panic/Oops markers ->
    Crash (DUE); gem5 panic/assert -> SimulatorError (tool); timeout ->
    Hang; clean exit with faults>=1 -> Masked (kernel absorbed the fault);
    clean exit with faults==0 -> Inactive.

    oracle_kind (v1.1 Phase 8.1, design doc §1.7): how the completed
    program's output is compared to the golden reference.
      exact_hash      — legacy 16-hex FINAL checksum (default; unchanged
                        behavior for ALL existing campaigns).
      array_hash      — ARRAYHASH=<64hex> line compared to golden_checksum
                        (which then carries the golden ARRAYHASH value).
      per_element_diff— ELEMDIFF n=<count> first=<idx> maxulp=<n> line;
                        count>0 -> SDC (first/maxulp into the reason),
                        count==0 -> Masked.
      fp_ulp          — ULP=<max_ulp_error> line; > oracle_tol -> SDC,
                        <= oracle_tol -> Masked (rounding-level differences
                        within tolerance are NOT corruption).
    All non-hash oracles run AFTER the SimulatorError/Hang/Crash/Inactive
    rules — the ordered §9.1 categories are unchanged; only the
    Masked-vs-SDC split at the end is oracle-specific."""
    # Normalize bytes (subprocess.TimeoutExpired.stdout/stderr may be bytes
    # even with text=True under some py versions) -> str.
    # Normalize bytes (subprocess.TimeoutExpired.stdout/stderr may be bytes
    # even with text=True under some py versions) -> str.
    def _s(x):
        if isinstance(x, bytes):
            return x.decode("utf-8", errors="replace")
        return x or ""
    stdout = _s(stdout)
    stderr = _s(stderr)
    out = stdout + "\n" + stderr
    out_checksum = extract_checksum(out)
    simerr = _is_simerr(stderr)

    # 0.4 argparse/usage failure guard: gem5's config script exiting with
    # code 2 is a Python argparse "unrecognized arguments" / usage error —
    # the simulation NEVER RAN (faults_injected==0). Treating it as Crash
    # let an entire invalid formal masquerade as "100% DUE" (lsqfwd formal,
    # runs/lsqfwd_formal_fwd: 384/384 exit=2 faults=0 classified Crash —
    # INVALID, kp920_proxy.py lacked --lsq_struct_mode). exit==2 with no
    # injection is ALWAYS a tool error.
    if returncode == 2 and not faults_injected:
        return ("SimulatorError",
                "config-script argparse/usage error (exit=2, simulation "
                "never ran, faults_injected=0) — tool failure, run invalid")

    # §3.2 FS pipeline classification (Phase 5.4): no SE checksum exists;
    # the oracle is kernel survival. gem5's own panic/assert is still a
    # tool error (simerr); the KERNEL's panic/Oops is the fault outcome.
    if fs_mode:
        kernel_died = ("Kernel panic" in out or "Kernel Oops" in out or
                       "internal error" in out.lower() and "Oops" in out)
        if simerr:
            return ("SimulatorError",
                    "gem5 panic/assert/SIGSEGV (tool failure) — run invalid")
        if kernel_died:
            return ("Crash",
                    "kernel panic/Oops under the fault (DUE per §3.2)")
        if timed_out:
            return ("Hang",
                    "FS run exceeded timeout — kernel wedged under the fault")
        if faults_injected >= 1:
            return ("Masked",
                    "kernel survived the injected fault (clean exit)")
        return ("Inactive", "no injection landed (window/target absent)")

    # 0.5 §2.2 RAT/freelist rename-inconsistency carve-out: a rename-map or
    # freelist fault breaks gem5 O3's internal rename consistency, which gem5
    # SE-mode reports as a panic/SIGSEGV (returncode<0, simerr markers in
    # stderr). The design doc §2.2 classifies RAT errors as Crash/DUE — the
    # rename-inconsistency is the EXPECTED fault outcome, NOT a tool failure.
    # Distinguish from a true SimulatorError (tool broke with NO injection):
    # if a fault DID land (faults_injected>=1) and the run died by signal /
    # panic with no clean program checksum, it's a Crash (rename-inconsistency
    # DUE). This prevents mis-labeling RAT-injection crashes as tool errors,
    # which would under-count method1's Crash-dominant outcome. E3 note: real
    # RTL handles rename-inconsistency via an arch trap; gem5 SE models it as
    # a simulator invariant (panic), so the gem5-panic IS the DUE manifestation.
    # OoO-track fix (2026-09-25, W8.1 Wave B): `not timed_out` guard — a
    # timeout SIGKILL is definitionally a Hang (rule 2: "Hang = timeout with
    # no trap; Crash = trap/exit!=0"), but a killed run arrives as
    # returncode<0 + no checksum + fault landed, so without the guard this
    # carve-out swallowed EVERY fault-landed timeout as Crash. Found on the
    # M2-gate D28 cells: destid_bitflip stalls a dependency forever → ROB
    # fills → no forward progress → 600s kill → mislabeled Crash; correct
    # outcome is Hang (TC'23 dependency-interception manifests as a stall on
    # the gem5 PRF model, not a fast architectural trap).
    if (faults_injected and faults_injected >= 1
            and returncode != 0 and not out_checksum
            and not timed_out):
        return ("Crash",
                f"gem5 panic/abort (exit={returncode}) with a fault landed "
                f"(faults_injected={faults_injected}) and no program checksum "
                f"— rename-inconsistency / fault-induced crash (DUE per §2.2), "
                f"NOT a tool failure (a true SimulatorError has faults_injected==0)")

    # 1. SimulatorError: the tool/simulator itself broke. This is NOT a valid
    #    FI outcome — it means the run is invalid (gem5 panic/assert/SIGSEGV).
    if simerr:
        return ("SimulatorError",
                "gem5 panic/assert/SIGSEGV in stderr (tool failure, not a "
                 "fault outcome) — run invalid")

    # 2. Hang: exceeded the Hang timeout with no program completion (no
    #    checksum). Distinguished from Crash: Hang = never finished (timeout),
    #    Crash = finished-but-trapped/exit!=0 (below).
    if timed_out and not out_checksum:
        return ("Hang",
                "exceeded Hang timeout with no program checksum "
                 "(control-flow corruption: never completed)")

    # 3. Crash: the workload trapped/aborted under the fault (gem5 reported
    #    an arch trap OR program exit code != 0), and no clean checksum.
    #    This is a real DUE (Detected Uncorrectable Error).
    #    NOTE: gem5 SE prints arch traps (illegal instruction, SError, abort)
    #    to stderr/stdout; a trap leaves no 16-hex FINAL line.
    crashed = (returncode != 0) or _is_arch_trap(stderr, stdout)
    if crashed and not out_checksum:
        # Distinguish from SimulatorError: here gem5 did NOT panic; the
        # WORKLOAD trapped (arch-level fault).
        trap = _trap_reason(stderr, stdout)
        return ("Crash",
                f"workload trapped/crashed (exit={returncode}"
                f"{', ' + trap if trap else ''}) — DUE")

    # 4. Inactive: 0 valid injections — the fault did not land.
    if faults_injected == 0:
        return ("Inactive",
                "0 valid injections (target absent/invalid at trigger, "
                "or XZR discard)")

    # 5/6. Program completed: apply the oracle (v1.1 Phase 8.1). The legacy
    # exact_hash path is byte-for-byte the old behavior; the non-hash kinds
    # only change HOW the completed output is compared to golden.
    if oracle_kind == "array_hash":
        # ARRAYHASH=<64hex> over the whole output array; golden_checksum
        # carries the golden run's array hash.
        ah = extract_arrayhash(out)
        if not ah:
            return ("SimulatorError",
                    f"no ARRAYHASH line, exit={returncode}, not timed out — "
                     f"oracle line missing, run invalid")
        if ah == golden_checksum:
            return ("Masked",
                    f"completed exit={returncode}, ARRAYHASH==golden "
                    f"({ah[:16]}...) — fault did not propagate")
        return ("SDC",
                f"completed exit={returncode}, ARRAYHASH {ah} != "
                f"golden {golden_checksum} — silent data corruption")

    if oracle_kind == "per_element_diff":
        # ELEMDIFF n=<count> first=<idx> maxulp=<n>: the kernel itself diffs
        # its output array against a golden copy; count>0 -> SDC.
        ed = extract_elemdiff(out)
        if ed is None:
            return ("SimulatorError",
                    f"no ELEMDIFF line, exit={returncode}, not timed out — "
                     f"oracle line missing, run invalid")
        n_diff, first, maxulp = ed
        if n_diff == 0:
            return ("Masked",
                    f"completed exit={returncode}, ELEMDIFF n=0 — every "
                    f"element matches the golden array")
        return ("SDC",
                f"completed exit={returncode}, ELEMDIFF n={n_diff} "
                f"first={first} maxulp={maxulp} — {n_diff} elements differ "
                f"from the golden array (first differing index {first}, "
                f"max ULP error {maxulp})")

    if oracle_kind == "fp_ulp":
        # ULP=<max_ulp_error>: max ULP distance over the output array.
        # > tol -> SDC; <= tol -> Masked (a rounding-level difference within
        # tolerance is NOT corruption — the exact_hash oracle would have
        # mis-counted it as SDC).
        ulp = extract_ulp(out)
        if ulp is None:
            return ("SimulatorError",
                    f"no ULP line, exit={returncode}, not timed out — "
                     f"oracle line missing, run invalid")
        if ulp <= oracle_tol:
            return ("Masked",
                    f"completed exit={returncode}, ULP={ulp} <= tol "
                    f"{oracle_tol} — within rounding tolerance")
        return ("SDC",
                f"completed exit={returncode}, ULP={ulp} > tol {oracle_tol} "
                f"— silent data corruption beyond rounding tolerance")

    # exact_hash (legacy default — unchanged behavior).
    if not out_checksum:
        # No checksum but not timed-out and exit 0 and not trapped: this is
        # an ambiguous/tool-error state — report honestly rather than guess.
        return ("SimulatorError",
                f"no program checksum, exit={returncode}, not timed out, "
                 f"no trap marker — ambiguous tool state, run invalid")

    if out_checksum == golden_checksum:
        return ("Masked",
                f"completed exit={returncode}, checksum==golden "
                f"({out_checksum}) — fault did not propagate")

    return ("SDC",
            f"completed exit={returncode}, checksum {out_checksum} != "
            f"golden {golden_checksum} — silent data corruption")


# gem5 SE-mode architecture-trap markers printed to stderr/stdout when the
# workload takes a fault (illegal instruction, SError, data/prefetch abort,
# etc.). These indicate the WORKLOAD crashed (Crash/DUE), not gem5.
_ARCH_TRAP_MARKERS = (
    "fatal: Unimplemented",          # arch inst not implemented
    "Instruction", "illegal instruction",
    "SError", "SError",
    "data abort", "Data Abort",
    "prefetch abort", "Prefetch Abort",
    "Abort", "abort",
    "Unknown instruction",
    "fault", "Fault",
    "signal", "Signal",
    " SIG",                            # killed by signal (e.g. SIGILL)
)


def _is_arch_trap(stderr, stdout):
    text = (stderr or "") + (stdout or "")
    # Require a program-level trap marker AND that gem5 did NOT itself panic
    # (the SimulatorError path already handled pure gem5 panics above). A trap
    # is a workload-level event gem5 reports and then exits non-zero OR prints
    # a 'Workload event' / 'exiting @' due to a fault.
    if not text:
        return False
    # gem5 SE reports traps via "warn: ... " or "Workload event" + non-zero
    # exit. The strongest signal is returncode != 0 (handled by caller's
    # `crashed` test); here we only add explicit trap-text detection for the
    # case where returncode is 0 but a trap was printed.
    return any(mk in text for mk in ("illegal instruction", "SError",
                                     "data abort", "prefetch abort",
                                     "Unknown instruction", "SIGILL",
                                     "SIGSEGV"))


def _trap_reason(stderr, stdout):
    text = (stderr or "") + (stdout or "")
    for mk in ("illegal instruction", "SError", "data abort",
               "prefetch abort", "Unknown instruction", "SIGILL",
               "SIGSEGV", "SIGABRT"):
        if mk in text:
            return f"trap:{mk}"
    return ""


# ---------------------------------------------------------------------------
# V2.0 L5 分类学层（implementation-plan.md Task WS3；两簿 04 表 L5 行）。
#
# 双轨期裁决（plan R10）：classify_run() 既有行为一字不动（V1.0 结果可复算，
# 九类 = tools/wilson.py:57-58 的有序全集）；classify_run_v2() 是其上的增量
# 映射层，两轨结果永不混表。
#
# V1.0 九类 → V2.0 L5 结局（SE 轨道）：
#   SimulatorError    → Simulator failure        不入任何架构结局分母
#   Inactive          → Injected-not-activated   不入 SDC 率分母（L0 口径：
#                                                reads_before_overwrite==0）
#   Masked            → Masked                   ─┐
#   Corrected         → Detected-contained        │ 五类结局（L5 守恒式右侧：
#   DetectedContained → Detected-contained        │ Activated = Masked +
#   SDC               → Data Corruption           │   Detected-contained + SDC +
#   Crash             → RAS-silent Crash          │   Crash + Timeout）
#   Hang              → RAS-silent Timeout       ─┘
#   Latent            → Latent                    报告列，不进结局五类
#   （无 V1 对应）     → Detected-uncontained      预留：检测到但未遏制——
#                                                V1 九类无法产生，只能由
#                                                检测器证据直接判定
#
# SE 轨道诚实取值：Crash/Hang 全部为 RAS-silent（SE 无硬件 RAS）；首检四类
# 无保护模型时为 "None"（程序正常完成、oracle 离线发现 SDC）或 "Application"
# （程序自检退出非零，归 Crash 之前）；ras_any 恒 False（B0 无 ECC/parity，
# 两簿 02 表「保护机制核验」行原文）。
V2_FIVE_OUTCOMES = ("Masked", "Detected-contained", "Data Corruption",
                    "RAS-silent Crash", "RAS-silent Timeout")
V2_OUTCOME_MAP = {
    "SimulatorError":    "Simulator failure",
    "Inactive":          "Injected-not-activated",
    "Masked":            "Masked",
    "Corrected":         "Detected-contained",
    "DetectedContained": "Detected-contained",
    "SDC":               "Data Corruption",
    "Crash":             "RAS-silent Crash",
    "Hang":              "RAS-silent Timeout",
    "Latent":            "Latent",
}
V2_FIRST_DETECTIONS = ("HW_RAS", "OS", "Application", "None")


def classify_run_v2(result_v1, *, first_detection=None, ras_any=False):
    """Map one V1.0 classify_run() result onto the V2.0 L5 taxonomy (SE track).

    result_v1: dict with at least {"category": <V1.0 九类之一>} — e.g.
      {"category": cat, "reason": reason} from wrapping classify_run()'s
      (category, reason) tuple. Anything else in the dict is carried
      untouched (the caller's per-run record stays whole).

    first_detection: the first detector of the fault, one of
      "HW_RAS" / "OS" / "Application"; None means no detector fired before
      the outcome was reached and maps to "None" (the honest SE value when
      the program completes and the offline oracle finds the SDC). Semantic
      consistency with the outcome is the CALLER's judgement; this layer
      only validates the enum (loud on typos).

    ras_any: whether a hardware RAS detected the fault at ANY point (not
      necessarily first). On the SE B0 track this is constantly False (no
      ECC/parity — both books' 02 protection-verification rows).

    Returns {"outcome", "first_detection", "ras_any", "in_denominator"}:
      in_denominator is True only for the five L5 outcome classes (the
      conservation-summands); Simulator failure / Injected-not-activated /
      Latent are excluded, matching the xlsx 结局计数差额 column semantics.
    """
    try:
        category = result_v1["category"]
    except (TypeError, KeyError):
        raise ValueError(
            f"result_v1 must be a dict with a 'category' key (wrap "
            f"classify_run()'s tuple), got: {result_v1!r}")
    if category not in V2_OUTCOME_MAP:
        raise ValueError(
            f"unknown V1.0 category {category!r} (expected one of "
            f"{sorted(V2_OUTCOME_MAP)}; Detected-uncontained has no V1 "
            f"counterpart — it needs detector evidence, not a mapping)")
    if first_detection is None:
        fd = "None"
    elif first_detection in V2_FIRST_DETECTIONS[:3]:  # HW_RAS / OS / Application
        fd = first_detection
    else:
        raise ValueError(
            f"first_detection must be one of {V2_FIRST_DETECTIONS[:3]} or "
            f"None, got {first_detection!r}")
    outcome = V2_OUTCOME_MAP[category]
    return {
        "outcome": outcome,
        "first_detection": fd,
        "ras_any": bool(ras_any),
        "in_denominator": outcome in V2_FIVE_OUTCOMES,
    }


def _selftest_v2():
    """--selftest-v2: 9 input classes × 1 case each + denominator gate."""
    cases = [
        ("SimulatorError", "gem5 panic (tool failure)"),
        ("Inactive", "0 valid injections"),
        ("Masked", "checksum==golden"),
        ("Corrected", "ECC-caught (protection model)"),
        ("DetectedContained", "detector contained the fault"),
        ("SDC", "checksum != golden"),
        ("Crash", "workload trapped"),
        ("Hang", "timeout, no completion"),
        ("Latent", "latent, reported outside the five"),
    ]
    assert len(cases) == 9 and {c for c, _ in cases} == set(V2_OUTCOME_MAP)
    seen_outcomes = set()
    for cat, reason in cases:
        r = classify_run_v2({"category": cat, "reason": reason})
        assert r["outcome"] == V2_OUTCOME_MAP[cat], (cat, r)
        assert r["outcome"] not in seen_outcomes or cat in (
            "Corrected", "DetectedContained"), cat  # only the pair may share
        seen_outcomes.add(r["outcome"])
        # 首检默认与 ras_any 默认（SE 诚实取值）
        assert r["first_detection"] == "None" and r["ras_any"] is False, r
        # denominator gate: 只对五类结局为真
        expect = V2_OUTCOME_MAP[cat] in V2_FIVE_OUTCOMES
        assert r["in_denominator"] is expect, (cat, r)
    # Detected-uncontained：V1 九类不可达（预留，需检测器证据）
    assert "Detected-uncontained" not in V2_OUTCOME_MAP.values()
    assert "Detected-uncontained" not in V2_FIVE_OUTCOMES
    # 未知类必须响亮报错（不得静默归类）
    for bad in ("Detected-uncontained", "sdc", ""):
        try:
            classify_run_v2({"category": bad})
            raise AssertionError(f"unknown category {bad!r} not rejected")
        except ValueError:
            pass
    # 非法首检值必须响亮报错；合法三值 + None 全通
    try:
        classify_run_v2({"category": "SDC"}, first_detection="hw_ras")
        raise AssertionError("bad first_detection not rejected")
    except ValueError:
        pass
    for fd in ("HW_RAS", "OS", "Application"):
        r = classify_run_v2({"category": "Crash"}, first_detection=fd,
                            ras_any=(fd == "HW_RAS"))
        assert r["first_detection"] == fd and r["ras_any"] == (fd == "HW_RAS")
    # reason 等额外字段不丢（调用方记录保持完整）
    r = classify_run_v2({"category": "SDC", "reason": "x", "run_id": "A01-F0-W3"})
    assert r["outcome"] == "Data Corruption"
    print("V2 taxonomy selftest PASS (9 mappings, denominator gate OK)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest-v2":
        _selftest_v2()
    else:
        print("usage: classify.py --selftest-v2", file=sys.stderr)
        sys.exit(2)
