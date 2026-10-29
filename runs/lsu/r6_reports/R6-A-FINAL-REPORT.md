# R6 A 单元（AGU）最终报告 — 2026-10-28

## 0. 结论摘要（先给事实）

- 起点 `659fa4cf`（= origin/fix/r6-f5-noeffect-20261026 = origin/fi-ding），工作分支 `fix/r6-a-unit-20261028`。
- A 单元 39 格：**9 POLICY_EXCLUDED_F6、4 BLOCKED_RULING（A06）、11 EXCLUDED_NO_FIRE（三 seed 全合法零注入）、9 PARTIAL_1_OF_3、6 OPEN_CHAIN_0_OF_3**。
- **合格 seed 总数：9**（每格 3 seed 中最多 1 个合格）。**没有任何 RunID 达到 3/3**。
- 修复并验证了 3 个真实根因（F5 计数、F0 span、SE 崩溃证据截断），均独立提交。
- **未达到“所有实际可执行格 COMPLETE_3_OF_3”**。原因是结构性的，见 §5，不是本次执行懈怠：子模型缺失、频率阈值结构性零、开放链门禁、以及频率策略每格只授权 3 个 seed。

## 1. 方法与纪律

- 三路只读诊断（Lane A/B/C）→ `R6-A-DIAG-{A,B,C}.md`；主 agent 建立唯一实现 owner 表（见 INITIAL-STATUS §5）。
- 每个 RunID+seed 独立目录、flock 防重复、原子 manifest、`.done`；证据落在主仓 `runs/lsu/r6_a*_<RunID>_s<seed>/`，不覆盖旧目录。
- 真实注入/链判定以 `addrpath_injections.log` + `CHAOS_LSU_TRIGGER` + `chain_report.json` 三源为准；传播文档由真实 prop_evt 生成，不合成。
- 未运行任何 F6；未重跑/修改任何 T 单元证据；T08-F4 维持 2 合格 + seed3 EXCLUDED_NO_FIRE。

## 2. 39 格分类（最终）

| 状态 | 数量 | RunID |
|---|---|---|
| POLICY_EXCLUDED_F6 | 9 | A04-F6-W3/W0、A05-F6-W3、A06-F6-W3/W5、A07-F6-W3/W5、A08-F6-W3/W5 |
| BLOCKED_RULING | 4 | A06-F0-W3/W5、A06-F2-W3/W5 |
| EXCLUDED_NO_FIRE_3_OF_3 | 11 | A01-F1-W3、A01-F1-W9、A01-F2-W3、A02-F2-W3、A04-F2-W0、A04-F2-W3、A05-F2-W3、A07-F4-W3、A07-F4-W5、A08-F2-W3 |
| PARTIAL_1_OF_3 | 9 | A01-F0-W9、A01-F2-W9、A02-F0-W3、A02-F0-W9、A02-F2-W9、A03-F5-W3、A03-F5-W10、A07-F0-W3、A07-F0-W5 |
| OPEN_CHAIN_0_OF_3 | 6 | A01-F0-W3、A04-F0-W0、A04-F0-W3、A05-F0-W3、A08-F0-W3、A08-F0-W5 |

## 3. 9 个合格 seed（全部有完整 L0→L5 或真实 containment）

| RunID | seed | 结局 | terminal | 证据目录 |
|---|---|---|---|---|
| A01-F0-W9 | 2 | Masked | full | `runs/lsu/r6_a_segv2_A01-F0-W9_s2` |
| A01-F2-W9 | 2 | Crash | full | `runs/lsu/r6_a_segv2_A01-F2-W9_s2` |
| A02-F0-W3 | 1 | **SDC** | full | `runs/lsu/r6_a_spanfix_A02-F0-W3_s1` |
| A02-F0-W9 | 1 | Crash | full | `runs/lsu/r6_a_segv2_A02-F0-W9_s1` |
| A02-F2-W9 | 1 | Crash | full | `runs/lsu/r6_a_segv2_A02-F2-W9_s1` |
| A03-F5-W3 | 3 | Crash | full（66 faults） | `runs/lsu/r6_a_segv2_A03-F5-W3_s3` |
| A03-F5-W10 | 3 | Crash | full（89 faults） | `runs/lsu/r6_a_fix2_A03-F5-W10_s3` |
| A07-F0-W3 | 2 | Masked | full | `runs/lsu/r6_a_segv2_A07-F0-W3_s2` |
| A07-F0-W5 | 2 | Masked | detected_contained（L3） | `runs/lsu/r6_a_segv2_A07-F0-W5_s2` |

9 份传播文档：`runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/Axx-Fx-Wx-seedN.md`。

## 4. 根因、修复、验证、构建

| # | 根因 | 提交 | 修复 | 真实验证 |
|---|---|---|---|---|
| 1 | F5 仅 `++fires`，CHAOSAddrPath 不回报 `noteOutcome` → `trigger.injected` 恒 0 | `cf224f1c` | trigger F5 构造置 `require_outcome_accounting`；AddrPath 三条出口回报 | A03-F5-W3 s3：`FUNNEL attempted=122 eligible=122 injected=66`（修复前恒 0；差额是正确值已等于卡死值的 no-op） |
| 2 | 非 A07 addrpath 模型 F0 仍用 span=1000，短流被截断采样（EARLY_BIAS） | `c5558c9e` | A 族 F0 统一 warmup=1 + 实测 golden 流长；缺表 loud refusal | 8 对 census；A04-F0-W3 s1 复跑无 EARLY_BIAS；A08-F0-W5 缺表时被正确 BLOCKED，补 census 后放行 |
| 3 | SE 下注入/下游未映射 VA 触发 `GenericPageTableFault` panic → stats 0B、gzip 无 trailer | `1e8e96fe` | 注入 VA 登记 + CHAOSAddrPath 激活 → guest SEGV 正常 exitSimLoop（基线仍 panic） | A03-F5-W3 s3：`truncated=False events=727 terminal=full L5 admitted=True stats=237760B`；A01/A02 崩溃样本 stats≈257KB |

构建：每次 C++ 改动后 `scons -j126 build/ARM/gem5.opt`，均 `EXIT=0`、0 warning/0 error。
二进制 SHA：`3db54541`（起点）→ `bdf82496`（F5+SPAN）→ `443e3d0f`（SEGV v1）→ **`37c9ec36`**（SEGV armed，最终）。
源提交等价：`cf224f1c`（F5）→ `c5558c9e`（SPAN）→ `1e8e96fe`（SEGV）。前 3 个验证样本的 manifest 记录的是运行时最后已提交 src head（`cf224f1c`），每目录有 `PROVENANCE-NOTE.json` 说明“构建树内容 == 1e8e96fe”。

## 5. 为什么没有 COMPLETE_3_OF_3（如实归因）

1. **子模型源码不存在**：A04-a（同对象地址换）无对象表；A05-a/b/d（base/index、SXTW/UXTW、pre/post）无操作数级钩子；A07-a/c（旧 EA、ready 丢失）未实现；A08-a/b（错通道、同周期 EA 互换）未实现（仅同页代理）。按工作令要求记为 NOT_IMPLEMENTED，不以字符串存在冒充动态覆盖。
2. **结构性零**：F1/F2/F4 首火阈值 50k–1.5M eligible，而 `agu_addrmodes`≈2.8k、`mini_check`≈3.2k；11 个 RunID 三 seed 均合法 NO_FIRE（EXCLUDED_NO_FIRE，不计 PASS/FAIL）。
3. **开放链**：多数 Masked/Crash 样本的真实链止于 L2（翻译阻断）或 L4（无消费者/无错误提交），L4→L5 缺失；门禁不允许 chain_end 冒充 L5，故不计 PASS。
4. **频率策略每格仅授权 3 个 seed**（`required_seeds=3`，seed>3 → POLICY_NOT_REQUIRED，无旁路）。失败的 seed 不能替换，工作令“默认不采用 replacement 策略”与此一致。
5. A06 语义仍不唯一（load shrink 方向、byte-enable 合法掩码定义、target 选择、触发口径），保持 BLOCKED_RULING，不自行发明。

## 6. 收尾补跑（批次 4，已完成）

- A08-F0-W5 / A08-F2-W5 此前被 SPAN loud refusal 正确阻断；补 census `(A08,sq_forward)=2582` 后放行。A08-F0-W5：s1/s2 开放链（L4），s3 发生非页错误的 abort（run.err 无 page-table panic，stats 0B）→ TRUNCATED，不再掩盖；A08-F2-W5：三 seed 全零注入。
- A03-F5-W10：s1/s2 翻译阻断（L2/L3），s3 **合格**（Crash/full/L5，89 faults，events=982）。
- 结果并入 `R6-A-STATUS.json`。

## 7. 子模型动态覆盖

| 子模型 | 状态 | 动态证据 |
|---|---|---|
| A01-a/b/c | IMPLEMENTED+ROUTED；band 逐事件抽，无 pin | F0/W9 合格与开放链 seed 中真实注入（bitmask 见日志） |
| A02-a/b | IMPLEMENTED+ROUTED（50/50） | A02-F0-W3 s1（mask 0x6 相邻）、A02 W9 seeds |
| A03-a/b | IMPLEMENTED+ROUTED（seed 奇偶） | A03 s1 stuck0、s2 stuck1、s3 stuck0 |
| A04-a | NOT_IMPLEMENTED | —（仅 A04-b 同页代理） |
| A04-b | IMPLEMENTED+ROUTED | A04 W3/W0 三 seed |
| A05-a/b/d | NOT_IMPLEMENTED | — |
| A05-c | IMPLEMENTED+ROUTED（近似） | A05 三 seed |
| A06-a/b | 裁决阻塞 | 未运行 |
| A07-a/c | NOT_IMPLEMENTED | — |
| A07-b | IMPLEMENTED+ROUTED | A07-W3/W5 三 seed |
| A08-a/b | NOT_IMPLEMENTED（仅代理） | A08 三 seed 走同页代理 |

## 8. 旧证据处理

旧 pilot（`r6_n6_A05-F0-W3_s1`、旧 worktree A01/A04/A06/A07）只作诊断参考，未移动/覆盖/删除。逐份核对结论见 DIAG-A/B/C。旧 A05 与当前二进制不同（`e8052842…` vs `3db54541…`），未计入本轮；旧 A04 pilot 地址落在 glibc 数据段而非 oracle 数组，按“地址属于 oracle 对象”应判 Injected-not-activated。

## 9. 最终判定

- A 单元**未完成**“实际可执行格全部 COMPLETE_3_OF_3”。
- 已完成：3 个根因修复、9 个合格 seed 的完整传播证据、39 格权威分类、子模型诚实覆盖表。
- 待办（需要新的语义裁决/实现/策略授权）：
  1. 实现 A04-a、A05-a/b/d、A07-a/c、A08-a/b（操作数级/配对级钩子）。
  2. A06 语义裁决。
  3. 结构性零格的频率/负载策略裁决（是否允许更换负载或放宽阈值——不得由本轮自行决定）。
  4. 若需 >3 seed 补跑，需要频率策略的显式授权。
