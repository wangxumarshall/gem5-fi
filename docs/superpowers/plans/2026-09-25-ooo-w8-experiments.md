# OoO W8 实验执行（量产跑批）Implementation Plan

> Spec：docs/gem5-fi/ooo/06-implementation-plan.md §4 W8 + §5 里程碑门 + §9 回填纪律；02-frequency-and-sampling.md 六步流程与样本量；05-expanded-matrix.csv E 行（门=E074/E075/E082/E083）。冲突裁决：00-05 优先。
> 前置：91/91 D 行注入器全部入库（W4-W7.4，HEAD 6990ef2e）；W3.1 两阶段编排入库（campaign.py two_phase，465467ea）；回填工具入库（5e66ebeb）。
> 本计划执行代理不 commit/push（编排者拥有提交权）；不重建 gem5（repo 根 build/ARM/gem5.opt 与 HEAD 一致）。

## 0. 口径裁决（编排者 2026-09-25，诚实记录）

1. **门格子档位被矩阵钉死 F0**（05-matrix E074/E075/E082/E083 行「适用频率」=F0）→ two_phase 用单档 `tiers: [F0]`。工具核实：`campaign.py parse_two_phase` 接受任意非空 F0-F3 子集（`pick_top ≤ len(tiers)` → 1），单档合法，pilot F0×20 → 选档（平凡，F0 必选）→ formal F0×2000。**无需等效路径**（工具原生支持）。
2. **CoreMark 格** = workloads/ooo/coremark/coremark 单二进制，n=2000，golden `coremark-golden-v1`（000000000000cf56），oracle exact_hash。
3. **Embench 格** = W1.2 六程序套件 {crc32, matmult-int, md5sum, minver, nbody, wikisort}，2000 次运行均摊：每程序 ceil(2000/6)=334，共 6×334=2004，套件级分类汇总（回填按 E-id 跨 campaign 聚合，backfill `aggs` 按 E-id 累加，已核实）。golden：`embenchcrc32/-matmult/-md5sum/-wikisort/-nbody/-minver-golden-v1`（runner.py GOLDEN_IDS 全部已注册）。
4. **工具现实（诚实偏差，必须记录）**：campaign.py 是**一 campaign 一 binary**（`workload.binary` 为 campaign 级字段，run_one_rep 对每个 rep 传同一 `--binary`；grid 轴无法切换 binary/golden）。因此「4 个门格」落地为 **14 个 campaign**：E074/E082（CoreMark，n=2000 各一）+ E075/E083 各拆 6 个程序 campaign（n=334 各一）。编排者指令中的单文件 `campaigns/ooo-w81-gate.yaml`（campaign_id=ooo_w81_gate）在此工具约束下不可实现；等效落地为 campaigns/ooo-w81-gate-*.yaml 文件族，campaign_id 统一前缀 `ooo_w81_gate_*`（回填时按 E-id 聚合回 4 格）。
5. **两波发射（gate-check 波先行）**：two_phase 把 pilot→formal 融合在一个进程里，pilot 完成即自动开烧 formal。为满足「pilot 4 格×F0×20 全部完成并复核 SDC 后才允许 formal 燃烧」的门纪律，先跑 **Wave A（gate-check）**：14 个 campaign，`formal_n: 1`（仅作管线贯通样本，永不回填），产出全部 14×20=280 个 pilot 结果（tier_selection.json + pilot_results.jsonl）；门复核通过后再跑 **Wave B（正式）**：同结构 14 个 campaign，`formal_n: 334/2000`。Wave B 的 pilot 与 Wave A 同 seed（seed 规则 base+cell×10M+slot×100K+rep，同 base_seed 同 slot）→ 280 个 pilot 是同 seed 决定论重放，波间分类一致性即免费的 replay-consistency 复核。代价：pilot 双跑（+280 run ≈ +26 min 墙钟）+ Wave A 各 1 个 orphan formal run（永不回填，campaign_id `ooo_w81_gatecheck_*` 不传入 backfill）。
6. **PYTHONHASHSEED=0**：campaign.py 对全部子进程强制（CHILD_ENV forced 0），无需额外设置（编排者 W1.3 要求由此满足）。
7. **D72/D73 合并行别名（编排者裁决 2026-09-25）**：E187/E188（D72）→ 别名 D74（E190/E191）、E189（D73）→ 别名 D75（E192），w85 yaml 的 D72/D73 int 核 stanza 已删除、alias_map 补 2 条（共 7 条）。依据三重：①04 合并条款原文「如果实际是同一套映射，此行与向量行应合并，**不重复跑**」；②03-workloads 规定 FP/SIMD Rename 单元用**向量版**依赖链核（矩阵未限定标签 + 03 规则 ⇒ dep_chain_vec）；③N3 平台事实（AArch64 标量 FP 走 VecRegClass，FloatRegClass 从未被重命名、flFloatMin=192 恒满——「标量FP空闲表」在本平台**就是** vec 空闲表，D72/D73 故障语义落点与 D74/D75 配置完全相同）。字面主义 int 核读法=向近乎静止的 vec 池注入（design-void，构造性 Inactive）且 D73 的池干涸事件大概率永不触发——非真实结果。与 W7.2/3 入库的 merged-rows（09cc506e）同口径；opClass Float* vs SimdFloat* 的归因差异后置 commit trace（W7.2 RAT 同裁决）。
8. **D61 混合负载确认（编排者裁决 2026-09-25）**：「Embench（含整数/浮点混合的程序）」= {nbody, minver}——六程序中唯一保证同时含整数循环/寻址代码与浮点主体的两个（crc32/matmult-int/md5sum/wikisort 纯整数无 FP 可误路由）；各 1000 次均摊。
9. **事件覆盖 n 语义（编排者裁决 2026-09-25，密度代理发现+02 文档核实）**：02 文档事件覆盖计数的统计意图 = n 个**独立事件锚定注入样本**（与 F0「n 即注入实例数」同功效基准）。campaign.py 现公式 `n_runs=ceil(target/density)` 只在稀有事件域（density<1/运行）成立；探针负载实测密度全部 ≥275,648 → 公式坍缩到 n=1（统计上无效）。正确通式 = `ceil(target / min(1, density))`，本平台全部 46 事件覆盖格 = **2000 次运行 × 每 run 1 次事件锚定单射**（每 run 必命中——密度≥1 保证非 Inactive）。**执行约束**：counting 块必须保留（manifest `counting_basis: 事件覆盖计数` 是 backfill E-id 匹配键，campaign.py 冻结期无 yaml-only 改法）——公式补丁（campaign.py 1 行）+ 46 stanza 生效 n 修正是 **Wave B 结束后的一个单元**；三个 yaml 头部已加 LAUNCH GUARD 禁止在补丁落地前启动 W8.2+。测量数据已入库（artifacts/ooo_w8_density/，18 二进制×2 重复全确定性、无零密度格）。
10. **classify 超时判序修复（2026-09-25，d6a72226）**：§2.2 carve-out 原先吞掉「带故障超时击杀」为 Crash（timed_out=True 仍命中 fault∧exit≠0∧无 checksum 分支，先于 Hang 判定）。修复=carve-out 加 `not timed_out`。**对门报告的影响**：Wave A pilot 的「D28 140/140 Crash」应读作 **140/140 Hang**（依赖停摆：destid 翻转→真依赖永不唤醒→ROB 塞满→无前进→600s 击杀；gem5 PRF 模型上 TC'23 依赖拦截表现为停摆而非快速陷阱）。**门判据只看 SDC=0 不受影响**；f3bb6b03 里程碑中的 Crash 表述按本条勘误。修复在 e082 campaign 启动（~00:50）前落地——e074/e075 全 Masked 不经 carve-out，在跑 campaign 行为不变。鲲鹏轨道历史 campaign 的同缺陷为已知边界（前向修复不回溯）。
11. **D28 全 600s 停摆 → Wave B ETA 修正（密度代理吞吐实测，2026-09-25）**：D25 侧 8.45 runs/min（57s/run）但 D28 侧每 run 跑满 600s hang_timeout（Wave A 证据 20/20+20/20 全超时，0.8 runs/min 地板）。Wave B 全波修正预测：D25 侧 ~3,271 run ≈6.5h + D28 侧 ~4,182 run ≈**87h** → **总 ≈94h，ETA ≈9月29日**（非原估 12h）。处置选项（待用户）：(a) 维持 600s 均匀口径慢跑（当前默认）；(b) W8.2+ 量产采用全局 300s hang_timeout 政策（负载正常 ~57s，5.3× 余量；D28 型停摆分类=Hang 与超时值无关）——吞吐外推：W8.2-W8.5 总量 221K-355K run，全快跑 18-29 天、25% 超时混合 ~99 天、全 600s 地板 308 天；300s 政策把 D28 型成本减半。
12. **W8.2+ hang_timeout=300s 全局政策（用户批准 2026-09-25）**：选项 (b) 获批——W8.2 及以后所有量产 campaign 的 hang_timeout 统一 600→300（负载正常完成 ~57s，300s=5.3× 余量；停摆型结局分类=Hang 与超时值无关，判据只更严不更松）。**Wave B 门跑批维持 600s 均匀口径跑完**（门数据一致性优先，改门内参数=方法学漂移）。落地方式：Wave B 结束后的 W8.2 备产单元（campaign.py 公式补丁为独立先行单元）里把 w82-w85 全部 stanza 的 hang_timeout 改 300 并解除 LAUNCH GUARD。W8.2 规模按 M3-gate 机制：M2 过门后先跑 W8.2（Int Rename 47 子 campaign）作吞吐验证批，报告实测预算后再续 W8.3-W8.5。

## 1. W8.1 — M2 门 campaign（E074/E075/E082/E083）★本批次

门定义（06 §5）：D25/D28（F0, CoreMark/Embench, n=2000）须复现 TC'23 SDC≈0%（ROB PC/目的寄存器标识符翻转被依赖检查拦截→Crash 主导）。**SDC>0% = 注入器有错，立即停止，不得继续烧 formal，更不得启动 W8.2+。**

精确 4 格（05-expanded-matrix.csv）：
- E074 = D25（ROB PC 字段单比特翻转）× CoreMark × F0 × 运行计数 2000
- E075 = D25 × Embench × F0 × 2000（六程序均摊 334×6=2004）
- E082 = D28（ROB 目的寄存器标识符字段单比特翻转）× CoreMark × F0 × 2000
- E083 = D28 × Embench × F0 × 2000

注入路由（已核实 runner.py rob 块）：D25 = `fault.model=transient_bit_flip` + `target.sub_field=pc_bitflip` → `--chaos_rob --rob_mode pc_bitflip --rob_target_class int`；D28 = `sub_field=destid_bitflip` → `--rob_mode destid_bitflip`（runner.py:914-924；ooo_proxy.py:583 非 oldphys 分支挂 CHAOSROB rob-insert 位点）。

### Task 1.1: 构造 28 个门 campaign yaml（Wave A gate-check 14 + Wave B 正式 14）
- [x] campaigns/ooo-w81-gatecheck-{e074,e075_<prog>,e082,e083_<prog>}.yaml：campaign_id `ooo_w81_gatecheck_*`，two_phase {tiers: [F0], pilot_n: 20, formal_n: 1, pick_top: 1}，base_seed 20260925，config C3，injector rob，hang_timeout 600。（28 文件已生成）
- [x] campaigns/ooo-w81-gate-{e074,e075_<prog>,e082,e083_<prog>}.yaml：campaign_id `ooo_w81_gate_*`，two_phase {tiers: [F0], pilot_n: 20, formal_n: 334（embench）/2000（coremark）, pick_top: 1}，replay_pct 1.0（见 §4 资源注）。
- [x] grid 轴沿用玩具验证过的形状（runs/ooo_w31_toy_rob_pcbitflip/c0000/*.yaml）：{target_index: [-1], field: [pc|destid], sub_field: [pc_bitflip|destid_bitflip], fault_model: [transient_bit_flip], protection_model: [none]}；campaign 级 ooo 块 {design_unit_id: D25|D28, experiment_cell_id: E074|E075|E082|E083, workload: CoreMark|Embench}。
### Task 1.2: manifest 生成验证（--dry）
- [x] `python3 tools/campaign.py campaigns/ooo-w81-gatecheck-e074.yaml --dry` → 20 个 pilot manifest 落 runs/ooo_w81_gatecheck_e074/c0000/；ooo 块逐字段核对通过（design_unit_id=D25/experiment_cell_id=E074/frequency_tier=F0/phase=pilot/counting_basis=运行计数 + target.sub_field=pc_bitflip + limits.max_faults=1 + oracle.golden_id=coremark-golden-v1）。
- [x] D28 Embench（ooo-w81-gate-e083_matmult-int.yaml --dry）核对通过（sub_field=destid_bitflip, golden_id=embenchmatmult-golden-v1, D28/E083/Embench）。
### Task 1.3: 1-run 真机采样（管线贯通）
- [x] 手工跑 e074 pilot p0000：`python3 tools/runner.py runs/ooo_w81_gatecheck_e074/c0000/...yaml --binary workloads/ooo/coremark/coremark` → `RESULT: classification=Masked faults_injected=1 exit=0`（checksum==golden 000000000000cf56）；注入日志 fired：`Tick: 73150, Site: rob_insert, mode=pc_bitflip, old_pc=0x400d00, new_pc=0x200400d00, bits=(33), hamming=1, faults_injected: 1`。
### Task 1.4: Wave A nohup 启动（gate-check）
- [x] 启动前 free available=21GB（≥8GB → --jobs 8）；无并行 gem5 进程。启动记录：`nohup bash runs/ooo_w81_gate/driver_waveA.sh > runs/ooo_w81_gate/driver_waveA.log 2>&1 &` **driver PID 706118，2026-09-25T10:06:50+08:00**，sweeper PID 706120（/tmp man-* mmin+20 每 5 min 清扫）；14 campaign 顺序：e074 → e075_crc32 → e082 → e083_crc32 → e075×5 → e083×5。
### Task 1.5: 门复核（pilot 4 格 × F0 × 20 全部完成后）
- [x] 读 14 个 artifacts/ooo_w81_gatecheck_*/tier_selection.json + runs/*/c0000/pilot_results.jsonl，逐格统计 SDC/Crash/Masked/Hang/Inactive/SimulatorError，引用真实输出。〔编排者亲测 2026-09-25 16:41（兜底 cron 接管；代理 watcher 触发后 20+ 分钟未见行动）：**14/14 格 280/280 行，SDC=0/280**；D25（E074+E075×6）140/140 全 Masked；D28（E082+E083×6）140/140 全 Crash（跨 7 负载完全确定性=依赖检查拦截机制复现）；tier_selection.json 14/14 齐、全部 tiers=[F0] 单档；Hang/Inactive/SimulatorError 全 0。D25 全 Masked=gem5 PRF-commit 结构掩蔽（W5 D32/33 平台属性），门判据只看 SDC≈0%——**pilot 级 M2 门通过**。〕
- [x] **判据：任一 (cell×program) pilot SDC>0 → 立即 kill 全部 campaign 进程，报告门失败（注入器有错），不启动 Wave B。** 全 SDC=0 → 启动 Wave B。〔SDC=0/280 → 启动条件满足〕
### Task 1.6: Wave B nohup 启动（正式）
- [x] nohup 驱动脚本顺序跑 14 个正式 campaign（--jobs 8）；验证前 ~10 个 formal run（手工以同 manifest 跑 runner.py 或读早期 artifacts）分类合理、注入 fired（fired_lines≥1；零注入样本须以 Inactive 可见，不得静默）。〔**编排者启动 2026-09-25 16:45:41，driver PID 755642**（nohup bash runs/ooo_w81_gate/driver_waveB.sh > driver_waveB.log；清扫器 755644；free available=21GB；e074 campaign PID 755653 跑中；replay_pct=1.0）。**协调注记（给 W8.1 代理）：Wave B 已由编排者启动——苏醒后勿双启动 driver_waveB.sh**；你的剩余职责=波间一致性复核（Wave B 各 campaign pilot 的 tier_selection class_counts vs Wave A 同 seed 逐格比对）+ formal 进度监控（预计 ~12h，~04:45 完成）。前 10 formal run 分类/注入核验由编排者在首批 formal 落地后执行。〕
- [ ] 波间一致性：Wave B 各 campaign pilot 的 tier_selection.json class_counts 与 Wave A 逐格比对（同 seed 决定论，不一致=发现，如实记录）。
### Task 1.7: 门判读与交付（formal 完成后）
- [ ] 4 格 formal 汇总（E075/E083 套件级 2004）：SDC 计数必须为 0；0/2000 的 Wilson 95% CI 上界引用（0/2000 → 上界 ≈0.18%；rule-of-three 3/n=0.15%）；Crash 主导（TC'23 复现）与 Masked/Hang/Inactive 占比如实报告；任一格 SDC>0（哪怕 1/2000）= 门失败，停止并报告。
- [ ] n_valid ≥2000（E074/E082）/≥2004（E075/E083 套件）核对；SimulatorError 计数单列（非有效 FI 结局）。
- [ ] 回填演练：`python3 tools/backfill_expanded_matrix.py --campaign runs/ooo_w81_gate_e074 runs/ooo_w81_gate_e075_* ... --matrix docs/gem5-fi/ooo/05-expanded-matrix.csv --dry-run`（只回填 n_valid 达标格；Wave A gatecheck 目录**永不**传入）。
- [ ] 产物清单交编排者 commit：28 yaml + runs/artifacts 两个目录 + 本计划 checkbox 勾选。

## 2. W8.2 — Int Rename 格群（D11-D24 → E 格，M3 门）

- [ ] 前置：M2 门通过（06 §5：M2 未过不得启动量产批次）。
- [ ] 格集：05-matrix 中 D11-D24 的全部非 deferred E 格（含 merged 行口径 D72-D77 之外的 int 族；RAT/FreeList/historyBuffer 注入器，runner rat/freelist 路由）。
- [ ] 每格流程（02 doc 六步）：适用频率含 F0-F3 的格 pilot tiers [F0,F1,F2,F3]×20 → 选非 Crash 占比最高 2 档 → formal 2000/档；F5/事件触发行按行内钉死语义（F5 用卡死模式、事件行用 counting event_coverage 密度倒推）。
- [ ] 验收：每格 n_valid+Wilson CI（campaign heatmap/summary）+ backfill 回填 7 列 + campaign 结果 commit（编排者）+ 异常清单（SimulatorError/冻结格/Inactive 率异常格逐条列出）。

## 3. W8.3 — Int Dispatch/ROB 格群（D25-D55 减门 4 格，M4 门）

- [ ] 格集：D25-D55 全部 E 格减去 W8.1 已完成的 E074/E075/E082/E083（PC/标识符双比特、卡死、换值、done 位、old-phys、指针族、IQ ready/tag、分发路由；rob/iq/rename(oldphys) 路由）。
- [ ] D55 分发路由行按 W5.12 honest-approximation 口径跑（或 blocker 如实记录）。
- [ ] 流程/验收同 W8.2（六步 + n_valid + CI + 回填 + commit）。

## 4. W8.4 — Int Decode 格群（D01-D10）

- [ ] 格集：D01-D10 全部 E 格（opcode/寄存器号/立即数/符号扩展/子字段/裂解控制；decode 路由，非法编码→SIGILL Crash 是预期基线）。
- [ ] 流程/验收同 W8.2。

## 5. W8.5 — FP/SIMD 三单元格群 + D83-D85 三关自检第二/三关（M5 门）

- [ ] 格集：D56-D91（merged 行口径：D62-66→vec 族、D72/73/76→D74/75/77）；SVE 谓词行 D78-D82 默认 deferred（06 §1.3，不混入 920 口径）。
- [ ] **三关自检第二/三关**：D83-D85（FP 负载重跑 ROB 基线格与高 SDC 格）须复现 FP 负载一致性（06 §1.2 三关自检记录交付）。
- [ ] 流程/验收同 W8.2。

## 6. W8.6 — 深挖档（仅论文级关键格）

- [ ] 仅对 W8.2-W8.5 中论文级关键结论格加测 16,587（1% 误差/99% 置信）；候选由元分析初筛决定，其余格不烧。事件覆盖不足的格优先换自设探针负载（02 doc 既定方案），不硬烧空转运行。

## 7. W8.7 — 非 Masked 样本 L1/L2/L3 重放遍

- [ ] 对 W8.2-W8.5 的非 Masked 样本（SDC/Crash/Hang）同 seed 带 --ctrace 重放：L2 五分类（commit_diff 五类+潜伏期 latency_seq）、L3 扇出（fanout.py liveness 上界代理）；L1 微架构快照（micro_diff）按 A4 采样口径。
- [ ] trace 不可用/截断的样本如实记 l2_error/l3_error，不伪造。回填潜伏期/污染扇出两列。

## 8. 资源纪律（全批次）

- 槽位：SE O3 单 gem5 ~1-2GB；宿主 29GB/126 核。campaign --jobs 8 起步；每波启动前复核 `free -g` available，<8GB 降 --jobs 6；OOM 屠批禁令（FS 4-slot 教训同源）。
- 断点续跑：campaign 产物按 per-rep manifest 落盘；进程被杀后已完成 campaign 的 artifacts 完整，重跑=重发该 campaign（two_phase 无中途续跑，接受 pilot 重跑成本，如实记录）。
- /tmp：gem5 outdir（man-*）每 run ~0.6MB、全程 ~9000 run ≈5GB；/tmp 现余 8.1GB。驱动脚本内嵌清扫循环（`find /tmp -maxdepth 1 -name 'man-*' -mmin +20 -exec rm -rf {} +`，每 5 min；单 run ≤630s，20 min 龄目录必为已完成 run，不误伤并行会话的在跑目录）。
- 持久化：全部量产用 nohup 驱动脚本后台跑（活过会话）；日志不入仓库根（落 runs/ooo_w81_gate/）。
- 并行会话：另一代理在跑 ctrace 验证（少量 gem5）；启动前后 ps+free 复核，避免撞车。

## 9. replay_pct 裁决（诚实记录）

Wave B 用 replay_pct: 1.0（非默认 5）：two_phase 的 replay 一致性复核在驱动进程内**串行**执行，5%×2000=100 次/格串行重放 ≈88 min/格（仅 CoreMark 两格即 +3h 串行尾巴）。1% → CoreMark 20 次/格、Embench 3 次/格，串行尾巴 ~1h。决定论证据不缺失：Wave A/B 同 seed pilot 重放（280 run）提供远强于 100 次 replay 的一致性复核，另 Wave A 每 campaign 自带 1 次 replay 检查。

## 10. M2 门判读标准（判据，不许漂移）

- **早期门信号**：Wave A pilot（14×20）任一 (D×workload×program) SDC>0 → kill 全部、报告门失败、回修注入器。pilot 永不入结果列（本判读是过程门，不是结果）。
- **formal 门判读**：4 格（E075/E083 套件级聚合）formal SDC 计数 = 0 → 门通过；引用 Wilson 95% CI 上界（0/2000 → [0, 0.18%]；0/2004 套件同量级）作为「SDC≈0%」的量化表述。任一格 SDC ≥1 → 门失败（1/2000 点估计 0.05% 虽小，但 TC'23 预期是被依赖检查完全拦截，任何 SDC 都是注入器实现可疑信号，按编排者红线处理：停、报告、不得继续）。
- **预期形态**（TC'23）：Crash 主导；Masked/Hang/Inactive 占比如实报；SimulatorError 单列（工具破裂，非 FI 结局）。

**通用**：代理不 commit/push；不 scons；不跑 W8.2+ 量产格（M2 门通过前）；报告只引用真实命令输出。
