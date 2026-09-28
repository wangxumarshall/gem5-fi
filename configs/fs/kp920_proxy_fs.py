# kp920_proxy_fs.py — §1.1 C2-KP V110 FS proxy config.
#
# v2 (2026-09-28) — THIN ARGV SHIM. The v1 design exec'd arm_chaos_fs.py and
# then chained a _pre_instantiate hook to apply the V110 params — but
# arm_chaos_fs.py ends with simulator.run(), so the post-exec hook
# assignment was DEAD CODE: the "V110 applied" print never appeared in any
# log, and all FS runs through this wrapper actually used DEFAULT gem5 O3
# params despite the C2-KP V110 label (evidence: config.ini dtb assoc=64,
# V110/B0 boots producing identical ticks). The V110 params now live INSIDE
# arm_chaos_fs.py (--v110_params, applied before the Simulator is built);
# this shim only selects them by injecting the flag.
#
# V110 params (docs/kunpeng.md §3, applied by arm_chaos_fs.py --v110_params):
#   width=4-wide, ROB=128, physInt=160, physFloat=192, LQ=48, SQ=42.
# IQ stays gem5's unified-vector (V110's distributed four-scheduler is the
# documented E3 limitation — identical to the SE C2-KP proxy).
# FS mode only (needs kernel/disk/bootloader from gem5-fs/).
print("[kp920_proxy_fs] shim: injecting --v110_params (params applied "
      "inside arm_chaos_fs.py, pre-Simulator)")
import os, sys

sys.argv.insert(1, "--v110_params")
se_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "se")
exec(compile(open(os.path.join(se_dir, "arm_chaos_fs.py")).read(), "arm_chaos_fs.py", "exec"))
