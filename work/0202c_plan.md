# WHEN5X3 MMU 23-chain completion — implementation plan

Round 0202c · 2026-11-17 · `gem5-fi-mmu-when5x3`

## Root causes (verified in raw traces)

23 PARTIAL are all `PARTIAL_ARCHITECTURE`: the MMU side is fully traced to
`translation_result` + `lsu_request`, but the downstream O3 pine (IFU for
fetch, LSU/commit for data) is never fault-tagged. Three classes:

### Class 1 — 12 instruction-fetch chains (M03-C02, M04-C02, M05-C02, M07-C05)
Execute-mode fetch mints a *synthetic* seq (`mmuNewSyntheticSeq`, 2^63 namespace)
because the O3 `Request` for a fetch line has `hasInstSeqNum()==false`. The
faulted fetch is traced to `lsu_request(mode=Execute)` but the DynInsts built
from the fetched line (`Fetch::buildInst`) are not bound to that transaction, so
IFU response / decode / commit are never emitted or fault-tagged.

**Fix**: thread the fetch translation id (tid) from `translateMmuOn`
(`mmuNoteLsuRequest`) through `finishTranslation` → `fetchBufferTxnId[tid]` →
`buildInst` (register fetch seq → tid) → commit/squash.

### Class 2 — 6 M05-C04/C05 erroneous-commit-consumer chains
M05 corrupts a partial TLB entry. The fault-tagged consumer load (walks the
corrupted partial entry → decoy PA) is *squashed* (decoy request issued, no
commit). The load that actually commits the decoy value is a *warm hit* on a
DTB entry poisoned by the faulted walk. Warm hits are intentionally untraced →
no fault-tagged response/writeback/commit.

**Fix**: record (instance, entry_id, generation) of the DTB entry filled by any
fault-tagged walk as *poisoned*; on a warm hit of a poisoned entry, mint a
consumer transaction adopting the fault so response/writeback/commit are tagged.

### Class 3 — 5 masked chains (M05-C03, M07-C02)
Same warm-hit / denied invisibility as Class 2. M05-C03 is masked (value dead /
overwritten). M07-C02 is masked (grant inverted → translation+lsu_request, but
the access still faults and the value is not consumed). Need an explicit
masking/denial event.

**Fix**: Class 2 adoption surfaces the committed consumer (masking becomes
explicit via squash/overwrite witnesses). For M07 add an explicit
`access_denied`/`masked` witness when a granted-after-inversion access still
delivers a fault or never commits.

## Frozen constraints (must NOT change)
Where (hook/field/bit/mutation op/duration), eligible predicate, fault-model
mutation semantics, oracle/terminal. Only ADD trace emission + correlation IDs.

## Order of work
1. Fetch IFU/decode/commit instrumentation (12 chains) — build + rerun + DAG.
2. Poisoned-entry warm-hit adoption (M05 data + masked) — build + rerun + DAG.
3. M07-C02 masking witness — build + rerun + DAG.
4. Rewrite propagation DAG builder to consume new events; re-run acceptance.
5. Evidence-index / report consistency fix (SampleRunID → RETRY path/SHA).