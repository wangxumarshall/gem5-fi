# G0-03 Environment Lock — LSU 故障注入实验环境固化记录

生成：2026-09-29 17:00（Session 001，P1；实际命令输出为准，非转抄）

## 软件环境（构建工具链，经 2026-09-29 成功重建验证）

| 项 | 值 | 采集命令 |
|---|---|---|
| OS | openEuler 24.03 LTS-SP3（内核 6.6.0-145.3.16.148.oe2403sp3.aarch64） | cat /etc/os-release; uname -a |
| gcc/g++ | 12.3.1（openEuler 12.3.1-111.oe2403sp3） | gcc --version |
| Python | 3.11.6 | python3 --version |
| SCons | 4.5.2 | scons --version |
| swig | 不在 PATH（gem5 v25.1 构建不依赖系统 swig，2026-09-25 与 09-29 两次成功构建为证） | which swig（空） |
| 主机 ISA | aarch64（native，无交叉工具链） | uname -m |

## 实验平台身份

| 项 | 值 |
|---|---|
| gem5 基线 | vendored CHAOS/gem5（上游 62c7bf2 = v25.1.0.1-6，CHAOS/gem5_base_version.md） |
| 仓库 commit | 以各 run manifest 的 identity.git_commit 为准（双跑验证时 = ee77b992，C++ 树同 ed6323e6） |
| gem5.opt SHA256 | b64c808d449d0d63e369513671ffc222de99e2f9d29ca9cab33042ad879f3214（2026-09-29 15:38 守卫 -j8 增量重建，零警告） |
| lsu_proxy.py SHA256 | 4001eba155ed9ee0d932986393299184167a79af508eb6ed0cb7b20dac53ec93 |
| SE 负载 | workloads/directed/（43 ELF，gcc -O2 -static native 构建；各 manifest 记录单负载 SHA256） |
| FS 依赖 | gem5-fs/（vmlinux、ubuntu.img、boot.arm64、dtb，3.0G） |
| B0 平台 | O3_ARM_v7a_3 + DTLB=32 等 19 参数（evidence/P0/g0_04_g0_05_check.md 19/19 对照） |

## 资源与守卫

| 项 | 值 |
|---|---|
| 硬件 | Kunpeng-920 126 逻辑核 / 29 GiB RAM / 16 GiB swap / /home 171G 可用 |
| 守卫 | tools/lsu_guard.py（编译 -j8 单实例、实验单实例、60s 采样、WARNING/TRIP，T1-T7 验证 evidence/P0/guard_verify.out） |
| seed 规则 | tools/lsu_seed.py（SHA256("lsu-fi-v1|RunID|phase|sample_index") 低64位 = digest[24:32] 大端，self-test PASS） |

## 可重建性声明

同 commit + 同工具链下 `cd CHAOS/gem5 && scons -j8 build/ARM/gem5.opt` 于 2026-09-29 成功复现（27 分钟，零编译警告，scons done）。
本 lock 的字段即 environment 复现所需最小集合；正式 campaign manifest 将引用本文件 + 当次 commit SHA。
