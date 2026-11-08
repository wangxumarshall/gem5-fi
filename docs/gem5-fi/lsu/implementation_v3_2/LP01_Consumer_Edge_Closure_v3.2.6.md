# LP01 consumer-edge closure (v3.2.6)

## What changed

`CHAOSPropagation::noteCommit` now:
- emits `consumer` + `register_dataflow` **only when**
  `consumer_input_fnv == taint.value_hash` (non-empty);
- emits `taint_value_mismatch` for a stale/unhashable source and does **not**
  re-taint its destination, does **not** write an edge, and does **not** set
  `any_consumer`;
- re-taints only from matched consumers, using the consumer's output hash.

`noteMemResponse` no longer hashes the packet payload as the writeback value.
It stores the response hit; `noteChainWriteback`, called after
`LSQUnit::writeback` (i.e. after `completeAcc`), reads the **actual PRF
value** and emits the `register_writeback` node. This fixes the 4-byte DA04
false mismatch (payload `a514af81` vs register `0x81af14a5`) while preserving
the payload→response hash in `source_value_hash`.

## Before/after (five LP01 pilots, same identities/ordinals)

| Pilot | old consumer records | old matches | old mismatches | new consumer records | new instructions | new mismatches |
|---|---:|---:|---:|---:|---:|---:|
| R01 | 183 | 129 | 54 | 110 | 96 | 45 |
| R02 | 1 | 1 | 0 | 1 | 1 | 0 |
| R03 | 6 | 3 | 3 | 3 | 3 | 3 |
| R04 | 1 | 1 | 0 | 1 | 1 | 0 |
| R05 | 6 | 3 | 3 | 3 | 3 | 3 |

The new "consumer records" are matched operands; `consumer_instructions`
is the unique dynamic-instruction count (a multi-source instruction can have
several operand records). R01's 183 → 155 total operands is explained by the
no-re-taint rule: a mismatched source no longer propagates the old taint to
the destination, so downstream consumers of that stale line disappear. All
five new traces are validator VALID, coverage COMPLETE, chain PASS.

## Validator / completeness

- `register_dataflow` edge: source hash = source event's
  `writeback_value_fnv`/`consumer_output_fnv`; destination hash = consumer
  output; consumer input must equal the propagated source hash.
- `producer_inst_seq`/`consumer_inst_seq` must match the endpoint events'
  dyn seq.
- Mismatched operands never create edges, so they cannot enter
  PropagationCoverage.
- `consumer_operand_records`, `consumer_instructions` and
  `taint_value_mismatch_records` are reported in the completeness report and
  pilot_meta.

## DA04 impact (why this round also fixed the public path)

The generic post-writeback change is what makes DA04's 4-byte load hash
continuous: the old source hash was the 4-byte payload; the consumer read
the extended register value. After the fix, R04/R05 have 0 mismatches,
1,009/7,714 matched consumer records, coverage COMPLETE and chain PASS.
See `DA04_End_to_End_Chain_Audit_v3.2.6.md`.
