#!/usr/bin/env bash
# T3-6 FS formal: TLB pfn_to_mapped_page (live-page) vs pfn_to_offset
# (unmapped) — ESR/DFSC distribution vs the core179 0x96000004 family
# (plan §5.7). Uses the fs_checkpoint two-phase pipeline (restore per run,
# ~13s each). Collects: injection log line + guest outcome (Oops panic
# text / silent run-to-timeout).
set -u
cd "$(dirname "$0")/.."
source /home/sdc/gem5-deps/env.sh
G5=CHAOS/gem5/build/ARM/gem5.opt
N=${N:-96}
ART=artifacts/t3-6-fs-tlb-formal
mkdir -p $ART

run_mode() {
    local mode=$1 label=$2
    local dir=$ART/$label
    mkdir -p $dir
    local JOBS=${JOBS:-4}
    for ((i=0;i<N;i++)); do
        local seed=$((20260825 + i))
        local out=$dir/r$i
        rm -rf $out
        ( timeout 150 $G5 --quiet --outdir=$out configs/se/fs_checkpoint.py \
            --phase=inject --ckpt-dir=cpts/base \
            --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
            --bootloader=gem5-fs/boot.arm64 \
            --injector=armtlb --probability=0.0005 --first-clock=100000 \
            --max-faults=1 --seed=$seed --tlb-target-field=pfn $mode \
            > $out.stdout 2> $out.stderr || true ) &
        while (( $(jobs -r | wc -l) >= JOBS )); do wait -n; done
    done
    wait
    # aggregate
    local oops=0 silent=0 inj=0 esr96000004=0 esr_other=0
    for ((i=0;i<N;i++)); do
        local out=$dir/r$i
        grep -q "Mode: pfn_to" $out/armtlb_injections.log 2>/dev/null && inj=$((inj+1))
        local esrhex
        # guest-side oops evidence: workload.dmesg (dumped on the dmesg exit
        # event) carries the full ESR print; board.terminal as fallback.
        esrhex=$(grep -aoE "Internal error: Oops: [0-9a-f]{8}" \
                     $out/board.workload.dmesg 2>/dev/null | head -1 | grep -oE "[0-9a-f]{8}")
        [ -z "$esrhex" ] && esrhex=$(grep -aoE "Internal error: Oops: [0-9a-f]{8}" \
                     $out/board.terminal 2>/dev/null | head -1 | grep -oE "[0-9a-f]{8}")
        if grep -qE "Internal error: Oops|panic condition" $out.stderr $out.stdout 2>/dev/null \
           || [ -n "$esrhex" ]; then
            oops=$((oops+1))
            echo "$esrhex" >> $dir/esr_values.txt
            case "$esrhex" in
                9600000*|8600000*) esr96000004=$((esr96000004+1)) ;;
                "") ;;  # oops without a decodable ESR print
                *) esr_other=$((esr_other+1)) ;;
            esac
        else
            silent=$((silent+1))
        fi
    done
    echo "$label: n=$N injected=$inj oops=$oops silent=$silent esr_translation_fault_family(96/86xx)=$esr96000004 esr_other=$esr_other" | tee -a $ART/summary.txt
    echo "  ESR histogram: $(sort $dir/esr_values.txt 2>/dev/null | uniq -c | tr '\n' ' ')" | tee -a $ART/summary.txt
}

run_mode "--tlb-pfn-select-mode=mapped_page" live_page
run_mode "--tlb-pfn-offset=4096" offset_unmapped
echo "done -> $ART/summary.txt"
