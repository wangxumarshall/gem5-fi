# §4.1 SDC Escape-Set Decomposition (from formal heatmaps)

| unit (campaign/cell) | protection | P_SDC [CI] | P_DUE [CI] | Reach | escape mechanism |
|---|---|---|---|---|---|
| bpu_branchy_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: predictor state, squash-recovers) |
| decode_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: decode latch) |
| example-prf-pilot<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 100.0% [34.2,100.0] | 0.0% [0.0,65.8] | 100.0% | ? (unit not in map) |
| example-prf-pilot<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,65.8] | 0.0% [0.0,65.8] | 100.0% | ? (unit not in map) |
| exec_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: int-ALU unprotected) |
| exmon_spinlock_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 100.0% [56.5,100.0] | 100.0% | A (RAS-out-of-scope: exclusive monitor state) |
| fpu_neon_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| iq_cholesky_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| iq_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: IQ unprotected) |
| l1d_reduce_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 100.0% [56.5,100.0] | 0.0% [0.0,43.5] | 100.0% | D (post-check escape via CHAOSL1DForward; cache raw vs secded_poison) |
| lsqfwd_formal_fwd<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | 100.0% | ? (unit not in map) |
| lsqfwd_fwd_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| lsqfwd_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% | ? (unit not in map) |
| mem_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| pilot_physreg_x3<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 100.0% [43.9,100.0] | 0.0% [0.0,56.1] | 100.0% | A (RAS-out-of-scope: PRF unprotected, raw=escape) |
| prf_formal_cholesky<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 3.9% [2.4,6.3] | 92.7% [89.7,94.9] | 100.0% | ? (unit not in map) |
| prf_formal_cholesky<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | ? (unit not in map) |
| prf_regchain_pilot<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 100.0% [56.5,100.0] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| prf_regchain_pilot<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | ? (unit not in map) |
| ras_regchain_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | F (RAS mechanism escape: exc_suppress swallows DUE) |
| rat_cholesky_pilot<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 0.0% [0.0,56.1] | 66.7% [20.8,93.8] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rat_cholesky_pilot<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rat_formal_cholesky<br>phys_mode=arch_frontend target_index=3 fault_model=transient_bit_flip | none | 0.3% [0.1,1.5] | 95.8% [93.3,97.4] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rat_formal_cholesky<br>phys_mode=arch_frontend target_index=9 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: RAT unprotected, raw=escape) |
| rob_cholesky_pilot<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,43.5] | 0.0% [0.0,43.5] | 100.0% | A (RAS-out-of-scope: ROB unprotected) |
| rob_formal_cholesky<br>phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip | none | 0.0% [0.0,1.0] | 0.0% [0.0,1.0] | 100.0% | A (RAS-out-of-scope: ROB unprotected) |

# §4.2 Protection Investment Priority (sorted by P_SDC × Reach)

| unit | P_SDC | Reach | SDC contribution proxy | current protection (proxy) | priority |
|---|---|---|---|---|---|
| l1d | 100.0% | 100.0% | 100.00% | none | HIGH |
| physreg | 100.0% | 100.0% | 100.00% | none | HIGH |
| rat | 0.3% | 100.0% | 0.26% | none | LOW |
| bpu | 0.0% | 100.0% | 0.00% | none | LOW |
| decode | 0.0% | 100.0% | 0.00% | none | LOW |
| exec | 0.0% | 100.0% | 0.00% | none | LOW |
| exmon | 0.0% | 100.0% | 0.00% | none | LOW |
| iq | 0.0% | 100.0% | 0.00% | none | LOW |
| ras | 0.0% | 100.0% | 0.00% | none | LOW |
| rob | 0.0% | 100.0% | 0.00% | none | LOW |
