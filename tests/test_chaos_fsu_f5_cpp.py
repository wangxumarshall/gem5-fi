"""Host-side verification of the [FSU][F5] CHAOSFPU implementation.

Two layers, both without a gem5 build (the host is under heavy load):

1. Compile and run tests/unit/chaos_fsu_f5_test.cc with g++ -O0. The header
   is pure standard C++, so the stuck-at semantics are tested for real.
2. Static wiring checks over CHAOSFPU.hh/.cc/.py: the five new parameters
   exist, the F5 path uses applyStuck/stuckActivated (never XOR), and the
   install is the only place that mints a new fault_id.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tests/unit/chaos_fsu_f5_test.cc"
INCLUDE = ROOT / "CHAOS/gem5/src"
FPU = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU"


def test_chaos_fsu_f5_unit(tmp_path):
    exe = tmp_path / "chaos_fsu_f5_test"
    compile_cmd = [
        "g++", "-O0", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-I", str(INCLUDE), str(SRC), "-o", str(exe),
    ]
    r = subprocess.run(compile_cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"compile failed:\n{r.stdout}\n{r.stderr}"
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 0, f"unit test failed:\n{run.stdout}\n{run.stderr}"
    assert "all checks passed" in run.stdout


def test_f5_python_params_exist():
    text = (FPU / "CHAOSFPU.py").read_text(encoding="utf-8")
    for name in ("permanentStuck", "stuckPolarity", "f5Warmup",
                 "f5SampleLimit", "f5KeepFirstLastN"):
        assert re.search(rf"^\s*{name}\s*=\s*Param\.", text, re.M), name


def test_f5_header_declares_one_install_and_bounded_samples():
    text = (FPU / "CHAOSFPU.hh").read_text(encoding="utf-8")
    for name in ("notePermanentExposure", "registerF5Taint",
                 "flushF5Samples", "emitF5ChainEnd",
                 "f5_last_samples", "f5_exposures_total",
                 "f5_exposures_sampled", "f5_exposures_dropped"):
        assert name in text, name


def test_f5_cc_uses_forced_polarity_not_xor():
    text = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    assert "chaos_fsu::applyStuck(" in text
    assert "chaos_fsu::stuckActivated(" in text
    # The F5 lane write must be guarded by permanent_stuck and call
    # applyStuck; the legacy XOR must remain the non-F5 branch only.
    assert re.search(
        r"lane_after\s*=\s*permanent_stuck\s*\?\s*"
        r"chaos_fsu::applyStuck\(", text)
    assert re.search(
        r"lane_after\s*=\s*permanent_stuck\s*[\s\S]{0,160}"
        r":\s*lane_before\s*\^\s*mi\.lane_mask", text)


def test_f5_install_is_the_only_new_fault_site():
    text = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    # one allocation in noteFaultApplied (non-F5 path), one at F5 install.
    assert text.count("next_fault_id++") == 2
    assert 'emitFsu("fault_installed"' in text
    assert 'emitFsu("exposure"' in text
    # The F5 branch must call notePermanentExposure, never noteFaultApplied
    # per exposure (that would mint a fault_id per event).
    assert re.search(
        r"if\s*\(permanent_stuck\)\s*\{[\s\S]{0,600}"
        r"notePermanentExposure\(dyn_inst, info\);", text)
    # noteFaultApplied is the NON-F5 branch only; the F5 path reaches it
    # zero times, so it must occur exactly once in the source call site.
    assert text.count("noteFaultApplied(dyn_inst, info);") == 1


def test_f5_chain_end_reports_capacity():
    text = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    assert '"exposures_total"' in text
    assert '"exposures_sampled"' in text
    assert '"exposures_dropped"' in text
    assert '"sample_policy"' in text
    assert 'emitFsu("chain_end"' in text


ACCOUNTING_FIELDS = (
    "eligible_seen_total", "warmup_configured", "warmup_eligible_skipped",
    "install_eligible_ordinal", "install_is_exposure",
    "post_install_eligible", "eligible_without_writable_dest",
    "selected_eligible_total", "eligible_delta_vs_census",
    "census_reference",
)


def test_f5_install_and_chain_end_emit_eligible_accounting():
    text = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    for name in ACCOUNTING_FIELDS:
        assert f'"{name}"' in text, name
    # The install snapshot is built once, before the L0 root is emitted, and
    # the same helper is reused on chain_end (single arithmetic source).
    assert "appendF5Accounting(kv, true);" in text
    assert "appendF5Accounting(kv, false);" in text
    assert text.index("appendF5Accounting(kv, true);") < \
        text.index('emitFsu("fault_installed"')
    # Install is exposure #1 and carries its own eligible ordinal/warm-up.
    assert "f5_install_eligible_ordinal = eligible_ordinal;" in text
    assert "f5WarmupEligibleSkipped(" in text
    # Matched eligible events with no writable destination are counted, not
    # silently dropped from the eligible accounting.
    assert "++f5_eligible_without_writable_dest;" in text
    # The census is a reference, not a required equality: only the delta
    # arithmetic is emitted and checked.
    assert "pre_registered_countOnly" in text
    assert "eligible_delta_vs_census" in text


def test_f5_event_budget_panics_loudly():
    text = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    assert "chaos_fsu::f5ResolveSampleBudget(" in text
    assert "budget.within_cap" in text
    assert re.search(
        r"if\s*\(!budget\.within_cap\)[\s\S]{0,220}panic\(", text)
    # The pure arithmetic helper is header-only and unit-tested.
    hh = (FPU / "chaos_fsu_fields.hh").read_text(encoding="utf-8")
    assert "F5_AUDITABLE_BUDGET = 190000" in hh
    assert "F5_EVENT_CAP = 200000" in hh
    assert "f5ResolveSampleBudget" in hh


def test_f5_samples_are_deduplicated_by_exposure_id():
    hh = (FPU / "CHAOSFPU.hh").read_text(encoding="utf-8")
    cc = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    assert "std::set<uint64_t> f5_sampled_exposure_ids;" in hh
    assert "markF5Sample(f5_exposures_total)" in cc
    assert "markF5Sample(sample.exposure_id)" in cc
    assert cc.count("++f5_exposures_sampled;") == 1   # only inside markF5Sample
    for name in ("sampled_unique", "omitted", "applied_to_all_exposures",
                 "sampled_is_observation_only"):
        assert f'"{name}"' in cc, name


def test_f5_l2_carries_bounded_multi_source_summary():
    hh = (FPU / "CHAOSFPU.hh").read_text(encoding="utf-8")
    cc = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    assert "f5_cell_sources" in hh and "f5_cell_sources" in cc
    assert "F5_MAX_CELL_SOURCES" in hh
    assert "noteF5CellActivation(" in cc
    assert "f5_cell_sources.erase(cs);" in cc
    for name in ("merged_activated_exposures", "observed_exposure_ids",
                 "sources_expanded", "sources_unexpanded",
                 "observation_scope", "cell_sources_overflow"):
        assert f'"{name}"' in cc, name
    assert '"observation_scope",' in cc
    assert "first_activated_chain" in cc
    # The summary hangs off the L2 operand_read event.
    idx = cc.index('emitFsu("operand_read"')
    assert cc.index('"merged_activated_exposures"') < idx


def test_f5_terminal_flush_runs_before_tracer_close():
    cc = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    # The injector's terminal events are registered on the tracer's late
    # flush hook (not a global exit callback whose order is construction-
    # order dependent).
    assert "registerExitFlush(" in cc
    assert "flushF5Samples(); emitF5ChainEnd();" in cc
    assert "registerExitCallback([this]() { emitF5ChainEnd(); })" not in cc
    # The first activated exposure is emitted IN-RUN (never deferred to the
    # tail buffer), so its L2-L5 chain exists before the tracer closes.
    assert re.search(
        r"if\s*\(first_exposure \|\| first_activated\)\s*\{\s*"
        r"action = F5_EMIT_NOW;", cc)

    prop = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                  "CHAOSPropagation.cc").read_text(encoding="utf-8")
    hook = prop.index("for (auto &hook : exit_flush_hooks)")
    evt_close = prop.index("gzclose(evt_gz_file);", hook)
    raw_close = prop.index("gzclose(gz_file);", hook)
    assert hook < evt_close, "injector flush must run before the evt gzclose"
    assert hook < raw_close, "injector flush must run before the raw gzclose"


def test_f5_new_event_fields_are_registered():
    # notePropEvt DROPS unknown keys; every newly emitted F5 field must be in
    # the injector-facing allowlist or the evidence would silently vanish.
    hh = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
                 "CHAOSPropagation.hh").read_text(encoding="utf-8")
    for name in ACCOUNTING_FIELDS + (
            "sampled_unique", "omitted", "applied_to_all_exposures",
            "sampled_is_observation_only", "merged_activated_exposures",
            "observed_exposure_ids", "sources_expanded",
            "sources_unexpanded", "observation_scope",
            "cell_sources_overflow"):
        assert f'"{name}"' in hh, name
