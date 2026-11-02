#!/usr/bin/env bash
# FSU baseline gem5 build with exclusive lock and evidence capture.
# Usage: bash tools/fsu_build_gem5.sh <tag>
set -u
ROOT=/home/sdc/gem5-fi-fsu
EVID="$ROOT/docs/gem5-fi/fsu/evidence/build"
TS="${1:-$(date +%Y%m%dT%H%M%S)}"
LOG="$EVID/build-$TS.log"
META="$EVID/build-$TS.meta.txt"
LOCK="$EVID/build.lock"
mkdir -p "$EVID"

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "BUILD_LOCK_HELD: $LOCK" >&2
  exit 75
fi

{
  echo "tag=$TS"
  echo "start=$(date -Is)"
  echo "host=$(hostname)"
  echo "cwd=$ROOT/CHAOS/gem5"
  echo "head=$(git -C "$ROOT" rev-parse HEAD)"
  echo "branch=$(git -C "$ROOT" branch --show-current)"
  echo "remote_fsu=$(git -C "$ROOT" rev-parse origin/fsu)"
  echo "cmd=scons -j4 build/ARM/gem5.opt"
  echo "python_config=${PYTHON_CONFIG:-default}"
  echo "scons=$(scons --version 2>&1 | grep -m1 'SCons:')"
  echo "gcc=$(gcc --version | head -1)"
  echo "gxx=$(g++ --version | head -1)"
  echo "python=$(python3 --version)"
  echo "loadavg_start=$(cat /proc/loadavg)"
  echo "mem_start=$(free -h | sed -n '2p')"
} > "$META"

cd "$ROOT/CHAOS/gem5" || exit 1
scons -j4 build/ARM/gem5.opt
rc=$?

{
  echo "end=$(date -Is)"
  echo "exit_code=$rc"
  echo "loadavg_end=$(cat /proc/loadavg)"
  if [ -x build/ARM/gem5.opt ]; then
    echo "binary=$ROOT/CHAOS/gem5/build/ARM/gem5.opt"
    echo "binary_sha256=$(sha256sum build/ARM/gem5.opt | awk '{print $1}')"
    echo "binary_size=$(stat -c %s build/ARM/gem5.opt)"
    echo "binary_mtime=$(stat -c %y build/ARM/gem5.opt)"
  else
    echo "binary=MISSING"
  fi
} >> "$META"
exit $rc
