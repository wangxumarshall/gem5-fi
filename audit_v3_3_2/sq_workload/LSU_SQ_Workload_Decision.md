# LSU v3.3.2 — SQ01/SQ03/SP05 workload decision dossier

**Agent:** Agent E (LSU v3.3.2 SQ workgroup)
**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Scope:** decision support only. **No formal workload mapping, Excel workbook,
pilot directory, source file, or model definition was modified.** The only
artifacts written are this dossier and the raw evidence under
`audit_v3_3_2/sq_workload/evidence/`.

**Pair under decision (researcher decision B, approval pending):**
original W3 `sq_drain` (SQ01/SQ03) and W6 `store_path` (SP05) vs the shared
candidate `sq_reload_v3212`.

---

## 0. Provenance of this round

| Item | Value | Source |
|---|---|---|
| gem5 binary | `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2` | `sha256sum build/ARM/gem5.opt`; every run manifest `gem5.binary_sha256` |
| config | `configs/se/lsu_proxy.py`, sha256 `01f912de3388aaf420aa69d5dd55098ddfb97851faf0269a6b009fcc389bf6e5` | run manifests |
| `sq_reload_v3212` ELF | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` | recomputed this round |
| `sq_reload_v3212.c` | `abbb0dcd3c22666a9b0e05a80743c32256d415e33a089b5755269d3db0614133` | recomputed |
| `sq_reload_v3212.golden` file | `24e3f93c7da83881513fd0c336616545c92f330d55400d3d32b8bad24010540d`; content `7df5034c23f3e703` | recomputed |
| `sq_reload_v3212.host.out` | `1212188700bdff0641f8eb53fb77d7ff94c6fcf6cbc0f1aa786787a24e771a9d`; content `checksum=0x7df5034c23f3e703` | recomputed |
| W3 `sq_drain` ELF | `d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f` | recomputed |
| W3 `sq_drain.c` | `23f93a3fb6041e3f901cb0e809374fdec4990495cead67f77a63c6fa8b7d0cc2` | recomputed |
| W3 golden | file `b7e346d64bd6beab6a31d131aa5ac7067879689d7a209d5549478a7bdcafa473`, content `ba3b3185e541ad03` | recomputed |
| W6 `store_path` ELF | `906b3798adc618f388c1988389dd67140afeba6c706456fdeebdd524dc55fbcf` | recomputed |
| W6 `store_path.c` | `8b7076ddc3ff01b24c8ceea745983f2efab7273b7532bd478a4f0a1ca27e5016` | recomputed |
| W6 golden | file `bdbdade6c0967ee83bfbd4c94d04ec2b35beb5430e331c2bf1ee6c47a9710da8`, content `checksum=0x2543a2a60de01795` | recomputed |
| Static symbols | `buf` @ `0x491990`, 2048 B (sq_reload); `a.0` @ `0x491990`, 65536 B (sq_drain) / 32768 B (store_path) | `readelf -sW` |

Tooling note: `tools/lsu_v331_census.py` was **not** used because it hard-codes
its output under `audit_v3_3_1/roi/census/` (outside this agent's ownership) and
deletes the trace. The runner it wraps,
`docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`, was invoked
directly with `--workload <abs path to sq_reload_v3212>` so every trace and
manifest is retained under `evidence/`. These are census/pilot artifacts;
oracle outcomes were recorded but never used to select ordinals.

Raw evidence:
`audit_v3_3_2/sq_workload/evidence/static_evidence.txt`,
`.../run_commands.txt`,
`.../contexts_summary.csv`,
`.../contexts_extracted.jsonl`,
`.../original_comparison.json`,
and the per-run directories `.../establish/`, `.../contexts/`, `.../original/`
(each with `manifest.json`, `pilot_meta.json`, `command.txt`, `stdout.log`,
`stderr.log`, `oracle.log`, `trace_v31.jsonl`, `lsq_fwd_injections.log`).

**Concurrency discipline:** all 24 gem5 runs were executed one process at a
time. No run timed out; each fault run reports exactly one injection.

---

## 1. Original workload evidence (same binary, real runs)

Re-run on the current binary `d3807fbe…`, seed = the model's R01 seed,
`--event-ordinal 1` (the frozen Excel ordinal). Full traces COMPLETE/VALID.

| Model | Workload | store seq | store addr | model record | reload_seq | consumer_seq | terminal | oracle |
|---|---|---:|---|---|---:|---:|---|---|
| SQ01 | W3 `sq_drain` | 18 | `0x7ffffefd10` | `STORE_COMMITTED_LANE_NOT_READ`; `mem_write_hash=a09e307a7f948acd`, `reload_data_hash=null`, `consumer_hash=null` | 0 | 0 | MASKED | PASS (`ba3b3185e541ad03`) |
| SQ03 | W3 `sq_drain` | 18 | `0x7ffffefd10` | `LIFECYCLE_ONLY` / `NO_DOWNSTREAM_EFFECT`; `canWB 0→1`; writeback 140910, commit 149380, drain 198275, `visible_before_commit=0` | 0 | 0 | MASKED | PASS (`ba3b3185e541ad03`) |
| SP05 | W6 `store_path` | 18 | `0x7ffffefd10` | `NO_RELOAD_OBSERVED`; complete_tick 150150, `storesToWB 4→3`, `mem_sent=0`, `write_skipped=1` | 0 | 0 | MASKED | PASS (`2543a2a60de01795`) |

Sources: `evidence/original/{SQ01_sq_drain_K1,SQ03_sq_drain_K1,SP05_store_path_K1}/`.
The selected ordinal-1 store is the C-runtime startup store, not the workload
array lane in either workload. Structurally, W3 and W6 make their stores once
per iteration and read the array back **only once at end of program** (W3
`ldrb w2,[x5],#1` @ `0x400590`; W6 `ldrb w0,[x4],#1` @ `0x400698`) — there is no
per-store reload consumer in either.

---

## 2. `sq_reload_v3212` evidence

### 2.1 Disassembly difference (real `objdump -d --disassemble=main`)

`sq_reload_v3212` main loop:

```
400538: sxtw  x0, w7
40053c: str   x6, [x8, x0, lsl #3]      ; the store (buf[i] = v)
400540: dmb   ish                       ; write/read barrier -> SQ drain
400544: ldr   x4, [x8, x0, lsl #3]      ; same-address reload (L1D consumer)
400548: mov   w0, #0
400550: lsr   x3, x4, x0                ; byte-wise FNV-1a over the reloaded value
400554: and   x3, x3, #0xff
400558: eor   x2, x3, x2
40055c: add   w0, w0, #8
400560: mul   x2, x2, x5
400564: cmp   w0, #0x40
400568: b.ne  400550 <main+0x60>
40056c: cmp   x4, x6                    ; r == v ?
400570: b.ne  4005a4 <main+0xb4>       ; corrupt path (control divergence)
400574: add   x1, x1, #1               ; equal path: path += 1
...
400584: b.ne  400538 <main+0x48>       ; next iteration
```

W3 `sq_drain` has stores (`strb w0,[x1]` @ `0x400530`, `strb w3,[x1,#1]` @
`0x400538`, `strb w0,[x1],#16` @ `0x400560`) and one end-of-program bulk read.
W6 `store_path` has five store regions (vectorised `str q0,[x0],#16` @
`0x400558/0x4005a0/0x4005d8`, `strb w1,[x2,x0]` @ `0x400644`, `strb w1,[x0],#4`
@ `0x400670`) and one end-of-program bulk read. Only `sq_reload_v3212` places a
same-address reload **immediately after** a `dmb ish` for every stored lane
(difference source: `evidence/static_evidence.txt`).

### 2.2 Target-event difference

- SQ01 hook is `lsq_write_sq_entry` (`SQEntry::_data[0] ^= 0x08`). `sq_reload`
  makes that SQ entry the sole source of the value the very next load reads.
- SQ03 hook is `executeStore` `_canWB` (plus paired `storesToWB`), unchanged;
  `sq_reload` adds the later same-address load that can observe early
  visibility.
- SP05 hook is `commitStores` selection + premature `completeStore` in
  `writebackStores` (`_completed 0→1`, `storesToWB −1`, `mem_sent=0`); the
  `sq_reload` reload reads the lane whose write was skipped.

The dynamic target state is formed in all 15 contexts (injection logs in
`evidence/contexts/*/lsq_fwd_injections.log`):

- SQ01: `Site: lsq_write_sq_entry`, `FaultType: sq01_bit3_flip`, one event.
- SQ03: `Site: executeStore_canWB`, `canwb_before=0 canwb_after=1`,
  `stores_to_wb_before=0 stores_to_wb_after=1`.
- SP05: `Site: commitStores_select` then
  `Site: writebackStores_prematureComplete`, `mem_sent=0`.

The reload is a real L1D read, not a same-cycle SQ forward, in every context:
`memory_request` has `sq_entry_id=-1`, and no `forwarding_decision` record
exists for the reload `dyn_inst_seq` (verified for all 15). For SQ01/SQ03 the
store had already written memory (`store_not_written_yet=0`); for SP05 the
store write was skipped (`store_not_written_yet=1`, no `store_mem_write`
record exists at all).

### 2.3 Ordinal establishment on the current binary

Rule frozen before probing: ROI start K\* = first eligible ordinal whose
selected store vaddr is inside `[buf, buf+0x800)` = `[0x491990, 0x492190)`,
address-only, outcome-blind. Boundary probes on `d3807fbe…`:

| Model | K\*−1 probe | K\* probe | Eligible streams |
|---|---|---|---|
| SQ01 | K=1005 → seq 12097, va `0x7ffffefbe8` (stack) | K=1006 → seq 12108, va `0x491990` (`buf[0]`) | funnel `attempted=1604 eligible=1604` |
| SQ03 | K=1008 → seq 12097, va `0x7ffffefbe8` | K=1009 → seq 12108, va `0x491990` | `eligible=1009` at the target |
| SP05 | K=939 → seq 12097 (guest libc abort, see below) | K=940 → seq 12108, va `0x491990` | `selected=1 fired=1 injected=1 eligible=940` |

So **K\* = 1006 (SQ01), 1009 (SQ03), 940 (SP05)** on the current binary —
identical to the v3.2.12 preflight, now re-measured on `d3807fbe…`. One honest
gap: the SP05 K=939 boundary probe aborted inside the guest libc
(`__libc_start_main` backtrace, no `pilot_meta.json`), exactly as recorded in
the v3.2.12 preflight. Its selected seq 12097 is the same dynamic store whose
address `0x7ffffefbe8` is measured by the SQ01/SQ03 K\*−1 traces.

Percentile construction (frozen convention, matching
`audit_v3_3_1/roi/LSU_60Context_ROI_Percentile_Mapping.csv`): rank
`k = ceil(p*128)` = **13, 39, 64, 90, 116** for p = 0.1/0.3/0.5/0.7/0.9, where
k is the 1-indexed rank inside the 128-store ROI, so the absolute eligible
ordinal is `K* + (k−1)`:

- SQ01: 1018, 1044, 1069, 1095, 1121
- SQ03: 1021, 1047, 1072, 1098, 1124
- SP05: 952, 978, 1003, 1029, 1055

All 15 contexts are distinct: 15/15 unique `(model, store_seq, store_addr)`,
15/15 COMPLETE/VALID traces, one injection each, no timeouts
(`evidence/contexts_summary.csv`).

---

## 3. Five-context results per model

### 3.1 SQ01 — store-data corruption → reload → consumer

| Rank (p) | Ordinal | store seq | store PC | store addr | sq idx/gen | inject byte0 | mem_write_hash | reload seq / PC / hash | consumer seq / PC / hash | chain verdict | terminal / oracle |
|---|---:|---:|---|---|---|---|---|---|---|---|---|
| 13 (0.1) | 1018 | 13328 | 0x40053c | 0x4919f0 | 956/1306 | 0x6d→0x65 | 21d267b2c8b57721 | 13330 / 0x400544 / 21d267b2c8b57721 | 13333 / 0x400550 / 21d267b2c8b57721 | COMPLETE_CHAIN | SDC / FAIL |
| 39 (0.3) | 1044 | 15122 | 0x40053c | 0x491ac0 | 982/1332 | 0x87→0x8f | d4e59c4d90e5da05 | 15124 / 0x400544 / d4e59c4d90e5da05 | 15127 / 0x400550 / d4e59c4d90e5da05 | COMPLETE_CHAIN | SDC / FAIL |
| 64 (0.5) | 1069 | 16847 | 0x40053c | 0x491b88 | 1007/1357 | 0xa0→0xa8 | 336b5d682cbd2549 | 16849 / 0x400544 / 336b5d682cbd2549 | 16852 / 0x400550 / 336b5d682cbd2549 | COMPLETE_CHAIN | SDC / FAIL |
| 90 (0.7) | 1095 | 18641 | 0x40053c | 0x491c58 | 1033/1383 | 0xba→0xb2 | e0a15931b120dcb5 | 18643 / 0x400544 / e0a15931b120dcb5 | 18646 / 0x400550 / e0a15931b120dcb5 | COMPLETE_CHAIN | SDC / FAIL |
| 116 (0.9) | 1121 | 20435 | 0x40053c | 0x491d28 | 1059/1409 | 0xd4→0xdc | 4cd11d8e73a6f3e1 | 20437 / 0x400544 / 4cd11d8e73a6f3e1 | 20440 / 0x400550 / 4cd11d8e73a6f3e1 | COMPLETE_CHAIN | SDC / FAIL |

**Explicit hash check:** `mem_write_hash == reload_data_hash == consumer_hash`
in **5/5** contexts (`contexts_summary.csv` column `hashes_equal=true`). The
injected byte is the only source of the divergence; the reload is served from
L1D after the store has written memory.

### 3.2 SQ03 — early `_canWB` permission → visibility timing

| Rank (p) | Ordinal | store seq / addr | sq idx/gen | canWB | writeback tick | drain tick | commit tick | visible before commit | reload seq / hash | effect | terminal / oracle |
|---|---:|---|---|---|---:|---:|---:|---|---|---|---|
| 13 (0.1) | 1021 | 13328 / 0x4919f0 | 956/1306 | 0→1 | 16372510 | 16372510 | 16376745 | **1** | 13330 / b6180e0c195fd2e9 | CHAIN_VISIBILITY_MOVED (`DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`) | MASKED / PASS |
| 39 (0.3) | 1047 | 15122 / 0x491ac0 | 982/1332 | 0→1 | 17001600 | 17007760 | 17005835 | **0** | 15124 / 9f995d89be67e92d | **LIFECYCLE_ONLY** (`NO_DOWNSTREAM_EFFECT`) | MASKED / PASS |
| 64 (0.5) | 1072 | 16847 / 0x491b88 | 1007/1357 | 0→1 | 17488240 | 17488240 | 17492475 | **1** | 16849 / fde383c67ac034f1 | CHAIN_VISIBILITY_MOVED | MASKED / PASS |
| 90 (0.7) | 1098 | 18641 / 0x491c58 | 1033/1383 | 0→1 | 17987200 | 17987200 | 17991435 | **1** | 18643 / aa2be3d3d60e3c9d | CHAIN_VISIBILITY_MOVED | MASKED / PASS |
| 116 (0.9) | 1124 | 20435 / 0x491d28 | 1059/1409 | 0→1 | 18628225 | 18628225 | 18632460 | **1** | 20437 / c7d78aff5e06edf9 | CHAIN_VISIBILITY_MOVED | MASKED / PASS |

**Explicit SQ03 statement:** this is a **visibility-timing shift**
(`CHAIN_VISIBILITY_MOVED`), **not a software-visible SDC**. The model changes
no address, size or data (`address_modified=0`, `size_modified=0`,
`data_modified=0`; oracle PASS in 5/5). The honest split is **4/5 contexts moved
visibility before commit; 1/5 (ordinal 1047 / rank 39 / 30%) did not** — there
`writeback_tick=17001600 < commit_tick=17005835 < drain_tick=17007760`, the
reload request happens at 17010455, after the drain, and it reads the correct
data. This context-level variation was not visible in the earlier consecutive
B series (K\*..K\*+4, all five moved); the percentile spread exposes it, and it
must be reported rather than suppressed.

### 3.3 SP05 — premature completion → skipped write → stale reload

| Rank (p) | Ordinal | store seq / addr | sq idx/gen | complete tick | storesToWB | mem_sent | write skipped | reload seq / PC / hash | consumer seq / PC / hash | model stage | terminal / oracle |
|---|---:|---|---|---|---:|---:|---:|---|---|---|---|
| 13 (0.1) | 952 | 13328 / 0x4919f0 | 956/1306 | 16377515 | 1→0 | 0 | 1 | 13330 / 0x400544 / a8c7f832281a39c5 | 13333 / 0x400550 / a8c7f832281a39c5 | RELOAD_UNVERIFIABLE | SDC / FAIL |
| 39 (0.3) | 978 | 15122 / 0x491ac0 | 982/1332 | 17006605 | 1→0 | 0 | 1 | 15124 / 0x400544 / a8c7f832281a39c5 | 15127 / 0x400550 / a8c7f832281a39c5 | RELOAD_UNVERIFIABLE | SDC / FAIL |
| 64 (0.5) | 1003 | 16847 / 0x491b88 | 1007/1357 | 17493245 | 1→0 | 0 | 1 | 16849 / 0x400544 / a8c7f832281a39c5 | 16852 / 0x400550 / a8c7f832281a39c5 | RELOAD_UNVERIFIABLE | SDC / FAIL |
| 90 (0.7) | 1029 | 18641 / 0x491c58 | 1033/1383 | 17992205 | 1→0 | 0 | 1 | 18643 / 0x400544 / a8c7f832281a39c5 | 18646 / 0x400550 / a8c7f832281a39c5 | RELOAD_UNVERIFIABLE | SDC / FAIL |
| 116 (0.9) | 1055 | 20435 / 0x491d28 | 1059/1409 | 18633230 | 1→0 | 0 | 1 | 20437 / 0x400544 / a8c7f832281a39c5 | 20440 / 0x400550 / a8c7f832281a39c5 | RELOAD_UNVERIFIABLE | SDC / FAIL |

SP05 specifics, all 5/5:

- `completeStore` really fires: `sp05_complete` record
  (`site=lsq_completeStore`, `completed_before=0 → after=1`,
  `stores_to_wb_before=1 → after=0`, `mem_sent=0`).
- The write is skipped: `write_skipped=1` and **no `store_mem_write` record
  exists** in any SP05 trace.
- Visibility: `memory_request` for the reload has `store_not_written_yet=1`,
  and the reload response is the zero word (`data_hex=0000000000000000`,
  hash `a8c7f832281a39c5`) — the same constant in all five contexts because
  each lane is zero-initialised; the correct value would hash differently.
- The consumer **is** observed: `consumer_commit` at seq 13333/15127/16852/
  18646/20440, PC `0x400550`, carrying the same `a8c7f832281a39c5`.
- Instrumentation gap: `store_data_fnv=null`, `data_correct=null`,
  `stage_outcome=RELOAD_UNVERIFIABLE` in 5/5. The model record therefore does
  **not itself prove** the lost value; the SDC claim rests on
  `write_skipped=1` + `mem_sent=0` + the absence of `store_mem_write` + the
  stale-zero reload hash + the oracle differential. Wiring `store_data_fnv`
  (and the early-anomaly event) is an approval prerequisite for a
  model-record-grade SP05 claim.

### 3.4 Tool-classification caveat (all models)

The frozen closure tool's generic field reports
`fault_effect_propagation_coverage = LIFECYCLE_ONLY` for every context,
including the SQ01 and SP05 SDC runs (`value_divergence_count = 0`). That is a
known generic-field limitation, not the model verdict. Quote the model records
(`sq01_chain`, `sq03_effect`, `sp05_stage`) and the oracle terminal; do not
relabel the tool output.

---

## 4. Comparison: original W3/W6 vs `sq_reload_v3212` (same binary)

| Model | Original terminal | Original chain | `sq_reload` 5-context terminal | Real difference |
|---|---|---|---|---|
| SQ01 | MASKED / PASS, `STORE_COMMITTED_LANE_NOT_READ`, reload 0, consumer 0 | no per-store consumer | **SDC 5/5**, `COMPLETE_CHAIN`, hash-equal chain | fault reaches an architectural consumer only on `sq_reload` |
| SQ03 | MASKED / PASS, `LIFECYCLE_ONLY`, `visible_before_commit=0`, reload 0 | no later load on the lane | **MASKED 5/5**, `CHAIN_VISIBILITY_MOVED` 4/5 + `LIFECYCLE_ONLY` 1/5 | early visibility is measurable on `sq_reload`; still not SDC |
| SP05 | MASKED / PASS, `NO_RELOAD_OBSERVED`, reload 0 | no reader of the skipped lane | **SDC 5/5**, reload reads stale zero, consumer observed | lost write becomes architecturally visible only on `sq_reload` |

No `NO_INJECTION` occurred in any of the 18 fault runs (original or candidate);
the injection count is 1 in every case. The difference is the consumer, not
the trigger.

---

## 5. Fault-semantics match

The fault models are unchanged (same hooks, target fields, masks and
selectors; no model source was touched):

- SQ01: `SQEntry::_data[0]`, byte0 `^ 0x08`, one-shot, F0; observed
  `0x6d→0x65`, `0x87→0x8f`, etc. — exactly one bit per context.
- SQ03: `SQEntry::_canWB` 0→1 at `executeStore`, paired `storesToWB +1`, no
  address/size/data change; observed as declared in 5/5.
- SP05: `_completed` 0→1 via the real `completeStore`, `storesToWB −1`,
  `mem_sent=0`, one shot; observed in 5/5.

What changes is the workload/oracle identity and the eligible-ordinal space,
not the fault semantics.

---

## 6. Golden / oracle identity

- Candidate: `sq_reload_v3212` golden `7df5034c23f3e703` (file SHA
  `24e3f93c…`), matching `host.out`. Oracle is sensitive here: SQ01 FAIL in
  5/5 and SP05 FAIL in 5/5; SQ03 PASS is expected by design (no data change).
- Original W3: golden `ba3b3185e541ad03`; oracle PASS in the SQ01/SQ03 runs.
- Original W6: golden `2543a2a60de01795`; oracle PASS in the SP05 run.
- The workbook has **no W1–W8 row** for `sq_reload_v3212`; adopting it requires
  a new/overridden workload+oracle identity. Sheet6 W6's `ExpectedGolden`
  field remains stale (`7284dc0b3f6c64cf` vs `2543a2a60de01795`), an existing
  workbook defect that any edit must fix.

---

## 7. Five-context feasibility (explicit answer)

**Yes, for all three models, as measured.** Each model produced five
**distinct** contexts at 10/30/50/70/90% of the 128-store ROI:

| Model | ROI start K\* | Context ordinals (rank 13/39/64/90/116) | store seqs | addresses | distinct | COMPLETE/VALID |
|---|---|---|---|---|---|---|
| SQ01 | 1006 | 1018, 1044, 1069, 1095, 1121 | 13328, 15122, 16847, 18641, 20435 | 0x4919f0, 0x491ac0, 0x491b88, 0x491c58, 0x491d28 | 5/5 | 5/5 |
| SQ03 | 1009 | 1021, 1047, 1072, 1098, 1124 | same five | same five | 5/5 | 5/5 |
| SP05 | 940 | 952, 978, 1003, 1029, 1055 | same five | same five | 5/5 | 5/5 |

The three models share the same five dynamic stores but count them in
different eligible-ordinal spaces (K\* differs: 1006/1009/940), as required by
"the model's own selector".

---

## 8. Final recommendation (one per model)

| Model | Recommendation | Basis |
|---|---|---|
| **SQ01** | **ADOPT** `sq_reload_v3212` | 5/5 distinct percentile contexts produce a `COMPLETE_CHAIN` SDC with `mem_write_hash == reload_data_hash == consumer_hash`; the original W3 run is MASKED with `reload_seq=0`. This is the strongest and cleanest replacement of the three. |
| **SQ03** | **CONDITIONAL ADOPT** | The designed consequence (early `_canWB` → visibility before commit) is observed in 4/5 percentile contexts, but 1/5 (ordinal 1047, 30%) is `LIFECYCLE_ONLY`. Terminal is MASKED, oracle PASS; this must be presented as a visibility-timing shift, never as SDC. Adopt only if the 4/5-vs-1/5 split and the MASKED label are frozen into the paper/workbook language. If the researcher requires a guaranteed 5/5 effect, the percentile rule must be re-frozen with an explicit outcome-blind justification — not by cherry-picking ordinal 1047 out. |
| **SP05** | **CONDITIONAL ADOPT** | The lost write is consumed with SDC in 5/5 and the consumer is observed, but the model record is `RELOAD_UNVERIFIABLE` because `store_data_fnv` is unwired (`null`) and the early-anomaly event is missing. Adopt only after wiring `store_data_fnv` (and the `NO_EARLY_ANOMALY_EVENT` binding) so the model record itself proves the lost value. Until then the SDC claim rests on `write_skipped=1`/`mem_sent=0`/missing `store_mem_write`/stale-zero reload hash plus the oracle differential. |

**No mapping change was made.** No Excel sheet, pilot identity, model source,
or formal workload mapping was edited by this audit. The recommendations above
are proposals for researcher approval only; no formal campaign, formal record,
or approval is claimed.

### Exact approval item

> Approve replacing the SQ workload identity for SQ01/SQ03/SP05 in sheets 5/6
> from W3 `sq_drain` (ELF `d423539c…`, golden `ba3b3185e541ad03`) and W6
> `store_path` (ELF `906b3798…`, golden `2543a2a60de01795`) to
> `sq_reload_v3212` (ELF `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6`,
> golden `7df5034c23f3e703`), with ROI start ordinals K\* = 1006 / 1009 / 940
> and five percentile `EventOrdinal`s 1018/1044/1069/1095/1121 (SQ01),
> 1021/1047/1072/1098/1124 (SQ03), 952/978/1003/1029/1055 (SP05); label SQ03
> as **MASKED / visibility-moved, not SDC**, with the measured 4/5 + 1/5 split
> recorded; and make SP05 adoption conditional on wiring `store_data_fnv` and
> the early-anomaly event. Mark the affected SampleRunIDs
> `DESIGN_CHANGE_REQUIRED` until this approval is recorded.

---

## 9. Residual gaps (stated, not zeroed)

1. No matched no-fault control was run in this round for the five new
   contexts. The v3.3.1 B series had one control (`C01B`) per model at the
   first ordinal; controls for all five contexts are an approval/formal-rerun
   item.
2. SP05 K=939 boundary probe aborted in the guest libc; no `pilot_meta.json`.
   Its selected seq 12097 and address `0x7ffffefbe8` are cross-bound from the
   SQ01/SQ03 K\*−1 traces of the same dynamic store.
3. SP05 `store_data_fnv`/`data_correct` are `null` (unwired) and the
   early-anomaly event is missing; `stage_outcome=RELOAD_UNVERIFIABLE`.
4. SQ03 ordinal 1047 does not exhibit the early-visibility effect
   (`LIFECYCLE_ONLY`); the mechanism is context-dependent at the percentile
   spread.
5. The generic closure-tool propagation field says `LIFECYCLE_ONLY` for every
   context, including SDC; model records and oracle must be quoted instead.
6. `sq_reload_v3212` has no W1–W8 baseline row; a no-fault baseline on the
   frozen formal binary is still required before formal adoption.
7. All evidence in this dossier is from the current on-disk binary
   `d3807fbe…`; it must not be merged with the earlier v3.2.12 pilot binary
   `720eb780…` or the final baseline `68c6ce73…`.
