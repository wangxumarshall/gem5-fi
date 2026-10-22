# R4-9-FSMC-A：W7 多核 litmus 载体端到端落地（载荷投放解通）+ A/D 两组逐项裁决

- 分支：`r4-9-fsmc-a`（worktree `.claude/worktrees/r4-9-fsmc-a`），base `d5fc8727`。
- 二进制（只读复用，**未做任何 scons 构建**）：
  `.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
  sha256 前缀 `7d52bc1392a10055`。
- 资产：`LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`；2 核 CHI 检查点
  `/tmp/r4-8-fsmc/mc_boot/cpt.243414599076`（R4-8-FSMC 产物，可再生）。
- 本报告是 **worktree 本地证据**（未改 MDSPEC worktree 的共享文档）。

## 0. 结论摘要

| 组 | 数量 | 裁决 | 依据 |
|---|---|---|---|
| A-1 | 4 | **`CARRIER_ROUTED_PENDING_RUN`**：载体 + 平台 + 载荷投放**真机端到端跑通**（4 次独立复现），campaign 路由 + golden 已接好；F0/F5 档位由 CHAOSExMon **真正消费**的旋钮表达 ⇒ routable。**本格自己的 campaign 样本尚未取、且注入对照未完成（§2.6），故不宣称 PASS** | §2.2–2.5 |
| A-2 | 6 | **`BLOCKED_TRIGGER_TIER_UNIMPL`**：`lsuTier`/`lsuSpanEvents`/`lsuWarmupEvents` 在 CHAOSExMon.py 有声明、在 .hh/.cc 里 **0 次**出现（grep 实证）⇒ F2 的 interval 与 F6 的确定性路径层没有落点；硬跑会让 F2/F6 与 F0 逐字节相同（错标） | §4 |
| B | 4 | 不变（注入器宿主构造性互斥） | R4-8-FSMC |
| C | 15 | 不变（模型语义未实现） | R4-8-FSMC |
| D | 6 | 不变（规格负载身份），理由补上 **find 实证**：PARSEC 开源但本仓库不可得 | §5 |

一句话：**"载荷投放"从 R4-8-FSMC 的"量化阻塞"变成"已解决并真机复现"**（§1/§3），
由此暴露的新阻塞是"CHAOSExMon 的 F 档位语义未实现"（§4），它把原来的 10 格一分为二。

## 1. 载荷投放的根因：两条实测事实 + 一个 ELF 装载坑

**事实 1（宿主侧算力成本可忽略）** —— 把 R4-8-FSMC `configs/fs/litmus.rcS` 里那段
860 KB base64 heredoc 原样喂给宿主 `sh`：

```
heredoc chars: 867741 -> decoded bytes: 650805
host sh+base64 decode rc=0 wall=0.020 s
host out size 642352
host 2.6MB file write wall=0.003 s
```

20 ms。所以**纯 shell + base64 的算力**不是 40 分钟量级的来源；成本在 gem5 guest
那条路径上（每次 exec/系统调用在 2 核 Ruby/O3 恢复态下都是**分钟**量级——仓库既有
记录：`m2_ptrchase.rcS` 2000 次 fork/exec ≈20 s/次）。

**事实 2（机制没问题，字节数是变量）** —— 换成 **1 × 9 KB freestanding ELF**
（base64 后 14 KB），**同一套机制**（readfile → `sh /tmp/next.sh` → base64 heredoc →
chmod → exec）在同一个 2 核 CHI 检查点上**跑到底**（§3）。R4-8-FSMC 的"三臂终态
一致"因此**不是机制坏**，而是"字节数 × guest 路径"超出了观测窗。

| 版本 | 载体 | 未压缩 | base64 后 | 结果 |
|---|---|---|---|---|
| R4-8-FSMC | 3 × libc 静态 ELF | 1.93 MB | 2.60 MB | 观测窗内解不出（三臂一致） |
| R4-9-FSMC-A | 1 × freestanding ELF | 9 392 B | ~14 KB | **端到端跑完**（§3） |

> 诚实边界：本轮**没有**再跑一遍 2.6 MB 原始载荷去画边际成本曲线（预算与宿主负载
> 都不允许）。把曲线量出来的工具已随本轮交付：`make -C workloads/litmus payload_free`
> 额外产出 `configs/fs/litmus_free_diag.rcS`，用**同一套 heredoc 机制**按
> 64 KB / 256 KB / 860 KB(→/dev/null) / 860 KB(→/tmp) 四级递升、每级打 `start`/`done`
> 标记；宿主带时间戳轮询 `board.terminal` 即得每级墙钟。下一轮要"每 MB 多少分钟"，
> 跑这一条就够（一次 gem5 调用）。

**事实 3（一个非显然的坑：零长 `.bss` PT_LOAD 段在 guest 里会 SIGSEGV）** ——
第一版加载荷能投放成功（sha256 逐字节一致），但一进 `_start` 就 `Segmentation fault`
(exit=139)，而同一份码在宿主 aarch64 上正常。定位靠 `readelf -l` 对照仓库里
**唯一能跑的 nostdlib 先例**（`configs/fs/sysreg_churn.rcS` 内嵌 ELF，解出来看）：

```
# 先例（可跑）                          # 我的（SIGSEGV）
LOAD 0x000000 0x400000 FileSiz=0x218    LOAD 0x000000 0x400000 FileSiz=0x1a44 MemSiz=0x1a44 R E
     MemSiz=0x218 R E                   LOAD 0x00fff0 0x41fff0 FileSiz=0x0    MemSiz=0x420 RW  <-- 零长段
（只有一个 LOAD）
```

修法：全局给**非零初值**（把数据挤出 .bss，进有文件字节支撑的 .data）+ `-Wl,-N`
（text+data 合并进同一个可写 LOAD）⇒ 回到"单段、FileSiz==MemSiz"的形态。
宿主行为不变（FINAL 不变），guest 不再崩。

## 2. 真机运行（原始输出）

命令模板（每次都 `flock /tmp/lsu_gem5_slot1.lock`，outdir 只写 `/tmp/r4-9-fsmc-a/`）：

```
gem5.opt --outdir=/tmp/r4-9-fsmc-a/<arm> configs/fs/lsu_multicore_fs.py \
    --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
    --bootloader=gem5-fs/boot.arm64 --num-cores=2 --coherence=chi --cpu=O3 \
    --restore-checkpoint=/tmp/r4-8-fsmc/mc_boot/cpt.243414599076 \
    --readfile=configs/fs/litmus_free.rcS
```

### 2.1 臂 A（零长 .bss 版）：投放成功、载荷 SIGSEGV

```
[boot_ckpt.rcS] restore pass: dispatching payload
[boot_ckpt.rcS] payload head: # litmus_free.rcS — W7 Atomic-Litmus 多核 FS payload（R4-9-FSMC-A，freestanding）。
[litmus_free.rcS] nproc=2
[litmus_free.rcS] cpuinfo processors=2
[litmus_free.rcS] decoding litmus_free
[litmus_free.rcS] sha256=3b82c14d049564775f8efbe0583fda96ab0da59b44be72a056e37a70e81ebd6d size=8384 emb=11180
[litmus_free.rcS] ===== running /tmp/litmus_free =====
Segmentation fault
[litmus_free.rcS] exit=139
[litmus_free.rcS] payload finished
```

`sha256` 与宿主产物**逐字节一致** ⇒ 投放链路（readfile → sh → base64）完全通了。

### 2.2 臂 B（单段 ELF + MP 自旋 50000）：SB 出 oracle，MP 无界

```
[litmus_free.rcS] sha256=8c34fdab093121441b4d00a0c9dfcc2b6f1a8c676bf27726b6e25a5dbbb53057 size=9392 emb=12524
[litmus_free.rcS] ===== running /tmp/litmus_free =====
LITMUS free begin nproc=2
LITMUS free sb nproc=2 rounds=64
LITMUS free sb hist r0r1: 00=0 01=34 10=30 11=0 forbidden(00)=0 bad=0 child_status=0
LITMUS free mp nproc=2 rounds=64 spin=50000
（此后 >4.5 min 无输出，被主动终止）
```

**这是本轮最关键的一条现场证据**：`forbidden(00)=0` 且直方图**两向都出现**
（01=34 / 10=30）—— 说明 2 核 CHI 平台上 core0/core1 的 store 双向可见
（真一致性），且无故障对照给出的正是"禁出现结果 = 0"的期望结果。
`child_status=0` 说明 guest 内的裸 `clone` + asm trampoline 工作正常。

### 2.3 臂 C（MP 自旋 2000/轮数 16，SB 可重复）：同一结论复现

```
LITMUS free sb hist r0r1: 00=0 01=34 10=30 11=0 forbidden(00)=0 bad=0 child_status=0
LITMUS free mp nproc=2 rounds=16 spin=2000
（同样被 MP 拖住）
```

SB 直方图与臂 B **完全一致**（01=34/10=30）⇒ 该配置下 SB 结果可重复。

### 2.4 臂 D（SB 64 / ATOM 32×4）：SB 可重复，ATOMIC 也被拖住

```
LITMUS free sb hist r0r1: 00=0 01=32 10=32 11=0 forbidden(00)=0 bad=0 child_status=0
LITMUS free mp SKIPPED (LITMUS_FREE_WITH_MP=0)
LITMUS free atomic nproc=2 rounds=32 incr_per_core=4
（ATOMIC 阶段 >5 min 未完成，被主动终止）
```

SB 第三次复现 `forbidden(00)=0`，且直方图这次是 **32/32 完全对称**。
ATOMIC 慢的原因同 MP 同类：每轮每核 4 次 ldxr/stxr CAS，跨核竞争让 stxr 失败重试
（宿主上每核要 150–200 次尝试才完成 128 次自增），而 guest 里**每次 LL/SC 都是一次
一致性事务** ⇒ 轮数/增量必须比宿主小一个量级。

### 2.5 臂 E（最终配置：SB 64 / MP 关 / ATOM 8×2）：第四个 SB 复现 + ATOMIC 仍未在窗内完成

```
LITMUS free begin nproc=2
LITMUS free sb nproc=2 rounds=64
LITMUS free sb hist r0r1: 00=0 01=30 10=34 11=0 forbidden(00)=0 bad=0 child_status=0
LITMUS free mp SKIPPED (LITMUS_FREE_WITH_MP=0)
LITMUS free atomic nproc=2 rounds=8 incr_per_core=2
（ATOMIC 阶段约 3.5 min 未完成，被主动终止）
```

**SB 第四次复现同一结论**（`forbidden(00)=0`，两侧 30/34）。ATOMIC 即使压到
8 轮 × 每核 2 次 CAS（每核仅 ~16 次 LL/SC 对）仍未在观测窗内完成 —— 说明 guest 里
**跨核 ldxr/stxr 竞争的重试链**（每次重试都是一次一致性往返）是主要成本，
与轮数近乎无关。这一点必须在报告里说清楚，因为它**决定了 A 组注入实验的可观测性**：

> **O01/O02/O03 的判别载体是"LDXR/STXR 原子性"**（`litmus_atomic.c` 文件头写得很明白：
> O01 腐蚀保留地址、O02 腐蚀 valid/version、O03 翻转状态码，都只会在 ldxr/stxr 竞争环
> 上显现；而 SB 里**根本没有 ldxr/stxr**）。所以 SB 的漂亮结果证明的是"平台一致性与
> 载体投放都可用"，**不能**替代 ATOMIC 作为注入判别式 —— 注入臂在 SB-only 配置下
> 预期无任何变化（这不构成"注入无效"的证据，只是没打到点子上）。

### 2.6 因此本轮**没有**完成"注入臂 vs 无故障臂"的对照（诚实声明）

未完成的直接原因、以及它不属于"格子被静默解锁"的理由：

1. 本轮完成的是 **A 组的载体侧**（投放 + 平台 + 故障-free litmus oracle + campaign
   路由/golden/档位门/断言），不是 A 组任何一格的**注入实验结论**。
2. 注入臂需要 ATOMIC 在 guest 内可观测，而 ATOMIC 在 4 次真机尝试（32×4、8×2）中都
   超出观测窗（§2.4/§2.5）⇒ **没有可比对的注入结果**。
3. 因此 10 格的裁决**一格都没有被解锁**：4 格是 `CARRIER_ROUTED_PENDING_RUN`
   （routable，本格样本未取），6 格是 `BLOCKED_TRIGGER_TIER_UNIMPL`；
   `tests/test_lsu_fsmc_verdict.py` 的双向断言把这两件事都钉住了。
4. 下一位接手方的**具体下一步**（都不需要重建 gem5）：
   * 把 ATOMIC 也想个"能观测"的写法：例如每核**只做 1 次** CAS、轮数 4：
     `-DLITMUS_FREE_ATOM_ROUNDS=4 -DLITMUS_FREE_ATOM_INCR=1`（Makefile 的 FREE_CFLAGS
     支持 `-D`），或者把竞争环换成"两核对不同地址各做 CAS"（牺牲竞争强度、换可观测性）；
   * 或者换 CPU 模型/缩短恢复态（本轮的宿主负载 ~115 与此有关）；
   * 一旦 ATOMIC 在 guest 内出结果，先跑无故障臂取 FINAL，再跑 `--chaos_exmon` 注入臂
     对照（命令模板见 §2），并把结果回填进本报告与 `FSMC_GOLDEN_FINAL`。

### 2.7 运行预算与时间账

本轮共 7 次 gem5 调用（全部 `flock /tmp/lsu_gem5_slot1.lock`、每次 `timeout 2100`，
outdir 只写 `/tmp/r4-9-fsmc-a/`）：3 条被 MP/ATOMIC 拖住而**主动终止**（未把槽位留到轮外，
结束时用 `flock -n` 确认 slot1 空闲），其余跑到底。单臂墙钟：恢复到用户态约 1.5–2.5 min，
载荷 3–8 min（视轮数）。预算上限 10，实际 7。

## 3. 为什么 MP 默认不跑（一条实测教训，不是省事）

MP 的读取侧用"有界自旋"等 flag：`for (i<2000) if (flag) break;`。宿主上
`timeouts=0`；但 guest 里**每一轮都跑满上界**。量级：SB 的 64 轮（约 10 次内存
操作/轮）实测约 2.5 min ⇒ 宿主侧一次 cache 事务 ≈0.2 s；于是 2000 次自旋 ≈ 数百秒/轮
（16 轮 ⇒ 小时级）。也就是说：**"主机上立刻可见"的 flag，在 guest 里要等到下一次
跨核一致性事务才可见，而自旋的粒度远小于该延迟**。

结论与取舍（诚实）：MP 原本只承担"跨核可见性判别器"的角色，而 **SB 的两侧直方图
已经给出同一证据**（01/10 两向都出现），所以 MP 不再承担判别职责；需要它在宿主上做
逻辑自检时用 `-DLITMUS_FREE_WITH_MP=1` 打开（宿主上 `timeouts=0`、`violations=0`）。
这条**不删代码、只改默认**，并把理由写进源码注释与 Makefile。

## 4. A 组 10 格的拆分：为什么 F0/F5 可以、F2/F6 不行

**F 档位的规格定义**（`docs/gem5-fi/lsu/task_plan.md:18`）：
`F0 单次瞬态；F1–F4 重复/突发；F5 永久；F6 确定性路径/矩阵规定层`；
`chaos_trigger.hh` 里 F1/F2/F3 是 **interval 档**（F2 = 260 000 cycles）。

**CHAOSExMon 实际消费了什么**（源码级）：

```
$ grep -rn "lsu\|Lsu\|LSU" CHAOS/gem5/src/arch/arm/CHAOSExMon/CHAOSExMon.hh CHAOSExMon.cc
（空）
```

* `CHAOSExMon.py:40-42` 声明了 `lsuTier` / `lsuWarmupEvents` / `lsuSpanEvents`；
* `CHAOSExMon.cc` 的构造函数只读 `probability / firstClock / lastClock /
  maxFaults / rngSeed / writeLog`；`inWindow()` 只做**时钟**窗；
  事件计数控制只有内部 `geometric(0.1)` 首跳（`events_to_skip`）；
* 它**不 include `chaos_trigger.hh`**（同 grep 为空）。

⇒ **F0**（单次瞬态）= `maxFaults=1`；**F5**（永久）= `maxFaults=0`（无限）——
都能用既有旋钮诚实表达；**F2 的 interval** 与 **F6 的确定性路径层**没有落点，
硬跑只能让 F2/F6 与 F0 产生**逐字节相同**的 flag 序列（错标，不是近似）。

campaign 侧（`tools/lsu_campaign.py`）：新家族 `exmon-fsmc`（`lsu_multicore_fs.py`
+ `litmus_free.rcS` + 2 核 CHI 检查点 `LSU_FS_MC_CHECKPOINT`，缺检查点**大声拒绝**）；
`_fsmc_tier_flags()` 只表达 F0/F5，其余返回 `None` ⇒ `_fsmc_tier_block_reason()`；
**故意不传 `--exmon_lsu_tier`**（在 C++ 里不被消费，传了就是半接线）。

## 5. D 组（W13 = PARSEC）审计

**(i) PARSEC 在本仓库内是否可得/可构建（aarch64）？——不可得，有实证：**

```
$ find . -iname "*parsec*" -not -path "./.git/*"
./CHAOS/gem5/tests/gem5/parsec_benchmarks                 <- gem5 上游测试脚手架
./CHAOS/gem5/configs/deprecated/example/gem5_library/x86-parsec-benchmarks.py
$ find . \( -iname "*dedup*" -o -iname "*ferret*" -o -iname "*streamcluster*" \
            -o -iname "*blackscholes*" \) -not -path "./.git/*"
（空）
```

唯一痕迹是 gem5 上游脚手架，而它**自己就是关掉的**：

```python
# CHAOS/gem5/tests/gem5/parsec_benchmarks/test_parsec.py:53
print("WARNING: PARSEC tests are disabled. This is due to our GitHub "
      "Actions self-hosted runners only having 60GB of disk space. The "
      "PARSEC Disk image is too big to use.")
return  # Remove this line to re-enable PARSEC tests.
        valid_hosts=(constants.host_x86_64_tag,),   # 仅 x86_64 宿主
        uses_kvm=True,
```

它依赖 `--resource-directory` 里的**预编译磁盘镜像**（下载物）+ KVM，且仅 x86_64
宿主。仓库内没有 PARSEC 源码 tarball、输入集、aarch64 构建。
**结论**：PARSEC **不是授权问题**（开源），是**本仓库不可得**——要它就得联网取
源码 + 输入集 + 在 aarch64 上构建 + 打进 guest 镜像，是独立工程量。
这条按"实测不可得"记录，而**不**按"法律障碍"记录。

**(ii) 换一个仓库内开源多线程载体能否保住格子语义？——不能，P09 还是构造性冲突：**

* `P09`（dirty-evict）走 **classic CHAOSCache**；W13 的语义是"**多线程真实应用**"。
  classic 多核**没有跨核一致性**（v25 `src/mem/cache/noncoherent_cache.*`，一致性目录
  已不存在——R4-8-FSMC §1.2 已实证），所以在 P09 能挂载的平台上多线程共享内存语义
  **不成立**：**载荷语义与注入器宿主构造性互斥**，与换什么开源负载无关。
* `O09`（RMW operand hook）另有模型缺口；其格子语义含"PARSEC 的多线程竞争窗口"，
  用仓库内单线程微探针替代会把结论适用范围从"真实多线程应用"缩成"单线程微探针"
  ——那是**改写格子定义**，属规格级决定。

**逐行裁决**（6 格）：全部保持 BLOCKED，理由写死为"PARSEC 实测不可得 + 模型/宿主
缺口"，**不擅自替换负载**。

## 6. 交付物与指纹

| 产物 | sha256 |
|---|---|
| `workloads/litmus/litmus_free` | `474d2a33fb92e815…`（完整值见 `tools/lsu_fsmc_verdict.py` 的 `CARRIER_SHA256`） |
| `configs/fs/litmus_free.rcS` | `144c9e3ba373a65b…` |
| `configs/fs/litmus_free_diag.rcS` | `d4f5256c1ec722f4…` |

三者 sha256 固定进 `CARRIER_SHA256`，由 `tests/test_lsu_fsmc_verdict.py` 实测磁盘比对
（防无声漂移）。宿主 golden：`FINAL=6b39e7aaa74b663f`（最终配置 SB 64 / ATOM 8×2；含 MP 时宿主亦为 0 计数）。

## 7. 真正不可替代的东西 / 给集成方

1. **2 核 CHI 检查点是 /tmp 临时产物**（启动≈16 min）。不在 git 里。集成方要么按
   R4-8-FSMC §3 的命令重生成，要么把目录固化到 git 外并设 `LSU_FS_MC_CHECKPOINT`。
   campaign 在检查点缺失时**大声拒绝**（理由串含 `fsmc-infra`），不静默跑。
2. **`CHAOSExMon` 的 F 档位语义**（6 格）：F2/F6 要落地必须给 CHAOSExMon 接上
   `chaos_trigger.hh`（C++ + 重建）。载体、平台、投放、golden、路由都已就位，
   下一次 scons 窗口内可一并做。
3. **PARSEC 身份**（6 格）：规格级决定，见 §5。
4. campaign 跑这些格需要 `LSU_FS_DIR` 指向真实资产目录（`fs_asset()` 缺省落在
   worktree 内，而 worktree 不带 `gem5-fs/` 子模块内容）。
5. **不要**把 `--exmon_lsu_tier` 接进 campaign：它在 CHAOSExMon 里不被消费。
   接上就等于声称一个没实现的窗。
