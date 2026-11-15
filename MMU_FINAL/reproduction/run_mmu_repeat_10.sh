#!/bin/bash
# Rebuild the 10 independent repeat runs from the archived commands.
#
#   ./run_mmu_repeat_10.sh --dry-run
#   ./run_mmu_repeat_10.sh --execute [OUTROOT]
#
# The archived command.sh files were generated and executed for
# MMU-REPEATABILITY-20261114.  Only the repository root, output directory and
# fresh disk copy are rewritten; fault parameters, executable name, rcS and
# run IDs are preserved verbatim.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

MODE=dry
OUT_ROOT="$MMU_REPO_ROOT/runs/MMU_FINAL_REPEAT_10_REPLICA"
if [ "${1:-}" = "--execute" ]; then MODE=execute; OUT_ROOT="${2:-$OUT_ROOT}"; fi
[ "${1:-}" = "--dry-run" ] && MODE=dry

OLD_ROOT="/home/sdc/gem5-fi-mmu-impl-v2"
OLD_LAUNCH="$OLD_ROOT/runs/MMU_FORMAL_CAMPAIGN_20261113/post_campaign_closure/final_closure/repeatability/launch"
REPEATS="$MMU_RESULTS_DIR/repeatability/repeats"

[ -d "$REPEATS" ] || mmu_die "missing repeat archive: $REPEATS"
[ "$MODE" = execute ] && mmu_check_runtime_assets

n=0
for src in "$REPEATS"/REP-FINAL-MMU-*; do
    [ -d "$src" ] || continue
    rid="$(basename "$src")"
    newrun="$OUT_ROOT/$rid"
    n=$((n + 1))
    if [ "$MODE" = dry ]; then
        echo "# $rid"
        sed -e "s#$OLD_LAUNCH/$rid#$newrun#g" \
            -e "s#$OLD_ROOT#$MMU_REPO_ROOT#g" "$src/command.sh" | grep '^exec ' | sed 's/^exec /echo /'
    else
        [ -e "$newrun" ] && mmu_die "refusing to overwrite $newrun"
        mkdir -p "$newrun/outdir"
        cp -a "$src/rcS.scoped" "$newrun/rcS.scoped"
        cp -a "$MMU_DISK_TEMPLATE" "$newrun/disk.img"
        sed -e "s#$OLD_LAUNCH/$rid#$newrun#g" \
            -e "s#$OLD_ROOT#$MMU_REPO_ROOT#g" "$src/command.sh" > "$newrun/command.sh"
        chmod +x "$newrun/command.sh"
        mmu_info "[$n/10] $rid"
        "$newrun/command.sh" > "$newrun/stdout.log" 2>&1 || {
            rc=$?; echo "$rc" > "$newrun/exit.txt"; mmu_die "$rid exited $rc"; }
        echo 0 > "$newrun/exit.txt"
    fi
done < <(true)

mmu_info "repeat runs enumerated: $n"
[ "$n" = 10 ] || mmu_die "expected 10 repeat runs, found $n"
[ "$MODE" = dry ] && mmu_info "dry run complete; nothing executed"
