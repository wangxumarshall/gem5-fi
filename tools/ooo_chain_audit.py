#!/usr/bin/env python3
"""[OOO][P1] ooo_chain_audit — per-sample L0-L5 chain integrity auditor
(L0-L5 run, 2026-10-12; plan Task 8, Subagent-C).

Independent audit of a finished campaign directory: every
samples/<run_id>/observation.json is checked against the frozen
`ooo-observation/v1` contract. The auditor NEVER relaxes a check to make
a campaign pass — a missing key, a wrong type, a drifted file sha, a
false "no_divergence" claim on a Crash sample are all violations.

Per sample:
  * parsability (json + required keys) -> else missing_layers=["ALL"],
    violations=["observation_unparseable"];
  * L0 (injected/activated/events funnel sanity), L1 (status+micro_diff),
    L2 (status in the legal vocabulary + commit_diff.verdict; Crash/Hang
    with status==ok and verdict==no_divergence is the false-report
    violation "crash_claimed_no_divergence"), L3 (status; unsupported
    requires a reason; PRF submodels must carry the proxy fanout),
    L4 (first_detection detector vocabulary None|Application|OS|
    Hardware RAS|n/a), L5 (nine-class vocabulary + conservation.ok);
  * the five admission-view semantic gates (2026-10-13, Fix-C; see
    semantic_gate_violations): l3_unsupported_with_activation,
    l0_funnel_missing, l2_diverged_zero_instructions,
    l1_valid_zero_snaps, first_divergence_from_empty_trace — scoped to
    activated>0 samples and NEVER relaxed (legacy data carrying them is
    flagged; the offline `correction-audit` quantifies the backlog);
  * identity: every required identity key present; gem5_sha256 must equal
    --frozen-gem5-sha when given;
  * files manifest: EVERY referenced file re-hashed (no spot checks),
    path-escape refused;
  * chain flag consistency (chain_complete <=> chain_gaps empty; an L3
    gap must be recorded when l3.status is unsupported).

Campaign level: run_id and seed uniqueness, nine-class counts, the
conservation ledger (five outcome classes + post-activation simulator
failures == activated total), gaps by level, and the honest-vs-invalid
split (chain_gaps==["L3"] from an unsupported L3 is an honest record,
NOT invalid).

Outputs <campaign_dir>/chain_audit.json + chain_audit.md. Exit codes:
  * campaign dir missing / no sample dirs -> 1;
  * --require-complete: any sample with violations (incl. missing
    observation) -> 1; honest L3 gaps alone -> 0.

CLI: audit --campaign-dir <d> [--require-complete] [--frozen-gem5-sha S]
           [--correction-mode]
      correction-audit --campaign-dir <d> [--frozen-gem5-sha S]
        offline re-audit of a FINISHED campaign under the current strict
        rules; writes only <campaign_dir>/correction_audit.json and never
        touches the original evidence.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter

SCHEMA_VERSION = "ooo-observation/v1"

# The five post-activation outcome classes of the conservation ledger
# (task letter: 五类和 + post_activation_simulator_failure == activated).
FIVE_OUTCOME_CLASSES = ("Crash", "Hang", "SDC", "Latent", "Masked")

L2_STATUSES = ("ok", "inactive_no_activation", "not_observed_before_crash",
               "truncated", "error")
# Deliberately NOT imported from ooo_observation: the audit pins the
# observation schema independently so producer-side vocabulary drift is
# caught, never silently accepted. Keep in sync BY HAND with
# ooo_observation.L3_STATUSES (FIX-RB: + not_observed_before_crash, the
# zero-byte crash-trace marker; chain gap L3 still recorded).
L3_STATUSES = ("ok", "unsupported", "inactive_no_activation", "error",
               "not_observed_before_crash")
COMMIT_VERDICTS = ("diverged", "no_divergence",
                   "truncated_no_divergence_in_prefix")
DETECTOR_VOCAB = (None, "None", "n/a", "Application", "OS", "Hardware RAS")
PRF_SUBMODELS = ("physreg", "prf", "phys_reg")

REQUIRED_TOP = ("schema_version", "identity", "l0", "l1", "l2", "l3",
                "l4", "l5", "violations", "chain_complete", "chain_gaps",
                # integration adjudication 2026-10-12 (lead): the canonical
                # replay position is TOP-LEVEL observation.replay (the
                # Subagent-A contract after the lead's disambiguation);
                # l2.replay is NOT required and not rejected.
                "replay",
                "files", "coverage_scope", "audit")
LAYER_KEYS = ("l0", "l1", "l2", "l3", "l4", "l5")

IDENTITY_KEYS = ("run_id", "campaign_id", "runid_row", "submodel",
                 "sample_index", "phase", "seed", "manifest_sha256",
                 "gem5_sha256", "config", "workload", "golden_key",
                 "chaos_commit", "patchset_sha256", "pythonhashseed",
                 "host", "started", "finished", "wall_s")

LAYER_SUBKEYS = {
    "l0": ("injected", "activated", "events", "skip_lines",
           "eligible_count", "attempted", "log_sha256"),
    "l1": ("status", "micro_diff", "first_divergence", "files"),
    "l2": ("status", "coverage", "commit_diff", "first_divergent_commit",
           "files"),
    "l3": ("status", "method", "fanout", "caveat", "reason"),
    "l4": ("status", "first_detection", "latency_from_l0", "oracle"),
    "l5": ("classification", "reason", "exit", "timed_out",
           "faults_injected", "checksum_observed", "checksum_golden",
           "detector", "conservation"),
}

NINE_CLASSES = ("SimulatorError", "Inactive", "Corrected",
                "DetectedContained", "Crash", "Hang", "SDC", "Latent",
                "Masked")


class AuditError(Exception):
    """Loud, user-facing audit error (bad invocation, unreadable tree)."""


# The five admission-view mandatory-FAIL gates (L0-L5 correction,
# 2026-10-13, Fix-C). All are scoped to samples with l0.activated >= 1:
# an activated sample must carry a complete observation chain.
SEMANTIC_GATE_VIOLATIONS = ("l3_unsupported_with_activation",
                            "l0_funnel_missing",
                            "l2_diverged_zero_instructions",
                            "l1_valid_zero_snaps",
                            "first_divergence_from_empty_trace",
                            # FIX-RB round 2 (central directive):
                            "l4_latency_without_detection",
                            "l4_negative_latency",
                            "l3_zero_scan_masquerade")


def semantic_gate_violations(obs):
    """The five admission-view mandatory-FAIL gates (L0-L5 correction,
    2026-10-13). Scoped to samples with l0.activated >= 1:

      * l3_unsupported_with_activation -- an activated sample whose L3
        (source-read association / fanout) is unsupported: a chain hole
        from the formal-admission viewpoint;
      * l0_funnel_missing -- l0.attempted or l0.eligible_count is
        null/missing without a legal limited reason (l0.status=no_log,
        or a documented non-empty l0.funnel_limited_reason /
        l0.limited_reason string);
      * l2_diverged_zero_instructions -- commit_diff.verdict=diverged
        with run_instructions 0/None/missing: an empty or unrecorded
        run trace cannot support a divergence verdict (the empty-trace
        fake divergence: first_divergence at seq=0
        class=instruction_flow_change is this pattern);
      * l1_valid_zero_snaps -- l1.status=ok with micro_diff.snaps_run
        not a positive int (zero or missing snaps under a "valid" L1);
      * first_divergence_from_empty_trace -- a first-divergence record
        (commit_diff.first_divergence or l2.first_divergent_commit)
        sourced from an empty run trace.

    Pure observation-shape checks: no file hashing, no identity checks
    (those live in audit_observation). Returns a list drawn from
    SEMANTIC_GATE_VIOLATIONS (may be empty). These rules are NEVER
    relaxed: legacy samples carrying them are flagged, and the offline
    correction-audit quantifies the backlog.
    """
    l0 = obs.get("l0") if isinstance(obs.get("l0"), dict) else {}
    l1 = obs.get("l1") if isinstance(obs.get("l1"), dict) else {}
    l2 = obs.get("l2") if isinstance(obs.get("l2"), dict) else {}
    l3 = obs.get("l3") if isinstance(obs.get("l3"), dict) else {}
    activated = l0.get("activated")
    if not (isinstance(activated, int) and activated > 0):
        return []
    out = []
    if l3.get("status") == "unsupported":
        out.append("l3_unsupported_with_activation")
    funnel_limited = l0.get("status") == "no_log"
    for k in ("funnel_limited_reason", "limited_reason"):
        r = l0.get(k)
        if isinstance(r, str) and r.strip():
            funnel_limited = True
    if (l0.get("attempted") is None or l0.get("eligible_count") is None) \
            and not funnel_limited:
        out.append("l0_funnel_missing")
    cd = l2.get("commit_diff") \
        if isinstance(l2.get("commit_diff"), dict) else {}
    run_instructions = cd.get("run_instructions")
    run_trace_empty = run_instructions is None or run_instructions == 0
    if cd.get("verdict") == "diverged" and run_trace_empty:
        out.append("l2_diverged_zero_instructions")
    if l1.get("status") == "ok":
        md = l1.get("micro_diff")
        snaps = md.get("snaps_run") if isinstance(md, dict) else None
        if not (isinstance(snaps, int) and snaps > 0):
            out.append("l1_valid_zero_snaps")
    fd_rec = any(isinstance(x, dict) for x in
                 (cd.get("first_divergence"),
                  l2.get("first_divergent_commit")))
    if fd_rec and run_trace_empty:
        out.append("first_divergence_from_empty_trace")
    # [FIX-RB round 2, central directive] L4 latency honesty + L3 scan
    # evidence, admission view (scoped to activated samples above).
    l4 = obs.get("l4") if isinstance(obs.get("l4"), dict) else {}
    lat = l4.get("latency_from_l0")
    fd_l4 = l4.get("first_detection")
    if isinstance(lat, dict):
        ticks = lat.get("ticks")
        insts = lat.get("committed_insts")
        has_num = (isinstance(ticks, (int, float))
                   and not isinstance(ticks, bool)) \
            or (isinstance(insts, (int, float))
                and not isinstance(insts, bool))
        no_event = (not isinstance(fd_l4, dict)) \
            or fd_l4.get("kind") is None
        if has_num and no_event:
            out.append("l4_latency_without_detection")
        for v in (ticks, insts):
            if isinstance(v, (int, float)) and not isinstance(v, bool)                     and v < 0:
                out.append("l4_negative_latency")
    hops = l3.get("hops") if isinstance(l3.get("hops"), list) else None
    scanned = l3.get("rows_scanned_after_source")
    if (l3.get("status") == "ok" and l3.get("method") == "source_read"
            and l3.get("source_row") is not None
            and not hops
            and not (isinstance(scanned, int) and scanned > 0)):
        # an ok source_read chain with a located source but ZERO rows
        # scanned and zero hops: "did not scan" masquerading as
        # "scanned, no consumers" -- never a complete chain
        out.append("l3_zero_scan_masquerade")
    return out


def sha256_file(path, _buf=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(_buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------- per-sample

def _check_files(obs, sample_dir, violations):
    """Re-hash EVERY file in the files manifest (not a spot check)."""
    files = obs.get("files")
    if not isinstance(files, dict):
        violations.append("files_manifest_malformed")
        return
    base = os.path.realpath(sample_dir)
    for rel in sorted(files):
        want = files[rel]
        p = os.path.join(sample_dir, rel)
        rp = os.path.realpath(p)
        if not (rp == base or rp.startswith(base + os.sep)):
            violations.append("file_path_escape:%s" % rel)
            continue
        if not os.path.isfile(p):
            violations.append("file_missing:%s" % rel)
            continue
        if not isinstance(want, str) or len(want) != 64:
            violations.append("file_sha_malformed:%s" % rel)
            continue
        got = sha256_file(p)
        if got != want:
            violations.append("file_sha_mismatch:%s" % rel)


def _check_identity(obs, frozen_gem5_sha, violations):
    ident = obs.get("identity")
    if not isinstance(ident, dict):
        violations.append("identity_malformed")
        return None
    for k in IDENTITY_KEYS:
        if k not in ident:
            violations.append("identity_missing_key:%s" % k)
    if "seed" in ident and not isinstance(ident["seed"], int):
        violations.append("identity_seed_not_int")
    for sub, keys in (("config", ("path", "sha256")),
                      ("workload", ("path", "sha256", "golden_id"))):
        d = ident.get(sub)
        if not isinstance(d, dict):
            violations.append("identity_%s_malformed" % sub)
            continue
        for k in keys:
            if k not in d:
                violations.append("identity_%s_missing_key:%s" % (sub, k))
    if frozen_gem5_sha:
        got = ident.get("gem5_sha256")
        if got != frozen_gem5_sha:
            violations.append("gem5_sha_mismatch")
    return ident


def _check_layers(obs, submodel, violations):
    """Per-layer status/consistency checks. Returns the observed
    classification (or None) for campaign-level accounting."""
    classification = None
    # the five admission-view semantic gates (2026-10-13): applied to
    # EVERY audit, never relaxed; --correction-mode only changes the
    # report tone, not the rules.
    violations.extend(semantic_gate_violations(obs))
    for lk in LAYER_KEYS:
        if not isinstance(obs.get(lk), dict):
            violations.append("layer_%s_malformed" % lk)
            continue
        for sk in LAYER_SUBKEYS[lk]:
            if sk not in obs[lk]:
                violations.append("missing_key:%s.%s" % (lk, sk))

    l0 = obs.get("l0") if isinstance(obs.get("l0"), dict) else {}
    l1 = obs.get("l1") if isinstance(obs.get("l1"), dict) else {}
    l2 = obs.get("l2") if isinstance(obs.get("l2"), dict) else {}
    l3 = obs.get("l3") if isinstance(obs.get("l3"), dict) else {}
    l4 = obs.get("l4") if isinstance(obs.get("l4"), dict) else {}
    l5 = obs.get("l5") if isinstance(obs.get("l5"), dict) else {}

    # ---- L0: injection funnel -------------------------------------
    injected, activated = l0.get("injected"), l0.get("activated")
    if not isinstance(injected, int) or injected < 0:
        violations.append("l0_injected_malformed")
    if not isinstance(activated, int) or activated < 0:
        violations.append("l0_activated_malformed")
    elif isinstance(injected, int) and activated > injected:
        violations.append("l0_activated_exceeds_injected")
    if not isinstance(l0.get("events"), list):
        violations.append("l0_events_not_list")

    # ---- L1 --------------------------------------------------------
    if l1 and not isinstance(l1.get("status"), str):
        violations.append("l1_status_malformed")
    elif l1.get("status") == "ok" and "micro_diff" in l1 \
            and not isinstance(l1.get("micro_diff"), (dict, type(None))):
        violations.append("l1_micro_diff_unreadable")

    # ---- L2 --------------------------------------------------------
    l2s = l2.get("status")
    cd = l2.get("commit_diff")
    if l2s not in L2_STATUSES:
        violations.append("l2_status_invalid")
    if l2s == "ok":
        if not isinstance(cd, dict):
            violations.append("l2_commit_diff_missing")
        elif cd.get("verdict") not in COMMIT_VERDICTS:
            violations.append("l2_verdict_invalid")

    # ---- L3 --------------------------------------------------------
    l3s = l3.get("status")
    if l3s not in L3_STATUSES:
        violations.append("l3_status_invalid")
    else:
        if l3s == "unsupported" and not (isinstance(l3.get("reason"), str)
                                         and l3["reason"].strip()):
            violations.append("l3_unsupported_without_reason")
        if l3s == "not_observed_before_crash" and not (
                isinstance(l3.get("reason"), str)
                and l3["reason"].strip()):
            violations.append("l3_not_observed_without_reason")
        if l3s == "ok" and not (isinstance(l3.get("method"), str)
                                and l3["method"].strip()):
            violations.append("l3_ok_without_method")
        if submodel and str(submodel).lower() in PRF_SUBMODELS \
                and l3s != "ok":
            # PRF carries the (proxy) fanout — an unsupported L3 on a PRF
            # sample is a chain hole that must not exist, not an honest gap.
            violations.append("l3_physreg_missing_fanout")

    # ---- L4 --------------------------------------------------------
    fd = l4.get("first_detection")
    if fd is not None:
        if not isinstance(fd, dict):
            violations.append("l4_first_detection_malformed")
        else:
            for k in ("kind", "detector", "tick", "seq", "note"):
                if k not in fd:
                    violations.append("l4_first_detection_missing:%s" % k)
            if fd.get("detector") not in DETECTOR_VOCAB:
                violations.append("l4_detector_invalid")
    # [FIX-RB round 2, central directive] latency honesty, ALL samples:
    # a latency number requires a REAL detection event (kind != None),
    # and no latency may be negative (the divergence cannot precede the
    # fault that caused it -- a negative is a parse/anchor bug, never
    # evidence).
    _lat = l4.get("latency_from_l0")
    if isinstance(_lat, dict):
        _ticks = _lat.get("ticks")
        _insts = _lat.get("committed_insts")
        _has_num = (isinstance(_ticks, (int, float))
                    and not isinstance(_ticks, bool)) \
            or (isinstance(_insts, (int, float))
                and not isinstance(_insts, bool))
        _no_event = (not isinstance(fd, dict)) or fd.get("kind") is None
        if _has_num and _no_event:
            violations.append("l4_latency_without_detection")
        if isinstance(_ticks, (int, float)) \
                and not isinstance(_ticks, bool) and _ticks < 0:
            violations.append("l4_negative_latency")
        if isinstance(_insts, (int, float)) \
                and not isinstance(_insts, bool) and _insts < 0:
            violations.append("l4_negative_latency")

    # ---- L5 --------------------------------------------------------
    classification = l5.get("classification")
    if classification not in NINE_CLASSES:
        violations.append("l5_classification_invalid")
        classification = None
    cons = l5.get("conservation")
    if not isinstance(cons, dict) or "ok" not in cons:
        violations.append("l5_conservation_missing")
    elif cons.get("ok") is not True:
        violations.append("conservation_not_ok")

    # ---- cross-layer consistency ------------------------------------
    if classification:
        cksum_obs = l5.get("checksum_observed")
        cksum_gold = l5.get("checksum_golden")
        if classification == "Inactive" and isinstance(activated, int) \
                and activated > 0:
            violations.append("conservation_inactive_with_activation")
        if classification in FIVE_OUTCOME_CLASSES \
                and isinstance(activated, int) and activated == 0:
            violations.append("conservation_outcome_without_activation")
        if classification == "Masked":
            if cksum_obs is None or cksum_gold is None:
                violations.append("masked_checksum_missing")
            elif cksum_obs != cksum_gold:
                violations.append("masked_checksum_mismatch")
        if classification == "SDC":
            if cksum_obs is None or cksum_gold is None:
                violations.append("sdc_checksum_missing")
            elif cksum_obs == cksum_gold:
                violations.append("sdc_checksum_matches_golden")
        # the false-report rule: a crashed/hung run with a "clean" L2 must
        # be recorded as not_observed_before_crash / truncated — NEVER as
        # a completed no-divergence comparison.
        if classification in ("Crash", "Hang") and l2s == "ok" \
                and isinstance(cd, dict):
            verdict = cd.get("verdict")
            if verdict == "no_divergence":
                violations.append("crash_claimed_no_divergence")
            elif verdict != "diverged":
                violations.append("crash_l2_status_ok_without_divergence")
    return classification


def _check_chain_flags(obs, violations):
    cc = obs.get("chain_complete")
    gaps = obs.get("chain_gaps")
    if not isinstance(cc, bool):
        violations.append("chain_complete_not_bool")
    if not isinstance(gaps, list) or any(not isinstance(g, str)
                                         for g in gaps):
        violations.append("chain_gaps_malformed")
        return cc, gaps
    if isinstance(cc, bool) and cc != (len(gaps) == 0):
        violations.append("chain_flag_gap_mismatch")
    l3 = obs.get("l3") if isinstance(obs.get("l3"), dict) else {}
    l3s = l3.get("status")
    if l3s in ("unsupported", "not_observed_before_crash") \
            and "L3" not in gaps:
        violations.append("l3_gap_not_recorded")
    # [FIX-RB round 2] an ok source_read chain whose source NEVER
    # COMMITTED (source_row null -- the honest in-flight terminal
    # state) legitimately costs gap L3: the observation completed but
    # no propagation chain exists. Any other ok-status gap has no
    # basis.
    if "L3" in gaps and l3s not in ("unsupported", "error",
                                    "not_observed_before_crash") \
            and not (l3s == "ok"
                     and isinstance(l3, dict)
                     and l3.get("method") == "source_read"
                     and l3.get("source_row") is None):
        violations.append("gap_l3_without_basis")
    return cc, gaps


def audit_observation(obs, sample_dir, frozen_gem5_sha=None):
    """Audit one parsed observation dict. Returns the per-sample result
    record (run_id, classification, missing_layers, violations,
    chain_complete, chain_gaps + accounting extras)."""
    violations = []
    missing_layers = []
    if not isinstance(obs, dict):
        return {"run_id": os.path.basename(sample_dir),
                "classification": None, "missing_layers": ["ALL"],
                "violations": ["observation_unparseable"],
                "chain_complete": None, "chain_gaps": [], "seed": None,
                "activated": None, "submodel": None}
    if obs.get("schema_version") != SCHEMA_VERSION:
        violations.append("schema_version_mismatch")
    for k in REQUIRED_TOP:
        if k not in obs:
            violations.append("missing_key:%s" % k)
    for lk in LAYER_KEYS:
        if lk not in obs or not isinstance(obs.get(lk), dict):
            missing_layers.append(lk.upper())
            if lk in obs:
                violations.append("layer_%s_malformed" % lk)
            else:
                violations.append("missing_layer_%s" % lk.upper())
    if not isinstance(obs.get("violations"), list):
        violations.append("violations_field_malformed")
    elif obs["violations"]:
        violations.append("observation_self_reported_violations")
    aud = obs.get("audit")
    if not isinstance(aud, dict) or "built_at" not in aud \
            or "builder_sha256" not in aud:
        violations.append("audit_block_malformed")
    if "coverage_scope" not in obs:
        violations.append("missing_key:coverage_scope")

    ident = _check_identity(obs, frozen_gem5_sha, violations)
    submodel = ident.get("submodel") if ident else None
    classification = _check_layers(obs, submodel, violations)
    cc, gaps = _check_chain_flags(obs, violations)
    _check_files(obs, sample_dir, violations)

    l0 = obs.get("l0") if isinstance(obs.get("l0"), dict) else {}
    l5 = obs.get("l5") if isinstance(obs.get("l5"), dict) else {}
    return {
        "run_id": (ident or {}).get("run_id")
        or os.path.basename(sample_dir),
        "classification": classification or l5.get("classification"),
        "missing_layers": missing_layers,
        "violations": violations,
        "chain_complete": cc,
        "chain_gaps": gaps if isinstance(gaps, list) else [],
        "seed": (ident or {}).get("seed"),
        "activated": l0.get("activated"),
        "submodel": submodel,
    }


# ---------------------------------------------------------- campaign level

def discover_samples(campaign_dir):
    """samples/<run_id> dirs, skipping dot-dirs (staging) and the
    QUARANTINE evidence area (honestly excluded, reported separately)."""
    sdir = os.path.join(campaign_dir, "samples")
    if not os.path.isdir(sdir):
        return [], 0
    out = []
    n_quarantine = 0
    for name in sorted(os.listdir(sdir)):
        if name.startswith("."):
            continue
        if name == "QUARANTINE":
            n_quarantine += 1
            continue
        p = os.path.join(sdir, name)
        if os.path.isdir(p):
            out.append(p)
    return out, n_quarantine


def audit_campaign(campaign_dir, frozen_gem5_sha=None, correction_mode=False):
    """Full campaign audit. Returns the rollup dict (also the payload
    written to chain_audit.json). `correction_mode` only annotates the
    report (legacy re-audit tone); the RULES are identical either way."""
    if not os.path.isdir(campaign_dir):
        raise AuditError("campaign dir not found: %s" % campaign_dir)
    sample_dirs, n_quarantine = discover_samples(campaign_dir)
    if not sample_dirs:
        raise AuditError("no sample dirs under %s/samples" % campaign_dir)

    samples = []
    seen_run_ids = {}
    seen_seeds = {}
    dup_run_ids, dup_seeds = [], []
    for sdir in sample_dirs:
        opath = os.path.join(sdir, "observation.json")
        obs = None
        if os.path.isfile(opath):
            try:
                with open(opath) as f:
                    obs = json.load(f)
            except (ValueError, OSError):
                obs = None
        if obs is None:
            rec = {"run_id": os.path.basename(sdir),
                   "classification": None, "missing_layers": ["ALL"],
                   "violations": ["observation_unparseable"],
                   "chain_complete": None, "chain_gaps": [], "seed": None,
                   "activated": None, "submodel": None}
        else:
            rec = audit_observation(obs, sdir, frozen_gem5_sha)
        # campaign-level uniqueness (flag every occurrence after the 1st)
        rid, seed = rec["run_id"], rec["seed"]
        if rid in seen_run_ids:
            rec["violations"] = rec["violations"] + ["duplicate_run_id"]
            if rid not in dup_run_ids:
                dup_run_ids.append(rid)
        seen_run_ids[rid] = seen_run_ids.get(rid, 0) + 1
        if isinstance(seed, int):
            if seed in seen_seeds:
                rec["violations"] = rec["violations"] + ["duplicate_seed"]
                if seed not in dup_seeds:
                    dup_seeds.append(seed)
            seen_seeds[seed] = seen_seeds.get(seed, 0) + 1
        samples.append(rec)

    cls_counts = Counter(s["classification"] for s in samples
                         if s["classification"])
    gaps_by_level = Counter()
    missing_counts = Counter()
    for s in samples:
        for g in s["chain_gaps"]:
            gaps_by_level[g] += 1
        for m in s["missing_layers"]:
            missing_counts[m] += 1

    activated_total = sum(s["activated"] for s in samples
                          if isinstance(s["activated"], int))
    five_sum = sum(cls_counts[c] for c in FIVE_OUTCOME_CLASSES)
    post_sim_fail = sum(1 for s in samples
                        if s["classification"] == "SimulatorError"
                        and isinstance(s["activated"], int)
                        and s["activated"] > 0)
    other_activated = sum(1 for s in samples
                          if s["classification"] in ("Corrected",
                                                     "DetectedContained")
                          and isinstance(s["activated"], int)
                          and s["activated"] > 0)
    n_invalid = sum(1 for s in samples if s["violations"])
    n_l3_gap = sum(1 for s in samples
                   if s["chain_gaps"] == ["L3"]
                   and not s["violations"])
    violation_counts = Counter()
    for s in samples:
        for v in s["violations"]:
            violation_counts[v] += 1
    rollup = {
        "tool": "ooo_chain_audit",
        "schema_version": SCHEMA_VERSION,
        "campaign_dir": os.path.abspath(campaign_dir),
        "frozen_gem5_sha": frozen_gem5_sha,
        "correction_mode": bool(correction_mode),
        "n_samples": len(samples),
        "n_chain_complete": sum(1 for s in samples
                                if s["chain_complete"] is True),
        "n_invalid": n_invalid,
        "n_l3_unsupported_gap": n_l3_gap,
        "violation_counts": dict(violation_counts),
        "gaps_by_level": dict(gaps_by_level),
        "missing_layers_counts": dict(missing_counts),
        "classification_counts": {c: cls_counts[c] for c in NINE_CLASSES
                                  if cls_counts[c]},
        "conservation": {
            "activated_total": activated_total,
            "five_outcome_sum": five_sum,
            "post_activation_simulator_failure": post_sim_fail,
            "other_activated_outcome_classes": other_activated,
            "conserved": (five_sum + post_sim_fail == activated_total
                          and other_activated == 0),
            "note": "five outcome classes = Crash+Hang+SDC+Latent+Masked; "
                    "post-activation simulator failures are derived as "
                    "SimulatorError samples with l0.activated>=1",
        },
        "duplicate_run_ids": dup_run_ids,
        "duplicate_seeds": dup_seeds,
        "n_quarantine_dirs": n_quarantine,
        "samples": samples,
    }
    return rollup


# ---------------------------------------------------------------- reports

def write_reports(campaign_dir, rollup):
    jpath = os.path.join(campaign_dir, "chain_audit.json")
    mpath = os.path.join(campaign_dir, "chain_audit.md")
    with open(jpath, "w") as f:
        json.dump(rollup, f, indent=1, ensure_ascii=False)
    lines = [
        "# chain_audit — %s" % rollup["campaign_dir"],
        "",
        "- n_samples: %d" % rollup["n_samples"],
        "- n_chain_complete: %d" % rollup["n_chain_complete"],
        "- n_invalid (violations non-empty): %d" % rollup["n_invalid"],
        "- n_l3_unsupported_gap (honest L3 gap, not invalid): %d"
        % rollup["n_l3_unsupported_gap"],
        "- violation_counts: %s" % json.dumps(
            rollup.get("violation_counts", {})),
        "- correction_mode: %s%s" % (
            rollup.get("correction_mode", False),
            " (re-audit of legacy data under the CURRENT strict rules; "
            "the violations quantify the correction backlog, not a fresh "
            "admission verdict)" if rollup.get("correction_mode")
            else " (fresh admission audit)"),
        "- gaps_by_level: %s" % json.dumps(rollup["gaps_by_level"]),
        "- missing_layers: %s"
        % json.dumps(rollup["missing_layers_counts"]),
        "- classification_counts: %s"
        % json.dumps(rollup["classification_counts"]),
        "- conservation: %s" % json.dumps(rollup["conservation"]),
        "- duplicate_run_ids: %s" % (rollup["duplicate_run_ids"] or "none"),
        "- duplicate_seeds: %s" % (rollup["duplicate_seeds"] or "none"),
        "- quarantine dirs: %d" % rollup["n_quarantine_dirs"],
        "",
        "| run_id | classification | chain_complete | gaps | "
        "missing_layers | violations |",
        "|---|---|---|---|---|---|",
    ]
    for s in rollup["samples"]:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            s["run_id"], s["classification"], s["chain_complete"],
            ",".join(s["chain_gaps"]) or "-",
            ",".join(s["missing_layers"]) or "-",
            ";".join(s["violations"]) or "-"))
    with open(mpath, "w") as f:
        f.write("\n".join(lines) + "\n")
    return jpath, mpath


# ------------------------------------------------- offline correction audit

def _execution_rows(campaign_dir):
    """Parsed results.jsonl rows carrying a run_id (the runner's
    execution ledger). Unparseable lines are skipped (they fail louder
    audits); a missing file is an honest zero, not an error."""
    p = os.path.join(campaign_dir, "results.jsonl")
    rows = []
    if not os.path.isfile(p):
        return rows
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("run_id"):
                rows.append(r)
    return rows


def correction_audit(campaign_dir, frozen_gem5_sha=None):
    """Offline re-audit of a FINISHED campaign's observations under the
    CURRENT strict rules (Fix-C Task 3, 2026-10-13). Never re-runs a
    sample and never rewrites any original evidence: the only artifact
    is <campaign_dir>/correction_audit.json. Every observation is fully
    audited via audit_observation (files manifest re-hashed); the
    summary quantifies the correction backlog:

      n                    samples audited
      semantic_invalid     samples with any violations
      fake_divergence_count  empty-trace fake divergences
      l3_unsupported       l3_unsupported_with_activation count
      l0_funnel_missing    l0_funnel_missing count
      chain_backfill_required  chain_complete_count <
                           execution_complete_count
    """
    if not os.path.isdir(campaign_dir):
        raise AuditError("campaign dir not found: %s" % campaign_dir)
    sample_dirs, n_quarantine = discover_samples(campaign_dir)
    if not sample_dirs:
        raise AuditError("no sample dirs under %s/samples" % campaign_dir)

    per_sample = []
    n_unparseable = 0
    evidence_readable = 0
    chain_complete_count = 0
    for sdir in sample_dirs:
        opath = os.path.join(sdir, "observation.json")
        obs = None
        if os.path.isfile(opath):
            try:
                with open(opath) as f:
                    obs = json.load(f)
            except (ValueError, OSError):
                obs = None
        if obs is None:
            n_unparseable += 1
            rec = {"run_id": os.path.basename(sdir), "classification": None,
                   "violations": ["observation_unparseable"]}
        else:
            rec = audit_observation(obs, sdir, frozen_gem5_sha)
            if not any(v.startswith(("file_missing", "file_sha_malformed",
                                     "file_sha_mismatch",
                                     "files_manifest_malformed",
                                     "file_path_escape"))
                       for v in rec["violations"]):
                evidence_readable += 1
            if rec["chain_complete"] is True:
                chain_complete_count += 1
        violations = rec["violations"]
        per_sample.append({
            "run_id": rec["run_id"],
            "classification": rec["classification"],
            "violations": violations,
            "l2_zero_trace_fake_divergence": bool(
                "l2_diverged_zero_instructions" in violations
                or "first_divergence_from_empty_trace" in violations),
        })

    def count_v(name):
        return sum(1 for p in per_sample if name in p["violations"])

    execution_complete_count = len(_execution_rows(campaign_dir))
    summary = {
        "n": len(per_sample),
        "semantic_invalid": sum(1 for p in per_sample if p["violations"]),
        "fake_divergence_count": sum(
            1 for p in per_sample if p["l2_zero_trace_fake_divergence"]),
        "l3_unsupported": count_v("l3_unsupported_with_activation"),
        "l0_funnel_missing": count_v("l0_funnel_missing"),
        "chain_backfill_required": (chain_complete_count
                                    < execution_complete_count),
        "l1_valid_zero_snaps": count_v("l1_valid_zero_snaps"),
        "first_divergence_from_empty_trace": count_v(
            "first_divergence_from_empty_trace"),
        "chain_complete_count": chain_complete_count,
        "execution_complete_count": execution_complete_count,
        "evidence_readable_count": evidence_readable,
        "observations_unparseable": n_unparseable,
        "n_quarantine_dirs": n_quarantine,
        "note": "offline re-audit of finished evidence under the current "
                "strict rules; original samples/observations are never "
                "modified, this file is the only artifact",
    }
    return {
        "tool": "ooo_chain_audit.correction-audit",
        "schema_version": "ooo-correction-audit/v1",
        "campaign_dir": os.path.abspath(campaign_dir),
        "frozen_gem5_sha": frozen_gem5_sha,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "per_sample": per_sample,
        "summary": summary,
    }


def write_correction_report(campaign_dir, report):
    jpath = os.path.join(campaign_dir, "correction_audit.json")
    with open(jpath, "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    return jpath


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="L0-L5 observation-chain integrity auditor")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit", help="audit one campaign directory")
    a.add_argument("--campaign-dir", required=True)
    a.add_argument("--require-complete", action="store_true",
                   help="exit 1 if any sample has violations (incl. "
                        "missing observation); honest L3 gaps alone "
                        "do not fail")
    a.add_argument("--frozen-gem5-sha", default=None,
                   help="expected sha256 of build/ARM/gem5.opt; every "
                        "sample's identity.gem5_sha256 must match")
    a.add_argument("--correction-mode", action="store_true",
                   help="annotate the report as a re-audit of legacy "
                        "data under the CURRENT strict rules (tone "
                        "only -- the rules and exit codes are "
                        "identical in both modes)")
    c = sub.add_parser("correction-audit",
                       help="offline re-audit of a FINISHED campaign "
                            "under the current strict rules; writes only "
                            "<campaign_dir>/correction_audit.json, never "
                            "touches the original evidence")
    c.add_argument("--campaign-dir", required=True)
    c.add_argument("--frozen-gem5-sha", default=None,
                   help="expected sha256 of build/ARM/gem5.opt; every "
                        "sample's identity.gem5_sha256 must match")
    args = ap.parse_args(argv)

    if args.cmd == "correction-audit":
        try:
            report = correction_audit(args.campaign_dir,
                                       frozen_gem5_sha=args.frozen_gem5_sha)
        except AuditError as e:
            print("[correction-audit] ERROR: %s" % e, file=sys.stderr)
            return 1
        try:
            jpath = write_correction_report(args.campaign_dir, report)
        except OSError as e:
            print("[correction-audit] ERROR: cannot write report: %s" % e,
                  file=sys.stderr)
            return 1
        s = report["summary"]
        print("[correction-audit] campaign=%s n=%d semantic_invalid=%d "
              "fake_divergence=%d l3_unsupported=%d l0_funnel_missing=%d "
              "chain_backfill_required=%s -> %s"
              % (report["campaign_dir"], s["n"], s["semantic_invalid"],
                 s["fake_divergence_count"], s["l3_unsupported"],
                 s["l0_funnel_missing"], s["chain_backfill_required"],
                 jpath))
        return 0

    try:
        rollup = audit_campaign(args.campaign_dir,
                                frozen_gem5_sha=args.frozen_gem5_sha,
                                correction_mode=args.correction_mode)
    except AuditError as e:
        print("[chain_audit] ERROR: %s" % e, file=sys.stderr)
        return 1
    try:
        jpath, mpath = write_reports(args.campaign_dir, rollup)
    except OSError as e:
        print("[chain_audit] WARNING: could not write reports: %s" % e,
              file=sys.stderr)
        jpath = mpath = None

    mode_tag = ("%scorrection-mode: re-audit of legacy data; violations "
                "below quantify the correction backlog"
                % ("[chain_audit] ",)) if args.correction_mode else ""
    if mode_tag:
        print(mode_tag)
    print("[chain_audit] campaign=%s n_samples=%d n_chain_complete=%d "
          "n_invalid=%d n_l3_unsupported_gap=%d conserved=%s"
          % (rollup["campaign_dir"], rollup["n_samples"],
             rollup["n_chain_complete"], rollup["n_invalid"],
             rollup["n_l3_unsupported_gap"],
             rollup["conservation"]["conserved"]))
    if rollup.get("violation_counts"):
        print("[chain_audit] violation_counts=%s"
              % json.dumps(rollup["violation_counts"]))
    for s in rollup["samples"]:
        if s["violations"]:
            print("[chain_audit] INVALID %s: %s"
                  % (s["run_id"], ";".join(s["violations"])))
    if jpath:
        print("[chain_audit] wrote %s and %s" % (jpath, mpath))
    if args.require_complete and rollup["n_invalid"] > 0:
        print("[chain_audit] FAIL (--require-complete): %d sample(s) with "
              "violations" % rollup["n_invalid"])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
