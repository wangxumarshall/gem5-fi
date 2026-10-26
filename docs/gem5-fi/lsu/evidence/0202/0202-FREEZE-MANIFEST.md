# 0202 FREEZE MANIFEST — six-chain rebuild

**Frozen at**: 2026-10-27 (host `cathelper-k8s-worker2`)。**演进记录**：U1–U5 为 2026-10-26 六链 freeze（binary `a99031a8…`）；2026-10-27 的 U6（显式整数 seed 身份）/U7（多 fault 保守 all()）/阶段4（证据耐久性）+ cache 协议修复（策略1/2）**改变了工具 SHA 与二进制**，故本 freeze 刷新为 binary `b501de2c…` + 下表工具 SHA。旧 `a99031a8…` 下的六项哈希 seed 结果**不得**与新 freeze 混用。
**Rule**: every one of the six seed-1 canaries must reference exactly this manifest. Any C++
or run-semantics change invalidates this freeze → rebuild, re-hash, and restart from the
first canary. Mixing binaries across the six is forbidden.

## Git identity

| Item | Value |
|---|---|
| remote | `git@github.com:wangxumarshall/gem5-fi.git` |
| base branch | `origin/lsu-mdspec-20261019` = `de81266c` |
| working branch | `fix/0202-six-chain-20261026` |
| HEAD at freeze | `e38d937f9214dc6669a89ae6305dba211abe1e84`（= `R0202-T02F2-MSHR-REPAIR.md` 首发提交；U6/U7/阶段4 之后的 HEAD） |
| baseline contained | `3f3eb617` is an ancestor of HEAD (verified) |
| working tree | clean |

## gem5 binary (authoritative)

| Item | Value |
|---|---|
| path | `CHAOS/gem5/build/ARM/gem5.opt` |
| SHA256 | `b501de2cca321a9abe92d75a5ae303d8ac3a72041afaaeb12dcb92cedf5b2320` |
| size | (见构建日志；`20261027T015021`) |
| mtime | 2026-10-26 19:19:06 +0800 |
| `file` | ELF 64-bit LSB executable, ARM aarch64, dynamically linked, with debug_info, not stripped |
| links | `libpython3.11.so.1.0` → `/opt/python3.11/lib/libpython3.11.so.1.0` |
| build cmd | `cd CHAOS/gem5 && PYTHON_CONFIG=/opt/python3.11/bin/python3.11-config scons -j8 build/ARM/gem5.opt` |
| exit code | 0 (`scons: done building targets.`) |
| warnings/errors | 15 warnings (all optional-feature: protoc/png/hdf5/capstone/tcmalloc), 0 errors |
| superseded | `70aab844…`（Python 3.8 构建，无法运行任何配置，从未用于 canary）；`a99031a8…`（0202-REBUILD 六链用，T02-F2-W4 explicit seed 1 触发 gem5 `assert(mshr)` ⇒ 失效）；`843d0e94…`（策略1 中间态，仅用于验证 SIGABRT 消失）。 |

## Toolchain

| Item | Value |
|---|---|
| compiler | GCC/G++ 10.3.1 (gem5 warns: officially supports GCC 11–14.2) |
| Python (embedded) | CPython **3.11.9**, `/opt/python3.11` (source-built from huaweicloud mirror, `--enable-shared`) |
| Python (scons) | 3.8.18 |
| SCons | 4.11.1 |
| ld | GNU Binutils 2.37 |

## Tool / config SHA256 (consumed by the canaries)

| File | SHA256 |
|---|---|
| tools/lsu_runner.py | `50d239964a1daf3a0fe183e73aae4063ff3c4a4047011c271cf8f66ac47d93b8` |
| tools/lsu_campaign.py | `e5195793a8a23b114479c831508ecc0c16166fb0f8daf4fdd21a9a493d1f809a` |
| tools/lsu_chain_check.py | `d6a3e742a050da3a116f9f2d5b44b601669bbb30a3805087497f6cc0f7cb1a5e` |
| tools/lsu_ready_contract.py | `958f0e4b254df49027349bbfdf1817e60d8e5f0167bbfe12bf829854e8ed381f` |
| tools/lsu_seed.py | `b1270f4415a214ca4e81f57a396c05bc6f472b9f3e6866b3be555413a99ef665` |
| tools/lsu_guard.py | `04be4e8a9ca265cbcd5854420657c6188645f1a3383cdbccc6a7022916c3e75f` |
| tools/lsu_freq_policy.py | `ab573f048c3e58b4227c5abac13e1e6e232c2d5c7b23817d644b9afda61940d8` |
| tools/lsu_gem5_bin.py | `0ea568afbbe157da3988dfcfbde86edd4999fcd0e4efee625a90da300b337fd1` |
| tools/classify.py | `16c686ac67dc715cd1ebb5bbce4c61cd400010f5c5b60a8d30cf36ca9328b2f2` |
| tools/lsu_l5_classify.py | `80084a68acf9944f99633aaddac28ba9002fdcdb82b18c0683af41875e9529d3` |
| tools/lsu_prop_fields.py | `fea200fe18bd2e27852f38c33ac501ea5f87e802dd5b79d7ffd58ba8248f8c11` |
| tools/lsu_r6_golden_control.py | `f9ed530edaf96e3ee6a19a9b703e1d3e9c4ecf09dc8a7e6f49c14c54eba8d818` |
| configs/fs/lsu_b0_fs.py | `5762df1ffee5cdff2c0ca0fe92b770acebcbe440a7aead7a78d7164f5638c9c3` |
| configs/fs/tlb_probe.rcS | `54798b7d0557b29e48a16767beaf24d3255acda72b16cc3e14cdc0bf88157cfc` |
| configs/fs/boot_ckpt.rcS | `c48752e1ccb6ed1a17bce62c53dd11266470aadb045d664ff2a279eaeb0d73e5` |
| configs/se/arm_chaos_fs.py | `cbc56de2648f980a08199fba63bea4c24d7233d68c3fcb09887693c9da6256e4` |

## FS assets (submodule `gem5-fs` @ `aa234b94c9af2cbada5e8ef86a193e04869a22a9`)

| File | Bytes | SHA256 |
|---|---|---|
| gem5-fs/vmlinux | 237,716,656 | `9b9b9ce70bc6fb831461b527ccf36f124f1af8f3dc717d7ef13e62060aecfa7e` |
| gem5-fs/ubuntu.img | 2,361,393,152 | `eb6d8091b9ec38a92bcc1b1b7e9ecd4a4cbcfe32f80c2b5db21ecf7ad3c96b3c` |
| gem5-fs/boot.arm64 | 1,432 | `37ca07b55da2c0843d6670bb0693d21159236e0c6b74526f531abaeeaab51bfd` |

## Checkpoint + golden identity

Filled in after generation (Phase 5); the six canaries must reference these exact values.

| Item | Value |
|---|---|
| checkpoint dir | `runs/lsu/0202_fs_cpt_boot_20261026T193235/cpt.239515184727` |
| checkpoint identity | real `cpt.<tick>` named from the actual tick (239,515,184,727) — **not** the legacy `cpt.237949797015` |
| checkpoint contents | 10 files, 28 MB; `m5.cpt` 10,321,248 B; `board.physmem.store*.pmem` present |
| checkpoint file-manifest SHA256 | `4a991958e23133d60e815b3b87cc37013d20e1069b1f1298d202d1a29b22bd56` |
| boot command | `gem5.opt --outdir <dir> configs/fs/lsu_b0_fs.py --kernel gem5-fs/vmlinux --disk gem5-fs/ubuntu.img --bootloader gem5-fs/boot.arm64 --cpu Atomic --readfile configs/fs/boot_ckpt.rcS` (exit 0; guest→userspace→`m5 checkpoint`→`m5 exit`) |
| B0 proof in checkpoint | `[board.processor.cores.core.mmu.dtb] size=32`; CPU `BaseAtomicSimpleCPU` |
| golden oracle | `b6d81b360a5672d80c27430f39153e2c` (md5 of 1 MiB zeros; `TLB_PROBE_GOLDEN`) |
| golden runs | 2× no-injection O3 restore + `tlb_probe.rcS`; **both** oracle `b6d81b360a5672d80c27430f39153e2c` + `ok=10/10`, exit 0; measured wall **2274 s** (run1) / **2299 s** (run2) → canary `--fs-timeout 2700 s` |
| golden B0 proof | `[arm_chaos_fs] LSU-B0 applied: DTLB=32 LQ=16 SQ=16` |
