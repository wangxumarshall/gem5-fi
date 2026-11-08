# LSU v3.2.6 — remaining issues

1. **LP01 has no SDC pilot.** All five v3.2.6 pilots are MASKED; 45/0/3/0/3
   stale-source operands are now diagnostics, not edges.
2. **DA04 R01–R03 were not rerun.** The load-side writeback hash change does
   not alter their injection path; no new traces are claimed for them.
3. **MD04 has no SDC pilot.** Three pilots have traced chains (R02 6, R03
   259, R05 2 consumers); R01/R04 are squashed.
4. **MD04 definition correction.** The Excel target field
   `possibleLoadViolation` is a load/load flag; W7’s store→load violation is
   the `M5PanicFault` detection. The implementation and audit use the latter
   and document the discrepancy.
5. **W7 eligible count.** Only six same-address/8-byte-store alias events
   exist; the five pilots use ordinals 1–5 (including two 16-byte LDP loads
   that cover the 8-byte store). R05 is a late-bound writeback (response
   consumed before the violation check).
6. **Warm-up/ROI not frozen.** LP01 R05 clinical ordinal 14 is historical;
   formal selection must be frozen separately and no post-hoc consumer
   filtering is approved.
7. **SE VA alias matching** remains VA-based; a different VA mapping to the
   same memory location is not matched.
8. **Vector consumers** have no scalar hash; they are explicit nulls, not
   failures.
9. **No formal 60-sample run; no multi-cell grid.**
10. **FW05** is audit-only; no implementation/pilots.
