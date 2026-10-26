# 2026-10-26 — 0202 六链重建 (six-chain rebuild)

**Branch**: `fix/0202-six-chain-20261026` (base `origin/lsu-mdspec-20261019` = `de81266c`)
**Host**: `cathelper-k8s-worker2` (openEuler 22.03 LTS, aarch64 Kunpeng-920, 64 cores, 2 NUMA nodes, 376 GiB RAM)
**Goal**: six isolated seed-1 engineering canaries, each a complete observation closed loop
under one frozen binary.

## 0. Scope (only these six RunIDs; nothing else)

| ITEM | RunID | Model | Freq | Fault | Target field |
|---|---|---|---|---|---|
| ITEM-041 | T01-F0-W4 | T01 | F0 | 单比特翻转 | L1 d-TLB VPN tag |
| ITEM-047 | T02-F0-W4 | T02 | F0 | 双比特翻转 | PPN |
| ITEM-049 | T02-F2-W4 | T02 | F2 (100000 evt ±50%) | 双比特翻转 | PPN |
| ITEM-052 | T04-F0-W4 | T04 | F0 | 换值 (legal mapped page) | PPN |
| ITEM-053 | T04-F2-W4 | T04 | F2 | 换值 | PPN |
| ITEM-054 | T04-F6-W4 | T04 | F6 (first TLB hit) | 换值 | PPN |

Workload W4 = `TLB-AliasPerm` → FS carrier `configs/fs/tlb_probe.rcS`.
Seed: `tools/lsu_seed.py` only (never hand-picked). **seed-1 only** — no seeds 2–3, no
30-sample pilot, no 385 screening, no formal 325. Debug runs tagged `ENGINEERING_ONLY`.

## 1. Baseline verification (DONE — evidence)

- `git merge-base --is-ancestor 3f3eb617 HEAD` → **0** (baseline contained). HEAD `de81266c`.
- Both known blockers are **already fixed** by commits after `3f3eb617`; re-verified in source:
  - `f2893b0b` R6-FIXCORR — `CHAOSPropagation.cc:1674-1675` labels `corr=origin` **only** on a
    contained terminal with no open downstream arm; grader NOT relaxed.
  - `4e61725f` R6-F0FUNNEL — `CHAOSArmTLB.cc:548-579` passive F0 counts
    (`attempted` at entry, `eligible` after cap+probability and before skip); summary reuses
    the real `faults_injected_count`. No RNG/skip/cap change.
  - F2 routing (`6ec7c5aa`), T04 live-page predicate (`37446e7a`), F6 (`f77bb0ab`) present.
- **Consequence**: no re-fix of those four; Phase 3 is satisfied by audit. Only ONE new patch
  unit is required (U1 below), driven by the checkpoint-identity rule.

## 2. Patch units (one patch = one commit, pushed to the branch)

### U1 — `lsu_runner.py` FS checkpoint is configurable, never a hardcoded old name
- **Why**: `tools/lsu_runner.py:42` hardcodes `CPT = runs/lsu/fs_cpt_boot/cpt.237949797015`.
  This rebuild generates a NEW checkpoint; faking that name (symlink/rename) is forbidden.
- **Change**: add `--fs-checkpoint` CLI + `LSU_FS_CHECKPOINT` env override, resolved in one
  place; record the resolved real path in `manifest.identity.checkpoint`; `build_guard_cmd`
  uses the resolved path. Default stays the legacy path for backward compatibility, but the
  freeze for this task always passes an explicit value.
- **Test** (`tests/test_lsu_runner_fs_checkpoint.py`): explicit arg wins; env used when no arg;
  identity + command both carry the same resolved path; a path with a non-legacy `cpt.<tick>`
  name round-trips; absent-everything falls back to legacy (documented).
- **Verify**: new test PASS; `test_lsu_freq_policy.py`, `test_lsu_ftier_armtlb_lookup.py`,
  `test_lsu_r6_f0funnel.py`, `test_lsu_r6_contained_corr.py` PASS; a `--dry-run` shows the
  real checkpoint in the command; unaffected SE hello smoke PASS.
- No C++ change ⇒ does not invalidate the binary; still must land **before** the freeze
  manifest is written (freeze binds tool SHAs).

## 3. Build (Phase 4)

- `cd CHAOS/gem5 && scons -j8 build/ARM/gem5.opt` under the guard build lock. **-j8** (LSU
  总方针 §8.1 hard cap 8, one compile task at a time) — the conservative of the two
  documented rules (CLAUDE.md says -j16; 总方针 and the task both cap at 8).
- Binary path per `tools/lsu_gem5_bin.py`: `CHAOS/gem5/build/ARM/gem5.opt`; exported as
  `LSU_GEM5_BIN` for every run.
- Required evidence: full command + exit code, log, `file` output, size, mtime, SHA256, git
  HEAD + dirty status, new-vs-existing warning separation, `scons: done building targets.`

## 4. Freeze manifest (Phase 4, after U1)

Bind: git commit, gem5 SHA256, all key tool SHAs (`lsu_runner.py`, `lsu_campaign.py`,
`lsu_chain_check.py`, `lsu_ready_contract.py`, `lsu_seed.py`, `lsu_guard.py`,
`lsu_freq_policy.py`, `lsu_gem5_bin.py`), compiler/Python/SCons versions, FS asset SHA256
(`vmlinux`, `ubuntu.img`, `boot.arm64`, dtb), date, hostname, checkpoint identity.
→ `docs/gem5-fi/lsu/evidence/0202/0202-FREEZE-MANIFEST.md` + `.json`.
Any C++/semantic change ⇒ freeze invalid ⇒ rebuild + rehash + restart from canary #1.

## 5. FS checkpoint + golden (Phase 5)

- Checkpoint from a **new** dir: `runs/lsu/0202_fs_cpt_boot_<ts>/`. Atomic boot,
  `--readfile configs/fs/boot_ckpt.rcS`, `m5 checkpoint` → real `cpt.<tick>` path recorded
  with a file-manifest SHA256. Success = guest reaches userspace, `m5 checkpoint` completes,
  `m5 exit` clean, memory/device state present.
- Golden: **two** no-injection runs over the same checkpoint with `configs/fs/tlb_probe.rcS`;
  require identical oracle md5 (`b6d81b360a5672d80c27430f39153e2c`) and `ok=10/10` in both;
  config.ini proof of B0/O3/TLB params; timeouts derived from measured wall time (no arbitrary
  shortening). Use `tools/lsu_r6_golden_control.py` (goes through `lsu_gem5_bin.py`).

## 6. Gascheduling the six canaries (Phase 6–7)

- Manifests: `python3 tools/lsu_runner.py --item ITEM-0NN --phase engineering --sample-index 0
  --output runs/lsu/0202_verify6_<ts>/manifests/<ITEM>.json` then freeze with the real
  checkpoint + a `ENGINEERING_ONLY` tag. `--dry-run` first: assert six pairwise-distinct
  normalized commands, F2 lines carry `--tlb_lsu_tier F2`, F6 carries `F6`, F0 carries none,
  sample count = 1 per RunID, output dirs disjoint.
- Execute via `lsu_runner.py --execute` (guard-wrapped) or `lsu_campaign.py` per-run, serial
  first; **max 2 concurrent** after profile; never exceed 4; never via `/tmp`.
- Order: T01-F0 → T02-F0 → T04-F0 → T02-F2 → T04-F2 → T04-F6.
- Per run: independent manifest, PID/PGID, logs, resource log, heartbeat, propagation stream,
  fault log, stats/config, classification, chain report, cell result, COMPLETE/INVALID.
- Failure policy: 1st diagnose + minimal fix; 2nd change strategy; 3rd same-class failure →
  STOP that RunID, raise DECISION REQUEST. If a semantic fix changes the freeze → mark all
  prior canaries `INVALID_FOR_NEW_FREEZE`, rebuild, restart from canary #1.

### Runtime-proof targets (the whole point of the rebuild)
- T01-F0: a contained terminal (`effective_pa_unchanged`) with `corr=origin`, continuous parent
  chain, later layers `N/A: contained at L2`, admitted.
- T02-F0 / T04-F0: full L0→L5 chain to a real terminal (`errant_commit` / real panic/Oops),
  **not** `chain_end`; F0 summary `CHAOS_LSU_TRIGGER: ... eligible=N` present.
- T02-F2 / T04-F2: `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1` and a
  `tier=F2` summary whose interval semantics differ from F0 (non-collapse).
- T04-F6: `tier=F6`, `injected=1`, matching `numFaultsInjected=1` (no phantom).
- T04 (all): replacement source/target both live, same page size, `pfn != 0`.

## 7. Strict acceptance (Phase 8)

Per run: `tools/lsu_chain_check.py` + `tools/lsu_ready_contract.py` (strict) actually executed,
output saved. Assert: identity == freeze; stream non-truncated, unique event ids, resolvable
parents; attempted/eligible/injected/applied/activated conservative and `activated=1`;
`inj` target/model/bits/freq/seed == manifest; one continuous parent path L0→terminal; corr
continuity; propagation terminus is a real detection/outcome event; containment terminus is a
real non-lifecycle contained terminal; every unreached layer has an honest N/A, never Unknown;
classification consistent with oracle/fault log/stats/chain report; T04/F2/F6 frequency
non-collapse.

## 8. Deliverables / stop

- `docs/gem5-fi/lsu/evidence/0202/R0202-VERIFY6.md` + machine-readable `.json`/`.csv`.
- Raw evidence root `runs/lsu/0202_verify6_<ts>/` (not committed).
- STOP after the six seed-1 canaries. No seeds 2–3, no formal, no extra RunIDs.

## 9. Resource gates (from 总方针 §8 + task)

- Compile: max `-j8`, one compile task at a time.
- gem5: concurrency 1 → (after profile) 2; hard cap 4.
- Do-not-start: `MemAvailable < 12 GiB`; sustained swap growth; unknown heavy processes; space
  short. Sample every 60 s; kill only PIDs/PGIDs owned by this task.
- **Host note**: swap was disabled at boot (`/etc/fstab` swap line commented; `SwapFree` 0 GiB),
  which made `tools/lsu_guard.py gate` refuse every run. A 16 GiB swapfile was provisioned at
  `/home/swapfile.0202` (not persisted to fstab) so the repo's own gate passes honestly rather
  than being bypassed. Disclosed in the report.

## 10. Stop / DECISION REQUEST conditions

- Baseline divergence (`3f3eb617` unreachable) — did not occur.
- Submodule/FS asset unobtainable — did not occur.
- Any strict-acceptance rule that cannot be met without relaxing the checker, changing a seed,
  editing the oracle/excel/frequency definitions, or faking evidence → STOP + DECISION REQUEST.
- Same-class failure 3× on one RunID → STOP that RunID + DECISION REQUEST.
