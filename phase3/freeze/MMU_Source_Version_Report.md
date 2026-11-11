# MMU Final Source / Binary Version Report

Date: 2026-11-12  
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` (original `/home/sdc/gem5-fi-mmu` untouched)  
Branch: `fsu`  
HEAD: `2a8422b42dcd4f2b3f388f2dee27a237d23a9242`  
Build: `scons -j16 build/ARM/gem5.opt`, BUILD_RC=0, log `phase3/freeze/build_m08_gate.log`

## Final binary

| Field | Value |
|---|---|
| Path | `CHAOS/gem5/build/ARM/gem5.opt` |
| SHA256 | `a71ce0ca21de143d9aa5ab05e29d9bee86dff213576941a3191a256f1d842024` |
| Size | 1237551576 bytes |
| mtime | 2026-11-12 00:27:28.041157812 +0800 |

## Source hashes (C++ changed in this round)

| File | SHA256 |
|---|---|
| `CHAOS/gem5/src/arch/arm/mmu.cc` | `bb2d62da2d4f2db7da00359ce85ecc860a9b30d39b3940af78b6bdb26e1bdded` |
| `CHAOS/gem5/src/arch/arm/table_walker.cc` | `54dbeeff2e40891eb018c4bf891a5446ab2b8c4fe88f69c40647c26923595985` |
| `CHAOS/gem5/src/arch/arm/table_walker.hh` | `89110e2081da62743e4c2325aa656976e945f086959bcd29f18882412e44b611` |
| `CHAOS/gem5/src/arch/arm/tlb.cc` | `1b7cc0f3a5c0ba374cf7b0886e25aa2680c46e88b47e86557823ced4fdf4c554` |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` | `884278fa4c2774eab379f3d46f833c9521125202374afb93378be29c8b6b7cf6` |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh` | `6228ac54c9d7d49f53c618125b602353a1b4dba9641dff3085ea726e3abbcdab` |

## Workload hashes

| Workload | Binary | SHA256 | Change |
|---|---|---|---|
| W9 | `workloads/mmu/W9/mmu_w9` | `4f3ddbf2615ebefcbc6e8499a862666679ba4c13e478af09dda9104ee6508c98` | unchanged (live binary embedded in rcS by the runner) |
| W10 | `workloads/mmu/W10/mmu_w10` | `20d9f249ae89981ea3bfe90873a88b8adf5c973a9ec0f13da025c1e66253262f` | fixed <code>--ctx R0x</code> VA index bug; binary embedded in rcS |
| W10S | `workloads/mmu/W10S/mmu_w10s` | `fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3` | cold target mmap immediately before STRB; all printf after store |
| W11 | `workloads/mmu/W11/mmu_w11` | `1393b2737e33db75a8dfa38dbd0fa888d7640e7fb791cb7da1df815bd21451c4` | unchanged |
| W12 | `workloads/mmu/W12/mmu_w12` | `8fa269fd88eaf9126f67cf80d5d77f13600e211948db5cd7f4b89f42c147fdbc` | unchanged |
| W13 | `workloads/mmu/W13/mmu_w13` | `6e7d926e863c15433b3887e3ac069169e510751190d4b0de5dae0e7aa886ec70` | fresh +0x1000 alias consumer before any TLBI (M05 partial-hit consume) |
| W14 | `workloads/mmu/W14/mmu_w14` | `dea4330c72cf9c6d965c782257a2af40d1ba75515d13a91815590c1fcb0041c9` | R02 LDADDAL atomic; every context populate+touch then mprotect |

## C++ changes in this round

- `mmu.cc` M08 hook: skip activation when the target instruction already has a real squash witness (`mmuSeqSquashed`), so the one-shot lands on a live translation. Fault site/location/SDC semantics unchanged.
- `CHAOSPropagation.hh/.cc`: added `mmuSeqSquashed(seq)` reading the real `mmu_txn[tid].squash_event` witness.
- No change to table_walker.cc/hh or tlb.cc in this round.

## Frozen configuration

- Authority workbook: `phase3/freeze/authority/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx` (40 FROZEN IDs, Seed `N/A_DETERMINISTIC`).
- Formal config: `phase3/freeze/authority/MMU_Formal_Config.json/.yaml` with the hashes above.
- Benchmark/checkpoint: fixed `runs/mmu_boot7/cpt.243261068760`, disk template `runs/disks/mmu_template.img`.
