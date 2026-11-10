#!/usr/bin/env bash
# End-to-end test: ifuzz generation -> snapshot fixing -> player replay ->
# checker on real cores -> synthetic defect detection.
set -euo pipefail
cd "$(dirname "$0")/.."

ROOT=$PWD
W=work/test-e2e
rm -rf "$W"
mkdir -p "$W"

./bin/ifuzzgen -n 300 -seed 42 -out "$W/cand" > "$W/gen.log"
echo "generated: $(find "$W/cand" -name '*.bin' | wc -l)"

./bin/sf_fix --in "$W/cand" --out "$W/corpus" --source e2e --jobs 4 \
  --ref-cores 0,4,8,12 --rejected "$W/rejected" | tee "$W/fix.json"
accepted=$(find "$W/corpus" -name '*.sfs' | wc -l)
if [ "$accepted" -lt 50 ]; then
  echo "FAIL: only $accepted snapshots accepted"
  exit 1
fi
echo "accepted: $accepted"

./bin/sf_player --corpus "$W/corpus" --core 0 --limit 200 | tee "$W/player.json"
python3 - "$W/player.json" <<'PY'
import json, sys
d = json.loads(open(sys.argv[1]).read().strip().splitlines()[-1])
assert d["failures"] == 0 and d["loaded"] >= 50, d
print("PASS player replay:", d)
PY

./bin/sf_checker --corpus "$W/corpus" --cores 0-3 --seconds 2 \
  --out "$W/check" | tee "$W/check.json"
python3 - "$W/check.json" <<'PY'
import json, sys
d = json.loads(open(sys.argv[1]).read().strip().splitlines()[-1])
assert d["mismatches"] == 0 and d["executions"] > 0, d
print("PASS checker:", d)
PY

set +e
./bin/sf_checker --corpus "$W/corpus" --cores 0-3 --seconds 2 \
  --inject flip:0:0:1:0 --out "$W/inject" > "$W/inject.json"
rc=$?
set -e
cat "$W/inject.json"
if [ "$rc" -ne 3 ]; then
  echo "FAIL: injected-defect checker exited $rc, expected 3"
  exit 1
fi
python3 - "$W/inject.json" <<'PY'
import json, sys
d = json.loads(open(sys.argv[1]).read().strip().splitlines()[-1])
assert d["mismatches"] > 0, d
print("PASS synthetic defect detected:", d["mismatches"], "mismatches")
PY
echo "ALL PASS test-e2e"
