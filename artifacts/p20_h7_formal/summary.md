# H7 formal (2-bit PTE + kernel-walk × ECC off/on) — 2026-09-11

Protocol: restore cpt.90000000 (base tick 90e9), injection window 95e9 absolute
(5e9 past restore, walk-dense boot segment), two_bit_corrupt (adjacent 2-bit) +
kernel_walk_only (TTBR1) + skip_empty_pte + seed-derived skip (seed%500+1,
dispersed injection sites), 360s censored window, 4-slot FIFO-semaphore
launcher (runs/h7formal/h7fast.sh), ~10h, 484/484 applied=1 (zero wasted runs).

| arm | n | kernel panic | fault-induced abort | survived | fatal rate [Wilson 95%] |
|---|---|---|---|---|---|
| ECC off | 384 | 100 | 88 | 196 | 49.0% [44.0, 53.9] |
| ECC on  | 100 | 0 | 0 | 100 | 0.0% [0.0, 3.7] |

Pilot comparison: ECC-off 47% [30.9,63.7] (n=30) — formal point estimate
inside the pilot CI. Three-round chain: single-bit user-space clear_valid =
kernel refills self-heal (0/30 fatal) → 2-bit kernel-space = ECC is the ONLY
line of defense (49.0% vs 0.0%, CI zero overlap).

Incidents honestly recorded (progress.md): first launch -P16 → OOM killer
destroyed 180 runs (rc=137/124, all invalid); second tick-base misreading
(window at 195e9 vs restore base 90e9) → 52 applied=0 runs discarded
(results_invalid_195e9.txt preserved).
