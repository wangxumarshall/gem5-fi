# LSU v3.2.5 — remaining issues

1. **DA04 causality uses the last send.** R04/R05 are SDC again under the
   last-send anchor (1,009 / 7,714 consumers). The first-send-only interim
   verdict was wrong. Remaining boundary: SE VA aliasing — a later reader
   through a different VA mapping to the same memory location is not matched
   (the matcher is VA-based). R04/R05 do not depend on an alias.
2. **LP01 has no SDC pilot.** All five targets commit the wrong value but
   the W5 checksum is unchanged (MASKED).
3. **Non-8-byte pilot coverage.** The size matrix (1/4/7/8/9/12/16) is
   unit-tested; the pilots only exercise 8-byte loads. For other sizes the
   payload and extended register value hash differently by design
   (`hash_basis=regval_extension`).
4. **Warm-up/ROI not frozen.** Clinical ordinals are temporary; the same
   ordinal can select a different dyn_inst_seq/tick under a different seed.
5. **Formal grid not run.** No 60-sample run and no multi-cell LP01 grid.
6. **Vector/matrix consumers** have no scalar value hash; continuity is
   scalar-only (null is explicit, not a failure).
7. **Trace storage.** Each LP01 JSONL is ~43 MB; five traces dominate this
   round's repository growth.
8. **SE address model.** `pa` is the cache-side address, not an FS physical
   address; see `LSU_v3.2.5_SE_Address_Semantics.md`.
