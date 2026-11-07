# LP01 temporary event selection (2026-11-08)

Excel identity is frozen: SampleRunID / Seed / EventOrdinal 1..5 are unchanged.
Warm-up and ROI are **not** frozen; this is an explicitly **TEMPORARY** event
selection, recorded here with the actual ordinal used.

## Probe

Command shape (one gem5 run per ordinal, R01 seed, W5 `load_response`):

```bash
build/ARM/gem5.opt --outdir=/tmp/lp01_probe/oN configs/se/lsu_proxy.py \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/load_response \
  --cpu O3 --variant B0 --probability 1.0 --chaos_propagation \
  --prop_trace_file prop_trace.csv.gz --chaos_l1dfwd --l1dfwd_first_clock 0 \
  --l1dfwd_fault_mask 0x8 --l1dfwd_max_faults 1 \
  --l1dfwd_rng_seed 1349924126 --l1dfwd_event_ordinal N
```

Acceptance predicate for a pilot target: exactly one `inj_l1dfwd`; one
`taint_reg` (actual register writeback); at least one `consumer`; a `commit`
node for the target dyn_inst_seq. Ordinals 1–60 were probed; the first five
that pass are 1, 2, 3, 4, 14 (ordinals 5–13 inject into loads with no
consumer, so they are not used).

The clinical ordinal is a stable selection RULE, but the dynamic
instruction/tick at that ordinal is not bit-identical across Excel seeds in
this O3 configuration. The table records the actual per-pilot values taken
from each `pilot_meta.json`; the probe-time value is in parentheses.

## Selection (actual per-pilot values)

| Pilot | SampleRunID | Seed | Excel ordinal | Clinical ordinal used | dyn_inst_seq | trigger tick | target address | size |
|---|---|---|---|---|---|---|---|---|
| R01 | LP01-F0-W5-S01-R01 | 1349924126 | 1 | **1** | 5 (5) | 172865 (172865) | 0x80da0 (0x80e10) | 8 |
| R02 | LP01-F0-W5-S01-R02 | 2648660520 | 2 | **2** | 48 (48) | 226380 (271425) | 0x80db8 (0x80e28) | 8 |
| R03 | LP01-F0-W5-S01-R03 | 2021175746 | 3 | **3** | 239 (225) | 605221 (606761) | 0x80dc0 (0x80e30) | 8 |
| R04 | LP01-F0-W5-S01-R04 | 3894776903 | 4 | **4** | 247 (233) | 605990 (607530) | 0x80dc8 (0x80e38) | 8 |
| R05 | LP01-F0-W5-S01-R05 | 1604604537 | 5 | **14** | 287 (235) | 625625 (661815) | 0x80df0 (0x80e40) | 8 |

Consumer counts observed at probe time: 183, 1, 6, 1, 6 respectively. All
targets are 8-byte loads, so the payload hash and the actual register value
hash are directly comparable (`hash_basis=payload_equals_regval`). Each
pilot re-verified commit + writeback + ≥1 consumer; all five are MASKED
(the committed wrong value does not change the W5 checksum).

## Ruling

The five Excel ordinals 1–5 would map to events 1,2,3,4 and 240; event 240
(ordinal 5) has zero consumers. Per the approved rule (“walk to
committed+consuming”), R05 uses ordinal 14. Excel EventOrdinal remains
recorded as 5 in `excel_identity.event_ordinal`; the clinical value is
`excel_identity.event_ordinal_used`.
