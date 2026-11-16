#!/bin/bash
# Build the 8 When-v2 workload families x 5 contexts and record host goldens.
# Host is native aarch64: plain gcc -O2 -static, no cross toolchain.
#
# Determinism: compile the translation unit and start.S into *named* object
# files (a gcc temp-object name would otherwise land in .symtab) and disable
# the linker build-id, so two builds of the same source produce the same ELF
# SHA256 — required by the artifact manifest.
set -euo pipefail
cd "$(dirname "$0")"

FAMILIES="agu lq sq fwd_full fwd_partial md align lp"
CFLAGS=(-O2 -static -nostdlib -nostartfiles -fno-ident)
LDFLAGS=(-static -nostdlib -nostartfiles -Wl,--build-id=none)

mkdir -p bin obj
: > SHA256SUMS
: > MANIFEST.csv
printf 'variant,source,elf_sha256,golden,oracle\n' > MANIFEST.csv

gcc "${CFLAGS[@]}" -c -o obj/start.o start.S

for fam in $FAMILIES; do
    src="lsu_when_${fam}.c"
    for ctx in 1 2 3 4 5; do
        name="${fam}_C0${ctx}"
        out="bin/${name}"
        obj="obj/${name}.o"
        gcc "${CFLAGS[@]}" -DCONTEXT="${ctx}" -c -o "${obj}" "${src}"
        gcc "${LDFLAGS[@]}" -o "${out}" obj/start.o "${obj}"
        golden="bin/${name}.golden"
        "${out}" > "${golden}.out"
        tail -n 1 "${golden}.out" > "${golden}"
        rm -f "${golden}.out"
        sha=$(sha256sum "${out}" | awk '{print $1}')
        echo "${sha}  ${out}" >> SHA256SUMS
        printf '%s,%s,%s,%s,%s\n' "${name}" "${src}" "${sha}" "${golden}" "$(cat "${golden}")" >> MANIFEST.csv
    done
done

echo "built $(grep -c . SHA256SUMS) variants"
