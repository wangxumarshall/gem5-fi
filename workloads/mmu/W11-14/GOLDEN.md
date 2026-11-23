# W10S and W11-W14 — No-Fault Golden Oracles

All five workloads are static aarch64 EL0 programs.  W11-W14 print one
`W<nn>_RESULT` line per context and a final `W<nn>_SUMMARY pass=N/5`; W10S
prints one `W10S_RESULT` line per store mode (`--warm`, `--cold`).
`result=PASS` always means the **no-fault** expectation held.  An injected run
that changes the outcome prints `result=FAIL` plus the evidence that the fault
propagated (foreign marker, decoy sentinel, or a completed protected access).

The run scripts install the binary into `/tmp` and execute `--all`, which
forks one process per context.  PFN values are boot/allocation dependent; only
their validity (`pagemap=ok`, `pfn_ok=1/1`) and distinctness matter.

---

## W10S — MMU-PTW Store variant (M08 / M06-R02), W10 read side untouched

A file-backed buffer is populated through the buffer alias `0x4002000000`;
pagemap finds a pair of 4 KiB pages with `neighbor_pfn == target_pfn ^ 1`.
The default is `PAGES_DEFAULT = 4096` pages (16 MiB, the W10 formal sample
size) and the search may grow to `PAGES_MAX = 65536` pages (256 MiB).  The
per-process backing file is `/tmp/mmu_w10s_pages.<pid>.bin`, created and
immediately unlinked (the rcS prefers `--file-dir /var/tmp/w10s`).  The target
page gets sentinel `0x7d`, the neighbor `0x51`.  The neighbor is mapped at
`neighbor_va = target_va + 0x200000` (`0x4001600000` for the M08 default).
The workload performs one 8-bit store of `0xab` to the target VA followed by
`DSB SY`, then reads back through the target VA and the neighbor alias.

Mapping order (verified in the 2026-11-11 freeze build):
- `--warm`: target mapped at `0x4001400000` with `MAP_POPULATE`, then read
  `WARM_ITERS = 128` times (target-relevant DTLB hit).
- `--cold` / `--ctx R02`: the target mmap is the **last statement before the
  store**; `MAP_POPULATE` installs the leaf PTE (a valid L3 Page descriptor
  for the walker) without creating a user TLB entry.  Between that mmap and
  the `STRB` there is no libc call at all (a gem5 O3 wrong-path `strlen` from
  the old pre-store `printf` used to fill the TLB first).  `W10S_STORE` is
  emitted **after** the store but still carries the pre-store captures and
  still precedes `W10S_RESULT`.

| mode | pre-store state | target | expected no-fault |
|------|-----------------|--------|-------------------|
| `--warm` (default) | target VA read 128x, store is a DTLB hit | M08 store redirect | `target_observed=0xab`, `neighbor_alias_observed=0x51`, `store_fault=0`, `result=PASS` |
| `--cold` / `--ctx R02` | no user access to target VA; store is the first translation and triggers a cold write walk | M06 R02 (EL0 write) | same: `target_observed=0xab`, `neighbor_alias_observed=0x51`, `store_fault=0`, `result=PASS` |

Golden line shape (real native output, 2026-11-12, PFNs allocation dependent):

```
W10S_ALLOC attempt=1 pages=4096 present_pages=4096 valid_pages=4096 pair=FOUND
W10S_STORE mode=warm target_va=0x4001400000 neighbor_va=0x4001600000 buffer_va=0x4002000000 max_pages=65536 pages=4096 attempts=1 target_pfn=0x20278ec00 neighbor_pfn=0x20278ec01 pair_xor1=1 target_before=0x7d neighbor_before=0x51 warm_iters=128 walk=warm_hit
W10S_RESULT mode=warm target_va=0x4001400000 neighbor_va=0x4001600000 neighbor_alias_va=0x4001600000 buffer_va=0x4002000000 pages_requested=4096 max_pages=65536 pages=4096 attempts=1 target_pfn=0x20278ec00 neighbor_pfn=0x20278ec01 pair_xor1=1 stored=0xab target_before=0x7d target_after=0xab neighbor_before=0x51 neighbor_after=0x51 target_observed=0xab neighbor_alias_observed=0x51 store_fault=0 fault_phase=none fault_addr=0x0 pagemap=ok pfn_ok=1/1 pfn_match=1 walk=warm_hit warm_iters=128 m08_redirect_signature=0 m06_write_fault_signature=0 selftest_store_fault=0 result=PASS
```

Injection evidence:
- **M08 store redirect**: `neighbor_alias_observed=0xab`, `target_observed=0x7d`,
  `m08_redirect_signature=1`, `result=FAIL` (the no-fault oracle is broken).
- **M06 R02 (cold write walk)**: `store_fault=11`,
  `fault_phase=store`, `m06_write_fault_signature=1`, `result=FAIL`
  (detected containment).  The cold run's first target-VA access is the store,
  so the walk is eligible for the M06 leaf valid-bit corruption.

The base template runs both `--warm` and `--cold` in sequence, each in its
own process.  The generated formal templates are scoped to exactly one
variant: `configs/fs/generated/mmu_w10s_run_M06_R02.rcS` runs
`--cold --target-va 0x4001100000` and `mmu_w10s_run_M08_R05.rcS` runs
`--warm --target-va 0x4001400000`; the payload block of both was rebuilt for
the 2026-11-11 freeze binary.

---

## W11 — MMU-ASID-Context-Conflict (M03)

Two pinned processes (CPU 0): A maps the fixed VA to page A/marker `0xA5`,
warms its TLB and blocks; B maps the same VA to page B/marker `0x5A` and does
the one target access.  B has never touched the VA, so its own-ASID lookup is
a miss.  A's non-global entry must stay resident (A stays alive throughout).

| ctx | target | expected `observed` | expected other fields |
|-----|--------|---------------------|-----------------------|
| R01 | LDR direct | `0x5a` | `branch=0` |
| R02 | LDR -> ADD | `0x5a` | `branch=0` |
| R03 | LDR -> CMP -> branch | `0x5a` | `branch=1` (matches B marker) |
| R04 | pointer load -> second LDR | `0x5a` | `branch=0`; A's pointer selects sentinel page 0 (`0xa5`), B's selects page 1 (`0x5a`) |
| R05 | ITLB fetch at same code VA | `0x5a` | code_A returns `0xa5`, code_B returns `0x5a`; B executes code_B |

Golden line shape (R05):

```
W11_RESULT ctx=R05 va=0x4005000000 pid_a=... pid_b=... pfn_a=0x... pfn_b=0x...
  pagemap=ok marker_a=0xa5 marker_b=0x5a observed=0x5a branch=0 stage=0
  b_signal=0 asid_source=trace pin_cpu=cpu0 expect=0x5a result=PASS
```

ASIDs are not readable from EL0; `asid_source=trace` marks that the distinct
ASID claim must be confirmed in the gem5 TLB trace.  Expected
`W11_SUMMARY pass=5/5`.

Injection evidence: `observed=0xa5` (marker A) in B with both PFNs valid and
distinct, plus the trace showing B's lookup selected A's ASID entry.

Notes:
- Data/ITLB pages are pre-filled by the parent in a memfd (fallback `/tmp`
  file) and mapped by B with `MAP_POPULATE` without any B-side user access, so
  B's target lookup is a true miss at every TLB level (this is the property
  R05 needs; a direct anonymous write by B could populate a shared L2 entry
  with B's ASID before the fetch).
- `pfn_a`/`pfn_b` are read from each process's own
  `/proc/self/pagemap` (CAP_SYS_ADMIN; root in the gem5 FS).

---

## W12 — MMU-TLB-Resident-PFN (M04)

One process maps target and decoy 4 KiB pages with distinct sentinels and
warms both, so the target access is a real DTLB/ITLB hit.

| ctx | target | expected `observed` | sentinels |
|-----|--------|---------------------|-----------|
| R01 | LDR direct | `0x7d` | target `0x7d`, decoy `0x51` |
| R02 | LDR -> ADD | `0x7d` | target `0x7d`, decoy `0x51` |
| R03 | LDR -> CMP -> branch | `0x7d` | `branch=1` |
| R04 | LDR -> address -> second LDR | `0x7d` | target `0x7d`, decoy `0x51` |
| R05 | ITLB warm hit, JIT code | `0x7d` | target code returns `0x7d`, decoy code returns `0x51` |

Golden line shape:

```
W12_RESULT ctx=R01 target_va=0x4008000000 target_pfn=0x... decoy_pfn=0x...
  observed=0x7d sentinel=0x7d decoy_sentinel=0x51 branch=0 mode=auto
  decoy_pfn_arg=0x0 decoy_arg_match=0 pagemap=ok pfn_ok=1/1 result=PASS
```

`--decoy-pfn <hex>` may pin the candidate PFN from a control run; `0` (the
rcS default) is auto mode.  When supplied, `mode=explicit` and
`decoy_arg_match=1` iff it equals the actual decoy mapping PFN.

Injection evidence: `observed=0x51` (decoy sentinel) and/or the ITLB code
returning `0x51`.  Expected `W12_SUMMARY pass=5/5`.

---

## W13 — MMU-WalkCache-PartialHit (M05)

Two 4 KiB regions exactly 2 MiB apart (`0x4010000000`, `0x4010200000`), both
`MAP_SHARED` (anonymous data, or memfd code) and `MADV_NOHUGEPAGE`.  Both are
warmed, creating compatible L2 partial entries.  The target leaf is then
invalidated from userspace with the closest legal sequence:

- data: `mprotect(target, 4096, PROT_READ)`
- code (R05): `mprotect(target, 4096, PROT_NONE)` then
  `mprotect(target, 4096, PROT_READ|PROT_EXEC)`, `__builtin___clear_cache`,
  `isb`

| ctx | target | expected `observed` | notes |
|-----|--------|---------------------|-------|
| R01 | LDR direct | `0x7d` | target sentinel `0x7d`, decoy `0x51` |
| R02 | LDR -> ADD | `0x7d` | decoy `0x51` |
| R03 | LDR -> CMP -> branch | `0x7d` | `branch=1` |
| R04 | LDR -> address -> second LDR | `0x7d` | decoy `0x51` |
| R05 | instruction fetch | `0x7d` | target code `0x7d`, decoy code `0x51` |

Golden line shape:

```
W13_SEQUENCE ctx=R01 ... mapping=MAP_SHARED anon/no-COW
  ops=mprotect(target,4096,PROT_READ) rc=0,-1 design_tlbi=VALE1IS expected_in_trace
W13_LIMITATION ctx=R01 EL0 cannot issue TLBI VALE1IS; ...
W13_RESULT ctx=R01 target_va=0x4010000000 target_pfn=0x... decoy_va=0x4010200000
  decoy_pfn=0x... observed=0x7d sentinel=0x7d decoy_sentinel=0x51 branch=0
  pagemap=ok pfn_ok=1/1 partial_hit=UNVERIFIED result=PASS
```

`partial_hit=UNVERIFIED` is deliberate: EL0 cannot observe walk-cache state or
issue `TLBI VALE1IS`.  The no-fault RESULT proves only that the legal
post-`mprotect` target access returns the target sentinel.  The actual kernel
TLBI mnemonic, leaf invalidation and partial-entry retention must be confirmed
in the gem5 TLB trace.  Expected `W13_SUMMARY pass=5/5`.

Injection evidence: `observed=0x51` after a re-walk that resumed from the
substituted L2 partial entry, with the trace showing the decoy L3 table base.
Do not claim a partial hit without that trace evidence.

---

## W14 — MMU-Permission-Guard (M07)

The parent owns one shared 4 KiB backing page through a read-write alias
(`0x400c000000`), initial value `0x1122334455667788`, JIT code at offset
`0x100` returning `0xc7`.  Each context runs in its own forked child with a
restricted alias over the same physical page.

Alias construction (2026-11-11 freeze build): the child first maps the alias
`PROT_READ|PROT_WRITE` with `MAP_SHARED|MAP_FIXED_NOREPLACE|MAP_POPULATE`,
performs a read-only touch (instantiates a valid leaf PTE), cleans the caches
for the code contexts, and only then `mprotect()`s to the context prot.
`MAP_POPULATE` on a `PROT_NONE` VMA installs no PTE at all (native pagemap:
`present=0`), which previously made R03/R05 take a TRANSLATION fault on a
zero L1 descriptor instead of a permission decision.  After the touch +
`mprotect(PROT_NONE)` the PTE stays present (native pagemap: `present=1`,
same PFN), so the access reaches the AP/XN permission decision.

| ctx | access | expected no-fault | expected fields |
|-----|--------|-------------------|-----------------|
| R01 | EL0 store through `PROT_READ` alias | SIGSEGV | `signal=11`, `si_code=2`, `shared_changed=0` |
| R02 | EL0 single-instruction atomic RMW `LDADDAL` (LSE) through `PROT_READ` alias | SIGSEGV | `signal=11`, `si_code=2`, `shared_changed=0` |
| R03 | EL0 read through `PROT_NONE` | SIGSEGV | `signal=11`, `si_code=2` |
| R04 | EL0 execute from `PROT_READ` (XN) JIT page | SIGSEGV | `signal=11`, `si_code=2`, `fault_addr=<VA>+0x100` |
| R05 | EL0 fetch from `PROT_NONE` JIT page | SIGSEGV | `signal=11`, `si_code=2`, `fault_addr=<VA>+0x100` |

R02 note: it used to be an `LDXR`/`STXR` pair.  The LDXR is a Read access
that fills the target TLB entry; the STXR is then a plain Mode=Write access
that hits that entry (warm hits open no MMU trace transaction), and the model's
`--mmu_target_mode Atomic` can never match a `STXR` (gem5 sets `is_atomic`
only for AMO requests).  The single `LDADDAL` is a true AMO: first access to
the VA (TLB miss), `Request::isAtomic()` set, one permission decision for the
"Atomic" class.  Disassembly: `0x401104: f8e00261 ldaddal x0, x1, [x19]`.

Golden line shape (R01):

```
W14_CHILD ctx=R01 pid=... phase=store_ro alias_va=0x400d000000 prot=PROT_READ access=store
W14_FAULT phase=store_ro signal=SIGSEGV
W14_RESULT ctx=R01 signal=11 phase=store_ro observed=0x2 observed_kind=si_code
  si_code=2 fault_addr=0x400d000000 shared_before=0x1122334455667788
  shared_after=0x1122334455667788 shared_changed=0 injected_success=0
  msg=fault result=PASS
```

Expected `W14_SUMMARY pass=5/5` (all contexts fault).

Injection evidence (M07 grant inversion):
- R01: `msg=done`, `injected_success=1`, `shared_changed=1`,
  `shared_after` with low byte `0xc1`, `result=FAIL` (no-fault oracle broken).
- R02: `shared_changed=1`, `shared_after = 0x1122334455667789`.
- R03: `observed` = `0x88` (first byte of the sentinel), `injected_success=1`.
- R04/R05: `observed=0xc7` (JIT code executed), `injected_success=1`.

---

## Binary provenance (2026-11-11 freeze rebuild)

Built with `workloads/mmu/build_all.sh` (`gcc -O2 -static -march=armv8-a+simd`):

| binary | SHA256 |
|--------|--------|
| `workloads/mmu/W10S/mmu_w10s` | `fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3` |
| `workloads/mmu/W14/mmu_w14` | `dea4330c72cf9c6d965c782257a2af40d1ba75515d13a91815590c1fcb0041c9` |

Superseded binaries are preserved under
`phase3/freeze/evidence/legacy_bins/` with their SHA256 recorded in
`phase3/freeze/evidence/legacy_bins/SHA256SUMS.txt`:
W10S `1e6efd74f1617134663caaab6b4aa9391d725e98de1d1cfe0e1d34da00dd27ee`,
W14 `6402b9da71f1bff63bb8d8aa628da8bd90546d55fc639a2a803d99bc3d12e89e`.

The payload blocks of the formal templates were rebuilt for these binaries:
`configs/fs/generated/mmu_w10s_run_M06_R02.rcS`,
`configs/fs/generated/mmu_w10s_run_M08_R05.rcS` and
`configs/fs/generated/mmu_w14_run_R01.rcS` … `_R05.rcS`.  The base templates
`configs/fs/mmu_w10s_run.rcS` and `configs/fs/mmu_w14_run.rcS` were outside
this agent's write scope; as of 2026-11-12 00:18 they also embed the new
payloads (verified by decompressing and hashing), matching the table above.
