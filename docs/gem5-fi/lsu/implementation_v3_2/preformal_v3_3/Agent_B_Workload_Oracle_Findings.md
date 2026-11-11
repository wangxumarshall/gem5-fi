# Agent B — Workload / Oracle Audit (LSU pre-formal finalization, 2026-11-11)

Read-only audit of the workloads required by the 12 models
`A01, A03, FW02, FW05, SQ01, SQ03, SP05, DA04, LP01, MD04, LQ04, RP01`
(formal RunIDs W1–W8). W9 SE/FS, Store-Buffer expansion and Data Prefetcher
are out of scope.

Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
(branch `lsu-preformal-v3.3.0-20261111`). No gem5 process was started and no
tracked file was modified. Tools used: `python3/openpyxl`, `ls`, `sha256sum`,
`file`, `objdump -d`, `nm`, `readelf`-grade static inspection, `git ls-files`.

Companion data: `LSU_Workload_Oracle_Audit.csv` (same directory).

---

## 1. Authoritative design sources read

| Source | Used for |
|---|---|
| `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx` sheet `6.工作负载及无故障基线` | W1–W8 AbsolutePath / Input / Script / Binary / SHA256 / Oracle |
| same workbook, sheet `3.最终12模型矩阵` | model → WorkloadID mapping (rows 2–13) |
| same workbook, sheet `5.60个样本执行矩阵` | per-model WorkloadPath / BinarySHA256 / Oracle / WarmUp / ROI |
| `audit_v3_2_12/CLOSURE_INPUTS_v3.2.12.md`, `W1_W8_Baseline_Map_v3.2.12.csv` | frozen 9-row baseline map (W8 splits into W8a/W8b) |
| `logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv` / `FINAL_BASELINE_REPORT.md` | no-fault goldens on the FINAL binary |
| `pilots_v3_2_12/*/manifest.json`, `pilot_meta.json`, `*_records_v3.2.12*.json`, `SUPPLEMENTARY_ORACLE_MANIFEST_v3.2.12.csv` | fault/control parity and actual injected PCs |
| `tools/classify.py`, `workloads/oracle_check.py` | oracle semantics |

FINAL binary identity: `build/ARM/gem5.opt` SHA256
`68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`
(recomputed in this worktree; equals `logs_v3_2_12/binary_v3212_final_candidate.sha256`
and `GIT_COMMIT_v3212.txt`).

The workbook `AbsolutePath` values point at sibling worktrees
(`lsu-platform-v3.2`, W2 at `lsu-platform-v3.2.10`). The re-anchored copies in
this worktree are **byte-identical**: every recomputed ELF SHA256 matches the
workbook / frozen map (see §3). Source and ELF are git-tracked in
`docs/gem5-fi/lsu/implementation_v3_2/workloads/`.

---

## 2. No-fault golden evidence (item 5)

`logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv` is the real baseline
artifact: 9/9 rows on the FINAL binary `68c6ce73`, each with exit 0, the exact
ELF SHA256, printed output and verdict PASS:

| W | Workload | golden | FINAL 68c6ce73 |
|---|---|---|---|
| W1 | agu_addrmodes | `728e604ffcec539d` | PASS |
| W2 | lq_lifetime_ordinal | `b097eb83f71545cb` | PASS |
| W3 | sq_drain | `ba3b3185e541ad03` | PASS |
| W4 | sq_forward | `1f4cbf14327717df` | PASS |
| W5 | load_response | `99c106541150be0e` | PASS |
| W6 | store_path | `2543a2a60de01795` | PASS |
| W7 | replay_dependency | `59fc61c040618747` | PASS |
| W8a | fw05_forward | `67afad307642983e` | PASS |
| W8b | alignment | `3f89eab79392ce69` | PASS |

This supersedes the older `BASELINE_SUMMARY.csv` (binary `720eb780…`), which
has identical exit codes/checksums. IMPORTANT: individual **pilot/control**
evidence is not all on the final binary — DA04/FW05/LP01/MD04 pilots were run
on `e527f26a…`, FW02/SQ01/SQ03/SP05 on `720eb780…`, A01/A03 mixed
`720eb780/68c6ce73`, RP01 only on `68c6ce73`. The no-fault goldens are on the
final binary; the closure pilots are not. Binary purity (never merge records
across binaries) must be enforced by `lsu_12model_closure.py --binary-sha`.

---

## 3. Source vs ELF vs Excel SHA — exact mismatch list (item 1–2)

| W | Source (.c) SHA256 | ELF SHA256 | Excel sheet6 SHA | Verdict |
|---|---|---|---|---|
| W1 | `26fd7f61…e3a` | `90a19003…49b` | `90a19003…49b` | MATCH |
| W2 | `416cf409…d2d` (+`.S` `5be6b3d7…20a`) | `fa25f785…7ba` | **`7c69fd27…56d` (lq_lifetime)** | **MISMATCH — sheet6 W2 is stale** |
| W3 | `23f93a3f…cc2` | `d423539c…88f` | `d423539c…88f` | MATCH |
| W4 | `af19ca80…bab` | `132a84f7…297` | `132a84f7…297` | MATCH |
| W5 | `411919a1…51f` | `3779e8ce…711` | `3779e8ce…711` | MATCH |
| W6 | `8b7076dd…016` | `906b3798…bcf` | `906b3798…bcf` | MATCH |
| W7 | `b0a5073d…421` | `ca15390f…8f4` | `ca15390f…8f4` | MATCH |
| W8a | `c79b4be9…fa4` | `0cf40509…1cf` | no W8a row; sheet5 Oracle `67afad30…` | MATCHES frozen FW05 map |
| W8b | `dd6f70a1…13a` | `89ff937a…8c0` | `89ff937a…8c0` | MATCH |

All nine ELFs are `ELF 64-bit LSB executable, ARM aarch64, statically linked,
not stripped`. Sizes 63,672–636,912 B (`lq_lifetime_ordinal` is freestanding,
67,304 B).

Concrete workbook defects (not ELF defects):
1. **sheet6 W2** names `lq_lifetime` (`7c69fd27…`, oracle `1624d44f…`). The
   frozen formal workload for LQ04 is `lq_lifetime_ordinal`
   (`fa25f785…`, oracle `b097eb83…`) per sheet5 and the frozen map. The
   tracked `lq_lifetime` ELF is a different, superseded build.
2. **sheet5 FW05** row has `WorkloadPath = FW05_Workload_Archive/bin/fw05_forward`
   and `BinarySHA256 = 0cf40509…`, but `BinaryPath = workloads/alignment` — an
   internal column inconsistency.
3. **sheet6 W8** has only one row (`alignment`); FW05's frozen workload
   `fw05_forward` is a second W8 workload (W8a), present in the frozen map but
   not in sheet6.
4. **run_lq_lifetime.sh** executes `./lq_lifetime`, not
   `./lq_lifetime_ordinal`; there is no run script for the frozen W2 ELF.
5. `store_path.golden` / `alignment.golden` / `lq_lifetime_ordinal.golden` use
   a `checksum=0x…` prefix while other goldens are bare hex; `oracle_check.py`
   normalises both — cosmetic only.

---

## 4. Disassembly — is the designed instruction sequence present? (item 3)

All quotes are real `objdump -d --disassemble=main` (or `_start`) output on the
tracked ELF.

- **W1 agu_addrmodes — YES.** `400558 ldr x1,[x2],#8`,
  `4005c0 ldr x2,[x5],#8`, `400604 ldr x1,[x2,#8]!` (pre-index),
  `400648 ldp x1,x6,[x2]`, `400678 ldrb w1,[x2],#3`,
  `40068c ldr x2,[x4,#4088]` (page-boundary), plus `str x0,[x1],#8`.
  Every designed addressing mode has a real load; a few modes were
  canonicalised by the compiler.
- **W2 lq_lifetime_ordinal — YES.** `_start` performs exactly five anchor
  loads (`400338 ldr x2,[x1]` … `400348 ldr x6,[x1,#32]`); `main` has
  `ldrb w1,[x4,w1,sxtw]` etc.
- **W3 sq_drain — YES (stores).** `400530 strb w0,[x1]`,
  `400538 strb w3,[x1,#1]`, `400540 stur w2,[x1,#-4]`,
  `400560 strb w0,[x1],#16`; the final `fnv1a` re-reads the whole 64 KiB
  (`400590 ldrb w2,[x5],#1`).
- **W4 sq_forward — NO.** `main` (0x4004f0–0x400700) contains **no data load
  at all**; only stores (`400534 str x1,[x2],#8`, `4005dc str x2,[x6,x1,lsl#3]`,
  `4006ac strb w2,[x3],#-1`, `stp q0` memset block). `buf` is non-volatile and
  GCC `-O2` constant-folded every "load-after-store". The designed
  store→load forwarding pair does not execute.
- **W5 load_response — YES.** Two independent loads per iteration:
  `400548 ldr x2,[x3,x2,lsl#3]`, `40054c ldr x1,[x3,x1,lsl#3]`.
- **W6 store_path — YES (stores).** `str q0,[x0],#16` (vectorised 16/32/64-bit
  regions), `strb w1,[x2,x0]`, `strb w1,[x0],#4`, final `ldrb` read-back.
  Half/word stores were vectorised into `STP Q`; no explicit `strh/str w`
  remains, but the store stream (the SP05 target, completeStore) is real.
- **W7 replay_dependency — YES.** Real same-address alias:
  `40050c str x0,[x2,x1,lsl#3]`, `40052c str x0,[x2,x4,lsl#3]`,
  `400530 ldr x1,[x2,x4,lsl#3]`.
- **W8a fw05_forward — YES.** Four distinct stores to the same address
  (`400554 str x1`, `400558 str x5`, `40055c str x6`, `400560 str x7`, all
  `[x3,x0,lsl#3]`) then `400564 ldr x0,[x3,x0,lsl#3]`.
- **W8b alignment — YES.** `400538 str w0,[x1],#4` and
  `400558 ldr w0,[x2],#4` implement the +1-offset unaligned 4-byte pair.

---

## 5. Dynamic-condition evidence — where the injections actually land (item 3/6)

Mapped every recorded `InjectionPC` to `nm` symbols and classified it against
each program's `main` range. This is the most important result of the audit.

| W | main range | injection PCs | in main? |
|---|---|---|---|
| W1 | 0x4004f0–0x400780 | 0x400790 `_start+0x10`, 0x400ad0 `__libc_start_main_impl+0x40`, 0x40c0f0/0x40c110 `_dl_aux_init` | **0/4** |
| W2 | \_start anchors | first five loads are the anchors | **YES by construction** |
| W3 | 0x4004f0–? | W3 pilots LIFECYCLE_ONLY; closure on `sq_reload_v3212` | n/a for W3 |
| W4 | 0x4004f0–0x400700 | 0x40c0c8 `_dl_aux_init`, 0x40a4f8 `sbrk`, 0x4448a4/c8 `_dl_find_object_init`, 0x422378 `_dl_protect_relro` | **0/5; main has no loads** |
| W5 | 0x4004f0–0x4005c0 | 0x4005d0 `_start+0x10`, 0x400910 `__libc_start_main_impl+0x40`, 0x4113a0/c0/c8 `_dl_aux_init` | **0/5** |
| W6 | 0x4004f0–0x400700 | v3.2.9 PCs 0x400a10/18/20/24 `__libc_start_main` (prologue stack stores); v3.2.12 on `sq_reload` | **0/5** |
| W7 | 0x4004f0–0x4005c0 | RP01: 0x4015fc `printf+0x8c`, 0x42a6d8/dc `_IO_doallocbuf`, 0x422a58 `__printf_buffer_done`, 0x44e2ec `_fini`; MD04: only 0x400530 `main` | **RP01 0/5; MD04 1/5** |
| W8a | 0x4004f0–0x400600 | 0x400564 `main+0x74` | **4/4** |
| W8b | 0x4004f0–0x400600 | 0x400538 `main+0x48` (R04/R05, ordinals 50/200); ordinals 1–3 libc | **2/5** |

Root cause: the frozen `EventOrdinal`/warm-up (`WarmUp` and `ROI` are still
`NEEDS_RESEARCHER_CONFIRMATION` in sheet5) counts eligible events from process
start. For every statically linked glibc workload the first events are in
`_start` / `__libc_start_main_impl` / `_dl_aux_init`, so ordinals 1–5/14 never
reach the workload's `main`. A01, LP01 and RP01 therefore have **no recorded
injection inside their designed loop**, and W4 cannot have one at all.

This is not "fabricated" — it is what the recorded `InjectionPC` fields and
`nm` say. It means the current pilot traces do not prove the designed dynamic
condition; they prove an incidental libc event.

---

## 6. Per-workload verdict and dependent models

| Workload | Models whose readiness depends on it | Status | Verdict |
|---|---|---|---|
| W1 agu_addrmodes | A01, A03 | PARTIAL | ELF/golden/oracle valid; ordinals select libc startup loads, A03 PC unrecorded |
| W2 lq_lifetime_ordinal | LQ04 | PARTIAL | freestanding anchors valid; sheet6 stale SHA + wrong run script; lifecycle-only oracle (expected MASKED) |
| W3 sq_drain | SQ01, SQ03 | PARTIAL | real stores + full-array read-back; only LIFECYCLE_ONLY evidence on W3; closure used sq_reload |
| W4 sq_forward | FW02 | **DESIGN_CHANGE_REQUIRED** | ELF has zero data loads in main; forwarding pair unproducible |
| W5 load_response | LP01 | PARTIAL | two-load loop valid; all ordinals select libc loads; no matched control on final binary |
| W6 store_path | SP05 | PARTIAL | store stream valid; SP05 injections were libc prologue stores / sq_reload; completion loss may HANG |
| W7 replay_dependency | MD04, RP01 | PARTIAL | str/ldr alias pair valid; RP01 5/5 and MD04 4/5 injected libc replays |
| W8a fw05_forward | FW05 | **READY** | same-address multi-store→load in main; wrong-source SDC observed; oracle demonstrably sensitive |
| W8b alignment | DA04 | **READY** | unaligned str/ldr in main; byte-enable SDC observed at ordinals 50/200 |

Counts: READY 2, PARTIAL 6, DESIGN_CHANGE_REQUIRED 1, BLOCKED 0
(9 workload rows; W8 is two ELFs).

Model-level readiness dependency:
- A01, A03 → W1
- LQ04 → W2
- SQ01, SQ03 → W3
- FW02 → W4
- LP01 → W5
- SP05 → W6
- MD04, RP01 → W7
- FW05 → W8a
- DA04 → W8b

Only FW05 (W8a) and DA04 (W8b) currently have a recorded injection inside the
designed `main` plus an oracle that demonstrably detects the designed error.

---

## 7. Oracle independence and detection capability (item 8)

The oracle is independent in every workload: the program computes a runtime
FNV-1a checksum over the data it actually produced/consumed and prints it; the
golden value comes from a **separate no-fault run** (`FINAL_BASELINE_SUMMARY.csv`,
binary `68c6ce73`); `oracle_check.py` / `tools/classify.py` compare the two.
No checksum is hard-coded in any source, and no source contains a TODO, stub,
or injection-aware branch (checked all nine `.c` files).

Detection capability differs by model design:
- Data-path models (A01/A03, SQ01, LP01, FW02, FW05, MD04, RP01, DA04) change
  the checksum when the corrupted value reaches the consumer — confirmed
  empirically for FW05 (`549c…` vs `67afad30`) and DA04 (`3f89e…4d`, `b948…`).
- Lifecycle/bookkeeping models (LQ04, SQ03, SP05) may leave the architectural
  checksum unchanged by design; the oracle can only report MASKED (or HANG for
  SP05 completion loss). That is honest, not an oracle bug, but it means these
  models cannot produce SDC evidence.
- W4's oracle would be sensitive to a forwarding error, but no forwarding
  event executes in main, so it has nothing to detect.

---

## 8. Blockers to carry into the formal round

1. **W4 / FW02 — DESIGN_CHANGE_REQUIRED.** Rebuild a forwarding workload whose
   loads survive `-O2` (volatile/opaque-asm store→load, or a different frozen
   workload), then re-run the W4 golden. Do not overwrite the tracked ELF
   without recording the new SHA.
2. **Warm-up/ROI (all models).** `WarmUp`/`ROI` remain
   `NEEDS_RESEARCHER_CONFIRMATION`. Until an event filter or a startup skip is
   frozen, ordinals 1–5/14 land in libc for W1/W5/W6/W7 (and partially W8b).
   The evidence must either re-select ordinals after a warm-up or add an
   opcode/PC filter.
3. **W3 vs supplementary workload.** SQ01/SQ03 (and the v3.2.12 SP05) closure
   records are on `sq_reload_v3212` (`bcab9cc5…`), which the frozen map states
   is **not** part of W1–W8. Either migrate the formal RunIDs to `sq_reload`
   (and update sheet6/sheet5) or re-run on W3/W6.
4. **W6 / SP05.** The W6 evidence is libc prologue stack stores; completion loss
   may HANG rather than SDC. Confirm the formal workload and the expected
   terminal before freezing.
5. **Workbook hygiene.** Fix sheet6 W2 (ordinal ELF), sheet5 FW05 BinaryPath,
   add W8a to sheet6, and provide `run_lq_lifetime_ordinal.sh`.
6. **Controls.** LP01, MD04 and DA04 have no paired control directory on the
   final binary (only no-fault baselines on older binaries); FW05/W8a has
   archive baselines R01–R05. Add matched controls on `68c6ce73` for the
   affected models before formal.

## 9. What was NOT verified

- No gem5 run was performed (out of scope); dynamic claims rest on the
  recorded `*_records_v3.2.12*.json`, `oracle.log`, `exit_code.txt` and
  `FINAL_BASELINE_SUMMARY.csv` artifacts in this worktree.
- The sibling-worktree paths named in the workbook were not visited; the
  re-anchored copies were verified by SHA256 instead.
- No workload was recompiled. The W4 finding is a property of the tracked ELF
  SHA `132a84f7…`, which is the artifact the frozen matrix names.
