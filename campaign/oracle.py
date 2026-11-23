#!/usr/bin/env python3
"""Semantic oracle parsing for WHEN-5X3 terminal lines.

The workload prints one W*_RESULT line per episode (W9/W10S/W11–W14).  An SDC
is a change in the *software-visible result*, so the oracle comparison must be
over the correctness-relevant fields (``observed``, ``expected``, ``result``,
``signal``, ``fault_class``, ``fault_addr``, ``value_ok``,
``injected_success``, ``branch``, permission status), never over the runtime
identity fields (``target_pfn`` / ``decoy_pfn`` / ``target_va`` /
``decoy_va`` / ``alias_va`` / ``pid`` / ``pagemap`` / ``pfn_ok``) which vary
with the guest's physical-page allocation and must not, on their own, trigger
an SDC verdict.
"""
import re

ORACLE_RE = re.compile(r"^W(?:9|10S|1[0-4])_(?:RESULT|SUMMARY|STORE)\b")

# correctness-relevant fields used for the semantic SDC comparison
SEMANTIC_KEYS = (
    "observed", "expected", "result", "signal", "fault_class", "fault_addr",
    "value_ok", "injected_success", "branch", "sentinel", "decoy_sentinel",
    "observed_kind", "si_code", "fault_code_ok", "shared_changed", "msg",
    "phase", "ctx",
)
# runtime identity fields that must NOT, on their own, trigger an SDC verdict
IDENTITY_KEYS = (
    "target_pfn", "decoy_pfn", "target_va", "decoy_va", "alias_va",
    "pid", "pagemap", "pfn_ok", "pte_present",
)


def oracle_lines(term):
    """Return the W*_RESULT/SUMMARY/STORE lines from a terminal line list."""
    return [ln for ln in (term or []) if ORACLE_RE.match(ln)]


def parse_line(line):
    """Parse a key=value line into a dict (values kept as strings)."""
    out = {}
    for tok in line.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out


def semantic_signature(line):
    """Canonical correctness signature for one oracle line.

    The leading ``Wnn_RESULT`` token and every ``SEMANTIC_KEYS`` field are
    kept; runtime identity fields are dropped so an SDC is never inferred from
    a physical-page-number / VA / pid difference alone."""
    if not line:
        return ()
    head = line.split()[0] if line.split() else line
    d = parse_line(line)
    parts = [head]
    for k in SEMANTIC_KEYS:
        if k in d:
            parts.append("%s=%s" % (k, d[k]))
    return tuple(parts)


def semantic_oracle(term):
    """Sorted list of semantic signatures for a run's oracle lines."""
    return sorted(semantic_signature(ln) for ln in oracle_lines(term))


def semantic_compare(fault_term, ctrl_term):
    """True when the fault and control oracles are semantically identical."""
    return semantic_oracle(fault_term) == semantic_oracle(ctrl_term)


def result_field(line):
    d = parse_line(line)
    return d.get("result", "")


def observed_field(line):
    d = parse_line(line)
    return d.get("observed", "")


def actual_value_from_fail(term):
    """The observed value of the FAIL episode, if any, else the last observed.

    Multi-episode W13 runs interleave PASS (0x7d) and FAIL (0x51) episodes; the
    fault's ActualValue is the observed of a FAIL episode (or CRASH/TIMEOUT),
    never the first PASS episode."""
    lines = oracle_lines(term)
    for ln in lines:
        if result_field(ln) == "FAIL":
            return observed_field(ln)
    for ln in reversed(lines):
        if result_field(ln) in ("CRASH", "TIMEOUT"):
            return observed_field(ln)
    for ln in lines:
        o = observed_field(ln)
        if o:
            return o
    return ""


def exit_signal_from(term):
    """Signal number of the first terminal line that reports one."""
    for ln in oracle_lines(term):
        d = parse_line(ln)
        if d.get("signal") not in (None, "", "0"):
            return d["signal"]
    return "0"


def episodes(term):
    """Return a list of per-episode dicts (observed, expected, result)."""
    out = []
    for ln in oracle_lines(term):
        d = parse_line(ln)
        out.append({
            "observed": d.get("observed", ""),
            "expected": d.get("expected", ""),
            "result": d.get("result", ""),
            "signal": d.get("signal", ""),
            "fault_class": d.get("fault_class", ""),
            "injected_success": d.get("injected_success", ""),
            "value_ok": d.get("value_ok", ""),
        })
    return out
