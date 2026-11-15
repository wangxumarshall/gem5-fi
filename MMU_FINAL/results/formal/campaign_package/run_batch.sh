#!/usr/bin/env bash
# MMU formal campaign batch driver (sequential; one gem5 at a time).
# Frozen inputs: v3.0.2 authority + audited runner. Never generates seeds.
set -u
REPO=/home/sdc/gem5-fi-mmu-impl-v2
CAMP="$REPO/runs/MMU_FORMAL_CAMPAIGN_20261113"
XL="$REPO/phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx"
CSV="$REPO/phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2/MMU_40_Sample_Matrix.csv"
RUNNER="$REPO/tools/mmu_formal_runner.py"
OUTROOT="$CAMP/${ATTEMPT_DIR:-attempt_A01}"
BATCH="${1:?batch name required}"
shift
SAMPLES=("$@")

cd "$REPO" || exit 2
exec 9>"$CAMP/campaign.lock.$BATCH"
if ! flock -n 9; then
  echo "CAMPAIGN_LOCK_BUSY" >&2
  exit 3
fi

for SID in "${SAMPLES[@]}"; do
  LOG="$CAMP/logs/${SID}.log"
  RES="$CAMP/logs/${SID}.result.json"
  OUTDIR="$OUTROOT/$SID"
  if [ -f "$OUTDIR/Validation/verdict.json" ] && \
     grep -q '"gem5_exit_code": 0' "$OUTDIR/sample_manifest.json" 2>/dev/null; then
    echo "SKIP_ALREADY_COMPLETE $SID"
    python3 - "$SID" "$OUTDIR" "$RES" <<'PY' >> "$LOG" 2>&1
import json,os,sys
sid,out,res=sys.argv[1:4]
attempt=os.environ.get("ATTEMPT_DIR","attempt_A01").replace("attempt_","")
v=json.load(open(out+"/Validation/verdict.json"))
json.dump({"sample_run_id":sid,"attempt":attempt,"status":"COMPLETED",
           "skipped":"already_complete","verdict":v},open(res,"w"),indent=1)
PY
    continue
  fi
  START=$(date -u +%FT%TZ)
  echo "=== START $SID $START ===" | tee -a "$LOG"
  python3 "$RUNNER" --repo-root "$REPO" --excel "$XL" --csv "$CSV" \
    --out-root "$OUTROOT" --sample "$SID" --timeout-sec 7200 \
    >> "$LOG" 2>&1
  RC=$?
  END=$(date -u +%FT%TZ)
  echo "=== END $SID rc=$RC $END ===" | tee -a "$LOG"
  python3 - "$SID" "$OUTDIR" "$RES" "$RC" "$START" "$END" <<'PY' >> "$LOG" 2>&1
import json,os,sys
sid,out,res,rc,start,end=sys.argv[1:7]
rc=int(rc)
attempt=os.environ.get("ATTEMPT_DIR","attempt_A01").replace("attempt_","")
d={"sample_run_id":sid,"attempt":attempt,"runner_exit_code":rc,
   "started_utc":start,"finished_utc":end}
v=None
try:
    v=json.load(open(out+"/Validation/verdict.json"))
    d["verdict"]=v
    d["status"]="COMPLETED" if rc==0 and v.get("RecordIntegrity")=="PASS" else "FAILED"
except Exception as e:
    d["status"]="OUTPUT_INCOMPLETE"
    d["error"]=repr(e)
try:
    m=json.load(open(out+"/sample_manifest.json"))
    d["gem5_exit_code"]=m.get("gem5_exit_code")
    d["timed_out"]=m.get("timed_out")
except Exception:
    pass
json.dump(d,open(res,"w"),indent=1)
print("STATUS",d["status"])
PY
done
echo "BATCH_DONE $BATCH"
