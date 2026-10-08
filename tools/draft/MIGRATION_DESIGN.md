# lsu_campaign.py 采样政策迁移设计（隔离 draft，2026-10-08）

状态：设计冻结待实施——**波次 5 运行期间不得应用到 tools/lsu_campaign.py**
（该文件是运行中 lsu_unit_pilot.py 的 import 依赖，F-023 教训）。
draft 副本：tools/draft/lsu_campaign_v2.py（本目录隔离开发+测试）。

## 政策依据
task_plan 全局实验口径 + D-2026-10-08-采样：30 pilot（六项版本一致才计入）
→ 全 RunID ≥385 → 仅 21 个固定 KEY RunID 至 2401（含 385）；无序贯停止；
Wilson 95% 报告；四层统计口径。

## KEY_RUNIDS（21 项，task_plan 冻结名单，唯一扩样集合，不得依结果增删）
A01-F0-W3, A04-F0-W3, T10-F0-W4, T04-F0-W4, S13-F0-W5, S04-F0-W5,
L01-F0-W5, L03-F0-W5, C04-F0-W6, C05-F0-W6, C10-F0-W6, C12-F0-W6,
O01-F0-W7, O05-F0-W7, P03-F0-W8, P07-F0-W8, P09-F0-W6, T10-F0-W11,
S13-F0-W12, O09-F0-W13, P09-F0-W13

## 修改点（行号 = 当前 tools/lsu_campaign.py@b555d997）

| # | 位置 | 现状（旧规则） | 迁移后（新规则） |
|---|---|---|---|
| M1 | L8-12 docstring | "main: sequential until Wilson half-width≤2pp or 5000" | "main: 仅 KEY_RUNIDS 累计至固定 2401；其余 304 项不进入 main 扩样；固定样本，无序贯停止" |
| M2 | 模块顶部新增常量 | — | KEY_RUNIDS=frozenset(21项)；SCREENING_TARGET=385；MAIN_TARGET_KEY=2401；CONFIG_FP（六项版本指纹：注入器/配置/workload/checkpoint/oracle/分类规则） |
| M3 | L519 `--main-target default=5000` | 全局 5000 上限 | **禁止简单改 default=2401**（会让全部 RunID 扩样）。改为 default=None + deprecated 说明；实际 target 在 run_cell_adaptive 内按 `runid in KEY_RUNIDS` 解析：重点→2401，非重点→385（不扩展） |
| M4 | L521 `--wilson-stop-hw default=0.02` | 控制序贯停止 | 保留 CLI 形参但标记 deprecated，**不参与任何停止判断**；help 注明"2026-10-08 政策后失效" |
| M5 | L602-604 target dict | 按 phase 取 args.*_target | main 分支改为 `MAIN_TARGET_KEY if runid in KEY_RUNIDS else args.screening_target` |
| M6 | L618-623 Wilson 停止块 | main 阶段 hw≤0.02 即停 | **整块删除**（固定样本量，唯一停止 = target-met / seed-cap） |
| M7 | L626-634 run 记录累计 | runs 只存 seed/activated/outcome | 增加 eligible 累计 + crash_kind 存储 + sim_fail 计数（outcome==Crash 且 crash_kind==simulator_assert → sim_fail，不进五类——对齐 unit_pilot audit 口径） |
| M8 | L637 sdc_rate=SDC/activated | 分母含 sim_fail | `denom = activated - sim_fail`；denom==0 → sdc_rate=None（NA，保留计数，不得伪造 0%） |
| M9 | L638 act_rate=activated/attempted | 分母 attempted | 改两层：eligible_rate=eligible/attempted（合法目标出现率）+ activation_rate=activated/eligible（故障激活率）；attempted/eligible 从 run_single_cell 结果累计（M7） |
| M10 | cell_results.json (L640-649) | 无版本指纹 | 增加 config_fp（M2）+ eligible/sim_fail/eligible_rate/sdc_rate(可为 null) 字段；pilot 计入 385/2401 累计时对比 config_fp，不一致 → 分层隔离标记，不静默混合 |
| M11 | resume/seed（引擎级） | campaign 逐 seed 新跑 | resume 扫描已有 seedN 目录的 verdict（对齐 unit_pilot 的 _valid_resumed 语义）——seed 按 1..N 不重复 |

不改项：L504 `--max-parallel default=4`（4 并发已批准）；L515 trial 30 / L517
screening 385（与新政一致）；F1-F4 per-run cluster 语义（L593-595、L660-664
已正确）；**MODEL_BLOCKED/MODEL_FLAGS/WL_BINARY/GOLDENS 常量接口零变更**
（unit_pilot.py 运行中 import 它们——P3 兼容性硬约束）。

## 测试清单（应用前必须全 PASS；draft 内跑，不碰正式文件）
T1  21 个 KEY RunID 全部解析 main target=2401
T2  其余 304 个 RunID 解析 main target=385（不扩展）
T3  325 项中无任何非重点项获得 2401（防"全局默认 2401"错误）
T4  pilot 30 计入累计不重复计数（同 seed 不二次累计）
T5  sim_fail 正确从 SDC 率分母扣除（sdc_rate=SDC/(act−simfail)）
T6  可分析 activated=0 → sdc_rate=None（非 0.0），classes 计数保留
T7  F1-F4 同一 run 多事件只算 1 个 cluster（per-run Wilson）
T8  --wilson-stop-hw=0.02 与旧 5000 传入均不影响停止（唯一停止=target/seed-cap）
T9  resume 后 sample_index/seed 不重复
T10 unit_pilot.py 对常量接口的 import 与 P3 30/300 行为零回归
测试实现：tools/draft/test_campaign_v2.py（mock run_single_cell，不跑 gem5）

## 应用条件（自然安全边界，全部满足才可替换正式文件）
1. /tmp/pilot_wave.log 出现 WAVE_DONE（bash 链三单元自然结束）
2. ps 无 bash 654696 / 无 unit_pilot / 无 gem5.opt / 无 lsu_guard run 进程
3. runs/lsu/guard/ 四槽锁文件全部不存在
4. guard_events.log 已安静（最后事件后无新增）
5. ps 全查无其他会话进程引用 lsu_campaign.py（含集群侧）
6. draft 测试 T1-T10 全 PASS + py_compile
应用流程：替换 → py_compile → --dry-run 冒烟 → commit → push → P4 引擎开发
