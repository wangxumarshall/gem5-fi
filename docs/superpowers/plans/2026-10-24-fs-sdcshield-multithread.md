# FS 模式 sdcshield 多线程验证通路（eigen_svd 双线程实证）— 计划与实测记录

日期：2026-10-23（验证执行）/ 2026-10-24（沉淀提交）
分支：feat/fs-sdcshield-multithread
前置：2026-09-22 `2026-09-22-sdcshield-fi-eval.md` Task 3.1 的设计（第二磁盘 +
readfile 通路）——本计划将其落地并扩展到**多核**。

## 1. 意图（why）

此前 gem5-fi 的 guest 侧验证全部走 SE 模式单线程 dual kernel（`workloads/sdcshield/`），
多线程行为（per-CPU pthread worker、跨线程屏障、一致性流量）在仿真里**不可达**。
本计划打通 **FS 模式（真实 Linux 5.15.36 + 真实 pthread）多核多线程验证通路**：
guest 内跑完整 sdcshield 二进制（含 forkfd 子进程 + per-CPU worker），
以 `eigen_svd_double -n 2` 为首个实证对象。

## 2. 交付物（one patch per unit）

| Patch | 文件 | 单元 |
|---|---|---|
| 1 | `tools/fs_mk_sdcshield_disk.sh` | 无 root 制盘（mke2fs -d）：sdcshield + 依赖库 + 宿主 loader → 32MB ext2 第二磁盘 |
| 2 | `configs/se/arm_fs_sdcshield.py` | 多核 FS config：`--num-cpus`、`--extra-disk`（vdb，CowDiskImage 包装）、`--readfile`、`--timeout`（SIGALRM）、`--save-checkpoint/--checkpoint`（KernelBooted 点两阶段） |
| 3 | `gem5-fs-work/guest_hold.sh`、`gem5-fs-work/guest_svd.sh`、`.gitignore` | guest 侧脚本（hold 交互模式 / 一次性 svd 验证模式）+ 产物排除（sdcshield.img、diskroot/） |

## 3. 关键工程决策（实测驱动）

1. **宿主 loader 方案**：guest 是 Ubuntu 20.04（glibc 2.31），宿主是 openEuler
   （glibc 2.34）。`export LD_LIBRARY_PATH=/mnt/libs` 会污染 guest 工具
   （实测 `_dl_fatal_printf GLIBC_PRIVATE` 崩溃）。改为
   `ld-linux-aarch64.so.1 --library-path /mnt/libs /mnt/bin/sdcshield`
   显式运行，不污染全局。
2. **第二盘必须 CowDiskImage 包装**：guest mount ext2 写 superblock，
   RawDiskImage(read_only=True) 触发 gem5 panic
   （实测 `disk_image.cc:147: panic: Cannot write to a read only disk image`）。
3. **一次 boot + 交互注入**：Atomic 下 boot ~20-40 分钟，逐轮 readfile 迭代成本过高。
   `--listener-mode=on` + `guest_hold.sh`（**不可 `exec sleep`** ——会替换 shell 使 console
   无 reader；正确做法是让脚本自然结束或后台 sleep，Ctrl-C 后 getty 重生 shell）+
   socat TCP 3456 注入命令。
4. **仿真速率适配**：~4ms guest/s wall。时长类参数（`-t`）不可行，用
   `--max-test-loop-count=K` 限定迭代；mesh 大内存用例（自适应 ~1.8GB）仿真不实用。
5. **Python ≥3.10 硬门槛**：gem5 25 stdlib PEP 604 注解，`PYTHON_CONFIG` 必须指向
   3.10+（本机编译 ~/py311，`PYTHON_CONFIG=$HOME/py311/bin/python3.11-config scons`；
   增量重链不够——libpython 是构建期探测的）。

## 4. 自验证证据（2026-10-23 实测，board.terminal 原文）

**环境**：`--num-cpus=2 --cpu=Atomic`，Ubuntu 20.04.4 LTS aarch64 guest，
Linux 5.15.36，`nproc`=2。

**① eigen_svd_double 双线程**（`-n 2 -O eigen_svd_double.mdim=64 --max-test-loop-count=1`）：

```
test-plans:
  fullsocket: [ { starting_cpu: 0, count: 2, threads: 2 } ]
- test: eigen_svd_double
  result: pass
  test-options: eigen_svd_double.mdim: 64
- test: mce_check
  result: pass
exit: pass
```

**② 多线程并发铁证**：`mesh_upi_sse_asymm_int -n 2 --max-test-loop-count=3` →
`exit: pass`。该用例单线程下必然拓扑 SKIP（`thread_count() < 2 → log_skip`）；
pass 即证明双 worker 真并发（跨核生产/消费 + sense-reversal 屏障 + 原子
fetch_add/CAS 在 2 个仿真 CPU 上正确工作）。

**③ 制盘脚本**：`bash tools/fs_mk_sdcshield_disk.sh` →
`sdcdisk: 22/8192 files (0.0% non-contiguous), 4816/8192 blocks`，e2fsck clean。

**④ guest 内二进制与依赖**：`/mnt/bin`（sdcshield）+ `/mnt/libs`（8 库 + loader）
列表正常；`--list-tests` 输出正常（memcpy0…）。

## 5. 诚实边界

- Atomic CPU：多线程**功能语义**成立（pthread 原语、一致性、golden byte-exact）；
  无时序精度。O3/TIMING 可选，慢 1-2 个数量级。
- 时长类验证（`-t` 长跑）在仿真速率下不可行。
- CHAOS 注入器四个 SE hook 在 FS 模式空转（gem5-doc :1063）——
  注入 × 多线程交叉验证仍待后续（FS 侧注入器是 Phase 3 TLB/SYS-reg 路线）。
- checkpoint 两阶段（`--save-checkpoint`）本轮未走通（实例静默死亡，原因未定），
  交互注入模式已覆盖需求；两阶段留待后续排查。

## 6. 复现命令

```bash
cd /home/sdc/wangxu/gem5-fi
bash tools/fs_mk_sdcshield_disk.sh          # 产物 gem5-fs-work/sdcshield.img
cd CHAOS/gem5
./build/ARM/gem5.opt --listener-mode=on --outdir=../../runs/fs_svd2 \
  ../../configs/se/arm_fs_sdcshield.py \
  --kernel=/home/sdc/wangxu/gem5-fi/gem5-fs/vmlinux \
  --disk=/home/sdc/wangxu/gem5-fi/gem5-fs/ubuntu.img \
  --bootloader=/home/sdc/wangxu/gem5-fi/gem5-fs/boot.arm64 \
  --root-partition=/dev/vda1 \
  --extra-disk=/home/sdc/wangxu/gem5-fi/gem5-fs-work/sdcshield.img \
  --readfile=/home/sdc/wangxu/gem5-fi/gem5-fs-work/guest_hold.sh \
  --num-cpus=2 --cpu=Atomic --timeout=28800
# 等 board.terminal 出现 "GUEST READY"，然后：
(printf '\x03'; sleep 25; echo "<命令>"; sleep 60) | socat - TCP:127.0.0.1:3456
# 命令模板（宿主 loader，不污染 guest）：
#   /mnt/libs/ld-linux-aarch64.so.1 --library-path /mnt/libs /mnt/bin/sdcshield \
#     -e eigen_svd_double -n 2 -O eigen_svd_double.mdim=64 --max-test-loop-count=1 -v
```
