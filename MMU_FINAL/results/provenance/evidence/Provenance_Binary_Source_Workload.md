# Binary / Source / Workload Provenance

## Frozen gem5 binary

- Path: `/home/sdc/gem5-fi-mmu-impl-v2/CHAOS/gem5/build/ARM/gem5.opt`
- Size: 1237801472 bytes
- SHA256: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`
- Equals all 40 sample `BinarySHA256`: **True**

## Source files (verified against the per-sample SHA256SUMS)

| File | SHA256 | Recorded | Match |
|---|---|---|---|
| `CHAOS/gem5/src/arch/arm/mmu.cc` | `bba49e65398f80aaf58b3ce5a954f4ffbd68278dd0b5c888124d249e28dd1c1b` | `bba49e65398f80aaf58b3ce5a954f4ffbd68278dd0b5c888124d249e28dd1c1b` | True |
| `CHAOS/gem5/src/arch/arm/table_walker.cc` | `54dbeeff2e40891eb018c4bf891a5446ab2b8c4fe88f69c40647c26923595985` | `54dbeeff2e40891eb018c4bf891a5446ab2b8c4fe88f69c40647c26923595985` | True |
| `CHAOS/gem5/src/arch/arm/table_walker.hh` | `89110e2081da62743e4c2325aa656976e945f086959bcd29f18882412e44b611` | `89110e2081da62743e4c2325aa656976e945f086959bcd29f18882412e44b611` | True |
| `CHAOS/gem5/src/arch/arm/tlb.cc` | `b81b7b4cc9eee2c7ba0b592775587dcc7610c8d18c237ba412d2c69ba80d52f4` | `b81b7b4cc9eee2c7ba0b592775587dcc7610c8d18c237ba412d2c69ba80d52f4` | True |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` | `38c0942ab5d2c4c73b7ee3763c1d7503b708ba9ba4f73c2fd051db6836052dc4` | `38c0942ab5d2c4c73b7ee3763c1d7503b708ba9ba4f73c2fd051db6836052dc4` | True |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh` | `90ea1b55a9a7e51db04fad4a23ceee3107ebc2d375c3d5c5902b9ffb6b2d3336` | `90ea1b55a9a7e51db04fad4a23ceee3107ebc2d375c3d5c5902b9ffb6b2d3336` | True |

## Checkpoint / kernel / bootloader

- Checkpoint: `/home/sdc/gem5-fi-mmu-impl-v2/runs/mmu_bootF1/cpt.244799013609` (10 files, 32311994 bytes)
- Kernel `/home/sdc/gem5-fi-mmu-impl-v2/gem5-fs/vmlinux`: `9b9b9ce70bc6fb831461b527ccf36f124f1af8f3dc717d7ef13e62060aecfa7e`
- Bootloader `/home/sdc/gem5-fi-mmu-impl-v2/gem5-fs/boot.arm64`: `37ca07b55da2c0843d6670bb0693d21159236e0c6b74526f531abaeeaab51bfd`

Full per-file checkpoint hashes are in the JSON.

## Workload identities

| Workload | Variant | Role | Path | SHA256 |
|---|---|---|---|---|
| W9 | canonical-rev | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu_rev/W9/Binary/mmu_w9` | `ec525687a757fd0f3865294481c687e754c06dc6a073dd2aa80306b04621732b` |
| W9 | canonical-rev | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu_rev/W9/mmu_w9.c` | `af3d619c032a5621ecd5ef6ba6435a546d0dea63de09432053b629016776be51` |
| W9 | canonical-rev | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/mmu_w9_run.rcS` | `083436ebe168e4c2dae045393d38899711abfd41c521efa05c5f4a326c5f33e2` |
| W9 | live-executed | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W9/mmu_w9` | `4f3ddbf2615ebefcbc6e8499a862666679ba4c13e478af09dda9104ee6508c98` |
| W9 | live-executed | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W9/mmu_w9.c` | `8a9c975330074f56319e406f8c70ce7ce3fb7c00a3b552c68f9a59a91f66004a` |
| W9 | live-executed | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/mmu_w9.rcS` | `2d05a2ea381e525f2efd85940e9d83949cc827a203598f3c06428349e4174490` |
| W10 | canonical | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W10/mmu_w10` | `733b8a80150b9728b640fbaad0889f139b09b92a98462778753975a4917a63ae` |
| W10 | canonical | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W10/mmu_w10.c` | `0c9458ac86112dc232bf1daf97487b3a7224f84ceaee1d67c97214f99bb1bb22` |
| W10 | canonical | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/mmu_w10_run.rcS` | `5088a508f79efec7b118b390589d73e35b82ee5774819dcc08be05aab9d66f5c` |
| W10S | variant | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W10S/mmu_w10s` | `fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3` |
| W10S | variant | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W10S/mmu_w10s.c` | `98a74c4dbb15dbb7914dbec34efe1a189e606c5078f941e1d4180c61e16b6f94` |
| W10S | variant | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/mmu_w10s_run.rcS` | `73bcaecf62c3402c39f8840a73f4d753c5cf7d597a3be8cae5ce0bbc007383c0` |
| W11 | canonical | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W11/mmu_w11` | `1393b2737e33db75a8dfa38dbd0fa888d7640e7fb791cb7da1df815bd21451c4` |
| W11 | canonical | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W11/mmu_w11.c` | `4fa8054c71d997d0b508a12d1ab0db1cb0c66bbbb5ac55a7655e9f7ed089e845` |
| W11 | canonical | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/mmu_w11_run.rcS` | `a84e72c8285776c221e34ce32404ee8a95237f302df7ae6098f8e4e043cfa459` |
| W12 | canonical | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W12/mmu_w12` | `8fa269fd88eaf9126f67cf80d5d77f13600e211948db5cd7f4b89f42c147fdbc` |
| W12 | canonical | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W12/mmu_w12.c` | `735846468787fd9f190604d73d403119f1470c885174a991cff5a8a947b372f9` |
| W12 | canonical | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/mmu_w12_run.rcS` | `3abe7a280ecb26d7110226bd08a1321daedf60c568adc5a77c8d80a980d0c5c0` |
| W13 | canonical | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W13/mmu_w13` | `6e7d926e863c15433b3887e3ac069169e510751190d4b0de5dae0e7aa886ec70` |
| W13 | canonical | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W13/mmu_w13.c` | `a5a05c337d562ec5e7d916247c229f7e3727c162ad35629721bc36fa8593edae` |
| W13 | canonical | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/mmu_w13_run.rcS` | `e6da471818ab0c3cd60bb7bea789e12e8cd83a747d192f6342e231e2e9e6c8ca` |
| W14 | canonical | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W14/mmu_w14` | `f15dc78e2efc683f2a653a40ed47d293b71c27aaa018594e67274e9098a7be36` |
| W14 | canonical | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W14/mmu_w14.c` | `261356afc15474a0dae9a060e86294bd4965a7acbbea544da59f55fee124a5d4` |
| W14 | canonical | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/mmu_w14_run.rcS` | `2f5da21c2dece5bf86ec357de4261d6684a1b046b3a8c8b9942fed725a188142` |
| W10S | generated rcS used | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W10S/mmu_w10s` | `fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3` |
| W10S | generated rcS used | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W10S/mmu_w10s.c` | `98a74c4dbb15dbb7914dbec34efe1a189e606c5078f941e1d4180c61e16b6f94` |
| W10S | generated rcS used | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/generated/mmu_w10s_run_M06_R02.rcS` | `c3b949057eef196b63b53a58c89ae533b1c27028c7a82f82ee293255ad47359e` |
| W10S | generated rcS used | Binary | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W10S/mmu_w10s` | `fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3` |
| W10S | generated rcS used | Source | `/home/sdc/gem5-fi-mmu-impl-v2/workloads/mmu/W10S/mmu_w10s.c` | `98a74c4dbb15dbb7914dbec34efe1a189e606c5078f941e1d4180c61e16b6f94` |
| W10S | generated rcS used | RuntimeScript | `/home/sdc/gem5-fi-mmu-impl-v2/configs/fs/generated/mmu_w10s_run_M08_R05.rcS` | `c7c723d114d9bd7d520f0e1524cd8e0909a10ebee5a023ea2fac6eb2a97d77d4` |

## Executed guest identity

- W9 matrix hash `ec525687a757fd0f3865294481c687e754c06dc6a073dd2aa80306b04621732b` identifies the mmu_rev build; the executed guest is the live build `4f3ddbf2615ebefcbc6e8499a862666679ba4c13e478af09dda9104ee6508c98` (rcS payload, disk image bytes, and output format all agree).
- W10S executed hash matches the matrix: `fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3`.

## Original frozen artifacts (unchanged)

- Original results ZIP: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/MMU_Final_Formal_Campaign_Results_Closure_Package.zip`
  SHA256 `caeaf6506495ed119a06a12075f5193276e2e1279286ddc56610016f39caa151`
- Original `analysis/final_summary.json` SHA256 `1451a3a1ab308ac3c8e976fbe98e4bc5e73b788cb5b2db62b9ae52fb842934fd`

No original campaign file was modified by this work.
