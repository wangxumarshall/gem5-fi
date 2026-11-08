# FW05 final fault definition (frozen 2026-11-08)

## Identity

- Model: FW05 (partially-overlapping data splice — retained ID)
- Name: Wrong-Source Store-to-Load Forwarding
- FaultConfigID: FW05-CFG01 (definition `FW05-DEF-v1`, option A)
- Unit: FWD
- Target function: the store→load forwarding decision in
  `LSQUnit::read()` full-coverage branch (`lsq_unit.cc` ~1646-1677)
- Hook: `CHAOSLSQFwd::maybeSubstituteFW05`, called only in
  `StructMode::Fw05OlderSrc`

## Fault mechanism

The load is normally served from `true_src`, the youngest matching store
selected by gem5's full-coverage forwarding. The fault serves the same
load bytes from a different, older store (`alt_src`) instead.

- No address change; no access-size change.
- No multi-store splice: `alt_src` must cover the entire load range.
- No delete; no byte-lane skew; no bit flip.
- One injection per sample, selected by `EligibleForwardingPairOrdinal`.
- If no eligible pair exists or the target ordinal is not reached, the run
  records `NOT_TRIGGERED`; no injection is fabricated.

## Eligibility (`FW05-ELIG-v1`)

All must hold:

1. Load is younger than both stores.
2. `true_src` and `alt_src` are different dynamic instructions.
3. `alt_src.seq < true_src.seq` (the alternative is older).
4. `true_src` covers the whole load range.
5. `alt_src.addr <= load_addr` and
   `alt_src.addr + alt_src.size >= load_addr + load_size` (full cover,
   no splice).
6. The load-size bytes at the true source and at
   `alt_src.data + (load_addr - alt_src.addr)` differ. If the data is
   equal, the event is NOT eligible (the fault would be unobservable).

## Required trace identity

TargetPairID, load seq/PC/address/size, true store seq/PC/address/size/data
FNV, alt store seq/PC/address/size/data FNV, copy offset,
SQ entry + generation for both stores, LQ entry + generation, eligible
ordinal, event ordinal, seed, SampleRunID.

Downstream: the response `data_fnv` must equal the alt-source FNV; the
register-writeback hash must equal the response-derived value; at least one
consumer input hash must equal the writeback hash. A mismatch is a chain
FAIL, not MASKED.

## Explicitly out of scope

Option B (true multi-store partial-overlap splice) is not supported by the
RTL/gem5 forwarding path and is not implemented. The model is not
renamed and is not deleted.
