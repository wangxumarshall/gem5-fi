# FW05 workload provenance

## Exact pilot binary

All five v3.2.7 FW05 manifests record the same workload path and SHA256:

| Pilot | workload SHA256 |
|---|---|
| FW05-R01 | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |
| FW05-R02 | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |
| FW05-R03 | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |
| FW05-R04 | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |
| FW05-R05 | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |

The archived `bin/fw05_forward` has exactly that SHA256. The archive is the
original binary, not a newly rebuilt look-alike.

## Source

`src/fw05_forward.c` SHA256:
`c79b4be9ee11cffbc5ca986eb418bcc9aad439429191140f4c92ca9347dfdfa4`

Compile command: `gcc -O2 -static src/fw05_forward.c -o fw05_forward`
Host: `aarch64`, `gcc (GCC) 12.3.1 (openEuler 12.3.1-111.oe2403sp3)`.

The source is the version compiled to the archived binary in this worktree.
The five pilots were run on 2026-11-08 from this exact binary; no source
change occurred between the R01–R05 runs and this archive.

## Golden / checksum

`golden/fw05_forward.golden` = `0x67afad307642983e`.
The workload prints `checksum=0x<16 hex>`; both the host build and gem5 print
the same value. Oracle check: string equality with the recorded golden.

## Inputs

No external input file. The workload initializes two static arrays (`buf[64]`,
`slow[1<<20]`) to zero and derives all addresses/values from the loop index.
