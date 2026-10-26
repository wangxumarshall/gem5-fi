# R6 Frequency Policy Overlay + F6 De-Duplication + fi-ding 收口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a single machine-readable frequency/statistics policy overlay that turns F6 into a stress-only, de-duplicated representative set, wire it into every scheduling/status entry point so F6 seed>1 can never launch, and then close the `lsu-mdspec-20261019` branch into `origin/fi-ding` via a clean merge worktree + rebuild.

**Architecture:** One generator tool (`tools/lsu_freq_policy.py`) owns the authoritative rule and emits both `R6-FREQUENCY-POLICY.json` (machine source) and `R6-FREQUENCY-POLICY.md` (audit report) from the same in-memory dict — no hand-maintained duplicate. Every consumer (wrapper, campaign, scheduler, contract, status table, runner) reads the JSON, never re-derives the rule. Policy is an **overlay**: the 325 ITEM checklist, the XLSX, the 5 generated Markdowns, the CSV and `runid_map.json` are never edited.

**Tech Stack:** Python 3 (stdlib only: `json`, `csv`, `hashlib`, `argparse`, `pathlib`), bash wrapper, repo-local test protocol (`ALL PASS` / `FAILURES: [...]` last line), `tools/lsu_test_runner.py` as the suite driver.

**Spec:** This plan implements the user's 2026-10-25 R6 ruling (frequency policy overlay §一–§十一) plus the follow-up amendment (branch close-out into `fi-ding`). Both are reproduced as constraints below because there is no separate spec file.

---

## Global Constraints

- **Do NOT rebuild gem5.** This round touches only Python/shell/docs/policy. `binary_source_head` = `12d05e8ca38e67b2ee1007bb7cbaab7351ea00df`; `binary_sha256` = `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`. Never claim the existing binary was built from a newer policy/tool commit.
- **Never `git add -A`.** Stage explicit paths only. `runs/`, `m5out/`, scratch dirs churn constantly.
- **Commit message must NOT end with `Co-Authored-By: Claude …`.**
- **One patch per unit.** Each task = one commit. Push after each commit to the feature branch `lsu-mdspec-20261019` (never `main`, never `fi-ding` until Task 14).
- **Immutable inputs — must be byte-identical before and after this whole plan:**
  - `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx` → `389546f0f8f3d0c6ece2ed33d3a8cfd1426faa9bbc101f7ad7d9612159e273e0`
  - `…方案.md` → `1c1cefae05bafb86966e0dfc8477c4866480bac93ce785b8a1c5710476ee0f28`
  - `…-03-位置x模型矩阵.md` → `33b3a0576ad9150238d04bc2382930d8e9572934536bb1f9c55507e28ec15c37`
  - `…-07-展开执行矩阵.md` → `a5859486fef054344dad6d594594f28b489de8f5a088519b4687dd8904b4ff75`
  - `…-09-逐RunID传播监控.md` → `2e71b37fe5a3d8cde7a2f93221500fdaa68a5ae185d40ef16c12c66e81025125`
  - `…-10-源码监控映射.md` → `d1b92b03502cf68bc5241fc5051485cb61ffadfc7deec3d32cccd1a57919b63f`
  - `artifacts/lsu-trial/07-expanded-matrix-backfilled.csv` → `4eb13ba483d3b8a67f017c154e955efaed24f87b358e3729ae6b9d5333e26ffc`
  - `docs/gem5-fi/lsu/mdspec/runid_map.json` → `7ae61acceb0dab04de90f189cc56cb17ec30db9179ea444dd5579bd88a108ff5`
- **Never delete or overwrite:** any F6 row in any surface; the completed `T04-F6-W4` seed1 evidence; the running normal seed2/3; the 3 pre-existing uncommitted/untracked docs outside this plan's explicit file list.
- **Counts (measured, authoritative):** checklist ITEMs = **325** (F6 ITEMs = **64**); `runid_map.json` entries = **325** (F6 = **64**); CSV data rows = **337** (F6 = **68**; the 4 legacy F6 rows are V2.0-deleted models `T09-F6-W4`, `S12-F6-W5`, `C13-F6-W6`, `O08-F6-W7`). Any test asserting "64 F6" must assert it on the **checklist and runid_map** surfaces; on the CSV assert **68** and document the delta.
- **Max 2 concurrent gem5.** Never kill the running `r6c9-s2` / `r6c9-s3` tmux sessions or their gem5 children.
- **Completion standard this phase:** 5 NORMAL RunIDs × 3 seeds = **15/15**, plus representative `T04-F6-W4` = **1/1** → **16/16** (not 18/18).

**Policy definitions (verbatim from the ruling):**
- **A. F0–F5:** `run_policy=NORMAL`, `required_seeds=3`, `schedule_enabled=true`, `include_in_statistics=true`.
- **B. Selected representative F6:** `run_policy=STRESS_ONLY`, `required_seeds=1`, `schedule_enabled=true`, `include_in_statistics=false`.
- **C. Other duplicate F6:** `run_policy=STRESS_REDUNDANT`, `required_seeds=0`, `schedule_enabled=false`, `include_in_statistics=false`, `exclusion_reason=covered_by_representative_F6`.
- A not-required F6 seed2/seed3 is **`POLICY_NOT_REQUIRED`** — never FAIL/BLOCKED/SKIP/NOT_RUN/EVIDENCE_MISSING/TRUNCATED.

**Representative rule:** group the 64 F6 RunIDs by `model_id` (injector identity is per-model: `MODEL_FLAGS[model][0]` gives the family/class; `runid_map.json` `impl_status`/`spec_landed` names the hook). One representative per distinct model group; the rest are `STRESS_REDUNDANT`. `T04-F6-W4` is pinned as its group's representative (ARM TLB lookup / `pfn_to_mapped_page`). Deterministic tie-break: prefer a RunID with certified existing evidence, else the lexicographically smallest RunID. Measured result: **39 groups → 39 representatives, 25 redundant.**

## Review Focus

The failure modes this plan's tests must pin (most likely first):
1. **Policy silently defeating the audit identity** — a consumer that re-derives the rule instead of reading the JSON, so the 325-ITEM / 64-F6 count drifts. Each consumer task asserts it reads the shared overlay.
2. **A gated F6 seed still consuming a slot** — the wrapper exits *after* taking the lock or creating the outdir. Asserted by "gem5 count unchanged + no outdir + no `.done`".
3. **`POLICY_NOT_REQUIRED` leaking into a failure bucket** — the status table counting a not-required seed as `BLOCKED`/`EVIDENCE_MISSING`/FAIL. Asserted by an explicit not-in-set check.
4. **Bypass via direct campaign invocation** — calling `lsu_campaign.py` on F6 seed 2 succeeding anyway. Asserted by invoking the campaign path with the policy check and requiring refusal.
5. **`--cells all` scheduling a `schedule_enabled=false` cell** — asserted by parsing the scheduler's selection.
6. **A regenerated CSV/runid_map dropping RunIDs** — asserted by SHA + count equality on the immutable inputs.

---

## File Structure

**Create:**
- `tools/lsu_freq_policy.py` — the single generator + query API + `--check` drift verifier.
- `docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json` — generated machine source.
- `docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.md` — generated audit report.
- `tests/test_lsu_freq_policy.py` — the 16-assertion regression suite.
- `docs/superpowers/plans/2026-10-25-lsu-r6-frequency-policy.md` — this file.

**Modify (execution chain):**
- `runs/lsu/r6_c9_run.sh` — rewire the existing hardcoded gate to consult the policy tool (fallback logic kept).
- `tools/lsu_campaign.py` — add `--allow-stress-only`; refuse `STRESS_REDUNDANT`; refuse `STRESS_ONLY` seed>1; add `policy_decision` to `cell_results.json`.
- `tools/lsu_r6_schedule.sh` — `--cells all` filters `schedule_enabled=false`; never auto-resume absent F6 seeds.
- `tools/lsu_runner.py` — overlay `run_policy`/`required_seeds` onto each parsed manifest.
- `tools/lsu_ready_contract.py` — emit `policy_state` per entry; never map policy exclusion to `BLOCKED`.
- `tools/lsu_r6_status_table.py` — add orthogonal `policy_state` axis; keep `evidence_state` × `eligibility`.

**Modify (authoritative docs):**
- `docs/gem5-fi/lsu/完整任务执行清单.md`, `总方针.md`, `task_plan.md`, `progress.md`, `findings.md`.

---

### Task 0: Emergency F6 seed>1 gate in the running wrapper — **DONE (hotfix)**

Pre-empted the user's first priority before planning, because the running chains
(`r6c9-s2`, `r6c9-s3`) end with an unconditional `./runs/lsu/r6_c9_run.sh f6 <seed>`.

**Files:**
- Modify: `runs/lsu/r6_c9_run.sh` (untracked scratch wrapper; also referenced in Task 4)

- [x] **Step 1: Insert the guard** after `LOG=…` — rejects `batch=f6 && seed>1` with `POLICY_NOT_REQUIRED`, writes `runs/lsu/r6_c9_policy_decisions.jsonl`, `exit 0` (so the `&&` chain still reaches its own `tmux kill-session` cleanup).
- [x] **Step 2: Verify (real commands).**
  ```
  bash -n runs/lsu/r6_c9_run.sh && echo SYNTAX_OK
  pgrep -cf 'gem5\.opt --outdir'        # before: 2
  ./runs/lsu/r6_c9_run.sh f6 2 ; echo rc=$?   # POLICY_NOT_REQUIRED …, rc=0
  ./runs/lsu/r6_c9_run.sh f6 3 ; echo rc=$?   # POLICY_NOT_REQUIRED …, rc=0
  pgrep -cf 'gem5\.opt --outdir'        # after: 2 (unchanged — no slot consumed)
  ls -d runs/lsu/r6_c9_T04-F6-W4_s2 runs/lsu/r6_c9_T04-F6-W4_s3   # both: No such file
  ```
  Observed: gem5 count 2→2; both outdirs absent; two records appended to `r6_c9_policy_decisions.jsonl`.
- [ ] **Step 3: (no commit)** — this file is untracked scratch; Task 4 re-implements the same rule through the tracked tool.

---

### Task 1: Policy generator — rule + JSON + MD

**Files:**
- Create: `tools/lsu_freq_policy.py`
- Create (generated): `docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json`, `docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.md`
- Test: `tests/test_lsu_freq_policy.py` (created in Task 10; this task only needs the generator to run)

**Interfaces:**
- Produces:
  - `build_policy(runid_map_path: Path, matrix_path: Path) -> dict`
  - `POLICY_JSON = REPO/"docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json"`
  - `POLICY_MD = REPO/"docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.md"`
  - `load_policy(path=POLICY_JSON) -> dict`
  - `query(policy: dict, run_id: str, seed: int) -> dict` with keys `run_id, seed, run_policy, required_seeds, schedule_enabled, include_in_statistics, representative_for, exclusion_reason, existing_evidence, decision` where `decision ∈ {"ALLOW","ALLOW_STRESS_ONLY","POLICY_NOT_REQUIRED","REFUSE_STRESS_REDUNDANT"}`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_lsu_freq_policy.py` with just the first checks (the full suite is extended in Task 10):

```python
#!/usr/bin/env python3
"""Frequency-policy overlay contract test."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import lsu_freq_policy as P

fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond: fails.append(name)

def test_policy_covers_all_runids():
    pol = P.load_policy()
    ids = {e["run_id"] for e in pol["entries"]}
    rm = json.loads((REPO/"docs/gem5-fi/lsu/mdspec/runid_map.json").read_text("utf-8"))
    check("policy_covers_325", len(rm["entries"]) == 325 and all(e["run_id"] in ids for e in rm["entries"]))
    check("f6_is_64", sum(1 for e in pol["entries"] if e["frequency"]=="F6" and not e.get("legacy")) == 64)

def main():
    test_policy_covers_all_runids()
    print(f"\n{'ALL PASS' if not fails else 'FAILED (%d): %s' % (len(fails), fails)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 tests/test_lsu_freq_policy.py`
Expected: `ModuleNotFoundError: No module named 'lsu_freq_policy'`.

- [ ] **Step 3: Implement the generator**

Create `tools/lsu_freq_policy.py`. Core content:

```python
#!/usr/bin/env python3
"""lsu_freq_policy.py — R6 frequency/statistics policy overlay (single source of truth).

Rule (2026-10-25 ruling):
  F0-F5          -> NORMAL,           required_seeds=3, schedule_enabled=True,  in_stats=True
  representative F6 -> STRESS_ONLY,   required_seeds=1, schedule_enabled=True,  in_stats=False
  other F6       -> STRESS_REDUNDANT, required_seeds=0, schedule_enabled=False, in_stats=False
Representatives: one per distinct F6 model_id (injector/hook identity is per-model);
T04-F6-W4 pinned; tie-break prefers certified existing evidence, else lexicographically smallest.

Emits R6-FREQUENCY-POLICY.json (machine) and R6-FREQUENCY-POLICY.md (audit) from the SAME dict.
`--check` re-emits in memory and byte-compares against disk (drift = failure).
"""
import argparse, csv, hashlib, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MDS = REPO / "docs/gem5-fi/lsu/mdspec"
POLICY_JSON = MDS / "R6-FREQUENCY-POLICY.json"
POLICY_MD = MDS / "R6-FREQUENCY-POLICY.md"
RUNID_MAP = MDS / "runid_map.json"
MATRIX = REPO / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv"

SCHEMA_VERSION = "r6-frequency-policy/1"
DECISION_DATE = "2026-10-25"
DECISION_SOURCE = "user-ruling-2026-10-25:R6-frequency-policy-overlay"

REPRESENTATIVE_PIN = {"T04": "T04-F6-W4"}          # mandatory ARM TLB representative
EXISTING_EVIDENCE = {                              # runid -> certified evidence locator
    "T04-F6-W4": "runs/lsu/r6_c9_T04-F6-W4_s1 (seed1: eligible=1 injected=1 certified=true graceful=true terminal=full provable_to=L5)",
}

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _f6_rows_from_matrix():
    rows = list(csv.reader(open(MATRIX, encoding="utf-8")))
    return [r[1] for r in rows[1:] if len(r) > 1 and r[1].strip().split("-")[1:2] == ["F6"]]

def build_policy(runid_map_path=RUNID_MAP, matrix_path=MATRIX):
    rm = json.loads(Path(runid_map_path).read_text("utf-8"))
    entries = []
    f6 = [e for e in rm["entries"] if e["freq"] == "F6"]
    groups = {}
    for e in f6:
        groups.setdefault(e["model_id"], []).append(e["run_id"])

    def pick_rep(model, runids):
        if model in REPRESENTATIVE_PIN:
            return REPRESENTATIVE_PIN[model]
        with_ev = [r for r in runids if r in EXISTING_EVIDENCE]
        return (sorted(with_ev) or sorted(runids))[0]

    reps = {pick_rep(m, rs) for m, rs in groups.items()}
    rep_of = {r: pick_rep(m, rs) for m, rs in groups.items() for r in rs}

    for e in rm["entries"]:                       # authoritative 325
        rid, f = e["run_id"], e["freq"]
        if f == "F6":
            if rid in reps:
                entries.append(dict(run_id=rid, frequency=f, run_policy="STRESS_ONLY",
                    required_seeds=1, schedule_enabled=True, include_in_statistics=False,
                    representative_for=rid, exclusion_reason=None,
                    existing_evidence=EXISTING_EVIDENCE.get(rid), legacy=False))
            else:
                entries.append(dict(run_id=rid, frequency=f, run_policy="STRESS_REDUNDANT",
                    required_seeds=0, schedule_enabled=False, include_in_statistics=False,
                    representative_for=rep_of[rid], exclusion_reason="covered_by_representative_F6",
                    existing_evidence=None, legacy=False))
        else:
            entries.append(dict(run_id=rid, frequency=f, run_policy="NORMAL",
                required_seeds=3, schedule_enabled=True, include_in_statistics=True,
                representative_for=None, exclusion_reason=None, existing_evidence=None, legacy=False))

    known = {e["run_id"] for e in entries}
    for rid in sorted(set(_f6_rows_from_matrix()) - known):   # 4 legacy V2.0-deleted F6 rows
        entries.append(dict(run_id=rid, frequency="F6", run_policy="STRESS_REDUNDANT",
            required_seeds=0, schedule_enabled=False, include_in_statistics=False,
            representative_for=None, exclusion_reason="covered_by_representative_F6",
            existing_evidence=None, legacy=True))

    return {
        "schema_version": SCHEMA_VERSION, "decision_date": DECISION_DATE,
        "decision_source": DECISION_SOURCE,
        "immutable_inputs": {"xlsx_sha256": sha256(REPO/"docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"),
                             "generated_md_sha256": {p.name: sha256(p) for p in sorted(
                                 (REPO/"docs/gem5-fi/lsu").glob("gem5-fi-LSU单元故障注入方案*.md"))},
                             "matrix_sha256": sha256(MATRIX), "runid_map_sha256": sha256(RUNID_MAP)},
        "representative_groups": {m: {"representative": pick_rep(m, rs), "runids": sorted(rs)}
                                  for m, rs in sorted(groups.items())},
        "counts": {"total": len(entries),
                   "normal": sum(1 for e in entries if e["run_policy"] == "NORMAL"),
                   "stress_only": sum(1 for e in entries if e["run_policy"] == "STRESS_ONLY"),
                   "stress_redundant": sum(1 for e in entries if e["run_policy"] == "STRESS_REDUNDANT")},
        "entries": entries,
    }

def render_md(pol):
    L = [f"# R6 Frequency Policy (generated — do not hand-edit)",
         "", f"- schema_version: `{pol['schema_version']}`",
         f"- decision_date: {pol['decision_date']}",
         f"- decision_source: {pol['decision_source']}",
         f"- counts: {json.dumps(pol['counts'], ensure_ascii=False)}", "",
         "## Representative F6 groups", "",
         "| model | representative | runids |", "|---|---|---|"]
    for m, g in pol["representative_groups"].items():
        L.append(f"| {m} | {g['representative']} | {', '.join(g['runids'])} |")
    L += ["", "## F6 per-RunID policy table", "",
          "| RunID | policy | req_seeds | sched | in_stats | representative | reason |",
          "|---|---|---|---|---|---|---|"]
    for e in pol["entries"]:
        if e["frequency"] == "F6":
            L.append(f"| {e['run_id']} | {e['run_policy']} | {e['required_seeds']} | "
                     f"{e['schedule_enabled']} | {e['include_in_statistics']} | "
                     f"{e['representative_for'] or ''} | {e['exclusion_reason'] or ''} |")
    return "\n".join(L) + "\n"

def load_policy(path=POLICY_JSON):
    return json.loads(Path(path).read_text("utf-8"))

def query(pol, run_id, seed):
    e = next((x for x in pol["entries"] if x["run_id"] == run_id), None)
    if e is None:
        return {"run_id": run_id, "seed": seed, "decision": "UNKNOWN_RUNID"}
    if e["run_policy"] == "STRESS_REDUNDANT":
        dec = "REFUSE_STRESS_REDUNDANT"
    elif seed <= e["required_seeds"]:
        dec = "ALLOW_STRESS_ONLY" if e["run_policy"] == "STRESS_ONLY" else "ALLOW"
    else:
        dec = "POLICY_NOT_REQUIRED"
    return {**{k: e[k] for k in ("run_policy","required_seeds","schedule_enabled",
             "include_in_statistics","representative_for","exclusion_reason","existing_evidence")},
            "run_id": run_id, "seed": seed, "decision": dec}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify JSON+MD on disk match a fresh render")
    ap.add_argument("--query", nargs=2, metavar=("RUNID", "SEED"))
    a = ap.parse_args()
    pol = build_policy()
    if a.query:
        print(json.dumps(query(pol, a.query[0], int(a.query[1])), ensure_ascii=False))
        return 0
    if a.check:
        ok = (POLICY_JSON.read_text("utf-8") == json.dumps(pol, ensure_ascii=False, indent=1) + "\n"
              and POLICY_MD.read_text("utf-8") == render_md(pol))
        print("POLICY_CHECK: " + ("OK" if ok else "DRIFT"))
        return 0 if ok else 1
    POLICY_JSON.write_text(json.dumps(pol, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    POLICY_MD.write_text(render_md(pol), encoding="utf-8")
    print(json.dumps(pol["counts"], ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Generate and verify counts**

Run: `python3 tools/lsu_freq_policy.py`
Expected output: `{"total": 329, "normal": 261, "stress_only": 39, "stress_redundant": 29}` (261 NORMAL = 325−64; 39 reps + 25 redundant = 64 authoritative F6; +4 legacy redundant = 29).

Run: `python3 tools/lsu_freq_policy.py --check` → `POLICY_CHECK: OK`

- [ ] **Step 5: Verify the pinned query**

Run: `python3 tools/lsu_freq_policy.py --query T04-F6-W4 1` → `"decision": "ALLOW_STRESS_ONLY"`
Run: `python3 tools/lsu_freq_policy.py --query T04-F6-W4 2` → `"decision": "POLICY_NOT_REQUIRED"`
Run: `python3 tools/lsu_freq_policy.py --query T01-F0-W4 3` → `"decision": "ALLOW"`
Run: `python3 tools/lsu_freq_policy.py --query T01-F0-W4 4` → `"decision": "POLICY_NOT_REQUIRED"`

- [ ] **Step 6: Commit**

```bash
git add tools/lsu_freq_policy.py docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.md tests/test_lsu_freq_policy.py
git commit -m "[LSU][MDSPEC][R6-FREQPOLICY] 单一生成器产出机器策略 JSON 与可审计 MD"
git push origin lsu-mdspec-20261019
```

---

### Task 2: Campaign honours the policy (no direct-invocation bypass)

**Files:**
- Modify: `tools/lsu_campaign.py` (argparse `build_parser()` ~L2681; `run_cell_adaptive()` ~L2824; `main()` ~L2744)
- Test: `tests/test_lsu_freq_policy.py`

**Interfaces:**
- Consumes: `lsu_freq_policy.load_policy`, `lsu_freq_policy.query`.
- Produces: new CLI flag `--allow-stress-only` (loud opt-in that permits STRESS_ONLY **seed1 only**); `run_cell_adaptive` refuses with `SystemExit(3)` + explicit message when `query(...)["decision"]` is `REFUSE_STRESS_REDUNDANT` or (`POLICY_NOT_REQUIRED` for the requested seed range).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_lsu_freq_policy.py`:

```python
def test_campaign_refuses_redundant_and_seed2():
    import lsu_campaign as LC
    pol = P.load_policy()
    # every redundant F6 refuses
    red = [e["run_id"] for e in pol["entries"] if e["run_policy"] == "STRESS_REDUNDANT" and not e["legacy"]]
    check("redundant_exist", len(red) == 25)
    import lsu_freq_policy as FP
    bad = [r for r in red if FP.query(pol, r, 1)["decision"] != "REFUSE_STRESS_REDUNDANT"]
    check("all_redundant_refused", not bad, str(bad[:5]))
    # representative seed2 is not-required, seed1 allowed
    check("rep_seed1_allow", FP.query(pol, "T04-F6-W4", 1)["decision"] == "ALLOW_STRESS_ONLY")
    check("rep_seed2_not_required", FP.query(pol, "T04-F6-W4", 2)["decision"] == "POLICY_NOT_REQUIRED")
    # the campaign must expose the gate
    check("campaign_has_gate", hasattr(LC, "policy_decision"))
```
Add `test_campaign_refuses_redundant_and_seed2()` to `main()`.

- [ ] **Step 2: Run to verify it fails**

Run: `python3 tests/test_lsu_freq_policy.py`
Expected: FAIL `campaign_has_gate` (no `policy_decision` attribute yet).

- [ ] **Step 3: Implement the gate in `lsu_campaign.py`**

Add near the top-level imports (after the `lsu_prop_fields` import block):

```python
try:
    import lsu_freq_policy as _FP
except Exception:                                    # policy overlay optional at import time
    _FP = None

def policy_decision(run_id, seed, allow_stress_only=False):
    """Returns 'ALLOW' | 'ALLOW_STRESS_ONLY' | refuses via SystemExit.
    Never lets a policy exclusion masquerade as a technical block."""
    if _FP is None:
        return "ALLOW"
    try:
        pol = _FP.load_policy()
    except FileNotFoundError:
        return "ALLOW"
    d = _FP.query(pol, run_id, seed)["decision"]
    if d in ("ALLOW", "ALLOW_STRESS_ONLY"):
        return d
    if d == "REFUSE_STRESS_REDUNDANT":
        raise SystemExit("[R6-FREQPOLICY] %s is STRESS_REDUNDANT (covered_by_representative_F6); "
                         "refusing to run. Requires a separate explicit human ruling to restore." % run_id)
    if d == "POLICY_NOT_REQUIRED":
        raise SystemExit("[R6-FREQPOLICY] %s seed%d is POLICY_NOT_REQUIRED "
                         "(required_seeds reached / STRESS_ONLY cap)." % (run_id, seed))
    raise SystemExit("[R6-FREQPOLICY] %s seed%d: unknown runid." % (run_id, seed))
```

In `build_parser()` add:

```python
p.add_argument("--allow-stress-only", action="store_true",
               help="[R6-FREQPOLICY] permit a representative STRESS_ONLY F6 at seed1 only; "
                    "never permits seed>1 and never unblocks STRESS_REDUNDANT")
```

In `run_cell_adaptive()` at the top of the seed loop, insert before `seed += 1` (L2841):

```python
        policy_decision(runid, seed + 1, allow_stress_only=args.allow_stress_only)
```

and in `main()` after `a = ...` parsing, record the flag into args used by the loop (it is already on `a`).

Also add the decision into the rolled-up result dict (near L2938):

```python
    result["policy_decision"] = _FP.query(_FP.load_policy(), runid, 1)["run_policy"] if _FP else "UNKNOWN"
```

- [ ] **Step 4: Run to verify it passes**

Run: `python3 tests/test_lsu_freq_policy.py` → `ALL PASS`.

- [ ] **Step 5: Prove no direct-invocation bypass (real command)**

Run:
```bash
python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /tmp/polgate_probe --cells A04-F6-W0 --phase trial --max-seeds-per-cell 1 \
  --fs-checkpoint runs/lsu/fs_cpt_boot/cpt.237949797015
```
Expected: `SystemExit` message `[R6-FREQPOLICY] A04-F6-W0 is STRESS_REDUNDANT …`; non-zero exit; **no gem5 spawned** (`pgrep -cf 'gem5\.opt --outdir'` unchanged).

- [ ] **Step 6: Commit**

```bash
git add tools/lsu_campaign.py tests/test_lsu_freq_policy.py
git commit -m "[LSU][MDSPEC][R6-FREQPOLICY] campaign 直接调用也不得绕过频率政策"
git push origin lsu-mdspec-20261019
```

---

### Task 3: Scheduler `--cells all` filters `schedule_enabled=false`

**Files:**
- Modify: `tools/lsu_r6_schedule.sh` (selection block ~L292-297)
- Test: `tests/test_lsu_freq_policy.py`

**Interfaces:**
- Consumes: `R6-FREQUENCY-POLICY.json` (read via `python3 tools/lsu_freq_policy.py --query` or a small inline `python3 -c`).
- Produces: `--cells all` selects only contract-READY entries whose policy `schedule_enabled=true`.

- [ ] **Step 1: Write the failing test**

```python
def test_scheduler_all_excludes_redundant():
    import subprocess
    out = subprocess.run(["bash", "tools/lsu_r6_schedule.sh", "--cells", "all", "--dry-run"],
                         capture_output=True, text=True, cwd=str(REPO)).stdout
    pol = P.load_policy()
    red = {e["run_id"] for e in pol["entries"] if not e["schedule_enabled"]}
    leaked = [r for r in red if r in out]
    check("scheduler_all_excludes_disabled", not leaked, str(leaked[:5]))
```
Add to `main()`.

- [ ] **Step 2: Run to verify it fails**

Run: `python3 tests/test_lsu_freq_policy.py --only scheduler` (or full) → FAIL `scheduler_all_excludes_disabled` (a redundant RunID appears in the dry-run listing).

- [ ] **Step 3: Implement the filter**

In `lsu_r6_schedule.sh`, right after `sel=[e["run_id"] for e in ready]` (L297) / the `sel=[w for w in want]` branch, add a policy filter that runs regardless of `all` vs explicit list:

```bash
# [R6-FREQPOLICY] drop cells the frequency policy marks schedule_enabled=false.
POL_JSON="$(dirname "$MATRIX")/../../docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json"
if [ -f "$POL_JSON" ]; then
  sel=$(printf '%s\n' "${sel[@]}" | python3 - "$POL_JSON" <<'PY'
import json,sys
pol=json.load(open(sys.argv[1]))
off={e["run_id"] for e in pol["entries"] if not e.get("schedule_enabled", True)}
print("\n".join(r for r in sys.stdin.read().split() if r and r not in off))
PY
)
fi
```

Note: adjust `POL_JSON` to the absolute repo path used elsewhere in the script (the script already computes `$REPO`); prefer `$REPO/docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json`.

- [ ] **Step 4: Verify**

Run: `bash tools/lsu_r6_schedule.sh --cells all --dry-run 2>&1 | grep -cE 'F6-W'` → expected `1` (only `T04-F6-W4`, the sole READY representative). Confirm by inspection that no `STRESS_REDUNDANT` RunID is listed.

- [ ] **Step 5: Commit**

```bash
git add tools/lsu_r6_schedule.sh tests/test_lsu_freq_policy.py
git commit -m "[LSU][MDSPEC][R6-FREQPOLICY] scheduler --cells all 过滤 schedule_enabled=false"
git push origin lsu-mdspec-20261019
```

---

### Task 4: Rewire the wrapper to the tracked policy tool

**Files:**
- Modify: `runs/lsu/r6_c9_run.sh`
- Test: exercised in Task 10 via a shell dry-run assertion.

- [x] **Step 1: Replace the hardcoded rule with a tool call (keep the fallback)**

Replace the `[R6-FREQGUARD]` block from Task 0 with:

```bash
# [R6-FREQGUARD] consult the tracked policy overlay; fall back to the F6 seed1 rule if unavailable.
if [ "$BATCH" = f6 ]; then
  DEC=$(cd "$WT" && python3 tools/lsu_freq_policy.py --query T04-F6-W4 "$SEED" 2>/dev/null \
        | python3 -c 'import json,sys;print(json.load(sys.stdin)["decision"])' 2>/dev/null || true)
  [ -n "$DEC" ] || { [ "${SEED:-0}" -gt 1 ] && DEC=POLICY_NOT_REQUIRED || DEC=ALLOW_STRESS_ONLY; }
  if [ "$DEC" != "ALLOW_STRESS_ONLY" ] && [ "$DEC" != "ALLOW" ]; then
    printf '{"ts":"%s","batch":"%s","seed":%s,"run_id":"T04-F6-W4","decision":"%s","source":"r6_c9_run.sh:R6-FREQGUARD"}\n' \
      "$(date -Is)" "$BATCH" "$SEED" "$DEC" >> "$RUNS/r6_c9_policy_decisions.jsonl"
    echo "POLICY_NOT_REQUIRED batch=$BATCH seed=$SEED ($DEC) — not launched"
    exit 0
  fi
fi
```

- [x] **Step 2: Verify unchanged behaviour**

Run: `./runs/lsu/r6_c9_run.sh f6 2; echo rc=$?` → `POLICY_NOT_REQUIRED … rc=0`; gem5 count unchanged; no `r6_c9_T04-F6-W4_s2` outdir.

- [x] **Step 3: (no commit)** — untracked scratch file.

---

### Task 5: `lsu_runner.py` overlays policy on parsed manifests

**Files:**
- Modify: `tools/lsu_runner.py` (`build_manifest()` ~L97-186)
- Test: `tests/test_lsu_freq_policy.py`

**Interfaces:**
- Produces: each emitted manifest gains `run_policy`, `required_seeds`, `include_in_statistics` read from the overlay (never re-derived).

- [ ] **Step 1: Write the failing test**

```python
def test_runner_manifest_carries_policy():
    import lsu_runner as LR
    m = LR.build_manifest("T04-F6-W4", phase="trial", sample_index=0, output=None)
    check("manifest_run_policy", m.get("run_policy") == "STRESS_ONLY", str(m.get("run_policy")))
    check("manifest_required_seeds", m.get("required_seeds") == 1)
    m2 = LR.build_manifest("T01-F0-W4", phase="trial", sample_index=0, output=None)
    check("manifest_normal_seeds", m2.get("required_seeds") == 3)
```
Adjust the call signature to the real `build_manifest()` signature discovered at implementation time.

- [ ] **Step 2: Run → FAIL** (`run_policy` missing).

- [ ] **Step 3: Implement** — in `build_manifest()`, after `manifest["frequency"] = freq` (L154), add:

```python
    try:
        import lsu_freq_policy as _FP
        _q = _FP.query(_FP.load_policy(), run_id, 1)
        manifest["run_policy"] = _q["run_policy"]
        manifest["required_seeds"] = _q["required_seeds"]
        manifest["include_in_statistics"] = _q["include_in_statistics"]
    except Exception:
        pass                                          # overlay optional; never block manifest freeze
```

- [ ] **Step 4: Run → `ALL PASS`.**

- [ ] **Step 5: Commit**

```bash
git add tools/lsu_runner.py tests/test_lsu_freq_policy.py
git commit -m "[LSU][MDSPEC][R6-FREQPOLICY] runner manifest 叠加 run_policy/required_seeds"
git push origin lsu-mdspec-20261019
```

---

### Task 6: `ready_contract` reports policy without conflating BLOCKED

**Files:**
- Modify: `tools/lsu_ready_contract.py` (per-entry row build ~L399-415; `doc` ~L499-517)
- Test: `tests/test_lsu_freq_policy.py`

**Interfaces:**
- Produces: each entry gains `policy_state ∈ {NORMAL, STRESS_ONLY, STRESS_REDUNDANT}` and top-level `policy_counts`. A policy-excluded entry keeps its technical `status` (may remain `READY`/`PARTIAL`); `status` is never set to `BLOCKED` because of policy.

- [ ] **Step 1: Write the failing test**

```python
def test_ready_contract_policy_not_blocked():
    doc = json.loads((REPO/"docs/gem5-fi/lsu/mdspec/ready_contract.json").read_text("utf-8"))
    bad = [e["run_id"] for e in doc["entries"]
           if e.get("policy_state") == "STRESS_REDUNDANT" and e.get("status") == "BLOCKED"
           and e.get("category") != "…technical reason…"]
    check("policy_not_mapped_to_blocked", not bad, str(bad[:5]))
    check("policy_state_present", all("policy_state" in e for e in doc["entries"]))
```
(Implement the exact second condition to reflect the real `category` semantics; the invariant is: policy exclusion ⇒ not `BLOCKED`.)

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** — add `policy_state` per row from the overlay, and a `policy_counts` dict to `doc`. Do **not** touch the existing `_classify` / chain-gate demotion logic; policy is additive.

- [ ] **Step 4: Regenerate + verify**

Run: `python3 tools/lsu_ready_contract.py` then the test → `ALL PASS`.

- [ ] **Step 5: Commit**

```bash
git add tools/lsu_ready_contract.py docs/gem5-fi/lsu/mdspec/ready_contract.json docs/gem5-fi/lsu/mdspec/ready_contract.md tests/test_lsu_freq_policy.py
git commit -m "[LSU][MDSPEC][R6-FREQPOLICY] ready_contract 报告 policy_state，不与 BLOCKED 混同"
git push origin lsu-mdspec-20261019
```

---

### Task 7: `R6-STATUS-TABLE` gains an orthogonal `policy_state` axis

**Files:**
- Modify: `tools/lsu_r6_status_table.py` (`EVIDENCE_STATES`/`ELIGIBILITIES` ~L74-80; row build ~L275-299)
- Test: `tests/test_lsu_freq_policy.py`

**Interfaces:**
- Produces: a third, orthogonal field `policy_state ∈ {NORMAL, STRESS_ONLY, STRESS_REDUNDANT}` on every row; `POLICY_NOT_REQUIRED` never counted as failure/`BLOCKED`/`EVIDENCE_MISSING`.

- [ ] **Step 1: Write the failing test**

```python
def test_status_table_policy_axis():
    doc = json.loads((REPO/"docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json").read_text("utf-8"))
    rows = doc["rows"] if isinstance(doc, dict) and "rows" in doc else doc
    check("policy_axis_present", all("policy_state" in r for r in rows))
    bad = [r["run_id"] for r in rows
           if r.get("policy_state") == "STRESS_REDUNDANT"
           and r.get("evidence_state") in ("EVIDENCE_MISSING", "TRUNCATED")]
    check("redundant_not_counted_missing", not bad, str(bad[:5]))
```
Adjust to the real top-level shape after reading the file.

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** — add `POLICY_STATES = ("NORMAL","STRESS_ONLY","STRESS_REDUNDANT")` and populate `policy_state` per row from the overlay; leave `evidence_state`/`eligibility` untouched. A `STRESS_REDUNDANT` run with no runs stays `NOT_RUN` — not `EVIDENCE_MISSING`.

- [ ] **Step 4: Regenerate (real command)**

Run: `python3 tools/lsu_r6_status_table.py` then the test → `ALL PASS`.
Confirm `T04-F6-W4` row: `policy_state=STRESS_ONLY`, existing evidence preserved.

- [ ] **Step 5: Commit**

```bash
git add tools/lsu_r6_status_table.py docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md tests/test_lsu_freq_policy.py
git commit -m "[LSU][MDSPEC][R6-FREQPOLICY] R6-STATUS-TABLE 增加正交 policy_state 轴"
git push origin lsu-mdspec-20261019
```

---

### Task 8: Authoritative docs — amendment + policy reference

**Files:**
- Modify: `docs/gem5-fi/lsu/完整任务执行清单.md`, `docs/gem5-fi/lsu/总方针.md`, `docs/gem5-fi/lsu/task_plan.md`, `docs/gem5-fi/lsu/progress.md`, `docs/gem5-fi/lsu/findings.md`
- Test: `tests/test_lsu_freq_policy.py` (clean-checklist assertions covered in Task 10)

- [x] **Step 1: `完整任务执行清单.md`** — append an `## Amendment 2026-10-25 (frequency policy)` section that: keeps ITEM-001..325 verbatim; does not delete any of the 64 F6 ITEMs; states NORMAL/STRESS_ONLY/STRESS_REDUNDANT + `required_seeds` + statistics-inclusion rules; points to `R6-FREQUENCY-POLICY.json`; records this ruling as the amendment. Do not alter any ITEM's injection location/model/workload/propagation spec.

- [x] **Step 2: `总方针.md`** — add: F6 is a separate stress test, excluded from the F0–F5 main statistics; this ruling supersedes all earlier F6 multi-seed requirements; other frequency definitions unchanged.

- [x] **Step 3: `task_plan.md`** — pilot completion condition becomes `policy.required_seeds`; drop the assumption that all RunIDs use the same seed count; keep 325-ITEM audit coverage.

- [x] **Step 4: `progress.md` + `findings.md`** — record: this ruling; the currently-running normal seed2/3 (`r6c9-s2`, `r6c9-s3`); the `T04-F6-W4` seed1 certified evidence; that the XLSX/generated-MDs/CSV/runid_map were left unchanged and why; the new policy file paths + version; and the measured 64-vs-68 F6 delta.

- [x] **Step 5: Verify** — `grep -c '^### ITEM-' docs/gem5-fi/lsu/完整任务执行清单.md` → `325`; no F6 ITEM removed (`grep -c 'ITEM-.*F6-' … ` → `64`).

- [x] **Step 6: Commit**

```bash
git add docs/gem5-fi/lsu/完整任务执行清单.md docs/gem5-fi/lsu/总方针.md docs/gem5-fi/lsu/task_plan.md docs/gem5-fi/lsu/progress.md docs/gem5-fi/lsu/findings.md
git commit -m "[LSU][MDSPEC][R6-FREQPOLICY] 权威文档记录频率政策裁决与 F6 去重"
git push origin lsu-mdspec-20261019
```

---

### Task 9: Immutable-input integrity test

**Files:**
- Test: `tests/test_lsu_freq_policy.py`

- [ ] **Step 1: Write the test**

```python
import hashlib
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
BASE = {
 "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx":
   "389546f0f8f3d0c6ece2ed33d3a8cfd1426faa9bbc101f7ad7d9612159e273e0",
 "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md":
   "1c1cefae05bafb86966e0dfc8477c4866480bac93ce785b8a1c5710476ee0f28",
 "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md":
   "33b3a0576ad9150238d04bc2382930d8e9572934536bb1f9c55507e28ec15c37",
 "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md":
   "a5859486fef054344dad6d594594f28b489de8f5a088519b4687dd8904b4ff75",
 "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-09-逐RunID传播监控.md":
   "2e71b37fe5a3d8cde7a2f93221500fdaa68a5ae185d40ef16c12c66e81025125",
 "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-10-源码监控映射.md":
   "d1b92b03502cf68bc5241fc5051485cb61ffadfc7deec3d32cccd1a57919b63f",
 "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv":
   "4eb13ba483d3b8a67f017c154e955efaed24f87b358e3729ae6b9d5333e26ffc",
 "docs/gem5-fi/lsu/mdspec/runid_map.json":
   "7ae61acceb0dab04de90f189cc56cb17ec30db9179ea444dd5579bd88a108ff5",
}
def test_immutable_inputs_unchanged():
    for rel, want in BASE.items():
        check(f"sha_unchanged::{rel}", sha(REPO/rel) == want, sha(REPO/rel))

def test_counts_unchanged():
    import csv
    rows = list(csv.reader(open(REPO/"artifacts/lsu-trial/07-expanded-matrix-backfilled.csv", encoding="utf-8")))
    data = [r for r in rows[1:] if len(r)>1 and r[1].strip()]
    check("csv_rows_337", len(data) == 337)
    check("csv_f6_68", sum(1 for r in data if r[1].split("-")[1] == "F6") == 68)
    check("csv_runids_superset_325", len({r[1] for r in data}) >= 325)
```
Add both to `main()`.

- [ ] **Step 2: Run** → `ALL PASS` (nothing changed these inputs).

- [ ] **Step 3: Commit** (fold into Task 10's commit if convenient)

---

### Task 10: Complete the 16-assertion regression suite + full regression

**Files:**
- Test: `tests/test_lsu_freq_policy.py` (final form)

- [ ] **Step 1: Ensure all 16 required assertions are present and wired into `main()`:**

1. checklist still has ITEM-001..325, RunIDs unique, none deleted (Task 8 test)
2. policy covers all 325 RunIDs (Task 1 test)
3. F6 original rows still 64 — on checklist + runid_map (Task 1 test); CSV = 68 documented (Task 9)
4. `T04-F6-W4` = STRESS_ONLY, `required_seeds=1` (Task 1/2 test)
5. a representative F6 seed1 is schedulable (`ALLOW_STRESS_ONLY`) (Task 1/2 test)
6. same representative F6 seed2 rejected as `POLICY_NOT_REQUIRED` (Task 1/2 test)
7. STRESS_REDUNDANT any seed not scheduled by default (Task 2 test)
8. F0–F5 `required_seeds=3` (Task 1 test)
9. scheduler `all` excludes STRESS_REDUNDANT (Task 3 test)
10. campaign direct call cannot bypass policy (Task 2 test)
11. F6 not in the main statistics denominator (`include_in_statistics=false` for all F6) — add:
```python
    check("f6_not_in_stats", all(not e["include_in_statistics"]
          for e in P.load_policy()["entries"] if e["frequency"] == "F6"))
```
12. policy-not-required not counted as failure/BLOCKED/evidence_missing (Task 7 test)
13. XLSX SHA unchanged (Task 9)
14. 5 generated MD SHAs unchanged (Task 9)
15. CSV + runid_map retain all 325 RunIDs (Task 9)
16. currently-running normal seed2/seed3 unaffected — assert the policy did not touch `runs/`:
```python
def test_running_seeds_untouched():
    import subprocess
    check("gem5_still_running", int(subprocess.run(["bash","-c",
          "pgrep -cf 'gem5\\.opt --outdir' || true"],capture_output=True,text=True).stdout.strip() or 0) >= 1)
```

- [ ] **Step 2: Run the suite**

Run: `python3 tools/lsu_test_runner.py --only tests/test_lsu_freq_policy.py`
Expected: `ALL PASS`.

- [ ] **Step 3: Full regression, NEW FAIL=0**

Run: `python3 tools/lsu_test_runner.py --json /tmp/lsu_regress_policy.json 2>&1 | tail -30`
Expected: `NEW FAIL=0` (record the PASS/ENV/FAIL counts; any ENV must be disclosed, not counted as PASS). No SKIP/XFAIL, no weakened assertions.

- [ ] **Step 4: Commit**

```bash
git add tests/test_lsu_freq_policy.py
git commit -m "[LSU][MDSPEC][R6-FREQPOLICY] 16 项频率政策契约 + 不可变输入完整性回归"
git push origin lsu-mdspec-20261019
```

---

### Task 11: Land the 5 NORMAL × 3 seeds → 16/16 (operational, do not break the run)

**Files:** none (running experiments; evidence under `runs/lsu/`)

- [ ] **Step 1:** Do **not** touch `r6c9-s2` / `r6c9-s3`. Let `T01-F0-W4` seed2/seed3 finish; the same chains continue to `T02-F0-W4`, `T02-F2-W4`, `T04-F0-W4`, `T04-F2-W4` at seeds 2 and 3.
- [ ] **Step 2:** Monitor only:
```bash
tmux ls; pgrep -af 'gem5\.opt --outdir' | wc -l   # must stay ≤ 2
```
- [ ] **Step 3:** For each of the 5 NORMAL RunIDs × each seed, verify on completion: full chain or real explicit containment; `admitted=true`; `certified=true`; `evidence_truncated=false`; `violations=[]`; gzip intact; stats non-zero; injection counts consistent; campaign/checker agree; binary SHA undrifted (`e80528…6959`).
- [ ] **Step 4:** Confirm final tallies: NORMAL 15/15, `T04-F6-W4` STRESS_ONLY 1/1, total **16/16**. Record the per-RunID evidence paths.

---

### Task 12: Quiesce, commit, push the integration branch

- [ ] **Step 1:** Confirm zero running work:
```bash
pgrep -af 'gem5\.opt' ; pgrep -af 'lsu_campaign.py' ; pgrep -af 'scons' ; tmux ls
```
All must be empty (the `r6c9-s2`/`s3` sessions self-kill on chain completion). If gem5 is still running, **wait** — do not kill.
- [ ] **Step 2:** Confirm no unrelated files are staged. `git status --short` — stage explicit paths only.
- [ ] **Step 3:** Ensure every task commit from Tasks 1–10 is present; push (already pushed per-task) and verify:
```bash
git log --oneline origin/lsu-mdspec-20261019..HEAD
git push origin lsu-mdspec-20261019
```
- [ ] **Step 4:** Be explicit that the **existing binary was NOT rebuilt this round**:
  - `binary_source_head = 12d05e8ca38e67b2ee1007bb7cbaab7351ea00df`
  - `binary_sha256 = e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
  - `analysis_tool_head = <policy commit>` (the Task 10 commit)

---

### Task 13: Merge `lsu-mdspec-20261019` into `fi-ding` in a clean merge worktree

**Files:** none in the current worktree — a **separate** worktree is used.

- [ ] **Step 1:** `git fetch origin` ; inspect divergence:
```bash
git fetch origin
git log --oneline origin/fi-ding..lsu-mdspec-20261019 | head
git log --oneline lsu-mdspec-20261019..origin/fi-ding | head
git diff --stat origin/fi-ding lsu-mdspec-20261019 | tail -40
```
- [ ] **Step 2:** Create a fresh merge worktree based on latest `origin/fi-ding`:
```bash
git worktree add ../merge-r6-policy -b r6-policy-merge origin/fi-ding
cd ../merge-r6-policy
git merge --no-ff --no-squash lsu-mdspec-20261019
```
No rebase of existing experiment commits, no squash, no force push, and the running experiment worktree is never branch-switched.
- [ ] **Step 3:** On a **semantic** conflict in injector/config/oracle/propagation code: **stop and report**. Ordinary doc conflicts or stale test expectations may be reconciled minimally without weakening any assertion.

---

### Task 14: Verify the merge, rebuild from merged `fi-ding`, and push

- [ ] **Step 1:** In the merge worktree, run targeted tests then full regression:
```bash
python3 tools/lsu_test_runner.py --only tests/test_lsu_freq_policy.py
python3 tools/lsu_test_runner.py --json /tmp/lsu_regress_merge.json 2>&1 | tail -30
```
Require `NEW FAIL=0`.
- [ ] **Step 2:** Re-verify consistency: F6 policy unchanged; 325 ITEMs; status table consistent; 16/16 evidence intact.
- [ ] **Step 3:** If `fi-ding` introduced **no** semantic change to injector/config/oracle/propagation → **do not re-run the 16 samples**. If it did → list and re-run only the affected canary.
- [ ] **Step 4:** One unified build from merged `fi-ding` (only if C++ changed; else record that no rebuild was needed):
```bash
cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt 2>&1 | tee /tmp/build_merge.log
grep -iE 'warning|error' /tmp/build_merge.log | tail
sha256sum ../../build/ARM/gem5.opt    # repo-root binary
```
Record: `fi-ding merge commit`, new `binary SHA-256`, build log, warning diff, `analysis_tool_head`.
- [ ] **Step 5:** Minimal golden/smoke + full regression pass, then push:
```bash
git push origin fi-ding
git fetch origin && git rev-parse origin/fi-ding && git rev-parse HEAD   # must match
```

---

### Task 15: Next batch — only after the branch close-out

- [ ] **Step 1:** Only now, select the next batch: **6 NORMAL, RUNNABLE, incomplete** RunIDs from F0–F5 (never F6).
- [ ] **Step 2:** Run seed1 pilot only, max parallel 2, using the **merged, frozen** binary.
- [ ] **Step 3:** Do not auto-start any new F6; schedule other representative F6 as stress-only seed1 individually, later, once the NORMAL phase is stable. Do not start the formal full-matrix campaign. Do not merge `fi-ding` elsewhere.

---

## Self-Review

**1. Spec coverage** — every ruling section maps to a task: §二 emergency gate → Task 0/4; §四/§五 policy + representatives → Task 1; §六 docs → Task 8; §七 execution chain (runner/campaign/schedule/contract/status) → Tasks 2,3,5,6,7; §七.10/§三 no-deletion of CSV/runid_map → Tasks 9; §八 tests + binary identity → Tasks 9,10,12; §九 16/16 → Task 11; §十 close-out + next batch → Tasks 12–15; amendment (quiesce→commit→merge→build→push→verify→next) → Tasks 12–15. The 64-vs-68 F6 reconciliation is explicit in Global Constraints + Tasks 1/9.

**2. Placeholder scan** — no TBD/TODO; code blocks are complete for the core tool and gates. Tasks 5–7 reference "adjust to the real signature/shape after reading the file" — acceptable only because those are existing-file edits where the exact line numbers were recon-verified (given above), and the invariant to assert is stated verbatim.

**3. Type consistency** — `run_policy`/`required_seeds`/`schedule_enabled`/`include_in_statistics`/`representative_for`/`exclusion_reason`/`existing_evidence`/`policy_state`/`decision` are used identically across Tasks 1–7. `query()` is the only rule evaluator; no consumer re-derives the rule. `POLICY_NOT_REQUIRED` and `STRESS_REDUNDANT` are distinct tokens (`decision` vs `policy_state`).

**4. Review Focus coverage** — item 1 → Tasks 2,5,6,7 assert consumption-from-overlay; item 2 → Task 0/4 real-command verification; item 3 → Task 7; item 4 → Task 2 Step 5; item 5 → Task 3; item 6 → Task 9.

---

## Amendment 2026-10-25b — four verified findings from the user (mandatory, pre-Task-9)

These override any conflicting plan text below. The user supplied all four as *verified*.

**A1 — `--max-seeds-per-cell N` is cumulative, not per-seed.** `r6_c9_run.sh` passes `--max-seeds-per-cell "$SEED"`, so the `_s2` dir holds seed1+seed2 and `_s3` holds seed1+seed2+seed3. Re-runs of lower seeds are **NOT additional independent samples**. The 16/16 tally must deduplicate by `(RunID, sample_run_id/seed)`: exactly one authoritative evidence copy per `(RunID, seed)`; every superseded duplicate directory must be **listed as excluded** (never silently counted, never deleted).

**A2 — do not launch new duplicate seeds via this wrapper style.** The still-running `T04-F0-W4_s3` campaign is currently re-executing seed2 (and will then run seed3). Let it finish through the existing graceful-exit path — **do not kill it now**. Afterwards, no new invocation may be started that re-runs already-present `(RunID, seed)` pairs.

**A3 — a non-graceful timeout is not a PASS.** The previous `T04-F0-W4` seed2 evidence recorded `graceful=false, timeout=true, gem5_exit=-15` → **must not be counted as PASS**. After the current cumulative campaign completes, re-check the new seed2: if it is still non-graceful, **stop and do not merge**; diagnose why graceful exit failed. A forced timeout kill must never be recorded as a pass.

**A4 — policy must be exactly 325 unique RunIDs.** The generator currently reports `total=329` while `ready_contract` reports `325` with `policy_counts = 261+39+25`. The 329 = 325 authoritative + 4 legacy CSV-only F6 rows. This difference must be **explained and eliminated** before Tasks 9/10: the authoritative policy `entries` must be **exactly the 325 unique RunIDs**, with no hidden aliases or duplicates. The 4 legacy F6 rows (V2.0-deleted models `T09-F6-W4`, `S12-F6-W5`, `C13-F6-W6`, `O08-F6-W7`) move to a **separate, explicitly-named, clearly-documented section** (not `entries`), so the CSV stays covered without inflating the authoritative count. `query()` must still refuse them.

**Consequent additions to the task list:**
- **Task 1b (new):** restructure `tools/lsu_freq_policy.py` so `entries` == exactly 325; move the 4 legacy rows to a separate key; regenerate JSON+MD; update `tests/test_lsu_freq_policy.py` (`policy_covers_325`, `f6_is_64`) and add an explicit assertion that `len(entries) == 325` and `len({e["run_id"] for e in entries}) == 325`. Re-verify the campaign gate still refuses legacy F6.
- **Task 11 (revised):** the 16/16 count is over **distinct `(RunID, seed)` pairs**, produced by a dedup pass that writes an excluded-directories list; and the merge gate includes A3's graceful-exit check on `T04-F0-W4` seed2.
- **Task 8** must record A1–A4 in `progress.md`/`findings.md`.

### Task 11b (added 2026-10-25c) — guarded fix for the missing `squash_masked` containment kind

**Origin:** the Task 11 dedup verification returned **15/16**, with `T02-F2-W4` seed2 not admitted. Read-only diagnosis
(`.superpowers/sdd/2026-10-25-lsu-r6-frequency-policy/task-11-diagnosis.md`, confidence ~95%) found a **classifier gap**,
not a data fluke: seed2's chain does close L0→L5 at a `squash_masked` containment event, but that kind is absent from
`_TLB_KIND_LAYER` (`tools/lsu_chain_check.py:111`) and `P.KIND_LAYER`, so `_event_has_prefix` (`:335`) rejects it and the
`detected_contained` (`:437`), `squash_replay_masked` (`:442`) and `containment_from_events` (`:975/:1000`) closure paths
are dead for this kind.

**Authorized by explicit user ruling (2026-10-25c): implement the GUARDED fix.** Requirements:
1. Register `squash_masked` → L4 in both layering maps.
2. Guard against READY inflation: an explicit `errant_commit` terminal (genuine escape) must take PRECEDENCE over
   containment-by-squash; the squash path may only produce `detected_contained` when no higher-priority explicit uncontained
   terminal is present. (Note: `oracle=Crash` alone is NOT disqualifying — siblings with `Crash` are already admitted via a
   `full` chain.)
3. **Regrade audit (mandatory):** re-run the classifier over ALL existing evidence (no new gem5), and list every sample
   whose `terminal`/`provable_to`/`admitted` changes, with justification that no genuinely-escaping sample is promoted.
4. Add a regression test pinning the contain-by-squash path.
5. Acceptance: `T02-F2-W4` seed2 → `detected_contained`, admitted; full regression `NEW FAIL=0`; immutable inputs unchanged.
6. One unit per commit; the merge stays BLOCKED until 16/16 is re-verified.
