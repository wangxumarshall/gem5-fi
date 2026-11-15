# Model-ID-Free Confusability Analysis

This is a feature-availability analysis, **not** a trained classifier. No accuracy number is claimed. Ground-truth model IDs are used only to group the evidence below.

## M02 / M04 / M08 (all can produce wrong data or wrong PA)

| Model | RefillPFNChanged | EntryLineage | RequestPAChanged | PTW upstream | SquashObserved | Guest wrong value |
|---|---|---|---|---|---|---|
| M02 | 5/5 | 0/5 | 0/5 | 5/5 | 0/5 | 5/5 |
| M04 | 0/5 | 5/5 | 0/5 | 0/5 | 4/5 | 5/5 |
| M08 | 0/5 | 0/5 | 5/5 | 0/5 | 0/5 | 5/5 |

**Model-free separators when trace events are available:**

- `RefillPFNChanged_SIM=True` and PTW upstream -> M02-like refill-PFN corruption.
- `EntryLineagePresent_SIM=True` with no PTW upstream -> M04-like resident-entry substitution.
- `RequestPAChanged_SIM=True`, `RefillPFNChanged_SIM=False`, `EntryLineagePresent_SIM=False` -> M08-like final-PA corruption.

**Non-separable conditions:** if only `GuestValueMismatch_SW` or the production symptom `wrong data value` is available, these three are indistinguishable. If the trace lacks the refill/lineage/request-PA events, no model-free separation is possible. Production attribution is **UNKNOWN**.

## M01 / M03 (stale vs foreign TLB entry)

| Model | TLBI suppression path | ForeignASIDCandidate | TerminalSquash label | Guest wrong value |
|---|---|---|---|---|
| M01 | 5/5 | 0/5 | 0/5 | 5/5 |
| M03 | 0/5 | 5/5 | 4/5 | 1/5 |

**Model-free separators when trace events are available:**

- `UpstreamPathClass_SIM=TLBI_SUPPRESSION` and no foreign ASID candidate -> M01-like stale-translation path.
- `ForeignASIDCandidate_SIM=True` -> M03-like foreign-ASID false match; M03 may squash (detected) or be consumed by Execute (SDC).

**Non-separable conditions:** with only the production symptom "stale data after correct maintenance", both are possible. Without TLBI match/suppression or candidate-ASID evidence, no model-free separation is possible. Production availability of those events is **UNKNOWN**.

## What is actually production-available

Only generic software symptoms are proven available: wrong data value (with an oracle), unexpected access success, and SIGSEGV/exception class. None of the injector-internal TLB/PTW fields is proven production-observable; they are marked `UNKNOWN_PRODUCTION_OBSERVABILITY` or `SIMULATOR_ONLY`.

## Scope

No classifier was trained. This document only states which features separate the confusable pairs when simulator trace events are available, and where separation is impossible with production signals alone.
