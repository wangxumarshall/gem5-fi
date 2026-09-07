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

# Workload checksum = a standalone 16-hex line on its own (the kernels print
# FINAL=<16-hex> to stdout/stderr). Match the last such line in the combined
# output. Empty string if the program never printed one (Hang/Crash).
_CHECKSUM_RE = re.compile(r"^[0-9a-fA-F]{16}$", re.MULTILINE)

# gem5-side fatal markers (SimulatorError). These appear in stderr when gem5
# itself panics/asserts/segs fault — distinct from the workload trapping.
_SIMERR_MARKERS = ("panic", "Assertion", "SIGSEGV", "abort",
                   "fatal: ", "RuntimeError", "std::out_of_range",
                   "gem5 has encountered a segmentation fault")


def extract_checksum(text):
    """Return the last 16-hex standalone line in text, or '' if none."""
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
    if (faults_injected and faults_injected >= 1
            and returncode != 0 and not out_checksum):
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
