"""FP08 (fpsr_suppress / rounding_sub) contract tests — offline.

Scope of this file (no gem5 build, no simulation):

* SOURCE CONTRACT: exact assertions on CHAOSFPU.cc/.hh — which counters move,
  which event is emitted on each early-return path, and what the proxy
  boundary is.
* OUTPUT FORMAT: a parser + checker for the ``CHAOS_FPSR_*`` /
  ``CHAOS_ROUNDING_*`` exit lines, exercised with synthetic text that mirrors
  the REAL observed format (see docs/gem5-fi/fsu/FQ08-FP08-REGRESSION.md).

These tests do not prove a run happened.  Remaining real-simulation gaps are
listed in the same document; nothing here fabricates an injection.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_prop_fields as P  # noqa: E402

FPU_CC = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc"
FPU_HH = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.hh"
FPU_PY = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py"

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


def _fpsr_branch():
    # The comment is unique to the maybeCorrupt branch (the constructor and
    # the census/exit blocks do not carry it).
    return _between(_code(FPU_CC),
                    "// [FSU][FP08] Honest proxy accounting",
                    "// v1.1 Phase 9 mode 4 — rounding_sub")


def _rounding_branch():
    return _between(_code(FPU_CC),
                    "if (rounding_sub) {\n            ++rounding_attempted;",
                    "// [FSU][D3] Build a lane-relative mask")


# ---------------------------------------------------------------------------
# Output-format parser (synthetic text; NOT run evidence)
# ---------------------------------------------------------------------------

def parse_fp08_summary(text):
    """Parse CHAOS_FPSR_* / CHAOS_ROUNDING_* lines.

    Returns explicit None for missing keys and records duplicate lines (the
    real countOnly path emits the ROUNDING pair twice: once from dumpCensus
    and once from the startup exit callback).
    """
    fpsr_keys = {"ATTEMPTED": "attempted", "APPLIED": "applied",
                 "SUPPRESSED": "suppressed", "REASON": "reason"}
    rounding_keys = {"ATTEMPTED": "attempted", "APPLIED": "applied"}
    out = {"fpsr": {k: None for k in fpsr_keys.values()},
           "rounding": {k: None for k in rounding_keys.values()},
           "duplicates": [], "unparsed": []}
    seen = {}
    for line in text.splitlines():
        m = re.match(r"^CHAOS_FPSR_([A-Z_]+)=(.*)$", line.strip())
        if m:
            key, value = m.group(1), m.group(2)
            if key not in fpsr_keys:
                out["unparsed"].append(line.strip())
                continue
            field = fpsr_keys[key]
            if (("fpsr", field) in seen):
                out["duplicates"].append(line.strip())
            seen[("fpsr", field)] = True
            out["fpsr"][field] = value if field == "reason" else _int(value)
            continue
        m = re.match(r"^CHAOS_ROUNDING_([A-Z_]+)=(.*)$", line.strip())
        if m:
            key, value = m.group(1), m.group(2)
            if key not in rounding_keys:
                out["unparsed"].append(line.strip())
                continue
            field = rounding_keys[key]
            if (("rounding", field) in seen):
                out["duplicates"].append(line.strip())
            seen[("rounding", field)] = True
            out["rounding"][field] = _int(value)
    return out


def _int(value):
    try:
        return int(str(value), 10)
    except (TypeError, ValueError):
        return None


def check_fp08_summary(parsed, expect_fpsr=True, expect_rounding=True):
    """Offline conservation/boundary check of one parsed summary."""
    issues = []
    missing = []
    expected_reason = FPSR_REASON

    if expect_fpsr:
        f = parsed["fpsr"]
        for k in ("attempted", "applied", "suppressed"):
            if f[k] is None:
                missing.append("CHAOS_FPSR_%s" % k.upper())
        if f["reason"] is None:
            missing.append("CHAOS_FPSR_REASON")
        if None not in (f["attempted"], f["applied"], f["suppressed"]):
            if not (f["attempted"] == f["applied"] == f["suppressed"]):
                issues.append("fpsr conservation failed: attempted=%s "
                              "applied=%s suppressed=%s" %
                              (f["attempted"], f["applied"],
                               f["suppressed"]))
        if f["reason"] is not None and f["reason"] != expected_reason:
            issues.append("fpsr reason is not the proxy label: %r" %
                          (f["reason"],))

    if expect_rounding:
        r = parsed["rounding"]
        for k in ("attempted", "applied"):
            if r[k] is None:
                missing.append("CHAOS_ROUNDING_%s" % k.upper())
        if None not in (r["attempted"], r["applied"]):
            if r["applied"] > r["attempted"]:
                issues.append("rounding applied exceeds attempted: %s > %s" %
                              (r["applied"], r["attempted"]))

    if parsed["duplicates"]:
        issues.append("duplicate summary lines: %s" % parsed["duplicates"])
    if parsed["unparsed"]:
        issues.append("unparsed FP08 lines: %s" % parsed["unparsed"])
    return {"ok": not issues and not missing,
            "issues": issues, "evidence_missing": missing}


# ---------------------------------------------------------------------------
# Source contract: fpsr_suppress
# ---------------------------------------------------------------------------

def test_fpsr_counts_attempted_applied_suppressed_together():
    block = _fpsr_branch()
    assert "++fpsr_attempted;" in block
    assert "++suppressed_count;" in block
    assert "++fpsr_applied;" in block
    # The three increments are unconditional in the same block: by
    # construction attempted == applied == suppressed. There is no branch
    # between them.
    inc = [block.find("++fpsr_attempted;"),
           block.find("++suppressed_count;"),
           block.find("++fpsr_applied;")]
    assert -1 not in inc and inc == sorted(inc)
    between = block[inc[0]:inc[2]]
    for token in ("if (", "return", "continue"):
        assert token not in between, token


def test_fpsr_emits_one_suppress_event_with_reason_and_site():
    block = _fpsr_branch()
    assert 'emitFsu("suppress", 0, ~0ULL, kv);' in block
    assert '{"field", "fpsr_suppress"}' in block
    assert '{"attempted", "1"}' in block
    assert '{"applied", "1"}' in block
    assert '{"suppressed", "1"}' in block
    assert '{"reason", "%s"}' % FPSR_REASON in block
    assert '{"injection_site", "%s"}' % FPSR_SITE in block
    assert '{"hook_version", "1"}' in block
    assert '{"dyn_inst_seq", std::to_string(dyn_inst->seqNum)}' in block
    assert "return false;" in block
    # Proxy boundary: no architectural/PRF write and no budget consumption.
    for forbidden in ("getWritableReg", "setReg", "renameSrcReg", "memcpy",
                      "faults_injected_count++", "noteFaultApplied"):
        assert forbidden not in block, forbidden


def test_fpsr_boundary_is_explicitly_not_architectural_fpsr():
    cc = _code(FPU_CC)
    py = _code(FPU_PY)
    assert "fpsr_not_architecturally_modeled" in cc
    assert "no architectural" in cc or "not architecturally modeled" in cc
    assert "architecturally_modeled" in cc
    assert "FPSR" in py
    # fsu_prop_fields maps the suppress event to no L0-L5 layer.
    assert P.KIND_LAYER["suppress"] is None


# ---------------------------------------------------------------------------
# Source contract: rounding_sub
# ---------------------------------------------------------------------------

def test_rounding_counts_attempt_before_apply_and_only_on_success():
    block = _rounding_branch()
    attempt = block.find("++rounding_attempted;")
    okr = block.find("bool okr = false;")
    applied = block.find("++rounding_applied;")
    assert -1 not in (attempt, okr, applied)
    assert attempt < okr < applied
    # applied / budget / L0-L1 are inside `if (okr)`.
    gate = block.find("if (okr) {")
    assert gate != -1 and gate < applied
    assert "faults_injected_count++" in block[gate:]
    assert "noteFaultApplied(dyn_inst, fi);" in block[gate:]
    assert "return okr;" in block
    # Non-finite / no vector destination increments attempted only.
    assert "std::isfinite(d)" in block
    assert "dest->classValue() != VecRegClass" in block


def test_rounding_emits_real_l0_chain_with_proxy_site():
    block = _rounding_branch()
    assert 'fi.field = "rounding_sub";' in block
    assert 'fi.injection_site = "%s";' % ROUNDING_SITE in block
    assert 'fi.hook_version = "1";' in block
    assert "noteFaultApplied(dyn_inst, fi);" in block
    # noteFaultApplied is the L0 root + L1 carrier emitter.
    applied = _between(_code(FPU_CC), "CHAOSFPU::noteFaultApplied(",
                       "    // ------------------------------------------------------------------\n"
                       "    // [FSU][F5] Permanent stuck-at")
    assert 'emitFsu("fault_applied"' in applied
    assert 'emitFsu("carrier_state"' in applied
    # The early-return path also writes the injection log with the explicit
    # count, so log parsers see the same one injection.
    assert "mode=rounding_sub, faults_injected: " in block
    assert "fi.before = rbits;" in block
    assert "fi.after = robits;" in block
    assert "fi.mask = rbits ^ robits;" in block


def test_rounding_one_ulp_is_toward_the_opposite_neighbour():
    block = _rounding_branch()
    # LSB set -> move down; LSB clear -> move up. That is the opposite
    # neighbour of the current rounding direction (nearest).
    assert "std::nextafter(d, -std::numeric_limits<double>::infinity())" in block
    assert "std::nextafter(d,  std::numeric_limits<double>::infinity())" in block
    assert "(bits & 1)" in block


def test_rounding_boundary_is_fp64_lane64_offset0_vec_only():
    cc = _code(FPU_CC)
    assert ('if (rounding_sub && (precision != "fp64" || lane_width != 64 ||'
            in cc)
    assert 'lane_offset != 0))' in cc
    assert 'panic("CHAOSFPU: rounding_sub is FP64/lane64/offset0 only' in cc
    # Rate mode refuses the proxy (it bypasses the rate contract).
    assert "fpsr_suppress || f3_dependent || rounding_sub" in cc
    # PRF-WB hook and permanent_stuck refuse it too.
    assert "fma_weighted || rounding_sub || f3_dependent || fpsr_suppress" in cc
    assert "rounding_sub ||\n                f3_dependent || fpsr_suppress" in cc


# ---------------------------------------------------------------------------
# Conservation / independence / output completeness
# ---------------------------------------------------------------------------

def test_counters_are_distinct_members_and_independent():
    hh = _code(FPU_HH)
    for decl in ("uint64_t fpsr_attempted = 0;",
                 "uint64_t fpsr_applied = 0;",
                 "uint64_t rounding_attempted = 0;",
                 "uint64_t rounding_applied = 0;",
                 "uint64_t suppressed_count = 0;"):
        assert decl in hh, decl
    fpsr = _fpsr_branch()
    rounding = _rounding_branch()
    assert "rounding_" not in fpsr
    assert "fpsr_" not in rounding
    # suppressed_count is written ONLY by the fpsr placeholder.
    assert _code(FPU_CC).count("++suppressed_count;") == 1
    # The budget counter belongs to the real rounding application only.
    assert "faults_injected_count++" in rounding
    assert "faults_injected_count++" not in fpsr


def test_exit_summary_emits_all_fields_in_both_paths():
    cc = _code(FPU_CC)
    census = _between(cc, "CHAOSFPU::dumpCensus(",
                      "bool\n    CHAOSFPU::inWindow")
    for field in ("CHAOS_FPSR_ATTEMPTED=", "CHAOS_FPSR_APPLIED=",
                  "CHAOS_FPSR_SUPPRESSED=", "CHAOS_FPSR_REASON=",
                  "CHAOS_ROUNDING_ATTEMPTED=", "CHAOS_ROUNDING_APPLIED="):
        assert field in census, field
    assert FPSR_REASON in census
    # The injection pass has its own exit callback (the destructor only runs
    # dumpCensus in countOnly mode).
    callback = _between(cc, "if (fpsr_suppress || rounding_sub) {",
                        "// [FSU][D3] Honest decode-rejection accounting")
    for field in ("CHAOS_FPSR_ATTEMPTED=", "CHAOS_FPSR_APPLIED=",
                  "CHAOS_FPSR_SUPPRESSED=", "CHAOS_FPSR_REASON=",
                  "CHAOS_ROUNDING_ATTEMPTED=", "CHAOS_ROUNDING_APPLIED="):
        assert field in callback, field
    assert "registerExitCallback" in callback


def test_summary_parser_accepts_real_format_and_checks_conservation():
    text = "\n".join([
        "CHAOS_FPSR_ATTEMPTED=174018",
        "CHAOS_FPSR_APPLIED=174018",
        "CHAOS_FPSR_SUPPRESSED=174018",
        "CHAOS_FPSR_REASON=%s" % FPSR_REASON,
        "CHAOS_ROUNDING_ATTEMPTED=357",
        "CHAOS_ROUNDING_APPLIED=1",
    ])
    parsed = parse_fp08_summary(text)
    res = check_fp08_summary(parsed)
    assert res["ok"] is True, res
    assert parsed["fpsr"]["attempted"] == 174018
    assert parsed["rounding"]["applied"] == 1


def test_summary_parser_fails_closed_on_broken_conservation():
    text = "\n".join([
        "CHAOS_FPSR_ATTEMPTED=10",
        "CHAOS_FPSR_APPLIED=9",
        "CHAOS_FPSR_SUPPRESSED=10",
        "CHAOS_FPSR_REASON=%s" % FPSR_REASON,
        "CHAOS_ROUNDING_ATTEMPTED=5",
        "CHAOS_ROUNDING_APPLIED=6",
    ])
    res = check_fp08_summary(parse_fp08_summary(text))
    assert res["ok"] is False
    assert any("conservation" in i for i in res["issues"])
    assert any("applied exceeds attempted" in i for i in res["issues"])


def test_summary_parser_reports_missing_evidence_and_duplicates():
    only_rounding_twice = "\n".join([
        "CHAOS_ROUNDING_ATTEMPTED=0",
        "CHAOS_ROUNDING_APPLIED=0",
        "CHAOS_ROUNDING_ATTEMPTED=0",
        "CHAOS_ROUNDING_APPLIED=0",
    ])
    parsed = parse_fp08_summary(only_rounding_twice)
    res = check_fp08_summary(parsed, expect_fpsr=False)
    assert res["ok"] is False
    assert any("duplicate" in i for i in res["issues"])
    # Missing FPSR fields are evidence_missing, never a silent pass.
    res2 = check_fp08_summary(parse_fp08_summary(""), expect_fpsr=True,
                              expect_rounding=True)
    assert res2["ok"] is False
    assert "CHAOS_FPSR_ATTEMPTED" in res2["evidence_missing"]
    assert "CHAOS_ROUNDING_APPLIED" in res2["evidence_missing"]


def test_wrong_reason_string_is_rejected():
    text = "\n".join([
        "CHAOS_FPSR_ATTEMPTED=1",
        "CHAOS_FPSR_APPLIED=1",
        "CHAOS_FPSR_SUPPRESSED=1",
        "CHAOS_FPSR_REASON=fpsr_architectural",
        "CHAOS_ROUNDING_ATTEMPTED=1",
        "CHAOS_ROUNDING_APPLIED=1",
    ])
    res = check_fp08_summary(parse_fp08_summary(text))
    assert res["ok"] is False
    assert any("proxy label" in i for i in res["issues"])


# ---------------------------------------------------------------------------
# Early-return path inventory
# ---------------------------------------------------------------------------

def test_early_return_event_contract_inventory():
    cc = _code(FPU_CC)
    body = _between(cc, "CHAOSFPU::maybeCorrupt(",
                    "    // ------------------------------------------------------------------\n"
                    "    // [FSU][FR07-HOOK v2] Real PRF writeback-data boundary.")
    # Pre-eligibility exits emit nothing and are not accounted as attempts.
    assert "if (!isFpOpClass(oc)) return false;" in body
    assert "if (count_only) {" in body
    # The two FP08 early proxies are the only paths AFTER the gate that do
    # not fall through to the common PRF mask/injection block:
    #   fpsr -> explicit `suppress` event, no fault budget;
    #   rounding -> noteFaultApplied + explicit budget + L0/L1.
    assert 'emitFsu("suppress"' in body
    assert "noteFaultApplied(dyn_inst, fi);" in body
    # The "no writable dest" exit is honest but has no per-event reason
    # counter outside F5/rate; recorded as an evidence gap in the doc.
    assert "return false;  // no FP/vector dest register on this inst" in body


def test_no_other_path_reuses_the_fp08_sites_or_reason():
    cc = _code(FPU_CC)
    assert cc.count("fpsr_suppress_proxy") == 1
    assert cc.count("rounding_sub_one_ulp_proxy") == 1
    assert cc.count('"suppress"') == 1
    assert cc.count(FPSR_REASON) >= 2   # event + exit summary (+ comment)
