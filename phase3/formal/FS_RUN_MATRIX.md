# FS run matrix — MMU Pre-Formal Closure (final binary 6dca2195…)

All runs use unique TEST IDs and private outdirs; historical runs are never
overwritten. Binary: `CHAOS/gem5/build/ARM/gem5.opt`
SHA256 `6dca2195e1ec28e5094153dda1f5691a0038e80753ae994b4d5e6aa6fb9b8ff8`.

## Controls (no fault)

| TEST ID | Workload / rcS | Contexts | Purpose | Status |
|---|---|---|---|---|
| TEST-CTRL-W11-CLOSURE | W11 base `--all` | R01-R05 | M03 control | **PASS 5/5** (handshake) |
| TEST-CTRL-W12-R0x | W12 scoped R0x | one | M04 decoy PFN (final binary, scoped) | pending |
| TEST-CTRL-W13-CLOSURE | W13 base `--all` | R01-R05 | M05 control | pending |
| TEST-CTRL-W10S-WARM | W10S `--warm --target-va 0x4001400000` | M08 R05 control | pending |
| TEST-CTRL-W10S-COLD | W10S `--cold --target-va 0x4001100000` | M06 R02 control | pending |
| TEST-ENV-CTRL-W10 (reuse) | W10 `--ctx all` | R01-R05 | M06/M08 read controls | existing PASS |
| TEST-M07-P3B-CTRL-R01 (reuse) | W14 `--all` | R01-R05 | M07 control | existing PASS |
| runs/w9_trace_on_final (reuse) | W9 | R01-R05 | M01 control | existing PASS |

## Fault pilots

`python3 tools/mmu_formal_runner.py --pilot <ID> --model <M> --workload <W> --context <R> --target <VA> --eligible-event-index 1 --timeout 2400 [--extra-gem5-arg=...]`

| Model | Contexts | Target VA | Extra |
|---|---|---|---|
| M03 | R01-R04 | 0x4004000000 | `--mmu_target_instance l2_shared` |
| M03 | R05 | 0x4005000000 | mode Execute, instance l2_shared |
| M04 | R01-R04 | 0x4008000000 | decoy from `w12_decoy_map.json` |
| M04 | R05 | 0x4008000000 | mode Execute, instance itb |
| M05 | R01-R04 | 0x4010000000 | `--mmu_m05_decoy_va=0x4010200000` |
| M05 | R05 | 0x4010000000 | mode Execute + decoy VA |
| M06 | R01 | 0x4001000000 | W10, Read |
| M06 | R02 | 0x4001100000 | W10S-COLD-STORE, Write |
| M06 | R03 | 0x4001200000 | W10, Read |
| M06 | R04 | 0x4001300000 | W10, Read |
| M06 | R05 | 0x4001400000 | W10, Read |
| M07 | R01 | 0x400D000000 | Write |
| M07 | R02 | 0x400D000000 | Atomic |
| M07 | R03 | 0x400D200000 | Read |
| M07 | R04 | 0x400D400100 | Execute |
| M07 | R05 | 0x400D600100 | Execute |
| M08 | R01 | 0x4001000000 | W10, Read |
| M08 | R02 | 0x4001100000 | W10, Read |
| M08 | R03 | 0x4001200000 | W10, Read |
| M08 | R04 | 0x4001300000 | W10, Read |
| M08 | R05 | 0x4001400000 | W10S-WARM-STORE, Write |
| M01 | R01 | ASID 220 | regression |
| M02 | R01 | 0x4001000000 | regression |

## Deadlines / evidence

Every run has a 2400 s host timeout. M05 guest watchdog is 120 guest seconds.
A timeout is recorded as HANG/TIMEOUT only with the runner manifest's
`timed_out`, last tick/event, last PTW event, and gem5 exit code 124.

## Real finding (2026-11-11)

The decoy PFNs listed in the task brief (`0x83575/0x83542/0x83544/0x8353e/
0x83658`) came from the older `--all` control. On the final binary and a
scoped `--ctx R01` run the guest allocated target `0x8353e` and decoy
`0x83557`; the fail-closed M04 validation refused with
`fault_reason=decoy_key_mismatch`. Per-context scoped W12 controls are now the
authoritative decoy source (`w12_decoy_map.json`).
