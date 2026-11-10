#!/usr/bin/env bash
# Fleet window + quarantine feedback test, including a synthetic defect.
set -euo pipefail
cd "$(dirname "$0")/.."

W=work/test-fleet
rm -rf "$W"
mkdir -p "$W"
CORPUS=work/test-e2e/corpus
if [ ! -d "$CORPUS" ]; then
  echo "missing $CORPUS (run make test-e2e first)" >&2
  exit 1
fi

python3 tools/fleet.py --corpus "$CORPUS" --db "$W/db.sqlite" \
  --out-root "$W/runs" --cores 0-7 --window-cores 2 --window-seconds 2 \
  --windows 2 | tee "$W/fleet.log"

python3 tools/fleet.py --corpus "$CORPUS" --db "$W/db.sqlite" \
  --out-root "$W/runs" --cores 4-7 --window-cores 2 --window-seconds 2 \
  --windows 1 --inject flip:0:0:1:0 | tee "$W/inject.log"

python3 tools/quarantine.py --db "$W/db.sqlite" \
  --inject flip:0:0:1:0 --repeat 3 --found "$W/found" \
  --out "$W/quarantine.json" | tee "$W/quarantine.log"

python3 - "$W" <<'PY'
import json, os, sys
w = sys.argv[1]
fleet = json.loads(open(os.path.join(w, "fleet.log")).read().strip().splitlines()[-1])
inj = json.loads(open(os.path.join(w, "inject.log")).read().strip().splitlines()[-1])
q = json.load(open(os.path.join(w, "quarantine.json")))
assert fleet["executions"] > 0 and fleet["mismatches"] == 0, fleet
assert inj["mismatches"] > 0, inj
assert q["groups"] > 0 and q["confirmed"] == q["groups"], q
assert len(os.listdir(os.path.join(w, "found"))) > 0
print("PASS fleet:", fleet)
print("PASS synthetic window:", inj["mismatches"], "mismatches")
print("PASS quarantine:", q["groups"], "confirmed groups")
PY
echo "ALL PASS test-fleet"
