#!/usr/bin/env bash
# =============================================================================
# tools/lsu_r6_schedule.sh — FORMAL batch launcher / resume driver for the
# LSU fault-injection campaign (R6 batch tooling, lane L15-v2).
#
# WHAT IT DOES
#   Reads the authoritative contract docs/gem5-fi/lsu/mdspec/ready_contract.json
#   (325 cells: 241 READY / 84 BLOCKED; verdict.formal_phase=screening), and
#   drives the FORMAL phase of tools/lsu_campaign.py — one RunID per invocation,
#   one dedicated outdir per RunID, one guard-supervised process tree per run.
#
#   Guarantees encoded here (each is a requirement, not a nicety):
#     * FORMAL only: --phase screening (NEVER --phase trial). trial is refused
#       unless --allow-trial is passed explicitly.
#     * [R6-FREQPOLICY] selection filter: cells the frequency-policy overlay
#       (docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json) marks
#       schedule_enabled=false (STRESS_REDUNDANT F6) are dropped from the
#       selection — including manually listed --cells / --cells-file entries —
#       each with one visible [R6-FREQPOLICY] drop line (no silent caps).
#     * Seeds per cell: screening target 385; the 21 focus RunIDs
#       (contract verdict.focus_runids) get focus_target 2401. Both are read
#       from the contract; --max-seeds-per-cell 100000 is the compute bound
#       (the contract's own per-cell command text).
#     * FS runs need --fs-timeout 2700 (E1: shorter budgets truncate the
#       evidence stream); SE runs use --se-timeout 300. Both are flags.
#     * Outdir isolation: runroot MUST be under /home/sdc/gem5-fi-ding/runs/lsu/
#       — /tmp is refused (15 GiB tmpfs; an FS run set would fill it and /tmp
#       is not durable evidence). Default runroot is the contract's
#       formal_outdir basename under runs/lsu, i.e. stable across restarts so
#       resume works without retyping the path.
#     * Per-run hard wall-clock timeout, enforced twice: lsu_guard --max-seconds
#       inside, plus an outer watchdog that killpg()s the whole session so
#       orphaned gem5 children cannot survive a timed-out guard (the guard
#       TERMs but does not KILL on its max-seconds path).
#     * Exit codes recorded per RunID in <runroot>/runs.tsv.
#     * Resume: a RunID whose <runroot>/<runid>/cell_results.json exists AND
#       whose identity.json matches the current binary/contract/matrix/target/
#       phase is skipped. Resume is the default; --force reruns.
#     * Concurrency policy: start 6, raise to 8 only if MemAvailable > 8 GiB
#       AND iowait < 10% AND SwapFree not shrinking AND no new oom_kill; drop
#       to 6 if MemAvailable < 6 GiB OR swap grows OR iowait > 15%. The guard's
#       own STOP_DISPATCH red line is MemAvailable < 10 GiB and its aquire GATE
#       is MemAvailable < 12 GiB, so the dispatcher additionally applies
#       backpressure (never launches when the guard would refuse) — the
#       effective ramp floor is 12 GiB, not 8.
#     * 5-minute sampling loop printing MemAvailable / swap / iowait / load /
#       per-process gem5 RSS.
#     * Event-file compression: any uncompressed prop_evt.txt is gzipped after
#       a successful run (the tracer normally writes prop_evt.txt.gz directly);
#       --compress-logs also gzips run.out/run.err > 8 MiB.
#
# SELF-CHECK
#   tools/lsu_r6_schedule.sh --self-check   validate args/env/contract/binary/
#                                           checkpoint/FS assets/runroot, print
#                                           the plan (SE + FS examples),
#                                           launch nothing.
#   tools/lsu_r6_schedule.sh --dry-run      print the plan, launch nothing.
#   tools/lsu_r6_schedule.sh --verify       no launch: check identity of
#                                           already-complete RunIDs.
#
# THIS SCRIPT DOES NOT START THE FORMAL CAMPAIGN BY ITSELF. Launching the formal
# experiment is a separate, explicitly gated decision.
# =============================================================================
set -uo pipefail

REPO_DEFAULT="/home/sdc/gem5-fi-ding"
RUNS_LSU="/home/sdc/gem5-fi-ding/runs/lsu"
FS_DIR_DEFAULT="/home/sdc/gem5-fi-ding/gem5-fs"   # vmlinux/ubuntu.img/boot.arm64

# ---------------- defaults ----------------
RUNROOT=""
CONTRACT=""
MATRIX=""
BIN=""
FS_CPT=""
FS_DIR=""
PHASE="screening"
SCREEN_TARGET=""          # default: from contract verdict.screening_target (385)
FOCUS_TARGET=""           # default: from contract verdict.focus_target (2401)
MAIN_TARGET=5000          # only used if --phase main
MAX_SEEDS=100000
SE_TIMEOUT=300
FS_TIMEOUT=2700           # E1: FS evidence truncates below 2700s
PER_RUN_TIMEOUT=86400     # outer anti-hang cap per RunID (24 h; > any legit cell)
CAP_START=6
CAP_MIN=6
CAP_MAX=8
MEM_HI_MIB=8192           # spec: raise to 8 above this
MEM_LO_MIB=6144           # spec: drop to 6 below this
GUARD_MEM_FLOOR_MIB=12288 # lsu_guard GATE_MEM_MIN_GIB=12 -> acquire floor
GUARD_SWAP_FLOOR_MIB=4096 # lsu_guard GATE_SWAP_MIN_GIB=4
IOWAIT_HI_PM=100          # 10.0% (per-mille)
IOWAIT_LO_PM=150          # 15.0% (per-mille)
SAMPLE_INTERVAL=300       # 5 minutes
GUARD_SLOTS=8
CELLS=""
CELLS_FILE=""
COMPRESS_LOGS=0
RESUME=1
FORCE=0
ALLOW_TRIAL=0
DRY_RUN=0
SELF_CHECK=0
VERIFY_ONLY=0
IGNORE_GATE=0

die()  { echo "FATAL: $*" >&2; exit 2; }
warn() { echo "WARN: $*" >&2; }

usage() {
  sed -n '2,57p' "$0" | sed 's/^# \{0,1\}//'
  cat <<'EOF'

FLAGS
  --runroot DIR        output root (default <runs/lsu>/<contract formal_outdir>)
  --contract PATH      default <repo>/docs/gem5-fi/lsu/mdspec/ready_contract.json
  --matrix PATH        default <repo>/artifacts/lsu-trial/07-expanded-matrix-backfilled.csv
  --bin PATH           gem5.opt (default: contract gate.binary)
  --fs-checkpoint DIR  default: contract fs_checkpoint
  --fs-dir DIR         FS images dir (default /home/sdc/gem5-fi-ding/gem5-fs)
  --cells LIST|all     comma-separated RunIDs (default all READY; policy
                       schedule_enabled=false cells are always dropped, loudly)
  --cells-file FILE    one RunID per line ('#' comments allowed)
  --phase NAME         screening|main (default screening). trial needs --allow-trial
  --screening-target N default from contract (385)
  --focus-target N     default from contract (2401); applied to focus RunIDs
  --main-target N      only for --phase main (default 5000)
  --max-seeds-per-cell N   default 100000
  --se-timeout S       campaign --timeout (per SE gem5 sample, default 300)
  --fs-timeout S       campaign --fs-timeout (per FS gem5 sample, default 2700)
  --per-run-timeout S  outer hard cap per RunID (default 86400)
  --cap-start N --cap-min N --cap-max N   concurrency (default 6/6/8)
  --mem-hi-mib N --mem-lo-mib N           ramp thresholds (default 8192/6144)
  --sample-interval S  sampler period seconds (default 300)
  --guard-slots N      LSU_GUARD_SLOTS for guard (default 8; guard hard max 8)
  --compress-logs      also gzip run.out/run.err when > 8 MiB
  --force | --no-resume  ignore resume markers (rerun everything selected)
  --resume             resume is the default (re-enable after --force)
  --verify             do not launch: verify identity of already-complete RunIDs
  --dry-run            print plan, launch nothing
  --self-check         validate env+contract, print plan, launch nothing
  --allow-trial        permit --phase trial (NOT the formal phase)
  --ignore-gate        skip the pre-flight lsu_guard gate check (use only
                       when you have independently confirmed the gate)
  -h|--help
EOF
}

# ---------------- arg parsing ----------------
while [ $# -gt 0 ]; do
  case "$1" in
    --runroot) RUNROOT="${2:-}"; shift 2 ;;
    --contract) CONTRACT="${2:-}"; shift 2 ;;
    --matrix) MATRIX="${2:-}"; shift 2 ;;
    --bin) BIN="${2:-}"; shift 2 ;;
    --fs-checkpoint) FS_CPT="${2:-}"; shift 2 ;;
    --fs-dir) FS_DIR="${2:-}"; shift 2 ;;
    --cells) CELLS="${2:-}"; shift 2 ;;
    --cells-file) CELLS_FILE="${2:-}"; shift 2 ;;
    --phase) PHASE="${2:-}"; shift 2 ;;
    --screening-target) SCREEN_TARGET="${2:-}"; shift 2 ;;
    --focus-target) FOCUS_TARGET="${2:-}"; shift 2 ;;
    --main-target) MAIN_TARGET="${2:-}"; shift 2 ;;
    --max-seeds-per-cell) MAX_SEEDS="${2:-}"; shift 2 ;;
    --se-timeout) SE_TIMEOUT="${2:-}"; shift 2 ;;
    --fs-timeout) FS_TIMEOUT="${2:-}"; shift 2 ;;
    --per-run-timeout) PER_RUN_TIMEOUT="${2:-}"; shift 2 ;;
    --cap-start) CAP_START="${2:-}"; shift 2 ;;
    --cap-min) CAP_MIN="${2:-}"; shift 2 ;;
    --cap-max) CAP_MAX="${2:-}"; shift 2 ;;
    --mem-hi-mib) MEM_HI_MIB="${2:-}"; shift 2 ;;
    --mem-lo-mib) MEM_LO_MIB="${2:-}"; shift 2 ;;
    --sample-interval) SAMPLE_INTERVAL="${2:-}"; shift 2 ;;
    --guard-slots) GUARD_SLOTS="${2:-}"; shift 2 ;;
    --compress-logs) COMPRESS_LOGS=1; shift ;;
    --force|--no-resume) FORCE=1; shift ;;
    --resume) FORCE=0; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --self-check) SELF_CHECK=1; DRY_RUN=1; shift ;;
    --verify) VERIFY_ONLY=1; shift ;;
    --allow-trial) ALLOW_TRIAL=1; shift ;;
    --ignore-gate) IGNORE_GATE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1 (try --help)" ;;
  esac
done

for v in CAP_START CAP_MIN CAP_MAX MEM_HI_MIB MEM_LO_MIB IOWAIT_HI_PM IOWAIT_LO_PM \
         SAMPLE_INTERVAL PER_RUN_TIMEOUT SE_TIMEOUT FS_TIMEOUT MAX_SEEDS \
         GUARD_SLOTS MAIN_TARGET; do
  [[ "${!v}" =~ ^[0-9]+$ ]] || die "$v must be a non-negative integer, got '${!v}'"
done
[ "$CAP_MIN" -le "$CAP_START" ] || die "--cap-min ($CAP_MIN) > --cap-start ($CAP_START)"
[ "$CAP_START" -le "$CAP_MAX" ] || die "--cap-start ($CAP_START) > --cap-max ($CAP_MAX)"
[ "$CAP_MAX" -le "$GUARD_SLOTS" ] || die "--cap-max ($CAP_MAX) > --guard-slots ($GUARD_SLOTS): guard would refuse acquires"
[ "$GUARD_SLOTS" -le 8 ] || die "--guard-slots ($GUARD_SLOTS) > 8 (lsu_guard MAX_EXPERIMENT_SLOTS)"
[ "$MEM_LO_MIB" -lt "$MEM_HI_MIB" ] || die "--mem-lo-mib must be < --mem-hi-mib"
[ "$SE_TIMEOUT" -gt 0 ] || die "--se-timeout must be > 0"
[ "$FS_TIMEOUT" -gt 0 ] || die "--fs-timeout must be > 0"
[ "$PER_RUN_TIMEOUT" -gt "$FS_TIMEOUT" ] || die "--per-run-timeout ($PER_RUN_TIMEOUT) must exceed --fs-timeout ($FS_TIMEOUT): the outer cap would clip a legitimate FS sample"
case "$PHASE" in
  screening|main) : ;;
  trial) [ "$ALLOW_TRIAL" = 1 ] || die "--phase trial is NOT the formal phase; pass --allow-trial only for a deliberate trial run" ;;
  *) die "--phase must be screening|main|trial, got '$PHASE'" ;;
esac
case "$PHASE" in
  screening) TGT_FLAG="--screening-target" ;;
  main)      TGT_FLAG="--main-target" ;;
  trial)     TGT_FLAG="--trial-target" ;;
esac

# repo root = parent of tools/
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SELF_DIR/.." && pwd)"
[ -n "$CONTRACT" ] || CONTRACT="$REPO/docs/gem5-fi/lsu/mdspec/ready_contract.json"
[ -n "$MATRIX" ]   || MATRIX="$REPO/artifacts/lsu-trial/07-expanded-matrix-backfilled.csv"
[ -n "$FS_DIR" ]   || FS_DIR="$FS_DIR_DEFAULT"
# [R6-FREQPOLICY] authoritative frequency-policy overlay (schedule_enabled gate)
POL_JSON="$REPO/docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json"

command -v python3 >/dev/null || die "python3 not found"
[ -f "$CONTRACT" ] || die "contract not found: $CONTRACT"
[ -f "$MATRIX" ]   || die "matrix not found: $MATRIX"

# ---- contract-derived defaults (single source of truth) ----
CFIELDS="$(python3 -c '
import json,sys
d=json.load(open(sys.argv[1]))
v=d.get("verdict",{}); g=d.get("gate",{}); s=d.get("status",{})
print(v.get("screening_target",385), v.get("focus_target",2401),
      g.get("binary","-"), d.get("fs_checkpoint","-"),
      d.get("formal_outdir","runs/lsu/formal_325"),
      d.get("total",0), s.get("READY",0), s.get("BLOCKED",0),
      v.get("formal_phase","screening"), len(v.get("focus_runids",[])),
      d.get("max_parallel",1), d.get("seeds_per_cell",1))
' "$CONTRACT")" || die "could not parse contract: $CONTRACT"
read -r C_SCREEN C_FOCUS C_BIN C_CPT C_OUTDIR C_TOTAL C_READY C_BLOCKED C_PHASE \
        C_NFOCUS C_MAXPAR C_SEEDS <<<"$CFIELDS"

[ -n "$SCREEN_TARGET" ] || SCREEN_TARGET="$C_SCREEN"
[ -n "$FOCUS_TARGET" ]  || FOCUS_TARGET="$C_FOCUS"
[ -n "$BIN" ]           || BIN="$C_BIN"
[ -n "$FS_CPT" ]        || FS_CPT="$C_CPT"
# default runroot = the contract's formal_outdir basename, rooted at runs/lsu
[ -n "$RUNROOT" ]       || RUNROOT="$RUNS_LSU/$(basename "$C_OUTDIR")"

# ---- outdir isolation: never /tmp, always under runs/lsu ----
case "$RUNROOT" in
  /tmp/*|/tmp) die "refusing --runroot under /tmp (15 GiB tmpfs): FS results must live under $RUNS_LSU" ;;
esac
case "$RUNROOT" in
  "$RUNS_LSU"/*) : ;;
  /*) die "refusing --runroot '$RUNROOT': must be an absolute path under $RUNS_LSU" ;;
  *)  die "refusing relative --runroot '$RUNROOT': use an absolute path under $RUNS_LSU" ;;
esac
[ -x "$BIN" ] || die "gem5 binary not executable: $BIN"
[ -d "$FS_CPT" ] || die "FS checkpoint dir missing: $FS_CPT (contract fs_checkpoint)"

mkdir -p "$RUNROOT" || die "cannot create runroot $RUNROOT"
RUNROOT="$(cd "$RUNROOT" && pwd)"

# ---- identity of the frozen environment (resume verification basis) ----
CONTRACT_SHA="$(sha256sum "$CONTRACT" | cut -d' ' -f1)"
MATRIX_SHA="$(sha256sum "$MATRIX" | cut -d' ' -f1)"
EXPECT_BIN_SHA="$(python3 -c "import json,sys;d=json.load(open(sys.argv[1])).get('gate',{});print(d.get('binary_sha256',''))" "$CONTRACT")"
echo "[r6-batch] repo=$REPO"
echo "[r6-batch] contract=$CONTRACT sha256=${CONTRACT_SHA:0:16}"
echo "[r6-batch] matrix=$MATRIX sha256=${MATRIX_SHA:0:16}"
echo "[r6-batch] binary=$BIN"
if [ -n "$EXPECT_BIN_SHA" ]; then
  ACTUAL_BIN_SHA="$(sha256sum "$BIN" | cut -d' ' -f1)"
  if [ "$ACTUAL_BIN_SHA" = "$EXPECT_BIN_SHA" ]; then
    echo "[r6-batch] binary sha256 MATCHES contract gate (${EXPECT_BIN_SHA:0:16})"
  else
    warn "binary sha256 $ACTUAL_BIN_SHA != contract gate $EXPECT_BIN_SHA — the run would NOT be reproducible against the contract"
    [ "$SELF_CHECK" = 1 ] && die "self-check failed: binary identity mismatch"
  fi
else
  warn "contract gate.binary_sha256 empty — cannot pin binary identity for resume checks"
fi
echo "[r6-batch] checkpoint=$FS_CPT"
echo "[r6-batch] fs_dir=$FS_DIR"
echo "[r6-batch] runroot=$RUNROOT"
echo "[r6-batch] phase=$PHASE target_flag=$TGT_FLAG screening_target=$SCREEN_TARGET focus_target=$FOCUS_TARGET max_seeds=$MAX_SEEDS"
echo "[r6-batch] timeouts: se=$SE_TIMEOUT fs=$FS_TIMEOUT per_run=$PER_RUN_TIMEOUT"
echo "[r6-batch] concurrency cap_start=$CAP_START cap_min=$CAP_MIN cap_max=$CAP_MAX (guard slots=$GUARD_SLOTS)"
echo "[r6-batch] contract totals: total=$C_TOTAL ready=$C_READY blocked=$C_BLOCKED formal_phase=$C_PHASE focus_runids=$C_NFOCUS max_parallel=$C_MAXPAR seeds_per_cell=$C_SEEDS"

# ---------------- cell selection ----------------
SELECTED_FILE="$RUNROOT/selected_cells.txt"
FOCUS_FILE="$RUNROOT/focus_cells.txt"

python3 - "$CONTRACT" "$CELLS" "$CELLS_FILE" "$SELECTED_FILE" "$FOCUS_FILE" "$POL_JSON" <<'PY'
import json,sys,os
cpath, cells_arg, cells_file, out, fout, pol_path = sys.argv[1:7]
d=json.load(open(cpath))
ready=[e for e in d["entries"] if e.get("status")=="READY"]
by_id={e["run_id"]:e for e in ready}
want=None
if cells_arg and cells_arg!="all":
    want=[c.strip() for c in cells_arg.split(",") if c.strip()]
elif cells_file:
    want=[l.strip() for l in open(cells_file) if l.strip() and not l.startswith("#")]
if want is None:
    sel=[e["run_id"] for e in ready]
else:
    missing=[w for w in want if w not in by_id]
    if missing:
        raise SystemExit("unknown/not-READY RunIDs requested: %s" % ",".join(missing))
    sel=[w for w in want]
# [R6-FREQPOLICY] drop cells the frequency policy marks schedule_enabled=false.
# Applies to --cells all AND to explicit lists / --cells-file: a manually listed
# disabled cell is dropped loudly, never silently run. A missing overlay means
# no filter (optional overlay — same degradation as the campaign's gate).
dropped=[]
if pol_path and os.path.isfile(pol_path):
    pol=json.load(open(pol_path))
    off={e["run_id"]:e for e in pol.get("entries",[])
         if not e.get("schedule_enabled", True)}
    dropped=[r for r in sel if r in off]
    for r in dropped:
        print("[R6-FREQPOLICY] drop %s: schedule_enabled=false (run_policy=%s, exclusion_reason=%s)"
              % (r, off[r].get("run_policy","?"),
                 off[r].get("exclusion_reason") or "policy_excluded"))
    if dropped:
        sel=[r for r in sel if r not in off]
elif pol_path:
    print("[R6-FREQPOLICY] WARN policy overlay %s not found — selection is NOT policy-filtered"
          % pol_path, file=sys.stderr)
if not sel and dropped:
    raise SystemExit("[R6-FREQPOLICY] every requested RunID is schedule_enabled=false — nothing to schedule")
open(out,"w").write("\n".join(sel)+("\n" if sel else ""))
open(fout,"w").write("\n".join(d["verdict"].get("focus_runids",[]))+"\n")
print("[r6-batch] selected %d RunIDs (%d READY eligible, %d focus, %d policy-disabled dropped)" %
      (len(sel), len(ready), len(d["verdict"].get("focus_runids",[])), len(dropped)))
PY
[ $? -eq 0 ] || die "cell selection failed"

mapfile -t CELL_IDS < <(grep -v '^$' "$SELECTED_FILE" || true)
[ "${#CELL_IDS[@]}" -gt 0 ] || die "no cells selected"

# per-cell family (FS vs SE) and per-cell target: "runid<TAB>family<TAB>kind<TAB>target<TAB>model"
PLAN_FILE="$RUNROOT/plan.tsv"
python3 - "$CONTRACT" "$SELECTED_FILE" "$FOCUS_FILE" "$SCREEN_TARGET" "$FOCUS_TARGET" "$PLAN_FILE" <<'PY'
import json,sys
cpath, selp, focp, st, ft, outp = sys.argv[1:7]
d=json.load(open(cpath))
by_id={e["run_id"]:e for e in d["entries"]}
focus=set(x.strip() for x in open(focp) if x.strip())
rows=[]
for rid in (l.strip() for l in open(selp) if l.strip()):
    e=by_id[rid]
    fs = 1 if e.get("family")=="armtlb" else 0
    tgt = int(ft) if rid in focus else int(st)
    rows.append((rid, e.get("family","?"), "FS" if fs else "SE", tgt, e.get("model","?")))
with open(outp,"w") as f:
    for r in rows:
        f.write("%s\t%s\t%s\t%d\t%s\n" % r)
print("[r6-batch] plan written: %s (%d rows; FS=%d SE=%d focus=%d)" %
      (outp, len(rows), sum(1 for r in rows if r[2]=="FS"),
       sum(1 for r in rows if r[2]=="SE"), sum(1 for r in rows if int(r[3])==int(ft))))
PY
[ $? -eq 0 ] || die "plan generation failed"

FS_ROWS="$(awk -F'\t' '$3=="FS"' "$PLAN_FILE" | wc -l)"
# FS asset check only when an FS cell is selected
if [ "$FS_ROWS" -gt 0 ]; then
  for a in vmlinux ubuntu.img boot.arm64; do
    [ -f "$FS_DIR/$a" ] || die "FS asset missing: $FS_DIR/$a (set --fs-dir); $FS_ROWS FS cell(s) selected"
  done
  echo "[r6-batch] FS assets OK in $FS_DIR ($FS_ROWS FS cell(s))"
fi

print_example() {  # $1=kind (SE|FS) -> print the exact guard+campaign command
  local kind="$1" row
  row="$(awk -F'\t' -v k="$kind" '$3==k{print; exit}' "$PLAN_FILE")"
  [ -n "$row" ] || { echo "  (no $kind cell selected)"; return 0; }
  local rid fam k tgt model ck=""
  IFS=$'\t' read -r rid fam k tgt model <<<"$row"
  [ "$k" = "FS" ] && ck="--fs-checkpoint $FS_CPT "
  echo "  # $kind example ($rid, family=$fam, target=$tgt)"
  echo "  python3 tools/lsu_guard.py run --type experiment --desc \"R6-BATCH $rid\" \\"
  echo "      --runid $rid --log $RUNROOT/$rid/guard_rsrc.log --interval 60 --max-seconds $PER_RUN_TIMEOUT -- \\"
  echo "    env LSU_GEM5_BIN=$BIN LSU_FS_DIR=$FS_DIR LSU_GUARD_SLOTS=$GUARD_SLOTS LSU_GUARD_DIR=$RUNS_LSU/guard \\"
  echo "    python3 tools/lsu_campaign.py --matrix $MATRIX --outdir $RUNROOT --cells $rid \\"
  echo "      --phase $PHASE $TGT_FLAG $tgt --max-seeds-per-cell $MAX_SEEDS --max-parallel 1 \\"
  echo "      --timeout $SE_TIMEOUT --fs-timeout $FS_TIMEOUT ${ck}  # -> $RUNROOT/$rid/"
}

# ---------------- dry-run: print the plan, launch nothing ----------------
if [ "$DRY_RUN" = 1 ]; then
  echo
  echo "================ PLAN (no launch) ================"
  echo "  runroot=$RUNROOT"
  FOCUS_APPLIED="$(awk -F'\t' -v t="$FOCUS_TARGET" '$4==t' "$PLAN_FILE" | wc -l)"
  echo "  cells=${#CELL_IDS[@]}  FS=$FS_ROWS  SE=$(( ${#CELL_IDS[@]} - FS_ROWS ))  focus_applied=$FOCUS_APPLIED (contract focus_runids=$C_NFOCUS, $(( C_NFOCUS - FOCUS_APPLIED )) not READY)"
  echo "  per-RunID outdir: $RUNROOT/<RunID>/  (campaign --outdir=$RUNROOT)"
  print_example SE
  print_example FS
  echo "  --- first 5 plan rows ---"
  n=0
  while IFS=$'\t' read -r rid fam kind tgt model; do
    n=$((n+1)); [ "$n" -le 5 ] || continue
    printf '    %-14s %-9s %-3s target=%-5s -> %s/%s/\n' "$rid" "$fam" "$kind" "$tgt" "$RUNROOT" "$rid"
  done < "$PLAN_FILE"
  echo "  ... ($(( ${#CELL_IDS[@]} - 5 )) more; full plan: $PLAN_FILE)"
  echo "=================================================="
  if [ "$SELF_CHECK" = 1 ]; then
    echo "SELF-CHECK: PASS  (validated: args, contract parse, binary sha256, checkpoint dir, FS assets, runroot isolation, plan generation)"
    echo "SELF-CHECK: selected=${#CELL_IDS[@]} FS=$FS_ROWS runroot=$RUNROOT binary_sha=${ACTUAL_BIN_SHA:0:16}"
    echo "SELF-CHECK: NOTE nothing was launched (dry-run)."
  fi
  exit 0
fi

# ---------------- resume helpers ----------------
identity_ok() {  # $1=runid $2=target -> 0 if the recorded identity matches the env
  local f="$RUNROOT/$1/identity.json"
  [ -f "$f" ] || return 1
  python3 -c '
import json,sys
f,bsha,csha,msha,tgt,phase=sys.argv[1:7]
try: d=json.load(open(f))
except Exception: raise SystemExit(1)
ok = (d.get("binary_sha256")==bsha and d.get("contract_sha256")==csha
      and d.get("matrix_sha256")==msha and str(d.get("target"))==str(tgt)
      and d.get("phase")==phase)
raise SystemExit(0 if ok else 1)
' "$f" "$EXPECT_BIN_SHA" "$CONTRACT_SHA" "$MATRIX_SHA" "$2" "$PHASE"
}

run_complete() {  # $1=runid -> 0 if a finished cell_results.json is present
  local f="$RUNROOT/$1/cell_results.json"
  [ -f "$f" ] || return 1
  python3 -c '
import json,sys
try: d=json.load(open(sys.argv[1]))
except Exception: raise SystemExit(1)
raise SystemExit(0 if d.get("stop_reason") else 1)
' "$f"
}

write_identity() {  # $1=runid $2=target $3=kind $4=status
  python3 -c '
import json,sys,time
(p,rid,bsha,csha,msha,tgt,phase,kind,cpt,sto,fto,ms,host,status)=sys.argv[1:15]
json.dump({"runid":rid,"binary_sha256":bsha,"contract_sha256":csha,
           "matrix_sha256":msha,"target":int(tgt),"phase":phase,"kind":kind,
           "fs_checkpoint":cpt,"se_timeout":int(sto),"fs_timeout":int(fto),
           "max_seeds_per_cell":int(ms),"host":host,"seed_base":1,
           "status":status,"written":time.strftime("%Y-%m-%dT%H:%M:%S")},
          open(p,"w"), indent=1, ensure_ascii=False)
' "$RUNROOT/$1/identity.json" "$1" "$EXPECT_BIN_SHA" "$CONTRACT_SHA" \
    "$MATRIX_SHA" "$2" "$PHASE" "$3" "$FS_CPT" "$SE_TIMEOUT" "$FS_TIMEOUT" \
    "$MAX_SEEDS" "$(hostname)" "$4"
}

compress_events() {  # $1=run-dir ; compress raw event streams
  local dir="$1" n=0
  while IFS= read -r -d '' f; do
    gzip -9 -f "$f" 2>/dev/null && n=$((n+1))
  done < <(find "$dir" -type f -name 'prop_evt.txt' -print0 2>/dev/null)
  if [ "$COMPRESS_LOGS" = 1 ]; then
    while IFS= read -r -d '' f; do
      gzip -9 -f "$f" 2>/dev/null && n=$((n+1))
    done < <(find "$dir" -type f \( -name 'run.out' -o -name 'run.err' \) -size +8M -print0 2>/dev/null)
  fi
  [ "$n" -gt 0 ] && echo "[compress] $dir: $n file(s) gzipped"
  return 0
}

# ---------------- verify-only mode ----------------
if [ "$VERIFY_ONLY" = 1 ]; then
  echo
  printf '%-16s %-4s %-7s %-9s %-16s %s\n' RUNID KIND TARGET COMPLETE IDENTITY BIN/CPT
  bad=0
  while IFS=$'\t' read -r rid fam kind tgt model; do
    c="no"; identity_ok "$rid" "$tgt" && i="match" || i="MISMATCH/absent"
    run_complete "$rid" && c="yes"
    [ "$c" = "yes" ] && [ "$i" = "match" ] || bad=$((bad+1))
    meta="-"
    [ -f "$RUNROOT/$rid/identity.json" ] && meta="$(python3 -c "
import json,sys
try: d=json.load(open(sys.argv[1])); print(d.get('binary_sha256','')[:16], d.get('fs_checkpoint','').rsplit('/',1)[-1], d.get('status','-'))
except Exception: print('-')" "$RUNROOT/$rid/identity.json")"
    printf '%-16s %-4s %-7s %-9s %-16s %s\n' "$rid" "$kind" "$tgt" "$c" "$i" "$meta"
  done < "$PLAN_FILE"
  echo "VERIFY: $(( ${#CELL_IDS[@]} - bad ))/${#CELL_IDS[@]} complete+identity-match"
  [ "$bad" -eq 0 ] && exit 0 || exit 1
fi

# ---------------- host sampler + adaptive cap ----------------
SAMPLES="$RUNROOT/resource_samples.jsonl"
CAP_STATE="$RUNROOT/cap_state.json"
PREV_IOWAIT=0; PREV_TOTAL=0
PREV_PSWPIN=0; PREV_PSWPOUT=0; PREV_OOM=0; HAVE_PREV=0
SWAP_STREAK=0
CUR_CAP="$CAP_START"

read_iowait() { awk '/^cpu /{iowait=$6; total=0; for(i=2;i<=11;i++) total+=$i; print iowait, total}' /proc/stat; }
swap_counters() { awk '/^pswpin/{a=$2} /^pswpout/{b=$2} END{print a+0, b+0}' /proc/vmstat; }
oom_kills() { awk '/^oom_kill /{print $2+0} END{if(!NR)print 0}' /proc/vmstat; }
mem_avail_mib() { awk '/^MemAvailable/{print int($2/1024)}' /proc/meminfo; }
swap_free_mib() { awk '/^SwapFree/{print int($2/1024)}' /proc/meminfo; }
committed_mib() { awk '/^Committed_AS/{print int($2/1024)}' /proc/meminfo; }
gem5_rss() {  # "pid:rss_mib ..." for every process whose comm contains gem5
  local pid comm rss
  for pid in /proc/[0-9]*; do
    [ -r "$pid/comm" ] || continue
    comm="$(cat "$pid/comm" 2>/dev/null)" || continue
    case "$comm" in
      *gem5*) rss="$(awk '{print int($2*4096/1048576)}' "$pid/statm" 2>/dev/null)"
              [ -n "$rss" ] && printf '%s:%s ' "${pid##*/}" "$rss" ;;
    esac
  done
}

# guard GATE floor: never launch when lsu_guard would refuse (mem<12GiB or swap<4GiB)
can_acquire() {
  local m s
  m="$(mem_avail_mib)"; s="$(swap_free_mib)"
  [ "$m" -ge "$GUARD_MEM_FLOOR_MIB" ] && [ "$s" -ge "$GUARD_SWAP_FLOOR_MIB" ]
}

sample_and_adjust() {
  local now_iowait now_total diowait dtotal iowait_pm="null"
  local mem sw cf l1 gem5s npids pswpin pswpout d_swap d_oom cap_changed=""

  read -r now_iowait now_total < <(read_iowait)
  diowait=$(( now_iowait - PREV_IOWAIT )); dtotal=$(( now_total - PREV_TOTAL ))
  if [ "$HAVE_PREV" = 1 ] && [ "$dtotal" -gt 0 ]; then
    iowait_pm=$(( diowait * 1000 / dtotal ))
  fi

  read -r pswpin pswpout < <(swap_counters)
  if [ "$HAVE_PREV" = 1 ]; then
    d_swap=$(( (pswpin + pswpout) - (PREV_PSWPIN + PREV_PSWPOUT) ))
    d_oom=$(( $(oom_kills) - PREV_OOM ))
  else
    d_swap=0; d_oom=0
  fi

  PREV_IOWAIT="$now_iowait"; PREV_TOTAL="$now_total"
  PREV_PSWPIN="$pswpin"; PREV_PSWPOUT="$pswpout"; PREV_OOM="$(oom_kills)"
  HAVE_PREV=1

  mem="$(mem_avail_mib)"; sw="$(swap_free_mib)"; cf="$(committed_mib)"
  l1="$(cut -d' ' -f1 /proc/loadavg)"
  gem5s="$(gem5_rss)"
  npids="$(printf '%s' "$gem5s" | tr ' ' '\n' | grep -c ':' || true)"

  # swap growth: consecutive ticks with paging activity
  if [ "$d_swap" -gt 64 ]; then SWAP_STREAK=$((SWAP_STREAK+1)); else SWAP_STREAK=0; fi

  # ---- policy (documented in the header) ----
  local want="$CUR_CAP" iowait_high=0
  [ "$iowait_pm" != "null" ] && [ "$iowait_pm" -gt "$IOWAIT_LO_PM" ] && iowait_high=1
  if [ "$mem" -lt "$MEM_LO_MIB" ] || [ "$SWAP_STREAK" -ge 2 ] || [ "$iowait_high" = 1 ]; then
    want="$CAP_MIN"                                     # drop to 6
  elif [ "$mem" -gt "$MEM_HI_MIB" ] && [ "$mem" -ge "$GUARD_MEM_FLOOR_MIB" ] \
       && [ "$SWAP_STREAK" -eq 0 ] && [ "$d_oom" -eq 0 ] \
       && { [ "$iowait_pm" = "null" ] || [ "$iowait_pm" -lt "$IOWAIT_HI_PM" ]; }; then
    want="$CAP_MAX"                                     # raise to 8
  fi
  want=$(( want < CAP_MIN ? CAP_MIN : want ))
  want=$(( want > CAP_MAX ? CAP_MAX : want ))
  if [ "$want" != "$CUR_CAP" ]; then cap_changed="cap: $CUR_CAP -> $want"; CUR_CAP="$want"; fi

  printf '{"t":"%s","mem_available_mib":%s,"swap_free_mib":%s,"committed_mib":%s,"iowait_permille":%s,"load_1":%s,"gem5_n":%s,"gem5_rss_mib":"%s","swap_d_pages":%s,"oom_kill_delta":%s,"cap":%s}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$mem" "$sw" "$cf" \
    "$( [ "$iowait_pm" = "null" ] && echo null || echo "$iowait_pm" )" \
    "$l1" "$npids" "$gem5s" "$d_swap" "$d_oom" "$CUR_CAP" >> "$SAMPLES"
  printf '{"cap":%s,"mem_available_mib":%s,"swap_free_mib":%s,"updated":"%s"}\n' \
    "$CUR_CAP" "$mem" "$sw" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$CAP_STATE"

  echo "[sample $(date -u +%H:%M:%S)] mem_avail=${mem}MiB swap_free=${sw}MiB iowait=${iowait_pm}(pm) load1=${l1} gem5=${npids} rss=[${gem5s}] cap=${CUR_CAP}${cap_changed:+  $cap_changed}"
}

sampler_loop() {
  while [ -f "$RUNROOT/.sampler_run" ]; do
    sample_and_adjust
    sleep "$SAMPLE_INTERVAL"
  done
}

# ---------------- launcher ----------------
# The guard reads GUARD_DIR to compute its disk red line; if the dir does not
# exist snapshot() returns disk_*_gib=None and lsu_guard raises TypeError at
# the gate (guarded-None ordering bug in _disk_guard_reason). Always create it.
GUARD_DIR_PATH="$RUNS_LSU/guard"
mkdir -p "$GUARD_DIR_PATH" || die "cannot create guard dir $GUARD_DIR_PATH"

# Pre-flight gate: refuse to dispatch into a blocked gate (fail fast instead
# of launching N runs that would each come back rc=1 GATE_BLOCKED).
if [ "$IGNORE_GATE" != 1 ]; then
  GATE_OUT="$(LSU_GUARD_DIR="$GUARD_DIR_PATH" LSU_GUARD_SLOTS="$GUARD_SLOTS" \
              python3 "$REPO/tools/lsu_guard.py" gate 2>&1)" || true
  GATE_OK="$(printf '%s' "$GATE_OUT" | python3 -c '
import json,sys
try: d=json.loads(sys.stdin.read()); print("1" if d.get("ok") else "0")
except Exception: print("?")' 2>/dev/null || echo "?")"
  case "$GATE_OK" in
    1) echo "[r6-batch] pre-flight gate: OK" ;;
    0) echo "[r6-batch] pre-flight gate: BLOCKED — refusing to dispatch:"
       printf '%s\n' "$GATE_OUT" | sed 's/^/    /'
       die "guard gate blocked (see reasons above); free resources or pass --ignore-gate" ;;
    *) echo "[r6-batch] pre-flight gate: could not parse guard output — refusing to guess:"
       printf '%s\n' "$GATE_OUT" | sed 's/^/    /'
       die "guard gate unreadable" ;;
  esac
fi

: > "$RUNROOT/runs.tsv"
printf 'runid\tkind\ttarget\texit_code\tguard_reason\twall_s\tactivated\tstop_reason\tstatus\n' >> "$RUNROOT/runs.tsv"

touch "$RUNROOT/.sampler_run"
sampler_loop &
SAMPLER_PID=$!

declare -A JOB_PID=() JOB_PGID=() JOB_START=() JOB_TGT=() JOB_DIR=() JOB_KIND=()

request_stop() {  # INT/TERM: drain and kill in-flight sessions so no orphan survives
  touch "$RUNROOT/.stop_requested" 2>/dev/null
  echo "WARN: stop requested — killing ${#JOB_PID[@]} in-flight session(s)" >&2
  local rid pgid
  for rid in "${!JOB_PID[@]}"; do
    pgid="${JOB_PGID[$rid]:-}"
    [ -n "$pgid" ] && kill -TERM "-$pgid" 2>/dev/null
  done
}
trap 'request_stop' INT TERM

echo "[r6-batch] sampler started (pid $SAMPLER_PID, every ${SAMPLE_INTERVAL}s -> $SAMPLES)"
echo "[r6-batch] guard dir=$RUNS_LSU/guard (shared global cap of ${GUARD_SLOTS} experiment slots)"

launch_one() {  # rid fam kind tgt
  local rid="$1" fam="$2" kind="$3" tgt="$4"
  local dir="$RUNROOT/$rid"
  mkdir -p "$dir"
  local ck=(); [ "$kind" = "FS" ] && ck=(--fs-checkpoint "$FS_CPT")
  local cmd=(env "LSU_GEM5_BIN=$BIN" "LSU_GUARD_SLOTS=$GUARD_SLOTS" \
             "LSU_GUARD_DIR=$GUARD_DIR_PATH" "LSU_FS_DIR=$FS_DIR" \
             python3 "$REPO/tools/lsu_campaign.py" \
             --matrix "$MATRIX" --outdir "$RUNROOT" --cells "$rid" \
             --phase "$PHASE" "$TGT_FLAG" "$tgt" \
             --max-seeds-per-cell "$MAX_SEEDS" --max-parallel 1 \
             --timeout "$SE_TIMEOUT" --fs-timeout "$FS_TIMEOUT" "${ck[@]}")

  # record intended identity BEFORE launch (post-mortem for killed runs)
  write_identity "$rid" "$tgt" "$kind" launched

  setsid python3 "$REPO/tools/lsu_guard.py" run \
      --type experiment --desc "R6-BATCH $rid" --runid "$rid" \
      --log "$dir/guard_rsrc.log" --interval 60 --max-seconds "$PER_RUN_TIMEOUT" \
      -- "${cmd[@]}" >> "$dir/guard.out" 2>&1 &
  local pid=$!
  JOB_PID[$rid]=$pid
  JOB_PGID[$rid]=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')
  JOB_START[$rid]=$(date +%s)
  JOB_TGT[$rid]="$tgt"; JOB_DIR[$rid]="$dir"; JOB_KIND[$rid]="$kind"
  echo "[r6-batch] LAUNCH $rid ($fam, kind=$kind, target=$tgt) pid=$pid pgid=${JOB_PGID[$rid]} cap=$CUR_CAP"
}

reap_orphans() {  # $1=pgid — kill the whole session if it outlived the guard cap
  local pgid="$1"
  [ -n "$pgid" ] && kill -TERM "-$pgid" 2>/dev/null
  sleep 30
  [ -n "$pgid" ] && kill -KILL "-$pgid" 2>/dev/null
  [ -n "$pgid" ] && pkill -KILL -s "$pgid" 2>/dev/null
  return 0
}

collect_finished() {
  local rid pid rc now wall act stop reason status
  for rid in "${!JOB_PID[@]}"; do
    pid="${JOB_PID[$rid]}"
    kill -0 "$pid" 2>/dev/null && continue
    wait "$pid" 2>/dev/null; rc=$?
    now=$(date +%s); wall=$(( now - ${JOB_START[$rid]} ))
    reason="$(python3 -c '
import json,sys,os
p=sys.argv[1]; r="-"
if os.path.exists(p):
    for line in reversed(open(p,errors="ignore").read().splitlines()):
        line=line.strip()
        if line.startswith("{") and "run-finish" in line:
            try: r=json.loads(line).get("monitor_reason","-")
            except Exception: pass
            break
print(r)' "${JOB_DIR[$rid]}/guard.out" 2>/dev/null || echo "-")"
    act="-"; stop="-"
    if [ -f "${JOB_DIR[$rid]}/cell_results.json" ]; then
      read -r act stop < <(python3 -c "
import json,sys
try:
  d=json.load(open(sys.argv[1])); print(d.get('activated','-'), d.get('stop_reason') or '-')
except Exception: print('-','-')" "${JOB_DIR[$rid]}/cell_results.json")
    fi
    status="ok"
    [ "$rc" -ne 0 ] && status="FAILED(rc=$rc)"
    # rc=1 GATE BLOCKED and rc=2 ACQUIRE REFUSED are backpressure, not cell failure
    case "$rc" in 1) status="GATE_BLOCKED(requeue)";; 2) status="ACQUIRE_REFUSED(requeue)";; esac
    if [ "$wall" -ge "$PER_RUN_TIMEOUT" ]; then status="TIMEOUT-KILLED"; fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$rid" "${JOB_KIND[$rid]}" "${JOB_TGT[$rid]}" "$rc" "$reason" "$wall" \
      "$act" "$stop" "$status" >> "$RUNROOT/runs.tsv"
    if [ "$status" = "ok" ]; then
      compress_events "${JOB_DIR[$rid]}"
      write_identity "$rid" "${JOB_TGT[$rid]}" "${JOB_KIND[$rid]}" complete
      echo "[r6-batch] DONE   $rid rc=0 wall=${wall}s activated=$act stop=$stop"
    else
      echo "[r6-batch] FAILED $rid rc=$rc status=$status wall=${wall}s reason=$reason"
      case "$status" in *"(requeue)") RETRY_QUEUE+=("$rid");; esac
    fi
    unset 'JOB_PID[$rid]' 'JOB_PGID[$rid]' 'JOB_START[$rid]' 'JOB_TGT[$rid]' 'JOB_DIR[$rid]' 'JOB_KIND[$rid]'
  done
}

# dispatch loop
mapfile -t ROWS < "$PLAN_FILE"
declare -A ROW_BY_RID=()
PENDING=()
for row in "${ROWS[@]}"; do
  IFS=$'\t' read -r rid fam kind tgt model <<<"$row"
  ROW_BY_RID[$rid]="$row"
  if [ "$FORCE" != 1 ] && identity_ok "$rid" "$tgt" && run_complete "$rid"; then
    echo "[r6-batch] SKIP   $rid (already complete, identity match)"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$rid" "$kind" "$tgt" 0 "-" 0 "-" "-" "SKIPPED-RESUMED" >> "$RUNROOT/runs.tsv"
    continue
  fi
  PENDING+=("$row")
done

TOTAL_JOB=${#PENDING[@]}
echo "[r6-batch] pending RunIDs: $TOTAL_JOB (of ${#ROWS[@]})"
RETRY_QUEUE=()
IDX=0
while [ "$IDX" -lt "$TOTAL_JOB" ] || [ "${#JOB_PID[@]}" -gt 0 ]; do
  [ -f "$RUNROOT/.stop_requested" ] && { echo "[r6-batch] stop requested — draining"; break; }
  RUNNING=${#JOB_PID[@]}
  if [ "$IDX" -lt "$TOTAL_JOB" ] && [ "$RUNNING" -lt "$CUR_CAP" ]; then
    if can_acquire; then
      IFS=$'\t' read -r rid fam kind tgt model <<<"${PENDING[$IDX]}"
      launch_one "$rid" "$fam" "$kind" "$tgt"
      IDX=$((IDX+1))
    else
      echo "[r6-batch] backpressure: MemAvailable/SwapFree below guard GATE — not launching (cap=$CUR_CAP, running=$RUNNING)"
    fi
  fi
  if [ "${#JOB_PID[@]}" -gt 0 ]; then
    # outer watchdog: kill sessions that outlive per-run cap + 60 s of grace
    now=$(date +%s)
    for rid in "${!JOB_PID[@]}"; do
      pid="${JOB_PID[$rid]}"; pgid="${JOB_PGID[$rid]:-}"
      kill -0 "$pid" 2>/dev/null || continue
      if [ $(( now - ${JOB_START[$rid]} )) -ge $(( PER_RUN_TIMEOUT + 60 )) ]; then
        warn "outer watchdog: $rid exceeded ${PER_RUN_TIMEOUT}s+60s — killing session pgid=$pgid (reaping orphans)"
        reap_orphans "$pgid"
      fi
    done
    sleep 10
    collect_finished
  else
    sleep 5
  fi
done

# retry the backpressure-requeued ones once, serially at cap=1
if [ "${#RETRY_QUEUE[@]}" -gt 0 ] && [ ! -f "$RUNROOT/.stop_requested" ]; then
  echo "[r6-batch] retrying ${#RETRY_QUEUE[@]} backpressure-requeued RunID(s) at cap=1"
  CUR_CAP=1
  for rid in "${RETRY_QUEUE[@]}"; do
    row="${ROW_BY_RID[$rid]:-}"
    [ -n "$row" ] || continue
    IFS=$'\t' read -r _ fam kind tgt _ <<<"$row"
    launch_one "$rid" "$fam" "$kind" "$tgt"
    while [ "${#JOB_PID[@]}" -gt 0 ]; do sleep 10; collect_finished; done
  done
fi

rm -f "$RUNROOT/.sampler_run"
kill "$SAMPLER_PID" 2>/dev/null; wait "$SAMPLER_PID" 2>/dev/null
sample_and_adjust   # final tick

echo "[r6-batch] batch finished. summary: $RUNROOT/runs.tsv"
echo "[r6-batch]   ok       : $(awk -F'\t' 'NR>1 && $9=="ok"' "$RUNROOT/runs.tsv" | wc -l)"
echo "[r6-batch]   resumed  : $(awk -F'\t' 'NR>1 && $9=="SKIPPED-RESUMED"' "$RUNROOT/runs.tsv" | wc -l)"
echo "[r6-batch]   requeued : $(awk -F'\t' 'NR>1 && $9 ~ /requeue/' "$RUNROOT/runs.tsv" | wc -l)"
echo "[r6-batch]   failed   : $(awk -F'\t' 'NR>1 && $9!="ok" && $9!="SKIPPED-RESUMED"' "$RUNROOT/runs.tsv" | wc -l)"
echo "[r6-batch] resume with the SAME --runroot ($RUNROOT); complete RunIDs are skipped."
