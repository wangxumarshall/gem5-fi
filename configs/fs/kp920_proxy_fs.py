# kp920_proxy_fs.py — §1.1 C2-KP V110 FS proxy config (delegates to arm_chaos_fs).
# Phase 5.1: applies the TaiShan V110 O3 microarchitecture params (the same
# C2-KP point as configs/se/kp920_proxy.py) on top of the arm_chaos_fs board,
# via a chained _pre_instantiate hook — the ArmBoard builds its CPU lazily, so
# the O3 params are set after construction / before m5.instantiate().
# V110 params sourced from docs/kunpeng.md §3 (same dict as the SE config):
#   width=4-wide, ROB=128, physInt=160, physFloat=192, LQ=48, SQ=42.
# IQ stays gem5's unified-vector (V110's distributed four-scheduler is the
# documented E3 limitation — identical to the SE C2-KP proxy).
# FS mode only (needs kernel/disk/bootloader from gem5-fs/).
print("[kp920_proxy_fs] delegates to arm_chaos_fs.py + applies C2-KP V110 O3 params")
import os, sys
se_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "se")
exec(compile(open(os.path.join(se_dir, "arm_chaos_fs.py")).read(), "arm_chaos_fs.py", "exec"))

# ---- apply TaiShan V110 O3 params (the FS C2-KP point; Phase 5.1) ----
# After the exec, board/processor/cache_hierarchy are globals here. Chain our
# param application onto the (possibly CHAOS-patched) _pre_instantiate hook —
# the same chaining pattern arm_chaos_fs.py uses for the TLB/SysReg mounts.
# V110 dict values mirror configs/se/kp920_proxy.py exactly (single source:
# docs/kunpeng.md §3 / design doc §1.1).
V110_FS = {
    "fetch_width": 4, "decode_width": 4, "rename_width": 4,
    "issue_width": 4, "dispatch_width": 4, "commit_width": 4,
    "rob": 128, "phys_int": 160, "phys_float": 192,
    "lq": 48, "sq": 42,
}

_v110_done = [False]
_orig_pi = getattr(cache_hierarchy, "_pre_instantiate", None)
def _apply_v110(root):
    if _orig_pi:
        _orig_pi(root)
    if _v110_done[0]:
        return
    _v110_done[0] = True
    # Only the O3 CPU takes these params (Atomic/TIMING boot passes have no
    # ROB/PRF — the checkpoint pipeline boots Atomic then switches to O3,
    # and the restore run is the one that matters here).
    core0 = processor.get_cores()[0]
    cpu0 = core0.core
    try:
        cpu0.fetchWidth = V110_FS["fetch_width"]
        cpu0.decodeWidth = V110_FS["decode_width"]
        cpu0.renameWidth = V110_FS["rename_width"]
        cpu0.issueWidth = V110_FS["issue_width"]
        cpu0.dispatchWidth = V110_FS["dispatch_width"]
        cpu0.commitWidth = V110_FS["commit_width"]
        cpu0.numROBEntries = V110_FS["rob"]
        cpu0.numPhysIntRegs = V110_FS["phys_int"]
        cpu0.numPhysFloatRegs = V110_FS["phys_float"]
        cpu0.LQEntries = V110_FS["lq"]
        cpu0.SQEntries = V110_FS["sq"]
        print(f"[kp920_proxy_fs] C2-KP V110 O3 params applied: width=4-wide, "
              f"ROB={V110_FS['rob']}, physInt={V110_FS['phys_int']}, "
              f"physFloat={V110_FS['phys_float']}, LQ={V110_FS['lq']}, "
              f"SQ={V110_FS['sq']} (IQ unified-vector — E3, not V110 "
              f"distributed four-scheduler)")
    except Exception as e:
        # Non-O3 CPU (Atomic/TIMING boot pass): the params don't exist —
        # skip silently, this is the expected boot-CPU case.
        print(f"[kp920_proxy_fs] V110 params skipped (non-O3 CPU): {e}")
cache_hierarchy._pre_instantiate = _apply_v110
