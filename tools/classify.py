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


# fail_count oracle (plan §4.5 oracle.kind=fail_count): some kernels
# (accum_kernel, cholesky_numeric) print "iters=N fails=M variant=..." to
# stderr. fails>0 = SDC (a mismatch vs golden recompute). Match the LAST
# fails= in the combined output.
_FAILS_RE = re.compile(r"fails\s*=\s*(\d+)")


def extract_fail_count(text):
    """Return the last 'fails=N' count in text, or -1 if none."""
    if not text:
        return -1
    m = _FAILS_RE.findall(text)
    return int(m[-1]) if m else -1


def _is_simerr(stderr):
    if not stderr:
        return False
    low = stderr
    return any(mk in low for mk in _SIMERR_MARKERS)


def classify_run(stdout, stderr, returncode, faults_injected,
                 golden_checksum, timed_out=False):
    """Classify one run per plan §9.1 (ordered). Returns the category string
    plus a short reason (for the evidence log)."""
    out = (stdout or "") + "\n" + (stderr or "")
    out_checksum = extract_checksum(out)
    simerr = _is_simerr(stderr)

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

    # 5/6. Program completed with a checksum: compare to golden.
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
# S0-3: protection-aware nine-class classification (plan §4.3, §6.5).
#
# The six-class classify_run() is the raw baseline. The nine-class extension
# splits Masked/SDC by the ECC outcome the injector reported in its log:
#   Corrected        : ECC corrected the fault (single-bit) — outcome == golden.
#                      (was Masked; now distinguished as "the protection worked")
#   DetectedContained : ECC detected but couldn't correct (2-bit) -> poisoned,
#                      contained (no propagation to arch output). A DUE that did
#                      NOT escape. (was Crash/Masked; now "detected+contained")
#   Latent           : >=3-bit (beyond SECDED) — undetected but the corrupted
#                      value is NOT yet consumed (overwritten before read).
#                      (was Masked; now "latent, not yet SDC")
#   SDC / Masked / Crash / Hang / Inactive / SimulatorError : unchanged.
#
# The injector reports the ECC outcome via a log line marker. This module
# parses it; the six-class path is the fallback when no marker is present
# (raw / protectionModel=none runs).
# ---------------------------------------------------------------------------

# Injector log markers (emitted by protection-aware injectors, plan §4.2).
_PA_MARKERS = {
    "Corrected":          ("EccCorrected", "Corrected:", "ECC-corrected"),
    "DetectedContained":  ("Poisoned:", "DetectedContained:", "poisoned"),
    "Latent":             ("Latent:", ">=3-bit", "beyond-SECDED"),
}


def _parse_pa_outcome(out_text):
    """Return the protection-aware outcome label from injector log text, or
    '' if no PA marker (raw run). First match wins (injector reports one)."""
    if not out_text:
        return ""
    for label, markers in _PA_MARKERS.items():
        if any(m in out_text for m in markers):
            return label
    return ""


def classify_run_pa(stdout, stderr, returncode, faults_injected,
                    golden_checksum, timed_out=False):
    """Protection-aware nine-class classifier (plan §4.3). Same ordered
    evaluation as classify_run, but splits Masked/SDC by the ECC outcome
    reported in the injector log. Returns (category, reason). When no PA
    marker is present, falls back to the six-class labels (raw run)."""
    out = (stdout or "") + "\n" + (stderr or "")
    out_checksum = extract_checksum(out)
    simerr = _is_simerr(stderr)

    if simerr:
        return ("SimulatorError",
                "gem5 panic/assert/SIGSEGV (tool failure) — run invalid")

    if timed_out and not out_checksum:
        return ("Hang", "exceeded Hang timeout, no checksum (control-flow "
                        "corruption: never completed)")

    crashed = (returncode != 0) or _is_arch_trap(stderr, stdout)
    pa = _parse_pa_outcome(out)  # ECC outcome from injector log

    # DetectedContained: ECC detected-but-uncorrectable (2-bit poison) that
    # did not escape — a contained DUE, distinct from Crash (which escaped).
    if crashed and pa == "DetectedContained":
        trap = _trap_reason(stderr, stdout)
        return ("DetectedContained",
                f"ECC detected+contained (poisoned, no escape) "
                f"{', ' + trap if trap else ''} — contained DUE")

    if crashed and not out_checksum:
        trap = _trap_reason(stderr, stdout)
        return ("Crash",
                f"workload trapped/crashed (exit={returncode}"
                f"{', ' + trap if trap else ''}) — DUE")

    if faults_injected == 0:
        return ("Inactive", "0 valid injections (target absent/invalid)")

    if not out_checksum:
        return ("SimulatorError",
                f"no checksum, exit={returncode}, no trap — ambiguous, invalid")

    if out_checksum == golden_checksum:
        # Split Masked by ECC outcome: Corrected (ECC worked) vs Latent
        # (>=3-bit undetected but not yet consumed) vs plain Masked (raw).
        if pa == "Corrected":
            return ("Corrected",
                    f"ECC corrected single-bit -> checksum==golden "
                    f"({out_checksum}) — protection worked")
        if pa == "Latent":
            return ("Latent",
                    f">=3-bit beyond SECDED, undetected but not consumed -> "
                    f"checksum==golden ({out_checksum}) — latent, not SDC")
        return ("Masked",
                f"completed checksum==golden ({out_checksum}) — fault did "
                f"not propagate")

    # checksum != golden (was SDC). A Latent that got consumed is now SDC.
    return ("SDC",
            f"completed checksum {out_checksum} != golden {golden_checksum} "
            f"— silent data corruption")


# Nine-class ordered list (plan §4.3, §6.5) for campaign tallies.
NINE_CLASSES = ["SimulatorError", "Hang", "Crash", "DetectedContained",
                "Inactive", "Corrected", "Latent", "Masked", "SDC"]

