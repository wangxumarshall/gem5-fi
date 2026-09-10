# method2 AGU arm formal — byte7_zero (canonical->non-canonical address)

n=384 seeds (20260900+i), checkpoint restore (cpt.237933688473) + O3 +
m2_ptrchase.rcS scheduler-walk workload, single fault per run, short
window (900s cap per run on the fault machine).

**Result: 384/384 KERNEL OOPS — P_DUE = 100.0% [99.0, 100.0] (Wilson).**

Every run: AGU byte7_zero -> non-canonical kernel address -> kfree-class
NULL/garbage deref Oops in the scheduler task-release path (sample dmesg
in sample_oops_dmesg.txt). Zero SDC, zero Masked — the address-path
corruption is deterministically fatal in kernel context.

§4.2 implication: the AGU/address-generation path has NO silent mode on
this workload family — a canonicality violation is always detected (as
a crash). The method2 field signature (garbage pointer -> translation
fault) is the expected, dominant outcome; protection = address
canonicality check at AGU output (cheap, deterministic detection).
