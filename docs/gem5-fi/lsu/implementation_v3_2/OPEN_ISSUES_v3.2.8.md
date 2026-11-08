# Open issues — LSU v3.2.8

These are unresolved at the end of this round. None is silently converted into a
pass or a MASKED result.

1. **SQ03 has no load consumer.** All five pilots stop at
   `injection → store_writeback → store_mem_write → sq03_complete`;
   `consumer_instructions=0`. The time shift (R01 −9,240 ticks, R05 −385 ticks)
   is real but does not reach a register/consumer/application observer. SQ03
   therefore remains `PROPAGATION_VERIFIED=0`. The next step needs a workload
   where a later load reads the target store (or an ordering-sensitive
   consumer), not a re-run of `sq_drain`.
2. **No SQ03 SDC pilot.** All five applications pass the oracle. Terminal
   MASKED is correct; it is not evidence that the fault is harmless in general.
3. **FW05 SDC evidence is model-level, not formal-60.** Four SDCs are
   reproducible on the final binary, but this is a five-pilot result. The
   60-sample formal run has not started.
4. **Global Warm-up/ROI not frozen.** `ConfigFrozen` is `NO` for all 60 rows.
   Only the FW05 model-specific configuration is frozen.
5. **Host-load-sensitive external timeouts.** During the final-binary recheck,
   the batch wrapper's 300 s timeout fired while the host load average was
   > 50; standalone re-runs of the same commands exited 0 in ~3.3 s. This is a
   host scheduling effect, not a simulator hang, but external timeouts must be
   paired with load control for formal batches.
6. **SQ03 watchdog is tick-based only.** A host stall is covered only by the
   external timeout (see item 5). A livelock that still advances ticks is
   covered by the watchdog; a process frozen without tick advance is not.
7. **SP05 is definition-only.** The definition and entry-keyed one-shot rules
   plus unit test exist; the live `completeStore` hook, trace, watchdog and
   pilots are the next round. `IMPLEMENTED=0` is intentional.
8. **Large traces are not in Git.** Raw JSONL/gzip traces (188 MB per SQ03
   pilot, 34 MB per FW05 pilot) are kept on disk and in the package zip; Git
   keeps manifests, logs and checksums (`pilots_v3_2_8/SQ03_TRACE_STORAGE.md`).
9. **Rebuild byte-identity is environment-dependent.** The archived FW05
   binary is the exact pilot binary. A rebuild reproduces the checksum in this
   environment; build-id bytes can differ on another toolchain. The archived
   binary SHA is authoritative.
10. **LQ04 and RP01 remain audited-only.** Unchanged from v3.2.7; no code or
    pilots in this round.
11. **`tests/test_claim_concurrency.py` cannot run here.** Its `check` fixture
    comes from the `pytest-check` plugin, which is not installed in this
    environment (5 setup errors). The file is unchanged since `977d7ced` and is
    unrelated to v3.2.8. The rest of the suite passes (31 passed).
