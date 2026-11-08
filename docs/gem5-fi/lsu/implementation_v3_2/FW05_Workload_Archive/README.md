# FW05 workload archive — `fw05_forward`

This is the exact workload used by the five v3.2.7 FW05 pilots and frozen by
the researcher as FW05's only formal workload (LSU v3.2.8).

## Layout

```
src/fw05_forward.c          C source
bin/fw05_forward            exact pilot binary (aarch64, static)
golden/fw05_forward.golden  expected output
build.sh                    rebuild from source
run_pilot.sh                gem5 pilot command
config/                     recorded gem5 command lines of R01/R02
logs/compiler_version.txt   host + compiler provenance
inputs/README.md            input/initialization statement
PROVENANCE.md               SHA256 and pilot-manifest provenance
SHA256SUMS                  hashes of every archive file
```

## Rebuild

```bash
./build.sh
```

The archived binary is authoritative. A rebuild may differ in toolchain
build-id/metadata bytes; verify it by the printed checksum
(`checksum=0x67afad307642983e`), not by binary SHA.

## Run

```bash
./run_pilot.sh /tmp/fw05_r01 1025137124 1
```

The pilot runner used for the formal records is
`docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`:

```bash
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model FW05 --pilot-id FW05-R01 --context-index 1 --preserve-sample-id \
  --outdir /tmp/fw05_r01
```

## Input and oracle

There is no external input file: `buf` and `slow` are zero-initialized static
arrays, so initialization is fully described by the source. The program prints
`checksum=0x<16 hex>`; the golden is `0x67afad307642983e`. The same value is
printed by the host build and by gem5; the gem5 run must exit 0.

## Historical workload

The v3.2.2 Excel used W8 `alignment` for FW05. It cannot reliably produce an
eligible wrong-source forwarding pair (probe `alt=no`), so it is retained only
as historical configuration (see `../excel/FW05_OLD_NEW_DIFF_v3.2.3.md`).
