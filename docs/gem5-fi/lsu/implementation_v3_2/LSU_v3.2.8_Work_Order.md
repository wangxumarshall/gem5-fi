# LSU v3.2.8 work order (researcher, 2026-11-08)

Authoritative scope for this round. Base: v3.2.7 (`f26218f8`).
No 60-sample formal run.

## A. FW05 formal configuration freeze

- Final name: **Wrong-Source Store-to-Load Forwarding**.
- Mechanism: the load normally takes the youngest matching forwarding store;
  the fault takes an older store that also satisfies the forwarding
  conditions. This is wrong-source selection, **not** multi-store splicing.
- Hook: `LSQUnit::read()`, `CHAOSLSQFwd::maybeSubstituteFW05()`,
  `fw05_rules.hh`. Do not widen the already-verified definition.
- `fw05_forward` is approved as FW05's only formal workload. The historical
  W8 `alignment` configuration and the five v3.2.7 pilots are retained.
- Archive the workload completely: source, input/init, generator, compile
  script/args, dependencies, binary, gem5 config, pilot script, golden and
  checksum method, README.
- Verify the full workload SHA256; the manifests record prefix
  `0cf40509...`. Compare R01–R05 individually; if they differ, record it.
  If the original cannot be recovered, mark it missing; never substitute a
  similar new file.
- Run no-fault baselines for R01–R05 with the same workload, seed,
  initialization and oracle method; record golden/actual/exit/SHAs.
  Do not copy one sample's golden to another without checking.
- Publish Excel v3.2.3 (or next free version), changing only the five FW05
  rows: FaultModelName, TargetUnit, TargetSubunit, TargetFunction,
  TargetField, FaultAction, WorkloadName, WorkloadPath, WorkloadSHA256,
  Oracle, PilotStatus. Keep SampleRunID/RunID/SubTaskID/Seed; do not
  change the other 11 models; add a revision record explaining the
  alignment → fw05_forward change and the retained history. Do **not** set
  all 60 ConfigFrozen=YES.

## B. SQ03 safety hardening and five pilots

- Frozen model: **Premature Store Writeback Permission**
  (`SQEntry::_canWB`, `LSQUnit::executeStore()`); do not redesign it.
- Audit `max_faults` semantics. If 0 means unlimited, SQ03 must not use it.
  Add a hard per-sample cap, one-shot protection, injection-count assert,
  in-simulator watchdog and external timeout. Preserve partial trace/logs
  on HANG/TIMEOUT; never report a timeout as MASKED.
- Five pilots with the original SampleRunID/Seed. Record store identity
  (seq, PC, addr, size, SQ idx/gen), canWB before/after, storesToWB
  before/after, injection tick, writeback tick, commit result, later
  load/consumer relation, terminal, oracle, HANG/replay/coverage status.
- Prove: target store exists and meets the condition; canWB changes;
  counters stay consistent; one injection only; no other store corrupted;
  later events linked by real dynamic identity. Do not claim injection from
  a hook call alone.
- Add SQ03 no-fault baselines with the same seed/workload; compare writeback
  timing and oracle. Time shift alone is not SDC.
- Build a real SQ03 trace: allocation → SQ entry → writeback permission →
  injection → writeback → completion → later load/consumer → register
  writeback → commit → oracle. Do not fabricate missing events; judge
  RecordIntegrity / TraceCompleteness / PropagationCoverage separately.
- The five pilots must all run; SDC is not required. Keep MASKED/SQUASHED/
  CRASH/SDC honestly.

## C. Platform and delivery

- Use an independent branch; keep all historical pilots/traces; no
  `git clean -fd`; no blanket `git add`; do not overwrite the v3.2.7
  package; record commits and the final binary SHA256; check Excel/CSV/
  manifest/trace consistency.
- Update `MODEL_STATUS_MATRIX.csv` only from real evidence. FW05 must state
  workload frozen/archived/baseline done/five pilots verified. SQ03 only
  after safety + five pilots + propagation adjudication.
- Package `LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip` with the
  A/B/C contents listed in the work order, README, unresolved issues and
  the final answers.
- After this round, continue SP05.
