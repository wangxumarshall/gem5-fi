# LP01 — Source audit and size<8 OOB fix (LSU v3.2.4)

**Date:** 2026-11-07
**Status:** SOURCE_AUDITED / IMPLEMENTED / COMPILED / UNIT_TESTED; pilots and PROPAGATION_VERIFIED are the next round.

## Source mapping

| Item | Finding |
|---|---|
| Real structure | `o3::LSQUnit::completeDataAccess(PacketPtr)` (`lsq_unit.cc:107-215`) |
| Hook | `lsq_unit.cc:199-201` calls `CHAOSL1DForward::maybeCorrupt(request->mainPacket())` before register writeback |
| Injector | `CHAOSL1DForward::maybeCorrupt(PacketPtr)` (`CHAOSL1DForward.cc:67`) |
| Packet payload | `Packet::getPtr<uint8_t>()` (load response data) |
| Old corruption | `uint64_t *p = reinterpret_cast<uint64_t*>(data); n = sz/8; if (n==0) n=1; p[i] ^= mask` — always writes one 8-byte word |
| Defect | for response `size < 8` the cast + 8-byte store is out of bounds (heap overrun / UB); the model has no size<8 support |
| Fix | `chaos_lp01::xorMask(data, size, mask)` — byte-wise, mask repeats every 8 bytes; identical behavior for size ≥ 8 |
| Unit test | `tests/test_lp01_bytewise.cc` (asserts 1/4/7/16-byte payloads; RED before the header existed) |

## Verification

```text
LP01 byte-wise corruption unit test: PASS
scons -j16 build/ARM/gem5.opt -> exit 0
no-fault alignment baseline -> checksum=0x3f89eab79392ce69 (golden)
```

## Not yet done

- LP01 pilots on W5 `load_response`, target-event proof, and its own propagation chain.
- The existing `CHAOSL1DForward` tracer link (the v3.2.3 audit noted it has no trace link); LP01 will need the same store-style chain work before any PROPAGATION_VERIFIED claim.

## v3.2.5 semantic ruling (from Excel, not from the old implementation)

Excel v3.2.1 Sheet 3 (`TargetField=Packet::data[0]`), Sheet 5
(`BitEntryByteIndex=byte0 bit3`, `FaultValue=data[0] ^= 0x08（严格按size逐字节）`)
and the recommended option A define a **single-bit fault in response byte 0**.
For sizes 1/4/7/8/9/12/16 only `data[0]` changes; the old mask-repetition over
byte 8 is not part of LP01-CFG01. The unit test pins all seven sizes plus 0.

Status after the semantic fix: DESIGNED / SOURCE_AUDITED / IMPLEMENTED /
COMPILED / UNIT_TESTED. Pilots and PROPAGATION_VERIFIED remain open until the
W5 five-pilot round.
