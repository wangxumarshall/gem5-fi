# Campaign: h2_window_sweep

- cells: 12, reps/cell: 96, total runs: 1152
- injector: physreg, workload: workloads/directed/reg_chain
- gem5: `/home/sdc/wangxu/gem5-fi-wangxu/CHAOS/gem5/build/ARM/gem5.opt`

## Honest boundaries (plan §11.3)
- All P_SDC are gem5 O3 conditional probabilities, NOT product FIT (no raw device rate).
- SE mode: no MMU-on translation (TLB/PTW/AGU need FS).
- Results NOT second-machine-reproduced → 'single-machine, unconfirmed'.

## Per-cell results

| cell | SDC | n_valid | P_SDC | 95% CI | first_run |
|---|---|---|---|---|---|
| layer=arch_frontend,target_arch=3,bit_indices=[0],rob_entries=96,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[0],rob_entries=128,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[0],rob_entries=160,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[63],rob_entries=96,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[63],rob_entries=128,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=3,bit_indices=[63],rob_entries=160,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=2,bit_indices=[0],rob_entries=96,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=2,bit_indices=[0],rob_entries=128,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=2,bit_indices=[0],rob_entries=160,RT_Benign=0,RT_Masked=0,RT_SDC=96,RT_Crash=0,P_SDC_given_reads_gt0=1.0000,reads_median=1975000 | 96 | 96 | 1.0000 | [0.9615,1.0000] | SDC |
| layer=arch_frontend,target_arch=2,bit_indices=[63],rob_entries=96,RT_Benign=0,RT_Masked=0,RT_SDC=0,RT_Crash=0,P_SDC_given_reads_gt0=,reads_median=7425000 | 0 | 96 | 0.0000 | [0.0000,0.0312] | Hang |
| layer=arch_frontend,target_arch=2,bit_indices=[63],rob_entries=128,RT_Benign=0,RT_Masked=0,RT_SDC=0,RT_Crash=0,P_SDC_given_reads_gt0=,reads_median=7450000 | 0 | 96 | 0.0000 | [0.0000,0.0312] | Hang |
| layer=arch_frontend,target_arch=2,bit_indices=[63],rob_entries=160,RT_Benign=0,RT_Masked=0,RT_SDC=0,RT_Crash=0,P_SDC_given_reads_gt0=,reads_median=7450000 | 0 | 96 | 0.0000 | [0.0000,0.0312] | Hang |
