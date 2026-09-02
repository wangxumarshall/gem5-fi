# kp920_proxy_fs.py — §1.1 C2-KP V110 FS proxy config (delegates to arm_chaos_fs).
# V110 params (ROB128/physInt160/etc) applied via _pre_instantiate hook (TODO).
# FS mode only (needs kernel/disk/bootloader).
print("[kp920_proxy_fs] delegates to arm_chaos_fs.py; V110 params TODO")
import os, sys
se_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "se")
exec(compile(open(os.path.join(se_dir, "arm_chaos_fs.py")).read(), "arm_chaos_fs.py", "exec"))
