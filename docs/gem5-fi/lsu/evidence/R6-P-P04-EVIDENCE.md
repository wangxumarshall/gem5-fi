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
