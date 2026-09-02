# Campaign: prf_x3_formal

- cells: 8, reps/cell: 96, total runs: 768
- injector: physreg, workload: workloads/directed/reg_chain
- gem5: `/home/sdc/wangxu/gem5-fi-wangxu/CHAOS/gem5/build/ARM/gem5.opt`

## Honest boundaries (plan §11.3)
- All P_SDC are gem5 O3 conditional probabilities, NOT product FIT (no raw device rate).
- SE mode: no MMU-on translation (TLB/PTW/AGU need FS).
- Results NOT second-machine-reproduced → 'single-machine, unconfirmed'.

## Per-cell results

| cell | SDC | n_valid | P_SDC | 95% CI | first_run |
|---|---|---|---|---|---|
| layer=arch_frontend,target_arch=3,bit_indices=[0] | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[11] | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[12] | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[31] | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[32] | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[47] | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[48] | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[63] | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
