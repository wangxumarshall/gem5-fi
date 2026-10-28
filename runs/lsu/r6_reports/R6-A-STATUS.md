# R6 A 单元（AGU）最终状态 — 2026-10-28

- 起点：`659fa4cf`；分支：`fix/r6-a-unit-20261028`
- 最终二进制：`CHAOS/gem5/build/ARM/gem5.opt` sha256 `37c9ec36…`（含 F5/SPAN/SEGV 三项修复）
- 合格 seed 总数：**9**（39 格中）

## 1. 39 格分类

| 状态 | 数量 |
|---|---|
| BLOCKED_RULING | 4 |
| EXCLUDED_NO_FIRE_3_OF_3 | 11 |
| OPEN_CHAIN_0_OF_3 | 6 |
| PARTIAL_1_OF_3 | 9 |
| POLICY_EXCLUDED_F6 | 9 |

## 2. 逐 RunID（合格 seed / 3）

| RunID | 状态 | 合格 | 子模型 | 备注 |
|---|---|---|---|---|
| A01-F0-W3 | OPEN_CHAIN_0_OF_3 | 0/3 | A01-a/b/c: IMPLEMENTED+ROUTED（band 逐事件随机抽，无 pin；动态覆盖见下） | seed1=OPEN_CHAIN(Crash,crash_translation_blocked); seed2=OPEN_CHAIN(Masked,provable_to_L2_then_unknown); seed3=OPEN_CHAIN(Masked,provable_to_L2_then_unknown) |
| A01-F1-W3 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A01-a/b/c: IMPLEMENTED+ROUTED（band 逐事件随机抽，无 pin；动态覆盖见下） | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A01-F2-W3 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A01-a/b/c: IMPLEMENTED+ROUTED（band 逐事件随机抽，无 pin；动态覆盖见下） | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A01-F0-W9 | PARTIAL_1_OF_3 | 1/3 | A01-a/b/c: IMPLEMENTED+ROUTED（band 逐事件随机抽，无 pin；动态覆盖见下） | seed1=OPEN_CHAIN(Crash,crash_translation_blocked); seed2=QUALIFIED(Masked,full); seed3=OPEN_CHAIN(Crash,crash_translation_blocked) |
| A01-F1-W9 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A01-a/b/c: IMPLEMENTED+ROUTED（band 逐事件随机抽，无 pin；动态覆盖见下） | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A01-F2-W9 | PARTIAL_1_OF_3 | 1/3 | A01-a/b/c: IMPLEMENTED+ROUTED（band 逐事件随机抽，无 pin；动态覆盖见下） | seed1=OPEN_CHAIN(Crash,crash_translation_blocked); seed2=QUALIFIED(Crash,full); seed3=OPEN_CHAIN(Crash,crash_translation_blocked) |
| A02-F0-W3 | PARTIAL_1_OF_3 | 1/3 | A02-a/b: IMPLEMENTED+ROUTED（50/50 抽） | seed1=QUALIFIED(SDC,full); seed2=OPEN_CHAIN(Crash,crash_translation_blocked); seed3=OPEN_CHAIN(Masked,provable_to_L2_then_unknown) |
| A02-F2-W3 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A02-a/b: IMPLEMENTED+ROUTED（50/50 抽） | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A02-F0-W9 | PARTIAL_1_OF_3 | 1/3 | A02-a/b: IMPLEMENTED+ROUTED（50/50 抽） | seed1=QUALIFIED(Crash,full); seed2=OPEN_CHAIN(Crash,crash_translation_blocked); seed3=OPEN_CHAIN(Crash,crash_translation_blocked) |
| A02-F2-W9 | PARTIAL_1_OF_3 | 1/3 | A02-a/b: IMPLEMENTED+ROUTED（50/50 抽） | seed1=QUALIFIED(Crash,full); seed2=OPEN_CHAIN(Crash,crash_translation_blocked); seed3=OPEN_CHAIN(Crash,crash_translation_blocked) |
| A03-F5-W3 | PARTIAL_1_OF_3 | 1/3 | A03-a/b: IMPLEMENTED+ROUTED（seed 奇偶）；F5 计数已修复 | seed1=OPEN_CHAIN(Crash,crash_translation_blocked); seed2=OPEN_CHAIN(Crash,crash_translation_blocked); seed3=QUALIFIED(Crash,full) |
| A03-F5-W10 | PARTIAL_1_OF_3 | 1/3 | A03-a/b: IMPLEMENTED+ROUTED（seed 奇偶）；F5 计数已修复 | seed1=OPEN_CHAIN(Crash,crash_translation_blocked); seed2=OPEN_CHAIN(Crash,crash_translation_blocked); seed3=QUALIFIED(Crash,full) |
| A04-F0-W3 | OPEN_CHAIN_0_OF_3 | 0/3 | A04-a: NOT_IMPLEMENTED（无对象表）；A04-b: 同页代理 IMPLEMENTED+ROUTED | seed1=OPEN_CHAIN(Masked,provable_to_L4_then_unknown); seed2=OPEN_CHAIN(Crash,provable_to_L4_then_unknown); seed3=OPEN_CHAIN(Masked,provable_to_L4_then_unknown) |
| A04-F2-W3 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A04-a: NOT_IMPLEMENTED（无对象表）；A04-b: 同页代理 IMPLEMENTED+ROUTED | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A04-F0-W0 | OPEN_CHAIN_0_OF_3 | 0/3 | A04-a: NOT_IMPLEMENTED（无对象表）；A04-b: 同页代理 IMPLEMENTED+ROUTED | seed1=OPEN_CHAIN(Crash,provable_to_L4_then_unknown); seed2=OPEN_CHAIN(SDC,provable_to_L4_then_unknown); seed3=OPEN_CHAIN(Masked,provable_to_L4_then_unknown) |
| A04-F2-W0 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A04-a: NOT_IMPLEMENTED（无对象表）；A04-b: 同页代理 IMPLEMENTED+ROUTED | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A04-F6-W3 | POLICY_EXCLUDED_F6 | 0/3 | A04-a: NOT_IMPLEMENTED（无对象表）；A04-b: 同页代理 IMPLEMENTED+ROUTED | 工作令固定排除；未运行，不计 PASS/FAIL |
| A04-F6-W0 | POLICY_EXCLUDED_F6 | 0/3 | A04-a: NOT_IMPLEMENTED（无对象表）；A04-b: 同页代理 IMPLEMENTED+ROUTED | 工作令固定排除；未运行，不计 PASS/FAIL |
| A05-F0-W3 | OPEN_CHAIN_0_OF_3 | 0/3 | A05-c: IMPLEMENTED+ROUTED（低字节旋转近似）；A05-a/b/d: NOT_IMPLEMENTED | seed1=OPEN_CHAIN(Masked,provable_to_L4_then_unknown); seed2=OPEN_CHAIN(Crash,provable_to_L4_then_unknown); seed3=OPEN_CHAIN(Masked,provable_to_L4_then_unknown) |
| A05-F2-W3 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A05-c: IMPLEMENTED+ROUTED（低字节旋转近似）；A05-a/b/d: NOT_IMPLEMENTED | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A05-F6-W3 | POLICY_EXCLUDED_F6 | 0/3 | A05-c: IMPLEMENTED+ROUTED（低字节旋转近似）；A05-a/b/d: NOT_IMPLEMENTED | 工作令固定排除；未运行，不计 PASS/FAIL |
| A06-F0-W3 | BLOCKED_RULING | 0/3 | BLOCKED_RULING：合法变换语义不唯一 | access-size/byte-enable 合法变换语义互斥，未自行发明 |
| A06-F2-W3 | BLOCKED_RULING | 0/3 | BLOCKED_RULING：合法变换语义不唯一 | access-size/byte-enable 合法变换语义互斥，未自行发明 |
| A06-F0-W5 | BLOCKED_RULING | 0/3 | BLOCKED_RULING：合法变换语义不唯一 | access-size/byte-enable 合法变换语义互斥，未自行发明 |
| A06-F2-W5 | BLOCKED_RULING | 0/3 | BLOCKED_RULING：合法变换语义不唯一 | access-size/byte-enable 合法变换语义互斥，未自行发明 |
| A06-F6-W3 | POLICY_EXCLUDED_F6 | 0/3 | BLOCKED_RULING：合法变换语义不唯一 | 工作令固定排除；未运行，不计 PASS/FAIL |
| A06-F6-W5 | POLICY_EXCLUDED_F6 | 0/3 | BLOCKED_RULING：合法变换语义不唯一 | 工作令固定排除；未运行，不计 PASS/FAIL |
| A07-F0-W3 | PARTIAL_1_OF_3 | 1/3 | A07-b: IMPLEMENTED+ROUTED；A07-a/A07-c: NOT_IMPLEMENTED | seed1=OPEN_CHAIN(Masked,provable_to_L4_then_unknown); seed2=QUALIFIED(Masked,full); seed3=OPEN_CHAIN(Masked,provable_to_L3_then_unknown) |
| A07-F4-W3 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A07-b: IMPLEMENTED+ROUTED；A07-a/A07-c: NOT_IMPLEMENTED | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A07-F0-W5 | PARTIAL_1_OF_3 | 1/3 | A07-b: IMPLEMENTED+ROUTED；A07-a/A07-c: NOT_IMPLEMENTED | seed1=OPEN_CHAIN(Masked,provable_to_L4_then_unknown); seed2=QUALIFIED(Masked,detected_contained); seed3=OPEN_CHAIN(Masked,provable_to_L4_then_unknown) |
| A07-F4-W5 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A07-b: IMPLEMENTED+ROUTED；A07-a/A07-c: NOT_IMPLEMENTED | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A07-F6-W3 | POLICY_EXCLUDED_F6 | 0/3 | A07-b: IMPLEMENTED+ROUTED；A07-a/A07-c: NOT_IMPLEMENTED | 工作令固定排除；未运行，不计 PASS/FAIL |
| A07-F6-W5 | POLICY_EXCLUDED_F6 | 0/3 | A07-b: IMPLEMENTED+ROUTED；A07-a/A07-c: NOT_IMPLEMENTED | 工作令固定排除；未运行，不计 PASS/FAIL |
| A08-F0-W3 | OPEN_CHAIN_0_OF_3 | 0/3 | A08-a/A08-b: NOT_IMPLEMENTED（仅 a08_subst 同页代理） | seed1=OPEN_CHAIN(Masked,provable_to_L4_then_unknown); seed2=OPEN_CHAIN(Crash,provable_to_L4_then_unknown); seed3=OPEN_CHAIN(Masked,provable_to_L4_then_unknown) |
| A08-F2-W3 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A08-a/A08-b: NOT_IMPLEMENTED（仅 a08_subst 同页代理） | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A08-F0-W5 | OPEN_CHAIN_0_OF_3 | 0/3 | A08-a/A08-b: NOT_IMPLEMENTED（仅 a08_subst 同页代理） | seed1=OPEN_CHAIN(Masked,provable_to_L4_then_unknown); seed2=OPEN_CHAIN(Masked,provable_to_L4_then_unknown); seed3=TRUNCATED(Crash,provable_to_L3_then_unknown) |
| A08-F2-W5 | EXCLUDED_NO_FIRE_3_OF_3 | 0/3 | A08-a/A08-b: NOT_IMPLEMENTED（仅 a08_subst 同页代理） | seed1=EXCLUDED_NO_FIRE(Masked,None); seed2=EXCLUDED_NO_FIRE(Masked,None); seed3=EXCLUDED_NO_FIRE(Masked,None) |
| A08-F6-W3 | POLICY_EXCLUDED_F6 | 0/3 | A08-a/A08-b: NOT_IMPLEMENTED（仅 a08_subst 同页代理） | 工作令固定排除；未运行，不计 PASS/FAIL |
| A08-F6-W5 | POLICY_EXCLUDED_F6 | 0/3 | A08-a/A08-b: NOT_IMPLEMENTED（仅 a08_subst 同页代理） | 工作令固定排除；未运行，不计 PASS/FAIL |

## 3. 根因与修复

- **F5COUNT** `cf224f1c`：CHAOSAddrPath F5 noteOutcome 回报；验证：A03-F5-W3 s3 FUNNEL injected=66/eligible=124
- **SPAN** `c5558c9e`：A 族 F0 warmup=1+实测 span；验证：A04-F0-W3 s1 复跑无 EARLY_BIAS
- **SEGV** `1e8e96fe`：注入/下游未映射访问 → guest SEGV 优雅 teardown；验证：A03-F5-W3 s3 admitted=True full L5

## 4. 未能完成的原因（如实）

- 子模型缺失：A04-a、A05-a/b/d、A07-a/c、A08-a/b 源码不存在；A06 语义仍不唯一（BLOCKED_RULING）。
- 结构性零：F1/F2/F4 首火阈值（50k–1.5M eligible）大于短负载流长（agu_addrmodes≈2.8k、mini_check≈3.2k），10 个 RunID 三 seed 全部合法 NO_FIRE。
- 开放链：多数 Masked/Crash 样本链止于 L2/L4，缺少真实 L5 检测事件；按门禁不计 PASS。
- 频率策略每格仅授权 3 个 seed（seed>3 一律 POLICY_NOT_REQUIRED），失败样本不能补跑。
- A03-F5-W10 本轮未执行。

## 5. 传播文档

- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/A01-F0-W9-seed2.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/A01-F2-W9-seed2.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/A02-F0-W3-seed1.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/A02-F0-W9-seed1.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/A02-F2-W9-seed1.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/A03-F5-W3-seed3.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/A07-F0-W3-seed2.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/A07-F0-W5-seed2.md`
