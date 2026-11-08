# FW05 no-fault baselines (v3.2.8)

Workload: `fw05_forward`, SHA256
`0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf`.
Binary: `8377c011bb5916be67fa1132232440ae7f8be02351c3034624a339319a545bec`.
Golden: `0x67afad307642983e` (host build and gem5 agree).

Each baseline uses the pilot's Seed and initialization (no external input),
with the injector attached but probability 0 (`--lsq_struct_mode byte_flip
--probability=0.0`), so the fault path is disabled.

| Pilot | Seed | Exit | Actual | Golden | Oracle |
|---|---:|---:|---|---|---|
| R01 | 1025137124 | 0 | 0x67afad307642983e | 0x67afad307642983e | PASS |
| R02 | 1653118510 | 0 | 0x67afad307642983e | 0x67afad307642983e | PASS |
| R03 | 2442802213 | 0 | 0x67afad307642983e | 0x67afad307642983e | PASS |
| R04 | 899944922 | 0 | 0x67afad307642983e | 0x67afad307642983e | PASS |
| R05 | 2836530945 | 0 | 0x67afad307642983e | 0x67afad307642983e | PASS |

All five no-fault runs pass. The workload has no seed-varying legal output:
`seed` only drives the injector RNG, and with fault injection disabled the
program is deterministic.

## Relation to the five pilots

All five v3.2.7 manifests record the **same** workload SHA256 as the archive,
so the historical pilot results are reused (no rerun needed for provenance):
R01 SQUASHED/MASKED with oracle PASS; R02–R05 SDC with oracle FAIL. The
no-fault baselines all PASS, so the R02–R05 checksum differences are caused
by the injected wrong-source forwarding, not by a broken workload or oracle.

Raw logs: `FW05_Workload_Archive/baselines/R01..R05/stdout.log`.
Machine-readable: `evidence_v3_2_8/FW05_no_fault_baselines.csv`.
