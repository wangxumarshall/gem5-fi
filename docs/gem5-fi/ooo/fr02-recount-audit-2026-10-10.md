# FR02 重判最终审计报告（faults_injected 假阳性全量重判）

- 日期: 2026-10-10（recount 于 18:04:50 完成最终写入；本报告数据快照 18:05 之后）
- 仓库: /home/sdc/gem5-fi-ding @ `297694f821`（fi-ding）
- 审计对象: `formal_FR02_dcv`（rat · `map_bitflip2_adj_vec` · local_mbu · C3 · dep_chain_vec, n=650）与 `topup_FR02_dcv`（同 cell, n=40）在提交 `297694f`（faults_injected 解析 bug 修复）前后的口径差异
- 重判数据: `/tmp/recount-A.csv`（198 行, half-aa 满额）+ `/tmp/recount-B.csv`（196 行, half-ab 197 任务缺 1）, worker `/tmp/recount-worker.sh`, binary `build/ARM/gem5.opt` sha256 前缀 `1a618953`（修复后构建, 2026-10-10 15:06:42）
- 配套 overlay: `docs/gem5-fi/ooo/fr02-correction-overlay-2026-10-10.json`（395 条逐 run 记录 + 修正统计）
- 纪律: 只读审计。原始 `results.jsonl` 与 manifests 一字节未动；除上述 overlay 与本报告外未写/改任何文件。

---

## 0. 背景与根因（一句话版）

`tools/runner.py:1524-1568` 的注入日志解析把"无 `faults_injected:` 标记的非空行"逐行 +1；修复前 CHAOSRenameMap/CHAOSDecode 的诚实跳过（honest skip）行不带标记 → **从未激活**的运行被记 f=跳过行数（1 条 → 假 f=1 假激活 Masked；≥2 条 → 假 f≥2 G5 VIOLATION）。已激活运行不受影响（修复前成功行已带标记, last-marker-wins 自纠; 机理见 §5）。修复 = 提交 `297694f` 给全部 27 处（RenameMap）/31 处（Decode）日志语句追加计数标记，注入行为零变化。实证: 修复后 mtime 的 362 个 `/tmp/man-*` 日志文件非空行 100% 带标记，0 例外。

## 1. 任务执行与丢行定位

- 任务宇宙 = 395 = formal 非 Inactive 非 Hang 377（650 − 270 Inactive − 3 Hang）+ topup 非 Inactive 18。旧 Inactive 行无需重判（旧 f=0 在两种 binary 下都不可能伪造: 激活必有带标记成功行）；3 条 formal Hang（r0221/r0338/r0467, f=null）按设计不重判。
- **实际执行 394/395**。缺失行: `runs/topup_FR02_dcv/c0000/topup_FR02_dcv-c0000-r0021.yaml`（half-ab 任务在, B.csv 无对应 RESULT 行）。
- **丢行原因（确定性解释, 非臆测）**: worker 用 `timeout 300` + VEC binary 重放该 manifest。其种子 20261821 == formal r0221 的种子（topup base 20261800+21 = formal base 20261600+221, 40/40 种子重叠见 §6）；formal r0221 在同一 VEC binary 下本身就是 **Hang**（旧记录 exit=-1, timed_out=True）。同种子同 binary 的确定性重放同样挂起 → 300s 被杀 → runner 未打印 RESULT → grep 无输出 → CSV 缺行。分类**不猜测**, 按 pending/lost 标注（overlay `change_type=lost-timeout`）。该行本属被排除的 topup 集合, 对统计零影响。
- A∩B 重复 0; A 198/198 满额。

## 2. 逐条 join 翻转矩阵（394 recount 行 vs 旧记录, 按 manifest/run_id）

### 2.1 formal（377/377 全部重判完成）

| 旧 (cls/f) → 新 (cls/f) | 计数 | 判定 |
|---|---|---|
| Masked/1 → Masked/1 | 275 | confirmed（真实激活被掩蔽） |
| SDC/1 → SDC/1 | 45 | confirmed（**零翻转**） |
| Crash/1 → Crash/1 | 8 | confirmed（**零翻转**） |
| **Masked/1 → Inactive/0** | **45** | **fake-activation-flip（假激活）** |
| **Masked/2 → Inactive/0** | **4** | **fake-activation-flip**（r0068/r0426/r0545/r0625, 旧 f=2 全部为假, 真实注入 0） |
| 合计 | 377 | 新 faults 分布: f=1 × 328, f=0 × 49 |

要点:
- **翻转只有一种方向**: 假激活 Masked → Inactive。SDC 45/45、Crash 8/8 零翻转——符合机理: SDC 需要真实注入改变输出哈希, Crash（classify.py 规则 0.5, f≥1 且无 checksum）在真实注入下同样成立; 跳过行伪造不出这两类。
- 旧 f=2 的 4 条全部为假（真实注入 0）, 与提交信息"5 个 FR02 运行被误记 f=2（4 formal + 1 topup）"一致（topup 的 r0014 见 §4）。
- **假阳性率**: 旧 Masked/f=1 中 45/320 = **14.06%** 为假激活; 重判全集 49/377 = 13.00%。

### 2.2 topup（17/18 重判完成, 1 丢行）— 全部无效, 不入统计

| 旧 (cls/f) → 新 (cls/f) | 计数 | 判定 |
|---|---|---|
| Masked/1 → SDC/1 | 10 | excluded-topup |
| Masked/2 → SDC/1 | 1 | excluded-topup（旧 f=2 的 r0014） |
| Masked/1 → Inactive/0 | 5 | excluded-topup |
| Masked/1 → Crash/1 | 1 | excluded-topup |
| （r0021 无行） | 1 | lost-timeout |

### 2.3 与 16:53 中期快照的收敛性

| 桶 | 16:53 快照(230 行) | 最终(377 行) | 增量(147 行) |
|---|---|---|---|
| Masked/1→Masked/1 | 169 | 275 | +106 |
| SDC/1→SDC/1 | 30 | 45 | +15 |
| Masked/1→Inactive/0 | 27 | 45 | +18 |
| Crash/1→Crash/1 | 2 | 8 | +6 |
| Masked/2→Inactive/0 | 2 | 4 | +2 |
| 假激活率 | 29/230=12.6% | 49/377=13.0% | 20/147=13.6% |

各桶单调增长、**无任何桶反转**; 增量假激活率 13.6% 与快照期 12.6% 一致 → 重判过程无漂移, 早期样本代表性成立。我 16:53 的外推（"formal 假激活 ≈44, n_valid≈329"）与最终值（49, 328 激活）误差 <3%。

## 3. §四 报告字段（formal_FR02_dcv, 修正口径）

| 字段 | 值 | 说明 |
|---|---|---|
| attempted | **395 任务 / 394 实际执行** | 1 行 lost-timeout（topup r0021, §1） |
| triggered/activated（新口径 f≥1） | **328 / 650 = 50.5%**（重判集内 328/377） | 275 Masked + 45 SDC + 8 Crash |
| faults_injected 分布（新, 全 650） | **f=0: 319, f=1: 328, f=2: 0, null: 3** | null = 3 条未重判的 Hang; 旧口径为 {0:270, 1:373, 2:4, null:3} |
| Inactive（新） | **319**（270 旧真 Inactive + 49 假激活翻转） | 旧 270 |
| Hang / f=null | **3**（r0221/r0338/r0467, 未重判, 分类不变） | |
| SimulatorError | **0** | |
| **有效 activated 分母（修正后）** | **328**（f≥1 且经修复后 binary 验证）; §1.4 口径 n_valid = 650−319−0 = **331**（含 3 条无法验证激活的 Hang） | |
| L5 分类 | **n/a** | 这些 SE 运行没有 L0–L5 观测链数据, 如实记 n/a, 不虚构 |

**与原报告（artifacts/formal_FR02_dcv/summary.md: n=650, n_valid=380, P_SDC 11.8% [9.0,15.5], P_DUE 2.9% [1.6,5.1], Reach 58.5% [54.6,62.2]）的差异**（Wilson 95% score interval, tools/wilson.py 公式, Z=1.959963984540054; 旧数字经同公式精确复现 11.84% [8.97,15.48]）:

| 指标 | 旧口径 | 修正口径 | 变化 |
|---|---|---|---|
| n_valid | 380 | **331**（§1.4）/ 328（activated） | **−49（−12.9%）** |
| P_SDC | 11.8% [9.0,15.5] | **13.6% [10.3,17.7]**（45/331; activated 分母 13.7% [10.4,17.9]） | +1.8pp, CI 重叠 |
| P_DUE | 2.9% [1.6,5.1] | **3.3% [1.9,5.9]**（11/331） | +0.4pp |
| Reach | 58.5% [54.6,62.2] | **50.9% [47.1,54.7]**（331/650; activated 328/650=50.5%） | **−7.5pp** |

**seed 级异常清单**:
1. topup base_seed 20261800 落在 formal 种子域 [20261600, 20261600+649] 内; **topup r0000–r0039 的种子与 formal r0200–r0239 逐对相同（40/40 程序化验证, rng/trigger/target/fault 全字段一致, 唯一差异 oracle.golden_id）**。
2. topup 原始运行实际用 **INT dep_chain binary + depchainint-golden-v1**（artifacts/topup_FR02_dcv/summary.md 第 5 行）, 与 FR02-dcv cell 的 dep_chain_vec 负载不同 → 原始 40 运行**不是** formal 的字面重复, 但构成同 cell 的 workload 轴混入。
3. recount worker 对 topup manifest 喂 VEC binary → 产生 formal r0200–r0239 的**精确确定性重复**（§4）。
4. 丢行 topup r0021（种子 20261821）确定性复现 formal r0221 的 Hang → 300s 被杀（§1）。

## 4. 18 条 topup 废行处理（全部 excluded, 不进任何统计）

**理由（三重无效）**:
1. **负载错配**: topup manifest 的 golden_id=`depchainint-golden-v1`, 原始运行用 INT binary; recount worker 统一喂 `--binary workloads/ooo/dep_chain/dep_chain_vec` → 跑的是"VEC 负载 + INT golden"的错误组合。
2. **确定性重复**: 种子与故障参数和 formal r0200–r0239 完全一致（§6 异常 1）, VEC binary 重放 = formal 样本的逐位重复执行。**实证 17/17 全部命中确定性映射, 0 错配**: topup rN 的重放 f 与 formal r(200+N) 的新 f 完全一致; 分类按 golden 错配映射精确预测（formal Masked→topup SDC, formal Inactive→topup Inactive, formal SDC→topup SDC, formal Crash→topup Crash）。例: topup r0000/r0006/r0025/r0028/r0030 重放 Inactive 对应 formal r0200/r0206/r0225/r0228/r0230 的假激活翻转; topup r0039 重放 Crash 对应 formal r0239 Crash。
3. **必然误判 SDC**: 激活运行（f≥1）的输出哈希是 VEC 值, 与 manifest 携带的 INT golden（98e5e31e726e383f, runner.py:116）必不相等 → classify.py exact_hash 规则强制 SDC（runner.py:524-552 解析 golden 无 binary 交叉校验）。重判 12 条激活行中 11 条 SDC + 1 条 Crash 全部为该伪影。

**后果**: 旧 topup 的 18 条 "valid"（17 Masked/f=1 + 1 Masked/f=2）**至今未获合法重判, 处于 UNVERIFIED 状态**。修正统计因此只基于 formal; 若需恢复 topup 样本, 须用 INT binary + 原种子重跑（或改用 VEC 负载 + 新种子域重新补样, 并先解决异常 1 的种子重叠）。

## 5. 机理备注（对解读重要）

修复前成功注入行已带 `faults_injected: N` 标记（`git show 297694f~1` 可证）, 因此 last-marker-wins 使"K 条跳过 + 1 条成功"的已激活运行在旧 binary 下也解析为正确的 f=1。**受害集合 = 日志只含无标记跳过行、从未激活的运行**: 恰 1 条跳过行 → 假 f=1（假激活 Masked, 45 条）; ≥2 条 → 假 f≥2（G5 VIOLATION, formal 4 条 + topup 1 条, 全部为假）。这解释了 §2.1 翻转矩阵的单一方向与 SDC/Crash 零翻转, 也是 D04-c/D04-e 等 decode 模式（成功行同样带标记）pilot Reach=100% 预计可原样延续到 formal 的依据。FR02 假激活率 14% 不可外推到 decode 模式: FR02 的机制是"目标架构寄存器窗口内仅被写 1 次且双 bit 翻出 [0,48)"（非目标 reg 守卫静默返回, 单次 OOB 写入 = 恰 1 条跳过行, 结构性高频）。

## 6. 结论与修正后数字（formal-only, 诚实口径）

- **修正后 FR02-dcv（dep_chain_vec）**: n=650, Inactive 319, Masked 275, SDC 45, Crash 8, Hang 3; 激活 328; n_valid 331; **P_SDC 13.6% [10.3,17.7]; P_DUE 3.3% [1.9,5.9]; Reach 50.9% [47.1,54.7]**。
- 旧口径对 Reach 高估 7.5pp（58.5%→50.9%）, 对 n_valid 高估 49（380→331, −12.9%）, P_SDC 被稀释 1.8pp（11.8%→13.6%, CI 重叠, 结论方向不变: FR02 仍为 SDC 主导的单元）。
- topup 18 条 valid 无法修正（§4）, 不得并入修正口径; "formal+topup 390 valid" 的旧全局口径应弃用。
- 原始 results.jsonl / manifests / artifacts 未改写; 全部修正以本报告 + overlay 形式叠加。

## 7. 交接事项

- **watcher PID 911837**（`while … A<198 || B<197 … sleep 30`）: 完成条件含 B≥197, 而最终 B=196（1 丢行）→ **该 watcher 永不自行退出**。按只读纪律本审计未动它; 请归属方手动终止。
- overlay 文件: `docs/gem5-fi/ooo/fr02-correction-overlay-2026-10-10.json`（395 条: confirmed 328 / fake-activation-flip 49 / excluded-topup 17 / lost-timeout 1; 含修正汇总与 Wilson CI）。
- 建议后续（决策属主 agent）: ① topup 如需保留须用 INT binary 合法重判或换 VEC 负载+新种子域重补; ② 未来 topup 种子域避开 formal 域; ③ shared runner.py 解析器加固（退出时强制汇总行）另行统一决策。

## 8. 证据索引（关键命令/文件）

- 任务/结果: `/tmp/recount-half-aa`(198) `/tmp/recount-half-ab`(197) `/tmp/recount-A.csv`(198) `/tmp/recount-B.csv`(196, 18:04:50 最后写入) `/tmp/recount-worker.sh`
- 旧记录: `runs/formal_FR02_dcv/c0000/results.jsonl`(650) `runs/topup_FR02_dcv/c0000/results.jsonl`(40); 旧口径: `artifacts/formal_FR02_dcv/summary.md` `artifacts/topup_FR02_dcv/summary.md`
- 根因代码: `tools/runner.py:1524-1568`(解析) `:1573-1588`(G5/RESULT) `:524-552`(golden 解析); 修复: commit `297694f`（CHAOSRenameMap.cc 10 块 / CHAOSDecode.cc 22 块）; `tools/tests/test_faults_log_contract.py`（复跑 SELFTEST PASS, exit=0）
- 分类规则: `tools/classify.py:126-280`; Wilson: `tools/wilson.py`（Z=1.959963984540054）
- 种子重叠: `runs/topup_FR02_dcv/c0000/*.yaml` vs `runs/formal_FR02_dcv/c0000/*-r02xx.yaml`（40/40 对字段级 diff, 仅 oracle.golden_id 差异）
- 修复后日志实证: `/tmp/man-*`（mtime≥15:06:42 的 362 个日志文件非空行 100% 带标记）
