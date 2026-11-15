# MMU Independent Repeatability Validation Plan

**Status: DESIGN ONLY — awaiting researcher approval. No gem5 experiment was started.**

The 40 formal samples are different dynamic contexts, not independent repeats. The A01/A02 retries are not independent repeats either (A02 replaces an interrupted A01).

## Why these 10

Each candidate was checked against the actual frozen trace, manifest and verdict before selection.

| RepeatID | Original | Model | Ctx | Mode | Original terminal | Activation / fault site | Reason |
|---|---|---|---|---|---|---|---|
| REP-MMU-M01-R01-01 | M01-F0-W9-S01-R01 | M01 | R01 | Read | SDC | mmu_fault_arm / retain_l2_complete_invalidation | core stale-translation path (SDC) |
| REP-MMU-M02-R02-01 | M02-F0-W10-S01-R02 | M02 | R02 | Read | SDC | refill_pfn_corrupt / refill_pfn_xor_bit0 | refill PFN corruption path (SDC) |
| REP-MMU-M03-R01-01 | M03-F0-W11-S01-R01 | M03 | R01 | Read | SQUASHED | mmu_fault_activate / tlb_lookup_miss_false_hit | false-ASID hit ending in legal squash (SQUASHED) |
| REP-MMU-M03-R05-01 | M03-F0-W11-S01-R05 | M03 | R05 | Execute | SDC | mmu_fault_activate / tlb_lookup_miss_false_hit | false-ASID hit consumed by Execute (SDC) |
| REP-MMU-M04-R05-01 | M04-F0-W12-S01-R05 | M04 | R05 | Execute | SDC | mmu_fault_activate / tlb_lookup_hit_pfn_subst | resident-entry substitution consumed by ITLB (SDC) |
| REP-MMU-M05-R05-01 | M05-F0-W13-S01-R05 | M05 | R05 | Execute | SDC | mmu_fault_activate / ptw_insertPartialTableEntry | partial walk-cache pointer substitution (SDC) |
| REP-MMU-M06-R02-01 | M06-F0-W10-S01-R02 | M06 | R02 | Write | DETECTED_CONTAINED | mmu_fault_activate / ptw_doLongDescriptor_valid_clear | invalid leaf descriptor detected on a store (W10S) |
| REP-MMU-M07-R01-01 | M07-F0-W14-S01-R01 | M07 | R01 | Write | SDC | mmu_fault_activate / mmu_checkPermissions64 | permission inversion: unauthorized RO write (SDC) |
| REP-MMU-M07-R05-01 | M07-F0-W14-S01-R05 | M07 | R05 | Execute | SDC | mmu_fault_activate / mmu_checkPermissions64 | permission inversion: unauthorized XN execute (SDC) |
| REP-MMU-M08-R01-01 | M08-F0-W10-S01-R01 | M08 | R01 | Read | SDC | mmu_fault_activate / mmu_translate_set_paddr | final PA materialization corruption (SDC) |

## Execution requirements

1. Use an independent gem5 process per repeat; max 4 concurrent.
2. Use a new `RepeatID`/`AttemptID` and a new output path under `repeatability/<RepeatID>/`; never overwrite the original 40 SampleRunIDs.
3. Use the same frozen binary (`b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`), workload binary, rcS and fault parameters recorded per row.
4. Exactly one fault source per run; record the full `prop_evt.txt.gz` trace.
5. Compare each repeat event-by-event with its original sample.

## Comparison metrics (all 8 must be reported)

1. Fault activation consistent (kind, fault site, field).
2. Target event consistent (ordinal/condition).
3. Fault state consistent (before/after values).
4. EntryID/Generation identity relation as specified.
5. VA/PA change consistent.
6. Downstream consumer consistent.
7. TerminalState consistent.
8. PropagationSignature consistent.

Exact EventIDs/ticks are expected to match under a fresh deterministic restore; a mismatch is investigated and reported, not silently accepted.

## Per-repeat assertions

### REP-MMU-M01-R01-01 (repeat of M01-F0-W9-S01-R01)

- Fault parameters: `{"mmu_fault_model": "M01", "mmu_fault_enable": "true", "mmu_target_va": "", "mmu_target_n": "", "mmu_eligible_event_index": "", "mmu_target_mode": "", "mmu_target_walk_level": "", "mmu_m02_dram_lo": "", "mmu_m02_dram_hi": "", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{}`
- Entry identity relation: retained L2 entry valid=true, same entry_id/generation survives the matching TLBI and is consumed afterwards
- Expected consumer: LSU Read; terminal: SDC

### REP-MMU-M02-R02-01 (repeat of M02-F0-W10-S01-R02)

- Fault parameters: `{"mmu_fault_model": "M02", "mmu_fault_enable": "true", "mmu_target_va": "", "mmu_target_n": "", "mmu_eligible_event_index": "", "mmu_target_mode": "", "mmu_target_walk_level": "", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"old_pfn": "834b2", "new_pfn": "834b3", "old_pa": "834b2000", "new_pa": "834b3000"}`
- Entry identity relation: refill PFN changes by XOR bit0 (old_pfn 0x834b2 -> new_pfn 0x834b3) and the inserted entry is later hit
- Expected consumer: LSU Read; terminal: SDC

### REP-MMU-M03-R01-01 (repeat of M03-F0-W11-S01-R01)

- Fault parameters: `{"mmu_fault_model": "M03", "mmu_fault_enable": "true", "mmu_target_va": "0x4004000000", "mmu_target_n": "12", "mmu_eligible_event_index": "1", "mmu_target_mode": "Read", "mmu_target_walk_level": "", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"candidate_asid": "236", "candidate_pfn": "0x83543"}`
- Entry identity relation: candidate_asid != request ASID; candidate entry/generation selected on a miss; R01 ends in squash before arch update
- Expected consumer: LSU Read; terminal: SQUASHED

### REP-MMU-M03-R05-01 (repeat of M03-F0-W11-S01-R05)

- Fault parameters: `{"mmu_fault_model": "M03", "mmu_fault_enable": "true", "mmu_target_va": "0x4005000000", "mmu_target_n": "12", "mmu_eligible_event_index": "1", "mmu_target_mode": "Execute", "mmu_target_walk_level": "", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"candidate_asid": "236", "candidate_pfn": "0x83543"}`
- Entry identity relation: candidate_asid != request ASID; candidate entry/generation selected on a miss; R01 ends in squash before arch update
- Expected consumer: Execute (IFU/LSU); terminal: SDC

### REP-MMU-M04-R05-01 (repeat of M04-F0-W12-S01-R05)

- Fault parameters: `{"mmu_fault_model": "M04", "mmu_fault_enable": "true", "mmu_target_va": "0x4008000000", "mmu_target_n": "12", "mmu_eligible_event_index": "1", "mmu_target_mode": "Execute", "mmu_target_walk_level": "", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"old_pfn": "0x83559", "new_pfn": "0x8353c", "old_pa": "0x83559000", "new_pa": "0x8353c000", "candidate_asid": "234", "candidate_pfn": "0x8353c"}`
- Entry identity relation: resident entry_id/generation stays valid; substituted PFN is a different mapped page of the same size
- Expected consumer: Execute (IFU/LSU); terminal: SDC

### REP-MMU-M05-R05-01 (repeat of M05-F0-W13-S01-R05)

- Fault parameters: `{"mmu_fault_model": "M05", "mmu_fault_enable": "true", "mmu_target_va": "0x4010000000", "mmu_target_n": "21", "mmu_eligible_event_index": "1", "mmu_target_mode": "Execute", "mmu_target_walk_level": "2", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"next_table_pa_before": "0x81d28000", "next_table_pa_after": "0x81ce7000"}`
- Entry identity relation: partial entry next_table_pa changes; later partial hit resumes at the decoy L3 table
- Expected consumer: Execute (IFU/LSU); terminal: SDC

### REP-MMU-M06-R02-01 (repeat of M06-F0-W10-S01-R02)

- Fault parameters: `{"mmu_fault_model": "M06", "mmu_fault_enable": "true", "mmu_target_va": "0x4001100000", "mmu_target_n": "12", "mmu_eligible_event_index": "1", "mmu_target_mode": "Write", "mmu_target_walk_level": "3", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"descriptor_before": "0x6000008352cfc3", "descriptor_after": "0x6000008352cfc2"}`
- Entry identity relation: descriptor bits[1:0] 0b11 -> 0b10 on the fetched leaf; PTE memory is not written
- Expected consumer: LSU Write; terminal: DETECTED_CONTAINED

### REP-MMU-M07-R01-01 (repeat of M07-F0-W14-S01-R01)

- Fault parameters: `{"mmu_fault_model": "M07", "mmu_fault_enable": "true", "mmu_target_va": "0x400d000000", "mmu_target_n": "12", "mmu_eligible_event_index": "1", "mmu_target_mode": "Write", "mmu_target_walk_level": "", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"permission_before": "false", "permission_after": "true"}`
- Entry identity relation: same VA/PA/PFN; permission_before=false -> permission_after=true at the permission checker
- Expected consumer: LSU Write; terminal: SDC

### REP-MMU-M07-R05-01 (repeat of M07-F0-W14-S01-R05)

- Fault parameters: `{"mmu_fault_model": "M07", "mmu_fault_enable": "true", "mmu_target_va": "0x400d600180", "mmu_target_n": "12", "mmu_eligible_event_index": "1", "mmu_target_mode": "Execute", "mmu_target_walk_level": "", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"permission_before": "false", "permission_after": "true"}`
- Entry identity relation: same VA/PA/PFN; permission_before=false -> permission_after=true at the permission checker
- Expected consumer: Execute (IFU/LSU); terminal: SDC

### REP-MMU-M08-R01-01 (repeat of M08-F0-W10-S01-R01)

- Fault parameters: `{"mmu_fault_model": "M08", "mmu_fault_enable": "true", "mmu_target_va": "0x4001000000", "mmu_target_n": "12", "mmu_eligible_event_index": "1", "mmu_target_mode": "Read", "mmu_target_walk_level": "", "mmu_m02_dram_lo": "0x80000000", "mmu_m02_dram_hi": "0x100000000", "mmu_m08_pa_xor_mask": "0x1000", "seed": "N/A_DETERMINISTIC", "seed_policy": "DETERMINISTIC"}`
- Expected fault state: `{"old_pfn": "0x834b2", "new_pfn": "0x834b2", "old_pa": "0x834b2000", "new_pa": "0x834b3000", "request_pa_before": "0x834b2000", "request_pa_after": "0x834b3000"}`
- Entry identity relation: TLB entry/PFN unchanged; Request PA changes by XOR 0x1000
- Expected consumer: LSU Read; terminal: SDC

## Stop condition

This round stops after the plan is delivered. No repeat is started until the researcher approves.
