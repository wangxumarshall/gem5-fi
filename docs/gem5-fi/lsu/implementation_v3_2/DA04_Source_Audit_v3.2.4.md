# DA04 — Source Audit (LSU v3.2.4)

**Date:** 2026-11-07
**Tree:** `lsu-platform-v3.2.4`, base `7f54db8d` (v3.2.3 final)
**Model:** DA04 — Byte-enable construction, F0, 4-bit mask bit0 clear (`0xF -> 0xE`)

## 1. What gem5's byte-enable actually is

| Item | Finding | Evidence |
|---|---|---|
| Data type and width | `std::vector<bool> _byteEnable`; length equals the access size (not a fixed 4-bit word) | `CHAOS/gem5/src/mem/request.hh:403` |
| Setter contract | `Request::setByteEnable` asserts `be.size() == _size` | `request.hh:715-720` |
| Generation site | `LSQ::pushRequest` builds the mask for a new request; the ARM ISA passes no `byte_enable`, so a regular store gets `std::vector<bool>(size, true)` | `CHAOS/gem5/src/cpu/o3/lsq.cc:831-835` |
| Bit-to-lane mapping | index 0 = lowest-addressed byte (`packet data[0]`, AArch64 little-endian = register bits [7:0]); for `size==4` the four entries are exactly the 4-bit mask, bit0 = lowest byte | `Packet::writeData`, `packet.hh:1321-1336` |
| Propagation | `addReq` slices the vector per fragment and calls `Request::setByteEnable` | `lsq.cc:1116-1129`, `lsq.cc:1005` |
| Does the SQ keep it? | The SQ entry keeps data and the `LSQRequest`; the mask lives on `LSQRequest::_byteEnable` and each fragment `Request`, and SQ drain rebuilds packets from that same `Request` | `lsq_unit.cc:869-990`, `lsq.cc:1270-1300` |
| Does it affect the memory write? | Yes. Clearing bit0 makes `Packet::isMaskedWrite()` true; `BaseCache::updateBlockData -> cpkt->writeDataToBlock` writes only enabled bytes | `packet.hh:1449-1453`, `1321-1336`; `mem/cache/base.cc:838-858` |
| Load path | The forwarding memcpy does not consult byte-enable (no `byteEnable` reference in `lsq_unit.cc`); the memory path returns the real cache bytes | `lsq_unit.cc:1557-1623`, `107-215` |

**Conclusion.** gem5 stores the mask as a byte vector, not a fixed 4-bit field. For `size==4` stores it is exactly four lanes, and index 0 is the lowest-addressed byte. Clearing it is consumed natively by gem5's masked-write path, so no address/size/data change is needed to affect the memory write.

## 2. DA04 source mapping table

| Microarchitectural position | LSU structure | Source file | Function | Lines | Original mask | Fault mask | Trigger | Downstream propagation |
|---|---|---|---|---|---|---|---|---|
| Byte-enable construction | `LSQ::LSQRequest` | `CHAOS/gem5/src/cpu/o3/lsq.cc` | `LSQ::pushRequest` | 831-835 | `0xF` | `0xE` | target dynamic Store (size=4, all-ones mask, F0 ordinal) | `addReq -> Request::setByteEnable -> Packet::isMaskedWrite -> writeData -> cache block` |
| SQ allocation | `o3::LSQUnit::StoreQueue` | `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` | `LSQUnit::insertStore` | 426-450 | — | — | store issue | SQ idx/generation recorded in the injection node |
| SQ data install | SQ entry | `lsq_unit.cc` | `LSQUnit::write` | 1815-1865 | — | — | store data copied into SQ | (DA04 leaves data untouched; SQ01 corrupts it here) |
| SQ drain / store writeback | `LSQUnit::writebackStores` | `lsq_unit.cc` | `LSQUnit::writebackStores` | 869-990 | `0xF` | `0xE` | `canWB` and cache port available | `buildPackets` -> `sendPacketToCache` |
| Memory request | `LSQ::SingleDataRequest` | `lsq.cc` | `buildPackets` / `sendPacketToCache` | 1270-1300 / 1367 | inherited | inherited | after drain | `Packet::createWrite(req)` |
| Actual memory write | `BaseCache` | `CHAOS/gem5/src/mem/cache/base.cc` | `BaseCache::updateBlockData` | 838-858 | writes all 4 lanes | writes lanes 1-3 | cache accepts the WriteReq | masked block bytes |
| Later load | `LSQUnit::completeDataAccess` | `lsq_unit.cc` | `completeDataAccess` / `writeback` | 107-215 | — | — | load covers the affected byte | `resp -> taint_reg -> consumer` |
| Application oracle | workload `alignment` | `implementation_v3_2/workloads/alignment.c` | `main` | checksum | — | — | run completion | oracle PASS/FAIL |

## 3. Hook decision

- Hook after the mask assignment at `lsq.cc:831-835`, inside the new-request branch, **before** `inst->setRequest()`.
- This is the site the Excel sheet names (`pushRequest/addReq 构造 Request 时`), and it is the single point where the vector exists before any fragment is built.
- Store-only filter: `!isLoad && !isAtomic && inst->sqIdx >= 0`, excluding `LLSC`, `NO_ACCESS`, `STORE_NO_DATA`, `CACHE_BLOCK_ZERO`.
- `inst->sqIdx` and `inst->sqEntryGeneration` are already assigned by `LSQUnit::insertStore` (issue time) before `executeStore` calls `initiateAcc -> pushRequest`; the injection node can therefore carry the real SQ entry identity.
- Size/eligibility: exactly `size == 4` and a four-entry all-true mask. Non-4-byte and already-masked requests never enter the eligible stream.

## 4. Semantic boundaries recorded honestly

1. **Forwarding ignores byte-enable.** If a younger load forwards from the faulted store's SQ entry, it receives the intended store data, not the masked-lane effect. The trace records this as `byte_enable_not_applied_in_forward=1`; such a pilot is not claimed to have affected a memory write.
2. **Masked write is real.** When the store drains and the cache applies it, the disabled lane is expected to be byte-identical before and after. `store_mem_write` records `disabled_unchanged` and `lane0_before/lane0_after`.
3. **Physical vs virtual address.** SE uses an identity mapping; the tracer records the packet address as PA and the store address as VA, consistent with the existing tracer assumption.
4. **Load is not a DA04 injection site.** The hook is inside the store branch only; no Load can receive this fault.

## 5. Verification of cited lines

Commands run on 2026-11-07 (output quoted in the execution session):

```bash
sed -n '830,835p' CHAOS/gem5/src/cpu/o3/lsq.cc
sed -n '400,406p' CHAOS/gem5/src/mem/request.hh
sed -n '714,721p' CHAOS/gem5/src/mem/request.hh
sed -n '1448,1454p' CHAOS/gem5/src/mem/packet.hh
```
