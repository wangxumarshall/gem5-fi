#!/usr/bin/env bash
# LSU v3.3.3 — reproduce the frozen campaign from a fresh clone.
#
# Usage:
#   bash reproduce_from_clone.sh <clone_dir> [archive_root] [--regen]
#
# The frozen final_config scripts hardcode ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12.
# This wrapper rewrites only the ROOT line of *copies* under <clone>/.repro/; the
# originals in audit_v3_3_3/trace_closure/final_config/ are never edited. The
# transformed copies' SHA256 values are recorded for auditability.
#
# --regen additionally rebuilds the collector and final reports from the archived
# raw data. It never reruns the 120 experiments.
set -euo pipefail

CLONE=${1:?usage: reproduce_from_clone.sh <clone_dir> [archive_root] [--regen]}
ARCH=${2:-/home/sdc/lsu-v333-archive}
REGEN=0
for a in "$@"; do [ "$a" = "--regen" ] && REGEN=1; done

BIN_SHA=62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
CFG_SHA=8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
CAMPAIGN=LSU-V333-FINAL-20261112

cd "$CLONE"

echo "== 1. source closure =="
sha256sum --quiet -c audit_v3_3_3/trace_closure/final_config/SOURCE_MANIFEST.sha256
echo "SOURCE_OK"

echo "== 2. config =="
get_cfg=$(sha256sum configs/se/lsu_proxy.py | cut -d' ' -f1)
[ "$get_cfg" = "$CFG_SHA" ] || { echo "config hash mismatch: $get_cfg" >&2; exit 1; }
echo "CONFIG_OK $get_cfg"

echo "== 3. binary =="
mkdir -p build/ARM
cp "$ARCH/binary/gem5.opt.v333-62e1b1be" build/ARM/gem5.opt
chmod +x build/ARM/gem5.opt
get_bin=$(sha256sum build/ARM/gem5.opt | cut -d' ' -f1)
[ "$get_bin" = "$BIN_SHA" ] || { echo "binary hash mismatch: $get_bin" >&2; exit 1; }
echo "BINARY_OK $get_bin"

echo "== 4. transformed scripts =="
mkdir -p .repro
for s in 01_launch_campaign.sh 02_manifest_only.sh 03_full_collector.sh 04_final_reports.sh launch_commands_final.sh; do
  sed "s#^ROOT=.*#ROOT=$PWD#" "audit_v3_3_3/trace_closure/final_config/$s" > ".repro/$s"
  chmod +x ".repro/$s"
done
( cd .repro && sha256sum 01_launch_campaign.sh 02_manifest_only.sh 03_full_collector.sh 04_final_reports.sh launch_commands_final.sh ) | tee .repro/transformed.sha256

echo "== 5. 120-task dry run =="
bash .repro/01_launch_campaign.sh --dry-run

if [ "$REGEN" = "1" ]; then
  echo "== 6. regenerate collector and reports from archived raw data =="
  mkdir -p runs/lsu
  cp -a "$ARCH/raw_extracted/formal_v333_final_20261112" runs/lsu/
  bash .repro/02_manifest_only.sh
  bash .repro/03_full_collector.sh
  FORCE=1 bash .repro/04_final_reports.sh
  echo "REGEN_OK"
fi

echo "REPRODUCTION_CHECKS_DONE (no experiments rerun)"
