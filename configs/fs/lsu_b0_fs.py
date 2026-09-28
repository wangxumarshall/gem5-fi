#!/usr/bin/env python3
# lsu_b0_fs.py — LSU B0 full-system platform (09 §3 W7 / M3 plan Task 4).
#
# v2 (2026-09-28) — THIN ARGV SHIM. The v1 design exec'd arm_chaos_fs.py and
# then chained a _pre_instantiate hook to apply the B0 deltas — but
# arm_chaos_fs.py ends with simulator.run(), so the post-exec hook
# assignment was DEAD CODE (never executed: no B0 print in the boot log,
# config.ini dtb assoc=64, and the B0 boot produced a tick identical to the
# V110 boot — same default config, deterministic). The platform params now
# live INSIDE arm_chaos_fs.py (--lsu_b0, applied before the Simulator is
# constructed); this shim only selects them by injecting the flag.
#
# B0 deltas (02 parameter table, applied by arm_chaos_fs.py --lsu_b0):
#   DTLB = 32 entries (02 r11; gem5 ArmTLB default 64 — W1 ③; the S1
#          sensitivity variant restores 64)
#   LQ/SQ = 16/16       (02 r7/r8; the V110 proxy uses 48/42)
print("[lsu_b0_fs] shim: injecting --lsu_b0 (params applied inside "
      "arm_chaos_fs.py, pre-Simulator)")
import os
import sys

sys.argv.insert(1, "--lsu_b0")
_se_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "se")
exec(compile(open(os.path.join(_se_dir, "arm_chaos_fs.py")).read(),
             "arm_chaos_fs.py", "exec"))
