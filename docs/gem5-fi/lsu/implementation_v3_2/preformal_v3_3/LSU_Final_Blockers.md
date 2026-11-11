# LSU 12-Model Pre-Formal — Final Blockers (v3.3.0, 2026-11-11)

Verdict: **NOT_READY** for a formal campaign. `12_MODEL_FORMAL_READY=NO`.
Scope is the researcher's 2026-11-11 decision: 12 models × R01–R05 = 60
contexts. The 74-model baseline is out of scope and is not a blocker here.

Each item below was reproduced from files/commands in this worktree; nothing
is copied from the v3.2.12 reports without re-checking.

## B1. Warm-up / ROI and EventOrdinal are not frozen (approval blocker)

The authoritative workbook (sheet `5.60个样本执行矩阵`) carries
`WarmUp = ROI = NEEDS_RESEARCHER_CONFIRMATION` and `EventOrdinal = 1..5` for
all 60 rows. The project's own recommendation
(`LSU_Warmup_ROI_Recommendation_v3.2.2.md`) explicitly rejects `WarmUp=0`
("A WarmUp=0 formal sample would inject into libc or the initializer") and
recommends placing R01–R05 at 10/30/50/70/90 % inside the ROI, converted to
event counts by a phase-instrumented run.

Observed on the final binary: with `WarmUp=0`, A01's ordinal-2 load is
`seq=48 PC=0x400ad0`, FW02's ordinal-1 forwarding pair is the stack pair
`vaddr=0x7ffffefbd0`, SP05/LP01/RP01/MD04 ordinals likewise land in startup
code. This is not the designed workload loop, so Gate A cannot pass.
**Required:** researcher approval of the warm-up boundary and the converted
`EventOrdinal` values (or explicit acceptance of startup events). Seeds and
SampleRunIDs stay unchanged.

## B2. Matched controls missing for 42 of 60 contexts

Only 18/60 formal contexts have a matched control with the same binary, seed,
workload and dynamic context; 42 are `MISSING` (all of DA04, FW05, LP01,
MD04, plus most FW02/A03 rows). The one historical misfire,
`SUPP-FW02-C01` (`--probability 0.0` still fired), is now fixed in code
(commit 364a6057) and re-verified (`V33F-FW02-C01`: control_valid=true,
misfire=false), but the formal rows still need their own controls.

## B3. 45/60 contexts have no evidence on the final binary

Evidence is keyed by binary SHA: A01/A03/RP01 on `68c6ce73` (v3.2.12 final),
FW02/SQ01/SQ03/SP05 on `720eb780`, FW05/LP01/MD04/DA04 on `e527f26a` /
`0de25644` / `3e9148fc`, LQ04 on `f3c2a442`. The two binaries `720eb780`
and `e527f26a` are no longer on disk, so those runs cannot be re-inspected
or reproduced in place. Only 5 fault contexts and 2 controls were re-run on
the v3.3 binary (`d3807fbe…`). A formal campaign must not mix these chains.

## B4. W4 (FW02) frozen ELF cannot execute the designed event

`workloads/directed/sq_forward` (sha `132a84f7…`) has 15 stores and **one**
load in `main`: GCC -O2 folded every store-then-load pair of the
non-volatile array. The FW02 decision therefore fires on libc/stack pairs,
not the designed forwarding pair. A load-preserving implementation is
committed as a proposal (`workloads/directed/sq_forward_v33*`, commit
c1846ae4; 10 loads/12 stores in main) and was piloted successfully, but
replacing the frozen ELF changes the workbook SHA and needs approval.

## B5. SQ01/SQ03/SP05 formal workload rows are stale

The authoritative rows name `sq_drain` / `store_path`, while the v3.2.12
closure evidence was produced on `sq_reload_v3212` (sha `bcab9cc5…`), which
`CLOSURE_INPUTS_v3.2.12.md` itself states is not one of W1–W8. The 15
contexts cannot be formal-ready until the workload row and the evidence
agree.

## B6. FW05 store→reload edge is not proven; the register consumer chain is

On the v3.3 binary the native chain is present and hash-linked:
`inj_fw05` (alt-store data `a06ea71b…`) → `taint_reg` (`a06ea71b…`) →
`consumer` seq 12094 (`a06ea71b…`, commit 5798). A later covering load
(seq 50512) is now recorded as `fw05_reload`, but it reads **neither** the
true-store nor the alt-store hash (`reads_true_store=0`, `reads_alt_store=0`),
so it is not evidence that the corrupted store lane was reloaded. The
v3.2.11 frozen import remains the only "complete" FW05 verdict; it must not
be presented as a v3.3-native store→reload chain.

## B7. A01 R01 crash and RP01 R02/R03 squash causation remain open

- A01 R01 (and R03) still have no causal crash attribution: panic VA `0`
  matches nothing on-chain. A01 closes on R02/R04/R05 wrong-EA MASKED only.
- RP01 R02/R03 now carry the real `triggering_seq` (87/110/237…), but the
  recorder classifies `fault_tracked=0; squash_cause=unrelated`; the squash
  is not proven to be fault-caused. They stay PARTIAL.
- A03 now has a native crash link (`a03_fault`, fault VA == `a03_stream`
  actual EA, matches=1), but the fatal cut still leaves `RecordIntegrity=
  TRUNCATED`; this is honest and accepted by the frozen E6 conjunction.

## B8. Configuration is not frozen

`ConfigFrozen = NO` on all 60 rows. The workbook's `gem5Commit=6f98088a` is
a stale ATLAS commit, and several `WorkloadPath`/`BinaryPath` entries point
at other worktrees. `run_pilot.py` has no `--dry-run`. The resource gate is
fine (`lsu_guard.py gate`: ok=true, disk 65.9 GiB free > 20 GiB, MemAvailable
25.7 GiB, 0 gem5 processes), but the configuration decision cannot be
frozen until B1–B5 are closed.

## B9. Record residuals carried honestly

FW05 R01, FW02 R01/R05, DA04 R01, MD04 R01/R04, RP01 R02/R03 remain PARTIAL
(squash before consumer, or unproven squash causation). A01 R03 stays
PARTIAL via the discard companion. Two records are UNRESOLVED. These are
record-level residuals, not model gaps, and are never upgraded by hand.

## What is NOT a blocker

- Disk: 65.9 GiB free (20 GiB gate).
- Host: 126 cores, 25.7 GiB available, no concurrent gem5.
- Test suites: `tests/` 180 passed, platform tests 107 passed.
- 74-model/4075-sample baseline: explicitly out of scope this round.
