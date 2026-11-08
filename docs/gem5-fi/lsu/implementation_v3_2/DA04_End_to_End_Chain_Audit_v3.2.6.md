# DA04 end-to-end propagation audit (v3.2.6)

**Binary:** `0de2564468fd710bf1df22d2336acac0ea92f7bc1ef5780178f18f497a302d7d`
**Pilots:** `pilots_v3_2_6/DA04-R04`, `DA04-R05` (v3.2.4/v3.2.5 not overwritten)

## Original-data check (requested)

The v3.2.4 CSV contained no load-side `mem_req` events (the tracer had no
such hook). The v3.2.5 hook was therefore necessary, not a converter-only
fix. v3.2.6 reruns the two pilots with the final hook.

## R04 chain (real values)

| Stage | Evidence |
|---|---|
| Store byte-enable injection | seq 13832, addr `0x4919d5`, size 4, `0xF→0xE`, data `c114af81` (fnv `ef9edb828f3fc2c`), SQ 1478/gen 1877 |
| SQ processing | `store_writeback` (be=0xE) then `store_mem_write` at tick 17,042,410; block `0x769c0`+21, `lane0 before/after = 0xA5/0xA5`, `enabled_written=1`, `disabled_unchanged=1` |
| Load memory request | seq 19210, request_id 35, fragment 3665, LQ 758/gen 1243; first send 2,286,900; **last send 17,889,025**; `candidate=1` (last send > store write) |
| Load response | tick 17,889,795, request_id 35, `data_hex=a514af81`, `data_fnv=d9a56276a6025898` |
| Register writeback | actual PRF `writeback_value=81af14a5` (little-endian 4-byte), `writeback_value_fnv=a959f41d27dbce18`, `payload_fnv=d9a56276a6025898`, `hash_basis=regval_extension` |
| Consumer | 1,009 matched operand records, 1,009 unique instructions; first consumer input hash `a959f41d27dbce18`; **0 hash mismatches** |
| Commit | load seq 19210 commits; errant commit at 17,890,565 |
| Oracle | FAIL `3f89eab79392ce4d` vs golden `3f89eab79392ce69` → SDC |
| Trace | validator VALID, coverage COMPLETE, chain PASS |

## R05 chain (real values)

| Stage | Evidence |
|---|---|
| Injection | seq 14582, addr `0x491c2d`, size 4, `0xF→0xE`, data `77623036`, SQ 1628/gen 2027 |
| Cache write | tick 17,157,910, block `0x76c00`+45, lane0 `0xA5→0xA5`, disabled lane unchanged |
| Load request | seq 19960, request 91, fragment 3824, first send 13,118,105, **last send 18,004,525**, candidate=1 |
| Response | tick 18,005,295, `data_hex=a5623036`, `data_fnv=7cc505782442859c` |
| Writeback | actual PRF `363062a5`, hash `bdb2b3575183d5c`, payload hash `7cc505782442859c` |
| Consumer | 7,714 matched operand records, 7,713 unique instructions; 0 mismatches |
| Oracle | FAIL `b948f769e7d691f5` → SDC |
| Trace | validator VALID, coverage COMPLETE, chain PASS |

## Request/response association and ordering

- `memory_response.request_id` equals the load `mem_req.request_id`
  (35 / 91); dyn seq matches (19210 / 19960).
- `mem_req.last_send_tick` is after `store_mem_write` tick; `candidate=1`.
- Ordering: store_mem_write < load mem_req < response < writeback < consumer < commit.
- The completeness checker enforces these (`response_without_request`,
  `response_request_not_causal`, `response_dyn_seq_mismatch`,
  `request_before_store_write`, `load_request_before_store_write_event`).

## PropagationEdge hashes

- R04: 1,018 edges (1,009 `register_dataflow`, 9 `ptag_sequence`); 0 missing
  `edge_type`; all register edges have both hashes.
- R05: 7,724 edges (7,714 register_dataflow); 0 missing `edge_type`.
- Validator: source hash = source event output hash; destination hash =
  consumer output hash; consumer input = propagated source. `VALID`.

## Verdict

The DA04 chain is machine-verifiable end-to-end for R04/R05:
`byte-enable injection → SQ → cache block update → load memory request →
response → actual PRF writeback → 1,009/7,714 consumers → commit → oracle`.
The 4-byte payload/register hash mismatch that appeared in the intermediate
v3.2.6 build was a trace bug (payload hashed as register value), not a
propagation failure; it is fixed by the post-`completeAcc` writeback read.
