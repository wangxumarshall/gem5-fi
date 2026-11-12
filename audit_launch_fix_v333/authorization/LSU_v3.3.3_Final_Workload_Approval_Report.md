# LSU v3.3.3 — Final Workload Approval Report

**Date:** 2026-11-12  
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`  
**Branch:** `lsu-v3.3.1-context-workload-20261111`  
**HEAD:** `13c029e51d6ef3df4fc3de85e1e21a20a4defa9a`  
**Candidate binary:** `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`  
**Candidate config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`  
**Campaign ID:** `LSU-V333-FORMAL-20261112`

## 1. 结论摘要

| 分类 | 数量 | 说明 |
|---|---|---|
| A. `EXPLICITLY_APPROVED` | **30** | 6 个模型级 workload 变更由一次明确的研究者选择批准，覆盖 30 个上下文 |
| B. `SERVER_RECORDED_ONLY` | **0** | 未发现仅有服务器标签而无研究者指令的情况 |
| C. `PENDING_APPROVAL` | **0** | — |
| D. `NOT_APPLICABLE` | **0** | 30 个全部是真实设计变更 |

**最终状态：`READY_FOR_RESEARCHER_AUTHORIZATION`**

本阶段未启动任何正式 Fault/Control 任务，未修改任何 C++/配置/workload/身份。

## 2. 审批证据链（可独立复核）

审批不是来自 Excel 标签、Git commit 或服务器自述，而是来自 harness 记录的
`AskUserQuestion` 用户选择：

1. 决策问题于 **2026-11-11T16:14:54.385Z**（= 2026-11-12 00:14:54 +0800）
   以四个分组问题呈现：workload、A01/A03 根因修复、终态标签、配置冻结。
2. 研究者的选择记录于同一会话转录 **line 572** 的 `toolUseResult.answers`：

   - Q1 workload：**全部采用（推荐）**
   - Q2 A01/A03：**批准根因修复+重算（推荐）**
   - Q3 终态标签：**采用证据标签（推荐）**
   - Q4 配置冻结：**批准定义，验证后冻结 SHA（推荐）**

   记录时间：**2026-11-12 08:58:43 +0800 (UTC 2026-11-12T00:58:43.355Z)**。
3. 转录路径：

   ```
   /home/sdc/.claude/projects/-home-sdc-gem5-fi-ding--claude-worktrees-
   r6-s-w1-continuation-20261101/0e60f058-b2ca-4b83-87ca-423a7f3606f2.jsonl
   ```

4. 落盘记录：`audit_v3_3_3/decisions/LSU_v3.3.3_Researcher_Approval.md`；
   提交 `200e31f5`。落盘记录与转录一致。

**重要边界（必须如实说明）：** 研究者批准的是 **6 个模型级 workload 变更**，
不是 30 个上下文逐一批准。30 个上下文的 SampleRunID/Seed 均未改变，
因此由模型级批准覆盖；但不得把这句话表述为「30 个上下文各自获得单独批准」。

## 3. 30 个 Override 的逐条分类

30 个 override 全部为 **A. EXPLICITLY_APPROVED**。逐条明细（含 13 项字段、
反汇编/trace/oracle 证据、执行命令）见同目录的
`LSU_v3.3.3_Final_Workload_Approval_Packet.xlsx` 工作表 `01_Override_30`。

| Model | Contexts | 原 Workload | 新 Workload | 批准 | 条件 |
|---|---|---|---|---|---|
| FW02 | R01–R05 | sq_forward (W4) | `sq_forward_w4v2` | 全部采用（推荐） | 无附加条件 |
| RP01 | R01–R05 | replay_dependency (W7) | `replay_partial_v332` | 全部采用（推荐） | 已声明静态 PC 限定与 internal watchdog 终态 |
| MD04 | R01–R05 | replay_dependency (W7) | `md04_violations_v332` | 全部采用（推荐） | 已在新 binary 上复核事件计数（N=8） |
| SQ01 | R01–R05 | sq_drain (W3) | `sq_reload_v3212` | 全部采用（推荐） | 无附加条件 |
| SQ03 | R01–R05 | sq_drain (W3) | `sq_reload_v3212` | 全部采用（推荐） | 条件是冻结 MASKED/VISIBILITY_TIMING_SHIFT 标签（已接受并写入台账） |
| SP05 | R01–R05 | store_path (W6) | `sq_reload_v3212` | 全部采用（推荐） | 条件「store_data_fnv 新构建验证通过后正式采用」已满足（store_data_fnv 存在）；commit/writeback 证据缺失属于证据完整度问题，不改变 workload 采纳决定 |

## 4. 技术依据（六项变更）

### FW02

- **原设计问题：** FW02（F6 f6_fw02，抑制一次 store→load 转发）在原 W4 上没有 in-main consumer，pre-formal 只能得到 MASKED。
- **原/新差异：** 原 W4 的 main 只有 store（0x400534/0x40055c），没有 in-main 数据 load；W4-v2 在 main 内加入全重叠转发对 0x400530 str / 0x400538 ldr，以及 +6 偏置子宽对 0x400570 str / 0x400574 ldur，另有两组 同类对。
- **故障语义：** 故障语义不变：仍然是「抑制一次转发决策」。改变的是消费者和 eligible 事件流（in-main N=60，ordinals 8–67）。
- **对语义的影响：** 使 FW02 具备可观测的 in-main 转发消费者；不改变注入 hook、bit 位置或触发条件。
- **证据：** objdump: 0x400530 str x3,[x1,x4,lsl#3] / 0x400538 ldr x4,[x1,x4,lsl#3]；0x400570 str x5 / 0x400574 ldur w3,[x4,#-6]。census: in-main 8–67 共 60 个 eligible；分位 13/25/37/49/61。oracle golden 1f4cbf14327717df；5/5 control PASS；fault 4 SDC + R03 MASKED。
- **研究影响：** 采纳后 FW02 可进入因果链研究；若保留原 W4，该模型只有 MASKED/无消费者结论，无法支撑 F6 转发故障的传播论证。
- **ELF SHA256：** `a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2`
- **原 ELF SHA256：** `132a84f7f21be052bc1f2c9baf1c12d5bd3462aae03b1d42778c94e69b0af297`
- **实际执行：** `f6_fw02`（完整命令见任务映射表）

### RP01

- **原设计问题：** RP01 需要部分地址覆盖（PartialAddrRangeCoverage）才能触发 「跳过一次 replay reschedule」的设计场景。
- **原/新差异：** 原 W7 的 store→load 只有完整 8B 重叠（0x40052c str / 0x400530 ldr，同一 index）；新负载在 0x40055c str x0,[x4] 后用 0x400560 ldur w0,[x4,#6] 形成 2 字节部分重叠。
- **故障语义：** 故障语义不变：跳过一次 rescheduleMemInst。改变的是存在部分 重叠的消费者。
- **对语义的影响：** 五个上下文共享静态 PC/几何，但动态执行不同（load_seq 16293/23229/30165/37101/44037，lq idx/gen、store_seq、tick 均不同）。该「同静态 PC、异动态执行」是必须在论文中声明的限定。
- **证据：** objdump: 0x40055c str x0,[x4] / 0x400560 ldur w0,[x4,#6]。census: 255 个 eligible 全部 load_pc=0x400560，ROI 1–255；分位 26/77/128/179/230。5/5 fault 触发一次 skip 后进入 in-model watchdog（20M cycles）；5/5 control PASS；golden f3b1c554273d23f7；fault 无 checksum（NO_CHECKSUM）。
- **研究影响：** 采纳后 RP01 具备设计中的部分重叠场景；若保留原 W7，只能观察 完整重叠，RP01 失去设计场景。
- **ELF SHA256：** `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42`
- **原 ELF SHA256：** `ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4`
- **实际执行：** `rp01_skip_replay`（完整命令见任务映射表）

### MD04

- **原设计问题：** MD04 需要至少 5 个不同的动态上下文；原 W7 只有 1 个。
- **原/新差异：** 原 W7 在 v3.3.1 census 中只有 1 个 eligible violation （N_ROI=1）；新负载在 main 内构造 8 个 violation pair（L1/L3/L4/L6/L8 等），5 个分位点映射到 5 个不同的真实 pair。
- **故障语义：** 故障语义不变：在 LSQUnit::checkViolations 处 SKIP_M5PANICFAULT_RETURN_ONCE。
- **对语义的影响：** 改变违规事件数量与上下文；故障定义不变。R01 为 MASKED（load_complete=1），R02–R05 为 SDC（load_complete=0）。
- **证据：** census: ROI 3–10（N=8），分位 3/5/6/8/10 对应 L1/L3/L4/L6/L8。5/5 control PASS；golden 22be5ae3364d0c9f；fault 4 SDC + R01 MASKED。
- **研究影响：** 采纳后 MD04 才有 5 个可用上下文；若保留原 W7，上下文数量不足。
- **ELF SHA256：** `dd241c3097e61495141e614ce493ba4b2901a7df751baa95e69365bdf8f95c43`
- **原 ELF SHA256：** `ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4`
- **实际执行：** `md04`（完整命令见任务映射表）

### SQ01

- **原设计问题：** SQ01 需要同地址 reload 读取被注入的 SQ 数据；原 W3 无消费者。
- **原/新差异：** 原 W3 只写数组、末尾读一次，选中的 lane 从未被消费；新负载在 0x40053c str x6,[x8,x0,lsl#3]，0x400540 dmb ish，0x400544 ldr x4,[x8,x0,lsl#3] 同地址重读，0x400550 起为消费者。
- **故障语义：** 故障语义不变：SQEntry::_data[0] ^= 0x08。
- **对语义的影响：** 故障字节与源值只在 byte0^0x08 不同；reload 走 L1D read（sq_entry_id=-1，无转发决策）。
- **证据：** objdump 同上。5/5 COMPLETE_CHAIN；mem_write_hash == reload_data_hash == consumer_hash（21d2…/d4e5…/336b…/e0a1…/4cd1…）；分位 1018/1044/1069/1095/1121；golden 7df5034c23f3e703；5/5 fault FAIL。
- **研究影响：** 采纳后 SQ01 为完整直连 oracle 的 SDC 链；否则保持无消费者 MASKED。
- **ELF SHA256：** `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6`
- **原 ELF SHA256：** `d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f`
- **实际执行：** `sq01_bit3`（完整命令见任务映射表）

### SQ03

- **原设计问题：** SQ03 需要可观测的 `_canWB` 时序效应；原 W3 无后续读取。
- **原/新差异：** 原 W3 无后续 load，_canWB 效应仅体现在生命周期；新负载提供 同地址 reload（0x400544）作为可观测点。
- **故障语义：** 故障语义不变：`_canWB 0→1`、`storesToWB 0→1`，不改变 地址/大小/数据。
- **对语义的影响：** 表现为可见性时序移动，而不是数据错误；5/5 oracle PASS。
- **证据：** 5 个上下文中 4/5 为 CHAIN_VISIBILITY_MOVED（cache block update 早于 commit），1/5（ordinal 1047）为 LIFECYCLE_ONLY；reload 请求均在 commit 之后，无可观测的 pre-commit consumer；golden 7df5034c23f3e703。
- **研究影响：** 采纳后 SQ03 可区分「提前可见」与「无效应」；论文中必须冻结 MASKED / VISIBILITY_TIMING_SHIFT 标签与 4/5 + 1/5 分裂。
- **ELF SHA256：** `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6`
- **原 ELF SHA256：** `d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f`
- **实际执行：** `sq03_canwb`（完整命令见任务映射表）

### SP05

- **原设计问题：** SP05 需要架构消费者来观察 completeStore 写跳过；原 W6 只会得到 MASKED / NO_RELOAD_OBSERVED。
- **原/新差异：** 原 W6 只填充缓冲区，没有 load 读取被跳过的 store lane；新负载的 同地址 reload（0x400544）读取被跳过的 lane。
- **故障语义：** 故障语义不变：completeStore 的写跳过；修复是记录路径 （store_data_fnv）而非故障定义。
- **对语义的影响：** store 数据可绑定（store_data_fnv 已出现），但缺少独立的 commit_event / writeback_event，证据完整度仍为 QUALIFIED。
- **证据：** completeStore 触发；storesToWB 1→0；mem_sent=0；write_skipped=1；无 store_mem_write；reload 读到零值 a8c7f832281a39c5；consumer 可见；5/5 oracle FAIL；store_data_fnv 在 summary.json/trace 中存在。
- **研究影响：** 采纳后 SP05 具备架构消费者；但 SP05 仍只能以 QUALIFIED 披露，不能宣称完整 commit→writeback 链。
- **ELF SHA256：** `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6`
- **原 ELF SHA256：** `906b3798adc618f388c1988389dd67140afeba6c706456fdeebdd524dc55fbcf`
- **实际执行：** `sp05_complete`（完整命令见任务映射表）

## 5. 七个问题的直接回答

1. **哪些 Workload 变更已经获得明确批准？**
   全部 6 个模型级变更（FW02/RP01/MD04/SQ01/SQ03/SP05），覆盖 30 个上下文。
2. **哪些只是服务器自行记录为 APPROVED？** 0 个。
3. **哪些变更尚未获得批准？** 0 个。
4. **如果保留原始 Workload，会有什么问题？** 见 §4 各模型的「原设计问题」：
   FW02 无 in-main consumer；RP01 无部分重叠；MD04 只有 1 个 violation；
   SQ01 无消费者；SQ03 只有 lifecycle 效应；SP05 无 reload 消费者。
5. **如果采用新 Workload，是否改变原始故障语义？** 不改变。六个模型的
   hook/bit/触发条件均未变，改变的是消费者与 eligible 事件流。
6. **是否影响 60 个 SampleRunID 和权威 Seed？** 不影响；逐行核对一致。
7. **最终正式 Campaign 应使用哪些 ELF 和 Config？** 见 §6。

## 6. 正式 Campaign 使用的 ELF 与 Config

| Model | Workload | ELF SHA256 |
|---|---|---|
| A01 | `agu_addrmodes` | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| A03 | `agu_addrmodes` | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| FW02 | `sq_forward_w4v2` | `a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2` |
| FW05 | `fw05_forward` | `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` |
| SQ01 | `sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| SQ03 | `sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| SP05 | `sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| DA04 | `alignment` | `89ff937a73a01708c5781385e9a9f9740254a456d4f07042b2b480c4677918c0` |
| LP01 | `load_response` | `3779e8ced41a07d798f78c97a1f5d10187c812a24a81b599c19ae68a0753e711` |
| MD04 | `md04_violations_v332` | `dd241c3097e61495141e614ce493ba4b2901a7df751baa95e69365bdf8f95c43` |
| LQ04 | `lq_lifetime_ordinal` | `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba` |
| RP01 | `replay_partial_v332` | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |

- Binary：`build/ARM/gem5.opt` = `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
- Config：`configs/se/lsu_proxy.py` = `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
- 不得使用主仓库旧 binary `6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`。

## 7. 已披露的文档不一致（只报告，不修改）

| # | 位置 | 观察 | 影响 |
|---|---|---|---|
| 1 | `audit_v3_3_3/LSU_60Context_Final_Readiness_Matrix.csv` | 30 行仍为 `CANDIDATE_PENDING_APPROVAL` | 历史文件，记录批准前状态；不覆盖 |
| 2 | `audit_v3_3_3/LSU_60Context_Final_Readiness.csv` | 同样仍为 `CANDIDATE_PENDING_APPROVAL` | 与 launch 副本冲突；以 launch 副本和本报告为准 |
| 3 | `audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv` | `SampleRunID` 列为 legacy `V332-<M>-R0x` | collector 以 (ModelID, ContextID) 索引，功能无影响；该列不可作为权威 ID |
| 4 | `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` | `WorkloadPath` 指向旧 worktree `lsu-platform-v3.2` | runner 用 ROOT-relative 解析，实际执行 v3.2.12 ELF |
| 5 | `audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md` | A03 校验和为 re-census 前旧值 | 历史文件；当前权威为 run summary/causal CSV |
| 6 | `audit_v3_3_3/LSU_12Model_Workload_Oracle_Audit.csv` | 同行含 `CANDIDATE_PENDING_APPROVAL` 与 `OVERRIDE_APPROVED` | 两列语义不同，易误读 |

## 8. 声明

- 未修改 C++ 源码、故障模型语义、workload、SampleRunID、Seed、ROI、二进制。
- 未重新编译 gem5。
- 未启动任何正式 Fault/Control 任务。
- 本报告中的 SHA256 均由本次运行 `sha256sum`/Python `hashlib` 实测。

