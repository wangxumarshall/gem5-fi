# §4.1 SDC Escape-Set Decomposition (from formal heatmaps)

| unit (campaign/cell) | protection | P_SDC [CI] | P_DUE [CI] | Reach | escape mechanism |
|---|---|---|---|---|---|
| addrmap_formal_fwd<br>target_index=0 fault_model=stuck_at_one | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| bpu_branchy_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| bpu_formal<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| decode_formal<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.3% [0.1,1.5] | 24.1% [20.1,28.6] | 100.0% | A (RAS-out-of-scope: decode latch) |
| decode_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: decode latch) |
| example-prf-pilot<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 100.0% [34.2,100.0] | 0.0% [0.0,65.8] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| example-prf-pilot<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,65.8] | 0.0% [0.0,65.8] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| exec_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| exec_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| exmon_formal_spinlock<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | 100.0% | A (RAS-out-of-scope: exclusive monitor state) |
| exmon_spinlock_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 100.0% [56.5,100.0] | 100.0% | A (RAS-out-of-scope: exclusive monitor state) |
| fpu_formal_gemm<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| fpu_formal_neon<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,5.4] | 0.0% [0.0,5.4] | 17.4% | A (RAS-out-of-scope: FSU unprotected) |
| fpu_neon_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: FSU unprotected) |
| freelist_formal_cholesky<br>target_index=3 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 72.0% [67.3,76.4] | 100.0% | A (RAS-out-of-scope: freelist unprotected) |
| freelist_formal_cholesky<br>target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 76.9% [72.3,80.8] | 100.0% | A (RAS-out-of-scope: freelist unprotected) |
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
| lsqfwd_formal_fwd<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 4.7% [3.0,7.3] | 27.6% [23.3,32.2] | 100.0% | A (RAS-out-of-scope: store-buffer path) |
| lsqfwd_fwd_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: store-buffer path) |
| lsqfwd_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% | A (RAS-out-of-scope: store-buffer path) |
| mem_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
| mem_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | E (DRAM backing store; secded via CHAOSMem protectionModel) |
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
| prf_regchain_pilot<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 100.0% [56.5,100.0] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_regchain_pilot<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
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

# §4.2 Protection Investment Priority (sorted by P_SDC × Reach)

| unit | P_SDC | Reach | SDC contribution proxy | current protection (proxy) | priority |
|---|---|---|---|---|---|
| physreg | 100.0% | 100.0% | 100.00% | none | HIGH |
| l1d | 100.0% | 100.0% | 100.00% | none | HIGH |
| l1d_fwd | 90.9% | 100.0% | 90.89% | none | HIGH |
| lsq_fwd | 37.6% | 100.0% | 37.57% | none | HIGH |
| decode | 0.3% | 100.0% | 0.26% | none | LOW |
| rat | 0.3% | 100.0% | 0.26% | none | LOW |
| memory | 0.0% | 100.0% | 0.00% | none | LOW |
| bpu | 0.0% | 100.0% | 0.00% | none | LOW |
| exec | 0.0% | 100.0% | 0.00% | none | LOW |
| exmon | 0.0% | 100.0% | 0.00% | none | LOW |
| fsu | 0.0% | 100.0% | 0.00% | none | LOW |
| freelist | 0.0% | 100.0% | 0.00% | none | LOW |
| iq | 0.0% | 100.0% | 0.00% | none | LOW |
| ras | 0.0% | 93.7% | 0.00% | none | LOW |
| rob | 0.0% | 100.0% | 0.00% | none | LOW |
