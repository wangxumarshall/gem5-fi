# Agent C — SQ01/SQ03/SP05 Final Comparison (LSU v3.3.3 closure round)

**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Role:** Agent C (SQ specialty), read-only Phase-1 audit.
**Authoritative input:** `audit_v3_3_3/README_GROUND_TRUTH.md` (read in full; §1–§8 followed).
**Constraint compliance:** no source/config/workload/tool/Excel/`audit_v3_3_2/` file was modified; no gem5 run, no pilot. Only this report was written. Scratch analysis was done in `/tmp` (read-only parsing of existing traces).

---

## 0. Header

### 0.1 Scope

Compare the frozen originals **W3 `sq_drain`** (SQ01/SQ03) and **W6 `store_path`** (SP05) against the candidate **`sq_reload_v3212`**, on raw evidence:

1. SQ01 — SQ data byte0 bit3 flip at `lsq_write_sq_entry` → store-memory → L1D reload → register/consumer chain.
2. SQ03 — premature `_canWB` at `executeStore` (+ paired `storesToWB`) → early drain/visibility vs architectural commit.
3. SP05 — premature `completeStore` at `writebackStores` → skipped cache write → stale reload.
4. Provenance: dossier binary `d3807fbe` vs matrix binary `070d68a6`; recomputed ELF/golden SHAs; workbook baseline row.
5. Per-model recommendation and Excel/SampleRunID/Seed impact.

### 0.2 Binaries and identities verified in this audit

| Item | Value | Verified by |
|---|---|---|
| Current live binary | `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca` | `sha256sum build/ARM/gem5.opt` (ran now) |
| Git HEAD / branch | `3097ad82e7066f18fc35cf64dcb612a05c1fc021` / `lsu-v3.3.1-context-workload-20261111` | `git rev-parse HEAD`, `git branch --show-current` |
| Matrix-run binary (all 30 SQ/SP run dirs) | `070d68a6…5f5ca` | `summary.json:binary_sha` and `manifest.json:gem5.binary_sha256` of all 30 dirs |
| Dossier/probe binary (`sq_workload/evidence/**`) | `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2` | `manifest.json:gem5.binary_sha256` of all 24 evidence dirs; also `audit_v3_3_1/report/PROVENANCE.md:9` |
| Config | `configs/se/lsu_proxy.py`, SHA `01f912de3388aaf420aa69d5dd55098ddfb97851faf0269a6b009fcc389bf6e5` | `sha256sum` live + every manifest (both binaries) |
| `sq_reload_v3212` ELF | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` | `sha256sum` (recomputed) |
| `sq_reload_v3212.c` | `abbb0dcd3c22666a9b0e05a80743c32256d415e33a089b5755269d3db0614133` | `sha256sum` |
| `sq_reload_v3212.golden` (file / content) | `24e3f93c7da83881513fd0c336616545c92f330d55400d3d32b8bad24010540d` / `7df5034c23f3e703` | `sha256sum`, `cat` |
| `sq_reload_v3212.host.out` | `checksum=0x7df5034c23f3e703` | `cat` |
| W3 `sq_drain` ELF | `d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f` | `sha256sum` |
| W3 golden | `ba3b3185e541ad03` | `cat sq_drain.golden` |
| W6 `store_path` ELF | `906b3798adc618f388c1988389dd67140afeba6c706456fdeebdd524dc55fbcf` | `sha256sum` |
| W6 golden (file content) | `checksum=0x2543a2a60de01795` | `cat store_path.golden` |

All recomputed SHAs match `audit_v3_3_2/sq_workload/LSU_SQ_Workload_Decision.md` §0, `audit_v3_3_2/LSU_Workload_Oracle_Final_Audit.csv`, and sheet 5's W3/W6 rows.

Static symbols (`readelf -sW`): `buf` @ `0x491990`, 2048 B (`sq_reload_v3212`); `a.0` @ `0x491990`, 65536 B (`sq_drain`) / 32768 B (`store_path`).

### 0.3 Files inspected (all read-only)

- Runs: `audit_v3_3_2/runs/{SQ01,SQ03,SP05}-R{01..05}-{fault,control}/` (`manifest.json`, `summary.json`, `command.txt`, `oracle.log`, `lsq_fwd_injections.log`, `trace_v31.jsonl`).
- Probe evidence: `audit_v3_3_2/sq_workload/evidence/{contexts/*,original/*,establish/*}/` (same file set) + `contexts_summary.csv`, `contexts_extracted.jsonl`, `original_comparison.json`, `run_commands.txt`, `static_evidence.txt`.
- Tables: `audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv`, `audit_v3_3_2/roi/LSU_60Context_ROI_Percentile_Mapping.csv`, `audit_v3_3_2/roi/LSU_60Context_Distinctness_Audit.csv`, `audit_v3_3_2/LSU_60Context_Final_Readiness_Matrix.csv`, `audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final.csv`, `audit_v3_3_2/LSU_Diagnostic_Features_Final.csv`, `audit_v3_3_2/LSU_12Model_Source_Hook_Audit.csv`.
- Dossier: `audit_v3_3_2/sq_workload/LSU_SQ_Workload_Decision.md`.
- Source: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{cc,hh}`, `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/{CHAOSLSQFwd.cc,sp05_rules.hh}`, `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`.
- Workloads/Excel: `docs/gem5-fi/lsu/implementation_v3_2/workloads/*`, `.../excel/60_SAMPLE_MATRIX.csv`, `.../excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`.
- Tools: `tools/lsu_propagation_audit.py`, `tools/lsu_v332_matrix.py`, `tools/lsu_v332_supplement.py`.

### 0.4 Reproduction commands used (no gem5)

```
sha256sum build/ARM/gem5.opt
sha256sum docs/gem5-fi/lsu/implementation_v3_2/workloads/{sq_reload_v3212,sq_reload_v3212.c,sq_reload_v3212.golden,sq_drain,sq_drain.c,store_path,store_path.c}
objdump -d --disassemble=main <workload>
readelf -sW <workload> | grep ' buf$\| a\.0$'
python3  # read-only JSONL/CSV/xlsx parsing of the files listed above
```

---

## 1. SQ01 — store-data corruption (`lsq_write_sq_entry`, byte0 ^ 0x08)

### 1.1 Static evidence (real `objdump -d --disassemble=main`)

`sq_reload_v3212` main loop (`docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212`):

```
400538: sxtw  x0, w7
40053c: str   x6, [x8, x0, lsl #3]      ; buf[i] = v               <- fault store
400540: dmb   ish                       ; forces SQ drain + no forward
400544: ldr   x4, [x8, x0, lsl #3]      ; same-address reload (L1D)
400550: lsr   x3, x4, x0                ; consumer: byte-wise FNV-1a
40056c: cmp   x4, x6                    ; r == v ?
400570: b.ne  4005a4 <main+0xb4>        ; corrupt path (control divergence)
400574: add   x1, x1, #1               ; equal path
400584: b.ne  400538 <main+0x48>        ; 128 iterations (cmp w7,#0x80)
```

The fault hook is `CHAOSLSQFwd::maybeCorruptStoreData` (`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:935-974`): it reads `old_byte = data[0]`, computes `new_byte = old_byte ^ 0x08`, writes `data[0] = new_byte`, then calls `noteStoreDataInjection(...)`. Nothing else is touched.

W3 `sq_drain` (`main`): stores at `0x400530` (`strb w0,[x1]`), `0x400538` (`strb w3,[x1,#1]`), `0x400540` (`stur w2,[x1,#-4]`), `0x400560` (`strb w0,[x1],#16`); the only readback is the single end-of-program bulk read at `0x400590` (`ldrb w2,[x5],#1`). There is **no per-store reload consumer** in W3, which is why the original run is structurally incapable of showing a chain.

### 1.2 Dynamic evidence — five contexts (raw traces)

Source of truth per run: `audit_v3_3_2/runs/SQ01-R0<k>-fault/trace_v31.jsonl`, `oracle.log`, `lsq_fwd_injections.log`, `manifest.json`. Ordinal confirmed in `command.txt` (`--lsqfwd_event_ordinal`).

| Ctx | Ordinal | Store seq | Store PC | Store VA | SQ idx/gen | Inject tick | Byte old→new | mem_write_hash (store_writeback & store_mem_write) | Reload seq / LQ idx | Reload req → resp tick | reload_data_hash (=mem_response) | Consumer seq / PC | Consumer commit tick | consumer_hash | Oracle (got) | Terminal |
|---|---:|---:|---|---|---:|---:|---|---|---|---:|---|---:|---:|---|---|---|
| R01 | 1018 | 13328 | 0x40053c | 0x4919f0 | 956/1306 | 16372510 | 0x6d→0x65 | `21d267b2c8b57721` (16377515) | 13330 / 759 | 16380210 → 16380980 | `21d267b2c8b57721` | 13333 / 0x400550 | 16382135 | `21d267b2c8b57721` | FAIL `7927a4e45a3271dc` | SDC |
| R02 | 1044 | 15122 | 0x40053c | 0x491ac0 | 982/1332 | 17001600 | 0x87→0x8f | `d4e59c4d90e5da05` (wb 17006605 / memw 17012765) | 15124 / 785 | 17015460 → 17016230 | `d4e59c4d90e5da05` | 15127 / 0x400550 | 17017385 | `d4e59c4d90e5da05` | FAIL `580f7a29038389ac` | SDC |
| R03 | 1069 | 16847 | 0x40053c | 0x491b88 | 1007/1357 | 17488240 | 0xa0→0xa8 | `336b5d682cbd2549` (17493245) | 16849 / 810 | 17495940 → 17496710 | `336b5d682cbd2549` | 16852 / 0x400550 | 17497865 | `336b5d682cbd2549` | FAIL `a372640bc071881c` | SDC |
| R04 | 1095 | 18641 | 0x40053c | 0x491c58 | 1033/1383 | 17987200 | 0xba→0xb2 | `e0a15931b120dcb5` (17992205) | 18643 / 836 | 17994900 → 17995670 | `e0a15931b120dcb5` | 18646 / 0x400550 | 17996825 | `e0a15931b120dcb5` | FAIL `406db02f8dc2912c` | SDC |
| R05 | 1121 | 20435 | 0x40053c | 0x491d28 | 1059/1409 | 18628225 | 0xd4→0xdc | `4cd11d8e73a6f3e1` (18633230) | 20437 / 862 | 18635925 → 18636695 | `4cd11d8e73a6f3e1` | 20440 / 0x400550 | 18637850 | `4cd11d8e73a6f3e1` | FAIL `1aea82f645a9ac9c` | SDC |

All 15 **fault** runs are `trace_completeness=COMPLETE`, `record_integrity=VALID`, `injection_count=1`, exit 0 (`summary.json`). All 15 **control** runs exit 0 with `injection_count=0` and `oracle=true` (`ORACLE_PASS` in `oracle.log`); their summary terminal is `UNRESOLVED/NO_INJECTION_EVENT, observed_terminal=MASKED`.

**Chain verdict = COMPLETE_CHAIN in 5/5** — verified directly from the `sq01_chain` record, not from a summary table:

- R01: `record=sq01_chain;...;mem_write_hash=21d267b2c8b57721;reload_seq=13330;reload_data_hash=21d267b2c8b57721;consumer_seq=13333;consumer_hash=21d267b2c8b57721;chain_verdict=COMPLETE_CHAIN`
- R02: `...;d4e59c4d90e5da05;...;COMPLETE_CHAIN`
- R03: `...;336b5d682cbd2549;...`
- R04: `...;e0a15931b120dcb5;...`
- R05: `...;4cd11d8e73a6f3e1;...`

Independently corroborated by the raw hop records (not only the consolidated node): `store_writeback` (`data_fnv=…`), `store_mem_write` (`packet_data_fnv=…`), `memory_response` (`data_fnv=…`), `register_writeback` (`payload_fnv=…`, `value_matches_payload=1`), and `consumer_commit` at seq 13333:

```
{"event_type":"consumer_commit","dyn_inst_seq":13333,"timestamp":16382135,
 "detail":"class=int;src_idx=0;pc=400550;source_event_id=5083;
 source_value_hash=21d267b2c8b57721;consumer_input_value=7f7d6b7e71787b65;
 consumer_input_fnv=21d267b2c8b57721;consumer_input_matches_source=1;..."}
```

### 1.3 Is the reload an L1D read after the store wrote memory (not a same-cycle SQ forward)?

Yes, in 5/5:

- `memory_request` for the reload has `sq_entry_id=-1` and `store_not_written_yet=0` with `last_send_before_store_write=0`; e.g. R01: `...;store_write_tick=16377515;last_send_before_store_write=0;store_not_written_yet=0;overwritten=0;lq_entry_id=759;sq_entry_id=-1` at tick 16380210.
- `memory_response` is emitted from unit `L1D` (`"unit":"L1D","sub_unit":"response"`), after the send (R01 16380980 > 16380210).
- **No `forwarding_decision` exists for any reload seq** (13330/15124/16849/18643/20437). The 11 `forwarding_decision` records in each trace belong to unrelated loads (`load_seq` = 238, 239, 5902, 9930, 10988, 12052, 21914, 21920, 22014, 22075, 23669), none equal to a reload seq.
- The store itself committed before the cache write and the reload: R01 commit 16376745 < store_mem_write 16377515 < reload send 16380210.
- The `dmb ish` + program order mechanism is documented in `sq_reload_v3212.c`: the barrier only executes at the commit head and only when `iewStage->hasStoresToWB()` is false, so the freed SQ entry cannot match in `LSQUnit::read()`.

### 1.4 Is the injected byte the only divergence, and is the oracle sensitive?

**Yes.** The workload is deterministic and its expected value can be reconstructed from source: `v_i = 0x73715f72656c6f61 + i * 0x0101010101010101`, lane `i = (va − 0x491990)/8`. Using standard FNV-1a-64 over the 8 payload bytes (verified against the tracer's own hashes):

| Ctx | i | Unfaulted value (`v_hex`) | Unfaulted hash | Injected payload (`store_mem_write.packet_data_hex`) | Byte diffs | XOR | Injected hash | Oracle got |
|---|---:|---|---|---|---|---|---|---|
| R01 | 12 | `6d7b78717e6b7d7f` | `b6180e0c195fd2e9` | `657b78717e6b7d7f` | 1 (byte 0) | `0x08` | `21d267b2c8b57721` | `7927a4e45a3271dc` |
| R02 | 38 | `8795928b98859799` | `9f995d89be67e92d` | `8f95928b98859799` | 1 (byte 0) | `0x08` | `d4e59c4d90e5da05` | `580f7a29038389ac` |
| R03 | 63 | `a0aeaba4b19eb0b2` | `fde383c67ac034f1` | `a8aeaba4b19eb0b2` | 1 (byte 0) | `0x08` | `336b5d682cbd2549` | `a372640bc071881c` |
| R04 | 89 | `bac8c5becbb8cacc` | `aa2be3d3d60e3c9d` | `b2c8c5becbb8cacc` | 1 (byte 0) | `0x08` | `e0a15931b120dcb5` | `406db02f8dc2912c` |
| R05 | 115 | `d4e2dfd8e5d2e4e6` | `c7d78aff5e06edf9` | `dce2dfd8e5d2e4e6` | 1 (byte 0) | `0x08` | `4cd11d8e73a6f3e1` | `1aea82f645a9ac9c` |

`store_mem_write` also records `enabled_written=1;disabled_unchanged=1;lane0_packet=0x65;lane0_before=0x0;lane0_after=0x65` (R01) — only the enabled lane changed. The **oracle is sensitive: FAIL 5/5**, with five distinct, reproducible checksums (`oracle.log` per run). The five `got` checksums differ from each other because the corrupt `r ^ v` path is taken at a different lane/iteration in each context.

A strong cross-check: the SQ03 (unmodified-data) reload hashes equal the SQ01 *unfaulted* hashes above (`b618…`, `9f99…`, `fde3…`, `aa2b…`, `c7d7…`), confirming both that the source-derived expected values are right and that the only SQ01 change is the injected bit.

### 1.5 Are the five contexts distinct dynamic stores?

Yes — per model, 5/5 unique `(store_seq, store_addr, sq_idx, entry_generation, inject_tick, reload lq_idx)`:

| Ctx | Ordinal | store seq | addr | sq idx/gen | inject tick | reload lq idx |
|---|---:|---:|---|---:|---:|---:|
| R01 | 1018 | 13328 | 0x4919f0 | 956/1306 | 16372510 | 759 |
| R02 | 1044 | 15122 | 0x491ac0 | 982/1332 | 17001600 | 785 |
| R03 | 1069 | 16847 | 0x491b88 | 1007/1357 | 17488240 | 810 |
| R04 | 1095 | 18641 | 0x491c58 | 1033/1383 | 17987200 | 836 |
| R05 | 1121 | 20435 | 0x491d28 | 1059/1409 | 18628225 | 862 |

The ordinal→store mapping is the frozen percentile rule `k = ceil(p·128) = 13, 39, 64, 90, 116`, absolute ordinal `K* + (k−1)` with `K* = 1006`, giving 1018/1044/1069/1095/1121; each ordinal is visible in the run command (`--lsqfwd_event_ordinal N`) and in `lsq_fwd_injections.log` (`Site: lsq_write_sq_entry, seq: …`).

**Caveat (must be in the paper):** SQ01, SQ03 and SP05 use the **same five dynamic stores** (same seq/addr); they are five distinct contexts *per model*, not fifteen independent software samples.

### 1.6 SQ01 verdict

- Chain: **COMPLETE_CHAIN 5/5**, raw-hash verified.
- Reload: real L1D read (`sq_entry_id=-1`, L1D response, no forwarding-decision record for the reload seq).
- Divergence: exactly one byte (bit-3 flip) per context; `mem_write_hash == reload_data_hash == consumer_hash`.
- Oracle: sensitive, FAIL 5/5.
- No `NO_INJECTION`; injection count 1 in every run; all traces COMPLETE/VALID.

**Defects found (SQ01):** none in the model/chain. Downstream/reporting defects: C-04 (workbook identity/ordinals), C-06 (evidence binary is `d3807fbe`, not the final `070d68a6`), C-07 (generic diagnostic CSV says `NO_DIVERGENCE` despite the complete chain), C-09 (weak controls), C-10 (shared stores across models), C-12 (minor funnel-count typo).

---

## 2. SQ03 — premature `_canWB` (visibility timing)

### 2.1 Static evidence

Hook: `LSQUnit::executeStore` (`CHAOS/gem5/src/cpu/o3/lsq_unit.cc:884-908`):

```
if (cpu->lsqFwd && !storeQueue[store_idx].canWB() &&
    !store_inst->isStoreConditional() && !store_inst->isAtomic()) {
    const bool canwb_before = storeQueue[store_idx].canWB();
    const uint64_t stores_before = storesToWB;
    if (cpu->lsqFwd->maybeSetCanWB(...)) {
        storeQueue[store_idx].canWB() = true;
        ++storesToWB;
        ... noteSQ03Injection(... canwb_before, true, stores_before, storesToWB, curTick(), ...)
    }
}
```

`maybeSetCanWB` (`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:729-763`) sets the flag, bumps `eligible_count`, and asserts exactly one injection. **No address, size or data is touched.** The early `canWB` lets `writebackStores()` drain the store to the cache **before** its architectural commit; the paired `++storesToWB` keeps `completeStore` accounting balanced.

### 2.2 Dynamic evidence — five contexts

| Ctx | Ordinal | Store seq / VA | sq idx/gen | canWB | storesToWB | inject = store_writeback send tick | store_mem_write (block update) tick | completeStore tick | commit tick | visible before commit | Reload seq / LQ idx | Reload req → resp | reload hash (unfaulted) | effect_outcome | Terminal / Oracle |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---|---:|---|---|---|---|---|
| R01 | 1021 | 13328 / 0x4919f0 | 956/1306 | 0→1 | 0→1 | 16372510 | 16372510 | 16373280 | 16376745 | **1** | 13330 / 759 | 16379055 → 16379825 | `b6180e0c195fd2e9` | CHAIN_VISIBILITY_MOVED (`DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`) | MASKED / PASS |
| R02 | 1047 | 15122 / 0x491ac0 | 982/1332 | 0→1 | 0→1 | 17001600 | **17007760** | 17008530 | 17005835 | **0** | 15124 / 785 | 17010455 → 17011225 | `9f995d89be67e92d` | **LIFECYCLE_ONLY** (`NO_DOWNSTREAM_EFFECT`) | MASKED / PASS |
| R03 | 1072 | 16847 / 0x491b88 | 1007/1357 | 0→1 | 0→1 | 17488240 | 17488240 | 17489010 | 17492475 | **1** | 16849 / 810 | 17494785 → 17495555 | `fde383c67ac034f1` | CHAIN_VISIBILITY_MOVED | MASKED / PASS |
| R04 | 1098 | 18641 / 0x491c58 | 1033/1383 | 0→1 | 0→1 | 17987200 | 17987200 | 17987970 | 17991435 | **1** | 18643 / 836 | 17993745 → 17994515 | `aa2be3d3d60e3c9d` | CHAIN_VISIBILITY_MOVED | MASKED / PASS |
| R05 | 1124 | 20435 / 0x491d28 | 1059/1409 | 0→1 | 0→1 | 18628225 | 18628225 | 18628995 | 18632460 | **1** | 20437 / 862 | 18634770 → 18635540 | `c7d78aff5e06edf9` | CHAIN_VISIBILITY_MOVED | MASKED / PASS |

Raw sources: `audit_v3_3_2/runs/SQ03-R0<k>-fault/trace_v31.jsonl` (`injection`, `store_writeback` ×2, `store_mem_write`, `sq03_complete`, `commit`, `memory_request`, `memory_response`, `sq03_effect`) and `oracle.log`.

### 2.3 Semantics check

- `_canWB 0→1` and paired `storesToWB +1`: verified in 5/5 (`...;canwb_before=0;canwb_after=1;stores_to_wb_before=0;stores_to_wb_after=1;...`).
- No address/size/data modification: the injection record declares `address_modified=0;size_modified=0;data_modified=0`, and is **independently confirmed**: the store payload (`store_writeback.data_hex`) and reload hash equal the source-derived unfaulted value in all five contexts (e.g. R01 `6d7b78717e6b7d7f` → `b6180e0c195fd2e9`).
- Early visibility before commit: **4/5**. In R01/R03/R04/R05 the L1D block update (`store_mem_write`) precedes the architectural commit. In **R02 (ordinal 1047)** the block update is at 17007760, *after* commit 17005835 → `visible_before_commit=0`, `LIFECYCLE_ONLY`.
- The two "writeback" ticks are different concepts: `writeback_tick` = cache-send tick (`lsq_writebackStores`), `drain_tick` = actual block update (`BaseCache::updateBlockData` / `store_mem_write`). The verdict uses the block-update tick. For R02 they differ by 6160 ticks; this is what makes R02 `LIFECYCLE_ONLY`.

### 2.4 Does the reload observe pre-commit visibility? (important precision)

**No, in any of the five contexts.** In every run the reload request tick is *after* the store's commit tick (R01 16379055>16376745; R02 17010455>17005835; R03 17494785>17492475; R04 17993745>17991435; R05 18634770>18632460). This is structural: the workload's `dmb ish` is younger than the store and executes at the commit head only after the store has left `storesToWB`, and the load is younger than the barrier, so the reload cannot be issued before the store commits.

Therefore SQ03's measured effect is exactly: **"the store's cache-block update occurred before its architectural commit in 4/5 contexts; no architectural consumer can observe it; the oracle is unchanged."** It is a microarchitectural visibility-timing shift, not an architectural data corruption.

### 2.5 Is MASKED/PASS the correct terminal, and is any SDC being smuggled in?

**MASKED (oracle PASS) is the correct terminal.** Evidence:

- `oracle.log` in all five fault runs: `expected=7df5034c23f3e703 got=7df5034c23f3e703 ORACLE_PASS`.
- `summary.json` terminal `MASKED`, reason `STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS` (5/5).
- Prop arena CSV: `SQ03,R0x,...,MASKED,STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS,PASS,...` (`audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv`).
- The model record itself says `canwb_state_changed=1`, `data` untouched, and `effect_outcome` is `CHAIN_VISIBILITY_MOVED` (4/5) or `LIFECYCLE_ONLY` (1/5).

No SDC is being smuggled in **by the model record or the oracle**. Two downstream artefacts do conflict and must be controlled:

1. `audit_v3_3_2/LSU_Diagnostic_Features_Final.csv` says for all five SQ03 rows `ValueDivergenceCount=0;ControlDivergenceCount=0;PropagationCoverage=LIFECYCLE_ONLY;FaultEffectReason=TRIGGERED_NO_DIVERGENCE;Terminal=MASKED`. For SQ03 this is terminal-consistent, but the same generic fields are **wrong for SQ01/SP05** (see §5).
2. The readiness matrix carries the qualifier `VISIBILITY_TIMING_SHIFT (CHAIN_VISIBILITY_MOVED 4/5), NOT SDC` on every SQ03 row (`audit_v3_3_2/LSU_60Context_Final_Readiness_Matrix.csv`) — this qualifier must survive into the final workbook/matrix, not just the readiness CSV.

**The paper must state:** terminal MASKED / ORACLE_PASS; effect = cache-block update before commit in 4/5 contexts; the 1/5 exception (ordinal 1047, rank 39, p=0.30) had block update after commit; no pre-commit reload consumer exists by workload construction (dmb + program order); no data/address/size change; this is a visibility-timing fault class, never SDC.

**Defects found (SQ03):** C-11 (no paired no-fault timing reference for the same store), plus C-04/C-06/C-07/C-09/C-10 as above. No data/chain defect; no SDC.

---

## 3. SP05 — lost store completion (`completeStore` at `writebackStores`)

### 3.1 Static evidence

Selection: `LSQUnit::commitStores` → `CHAOSLSQFwd::maybeSelectSP05(...)` (`lsq_unit.cc:1010-1016`), logged as `Site: commitStores_select`.
Injection: `writebackStores` checks `maybeCompleteSP05(...)` before the cache send (`lsq_unit.cc:1069-1093`); on fire it calls `noteSP05Injection(...)`, then `completeStore(storeWBIt)` and skips the send. The store's SQ data is available at that point as `storeWBIt->data()` / `request->_size` (the same buffer copied to `inst->memData` at `lsq_unit.cc:1112-1118`), **but it is not passed to the propagation hook**.

`lsq_unit.cc:1503-1508` (real `completeStore`): when the premature completion was traced, `noteSP05Complete(...)` records `canwb_before/completed_before/stores_to_wb_before/stores_to_wb_after/mem_sent=false/complete_tick`.

### 3.2 Dynamic evidence — five contexts

| Ctx | Ordinal | Store seq / VA | sq idx/gen | complete/inject tick | storesToWB | mem_sent | write_skipped | reload seq / LQ idx | reload req → resp | reload hash | consumer seq / PC / commit | consumer hash | store_data_fnv | data_correct | stage_outcome | Terminal / Oracle |
|---|---:|---|---|---|---:|---:|---:|---:|---|---|---|---|---|---|---|---|---|
| R01 | 952 | 13328 / 0x4919f0 | 956/1306 | 16377515 | 1→0 | 0 | 1 | 13330 / 759 | 16379440 → 16380210 | `a8c7f832281a39c5` | 13333 / 0x400550 / 16381365 | `a8c7f832281a39c5` | **null** | null | RELOAD_UNVERIFIABLE | SDC / FAIL |
| R02 | 978 | 15122 / 0x491ac0 | 982/1332 | 17006605 | 1→0 | 0 | 1 | 15124 / 785 | 17008530 → 17015460 | `a8c7f832281a39c5` | 15127 / 0x400550 / 17016615 | `a8c7f832281a39c5` | **null** | null | RELOAD_UNVERIFIABLE | SDC / FAIL |
| R03 | 1003 | 16847 / 0x491b88 | 1007/1357 | 17493245 | 1→0 | 0 | 1 | 16849 / 810 | 17495170 → 17495940 | `a8c7f832281a39c5` | 16852 / 0x400550 / 17497095 | `a8c7f832281a39c5` | **null** | null | RELOAD_UNVERIFIABLE | SDC / FAIL |
| R04 | 1029 | 18641 / 0x491c58 | 1033/1383 | 17992205 | 1→0 | 0 | 1 | 18643 / 836 | 17994130 → 17994900 | `a8c7f832281a39c5` | 18646 / 0x400550 / 17996055 | `a8c7f832281a39c5` | **null** | null | RELOAD_UNVERIFIABLE | SDC / FAIL |
| R05 | 1055 | 20435 / 0x491d28 | 1059/1409 | 18633230 | 1→0 | 0 | 1 | 20437 / 862 | 18635155 → 18635925 | `a8c7f832281a39c5` | 20440 / 0x400550 / 18637080 | `a8c7f832281a39c5` | **null** | null | RELOAD_UNVERIFIABLE | SDC / FAIL |

Raw sources: `audit_v3_3_2/runs/SP05-R0<k>-fault/{trace_v31.jsonl,oracle.log,lsq_fwd_injections.log}`.

### 3.3 Every SP05 claim re-verified

- **`completeStore` fires**: `sp05_complete` record (`site=lsq_completeStore;...;canwb_before=1;completed_before=0;stores_to_wb_before=1;stores_to_wb_after=0;mem_sent=0;complete_tick=…`) exists in 5/5; the injection record also carries `completed_before=0;completed_after=1`.
- **`storesToWB 1→0`**: 5/5 (see `injection` and `sp05_complete`).
- **`mem_sent=0`**: 5/5.
- **`write_skipped=1`**: 5/5 (`write_skipped = completion_tick!=0 && drain_tick==0`).
- **No `store_mem_write`** record exists in any SP05 trace (record-type census: `injection|sp05_complete|sp05_stage|memory_request|memory_response|register_writeback|errant_commit|forwarding_decision|lq/sq_lifecycle|propagation_edge|summary` only). Likewise no `store_writeback`.
- **Reload reads zero**: `memory_response` = `data_hex=0000000000000000;data_fnv=a8c7f832281a39c5` (standard FNV-1a-64 of 8 zero bytes = `a8c7f832281a39c5`, verified independently). `memory_request` has `store_not_written_yet=1;sq_entry_id=-1;last_send_before_store_write=0;overwritten=0`.
- **Consumer observed**: `consumer_commit` at seq 13333 (PC 0x400550) with `source_value_hash=a8c7f832281a39c5;consumer_input_fnv=a8c7f832281a39c5;consumer_input_matches_source=1` (R01), and the corresponding seqs in R02–R05.
- **Oracle FAIL 5/5**: distinct checksums `c7a1b3a591c68328`, `34890178967da568`, `225c6839dd319a5c`, `d42d86ee46895884`, `c6e1c98b1480efd4`.

### 3.4 What the model record proves today vs what only the oracle proves

**Model record proves (5/5):**
- The fault fired on the selected store and `completeStore` ran with `mem_sent=0`;
- The store was counted as completing (`completed 0→1`, `storesToWB 1→0`) while its cache write never happened (`drain_tick=0`, no `store_mem_write`);
- A younger same-address reload was bound (`reload_seq`) and delivered the zero word (`reload_data_hash=a8c7f832281a39c5`);
- That value flowed through register writeback into a committed consumer (`consumer_commit`, same hash).

**Model record does NOT prove, today:**
- The store's **intended bytes** (`store_data_fnv=null`), hence it cannot prove the reload value differs from what the store should have written, hence `data_correct=null` and `stage_outcome=RELOAD_UNVERIFIABLE`. The record is a *chain with a missing store-side hash*, not a closed dataflow chain.
- The store's architectural commit tick (`sp05_stage.commit_tick=0`); see C-03 — this is an artefact, not evidence that the store never committed.
- An early-anomaly event in the frozen sense (`store_writeback`/`store_mem_write`), which a skipped write can never emit (see §4.3).

**Only the oracle (+ audit-side source reconstruction) proves:** the lost write changed the software-visible result. The oracle differential (FAIL 5/5 vs golden `7df5034c23f3e703`) is the architectural proof; the trace binds it to this store and this reload. Independently, reconstructing `v_i` from `sq_reload_v3212.c` gives intended hashes `b618…/9f99…/fde3…/aa2b…/c7d7…` — all different from the reload's `a8c7f832281a39c5`; therefore, once `store_data_fnv` is wired, the record will read `data_correct=0` and `stage_outcome=CHAIN_VISIBILITY_LOST` in 5/5. This audit-side derivation is not a substitute for the model record; it is the predicted post-fix value that the fix must reproduce.

**Defects found (SP05):** C-01 (`store_data_fnv` unwired → `RELOAD_UNVERIFIABLE`), C-02 (early-anomaly event), C-03 (`commit_tick=0` artefact), C-08 (SDC label without qualifier), plus C-04/C-06/C-07/C-09/C-10. Injection semantics (completeStore fires, storesToWB 1→0, mem_sent=0, write skipped, reload zero, consumer observed) are correct.

---

## 4. Root cause — why `store_data_fnv` is null for SP05, and how to wire it

### 4.1 Exact code path (quoted)

`CHAOSPropagation::noteSP05Injection` (`CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc:1809-1856`) builds the detail string and the registry entry:

```cpp
d << "site=writebackStores_prematureComplete;family=sp05;model=SP05"
  << ... << ";mem_sent=0" << ...;
FaultStoreEntry fe;
fe.ptag = ptag; fe.dyn_seq = dyn_seq; fe.base = addr; fe.size = size;
fe.idx = sq_idx; fe.gen = sq_gen; fe.byte_begin = addr; fe.byte_end = addr + size;
fe.family = "sp05_complete";
fe.registered = inject_tick;
fault_store_registry[dyn_seq] = fe;
```

**No data bytes are in the signature** (`CHAOSPropagation.hh:348-353`) and **none are stored**; `fe.data_fnv` remains `""`.

Then `emitChainRecord` (`CHAOSPropagation.cc:2819-2853`) assembles `sp05_stage`:

```cpp
st.store_data_hash = e.data_fnv;           // "" here
st.reload_data_hash = e.reload_seq ? e.reload_hash : "";
const chaos_sp05::StageOutcome o = chaos_sp05::stageVerdict(st);
...
// store_data_fnv stays null until the shared-file request
// (noteSP05Injection needs the SQ entry's bytes) is wired;
// data_correct honestly follows (null = unknown).
<< ";store_data_fnv=" << (e.data_fnv.empty() ? "null" : e.data_fnv)
<< ";data_correct=" << data_correct
```

`chaos_sp05::stageVerdict` (`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/sp05_rules.hh:95-106`) returns `RELOAD_UNVERIFIABLE` when either hash is absent — so `data_correct` is `null` by construction, not by accident.

The call site (`CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1069-1088`) reads:

```cpp
DynInstPtr inst = storeWBIt->instruction();
LSQRequest* request = storeWBIt->request();
...
if (cpu->lsqFwd && !request->isSent() &&
    cpu->lsqFwd->maybeCompleteSP05(inst->seqNum, inst->sqIdx,
                                   inst->sqEntryGeneration, false)) {
    ...
    cpu->chaosPropagation->noteSP05Injection(
        inst->seqNum, pc, inst->effAddr, request->mainReq()->getSize(),
        inst->sqIdx, inst->sqEntryGeneration, false, true,
        (uint64_t)storesToWB, (uint64_t)(storesToWB - 1), curTick(),
        cpu->lsqFwd->sp05Eligible());
    completeStore(storeWBIt);
    ... skip send ...
}
...
inst->memData = new uint8_t[request->_size];
if (storeWBIt->isAllZeros()) memset(inst->memData, 0, request->_size);
else memcpy(inst->memData, storeWBIt->data(), request->_size);   // lines 1112-1118
```

**The missing input is exactly `storeWBIt->data()` + `request->_size`** (the SQ entry's intended bytes) at the moment the send is suppressed. They are stable and available on the same line; `isAllZeros()` must be honored (zero-fill then hash).

### 4.2 Proposed source-level wiring (recording only)

1. `lsq_unit.cc` (SP05 branch, ~line 1082): pass the data, its size and a real commit tick:
   ```cpp
   std::vector<uint8_t> zeros(request->_size, 0);           // isAllZeros case
   const uint8_t *sq_data = storeWBIt->isAllZeros()
                          ? zeros.data() : storeWBIt->data();
   cpu->chaosPropagation->noteSP05Injection(
       inst->seqNum, inst->pcState().instAddr(), inst->effAddr,
       request->mainReq()->getSize(), inst->sqIdx,
       inst->sqEntryGeneration, false, true,
       (uint64_t)storesToWB, (uint64_t)(storesToWB - 1), curTick(),
       cpu->lsqFwd->sp05Eligible(),
       sq_data, (unsigned)request->_size,              // NEW
       cpu->lsqFwd->sp05SelectTick());                 // NEW (commitStores tick)
   ```
   The zero buffer makes the all-zero case hash 8 zero bytes (`a8c7f832281a39c5` for size 8), matching the data that would have been written.
2. `CHAOSPropagation.hh` (~line 348) and `CHAOSPropagation.cc` (~line 1809): extend the signature with `const uint8_t *store_data, unsigned store_size, Tick commit_tick`. In the body:
   ```cpp
   if (store_data && store_size) {
       std::ostringstream fh; fh << std::hex << fnv1a64(store_data, store_size);
       fe.data_fnv = fh.str();
       fe.data_hex = bytesToHex(store_data, store_size);
   }
   fe.store_commit_tick = commit_tick;   // fixes sp05_stage.commit_tick=0
   ```
   `fnv1a64`/`bytesToHex` already exist and are used by `noteStoreBEInjection` (`CHAOSPropagation.cc:526-541`) and the writeback path.
3. `CHAOSLSQFwd::maybeSelectSP05` (already called at `commitStores`, `lsq_unit.cc:1010-1016`) should save `sp05_select_tick = curTick()`; expose `sp05SelectTick()`. The store's architectural commit is happening at that call, so `commit_tick` becomes real. (Alternative: record the commit tick from `noteCommit` using a pre-registration hook keyed on `sp05_target_seq`; the select-tick route is simpler and matches the existing SP05 identity state.)
4. No other call site exists (`grep -rn noteSP05Injection` → only `lsq_unit.cc:1082`), so the signature change is single-site.

After this, `chaos_sp05::stageVerdict` returns `CHAIN_VISIBILITY_LOST` and `data_correct=0` in all five contexts (predicted values in §3.4), and `sp05_stage.commit_tick` becomes non-zero.

### 4.3 Early-anomaly event

The frozen audit tool expects, for SP05, an early-anomaly event of kind `store_writeback` or `store_mem_write`:

`tools/lsu_propagation_audit.py:75-88`:
```python
EARLY_ANOMALY_KINDS = {
    ...
    "SQ01": ("store_writeback", "store_mem_write"),
    "SQ03": ("store_writeback", "store_mem_write"),
    "SP05": ("store_writeback", "store_mem_write"),
```
and `:603-616` marks `early_anomaly_verified="missing"` + `NO_EARLY_ANOMALY_EVENT` when none exists.

For SP05 the whole point is that **no store write happens**, so these two kinds structurally cannot appear. The honest anomaly is the premature completion itself. Two fixes, both recording-only:

- **Preferred:** emit a dedicated event from `noteSP05Complete` when `mem_sent=false` and `complete_tick!=0`, e.g. `writeNode(ptag, "store_write_skipped", dyn_seq, ..., "site=lsq_completeStore;store_seq=...;mem_sent=0;stores_to_wb_before=1;stores_to_wb_after=0;write_skipped=1;complete_tick=...")`, and add `"store_write_skipped"` to `EARLY_ANOMALY_KINDS["SP05"]`.
- **Minimal:** add `"sp05_complete"` to `EARLY_ANOMALY_KINDS["SP05"]` (the node already exists on the fault ptag chain, `CHAOSPropagation.cc:1879-1882`).

Do **not** synthesize a fake `store_writeback`/`store_mem_write`; that would falsely assert a memory write.

### 4.4 Does the fix change fault semantics? Rebuild/regression risk

- **Semantics: no.** None of the changes alters `maybeSetCanWB`, `maybeSelectSP05`, `maybeCompleteSP05`, data buffers, byte enables, `storesToWB`, `completeStore`, or the skipped send. All edits read state and write trace fields. The injected store still completes prematurely without a cache write.
- **Timing: no cycle change.** Hashing at the injection point is CPU-time work only (no `schedule()`/`curTick()` change); the trace write already happens there.
- **Rebuild:** C++ only (`CHAOSPropagation.cc/.hh`, `CHAOSLSQFwd.cc/.hh`, `lsq_unit.cc`) → full `scons -j16 build/ARM/gem5.opt` (per CLAUDE.md, `-j16` for clean builds). Python tool change (`tools/lsu_propagation_audit.py`) needs no rebuild.
- **Regression risk:** low but non-zero. (a) Trace-schema consumers that assume a fixed `sp05_stage` field set will see `store_data_fnv`/`data_correct` change from `null` to concrete; (b) adding a new event type can affect generic trace counters (`summary.counts.events`) and any tool that enumerates event types; (c) the early-anomaly table change alters `early_anomaly_verified` for SP05 from `missing` to `yes`, hence the closure/diagnostic CSVs. Required verification after the patch: rebuild clean (0 new warnings/errors), re-run one SP05 context (R01) and confirm `store_data_fnv=b6180e0c195fd2e9`, `data_correct=0`, `stage_outcome=CHAIN_VISIBILITY_LOST`, `commit_tick!=0`, `write_skipped=1`, `mem_sent=0`; re-run one SQ01 and one SQ03 context and confirm their records are byte-identical to the pre-patch ones (except no SP05 fields); run the canonical `reg_chain` regression (`exit: pass`, no SIGSEGV).

---

## 5. Original W3/W6 vs candidate `sq_reload_v3212`

All values below are from raw traces; originals were run only on `d3807fbe` (probe evidence), candidates on both binaries (probe evidence and matrix runs; values identical).

| Model | Original workload / ordinal | Original raw result | Candidate 5-context result | Real difference |
|---|---|---|---|---|
| SQ01 | W3 `sq_drain`, ordinal 1 | injection seq 18 `0x7ffffefd10` (C-runtime startup store, not the array); `sq01_chain`: `mem_write_hash=a09e307a7f948acd;reload_seq=0;reload_data_hash=null;consumer_seq=0;consumer_hash=null;chain_verdict=STORE_COMMITTED_LANE_NOT_READ`; terminal MASKED; oracle PASS `ba3b3185e541ad03` | COMPLETE_CHAIN 5/5, hashes equal, SDC, oracle FAIL 5/5 | The fault reaches an architectural consumer only on `sq_reload` (W3 has one end-of-program bulk read at `0x400590`, no per-store reload) |
| SQ03 | W3 `sq_drain`, ordinal 1 | injection seq 18 at `0x4008d0`; `sq03_effect`: `canwb 0→1;writeback_tick=140910;drain_tick=198275;commit_tick=149380;reload_seq=0;visible_before_commit=0;effect_outcome=LIFECYCLE_ONLY;effect_reason=NO_DOWNSTREAM_EFFECT`; terminal MASKED; oracle PASS | MASKED 5/5; `CHAIN_VISIBILITY_MOVED` 4/5 + `LIFECYCLE_ONLY` 1/5; oracle PASS 5/5 | Early visibility is measurable on `sq_reload` (same-address reload); still not SDC |
| SP05 | W6 `store_path`, ordinal 1 | injection seq 18 `0x7ffffefd10` (startup store); `sp05_stage`: `completion_tick=150150;commit_tick=0;writeback_tick=150150;drain_tick=0;write_skipped=1;reload_seq=0;reload_data_hash=null;stage_outcome=NO_RELOAD_OBSERVED`; terminal MASKED; oracle PASS `2543a2a60de01795` | SDC FAIL 5/5, reload reads zero `a8c7f832281a39c5`, consumer observed; model record `RELOAD_UNVERIFIABLE` | The lost write becomes architecturally visible only on `sq_reload` |

Raw originals: `audit_v3_3_2/sq_workload/evidence/original/{SQ01_sq_drain_K1,SQ03_sq_drain_K1,SP05_store_path_K1}/{trace_v31.jsonl,oracle.log,manifest.json}`. All three manifests: binary `d3807fbe…`, workload SHAs `d423539c…` (W3) / `906b3798…` (W6), seeds 591611458 / 2214819981 / 1489155957, injection count 1.

Important honesty point already in the dossier: the ordinal-1 "original" runs select the **C-runtime startup store**, not the workload array lane; they prove "ordinal 1 has no consumer", not "the workload can never have one". W3/W6 structurally read their arrays once at end of program (W3 `0x400590 ldrb w2,[x5],#1`; W6 `0x400698 ldrb w0,[x4],#1` in `main`), so no per-store reload consumer exists in either.

---

## 6. Provenance discipline

### 6.1 Which runs produced which table

| Evidence set | Binary (manifest) | What it is used for |
|---|---|---|
| `audit_v3_3_2/sq_workload/evidence/{contexts,original,establish}/**` (24 dirs) | **`d3807fbe…`** (v3.3.1 packaged binary; see `audit_v3_3_1/report/PROVENANCE.md:9`) | Dossier tables (`LSU_SQ_Workload_Decision.md` §1–§3), K* boundary probes (1005/1006, 1008/1009, 939/940), original W3/W6 runs |
| `audit_v3_3_2/runs/{SQ01,SQ03,SP05}-R0{1..5}-{fault,control}/` (30 dirs) | **`070d68a6…`** (current live binary; `sha256sum` ran now) | v3.3.2 matrix tables: propagation CSV, ROI mapping, distinctness audit, readiness matrix, controls CSV, diagnostic features |
| `d3807fbe…` vs `070d68a6…` value comparison | — | **No value-level mixing found.** A direct record-by-record comparison of all 15 `evidence/contexts/*` traces against their `runs/*-fault` counterparts shows the `injection`, `memory_request`, `memory_response` and model-rule (`sq01_chain`/`sq03_effect`/`sp05_stage`) records are **byte-identical** (same timestamps, seqs, hashes, verdict strings) in 15/15 pairs (`ALL KEY RECORD IDENTICAL: True`) |

So the dossier's table was produced by the **d3807fbe** runs, while the matrix CSVs were produced by **070d68a6** runs. Their numbers agree, but a report that cites "070d68a6 evidence" for the dossier's table would be laundering provenance: the dossier's own §0 provenance row (`d3807fbe`) is the correct one for its evidence. The K* boundary probes themselves exist **only** on `d3807fbe`; they were not re-probed on `070d68a6` (no runs allowed in Phase 1). The 15 overlapping percentile ordinals mapping to identical stores is strong corroboration of an unchanged ordinal space, but it is not a re-measurement of K*.

No file-level mixed-binary concatenation exists inside any single table. The risk is cross-table (dossier evidence + matrix table) and must be labelled per row.

### 6.2 Recomputed ELF/golden SHAs (current files)

```
bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6  sq_reload_v3212
abbb0dcd3c22666a9b0e05a80743c32256d415e33a089b5755269d3db0614133  sq_reload_v3212.c
24e3f93c7da83881513fd0c336616545c92f330d55400d3d32b8bad24010540d  sq_reload_v3212.golden   (content 7df5034c23f3e703)
d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f  sq_drain
23f93a3fb6041e3f901cb0e809374fdec4990495cead67f77a63c6fa8b7d0cc2  sq_drain.c              (golden ba3b3185e541ad03)
906b3798adc618f388c1988389dd67140afeba6c706456fdeebdd524dc55fbcf  store_path
8b7076ddc3ff01b24c8ceea745983f2efab7273b7532bd478a4f0a1ca27e5016  store_path.c            (golden checksum=0x2543a2a60de01795)
```

These match `LSU_SQ_Workload_Decision.md` §0, `LSU_Workload_Oracle_Final_Audit.csv`, and the run manifests (`workload.sha256 = bcab9cc5…`). `sq_reload_v3212.host.out` = `checksum=0x7df5034c23f3e703`; the oracle golden and host output agree.

### 6.3 `sq_reload_v3212` has no W1–W8 baseline row

- Sheet `6.工作负载及无故障基线` of `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx` has exactly 8 data rows: W1 AGU-AddrModes, W2 LQ-Lifetime, W3 SQ-Drain, W4 SQ-Forward, W5 Load-Response, W6 Store-Path, W7 Replay-Dependency, W8 Alignment. No `sq_reload_v3212` row.
- `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` contains **0** occurrences of `sq_reload_v3212` (grep count 0).
- The workbook's `xl/sharedStrings.xml` contains no `sq_reload` string and no worksheet XML references it.
- `audit_v3_3_1/audits/LSU_12Model_Workload_Readiness.csv` already states the candidate is "NOT part of W1-W8".

**Implication:** adoption is a **workload-identity change**, not a parameter change. It requires (a) a new/overridden W-row with ELF/golden/oracle/baseline status, (b) sheet-5 WorkloadPath/ELF/Oracle/EventOrdinal updates for the 15 rows, and (c) an explicit researcher approval. Note also that **a no-fault baseline for the candidate does exist empirically** in this round: all 15 matrix control runs use the same binary/workload and pass the oracle (`oracle.log` ORACLE_PASS, `injection_count=0`), though they are not recorded in sheet 6.

### 6.4 Workbook identity facts (verified via openpyxl)

Sheet 5 rows (15): authoritative IDs are `SQ01-F0-W3-S01-R01..R05`, `SQ03-F0-W3-S02-R01..R05`, `SP05-F6-W6-S01-R01..R05`; `Seed` values are 591611458 / 576447973 / 1257175390 / 3116972755 / 172636228 (SQ01), 2214819981 / 1486471869 / 3102670938 / 3974203372 / 729970077 (SQ03), 1489155957 / 1290498198 / 2768710389 / 2741073922 / 4098160626 (SP05). **Every seed matches the run manifests exactly (15/15).** But:

- `EventOrdinal` in the workbook is **1,2,3,4,5**, while the runs use the percentile ordinals **1018/1044/1069/1095/1121 (SQ01), 1021/1047/1072/1098/1124 (SQ03), 952/978/1003/1029/1055 (SP05)**.
- `WorkloadPath`/`BinarySHA256`/`Oracle` are the old W3/W6 identities (`sq_drain` `d423539c…` / `ba3b3185…`; `store_path` `906b3798…` / `2543a2a60de01795`).
- `DecisionStatus=NEEDS_USER_DECISION`, `ConfigFrozen=NO`, `RunStatus=NOT_RUN` (SQ01) / `PILOT_RUN` (SQ03, SP05).
- Sheet 6 W6 `ExpectedGolden` is **stale**: `7284dc0b3f6c64cf` vs the actual golden `2543a2a60de01795` (W3's is correct).

---

## 7. Consolidated issue list

Approval = researcher/excel approval required (Y/N). Regression risk is for the proposed one-shot fix.

| IssueID | Class | Model/context | Root cause | Raw evidence | Affected files | Proposed one-shot fix | Validation command | Approval | Regression risk |
|---|---|---|---|---|---|---|---|---|---|
| **C-01** | A (hook) | SP05 R01–R05 | `noteSP05Injection` never receives/stores the SQ entry bytes, so `FaultStoreEntry::data_fnv` stays empty → `store_data_fnv=null`, `data_correct=null`, `RELOAD_UNVERIFIABLE` | `CHAOSPropagation.cc:1809-1856` (no data arg), `:2826-2850` (comment admits the gap); `CHAOSPropagation.hh:348-353`; `lsq_unit.cc:1069-1088`; traces `sp05_stage` 5/5 | `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{cc,hh}`, `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` | Pass `storeWBIt->data()`/`isAllZeros` + `request->_size` into `noteSP05Injection`; set `fe.data_fnv`/`data_hex` via existing `fnv1a64`/`bytesToHex` (§4.2) | rebuild `scons -j16`; re-run `SP05-R01`; assert `store_data_fnv=b6180e0c195fd2e9`, `data_correct=0`, `stage_outcome=CHAIN_VISIBILITY_LOST`; SQ01/SQ03 records unchanged | N (A-class code fix; Excel qualifier removal after) | Medium (signature + record values) |
| **C-02** | A/C | SP05 R01–R05 | Early-anomaly table expects `store_writeback`/`store_mem_write`, which a skipped write cannot emit; trace has neither | `tools/lsu_propagation_audit.py:75-88,603-616`; record census of `SP05-R0x-fault/trace_v31.jsonl` shows no `store_writeback`/`store_mem_write` | `tools/lsu_propagation_audit.py`; `CHAOSPropagation.cc` `noteSP05Complete` | Emit `store_write_skipped` at `noteSP05Complete` (mem_sent=0) and add it to `EARLY_ANOMALY_KINDS["SP05"]` (or minimal: add `sp05_complete`) | re-run tool on SP05 R01; `early_anomaly_verified=yes`, no `NO_EARLY_ANOMALY_EVENT` | N | Low (diagnostic only) |
| **C-03** | A/C | SP05 R01–R05 | `sp05_stage.commit_tick=0` in 5/5 is an artefact: registry entry is created in `writebackStores`, i.e. after the store's commit, so `noteCommit` never sets `store_commit_tick` | `trace_v31.jsonl` 5/5 `commit_tick=0`; no `commit` event in SP05 traces; `CHAOSPropagation.cc:2470-2475` vs `:1840-1853`; `lsq_unit.cc:1010-1016` | `CHAOSPropagation.{cc,hh}`, `CHAOSLSQFwd.{cc,hh}`, `lsq_unit.cc` | Capture `curTick()` in `maybeSelectSP05` (commitStores) and pass it to `noteSP05Injection`; set `fe.store_commit_tick` | re-run SP05 R01; `commit_tick>0` and `< complete_tick` | N | Low (record only) |
| **C-04** | D | SQ01/SQ03/SP05 all 15 | Workbook has no `sq_reload_v3212` W-row; sheet 5 still names W3/W6, EventOrdinal 1–5; SampleRunIDs provisional in CSVs (`V332-…`) vs frozen `SQ01-F0-W3-S01-Rxx`-style | openpyxl dump of sheet 6 (8 rows W1–W8), sheet 5 (15 rows), `60_SAMPLE_MATRIX.csv` grep=0; `LSU_SQ_Workload_Decision.md` §0/§6 | `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx` sheets 5/6; `excel/60_SAMPLE_MATRIX.csv` | Add W9 `sq_reload_v3212` row (ELF `bcab9cc5…`, golden `7df5034c23f3e703`, baseline status from controls); update 15 sheet-5 rows' WorkloadPath/ELF/Oracle/EventOrdinal; create new RunIDs/SubTaskIDs; keep seeds; map provisional `V332-*` → frozen IDs explicitly | re-open workbook, verify 15 rows' seeds == manifests and ordinals == runs | **Y** | Low (identity only) |
| **C-05** | D | W6 | Sheet 6 `ExpectedGolden=7284dc0b3f6c64cf` stale vs actual `2543a2a60de01795` | openpyxl sheet 6 row W6; `store_path.golden` content | `excel/…v3.2.7.xlsx` sheet 6 | Correct to `2543a2a60de01795` (or record the two as historical/current) | openpyxl read-back | **Y** | None |
| **C-06** | D | SQ01/SQ03/SP05 provenance | Dossier evidence is on `d3807fbe` (v3.3.1 binary), matrix tables on `070d68a6`; both agree value-for-value but the provenance rows differ; K* probes exist only on `d3807fbe` | `manifest.json` of evidence dirs vs run dirs; `audit_v3_3_1/report/PROVENANCE.md:9`; `sha256sum build/ARM/gem5.opt` | `audit_v3_3_2/sq_workload/LSU_SQ_Workload_Decision.md`; any merged report | Label every table/row with its evidence binary; re-probe K* (1005/1006, 1008/1009, 939/940) on the frozen final binary during the revalidation phase | verify each cited row's manifest SHA matches its table's stated binary | Y (part of final package) | None (audit text) |
| **C-07** | C (tool) | SQ01/SQ03/SP05 all 15 | `LSU_Diagnostic_Features_Final.csv` reports generic `ValueDivergenceCount=0;ControlDivergenceCount=0;PropagationCoverage=LIFECYCLE_ONLY;FaultEffectReason=TRIGGERED_NO_DIVERGENCE`, including the SQ01/SP05 SDC contexts. Source: `pilot_meta.json.classification` is produced by `fault_effect_coverage.py`, which never consumes the model records (`sq01_chain`/`sq03_effect`/`sp05_stage`) and therefore sees "no value divergence" | `audit_v3_3_2/runs/*/pilot_meta.json` (`classification.fault_effect_evidence.value_divergence_count=0`, `chain_event_types` includes `sq01_chain`); `audit_v3_3_2/LSU_Diagnostic_Features_Final.csv` (15 rows); generator `docs/gem5-fi/lsu/implementation_v3_2/platform/fault_effect_coverage.py:270-334`; consumed at `run_pilot.py:1093`, written at `tools/lsu_v332_supplement.py:148-157` | `docs/gem5-fi/lsu/implementation_v3_2/platform/fault_effect_coverage.py`; `tools/lsu_v332_supplement.py` | Extend the classifier with `MODEL_RULE_KINDS` (already defined in `tools/lsu_propagation_audit.py:93-97`): when `sq01_chain.chain_verdict=COMPLETE_CHAIN` or `sp05_stage` shows `write_skipped=1/reload!=store`, set value divergence/coverage from the model record; never hand-edit the CSV | regenerate; SQ01/SP05 rows show a non-zero value-divergence / complete chain; SQ03 shows visibility-moved | N | Low (report only) |
| **C-08** | D/C | SP05 all 5 | Matrix terminal `SDC` is not accompanied by the `RELOAD_UNVERIFIABLE` qualifier except in the readiness matrix; controls/propagation CSVs say plain SDC | `LSU_60Context_Causal_Propagation_Final.csv`, `LSU_Fault_Control_Pair_Final.csv`, `LSU_60Context_Final_Readiness_Matrix.csv` | matrix/CSV generators | Carry the qualifier (or withhold SP05 from "SDC" until C-01 lands) in every table | grep: every SP05 SDC row has the qualifier | Y | None |
| **C-09** | B/C | all 15 controls | Controls are `--probability 0.0` no-ops; `lsq_fwd_injections.log` shows `eligible=0` (SQ03/SP05) or the file is absent (SQ01), so they prove the workload/oracle baseline but **not** that the target ordinal reaches the same store on the same binary/seed | `runs/SQxx-Rnn-control/{command.txt,lsq_fwd_injections.log}`; `LSU_Fault_Control_Pair_Final.csv` `ControlProof=INJECTOR_ABSENT` | `run_pilot.py`/`lsu_v332_matrix.py` control mode | Run controls in count-only/no-inject mode with the same ordinal and record the eligible funnel + selected store identity; keep `injected=0` | control log shows `eligible≥K*+rank` and (for SP05) `selected=1,fired=0,injected=0` | Y | Low (new runs only) |
| **C-10** | B (reporting) | cross-model | SQ01/SQ03/SP05 share the same five dynamic stores (same seq/VA); they are five contexts per model, not 15 independent software samples | §1.5 table; §2.2/§3.2 store seqs identical across models | paper/workbook notes | State the shared-store design explicitly; do not count 15 independent samples | — | N | None |
| **C-11** | C | SQ03 all 5 | No paired no-fault reference for the same store's writeback tick; `noteStoreWriteback`/`noteSQ03Writeback` only emit for registered fault stores, so the control cannot show the baseline drain tick; the "visibility moved" claim is fault-run timing + model logic | control traces have no `store_writeback`; `noteStoreWriteback` early-returns unless `fault_store_registry` contains the seq (`CHAOSPropagation.cc:575-577`) | `CHAOSPropagation.cc` (optional read-only baseline record) | Either (a) state the limitation in the paper, or (b) add a read-only baseline timing record for scheduled stores in a control-only mode | — | N/Y | Low |
| **C-12** | D (minor) | SQ01 R01 | Dossier funnel count "attempted=1604 eligible=1604" but R01 log says `attempted=1603 eligible=1603` | `runs/SQ01-R01-fault/lsq_fwd_injections.log` | dossier §2.3 | Correct to per-context values (R01 1603; R02–R05 1604) | grep logs | N | None |

---

## 8. Recommendations

| Model | Recommendation | Exact conditions |
|---|---|---|
| **SQ01** | **ADOPT** (technical evidence is complete) | 1) Same-change Excel identity update (C-04): W9 row + sheet-5 path/ELF/oracle/EventOrdinal; 2) keep the five percentile ordinals 1018/1044/1069/1095/1121 with K*=1006; 3) fix C-07 so the diagnostic CSV does not contradict the chain; 4) state that the five stores are shared with SQ03/SP05; 5) record the evidence binary per row (C-06) and re-probe K* on the final binary during revalidation. No fault-semantics condition: the model is unchanged and the chain is raw-verified. |
| **SQ03** | **CONDITIONAL ADOPT** | 1) Freeze the label **MASKED / VISIBILITY-TIMING SHIFT, NOT SDC** in the paper, workbook qualifier, and any summary table; 2) record the measured split **4/5 CHAIN_VISIBILITY_MOVED + 1/5 LIFECYCLE_ONLY (ordinal 1047)** with ticks, and state that the reload request is after commit in 5/5 (no pre-commit consumer by dmb construction); 3) do not claim a software-visible effect; 4) C-11 limitation stated or baseline timing record added; 5) C-04 identity update. If the researcher requires a guaranteed 5/5 effect, re-freeze the percentile rule outcome-blind — do **not** cherry-pick ordinal 1047 out. |
| **SP05** | **CONDITIONAL ADOPT** | 1) Land **C-01** (`store_data_fnv` wiring) and **C-02** (early-anomaly event) and **C-03** (`commit_tick`) before any "model-record-grade SDC" claim; until then the matrix must carry `RELOAD_UNVERIFIABLE` (C-08) and the SDC claim rests on write_skipped/mem_sent/absent store_mem_write/stale-zero reload + oracle differential; 2) after the fix, re-run the five contexts and confirm `data_correct=0`, `stage_outcome=CHAIN_VISIBILITY_LOST`; 3) C-04 identity update. Current raw evidence is strong but the model record is incomplete — do not inflate it to PASS/complete-chain today. |

**Impact on SampleRunID / Seed / Excel (C-04):**
- **Seeds: unchanged.** The workbook's 15 seeds equal the run manifests 15/15.
- **SampleRunIDs: must be re-issued, not silently replaced.** The authoritative IDs embed the workload (`SQ01-F0-W3-S…`, `SQ03-F0-W3-S…`, `SP05-F6-W6-S…`). With `sq_reload_v3212` adopted, either add a `W9` workload row and new RunIDs `<MODEL>-F0-W9-Sxx-Rxx` (SP05: `F6-W9`), or keep the RunIDs and add an explicit `WorkloadOverride` column with approval. The v3.3.2 provisional IDs `V332-<model>-R<ctx>` must be mapped explicitly to the frozen IDs.
- **Excel:** sheet 5 (15 rows) — WorkloadPath, BinarySHA256 (workload ELF), Oracle, EventOrdinal (→ percentile), DecisionStatus; sheet 6 — new W9 row (ELF `bcab9cc5…`, golden `7df5034c23f3e703`, baseline status, ROI), and fix W6 `ExpectedGolden` (C-05). Mark the affected SampleRunIDs `DESIGN_CHANGE_REQUIRED` until approval is recorded.

---

## 9. Bottom line

1. **SQ01 is the clean result.** Five distinct percentile contexts, `COMPLETE_CHAIN` 5/5, raw-verified `mem_write_hash == reload_data_hash == consumer_hash`, real L1D reload (`sq_entry_id=-1`, L1D response, zero forwarding-decisions for the reload seq), exactly one flipped byte (bit 3 of byte 0; source-derived expected value confirms it), oracle sensitive FAIL 5/5. No model defect found. Adoption is gated only by D-class identity/provenance bookkeeping.
2. **SQ03 is a real but non-architectural effect.** `_canWB 0→1` + paired `storesToWB +1`, no address/size/data change; cache-block update before commit in 4/5 (ordinal 1047 is the exception), but the reload request is after commit in all five (dmb forces it), so the oracle is unchanged 5/5. **MASKED/PASS is the correct terminal**; the paper must present it as a visibility-timing shift and record the 4/5 + 1/5 split. No SDC.
3. **SP05 is an SDC-class fault with an incomplete model record.** `completeStore` fires, `storesToWB 1→0`, `mem_sent=0`, `write_skipped=1`, no `store_mem_write`, reload reads zero (`a8c7f832281a39c5`), consumer observed, oracle FAIL 5/5. But `store_data_fnv=null` because the SQ bytes are not threaded into `noteSP05Injection`; `data_correct=null` and `RELOAD_UNVERIFIABLE` are therefore honest, and the SDC claim currently rests on the oracle + trace shape, not the model record. Wiring `store_data_fnv` (plus the early-anomaly event and a real commit tick) is a recording-only fix that will produce `CHAIN_VISIBILITY_LOST`/`data_correct=0`, matching the audit-side reconstruction exactly.
4. **Provenance:** the dossier's evidence is on `d3807fbe` (v3.3.1 binary), the matrix tables on `070d68a6`; values agree 15/15 but the two must be labelled per row. `sq_reload_v3212` has no W1–W8 row anywhere in the workbook, and the frozen sheet-5 rows still carry EventOrdinal 1–5 and the old W3/W6 identities.
5. **No verdict inflation:** SQ01 ADOPT; SQ03 and SP05 CONDITIONAL ADOPT with the conditions above. The generic diagnostic CSV's `LIFECYCLE_ONLY/NO_DIVERGENCE` rows for SQ01/SP05 are a tool defect, not a model verdict.

---

## 10. Could not verify

1. **K* boundary re-probe on `070d68a6`.** K*=1006/1009/940 exists only on `d3807fbe` (`evidence/establish/*`). The 15 percentile ordinals map identically on both binaries (strong corroboration), but the boundary probes themselves were not re-run (no gem5 runs in Phase 1).
2. **Original W3/W6 on `070d68a6`.** Original runs exist only on `d3807fbe`; their MASKED terminals are not re-measured on the final binary.
3. **A positive control proof for the target ordinal.** Controls use `--probability 0.0`; SQ03/SP05 control logs show `eligible=0` and SQ01's log is absent, so the controls prove the workload/oracle baseline but not that the selector reached the same store (C-09).
4. **Baseline (no-fault) writeback tick for the SQ03 target store.** No control-side `store_writeback`/`store_mem_write` record exists for that store (instrumentation is fault-registry-gated); the "visibility moved" claim is fault-run timing plus model logic, not a paired differential (C-11).
5. **Post-fix SP05 record values.** The predicted `store_data_fnv` values (`b618…`, `9f99…`, `fde3…`, `aa2b…`, `c7d7…`) and `data_correct=0` are derived from the workload source + standard FNV-1a-64, not from a patched binary (no runs allowed). They must be confirmed by the revalidation run.
6. **History of `d3807fbe` vs `070d68a6` source diffs.** The two binaries' source delta was not audited here; only the fact that they are distinct builds and that the SQ/SP records agree value-for-value on the 15 overlapping contexts.
