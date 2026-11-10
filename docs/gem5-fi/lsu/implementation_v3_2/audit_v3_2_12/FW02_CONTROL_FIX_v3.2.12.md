# FW02 control fix — SUPP-FW02-C01 misfire root cause and the corrected control command

**Round:** LSU v3.2.12 propagation closure (Tasks 9/11/12/13 evidence audit)
**Auditor worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` (HEAD `f15fe483`)
**Pilot binary (pinned, verified on disk):** `sha256(build/ARM/gem5.opt) = 720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070` (equals `logs_v3_2_12/binary_v3212_trace.sha256` and every SUPP manifest's `binary_sha256`)
**Date:** 2026-11-10. Read-only audit; no gem5/scons run, nothing committed, original misfire artifacts untouched.

---

## 1. The observed misfire

`SUPP-FW02-C01` is the matched no-fault control for FW02 context R01: the runbook
command (RUNBOOK_v3.2.12.md §4) is the R01 fault command plus `--probability 0.0`.
Recorded outcome (`pilots_v3_2_12/SUPP-FW02-C01/pilot_meta.json`):

- `run_role: "CONTROL"`, `injection_count: 1`, `control_valid: false`,
  `control_misfire: true`, `accepted: false`;
- `lsq_fwd_injections.log`: `Tick: 556325, Site: store->load_forward_decision,
  FaultType: f6_fw02_suppress, load_seq: 397, store_seq: 383, Vaddr: 0x7ffffefc28,
  FwdSize: 8, faults_injected: 1` plus `CHAOS_FW02_SUMMARY: observed=6
  suppressed=1 load_seq=397 store_seq=383`;
- `oracle.log`: `expected=1f4cbf14327717df got=1f4cbf14327717df ORACLE_PASS`
  (the suppressed forward was value-neutral on this pair);
- the runner process exited **1** (`run_pilot.py:1028` — `return 0 if accepted else 1`).
  `pilot_meta.json`'s `"exit_code": 0` is the *gem5 child's* return code
  (`proc.returncode`, `run_pilot.py:987`), not the runner's.

The misfire is **byte-identical to the SUPP-FW02-R01 fault run**: same tick 556325,
same load_seq 397 / store_seq 383, same vaddr 0x7ffffefc28, same summary line —
i.e. `--probability 0.0` had **zero effect** on whether the FW02 fault fires.

## 2. Root cause (exact, with file:line at HEAD f15fe483)

The CLI was passed and reached gem5 — this is **not** a CLI-plumbing bug and **not**
a trigger-probability override. `command.txt` and `manifest.json` (`"probability"`,
`"0.0"` at manifest line 46) both record `--probability 0.0`. The cause is the
documented design of the F6_fw02 injector: it is **ordinal-gated and deliberately
probability-independent**, so a mounted `f6_fw02` injector fires even at
probability 0:

1. **Attach ignores probability for F6Fw02.** The injector self-attaches when
   `probability > 0.0f || struct_mode == StructMode::F6Fw02 || …`
   (`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:81-87`; `cpu->lsqFwd = this`
   at `:126`), and the F6Fw02 block repeats it explicitly:
   "`FW02: attach even with probability==0 (this mode suppresses a forwarding
   match, it does not corrupt forwarded bytes)`" (`CHAOSLSQFwd.cc:134-138`).
   With probability 0 the SQ01 mode does NOT satisfy `:81` (Sq01Bit3 is not in the
   exception list), `cpu->lsqFwd` stays NULL, and the `lsq_unit.cc:2120` hook guard
   (`if (cpu->lsqFwd && !(…) && !…isCacheMaintenance() && !…isAtomic())`) blocks the
   call — which is exactly why `SUPP-SQ01-C01` (same `--probability 0.0` convention)
   is a valid control with `injection_count=0` and no `lsq_fwd_injections.log`.
2. **The suppression decision never consults probability.**
   `CHAOSLSQFwd::maybeSuppressForwarding` (`CHAOSLSQFwd.cc:1019-1071`, called at
   `lsq_unit.cc:1787` inside the FullAddrRangeCoverage branch) gates only on
   `struct_mode == F6Fw02` (`:1023`), `f6_fired` (`:1025`), the ordinal
   (`f6_event_ordinal`, `:1026`) and `max_faults` (`:1027`). With
   `--lsqfwd_event_ordinal 1 --max_faults 1` the first eligible store→load forward
   (observed event #1) is suppressed unconditionally at probability 0.
3. **Platform-level gap:** `run_pilot.py` has no FW02 branch in its per-model flag
   list — FW02 falls into the `else` arm which always mounts
   `--chaos_lsqfwd --lsq_struct_mode f6_fw02` (`platform/run_pilot.py:617-620`), so a
   run_pilot FW02 CONTROL is structurally guaranteed to misfire. The **LQ04 branch
   already solves this exact problem** (`run_pilot.py:612-616`): "Matched no-fault
   control: the LQ04 selector is ordinal-gated, not probability-gated, so a mounted
   injector would still fire. Omit the injector entirely; --chaos_propagation stays
   on." — FW02 (and DA04, whose `Da04BeBit0` is in the same attach list,
   `CHAOSLSQFwd.cc:82`) needs the same treatment.

This was **predicted before the run**: RUNBOOK_v3.2.12.md §7n documents this exact
mechanism and rules the exit-1 misfire "the platform's honest role-exclusive
rejection — do not 'fix' or relabel it; keep the record as evidence that FW02 is
ordinal-gated." `run_roles.py` (`control_valid`, `compute_acceptance`) correctly
refused the control (role-exclusive acceptance; a control that fired is an invalid
control, not a fault run). The misfire record stands as evidence and must NOT be
overwritten.

## 3. The ONE corrected control command (for the main agent to run)

A true no-fault FW02 control must **omit the injector mount entirely** — the
RUNBOOK §7n / A03-LQ04 precedent. Direct gem5 invocation into a NEW outdir (never
overwrite; `SUPP-FW02-C01` is preserved as the honest misfire record):

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12 && \
mkdir -p docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-FW02-CONTROL-REF && \
build/ARM/gem5.opt \
  --outdir=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-FW02-CONTROL-REF \
  configs/se/lsu_proxy.py \
  --cmd=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_forward \
  --cpu O3 --variant B0 --probability 0.0 \
  --chaos_propagation --prop_trace_file prop_trace.csv.gz
```

Properties of this command (all source-verified):

- **No injector is mounted** (`--chaos_lsqfwd` / `--lsq_struct_mode f6_fw02` are
  absent), so no suppression can occur by construction — `cpu->lsqFwd` is never
  set (`CHAOSLSQFwd.cc:126` never runs; no CHAOSLSQFwd SimObject exists).
- `--probability`, `--chaos_propagation`, `--prop_trace_file` are all common
  `lsu_proxy.py` flags (`configs/se/lsu_proxy.py:215,646,650`) — the command is
  valid without the injector mount. `--probability 0.0` is inert here (no injector
  consumes it) and is kept only to state intent; likewise the carried seed would be
  inert (no RNG consumer) — the run's determinism is exact anyway (the misfire's
  checksum equals the fault runs': `1f4cbf14327717df`).
- Same workload (frozen SHA `132a84f7f21be052…`), same CPU/variant as the FW02
  family, same trace machinery — the resulting `prop_trace.csv.gz` /
  `trace_v31.jsonl` give the no-fault memory-response/hash reference for the
  `sq_forward` stores, which is what the FW02 audit needs from a control.
- **Honesty caveat:** this is a *reference run*, not a run_pilot CONTROL-role record
  (it produces raw artifacts + trace, no `pilot_meta.json`/`manifest.json` CONTROL
  record) — the RUNBOOK §7n labels it exactly so. If a role-recorded FW02 control is
  wanted, the follow-up patch is the LQ04 precedent applied to FW02 in
  `run_pilot.py` (a `--model FW02` branch that sets `extra = []` when
  `args.probability == 0.0`, mirroring `run_pilot.py:612-616`), then re-run
  `run_pilot.py --model FW02 … --probability 0.0` into a NEW outdir such as
  `SUPP-FW02-C01-r2`. That patch is intentionally NOT part of this audit (read-only).

## 4. Contrast table (why the other controls worked)

| run | mode | attach at p=0? | selector probability gate | injection_count | control_valid |
|---|---|---|---|---|---|
| SUPP-FW02-C01 | `f6_fw02` | **yes** (`CHAOSLSQFwd.cc:81-87,134-137`) | **none** (`:1023-1028`) | 1 (misfire) | false |
| SUPP-SQ01-C01 | `sq01_bit3` | no (`:81` — Sq01Bit3 not in list; hook blocked at `lsq_unit.cc:2120`) | attach-level | 0 | true |
| SUPP-SQ03-C01 | `sq03_canwb` | no | `maybeSetCanWB`: `probability <= 0.0f → return false` (`:734-735`) | 0 | true |
| SUPP-SP05-C01 | `sp05_complete` | no | `maybeSelectSP05`: `probability <= 0.0f → … return false` (`:538`) | 0 | true |
| (reference) SUPP-A01-C01 | `a01_bit3_load` (CHAOSAddrPath) | no | — | 0 | true |
