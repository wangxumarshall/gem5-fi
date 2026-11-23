#!/bin/bash
# Build the E2E-instrumented 8 workload families x 5 contexts.
# Arithmetic semantics are identical to the frozen When-v2 source; the only
# change is the read-free sw_mark4 event stream.  Host is native aarch64.
set -euo pipefail
cd "$(dirname "$0")"

FAMILIES="agu lq sq fwd_full fwd_partial md align lp"
CFLAGS=(-O2 -static -nostdlib -nostartfiles -fno-ident -ffixed-x28)
LDFLAGS=(-static -nostdlib -nostartfiles -Wl,--build-id=none)
FROZEN=${LSU_FROZEN_WORKLOADS:-$(pwd)/frozen}

mkdir -p bin obj
: > SHA256SUMS
printf 'variant,source,elf_sha256,golden,oracle,frozen_oracle,match\n' \
    > MANIFEST.csv

gcc "${CFLAGS[@]}" -c -o obj/start.o src/start.S

for fam in $FAMILIES; do
    src="src/lsu_when_${fam}.c"
    for ctx in 1 2 3 4 5; do
        name="${fam}_C0${ctx}"
        out="bin/${name}"
        obj="obj/${name}.o"
        gcc "${CFLAGS[@]}" -DCONTEXT="${ctx}" -c -o "${obj}" "${src}"
        gcc "${LDFLAGS[@]}" -o "${out}" obj/start.o "${obj}"
        got=$("${out}")
        want=$(cat "${FROZEN}/bin/${name}.golden")
        [ "$got" = "$want" ] || { echo "GOLDEN MISMATCH ${name}: $got != $want"; exit 1; }
        echo "$got" > "bin/${name}.golden"
        sha=$(sha256sum "${out}" | awk '{print $1}')
        echo "${sha}  ${out}" >> SHA256SUMS
        printf '%s,%s,%s,%s,%s,%s,%s\n' "${name}" "${src}" "${sha}" \
            "bin/${name}.golden" "$got" "$want" "YES" >> MANIFEST.csv
    done
done

echo "built $(grep -c . SHA256SUMS) variants; all goldens match the frozen source"
