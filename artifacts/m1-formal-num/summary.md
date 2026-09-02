# Campaign: method1_f5_accum_formal

- cells: 1, reps/cell: 384, total runs: 384
- injector: rat, workload: workloads/directed/accum_kernel
- gem5: `/home/sdc/wangxu/gem5-fi-wangxu/CHAOS/gem5/build/ARM/gem5.opt`

## Honest boundaries (plan §11.3)
- All P_SDC are gem5 O3 conditional probabilities, NOT product FIT (no raw device rate).
- SE mode: no MMU-on translation (TLB/PTW/AGU need FS).
- Results NOT second-machine-reproduced → 'single-machine, unconfirmed'.

## Per-cell results

| cell | SDC | n_valid | P_SDC | 95% CI | first_run |
|---|---|---|---|---|---|
| layer=physical,target_arch=9,semantic_role=int_accum,fault_model=legal_domain_sub,f5_substitute_target=-1 | 114 | 148 | 0.7703 | [0.6962,0.8307] | SimulatorError |
