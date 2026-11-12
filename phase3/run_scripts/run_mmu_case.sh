#!/bin/bash
# Phase 3 MMU model runner (M03-M08 pilots + M01/M02 regression).
#
# One gem5 process per invocation; fresh disk copy and private outdir for
# every run. TEST IDs only (no formal Seed / SampleRunID). Fault enablement
# is independent of --prop_mmu_trace and --prop_write_log.
#
# Usage:
#   run_mmu_case.sh <outdir> <test-id> <W9|W10|W11|W12|W13|W14> \
#                   <NONE|M01..M08> <target> [trace] [wlog] [extra gem5 args...]
#
# Model target meanings:
#   M01 target = target ASID (220)
#   M02 target = target VA          (e.g. 0x4001300000)
#   M03 target = target VA (process B's fixed VA)
#   M04 target = target VA          (decoy via extra --mmu_m04_decoy_pfn)
#   M05 target = target VA          (decoy via extra --mmu_m05_decoy_table_base)
#   M06 target = target VA
#   M07 target = target VA          (extra: --mmu_target_mode Read|Write|Atomic|Execute)
#   M08 target = target VA          (extra: --mmu_target_mode Read|Write)
#
# Environment overrides (W11-W14 reuse the boot checkpoint):
#   MMU_CKPT, MMU_RCS, MMU_VA_LO, MMU_VA_HI
#   MMU_CTX          scope a multi-context rcS to one R0x (no-fault controls)
#   MMU_M02_OLD_PFN  REQUIRED for M02: the per-context target PFN resolved
#                    from an independent no-fault W10 control.  There is no
#                    literal default (the legacy 0x83480 is wrong for scoped
#                    runs).  See tools/mmu_collect_w10_pfn.py.
set -euo pipefail

WS=/home/sdc/gem5-fi-mmu-impl-v2
GEM5="$WS/CHAOS/gem5/build/ARM/gem5.opt"
OUT="$1"; TESTID="$2"; WL="$3"; FAULT="$4"; TARGET="${5:-}"
TRACE="${6:-on}"
WLOG="${7:-on}"
shift 7 2>/dev/null || true
EXTRA=("$@")

case "$WL" in
  W9)
    CKPT="$WS/runs/mmu_bootF1/cpt.244799013609"
    RCS="$WS/configs/fs/mmu_w9_run.rcS"
    VA_LO=0x4000000000; VA_HI=0x4000100000 ;;
  W10)
    CKPT="$WS/runs/mmu_bootF1/cpt.244799013609"
    RCS="$WS/configs/fs/mmu_w10_run.rcS"
    VA_LO=0x4001000000; VA_HI=0x4001500000 ;;
  W11)
    CKPT="$WS/runs/mmu_bootF1/cpt.244799013609"
    RCS="$WS/configs/fs/mmu_w11_run.rcS"
    VA_LO=0x4004000000; VA_HI=0x4007000000 ;;
  W12)
    CKPT="$WS/runs/mmu_bootF1/cpt.244799013609"
    RCS="$WS/configs/fs/mmu_w12_run.rcS"
    VA_LO=0x4008000000; VA_HI=0x400B000000 ;;
  W13)
    CKPT="$WS/runs/mmu_bootF1/cpt.244799013609"
    RCS="$WS/configs/fs/mmu_w13_run.rcS"
    VA_LO=0x4010000000; VA_HI=0x4010400000 ;;
  W14)
    CKPT="$WS/runs/mmu_bootF1/cpt.244799013609"
    RCS="$WS/configs/fs/mmu_w14_run.rcS"
    VA_LO=0x400C000000; VA_HI=0x400E000000 ;;
  W10S)
    CKPT="$WS/runs/mmu_bootF1/cpt.244799013609"
    RCS="$WS/configs/fs/mmu_w10s_run.rcS"
    VA_LO=0x4001400000; VA_HI=0x4001700000 ;;
  *)
    echo "bad workload $WL" >&2; exit 2 ;;
esac
CKPT="${MMU_CKPT:-$CKPT}"
RCS="${MMU_RCS:-$RCS}"
VA_LO="${MMU_VA_LO:-$VA_LO}"
VA_HI="${MMU_VA_HI:-$VA_HI}"

[ -e "$RCS" ] || { echo "missing rcS $RCS" >&2; exit 2; }
[ -d "$CKPT" ] || { echo "missing checkpoint $CKPT" >&2; exit 2; }

RUN="$OUT/run"
mkdir -p "$OUT"/{Config,Run_Log,Trace,SHA256} "$RUN"

# MMU_CTX scopes a multi-context rcS to one context.  This is how an
# independent NO-FAULT control is produced for a per-context sample (the
# guest allocation history of an `--ctx all` run does not transfer).
if [ -n "${MMU_CTX:-}" ]; then
  SCOPED="$OUT/rcS.scoped"
  if grep -q -- "--ctx all" "$RCS"; then
    sed "s/--ctx all/--ctx $MMU_CTX/" "$RCS" > "$SCOPED"
    RCS="$SCOPED"
  elif grep -q -- "--all" "$RCS"; then
    sed "s/--all/--ctx $MMU_CTX/" "$RCS" > "$SCOPED"
    RCS="$SCOPED"
  elif grep -q -- "--ctx $MMU_CTX" "$RCS"; then
    :  # already single-context
  else
    echo "MMU_CTX=$MMU_CTX cannot be applied to $RCS" >&2; exit 2
  fi
fi

DISK="$OUT/disk.img"
if [ -e "$DISK" ]; then echo "refuse to overwrite $DISK" >&2; exit 3; fi
cp --reflink=auto "$WS/runs/disks/mmu_template.img" "$DISK"

FAULT_ARGS=()
case "$FAULT" in
  NONE) ;;
  M01)
    [ -n "$TARGET" ] || { echo "M01 needs target ASID" >&2; exit 2; }
    FAULT_ARGS=(--mmu_fault_model M01 --mmu_fault_enable true
                --mmu_m01_va 0x4000000000 --mmu_m01_asid "$TARGET"
                --mmu_m01_vmid 0 --mmu_m01_regime 0
                --mmu_m01_security_state 0 --mmu_m01_n 12) ;;
  M02)
    [ -n "$TARGET" ] || { echo "M02 needs target VA" >&2; exit 2; }
    # No literal old_pfn.  The per-context W10 target PFN must come from an
    # independent no-fault scoped control (tools/mmu_collect_w10_pfn.py).
    [ -n "${MMU_M02_OLD_PFN:-}" ] || {
      echo "M02 needs MMU_M02_OLD_PFN from an independent no-fault W10 control; refusing the legacy 0x83480" >&2
      exit 2; }
    FAULT_ARGS=(--mmu_fault_model M02 --mmu_fault_enable true
                --mmu_m02_va "$TARGET" --mmu_m02_old_pfn "$MMU_M02_OLD_PFN"
                --mmu_m02_xor_mask 1 --mmu_m02_dram_lo 0x80000000
                --mmu_m02_dram_hi 0x100000000) ;;
  M03|M04|M06|M07|M08)
    [ -n "$TARGET" ] || { echo "$FAULT needs target VA" >&2; exit 2; }
    FAULT_ARGS=(--mmu_fault_model "$FAULT" --mmu_fault_enable true
                --mmu_target_va "$TARGET" --mmu_target_n 12
                --mmu_eligible_event_index 1
                --mmu_m02_dram_lo 0x80000000
                --mmu_m02_dram_hi 0x100000000)
    case "$FAULT" in
      M06) FAULT_ARGS+=(--mmu_target_walk_level 3) ;;
      M07) FAULT_ARGS+=(--mmu_fault_persistence one_shot) ;;
    esac
    ;;
  M05)
    [ -n "$TARGET" ] || { echo "M05 needs target VA" >&2; exit 2; }
    # M05 targets the L2 partial walk cache => 2 MiB (n=21) pages.
    FAULT_ARGS=(--mmu_fault_model M05 --mmu_fault_enable true
                --mmu_target_va "$TARGET" --mmu_target_n 21
                --mmu_eligible_event_index 1
                --mmu_target_walk_level 2
                --mmu_m02_dram_lo 0x80000000
                --mmu_m02_dram_hi 0x100000000) ;;
  *) echo "bad fault $FAULT" >&2; exit 2 ;;
esac

TRACE_ARGS=()
[ "$TRACE" = "on" ] && TRACE_ARGS=(--prop_mmu_trace)

CMD=("$GEM5" --outdir "$RUN"
     "$WS/configs/fs/lsu_b0_fs.py"
     --kernel "$WS/gem5-fs/vmlinux" --disk "$DISK"
     --bootloader "$WS/gem5-fs/boot.arm64" --cpu O3
     --restore-checkpoint "$CKPT" --readfile "$RCS"
     --chaos_propagation
     --prop_mmu_va_lo "$VA_LO" --prop_mmu_va_hi "$VA_HI"
     --prop_run_id "$TESTID" --prop_sample_run_id "$TESTID"
     "${TRACE_ARGS[@]}" --prop_write_log "$WLOG"
     "${FAULT_ARGS[@]}" "${EXTRA[@]}")

printf '%q ' "${CMD[@]}" > "$OUT/Run_Log/command.txt"
printf '\n' >> "$OUT/Run_Log/command.txt"
echo "[run_mmu_case] $TESTID $WL $FAULT target=$TARGET trace=$TRACE wlog=$WLOG extra=${EXTRA[*]:-}"
set +e
"${CMD[@]}" > "$OUT/Run_Log/gem5_stdout.log" 2>&1
RC=$?
set -e
echo "[run_mmu_case] gem5 exit=$RC"
echo "$RC" > "$OUT/Run_Log/gem5_exit_code.txt"
echo "$TRACE" > "$OUT/Run_Log/trace_switch.txt"
echo "$WLOG" > "$OUT/Run_Log/write_log_switch.txt"

cp -f "$RUN/config.ini" "$OUT/Config/config.ini" 2>/dev/null || true
cp -f "$RUN/config.json" "$OUT/Config/config.json" 2>/dev/null || true
cp -f "$RUN/prop_evt.txt.gz" "$OUT/Trace/prop_evt.txt.gz" 2>/dev/null || true
cp -f "$RUN/prop_trace.csv.gz" "$OUT/Trace/prop_trace.csv.gz" 2>/dev/null || true
cp -f "$RUN/board.terminal" "$OUT/Run_Log/board.terminal" 2>/dev/null || true
cp -f "$RUN/stats.txt" "$OUT/Run_Log/stats.txt" 2>/dev/null || true
grep -aE "W(9|10|11|12|13|14)_RESULT|W1[1-4]_(INFO|LIMITATION)" \
    "$OUT/Run_Log/board.terminal" > "$OUT/Run_Log/golden_output.txt" 2>/dev/null || true
( cd "$OUT" && sha256sum Config/* Trace/* Run_Log/board.terminal \
    Run_Log/golden_output.txt Run_Log/gem5_stdout.log \
    Run_Log/command.txt Run_Log/stats.txt disk.img \
    > SHA256/SHA256SUMS.txt 2>/dev/null ) || true
echo "[run_mmu_case] done $TESTID rc=$RC"
exit "$RC"
