# 0202 ENVIRONMENT LOCK — six-chain rebuild

Measured on the 0202 host at takeover (2026-10-26). No value here is copied from any 0101
record; every line was produced by a command on this host.

## Host

| Item | Value |
|---|---|
| hostname | `cathelper-k8s-worker2` |
| uname | `Linux 5.10.0-60.139.0.166.oe2203.aarch64 #1 SMP Thu May 30 05:18:35 UTC 2024 aarch64` |
| OS | openEuler **22.03 LTS** (`/etc/os-release`; NOT 24.03 as in the old notes) |
| CPU | HiSilicon Kunpeng-920, 64 cores, 2 sockets × 32, no SMT, max 3000 MHz |
| NUMA | 2 nodes (node0 CPUs 0-31, node1 CPUs 32-63), distance 10/32 |
| RAM | 376 GiB total, 366 GiB available at takeover |
| Swap | **0 GiB at takeover** (vendor `/etc/fstab` swap line is commented out, line 16) |
| Disk | `/home` 1.1 T (822 G free), `/` 69 G (42 G free), `/tmp` tmpfs 189 G |

## Deviation recorded (disclosed)

`tools/lsu_guard.py gate` refuses every run when `SwapFree < 4 GiB`. With swap disabled at
boot this gate could never pass. Resolved by **provisioning** swap (not bypassing the gate):
16 GiB swapfile `/home/swapfile.0202`, **not** persisted to `/etc/fstab`. After this,
`lsu_guard.py gate` returns `"ok": true`. Any operator can revert with
`sudo swapoff /home/swapfile.0202 && sudo rm /home/swapfile.0202`.

## Toolchain (verified present; not upgraded blindly)

| Tool | Path | Version |
|---|---|---|
| git | /usr/bin/git | 2.33.0 |
| gcc / g++ | /usr/bin/gcc | 10.3.1 (gem5 warns: officially supports GCC 11–14.2) |
| ld | /usr/bin/ld | GNU Binutils 2.37 |
| python3 (build) | /usr/local/bin/python3 → /usr/local/bin/python3.8 | 3.8.18 (`python3-config` → `/usr/local/include/python3.8`, `Python.h` present) |
| python3 (system) | /usr/bin/python3 → python3.9 | 3.9.9 (not used by scons) |
| scons | /home/sdc/.local/bin/scons (runs on python3.8) | 4.11.1 |
| m4 | present | GNU M4 1.4.19 |
| make | present | GNU Make 4.3 |
| pkg-config | present | 1.8.0 |
| zlib | /usr/include/zlib.h present | — |
| numactl | present | — |
| zstd | /usr/bin/zstd | 1.5.0 (used to restore FS assets) |
| timeout | coreutils | 9.0 |
| /usr/bin/time | installed via `dnf install time` | GNU time 1.9 |

## Python packages (installed for the build/3.8, user scope)

| Package | Version | Why |
|---|---|---|
| mako | 1.3.12 | gem5 ISA codegen (was MISSING → hard build blocker) |
| jsonschema | latest (pip --user) | `tools/campaign.py`, `tools/runner.py` |
| PyYAML | 6.0.2 | present |
| pytest | 8.3.5 | present |

**Absent but non-essential** (gem5 disables the features; warnings only): `protoc`, `png.h`,
HDF5, capstone, tcmalloc. Not required for the ARM FS binary used here.

## Git

| Item | Value |
|---|---|
| remote | `git@github.com:wangxumarshall/gem5-fi.git` (HTTPS times out on this host; **SSH works**) |
| base branch | `origin/lsu-mdspec-20261019` = `de81266c` |
| baseline contained | `git merge-base --is-ancestor 3f3eb617 HEAD` → exit 0 |
| working branch | `fix/0202-six-chain-20261026` |
| pre-existing remote branch | none (branch created fresh) |

## FS assets (submodule `gem5-fs` @ `aa234b94c9af2cbada5e8ef86a193e04869a22a9`)

The submodule ships **zstd-compressed split parts**; the real files were produced by
`bash gem5-fs/restore.sh`. All three required files exist and are non-empty.

| File | Bytes | SHA256 |
|---|---|---|
| gem5-fs/vmlinux | 237,716,656 | `9b9b9ce70bc6fb831461b527ccf36f124f1af8f3dc717d7ef13e62060aecfa7e` |
| gem5-fs/ubuntu.img | 2,361,393,152 | `eb6d8091b9ec38a92bcc1b1b7e9ecd4a4cbcfe32f80c2b5db21ecf7ad3c96b3c` |
| gem5-fs/boot.arm64 | 1,432 | `37ca07b55da2c0843d6670bb0693d21159236e0c6b74526f531abaeeaab51bfd` |
| gem5-fs/armv8_gem5_v1_1cpu.dtb | 3,470 | `4c73fedd3a393f006432a88ba788664b4c9903936aeb34d79ad464f715405240` |

Sizes match the `gem5-fs/readme.md` documented values byte-for-byte (independent confirmation).

## Concurrency rules in force

- Compile: `scons -j8`, **one compile task at a time** (LSU 总方针 §8.1 hard cap 8).
  CLAUDE.md says `-j16` for clean builds; the conservative cap 8 is used and the conflict is
  recorded in findings.
- gem5: start at 1, profile, then at most 2; **hard cap 4**.
