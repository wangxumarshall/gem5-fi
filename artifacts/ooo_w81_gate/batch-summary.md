# W8.1 批次小结（FINAL — 全部数据为 formal 实测）

> 状态：草稿（编排者 2026-09-26）。Wave B 双车道（driver_waveB3, 24 jobs/车道）完成后
> 由完成协议填充 D28 数据并随 W8.1 数据单元提交。所有 D25 数字为回填 dry-run 真实输出。

## 1. 批次范围与执行

- **4 门格**（05-expanded-matrix.csv）：E074（D25 ROB PC 字段×CoreMark）、E075（D25×Embench 六程序套件）、E082（D28 ROB dest-id×CoreMark）、E083（D28×Embench 套件），各 F0、n=2000（套件 334×6=2004）。
- **执行结构**：Wave A gate-check（14 campaign，pilot-only formal_n:1，280 pilot 行）→ 门审 → Wave B formal。Wave B 双车道 24 jobs（RSS 实测 96MB/gem5；D28 停摆吞吐=jobs/600s=2.4/min/车道）。
- **分类器**：d6a72226 修复后口径（超时击杀→Hang）；Wave A pilot 的 D28「Crash」按裁决 10 勘误读作 Hang。
- **波间一致性**（同 seed 决定论）：7/8 IDENTICAL + 1/8 预期 DIFFERS（e082: Crash×20→Hang×20 = 分类器修复的干净隔离证据）。

## 2. 结果表（formal）

| 格 | D 行 | 负载 | n | Masked | SDC | Crash | Hang | 传播轴 propagated% |
|---|---|---|---|---|---|---|---|---|
| E074 | D25 pc_bitflip | CoreMark | 2000 | 2000 | 0 | 0 | 0 | 0.00 [0.00,0.19] |
| E075 | D25 pc_bitflip | Embench×6 | 2004 | 2004 | 0 | 0 | 0 | 0.00 [0.00,0.19] |
| E082 | D28 destid_bitflip | CoreMark | 2000 | 0 | 0 | 0 | 2000 | 100.00 [99.81,100.00] |
| E083 | D28 destid_bitflip | Embench×6 | 2004 | 0 | 0 | 0 | 2004 | 100.00 [99.81,100.00] |

Wilson 95% CI 由 backfill 工具计算（0/2000 → [0.00,0.19]；注：rule-of-three 3/n=0.15%，Wilson 精确值 0.19%）。

## 3. 与 TC'23 基线的对比（裁决 13 口径：偏离=平台发现）

| 项 | TC'23 报告 | 本平台实测 | 解读 |
|---|---|---|---|
| ROB 翻转 SDC | ≈0%（图 3，Armv7/Armv8 一致） | D25 侧 0/4004；D28 侧〔待填〕 | SDC≈0 复现成立（注入器正向控制已独立验证） |
| 拦截机制 | commit 前依赖检查失败→Crash（快速陷阱） | D25：100% Masked（PC 字段=commit 路径不消费的元数据，结构掩蔽）；D28：100% Hang（依赖停摆：错 dest id→真依赖永不唤醒→ROB 满→600s 击杀） | **机制层面双重偏离**：gem5 O3 PRF 模型无 TC'23 描述的快速依赖检查陷阱；拦截以「结构掩蔽」（D25）与「停摆」（D28）两种形态出现 |
| 传播轴 | — | D25 propagated=0（纯掩蔽）；D28 propagated=〔待填：Hang 属传播后被捕获/停摆〕 | silent-vs-caught = 检测覆盖率差异；D28 的停摆=依赖拦截在无陷阱模型上的表现 |

## 4. 注入器正确性（正向控制，裁决 13）

证据日志可复算（old/new/bits 逐例核对，W5/W7.4 各批次）；同 seed 复现字节一致（波间 7/8 IDENTICAL + e082 的分类语义差异干净隔离）；golden 无注入回归（45737cc9a76c0dce 恒定）；L2 trace 链路验证（W7.4 ctrace 闭环）。**门判读：注入器正确性成立；TC'23 对比=基线报告，机制偏离作为平台发现记录。**

## 5. 诚实边界

- D28 全 600s 停摆 → 每格 2000×600s/24 jobs ≈ 13.9h 纯墙钟（Wave B ETA 9/27 ~01:30）。
- 潜伏期/污染扇出列：全 Masked/全 Hang 格无 L2/L3 重放数据 → 回填为 n/a（审计 G1 允许显式 n/a；完成协议须核验 backfill 实际写入值非空）。
- **Hang 类 L2 实证（2026-09-26 预实验）**：D28 停摆样本 ctrace=0 字节（故障冻结按序 commit 于首次 gzflush 边界前）→ L2=presence 级（run_instructions=0，②指令流改变 presence）。W8.7 对停摆类的 L2 价值=证明「run 侧无产出」，五分类细分不适用。
- Wave A orphan formal 探针（formal_n:1 的 14 个 run）永不入回填。
- 本批数据生成期间 classify 修复（d6a72226）中途落地：e074/e075 全 Masked 不经修复路径（零影响）；e082/e083 formal 全程修复后口径。

### 5.5 数据完整性检查（完成协议必做，2026-09-26 外部构建并发事件后新增）

- **D28 格 Crash 计数必须=0**（pilot/formal 全部证据表明 D28=确定性停摆；**OOM 击杀的 gem5 会被误分类为 Crash**——exit≠0+无checksum+非超时命中 carve-out）。任何 Crash>0：①查 dmesg OOM 窗口 ②按 seed 确定性重跑涉事 rep 比对 ③确认 OOM 污染则该 rep 按重跑结果修正并在小结记录。
- 事件背景：2026-09-26 12:58 哨兵捕获 available 9G（并行会话 lsu 构建 ld 8GB 峰值与我方 96 路重叠，swap 4G）；13:00 ld 退出，全程零 OOM 零污染（dmesg 核实）。

## 6. 后续动作（固定队列）

公式补丁提交 → iq sampling 修复提交 → w82 备产就绪（300s+解除 GUARD）→ W8.2 量产启动（47 子 campaign，24 jobs 参考并行度）→ 吞吐预算报告。
