#!/bin/sh
# install_rcS.sh — rebuild the W14 guest binary and re-embed it into the
# self-contained checkpoint rcS payloads.
#
# The host is native aarch64, so the canonical workload build is:
#     gcc -O2 -static -march=armv8-a+simd -o mmu_w14 mmu_w14.c
# (same flags as workloads/mmu/build_all.sh).
#
# The base template is configs/fs/mmu_w14_run.rcS.  Its gzip+base64 payload
# block is replaced in place; the five configs/fs/generated/mmu_w14_run_R0x.rcS
# templates are regenerated from the base template with `--all` -> `--ctx R0x`.
#
# Usage: ./install_rcS.sh [CC]
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../../.." && pwd)
CC=${1:-${CC:-gcc}}

echo "[w14] build"
$CC -O2 -static -march=armv8-a+simd -o "$HERE/mmu_w14" "$HERE/mmu_w14.c"

echo "[w14] embed"
python3 - "$ROOT" "$HERE/mmu_w14" <<'PY'
import base64
import gzip
import os
import sys

root, binary = sys.argv[1], sys.argv[2]
raw = open(binary, "rb").read()
# mtime=0 keeps the embedded gzip reproducible.
payload = base64.encodebytes(
    gzip.compress(raw, compresslevel=9, mtime=0)).decode("ascii")

base = os.path.join(root, "configs", "fs", "mmu_w14_run.rcS")
text = open(base, "r").read()
begin = "<<'MMU_W14_B64'\n"
end = "\nMMU_W14_B64"
i = text.index(begin) + len(begin)
j = text.index(end, i)
scoped = text[:i] + payload.rstrip("\n") + text[j:]
open(base, "w").write(scoped)

gen_dir = os.path.join(root, "configs", "fs", "generated")
os.makedirs(gen_dir, exist_ok=True)
for ctx in ("R01", "R02", "R03", "R04", "R05"):
    if "/tmp/mmu-w14 --all" not in scoped:
        raise SystemExit("base rcS lost the '--all' launch line")
    out = scoped.replace("/tmp/mmu-w14 --all", "/tmp/mmu-w14 --ctx " + ctx)
    open(os.path.join(gen_dir, "mmu_w14_run_%s.rcS" % ctx), "w").write(out)
print("[w14] base payload embedded; generated R01-R05 refreshed")
PY

echo "[w14] sha256"
sha256sum "$HERE/mmu_w14" "$ROOT/configs/fs/mmu_w14_run.rcS" \
          "$ROOT"/configs/fs/generated/mmu_w14_run_R0{1,2,3,4,5}.rcS
