# LSU — 12-model progress after v3.2.4 (2026-11-07)

Status vocabulary: DESIGNED / SOURCE_AUDITED / IMPLEMENTED / COMPILED /
UNIT_TESTED / PILOT_RUN / PROPAGATION_VERIFIED.

| # | Model | Status after v3.2.4 | Evidence |
|---|---|---|---|
| 1 | A01 (AGU address bit3) | PILOT_RUN (v3.2.1; terminal re-judged) | A01-R01 CRASH, R02/R04/R05 MASKED, R03 SQUASHED |
| 2 | A03 (AGU stuck-at) | PILOT_RUN (v3.2.1) | A03-R01..R05 CRASH |
| 3 | FW02 (forward suppression) | PILOT_RUN | v3.2.4 R01/R05 SQUASHED; R03/R04 MASKED; R02 CRASH |
| 4 | SQ01 (store data bit3) | PILOT_RUN (store writeback + memory write; no consumer) | `LSU_v3.2.4_SQ01_Propagation.md` |
| 5 | DA04 (byte-enable bit0) | **PROPAGATION_VERIFIED** | `DA04_Implementation_v3.2.4.md`, `pilots_v3_2_4/DA04_PILOTS.md` |
| 6 | LP01 (load response data) | SOURCE_AUDITED / IMPLEMENTED / COMPILED (pilots next) | `CHAOSL1DForward/README_LP01_AUDIT.md` |
| 7 | MD04 (load-store violation suppress) | DESIGNED | v3.2.3 audit |
| 8 | FW05 (wrong-source forwarding) | DESIGNED | v3.2.3 audit |
| 9 | SQ03 (canWB early writeback) | DESIGNED | v3.2.3 audit |
| 10 | SP05 (store completion suppression) | DESIGNED | v3.2.3 audit |
| 11 | LQ04 (LQ entry invalidation) | DESIGNED (HIGH-RISK) | v3.2.3 audit |
| 12 | RP01 (replay suppression) | DESIGNED | v3.2.3 audit |

Implementation order remains: SQ01 (done) -> DA04 (done) -> LP01 (started)
-> MD04 -> FW05 -> SQ03 -> SP05 -> LQ04 -> RP01.
