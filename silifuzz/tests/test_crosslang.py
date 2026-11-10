#!/usr/bin/env python3
"""Cross-language check: the Python encoder must agree with the C++ one, and
snapshots written by either side must be playable by the other."""

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import sfsnapshot as sf  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def check(ok, name, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ((" " + detail) if detail and not ok else ""))
    return 0 if ok else 1


def main():
    failures = 0
    os.makedirs("work", exist_ok=True)
    out = run(["./bin/test_snapshot"])
    if out.returncode != 0:
        print(out.stdout)
        return 1
    m = re.search(r"sample_sha256=([0-9a-f]{64})", out.stdout)
    failures += check(m is not None, "test_snapshot produced sample hash")
    if not m:
        return failures
    cpp_hash = m.group(1)

    sample = sf.load("work/sample.sfs")
    failures += check(sf.content_hash(sample) == cpp_hash,
                      "python content hash == C++ content hash",
                      f"{sf.content_hash(sample)} != {cpp_hash}")
    with open("work/sample.sfs", "rb") as f:
        raw = f.read()
    failures += check(sf.encode(sample) == raw, "python re-encode is byte identical")

    # Python-authored snapshot, captured and replayed by the C++ player.
    code = [0xD28000E0, 0x8B000000, 0xD4200000]  # mov x0,#7; add x0,x0,x0; brk
    snap = sf.Snapshot(meta='{"source":"python-crosslang"}')
    snap.mappings = [
        sf.MemoryMapping(sf.CODE_BASE, 4096, sf.PERM_READ | sf.PERM_EXEC,
                         b"".join(c.to_bytes(4, "little") for c in code)),
        sf.MemoryMapping(sf.STACK_BASE, 4096, sf.PERM_READ | sf.PERM_WRITE),
    ]
    snap.regs.pc = sf.CODE_BASE
    snap.regs.sp = sf.STACK_TOP
    sf.save("work/py_src.sfs", snap)
    failures += check(sf.load("work/py_src.sfs").regs.pc == sf.CODE_BASE,
                      "python snapshot round-trip")

    cap = run(["./bin/sf_player", "--snapshot", "work/py_src.sfs", "--core", "0",
               "--capture", "work/py_cap.sfs"])
    failures += check(cap.returncode == 0, "C++ player runs Python snapshot",
                      cap.stderr)
    captured = sf.load("work/py_cap.sfs")
    failures += check(len(captured.end_states) == 1, "captured end state")
    e = captured.end_states[0]
    failures += check(e.signal == 5, "captured SIGTRAP", str(e.signal))
    failures += check(e.regs.x[0] == 14, "captured x0 == 14", hex(e.regs.x[0]))
    failures += check(e.regs.pc == sf.CODE_BASE + 8, "captured pc",
                      hex(e.regs.pc))
    failures += check(captured.id == sf.content_id(captured),
                      "captured id == content id")

    replay = run(["./bin/sf_player", "--snapshot", "work/py_cap.sfs",
                  "--core", "0", "--repeat", "3"])
    failures += check(replay.returncode == 0, "replay matches captured end state",
                      replay.stdout + replay.stderr)
    failures += check(replay.stdout.count('"match":true') == 3,
                      "three matching replays")

    # Corrupt files are rejected by Python as well.
    try:
        sf.decode(raw[:20])
        failures += check(False, "python rejects truncated snapshot")
    except ValueError:
        failures += check(True, "python rejects truncated snapshot")

    print(f"{'ALL PASS' if failures == 0 else 'TESTS FAILED'} failures={failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
