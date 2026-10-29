# R6 A 单元（AGU）初始权威状态表 — 2026-10-28

- 权威起点提交：`659fa4cf6ea2095e178f43df9f177bff8260bda2`（HEAD = origin/fix/r6-f5-noeffect-20261026 = origin/fi-ding）
- 工作分支：`fix/r6-a-unit-20261028`
- gem5：`CHAOS/gem5/build/ARM/gem5.opt`，SHA-256 `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`，binary_source_head `1f344a5b66da30267c578536e00a1ad4ad56bb31`（HEAD 祖先，已核验）
- 机读版本：`R6-A-INITIAL-STATUS.json`
- 只读诊断报告：`R6-A-DIAG-A.md`（A01/A02/A03）、`R6-A-DIAG-B.md`（A04/A05/A06）、`R6-A-DIAG-C.md`（A07/A08）

## 1. 分类汇总（39 格）

| 状态 | 数量 |
|---|---|
| READY_FOR_CANARY | 11 |
| REVIEW_REQUIRED | 15 |
| BLOCKED_RULING | 4 |
| POLICY_EXCLUDED_F6 | 9 |
| **合计** | **39** |

## 2. 逐 RunID 状态

| RunID | 状态 | 依据（证据路径/结论） |
|---|---|---|
| A01-F0-W3 | READY_FOR_CANARY | `CHAOSAddrPath.cc:253-267` A01 单 bit 低/中/高 band；F0 单次抽样可触发（旧 trial activated=5，仅诊断参考） |
| A01-F1-W3 | REVIEW_REQUIRED | F1 首火 500k–1.5M eligible（`chaos_lsu_trigger.hh` interval=1,000,000，`scheduleNext` 半区间抖动）；W3 观测 eligible≈2.7k → 结构性零 |
| A01-F2-W3 | REVIEW_REQUIRED | F2 首火 50k–150k；W3 eligible≈2.7k → 结构性零（旧 trial activated=0） |
| A01-F0-W9 | READY_FOR_CANARY | **W9 重新评估**：SE 载体 `workloads/directed/gap_bfs`（aarch64 static ELF）+ golden `030921682b3731f2`；`R6-STATUS-TABLE.md:54` RUNNABLE。FS 镜像无 GAP 只约束 FS（T08），不约束 SE W9 |
| A01-F1-W9 | REVIEW_REQUIRED | F1 阈值 500k–1.5M > gap_bfs eligible≈265k → 结构性零 |
| A01-F2-W9 | READY_FOR_CANARY | W9 重新评估（同上）；F2 阈值 50k–150k < 265k，可触发 |
| A02-F0-W3 | READY_FOR_CANARY | `CHAOSAddrPath.cc:268-285` 相邻/非相邻双 bit；F0 可触发 |
| A02-F2-W3 | REVIEW_REQUIRED | F2 结构性零（W3 eligible≈2.7k） |
| A02-F0-W9 | READY_FOR_CANARY | W9 重新评估（同上） |
| A02-F2-W9 | READY_FOR_CANARY | W9 重新评估（同上）；F2 可达 |
| A03-F5-W3 | REVIEW_REQUIRED | **F5 计数缺陷**：`chaos_lsu_trigger.hh:251-256` F5 仅 `++fires`，要求注入器 `noteOutcome()` 回报；`CHAOSAddrPath.cc` 从未调用（全仓仅 `CHAOSArmTLB.cc:832/865`），`trigger.injected` 恒 0 → funnel/L5 activated 结构性 0 |
| A03-F5-W10 | REVIEW_REQUIRED | 同上；另需事件流体积/增长率监控 |
| A04-F0-W3 | READY_FOR_CANARY | `a04_subst` 同页 16B 代理（`:585-595`）已路由；A04-a 同对象子模型 NOT_IMPLEMENTED |
| A04-F2-W3 | REVIEW_REQUIRED | F2 结构性零（旧 trial activated=0） |
| A04-F0-W0 | READY_FOR_CANARY | 同上；W0=mini_check，SE 下 mprotect/guard page 退化，oracle 需实测核实 |
| A04-F2-W0 | REVIEW_REQUIRED | F2 结构性零 |
| A05-F0-W3 | READY_FOR_CANARY | 仅 `a05_shift`（子模型 c，低字节旋转近似，`:596-602`）实现并路由；A05-a base/index、A05-b SXTW/UXTW、A05-d pre/post **NOT_IMPLEMENTED** |
| A05-F2-W3 | REVIEW_REQUIRED | F2 结构性零 |
| A06-F0-W3 | BLOCKED_RULING | 合法变换语义不唯一：load shrink 方向、byte-enable “合法掩码”定义、target 选择、触发口径均有互斥选项；`2026-10-19-lsu-mdspec-port-and-l05.md:58-68` 仍为 BLOCKED+另提裁决，R4-8 自裁被 R4-10 NO-GO 否定（`R4-10-INTEGRATION-REPORT.md:31`），R6 裁决 D–I 无 A06 |
| A06-F0-W5 | BLOCKED_RULING | 同上 |
| A06-F2-W3 | BLOCKED_RULING | 同上；另有 F2 结构性零 |
| A06-F2-W5 | BLOCKED_RULING | 同上；另有 F2 结构性零 |
| A07-F0-W3 | READY_FOR_CANARY | clean ready hook 已存在：`iew.cc:1194-1218` → `CHAOSAddrPath::maybeDelayAguReady`（`:852-952`），resume `iew.cc:1412-1483`；仅 A07-b 实现，A07-a/A07-c **NOT_IMPLEMENTED** |
| A07-F4-W3 | REVIEW_REQUIRED | F4 首火 ≥50k eligible（interval=100,000），W3 eligible≈2.8k → 结构性零；addrpath 缺 interval 拒斥门禁（会安静产出 activated=0） |
| A07-F0-W5 | READY_FOR_CANARY | 同上；W5 载体待 canary 实测 |
| A07-F4-W5 | REVIEW_REQUIRED | F4 结构性零 |
| A08-F0-W3 | REVIEW_REQUIRED | 仅 `a08_subst`（同页地址代理）路由；A08-a 错通道 / A08-b 同周期 EA 互换 **NOT_IMPLEMENTED**（Request 在 PRE hook 之后构造，事后互换不安全） |
| A08-F2-W3 | REVIEW_REQUIRED | 同上；F2 结构性零 |
| A08-F0-W5 | REVIEW_REQUIRED | 同上 |
| A08-F2-W5 | REVIEW_REQUIRED | 同上 |
| A04-F6-W3/W0、A05-F6-W3、A06-F6-W3/W5、A07-F6-W3/W5、A08-F6-W3/W5（9 格） | POLICY_EXCLUDED_F6 | 工作令固定排除；本轮不运行、不计 PASS/FAIL |

## 3. 与工作令预设口径的差异（必须显式记录）

1. **W9 不再是 BLOCKED_WORKLOAD_GAP**：工作令的前提是“FS 镜像通过 debugfs 确认不含 GAP/Graph500”。只读核验表明 A01/A02 的 W9 是 **SE** 负载 `gap_bfs`（`runid_map.json` 指定，golden `030921682b3731f2` 已记录），
   `R6-STATUS-TABLE.md` 判 RUNNABLE，且 `R4-8-S10-span-report.md:128` 使用同一 golden。FS 镜像结论只约束 T08-FS。按工作令 §3.2 的重新评估条款，5 个 W9 格改为可执行评估（F1-W9 仍因阈值结构性零）。
2. **21 格“预计可执行”中，仅 11 格静态 READY**：其余受 F1/F2/F4 结构性零、F5 计数缺陷、或子模型未实现影响，已逐格标注。
3. **A06 保持 BLOCKED_RULING**：交互语义仍不唯一，本报告不发明语义。

## 4. 子模型实现状态（静态）

| 子模型 | 状态 | 证据 |
|---|---|---|
| A01-a/b/c | IMPLEMENTED + ROUTED | `CHAOSAddrPath.cc:258-262` band=rng()%3 逐事件抽；**无 band pin，3 seed 不保证全覆盖**，需辅助 canary |
| A02-a/b | IMPLEMENTED + ROUTED | `:273-279` 50/50 抽；同上需辅助 canary |
| A03-a/b | IMPLEMENTED + ROUTED | campaign seed 奇偶（`lsu_campaign.py:2824-2830`，seed1/2/3→stuck0/stuck1/stuck0）；F5 计数缺陷阻断 |
| A04-a | NOT_IMPLEMENTED | 无对象表；only 同页代理 |
| A04-b | IMPLEMENTED（同页代理）+ ROUTED | `:585-595`；无对象/liveness 过滤，候选集合/距离未记录 |
| A05-a/b/d | NOT_IMPLEMENTED | 需操作数级 AGU 钩子 |
| A05-c | IMPLEMENTED + ROUTED（近似） | `:596-602` 低字节旋转；旧 run 真实注入但落在 base+imm ldr，不满足“对应寻址模式”触发 |
| A06-a/b | IMPLEMENTED + ROUTED，但**语义裁决阻塞** | `:603-...`/`be_mode`；runid_map 未唯一规定合法变换 |
| A07-a/c | NOT_IMPLEMENTED | 仅 a07b_ready_delay 落地 |
| A07-b | IMPLEMENTED + ROUTED | `iew.cc` + `CHAOSAddrPath.cc:852-952` |
| A08-a/b | NOT_IMPLEMENTED | 仅 a08_subst 代理 |

## 5. 文件所有权表（单一实现 owner）

| 文件 | 角色 | Owner |
|---|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/{CHAOSAddrPath.cc,.hh,.py}` | A01–A08 共享注入点 | 主 agent（唯一实现） |
| `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh` | 全 LSU 触发语义 | 主 agent |
| `CHAOS/gem5/src/cpu/o3/iew.{cc,hh}`、`lsq.cc`、`lsq_unit.cc` | A07/A08/A 共享 | 主 agent |
| `configs/se/*`（lsu proxy） | 挂载参数 | 主 agent |
| `tools/lsu_campaign.py`、`tools/lsu_runid_map.py`、`tools/lsu_chain_check.py` | 工具链 | 主 agent |
| `tests/*` | 测试 | 主 agent |
| `runs/lsu/r6_reports/R6-A-DIAG-{A,B,C}.md` | 只读诊断产物 | 各 Lane（已完成，不再修改） |

三路诊断 subagent 均为只读，不持有任何实现文件写权限。

## 6. 下一步（本轮执行顺序）

1. 修复 F5 计数缺陷（失败测试 → 最小修复 → 定向测试 → 统一构建），解锁 A03。
2. 代表 canary（每模型 seed1）：A01-F0-W3、A02-F0-W3、A03-F5-W3、A04-F0-W3、A05-F0-W3、A07-F0-W3；A08 需先决定是否按规格实现。
3. canary 通过后补齐 3 seed；F2/F4 结构性零格用真实 eligible 数据裁决（EXCLUDED_NO_FIRE 或结构性零）。
