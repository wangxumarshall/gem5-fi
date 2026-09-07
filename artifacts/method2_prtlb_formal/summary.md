# method2 PRF + TLB arm formals (the last two arms of §2.10 C)

n=384 seeds each, checkpoint restore + m2_ptrchase.rcS (scheduler-walk
workload — the KERNEL-ACTIVE regime) + O3, single fault per run.
Verdict per run: KERNEL_OOPS (handler exit, Crash/DUE) / timeout (Hang) /
clean exit without Oops (kernel survived).

| arm | P_DUE (Oops) | P_Hang | survived | verdict |
|---|---|---|---|---|
| PRF (active-only phys flip) | 25/384 = **6.5%** [4.4,9.5] | 7/384 = 1.8% | 352/384 = 91.7% | mostly absorbed; a small fatal tail |
| TLB (live-page substitution) | 384/384 = **100.0%** [99.0,100.0] | 0 | 0 | deterministically fatal under kernel-active load |

## The activity-dependence law (supersedes the steady-state-only reading)

The TLB live-page arm's result INVERTS between kernel regimes:
- steady-state (shell idle, Phase 5.4 formal): 384/384 Masked (0% Crash)
- kernel-active (scheduler-walk, this formal): 384/384 Oops (100% DUE)

The live-page substitution's danger is decided by whether the wrongly-
mapped page is ACTIVELY consumed — under kernel-active load it always
is. The Phase 5.4 'silent pathway existence proof' stands, but its
quantification was regime-limited: the worst-case P_SDC/P_DUE bound
requires the kernel-active regime. (fs oracle note: 'Oops' here is a
detected crash; the silent-SDC share of the survived runs remains
indistinguishable under this oracle.)

The PRF arm (6.5% DUE) is the smallest fatal tail of the three arms —
consistent with the SE-side forwarding-masking law plus kernel
absorption; single flips rarely reach architectural state on kernel
paths.

## Three-root-cause final table (kernel-active regime)

| arm | P_DUE | reading |
|---|---|---|
| AGU byte7_zero | 100.0% | address canonicality violation — always detected |
| TLB live-page | 100.0% | wrong-page access under active load — always fatal |
| PRF single flip | 6.5% | mostly absorbed (forwarding + kernel absorption) |

Both the AGU and TLB arms are deterministically fatal under kernel-active
load (different signatures: AGU -> kfree-class NULL deref in the
scheduler path; TLB -> wrong-page data/Oops). The method2 field signature
(kfree NULL deref) matches the AGU arm specifically.
