# DA04 — Implementation and Evidence (LSU v3.2.4)

**Date:** 2026-11-07
**Branch:** `lsu-platform-v3.2.4` (base `7f54db8d`, v3.2.3 final)
**Binary:** `build/ARM/gem5.opt`, sha256 `dae736b2c627960523579482ac0e2916bd015a290afffa88cdc941dec41a6e9c`
**Spec:** `docs/superpowers/specs/2026-11-07-lsu-v3.2.4-da04.md`
**Source audit:** `DA04_Source_Audit_v3.2.4.md`

## 1. Fault definition (unchanged from the researcher's ruling)

4-bit byte-enable of a 32-bit store, bit0 cleared:

```text
1111 -> 1110
0xF  -> 0xE
```

Address, access size and store data are untouched. Store path only; Load is
not an eligible DA04 injection site.

## 2. Source mapping and hook

| Position | File / function / line | Implementation |
|---|---|---|
| Byte-enable construction | `CHAOS/gem5/src/cpu/o3/lsq.cc`, `LSQ::pushRequest`, 831-835 | after `request->_byteEnable = ...`, before `inst->setRequest()`; store-only filter (`!isLoad && !isAtomic && sqIdx>=0`, excludes LLSC/NO_ACCESS/STORE_NO_DATA/CACHE_BLOCK_ZERO) |
| Mask logic | `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/da04_byte_enable.hh` | `eligible(size==4 && 4 all-true lanes)`, `clearLane0`, `maskOf` |
| Injector mode | `CHAOSLSQFwd.cc` `StructMode::Da04BeBit0` (`--lsq_struct_mode da04_be_bit0`) | F0 `ChaOSLsuTrigger`; one fault; log `Site: lsq_pushRequest_byte_enable` |
| SQ entry identity | `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` `insertStore` | `sqIdx`/`sqEntryGeneration` read at injection |
| SQ drain / store writeback | `lsq_unit.cc` `writebackStores` 934-949 | `store_writeback` node with real `be_mask` and data hash |
| Actual memory write | `CHAOS/gem5/src/mem/cache/base.cc` `updateBlockData` 838-880 | `store_mem_write` node: PA, offset, be_mask, before/after, `enabled_written`, `disabled_unchanged`, `lane0_*` |
| Later load | `CHAOSPropagation::noteMemResponse` | matches the faulted store's byte by Request VA/size; `resp -> taint_reg -> consumer` |
| Forwarding boundary | `CHAOSPropagation::noteForwarding` | joins the chain; records that gem5 forwarding does not consult byte-enable |

gem5's native masked-write path is what makes the fault real:
`Packet::isMaskedWrite()` (`packet.hh:1449`), `Packet::writeData`
(`packet.hh:1321-1336`), `BaseCache::updateBlockData -> writeDataToBlock`
(`base.cc:851-854`).

## 3. Injection record (real fields)

Every DA04 injection node carries: `FaultModel=DA04`,
`OriginalByteEnable=0xF`, `InjectedByteEnable=0xE`, `ChangedBit=0`,
`AddressBefore=AddressAfter`, `AccessSizeBefore=AccessSizeAfter`,
`StoreDataBefore=StoreDataAfter` (same FNV hash), SQ entry id and generation.
All values come from the live request at `pushRequest`; none are copied from
the config.

Example (DA04-R04):

```text
injection: seq=13832 sq=1478 gen=1877
  old_be=0xf new_be=0xe changed_bit=0
  addr_before=0x4919d5 addr_after=0x4919d5 size_before=4 size_after=4
  store_data_fnv=ef9edb828f3fc2c (same before/after)
store_writeback: be_mask=0xe data_fnv=ef9edb828f3fc2c
store_mem_write: pa=0x769c0 offset=21 be=0xe
  packet_data=...c1... before=...a5... after=...a5...
  enabled_written=1 disabled_unchanged=1 lane0 packet/before/after=0xc1/0xa5/0xa5
memory_response: seq=19210 pa=0x769d5 data_hex=a514af81  (byte0=0xa5)
register_writeback + errant_commit + 9064 consumer commits
oracle: checksum=0x3f89eab79392ce4d (golden 0x3f89eab79392ce69) -> FAIL
```

## 4. Status ladder

| Level | Status | Evidence |
|---|---|---|
| DESIGNED | yes | spec |
| SOURCE_AUDITED | yes | `DA04_Source_Audit_v3.2.4.md` |
| IMPLEMENTED | yes | commits `c3190f45`, `56b42650`, `4b2487a6` |
| COMPILED | yes | `logs/build_v324.log`, `logs/build_v324_fixes.log`, scons exit 0 |
| UNIT_TESTED | yes | `tests/test_da04_byte_enable.cc` RED→GREEN; `logs/unit_test_da04_*.log` |
| PILOT_RUN | yes | `pilots_v3_2_4/DA04-R01..R05`, all `accepted=true` |
| PROPAGATION_VERIFIED | **yes** | R03/R04/R05 chains complete with `chain_integrity=PASS`; R04/R05 SDC with the disabled-lane proof |

PROPAGATION_VERIFIED is claimed on the evidence bar in the spec: one ptag
chain containing injection -> store writeback -> actual cache write -> load
response -> register writeback -> consumer commit, with the DA04 mask
invariant (`disabled_unchanged=1`) and the load returning the old byte.
It is **not** inferred from "five runs succeeded".

## 4b. Chain-attribution guard (whole-branch review fix)

The fresh reviewer found that load attachment was address-overlap only. The
fix (`store_chain_rules.hh`, used in `noteMemResponse`) requires:

- the load is younger than the store (`load_seq > store_seq`),
- the actual cache write already happened (`written_tick != 0` and
  `now >= written_tick`),
- no different store overwrote the faulted byte (`noteStoreWrite` marks the
  registry entry and emits a `store_overwrite` node).

Effect on the pilots: R03's earlier "consumer" was an address-only match
after a later overwrite; it is now correctly MASKED/lane-not-read. R04/R05
keep complete consumer chains (the load responded before the overwrite).
This is recorded rather than hidden; the five-pilot csv in this directory
is the post-fix run.

## 5. Boundary recorded honestly

- The five clinical ordinals are a **TEMPORARY_EVENT_SELECTION**: Excel
  1..5 hit dynamic-loader stores that are all squashed. Excel
  SampleRunID/Seed are preserved; `excel_identity.event_ordinal_used` records
  the clinical ordinal.
- `store_mem_write` records the physical block address; injection records the
  virtual address. SE's translation is visible in the trace (e.g. VA
  `0x4919d5` -> PA `0x769d5`); load matching uses Request VA.
- A forwarded load receives the intended store data because gem5's forwarding
  memcpy ignores byte-enable; such a run is recorded as a forwarding-chain
  MASKED, not as a memory-write effect.
