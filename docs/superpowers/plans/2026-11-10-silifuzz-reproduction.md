# SiliFuzz 规格复现计划（ARM64 / 单机 128 核）

日期：2026-11-10
依据：`docs/papers/ref/silifuzz.pdf`（K. Serebryany, M. Lifantsev, K. Shtoyk,
D. Kwan, P. Hochschild. *SiliFuzz: Fuzzing CPUs by proxy*, 2021）
仓库约束：`AGENTS.md` 要求目标架构为 ARM；运行平台 ARM 或 X86。当前主机为
aarch64 openEuler 24.03 SP4 / Kunpeng 920，128 核、30 GiB 内存、`/home` 剩余
约 108 GiB，无 x86 机器，`sdc-0102` SSH 不可达。

## 1. 目标与边界

在 `silifuzz/` 下按论文第 2 节复现以下组件，并全部用真实命令验证：

1. **Snapshot**（§2.2）：寄存器初态、带权限的内存映射与数据、期望的结束状态
   （可多组）、产生方式元数据。
2. **Player**（§2.3）：driver + harness 双进程；命令序列
   MapMemory / WriteMemory / ProtectMemory / ExecuteSnapshot / ChecksumMemory；
   绑定核心；比对结束状态；不匹配即报告潜在缺陷。
3. **Snapshot 生成**（§2.4）：三种代理——反汇编器（论文用 XED，本实现用
   Capstone ARM64）、随机合法指令生成器（论文用 syzkaller ifuzz x86，本实现用
   syzkaller ifuzz 的 ARM64 后端）、CPU 模拟器（论文用 Unicorn x86，本实现用
   Unicorn ARM64）；libFuzzer 覆盖率引导。
4. **修复与端态录制**（§2.4.4）：缺页补映射、去系统调用与不确定性、跨核端态
   一致性、3 秒 CPU 时间上限；非法指令保留。
5. **规模化执行**（§2.5）：checker 以 50 个 snapshot 为一批、生成 1000 次执行
   的随机列表、多队列分发、每核一个 player；机器级 4 核 / 2 分钟窗口并轮转。
6. **反馈闭环**（§2.6）：结果库、隔离/复测流程、命中样本无条件入语料。

论文的 ISA 专属内容（x86-64 的 XED、SDE、`0xCC` 陷阱、附录中的 x87 缺陷）按
`AGENTS.md` 改为 ARM64 等价物；`BRK #0` 作为 snapshot 结束陷阱。这是规格映射，
不是逐字节复刻 x86 编码。

**非目标**（会在文档中明示）：不声称找到真实硬件缺陷；不声称拥有 Google 生产
机群；不声称 500,000 条语料全部重新生成到同一覆盖度；不复刻附录 A–D 的 x86
缺陷本身。

## 2. 环境事实（已核实）

```text
uname -a : Linux ... 6.6.0-159.4.3.154.oe2403sp4.aarch64
lscpu    : Kunpeng-920, 128 CPUs, 1 thread/core, 4 NUMA nodes (32 cores each)
python3  : 3.11.6, unicorn 2.1.4, capstone 5.0.7 (wheel 内含 C 库与头文件)
go       : go1.24.2 linux/arm64
clang    : 17.0.6, libFuzzer 可用（-fsanitize=fuzzer 实测）
git      : 可访问 GitHub（https，直连需绕过本机 gitclone 镜像重写）
```

已用原型验证的关键机制（`silifuzz/.scratch/proto2.cc`）：在 SIGTRAP handler
中改写内核信号帧的 `ucontext`（x0–x30 / sp / pc / pstate / fpsimd_context），
从 handler 正常返回，由内核 `rt_sigreturn` 一次性恢复全部状态并跳入 snapshot；
snapshot 以 `BRK #0` 结束时再次进入 handler 并 `siglongjmp` 回 harness。
实测 `mem0=0x3ff8000000000000 mem1=0x4004000000000000`（q0/q1 精确恢复），
寄存器与故障地址均正确。glibc 自带 getcontext/setcontext 只恢复调用者保存的
子集（反汇编确认），故不采用。

构建产物放在 `silifuzz/third_party/`（gitignore），不提交二进制。

## 3. 设计

### 3.1 Snapshot 二进制格式（自描述、跨 C++/Python）

固定小端，标识 `SILIFZ01`，版本 1。字段顺序：

```text
header: magic[8], version u32, arch u32(1=AArch64), flags u32, id u64,
        meta_len u32, meta_json[meta_len]
initial regs: x[31] u64, sp u64, pc u64, pstate u64, fpcr u64, fpsr u64,
              v[32][16] bytes
memory: count u32; each { start u64, size u64, perms u32,
                         data_kind u32 (0=zero, 1=inline), data_len u32,
                         data[data_len] }
end_states: count u16; each { signal u32, sig_addr u64,
                              regs (同上), checksum_count u32,
                              {start u64, size u64, fnv1a64 u64}[] }
```

`perms` 位：1=R, 2=W, 4=X。结束状态的 `regs` 与初态同布局。
元数据 JSON 至少含 `source`、`seed`、`created_unix`、`proxy`、`notes`。
校验和对每个映射区域逐 4 KiB 页计算 FNV-1a 64。

固定布局：代码 `0x10000000`、数据从 `0x20000000` 起（最多 4 页）、栈
`0x30000000`（sp = +0x800）。snapshot 一次性执行，地址可重复使用。

### 3.2 Player

- `sf_harness`：子进程，命令循环；用 §2 的信号帧机制执行 snapshot；捕获
  信号号、`si_addr`、完整寄存器、逐页校验和；用 `sigaltstack` 防止
  snapshot 栈不可用；对 SIGTRAP/SIGSEGV/SIGILL/SIGFPE/SIGBUS 建 handler。
- `sf_player`：driver，`fork/exec` harness 并通过 `socketpair` 发送二进制命令；
  `sched_setaffinity` 绑定核心；超时（默认 3 s）杀掉并重启 harness。
- 命令：RESET / MAP / WRITE / PROTECT / EXEC / CHECKSUM / QUIT。
- 结束状态比较：signal、sig_addr、x0–x30、sp、pc、pstate、fpcr、fpsr、
  v0–v31、所有映射页校验和。
- snapshot 代码执行前静态保证无系统调用（生成/修复阶段拒绝 SVC/HVC/SMC），
  数据页 NX、代码页 RX，禁止自修改。

### 3.3 生成代理

| 论文 | 本实现 | 目标 |
| --- | --- | --- |
| XED + libFuzzer | Capstone ARM64（源码 + `-fsanitize=fuzzer-no-link` 插桩） | `proxies/capstone_fuzz.cc` |
| ifuzz（x86） | syzkaller `pkg/ifuzz/arm64`（固定版本、只 vendor 需要的包） | `tools/ifuzzgen` |
| Unicorn（x86） | Unicorn 2.1.4 ARM64（源码插桩） | `proxies/unicorn_fuzz.cc` |

每个 libFuzzer 目标以 4 KiB 固定地址映射输入并执行（Unicorn）或解码
（Capstone）；语料按文件哈希去重。

### 3.4 修复流水线

对每个候选指令序列：

1. 长度 4..1024 字节、4 字节对齐；扫描并拒绝 SVC/HVC/SMC（系统调用）。
2. 构造初态：代码页 + `BRK #0`，数据页（伪随机内容，种子由内容哈希决定），
   栈页；x0–x30 一半指向数据窗口、一半伪随机；v0–v31 伪随机；pstate=0。
3. 逐次执行；若 SIGSEGV/SIGBUS 且地址落在允许窗口、映射数 < 4，则补零页重试。
4. 确定性：同核重复 3 次，端态必须一致。
5. 跨核：在 4 个参考核（0/32/64/96，覆盖 4 个 NUMA 节点）各执行 1 次；
   端态不一致则归为 multi-state 丢弃（论文 §2.4.4 当前策略）。
6. 记录端态与元数据；按内容哈希去重。
7. 单条 CPU 时间上限 3 s；超时/异常信号（SIGSYS 等）拒绝。

被拒绝样本写入 `work/rejected/` 并记录原因，统计拒绝率。

### 3.5 Checker

- `sf_checker`：读取语料；每批随机 50 条，按均匀分布生成 1000 次执行；
  多个批并发（隐藏 I/O）；执行列表经多队列分发给每个核心一个 player。
- 两种模式：`sampled`（严格按论文 50/1000）与 `sweep`（每条语料在每核执行
  一次，用于全量验收）。
- 2 分钟时间预算、核心列表、结果 JSONL；统计 IO 字节/执行次数以量化批处理
  摊薄效果。
- 命中（端态不匹配）时保存 snapshot、核心、时间、实际/期望端态，并复制到
  `corpus/found/`（论文 §2.6 无条件保留）。

### 3.6 Fleet 与反馈

- `sf_fleet`：4 核窗口、2 分钟预算、窗口轮转（`--window-seconds` 可缩短用于
  功能验证）；SQLite `results.db` 记录 machine/core/snapshot/outcome/mismatch。
- `sf_quarantine`：读取结果库，对"同一核多日复现"的机器/核标记隔离；重跑命中
  语料；维护已知问题清单。单机条件下只能用合成缺陷注入验证检测路径。
- 合成缺陷：harness `--inject-fault` 在指定条件下翻转结果（明确标注 synthetic），
  用于验证 checker→quarantine→复测→入语料闭环，不冒充真实硬件缺陷。

## 4. 任务分解（一任务一 commit）

- [x] **T1 规格、计划与脚手架**：本文件、`silifuzz/README.md`、`.gitignore`、
      `Makefile`、目录骨架。验证：`make -n`、`git diff --check`。
- [x] **T2 Snapshot 格式库**：C++ `snapshot.{hh,cc}` + Python `sfsnapshot.py`，
      编解码/校验和/端态比较；单测覆盖往返、跨语言一致性、损坏检测。
      验证：`make test-snapshot`。
- [x] **T3 Player**：harness/driver/CLI；已知 ARM64 片段（ALU、FP、内存、
      BRK、非法指令、缺页）端态测试；双进程隔离；3 s 超时。
      验证：`make test-player`（输出真实端态）。
- [x] **T4 生成代理**：依赖构建脚本 + 三个代理 + 语料导出；实际 fuzz 运行。
      验证：各代理覆盖增长、语料数量、`-runs` 冒烟。
- [x] **T5 修复流水线**：实现 §3.4；单测 + 小规模端到端（生成→修复→玩家）。
      验证：`make test-fix`，真实拒绝率与语料样本。
- [x] **T6 Checker**：§3.5；50/1000 批处理、多核、时间预算、JSONL、命中保存。
      验证：`make test-checker`（多核真实执行 + 批处理统计）。
- [x] **T7 Fleet/隔离/合成缺陷**：§3.6；SQLite、窗口轮转、隔离复测；
      合成缺陷被检出并进入 found。
      验证：`make test-fleet`（真实 2 分钟窗口 + 合成故障检出）。
- [x] **T8 规模化实测**：生成尽可能大的语料（目标 ≥50,000，尽量逼近论文
      500,000 的量级）、跨核修复、128 核 sweep/sampled 实测；记录吞吐、
      拒绝率、IO 摊薄、缺陷检测延迟；产物在 `silifuzz/evidence/`。
      验证：真实运行日志与汇总 JSON。
- [x] **T9 文档与收尾**：README（使用/复现命令）、`docs/paper-mapping.md`、
      `docs/measurements.md`、`docs/limitations.md`；与原文逐条对照；
      全量回归。验证：clean build + 全部测试 + 文档命令逐条执行。

## 5. 验收标准

1. `make -C silifuzz clean all` 在空构建目录成功，无新增 warning/error。
2. 单元与端到端测试全部真实通过，退出码 0。
3. 至少一次真实的 128 核 checker 运行、一次 4 核 / 2 分钟 fleet 窗口。
4. 合成缺陷被 checker 检出、隔离、复测，并保存命中 snapshot。
5. 所有数字来自实际命令输出，写入 `docs/measurements.md`；无法达到原文的
   项目逐条列出原因。

## 6. 已知限制（将写入文档）

- 单机 1 台、128 核；无 Google 生产机群与跨平台（多微架构）参考端态。
- ARM64 only；x86-64 的 XED/SDE/0xCC 语义未复刻。
- 代理与原论文不同（Capstone / Unicorn ARM64 / ifuzz ARM64），覆盖度不可直接
  与 XED/Unicorn x86 对比。
- 语料规模、生成时长与 500,000 条的目标可能有差距，以实测为准。
- 真实硬件无已知缺陷；检测闭环只由合成注入验证。
- 论文的 2 分钟/4 核是生产调度参数，单机复现只验证机制与吞吐。

## 7. 执行结果（2026-11-10）

- 语料：95,402 条（ifuzz 92,652 / Capstone 1,600 / Unicorn 1,150），212,647,273 B。
- 修复：ifuzz 97,952 候选 → 92,652 收录（syscall 拒绝 3,928、timeout 1,372），
  557,311 次执行、132.4 s；Capstone/Unicorn 合计 2,752 候选、2,750 收录。
- 128 核全量 sweep：12,211,456 次执行（95,402 × 128），45.473 s，
  268,540 次/秒，0 不匹配。
- 4 核 / 2 分钟窗口 × 4：20,583,479 次执行，0 不匹配（42.0–43.3 千次/秒）。
- 合成缺陷（`flip:0:0:1:0`）4 核窗口：124,047/124,047 次不匹配；
  小语料 quarantine 580/580 组确认。
- `make test`：55 项 PASS、0 FAIL；clean build 无新增告警。
- 证据：`silifuzz/evidence/`、`silifuzz/docs/measurements.md`。
- 未发现真实硬件缺陷；限制见 `silifuzz/docs/limitations.md`。
