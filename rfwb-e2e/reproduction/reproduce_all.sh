#!/usr/bin/env bash
# Single entry point for RF/WB reproduction.
#
#   --check            design/dependency dry-run (no gem5 run)
#   --build-workloads  rebuild ELFs into workloads/build_rebuilt/
#   --build-gem5       build the patched gem5.opt
#   --prescan          25 count-only eligible-event scans
#   --plan             compute T01/T02/T03 and compare with the frozen plan
#   --faults           75 Fault runs from the generated timing plan
#   --controls         25 Control runs (RFWB_MODE=off)
#   --validate         golden + classification + result validation
#   --smoke            5 Faults + 5 Controls + 1 M005 prescan (no full run)
#   --all              prescan + plan + faults + controls + validate
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../scripts/lib/common.sh"
rfwb_require_tools
rfwb_locate

CHECK_PY="$RFWB_ROOT/scripts/validation/validate_design.py"
PLAN_PY="$RFWB_ROOT/scripts/prescan/compute_timing_plan.py"
PLAN_VALIDATE_PY="$RFWB_ROOT/scripts/prescan/validate_timing_plan.py"
PLAN_FROZEN="$RFWB_ROOT/configs/timing/frozen_timing_plan.tsv"
SAMPLE_MAP="$RFWB_ROOT/configs/timing/evidence_sample_ids.tsv"
EXPECTED="$RFWB_ROOT/configs/fault_models/frozen_classification.tsv"
GOLDEN="$RFWB_ROOT/golden"
STRICT=()
[ "${RFWB_STRICT_TARGET_SEQ:-0}" = "1" ] && STRICT=(--strict-target-seq)

usage() {
    sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

do_plan() {
    mkdir -p "$RUNS"
    python3 "$PLAN_PY" --traces "$RUNS/traces" --out "$RUNS/timing_plan.tsv" \
        --sample-map "$SAMPLE_MAP" "${STRICT[@]}"
    python3 "$PLAN_VALIDATE_PY" --generated "$RUNS/timing_plan.tsv" \
        --frozen "$PLAN_FROZEN" \
        --corrected-m005 "$RFWB_ROOT/configs/timing/corrected_prescan_summary.tsv" \
        "${STRICT[@]}"
}

do_validate() {
    local plan="$RUNS/timing_plan.tsv"
    [ -f "$plan" ] || plan="$PLAN_FROZEN"
    python3 "$RFWB_ROOT/scripts/validation/validate_results.py" \
        --runs "$RUNS/samples" --traces "$RUNS/traces" --plan "$plan" \
        --expected "$EXPECTED" --golden "$GOLDEN"
}

do_smoke() {
    export RUNS=${SMOKE_RUNS:-$RFWB_ROOT/runs/smoke}
    rm -rf "$RUNS"
    mkdir -p "$RUNS"
    rfwb_require_gem5
    echo "== smoke: M005 C01 prescan =="
    "$RFWB_ROOT/scripts/experiment/run_one.sh" M005 C01 count 0 SCAN-M005-C01-N
    python3 "$PLAN_PY" --traces "$RUNS/traces" --out "$RUNS/timing_plan.tsv" \
        --sample-map "$SAMPLE_MAP" --allow-missing "${STRICT[@]}"
    python3 "$PLAN_VALIDATE_PY" --generated "$RUNS/timing_plan.tsv" \
        --frozen "$PLAN_FROZEN" \
        --corrected-m005 "$RFWB_ROOT/configs/timing/corrected_prescan_summary.tsv" \
        --allow-subset "${STRICT[@]}"

    echo "== smoke: 5 Controls (C01) =="
    for m in M001 M002 M003 M004 M005; do
        "$RFWB_ROOT/scripts/experiment/run_one.sh" "$m" C01 off 0 "CTRL-RFWB-${m}-C01-RUN"
    done

    echo "== smoke: 5 Faults (C01 T01) =="
    head -1 "$PLAN_FROZEN" > "$RUNS/smoke_plan.tsv"
    for m in M001 M002 M003 M004; do
        row=$(awk -F'\t' -v m="$m" '$1==m && $2=="C01" {print; exit}' "$PLAN_FROZEN")
        [ -n "$row" ] || { echo "ERROR: no frozen row for $m C01" >&2; exit 2; }
        printf '%s\n' "$row" >> "$RUNS/smoke_plan.tsv"
        ord=$(printf '%s\n' "$row" | cut -f4)
        sid=$(printf '%s\n' "$row" | cut -f11)
        "$RFWB_ROOT/scripts/experiment/run_one.sh" "$m" C01 fault "$ord" "$sid" 0
    done
    # M005 must use the freshly scanned target sequence, not the frozen seq,
    # because absolute seq numbers shift with the guest stack layout.
    m5row=$(awk -F'\t' '$1=="M005" && $2=="C01" {print; exit}' "$RUNS/timing_plan.tsv")
    [ -n "$m5row" ] || { echo "ERROR: no generated M005 C01 plan row" >&2; exit 2; }
    printf '%s\n' "$m5row" >> "$RUNS/smoke_plan.tsv"
    ord=$(printf '%s\n' "$m5row" | cut -f4)
    tseq=$(printf '%s\n' "$m5row" | cut -f7)
    sid=$(printf '%s\n' "$m5row" | cut -f11)
    "$RFWB_ROOT/scripts/experiment/run_one.sh" M005 C01 fault "$ord" "$sid" "$tseq"

    echo "== smoke: golden + partial result validation =="
    python3 "$RFWB_ROOT/scripts/validation/check_golden.py" \
        --runs "$RUNS/samples" --golden "$GOLDEN" --allow-partial
    python3 "$RFWB_ROOT/scripts/validation/validate_results.py" \
        --runs "$RUNS/samples" --traces "$RUNS/traces" --plan "$RUNS/smoke_plan.tsv" \
        --expected "$EXPECTED" --golden "$GOLDEN" --allow-partial
    echo "SMOKE PASS (5 Fault + 5 Control + M005 C01 prescan)"
}

mode=${1:---check}
shift || true
case "$mode" in
    --check)          python3 "$CHECK_PY" ;;
    --build-workloads) "$RFWB_ROOT/scripts/build/build_workloads.sh" ;;
    --build-gem5)     "$RFWB_ROOT/scripts/build/build_gem5.sh" ;;
    --prescan)        rfwb_require_gem5; "$RFWB_ROOT/scripts/prescan/run_prescan.sh" ;;
    --plan)           do_plan ;;
    --faults)         rfwb_require_gem5; "$RFWB_ROOT/scripts/experiment/run_faults.sh" ;;
    --controls)       rfwb_require_gem5; "$RFWB_ROOT/scripts/experiment/run_controls.sh" ;;
    --validate)       do_validate ;;
    --smoke)          do_smoke ;;
    --all)
        rfwb_require_gem5
        "$RFWB_ROOT/scripts/prescan/run_prescan.sh"
        do_plan
        "$RFWB_ROOT/scripts/experiment/run_faults.sh"
        "$RFWB_ROOT/scripts/experiment/run_controls.sh"
        do_validate
        ;;
    --help|-h)        usage ;;
    *)                usage; echo "ERROR: unknown mode $mode" >&2; exit 2 ;;
esac
