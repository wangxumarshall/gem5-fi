# M07-F0-W14-W5X3-C02-T02 完整传播链证据（SQUASHED_BEFORE_MEMORY_ACCESS）

> 样本 `M07-F0-W14-W5X3-C02-T02`（模型 M07 / 上下文 C02 / 时机 T02）。  
> 本轮（W5X3-OBS-0222）通过纯观测埋点，在运行时直接证明故障请求从激活到
> squash 丢弃的完整生命周期；终态 **SQUASHED_BEFORE_MEMORY_ACCESS**，
> Completeness **FULL**（不再标记 PARTIAL / REQUEST_PENDING_AT_ROI_END）。

## 1. 目标动态指令

| 项 | 值 |
|---|---|
| DynInstSeq | 27030544 |
| TranslationID | 9 |
| ASID | 242 |
| PC | 0x401a54 |
| VA | 0x400d200000 |
| PA | 0x83474000 |
| Episode | 2（PID 320） |
| Fault | M07 权限 grant 反转（false → true，one-shot），Where=MMU::checkPermissions64 |

## 2. 完整运行时事件链（原始 Trace，含 EventID / Tick / 行号）

Trace：`runs/W5X3_OBS/M07-F0-W14-W5X3-OBS-C02-T02/Trace/prop_evt.txt.gz`（SHA256 ``522e21b8d8127c8be321a9f1cf19c52c6fd4d1fe2230f18af7596e1e4ed9df1c``）

| EventID | parent | Kind | Tick | 行号 | 说明 |
|---|---|---|---|---|---|
| 573 | 572 | translation_start | 252700186194 | 575 | 翻译开始（MMU::getTE） |
| 579 | 578 | squash | 252700186860 | 581 | Pre-activation Squash（负载在页表游走期间被 squash，游走仍继续） |
| 599 | 597 | mmu_fault_activate | 252700191189 | 601 | 故障激活：permission grant false → true（M07 one-shot） |
| 600 | 599 | translation_result | 252700191189 | 602 | 翻译结果 NoFault（反转后放行）（fault_status=NoFault） |
| 601 | 600 | lsu_request | 252700191189 | 603 | LSU 请求（translateMmuOn，翻译完成、即将移交 LSQ） |
| 602 | 601 | translation_response_received | 252700191189 | 604 | 翻译结果真正返回并被 LSQ 接收 |
| 603 | 602 | squash_translation_decision | 252700191189 | 605 | LSQ 判定动态指令已 Squashed → discard_due_to_prior_squash（decision=discard_due_to_prior_squash, released=1） |
| 604 | 603 | squash_translation_invoked | 252700191189 | 606 | 实际调用 squashTranslation()（released=1 → 置 TranslationSquashed 并 self-destruct）（released=1，置 TranslationSquashed + self-destruct） |
| 605 | 604 | translation_request_discarded | 252700191189 | 607 | 请求生命周期终止（prior_squash_before_translation_completion，清理完成）（terminal_reason=prior_squash_before_translation_completion） |
| 606 | 605 | cache_dispatch_decision | 252700191189 | 608 | Cache 派发被阻止（cache_dispatch_blocked_by_squash）（dispatch_decision=cache_dispatch_blocked_by_squash） |

所有事件 fault_id=1（自激活起）、translation_id=9、dyn_inst_seq=27030544、
request_id=27030544，parent_event_id 逐级链式相连（599→600→601→602→603→604→605→606）。

**观测语义（0222 埋点精度）**：上表 5 类新增事件由 `mmuNoteLsqTranslationFinish()`
在 `SingleDataRequest::finish()` 的原始 `isSquashed()` 分支**之前**连续发射：运行时先读取
真实的 `_inst->isSquashed()`（decision 字段）与 `isReleased()`（released 字段，=1 表示 LSQ
entry 已释放），把状态写入事件，随后原始控制流才执行 `squashTranslation()`（置
`TranslationSquashed`，released=1 时 `delete this` 销毁 Request）。因此新事件是**紧邻实际
控制流的观测性决策/终止标记，不是在实际调用后分别发射的回调**；`cache_dispatch_decision(
cache_dispatch_blocked_by_squash)` 是基于 Squash 分支 + 请求生命周期的观测性判定（该请求
全 Trace 无 `cache_request`/`memory_response`/`rf_writeback`/`commit`）。

## 3. Fault → Terminal 因果 DAG

```text
Translation Start
      |
      v
Pre-activation Squash  (负载在页表游走期间被 squash)
      |
      v
MMU Fault Activation   (permission: false -> true, fault_id=1)
      |
      v
Translation Result     (NoFault, 同 tid/seq/request_id)
      |
      v
LSU Translation Request
      |
      v
Translation Response Received
      |
      v
Squash Status Check    (decision=discard_due_to_prior_squash)
      |
      v
squashTranslation()    (released=1 -> TranslationSquashed + self-destruct)
      |
      v
Request Cleanup / Discard  (prior_squash_before_translation_completion)
      |
      v
CACHE_DISPATCH_BLOCKED_BY_SQUASH
      |
      v
Terminal: SQUASHED_BEFORE_MEMORY_ACCESS
```

## 4. 七个因果环节的运行时证据

| # | 环节 | 证据（EventID） |
|---|---|---|
| 1 | 故障激活修改了该 Translation 的权限状态 | `mmu_fault_activate` event 599，permission_before=false → after=true |
| 2 | Translation Result NoFault 对应同一请求 | `translation_result` event 600（fault_id=1, tid=9, seq=27030544） |
| 3 | LSU 接收了该翻译响应 | `translation_response_received` event 602 |
| 4 | LSU 检查发现 DynInst 已 Squashed | `squash_translation_decision` event 603（discard_due_to_prior_squash, released=1） |
| 5 | 请求进入 squashTranslation 清理分支 | `squash_translation_invoked` event 604 |
| 6 | 请求完成 Discard | `translation_request_discarded` event 605（prior_squash_before_translation_completion, released=1） |
| 7 | 请求未进入 Cache / 架构提交 | `cache_dispatch_decision` event 606（cache_dispatch_blocked_by_squash）；全 Trace 无该 seq 的 cache_request / memory_response / rf_writeback / commit |

## 5. 与 Control 的对照

同一条 load（seq=27030544）在 Control 中 `translation_result(fault_status=Data)`，无 `lsu_request`，随后同样 `squash_translation_decision=discard_due_to_prior_squash` + `translation_request_discarded`。

Control：`runs/W5X3_OBS/CTRL-OBS-M07-C02/Trace/prop_evt.txt.gz`（SHA256 ``19061f4cfc7b5390bf324eb70ddd21e7d5a5dee7681142d1145e6ccd2620ed2a``）。

## 6. Guest SIGSEGV 独立性说明

Guest 仍报告 `signal=11 si_code=2 fault_addr=0x400d200000 result=PASS`（架构预期 SIGSEGV）。
该 SIGSEGV **不是**故障动态指令造成的：故障指令得到 `fault_status=NoFault`（授权被反转放行），
其请求在翻译完成时因「指令已被预热 squash」被丢弃（本文件 §2/§4）；SIGSEGV 来自未故障的
架构拒绝路径（execute-only 权限拒绝，one-shot 已被消耗）。因此本样本是**微架构传播+终止链的
完整观测**，不是软件层面 SDC，也不把 Guest SIGSEGV 错误归因于故障指令。

## 7. 溯源

| 项 | 值 |
|---|---|
| 新 Build Hash | `ce80a9c983b31f77c9b4a6626012505fd3484d5c00df5b9399a9d6975ab2b73d` |
| Fault Trace SHA256 | `522e21b8d8127c8be321a9f1cf19c52c6fd4d1fe2230f18af7596e1e4ed9df1c` |
| Control Trace SHA256 | `19061f4cfc7b5390bf324eb70ddd21e7d5a5dee7681142d1145e6ccd2620ed2a` |
| 新增埋点 Patch | `work/0222_lsq_translation_lifecycle.patch` |
| 复现命令 | `python3 work/rerun_m07_c02_obs.py`（或见 Run_Log/command.txt） |
| 终态 | SQUASHED_BEFORE_MEMORY_ACCESS（Completeness=FULL） |
