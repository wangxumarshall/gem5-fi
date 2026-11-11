# MMU Trace Validation Report (2026-11-12)

Frozen binary `a71ce0ca…`. All verdicts come from the real PROP-EVT streams;
no run was accepted on file existence or guest output alone.

## 1. Validator changes in this round

1. **Removed the blanket `Execute => COMPLETE` shortcut** in
   `tools/mmu_formal_validate.py`. It hid missing causal kinds: e.g. M03 R05
   had `missing_kind:tlb_lookup_hit` and no consumer/commit but reported
   COMPLETE. Execute runs now obey the same real-evidence rules.
2. **Fixed the all-digit hex PA comparison** in
   `_cross_dynamic_wrong_commit()`: PROP-EVT `pa=` fields are unprefixed hex
   (`pa=83557000`); the old `_hexval()` parsed them as decimal, so no carrier
   was ever found. It now parses base-16 explicitly.
3. **Fixed `mmu_trace_validate_v3.py` `UnboundLocalError`**: a chain with no
   resolvable W9 ASID/W10 VA now records `ctx=""`, basis `unresolved`.
4. Kept the M02 lineage gate, the M06 state/result/exception separation, and
   the M05 partial-hit proof unchanged. No threshold was relaxed.

## 2. Frozen-binary evidence with real event anchors

- **M05 (TEST-M05-R01B)**: activation ev232 at 0x4010000000
  (`next_table_pa_before=0x81c4d000 -> 0x81c1f000`); alias access at
  0x4010001000 hits the partial entry ev354 (`entry_partial=1,
  pfn=0x81c1f000`), reads the decoy PTE, then a complete hit
  `pfn=0x83545` and `translation_result pa=0x83545000`; guest
  `observed=0x51`. Verdict CONSUMED/FULL/COMPLETE/SDC/FAIL. R02–R04 are the
  same chain with their own context instructions and PFNs.
- **M06 (TEST-M06-R02E)**: the target store is the FIRST translation of
  0x4001100000 (`translation_start mode=Write seq=230633839`), full L0..L3
  walk, M06 activation at ev8482; the prior wrong-path Read is gone. Verdict
  DETECTED_CONTAINED, trace COMPLETE, zero missing edges.
- **M07 (TEST-M07-R02B)**: `LDADDAL` first access is Atomic; activation at
  `checkPermissions64` (ev335) inverts deny→grant; the shared read-only
  value changes (`shared_changed=1`) and the guest result is FAIL. Verdict
  SDC/FAIL, trace COMPLETE.
- **M08 (TEST-M08-R02C)**: the squashed seq no longer burns the one-shot;
  activation moved to live seq 206159145 (ev4438), request PA
  `0x834b6000 -> 0x834b7000`, carried through translation_result/lsu/cache
  and then squashed. Verdict SQUASHED/PASS, trace COMPLETE. R03/R04 have
  the same shape; R01/R05 are SDC with full commit chains.
- **M01 (TEST-M01-R02E)**: canonical ASIDs 220–236; `ctx=R02
  observed=0xaa result=FAIL`; verdict SQUASHED/FAIL, trace COMPLETE.

## 3. Evidence that is NOT accepted

- **M05 R05 (TEST-M05-R05B)**: the guest observed the decoy 0x51, but the
  Execute fetch has no lookup/partial_insert/translation_result events, so
  `TraceCompleteness=PARTIAL/TRACE_INCOMPLETE`. Not accepted as SDC on the
  guest output alone.
- **M02 R02 (TEST-M02-R02B)**: `NO_ELIGIBLE_EVENT`; the M02 refill hook never
  matches because `--mmu_m02_old_pfn 0x83480` != the run's
  `target_pfn=0x834b6`. Not accepted.
- **M07 R03 (TEST-M07-R03B)**: `NO_ELIGIBLE_EVENT`; PROT_NONE decodes as an
  Invalid descriptor (Translation fault), no `permission_eval`.
- **M07 R05**: old run, same Invalid-descriptor path; no distinct M07
  realization.
- **M03/M04**: real evidence but on older binaries, flagged
  `BLOCKED_BINARY` by the frozen-config provenance gate.

## 4. Stale-verdict race (historical)

`TEST-M06-R05B` and `TEST-M08-R03` had verdicts written 17 s / 41 s before
their gzip streams closed (no `sample_manifest.json`, non-runner
invocations). Their complete traces were revalidated into
`phase3/freeze/evidence/reval/`. The formal runner now waits for
`prop_evt.txt.gz` size+mtime stability and retries once on a truncated
read, recording `trace_read_error` if it persists.

## 5. Reproduce

```bash
python3 tools/mmu_formal_validate.py --run-dir runs/TEST-M05-R01B \
  --model M05 --workload W13 --context R01 --target-va 0x4010000000 \
  --target-mode Read --control-run runs/TEST-CTRL-W13-CLOSURE \
  --report-json /tmp/m05.json
python3 tools/mmu_formal_validate.py --run-dir runs/TEST-M06-R02E \
  --model M06 --workload W10 --context R02 --target-va 0x4001100000 \
  --target-mode Write --control-run runs/TEST-CTRL-W10S-COLD \
  --report-json /tmp/m06.json
```
