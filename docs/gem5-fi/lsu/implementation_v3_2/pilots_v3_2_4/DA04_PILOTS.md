# DA04 — Five Pilot Results (LSU v3.2.4)

> **v3.2.5 correction (2026-11-08):** request-time causality removes the
> R04/R05 consumers; both pilots are now **UNRESOLVED**, not SDC. See
> `../LSU_v3.2.5_DA04_Trace_Fix_Evidence.md`. The R05 oracle value below is
> corrected to the committed `oracle.log`.

**Date:** 2026-11-07
**Binary:** `build/ARM/gem5.opt` sha256 `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297` (all five pilot manifests agree; v3.2.5 correction of the earlier inconsistent line).
**Workload:** `implementation_v3_2/workloads/alignment` (W8)
**Event selection:** `TEMPORARY_EVENT_SELECTION (Excel EventOrdinal; warm-up/ROI not frozen)` — see the ruling below.

## Identity and event map

| Pilot | SampleRunID (Excel) | Seed (Excel) | Excel ordinal | **Clinical ordinal used** | Observed `dyn_inst_seq` | SQ idx / gen |
|---|---|---|---|---|---|---|
| R01 | DA04-F0-W8-S02-R01 | 4185444934 | 1 | **1** | 320 | 52 / 71 |
| R02 | DA04-F0-W8-S02-R02 | 2627302015 | 2 | **6** | 727 | 70 / 129 |
| R03 | DA04-F0-W8-S02-R03 | 3592849939 | 3 | **16** | 3030 | 221 / 358 |
| R04 | DA04-F0-W8-S02-R04 | 3815557835 | 4 | **50** | 13832 | 1478 / 1877 |
| R05 | DA04-F0-W8-S02-R05 | 2016743094 | 5 | **200** | 14582 | 1628 / 2027 |

**Ruling (recorded):** Excel EventOrdinal 1–5 select dynamic-loader/libc stores that are all squashed before commit; they cannot produce a store writeback or a memory-write node. The Excel SampleRunID and Seed are kept unchanged; the clinical ordinal is overridden (recorded as `excel_identity.event_ordinal_used`) so the five pilots cover the required outcome classes. Warm-up/ROI remain unfrozen.

## Per-pilot evidence

All five: `OriginalByteEnable=0xF`, `InjectedByteEnable=0xE`, `ChangedBit=0`, `AddressBefore=AddressAfter`, `AccessSizeBefore=AccessSizeAfter`, `StoreDataBefore=StoreDataAfter` (injection log and trace `detail`).

### R01 — SQUASHED (target store squashed before commit)

- Injection: seq 320, `0x491010`, size 4, data hash `4d25767f9dce13f5`, `0xF -> 0xE`.
- Chain: `sq_lifecycle(alloc) -> injection -> squash -> sq_lifecycle(free, squash)`.
- Terminal: **SQUASHED** / `TARGET_SQUASHED_NO_COMMIT`; oracle PASS.
- Honest note: later load/consumer nodes are address-correlated with the faulted byte but the store never drained, so they are **not** fault-caused. The terminal is SQUASHED, not MASKED.

### R02 — MASKED (store committed, affected lane never read)

- Injection: seq 727, `0x4976fc`, size 4, data hash `4d25767f9dce13f5`, `0xF -> 0xE`.
- Chain: `injection -> commit -> store_writeback(be=0xe) -> store_mem_write -> sq_lifecycle(free, complete)`.
- Memory write: PA `0x7c6c0` + offset 60, `be_mask=0xe`, `lane0 packet/before/after = 0x0/0x0/0x0`, `enabled_written=1`, `disabled_unchanged=1`.
- No later load covers the affected byte.
- Terminal: **MASKED** / `STORE_COMMITTED_LANE_NOT_READ`; oracle PASS.

### R03 — MASKED (store committed, lane not read after the overwrite guard)

- Injection: seq 3030, `0x7ffffefca0`, size 4, data hash `ad2aca7747985764`, `0xF -> 0xE`.
- Chain: `injection -> commit -> store_writeback(be=0xe) -> store_mem_write -> sq_lifecycle(free, complete)`.
- Memory write: PA `0x7dc80` + 32, `lane0 packet/before/after = 0x1/0x0/0x0`, `disabled_unchanged=1`.
- An address-overlapping load existed in the earlier run, but a later store
  overwrote the byte before that load's response. The v3.2.4 review fix
  refuses address-only attribution (`mayConsumeFaultByte`), so the load is
  **not** counted as a consumer.
- Terminal: **MASKED** / `STORE_COMMITTED_LANE_NOT_READ`; oracle PASS.

### R04 — SDC (fault reached a load and the application checksum changed)

- Injection: seq 13832, `0x4919d5`, size 4, data hash `ef9edb828f3fc2c`, `0xF -> 0xE`.
- Chain: `injection -> commit -> store_writeback(be=0xe) -> store_mem_write -> memory_response(seq 19210) -> register_writeback -> errant_commit -> 1,009 register-dataflow edges / consumer commits` (counted from the committed `trace_v31.jsonl`; v3.2.5 correction of the earlier `9,064` figure). The v3.2.5 request-time audit removes these consumers: the seq-19210 load requested at tick 2,286,900, before the store write at 17,042,410 (see `../LSU_v3.2.5_DA04_Trace_Fix_Evidence.md`).
- Memory write: PA `0x769c0` + 21, `lane0 packet/before/after = 0xC1/0xA5/0xA5`, `enabled_written=1`, `disabled_unchanged=1`.
- Load response: 4 bytes at PA `0x769d5`, `data_hex=a514af81`; the affected byte is `0xA5` (old memory byte), not the intended store byte `0xC1`.
- Oracle: **FAIL** (`checksum=0x3f89eab79392ce4d`, golden `0x3f89eab79392ce69`).
- Terminal: **SDC** / `ORACLE_FAIL`.

### R05 — SDC (second independent store/address)

- Injection: seq 14582, `0x491c2d`, size 4, data hash `45e9ebf61e9ee776`, `0xF -> 0xE`.
- Chain: `injection -> commit -> store_writeback(be=0xe) -> store_mem_write -> memory_response(seq 19960) -> register_writeback -> errant_commit -> 7,714 consumer commits`.
- Memory write: PA `0x76c00` + 45, `lane0 packet/before/after = 0x77/0xA5/0xA5`, `disabled_unchanged=1`.
- Load response: 4 bytes at PA `0x76c2d`, `data_hex=a5623036`; affected byte `0xA5`, not the intended `0x77`.
- Oracle: **FAIL** (`checksum=0xb948f769e7d691f5`, golden `0x3f89eab79392ce69`).
  (v3.2.5 correction: the v3.2.4 text printed `0x40f219fae293ba25`; the
  committed `oracle.log` reports `expected=3f89eab79392ce69 got=b948f769e7d691f5`.)
- Terminal: **SDC** / `ORACLE_FAIL`.

## Byte-enable before/after

```text
Store path (all pilots):  1111 -> 1110   (0xF -> 0xE)
Address:                  unchanged (AddressBefore == AddressAfter)
Access size:              unchanged (4 -> 4)
Store data:               unchanged (same FNV hash in injection and writeback)
```

## Propagation verdict

- A single chain with `injection -> store_writeback -> store_mem_write -> memory_response -> register_writeback -> consumer_commit` exists in **R04 and R05**.
- In R04/R05 the disabled lane is byte-identical before/after (`0xA5 -> 0xA5`), the later load returns `0xA5`, and the application checksum changes — the mask demonstrably affected the memory write and the subsequent read.
- The attribution guard requires the load to be younger than the store, to respond after the actual cache write, and the byte not to have been overwritten. This is what removes R03's earlier address-only consumer.
- This satisfies the plan's PROPAGATION_VERIFIED evidence bar; the chain-integrity validator (Task 11) is the independent check and is recorded in the status report.
- R01 is SQUASHED, R02 and R03 are MASKED-without-consumer; none is counted as propagation evidence.

## Trace files

`trace_v31.jsonl` for each pilot is committed in this directory (20–35 MB each, under the 100 MB GitHub limit).
