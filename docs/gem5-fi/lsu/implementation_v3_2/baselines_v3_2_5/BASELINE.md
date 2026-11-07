# LSU v3.2.5 baseline (2026-11-08)

- Base branch: `lsu-platform-v3.2.4` @ `d4b8276e`
- New branch: `lsu-platform-v3.2.5`
- Build: `scons -j16 build/ARM/gem5.opt`
- Pre-change binary SHA-256: see `binary.sha256`
- W5 `load_response` no-fault oracle: `checksum=0x99c106541150be0e` (Excel golden `99c106541150be0e`) — PASS
- Host: aarch64 openEuler 24.03, gcc 12.3.1, SCons 4.5.2
- Scope: pilots only; the 60 formal samples are not run in this round.
