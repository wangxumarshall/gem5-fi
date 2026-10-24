#!/usr/bin/env python3
"""R6-FIXEXIT contract: the fault-induced panic exit string must be mapped.

Static contract (same style as the other tests/test_lsu_hook_* suites): it
inspects the real sources, so it fails before the fix and passes after.

The defect: `arch/arm/linux/fs_workload.cc` writes
"Kernel panic in simulated kernel" for a fault-induced panic, but
`exit_event.py`'s EXACT-match table only knew "…simulated system." /
"…in guest", so the string fell through to NotImplementedError (exit=1)
instead of reaching a registered handler.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EE = (ROOT / "CHAOS/gem5/src/python/gem5/simulate/exit_event.py").read_text()
SE = (ROOT / "configs/se/arm_chaos_fs.py").read_text()
MC = (ROOT / "configs/fs/lsu_multicore_fs.py").read_text()

failed = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failed.append(name)


def main():
    # 1. the two exact strings are mapped to the two distinct enum values
    check("panic string maps to KERNEL_PANIC",
          'exit_string == "Kernel panic in simulated kernel"' in EE
          and "return ExitEvent.KERNEL_PANIC" in EE)
    check("oops-in-kernel string maps to KERNEL_OOPS",
          'exit_string == "Kernel oops in simulated kernel"' in EE
          and "return ExitEvent.KERNEL_OOPS" in EE)

    # 2. the pre-existing branches survive (no deletion / weakening)
    for s in ('"Kernel panic in simulated system."', '"Kernel oops in simulated system."',
              '"Kernel panic in guest"', '"Kernel oops in guest"'):
        check(f"pre-existing branch kept: {s}", s in EE)

    # 3. NO broad catch was introduced: unknown strings must still fail loudly
    check("unknown exit string still raises NotImplementedError",
          "raise NotImplementedError(" in EE)
    for bad in ("startswith(\"Kernel\",", "in exit_string", "'Kernel' in", '"Kernel" in'):
        check(f"no broad catch via {bad}", bad not in EE)

    # 4. both FS configs register a KERNEL_PANIC handler
    for nm, src in (("arm_chaos_fs", SE), ("lsu_multicore_fs", MC)):
        check(f"{nm} registers KERNEL_PANIC",
              "ExitEvent.KERNEL_PANIC: _kernel_panic_exit" in src)
        check(f"{nm} keeps KERNEL_OOPS registered",
              "ExitEvent.KERNEL_OOPS: _kernel_oops_exit" in src)
        check(f"{nm} defines _kernel_panic_exit",
              "def _kernel_panic_exit():" in src)

    print()
    if failed:
        print(f"FAILURES: {failed}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
