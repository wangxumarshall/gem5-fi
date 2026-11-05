# R6-P-P04 — faithful P04-a queue-valid submodel (pilot, 2026-11-04)

**Status: IMPLEMENTED / PILOT ONLY / NOT CERTIFIED.** P04-a is the first
faithful P04 submodel; the old P04→P05 drop/dup routing is removed.

## Model (real state, not a drop/dup approximation)

`Queued::DeferredPacket` gains a shadow `chaosQueueValid` bit (default true).
`CHAOSPrefetch` mode `p04_queue_valid` clears the bit of the first live queue
entry **without removing it** (queue pointer/count unchanged). `Queued::
getPacket` skips and removes invalid entries at issue time, so the skipped
prefetch is a real queue-valid effect. The entry is emitted as:

- L0 `inj` (registerCacheFault, field=prefetch);
- L1 `pf_train` (field=queue, before=valid, after=invalid);
- L2 `pf_queue` (field=queue_valid, before=1, after=0, state=invalid);
- L2 `pf_queue` at issue (same field, state_after=invalid_skipped).

No P05 drop/dup is used. P04-b (pointer) and P04-c (entry selection) are NOT
implemented.

## Binary / span

- Binary: `runs/lsu/r6_p_unit/binaries/gem5.opt-d97276d9`
  (sha256 `d97276d90b1c3e9dcfdba840d0d980796b5654703b3cec207fb2f85c916f7333`,
  source `d9be2743`).
- Exact-absolute-command no-fault census (`span=1e9`, seed 1):
  `beebs_kernels` attempted=143 eligible=2; `prefetch_stride` attempted=131
  eligible=2. Frozen span = 2, warmup=1 (draw in {1,2} always lands).
- No-fault goldens with the mode mounted but no fire: W2 `a10b9827edd8a9fb`,
  W8 `629727c0ad9ca8ef` (registry match).

## Seed1 pilot (real output, `campaign_p04_20261104`)

| RunID | injection | terminal | admitted | oracle |
|---|---|---|---|---|
| P04-F0-W2 | `P04_queue_valid Tick: 148525300 pf_addr=0x77980 queue entry valid -> invalid (index 0)` | `provable_to_L2_then_unknown` | False | Masked |
| P04-F0-W8 | `P04_queue_valid Tick: 107286025 pf_addr=0x76980 queue entry valid -> invalid (index 0)` | `provable_to_L2_then_unknown` | False | Masked |

All events are real: inj → pf_train(valid→invalid) → pf_queue(queue_valid 1→0)
→ pf_queue(invalid_skipped). The chain is `provable_to_L2_then_unknown`: no
L3/L5 evidence was observed in this pilot. That is **not** a claim that the
fault can never have an architectural effect — a later demand could still
miss because the prefetch was skipped; the pilot simply did not observe it.
No L5 is fabricated; a dedicated "performance / no-arch-consumption"
evidence class would be a separate, explicitly versioned classification and
is not introduced here (general admission and COMPLETE counts are
unchanged).

## Honesty boundary

- P04-a and P04-c are implemented as pilots; P04-b (pointer) is unimplemented;
  P04-F5 seeds have not been run.
- The pilot does not certify P04-F0-W2/W8: the L5 gate correctly refuses a
  chain with no detection/escape/containment.
- No model substitution: the P05 drop/dup mapping is gone from
  `MODEL_FLAGS["P04"]`.

---

## P04-c entry-selection pilot (2026-11-04)

**Status: IMPLEMENTED / PILOT ONLY / NOT CERTIFIED.** P04-b (pointer) is
still not implemented.

- Model: `Queued::chaosSelectWrongEntry` swaps the **second live entry** into
  the head position; the correct head stays queued (moved behind it) and the
  wrong entry is issued next. Requires ≥2 live entries. This is a selection
  error, not a drop/dup.
- Binary: `runs/lsu/r6_p_unit/binaries/gem5.opt-0cb5073d`
  (sha256 `0cb5073d8d7faec2425ef9f1ffc4fe03a18c70cc6f5416c894b0bda58d477396`,
  source `53561cba`).
- No-fire goldens with the mode mounted: W2 `a10b9827edd8a9fb`,
  W8 `629727c0ad9ca8ef` (registry match).
- Census (exact absolute command, span=1e9): P04c W2 eligible=2, W8
  eligible=2 (`>=2 live entries` samples).
- Seed1 (span=2): both W2/W8 inject `P04_queue_select`; events are real:
  `inj` → `pf_train` (`field=queue_select`, `before=0`, `after=1`) →
  `pf_queue` (`field=queue_select`, `before=head`, `after=wrong`,
  `state_after=wrong_selected`). Checker terminal
  `provable_to_L2_then_unknown` (path `0 -> 1 -> 2`); gzip EOF, stats
  1768/1765 lines, exit 0.
- Boundary: no L3/L5 evidence was observed in this pilot. That is not a
  claim that the fault can never affect a later demand (the correct head was
  delayed, not dropped). Not certified; no fabricated L5; general admission
  and COMPLETE counts are unchanged.

---

## P04-c behavioral verification — real issue reversal (2026-11-04 takeover)

**Status: IMPLEMENTED / BEHAVIOR-VERIFIED PILOT / NOT CERTIFIED.** This
section answers the fidelity question with runtime behavior, not source
string matching.

### What the authoritative model requires

Sheet 03 P04: queue entry/valid/head-tail pointers; P04-c = "选择另一个
合法队列项" (select another legal queue entry); activation only when the
queue is non-empty and the fault value is actually read/selected/consumed
downstream. The model must not be a P05 drop/dup.

### What the implementation does

`Queued::chaosSelectWrongEntry` scans the live queue (valid shadow bits),
takes the first live entry (the correct head) and the second live entry,
and swaps only their list positions (`std::iter_swap`). No entry is erased,
no field (address/PC/priority/valid) is changed, and the queue length is
unchanged. `getPacket` issues `pfq.front()` as usual, so the second entry
is issued first and the correct head is issued later.

Trigger position: `CHAOSPrefetch::maybeCorrupt` is called at the tail of
`Stride::calculatePrefetch`, i.e. on the already-queued entries of earlier
accesses, before this access's new candidates are inserted. Eligibility is
`chaosHasTwoLiveEntries()` (>= 2 live entries).

### Normal-scheduling comparison (control)

`addToQueue` keeps the queue priority-ordered; `alreadyInQueue` can move an
entry forward only when that same entry's priority is updated. Neither
changes the identity of the entry at the head. The fault instead swaps two
distinct live entries with unchanged priorities. A no-fault control with
the same binary/mode/seed (`span=1e9`, no fire) shows the normal order:

```
148525301: ... Generating prefetch for 0x77980.
148525302: ... Generating prefetch for 0x77b40.
```
W8 control: `0x76980` then `0x76b40`.

### Fault run (real behavior log, new evidence)

Binary `runs/lsu/r6_p_unit/binaries/gem5.opt-a0d0e8af`, sha256
`a0d0e8af9d2242dd6250c24f48bdecf396e4bcc6c220dbbc6e331b65f49cd687`,
source head `5d6399d8` + this patch. Evidence:
`runs/lsu/r6_p_unit/campaign_p04c_behavior_20261104/`.

W2 (`P04C-F0-W2`, seed1, span=2):

```
Tick: 148525300 event=select head=0x77980 second=0x77b40 fault_id=1 pf_request_id=4294967297
Tick: 148525301 event=issue role=wrong_selected va=0x77b40 fault_id=1 pf_request_id=4294967297
Tick: 148525302 event=issue role=head_issued_late va=0x77980 fault_id=1 pf_request_id=4294967297
```

W8 (`P04C-F0-W8`, seed1, span=2):

```
Tick: 107286025 event=select head=0x76980 second=0x76b40 fault_id=1 pf_request_id=4294967297
Tick: 107286026 event=issue role=wrong_selected va=0x76b40 fault_id=1 pf_request_id=4294967297
Tick: 107286027 event=issue role=head_issued_late va=0x76980 fault_id=1 pf_request_id=4294967297
```

This is a decisive behavioral result:
- the correct head (`0x77980`/`0x76980`) is **retained** in the queue;
- the second legal entry (`0x77b40`/`0x76b40`) is **issued first** (wrong
  selection), then the correct head is issued late;
- both entries are issued exactly once (queue conservation, no drop/dup);
- the issue order is exactly reversed relative to the no-fault control.

The propagation stream now carries the two identities
(`field=queue_select before=<head> after=<second>`,
`state_after=wrong_selected`) and the existing `pf_issue` node records the
real wrong-entry issue. Tests in `tests/test_lsu_hook_p04.py` parse the
behavior log and assert the order, not source strings.

### RunID mapping (no new official RunIDs)

`P04C-F0-W2` / `P04C-F0-W8` are **submodel pilot labels only**. They map to
the authoritative RunIDs `P04-F0-W2` / `P04-F0-W8` and are not counted as
new RunIDs or seeds. The authoritative P04 RunIDs remain not certified
(terminal `provable_to_L2_then_unknown`; no L3/L5 observed, no
architectural-impact claim).

### Honest boundary

No L3/L5 event was observed. The correct head was delayed, not dropped, so
the pilot cannot and does not claim "no architectural effect"; it only
proves that the P04-c mechanism is a real entry-selection error. P04-b is
implemented in the next section; P04-F5 has not been run.

---

## P04-b tail-pointer -1 — implementation and behavior (2026-11-04)

**Status: IMPLEMENTED / BEHAVIOR-VERIFIED PILOT / NOT CERTIFIED.**

### Model

Sheet 03 P04-b is a queue pointer error (±1). The implementation arms a
one-shot `chaosTailPointerBack` on the prefetch queue; the next
`addToQueue(pfq, ...)` inserts the new prefetch **before the current tail**
instead of at the back/priority position. No entry is erased, no entry is
duplicated, and no address/PC/priority field is changed: the inserted entry
and the former tail are both retained and both issued, only the order
changes. Eligibility requires a queue with at least two entries (a tail
distinct from the head) and a pending generated prefetch.

This is not the P05 drop/dup approximation: the new entry is added exactly
once and no existing entry is removed; the fault is a pointer position
error (`tail-1`).

### Binary / census / evidence

- Binary `runs/lsu/r6_p_unit/binaries/gem5.opt-f52461b5`, sha256
  `f52461b56a7758c366d54d2c4a4f5915e528025c7e3931f82378931a128dc4a9`,
  source head `a4c0d088` + this patch. Build log
  `r6o-logs/p04b_build2.log` (zero introduced warnings).
- Exact absolute-command no-fault census (`span=1e9`, seed 1):
  `census_p04b_20261104/` — W2 `attempted=143 eligible=1`, W8
  `attempted=131 eligible=1`. Frozen `warmup=1, span=1` (draw always lands).
- Fault pilots: `runs/lsu/r6_p_unit/campaign_p04b_20261104/`.

### Real behavior (seed1)

W2 (`P04B-F0-W2`):

```
Tick: 148525300 event=arm tail=0x77ec0 insert=0x77580 size=4 fault_id=1 pf_request_id=4294967297
Tick: 148525686 event=issue role=pointer_inserted va=0x77580 fault_id=1 pf_request_id=4294967297
Tick: 148525687 event=issue role=pointer_tail_shifted va=0x77ec0 fault_id=1 pf_request_id=4294967297
```

W8 (`P04B-F0-W8`):

```
Tick: 107286025 event=arm tail=0x76ec0 insert=0x76580 size=4 fault_id=1 pf_request_id=4294967297
Tick: 107286410 event=issue role=pointer_inserted va=0x76580 fault_id=1 pf_request_id=4294967297
Tick: 107286411 event=issue role=pointer_tail_shifted va=0x76ec0 fault_id=1 pf_request_id=4294967297
```

No-fault controls (`control_W2_nofault`, `control_W8_nofault`, HWPrefetch
debug) show the normal order tail-first:

```
W2: 148525686 Generating prefetch for 0x77ec0; 148525687 ... 0x77580
W8: 107286029 Generating prefetch for 0x76ec0; 107286410 ... 0x76580
```

The fault reverses the relative order of the inserted entry and the former
tail; both issue exactly once. Propagation events:
`field=queue_pointer`, `before=<tail index>`, `after=<tail-1 index>`,
`state_after=tail_minus_one`.

### RunID mapping and boundary

`P04B-F0-W2` / `P04B-F0-W8` are submodel pilot labels mapping to the
authoritative `P04-F0-W2` / `P04-F0-W8`; they are not new official RunIDs
or seeds. Terminal `provable_to_L2_then_unknown`, not admitted, no L3/L5
observed; no architectural-impact claim. Seeds 2/3 were not run (pilot
only). At the time of this pilot P04-F5 permanent semantics had not been
established; see the fixed-slot v2 section below.

---

## P04-F5 permanent queue-valid fault — v1 whole-queue field (2026-11-05, SUPERSEDED)

> **SUPERSEDED (2026-11-05): the whole-queue valid-field latch below
> changes N state bits (every live entry plus every later insertion) and is
> a semantic expansion of the scheme's "每次运行仅选一个 bit/字段". The
> fixed-slot v2 model in the next section is the authoritative P04-F5
> evidence. This section is retained unchanged as historical evidence.**

**Status: IMPLEMENTED / BEHAVIOR-VERIFIED / 3 SEEDS / NOT CERTIFIED.**
F5 is the authoritative permanent tier. The single landed arm is **P04-a
(queue valid stuck)**; P04-b/c are not part of this F5 pass. The result is
a real performance-only fault: the checker refuses admission and the
oracle is Masked on every seed. No L5 is fabricated.

### Authoritative semantics and the faithful mapping

Sheet 03 P04: the queue entry, valid, and head/tail pointer; F5 = "warm-up
后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段"
(permanent; run-level sample).

- **Location**: the prefetch request queue's valid field.
- **Period**: from the first eligible event after warm-up to the end of
  the run.
- **Recovery**: none (permanent until run end).
- **Physical fault identity**: ONE latched `fault_id` per run.
- **Trigger opportunities / effective changes / propagation instances**:
  the latch is the single effective write (injected=1). Every later
  ready-queue entry born invalid, and every invalid entry skipped at
  issue, is a propagation instance of that same physical fault — they
  share the fault_id and carry their own request-level `pf_request_id`.

gem5's prefetch queue is a `std::list` without fixed slots. A stuck valid
bit on one *dynamic entry* would end when that entry is consumed, i.e. it
would be a transient fault. The faithful permanent mapping is therefore
the per-queue valid **field**: every entry present at latching and every
later insertion into the ready queue reads invalid, while the entry's
address/PC/priority/request identity are untouched. This is the scheme's
"one field" granularity and is the minimal implementation that stays
permanent. It is documented here rather than silently approximated.

### Implementation

- `Queued::chaosLatchQueueValidStuck(fault_id, pfid)` sets the run-long
  stuck state and invalidates every live ready-queue entry (no entry is
  removed; the issue path skips it).
- `Queued::addToQueue` calls `chaosApplyStuckValid()` for every new ready
  entry (both the normal and the tail-pointer insertion paths); it clears
  the shadow valid bit and records the birth (`state_after=
  invalid_stuck_birth`) under the same latched fault id.
- `CHAOSPrefetch` (mode `p04_queue_valid`, tier F5) latches once at the
  first eligible event: `noteOutcome(true)`, `injected=1`; every later
  eligible call would re-write the same value and is reported
  `noteOutcome(false)` (in this workload the sticky state removes all
  live entries, so no later fire occurs — `fires=1`).
- `Queued::getPacket` keeps the real skip (`invalid_skipped`) and records
  it as an L2 propagation instance.
- F5 campaign flags are unchanged (`--prefetch_max_faults 0`,
  warm-up 0); the latch is the single physical fault.

### Binary / census / controls

- Binary: `CHAOS/gem5/build/ARM/gem5.opt`, sha256
  `cb98fbb5f2d82ed70d26f651a6d12a97f7af740aa176e54869c4f1e3c8b4231b`,
  source head `f502fd19` + this patch. Build log `/tmp/p04f5_build2.log`
  (exit 0, zero warnings). Intermediate binary
  `d241f5b9…` (same semantics, pre-audit-label fix) is **not evidence**.
- No-fault controls (same binary/mode/workload, warm-up `1e9` so the F5
  trigger never arms): W2 output `a10b9827edd8a9fb`, W8
  `629727c0ad9ca8ef` — registry goldens — `fires=0 injected=0`, and the
  behavior log is empty (no latch).
- Epoch: `campaign_p04f5_20261105` (seed1), `campaign_p04f5_seed23_20261105`
  (seeds 2/3). Exact campaign matrix/command preserved by the runner.

### 3-seed diagnostic results (all real output)

| RunID | seed | latch tick / entries | terminal | admitted | oracle | output |
|---|---|---|---|---|---|---|
| P04-F5-W2 | 1/2/3 | 148525300, 4 live, 3 latch-invalidated | `provable_to_L2_then_unknown` | False | Masked | `a10b9827edd8a9fb` (golden) |
| P04-F5-W8 | 1/2/3 | 107286025, 4 live, 3 latch-invalidated | `provable_to_L2_then_unknown` | False | Masked | `629727c0ad9ca8ef` (golden) |

Every run: `attempted=143/131 eligible=1 injected=1 fires=1
no_effect=0` (W2/W8), `fires == injected + no_effect`, gzip intact,
stats 1767/1765 lines, exit 0, no truncation. Propagation stream (35
lines incl. header/chain_end): `pf_train` 1 (`state_after=
stuck_until_end`), latch `pf_queue` 4 (`invalid_stuck`), birth 12
(`invalid_stuck_birth`), issue skip 16 (`invalid_skipped`) — **33
propagation instances of the one physical `fault_id=1`**, each with its
own request-level `pf_request_id` (16 distinct request ids). Real
behavior log:

```
Tick: 148525300 event=latch field=queue_valid before=valid after=invalid state=stuck_until_end entries=4 latch_invalidated=3 va=0x77980 pc=0x416174 fault_id=1 pf_request_id=4294967297
Tick: 107286025 event=latch field=queue_valid before=valid after=invalid state=stuck_until_end entries=4 latch_invalidated=3 va=0x76980 pc=0x415fb4 fault_id=1 pf_request_id=4294967297
```

### Seeds are determinism replications, not independent draws

All three seeds latch at the same tick/address. This is by construction:
the authoritative F5 activation is "the first eligible event after
warm-up" (warm-up 0 here), and the directed workloads are deterministic.
The P04-F5 seeds are therefore determinism replications of one activation
point, exactly like directed controls; they do not add independent
fault-location samples. This is recorded rather than presented as 3
independent samples.

### Honesty boundary

- The P04-F5 RunIDs are **NOT certified**: the chain is provably L2 (the
  queue-valid change) and stops there — each skipped prefetch never
  issues, so there is no fill/eviction event to follow, and the later
  demand misses are not causally joined to the skipped request (the
  workloads show no post-latch demand on those four lines in the stream).
  The workloads' outputs stay golden on all seeds (performance-only).
- No L3/L5 was observed and none is fabricated; no containment is
  auto-added.
- P04-b/P04-c have no F5 implementation this pass; the F5 landed arm is
  P04-a only. The unit remains PARTIAL_SUBMODEL.

---

## P04-F5 fixed-slot v2 — authoritative permanent semantics (2026-11-05)

**Status: IMPLEMENTED / BEHAVIOR-VERIFIED / 3 SEEDS / NOT CERTIFIED.**
This section supersedes the whole-queue valid-field latch above. The
RunID-level result is unchanged (chain L2, oracle Masked, no certification),
but the fault now changes exactly one physical valid bit.

### Semantic correction

The scheme's F5 is "warm-up 后第一个 eligible event 起持续到运行结束；每次
运行仅选一个 bit/字段". The v1 implementation invalidated every live entry
and every later insertion — N state bits, not one. It was a semantic
expansion, not the only faithful mapping.

gem5's ready queue is a `std::list` without fixed slots. The v2 mapping is a
**logical fixed slot**: every enqueue advances a write pointer and the entry
gets `chaosSlot = enqueue_ordinal mod queueSize`, the analogue of a circular
FIFO slot. At the F5 latch the first live entry's slot is selected; exactly
that slot's valid bit reads 0 for the rest of the run. Later entries
allocated to the same slot are born invalid; every other slot is untouched
and issues normally. One physical fault id, no recovery path.

This is a documented structural abstraction of a list-based queue, not a
claim that gem5 has a physical circular array. The old whole-queue evidence
is retained, not rewritten.

### Implementation

- `DeferredPacket::chaosSlot` is assigned in `Queued::addToQueue` for every
  ready-queue enqueue (`chaosEnqueueSeq++ % queueSize`).
- `Queued::chaosLatchQueueValidStuck(fault_id, pfid, invalidated)` picks the
  first live entry's slot, invalidates only entries in that slot, returns
  the invalidated count and fills `invalidated` for lineage.
- `Queued::chaosApplyStuckValid` gates on the same slot
  (`dpp.chaosSlot != chaosStuckSlotIdx`).
- The F5 path in `CHAOSPrefetch` uses `chaosPeekLiveQueueEntry` (read-only)
  instead of the F0 pre-clear; a pre-clear would have invalidated one entry
  and then latched a different slot, changing two bits.

### Binary / build

- Binary `runs/lsu/r6_p_unit/binaries/gem5.opt-b2bf0cd3`, sha256
  `b2bf0cd37fe77d045a20424c6ba9a7a394f97cb7f10bf8927061bea53000a3a5`.
- Source: commit `a00ab5c7` (fixed-slot patch). Build log
  `/tmp/p04f5v2_build3.log`; exit 0, no new warnings (only the pre-existing
  host capstone/png/HDF5 environment warnings).
- Intermediates `00ccfd81…` (pre-peek, two-bit pre-clear bug) and the v1
  `cb98fbb5…` binary are **not evidence**; SHAs retained here.

### Results (campaign `campaign_p04f5_v2_20261105`)

| RunID | seed | latch tick / slot | entries / latch_invalidated | terminal | admitted | oracle | output |
|---|---|---|---|---|---|---|---|
| P04-F5-W2 | 1/2/3 | 148525300 / 11 | 1 / 1 | `provable_to_L2_then_unknown` | False | Masked | `a10b9827edd8a9fb` (golden) |
| P04-F5-W8 | 1/2/3 | 107286025 / 28 | 1 / 1 | `provable_to_L2_then_unknown` | False | Masked | `629727c0ad9ca8ef` (golden) |

Every run: `injected=1`, `fires=2`, `no_effect=1`,
`fires == injected + no_effect`; gzip intact, stats non-zero, exit 0, no
truncation. Real behavior lines:

```
Tick: 148525300 event=latch field=queue_valid before=valid after=invalid state=stuck_until_end slot=11 entries=1 latch_invalidated=1 va=0x77980 pc=0x416174 fault_id=1 pf_request_id=4294967297
Tick: 107286025 event=latch field=queue_valid before=valid after=invalid state=stuck_until_end slot=28 entries=1 latch_invalidated=1 va=0x76980 pc=0x415fb4 fault_id=1 pf_request_id=4294967297
```

Propagation stream: `pf_train` 1 (`state_after=stuck_until_end`), latch
`pf_queue` 1 (`invalid_stuck`, `entry_index` = selected slot), issue skip 1
(`invalid_skipped`). **No same-slot birth occurred after the latch in these
short runs** (`invalid_stuck_birth=0`); the permanent slot gate remains
active to run end, but no birth instance is observed here. The other live
queue entries (e.g. 0x77b40 in W2) are untouched and issue normally — this
is the correction the v1 evidence could not show.

### Controls

Same binary/mode/workload with warm-up `1e9` (`campaign_p04f5_v2_controls_20261105`):
W2 `injected=0`, output `a10b9827edd8a9fb`; W8 `injected=0`, output
`629727c0ad9ca8ef`; behavior log empty (no latch).

### Seeds and honesty boundary

- Seeds 1/2/3 are determinism replications: F5 has no span draw and the
  directed workloads are deterministic; all seeds latch at the same
  tick/address. They are not independent fault-location samples.
- NOT certified: the chain is provably L2 and stops there; skipped
  prefetches never issue, so no fill/eviction follows. The output stays
  golden on all seeds. No L3/L5 is fabricated.
- The old v1 evidence (`campaign_p04f5_20261105`,
  `campaign_p04f5_seed23_20261105`) remains on disk as superseded history.
