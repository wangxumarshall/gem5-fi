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
