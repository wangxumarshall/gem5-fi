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
→ pf_queue(invalid_skipped). There is no L3/L5 because a skipped prefetch has
no architectural data effect; the chain stops at L2 honestly and is not
admitted. This is a performance-only fault, not an SDC claim.

## Honesty boundary

- P04-a only; P04-b/c unimplemented; P04-F5 seeds not run.
- The pilot does not certify P04-F0-W2/W8: the L5 gate correctly refuses a
  chain with no detection/escape/containment.
- No model substitution: the P05 drop/dup mapping is gone from
  `MODEL_FLAGS["P04"]`.
