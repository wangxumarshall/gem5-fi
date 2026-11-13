# M07 Parameter Parity Report

Exact VA = authority `TargetVAExact` = final F1 pilot. `--mmu_target_n 12` and the page-masked match key are unchanged.

| Sample | Authority exact | Pilot | Plan | Mode | Instruction | Page base | n | Masked key | Status |
|---|---|---|---|---|---|---|---|---|---|
| M07-F0-W14-S01-R01 | 0x400d000000 | 0x400d000000 | 0x400d000000 | Write | R01 RO Store - EL0 store through a read-only alias. | 0x400d000000 | 12 | 0x400d000000 | PASS |
| M07-F0-W14-S01-R02 | 0x400d000000 | 0x400d000000 | 0x400d000000 | Atomic | R02 RO Atomic RMW - EL0 atomic RMW through a read-only alias. | 0x400d000000 | 12 | 0x400d000000 | PASS |
| M07-F0-W14-S01-R03 | 0x400d200000 | 0x400d200000 | 0x400d200000 | Read | R03 Execute-only mapping + EL0 Load - EL0 load from a valid PAGE_EXECONLY leaf (denied by AP, not by translation). | 0x400d200000 | 12 | 0x400d200000 | PASS |
| M07-F0-W14-S01-R04 | 0x400d400100 | 0x400d400100 | 0x400d400100 | Execute | EL0 execute from a read-only (PROT_READ) JIT code page with UXN=1 (distinct VA/code blob/marker 0xc7 from R05) | 0x400d400000 | 12 | 0x400d400000 | PASS |
| M07-F0-W14-S01-R05 | 0x400d600180 | 0x400d600180 | 0x400d600180 | Execute | EL0 indirect-branch fetch into an XN page (br xN; target from runtime table; distinct VA/code blob/consumer/marker from R04) | 0x400d600000 | 12 | 0x400d600000 | PASS |

R05 note: the older closure pilot TEST-M07-R05 used `0x400d600100`; the final F1 pilot and W14 `R05_CODE_OFF=0x180` supersede it with `0x400d600180`.

