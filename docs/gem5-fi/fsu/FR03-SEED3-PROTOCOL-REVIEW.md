# FR03-F5-W3 seed3 协议复核（第二轮 R1）

> 复核对象：`runs/fsu/FSU-FR03-F5-W3/seed3/attempt-1` 与 `attempt-2`。
> 复核只读磁盘证据，未修改 `runs/`、未改索引、未重跑 gem5。
> 机器可读建议：`/tmp/fr03_seed3_protocol_review.json`（由主 agent 移入证据目录）。
> 当前工具重算：`tools/fsu_chain_check.py`（2026-11-04 工作树版本）。

## 0. 结论（先给事实）

1. **attempt-1 是真实结局，不是模拟器失败**：程序完整执行（exit 0、ARRAYHASH 输出、15/15 证据哈希匹配、gzip EOF 完整、事件身份无越界），故障确实激活过（generation 3 与 6 的写 exposure 值被改变），但**最终提交路径上的 generation 8 从未被故障改变**。逐 fault 链审计因此诚实地拒绝认证。run-level oracle = `Masked`。
2. **attempt-2 是改变实验目标后的重跑**：目标从 `lane0 bits 15..22 (0x007f8000) SA0` 改为 `lane0 sign (0x80000000) SA1`。这次改目标发生在看过 attempt-1 结果之后（配置 mtime 02:42:06 > attempt-1 失败 02:40；attempt-2 manifest 02:46:22），manifest 的 `revision_note` 自己写明新目标是为了 “guaranteed activation”。因此它是 **protocol deviation / supplemental evidence**，不是原预注册 seed3。
3. 不能用“重新预注册”消除“已经看过前次结果”的事实。attempt-2 的 SDC/认证结果可以作为补充证据保留，但不能替代 attempt-1 作为 seed3 的正式结果。
4. **计数建议：`FSU-FR03-F5-W3` 从 3/3 降为 2/3**（只计 seed1、seed2；seed3 保留 attempt-1 的未认证真实结局，attempt-2 标为补充证据）。本次复核不改索引、不改 `AUTHORITATIVE`。

## 1. 时间线

| 时间（2026-11-04, +0800） | 事件 | 证据 |
|---|---|---|
| 01:12:33 | commit `b365cee5` 提交 seed3 配置：`0x007f8000` SA0 lane0 | `git log -p -- configs/fsu/FSU-FR03-F5-W3-seed3.json` |
| 02:24:13 | FR03 W3 非正式 gate v3 产物完成 | `runs/fsu-gates/F5-FR03-W3-GATE-v3/` |
| 02:39:35 | attempt-1 manifest 创建（原预注册目标） | `attempt-1/manifest.json: created_at` |
| 02:40 | attempt-1 `.failed`：`oracle=Masked ... admitted_faults=[]` | `attempt-1/.failed` |
| 02:42:06 | 配置文件 mtime 变为 `0x80000000` SA1（**在 attempt-1 结果之后**） | `stat configs/fsu/FSU-FR03-F5-W3-seed3.json` |
| 02:42:12 | 非正式 `LANE0-SA1` gate pilot 开始（新目标） | `runs/fsu-gates/F5-FR03-W3-LANE0-SA1-GATE/.../manifest.json` |
| 02:43:15 | pilot `.done`：SDC、chain admitted/certified、terminal full | 同上 `.done` / `chain_report.json` |
| 02:46:22 | attempt-2 manifest 创建（新目标 + revision_note） | `attempt-2/manifest.json: created_at` |
| 02:47 | attempt-2 `.done`：admitted、SDC | `attempt-2/.done` / `oracle.json` |
| 03:49:17 | commit `40f2db5d` 记录改后的配置与 revision_note | `git log -p -- configs/fsu/FSU-FR03-F5-W3-seed3.json` |

关键补充：`LANE0-SA1` pilot 与正式 attempt-2 的 `inject/prop_evt.txt.gz` SHA-256 **完全相同**
（`1bf5bd61a96124fc2fe9730fc1fcacf76f8c3890428934aae739438e0c25fb21`）。
这说明新目标是先 pilot、再确定性重跑，而不是原目标的继续。

## 2. Manifest 完整 diff（attempt-1 → attempt-2）

```diff
--- attempt-1/manifest.json
+++ attempt-2/manifest.json
@@ -17,7 +17,7 @@
   "injector": {
     "component": "physreg",
-    "fault_mask": "0x007f8000",
+    "fault_mask": "0x80000000",
@@ -28,7 +28,7 @@
       "vec_lane_width": 32,
       "vec_lane_offset": 0,
-      "fault_type": "stuck_at_zero",
+      "fault_type": "stuck_at_one",
@@ -44,17 +44,18 @@
-    "mask": "0x007f8000",
-    "polarity": 0,
-    "fault_type": "stuck_at_zero"
+    "mask": "0x80000000",
+    "polarity": 1,
+    "fault_type": "stuck_at_one",
+    "revision_note": "attempt-1 used fixed mantissa 0x7f8000 SA0 lane0. It
+     activated only in generations 3/6; the generation-8 value that committed
+     was never changed by the fault, so the chain audit honestly refused full.
+     attempt-1 is kept as a failed pre-registration. attempt-2 freezes sign SA1
+     lane0 BEFORE the run: it is a target with guaranteed activation on these
+     strictly positive results, not a post-hoc search for SDC."
-  "notes": "FR03 formal seed3: ... fixed mantissa bits 15..22, SA0 ..."
+  "notes": "FR03 formal seed3 (attempt-2): ... lane0 sign SA1 ..."
@@
-  "attempt": 1,
-  "created_at": "2026-11-04T02:39:35",
+  "attempt": 2,
+  "created_at": "2026-11-04T02:46:22",
```

未变化的身份字段：`run_id=FSU-FR03-F5-W3`、`model_id=FR03`、`unit=FSU Pipe`、
`freq=F5`、`submodel=FR03`、`config_family=C3`、`config_profile=B0`、
`workload.*`（binary/identity/golden）、`max_faults=1`、`first_clock=0`、
`probability=1.0`、`reg_class=vector`、`target_phys_idx=0`、
`require_allocated=true`、`vec_lane_width=32`、`vec_lane_offset=0`、
`source_head=f7473c54...`、`gem5_sha256=04be57c3...`、`workload_sha256=d8b01bc0...`。

## 3. 配置变更与冻结时间

当前 `configs/fsu/FSU-FR03-F5-W3-seed3.json`（mtime `02:42:06`）相对
`b365cee5` 的差异与上面 manifest diff 同构：`fault_mask`、
`physreg_mode.fault_type`、`pre_registration.mask/polarity/fault_type`
全部改变，并新增 `pre_registration.revision_note` 与新的 `notes`。
该配置直到 `40f2db5d`（03:49:17）才进入 git；运行时的 `source_head`
仍是 `f7473c54`，说明改动当时只在工作区。

- 原配置在 `f7473c54` 中也存在且内容为 `0x007f8000` SA0（attempt-1 一致）。
- attempt-1 manifest 的 `pre_registration` 与旧配置一致；attempt-2 manifest
  的 `pre_registration` 与新配置一致。两份 manifest 都没有记录“配置在运行前
  被改过”之外的解释，只有 `revision_note` 明说改目标的原因。

## 4. 四象限（必须分开看）

| attempt | execution_completed | evidence_valid | activated | chain_certified | run-level oracle |
|---|---|---|---|---|---|
| attempt-1（原目标 fixed mantissa SA0） | 是（exit 0，ARRAYHASH 输出） | 是（15/15 SHA 匹配，gzip EOF 完整，identity 无违规） | **是**（generation 3、6 的写 exposure；`first_activated_sn=9538`） | **否** | `Masked`（ARRAYHASH == golden） |
| attempt-2（改目标 sign SA1） | 是（exit 0，ARRAYHASH 输出） | 是（15/15 SHA 匹配，gzip EOF 完整，identity 无违规） | 是（install + generation 2/4/5；install 激活无 `dyn_inst_seq`，`first_activated_sn` 为空/`n/a`） | **是** | `SDC`（ARRAYHASH != golden） |

> “activated” 不等于 “chain_certified”。attempt-1 的 activated 写发生
> 在 generation 3/6，但当前 checker 选出的直达 L5 路径经过 generation 8；
> generation 8 的 committed 值 `0x3e800000` 在目标 mantissa mask 上没有任何位
> 被改变，因此 `activation_chain_not_through_first_activated`。

## 5. attempt-1 明细（当前工具重算）

- `execution_completed`：`run.out` 输出 `ARRAYHASH=cb66197d...`，`oracle.json`
  `returncode=0`、`timed_out=false`。
- `evidence_valid`：`evidence_sha256.json` 15 个文件全部存在且哈希匹配；
  `prop_evt.txt.gz` / `prop_trace.csv.gz` gzip 可完整解压；事件
  `run_id/sample_run_id` 全部为本 seed。
- `activated` generation：**3、6**（`phys_write` 事件 `event_id=9`、
  `event_id=54`，`activated=1`）。
- `first_activated_sn`：**9538**。
- L5：**2,040** 条真实 `commit` 事件，**3** 条 `squash` 事件；`chain_end`
  记录 `commit_events=2040`、`squash_events=3`、`read_exposures_total=65554`、
  `write/exposures_total=8`。
- committed 路径 generation：**8**（2,030/2,040 条 commit 在 gen8；gen3–gen7 各 2 条）。
  gen8 的 committed 写 `0x3e800000` 未被故障改变。
- terminal：
  - 归档 `attempt-1/chain_report.json`：`admitted=false`、`certified=false`，
    violation `activation_chain_not_through_first_activated`，但 fault terminal
    仍写着 `full`。
  - **当前 `tools/fsu_chain_check.py` 重算**：`admitted=false`、`certified=false`，
    terminal **`exposed_unconsumed`**，violation 同上，L5 witness event id 6171。
  - 归档报告的 `full` 已过期且与自身 admission 失败矛盾；当前工具为权威，
    不影响“未认证”结论。
- oracle：`Masked`。

## 6. attempt-2 明细（当前工具重算）

- `execution_completed`：是（exit 0，ARRAYHASH `3600cd47...`）。
- `evidence_valid`：是（15/15 SHA 匹配，gzip 完整，identity 无违规）。
- `activated` generation：install（event 0）+ **2、4、5**；gen3 写未改变值。
  `first_activated_sn`：空/`n/a`（install 激活没有 `dyn_inst_seq`；不要把它
  与 attempt-1 的 9538 混用）。
- L5：**2,045** 条 commit、**1** 条 squash；committed 路径 generation **5**。
- terminal：`full`；`chain admitted=true`、`certified=true`。
- oracle：`SDC`。
- 与 `LANE0-SA1` pilot 的 `prop_evt` SHA-256 完全相同（见 §1），证明这是
  同一新目标的确定性重跑。

## 7. 判定：实现修复后重跑，还是改变目标的新实验？

**结论：改变目标的新实验（protocol deviation / supplemental evidence），
不是“实现修复后按原目标重跑”。**

依据：

1. 变更的是**实验目标本身**（bit field + polarity：mantissa 15..22 SA0 →
   sign SA1），不是 runner/注入器实现路径、也不是同一目标的证据修复。
2. 变更发生在 attempt-1 的结果之后，且 manifest `revision_note` 明确说新目标
   是为“guaranteed activation”选的；这属于结果驱动（result-driven）。
3. 新目标先有 02:42–02:43 的非正式 pilot，再有 02:46 的正式 attempt-2；
   pilot 与正式 attempt-2 的 `prop_evt` 字节相同。
4. 原目标并未因模拟器失败而无法执行：attempt-1 完整执行、证据有效、真实激活，
   只是“激活的 generation 没有决定最终提交值”，oracle 为 `Masked`。这是
   一个合法但未认证的真实结局，不是实现 bug。

因此：

- attempt-1 = **真实但未认证的 seed3 结局**（保留，不删除，不补造 `full`）。
- attempt-2 = **补充证据**（SDC、链路认证，但目标不同；可另立新实验记录）。
- 重新预注册不能消除“已经看过 attempt-1 结果”的事实；它只能把偏离记录清楚。

## 8. 计数影响

当前索引把 `seed3/AUTHORITATIVE` 指向 attempt-2，因此显示
`FSU-FR03-F5-W3 = 3/3`。按上面的判定应改为：

- `FSU-FR03-F5-W3`：**3/3 → 2/3**（seed1、seed2 认证；seed3 的原目标结局
  `Masked`/未认证，attempt-2 是补充证据不计入）。
- 历史视图（若应用）：admitted seeds **42 → 41**，complete RunID（3/3）
  **14 → 13**。
- 活跃 F0/F5 视图（若应用）：admitted seeds **33 → 32**，complete RunID
  **11 → 10**。
- `seed_completion_counts` 会把该 RunID 从 `3/3` 移到 `2/3`（`with_2_of_3`
  从 0 变 1）；`admitted_seeds_total` 少 1。

本复核**没有**修改 `runs/`、`AUTHORITATIVE` 或索引；以上只是建议，由主 agent
决定是否落盘。

## 9. 其他正式 seed 扫描（gate → formal 配置冻结）

方法：比较 gate 产物完成时间、正式 component/manifest 的 `created_at`、
配置文件 mtime，并用当前工具重算 suite_hash 与 manifest 中的 suite_hash。
结果：**除 FR03 seed3 外，未发现“看到正式结果后换目标”的情况。**

| RunID | gate 完成 | 配置 mtime | 正式运行（最早 component created_at） | 冻结判定 | 备注 |
|---|---|---|---|---|---|
| `FSU-FP06-F5-W4` | 01:24:01 | 01:26:37（3 个 seed 配置） | 01:26:43 | 正式前冻结 | 只在 gate 后把 `eligible_census_reference` 2,097,155 改为 1,310,723 并加说明；mask/polarity/precision 未变。seed1 在配置写入 6 秒后开始，属 gate 驱动的 census 元数据修正，非结果驱动换目标 |
| `FSU-FP06-F5-W5` | v5 02:41:01 PASS 5/5 | 01:36:11 | 02:42:11 | 正式前冻结 | 配置在 gate v1/v2 失败后（01:36）把 seed plan 从 sign SA0 改为混合结果位（`0x00400000` SA0 / `0x20000000` SA1 / fixed mantissa SA0），suite notes 明确标注为 gate 阶段激活覆盖修正；suite_hash 与正式 manifest 一致。NIGHT-QUEUE 日志写的 04:10 晚于产物时间，产物时间 02:41:01 为权威 |
| `FSU-FP04-F0-W6` | v1 03:53:08 失败；v2 03:56:11 PASS | 03:55:28 | 04:00:28（seed1 attempt-1；最终采用 attempt-3，04:06:46） | 正式前冻结 | 03:55 把 `submodel` 标签 `FP04-W6 → FP04-a`（suite_hash 不变）；属 gate 阶段标签修正。正式 seed1 使用 attempt-3；attempt-1/2/3 的 injector/target 完全相同，element-oracle mismatch 数相同（SVD 3、FFT 8、sparse 256），是确定性重试/复现，不是换目标。SVD 的 run-level oracle=Masked、element oracle=SDC，属 oracle 层区别 |
| `FSU-FP06-F5-W6` | 03:59:35 PASS 3/3 | 03:13:39 | 04:11:03 | 正式前冻结 | 配置在第三次 commit 后未再改；正式全部 attempt-1；suite_hash 一致 |
| `FSU-FR03-F5-W3` seed1/2 | gate v3 02:24:13 | seed1 02:12:51 / seed2 00:35:24 | seed1 02:28:45 / seed2 02:34:28 | 正式前冻结 | 两者均 `Masked`，但 `audit.ok/certified=true`（链路达到 L5，run-level 输出未变） |

补充：三个正式 suite 的当前配置重算 suite_hash 与各自 `suite_manifest.suite_hash`
完全一致（W5 F0 `7282decf...`、W5 F5 `29e2f8d3...`、W6 F0 `7af52ddc...`、
W6 F5 `2d1a8f9d...`），说明正式运行后 suite 身份未被改动。

## 10. 未解决 / 交给主 agent

1. 是否把 `seed3/AUTHORITATIVE` 改回 attempt-1（或删除）并执行 3/3→2/3 的索引
   修正，由主 agent 决定；本复核不碰 `runs/`。
2. attempt-1 的归档 `chain_report.json` terminal=`full` 是旧工具产物；当前
   checker 为 `exposed_unconsumed`。若保留该目录，建议在证据说明中标注
   “stale terminal, recomputed by current checker”，不要手工改旧证据。
3. attempt-2 若保留，应标为 `protocol deviation / supplemental evidence`，
   不得作为原 seed3 的预注册重跑；其与 LANE0-SA1 pilot 的同 SHA 证据应一并引用。
