# Gate 2 — Workloads and Pilots

**Date:** 2026-11-06
**Branch:** `lsu-platform-v3.2`
**gem5:** v25.1.0.1, built from this worktree (`build/ARM/gem5.opt`
SHA256 `b233a4cbb1085887c1a8533a77a9fa0885dcb36aa34608f7a90245b7395eaabe`)

## W1-W8 no-fault baselines

All eight baselines were re-run with the Gate-2 binary after the W6/W8 source
repair and the three hooks were built. Every run exited 0 and passed its
frozen oracle.

| ID | Workload | Exit | Oracle | finalTick | Target-event proof |
|---|---|---:|---|---:|---|
| W1 | agu_addrmodes | 0 | PASS | 19544525 | AGU address formation: 6 `Read called` + `Doing memory access` |
| W2 | lq_lifetime | 0 | PASS | 37983715 | 6232 `Inserting load`, 756 squashed loads |
| W3 | sq_drain | 0 | PASS | 149995615 | 31092 `Writing back store` + 31092 `Completing store` |
| W4 | sq_forward | 0 | PASS | 19112940 | 6 `Forwarding from store`, 1 forwarding mis-match |
| W5 | load_response | 0 | PASS | 55153560 | 18269 `Read called` + `Doing memory access` |
| W6 | store_path | 0 | PASS | 92581720 | 10609 `Completing store` |
| W7 | replay_dependency | 0 | PASS | 40653690 | 267 `forwLoads`, 5 `rescheduledLoads`, 7 `memOrderViolation` |
| W8 | alignment | 0 | PASS | 34556445 | unaligned addresses `0x…0a..0x…0f` in `Read called` |

W6/W8 source repair evidence:

- Guard-page probe on the original offsets: `SIGSEGV` (exit 139) for both.
- Guard-page probe on the fixed offsets: `NO_FAULT` (exit 0) for both.
- Fixed binaries: `store_path` SHA256 `906b3798…fbcf`, `alignment`
  SHA256 `89ff937a…18c0`; new goldens
  `0x2543a2a60de01795` and `0x3f89eab79392ce69`.
- Originals preserved under `workloads/_original_v31/`.

## Pilots

Pilot IDs are independent `PILOT-...` IDs. The seeds are copied verbatim from
the frozen Excel rows; no formal sample ID or seed was changed.

### A01 / F0 — single transient AGU EA bit-3 flip

- Command: `--chaos_addrpath --agu_pre_mode a01_bit3_load
  --addrpath_lsu_tier F0 --addrpath_max_faults 1 --addrpath_rng_seed 2108120075`
- Site: `lsq_pushRequest_PRE` (the audited pushRequest entry, not
  `sendFragmentToTranslation`).
- Trigger: `attempted=2785 eligible=1466 injected=1`.
- Injected event: `old_addr=0x7ffffefdc0 → new_addr=0x7ffffefdc8`
  (`new == old ^ 0x8`), load only.
- Trace: 12 events, 10 PropagationEdges: injection → address_formed →
  memory_request → memory_response → register_writeback → errant_commit →
  five consumer commits.
- Oracle: PASS; terminal `MASKED`; trace COMPLETE.
- **Pilot accepted.**

### A03 / F5 — persistent bit-3 stuck-at-0

- Command: `--chaos_addrpath --agu_pre_mode a03_bit3_stuck0_load
  --addrpath_lsu_tier F5 --addrpath_max_faults 0 --addrpath_rng_seed 663646247`
- Trigger: `attempted=284 eligible=146 injected=146`; every eligible load
  received the condition. `nochange` applications are logged with
  `value_changed=0` and counted, not dropped.
- First changed event: `0x7ffffefdb8 → 0x7ffffefdb0` (`new == old & ~0x8`).
- The persistent condition eventually corrupts a stack access:
  `0xffffffffffb73c58 → 0xffffffffffb73c50`, producing a gem5
  `Page table fault` at commit. The pilot is therefore recorded as
  `RunStatus=SIMULATOR_ERROR`, `FaultActivationStatus=TRIGGERED`,
  `TerminalState=CRASH`.
- Trace: 563 captured CSV nodes → 564 JSONL events, 489 edges, 73 injection
  nodes, and 417 nodes carrying `activation_status=TRIGGERED` (a per-node
  status flag, not a count of distinct activations). gem5 aborted before the
  stats dump, so `stats.txt` is empty and no stats claim is made. The gzip trailer is absent because gem5
  aborted; every completed node was flushed, and a terminal
  `simulator_abort` event was appended. TraceCompleteness=COMPLETE to the
  observed crash terminal.
- **Pilot accepted as a real F5 trigger with a CRASH terminal; it is not a
  Masked/SDC sample and must not be counted as one.**

### FW02 / F6 — conditional forwarding false miss

- Command: `--chaos_lsqfwd --lsq_struct_mode f6_fw02 --max_faults 1
  --rng_seed 2941542370`
- Trigger: 6 real full-coverage store→load pairs observed; the first pair
  (`load_seq=397`, `store_seq=383`, `Vaddr=0x7ffffefc28`) suppressed exactly
  once.
- The target load then went to the memory path; the injected suppression is
  recorded at the full-coverage decision point.
- Trace: 4 events, 3 PropagationEdges: injection → address_formed →
  memory_response → register_writeback. The trigger pair (`load_seq=397`,
  `store_seq=383`) is recorded in `lsq_fwd_injections.log` and
  `pilot_meta.json`; the current propagation node does not carry the store
  seq field, so the pair is not reconstructible from the JSONL alone.
- Oracle: PASS; terminal `MASKED`; trace COMPLETE.
- **Pilot accepted.**

## Gate 2 verdict

The three injection modes are now backed by real source hooks and real
runs:

- F0: exactly one eligible load injected (A01).
- F5: every eligible load re-applied the condition (A03, 146 applications),
  with a real downstream crash.
- F6: one named store→load forwarding event triggered one suppression
  (FW02).

Trace identity was corrected after review: every injection now carries a
unique `injection_event_id`, and memory responses store their physical
address in `pa` (not `va`). See the regenerated `trace_v31.jsonl` files.

Gate 2 is accepted for the three pilots. Gate 3 (remaining nine models) and
Gate 4 (60 formal samples) have not started.
