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

The eligible load-response stream is deterministic; with `probability=1.0`
and a fixed mask the seed does not change which event ordinal N is. Each
pilot below re-verifies its own dyn_inst_seq and tick in `pilot_meta.json`.

## Selection

| Pilot | SampleRunID | Seed | Excel ordinal | Clinical ordinal used | dyn_inst_seq | trigger tick | target address | size |
|---|---|---|---|---|---|---|---|---|
| R01 | LP01-F0-W5-S01-R01 | 1349924126 | 1 | **1** | 5 | 172865 | 0x80e10 | 8 |
| R02 | LP01-F0-W5-S01-R02 | 2648660520 | 2 | **2** | 48 | 271425 | 0x80e28 | 8 |
| R03 | LP01-F0-W5-S01-R03 | 2021175746 | 3 | **3** | 225 | 606761 | 0x80e30 | 8 |
| R04 | LP01-F0-W5-S01-R04 | 3894776903 | 4 | **4** | 233 | 607530 | 0x80e38 | 8 |
| R05 | LP01-F0-W5-S01-R05 | 1604604537 | 5 | **14** | 235 | 661815 | 0x80e40 | 8 |

Consumer counts observed at probe time: 183, 1, 6, 1, 6 respectively. All
targets are 8-byte loads, so the payload hash and the actual register value
hash are directly comparable (`hash_basis=payload_equals_regval`).

## Ruling

The five Excel ordinals 1–5 would map to events 1,2,3,4 and 240; event 240
(ordinal 5) has zero consumers. Per the approved rule (“walk to
committed+consuming”), R05 uses ordinal 14. Excel EventOrdinal remains
recorded as 5 in `excel_identity.event_ordinal`; the clinical value is
`excel_identity.event_ordinal_used`.
