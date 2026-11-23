# WHEN-5X3 W11–W14 工作负载复现说明 (workload build & repro)

## 工作负载源码与二进制

| Workload | 源码 | 静态二进制 | 动态二进制(实际运行) |
|---|---|---|---|
| W11 | `workloads/mmu_w5x3/w11.c` | `mmu_w11` | `mmu_w11.dyn` |
| W12 | `workloads/mmu_w5x3/w12.c` | `mmu_w12` | `mmu_w12.dyn` |
| W13 | `workloads/mmu_w5x3/w13.c` | `mmu_w13` | `mmu_w13.dyn` |
| W14 | `workloads/mmu_w5x3/w14.c` | `mmu_w14` | `mmu_w14.dyn` |

实际运行的是动态链接的 `.dyn` 二进制（依赖 guest 镜像内的 glibc 2.31，
`/lib/ld-linux-aarch64.so.1` + `work/guest_libs/libc.so.6`），以 base64+xz
嵌入在 `campaign/rcs/M*.rcS` 中，运行时解压到 `/tmp/w5x3_workload`。
`rcs` 头部声明 `binary_sha256=<hash>`，保证每次运行不静默使用陈旧负载。

## 构建命令

工具链：`aarch64-linux-gnu-gcc`（GCC 10.3.1，`/usr/bin/aarch64-linux-gnu-gcc`）。

```sh
# 动态版本（实际运行；链接 guest 自带 glibc 2.31）
aarch64-linux-gnu-gcc -O2 -march=armv8-a+simd -o mmu_w13.dyn mmu_w13.c
# 静态版本（自包含，供交叉验证/反汇编对照）
aarch64-linux-gnu-gcc -O2 -static -march=armv8-a+simd -o mmu_w13 mmu_w13.c
```

W11–W14 同理，替换源文件与输出名。

## 每 (Model,Context) 的 guest 上下文 (gen_rcs.py PLAN)

| Model | W13 上下文 | 语义 |
|---|---|---|
| M05-C02 | R05 | instruction fetch (ITLB/PTW) |
| M05-C03 | C03 | weak/dead consumer（读后丢弃，`observed` 强制 0） |
| M05-C04 | R04 | LDR -> 地址派生二次 LDR |
| M05-C05 | R03 | LDR -> CMP -> 条件分支 |

guest 上下文完整映射见 `campaign/gen_rcs.py` 的 `PLAN` 表；W13 内部上下文定义见
`w13.c` 顶部注释（R01 直接 LDR / R02 LDR+ADD / R03 LDR+CMP+branch /
R04 LDR+addr+LDR / R05 取指）。

## W13 关键 PC 反汇编

见 `work/disasm/W13_consumer_disasm.md`：

- `0x401c0c` — C03 weak consumer（`and w0,w0,#0xff`；后续 `mov x25,#0` 丢弃）。
- `0x401bb4` — C04 二次 load 的 consumer（`and x25,x25,#0xff`）。
- `0x401b50` — C05 比较分支的 consumer（`and w25,w25,#0xff`；后接 `cmp w25,#0x7d`）。

反汇编全量见 `work/disasm/mmu_w1[1-4].dyn.disasm.txt`。

## 复现

1. 冻结 checkpoint：`runs/mmu_bootF1/cpt.244799013609`（SHA256 见 `run_manifest.json`）。
2. 磁盘：`runs/disks/mmu_template.img`；内核 `gem5-fs/vmlinux`；bootloader
   `gem5-fs/boot.arm64`。
3. gem5：`CHAOS/gem5/build/ARM/gem5.opt`（0202c 观测版，SHA256 见
   `work/0202c_source_diff.md` 的 binaries 表）。
4. rcS：`campaign/rcs/<Model>-<Context>.rcS`；运行命令见各 run 的
   `Run_Log/command.txt`。
