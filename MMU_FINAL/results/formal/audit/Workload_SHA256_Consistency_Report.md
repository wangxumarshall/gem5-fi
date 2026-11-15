# Workload SHA256 Consistency Report

All hashes below were recomputed with `sha256sum` / Python `hashlib` on the real files; rcS payloads were base64-decoded and gunzipped.

## Bottom line

| Hash | Physical identity | Not |
|---|---|---|
| `ec525687a757fd0f3865294481c687e754c06dc6a073dd2aa80306b04621732b` | `workloads/mmu_rev/W9/Binary/mmu_w9` (canonical rev build, what the matrix records) | not the executed guest binary; not the rcS file hash |
| `4f3ddbf2615ebefcbc6e8499a862666679ba4c13e478af09dda9104ee6508c98` | `workloads/mmu/W9/mmu_w9` (live build; embedded in `configs/fs/mmu_w9.rcS` and installed at `/root/mmu_w9`) | not the hash recorded in the matrix |
| `fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3` | `workloads/mmu/W10S/mmu_w10s` (embedded in both generated W10S rcS) | not the rcS file hash |

## W9: both hashes are real, but they are different builds

- Matrix/manifest `WorkloadSHA256` = `ec525687a757fd0f3865294481c687e754c06dc6a073dd2aa80306b04621732b` = the preflight-selected canonical rev build (`workloads/mmu_rev/W9/Binary/mmu_w9`).
- Frozen campaign provenance (`provenance.json/md`) = `4f3ddbf2615ebefcbc6e8499a862666679ba4c13e478af09dda9104ee6508c98` = the live build (`workloads/mmu/W9/mmu_w9`), path-correct.
- The two `.c` sources differ: live `8a9c975330074f56319e406f8c70ce7ce3fb7c00a3b552c68f9a59a91f66004a` (no `consumer_result`) vs rev `af3d619c032a5621ecd5ef6ba6435a546d0dea63de09432053b629016776be51` (adds `consumer_result`). The two ELFs differ.
- Executed guest evidence: `configs/fs/mmu_w9.rcS` embeds `4f3ddbf2615ebefcbc6e8499a862666679ba4c13e478af09dda9104ee6508c98`; the frozen guest output has no `consumer_result` field; a direct byte scan of a formal `disk.img` contains the live format string `vec0=0x%02x result=%s` and does **not** contain the rev format string `vec0=0x%02x consumer_result=0x%02x result=%s`.
- Therefore `WorkloadSHA256` in the frozen matrix means *"preflight-selected canonical ELF"*, **not** *"executed guest binary"*. For the five M01 samples it does not identify the ELF that produced the observed output.
- This is a provenance-field limitation, not an execution divergence: the M01 fault targets the TLB, and the oracle comparison uses the output of the executed live build against the independent control. No result is reclassified here.

## W10S is a legal internal variant of W10

- Authority WorkloadID stays `W10`; the two samples are `W10S-COLD-STORE` (M06/R02) and `W10S-WARM-STORE` (M08/R05), access mode Write, documented in `phase3/freeze/authority/MMU_Formal_Config.json` and in `mmu_formal_preflight.py` `W10S_VARIANTS`.
- The executed rcS embeds `fede5f3ea4c3224f34ef9768a8cbb0fe49b071cab86306e67e7a73610f11b0a3`, which matches the matrix `WorkloadSHA256` exactly; the two W10S sample records are semantically consistent.
- The formal workload list contains six IDs (W9-W14); W10S is deliberately not a formal WorkloadID.

## Recommended field split (no original field modified)

| Proposed field | Definition |
|---|---|
| `WorkloadSourceSHA256` | SHA256 of the frozen workload C source; currently: not recorded per sample (computable) |
| `WorkloadBinarySHA256` | SHA256 of the preflight-selected canonical ELF (what the current WorkloadSHA256 records); currently: sample_manifest.workload_sha256 |
| `RuntimeScriptSHA256` | SHA256 of the rcS actually supplied to gem5; currently: computable from rcs_source / rcS.scoped |
| `WorkloadVariant` | Internal variant that keeps the authoritative WorkloadID unchanged (W10S-COLD-STORE, ...); currently: sample_manifest.workload_variant |
| `ExecutedGuestBinarySHA256` | SHA256 of the ELF actually executed inside the guest (disk /root binary or rcS payload); currently: computable: rcS embedded payload / W9 install |

## Documentation defects found

- `/home/sdc/gem5-fi-mmu-impl-v2/phase3/final/MMU_Final_40_Sample_Runner_Describe_Audit_Package_v2/MMU_Final_Provenance.txt`: labels ec5256.. with the live workloads/mmu/W9 path; the file at that path hashes to 4f3ddb..
- `/home/sdc/gem5-fi-mmu-impl-v2/phase3/freeze/authority/MMU_Formal_Config.json`: W9_note states both builds are "the same W9 source"; the two .c files and ELFs differ

## Sample dispositions

`{"FIELD_SEMANTICS_MISMATCH": 5, "OK": 35}`

The 5 `FIELD_SEMANTICS_MISMATCH` rows are exactly the five M01/W9 samples; the other 35 rows match the executed rcS payload. `mmu_formal_validate.py` does not verify `workload_sha256`; the runner does via its frozen table, which is why the matrix is internally consistent while still naming a different W9 build from the executed one.

## Verdict

`WORKLOAD_HASH_AUDIT = EXPLAINED_WITH_DOCUMENTED_LIMITATION`. W9 field semantics are now split into WorkloadSourceSHA256 / WorkloadBinarySHA256 / RuntimeScriptSHA256 / WorkloadVariant; W10S is a documented legal variant. Original SampleRunID and WorkloadID values are unchanged.
