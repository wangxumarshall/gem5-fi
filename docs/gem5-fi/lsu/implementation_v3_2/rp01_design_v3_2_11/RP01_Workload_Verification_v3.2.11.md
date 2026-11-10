# RP01 Workload Verification — v3.2.11

**Workload:** `replay_dependency`  **Expected SHA256:** `ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4`
**Expected Oracle:** `59fc61c040618747`

## 1. Existence and identity

| Check | Result |
|---|---|
| `docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency` exists | **yes** (ELF) |
| SHA256 | **matches** `ca15390f…38f4` |
| Duplicate `final_paper_audit_v3_1/workload_sources/replay_dependency` | same SHA256 |
| `replay_dependency.golden` | `59fc61c040618747` |
| `replay_dependency.host.out` | `checksum=0x59fc61c040618747` |
| Golden reproducible on the host | **yes** (the golden file is the host run output) |

No re-generation and no substitution was performed. The workload is the original W7 file.

## 2. Source analysis (`replay_dependency.c`)

- `static volatile uint64_t a[1024]`, initialized to `a[i]=i`.
- 256 iterations: `idx=(r*37)&1023; q[idx]=r; asm volatile("" ::: "memory"); s+=p[idx];`
- The store and the load are the **same 8-byte address** (`q[idx]` / `p[idx]`, both `uint64_t *`), separated by a compiler memory barrier.
- The checksum is `s ^ fnv1a(a,4096)`; the loaded value directly feeds `s`, so a downstream consumer is observable through the application checksum.

**Important caveat:** at the C level the store and load are full-width (8-byte) same-address accesses, which normally produce **full** address-range coverage, not `PartialAddrRangeCoverage`. The five partial-forward replay events observed in the existing probe (below) therefore come from other dynamic access patterns in the compiled binary (compiler-generated sequences, overlapping adjacent iterations, or split accesses), not from the literal `q[idx]=r; s+=p[idx]` pair. Whether the compiled workload deterministically produces five distinct partial-forward events under each RP01 seed must be established by a **clean count-only preflight**. The source alone does not prove it.

## 3. Existing replay evidence (read-only, not a substitute for the count-only preflight)

`pilots_v3_2_2/REPLAY-RW02/replay_pilot_summary.json` (workload `replay_dependency`, seed 3135797961, FW02 fault-on, `--prop_replay_all`):

- `replay_count = 5`
- Reason for all five: `partial_forward_mismatch`
- Distinct `(seq, pc, tick, lq_entry, entry_generation)` tuples; 3 `COMMITTED`, 2 `SQUASHED`
- The summary explicitly notes: *“replays are real partial_forward_mismatch reschedules of replay_dependency; they are observed under a fault run and are not claimed to be caused by the injected bit flip.”*

This proves the workload **can** produce at least five real partial-forward replays, but it does **not** prove that the five frozen RP01 seeds/ordinals produce five distinct eligible events. The binary and seed differ from the RP01 plan.

## 4. Requirements still open

1. A clean no-fault count-only run (no injection) with the five frozen seeds and ordinal 1–5 must list the first five eligible partial-forward events per seed and prove five distinct dynamic contexts. This is a **future, approval-gated** step; it was not executed in this round.
2. If a seed yields fewer than five distinct events, report `WORKLOAD_INSUFFICIENT_FOR_FIVE_CONTEXTS` and propose a workload adjustment: add a deliberate partial overlap (e.g., two 4-byte stores covering one 8-byte load, or an 8-byte store and an 8-byte load offset by 4 bytes) in a **new** workload, preserve `replay_dependency` and its SHA/golden, record the new SHA256 and re-validate the golden oracle. Do not silently replace the original.

## 5. Verdict

- File and SHA: **verified**.
- Oracle: **verified** (`59fc61c040618747`).
- Partial-forward replay capability: **observed** (5 events in a prior probe), but not yet proven under the five RP01 seeds.
- Workload status for RP01: **VERIFIED_WITH_PREFLIGHT_REQUIRED**.
