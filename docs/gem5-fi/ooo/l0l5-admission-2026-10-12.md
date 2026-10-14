# OOO L0-L5 阶段一准入报告（2026-10-12）

> 任务书 §阶段一验收屏障 A–J 逐项判定。全部证据路径为绝对路径；本报告与
> `runs/ooo-l0l5/admission/admission_handoff.json`（机器可读版）同时存在。
> 执行人：服务器总负责人 AI（huawei0201），Subagent-A/B/C 实现交付已审查合并。

## 冻结身份

| 项 | 值 |
|---|---|
| 源码冻结点（chaos_commit，formal yaml 声明值） | 见下方冻结对（H1=代码冻结，H2=冻结声明提交） |
| gem5.opt SHA256 | `1a618953b014514713c0ad98c7f3d69a48171d81f0463d934bccdfcfc0070bf3` |
| 开发分支 | `ooo/l0l5-chain`（基点 f2ee885，主仓 fi-ding 不动，未 push） |
| L2 策略 | window，pre_seq=10000，post_seq=3000000，msnap_every=1000（实测依据 `runs/ooo-l0l5/audit/l2-policy.md`：coremark 全程自差分 246.2s、0:3M=67.9s） |

## 屏障判定

| # | 屏障 | 判定 | 证据 |
|---|---|---|---|
| A | 单元测试全部通过 | **PASS** | 13 套全绿：guard 26 检查、guard-race 34（8 进程恰一 claim/≤2 槽/SIGKILL 回收/50 轮 churn）、scheduler-dry 88×2 连跑、observation 95、sample_runner 69（真 gem5）、golden_key（含真 smoke 双跑）、runner_msnap 16（含截断诚实路径）、commit_diff seq-range 16、chain_audit 47、E2E self 29、admission self 10、handoff 11、faults-log contract |
| B | 正常/Masked/SDC/abort-Crash 三类 E2E | **PASS** | `runs/ooo-l0l5/e2e/e2e_result.json` OVERALL=PASS：normal（极晚 trigger→Inactive，chain_complete=true 无 gap）、masked（Masked，µarch 有分歧而 arch 校验和不变）、crash（exit=-6，0 字节 ctrace=诚实截断，绝不 no_divergence）、sdc（FR02 seed 20261600 复刻，SDC + commit_diff primary=data_corruption@seq165 + detector=Application）；四类 replay determinism 全 match |
| C | 4 RunID × n=2 engineering 准入 | **PASS** | `runs/eng2_{D01-F0-W6-c,D02-F0-W6-b,D02-F0-W6-c,D04-F0-W4-d}/` 各 2 样本 COMPLETE + 2 replay match；`runs/ooo-l0l5/admission/admission_checks.json` OVERALL=PASS（identity/conservation/traces/no_overwrite/replay/observation/goldens 七项全 PASS，samples=8） |
| D | activated>0 样本证据链可读 | **PASS** | eng2 7 个 activated 样本均有 ref/fault ctrace（窗口保留）+ msnap + commit_diff + micro_diff + L5（admission traces 项 PASS）；Crash/Hang 样本按截断前缀如实记录 |
| E | observation 可解析、身份/哈希一致 | **PASS** | admission identity + observation 项 PASS（逐样本 files sha256 全量复核、gem5 sha 冻结比对、chaos_commit 一致） |
| F | Crash 截断语义诚实 | **PASS** | 审计规则 `crash_claimed_no_divergence`（Crash+ok+no_divergence=violation）；E2E crash 类 0 字节 trace → truncated 诚实；预算杀修复后 fault-landed 挂起=Hang/DUE（曾误报 SimulatorError，已修，见已知限制③） |
| G | 防重锁并发竞争测试 | **PASS** | `tools/tests/test_ooo_guard_race.py` 34 检查（Subagent-B） |
| H | 资源监控与自动降档测试 | **PASS** | `tools/tests/test_ooo_scheduler_dry.py` 88 检查 ×2 连跑（策略阶梯 6→8→6→4、身份漂移→TRIP 归零+exit 2 实测） |
| I | 无共享写入/覆盖 | **PASS** | admission no_overwrite 项 PASS（.staging 无残留、run_id 无重复、样本目录归属核验）；QUARANTINE 保留全部失败证据 |
| J | admission_handoff.json | **PASS** | `runs/ooo-l0l5/admission/admission_handoff.json`（本报告的机器可读版，含全部测试/提交/哈希/已知限制/逐屏障 PASS） |

## eng2 准入样本分类账（8/8）

| RunID | rep0 | rep1 | replay |
|---|---|---|---|
| D01-F0-W6-c (imm_bitflip@coremark) | Hang（预算杀，诚实 DUE） | Masked | 2/2 match |
| D02-F0-W6-b (bitflip2_nonadj@coremark) | Masked | Masked | 2/2 match |
| D02-F0-W6-c (bitflip2_cross@coremark) | Masked | Masked | 2/2 match |
| D04-F0-W4-d (dest_reg_sub@dep_chain) | Masked | Masked | 2/2 match |

守恒：activated 8 = 五类主结局 7（6 Masked + 1 Hang）+ post_activation_simulator_failure 1（该样本随后按 Hang 修正重跑，见已知限制③；修正后账目为 activated 8 = 五类 8）。

## 已知限制（如实，不放宽）

1. **L3 对 decode 族 unsupported**：commit trace 只记录 dest 寄存器，无 source-read 关联；decode 样本 chain_complete=false、gaps=["L3"]，在 handoff 中单独计入 l3_unsupported_only，绝不冒充完整链（任务书 §二.3 规定）。
2. **eng2 执行跨越驱动器修复提交**：e450348（大部分）→ b5b3619（截断救援）→ 4fcbe40（预算杀分类）。gem5 binary、种子、manifest 在整个期间零变化（身份守卫全程核验 gem5 sha 不变）；差异仅在驱动器侧后处理逻辑。formal 将在冻结点单提交上运行。
3. **预算杀误分类事故与修复**：eng2 D01-c rep0 首跑把 fault-landed 挂起误报 SimulatorError；根因（驱动器丢弃部分输出+无 L0 漏斗裁决）已修（4fcbe40），误分类样本隔离于 `runs/eng2_D01-F0-W6-c/QUARANTINE/misclassified-simerror-r0000.p1`（全证据保留），重跑为 Hang 且 replay match。
4. **崩溃于首刷前的样本**：ctrace 为 0 字节（诚实截断空），窗口锚退化为 [0, post]，coverage note 如实记录。
5. **观察项**：smoke decode seed 20261017 为 Hang（工具 fixture 探测发现，未使用）；goldens 目录曾有构建中残留（已自然 COMPLETE）。

## 阶段二启动面（本报告提交后立即执行）

RunAgent-A=`formal_D01-F0-W6-c`、B=`formal_D02-F0-W6-b`、C=`formal_D02-F0-W6-c`（各 ≤2 槽，全机 6，NUMA 每实例 worker 交替 0/1）；稳定 900s+门槛后 daemon 自动升 8 并代启 RunAgent-D=`formal_D04-F0-W4-d`；TRIP 阶梯 8→6→4（不杀健康样本）。D05-b/c 不启动；D01-a/b 不重跑。
