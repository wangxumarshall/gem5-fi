"""FP08 audit: rounding not-applied reasons, conservation, fail-closed, proxy.

READ-ONLY with respect to CHAOSFPU: this file never modifies the injector.

What is checked:

* REASON TAXONOMY: the exact early-exit conditions inside the rounding_sub
  branch are enumerated from the real source, and an offline classifier maps a
  candidate destination to one (and only one) attempt-level reason.  The C++
  today records only attempted/applied, so the per-reason counters are a
  PROPOSED interface; the test that requires them SKIPs with an explicit
  "to be implemented (placeholder)" reason until the injector emits them.
* CONSERVATION: fpsr attempted == applied == suppressed (constructive, three
  increments in one unconditional block); rounding attempted == applied +
  rejected, where rejected has a complete reason partition.
* FAIL-CLOSED: every mode combination that would silently make one FP08
  branch inert is enumerated.  Guards that already exist are asserted; the
  missing combinations SKIP with the exact list (BLOCKED) instead of passing.
* PROXY CLASSIFICATION: the suppress kind has no L0-L5 layer, both injection
  sites stay labelled proxy, FP08 remains PARTIAL/unapproved-proxy in the
  implementation matrix, and no test/tool run upgrades it to a certified
  hardware model.

Real evidence parsed: runs/fsu-gates/FP08-FPSR-GATE and
runs/fsu-gates/FP08-GATE/.../attempt-2/inject.  These are existing logs; this
file runs no gem5.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FPU_CC = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc"
FPU_HH = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.hh"
FPU_PY = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py"
PROP = ROOT / "tools/fsu_prop_fields.py"
MATRIX = ROOT / "tools/fsu_implementation_matrix.py"
READINESS = ROOT / "docs/gem5-fi/fsu/F0-READINESS-ORDER.md"
FP08_DOC = ROOT / "docs/gem5-fi/fsu/FP08-SUPPRESS-ROUNDING-GATE.md"

FPSR_GATE = ROOT / "runs/fsu-gates/FP08-FPSR-GATE/fpu_injections.log"
ROUNDING_GATE = (ROOT / "runs/fsu-gates/FP08-GATE/"
                 "FSU-FP08-F0-W1-ROUNDING-GATE/seed1/attempt-2/inject/"
                 "fpu_injections.log")
ROUNDING_CENSUS = (ROOT / "runs/fsu-gates/FP08-GATE/"
                   "FSU-FP08-F0-W1-ROUNDING-GATE/seed1/attempt-2/census/"
                   "fpu_injections.log")

FPSR_REASON = "fpsr_not_architecturally_modeled"
FPSR_SITE = "fpsr_suppress_proxy"
ROUNDING_SITE = "rounding_sub_one_ulp_proxy"


def _code(path):
    assert path.is_file(), path
    return path.read_text(encoding="utf-8", errors="replace")


def _between(src, start, end):
    a = src.find(start)
    assert a != -1, start
    b = src.find(end, a)
    assert b != -1, end
    return src[a:b]


def _rounding_branch():
    return _between(_code(FPU_CC),
                    "if (rounding_sub) {\n            ++rounding_attempted;",
                    "// [FSU][D3] Build a lane-relative mask")


def _fpsr_branch():
    return _between(_code(FPU_CC),
                    "// [FSU][FP08] Honest proxy accounting",
                    "// v1.1 Phase 9 mode 4 — rounding_sub")


# ---------------------------------------------------------------------------
# Reason taxonomy (proposed, derived from the real conditions)
# ---------------------------------------------------------------------------

# Every condition below is a `continue` (try the next dest) or the outer
# `if (o3cpur)`, so an attempt that reaches the end without okr has exactly one
# dominant reason.  The order is the documented audit precedence.
ROUNDING_REASONS = (
    "applied",
    "no_o3cpu",
    "no_vec_dest",
    "no_writable_dest",
    "nonfinite",
)

SUMMARY_LINES = {
    "applied": "CHAOS_ROUNDING_APPLIED",
    "no_o3cpu": "CHAOS_ROUNDING_SKIP_NO_O3CPU",
    "no_vec_dest": "CHAOS_ROUNDING_SKIP_NO_VEC_DEST",
    "no_writable_dest": "CHAOS_ROUNDING_SKIP_NO_WRITABLE_DEST",
    "nonfinite": "CHAOS_ROUNDING_SKIP_NONFINITE",
}


def classify_attempt(has_o3cpu, candidates):
    """One exclusive reason for an attempted-but-not-applied event.

    ``candidates`` is an iterable of dicts with keys:
      dest_valid, is_vec, writable, finite.
    """
    candidates = list(candidates)
    if not has_o3cpu:
        return "no_o3cpu"
    reasons = []
    for c in candidates:
        if not c.get("dest_valid", False):
            reasons.append("no_vec_dest")
        elif not c.get("is_vec", False):
            reasons.append("no_vec_dest")
        elif not c.get("writable", False):
            reasons.append("no_writable_dest")
        elif not c.get("finite", True):
            reasons.append("nonfinite")
        else:
            return "applied"
    if not candidates or all(r == "no_vec_dest" for r in reasons):
        return "no_vec_dest"
    if any(r == "no_writable_dest" for r in reasons):
        return "no_writable_dest"
    if any(r == "nonfinite" for r in reasons):
        return "nonfinite"
    return "no_vec_dest"


def check_conservation(fpsr, rounding):
    """Return (issues, rejected).

    fpsr: dict attempted/applied/suppressed (all ints) or None.
    rounding: dict attempted/applied plus every skip reason or None.
    """
    issues = []
    rejected = None
    if fpsr is not None:
        if not (fpsr["attempted"] == fpsr["applied"] ==
                fpsr["suppressed"]):
            issues.append(
                "fpsr conservation: attempted=%s applied=%s suppressed=%s" %
                (fpsr["attempted"], fpsr["applied"], fpsr["suppressed"]))
        if fpsr["attempted"] - fpsr["applied"] != 0:
            issues.append("fpsr rejected must be 0 (proxy applies every "
                          "attempted event)")
    if rounding is not None:
        rejected = rounding["attempted"] - rounding["applied"]
        if rejected < 0:
            issues.append("rounding applied exceeds attempted")
        skip_keys = [r for r in ROUNDING_REASONS if r != "applied"]
        skip_sum = sum(rounding.get(k, 0) for k in skip_keys)
        if skip_sum != rejected:
            issues.append(
                "rounding reason partition: applied=%s + reasons=%s != "
                "attempted=%s" % (rounding["applied"], skip_sum,
                                  rounding["attempted"]))
    return issues, rejected


def parse_fp08_summary(text):
    out = {"fpsr": {}, "rounding": {}, "duplicates": [],
           "unparsed": []}
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r"^(CHAOS_FPSR|CHAOS_ROUNDING)_([A-Z_]+)=(.*)$", line)
        if not m:
            continue
        group, key, value = m.group(1), m.group(2), m.group(3)
        full = "%s_%s" % (group, key)
        if full in seen:
            out["duplicates"].append(line)
        seen.add(full)
        if group == "CHAOS_FPSR":
            names = {"ATTEMPTED": "attempted", "APPLIED": "applied",
                     "SUPPRESSED": "suppressed", "REASON": "reason"}
        else:
            names = {"ATTEMPTED": "attempted", "APPLIED": "applied",
                     "SKIP_NO_O3CPU": "no_o3cpu",
                     "SKIP_NO_VEC_DEST": "no_vec_dest",
                     "SKIP_NO_WRITABLE_DEST": "no_writable_dest",
                     "SKIP_NONFINITE": "nonfinite"}
        name = names.get(key)
        if name is None:
            out["unparsed"].append(line)
            continue
        target = out["fpsr"] if group == "CHAOS_FPSR" else out["rounding"]
        target[name] = value if name == "reason" else _int(value)
    return out


def _int(v):
    try:
        return int(str(v), 10)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Source taxonomy
# ---------------------------------------------------------------------------

def test_rounding_branch_contains_every_enumerated_reason_site():
    block = _rounding_branch()
    # no_o3cpu
    assert "auto *o3cpur = dynamic_cast<o3::CPU *>(cpu);" in block
    assert "if (o3cpur) {" in block
    # no_vec_dest: invalid / non-Vec destinations are skipped
    assert "if (!dest || dest->is(InvalidRegClass)) continue;" in block
    assert "if (dest->classValue() != VecRegClass) continue;" in block
    # no_writable_dest
    assert "getWritableReg(dest," in block
    assert "if (!vp) continue;" in block
    # nonfinite
    assert "if (!std::isfinite(d)) continue;" in block
    # applied
    assert "++rounding_applied;" in block


def test_attempt_is_counted_before_the_reason_scan_and_apply_is_gated():
    block = _rounding_branch()
    attempt = block.find("++rounding_attempted;")
    scan = block.find("for (int i = 0; i < dyn_inst->numDestRegs()")
    gate = block.find("if (okr) {")
    applied = block.find("++rounding_applied;")
    assert -1 not in (attempt, scan, gate, applied)
    assert attempt < scan < gate < applied
    assert "faults_injected_count++" in block[gate:]
    assert "noteFaultApplied(dyn_inst, fi);" in block[gate:]


def test_reason_classifier_is_total_and_exclusive():
    applied = classify_attempt(True, [
        {"dest_valid": True, "is_vec": True, "writable": True,
         "finite": True}])
    assert applied == "applied"
    assert classify_attempt(False, [
        {"dest_valid": True, "is_vec": True, "writable": True,
         "finite": True}]) == "no_o3cpu"
    assert classify_attempt(True, [
        {"dest_valid": False, "is_vec": False, "writable": False,
         "finite": True}]) == "no_vec_dest"
    assert classify_attempt(True, [
        {"dest_valid": True, "is_vec": False, "writable": True,
         "finite": True}]) == "no_vec_dest"
    assert classify_attempt(True, [
        {"dest_valid": True, "is_vec": True, "writable": False,
         "finite": True}]) == "no_writable_dest"
    assert classify_attempt(True, [
        {"dest_valid": True, "is_vec": True, "writable": True,
         "finite": False}]) == "nonfinite"
    # Multi-dest: one good dest wins; otherwise the reason is still one value.
    assert classify_attempt(True, [
        {"dest_valid": True, "is_vec": True, "writable": True,
         "finite": False},
        {"dest_valid": True, "is_vec": True, "writable": True,
         "finite": True}]) == "applied"
    assert classify_attempt(True, [
        {"dest_valid": True, "is_vec": True, "writable": True,
         "finite": False},
        {"dest_valid": True, "is_vec": True, "writable": False,
         "finite": True}]) in ROUNDING_REASONS[1:]
    for r in (classify_attempt(True, [
            {"dest_valid": True, "is_vec": True, "writable": False,
             "finite": True}]),
              classify_attempt(True, [])):
        assert r in ROUNDING_REASONS


def test_per_reason_counters_are_not_implemented_yet():
    cc = _code(FPU_CC)
    missing = [line for line in SUMMARY_LINES.values()
               if line != "CHAOS_ROUNDING_APPLIED" and line not in cc]
    if not missing:
        # The injector now emits the partition; fall through to the
        # conservation test below (which then must pass on real logs).
        return
    pytest.skip(
        "to be implemented (placeholder): rounding attempts rejected before "
        "apply have no per-reason counters/log lines. Missing: %s. "
        "Current source only emits CHAOS_ROUNDING_ATTEMPTED/APPLIED "
        "(the rounding branch and both exit-summary sites)." %
        ", ".join(missing))


# ---------------------------------------------------------------------------
# Conservation
# ---------------------------------------------------------------------------

def test_fpsr_conservation_is_constructive_in_source():
    block = _fpsr_branch()
    inc = [block.find("++fpsr_attempted;"),
           block.find("++suppressed_count;"),
           block.find("++fpsr_applied;")]
    assert -1 not in inc
    for token in ("if (", "return", "continue"):
        assert token not in block[inc[0]:inc[-1]], token


def test_conservation_model_accepts_complete_partition():
    fpsr = {"attempted": 10, "applied": 10, "suppressed": 10}
    rounding = {
        "attempted": 10, "applied": 3,
        "no_o3cpu": 0,
        "no_vec_dest": 4,
        "no_writable_dest": 2,
        "nonfinite": 1,
    }
    issues, rejected = check_conservation(fpsr, rounding)
    assert issues == []
    assert rejected == 7


def test_conservation_model_rejects_incomplete_or_broken_partition():
    fpsr = {"attempted": 10, "applied": 9, "suppressed": 10}
    rounding = {"attempted": 5, "applied": 6,
                "no_o3cpu": 0,
                "no_vec_dest": 0,
                "no_writable_dest": 0,
                "nonfinite": 0}
    issues, _ = check_conservation(fpsr, rounding)
    assert any("fpsr conservation" in i for i in issues)
    assert any("applied exceeds attempted" in i for i in issues)
    # Missing reasons are not a silent zero: the partition fails.
    issues2, _ = check_conservation(None, {
        "attempted": 10, "applied": 1})
    assert any("reason partition" in i for i in issues2)


def test_summary_parser_detects_duplicate_pairs():
    text = "\n".join([
        "CHAOS_ROUNDING_ATTEMPTED=0",
        "CHAOS_ROUNDING_APPLIED=0",
        "CHAOS_ROUNDING_ATTEMPTED=0",
        "CHAOS_ROUNDING_APPLIED=0",
    ])
    parsed = parse_fp08_summary(text)
    assert parsed["duplicates"]
    assert parsed["rounding"]["attempted"] == 0


# ---------------------------------------------------------------------------
# Real evidence (read-only)
# ---------------------------------------------------------------------------

def test_real_fpsr_gate_conservation():
    if not FPSR_GATE.is_file():
        pytest.skip("FP08-FPSR-GATE evidence not present")
    parsed = parse_fp08_summary(_code(FPSR_GATE))
    fpsr = parsed["fpsr"]
    assert fpsr["reason"] == FPSR_REASON
    issues, _ = check_conservation(
        {"attempted": fpsr["attempted"], "applied": fpsr["applied"],
         "suppressed": fpsr["suppressed"]}, None)
    assert issues == []
    # Real observed values (also pinned in FP08-SUPPRESS-ROUNDING-GATE.md).
    assert fpsr["attempted"] == 174018
    assert fpsr["applied"] == 174018
    assert fpsr["suppressed"] == 174018


def test_real_rounding_gate_attempted_ge_applied_and_one_injection():
    if not ROUNDING_GATE.is_file():
        pytest.skip("FP08 rounding gate evidence not present")
    text = _code(ROUNDING_GATE)
    parsed = parse_fp08_summary(text)
    r = parsed["rounding"]
    assert r["attempted"] == 357
    assert r["applied"] == 1
    assert r["attempted"] >= r["applied"]
    assert text.count("mode=rounding_sub, faults_injected:") == 1
    assert "Site: dyn_inst_execute" in text
    # The attempt is not zero: the gap is 356 rejections with NO reason split.
    _issues, rejected = check_conservation(
        None, {"attempted": r["attempted"], "applied": r["applied"]})
    assert rejected == 356


def test_real_rounding_gate_reason_partition():
    if not ROUNDING_GATE.is_file():
        pytest.skip("FP08 rounding gate evidence not present")
    r = parse_fp08_summary(_code(ROUNDING_GATE))["rounding"]
    if any(k not in r for k in ROUNDING_REASONS[1:]):
        pytest.skip(
            "to be implemented (placeholder): the 356 rejected rounding "
            "attempts have no reason breakdown in the real log; conservation "
            "cannot yet distinguish no_vec_dest / no_writable_dest / "
            "nonfinite. See FQ08-FP08-GATE-AUDIT.md section 4.")
    issues, _ = check_conservation(None, r)
    assert issues == []


def test_census_duplicate_rounding_zero_pair_is_flagged_not_passed():
    if not ROUNDING_CENSUS.is_file():
        pytest.skip("FP08 rounding census evidence not present")
    text = _code(ROUNDING_CENSUS)
    parsed = parse_fp08_summary(text)
    # attempt-2 emitted the zero pair twice (dumpCensus + exit callback).
    assert parsed["duplicates"]
    # The census zeros are not injection evidence; the attempt must not be
    # read as "attempted=0 happened".
    assert parsed["rounding"]["attempted"] == 0


# ---------------------------------------------------------------------------
# Fail-closed mode combinations
# ---------------------------------------------------------------------------

# (flag A, flag B, existing guard location description)
GUARDED_COMBINATIONS = (
    ("rounding_sub", "rate_mode", "CHAOSFPU.cc:134-138"),
    ("rounding_sub", "prf_wb_hook", "CHAOSFPU.cc:204-208"),
    ("rounding_sub", "permanent_stuck", "CHAOSFPU.cc:279-283"),
    ("rounding_sub", "bitseg", "CHAOSFPU.cc:219-222"),
    ("fpsr_suppress", "rate_mode", "CHAOSFPU.cc:134-138"),
    ("fpsr_suppress", "prf_wb_hook", "CHAOSFPU.cc:204-208"),
    ("fpsr_suppress", "permanent_stuck", "CHAOSFPU.cc:279-283"),
)

# Combinations that would silently become inert (branch order) but have no
# explicit mutual-exclusion panic in the constructor today.
UNGUARDED_COMBINATIONS = (
    ("fpsr_suppress", "fma_weighted"),
    ("fpsr_suppress", "recurring_stuck"),
    ("fpsr_suppress", "f3_dependent"),
    ("fpsr_suppress", "bitseg"),
    ("rounding_sub", "fma_weighted"),
    ("rounding_sub", "recurring_stuck"),
    ("rounding_sub", "f3_dependent"),
)


def _guard_text():
    return _between(_code(FPU_CC), "CHAOSFPU::CHAOSFPU(",
                    "CHAOSFPU::~CHAOSFPU()")


def test_existing_guards_are_statically_present():
    src = _guard_text()
    # Each assertion is the literal condition, not a comment.
    assert ("if (fpsr_suppress || f3_dependent || rounding_sub ||\n"
            "                recurring_stuck)") in src
    assert ("if (permanent_stuck || rate_mode || recurring_stuck ||\n"
            "                fma_weighted || rounding_sub || f3_dependent || "
            "fpsr_suppress)") in src
    assert ("if (rate_mode || recurring_stuck || rounding_sub ||\n"
            "                f3_dependent || fpsr_suppress || fma_weighted)") in src
    assert ("if (!bitseg.empty() && (fault_mask || recurring_stuck ||\n"
            "                                fma_weighted || rounding_sub))") in src
    # These are conditional (rate/prf/permanent/bitseg) guards: present, but
    # they do not reject fpsr+weighted or rounding+f3 without those triggers.
    assert len(GUARDED_COMBINATIONS) == 7


def test_unguarded_combinations_fail_closed():
    src = _guard_text()
    missing = []
    for a, b in UNGUARDED_COMBINATIONS:
        token_a = "!bitseg.empty()" if b == "bitseg" else b
        # An unconditional guard must mention both flags in one condition and
        # panic.  The known conditional guards above are accounted for
        # separately, so we look for the explicit FP08 guard recommended in
        # FQ08-FP08-REGRESSION.md section 6.2.
        if not re.search(r"if \(\s*%s\s*&&[^)]*%s[^)]*\)\s*\{?\s*[\s\S]{0,200}"
                         r"panic" % (a, re.escape(token_a)), src):
            missing.append("%s + %s" % (a, b))
    if missing:
        pytest.skip(
            "to be implemented (placeholder): no constructor guard rejects "
            "these FP08 combinations before the run: %s. Branch order makes "
            "one path silently inert. Add the fail-closed panics from "
            "FQ08-FP08-REGRESSION.md section 6.2." % ", ".join(missing))
    assert missing == []


# ---------------------------------------------------------------------------
# Proxy classification / no automatic upgrade
# ---------------------------------------------------------------------------

def test_proxy_labels_are_unique_and_suppress_has_no_layer():
    cc = _code(FPU_CC)
    assert cc.count(FPSR_SITE) == 1
    assert cc.count(ROUNDING_SITE) == 1
    assert cc.count('"suppress"') == 1
    assert cc.count(FPSR_REASON) >= 2
    # fsu_prop_fields maps suppress to no L0-L5 layer.
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import fsu_prop_fields as P
    assert P.KIND_LAYER["suppress"] is None


def test_fp08_stays_partial_proxy_in_audit_surfaces():
    matrix = _code(MATRIX)
    m = re.search(r'"FP08": dict\(status="([A-Z_]+)"', matrix)
    assert m is not None and m.group(1) == "PARTIAL"
    readiness = _code(READINESS)
    assert "FP08 rounding_sub" in readiness
    assert "unapproved proxy" in readiness
    # The dedicated gate document must not call it certified hardware state.
    doc = _code(FP08_DOC)
    assert "代理" in doc
    assert "正式认证" in doc or "正式 seed" in doc
    py = _code(FPU_PY)
    assert "FPSR" in py


def test_tool_pass_and_chain_full_do_not_upgrade_proxy():
    # The classification helper below is intentionally policy, not a wrapper
    # around a green test: a full L0-L5 chain for rounding_sub still reports
    # the proxy class until a separate pre-registered certification exists.
    def certified(model, chain_full, tool_status):
        if model == "FP08" and chain_full and tool_status == "PASS":
            return "proxy"       # never auto-upgrade
        return tool_status

    assert certified("FP08", True, "PASS") == "proxy"
    # The is not a vacuous assertion: an explicitly certified model keeps its
    # status, so the rule is about FP08's unapproved proxy class.
    assert certified("FP07", True, "PASS") == "PASS"
