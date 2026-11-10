# 论文规格映射（SiliFuzz, arXiv 2110.11519）

本文逐条对照 `docs/papers/ref/silifuzz.pdf` 第 2 节与 `silifuzz/` 的实现。
论文目标 ISA 是 x86-64；本仓库 `AGENTS.md` 要求目标架构为 ARM，因此 ISA 专属
部件映射为 ARM64 等价物，架构无关的规格（snapshot、player、checker、反馈闭环）
按原文实现。

## §2.2 Snapshot

| 论文要求 | 实现 |
| --- | --- |
| 全部用户可读寄存器初态，含 PC | `RegState`：x0–x30、sp、pc、pstate(NZCV)、fpcr、fpsr、v0–v31（`include/silifuzz/snapshot.hh`） |
| 内存映射 + 权限 + 数据 | `MemoryMapping{start,size,perms,data}`；页粒度，数据可短于映射，余下为零 |
| 期望结束状态（可多组） | `EndState{signal,sig_addr,regs,checksums}`；格式支持多组，生成时按论文“当前只保留端态一致者”写一组 |
| 异常 = 信号号 + 信号地址 | 捕获 `si_signo` / `si_addr`，例如 SIGSEGV 的故障地址、SIGILL 的 PC |
| 产生方式元数据 | `meta` JSON：source、candidate hash、code_bytes、mappings、attempts、created_unix |
| 无系统调用、单线程、确定性 | 生成/修复阶段拒绝 SVC/HVC/SMC；同核重复 3 次 + 4 个 NUMA 节点端态一致才收录 |
| 短小（典型 <100 字节） | 默认 4–1024 字节，ifuzz 序列中位约 100 字节；固定地址执行 |

**差异**：论文快照来自真实程序状态；本实现的初态由内容哈希确定性生成
（一半寄存器指向数据窗口，一半为小整数，x30 指向 BRK 跳板），因为输入是
随机指令序列而非进程快照。数据页为零填充（与论文“补充映射填零”一致）。

## §2.3 Player

| 论文要求 | 实现 |
| --- | --- |
| driver + harness 双进程隔离 | `Player`（driver）fork+exec `/proc/self/exe --harness`；harness 在独立地址空间执行 |
| MapMemory / WriteMemory / ProtectMemory / ExecuteSnapshot / ChecksumMemory | 协议命令 `kOpMap/kOpProtect/kOpChecksum/kOpExec`；另加 `kOpRunAll` 把一次执行的映射、执行、校验和合并成一个往返（语义相同，性能优化） |
| 绑定核心 | `sched_setaffinity` 在 harness 中设置 |
| 不匹配 = 潜在缺陷 | 逐项比较 signal、sig_addr、x0–x30/sp/pc/fpcr/fpsr/v0–v31、PSTATE.NZCV、每页 FNV-1a 校验和；不匹配写 `mismatches.jsonl` |
| x86 `0xCC` 结束陷阱 | ARM64 `BRK #0`（0xD4200000）；快照末尾与 RET 跳板各一个 |
| 执行可能崩溃的代码 | harness 捕获 SIGTRAP/SIGSEGV/SIGILL/SIGFPE/SIGBUS；信号帧入口恢复全部状态，`siglongjmp` 返回 |
| 3 秒 CPU 限制 | driver 每次执行 3 秒墙钟上限，超时杀 harness 并重启 |

PSTATE 只比较 NZCV：EL0 快照代码不能写 SSBS/PAN/SS 等位（见
`docs/limitations.md` 第 6 节）。

**实现要点**：glibc 的 `getcontext/setcontext` 只恢复调用者保存的寄存器子集
（反汇编确认），不能用于快照入口。harness 在 SIGTRAP handler 中改写内核信号帧
（`ucontext` 的 x0–x30/sp/pc/pstate 与 `fpsimd_context`），handler 正常返回后由
`rt_sigreturn` 一次性恢复完整状态；快照结束时再次进入 handler 并跳回命令循环。

## §2.4 Snapshot 生成

| 论文 | 本实现 |
| --- | --- |
| XED + libFuzzer 解码器代理 | `proxies/capstone_fuzz.cc`：Capstone ARM64 解码器，源码以 `-fsanitize=fuzzer-no-link` 插桩 |
| ifuzz 生成合法随机指令 | `tools/ifuzzgen`：vendored syzkaller `pkg/ifuzz/arm64`，按需生成 1–32 条合法指令 |
| Unicorn + libFuzzer 模拟器代理 | `proxies/unicorn_fuzz.cc`：Unicorn 2.1.4 ARM64，4 KiB 固定地址执行最多 1000 条指令 |
| 字典 | ifuzz 语料本身作为 Unicorn 目标的种子/字典来源（`work/seeds`） |

### §2.4.4 修复与端态录制

1. **补充映射**：执行触发 SIGSEGV/SIGBUS 且地址落在数据/栈窗口时，补一个零页
   重试，最多 32 个映射（论文：limited number of pages）。
2. **去不确定性**：静态拒绝 SVC/HVC/SMC；同核重复 3 次端态必须一致；
   超时/异常信号拒绝。
3. **端态确定**：在 4 个 NUMA 节点（0/32/64/96）各执行一次，端态完全一致才
   收录；否则记为 `multi_state` 丢弃（论文 §2.4.4 当前策略）。
4. **非法指令保留**：不做指令合法性过滤；SIGILL 是合法端态（附录 B 的
   illegal-instruction 行为在 ARM64 上同样保留）。

## §2.5 规模化执行

| 论文 | 实现 |
| --- | --- |
| checker 从磁盘读语料、批量、复用 | `sf_checker`：50 条一批，生成 1000 次均匀随机执行；批在内存中复用 |
| 多批并发隐藏 I/O | 生产者线程预取批，队列容量 2 批；workers 并发消费 |
| 多队列分发到每核 player | 每核一个 `Player`（driver + harness），共享执行队列 |
| 4 核（2 个 HT 对）/ 2 分钟窗口 | `fleet.py`：默认 4 物理核（本机无 SMT）、120 秒、窗口轮转覆盖全部 128 核 |
| 结果入库 | SQLite `runs` 表保存机器、核组、执行数、不匹配、速率、运行目录 |

另外提供 `--mode sweep`：每条语料在每核执行一次，用于全量验收；论文的
50/1000 采样对应 `--mode sampled`（默认）。

## §2.6 反馈闭环

| 论文 | 实现 |
| --- | --- |
| 隔离可疑机器/核 | `quarantine.py` 从结果库读取不匹配，按 (snapshot, core) 分组 |
| 多日复现才认定缺陷 | 单机条件下用多次独立复测代替“多日”；`--repeat` 次全部复现才 `confirmed` |
| 命中快照无条件保留 | `corpus/found/` 保存命中 snapshot；checker 实时复制 |
| 缺陷模式分析 | 结果库 + `mismatches.jsonl`（diff 字段：signal/sig_addr/xN/vN/内存页） |

**差异**：没有真实缺陷机器，闭环用 `--inject flip:REG:BIT:MOD:REM` 合成注入
验证（严格标注 synthetic）；真实硬件缺陷检测需要多机多日，本机未发现。

## 评估口径对照（§3）

论文：语料约 500,000；40% 仅 Unicorn/XED、20% 仅 ifuzz、40% 两者；45% 独有
发现；70% 缺陷影响同一物理核的两个逻辑核。

本机可复现的量：语料规模、执行吞吐、批处理 I/O 摊薄、跨核一致性、合成缺陷
检出延迟。不可复现的量：真实缺陷率、独有发现比例、物理核/逻辑核归属
（本机无 SMT、无缺陷机群）。所有实测数字见 `docs/measurements.md`。
