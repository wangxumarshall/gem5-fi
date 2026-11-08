# SP05 safety tests (v3.2.9)

Binary `cdf8d5fdf603598b8852e0044fc3d6b867f4ce4e22a91e3447e331dbfc565ce9`.
Workload `store_path`; logs under `evidence_v3_2_9/SP05_safety/`.

| Test | Command flags | Result |
|---|---|---|
| one-shot / clamp | `sp05_complete --max_faults 0 --sp05_event_ordinal 1` | exit 0; exactly one `writebackStores_prematureComplete` (seq 18, sq 1/gen 1); `CHAOS_SP05_STATUS fired=1 injected=1`; checksum `0x2543a2a60de01795` |
| non-target integrity | `--sp05_event_ordinal 2 --rng_seed 1290498198` | target seq 19, sq 2/gen 2; exactly one `sp05_complete`; committed/executed/fetched instruction counts identical to the control (211963/253012/223206) |
| control | `--probability 0.0 --sp05_event_ordinal 1` | exit 0; `selected=0 fired=0 injected=0`; checksum `0x2543a2a60de01795` |
| counter/state | trace `sp05_complete` | `canwb_before=1 completed_before=0 stores_to_wb_before=4 stores_to_wb_after=3 mem_sent=0`; delta exactly 1; one event per target |
| watchdog | `--sp05_watchdog_cycles 1` | exit **1**, `CHAOS_SP05_WATCHDOG=EXPIRED`; not MASKED |
| duplicate protection | rule test + `sp05_fired` | `tests/test_sp05_rules.cc` PASS; `assert(faults_injected_count==1)` |

`mem_sent=0` and the absence of a later `store_mem_write` for the target show the
store's cache write was skipped: this fault is premature completion / lost write,
not early visibility.
