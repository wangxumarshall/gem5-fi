# Real ARM CPU Case Mapping

Only one real case was supplied by the researcher; no additional case is invented.

## Mapping

| Field | Value |
|---|---|
| RealCaseID | RC-MMU-001 |
| ObservedSymptom | After the OS updates a page-table mapping and performs correct TLB maintenance/synchronization, the CPU still uses the old DTLB entry, accesses the old physical address and reads wrong data. |
| SuspectedUnit | DTLB (implementation-specific entry/tag-match/invalidation path; exact level and bank unknown) |
| IndirectSignal | software-visible stale data after correct TLBI with no exception; the old-PA marker is returned where the new-PA marker is expected |
| CandidateModel | M01 |
| MatchingFeatures | missed TLBI invalidation; entry remains valid=true; stale entry is consumed by a later lookup after the remap; old PA; wrong data value; no exception |
| DifferentiatingFeatures | gem5 M01 target is the l2_shared (unified L2) TLB entry, not the DTB; the injected site is TLB::flush invalidation suppression after an exact-key tlbi_match; the DTB copy was not a valid match at that moment (evicted/replaced). The real silicon defect may sit in DTLB tag matching, invalidation broadcast, or ASID/VMID handling and is not observable here. |
| Evidence | Researcher-supplied case description (no external citation exists in the repository); M01 mechanism/oracle documents: /home/sdc/gem5-fi-mmu-impl-v2/mmu_phase1_work/design/MMU_Final_Design_Package/02_Original_Audit_Reports/MMU_Propagation_Path.md; /home/sdc/gem5-fi-mmu-impl-v2/mmu_phase1_work/design/MMU_Final_Design_Package/02_Original_Audit_Reports/MMU_Terminal_Oracle.md; /home/sdc/gem5-fi-mmu-impl-v2/docs/gem5-fi/mmu/MMU_Review_Delta_Package/M01_Target_TLB_Selection.md; frozen M01 samples M01-F0-W9-S01-R01..R05 with tlbi_match+tlbi_suppressed and old-marker 0xaa consumption. |
| Confidence | MEDIUM |
| FunctionalSemanticMatch | HIGH |
| MicroarchitecturalStructureMatch | LOW_TO_MEDIUM |
| PropagationPathMatch | HIGH |
| DiagnosticFeatureMatch | MEDIUM_TO_HIGH |
| Limitations | No real-silicon trace, ASID sequence, or erratum/CVE citation is available; L2/unified TLB is not the DTLB; the gem5 fault is deliberate suppression of one matched invalidation, whereas the real root cause is unknown. |

## Four separate match dimensions

1. **Functional fault semantics — HIGH.** Both are a missed invalidation of a valid translation after correct software maintenance, leaving a stale entry consumable. The gem5 M01 entry is retained (`tlbi_match` then `tlbi_suppressed`) and later consumed after the remap.
2. **Microarchitectural structure — LOW_TO_MEDIUM.** The gem5 target is `l2_shared` (unified L2 TLB), not the DTB. The DTB copy was not a valid match at that moment (`M01_Target_TLB_Selection.md`). This mapping does **not** claim that the gem5 L2/unified TLB is the real chip's DTLB.
3. **Propagation path — HIGH.** stale entry -> old PA -> LSU/memory -> wrong data -> software oracle, with no exception. M01 R01-R05 all return the old marker 0xaa instead of the new marker 0x55.
4. **Diagnostic feature match — MEDIUM_TO_HIGH.** The diagnostic features are `tlbi_match`/`tlbi_suppressed`, a retained entry identity, a later consumption event and an old-PA marker. The real case lacks event-level evidence, so the feature match cannot be raised above medium.

## Limitations

- No external erratum/CVE/trace citation exists in the repository for the real case; the description is researcher-supplied.
- The real fault root cause (tag match vs invalidation broadcast vs ASID/VMID handling) is unknown.
- The gem5 fault is an intentional one-entry TLBI suppression, not a naturally occurring manufacturing defect.
- Cross-chip generality is unproven.
