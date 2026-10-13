#!/usr/bin/env python3
"""[OOO][P1] ooo_observation unit test (plan Task 5).

All fixtures are hand-inlined (NO gem5 dependency): decode success/skip
log lines in the exact shape of the 2026-10-12 real runs, a bad-tail
gzip (crashed-run trace), conservation positives/negatives, the
chain_completeness three states, and the SDC-vs-checksum consistency
rule. Run: python3 tools/tests/test_ooo_observation.py
"""
import gzip
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
import ooo_observation as om

FAILURES = []
CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


# verbatim decode success line (real run, /tmp/man-a70h4p0y 2026-10-12)
DECODE_SUCCESS = (
    "Tick: 423115, Site: fetch_decode, mode=reg_bitflip, pc=0x4195f0, "
    "orig_enc=0xf900dfe0, new_enc=0xf900dfe4, bits=[2], orig_mnemonic=str, "
    "new_mnemonic=str, regs_moved=1, macroop_new=0, faults_injected: 1\n")

# decode skip-then-success (D04-c src_swap shapes on the fixed binary;
# marker contract per tools/tests/test_faults_log_contract.py)
DECODE_SKIP_THEN_SUCCESS = (
    "Tick: 531685, Site: fetch_decode, mode=src_swap, pc=0x40c21c, "
    "orig_mnemonic=ldr — not a two-int-src data-proc format (skipped, "
    "no injection), faults_injected: 0\n"
    "Tick: 531686, Site: fetch_decode, mode=src_swap, pc=0x40c220, "
    "orig_enc=0x8b010041, new_enc=0x8b020021, rn=2->1, rm=1->2, "
    "orig_mnemonic=add, new_mnemonic=add, faults_injected: 1\n")

# post-fix r0068 RAT skip-only log (verbatim from the log-contract test)
RAT_SKIP_ONLY = (
    "Tick: 10102785, Site: rename_setEntry, mode=map_bitflip2_adj, "
    "class=vec, tid=0, arch=V0, old_phys=44, bits=(3,4) — flipped idx 52 "
    "out of [0,48) (skipped, no clamp), faults_injected: 0\n"
    "Tick: 10757285, Site: rename_setEntry, mode=map_bitflip2_adj, "
    "class=vec, tid=0, arch=V2, old_phys=44, bits=(3,4) — flipped idx 52 "
    "out of [0,48) (skipped, no clamp), faults_injected: 0\n")

ELIGIBLE_LOG = (
    "CHAOS_ELIGIBLE_COUNT=42\n" + DECODE_SUCCESS)


def wtmp(text, name="decode_injections.log"):
    d = tempfile.mkdtemp(prefix="obs-test-")
    p = os.path.join(d, name)
    with open(p, "w") as f:
        f.write(text)
    return d, p


def test_parse_injection_log():
    # 1. decode success line: injected=1, event carries the row fields
    d, p = wtmp(DECODE_SUCCESS)
    r = om.parse_injection_log(d, "decode")
    check("decode-success-injected", r["injected"] == 1, r)
    check("decode-success-one-event", len(r["events"]) == 1)
    ev = r["events"][0]
    check("decode-success-tick", ev["tick"] == 423115, ev)
    check("decode-success-site", ev["site"] == "fetch_decode", ev)
    check("decode-success-pc", ev["pc"] == "0x4195f0", ev)
    check("decode-success-orig-enc", ev["orig_enc"] == "0xf900dfe0", ev)
    check("decode-success-new-enc", ev["new_enc"] == "0xf900dfe4", ev)
    check("decode-success-bits", ev["bits"] == "[2]", ev)
    check("decode-success-raw", "faults_injected: 1" in ev["raw"])
    check("decode-success-no-skips", len(r["skips"]) == 0)
    # [FIX-A Task 1] real per-line funnel counts (semantics change per the
    # central fix-A mandate; the old pin was attempted is None):
    # 1 injection line, 0 skip lines -> attempted=1, eligible=1
    check("decode-success-attempted", r["attempted"] == 1, r["attempted"])
    check("decode-success-eligible", r["eligible"] == 1, r["eligible"])
    # eligible_count stays None: CHAOSDecode never writes a
    # CHAOS_ELIGIBLE_COUNT= line (only CHAOSLSQFwd/CHAOSExec do)
    check("decode-success-eligible-count-none", r["eligible_count"] is None)

    # 2. skip-then-success: marker-wins (injected=1), one event, one skip
    d, p = wtmp(DECODE_SKIP_THEN_SUCCESS)
    r = om.parse_injection_log(d, "decode")
    check("skipthen-injected", r["injected"] == 1, r)
    check("skipthen-events", len(r["events"]) == 1 and
          r["events"][0]["pc"] == "0x40c220", r["events"])
    check("skipthen-skips", len(r["skips"]) == 1 and
          r["skips"][0]["pc"] == "0x40c21c", r["skips"])
    # [FIX-A Task 1] funnel: 1 skip + 1 injection line were inspected;
    # only the injection line wrote a fault
    check("skipthen-attempted", r["attempted"] == 2, r["attempted"])
    check("skipthen-eligible", r["eligible"] == 1, r["eligible"])

    # 3. skip-only RAT log: injected=0, two skips, activated side = 0
    d, p = wtmp(RAT_SKIP_ONLY, name="rename_injections.log")
    r = om.parse_injection_log(d, "rat")
    check("rat-skips-injected", r["injected"] == 0, r)
    check("rat-skips-count", len(r["skips"]) == 2, r)
    check("rat-skips-no-events", len(r["events"]) == 0, r)
    check("rat-skip-bits-parens", r["skips"][0]["bits"] ==
          "(3,4) — flipped idx 52 out of [0,48) (skipped, no clamp)",
          r["skips"][0])
    check("rat-skip-class", r["skips"][0]["class"] == "vec", r["skips"][0])
    # [FIX-A Task 1] skip-only log: 2 events inspected, 0 faults written
    check("rat-skips-attempted", r["attempted"] == 2, r["attempted"])
    check("rat-skips-eligible", r["eligible"] == 0, r["eligible"])

    # 4. eligible count line is honored when present
    d, p = wtmp(ELIGIBLE_LOG)
    r = om.parse_injection_log(d, "decode")
    check("eligible-count", r["eligible_count"] == 42, r)

    # 5. direct-file path form and unknown component loudness
    r = om.parse_injection_log(p, "decode")
    check("direct-file-parse", r["injected"] == 1)
    try:
        om.parse_injection_log(d, "nosuchcomp")
        check("unknown-component-raises", False)
    except ValueError:
        check("unknown-component-raises", True)

    # 5b. missing log: no source -> attempted/eligible are honest None,
    # never a silent 0 (module honesty contract)
    d2 = tempfile.mkdtemp(prefix="obs-nolog-")
    r = om.parse_injection_log(d2, "decode")
    check("nolog-exists-false", r["log_exists"] is False, r)
    check("nolog-injected-zero", r["injected"] == 0, r)
    check("nolog-attempted-none", r["attempted"] is None, r)
    check("nolog-eligible-none", r["eligible"] is None, r)

    # 6. physreg-style marker-less log: runner counting rules (line count)
    d, p = wtmp("Cycle: 1000, PhysReg[12] (int) bit 3 flipped\n"
                "ReadTracePoll: t=1000\n"
                "Cycle: 2000, PhysReg[13] (int) bit 1 flipped\n",
                name="fault_injections.log")
    r = om.parse_injection_log(d, "physreg")
    check("physreg-line-count", r["injected"] == 2, r)
    check("physreg-poll-excluded", len(r["events"]) == 2, r)
    check("physreg-attempted", r["attempted"] == 2, r["attempted"])
    check("physreg-eligible", r["eligible"] == 2, r["eligible"])


def _ctrace_line(seq, tick, val="0000000000000000"):
    # seq,tid,tick,pc,op,ndest,class,arch,phys,val
    return "%d,0,%d,4195f0,add,1,1,5,12,%s" % (seq, tick, val)


def test_truncated_passthrough_and_l2_status():
    """A crashed run's gzip (no trailer) must yield an honest salvaged
    prefix; the clean prefix is never evidence of no divergence."""
    import commit_diff
    d = tempfile.mkdtemp(prefix="obs-trunc-")
    ref = os.path.join(d, "ref.csv.gz")
    run = os.path.join(d, "run.csv.gz")
    lines = [_ctrace_line(i, 1000 + i) for i in range(200)]
    with gzip.open(ref, "wt") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(d, "run.full"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(d, "run.full"), "rb") as f:
        blob = f.read()
    gz = gzip.compress(blob)
    # cut the gzip trailer + tail of the deflate stream (crash mid-write)
    with open(run, "wb") as f:
        f.write(gz[: int(len(gz) * 0.7)])
    cd = commit_diff.compare(ref, run, 0)
    check("trunc-run-truncated-flag", cd["run_truncated"] is True, cd)
    check("trunc-verdict", cd["verdict"] == "truncated_no_divergence_in_prefix",
          cd["verdict"])
    st = om.l2_status_from(cd, "Crash")
    check("trunc-crash-status", st == "not_observed_before_crash", st)

    # truncated BUT the salvaged prefix HAS a divergence -> status ok,
    # truncated flag passed through inside l2.commit_diff
    d2 = tempfile.mkdtemp(prefix="obs-trunc2-")
    bad = []
    for i in range(200):
        val = "deadbeefdeadbeef" if i == 5 else "0000000000000000"
        bad.append(_ctrace_line(i, 1000 + i, val))
    ref2 = os.path.join(d2, "ref.csv.gz")
    run2 = os.path.join(d2, "run.csv.gz")
    with gzip.open(ref2, "wt") as f:
        f.write("\n".join(lines) + "\n")
    gz2 = gzip.compress(("\n".join(bad) + "\n").encode())
    with open(run2, "wb") as f:
        f.write(gz2[: int(len(gz2) * 0.7)])
    cd2 = commit_diff.compare(ref2, run2, 0)
    check("trunc-div-run-truncated", cd2["run_truncated"] is True, cd2)
    check("trunc-div-has-divergence", cd2["first_divergence"] is not None
          and cd2["primary_class"] == "data_corruption", cd2["primary_class"])
    st2 = om.l2_status_from(cd2, "Crash")
    check("trunc-div-status-ok", st2 == "ok", st2)
# probe line

    # error / inactive semantics of the status derivation
    check("l2-error-status", om.l2_status_from(None, "Masked") == "error")
    errdict = dict(l2_error="x")
    check("l2-l2error-status",
          om.l2_status_from(errdict, "Masked") == "error")
    cleandict = dict(verdict="no_divergence", run_truncated=False,
                     first_divergence=None)
    check("l2-clean-status",
          om.l2_status_from(cleandict, "Masked") == "ok")


def test_conservation():
    # positive: activated=1 + Masked=1 -> conserved
    c = om.conservation_for(1, "Masked")
    check("cons-masked-ok", c["activated"] == 1 and c["masked"] == 1
          and c["conserved"] is True, c)
    # plan-schema keys (C audit reads .ok); per-class counts kept
    check("cons-schema-ok-key", c["ok"] is True, c)
    check("cons-schema-five-sum", c["five_primary_sum"] == 1, c)
    check("cons-schema-notes", isinstance(c["notes"], str), c)
    # negative: activated=1 but classification Inactive (five-outcome sum 0)
    c = om.conservation_for(1, "Inactive")
    check("cons-inactive-bad", c["activated"] == 1 and c["conserved"] is False
          and sum(c[k] for k in om.FIVE_MAIN_OUTCOMES) == 0, c)
    # activated=0 + Inactive -> conserved
    c = om.conservation_for(0, "Inactive")
    check("cons-inactive-zero", c["conserved"] is True, c)
    # SDC / Crash / Hang buckets
    c = om.conservation_for(1, "SDC")
    check("cons-sdc", c["sdc"] == 1 and c["conserved"] is True, c)
    c = om.conservation_for(1, "Crash")
    check("cons-crash", c["crash"] == 1 and c["conserved"] is True, c)
    c = om.conservation_for(1, "Hang")
    check("cons-hang", c["hang"] == 1 and c["conserved"] is True, c)
    # SimulatorError with a landed fault -> post_activation bucket
    c = om.conservation_for(1, "SimulatorError")
    check("cons-post-activation-simerr",
          c["post_activation_simulator_failure"] == 1
          and c["conserved"] is True, c)
    # SimulatorError with no fault -> plain invalid run, conserved at 0
    c = om.conservation_for(0, "SimulatorError")
    check("cons-simerr-zero",
          c["post_activation_simulator_failure"] == 0
          and c["conserved"] is True, c)
    # vocabulary drift is loud
    c = om.conservation_for(1, "NotAClass")
    check("cons-unknown-loud", c["conserved"] is False, c)
    check("cons-unknown-ok-false", c["ok"] is False, c)
    # SimulatorError-with-activation notes the exclusion from the 385
    c = om.conservation_for(1, "SimulatorError")
    check("cons-simerr-note", "385" in c["notes"], c["notes"])


def make_identity():
    ident = dict(
        run_id="obs-test-c0000-r0000", campaign_id="obs-test",
        runid_row="D01-F0-W6-c", submodel="decode", sample_index=0,
        phase="formal", seed=20261012, manifest_sha256="0" * 64,
        gem5_sha256="1a618953b014514713c0ad98c7f3d69a48171d81f0463d9"
                    "34bccdfcfc0070bf3",
        config=dict(path="configs/se/ooo_proxy.py",
                    sha256="0b9e18cb3932cc8d3f0067165117aa33d0fccb967d"
                           "ddad17c79b62a23395a8346"),
        workload=dict(path="workloads/ooo/smoke/smoke",
                      sha256="30cd303815735206e697df0163887bceecec2388a26"
                             "d22cfc27a4dc8cb98e85d",
                      golden_id="smoke-golden-v1"),
        golden_key="9859154dd47e7e734bbb27a7",
        chaos_commit="58d26fe", patchset_sha256="n/a", pythonhashseed=0,
        host="huawei0201", started="2026-10-12T17:30:00",
        finished="2026-10-12T17:30:05", wall_s=5.0)
    return ident


def make_ctx(classification, injected, component="decode",
             l1_status="ok", l2_status="ok", l3=None, l4_status="ok"):
    """A minimal but structurally complete ctx for build_observation."""
    if classification == "Masked":
        checksum_obs = "45737cc9a76c0dce"
    elif classification == "SDC":
        checksum_obs = "ffffffffffffffff"
    else:
        checksum_obs = ""
    l0 = dict(status="ok", component=component,
              log_name=om.LOG_FOR_COMPONENT.get(component, "n/a"),
              log_sha256="0" * 64, injected=injected,
              activated=injected,
              eligible_count=None, attempted=None, events=[], skips=[],
              skip_lines=0, truncated=False)
    l1 = dict(status=l1_status, micro_diff=dict(no_divergence=True),
              first_divergence=None, files=dict())
    l2 = dict(status=l2_status,
              coverage=dict(mode="full", seq_lo=None, seq_hi=None,
                            note="test"),
              commit_diff=dict(verdict="no_divergence", run_truncated=False,
                               first_divergence=None),
              first_divergent_commit=None, files=dict())
    if l3 is None:
        l3 = dict(status="unsupported", method=None, fanout=None,
                  caveat=None,
                  reason="commit trace records dest regs only; "
                         "source-read association not implemented for "
                         + component)
    l4 = dict(status=l4_status,
              first_detection=dict(kind=None, detector=None, tick=None,
                                   seq=None, note=""),
              latency_from_l0=dict(ticks=None, committed_insts=None,
                                   note=""),
              oracle=dict(kind="exact_hash", golden="45737cc9a76c0dce",
                          observed=checksum_obs or None,
                          match=(checksum_obs == "45737cc9a76c0dce")))
    l5 = dict(classification=classification, reason="test fixture",
              exit=0, timed_out=False, faults_injected=injected,
              checksum_observed=checksum_obs or None,
              checksum_golden="45737cc9a76c0dce", detector=None,
              conservation=None)
    ctx = dict(identity=make_identity(), l0=l0, l1=l1, l2=l2, l3=l3,
               l4=l4, l5=l5, files=dict(),
               coverage_scope=dict(mode="full", seq_lo=None, seq_hi=None,
                                   full_trace_lines=1, kept_lines=1,
                                   pruned=False, note="test"),
               audit=dict(built_at="2026-10-12T17:31:00",
                          builder_sha256="0" * 64))
    return ctx


def test_chain_completeness_three_states():
    # (a) decode activated sample -> L3 unsupported -> gap ["L3"]
    obs = om.build_observation(make_ctx("Masked", 1, component="decode"))
    check("chain-decode-incomplete", obs["chain_complete"] is False)
    check("chain-decode-gap-l3", obs["chain_gaps"] == ["L3"],
          obs["chain_gaps"])
    check("chain-decode-no-violations", obs["violations"] == [],
          obs["violations"])
    # (b) physreg activated sample with l3 ok+proxy -> complete
    l3proxy = dict(status="ok", method="proxy", fanout=dict(n_writes=3),
                   caveat="source-side reads are not recorded in the commit "
                          "trace; the liveness window is an upper-bound "
                          "proxy for consumer reads")
    obs = om.build_observation(
        make_ctx("Masked", 1, component="physreg", l3=l3proxy))
    check("chain-physreg-complete", obs["chain_complete"] is True,
          obs["chain_gaps"])
    check("chain-physreg-no-gaps", obs["chain_gaps"] == [], obs["chain_gaps"])
    # (c) inactive sample: L1-L4 all inactive_no_activation -> complete
    obs = om.build_observation(
        make_ctx("Inactive", 0, l1_status="inactive_no_activation",
                 l2_status="inactive_no_activation",
                 l4_status="inactive_no_activation"))
    obs["l3"] = dict(status="inactive_no_activation")
    obs = om.build_observation(obs)
    check("chain-inactive-complete", obs["chain_complete"] is True,
          obs["chain_gaps"])
    # (d) crash sample: l1 truncated (PARTIAL observation -- some snaps
    # were taken before the crash) stays chain-acceptable for Crash, but
    # l2 not_observed_before_crash is NOT chain-completeness evidence
    # ([FIX-A Task 2] central mandate: the status is honest -- it is not
    # a violation -- yet absence of observation must not count as a
    # completed L2 link), so the gaps are L2 + the L3 rule
    l3crash = dict(status="unsupported", reason="decode has no L3")
    obs = om.build_observation(
        make_ctx("Crash", 1, component="decode", l1_status="truncated",
                 l2_status="not_observed_before_crash", l3=l3crash,
                 l4_status="ok"))
    check("chain-crash-gaps-l2-l3", obs["chain_gaps"] == ["L2", "L3"],
          obs["chain_gaps"])
    check("chain-crash-incomplete", obs["chain_complete"] is False)
    check("chain-crash-l2-passthrough",
          obs["l2"]["status"] == "not_observed_before_crash")
    check("chain-crash-not-a-violation", obs["violations"] == [],
          obs["violations"])


def test_validate_rules():
    # SDC but checksum == golden -> violation
    ctx = make_ctx("SDC", 1)
    ctx["l5"]["checksum_observed"] = "45737cc9a76c0dce"
    ctx["l5"]["conservation"] = om.conservation_for(1, "SDC")
    obs = om.build_observation(ctx)
    ok, viol = om.validate_observation(obs)
    check("validate-sdc-equal-checksum-violation",
          not ok and any("SDC" in v for v in viol), viol)
    # SDC with a different checksum -> clean
    ctx = make_ctx("SDC", 1)
    obs = om.build_observation(ctx)
    ok, viol = om.validate_observation(obs)
    check("validate-sdc-clean", ok and viol == [], viol)
    # Masked with mismatched checksum -> violation
    ctx = make_ctx("Masked", 1)
    ctx["l5"]["checksum_observed"] = "ffffffffffffffff"
    obs = om.build_observation(ctx)
    ok, viol = om.validate_observation(obs)
    check("validate-masked-mismatch-violation",
          not ok and any("Masked" in v for v in viol), viol)
    # Inactive with a landed fault (l0.injected>=1) -> conservation violation
    ctx = make_ctx("Inactive", 1)
    obs = om.build_observation(ctx)
    ok, viol = om.validate_observation(obs)
    check("validate-inactive-landed-violation",
          not ok and any("Inactive" in v for v in viol), viol)
    # detector four-way map
    obs = om.build_observation(make_ctx("Masked", 1))
    check("detector-masked-none", obs["l5"]["detector"] is None,
          obs["l5"]["detector"])
    obs = om.build_observation(make_ctx("SDC", 1))
    check("detector-sdc-application", obs["l5"]["detector"] == "Application")
    obs = om.build_observation(make_ctx("Crash", 1, component="decode",
                                        l1_status="truncated",
                                        l2_status="not_observed_before_crash",
                                        l4_status="ok"))
    check("detector-crash-os", obs["l5"]["detector"] == "OS")
    obs = om.build_observation(make_ctx("Inactive", 0,
                                        l1_status="inactive_no_activation",
                                        l2_status="inactive_no_activation",
                                        l4_status="inactive_no_activation"))
    check("detector-inactive-na", obs["l5"]["detector"] == "n/a")


def test_build_observation_missing_block():
    # a missing l1 block becomes status=error — never silently omitted
    ctx = make_ctx("Masked", 1)
    ctx.pop("l1")
    obs = om.build_observation(ctx)
    check("missing-l1-error", obs["l1"]["status"] == "error"
          and "reason" in obs["l1"], obs["l1"])
    check("missing-l1-key-present", "l1" in obs)
    # missing l3 (no default unsupported magic — error is honest)
    ctx = make_ctx("Masked", 1)
    ctx.pop("l3")
    obs = om.build_observation(ctx)
    check("missing-l3-error", obs["l3"]["status"] == "error", obs["l3"])
    # missing l2 with the whole ctx gone
    obs = om.build_observation(dict(identity=make_identity(),
                                    l5=make_ctx("Masked", 1)["l5"]))
    check("missing-l2-error", obs["l2"]["status"] == "error", obs["l2"])


def test_observation_top_level_shape():
    obs = om.build_observation(make_ctx("Masked", 1, component="decode"))
    expected_keys = ("schema_version", "identity", "l0", "l1", "l2", "l3",
                     "l4", "l5", "replay", "violations", "chain_complete",
                     "chain_gaps", "files", "coverage_scope", "audit")
    for k in expected_keys:
        check("topkey-%s" % k, k in obs, sorted(obs.keys()))
    check("schema-version", obs["schema_version"] ==
          om.OBSERVATION_SCHEMA_VERSION)
    check("l0-shape", obs["l0"]["component"] == "decode"
          and obs["l0"]["log_name"] == "decode_injections.log"
          and obs["l0"]["skip_lines"] == 0, obs["l0"])
    # contract keys: l0.activated; l3 five keys always; conservation
    # schema keys with activated consistent
    check("l0-activated-key",
          obs["l0"]["activated"] == obs["l0"]["injected"], obs["l0"])
    check("l3-five-keys",
          all(k in obs["l3"] for k in
              ("status", "method", "fanout", "caveat", "reason")),
          sorted(obs["l3"].keys()))
    check("l3-unsupported-nulls",
          obs["l3"]["method"] is None and obs["l3"]["fanout"] is None
          and obs["l3"]["caveat"] is None, obs["l3"])
    cons = obs["l5"]["conservation"]
    check("cons-consistency-l0",
          cons["activated"] == obs["l0"]["activated"], cons)
    check("cons-schema-in-obs",
          cons["ok"] is True and cons["five_primary_sum"] == 1
          and isinstance(cons["notes"], str), cons)
    # coordinator replay contract: TOP-LEVEL replay, all keys present,
    # honest nulls when not performed, and NOTHING inside l2
    check("replay-top-level-default",
          obs["replay"]["performed"] is False
          and obs["replay"]["pass2_classification"] is None
          and obs["replay"]["determinism"] is None
          and obs["replay"]["verdict_pass2"] is None
          and obs["replay"]["checksum_pass2"] is None
          and obs["replay"]["performed_at"] is None, obs["replay"])
    check("replay-not-in-l2", "replay" not in obs["l2"], obs["l2"].keys())
    ctx2 = make_ctx("Masked", 1)
    ctx2["replay"] = dict(performed=True, pass2_classification="Masked",
                          determinism="match")
    obs2 = om.build_observation(ctx2)
    check("replay-performed-passthrough",
          obs2["replay"]["performed"] is True
          and obs2["replay"]["determinism"] == "match"
          and obs2["replay"]["verdict_pass2"] is None, obs2["replay"])
    # json round-trip (the written observation.json must be loadable)
    obs2 = json.loads(json.dumps(obs))
    ok, viol = om.validate_observation(obs2)
    check("json-roundtrip-validate", ok, viol)


def test_l0_funnel_invariant_and_limited():
    """[FIX-A Task 1] the L0 funnel must be monotone
    attempted >= eligible >= injected >= activated whenever all four are
    ints, and the l0 block must carry the honest `limited` scope note
    (gate rejections before the log point are not logged by the C++
    injectors, so attempted is a lower bound)."""
    # (a) a well-formed funnel passes validate
    ctx = make_ctx("Masked", 1, component="decode")
    ctx["l0"].update(dict(attempted=3, eligible=2))
    obs = om.build_observation(ctx)
    check("funnel-ok-no-violations",
          not any("funnel" in v for v in obs["violations"]),
          obs["violations"])
    # (b) eligible > attempted -> violation
    ctx = make_ctx("Masked", 1, component="decode")
    ctx["l0"].update(dict(attempted=1, eligible=2))
    obs = om.build_observation(ctx)
    check("funnel-eligible-gt-attempted",
          any("funnel" in v for v in obs["violations"]), obs["violations"])
    # (c) injected > eligible -> violation
    ctx = make_ctx("Masked", 1, component="decode")
    ctx["l0"].update(dict(attempted=3, eligible=0))
    obs = om.build_observation(ctx)
    check("funnel-injected-gt-eligible",
          any("funnel" in v for v in obs["violations"]), obs["violations"])
    # (d) None attempted (no source / legacy obs) skips the check
    ctx = make_ctx("Masked", 1, component="decode")
    obs = om.build_observation(ctx)
    check("funnel-none-skips-check",
          not any("funnel" in v for v in obs["violations"]),
          obs["violations"])
    # (e) l0_block_from on a real log: real counts + limited note
    d, p = wtmp(DECODE_SKIP_THEN_SUCCESS)
    blk = om.l0_block_from(d, "decode")
    check("l0blk-attempted", blk["attempted"] == 2, blk["attempted"])
    check("l0blk-eligible", blk["eligible"] == 1, blk["eligible"])
    check("l0blk-injected", blk["injected"] == 1, blk["injected"])
    check("l0blk-activated-derivation",
          blk["activated"] == blk["injected"], blk)
    check("l0blk-limited-note",
          isinstance(blk.get("limited"), str) and blk["limited"],
          blk.get("limited"))
    # (e2) [FIX-RB] eligible_count has no source in a decode log (only
    # CHAOSLSQFwd/CHAOSExec write CHAOS_ELIGIBLE_COUNT, at teardown) ->
    # the gate-recognized l0.limited_reason documents the n/a; the real
    # per-line counts stay; the admission gate stays silent (its own
    # documented escape clause -- the gate itself is NOT modified)
    import ooo_chain_audit as oca
    check("l0blk-limited-reason-present",
          isinstance(blk.get("limited_reason"), str)
          and "CHAOS_ELIGIBLE_COUNT" in blk["limited_reason"]
          and "eligible_count" in blk["limited_reason"]
          and "attempted=2" in blk["limited_reason"],
          blk.get("limited_reason"))
    check("l0blk-eligible-count-none-documented",
          blk["eligible_count"] is None
          and blk["attempted"] == 2 and blk["eligible"] == 1,
          (blk.get("eligible_count"), blk.get("attempted"),
           blk.get("eligible")))
    _obs = {"l0": blk, "l1": {}, "l2": {}, "l3": {}}
    check("gate-silent-with-reason",
          "l0_funnel_missing" not in
          oca.semantic_gate_violations(_obs),
          repr(oca.semantic_gate_violations(_obs)))
    _obs_bad = {"l0": dict(blk, limited_reason=None),
                "l1": {}, "l2": {}, "l3": {}}
    check("gate-fires-without-reason",
          "l0_funnel_missing" in
          oca.semantic_gate_violations(_obs_bad),
          repr(oca.semantic_gate_violations(_obs_bad)))
    # (e3) an lsq_fwd log WITH the CHAOS_ELIGIBLE_COUNT self-report:
    # eligible_count real, no limited_reason
    d3, _ = wtmp("CHAOS_ELIGIBLE_COUNT=3\n"
                 "Tick: 100, Site: lsq_fwd, faults_injected: 1\n",
                 name="lsq_fwd_injections.log")
    blk3 = om.l0_block_from(d3, "lsq_fwd")
    check("l0blk-self-reported-eligible-count",
          blk3["eligible_count"] == 3
          and blk3.get("limited_reason") is None,
          (blk3.get("eligible_count"), blk3.get("limited_reason")))
    # (f) missing log -> status no_log, funnel None + honest note
    d2 = tempfile.mkdtemp(prefix="obs-nolog2-")
    blk = om.l0_block_from(d2, "decode")
    check("l0blk-nolog-status", blk["status"] == "no_log", blk)
    check("l0blk-nolog-attempted-none", blk["attempted"] is None, blk)
    check("l0blk-nolog-eligible-none", blk["eligible"] is None, blk)


def test_zero_observation_crash_semantics():
    """[FIX-A Task 2] zero-line-trace Crash semantics in the observation
    layer: l2 not_observed_before_crash requires first_divergent_commit
    null (a non-null one is a violation -- "no observation" must never
    masquerade as "divergence observed"); the status and the new l1
    no_snapshots_before_crash are honest states (never violations) but
    are NOT chain-completeness evidence (they cost gaps L2/L1)."""
    # (a) the new l1 status is in the vocabulary
    check("l1-status-vocab-no-snapshots",
          "no_snapshots_before_crash" in om.L1_STATUSES, om.L1_STATUSES)
    # (b) validate: not_observed_before_crash + null fdc -> NO violation
    l3crash = dict(status="unsupported", reason="decode has no L3")
    obs = om.build_observation(
        make_ctx("Crash", 1, component="decode",
                 l1_status="no_snapshots_before_crash",
                 l2_status="not_observed_before_crash", l3=l3crash,
                 l4_status="ok"))
    check("zero-obs-validate-clean", obs["violations"] == [],
          obs["violations"])
    # (c) validate: not_observed_before_crash + NON-null fdc -> violation
    ctx = make_ctx("Crash", 1, component="decode",
                   l1_status="no_snapshots_before_crash",
                   l2_status="not_observed_before_crash", l3=l3crash,
                   l4_status="ok")
    ctx["l2"]["first_divergent_commit"] = dict(seq=0,
                                               class_="instruction_flow_change")
    obs = om.build_observation(ctx)
    check("zero-obs-fdc-nonnull-violation",
          any("first_divergent_commit" in v for v in obs["violations"]),
          obs["violations"])
    # (d) chain: both zero-observation statuses cost their level's gap
    # (honest absence of observation, not a violation)
    obs = om.build_observation(
        make_ctx("Crash", 1, component="decode",
                 l1_status="no_snapshots_before_crash",
                 l2_status="not_observed_before_crash", l3=l3crash,
                 l4_status="ok"))
    check("zero-obs-chain-gaps-l1-l2-l3",
          obs["chain_gaps"] == ["L1", "L2", "L3"], obs["chain_gaps"])
    check("zero-obs-chain-incomplete", obs["chain_complete"] is False)
    # (e) contrast: a REAL divergence in the salvaged prefix is status ok
    # (observation happened) and no L2 gap
    ctx = make_ctx("Crash", 1, component="decode", l3=l3crash,
                   l4_status="ok")
    ctx["l2"]["commit_diff"] = dict(
        verdict="diverged", run_truncated=True,
        first_divergence=dict(seq=5, class_="data_corruption",
                              run_line="5,0,1005,4195f0,add,1,1,5,12,"
                                       "deadbeefdeadbeef"))
    ctx["l2"]["first_divergent_commit"] = ctx["l2"]["commit_diff"][
        "first_divergence"]
    obs = om.build_observation(ctx)
    check("prefix-divergence-l2-ok", obs["l2"]["status"] == "ok",
          obs["l2"]["status"])
    check("prefix-divergence-no-l2-gap",
          "L2" not in obs["chain_gaps"], obs["chain_gaps"])
    # (f) l2 status derivation still maps a salvaged clean prefix to
    # not_observed_before_crash (fixture-level: prefix truncation)
    import commit_diff as cdmod
    import tempfile as _tf
    d = _tf.mkdtemp(prefix="obs-zero-")
    ref = os.path.join(d, "ref.csv.gz")
    lines = [_ctrace_line(i, 1000 + i) for i in range(50)]
    with gzip.open(ref, "wt") as f:
        f.write("\n".join(lines) + "\n")
    # 0-byte run trace: the crash-before-first-flush signature
    run = os.path.join(d, "run.csv.gz")
    open(run, "wb").close()
    cd = cdmod.compare(ref, run, 0)
    # the raw differ fabricates 50 one-sided divergences -- this is WHY
    # the sample runner must not call it on a 0-line trace (do_l2 fix)
    check("zero-line-raw-differ-fabricates",
          cd["verdict"] == "diverged"
          and cd["first_divergence"]["seq"] == 0
          and cd["divergence_counts"]["instruction_flow_change"] == 50,
          (cd["verdict"], cd["divergence_counts"]))


def main():
    print("test_parse_injection_log:")
    test_parse_injection_log()
    print("test_truncated_passthrough_and_l2_status:")
    test_truncated_passthrough_and_l2_status()
    print("test_conservation:")
    test_conservation()
    print("test_chain_completeness_three_states:")
    test_chain_completeness_three_states()
    print("test_validate_rules:")
    test_validate_rules()
    print("test_l0_funnel_invariant_and_limited:")
    test_l0_funnel_invariant_and_limited()
    print("test_zero_observation_crash_semantics:")
    test_zero_observation_crash_semantics()
    print("test_build_observation_missing_block:")
    test_build_observation_missing_block()
    print("test_observation_top_level_shape:")
    test_observation_top_level_shape()
    n = len(FAILURES)
    print("\n%s (%d checks)" % ("ALL PASS" if n == 0 else
                                "FAILURES: " + repr(FAILURES),
                                len(CHECKS)))
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
