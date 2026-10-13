#!/usr/bin/env python3
"""ooo_observation.py -- L0-L5 per-sample observation assembly (plan Task 5).

Pure module: consumes the artifacts the sample runner produces (injection
log text, micro_diff/commit_diff/fanout JSON, the runner RESULT line
fields) and assembles + validates the observation.json that pins ONE
sample's L0-L5 chain. It never runs gem5 and never spawns a subprocess.

Honesty contract (task-book 2.5/2.7):
  * absent/unknown evidence becomes a status=error / status=unsupported
    block with a reason -- never silently omitted, never fabricated as
    zero;
  * a truncated gzip prefix is PASSED THROUGH (the diff tools already
    salvage it); a clean prefix is never claimed as no-divergence
    evidence (l2 status not_observed_before_crash);
  * L3 fanout exists ONLY for the PRF (method=proxy + caveat); every
    other component is unsupported and costs chain_complete (gap L3);
  * L0 funnel counts are REAL per-line counts of the injector's log
    (fix-A Task 1): attempted = skip lines + injection lines, eligible =
    injection lines (faults actually written), injected = the final
    faults_injected counter, and the l0 block carries a `limited` note
    naming what the C++ injectors do NOT log (gate rejections before
    the log point), so attempted is a lower bound of hook-level
    inspections. Without a log (no source) attempted/eligible are None,
    never a silent 0.

Vocabulary (one classifier, no drift): the L5 classes are wilson.py's
ALL_CLASSES; the five MAIN outcomes of an activated fault in this track
are masked/sdc/crash/hang/latent, plus corrected/detected_contained
(protection-track classes, kept at 0 here) and the
post_activation_simulator_failure bucket.
"""

import hashlib
import json
import os
import re
import time

OBSERVATION_SCHEMA_VERSION = "ooo-observation/v1"

# manifest target.component -> the injector's log file inside the gem5 -d
# outdir. The log names mirror runner.py's INJECTION_LOGS search list;
# the component-to-log pairing is the gem5 source of truth (CHAOSReg and
# CHAOSPhysReg both write fault_injections.log, CHAOSRenameMap writes
# rename_injections.log, CHAOSDecode decode_injections.log, ...).
LOG_FOR_COMPONENT = dict(
    gpr="fault_injections.log",
    physreg="fault_injections.log",
    memory="main_mem_injections.log",
    l1d="cache_injections.log",
    rat="rename_injections.log",
    freelist="freelist_injections.log",
    rob="rob_injections.log",
    iq="iq_injections.log",
    lsq_fwd="lsq_fwd_injections.log",
    exec="exec_injections.log",
    fsu="fpu_injections.log",
)
LOG_FOR_COMPONENT.update(dict(
    l1d_fwd="l1d_fwd_injections.log",
    bpu="bpu_injections.log",
    decode="decode_injections.log",
    ras="ras_injections.log",
    exmon="exmon_injections.log",
    addr_path="addrpath_injections.log",
    ptw="ptw_injections.log",
    l1_tlb="armtlb_injections.log",
    sysreg="sysreg_injections.log",
))

FIVE_MAIN_OUTCOMES = ("masked", "sdc", "crash", "hang", "latent")
EXTRA_OUTCOMES = ("corrected", "detected_contained")
CLASS_TO_OUTCOME = dict(
    Masked="masked", SDC="sdc", Crash="crash", Hang="hang",
    Latent="latent", Corrected="corrected",
    DetectedContained="detected_contained")
KNOWN_CLASSES = ("SimulatorError", "Inactive", "Corrected",
                 "DetectedContained", "Crash", "Hang", "SDC", "Latent",
                 "Masked")

# l4 first-detection source (task-book: four-way, no others)
DETECTOR_FOR_CLASS = dict(Masked=None, SDC="Application", Crash="OS",
                          Hang="OS", SimulatorError="n/a", Inactive="n/a")
FIRST_DETECTION_KIND = dict(SDC="checksum_mismatch",
                            Crash="abnormal_termination",
                            Hang="timeout")

L1_STATUSES = ("ok", "truncated", "error", "inactive_no_activation",
               "no_snapshots_before_crash")
L2_STATUSES = ("ok", "not_observed_before_crash", "error",
               "inactive_no_activation")
L3_STATUSES = ("ok", "unsupported", "error", "inactive_no_activation")
L4_STATUSES = ("ok", "none_detected", "error", "inactive_no_activation")

IDENTITY_FIELDS = ("run_id", "campaign_id", "runid_row", "submodel",
                   "sample_index", "phase", "seed", "manifest_sha256",
                   "gem5_sha256", "config", "workload", "golden_key",
                   "chaos_commit", "patchset_sha256", "pythonhashseed",
                   "host", "started", "finished", "wall_s")
CORE_KEYS = ("schema_version", "identity", "l0", "l1", "l2", "l3", "l4",
             "l5", "replay", "files", "coverage_scope", "audit")

# coordinator contract (2026-10-12): replay lives at the TOP LEVEL
# observation.replay with ALL keys present even when not performed
# (honest nulls); it is NOT duplicated inside l2.
REPLAY_FIELDS = ("performed", "pass2_classification", "determinism",
                 "verdict_pass2", "checksum_pass2", "performed_at")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# ------------------------------------------------------------------ L0 parse

_MARKER_RE = re.compile(r"faults_injected:\s*(\d+)")
_ELIGIBLE_RE = re.compile(r"CHAOS_ELIGIBLE_COUNT=(\d+)")
_INT_RE = re.compile(r"-?[0-9]+")


def _split_top(line):
    """Split a log line on commas OUTSIDE () [] groups, so values like
    bits=(3,4) or (skipped, no clamp) survive as one token."""
    parts, depth, cur = [], 0, []
    for ch in line:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur).strip())
    return [p for p in parts if p]


def _parse_log_line(line):
    """Tick: N, Site: X, k=v, ... -> a dict of row fields."""
    d = dict()
    for tok in _split_top(line):
        if tok.startswith("Tick:"):
            try:
                d["tick"] = int(tok.split(":", 1)[1].strip())
            except ValueError:
                d["tick_raw"] = tok
        elif tok.startswith("Site:"):
            d["site"] = tok.split(":", 1)[1].strip()
        elif "=" in tok:
            k, v = tok.split("=", 1)
            k = k.strip()
            v = v.strip()
            d[k] = int(v) if _INT_RE.fullmatch(v) else v
    return d


def parse_injection_log(path, component):
    """Parse one injector's evidence log into the L0 funnel.

    `path` is either the gem5 result dir (the component->log mapping
    above resolves the file) or the log file itself. Lines carrying the
    "faults_injected: N" marker follow the log contract (runner.py
    marker-wins): a marker line is an EVENT when its counter INCREASED
    (the injection happened on that line), a SKIP when it did not.
    Marker-less logs (CHAOSPhysReg Cycle:-lines, ...) are counted with
    runner.py's exact exclusion rules.

    Funnel semantics (fix-A Task 1, per-line real counts):
      attempted = len(events) + len(skips) -- every LOGGED event the
                  injector actually inspected (draw-passing events that
                  reached the mode-specific check)
      eligible  = len(events) -- injection event lines: events where a
                  fault was actually WRITTEN
      injected  = the final faults_injected counter value (marker logs)
                  or the runner-style line count (marker-less logs)
    LIMITED (honest scope note, also carried as l0.limited): the C++
    injectors do NOT log events rejected before the log point -- the
    injection-window gate, the max_faults cap, the geometric skip, the
    probability draw, and the pre-draw cheap eligibility checks of
    D01-D07 (see CHAOSDecode.cc maybeCorrupt/maybeCorruptEncoding) --
    so `attempted` is a LOWER BOUND of hook-level inspections, not the
    hook invocation count. The log distinguishes attempted from eligible
    exactly (skip lines carry the unchanged counter, injection lines the
    incremented one), so neither count is null when a log exists.

    A missing log is NO SOURCE: attempted/eligible are None (honest
    n/a), never a silent 0. eligible_count is a SEPARATE injector
    self-reported counter from a CHAOS_ELIGIBLE_COUNT= line (written at
    teardown by CHAOSLSQFwd/CHAOSExec only; CHAOSDecode never writes
    one).

    Returns dict(injected, events, skips, eligible_count, eligible,
    attempted, truncated, log_path, log_exists).
    """
    log_path = path
    if os.path.isdir(path):
        if component not in LOG_FOR_COMPONENT:
            raise ValueError("unknown injector component %r; known: %s"
                             % (component, sorted(LOG_FOR_COMPONENT)))
        log_path = os.path.join(path, LOG_FOR_COMPONENT[component])
    if not os.path.exists(log_path):
        return dict(injected=0, events=[], skips=[], eligible_count=None,
                    eligible=None, attempted=None, truncated=False,
                    log_path=log_path, log_exists=False)
    with open(log_path, "r", errors="replace") as f:
        text = f.read()
    events, skips = [], []
    injected = 0
    last_counter = None
    eligible = None
    for line in text.splitlines():
        if not line.strip():
            continue
        m = _ELIGIBLE_RE.search(line)
        if m:
            eligible = int(m.group(1))
        mk = _MARKER_RE.search(line)
        if mk:
            counter = int(mk.group(1))
            rec = _parse_log_line(line)
            rec["faults_injected"] = counter
            rec["raw"] = line
            is_event = counter > 0 and (last_counter is None
                                        or counter > last_counter)
            if is_event:
                events.append(rec)
            else:
                skips.append(rec)
            last_counter = counter
            injected = counter
            continue
        # marker-less line families: mirror runner.py's counting rules
        if (line.startswith("ReadTracePoll")
                or line.startswith("ReadTraceFinal")):
            continue
        if "DIRECTED reg:" in line:
            continue
        if line.lstrip().startswith("protection:"):
            continue
        if "DUPLICATE_ALLOCATION:" in line:
            continue
        if ("Inactive" in line) or line.startswith("Error"):
            rec = _parse_log_line(line)
            rec["raw"] = line
            skips.append(rec)
            continue
        if line.strip():
            rec = _parse_log_line(line)
            rec["raw"] = line
            events.append(rec)
    if last_counter is None:
        injected = len(events)  # runner-style line counting
    return dict(injected=injected, events=events, skips=skips,
                eligible_count=eligible, eligible=len(events),
                attempted=len(events) + len(skips), truncated=False,
                log_path=log_path, log_exists=True)

# ------------------------------------------------------------- conservation


def conservation_for(activated, classification):
    """activated == five-main-outcomes sum + corrected + detected_contained
    + post_activation_simulator_failure, per sample (each bucket is a 0/1
    indicator). Vocabulary drift (a class outside wilson.ALL_CLASSES) is
    conserved=False -- loud, never waved through."""
    activated = int(activated or 0)
    cons = dict(activated=activated)
    for k in FIVE_MAIN_OUTCOMES + EXTRA_OUTCOMES:
        cons[k] = 0
    cons["post_activation_simulator_failure"] = 0
    outcome = CLASS_TO_OUTCOME.get(classification)
    if classification == "Inactive":
        pass  # activated must be 0; no outcome bucket
    elif classification == "SimulatorError":
        cons["post_activation_simulator_failure"] = 1 if activated else 0
    elif outcome is not None:
        cons[outcome] = 1
    total = sum(cons[k] for k in FIVE_MAIN_OUTCOMES + EXTRA_OUTCOMES)
    total += cons["post_activation_simulator_failure"]
    known = outcome is not None or classification in ("Inactive",
                                                      "SimulatorError")
    cons["five_primary_sum"] = sum(cons[k] for k in FIVE_MAIN_OUTCOMES)
    cons["conserved"] = bool(known and activated == total)
    # plan Task 5 schema keys (the C-domain audit reads .ok); the
    # per-class indicator counts above are a kept superset
    cons["ok"] = cons["conserved"]
    if not known:
        cons["notes"] = ("classification outside the 9-class vocabulary "
                         "(wilson.ALL_CLASSES)")
    elif classification == "SimulatorError" and activated:
        cons["notes"] = ("tool failure AFTER activation: counted in "
                         "post_activation_simulator_failure, excluded "
                         "from the 385 valid denominator")
    else:
        cons["notes"] = ""
    return cons


def l2_status_from(commit_diff, classification):
    """l2.status semantics (task contract):
      commit_diff missing or l2_error                  -> error
      truncated prefix, NO divergence, Crash/Hang      -> not_observed_before_crash
      truncated prefix WITH divergence                 -> ok (flag passthrough)
      truncated prefix, no divergence, other classes   -> error (unexpected:
                                                          a completed run
                                                          finalizes its gzip)
      otherwise                                        -> ok
    inactive_no_activation is set by the caller (no diff was attempted).
    """
    if not isinstance(commit_diff, dict) or commit_diff.get("l2_error"):
        return "error"
    run_trunc = bool(commit_diff.get("run_truncated")
                     or commit_diff.get("ref_truncated"))
    has_div = commit_diff.get("first_divergence") is not None
    if run_trunc and not has_div:
        if classification in ("Crash", "Hang"):
            return "not_observed_before_crash"
        return "error"
    return "ok"

# ----------------------------------------------------- l4 first detection


def tick_from_ctrace_raw(raw):
    """3rd CSV field of a ctrace line is the commit tick; None otherwise."""
    if not raw:
        return None
    try:
        return int(raw.split(",")[2])
    except (IndexError, ValueError):
        return None


def first_detection_for(classification, commit_diff=None):
    """l4.first_detection: kind/detector per the four-way table, tick/seq
    from the first L2 divergence when one exists (honest None when the
    outcome left no divergence point, e.g. a crash with a clean prefix)."""
    fd = dict(kind=FIRST_DETECTION_KIND.get(classification),
              detector=DETECTOR_FOR_CLASS.get(classification, "n/a"),
              tick=None, seq=None, note="")
    div = None
    if isinstance(commit_diff, dict):
        div = commit_diff.get("first_divergence")
    if div:
        fd["seq"] = div.get("seq")
        # RUN-side tick only: a one-sided divergence (the run trace ended
        # early) has no run line, and the ref-side tick would predate the
        # injection -- a misleading "negative latency", not evidence
        fd["tick"] = tick_from_ctrace_raw(div.get("run_line"))
    if classification == "SDC":
        fd["note"] = ("application checksum mismatch; first L2 divergence "
                      "seq recorded")
    elif classification == "Crash":
        fd["note"] = "workload trapped/aborted under the fault (OS channel)"
    elif classification == "Hang":
        fd["note"] = "exceeded hang timeout with no checksum (OS channel)"
    elif classification == "Masked":
        fd["note"] = "no detection: fault masked (checksum matches golden)"
    else:
        fd["note"] = "no first-detection semantics for this class"
    return fd

# -------------------------------------------------------- build observation


def _err(reason):
    return dict(status="error", reason=reason)


def build_observation(ctx):
    """Assemble the full observation dict from ctx (identity/l0/l1/l2/l3/
    l4/l5/files/coverage_scope/audit). A missing sub-block becomes a
    status=error block with a reason -- never silently omitted. Derived
    fields (conservation, detector, first_detection) are filled in when
    the ctx did not supply them; violations / chain_complete / chain_gaps
    are computed here so the written observation.json is self-contained.
    """
    ctx = dict(ctx or {})
    identity = ctx.get("identity") or dict()
    l0 = dict(ctx.get("l0") or _err("l0 missing"))
    if "activated" not in l0:
        inj = l0.get("injected")
        l0["activated"] = inj if isinstance(inj, int) else 0
    l5 = dict(ctx.get("l5") or _err("l5 missing"))
    cls = l5.get("classification")
    if not l5.get("conservation"):
        l5["conservation"] = conservation_for(l0["activated"], cls)
    if not l5.get("detector"):
        l5["detector"] = DETECTOR_FOR_CLASS.get(cls, "n/a")
    l4 = dict(ctx.get("l4") or _err("l4 missing"))
    if not l4.get("first_detection"):
        cd = (ctx.get("l2") or dict()).get("commit_diff")
        l4["first_detection"] = first_detection_for(cls, cd)
    if not l4.get("detector"):
        l4["detector"] = l5.get("detector")
    l1 = dict(ctx.get("l1") or _err("l1 diff missing"))
    l2 = dict(ctx.get("l2") or _err("l2 diff missing"))
    if "coverage" not in l2:
        l2["coverage"] = dict(mode="n/a", seq_lo=None, seq_hi=None,
                              note="not provided")
    if "commit_diff" not in l2:
        l2["commit_diff"] = None
    if "first_divergent_commit" not in l2:
        l2["first_divergent_commit"] = (
            l2["commit_diff"].get("first_divergence")
            if isinstance(l2["commit_diff"], dict) else None)
    if "files" not in l2:
        l2["files"] = dict()
    if "files" not in l1:
        l1["files"] = dict()
    l3 = dict(ctx.get("l3") or _err("l3 missing"))
    # contract: the five l3 keys are ALWAYS present (null when not
    # applicable) -- consumers must never see a missing key
    for k in ("method", "fanout", "caveat", "reason"):
        l3.setdefault(k, None)
    files = ctx.get("files") or dict()
    coverage_scope = ctx.get("coverage_scope") or dict(
        mode="n/a", note="not provided")
    audit = ctx.get("audit") or dict(
        built_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        builder_sha256=sha256_file(__file__))
    replay = ctx.get("replay")
    if not isinstance(replay, dict):
        replay = dict()
    rbase = dict(performed=False, pass2_classification=None,
                 determinism=None, verdict_pass2=None, checksum_pass2=None,
                 performed_at=None)
    rbase.update(replay)
    replay = rbase
    obs = dict(schema_version=OBSERVATION_SCHEMA_VERSION, identity=identity,
               l0=l0, l1=l1, l2=l2, l3=l3, l4=l4, l5=l5, replay=replay,
               files=files, coverage_scope=coverage_scope, audit=audit)
    ok, violations = validate_observation(obs)
    obs["violations"] = violations
    complete, gaps = chain_completeness(obs)
    obs["chain_complete"] = complete
    obs["chain_gaps"] = gaps
    return obs

# ----------------------------------------------------------- validate


def validate_observation(obs):
    """Structure + conservation + per-class consistency. Returns
    (ok, violations). Crash/Hang may lack a checksum (the process died
    before printing FINAL) -- that is NOT a violation."""
    v = []

    def need(cond, msg):
        if not cond:
            v.append(msg)

    if not isinstance(obs, dict):
        return (False, ["observation is not a dict"])
    for k in CORE_KEYS:
        need(k in obs, "missing top-level key %s" % k)
    need(obs.get("schema_version") == OBSERVATION_SCHEMA_VERSION,
         "schema_version mismatch: %r" % obs.get("schema_version"))
    ident = obs.get("identity") or dict()
    for f in IDENTITY_FIELDS:
        need(f in ident, "identity missing %s" % f)
    for sub, fields in (("config", ("path", "sha256")),
                        ("workload", ("path", "sha256", "golden_id"))):
        subd = ident.get(sub)
        need(isinstance(subd, dict) and all(k in subd for k in fields),
             "identity.%s incomplete" % sub)
    l0 = obs.get("l0") or dict()
    need(isinstance(l0.get("injected"), int), "l0.injected must be int")
    need(isinstance(l0.get("activated"), int),
         "l0.activated must be int (landed injection count)")
    need(0 <= (l0.get("activated") or 0) <= (l0.get("injected") or 0),
         "l0.activated must be within [0, l0.injected]")
    # fix-A Task 1 funnel invariant, checked only when every count is an
    # int (a missing log leaves attempted/eligible None -- no source, no
    # check; legacy observations without `eligible` also skip it)
    funnel = [l0.get(k) for k in ("attempted", "eligible", "injected",
                                  "activated")]
    if all(isinstance(x, int) for x in funnel):
        need(funnel[0] >= funnel[1] >= funnel[2] >= funnel[3],
             "l0 funnel invariant violated: attempted=%s < eligible=%s < "
             "injected=%s < activated=%s must be monotone "
             "attempted >= eligible >= injected >= activated"
             % tuple(funnel))
    l5 = obs.get("l5") or dict()
    cls = l5.get("classification")
    need(cls in KNOWN_CLASSES,
         "l5.classification %r not in the 9-class vocabulary" % cls)
    cons = l5.get("conservation") or dict()
    need(cons.get("conserved") is True,
         "conservation not satisfied: %s" % json.dumps(cons, sort_keys=True))
    activated = cons.get("activated", 0)
    need(activated == l0.get("activated"),
         "l5.conservation.activated != l0.activated")
    if cls == "Inactive":
        need(activated == 0,
             "Inactive classification but conservation.activated != 0")
        need((l0.get("injected") or 0) == 0,
             "Inactive classification but l0.injected >= 1 (fault landed)")
    if cls == "Masked":
        need(l5.get("checksum_observed") is not None
             and l5.get("checksum_observed") == l5.get("checksum_golden"),
             "Masked but checksum_observed != checksum_golden")
        need(activated >= 1, "Masked but activated == 0")
    if cls == "SDC":
        need(l5.get("checksum_observed") is not None
             and l5.get("checksum_observed") != l5.get("checksum_golden"),
             "SDC but checksum_observed == checksum_golden (or missing)")
    l5det = l5.get("detector")
    if l5det is not None:
        need(l5det == DETECTOR_FOR_CLASS.get(cls, "n/a"),
             "l5.detector %r does not match the four-way table for %s"
             % (l5det, cls))
    for lvl, allowed in (("l1", L1_STATUSES), ("l2", L2_STATUSES),
                         ("l3", L3_STATUSES), ("l4", L4_STATUSES)):
        blk = obs.get(lvl) or dict()
        need(blk.get("status") in allowed,
             "%s.status %r not in %s" % (lvl, blk.get("status"), allowed))
    l3 = obs.get("l3") or dict()
    need(all(k in l3 for k in ("status", "method", "fanout", "caveat",
                               "reason")),
         "l3 must always carry status/method/fanout/caveat/reason")
    if l3.get("status") == "unsupported":
        need(bool(l3.get("reason")),
             "l3 unsupported without a reason (honesty contract)")
    # fix-A Task 2: "no observation possible" must never masquerade as
    # "divergence observed" -- with a 0-line run trace (crash before the
    # first commit flush) no commit_diff is run at all, so a
    # not_observed_before_crash L2 carrying a first_divergent_commit is
    # a fabrication and a hard violation
    l2blk = obs.get("l2") or dict()
    if l2blk.get("status") == "not_observed_before_crash":
        need(l2blk.get("first_divergent_commit") is None,
             "l2.status not_observed_before_crash but "
             "first_divergent_commit is not null (no observation was "
             "possible -- a divergence claim here is fabricated)")
    return (len(v) == 0, v)

# ----------------------------------------------------- chain completeness


def chain_completeness(obs):
    """(complete, gaps). Gap labels are level names (L1..L5).

    activated==0: L1-L4 must all be inactive_no_activation; if so the
    chain is COMPLETE (L0+L5 suffice -- no real observation gap).

    activated>=1: L1 ok (truncated accepted for Crash/Hang -- the sim
    dying is the observation, not a chain failure), L2 ok, L4 in
    ok/none_detected, L5 classified with conservation satisfied, no
    violations, and the L3 rule: physreg -> status ok + method proxy
    (chain_complete may be true); every other component -> status
    unsupported -> gap L3 (task-book: never faked).

    fix-A Task 2 (central mandate): l2 not_observed_before_crash and l1
    no_snapshots_before_crash are HONEST states -- never violations --
    but they are ABSENCE of observation, not completed links: they do
    not constitute chain-completeness evidence and cost gaps L2/L1.
    (Only l1 "truncated" stays Crash-acceptable: a salvaged snapshot
    prefix is partial but real observation.)
    """
    gaps = []
    l0 = obs.get("l0") or dict()
    l5 = obs.get("l5") or dict()
    cons = l5.get("conservation") or dict()
    activated = cons.get("activated",
                         1 if (l0.get("injected") or 0) >= 1 else 0)
    cls = l5.get("classification")
    if obs.get("violations"):
        gaps.append("L5")
    if not cls:
        gaps.append("L5")
    if not cons.get("conserved"):
        if "L5" not in gaps:
            gaps.append("L5")
    if activated == 0:
        for lvl in ("l1", "l2", "l3", "l4"):
            status = (obs.get(lvl) or dict()).get("status")
            if status != "inactive_no_activation":
                gaps.append(lvl.upper())
    else:
        cls_crash = cls in ("Crash", "Hang")
        l1s = (obs.get("l1") or dict()).get("status")
        if l1s != "ok" and not (cls_crash and l1s == "truncated"):
            gaps.append("L1")
        l2s = (obs.get("l2") or dict()).get("status")
        if l2s != "ok":
            gaps.append("L2")
        l3 = obs.get("l3") or dict()
        if l3.get("status") == "ok":
            # FIX-B integration: "proxy" = PRF liveness window (the
            # task-book-sanctioned approximation); "source_read" = the
            # real source->consumer chain from a v2 ctrace (ooo_l3).
            # Both are completed L3 links; anything else (or a missing
            # method) is a gap.
            if l3.get("method") not in ("proxy", "source_read"):
                gaps.append("L3")
        else:
            gaps.append("L3")
        l4s = (obs.get("l4") or dict()).get("status")
        if l4s not in ("ok", "none_detected"):
            gaps.append("L4")
    seen, out = set(), []
    for g in gaps:
        if g not in seen:
            seen.add(g)
            out.append(g)
    return (len(out) == 0, out)

# ------------------------------------------------------------ l0 assembly


def l0_block_from(path, component):
    """Assemble the observation's l0 block from the injector log.
    `path` is the gem5 result dir (or the log file), per
    parse_injection_log. A missing log is status=no_log with a zero
    injected count and attempted/eligible=None (no source -- honest
    n/a, never a silent 0).

    activated derivation (fix-A Task 1 docstring mandate): this track
    is single-fault, so activated := injected. The classification-aware
    rule "0 if classification == Inactive else injected" gives the same
    value on every VALID sample: validate/conservation require
    Inactive => injected == 0 (an Inactive sample with a landed fault
    is a conservation violation and is quarantined, never published),
    so the Inactive branch collapses to activated == injected == 0.
    l5.conservation.activated MUST equal this value (checked by
    validate).

    `limited` names the honest scope of the funnel counts: the C++
    injectors do not log events rejected before the log point (window
    gate, max_faults cap, geometric skip, probability draw, pre-draw
    cheap eligibility), so attempted/eligible count LOGGED events only
    and attempted is a lower bound of hook-level inspections.
    """
    funnel = parse_injection_log(path, component)
    if funnel["log_exists"]:
        status = "ok"
        log_sha = sha256_file(funnel["log_path"])
        limited = ("attempted/eligible count LOGGED events only (marker "
                   "lines: injection events + honest skips); the C++ "
                   "injectors do not log gate rejections before the log "
                   "point (injection-window, max_faults cap, geometric "
                   "skip, probability draw, pre-draw cheap eligibility "
                   "for D01-D07), so attempted is a lower bound of "
                   "hook-level inspections; eligible == injection event "
                   "lines == faults actually written")
        # [FIX-RB] admission-gate vocabulary: semantic_gate_violations
        # reads funnel_limited_reason / limited_reason when the funnel
        # has an n/a field. eligible_count is n/a whenever this log
        # carries no CHAOS_ELIGIBLE_COUNT= self-report -- decode/rat
        # injectors never write one (only CHAOSLSQFwd/CHAOSExec do, at
        # teardown; a crash before teardown also loses it). Documented
        # n/a: attempted/eligible stay the real per-line counts, and
        # this can never mask a missing log (that case is status=no_log
        # below, which the gate already covers on its own).
        if funnel["eligible_count"] is None:
            limited_reason = (
                "eligible_count n/a: no CHAOS_ELIGIBLE_COUNT= self-report "
                "in this injector log (only CHAOSLSQFwd/CHAOSExec write "
                "one, at teardown; decode/rat injectors never do, and a "
                "crash before teardown loses it). attempted=%d / "
                "eligible=%d are the real per-line logged counts "
                "(injection events + honest skips / injection events)."
                % (funnel["attempted"], funnel["eligible"]))
        else:
            limited_reason = None
    else:
        status = "no_log"
        log_sha = None
        limited = ("no injector log retained: attempted/eligible have no "
                   "source (None, honest n/a)")
        limited_reason = None
    return dict(
        status=status, component=component,
        log_name=os.path.basename(funnel["log_path"]),
        log_sha256=log_sha, injected=funnel["injected"],
        activated=funnel["injected"],
        eligible_count=funnel["eligible_count"],
        eligible=funnel["eligible"],
        attempted=funnel["attempted"], events=funnel["events"],
        skips=funnel["skips"], skip_lines=len(funnel["skips"]),
        limited=limited, limited_reason=limited_reason,
        truncated=funnel["truncated"])
