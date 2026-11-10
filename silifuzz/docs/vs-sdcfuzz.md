# silifuzz 与当前项目（sdcfuzz / gem5-CHAOS）的核心差异

本文说明 `silifuzz/` 与本仓库主线（`sdcfuzz/` + `CHAOS/gem5/` 研究工程，
下称 sdcfuzz）在目标、生成方式、判定口径和工程依赖上的核心差异，避免把两者
的数字、结论或代码混为一谈。

先说结论：

- **silifuzz 是论文规格的独立复现**：只依据
  `docs/papers/ref/silifuzz.pdf` 第 2 节，自己实现 Snapshot、player、
  三种代理、checker 和机群窗口；不依赖上游 sdcfuzz 代码，不使用
  Centipede/Runner/Orchestrator/Vault，也不使用 ACE/IBR/SAD 或
  gem5-CHAOS。
- **sdcfuzz 是本仓库的 ARM64 SDC 研究工程**：以 SiliFuzz 的
  “Snapshot + 真机执行”思路为工程基座，但核心目标是微架构感知的用例生成、
  gem5 故障注入评估和跨层闭环；其基线来自上游 sdcfuzz 的 ARM64 移植
  （Centipede、SnapRelocator、nolibc/seccomp Runner、Orchestrator、
  4 板部署），并叠加本仓库的 ACE/IBR/SAD、AutoµSens、NSGA-II、D13 等。
- 两者**不是同一个实现的两套皮肤**：snapshot 格式不兼容、判定 oracle
  不同、依赖的仿真/注入设施不同，数字不可直接相加或互相替代。

## 1. 一张表看核心差异

| 维度 | `silifuzz/`（本次复现） | sdcfuzz（本仓库主线） |
| --- | --- | --- |
| 定位 | 论文 §2 的独立规格复现、可复现基线与真机端态 checker | 面向竞赛/研究的 ARM64 SDC 生成—注入—验证闭环 |
| 代码来源 | 本目录新写；仅 vendored syzkaller ifuzz ARM64（Apache-2.0） | 上游 sdcfuzz（SiliFuzz ARM64 移植）资产 + 本仓库 gem5-CHAOS/工具 |
| ISA | ARM64（论文为 x86-64；按 `AGENTS.md` 映射） | ARM64（Kunpeng 920 / gem5 TaiShan V110 类模型） |
| 测试单元 | 二进制 Snapshot：寄存器 + 页映射 + 期望端态 | C 源码模板/指令序列（gem5 work-item）+ 上游 snapshot 语料 |
| 生成方式 | libFuzzer 模糊 Capstone 解码器 / Unicorn 模拟器；ifuzz 随机合法序列 | 19 条结构模板、D13 操作数启发式、AutoµSens 结构靶向、NSGA-II |
| 变异策略 | 字节级变异（代理 fuzz）+ 随机初态；无操作数/结构语义 | directed-on-random（D13）、指令/操作数替换、结构加权与多目标 |
| 覆盖反馈 | 代理软件的代码覆盖（Capstone/Unicorn 插桩） | 微架构覆盖：RF/L1 ACE、FU IBR、SAD；指令→结构映射 |
| 判定 oracle | 跨核/跨机端态逐位比较（signal/addr/寄存器/页校验和） | gem5-CHAOS 注入后的 golden vs faulty 差分（SDC 率）+ 真机 SDC/噪声分类 |
| 故障模型 | **没有**（只检测已存在的硬件缺陷/SDC） | 19 个 CHAOS 注入器、bit-flip、byte_lane_skew 等 |
| 仿真依赖 | 无（Capstone/Unicorn 仅作生成代理） | 强依赖 `CHAOS/gem5`（ACE/IBR/SAD、注入器、m5out） |
| 真机执行 | 本机 driver+harness player，逐核绑核；128 核 checker | 上游 nolibc/seccomp Runner + Orchestrator（4 板 446 核为外部证据） |
| 规模口径 | 95,402 条语料；128 核 sweep 12,211,456 次；4 核/2 分钟窗口 | 模板/语料级 campaign；4 板部署见 `docs/roadmap/ROADMAP.md`（外部证据） |
| 反馈闭环 | 结果库 → quarantine 复测 → 命中样本入 `found/` | Vault 持久库 + 血缘、D13 迭代（D1–D13）、RL/功耗（规划中） |
| 失败语义 | end-state mismatch = 该核潜在缺陷；超时/错误单独计 | `RunSnapOutcome` 区分真正 SDC 与噪声；masked/SDC/异常分类 |
| 目标读者 | 想核对论文实现、要独立基线的工程/评审 | 推进生成器、指标与故障注入研究，冲刺竞赛/论文 |

## 2. 三个“看起来一样、实际不同”的点

### 2.1 Snapshot 不是同一种东西

- `silifuzz` 的 snapshot 是**自定义二进制格式**（`SILIFZ01`，见
  `silifuzz/include/silifuzz/snapshot.hh`）：固定地址布局、期望端态内嵌、
  每页 FNV 校验和、无重定位、无沙箱；player 用信号帧恢复全部寄存器。
- sdcfuzz 的工程基座是上游 SiliFuzz ARM64 移植：**protobuf Snapshot +
  SnapRelocator + SnapCorpus + nolibc/seccomp Runner + Orchestrator**；
  本仓库的 19 条模板则走 `sdcfuzz/generator.py` 生成 C guest、在 gem5
  work-item 窗口内运行。
- 两者格式不互通：`silifuzz` 的 `.sfs` 不能被上游 Runner 直接播放，
  上游 snapshot 也不能直接进 `silifuzz` 的 checker。

### 2.2 “差分”不是同一种差分

- `silifuzz` 是**无故障模型的跨核差分**：同一 snapshot 在 128 个真实核上
  执行，端态（signal、故障地址、寄存器、内存校验和）必须与参考核一致；
  不一致即“该核可疑”。它回答的是“这颗 CPU 行为是否偏离参考”。
- sdcfuzz 是**注入故障后的 golden/faulty 差分**：在 gem5 里对寄存器或
  load/store 注入 bit-flip / 字节失序，比较注入与未注入结果，统计 SDC 率；
  真机上再用 `RunSnapOutcome` 把 SDC 与噪声分开。它回答的是“这个用例有多
  容易把故障传播成静默错误”。
- 因此：`silifuzz` 的 0 mismatch **不能**当作 sdcfuzz 的“SDC 检出率”，
  反过来 sdcfuzz 的注入 SDC 率也不能证明 `silifuzz` 的真机检查有效。

### 2.3 “覆盖引导”不是同一种覆盖

- `silifuzz` 的覆盖是**软件代理的代码覆盖**：Capstone 解码器路径、
  Unicorn 模拟器 C 代码路径（论文 §2.4 的 XED/ifuzz/Unicorn 映射）；
  它不提供任何微架构结构信息。
- sdcfuzz 的覆盖是**微架构指标**：`CHAOS/gem5/src/cpu/o3/rf_ace.*`、
  `fu_ibr.*`、`sad.*`（RF/L1 ACE、FU IBR、SAD），配合
  `tools/autousens.py` 的指令→结构映射与 `tools/nsga2.py` 的多目标
  选择；它关心寄存器/缓存/功能单元的激活，而不是代理软件的分支。
- 两者都叫“覆盖率”，但一个指导“生成更多解码/模拟路径”，另一个指导
  “激活更多硬件结构”。

## 3. 当前项目里 silifuzz 不做的部分

以下都是 sdcfuzz 的核心能力，`silifuzz/` 明确不实现，也不应被它的文档
暗示为已实现：

1. **故障注入与 SDC 率**：19 个 CHAOS 注入器、bit-flip/byte_lane_skew、
   masked/SDC 分类；见 `CHAOS/gem5/` 与 `tools/classify.py`。
2. **微架构覆盖指标**：RF/L1 ACE、FU IBR、SAD；见
   `CHAOS/gem5/src/cpu/o3/` 与 `scripts/test-rf-ace.sh` 等。
3. **结构靶向生成**：本仓库本地 19 条模板、D13、AutoµSens、NSGA-II；见
   `sdcfuzz/templates.py`、`tools/autousens.py`、`tools/nsga2.py`。
   （上游 `seeds/*.S` 经 2026-11-10 核查为 20 个、8 个模块，
   见 `docs/sdcfuzz/phase0-baseline.md`。）
4. **生产级 Runner/Orchestrator**：nolibc/seccomp 沙箱、分布式多板扫描、
   Vault 持久库与血缘（上游/外部证据，本仓库未完整落地）。
5. **RL/功耗应力**：`docs/roadmap/ROADMAP.md` 中标为 todo 的后续工作。

反过来，sdcfuzz 目前**没有**使用 `silifuzz/` 的实现、语料或 checker；
两者是并行的两条线，而不是调用关系。

## 4. 互补关系与使用建议

- 需要**核对论文复现是否可信**、或需要一个**独立于 sdcfuzz 工程栈**的
  真机端态基线：用 `silifuzz/`。它的语料、player、checker、机群窗口和
  95,402 条/12,211,456 次实测都可复现（见
  `silifuzz/docs/measurements.md`）。
- 需要**衡量/提升 SDC 检出能力**、做故障注入、微架构覆盖或结构靶向：
  用 sdcfuzz 主线（gem5-CHAOS + AutoµSens/NSGA-II）。
- 若要把两者放在同一篇报告里：
  - 可以并列引用为“论文基线”与“本仓库研究系统”；
  - 不要用 `silifuzz` 的 0 mismatch 声称“没有 SDC”，也不要拿 sdcfuzz 的
    注入 SDC 率与 `silifuzz` 的端态 mismatch 直接比较；
  - 两者共享 ARM64 目标与“生成→执行→反馈”的宏观思路，但测试单元、
    oracle、工具链均不同。

## 5. 事实边界

- `silifuzz/` 的数字（95,402 条语料、12,211,456 次 sweep、20,583,479 次
  4 核窗口、55 项测试）全部来自本会话的真实命令，证据在
  `silifuzz/evidence/`。
- sdcfuzz 的 4 板 446 核部署、D13 的 8.8× 提升、19 个注入器等，来自
  上游/历史证据，记录在 `docs/roadmap/ROADMAP.md` 与
  `docs/sdcfuzz/`；本文件不重新验证，也不把它们算作 `silifuzz` 的成果。
- 两者都受同一台 128 核 Kunpeng 920 限制；本机没有 sdcfuzz 的 4 板环境，
  也没有真实缺陷芯片。
