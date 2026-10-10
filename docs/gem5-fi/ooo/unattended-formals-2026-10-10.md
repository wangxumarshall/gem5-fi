# 无人值守推进：OOO 四模型 formal + FR02 recount 审计（2026-10-10 启动）

> 本文件是"休息日无人值守推进模式"（用户 2026-10-10 授权）的**运行清单与阶段日志**，是会话中断后恢复的权威入口。
> 决策树全文以用户当日指令为准；本文件是其可执行摘要 + 状态登记。主 agent 是唯一 campaign 调度者；subagent 只监控/审计/分析。

## 运行清单（Run Registry）

| 任务 | 身份 | PID/PGID | 日志/输出 | 恢复命令 |
|---|---|---|---|---|
| FR02 recount（**归属其他会话，勿动**） | /tmp/recount-worker.sh ×2；任务表 /tmp/recount-half-aa(198)/half-ab(197)；输出 /tmp/recount-{A,B}.csv | 911793 / 911794 | /tmp/recount-{A,B}.csv（完成信号 = 两 worker 进程消失；CSV 可能静默丢 timeout 行） | 不适用（禁终止/重启/修改） |
| formal_D04c_depchain | decode src_swap，base_seed 20263000，n_per_cell 385，hang 600，replay 0，C3/SE/workloads/ooo/dep_chain/dep_chain，golden depchainint-golden-v1 | 958859 / PGID 958859（16:25:35 启动） | /tmp/ooo-pipeline/formal_D04c_depchain.out；runs|artifacts /formal_D04c_depchain/ | `cd /home/sdc/gem5-fi-ding && setsid nohup python3 tools/campaign.py /tmp/ooo-pipeline/formal_D04c_depchain.yaml --jobs 2 > /tmp/ooo-pipeline/formal_D04c_depchain.out 2>&1 < /dev/null &` |
| formal_D04e_depchain | decode x0_sub，base_seed 20263500，其余同上 | 958858 / PGID 958858 | …/formal_D04e_depchain.out | 同上，换 formal_D04e_depchain.yaml |
| formal_D05b_depchain（批次2 待启动） | decode imm_rotate / local_mbu，base_seed 20264000 | — | — | yaml 已预写 /tmp/ooo-pipeline/formal_D05b_depchain.yaml |
| formal_R03c_depchain（批次2 待启动） | rat src_tag_swap / field map / width 7，base_seed 20264500 | — | — | yaml 已预写 /tmp/ooo-pipeline/formal_R03c_depchain.yaml |
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

- **[2026-10-10 18:25] FR02 recount 审计完成，独立复核一致，已本地提交**。修正口径（formal 650 全量）：假激活 49 条（45×Masked/1 + 4×Masked/2 全部→Inactive/0，单向翻转）；SDC 45/45、Crash 8/8 零翻转；**n_valid 380→331，P_SDC 11.8%→13.6% [10.3,17.7]，Reach 58.5%→50.9% [47.1,54.7]**；丢行 = topup r0021（种子同 formal r0221=Hang，确定性复现挂起被 timeout 杀，零统计影响）；topup 18 行三重无效全部 excluded，旧 "390 valid" 全局口径作废；L5=n/a。交付 `fr02-recount-audit-2026-10-10.md` + `fr02-correction-overlay-2026-10-10.json`（395 条）。watcher 911837 永不自行退出（B=196<197），留归属方处置。**pswpout 基线更新为 311274**（良性瞬态：recount 末期 ~256MB 冷页被换出后随进程退出释放——计数器累计但水位回满；三次采样冻结、pswpin=0、vmstat si/so=0，不触发降级阶梯）。批次1 进行中：D04c ~306/385（80%）、D04e ~292/385（76%）。
- **[2026-10-10 18:10] recount 完成，动作 (a) 触发**。recount 15:13:35–18:04:50 收口：recount-A.csv = 198/198 满额（零丢行）、recount-B.csv = **196/197（缺 1 行，符合"timeout 行被 grep 静默丢弃"的预判模式，待审计定位缺失 manifest）**。两 worker 进程消失；全机 gem5 自动回落 **4**（实测=4：D04c×2 + D04e×2）。归属方 watcher PID 911837 等待条件 A≥198 且 B≥197——B=196 使其永不触发（归属方进程，不动，已在审计中记录提醒）。D04c ~283/385（74%）、D04e ~272/385（71%），资源全绿。已重派 subagent C 产出 FR02 审计报告 + correction overlay（剔除 18 条 topup 废行）并本地提交。
- **[2026-10-10 17:10] 无人值守模式生效**。批次1 运行中：D04c ~109/385、D04e ~101/385、recount 257/395；17:04 电池全绿（gem5=6、Mem 24.5G、swap 零、iowait 0、身份零漂移）。ETA：recount ≈18:01、D04c ≈18:39、D04e ≈18:40。下一动作：recount 完成 → 审计+overlay+本地提交；批次1 完成 → 统计审计 → 自动启动批次2。
