# M05 Parameter Parity Report

Authoritative value: `0x4010200000` (W13_DECOY_VA; final F1 pilots R01-R05 use `--mmu_m05_decoy_table_base 0 --mmu_m05_decoy_va 0x4010200000`).

| Sample | Excel DecoyVA | Authority | Pilot | W13 symbol | Plan | Table base | Command flags | Status |
|---|---|---|---|---|---|---|---|---|
| M05-F0-W13-S01-R01 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0 | --mmu_m05_decoy_table_base 0 / --mmu_m05_decoy_va 0x4010200000 | PASS |
| M05-F0-W13-S01-R02 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0 | --mmu_m05_decoy_table_base 0 / --mmu_m05_decoy_va 0x4010200000 | PASS |
| M05-F0-W13-S01-R03 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0 | --mmu_m05_decoy_table_base 0 / --mmu_m05_decoy_va 0x4010200000 | PASS |
| M05-F0-W13-S01-R04 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0 | --mmu_m05_decoy_table_base 0 / --mmu_m05_decoy_va 0x4010200000 | PASS |
| M05-F0-W13-S01-R05 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0x4010200000 | 0 | --mmu_m05_decoy_table_base 0 / --mmu_m05_decoy_va 0x4010200000 | PASS |

Source precedence (`table_walker.cc:2979-3001`): a nonzero `--mmu_m05_decoy_va` selects the FORMAL path and forbids the pilot-only `live_partial_scan` fallback; the table base is only a consistency check when zero.

