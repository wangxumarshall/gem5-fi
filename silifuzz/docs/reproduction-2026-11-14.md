# SiliFuzz 原文复现：2026-11-14 复核记录

对象：`docs/papers/ref/silifuzz.pdf`（K. Serebryany et al., *SiliFuzz:
Fuzzing CPUs by proxy*, arXiv 2110.11519, 2021）第 2 节规格与第 3 节可复现
评估口径。实现目录：`silifuzz/`。主机：`sdc-0103`（Kunpeng 920，128 核，
4 NUMA 节点，无 SMT，openEuler 24.03 SP4）。

本文是 2026-11-10 首次复现之后的**独立复核**：重新构建、重跑 55 项测试、
重新统计语料、重跑 128 核 sweep、4 核/2 分钟窗口与合成注入。所有数字来自
本轮命令，日志在 `silifuzz/evidence/verify-20261114-*.log`。

## 1. 本轮结论

- **第 2 节（Snapshot / Player / 生成 / Checker / 机群窗口 / 反馈闭环）的
  机制全部复现**：55 项测试通过；新生成 1,996 条候选、修复收录 1,896 条；
  128 核 50/1000 采样 603,201 次执行 0 不匹配；128 核全量 sweep 12,211,456
  次执行 0 不匹配；4 核/2 分钟窗口 5,160,039 次执行 0 不匹配。
- **第 3 节的机群统计不可在本机复现**：论文的约 500,000 条语料、真实缺陷
  检出、45% 独有发现、70% 同物理核双逻辑核归属，都需要 Google 生产机群与
  已知坏机器；本机只有 1 台机器、无 SMT、无缺陷芯片。
- **没有发现真实硬件缺陷**。所有“检出”都来自 `--inject` 合成注入，只验证
  checker → 隔离 → 复测闭环，不能表述为硬件缺陷。

## 2. 构建与测试

```bash
cd silifuzz
make -j32
make test
```

第一次是增量构建；随后又做了一次 **clean 重建**，确认不是靠旧对象文件通过：

```bash
make clean && make -j32 && make test
```

结果（`evidence/verify-20261114-build-test.log`、
`evidence/verify-20261114-clean-build.log`）：

| 项 | 增量 | clean 重建 |
|---|---|---|
| 构建 | `BUILD_EXIT=0` | `BUILD_EXIT=0` |
| 测试 | `TEST_EXIT=0`，55 个 `PASS`，5 组 `ALL PASS` | `TEST_EXIT=0`，55 个 `PASS` |
| 覆盖的测试组 | snapshot、player（含超时/信号/恢复）、跨语言、e2e、fleet/quarantine | 同 |

测试不是“只跑一个 smoke”：`test_player` 覆盖 SIGTRAP/SIGSEGV/SIGILL/超时
恢复；`test_crosslang` 验证 Python 与 C++ 的内容哈希、字节级重编码与回放；
`test_e2e` 真实生成 290 条语料并做 4 核采样与合成缺陷；`test_fleet` 验证
窗口轮转与 580 组隔离复测。

## 3. 语料

```bash
python3 tools/corpus_stats.py work/corpus evidence/corpus-stats-20261114.json
```

| 项 | 本轮 | 2026-11-10 |
|---|---:|---:|
| snapshot 总数 | 95,402 | 95,402 |
| 磁盘占用 | 212,647,273 B | 同 |
| 平均每条 | 2,229 B | 同 |
| ifuzz / Capstone / Unicorn | 92,652 / 1,600 / 1,150 | 同 |
| 代码长度 p50 / p90 / max | 68 / 120 / 132 B | 同 |
| 端态 SIGILL / SIGSEGV / SIGTRAP / SIGBUS | 51,461 / 31,070 / 8,641 / 4,230 | 同 |

语料统计与 11-10 基线逐项一致。本轮另外跑了一次小规模生成-修复-回放
（不是 180 秒代理 fuzz 的全量重跑）：

```bash
./bin/ifuzzgen -n 2000 -seed 20261114 -min-insns 1 -max-insns 32 \
  -out work/cand/verify-20261114
./bin/sf_fix --in work/cand/verify-20261114 --out work/corpus-verify-20261114 \
  --source ifuzz --jobs 8 --spread --ref-cores 0,32,64,96 \
  --stats evidence/ifuzz-fix-20261114.json
./bin/sf_player --corpus work/corpus-verify-20261114 --core 0 --limit 1000
```

| 项 | 本轮 |
|---|---:|
| ifuzz 生成 | 2,000 请求，1,996 写入（1,996 unique） |
| sf_fix | 1,996 候选，**1,896 收录**，syscall 72、timeout 28 |
| 修复执行 | 11,405 次，12.217 s |
| player 回放 | 1,000 条，0 失败、0 超时 |

这说明第 2.4 节的“生成 → 补映射/去不确定性/跨核端态录制 → 回放”链路在
本轮仍然可执行；全量 95,402 条语料没有重新生成。

## 4. 规模执行

### 4.1 单核回放

```bash
/usr/bin/time -f 'real=%e' ./bin/sf_player --corpus work/corpus/ifuzz \
  --core 0 --limit 2000
```

结果：2,000 条快照，0 失败、0 超时，`real=0.37 s`，约 **5,405 条/秒**。
与 11-10 的 5,128 条/秒同一量级；论文没有给单核吞吐，这个数字只作为本机基线。

### 4.2 50/1000 采样（论文 §2.5.1）

```bash
./bin/sf_checker --corpus work/corpus --cores 0-127 --seconds 6 \
  --mode sampled --out evidence/sampled-20261114
```

| 指标 | 本轮 |
|---|---:|
| 执行次数 | **603,201** |
| 墙钟 | 6.042 s |
| 吞吐 | **99,834.7 次/秒** |
| 不匹配 / 超时 / 错误 | **0 / 0 / 0** |
| 批大小 / 每批执行 | **50 / 1000** |
| 批数 / 快照加载 | 604 / 30,200 |
| 语料读取 | 67,318,044 B |
| I/O 摊薄 | **111.6 B/次**（约 20×；单条快照 2,229 B） |

这直接复现了论文“50 条随机快照一批、每批生成 1000 次执行、把读取成本降低
约 20 倍”的口径：`2,229 / 111.6 = 19.97×`。采样模式不保证每条语料在 6 秒内
都被执行；全量覆盖由 4.3 的 sweep 负责。

### 4.3 128 核全量 sweep

```bash
./bin/sf_checker --corpus work/corpus --cores 0-127 --seconds 300 \
  --mode sweep --out evidence/sweep-20261114
```

| 指标 | 本轮 | 2026-11-10 干净基线 |
|---|---:|---:|
| 执行次数 | **12,211,456**（95,402 × 128） | 同 |
| 墙钟 | 64.757 s | 45.473 s |
| 吞吐 | 188,575 次/秒 | 268,540 次/秒 |
| 不匹配 / 超时 / 错误 | **0 / 0 / 0** | 0 / 0 / 0 |
| 语料读取 | 95,402 次、212,647,273 B | 同 |
| I/O 摊薄 | 17.4 B/次 | 同 |

本轮 sweep 与一次 gem5 重链接并行，吞吐低于 11-10 的干净基线；**执行次数与
0 不匹配是硬结论，吞吐取干净基线 268,540 次/秒作为上限、本轮 188,575 次/秒
作为保守下界**。两次都精确等于 `95,402 × 128`，说明 sweep 没有漏核或重复。

### 4.4 4 核 / 2 分钟窗口（论文 §2.5.2）

```bash
python3 tools/fleet.py --corpus work/corpus --db work/fleet/results-20261114.db \
  --out-root work/fleet/runs-20261114 --cores 0-127 --window-cores 4 \
  --window-seconds 120 --windows 1
```

| 窗口 | 核 | 执行次数 | 速率 | 不匹配 |
|---|---|---|---:|---:|
| 1 | 0-3 | **5,160,039** | **42,977.7/s** | **0** |

与 11-10 的 4 个窗口（5,191,935 / 5,143,335 / 5,199,733 / 5,048,476，
42,044–43,308/s）一致。论文的“4 核、最多 2 分钟、窗口最终覆盖所有核”在
本机按机制复现；没有生产作业调度器，也没有跨机器结果汇总。

### 4.5 合成缺陷检出

```bash
./bin/sf_checker --corpus work/corpus --cores 4-7 --seconds 5 \
  --inject flip:0:0:1:0 --out work/inject-20261114
```

结果：**211,837 次执行、211,837 次不匹配（100%）**，41,830 次/秒。注入直接
改写 harness 返回的 x0 bit0，所以 100% 检出是预期行为；它验证的是
checker → `mismatches.jsonl` → quarantine 的链路，不是故障模型，也不是硬件
缺陷。退出码 3 是“发现不匹配”的约定，不是脚本错误。

## 5. 论文条款逐条对照

| 论文条款 | 本机复现 | 证据 | 判定 |
|---|---|---|---|
| §2.2 Snapshot：寄存器初态、页映射、端态、异常地址 | 完整实现 `RegState`/`MemoryMapping`/`EndState` | `include/silifuzz/snapshot.hh`、`tests/test_snapshot` | 复现 |
| §2.3 Player：driver + harness 双进程、绑核、3 秒限制 | 完整实现，信号帧恢复全部寄存器 | `src/player.cc`、`src/harness.cc`、`tests/test_player` | 复现 |
| §2.4 代理 fuzz：XED/ifuzz/Unicorn | ARM64 映射为 Capstone / syzkaller ifuzz / Unicorn | `proxies/`、`evidence/*-fuzz.log` | 复现（代理不同） |
| §2.4.4 补映射、去不确定性、跨核端态录制 | 补零页、3 次同核 + 4 NUMA 节点一致才收录 | `src/sf_fix.cc`、`evidence/ifuzz-fix.json` | 复现 |
| §2.5.1 50/1000 批处理、多队列分发 | 50 条/批、1000 次/批，I/O 摊薄约 20× | `src/sf_checker.cc`；采样 603,201 次、111.6 B/次（19.97×）；sweep 17.4 B/次 | 复现 |
| §2.5.2 4 核 / 2 分钟 / 覆盖所有核 | 4 核 × 120 s 窗口，轮转机制 | `tools/fleet.py`、`evidence/verify-20261114-scale.log` | 机制复现 |
| §2.6 隔离、复测、命中样本保留 | 多日复现改为多次独立复测；命中入 `found/` | `tools/quarantine.py`、`tests/test_fleet.sh`（580 组确认） | 机制复现 |
| §3 语料约 500,000 | 95,402 | `evidence/corpus-stats-20261114.json` | 未达到（19%） |
| §3 40% 仅 Unicorn/XED、20% 仅 ifuzz、40% 两者 | 未测 | 需要已知缺陷机器做归因 | 不可复现 |
| §3 45% findings 独有 | 无真实 findings | 无生产机群 | 不适用 |
| §3 70% 缺陷影响同一物理核的双逻辑核 | 无 SMT（`thread_siblings_list=0`） | `lscpu` | 不适用 |
| 附录 A–D：F2XM1 / illegal-instruction overshoot / FCOS / x87 RDP | 论文为 x86-64；本实现为 ARM64 | `docs/limitations.md` §2 | 不适用 |

## 6. 与论文的真实差距

1. **ISA**：论文 x86-64，本实现 ARM64；XED→Capstone、SDE→无、`0xCC`→`BRK #0`，
   附录 A–D 的 x86 缺陷没有复现。
2. **规模**：1 台 128 核机器 vs Google 生产机群；没有第二台机器、没有已知坏
   机器池、没有多日复测。
3. **语料**：95,402 vs 约 500,000；代理 fuzz 只跑了数分钟，没有做语料蒸馏与
   跨代理交叉授粉的系统评估。
4. **初态来源**：本实现的初态由内容哈希确定性生成，不是从真实进程捕获；
   数据页零填充。这会影响“测试真实程序状态”的覆盖行为。
5. **缺陷检出**：0 个真实缺陷；合成注入只验证管线。
6. **性能口径**：论文没有给吞吐数字，本机 188k–269k 次/秒（sweep）、
   43k 次/秒（4 核窗口）只能作为本机基线，不能与论文机群对比。

### 6.1 附录 A–D 为什么不能在本实现复现

论文附录的四组缺陷都是 x86-64/x87 语义，ARM64 没有对应指令或寄存器：

| 附录 | 论文缺陷 | 本实现 |
|---|---|---|
| A | `F2XM1` 结果错误 | ARM64 无 x87，Capstone/Unicorn ARM64 不生成该指令 |
| B | 非法指令的 overshoot | ARM64 保留 `SIGILL` 端态，但没有 x86 的指令长度/overshoot 语义 |
| C | `FCOS` 计算错误 | 同上，无 x87 三角函数 |
| D | x87 数据指针（RDP）未更新 | ARM64 无 x87 RDP |

因此本实现只能复现“非法指令是合法端态”“信号地址/寄存器逐位比较”这些
架构无关的机制，不能复现附录 A–D 的具体缺陷模式。把它们写成“已复现”会是
不诚实的。

## 7. 复现命令（最短路径）

```bash
cd ~/sdc-mhw/silifuzz
make -j32 && make test
python3 tools/corpus_stats.py work/corpus evidence/corpus-stats-20261114.json
./bin/sf_player --corpus work/corpus/ifuzz --core 0 --limit 2000
./bin/sf_checker --corpus work/corpus --cores 0-127 --seconds 6 \
  --mode sampled --out evidence/sampled-20261114
./bin/sf_checker --corpus work/corpus --cores 0-127 --seconds 300 \
  --mode sweep --out evidence/sweep-20261114
python3 tools/fleet.py --corpus work/corpus --db work/fleet/results-20261114.db \
  --out-root work/fleet/runs-20261114 --cores 0-127 --window-cores 4 \
  --window-seconds 120 --windows 1
./bin/sf_checker --corpus work/corpus --cores 4-7 --seconds 5 \
  --inject flip:0:0:1:0 --out work/inject-20261114
```

## 8. 证据文件

```text
evidence/reproduction-20261114-summary.json  机读汇总（测试/语料/生成/采样/sweep/fleet/注入）
evidence/verify-20261114-build-test.log   增量构建 + 55 项测试
evidence/verify-20261114-clean-build.log  clean 重建 + 55 项测试
evidence/verify-20261114-generate.log     新生成 1,996 → 收录 1,896 → 回放
evidence/ifuzz-fix-20261114.json          本轮修复统计
evidence/verify-20261114-sampled.log      单核 5,405/s + 128 核 50/1000 采样
evidence/sampled-20261114/                采样 summary.json（0 不匹配）
evidence/verify-20261114-scale.log        语料统计 + sweep + fleet + 注入
evidence/corpus-stats-20261114.json       本轮语料统计
evidence/sweep-20261114/summary.json      128 核 sweep 原始输出
work/fleet/results-20261114.db            4 核窗口结果库
work/inject-20261114/                     合成注入结果
```

本文件不改变 `docs/measurements.md` 的 2026-11-10 基线；它是一次独立复核，
两者数字并列时以本文件的“本轮/干净基线”两列为准。
