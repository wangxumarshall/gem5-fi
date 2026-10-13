#!/usr/bin/env bash
# verify_gem5_injectors.sh — SVE/SME FI evaluation precondition check.
# Verifies (1) the gem5.opt binary carries the full 19-injector CHAOS set
# (python objects import works — the 2026-08-29 binary had a broken
# embedded registration), (2) the reg_chain golden anchor, (3) SVE/SME
# instruction executability (probe binary, default VL/SVL=128-bit).
# Usage: bash tools/verify_gem5_injectors.sh
set -u
cd "$(dirname "$0")/.."
source ~/gem5-deps/env.sh
G5=CHAOS/gem5/build/ARM/gem5.opt
RC=0

# --- 1. injector classes (nm symbol table; python import is proven by the
#        anchor runs below — a binary with a broken embedded python registry
#        fails at arm_chaos.py import time) ---
CLASSES="CHAOSReg CHAOSPhysReg CHAOSMem CHAOSCache CHAOSLSQFwd CHAOSAddrPath \
         CHAOSPTW CHAOSRenameMap CHAOSFreeList CHAOSROB CHAOSIQ CHAOSRAS \
         CHAOSExec CHAOSFPU CHAOSL1DForward CHAOSBPU CHAOSExMon CHAOSArmTLB \
         CHAOSArmSysReg"
N=$(nm -C "$G5" 2>/dev/null | grep -cE '^\S+ [TW] gem5::CHAOS(Reg|PhysReg|Mem|Cache|LSQFwd|AddrPath|PTW|RenameMap|FreeList|ROB|IQ|RAS|Exec|FPU|L1DForward|BPU|ExMon|ArmTLB|ArmSysReg)Params')
echo "injector param classes found: $N (expect >= 19)"
[ "$N" -ge 19 ] || { echo "FAIL: injector class count"; RC=1; }

# --- 2. reg_chain golden anchor (no injection, O3) ---
OUT=$(mktemp -d)
A1=$(timeout 300 "$G5" --quiet --outdir="$OUT" configs/se/arm_chaos.py \
     --cpu O3 --cmd workloads/directed/reg_chain --workload_args "200" \
     2>/dev/null | grep -oE '^[0-9a-f]{16}$' | tail -1)
echo "anchor1 reg_chain: ${A1:-<none>} (expect f247ef3fe6f02cfd)"
[ "$A1" = "f247ef3fe6f02cfd" ] || { echo "FAIL: reg_chain golden"; RC=1; }

# --- 3. SVE/SME executability anchor (default VL/SVL = 128-bit) ---
PROBE=workloads/sdcshield/sve_sme_probe
if [ ! -x "$PROBE" ]; then
    echo "anchor3: probe $PROBE missing — building from /tmp cache if present"
    if [ -x /tmp/sve_sme_probe ]; then PROBE=/tmp/sve_sme_probe; else
        echo "FAIL: no SVE/SME probe binary"; RC=1; PROBE=""
    fi
fi
if [ -n "$PROBE" ]; then
    A3=$(timeout 300 "$G5" --quiet --outdir="$OUT" configs/se/arm_chaos.py \
         --cpu O3 --cmd "$PROBE" 2>/dev/null | grep -E '^(SVE|SME)' | tr '\n' ';')
    echo "anchor3 SVE/SME: $A3"
    echo "$A3" | grep -q "SVE VL = 16 bytes" || { echo "FAIL: SVE probe"; RC=1; }
    echo "$A3" | grep -q "SME SVL = 16 bytes" || { echo "FAIL: SME probe"; RC=1; }
fi

rm -rf "$OUT"
[ "$RC" -eq 0 ] && echo "RESULT: ALL ANCHORS OK" || echo "RESULT: FAILURES PRESENT"
exit $RC
