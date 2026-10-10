# 无人值守推进：OOO 四模型 formal + FR02 recount 审计（2026-10-10 启动）

> 本文件是"休息日无人值守推进模式"（用户 2026-10-10 授权）的**运行清单与阶段日志**，是会话中断后恢复的权威入口。
> 决策树全文以用户当日指令为准；本文件是其可执行摘要 + 状态登记。主 agent 是唯一 campaign 调度者；subagent 只监控/审计/分析。

## 运行清单（Run Registry）

| 任务 | 身份 | PID/PGID | 日志/输出 | 恢复命令 |
|---|---|---|---|---|
| FR02 recount（**归属其他会话，勿动**） | /tmp/recount-worker.sh ×2；任务表 /tmp/recount-half-aa(198)/half-ab(197)；输出 /tmp/recount-{A,B}.csv | 911793 / 911794 | /tmp/recount-{A,B}.csv（完成信号 = 两 worker 进程消失；CSV 可能静默丢 timeout 行） | 不适用（禁终止/重启/修改） |
| formal_D04c_depchain | decode src_swap，base_seed 20263000，n_per_cell 385，hang 600，replay 0，C3/SE/workloads/ooo/dep_chain/dep_chain，golden depchainint-golden-v1 | 958859 / PGID 958859（16:25:35 启动） | /tmp/ooo-pipeline/formal_D04c_depchain.out；runs|artifacts /formal_D04c_depchain/ | `cd /home/sdc/gem5-fi-ding && setsid nohup python3 tools/campaign.py /tmp/ooo-pipeline/formal_D04c_depchain.yaml --jobs 2 > /tmp/ooo-pipeline/formal_D04c_depchain.out 2>&1 < /dev/null &` |
| formal_D04e_depchain | decode x0_sub，base_seed 20263500，其余同上 | 958858 / PGID 958858 | …/formal_D04e_depchain.out | 同上，换 formal_D04e_depchain.yaml |
| formal_D05b_depchain（**已完成** 21:02，driver 已退出） | decode imm_rotate / local_mbu，base_seed 20264000 | 1053397（已退出） | /tmp/ooo-pipeline/formal_D05b_depchain.out | （历史）启动命令见 git 历史版本 |
| formal_R03c_depchain（**已完成** 21:15，driver 已退出） | rat src_tag_swap / field map / width 7，base_seed 20264500 | 1053396（已退出） | /tmp/ooo-pipeline/formal_R03c_depchain.out | （历史）同上 |
| topup 备用 seed 块 | D04c 20265000 / D04e 20265100 / D05b 20265200 / R03c 20265300 | — | — | 仅当某模型 385 attempt 后有效 <385，按实测有效率一次性有上限补跑，topup 后重审，禁止无限补跑 |

## 关键事实（审计/监控依据）

1. **campaign.py 落盘语义**：results.jsonl 在全部 385 rep + 1 replay 完成后由 driver 一次性写出（`tools/campaign.py` 结果聚合段）；中途不存在；**driver 中途死亡 = 该模型已跑结果全丢，需整跑重跑**（恢复命令见上表）。`.out` 进度行受 stdout 块缓冲延迟，中途进度看 `ps` 里 gem5 的 `rng_seed`（D04c rep = seed−20263000；D04e = seed−20263500；D05b = seed−20264000；R03c = seed−20264500）。
2. **速率基线**：pilot 真实基线 42.7s/rep/worker（pilot_D04c.out：jobs=4，30 reps/320s）；formal 实测 ~40–46s/rep；recount ~50s/task（dep_chain_vec）。持续 >64s/rep = 异常。
3. **binary 链**：六 formal + 四 pilot 用冻结 binary `9ecab3ad…`；现役 `1a618953…`（15:06 构建，297694f 仅日志标记修复，注入行为不变；修复覆盖 100%，subagent C 程序化核验：RenameMap 27/27、Decode 31/31 日志语句带标记，362 个 post-fix 日志 0 无标记行）。
4. **身份基线（16:24 冻结）**：HEAD `297694f821dee6a87a1083a9cba7aa0727742cda`；gem5.opt sha256 `1a618953b014…`；dep_chain sha256 `991d556a…`；tools md5 campaign `ae748f84` / runner `bf33e9c6` / classify `bc635ab1`；/proc/vmstat pswpout 基线 245738、pswpin 0。
5. **recount 已知缺陷（C 审计，消费结果时必须处理）**：任务表尾部 18 条 topup_FR02 manifest 原跑 INT dep_chain 负载 + INT golden（种子与 formal r0200–r0239 相同），而 recount-worker.sh 统一喂 VEC binary → 该 18 行 = formal 确定性重复 + 必然误判 SDC，**审计时剔除**；recount CSV 对 timeout 行静默丢行（join 时区分 pending/lost）。
6. **健康判据（C 实证）**：D04c/D04e 已跑 151 个运行 skip-only=0 → formal Reach 应保持 ~100%，**明显 Inactive 或 f≥2 = 真异常**（非日志修复可解释）；D05b/R03c 开跑后先各抽 5–10 个运行日志（decode_injections.log / rename_injections.log）看 skip-only 构成再下结论。
7. **FR02 recount 中期快照（16:53，230 条重判）**：Masked/1→Inactive/0 共 27（旧 Masked/f=1 的 13.8% 假激活）+ f=2 两条全假；SDC 30/30、Crash 2/2 零翻转；外推 formal n_valid 373→≈329、P_SDC 12.1%→≈13.7%（最终以 recount 完成为准）。

## 自动化决策树（用户授权摘要）

1. **并发**：临时全机 gem5≤6（recount 2 + D04c 2 + D04e 2）；recount 结束 → 自动回落 ≤4；释放名额不用于提高单模型 jobs；禁止 8。
2. **批次接力**：批次1 两模型完成 + 统计审计 → **直接启动批次2**（D05-b + R03-c 各 jobs=2，全机 ≤4），不等用户确认。
3. **有效样本规则**：目标 ≥385 **valid**/模型（不计 Inactive、f=0、f 不符模型定义、无真实故障写入、SimulatorError、身份不一致、unknown、资源争用伪超时）；385 attempt 不足 → 按实测有效率一次性有上限 topup（新 seed 块），不覆盖旧结果，topup 后重审。
4. **资源阶梯**：Mem≥10G 且无持续 swap 且 iowait≤10% → 继续；Mem<10G 或持续 swap → 停止派发新样本、总并发降至 4 → 仍不稳降至 2 → 稳定 15 分钟后 2→4 恢复；recount 结束后不得回 6；不杀其他会话进程；≤6 硬上限。
5. **recount 完成后**：自动生成审计报告（attempted / triggered / faults_injected 0/1/2/其他 / Inactive / Hang/null / SimulatorError / 有效 activated 分母 / L5（可得范围内，不可得记 n/a）/ 与原报告差异 / seed 级异常清单）+ **correction overlay**（不改原始 results.jsonl）+ 本地提交；不阻塞四模型 formal。
6. **共享 runner/classifier/schema 缺陷**：不热修运行中代码；未受影响样本安全收尾；暂停依赖缺陷的新样本；修复方案+最小复现留档，批次边界再修。
7. **单模型失败**：只停该模型派发（标记 quarantined/needs-audit），保留现场，其他模型继续；不因单模型失败让全机空闲；不修改分类器掩盖错误。
8. **Git**：允许本地分项提交（审计报告 / correction overlay / 离线统计工具 / 本清单）；禁 push、fetch、merge/rebase/reset/clean；不提交 runs、artifacts、build、冻结 binary、/tmp。
9. **硬停条件（仅这些）**：可能覆盖/删除原始结果；需要 push 或破坏性 Git；两 campaign 写同一目录；binary/workload 身份漂移；OOM/磁盘耗尽/硬件故障；结果无法确定归属；需要改变故障模型科学定义。单点停止时继续其他独立安全工作。
10. **监控**：每 ~9 分钟电池（gem5/Mem/swap/iowait/身份/进度/速率）；~30 分钟一轮 subagent B 守卫；模型 results.jsonl 落盘后派 subagent A 结果审计；recount 完成后重派 subagent C 产出审计报告。阶段推进即更新本文件。

## 阶段日志

- **[2026-10-10 21:25] ★ 全量收口：四模型 + FR02 审计全部完成，无人值守任务终止**。R03-c 审计：385/385 valid（Masked 304 + Crash 81）、385×f=1、P_SDC 0.0% [0.0,1.0]、P_DUE 21.0% [17.3,25.4]（pilot 26.7% [14.2,44.4]，CI 内）、r0000–r0384 无缺无重。批次2 独立审计（subagent A）已派发，结果返回后追加登记。gem5=0、全部 driver 正常退出、全机资源干净。

  **四模型最终结果总表（全部 ≥385 valid、零 topup、零异常）**：

  | 模型 | 模式 | valid | Masked | Crash | SDC | P_SDC [95%CI] | P_DUE [95%CI] | pilot P_DUE | Reach |
  |---|---|---|---|---|---|---|---|---|---|
  | D04-c | decode src_swap | **385/385** | 310 | 75 | 0 | 0.0% [0.0,1.0] | 19.5% [15.8,23.7] | 20% [9.5,37.3] ✓ | 100% |
  | D04-e | decode x0_sub | **385/385** | 329 | 56 | 0 | 0.0% [0.0,1.0] | 14.5% [11.4,18.4] | 10% [3.5,25.6] ✓ | 100% |
  | D05-b | decode imm_rotate | **385/385** | 277 | 108 | 0 | 0.0% [0.0,1.0] | 28.1% [23.8,32.7] | 30% [16.7,47.9] ✓ | 100% |
  | R03-c | rat src_tag_swap | **385/385** | 304 | 81 | 0 | 0.0% [0.0,1.0] | 21.0% [17.3,25.4] | 26.7% [14.2,44.4] ✓ | 100% |

  合计 **1540 个有效样本**；四模型全部 385×f=1（100% 激活，与 pilot Reach 100% 及 subagent C 的"skip-only=0"预判一致）；**零 SDC / 零 Inactive / 零 Hang / 零 SimulatorError / 零 unknown / 零重复 seed**；全部 faults_injected 统计基于 parser 修复后 binary（297694f），口径可靠。

  **科学结论**：四个 D04/D05/R03 子模式在 dep_chain/C3/SE 下均为 **0% SDC 的纯 DUE/Masked 剖面**（P_DUE 14.5–28.1%）——与 OOO 族既有格局一致（译码/重命名类故障 → 崩溃型 DUE，无静默数据损坏逃逸），且这是 parse-fix 后口径下的可信测量。

  **运行合规记录**：批次1/批次2 各 2 模型 × jobs=2；临时上限 6 仅存在于 recount 并行窗口（16:25–18:04），recount 结束后自动回落 4 并全程保持；全程序零 swap-in、pswpout 仅一次良性瞬态（+65536 页后冻结）、iowait 恒 0、无 OOM；身份五项（HEAD/binary/workload/3 工具 md5）每 9 分钟核验零漂移；速率 35–53s/rep 全程在基线 42.7s±50% 内；无结果文件串写、无日志覆盖；原始 runs/artifacts/manifests 零改动。

  **本地提交清单**（未 push，按 0101/0201 协调策略）：`65559fa`（运行清单+决策树）、`0244e9c`（FR02 recount 审计+correction overlay，主 agent 独立复核一致）、本提交（终稿收口）。

  **遗留事项**（供用户决策，均不阻塞）：① 归属方 watcher PID 911837 因 B=196<197 永不退出（recount 归属会话处置）；② per-run manifest 无 workload.binary 字段（工具改进项）；③ recount 的 18 条 topup 废行已在 overlay 中 excluded，旧 "390 valid" 口径作废；④ 批次2 subagent A 独立审计结果待返回（返回后追加登记）；⑤ 六模型旧 formal 结果 + 本次四模型新结果均为 untracked artifacts（按纪律不入库，由用户决定提交方式）。
- **[2026-10-10 21:05] D05-b formal 完成并通过统计审计（无需 topup）**：385/385 行、r0000–r0384 无缺无重；Masked 277 + Crash 108 → **n_valid=385 ✓**；faults 385×1（100% 激活）；**P_SDC 0.0% [0.0,1.0]，P_DUE 28.1% [23.8,32.7]**（pilot 30% [16.7,47.9]，CI 内一致），**Reach 100%**；artifacts 已落盘。R03-c ~352/385（91%，ETA ≈21:15）→ 完成后进入全量收口。
- **[2026-10-10 19:11] 批次2 30 条门通过**：D05-b 48 抽样 run 全部最终 f=1（skip-only=0，多行=跳过行+成功行）；R03-c 41 抽样 run 全部 f=1（单行 rename_srcTags 成功日志，phys 标签互换实证，skip-only=0）；批次 2 全部注入日志零无标记行；速率 D05-b ≈36.8s/rep、R03-c ≈44.5s/rep（阈值内）；与两模型 pilot Reach 100% 一致。电池全绿（gem5=4、Mem 24.3G、pswpout 冻结、iowait 0、身份 0244e9c）。
- **[2026-10-10 19:05] subagent A 独立双审计返回：D04c/D04e 双 PASS，主 agent 数字全部复核吻合**（Wilson CI 复算差<1e-12；manifest 身份 770/770 全量吻合；pilot 对照 z 检验均不显著；Crash=exit−6 与 classify.py L220–227 约定自洽）。勘误：r0000 实际在 results.jsonl **第 2 行**（此前"在中部"叙述有误，零统计影响）。两项非阻断观察留档：① per-run manifest 无 workload.binary 字段——binary 身份仅能经 campaign yaml + golden_id 间接钉死（工具改进项，批次边界后可立项）；② 131 个 Crash 全部 exit=-6（SIGABRT），jsonl 不保留 stderr，本次证实的是与分类约定自洽。
- **[2026-10-10 18:59] 批次1 收口通过；批次2 已自动启动**。D04e 审计：385/385 valid（Masked 329 + Crash 56）、385×f=1、P_SDC 0.0% [0.0,1.0]、P_DUE 14.5% [11.4,18.4]（pilot 10% [3.5,25.6]，CI 重叠）、r0000–r0384 无缺无重、无 bad_runs.log。**批次1 汇总：两模型均 385/385 valid、零 Inactive / 零 f≥2 / 零 SimulatorError / 零 Hang、无需 topup、pilot 趋势零不可解释偏移**（D04c P_DUE 19.5% vs pilot 20%；D04e 14.5% vs 10%）。批次2 18:57:33 启动：formal_D05b_depchain driver **1053397**、formal_R03c_depchain driver **1053396**（各 jobs=2、hang 600、独立 .out；yaml 与 pilot 逐字段 diff 仅 4 处预期差异；r0000 种子 20264000/20264500 实证；gem5=4）。subagent A 已派出对 D04c/D04e 做独立双审计（与批次2 并行；若发现问题按单模型隔离处置）。
- **[2026-10-10 18:50] D04-c formal 完成并通过统计审计（无需 topup）**：385/385 行、r0000–r0384 无缺无重（results.jsonl 为完成序非排序序，首行 r0001、r0000 在第 2 行，已 python 全集核验；r0000 位置勘误见 19:05 条目）；分类 Masked 310 + Crash 75 → **n_valid=385 ✓**；faults_injected **385×1**（100% 激活，与 pilot Reach 100% 及 subagent C 预判 skip-only=0 一致；零 Inactive/零 f≥2/零 SimulatorError/零 Hang/无 bad_runs.log）；**P_SDC 0.0% [0.0,1.0]，P_DUE 19.5% [15.8,23.7]**（pilot 20% [9.5,37.3] 一致），**Reach 100%**；wall 8510s。driver 958859 已正常退出。D04-e 剩 ~16 rep（ETA ≈18:55）。
- **[2026-10-10 18:25] FR02 recount 审计完成，独立复核一致，已本地提交**。修正口径（formal 650 全量）：假激活 49 条（45×Masked/1 + 4×Masked/2 全部→Inactive/0，单向翻转）；SDC 45/45、Crash 8/8 零翻转；**n_valid 380→331，P_SDC 11.8%→13.6% [10.3,17.7]，Reach 58.5%→50.9% [47.1,54.7]**；丢行 = topup r0021（种子同 formal r0221=Hang，确定性复现挂起被 timeout 杀，零统计影响）；topup 18 行三重无效全部 excluded，旧 "390 valid" 全局口径作废；L5=n/a。交付 `fr02-recount-audit-2026-10-10.md` + `fr02-correction-overlay-2026-10-10.json`（395 条）。watcher 911837 永不自行退出（B=196<197），留归属方处置。**pswpout 基线更新为 311274**（良性瞬态：recount 末期 ~256MB 冷页被换出后随进程退出释放——计数器累计但水位回满；三次采样冻结、pswpin=0、vmstat si/so=0，不触发降级阶梯）。批次1 进行中：D04c ~306/385（80%）、D04e ~292/385（76%）。
- **[2026-10-10 18:10] recount 完成，动作 (a) 触发**。recount 15:13:35–18:04:50 收口：recount-A.csv = 198/198 满额（零丢行）、recount-B.csv = **196/197（缺 1 行，符合"timeout 行被 grep 静默丢弃"的预判模式，待审计定位缺失 manifest）**。两 worker 进程消失；全机 gem5 自动回落 **4**（实测=4：D04c×2 + D04e×2）。归属方 watcher PID 911837 等待条件 A≥198 且 B≥197——B=196 使其永不触发（归属方进程，不动，已在审计中记录提醒）。D04c ~283/385（74%）、D04e ~272/385（71%），资源全绿。已重派 subagent C 产出 FR02 审计报告 + correction overlay（剔除 18 条 topup 废行）并本地提交。
- **[2026-10-10 17:10] 无人值守模式生效**。批次1 运行中：D04c ~109/385、D04e ~101/385、recount 257/395；17:04 电池全绿（gem5=6、Mem 24.5G、swap 零、iowait 0、身份零漂移）。ETA：recount ≈18:01、D04c ≈18:39、D04e ≈18:40。下一动作：recount 完成 → 审计+overlay+本地提交；批次1 完成 → 统计审计 → 自动启动批次2。
