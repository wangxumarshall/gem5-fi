# SiliFuzz 复现 vs 当前 sdcfuzz：能力对比（2026-11-14）

本文把 `silifuzz/` 的论文复现与 `sdcfuzz/` 主线放在同一张能力表里，并给出
可引用的数字。两者共享“生成 → 执行 → 反馈”的宏观思路，但**测试单元、判定
oracle、工具链不同**，数字不能直接相加，也不能互相替代。

- `silifuzz/`：SiliFuzz 论文第 2 节的 ARM64 规格复现 + 真机端态 checker。
  本轮复核见 `silifuzz/docs/reproduction-2026-11-14.md`。
- `sdcfuzz/`：面向 ARM64 SDC 的生成—注入—验证闭环，包含 gem5-CHAOS、
  ACE/IBR/SAD、AutoµSens、NSGA-II、19 条结构模板与 D13。
  Phase 1 收尾见 `docs/sdcfuzz/phase1-verification.md`。

## 1. 一张表看差异

| 维度 | `silifuzz/`（论文复现） | `sdcfuzz/`（当前主线） |
|---|---|---|
| 定位 | 论文 §2 的独立规格复现、可复现基线与真机端态 checker | 微架构感知的 SDC 用例生成、故障注入与跨层验证 |
| ISA | ARM64（论文 x86-64；按仓库约束映射） | ARM64（Kunpeng 920 / gem5 O3） |
| 测试单元 | 二进制 Snapshot：寄存器 + 页映射 + 期望端态 | C 模板/指令序列（gem5 work-item）+ 上游 snapshot 语料 |
| 生成方式 | libFuzzer 模糊 Capstone 解码器 / Unicorn 模拟器；ifuzz 随机合法序列 | 19 条手工结构模板、D13 操作数启发式、AutoµSens 结构靶向、NSGA-II |
| 变异策略 | 字节级变异（代理 fuzz）+ 随机初态；无操作数/结构语义 | directed-on-random（D13）、指令/操作数选择、结构加权与多目标 |
| 覆盖反馈 | 代理软件的代码覆盖（Capstone/Unicorn 插桩） | 微架构覆盖：RF/L1 ACE、FU IBR、SAD；9 类结构 |
| 判定 oracle | 跨核/跨机端态逐位比较（signal/addr/寄存器/页校验和） | gem5-CHAOS 注入后的 golden vs faulty 差分（SDC 率）+ 真机 SDC/噪声分类 |
| 故障模型 | **没有**（只检测已存在的缺陷） | 19 个 CHAOS 注入器、bit-flip、byte_lane_skew 等 |
| 仿真依赖 | 无（Capstone/Unicorn 仅作生成代理） | 强依赖 `CHAOS/gem5`（ACE/IBR/SAD、注入器、m5out） |
| 真机执行 | driver+harness player，逐核绑核；128 核 checker | 上游 nolibc/seccomp Runner + Orchestrator（4 板 446 核为外部证据） |
| 规模 | 505,020 条语料；64,642,560 次 sweep；4 核窗口 5.17M 次/2 分钟 | 19 模板 × 9 结构；AutoµSens 16 探针/8 可靶向结构；D13 4×100 |
| 反馈闭环 | 结果库 → quarantine 复测 → 命中样本入 `found/` | Vault 持久库 + 血缘（Phase 3）、D1–D13 迭代、RL/功耗（规划中） |
| 失败语义 | end-state mismatch = 该核潜在缺陷；超时/错误单独计 | `RunSnapOutcome` 区分真正 SDC 与噪声；masked/SDC/异常分类 |
| 目标读者 | 核对论文实现、要独立基线的工程/评审 | 推进生成器、指标与故障注入研究，冲刺竞赛/论文 |

## 2. 可引用的量化数字

### 2.1 SiliFuzz 复现（本轮真实命令）

| 指标 | 值 | 证据 |
|---|---:|---|
| 基线语料 | 95,402 条 / 202.8 MiB（212.6 MB） | `silifuzz/evidence/corpus-stats-20261114.json` |
| 规模复核语料 | **505,020 条 / 1.05 GiB（1.13 GB）**（约 50 万，全部 ifuzz） | `silifuzz/evidence/corpus-stats-500k.json` |
| 新生成 → 修复 | 1,996 候选 → 1,896 收录（12.2 s） | `silifuzz/evidence/verify-20261114-generate.log` |
| 95k 全量 sweep | 12,211,456 次执行，0 不匹配 | `silifuzz/evidence/verify-20261114-scale.log` |
| 505k 全量 sweep | **64,642,560 次执行，0 不匹配** | `silifuzz/evidence/sweep-500k/summary.json` |
| sweep 吞吐 | 188,575 次/秒（95k，含并发重链接）；274,515.8 次/秒（505k）；268,540 次/秒（11-10 基线） | 同上 + `docs/measurements.md` |
| 95k 4 核 / 2 分钟窗口 | 5,160,039 次，42,977.7 次/秒，0 不匹配 | 同上 |
| 505k 4 核 / 2 分钟窗口 | **5,168,126 次，43,022.0 次/秒，0 不匹配** | `silifuzz/evidence/verify-20261114-500k.log` |
| 测试 | 55 项 PASS，`make test` 退出 0 | `silifuzz/evidence/verify-20261114-build-test.log` |
| 合成注入 | 211,837/211,837 不匹配（100%，synthetic） | 同上 |

### 2.2 sdcfuzz 当前（Phase 1 收尾）

| 指标 | 值 | 证据 |
|---|---:|---|
| 结构模板 | 19 条，覆盖 7 类 target | `sdcfuzz/templates.py`、`m5out/phase1-verify-20261114/v2/coverage2/coverage_matrix.json` |
| 可观测结构 | 9 类（rf/vec/l1i/l1d/alu/mult/div/fpadd/fpmul） | `tools/autousens.py` |
| 可逐指令靶向结构 | 8 类（`l1i` 为 cache-line 粒度，显式拒绝） | `structure_map.json` 的 `targetability` |
| 指令探针 | 16 条 + baseline | `workloads/directed/structural_probe_workload.c` |
| 模板覆盖 | 19/19 模板全部必需指标 > 0；9/9 结构真实激活 | `coverage_summary.md` |
| AutoµSens 靶向 | 8/8 可靶向结构逐一验证净激活 > 0 | `m5out/phase1-verify-20261114/v2/autousens.log` |
| NSGA-II | Pareto 非空（size=8–14），knee 在 gem5 中验证 | 同上 |
| ACE/IBR/SAD | RF ACE（整数 + 向量）、L1 ACE、5 类 FU IBR、8 类 SAD 资源 | `CHAOS/gem5/src/cpu/o3/`、`scripts/test-*.sh` |
| gem5 注入器 | 19 个 CHAOS 注入器 | `CHAOS/gem5/src/cpu/o3/CHAOS*` |
| D13 检出提升 | bit-flip 2.833×、structural 12.800×（本机 4×100 复现记录） | `docs/sdcfuzz/d13-repro/summary.json` |
| Phase 1 闸门 | 9 步全通过 | `m5out/phase1-gate/phase1_gate.json` |

## 3. 三个“看起来一样、实际不同”的点

### 3.1 Snapshot 不是同一种东西

- `silifuzz` 的 snapshot 是自定义二进制格式（`SILIFZ01`）：固定地址布局、
  期望端态内嵌、每页 FNV 校验和、无重定位、无沙箱；player 用信号帧恢复全部
  寄存器。
- sdcfuzz 的工程基座是上游 SiliFuzz ARM64 移植：protobuf Snapshot +
  SnapRelocator + SnapCorpus + nolibc/seccomp Runner + Orchestrator；本仓库
  的 19 条模板走 `sdcfuzz/generator.py` 生成 C guest，在 gem5 work-item
  窗口内运行。
- 两者格式不互通：`silifuzz` 的 `.sfs` 不能被上游 Runner 直接播放，上游
  snapshot 也不能直接进 `silifuzz` 的 checker。

### 3.2 “差分”不是同一种差分

- `silifuzz` 是**无故障模型的跨核差分**：同一 snapshot 在 128 个真实核上
  执行，端态必须与参考核一致；不一致即“该核可疑”。它回答“这颗 CPU 行为
  是否偏离参考”。
- sdcfuzz 是**注入故障后的 golden/faulty 差分**：在 gem5 里对寄存器或
  load/store 注入 bit-flip / 字节失序，比较注入与未注入结果，统计 SDC 率；
  真机上再用 `RunSnapOutcome` 把 SDC 与噪声分开。它回答“这个用例有多容易
  把故障传播成静默错误”。
- 因此：`silifuzz` 的 0 mismatch **不能**当作 sdcfuzz 的“SDC 检出率”，
  反过来 sdcfuzz 的注入 SDC 率也不能证明 `silifuzz` 的真机检查有效。

### 3.3 “覆盖引导”不是同一种覆盖

- `silifuzz` 的覆盖是**软件代理的代码覆盖**：Capstone 解码器路径、Unicorn
  模拟器 C 代码路径；不提供任何微架构结构信息。
- sdcfuzz 的覆盖是**微架构指标**：RF/L1 ACE、FU IBR、SAD，配合
  `tools/autousens.py` 的指令→结构映射与 `tools/nsga2.py` 的多目标选择。
- 两者都叫“覆盖率”，但一个指导“生成更多解码/模拟路径”，另一个指导
  “激活更多硬件结构”。不能把 95,402 条语料的代理覆盖与 9 类结构覆盖
  放在同一张表里比大小。

## 4. 能力互补清单

| sdcfuzz 有、`silifuzz/` 没有 | `silifuzz/` 有、sdcfuzz 没有 |
|---|---|
| RF/L1 ACE、FU IBR、SAD 三类微架构指标 | 独立的跨核端态 checker（signal/addr/寄存器/页校验和） |
| 19 个 CHAOS 注入器与 golden/faulty 差分 | 12,211,456 次 128 核全量 sweep 的工程验证 |
| AutoµSens 结构映射与逆向靶向 | 50/1000 批处理与 17.4 B/次 I/O 摊薄 |
| NSGA-II 多目标序列集 | 4 核/2 分钟机群窗口与 quarantine 复测闭环 |
| D13 操作数启发式（2.833×/12.800×） | 与 sdcfuzz 工程栈完全独立的实现，可作交叉核对 |

## 5. 互补关系与使用建议

- 需要**核对论文复现是否可信**、或需要一个**独立于 sdcfuzz 工程栈**的真机
  端态基线：用 `silifuzz/`。它的语料、player、checker、机群窗口和
  12,211,456 次 sweep 都可复现。
- 需要**衡量/提升 SDC 检出能力**、做故障注入、微架构覆盖或结构靶向：用
  sdcfuzz 主线（gem5-CHAOS + AutoµSens/NSGA-II）。
- 若要把两者放在同一篇报告里：
  - 并列引用为“论文基线”与“本仓库研究系统”；
  - 不要用 `silifuzz` 的 0 mismatch 声称“没有 SDC”，也不要拿 sdcfuzz 的
    注入 SDC 率与 `silifuzz` 的端态 mismatch 直接比较；
  - 两者共享 ARM64 目标与“生成→执行→反馈”的宏观思路，但测试单元、
    oracle、工具链均不同。
- 真正公平的“SDC 检出能力”对比需要**同一批已知坏机器 + 同一份语料 +
  同一执行窗口**；本机两者都缺，因此本文只做能力矩阵，不做胜负结论。
  后续的等长流随机注入对照见
  [`silifuzz-vs-sdcfuzz-fi-2026-11-14.md`](silifuzz-vs-sdcfuzz-fi-2026-11-14.md)：
  在 FP 数据通路、CHAOSFPU 源读注入、3600 指令等长流下，sdcfuzz 178/240
  (74.17%) vs SiliFuzz 0/240；该结果只覆盖 FP 通路，不改变本文关于整数/
  端态 checker 不可直接比较的结论。

## 6. 事实边界

- `silifuzz/` 的数字全部来自本轮真实命令，证据在
  `silifuzz/evidence/verify-20261114-*.log`；505k 规模复核的语料构成是
  ifuzz-only，不能据此声称复现了论文的 40/20/40 代理混合。
- sdcfuzz 的 4 板 446 核部署、p2 草稿属于外部证据，本机未复验；D13 的
  2.833×/12.800× 来自本机 `docs/sdcfuzz/d13-repro/summary.json` 的 4×100
  记录，不是本轮重新跑的 400 次实验。
- Phase 1 的 9 步闸门、AutoµSens 8 结构靶向、19 模板 9/9 结构覆盖是本轮
  真实运行；具体输出见 `docs/sdcfuzz/phase1-verification.md`。
- 两者都受同一台 128 核 Kunpeng 920 限制；本机没有 sdcfuzz 的 4 板环境，
  也没有真实缺陷芯片。
