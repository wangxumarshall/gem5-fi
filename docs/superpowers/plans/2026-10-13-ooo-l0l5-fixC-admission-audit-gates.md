# OOO L0-L5 Fix-C: Admission/Audit Gate Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement
> this plan task-by-task (Subagent-C is the dedicated implementer; the central task brief
> mandates immediate execution, no user review loop). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make the L0-L5 audit/admission gates strictly FAIL on the five semantic holes the
four completed formal campaigns exposed (L3-unsupported-with-activation, missing L0 funnel,
empty-trace fake divergences, ok-L1-with-zero-snaps), split handoff execution/chain status
fields, and produce offline `correction_audit.json` re-audits for the four formal campaign
dirs — never relaxing a rule and never rewriting original evidence.

**Architecture:** All five new mandatory-FAIL rules live in one pure function
`semantic_gate_violations(obs)` inside `tools/ooo_chain_audit.py`, called by the existing
`_check_layers` (so `audit`/`audit_observation` inherit them), by `ooo_handoff.py` (for the
new split fields), and by `tools/tests/e2e/ooo_l0l5_admission.py` (new "chain" item). A new
`correction-audit` CLI subcommand reuses `audit_observation` per sample and writes only
`<campaign_dir>/correction_audit.json`. Old fields are kept for compatibility; new fields
are additive.

**Tech Stack:** Python 3 stdlib only (argparse, json, hashlib, os, collections). No gem5
rebuild (tools/ only). Tests are plain scripts with process exit codes, run with
`python3 tools/tests/...`.

**Spec:** Central task brief "OOO 观测链纠偏 Subagent-C（准入与审计门修复）" (2026-10-13,
delivered in the agent prompt; frozen facts quoted inline below). Worktree:
`/home/sdc/gem5-fi-ding/.claude/worktrees/ooo-fixC`, branch `ooo/l0l5-fixC`, base 2a25073.

## Global Constraints

- Work ONLY in `/home/sdc/gem5-fi-ding/.claude/worktrees/ooo-fixC` (branch `ooo/l0l5-fixC`).
- File ownership (only these): `tools/ooo_chain_audit.py`, `tools/ooo_handoff.py`,
  `tools/tests/e2e/ooo_l0l5_admission.py`, `tools/tests/e2e/ooo_l0l5_e2e.py` (admission
  assertion parts only — current design needs NO change there), `tools/tests/test_ooo_chain_audit.py`,
  `tools/tests/test_ooo_handoff.py`, plus this plan file.
- Forbidden to modify: `ooo_observation.py`, `ooo_sample_runner.py`, `runner.py`,
  `commit_diff.py`, `ooo_l3.py`, guard/scheduler, any C++.
- Gates only get STRICTER, never relaxed. Old samples producing mass violations under the
  new rules is intended — the correction audit quantifies it.
- Original evidence is never rewritten: `correction-audit` writes only
  `<campaign_dir>/correction_audit.json` (runs/ is untracked data, not committed).
- One commit per task, message prefix `[OOO][FIX-C]`, NO Co-Authored-By line, do NOT push.
- Self-test scratch dirs stay under the sanctioned selftest roots (never /tmp bare):
  `OOO_SELFTEST_ROOT`/`OOO_ADMISSION_SELFTEST_ROOT` env or their
  `/home/sdc/gem5-fi-ding/runs/ooo-l0l5/selftest/...` defaults.
- Campaign data lives in the MAIN repo at `/home/sdc/gem5-fi-ding/runs/formal_{D01-F0-W6-c,
  D02-F0-W6-b,D02-F0-W6-c,D04-F0-W4-d}` (untracked; read-only for us except the new
  correction_audit.json). Frozen gem5 sha for these runs:
  `1a618953b014514713c0ad98c7f3d69a48171d81f0463d934bccdfcfc0070bf3`.

### Frozen facts about the four formal campaigns (measured 2026-10-13, main repo)

- `formal_D02-F0-W6-b`, `formal_D02-F0-W6-c`, `formal_D04-F0-W4-d`: 385/385 results.jsonl
  rows, 385 sample dirs each. `formal_D01-F0-W6-c`: **still running** at plan time
  (377 rows at 09:50; scheduler PID 2231448 active) — re-check completion before Task 5.
- All samples: `l0.attempted=null`, `l0.eligible_count=null`, `l3.status=unsupported`
  (activated=1), `chain_complete=false`, `chain_gaps=["L3"]`.
- Zero-trace Crash pattern (fake divergence): `l2.status=ok`,
  `commit_diff.verdict=diverged`, `run_instructions=0`, `aligned_pairs=0`,
  `first_divergence={seq:0, class:"instruction_flow_change", level:"presence",
  run_line:null}`. Counts: D01-c 38, D02-b 99, D02-c 147, D04-d 96.
  Non-zero-trace Crash/Hang samples (run_instructions>0, e.g. 2297/3000071) are honest
  partial traces and must NOT be flagged.
- Old audit verdict (the bug being fixed): D02-b `chain_audit.json` says `n_invalid: 0`,
  `n_l3_unsupported_gap: 385` — i.e. all-false chains and fake divergences passed.

## Review Focus (input classes the brief implies but old tests never exercised)

1. Activated sample with `l3.status=unsupported` must FAIL admission (was counted as
   "honest gap", PASS) — Task 1 fixture f9 + Task 4 negative (a).
2. `l0.attempted`/`eligible_count` null on an activated sample must FAIL (was silently
   accepted) — Task 1 fixture f10 + Task 4 negative (b).
3. `verdict=diverged` with `run_instructions=0` (empty run trace) is a fake divergence and
   must FAIL, while the same verdict with `run_instructions>0` must stay clean — Task 1
   fixture f11 (both directions) + Task 4 negative (c).
4. `l1.status="ok"` with `snaps_run` 0/missing must FAIL, while `l1.status="truncated"`
   with `snaps_run=0` (honest crash record) must stay clean — Task 1 fixture f12 (both
   directions).
5. A campaign where 100% of samples have `chain_complete=false` must FAIL admission
   overall (never "all-false still PASS") — Task 4 negative (d), plus handoff
   `chain_backfill_required=true` so `status=COMPLETE` cannot masquerade as a full chain
   (Task 2 assertions).

---

### Task 1: Five semantic-gate violations + `--correction-mode` + violation counts (ooo_chain_audit.py)

**Files:**
- Modify: `tools/ooo_chain_audit.py` (new function `semantic_gate_violations`, hook into
  `_check_layers`, rollup `violation_counts`, CLI `--correction-mode`)
- Test: `tools/tests/test_ooo_chain_audit.py` (update fixtures 1/3/8 to the strict
  contract; add fixtures 9–12)

**Interfaces:**
- Produces: `semantic_gate_violations(obs: dict) -> list[str]` — public, pure (no file
  hashing, no identity checks); returns a subset of
  `SEMANTIC_GATE_VIOLATIONS = ("l3_unsupported_with_activation", "l0_funnel_missing",
  "l2_diverged_zero_instructions", "l1_valid_zero_snaps",
  "first_divergence_from_empty_trace")`. Consumed by `_check_layers` (same file),
  Task 2 (ooo_handoff) and Task 4 (admission).
- Produces: rollup key `"violation_counts": {violation_name: n}` in `audit_campaign`
  output / chain_audit.json; `"correction_mode": bool` when `audit --correction-mode`.
- Existing signatures (`audit_observation(obs, sample_dir, frozen_gem5_sha=None)`,
  `audit_campaign(campaign_dir, frozen_gem5_sha=None)`) are UNCHANGED.

Rule semantics (all scoped to `isinstance(l0.activated, int) and activated > 0`):

- `l3_unsupported_with_activation`: `l3.status == "unsupported"`.
- `l0_funnel_missing`: `l0.attempted is None or l0.eligible_count is None` AND no legal
  limited reason. Legal limited reasons: `l0.status == "no_log"`, or a non-empty string
  `l0.funnel_limited_reason` / `l0.limited_reason` (documented forward path for the
  observation builder; today's builder emits none, so every activated legacy sample is
  flagged — intended).
- `l2_diverged_zero_instructions`: `commit_diff.verdict == "diverged"` and
  `commit_diff.run_instructions` is 0/None/missing (an empty or unrecorded run trace
  cannot support a divergence verdict).
- `l1_valid_zero_snaps`: `l1.status == "ok"` and not (`micro_diff` is a dict with int
  `snaps_run > 0`). (`l1.status == "truncated"` with snaps_run=0 is the honest crash
  record and stays clean.)
- `first_divergence_from_empty_trace`: a first-divergence record exists
  (`commit_diff.first_divergence` or `l2.first_divergent_commit` is a dict) and
  `commit_diff.run_instructions` is 0/None/missing.

- [x] **Step 1: Update + write the failing tests first**

In `tools/tests/test_ooo_chain_audit.py`:
- `make_obs`: default `l3_status="ok"` (method `"proxy"`, fanout
  `{"upper_bound": 3}`, caveat set); `l0` gets `"attempted": 1` (keep
  `eligible_count: 17`); `l1.micro_diff` (non-inactive) becomes
  `{"snaps_run": 11121, "rat_divergences": 0, "first_divergence_snap": None}`;
  `commit_diff` gains `"run_instructions": 3000071, "aligned_pairs": 3000071`.
  (`chain_complete`/`chain_gaps` logic already keys off `l3s` and stays.)
- Fixture 1 stays the clean case but its gaps/L3 assertions flip to the full-chain
  expectation (`chain_complete is True`, `chain_gaps == []`,
  `res["n_l3_unsupported_gap"] == 0`).
- New fixtures (same file, same style):

```python
def test_fixture9_l3_unsupported_with_activation():
    print("[fixture 9] activated>0 + l3 unsupported -> admission-view violation")
    d = fresh_campaign("f9-l3-gap")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013, l3_status="unsupported")
    install_sample(d, obs)
    res = audit.audit_campaign(d)
    v = res["samples"][0]["violations"]
    check("f9-l3-unsupported-with-activation",
          "l3_unsupported_with_activation" in v, repr(v))
    check("f9-gaps-still-counted", res["gaps_by_level"].get("L3") == 1)
    check("f9-not-honest-only", res["n_l3_unsupported_gap"] == 0)
    # scope: activated==0 must NOT fire the gate
    obs2 = make_obs("e2e_fixture-c0000-r0001", 20261014,
                    classification="Inactive")
    obs2["l3"]["status"] = "unsupported"  # weird but not gate-relevant
    obs2["chain_complete"] = False
    obs2["chain_gaps"] = ["L3"]
    d2 = fresh_campaign("f9-scope")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f9-activated0-not-gated",
          "l3_unsupported_with_activation" not in v2, repr(v2))


def test_fixture10_l0_funnel_missing():
    print("[fixture 10] attempted/eligible null -> l0_funnel_missing")
    d = fresh_campaign("f10-funnel")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    obs["l0"]["attempted"] = None  # eligible_count stays 17
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f10-attempted-null-flagged", "l0_funnel_missing" in v, repr(v))
    # legal limited reason (documented forward path) must NOT fire
    obs2 = make_obs("e2e_fixture-c0000-r0000", 20261013)
    obs2["l0"]["attempted"] = None
    obs2["l0"]["eligible_count"] = None
    obs2["l0"]["funnel_limited_reason"] = (
        "injector has no eligible/attempted counter source (documented)")
    d2 = fresh_campaign("f10-limited")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f10-limited-reason-clean", "l0_funnel_missing" not in v2, repr(v2))


def test_fixture11_fake_divergence():
    print("[fixture 11] diverged + run_instructions=0 -> fake divergence")
    d = fresh_campaign("f11-fake-div")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013,
                   classification="Crash", l2_status="ok",
                   l2_verdict="diverged",
                   l2_primary_class="instruction_flow_change")
    obs["l2"]["commit_diff"]["run_instructions"] = 0
    obs["l2"]["commit_diff"]["aligned_pairs"] = 0
    obs["l2"]["commit_diff"]["first_divergence"] = {
        "seq": 0, "class": "instruction_flow_change", "level": "presence",
        "detail": "seq 0 only in ref (run side missing)",
        "ref_line": "0,0,73535,400d00,nop,0", "run_line": None}
    obs["l2"]["first_divergent_commit"] = \
        obs["l2"]["commit_diff"]["first_divergence"]
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f11-zero-instr-diverged-flagged",
          "l2_diverged_zero_instructions" in v
          and "first_divergence_from_empty_trace" in v, repr(v))
    # control: same shape but a REAL partial trace (run_instructions>0)
    obs2 = make_obs("e2e_fixture-c0000-r0000", 20261013,
                    classification="Crash", l2_status="ok",
                    l2_verdict="diverged",
                    l2_primary_class="instruction_flow_change")
    obs2["l2"]["commit_diff"]["run_instructions"] = 2297
    obs2["l2"]["commit_diff"]["aligned_pairs"] = 2297
    obs2["l2"]["commit_diff"]["first_divergence"] = {
        "seq": 5, "class": "instruction_flow_change", "level": "presence",
        "detail": "real prefix divergence", "ref_line": "x", "run_line": "y"}
    obs2["l2"]["first_divergent_commit"] = \
        obs2["l2"]["commit_diff"]["first_divergence"]
    d2 = fresh_campaign("f11-real-partial")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f11-real-partial-clean",
          "l2_diverged_zero_instructions" not in v2
          and "first_divergence_from_empty_trace" not in v2, repr(v2))


def test_fixture12_l1_zero_snaps():
    print("[fixture 12] l1 ok + snaps_run=0 -> l1_valid_zero_snaps")
    d = fresh_campaign("f12-zero-snaps")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    obs["l1"]["micro_diff"]["snaps_run"] = 0
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f12-ok-zero-snaps-flagged", "l1_valid_zero_snaps" in v, repr(v))
    # honest truncated crash record with zero snaps must stay clean
    obs2 = make_obs("e2e_fixture-c0000-r0000", 20261013,
                    classification="Crash", l2_status="truncated",
                    l2_verdict="truncated_no_divergence_in_prefix")
    obs2["l1"]["status"] = "truncated"
    obs2["l1"]["micro_diff"]["snaps_run"] = 0
    d2 = fresh_campaign("f12-honest-truncated")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f12-truncated-zero-snaps-clean", "l1_valid_zero_snaps" not in v2,
          repr(v2))
```

Also update the module docstring fixture list (1–8 -> 1–12) and the `main()` call list.

- [x] **Step 2: Run tests, verify the new fixtures FAIL** (function not yet implemented)
  Run: `python3 tools/tests/test_ooo_chain_audit.py`
  Expected: f9/f10/f11/f12 checks FAIL (violations missing); fixtures 1/3/7/8 PASS.

- [x] **Step 3: Implement in tools/ooo_chain_audit.py**

```python
SEMANTIC_GATE_VIOLATIONS = ("l3_unsupported_with_activation",
                            "l0_funnel_missing",
                            "l2_diverged_zero_instructions",
                            "l1_valid_zero_snaps",
                            "first_divergence_from_empty_trace")


def semantic_gate_violations(obs):
    """The five admission-view mandatory-FAIL gates (L0-L5 correction,
    2026-10-13). Scoped to samples with l0.activated >= 1: an activated
    sample must carry a complete observation chain — an L3 hole, a
    missing L0 funnel (without a documented limited reason), a
    divergence verdict or first-divergence record sourced from an
    EMPTY run trace, or an L1 recorded ok with zero snaps are all
    semantic violations. Pure observation-shape checks: no file
    hashing, no identity checks (those live in audit_observation).
    Returns a list drawn from SEMANTIC_GATE_VIOLATIONS (may be empty).
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
    return out
```

Hook into `_check_layers` (top of the function, after the layer dicts are
extracted... simplest: at the very start, `violations.extend(semantic_gate_violations(obs))`
— `_check_layers` receives `obs`). Rollup in `audit_campaign`:

```python
    violation_counts = Counter()
    for s in samples:
        for v in s["violations"]:
            violation_counts[v] += 1
```
add `"violation_counts": dict(violation_counts)` to the rollup, and
`"correction_mode": correction_mode` param threaded from the CLI (`audit_campaign(campaign_dir,
frozen_gem5_sha=None, correction_mode=False)` — additive kwarg). `--correction-mode` on the
`audit` subparser sets it; `write_reports` md gains a line
`- correction_mode: true (re-audit of legacy data under current strict rules)` when set; the
summary print in correction mode prefixes `[chain_audit][correction-mode]` and notes the
violations quantify the correction backlog. Rules and exit codes are IDENTICAL in both
modes (the flag changes tone/annotation only). Update the module docstring accordingly.

- [x] **Step 4: Run the full test file — ALL PASS**
  Run: `python3 tools/tests/test_ooo_chain_audit.py`
  Expected: `ALL PASS` (all fixtures incl. 1–12 and CLI edges).

- [x] **Step 5: Commit**
```bash
git add tools/ooo_chain_audit.py tools/tests/test_ooo_chain_audit.py \
        docs/superpowers/plans/2026-10-13-ooo-l0l5-fixC-admission-audit-gates.md
git commit -m "[OOO][FIX-C] chain-audit: five semantic-gate mandatory-FAIL rules + --correction-mode + violation_counts rollup"
```

---

### Task 2: Handoff execution/chain status field split (ooo_handoff.py)

**Files:**
- Modify: `tools/ooo_handoff.py` (`build_campaign_handoff`, `write_campaign_handoff`,
  `build_master_handoff`)
- Test: `tools/tests/test_ooo_handoff.py`

**Interfaces:**
- Consumes: `ooo_chain_audit.semantic_gate_violations(obs)` (Task 1).
- Produces (handoff.json top level, additive; legacy `status` + `chain` block kept):
  `execution_status` ("COMPLETE"|"PARTIAL", same rule as legacy status),
  `execution_complete_count` (int; parsed results.jsonl rows with a run_id),
  `evidence_readable_count` (int; observation parses AND every `files` manifest entry
  exists on disk — existence check, sha verification stays the audit's job),
  `chain_complete_count`, `chain_incomplete_count`, `chain_gap_histogram` (alias of
  legacy `chain.gap_histogram`), `chain_backfill_required` (bool:
  `chain_complete_count < execution_complete_count`), `semantic_invalid_count` (int;
  observations with non-empty `semantic_gate_violations`).
- Master handoff `totals` gains the sum of each new count.

- [x] **Step 1: Extend the test first** — in `tools/tests/test_ooo_handoff.py` after the
  existing `check("status-complete", ...)`:

```python
        check("split-execution-status",
              h["execution_status"] == "COMPLETE"
              and h["execution_complete_count"] == 3
              and h["evidence_readable_count"] == 3)
        check("split-chain-backfill",
              h["chain_complete_count"] == 1
              and h["chain_incomplete_count"] == 2
              and h["chain_gap_histogram"] == {"L3": 2}
              and h["chain_backfill_required"] is True)
        check("split-semantic-invalid",
              h["semantic_invalid_count"] == 2,
              str(h["semantic_invalid_count"]))  # Masked+Crash (l3
        # unsupported + funnel null); Inactive is gated off (activated=0)
        check("split-md-discloses-backfill",
              "chain_backfill_required: True" in open(mp).read()
              if os.path.exists(mp) else False)
```
(note: the md check must run after `write_campaign_handoff` further down — place the
`split-md-discloses-backfill` check after the `files-written` check; `mp` is bound there.)

- [x] **Step 2: Run — verify FAIL** (`python3 tools/tests/test_ooo_handoff.py`; new checks
  FAIL with KeyError `execution_status`).

- [x] **Step 3: Implement in ooo_handoff.py**

In `build_campaign_handoff`:
```python
    import ooo_chain_audit  # at module top with the other imports
```
After the observation loop (which already computes `chain_complete_n`, `gap_hist`):
```python
    # --- execution/chain split (L0-L5 correction 2026-10-13) -----------
    execution_complete_count = sum(
        1 for r in rows if isinstance(r, dict) and r.get("run_id"))
    evidence_readable_count = 0
    semantic_invalid_count = 0
    for name in sorted(obs):
        o = obs[name]
        if not isinstance(o, dict):
            continue
        readable = True
        for rel in (o.get("files") or {}):
            if not os.path.isfile(os.path.join(campaign_dir, "samples",
                                               name, rel)):
                readable = False
                break
        if readable:
            evidence_readable_count += 1
        if ooo_chain_audit.semantic_gate_violations(o):
            semantic_invalid_count += 1
    chain_complete_count = chain_complete_n
    chain_incomplete_count = n_obs_ok - chain_complete_n  # unreadable == incomplete
    execution_status = ("COMPLETE" if n_valid >= cy.get("n_per_cell", 10**9)
                        else "PARTIAL")
```
Then in the dict `h`: keep `"status": execution_status` (legacy alias) and add the eight
new top-level keys (values above; `chain_backfill_required` is
`chain_complete_count < execution_complete_count`). In `write_campaign_handoff`'s md,
after the status line add:
```python
        f.write(f"- execution_status: **{h['execution_status']}**  "
                f"executed: {h['execution_complete_count']}  "
                f"evidence_readable: {h['evidence_readable_count']}  "
                f"semantic_invalid: {h['semantic_invalid_count']}\n")
        f.write(f"- chain_backfill_required: "
                f"**{h['chain_backfill_required']}** "
                f"(complete {h['chain_complete_count']} < executed "
                f"{h['execution_complete_count']}; gap histogram "
                f"{h['chain_gap_histogram']}) — execution COMPLETE is NOT "
                f"a complete observation chain\n")
```
In `build_master_handoff` `totals` add:
```python
            "execution_complete_count": sum(p["execution_complete_count"]
                                            for p in per),
            "evidence_readable_count": sum(p["evidence_readable_count"]
                                           for p in per),
            "chain_backfill_required": any(p["chain_backfill_required"]
                                           for p in per),
            "semantic_invalid_count": sum(p["semantic_invalid_count"]
                                          for p in per),
```

- [x] **Step 4: Run — ALL PASS** (`python3 tools/tests/test_ooo_handoff.py`).

- [x] **Step 5: Commit**
```bash
git add tools/ooo_handoff.py tools/tests/test_ooo_handoff.py
git commit -m "[OOO][FIX-C] handoff: split execution vs chain status (execution_status/evidence_readable/chain_backfill_required/semantic_invalid)"
```

---

### Task 3: Offline `correction-audit` subcommand (ooo_chain_audit.py)

**Files:**
- Modify: `tools/ooo_chain_audit.py` (new `correction_audit()` + CLI subcommand)
- Test: `tools/tests/test_ooo_chain_audit.py` (new `test_correction_audit()` fixture)

**Interfaces:**
- Produces: CLI `python3 tools/ooo_chain_audit.py correction-audit --campaign-dir <d>
  [--frozen-gem5-sha S]` and function `correction_audit(campaign_dir,
  frozen_gem5_sha=None) -> dict`. Writes ONLY `<campaign_dir>/correction_audit.json`:
```json
{"tool": "ooo_chain_audit.correction-audit", "schema_version": "ooo-correction-audit/v1",
 "campaign_dir": "...", "frozen_gem5_sha": "...", "generated_at": "...",
 "per_sample": [{"run_id": "...", "classification": "...", "violations": [...],
                 "l2_zero_trace_fake_divergence": false}],
 "summary": {"n": 385, "semantic_invalid": 385, "fake_divergence_count": 99,
             "l3_unsupported": 385, "l0_funnel_missing": 385,
             "chain_backfill_required": true,
             "l1_valid_zero_snaps": 0, "first_divergence_from_empty_trace": 99,
             "chain_complete_count": 0, "execution_complete_count": 385,
             "evidence_readable_count": 385, "observations_unparseable": 0,
             "note": "offline re-audit under current strict rules; original evidence untouched"}}
```
  `l2_zero_trace_fake_divergence` = has `l2_diverged_zero_instructions` OR
  `first_divergence_from_empty_trace`. `semantic_invalid` = samples with any violations.
  `execution_complete_count` = parsed results.jsonl rows with a run_id (same definition as
  Task 2). Exit 0 when the report is written; 1 on AuditError (missing dir / no samples).

- [x] **Step 1: Write the failing test** — in `tools/tests/test_ooo_chain_audit.py`:

```python
def test_correction_audit():
    print("[correction-audit] legacy-shaped campaign -> quantified correction")
    d = fresh_campaign("corr-audit")
    # one legacy Masked sample (l3 unsupported, funnel null) + one fake-div Crash
    obs1 = make_obs("e2e_fixture-c0000-r0000", 20261013,
                    l3_status="unsupported")
    obs1["l0"]["attempted"] = None
    install_sample(d, obs1)
    obs2 = make_obs("e2e_fixture-c0000-r0001", 20261014,
                    classification="Crash", l2_status="ok",
                    l2_verdict="diverged",
                    l2_primary_class="instruction_flow_change")
    obs2["l2"]["commit_diff"]["run_instructions"] = 0
    obs2["l2"]["commit_diff"]["first_divergence"] = {
        "seq": 0, "class": "instruction_flow_change", "level": "presence",
        "ref_line": "0,0,7,4,nop,0", "run_line": None}
    obs2["l2"]["first_divergent_commit"] = \
        obs2["l2"]["commit_diff"]["first_divergence"]
    install_sample(d, obs2)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "e2e_fixture-c0000-r0000"}) + "\n")
        f.write(json.dumps({"run_id": "e2e_fixture-c0000-r0001"}) + "\n")
    out = os.path.join(d, "correction_audit.json")
    r = subprocess.run([sys.executable, TOOL, "correction-audit",
                        "--campaign-dir", d], capture_output=True, text=True,
                       errors="replace", timeout=120)
    check("corr-cli-exit0", r.returncode == 0,
          f"rc={r.returncode} {r.stdout[-200:]}{r.stderr[-200:]}")
    with open(out) as f:
        rep = json.load(f)
    s = rep["summary"]
    check("corr-summary-counts",
          s["n"] == 2 and s["semantic_invalid"] == 2
          and s["l3_unsupported"] == 2 and s["l0_funnel_missing"] == 2
          and s["fake_divergence_count"] == 1
          and s["first_divergence_from_empty_trace"] == 1,
          json.dumps(s))
    check("corr-backfill-required",
          s["chain_backfill_required"] is True
          and s["chain_complete_count"] == 0
          and s["execution_complete_count"] == 2, json.dumps(s))
    ps = {p["run_id"]: p for p in rep["per_sample"]}
    check("corr-per-sample-flag",
          ps["e2e_fixture-c0000-r0001"]["l2_zero_trace_fake_divergence"]
          is True
          and ps["e2e_fixture-c0000-r0000"]
          ["l2_zero_trace_fake_divergence"] is False)
    check("corr-originals-untouched",
          os.path.exists(os.path.join(d, "samples", "e2e_fixture-c0000-r0000",
                                      "observation.json")))
```
Add `test_correction_audit()` to `main()`.

- [x] **Step 2: Run — verify FAIL** (subcommand unknown → argparse error rc=2).

- [x] **Step 3: Implement** `correction_audit()` + CLI in `tools/ooo_chain_audit.py`
  (reuses `discover_samples`, `audit_observation`; reads results.jsonl rows for
  `execution_complete_count`; writes correction_audit.json; prints a one-line summary
  `"[correction-audit] campaign=%s n=%d semantic_invalid=%d fake_divergence=%d
  l3_unsupported=%d l0_funnel_missing=%d chain_backfill_required=%s -> %s"`).

- [x] **Step 4: Run — ALL PASS** (`python3 tools/tests/test_ooo_chain_audit.py`).

- [x] **Step 5: Commit**
```bash
git add tools/ooo_chain_audit.py tools/tests/test_ooo_chain_audit.py
git commit -m "[OOO][FIX-C] chain-audit: offline correction-audit subcommand (per-sample re-audit, correction_audit.json, originals untouched)"
```

---

### Task 4: Admission gate hardening (e2e/ooo_l0l5_admission.py)

**Files:**
- Modify: `tools/tests/e2e/ooo_l0l5_admission.py` (`run_admission` new "chain" item +
  chain summary; self-test happy fixtures lifted to the strict contract; 4 new negatives)
- `tools/tests/e2e/ooo_l0l5_e2e.py`: NO change expected (its self-test does not call
  `audit_observation`; only `run_class`/real e2e does, which is out of scope here).

**Interfaces:**
- Consumes: `ooo_chain_audit.semantic_gate_violations(obs)` (Task 1).
- Produces: admission report item `"chain"` (per-sample semantic-gate failures +
  campaign-level `chain_complete_false_ratio_100pct` failure) and
  `report["chain_summary"] = {"n_samples", "n_chain_complete", "n_chain_incomplete",
  "all_chain_incomplete"}`. `overall` FAILs when any item fails (existing formula covers
  it once "chain" joins `item_fails`).

Rules (per central brief):
- any eng sample activated>0 with L3 status != "ok" → FAIL;
- attempted/eligible empty → FAIL (via `l0_funnel_missing`);
- zero-instruction fake divergence → FAIL (via `l2_diverged_zero_instructions` /
  `first_divergence_from_empty_trace`);
- chain_complete=false on 100% of samples → verdict must FAIL.

- [x] **Step 1: Update the self-test fixtures + add negatives (test first)**

`_mk_eng2_obs` lifted to the strict contract: `l3` default
`{"status": "ok", "method": "proxy", "fanout": {"upper_bound": 3}, "caveat":
"PRF liveness proxy", "reason": None}`; `l0` `"attempted": 5` (eligible_count stays 5);
`l1.micro_diff` → `{"snaps_run": 10}`; `l2.commit_diff` gains
`"run_instructions": 11121`; `chain_complete` True / `chain_gaps` [] for non-inactive
(Inactive unchanged). Docstring note: under the strict gates only L3-ok chains pass
admission (physreg-style proxy fanout); decode/rat L3-unsupported samples FAIL by design.

New negatives after the existing ones in `_self_test_body`:

```python
    # (a) activated>0 + L3 unsupported -> chain item FAIL (the old gate PASSED this)
    d, obs = fresh_negative("eng2_neg_l3gap")
    obs["l3"] = {"status": "unsupported", "method": None, "fanout": None,
                 "caveat": None, "reason": "no source-read association"}
    obs["chain_complete"] = False
    obs["chain_gaps"] = ["L3"]
    _install_eng2_sample(d, obs, cfg_sha, wl_sha)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_l3gap-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_l3gap.json")
    r = _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-l3gap-chain-fails",
          rep["items"]["chain"]["status"] == "FAIL"
          and any("l3_unsupported_with_activation" in x for x in
                  rep["items"]["chain"]["failures"]),
          json.dumps(rep["items"]["chain"]))
    check("neg-l3gap-overall-fails", rep["overall"] == "FAIL"
          and r.returncode == 1)

    # (b) attempted/eligible empty -> FAIL
    d, obs = fresh_negative("eng2_neg_funnel")
    obs["l0"]["attempted"] = None
    obs["l0"]["eligible_count"] = None
    _install_eng2_sample(d, obs, cfg_sha, wl_sha)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_funnel-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_funnel.json")
    _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-funnel-chain-fails",
          any("l0_funnel_missing" in x for x in
              rep["items"]["chain"]["failures"]))

    # (c) zero-instruction fake divergence -> FAIL
    d, obs = fresh_negative("eng2_neg_fakediv")
    obs["l5"].update({"classification": "Crash", "exit": -6,
                      "checksum_observed": None, "faults_injected": 1})
    obs["l2"]["commit_diff"] = {
        "verdict": "diverged", "primary_class": "instruction_flow_change",
        "run_instructions": 0, "aligned_pairs": 0,
        "first_divergence": {"seq": 0,
                             "class": "instruction_flow_change",
                             "level": "presence", "ref_line": "0,0,7,4,n,0",
                             "run_line": None}}
    obs["l2"]["first_divergent_commit"] = \
        obs["l2"]["commit_diff"]["first_divergence"]
    _install_eng2_sample(d, obs, cfg_sha, wl_sha)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_fakediv-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_fakediv.json")
    _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-fakediv-chain-fails",
          any("l2_diverged_zero_instructions" in x for x in
              rep["items"]["chain"]["failures"])
          and any("first_divergence_from_empty_trace" in x for x in
                  rep["items"]["chain"]["failures"]))

    # (d) 100% chain_complete=false -> verdict must FAIL (no all-false PASS)
    d, obs = fresh_negative("eng2_neg_allfalse")
    obs["chain_complete"] = False
    obs["chain_gaps"] = ["L3"]
    obs["l3"] = {"status": "unsupported", "method": None, "fanout": None,
                 "caveat": None, "reason": "no source-read association"}
    _install_eng2_sample(d, obs, cfg_sha, wl_sha)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_allfalse-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_allfalse.json")
    _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-allfalse-ratio-rule",
          any("chain_complete_false_ratio_100pct" in x for x in
              rep["items"]["chain"]["failures"])
          and rep["overall"] == "FAIL", json.dumps(rep["items"]["chain"]))
```

- [x] **Step 2: Run — verify FAIL** (`python3 tools/tests/e2e/ooo_l0l5_admission.py
  --self-test`; happy path FAILs on the new "chain" item / unknown key, negatives FAIL).

- [x] **Step 3: Implement in run_admission** — add `"chain"` to the `item_fails` dict;
  after loading each sample's `obs`:

```python
            for v in ooo_chain_audit.semantic_gate_violations(obs):
                item_fails["chain"].append("%s:%s" % (run_id, v))
```
plus chain-flag accounting (`cc = obs.get("chain_complete")`;
`n_chain_complete/n_chain_incomplete` counters, skipping unloadable observations — they
already fail "observation"), and after the loop:

```python
    if n_chain_total > 0 and n_chain_incomplete == n_chain_total:
        item_fails["chain"].append(
            "chain_complete_false_ratio_100pct: %d/%d samples incomplete — "
            "an all-false chain can never PASS admission" %
            (n_chain_incomplete, n_chain_total))
    report["chain_summary"] = {
        "n_samples": n_chain_total, "n_chain_complete": n_chain_complete,
        "n_chain_incomplete": n_chain_incomplete,
        "all_chain_incomplete": (n_chain_total > 0
                                 and n_chain_incomplete == n_chain_total)}
```
Update the module docstring (per-sample item 7 "chain — semantic gates + all-false rule").

- [x] **Step 4: Run — ALL PASS** (`python3 tools/tests/e2e/ooo_l0l5_admission.py
  --self-test` → `ALL PASS`), and regression: `python3 tools/tests/e2e/ooo_l0l5_e2e.py
  --self-test` → `ALL PASS` (unaffected test, must stay green), plus re-run
  `python3 tools/tests/test_ooo_chain_audit.py` and `python3 tools/tests/test_ooo_handoff.py`.

- [x] **Step 5: Commit**
```bash
git add tools/tests/e2e/ooo_l0l5_admission.py
git commit -m "[OOO][FIX-C] admission: chain item — semantic-gate + all-false-chain mandatory FAIL rules; happy fixtures lifted to strict contract"
```

---

### Task 5 (verification, no code commit): Real correction audits of the four formal campaigns

- [x] **Step 1:** Confirm `formal_D01-F0-W6-c` finished (results.jsonl == 385 rows and no
  `ooo_sample_runner`/`ooo_scheduler` processes for it); if still running, wait and
  re-check (it progresses ~1 sample/2-4 min with 2 slots).
- [x] **Step 2:** Run for each of the four campaign dirs (from the worktree, against the
  main-repo runs/ paths, frozen sha 1a618953...):
```bash
python3 tools/ooo_chain_audit.py correction-audit --campaign-dir \
  /home/sdc/gem5-fi-ding/runs/formal_D01-F0-W6-c --frozen-gem5-sha 1a618953b014514713c0ad98c7f3d69a48171d81f0463d934bccdfcfc0070bf3
```
  Expected (from the frozen-facts survey): semantic_invalid == n (all samples carry
  l3_unsupported_with_activation + l0_funnel_missing); fake_divergence_count == 38/99/147/96
  (D01-c count to be re-measured at completion); chain_backfill_required == true everywhere.
- [x] **Step 3:** Cross-check each generated `correction_audit.json` against the survey
  numbers (spot-check 3 per_sample entries incl. one fake-divergence Crash and one
  non-zero-trace Crash); record the four summaries verbatim in the final report.
- [x] **Step 4 (optional if repo policy requires):** no commit — correction_audit.json
  files live in untracked runs/ dirs; the numbers go into the subagent report. If the
  lead wants them in-repo, that is the lead's call (artifacts/ dirs exist for this).

---

## Execution record (2026-10-13, Subagent-C)

All 24 steps complete; 4 task commits on `ooo/l0l5-fixC` (base 2a25073), not pushed:

- Task 1 `1e6a87a` — five semantic-gate rules + `--correction-mode` + `violation_counts`
- Task 2 `83cc75a` — handoff execution/chain status split
- Task 3 `4c5840e` — offline `correction-audit` subcommand
- Task 4 `d5c4c4d` — admission gate chain item + all-false rule

Verification (all real runs): `test_ooo_chain_audit.py` ALL PASS (67 checks),
`test_ooo_handoff.py` ALL PASS, `ooo_l0l5_admission.py --self-test` ALL PASS
(16 checks incl. 4 new chain negatives), `ooo_l0l5_e2e.py --self-test` ALL PASS
(unaffected regression).

Task 5 real correction audits (frozen gem5 sha `1a618953...`, originals untouched,
each `correction_audit.json` written into the campaign dir; full evidence re-hash —
`evidence_readable_count=385` in all four, no file-integrity violations, the defects
are purely semantic):

| campaign | n | semantic_invalid | fake_divergence | l3_unsupported | l0_funnel_missing | l1_zero_snaps | backfill |
|---|---|---|---|---|---|---|---|
| formal_D01-F0-W6-c | 385 | 385 | 38 | 385 | 385 | 0 | true |
| formal_D02-F0-W6-b | 385 | 385 | 99 | 385 | 385 | 0 | true |
| formal_D02-F0-W6-c | 385 | 385 | 147 | 385 | 385 | 0 | true |
| formal_D04-F0-W4-d | 385 | 385 | 96 | 385 | 385 | 0 | true |

Deltas vs plan (all minor, no scope change):
- D01-c was still running at plan time (377 rows, 09:50); it reached 385/385 on its
  own by 10:30 (scheduler exited) and was audited at completion — matches the
  brief's frozen "385/385".
- test-fixture polish during TDD: fixture-1 assertions flipped to the full-chain
  contract; the handoff flip-test also fixes l2/l3/l1 for the flipped samples
  (the Crash fixture's commit_diff gained `run_instructions` — without it the
  strict `first_divergence_from_empty_trace` rule correctly kept flagging it);
  the correction-audit fixture's Crash carries the full legacy shape (l3
  unsupported + funnel null + empty trace) like the real campaigns.
- D04-d has 9 honest real-partial Crash samples (run_instructions>0): correctly
  NOT flagged as fake divergences; its fake-div 96 includes the campaign's one
  Hang (empty trace), consistent with 104 Crash = 95 fake + 9 real.
