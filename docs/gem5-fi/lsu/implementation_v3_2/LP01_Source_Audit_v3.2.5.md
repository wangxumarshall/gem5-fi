# LP01 source audit (LSU v3.2.5)

## Source mapping

| Item | Finding |
|---|---|
| Structure | `o3::LSQUnit::completeDataAccess(PacketPtr)` (`CHAOS/gem5/src/cpu/o3/lsq_unit.cc`) |
| Hook | calls `CHAOSL1DForward::maybeCorrupt(request->mainPacket(), inst->isLoad(), before, mask)` before `writeback()` |
| Injector | `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.{hh,cc}` |
| Payload | `Packet::getPtr<uint8_t>()` of the load response |
| Semantics | `chaos_lp01::corruptByte0`: only byte lane 0, `mask & 0xff`, size-bounded; size 0 / mask 0 no-op |
| Trace | `CHAOSPropagation::noteL1DForwardInjection` / `noteMemResponse` / `noteL1DForwardWriteback` |
| Consumer | `CHAOSPropagation::noteCommit` (input + output hashes) |

## Check list (user Phase 1)

1. **Packet actual returned data** — the injector reads/writes `pkt->getPtr<uint8_t>()` of the response packet; the trace's `orig_data_hex`/`inj_data_hex` are taken from that buffer.
2. **After L1D read** — the hook is in `completeDataAccess`, after the response returned from memory.
3. **Before register writeback** — the XOR runs before `writeback(inst, mainPacket)`; the writeback event is emitted after `completeAcc` and reads the PRF.
4. **Load response only** — eligibility requires `pkt->hasData() && !pkt->isWrite() && is_load && !req->isInstFetch()`. SC/atomic/I-fetch are rejected.
5. **Address / size / request id unchanged** — the injector changes only payload byte 0; the trace records the injection address and size and the payload length; request/response/fragment ids are attached, not regenerated.

## Payload-size semantics (Excel-derived, not inferred from the old code)

Sheet 3 `TargetField=Packet::data[0]`; Sheet 5 `BitEntryByteIndex=byte0 bit3`,
`FaultValue=data[0] ^= 0x08（严格按size逐字节）`, recommended option A.
The model is one bit in response byte 0. For sizes 1/4/7/8/9/12/16 exactly
`data[0]` changes; bytes 1..N-1 are untouched. The old “mask repeats at byte
8” behavior is not LP01-CFG01. Mask bits 8..63 are outside the modeled lane.
Size 0 and mask 0 are no-ops.

## Unit tests

`tests/test_lp01_bytewise.cc` pins 0/1/4/7/8/9/12/16 plus the ordinal helper.
Real output: `LP01 byte-0 payload matrix (0/1/4/7/8/9/12/16): PASS`.
