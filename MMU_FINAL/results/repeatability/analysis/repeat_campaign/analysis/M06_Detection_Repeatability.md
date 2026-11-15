# M06 Detection Repeatability

## REP-FINAL-MMU-M06-R02-01 / R02

- Activation: MATCH; Propagation: MATCH; Terminal: MATCH
- Formal terminal DETECTED_CONTAINED → repeat DETECTED_CONTAINED
- Repeat oracle: `W10S_RESULT mode=cold target_va=0x4001100000 neighbor_va=0x4001300000 neighbor_alias_va=0x4001300000 buffer_va=0x4002000000 pages_requested=4096 max_pages=65536 pages=4096 attempts=1 target_pfn=0x8352c neighbor_pfn=0x8352d pair_xor1=1 stored=0xab target_before=0x7d target_after=0xab neighbor_before=`

Detection is DETECTED_CONTAINED (exception delivered), not generic masked.
