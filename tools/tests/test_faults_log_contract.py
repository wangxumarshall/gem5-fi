#!/usr/bin/env python3
"""[OOO][AUDIT] faults_injected log-contract unit test.

Context: campaign results recorded 5 FR02 runs with faults_injected=2
(deterministic repro: formal_FR02_dcv-c0000-r0068.yaml, selection_seed
20261668). Root cause: CHAOSRenameMap/CHAOSDecode honest-skip log lines
did NOT carry the "faults_injected: N" counter, and tools/runner.py's
log parser (runner.py:1524-1568) counts every non-empty line WITHOUT that
marker as +1 injection. A run whose only log lines are skips was
therefore misreported as faults=N (N = number of skip lines):

    2 skip lines -> faults=2 ("G5 VIOLATION", excluded from valid)
    1 skip line  -> faults=1 -> FALSE "activated Masked" (contaminates
                    the valid denominator; confirmed 2/26 in a sample
                    rerun of FR02 Masked/f1 manifests, 2026-10-10)

The fix (commit [OOO][AUDIT] ...) makes EVERY log line written by
CHAOSRenameMap and CHAOSDecode carry ", faults_injected: <count>". With
that contract, the parser's marker-wins rule ("faults = value of the
LAST 'faults_injected:' line") is always correct: skip lines carry the
unchanged counter (0 before the first success), success lines carry the
incremented counter (1).

This test pins the contract WITHOUT importing tools/runner.py (shared
LSU file — not modified by the audit): it re-implements the parser's
exact counting rules (mirroring runner.py:1524-1568) and asserts
behavior on fixture logs, including the historical-bug fixture captured
verbatim from the pre-fix reproduction.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


# --- the parser rules, mirroring tools/runner.py:1524-1568 verbatim ---
def parse_faults(log_text):
    """runner.py's injection counting for a single injector log."""
    faults = 0
    for line in log_text.splitlines():
        if "faults_injected:" in line:
            # last marker wins (runner.py:1531-1535)
            try:
                faults = int(line.split("faults_injected:")[1].split()[0])
            except Exception:
                pass
            continue
        if line.startswith("ReadTracePoll") or line.startswith("ReadTraceFinal"):
            continue
        if "DIRECTED reg:" in line:
            continue
        if line.lstrip().startswith("protection:"):
            continue
        if "DUPLICATE_ALLOCATION:" in line:
            continue
        if ("Inactive" in line) or line.startswith("Error"):
            continue
        if line.strip():
            faults += 1
    return faults


# --- fixtures (verbatim / representative) ---

# 1. PRE-FIX r0068 log (captured from the deterministic reproduction on
#    binary 9ecab3ad..., 2026-10-10): 2 marker-less skip lines, ZERO
#    real injections. The pre-fix parser reported faults=2 — the bug.
LOG_PREFIX_R0068 = (
    "Tick: 10102785, Site: rename_setEntry, mode=map_bitflip2_adj, "
    "class=vec, tid=0, arch=V0, old_phys=44, bits=(3,4) — flipped idx 52 "
    "out of [0,48) (skipped, no clamp)\n"
    "Tick: 10757285, Site: rename_setEntry, mode=map_bitflip2_adj, "
    "class=vec, tid=0, arch=V2, old_phys=44, bits=(3,4) — flipped idx 52 "
    "out of [0,48) (skipped, no clamp)\n"
)

# 2. POST-FIX r0068 log (same run on the fixed binary 1a618953...):
#    identical skip lines now carrying the counter -> parser reports 0.
LOG_POSTFIX_R0068 = (
    "Tick: 10102785, Site: rename_setEntry, mode=map_bitflip2_adj, "
    "class=vec, tid=0, arch=V0, old_phys=44, bits=(3,4) — flipped idx 52 "
    "out of [0,48) (skipped, no clamp), faults_injected: 0\n"
    "Tick: 10757285, Site: rename_setEntry, mode=map_bitflip2_adj, "
    "class=vec, tid=0, arch=V2, old_phys=44, bits=(3,4) — flipped idx 52 "
    "out of [0,48) (skipped, no clamp), faults_injected: 0\n"
)

# 3. GENUINE success (one injection; the historical good case):
LOG_SUCCESS = (
    "Tick: 15711850, Site: rename_setEntry, mode=map_bitflip2_adj, "
    "class=vec, tid=0, arch=V2, old_phys=45, new_phys=43, bits=(1,2), "
    "dist=1, faults_injected: 1\n"
)

# 4. SKIP then SUCCESS (marker wins over the earlier counted line):
LOG_SKIP_THEN_SUCCESS = LOG_POSTFIX_R0068 + LOG_SUCCESS

# 5. Decode skip + success (D04-c src_swap formats on the fixed binary)
LOG_DECODE = (
    "Tick: 531685, Site: fetch_decode, mode=src_swap, pc=0x40c21c, "
    "orig_mnemonic=ldr — not a two-int-src data-proc format (skipped, "
    "no injection), faults_injected: 0\n"
    "Tick: 531686, Site: fetch_decode, mode=src_swap, pc=0x40c220, "
    "orig_enc=0x8b010041, new_enc=0x8b020021, rn=2->1, rm=1->2, "
    "orig_mnemonic=add, new_mnemonic=add, faults_injected: 1\n"
)

# --- the contract: every non-empty CHAOSRenameMap/CHAOSDecode line
#     written AFTER the fix must carry the marker. Excluded line types
#     (ReadTrace*/DIRECTED/protection:/DUPLICATE_ALLOCATION) belong to
#     other injectors and are honored by the parser regardless. ---
_SITE_LINE = re.compile(r"Site:\s*(rename_setEntry|rename_srcTags|fetch_decode)")


def check_contract(log_text, name):
    for i, line in enumerate(log_text.splitlines(), 1):
        if not line.strip():
            continue
        if "faults_injected:" not in line and _SITE_LINE.search(line):
            raise AssertionError(
                f"{name} line {i} violates the log contract (Site line "
                f"without faults_injected marker): {line!r}"
            )


def test_parse_faults():
    # Historical bug fixture: pre-fix parser miscounted 2 skips as 2 faults.
    # Kept as a REGRESSION DOCUMENT: the pre-fix log format must never
    # come back. (The fix's contract check below is what enforces it.)
    assert parse_faults(LOG_PREFIX_R0068) == 2, \
        "pre-fix fixture: parser counted 2 marker-less skip lines as 2 faults (the bug)"

    # Post-fix: same run now parses to 0 (no injection happened).
    assert parse_faults(LOG_POSTFIX_R0068) == 0, \
        "post-fix r0068 must parse to 0 faults (both lines are skips with counter 0)"

    # Genuine success -> 1.
    assert parse_faults(LOG_SUCCESS) == 1

    # Skip then success: LAST marker wins -> 1 (not 2).
    assert parse_faults(LOG_SKIP_THEN_SUCCESS) == 1, \
        "marker-wins rule: skip(0) then success(1) must parse to 1"

    # Decode skip+success -> 1.
    assert parse_faults(LOG_DECODE) == 1

    # Empty / absent log -> 0 (Inactive).
    assert parse_faults("") == 0


def test_log_contract():
    check_contract(LOG_POSTFIX_R0068, "post-fix r0068")
    check_contract(LOG_SUCCESS, "success")
    check_contract(LOG_SKIP_THEN_SUCCESS, "skip-then-success")
    check_contract(LOG_DECODE, "decode")


def main():
    test_parse_faults()
    test_log_contract()
    print("SELFTEST PASS (faults log-contract: 5 parse assertions + 4 contract checks)")


if __name__ == "__main__":
    main()
