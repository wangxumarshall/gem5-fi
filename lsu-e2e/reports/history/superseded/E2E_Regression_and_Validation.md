# E2E regression and validation

* Instrumented workload variants built: **40**; native golden checksums all equal the frozen When-v2 goldens (build script exits on any mismatch).
* Paired controls: **60/60** COMPLETED with oracle pass and zero injections.
* Fault runs with a real injection ledger: **180/180**.
* Ordinal identity matches: **180/180**.
* SDC runs with a continuous software hash chain: **108/108**.
* E2E complete: **180/180**.

## Instrumentation non-invasiveness

* The marker is four `mov x28` ALU instructions. It performs no load/store/syscall and therefore cannot enter an LSU injector's eligible stream; `-ffixed-x28` prevents the compiler from using the marker register for program state.
* Control eligible counts: **33/60 identical** to the frozen census; the remaining cells differ (mostly C05). The markers are ALU-only, but in speculative contexts they enlarge the speculation window and change how many squashed loads are counted; a few boundary events come from compiler register allocation. No old ordinal was reused: every control, eligible census, ordinal and fault was re-run under the new ELFs; the full comparison is `E2E_Eligible_Census_Comparison.csv`.
* Control and fault checksums are read only from stdout; the marker stream is read only from the commit trace.

## Evidence limits (not hidden)

* Software markers are observers. They are excluded from the application-consumer graph so a load is never claimed consumed just because the observer read it.
* For watchdog runs the commit trace can lose its gzip tail; the injector watchdog record's `last_commit_dyn_seq`/`last_commit_tick` is used as the authoritative progress witness, and the truncation is recorded per run.
* SE mode produced no natural application crash and no kernel panic. No assertion or panic was fabricated.
* Full-system assets are present on 0101, but the 180 SE samples are not replaced by FS results.

## Historical integrity

* Frozen commit `e8759972a8e65856b540629a0defdd7e744ff921`, tag `LSU_When_v2_FINAL_FROZEN`, and the frozen result/archive files were not edited.
* The new source worktree is on branch `e2e-causal-20261117`.
