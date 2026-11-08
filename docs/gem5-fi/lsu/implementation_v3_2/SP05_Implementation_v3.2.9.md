# SP05 implementation and five pilots (v3.2.9)

Binary `303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0`.
Definition: **Premature Store Completion** (`SP05-CFG01`). Hook: target
selection in `LSQUnit::commitStores` (Nth store earning `canWB`), fault action
in `LSQUnit::writebackStores` calling the real `LSQUnit::completeStore`
before the cache write is sent.

## State change

For the target: `_completed` false→true and `storesToWB` −1 at the injection
tick; the cache write is skipped (`mem_sent=0`, no later `store_mem_write`).
The request is freed by `LSQEntry::clear()` through the same path used by the
existingsize-0 instant completions. This is a premature completion / lost
write, not early visibility.

## Five pilots (Excel identities, workload `store_path`, ordinals 1–5)

| Pilot | SampleRunID | seed | seq | sq idx/gen | storesToWB | inject tick | terminal | oracle |
|---|---|---|---:|---|---|---|---:|---|---|
| R01 | SP05-F6-W6-S01-R01 | 1489155957 | 18 | 1/1 | 4→3 | 150150 | MASKED | PASS |
| R02 | SP05-F6-W6-S01-R02 | 1290498198 | 19 | 2/2 | 4→3 | 150150 | MASKED | PASS |
| R03 | SP05-F6-W6-S01-R03 | 2768710389 | 23 | 3/3 | 4→3 | 150150 | MASKED | PASS |
| R04 | SP05-F6-W6-S01-R04 | 2741073922 | 24 | 4/4 | 4→3 | 150150 | MASKED | PASS |
| R05 | SP05-F6-W6-S01-R05 | 4098160626 | 28 | 5/5 | 6→5 | 150535 | MASKED | PASS |

All five: exactly one injection, one `sp05_complete`, trace
COMPLETE/VALID, propagation coverage COMPLETE, chain PASS,
`consumer_instructions=0`, checksum equals the matched control
`0x2543a2a60de01795`. No HANG, no TIMEOUT.

## Propagation

Real stages: `injection` (writebackStores_prematureComplete) → `sq_lifecycle`
free/complete → `sp05_complete`, linked by the injection ptag and the store's
dynamic seq. The store commits (`STORE_COMMITTED_LANE_NOT_READ`); no later
load reads the target address in `store_path`, so there is no register
writeback or consumer stage. `PROPAGATION_VERIFIED` stays 0.

## Safety

`max_faults==0` → 1; independent `sp05_fired`; `assert(injected==1)`;
`storesToWB` delta exactly 1; only the selected `(idx,gen)` can fire;
`!request->isSent()` gate; watchdog exits 1 on expiry; runner timeout intact.
See `SP05_Safety_Tests_v3.2.9.md`.
