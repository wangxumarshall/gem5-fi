#!/usr/bin/env python3
"""Pure-python Wilson 95% score interval + the 9-class campaign denominators
(design doc `docs/KUNPENG920-故障注入方案详细工程设计.md` §1.4).

No scipy/numpy hard-dependency: this module imports only the stdlib `math` so
the campaign driver can run on a minimal host. (scipy is available on this
machine, but the tool must not gate on it — campaigns may run elsewhere.)

Definitions (§1.4):
  N_valid        = N_total - N_inactive - N_simerror
  P_SDC          = N_SDC / N_valid
  P_DUE          = (N_crash + N_hang) / N_valid
  P_escape       = (N_SDC + N_latent) / N_valid
  Reachability   = N_valid / (N_total - N_simerror)

The nine ordered classes (§1.4, classify.py):
  SimulatorError, Inactive, Corrected, DetectedContained,
  Crash, Hang, SDC, Latent, Masked
For the current SE injectors only {SimulatorError, Inactive, Crash, Hang,
SDC, Masked} occur; the protection-model classes (Corrected,
DetectedContained, Latent) appear once §1.2 lands — carried through unchanged.

Usage:
  from tools.wilson import wilson_ci, cell_stats
  lo, hi, p_hat = wilson_ci(k, n)        # k successes in n trials, 95% CI
  stats = cell_stats(counter)            # counter: {class: count}
"""
import math

# 95% Wilson z-value (two-sided). 1.96 is the standard normal 0.975 quantile.
Z95 = 1.959963984540054


def wilson_ci(k, n, z=Z95):
    """Wilson score 95% confidence interval for a binomial proportion.

    Returns (low, high, p_hat). `k` = successes, `n` = trials. If n==0
    returns (0.0, 0.0, 0.0) — no data, no claim (honest: not a 0% upper bound).
    For the k==0 case, `high` is the 95% one-sided upper bound 3/n (rule of 3),
    captured naturally by the Wilson formula — preferred over a hard 3/n hack.
    """
    if n <= 0:
        return 0.0, 0.0, 0.0
    k = max(0, min(k, n))
    phat = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (phat + z2 / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z2 / (4 * n * n))) / denom
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return lo, hi, phat


# The nine ordered outcome classes (kept in sync with tools/classify.py).
ALL_CLASSES = (
    "SimulatorError", "Inactive", "Corrected", "DetectedContained",
    "Crash", "Hang", "SDC", "Latent", "Masked",
)


def cell_stats(counter):
    """Compute the §1.4 denominator-derived statistics for one campaign cell.

    `counter`: dict {class_name: int} (counts of each classification outcome).
    Returns a dict with N_total, N_valid, the rates (point + Wilson 95% CI),
    and Reachability. All rates are 0/0 -> 0.0 (no claim) rather than NaN.
    """
    for c in ALL_CLASSES:
        counter.setdefault(c, 0)
    n_total = sum(counter[c] for c in ALL_CLASSES)
    n_inactive = counter["Inactive"]
    n_simerr = counter["SimulatorError"]
    n_valid = n_total - n_inactive - n_simerr

    n_sdc = counter["SDC"]
    n_crash = counter["Crash"]
    n_hang = counter["Hang"]
    n_latent = counter["Latent"]

    # Point estimates (guard divide-by-zero -> 0.0, no claim on empty cells).
    p_sdc = n_sdc / n_valid if n_valid else 0.0
    p_due = (n_crash + n_hang) / n_valid if n_valid else 0.0
    p_escape = (n_sdc + n_latent) / n_valid if n_valid else 0.0
    reach = n_valid / (n_total - n_simerr) if (n_total - n_simerr) else 0.0

    # Wilson 95% CI on each rate (denominator = N_valid for the rates,
    # N_total - N_simerror for reachability, per §1.4).
    sdc_lo, sdc_hi, _ = wilson_ci(n_sdc, n_valid)
    due_lo, due_hi, _ = wilson_ci(n_crash + n_hang, n_valid)
    esc_lo, esc_hi, _ = wilson_ci(n_sdc + n_latent, n_valid)
    rch_lo, rch_hi, _ = wilson_ci(n_valid, n_total - n_simerr)

    return {
        "counts": dict(counter),
        "n_total": n_total,
        "n_inactive": n_inactive,
        "n_simerror": n_simerr,
        "n_valid": n_valid,
        "P_SDC": p_sdc, "P_SDC_ci": (sdc_lo, sdc_hi),
        "P_DUE": p_due, "P_DUE_ci": (due_lo, due_hi),
        "P_escape": p_escape, "P_escape_ci": (esc_lo, esc_hi),
        "Reachability": reach, "Reachability_ci": (rch_lo, rch_hi),
    }
