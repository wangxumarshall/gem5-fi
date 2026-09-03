# Campaign: prf_x3_readtrace_formal

- cells: 4, reps/cell: 384, total runs: 1536
- injector: physreg, workload: workloads/directed/reg_chain
- gem5: `/home/sdc/wangxu/gem5-fi-wangxu/CHAOS/gem5/build/ARM/gem5.opt`

## Honest boundaries (plan §11.3)
- All P_SDC are gem5 O3 conditional probabilities, NOT product FIT (no raw device rate).
- SE mode: no MMU-on translation (TLB/PTW/AGU need FS).
- Results NOT second-machine-reproduced → 'single-machine, unconfirmed'.

## Per-cell results

| cell | SDC | n_valid | P_SDC | 95% CI | first_run |
|---|---|---|---|---|---|
| layer=arch_frontend,target_arch=3,bit_indices=[0],RT_Benign=0,RT_Masked=0,RT_SDC=384,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 384 | 384 | 1.0000 | [0.9901,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[31],RT_Benign=0,RT_Masked=0,RT_SDC=384,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 384 | 384 | 1.0000 | [0.9901,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[32],RT_Benign=0,RT_Masked=0,RT_SDC=384,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 384 | 384 | 1.0000 | [0.9901,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[63],RT_Benign=0,RT_Masked=0,RT_SDC=384,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 384 | 384 | 1.0000 | [0.9901,1.0000] | SDC |
