# gem5 AArch64 全系统 (FS) 仿真指南

本目录 (`/home/sdc/vmcore/gem5-fi/gem5-fs/`) 包含用于支持 `gem5-fi`（AArch64 鲲鹏 920 / TaiShan V110 架构）进行全系统仿真的四件套核心文件。

> **注意**：本目录的绝对路径是 `/home/sdc/vmcore/gem5-fi/gem5-fs/`（位于 `gem5-fi` 仓库内部）。早期版本的本文档曾误写为 `/home/sdc/vmcore/gem5-fs/`（缺少 `-fi`），该路径**不存在**，会导致 gem5 报 `fatal: Failed to open file`。下方所有命令已使用正确路径。

## 1. 核心文件说明

四件套缺一不可，均已就绪且与源码严格对应（以下字节大小与路径经 `stat` 实测确认）：

| 文件 | 大小 | 说明 |
|---|---|---|
| `vmlinux` | 237,716,656 B | Linux 5.15.36 版本的 AArch64 内核镜像（ELF64，入口 `0xffffffc008000000`，带 KASLR 内核虚拟基址，含 debug_info，`readelf -h` 确认 Machine: AArch64）。版本字符串 `Linux version 5.15.36 (kaustavg@citra) #1 SMP PREEMPT Thu Apr 28 13:51:08 PDT 2022`。 |
| `ubuntu.img` | 2,361,393,152 B | Ubuntu 20.04 Raw 格式原始磁盘镜像（解压自官方 arm64 img）。 |
| `boot_emm.arm64` 等 | 1,432 B | AArch64 Bootloader，已直接在当前主机 `gem5-fi/CHAOS/gem5/system/arm/bootloader/arm64/` 源码树下用 `gcc` 原生编译，与源码 100% 对应。 |
| `armv8_gem5_v1_1cpu.dtb` 等 | 3,470 B | Device Tree Blob 设备树文件，已在当前主机 `gem5-fi/CHAOS/gem5/system/arm/dt/` 源码树下用 `dtc` 原生编译生成。 |

## 2. 如何启动 FS 仿真

确保已编译 gem5 二进制文件（如 `build/ARM/gem5.opt`，本仓库实测大小 1,101,653,000 B，2026-08-26 16:45 编译就绪）。推荐使用 gem5 自带的 `fs_bigLITTLE.py` 配置脚本启动。

### 基础运行命令示例（VExpress_GEM5_V1 单核）：

```bash
# 切换到 gem5 根目录
cd /home/sdc/vmcore/gem5-fi/CHAOS/gem5

# 运行全系统仿真（注意：四件套路径在 gem5-fi/gem5-fs/ 下，勿漏 -fi）
./build/ARM/gem5.opt configs/example/arm/fs_bigLITTLE.py \
    --kernel /home/sdc/vmcore/gem5-fi/gem5-fs/vmlinux \
    --disk  /home/sdc/vmcore/gem5-fi/gem5-fs/ubuntu.img \
    --bootloader /home/sdc/vmcore/gem5-fi/gem5-fs/boot_emm.arm64 \
    --dtb   /home/sdc/vmcore/gem5-fi/gem5-fs/armv8_gem5_v1_1cpu.dtb \
    --machine-type VExpress_GEM5_V1 \
    --caches \
    --mem-size 2GB
```

启动后 gem5 会先打印（实测确认，真实输出）：

```
info: kernel located at: /home/sdc/vmcore/gem5-fi/gem5-fs/vmlinux
info: Using bootloader at address 0x10
info: Using kernel entry physical address at 0x80000000
info: Loading DTB file: /home/sdc/vmcore/gem5-fi/gem5-fs/armv8_gem5_v1_1cpu.dtb at address 0x88000000
info: Simulated platform: VExpress_GEM5_V1
```

> **性能提示（诚实）**：单核全系统仿真启动到 Linux bash 极慢——gem5 单线程每秒仅模拟数千至数万条指令，Linux 完整启动常需数十分钟到数小时真实墙钟时间。若仅验证启动到内核解压/挂载阶段，建议用 `timeout` 包裹并观察日志。

（若需多核，将 dtb 替换为 `armv8_gem5_v1_2cpu.dtb` 等，并添加 CPU 数量参数如 `--big-cpus 2`。）

## 3. 连接终端 (m5term)

启动上述命令后，gem5 会开启终端监听端口（默认 3456）。在另一会话用 `m5term` 连接查看 Linux 启动日志或交互（m5term 已在 `gem5-fi/CHAOS/gem5/util/term/m5term` 编译就绪，实测 81,440 B）：

```bash
cd /home/sdc/vmcore/gem5-fi/CHAOS/gem5/util/term
make            # 已编译则可跳过
./m5term localhost 3456
```

## 4. 与 gem5-fi 故障注入结合

在验证上述标准 FS 仿真能成功进入 Linux bash 后，可结合 `gem5-fi` 的 CHAOS 注入器在目标模拟周期或指定 PC 处执行故障注入。P-D1（CHAOSLSQFwd）/ P-D2（CHAOSAddrPath）/ P-D3（CHAOSPTW）三模块均已编译进 `gem5.opt`（`nm` 确认符号在二进制内）。

**关键事实（源码静态确证）**：H6/H7 的 SE 模式 null 结果根因已查明——D2 钩子（`lsq.cc:1146 corruptAddr`）在 `translateTiming` 前破坏 vaddr，但 SE 模式走 `translateMmuOff`→`setPaddr(vaddr)` 直接物理映射（物理内存从 0 起仅 512 MiB），byte7 清零后地址仍落在有效物理区间故不 fault；D3 钩子（`table_walker.cc:1959 corruptDescriptor`）在 `doLongDescriptor`，SE 模式从不调用页表走查器故 `numFaultsInjected=0`。**FS 模式下 SCTLR.M=1，走真实 TLB 查询→页表走查器**，D2/D3 钩子才会被真正触发——故 H6/H7 必须在 FS 模式验证。详见 `docs/cases/core179-microarch-rootcause-synthesis/FI_DESIGN_SUPPLEMENT.md` 顶部诚实声明。

所有内存映射与系统寄存器配置与 VExpress_GEM5_V1 及配套 bootloader 兼容。
