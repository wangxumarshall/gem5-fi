# FW05 implementation and five pilots (v3.2.7)

**Binary:** see `logs_v3_2_7/binary_final.sha256` (built from this branch)
**Definition:** `FW05_Definition_Freeze_v3.2.7.md` (`FW05-DEF-v1`, option A)

## What is implemented

`CHAOSLSQFwd::maybeSubstituteFW05` is called from the full-coverage
forwarding decision in `LSQUnit::read()`. It receives the gem5-selected true
source and the nearest older SQ entry with data, plus real seqs, addresses,
sizes and data pointers. `chaos_fw05::isEligible` requires:

- two distinct stores, with the alternative older than the true source;
- load younger than both;
- true source covers the whole load;
- alternative covers the whole load range (no multi-store splice);
- the load-sized bytes actually differ.

Only then is the load buffer filled from the alternative. Address and size
are never changed. The legacy `fwd_source_sub` path is untouched and is
tried only when FW05 declines.

The trace emits `inj_fw05` with TargetPairID, load/PC/addr/size, true and
alt store seq/PC/addr/size/data FNV, SQ/LQ entry+generation, eligible
ordinal, event ordinal, seed, and modification flags. Because a forwarded
load has no memory response, the register writeback is emitted from
`LSQUnit::writeback()`; the PRF value hash equals `alt_data_fnv` (FNV-1a
64-bit, little-endian register basis), and consumers are tainted from it.

## Workload gap and pilot-only override

The frozen W8 `alignment` workload has no two overlapping stores to the same
address in flight: with `--lsq_struct_mode fw05_older_src` it produced zero
eligible events (probe: `alt=no`). A dedicated directed workload,
`workloads/fw05_forward.c`, was built: an older unrelated store, four
distinct 8-byte stores to the same address, then an 8-byte load. The
load sometimes executes before the later stores, in which case the later
store triggers a violation and replays the load; the eligible ordinals are
therefore 1..5. The pilots use the Excel SampleRunID/Seed and a
pilot-only workload override; the manifest records
`path_source=pilot_override (Excel path retained in sample)`. The Excel
WorkloadPath/Oracle were **not** changed. This gap must be resolved before
the 60-sample formal run.

## Five pilots (Excel seeds, event ordinal 1..5)

| Pilot | seed | ordinal | true/alt store | load | alt FNV | terminal | consumers | oracle |
|---|---:|---:|---|---:|---|---|---:|---|
| R01 | 1025137124 | 1 | 12111/12110 | 12114 | 6407d731d902cbed | SQUASHED | 0 | PASS |
| R02 | 1653118510 | 2 | 12155/12154 | 12156 | a06ea71be9c5aa88 | SDC | 2001 | FAIL (SDC) |
| R03 | 2442802213 | 3 | 12190/12189 | 12191 | 141ad82d6cd5f32f | SDC | 2000 | FAIL (SDC) |
| R04 | 899944922 | 4 | 12225/12224 | 12226 | fe9b431f6a056432 | SDC | 1999 | FAIL (SDC) |
| R05 | 2836530945 | 5 | 12260/12259 | 12261 | 5b96aecb6003c639 | SDC | 1998 | FAIL (SDC) |

All five: one injection, target proof all true (distinct stores, younger
load, full cover, data differs, address/size unchanged), validator VALID,
trace COMPLETE, chain PASS, accepted.

**Dataflow proof (R02):** injection alt FNV `a06ea71be9c5aa88`;
`register_writeback` `writeback_value_fnv=a06ea71be9c5aa88`; 2001
consumer instructions matched; commit present; oracle FAIL (checksum
`0x549c9e0347adaf23` vs golden `0x67afad307642983e`). This is SDC, not
some later perturbation: the PRF value is the alternative store's bytes.

## Unit test and build

- `tests/test_fw05_rules.cc` PASS (full cover, no splice, data equality,
  older/store ordering, offset alignment).
- `scons -j126 build/ARM/gem5.opt` exit 0, no new warnings.
- Platform suite 78 passed.

## Non-claims

- No 60-sample formal run.
- FW05 uses a pilot-only directed workload because W8 alignment cannot
  produce the event; the frozen Excel workload/oracle still need a
  researcher decision.
- R01 is squashed; R02-R05 are SDC with ~2,000 matched consumers.
