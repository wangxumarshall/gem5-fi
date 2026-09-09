# §4.1 SDC Escape-Set Decomposition (from formal heatmaps)

| unit (campaign/cell) | protection | P_SDC [CI] | P_DUE [CI] | Reach | escape mechanism |
|---|---|---|---|---|---|
| addrmap_formal_fwd<br>target_index=0 fault_model=stuck_at_one | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| bpu_branchy_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| bpu_formal<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| bpu_formal_regchain<br>target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| decode_formal<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.3% [0.1,1.5] | 24.1% [20.1,28.6] | 100.0% | A (RAS-out-of-scope: decode latch) |
| decode_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: decode latch) |
| example-prf-pilot<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 100.0% [34.2,100.0] | 0.0% [0.0,65.8] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| example-prf-pilot<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,65.8] | 0.0% [0.0,65.8] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| exec_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| exec_formal_regchain<br>target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| exec_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| exmon_formal_spinlock<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | 100.0% | A (RAS-out-of-scope: exclusive monitor state) |
| exmon_spinlock_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 100.0% [56.5,100.0] | 100.0% | A (RAS-out-of-scope: exclusive monitor state) |
| fpu_formal_gemm<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| fpu_formal_neon<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,5.4] | 0.0% [0.0,5.4] | 17.4% | A (RAS-out-of-scope: FSU unprotected) |
| fpu_neon_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| freelist_formal_cholesky<br>target_index=3 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 72.0% [67.3,76.4] | 100.0% | A (RAS-out-of-scope: freelist unprotected) |
| freelist_formal_cholesky<br>target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 76.9% [72.3,80.8] | 100.0% | A (RAS-out-of-scope: freelist unprotected) |
| fwdphase_curve_1<br>target_index=0 bit=1 fault_model=delay_omission | none | 0.0% [0.0,3.9] | 100.0% [96.2,100.0] | 100.0% | ? (unit not in map) |
| fwdphase_curve_2<br>target_index=0 bit=2 fault_model=delay_omission | none | 0.0% [0.0,3.9] | 100.0% [96.2,100.0] | 100.0% | ? (unit not in map) |
| fwdphase_curve_4<br>target_index=0 bit=4 fault_model=delay_omission | none | 0.0% [0.0,3.9] | 100.0% [96.2,100.0] | 100.0% | ? (unit not in map) |
| fwdphase_curve_8<br>target_index=0 bit=8 fault_model=delay_omission | none | 0.0% [0.0,3.9] | 100.0% [96.2,100.0] | 100.0% | ? (unit not in map) |
| fwdsrc_formal_fwd<br>target_index=0 fault_model=stuck_at_zero | none | 37.6% [32.8,42.5] | 57.4% [52.4,62.3] | 100.0% | A (RAS-out-of-scope: store-buffer path) |
| iq_cholesky_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f5_formal_madd<br>target_index=0 fault_model=legal_domain_sub | none | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f5f6_pilot<br>target_index=0 fault_model=legal_domain_sub | none | 0.0% [0.0,43.5] | 100.0% [56.5,100.0] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f5f6_pilot<br>target_index=0 fault_model=intermittent_burst | none | 0.0% [0.0,43.5] | 100.0% [56.5,100.0] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f6_phase_curve<br>target_index=0 bit=1 fault_model=intermittent_burst | none | 0.0% [0.0,3.9] | 100.0% [96.2,100.0] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f6_phase_curve<br>target_index=0 bit=2 fault_model=intermittent_burst | none | 0.0% [0.0,3.9] | 100.0% [96.2,100.0] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f6_phase_curve<br>target_index=0 bit=4 fault_model=intermittent_burst | none | 0.0% [0.0,3.9] | 100.0% [96.2,100.0] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f6_phase_curve<br>target_index=0 bit=8 fault_model=intermittent_burst | none | 0.0% [0.0,3.9] | 100.0% [96.2,100.0] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f6_phase_curve_cholesky<br>target_index=0 bit=1 fault_model=intermittent_burst | none | 0.0% [0.0,3.9] | 5.2% [2.2,11.6] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f6_phase_curve_cholesky<br>target_index=0 bit=2 fault_model=intermittent_burst | none | 0.0% [0.0,3.9] | 3.1% [1.1,8.8] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f6_phase_curve_cholesky<br>target_index=0 bit=4 fault_model=intermittent_burst | none | 0.0% [0.0,3.9] | 8.3% [4.3,15.6] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_f6_phase_curve_cholesky<br>target_index=0 bit=8 fault_model=intermittent_burst | none | 0.0% [0.0,3.9] | 5.2% [2.2,11.6] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 75.3% [70.7,79.3] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| l1d_formal_reduce<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 97.7% [95.6,98.8] | 0.0% [0.0,1.0] | 100.0% | D (post-check escape via CHAOSL1DForward; cache raw vs secded_poison) |
| l1d_formal_reduce_secded<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | secded_poison | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | D (post-check escape via CHAOSL1DForward; cache raw vs secded_poison) |
| l1d_reduce_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 100.0% [56.5,100.0] | 0.0% [0.0,43.5] | 100.0% | D (post-check escape via CHAOSL1DForward; cache raw vs secded_poison) |
| l1dfwd_formal_reduce<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 90.9% [87.6,93.4] | 0.0% [0.0,1.0] | 100.0% | D (post-check escape: ECC-check-later datapath) |
| l1i_formal_loop<br>target_index=0 fault_model=stuck_at_zero | none | 0.0% [0.0,1.0] | 0.8% [0.3,2.3] | 100.0% | ? (unit not in map) |
| l1i_formal_loop<br>target_index=0 fault_model=stuck_at_one | none | 0.0% [0.0,1.0] | 0.3% [0.1,1.5] | 100.0% | ? (unit not in map) |
| l2_formal_reduce<br>target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | ? (unit not in map) |
| lsqfwd_formal_fwd<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 4.7% [3.0,7.3] | 27.6% [23.3,32.2] | 100.0% | A (RAS-out-of-scope: store-buffer path) |
| lsqfwd_fwd_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: store-buffer path) |
| lsqfwd_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% | A (RAS-out-of-scope: store-buffer path) |
| mem_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| mem_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| p12_setB_dram<br>fault_model=transient_bit_flip mem_addr_start=4194304 mem_addr_end=5242880 | none | 85.0% [64.0,94.8] | 0.0% [0.0,16.1] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| p12_setB_fpu<br>fault_model=transient_bit_flip | none | 100.0% [83.9,100.0] | 0.0% [0.0,16.1] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| p12_setB_l2<br>fault_model=transient_bit_flip target_block_addr=4325376 | none | 50.0% [29.9,70.1] | 0.0% [0.0,16.1] | 100.0% | ? (unit not in map) |
| p12_setB_specleak<br>fault_model=intermittent_burst target_index=10 | none | 5.6% [1.0,25.8] | 0.0% [0.0,17.6] | 90.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| p15_h2_fc_scan<br>fault_model=transient_bit_flip bit=0 target_index=3 rob=160 | none | 0.0% [0.0,27.8] | 0.0% [0.0,27.8] | 100.0% | ? (unit not in map) |
| p15_h2_repro<br>fault_model=transient_bit_flip bit=0 target_index=3 rob=128 | none | 100.0% [72.2,100.0] | 0.0% [0.0,27.8] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| p15_h2_repro<br>fault_model=transient_bit_flip bit=0 target_index=3 rob=160 | none | 0.0% [0.0,27.8] | 0.0% [0.0,27.8] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| p17_repro_fpu_svd<br>fault_model=transient_bit_flip fpu_bitseg=mant_hi | none | 92.0% [85.0,95.9] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| p17_repro_l2<br>fault_model=transient_bit_flip target_block_addr=4325376 | none | 56.0% [46.2,65.3] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| p17_repro_specleak<br>fault_model=intermittent_burst target_index=10 | none | 15.6% [9.7,24.2] | 0.0% [0.0,3.9] | 96.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| p81_campaign_smoke<br>fault_model=transient_bit_flip | none | 100.0% [20.6,100.0] | 0.0% [0.0,79.3] | 100.0% | ? (unit not in map) |
| p82_legacy_smoke<br>fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| p82_uniform_smoke<br>fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| p84_recurring_smoke<br>fault_model=recurring_result_stuck | none | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% | ? (unit not in map) |
| pilot_physreg_x3<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 100.0% [43.9,100.0] | 0.0% [0.0,56.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=0 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=0 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=0 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=1 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=1 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=1 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=2 bit=0 fault_model=transient_bit_flip | none | 100.0% [92.9,100.0] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=2 bit=2 fault_model=transient_bit_flip | none | 100.0% [92.9,100.0] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=2 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=4 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=4 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=4 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=5 bit=0 fault_model=transient_bit_flip | none | 100.0% [92.9,100.0] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=5 bit=2 fault_model=transient_bit_flip | none | 100.0% [92.9,100.0] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=5 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=6 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=6 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=6 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=7 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=7 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=7 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=19 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=19 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=19 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=29 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=29 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=29 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=30 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=30 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_abiclass_pilot<br>phys_mode=arch_frontend target_index=30 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_boundary<br>phys_mode=arch_frontend target_index=3 bit=1 fault_model=transient_bit_flip | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_boundary<br>phys_mode=arch_frontend target_index=3 bit=2 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_boundary<br>phys_mode=arch_frontend target_index=3 bit=3 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_boundary<br>phys_mode=arch_frontend target_index=3 bit=5 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_boundary<br>phys_mode=arch_frontend target_index=3 bit=7 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_boundary<br>phys_mode=arch_frontend target_index=3 bit=9 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_boundary<br>phys_mode=arch_frontend target_index=3 bit=10 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 fault_model=transient_bit_flip | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=3 bit=11 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=3 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=3 bit=32 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=3 bit=47 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=3 bit=63 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=9 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=9 bit=11 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=9 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=9 bit=32 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=9 bit=47 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_bitseg_pilot<br>phys_mode=arch_frontend target_index=9 bit=63 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_formal_cholesky<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 3.9% [2.4,6.3] | 92.7% [89.7,94.9] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_formal_cholesky<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_trigger_scan<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=128 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_trigger_scan<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=160 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_trigger_scan<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=192 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_trigger_scan_80k<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=128 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_trigger_scan_80k<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=160 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_trigger_scan_80k<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=192 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=96 phys_int=128 fault_model=transient_bit_flip | none | 100.0% [88.6,100.0] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=96 phys_int=160 fault_model=transient_bit_flip | none | 100.0% [88.6,100.0] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=96 phys_int=192 fault_model=transient_bit_flip | none | 100.0% [88.6,100.0] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=128 phys_int=128 fault_model=transient_bit_flip | none | 100.0% [88.6,100.0] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=128 phys_int=160 fault_model=transient_bit_flip | none | 100.0% [88.6,100.0] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=128 phys_int=192 fault_model=transient_bit_flip | none | 100.0% [88.6,100.0] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=128 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=160 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_h2_window_pilot<br>phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=192 fault_model=transient_bit_flip | none | 0.0% [0.0,11.3] | 0.0% [0.0,11.3] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_ptrchase_phys_pilot<br>phys_mode=phys target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| prf_ptrchase_pilot<br>phys_mode=arch_frontend target_index=0 bit=0 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| prf_ptrchase_pilot<br>phys_mode=arch_frontend target_index=0 bit=31 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| prf_ptrchase_pilot<br>phys_mode=arch_frontend target_index=0 bit=63 fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| prf_regchain_pilot<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 100.0% [56.5,100.0] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_regchain_pilot<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| ptw_h7_pilot_fs<br>target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% | ? (unit not in map) |
| ptw_h7_pilot_fs<br>target_index=0 fault_model=transient_bit_flip | secded | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% | ? (unit not in map) |
| ptw_h7_pilot_fs<br>target_index=0 fault_model=stuck_at_zero | none | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% | ? (unit not in map) |
| ptw_h7_pilot_fs<br>target_index=0 fault_model=stuck_at_zero | secded | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% | ? (unit not in map) |
| pwf_v11_dram_addrmap_pilot<br>fault_model=stuck_at_one mem_addr_start=4194304 mem_addr_end=5242880 | none | 88.0% [80.2,93.0] | 0.0% [0.0,3.7] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| pwf_v11_dram_formal<br>fault_model=transient_bit_flip mem_addr_start=4194304 mem_addr_end=5242880 | none | 85.4% [81.5,88.6] | 0.0% [0.0,1.0] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| pwf_v11_dram_pilot<br>fault_model=transient_bit_flip mem_addr_start=4194304 mem_addr_end=5242880 | none | 87.0% [79.0,92.2] | 0.0% [0.0,3.7] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| pwf_v11_fpu_fmaw_rec_pilot<br>fpu_mode_fma_weighted=True fault_model=transient_bit_flip | none | 99.0% [94.5,99.8] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_modes_pilot<br>fpu_bitseg=sign fault_model=transient_bit_flip | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_modes_pilot<br>fpu_bitseg=exp_hi fault_model=transient_bit_flip | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_modes_pilot<br>fpu_bitseg=exp_lo fault_model=transient_bit_flip | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_modes_pilot<br>fpu_bitseg=mant_hi fault_model=transient_bit_flip | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_modes_pilot<br>fpu_bitseg=mant_mid fault_model=transient_bit_flip | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_modes_pilot<br>fpu_bitseg=mant_lo fault_model=transient_bit_flip | none | 99.0% [94.5,99.8] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_pilot<br>fault_model=transient_bit_flip | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_recurring_pilot<br>fpu_mode_recurring_stuck=True fault_model=recurring_result_stuck | none | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_svd_formal<br>fpu_bitseg=mant_hi fault_model=transient_bit_flip | none | 92.5% [89.4,94.7] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_fpu_svd_formal<br>fpu_bitseg=mant_lo fault_model=transient_bit_flip | none | 83.1% [79.0,86.5] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v11_l2_formal<br>fault_model=transient_bit_flip target_block_addr=4325376 | none | 49.0% [44.0,53.9] | 0.0% [0.0,1.0] | 100.0% | ? (unit not in map) |
| pwf_v11_l2_pilot<br>fault_model=transient_bit_flip target_block_addr=4325376 | none | 49.0% [39.4,58.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v11_l2_size_sweep<br>fault_model=transient_bit_flip target_block_addr=4325376 l2_size=256KiB | none | 50.0% [41.5,58.5] | 0.0% [0.0,2.9] | 100.0% | ? (unit not in map) |
| pwf_v11_l2_size_sweep<br>fault_model=transient_bit_flip target_block_addr=4325376 l2_size=512KiB | none | 52.3% [43.8,60.8] | 0.0% [0.0,2.9] | 100.0% | ? (unit not in map) |
| pwf_v11_l2_size_sweep<br>fault_model=transient_bit_flip target_block_addr=4325376 l2_size=1MiB | none | 49.2% [40.7,57.8] | 0.0% [0.0,2.9] | 100.0% | ? (unit not in map) |
| pwf_v11_rob_specleak_depth<br>fault_model=intermittent_burst target_index=10 rob=96 | none | 8.1% [4.4,14.2] | 11.3% [6.9,18.1] | 96.9% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v11_rob_specleak_depth<br>fault_model=intermittent_burst target_index=10 rob=128 | none | 9.8% [5.7,16.4] | 13.1% [8.2,20.2] | 95.3% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v11_rob_specleak_depth<br>fault_model=intermittent_burst target_index=10 rob=160 | none | 5.6% [2.7,11.0] | 19.1% [13.2,26.8] | 98.4% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v11_rob_specleak_formal<br>fault_model=intermittent_burst target_index=10 | none | 16.5% [11.0,24.2] | 0.0% [0.0,3.1] | 94.5% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v11_rob_specleak_formal<br>fault_model=intermittent_burst target_index=9 | none | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v11_rob_specleak_formal<br>fault_model=intermittent_burst target_index=3 | none | 0.0% [0.0,2.9] | 0.0% [0.0,2.9] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v11_rob_specleak_pilot<br>fault_model=intermittent_burst target_index=10 | none | 14.0% [8.3,22.5] | 0.0% [0.0,4.0] | 93.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v12_bpu_ras_pilot<br>fault_model=delay_omission | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| pwf_v12_bpu_target_pilot<br>fault_model=local_mbu | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| pwf_v12_dram_ecc_pilot<br>fault_model=transient_bit_flip mem_addr_start=4194304 mem_addr_end=5242880 | none | 87.0% [79.0,92.2] | 0.0% [0.0,3.7] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| pwf_v12_dram_ecc_pilot<br>fault_model=transient_bit_flip mem_addr_start=4194304 mem_addr_end=5242880 | secded | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| pwf_v12_dram_ecclogic_pilot<br>fault_model=transient_bit_flip mem_addr_start=4194304 mem_addr_end=5242880 ecc_logic_fault=True | secded | 85.0% [76.7,90.7] | 0.0% [0.0,3.7] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| pwf_v12_exec_chol_pilot<br>fault_model=transient_bit_flip | none | 10.1% [5.6,17.6] | 52.5% [42.8,62.1] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| pwf_v12_exec_formal<br>fault_model=transient_bit_flip | none | 69.5% [64.8,73.9] | 20.1% [16.4,24.3] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| pwf_v12_exec_formal<br>fault_model=recurring_result_stuck | none | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| pwf_v12_exec_pilot<br>fault_model=transient_bit_flip | none | 68.0% [58.3,76.3] | 20.0% [13.3,28.9] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| pwf_v12_exec_pilot<br>fault_model=recurring_result_stuck | none | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| pwf_v12_iq_formal<br>fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 63.5% [58.6,68.2] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| pwf_v12_iq_omit_pilot<br>fault_model=transient_bit_flip | none | 0.0% [0.0,3.7] | 58.0% [48.2,67.2] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| pwf_v12_iq_pilot<br>fault_model=legal_domain_sub | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| pwf_v12_iq_pilot<br>fault_model=intermittent_burst | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=opcode | none | 0.0% [0.0,3.7] | 2.0% [0.5,7.0] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=opcode | sed | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=rn | none | 1.0% [0.2,5.5] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=rn | sed | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=rm | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=rm | sed | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=rd | none | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=rd | sed | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=imm12 | none | 1.0% [0.2,5.5] | 1.0% [0.2,5.5] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=imm12 | sed | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=cond | none | 0.0% [0.0,3.8] | 0.0% [0.0,3.8] | 100.0% | ? (unit not in map) |
| pwf_v12_l1i_fields_pilot<br>fault_model=transient_bit_flip l1i_field=cond | sed | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l2_arms_formal<br>fault_model=transient_bit_flip target_field=data | secded | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | ? (unit not in map) |
| pwf_v12_l2_arms_formal<br>fault_model=transient_bit_flip target_field=tag | secded | 51.2% [46.2,56.2] | 1.1% [0.4,2.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l2_arms_pilot<br>fault_model=transient_bit_flip target_field=data | none | 47.0% [37.5,56.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l2_arms_pilot<br>fault_model=transient_bit_flip target_field=data | secded | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l2_arms_pilot<br>fault_model=transient_bit_flip target_field=tag | none | 39.0% [29.8,49.0] | 0.0% [0.0,3.9] | 100.0% | ? (unit not in map) |
| pwf_v12_l2_arms_pilot<br>fault_model=transient_bit_flip target_field=tag | secded | 47.0% [37.5,56.7] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_l2_victim_pilot<br>fault_model=transient_bit_flip victim_fault=True l2_size=256KiB | none | 53.0% [43.3,62.5] | 0.0% [0.0,3.7] | 100.0% | ? (unit not in map) |
| pwf_v12_prf_x3_formal<br>fault_model=transient_bit_flip bit=0 target_index=3 rob=96 | none | 100.0% [99.0,100.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| pwf_v12_prf_x3_formal<br>fault_model=transient_bit_flip bit=0 target_index=3 rob=128 | none | 100.0% [99.0,100.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| pwf_v12_specleak_x10_c2_formal<br>fault_model=intermittent_burst target_index=10 | none | 5.9% [3.9,8.8] | 11.3% [8.5,14.9] | 96.9% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v12_specleak_x10_formal<br>fault_model=intermittent_burst target_index=10 | none | 14.9% [11.7,18.9] | 0.0% [0.0,1.0] | 95.8% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| pwf_v13_bpu_formal<br>fault_model=local_mbu | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| pwf_v13_bpu_formal<br>fault_model=delay_omission | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| pwf_v13_dram_c2_formal<br>fault_model=transient_bit_flip mem_addr_start=4194304 mem_addr_end=5242880 | none | 30.2% [25.8,35.0] | 0.0% [0.0,1.0] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| pwf_v13_dram_ecclogic_formal<br>fault_model=transient_bit_flip mem_addr_start=4194304 mem_addr_end=5242880 ecc_logic_fault=True | secded | 83.3% [79.3,86.7] | 0.0% [0.0,1.0] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| pwf_v13_exec_c2_formal<br>fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 52.1% [47.1,57.0] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| pwf_v13_exec_chol_formal<br>fault_model=transient_bit_flip | none | 8.7% [6.2,11.9] | 51.6% [46.6,56.6] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| pwf_v13_fpu_svd_c2_formal<br>fault_model=transient_bit_flip fpu_bitseg=mant_hi | none | 100.0% [99.0,100.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v13_fpu_svd_c2_formal<br>fault_model=transient_bit_flip fpu_bitseg=mant_lo | none | 91.1% [87.9,93.6] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| pwf_v13_l1i_formal<br>fault_model=transient_bit_flip l1i_field=imm12 | none | 0.5% [0.1,1.9] | 1.1% [0.4,2.7] | 100.0% | ? (unit not in map) |
| pwf_v13_l1i_formal<br>fault_model=transient_bit_flip l1i_field=cond | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | ? (unit not in map) |
| ras_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.1] | 0.0% [0.0,1.1] | 93.7% | F (RAS mechanism escape: exc_suppress swallows DUE) |
| ras_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | F (RAS mechanism escape: exc_suppress swallows DUE) |
| rat_cholesky_pilot<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 0.0% [0.0,56.1] | 66.7% [20.8,93.8] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rat_cholesky_pilot<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rat_f5_formal_cholesky<br>phys_mode=arch_frontend target_index=3 fault_model=legal_domain_sub | none | 0.0% [0.0,1.0] | 59.7% [54.7,64.5] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rat_f5_formal_cholesky<br>phys_mode=arch_frontend target_index=9 fault_model=legal_domain_sub | none | 0.0% [0.0,1.0] | 0.5% [0.1,1.9] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rat_formal_cholesky<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 0.3% [0.1,1.5] | 95.8% [93.3,97.4] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rat_formal_cholesky<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rob_cholesky_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: ROB unprotected) |
| rob_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: ROB unprotected) |
| specleak_branchy_pilot<br>target_index=3 fault_model=intermittent_burst | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| specleak_formal_branchy<br>target_index=3 fault_model=intermittent_burst | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| specleak_formal_branchy<br>target_index=9 fault_model=intermittent_burst | none | 0.0% [0.0,1.1] | 0.0% [0.0,1.1] | 88.5% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| specleak_formal_x19<br>target_index=19 fault_model=intermittent_burst | none | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| sysreg_f5_pilot<br>target_index=0 fault_model=legal_domain_sub | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| sysreg_f5_pilot<br>target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| tlbf5_formal_fs<br>target_index=0 fault_model=legal_domain_sub | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | ? (unit not in map) |
| tlbf5_pilot<br>target_index=0 fault_model=legal_domain_sub | none | 0.0% [0.0,65.8] | 0.0% [0.0,65.8] | 100.0% | ? (unit not in map) |

# §4.2 Protection Investment Priority (P_SDC x Reach, occupancy-weighted; weights: occupancy_cholesky_C2.stats)

| unit | P_SDC | Reach | SDC contribution | occupancy weight | weighted priority | current protection (proxy) | priority |
|---|---|---|---|---|---|---|---|
| physreg | 100.0% | 100.0% | 100.00% | 8.3% | 8.33% | none | HIGH |
| fsu | 100.0% | 100.0% | 100.00% | 8.3% | 8.33% | none | HIGH |
| l1d | 97.7% | 100.0% | 97.66% | 5.6% | 5.46% | none | HIGH |
| l1d_fwd | 90.9% | 100.0% | 90.89% | 5.6% | 5.09% | none | HIGH |
| memory | 85.4% | 100.0% | 85.42% | 0.0% | 0.00% | none | LOW |
| exec | 69.5% | 100.0% | 69.53% | 8.3% | 5.79% | none | HIGH |
| l2 | 51.2% | 100.0% | 51.21% | 1.5% | 0.77% | secded | MED |
| lsq_fwd | 37.6% | 100.0% | 37.57% | 11.9% | 4.45% | none | HIGH |
| rat | 14.9% | 95.8% | 14.33% | 11.9% | 1.70% | none | HIGH |
| l1i | 0.5% | 100.0% | 0.52% | 6.5% | 0.03% | none | LOW |
| decode | 0.3% | 100.0% | 0.26% | 0.0% | 0.00% | none | LOW |
| bpu | 0.0% | 100.0% | 0.00% | 0.0% | 0.00% | none | LOW |
| exmon | 0.0% | 100.0% | 0.00% | 0.0% | 0.00% | none | LOW |
| freelist | 0.0% | 100.0% | 0.00% | 11.9% | 0.00% | none | LOW |
| iq | 0.0% | 100.0% | 0.00% | 11.9% | 0.00% | none | LOW |
| ras | 0.0% | 93.7% | 0.00% | 0.0% | 0.00% | none | LOW |
| rob | 0.0% | 100.0% | 0.00% | 8.3% | 0.00% | none | LOW |
