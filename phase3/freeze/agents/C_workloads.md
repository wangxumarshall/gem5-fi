# Agent C — Workloads (W10S / W14) formal-freeze report

Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` (never touched `/home/sdc/gem5-fi-mmu`).
No gem5/scons run. All verification below is native aarch64 (openEuler, gcc
10.3.1, `sudo` for pagemap).

## 0. Files changed

| file | change |
|------|--------|
| `workloads/mmu/W10S/mmu_w10s.c` | cold mode: target mmap moved to immediately before the STRB; all printf moved after the store; `W10S_STORE` still reports pre-store captures |
| `workloads/mmu/W14/mmu_w14.c` | R02 `LDXR`/`STXR` → single `LDADDAL` (LSE AMO); every context maps RW+`MAP_POPULATE`, read-touches the page, then `mprotect()`s to the restricted prot |
| `configs/fs/generated/mmu_w10s_run_M06_R02.rcS`, `..._M08_R05.rcS`, `mmu_w14_run_R01..R05.rcS` | embedded base64/gzip binary payload replaced with the new binaries |
| `workloads/mmu/W11-14/GOLDEN.md` | real outputs, page count/warm-iters corrections, mapping-order and R02 notes, hash provenance |
| `phase3/freeze/evidence/legacy_bins/mmu_{w10s,w14}.bak` + `SHA256SUMS.txt` | preserved pre-freeze binaries |

Unchanged: target VAs (R02 `0x4001100000`, R05 `0x4001400000`), neighbor delta
`0x200000`, sentinels `0x7d/0x51/0xab`, `PAGES_DEFAULT = 4096` (16 MiB, W10S's
own default, distinct from W10's 32768), `WARM_ITERS = 128`, mode semantics,
W14 contexts/VAs.

## 1. W10S cold root cause (verified from the real trace)

`runs/TEST-M06-R02C/Trace/prop_evt.txt.gz` events 8465..8494: the pre-store
Read at `va=4001100000`, `dyn_inst_seq=230707398`, is `pc=0x4198d0` =
`__strlen_asimd`'s `ldp x2,x3,[x0]` with `x0=0x4001100000`. It is followed by
`rf_writeback` then **`squash`** (event 8495); the next correct-path commit is
`pc=0x42e210` = `_itoa_word` inside the `printf("W10S_STORE ...")` number
formatting. The real store (`seq=230759401`, `pc=0x4013a8` `strb`) then does
`tlb_lookup_miss` L0 → `tlb_lookup_hit` L3: it hits the entry the squashed
wrong-path load filled. Conclusion: the read is caused by the **workload's own
printf path** (gem5 O3 wrong-path speculative `strlen`), not by kernel
populate/prefault and not by the guest environment; kernel `MAP_POPULATE`
itself creates no translation (no other target-VA event precedes the store).

Fix: remove every variadic/indirect libc call from the mapping→store window.
Cold sequence now: `sigsetjmp`/`sigaction` → `mmap(target_va, PAGE, RW,
MAP_SHARED|MAP_FIXED_NOREPLACE|MAP_POPULATE, fd, tgt*PAGE)` → `DSB SY` →
`STRB 0xAB` → `DSB SY` → readback → pagemap check → `W10S_STORE`/`W10S_RESULT`.
`madvise(MADV_NOHUGEPAGE)` on the target runs after the store (a file-backed
MAP_SHARED mapping is never khugepaged). Warm mode is unchanged except that
its `W10S_STORE` line is also emitted after the store (same pre-store captures).

### First-translation proof

Disassembly of the shipped W10S binary, cold success path (no `bl` between
`__mmap64` and the store; the selftest branch is not taken formally):

```
4012a4: bl 41b9d0 <__mmap64>
4012a8: str x0,[sp,#520]
4012ac: ldr x0,[sp,#520]
4012b0: cmn x0,#0x1
4012b4: b.ne 40121c <main+0xcfc>     ; success path
40121c: ldr w0,[sp,#444]             ; selftest flag (0 formally)
401220: cbnz w0,4012f4               ; not taken
401224: adrp x0,492000 ; 401230: str w1,[x0,#336]   ; g_fault_phase=FP_STORE
401234: dsb sy
401238: ldr x1,[sp,#520]
40123c: mov w2,#0xffffffab
401240: strb w2,[x1]                 ; <-- the EL0 store
```

Native read-watchpoint (`sudo gdb`: `rwatch *(unsigned char*)0x4001100000`)
on the cold run stopped only at `0x401258`, the post-store readback
(`ldrb w1,[x1]` at `0x401254`, immediately after the `strb` at `0x401240`):
```
Hardware read watchpoint 1: *(unsigned char*)0x4001100000
Value = 171 '\253'
0x0000000000401258 in main ()
=> 0x401258 <main+3384>: and w1, w1, #0xff
```
i.e. no architectural user read of the target VA before the store.

## 2. W10S dynamic sentinel / XOR1 checks (native, shipped binary)

PFN pair is allocation dependent; the oracle only needs `pair_xor1=1` and the
fixed sentinels. Two consecutive runs produced the same pair; real output:

```
$ sudo ./W10S/mmu_w10s --cold --target-va 0x4001100000            # rc=0
W10S_ALLOC attempt=1 pages=4096 present_pages=4096 valid_pages=4096 pair=FOUND
W10S_STORE mode=cold target_va=0x4001100000 neighbor_va=0x4001300000 buffer_va=0x4002000000 max_pages=65536 pages=4096 attempts=1 target_pfn=0x32d8470 neighbor_pfn=0x32d8471 pair_xor1=1 target_before=0x7d neighbor_before=0x51 warm_iters=0 walk=cold_write
W10S_RESULT mode=cold target_va=0x4001100000 neighbor_va=0x4001300000 neighbor_alias_va=0x4001300000 buffer_va=0x4002000000 pages_requested=4096 max_pages=65536 pages=4096 attempts=1 target_pfn=0x32d8470 neighbor_pfn=0x32d8471 pair_xor1=1 stored=0xab target_before=0x7d target_after=0xab neighbor_before=0x51 neighbor_after=0x51 target_observed=0xab neighbor_alias_observed=0x51 store_fault=0 fault_phase=none fault_addr=0x0 pagemap=ok pfn_ok=1/1 pfn_match=1 walk=cold_write warm_iters=0 m08_redirect_signature=0 m06_write_fault_signature=0 selftest_store_fault=0 result=PASS

$ sudo ./W10S/mmu_w10s --warm --target-va 0x4001400000            # rc=0
W10S_ALLOC attempt=1 pages=4096 present_pages=4096 valid_pages=4096 pair=FOUND
W10S_STORE mode=warm target_va=0x4001400000 neighbor_va=0x4001600000 buffer_va=0x4002000000 max_pages=65536 pages=4096 attempts=1 target_pfn=0x32d8470 neighbor_pfn=0x32d8471 pair_xor1=1 target_before=0x7d neighbor_before=0x51 warm_iters=128 walk=warm_hit
W10S_RESULT mode=warm target_va=0x4001400000 neighbor_va=0x4001600000 neighbor_alias_va=0x4001600000 buffer_va=0x4002000000 pages_requested=4096 max_pages=65536 pages=4096 attempts=1 target_pfn=0x32d8470 neighbor_pfn=0x32d8471 pair_xor1=1 stored=0xab target_before=0x7d target_after=0xab neighbor_before=0x51 neighbor_after=0x51 target_observed=0xab neighbor_alias_observed=0x51 store_fault=0 fault_phase=none fault_addr=0x0 pagemap=ok pfn_ok=1/1 pfn_match=1 walk=warm_hit warm_iters=128 m08_redirect_signature=0 m06_write_fault_signature=0 selftest_store_fault=0 result=PASS
```

## 3. W14 — per-context instruction evidence (shipped binary, `objdump -d`)

Alias construction for every ctx: `bl __mmap64` at `0x400ff0` (RW+`MAP_POPULATE`)
→ touch read `0x401000: ldrb w0,[x0]` → (`0x401138: bl __clear_cache` + `isb`
for R04/R05) → `0x401028: bl __mprotect` to the restricted prot.

```
R03 read  : 4010f4: 39400273  ldrb w19,[x19]          ; PROT_NONE load
R02 atomic: 401104: f8e00261  ldaddal x0,x1,[x19]     ; LSE AMO, PROT_READ alias
R01 store : 401124: 39000261  strb w1,[x19]           ; 0xc1 store, PROT_READ alias
R04/R05   : 401048 add x19,x19,#0x100 ; 401054: d63f0000 blr x0
```
(`ldxr`/`stxr` at 0x40038c/0x400404/... are glibc malloc-lock internals.)

R02 finding (answers the model/target question): the old `LDXR`/`STXR` pair was
a true atomic RMW, but its MMU events explain the old trace gap. `LDXR` is a
Read miss (trace: `translation_start mode=Read seq=105835477 pc=0x400fec`...)
that fills the target TLB entry; `STXR` is then a plain Mode=Write access that
**hits** that entry. In the tracer a full TLB hit opens no transaction
(`translation_start` is miss-triggered, tlb.cc comment "warm-hit repetitions of
a VA create no trace at all"), and `mmuNotePermission` cannot attach to
`(stxr_seq, va)`, so no Write/Atomic `permission_eval` is emitted — yet the
permission check really runs and denies (the guest takes SIGSEGV at
`0x400d000000` and the kernel issues `tlbi_match/invalidate` for it).
Moreover `--mmu_target_mode Atomic` can never match an `STXR`: gem5 sets
`Request::isAtomic()` only for AMO requests (`ATOMIC_RETURN_OP`/
`ATOMIC_NO_RETURN_OP`; `amo64.isa`). So the context truly exercised an atomic
RMW but **not** the model's "Atomic" translation class. The workload now uses
one `LDADDAL` (ARMv8.1 LSE): first access to the VA (miss) and
`Request::isAtomic()` set, one permission decision for the Atomic class.
`FEAT_LSE` is in the configured ArmRelease (`runs/.../config.ini`) and gem5
implements `ldaddal` (`src/arch/arm/isa/insts/amo64.isa`); the host reports
`atomics` in `/proc/cpuinfo`.

R03/R05 PTE finding: `MAP_POPULATE` on a `PROT_NONE` VMA installs no PTE at all
(native probe below), and the M07 trace walked a literally zero L1 descriptor
(`pte_value_before=0 descriptor_type=Invalid walk_level=L1`), i.e. a
TRANSLATION fault, not a permission fault. The workload now maps RW, touches
the page (guaranteed PTE), then mprotects to `PROT_NONE`. Native pagemap for
the exact new sequence:
```
R03 va=0x400d200000 after touch:   present=1 pfn=0x3e728e8
R03 va=0x400d200000 after mprotect(PROT_NONE): present=1 pfn=0x3e728e8
R05 va=0x400d600000 after touch:   present=1 pfn=0x3e5665d
R05 va=0x400d600000 after mprotect(PROT_NONE): present=1 pfn=0x3e5665d
```
and the old behaviour measured in the same probe:
`PROT_NONE+MAP_POPULATE: present=0`.  Raw AP/XN bits are not readable from EL0;
the gem5 trace must show the non-zero PTE and the permission_eval.

## 4. W14 native result (`./W14/mmu_w14 --all`, rc=0)

```
W14_RESULT ctx=R01 signal=11 phase=store_ro observed=0x2 observed_kind=si_code si_code=2 fault_addr=0x400d000000 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=0 msg=fault result=PASS
W14_RESULT ctx=R02 signal=11 phase=atomic_rmw_ro observed=0x2 observed_kind=si_code si_code=2 fault_addr=0x400d000000 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=0 msg=fault result=PASS
W14_RESULT ctx=R03 signal=11 phase=read_prot_none observed=0x2 observed_kind=si_code si_code=2 fault_addr=0x400d200000 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=0 msg=fault result=PASS
W14_RESULT ctx=R04 signal=11 phase=exec_xn observed=0x2 observed_kind=si_code si_code=2 fault_addr=0x400d400100 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=0 msg=fault result=PASS
W14_RESULT ctx=R05 signal=11 phase=fetch_prot_none observed=0x2 observed_kind=si_code si_code=2 fault_addr=0x400d600100 shared_before=0x1122334455667788 shared_after=0x1122334455667788 shared_changed=0 injected_success=0 msg=fault result=PASS
W14_SUMMARY pass=5/5
```
Two consecutive `--all` runs are byte-identical after normalizing `pid=`
(`diff` empty) — fixed VAs, fixed sentinels, no random data/addresses; only the
reported PID varies. Per-context `--ctx` runs give the same result lines.

## 5. Build and rcS

`build_all.sh` verified in a `/tmp` copy of the five workload dirs: it rebuilt
W10S/W11/W12/W13/W14 and reproduced exactly the repo hashes (W11–W13 unchanged:
`1393b273…`, `8fa269fd…`, `73baad4b…`); flags unchanged,
`gcc -O2 -static -march=armv8-a+simd`.

SHA256 (`legacy_bins/SHA256SUMS.txt` holds the old):
- W10S old `1e6efd74f1617134663caaab6b4aa9391d725e98de1d1cfe0e1d34da00dd27ee`
  → new **`fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3`**
- W14 old `6402b9da71f1bff63bb8d8aa628da8bd90546d55fc639a2a803d99bc3d12e89e`
  → new **`dea4330c72cf9c6d965c782257a2af40d1ba75515d13a91815590c1fcb0041c9`**

rcS runner scoping (generated templates; payload replaced, command lines
unchanged):
- `configs/fs/generated/mmu_w10s_run_M06_R02.rcS` lines 5066–5070:
  `# ---- W10S_VARIANT M06_R02 BEGIN ----`
  `/tmp/mmu-w10s --cold --target-va 0x4001100000 --file-dir "$BUF_DIR"`
  `# ---- W10S_VARIANT M06_R02 END ----`
- `configs/fs/generated/mmu_w10s_run_M08_R05.rcS` lines 5066–5070:
  same markers with `/tmp/mmu-w10s --warm --target-va 0x4001400000 --file-dir "$BUF_DIR"`.
- `configs/fs/generated/mmu_w14_run_R0{1..5}.rcS`: `/tmp/mmu-w14 --ctx R0x`.
All 7 files pass `sh -n`; the embedded payload decompresses (gzip → sha256) to
exactly the new binaries. W10S scoping must keep `--prop_mmu_va_lo
0x4001100000 --prop_mmu_va_hi 0x4001700000` (cold neighbor `0x4001300000`) and
`--mmu_target_mode Write --mmu_target_walk_level 3`.

## 6. Remaining risk (honest)

1. **Base templates.** `configs/fs/mmu_w10s_run.rcS` / `mmu_w14_run.rcS` were
   stale at start (outside this agent's write scope); as of 00:18 they were
   regenerated elsewhere and now decompress to the new hashes (verified) —
   re-check before any formal campaign.
2. **Gem5 confirmation is pending** (Main): W10S cold must show the store's
   Write translation as the first target-VA event with a full L0..L3 walk and
   no earlier Read; W14 R03/R05 must show a non-zero valid PTE (AP=00) and a
   permission decision, not `descriptor_type=Invalid`; R02 must show an
   Atomic-class miss/decision.
3. W14 R02 requires FEAT_LSE/`LDADDAL`; with LSE disabled the child SIGILLs (not caught).
4. W10S cold relies on `MAP_POPULATE` installing the leaf PTE. The old M06
   trace proved a valid L3 Page descriptor (`pte_v=6000008349efc3`) for
   `0x4001100000`, but one M07 guest mapping was left unpopulated — hence the
   W14 touch. If a future guest kernel skips MAP_POPULATE here, the cold store
   would fault on an invalid leaf (still first access, but no valid-L3 walk).
5. W10S PFN choice is allocation dependent; the oracle needs only `pair_xor1=1` + sentinels; VAs fixed.
