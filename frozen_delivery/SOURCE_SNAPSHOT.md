# MMU WHEN-5X3 — gem5 关键源码快照与溯源 (final frozen source snapshot)

本文件是 MMU WHEN-5X3 研究的 **gem5 构建版本关键源码快照索引**。只做快照与归档，
不修改源码、不重新编译、不改变任何故障语义。

## 1. gem5 版本与构建

| 项 | 值 |
|---|---|
| gem5 版本 | **25.1.0.1**（`RELEASE-NOTES.md` 顶部标注；source tree 自包含，无 `.git` 元数据） |
| 构建目录 | `CHAOS/gem5/build/ARM/gem5.opt` |
| build_opts | `ARM`（默认；`build_opts/ARM`） |
| 构建命令 | `cd CHAOS/gem5 && scons -j<N> build/ARM/gem5.opt`（本项目各轮 `-j4/16/24/64`） |
| 工具链 | GCC 10.3.1（`work/build_0202c*.log`；gem5 官方支持 GCC 11–14，此处为宿主工具链） |
| 当前盘上二进制 | `fb1b6f010034f27312f2df215e00ada08cb7df811ef7425e4585b623a7e1d3f8`（0202c + `MMU_CONSUMER_REUSE_CAP=16`） |

**三个参与实验的构建哈希**（每样本所属构建见 `control_map.json` / `authoritative_trace_index.csv` 的 `BuildHash` 列）：

| BuildHash (前 16) | 全称 | 用途 |
|---|---|---|
| `741cdc567f489444` | `741cdc567f4894448ed9aea08bcf9f9db2d65f42e089becac587890bfe9047b3` | 原构建（`runs/W5X3/CTRL-*`、M07-C02-T03 等原始 117 条） |
| `eb327197c073dddf` | `eb327197c073dddf039fdb63662d2cfa266394507ae0cb4630d0f4ff4dd76f65` | 0202c + IFU 埋点 + `masked_reason`（12 取指 + 2 M07-C02 + CTRL2） |
| `fb1b6f010034f273` | `fb1b6f010034f27312f2df215e00ada08cb7df811ef7425e4585b623a7e1d3f8` | 0202c + `MMU_CONSUMER_REUSE_CAP=16`（9 M05 数据 + CTRL2B）；**唯一残留在磁盘的二进制** |

`eb327`/`fb1b6f` 均为纯观测改动，二者仅差 `MMU_CONSUMER_REUSE_CAP` 一处（只影响
M05 数据路径的 trace 体量，不影响故障语义）。

## 2. 关键源码文件清单（实际构建版本）

下表为 `CHAOS/gem5/src/` 快照（fb1b6f 构建所用源码树；eb327 与之仅差
`MMU_CONSUMER_REUSE_CAP=16` 一处，下表文件内容一致）。「本轮修改」= 本研究是否改动该文件
（Frozen=fault-injection 注入实现；0202b/0202c=纯观测埋点）。快照文件在 `gem5_source/`
目录，以扁平化文件名 `src_xxx.yyy` 保存（见 §3）。

| # | 相对路径 | SHA256 | 本轮修改 | 观测事件 / 实际调用位置 |
|---|---|---|---|---|
| 1 | `src/cpu/o3/lsq.cc` | `6aca839cd2ca3d6e8e6c56862c53a6c92cb0449067e8616ba546f413cab060d0` | 否（原始） | 翻译完成 `LSQ::SingleDataRequest::finish` @988；`isSquashed()→squashTranslation()` @996 |
| 2 | `src/cpu/o3/lsq.hh` | `2071bfa2da5393a7f32bf7b0094b57ac7e487813ac8965d8dc193bd627d84e5a` | 否（原始） | `LSQRequest::squashTranslation()` @609（置 `TranslationSquashed`） |
| 3 | `src/cpu/o3/lsq_unit.cc` | `185b1fde6aaba14b8042227dc7035c1f2cdfd6c0fa69ba915d0192d6a988d7f3` | Frozen | `squash` 事件 @1208/1287（`LSQUnit::squash`）；load 入口 @715；派发 `sendPacketToCache` @1617 |
| 4 | `src/cpu/o3/fetch.cc` | `b6251fdcf492937fc8856d3a779545c1cf02612eb4fab7196900691b49884ad6` | 0202c | `ifu_response` @`processCacheCompletion`；`ifu_decode` @`buildInst`；`mmuTakeFetchTxn` @`finishTranslation` |
| 5 | `src/cpu/o3/fetch.hh` | `a42f07731c692a7d5c46e0b03bde02791615055f923ab3f4916cd5f95fb38dd8` | 0202c | `fetchBufferTxnId[MaxThreads]`（fetch 缓冲的开放 MMU 取指事务） |
| 6 | `src/cpu/o3/decode.cc` | `7dc8af01652f6305019d79672fb2006e141b95ffe29994adf0ce3d89c7ed9394` | 否（原始） | 参照（`ifu_decode` 为 Fetch 侧 DynInst 构建，**非** O3 `Decode::tick`） |
| 7 | `src/cpu/o3/commit.cc` | `11e03973929ac38e736ed5a7c500f617702a5d06facc0791143e4ce4732300aa` | Frozen | `exception_delivery` @1266（`Commit::commitHead`，且 `!ReExec`）；`commit` 事件 @1356 |
| 8 | `src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` | `0f23ea4b266c660f1a3b9cdbdba362b136c84c57e601c37ab0645a55794f356c` | Frozen+0202c | 新增：故障注入 + 传播追踪（`mmuNote*` 系列事件发射、`MMU_CONSUMER_REUSE_CAP=16`、`masked_reason`） |
| 9 | `src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh` | `08564143504d04c0f9306c741304e20988662c48d662ef44cf2d348c38510405` | Frozen+0202c | 新增：事件注册表 + IFU 钩子声明（`mmuNoteIfuResponse` 等） |
| 10 | `src/mem/cache/cache.cc` | `e94bfeece83de049db5737cba536edabe81a62f5e7d4f6927e8935ed201fa016` | Frozen | `cache_request` @181（`Cache::access`）；`cache_lookup` @250 |
| 11 | `src/mem/cache/base.cc` | `d60848179b063d3c8648a279f39e85d28d17c7be9adb1a8805e9677cd06d06eb` | Frozen | `mshr_alloc` @724；`cache_response` @744/752（`BaseCache::recvTimingResp`） |
| 12 | `src/arch/arm/mmu.cc` | `1b042589b8bbab27f992a9c56309756a13858bfcf2bed9cc30f8ac21fbf71447` | Frozen+0202b+0202c | `permission_eval` @731；M07 grant 反转 `mmu_fault_activate` @785；`translation_result` @1380；`lsu_request` @1388（`translateMmuOn`，`fault==NoFault&&hasPaddr()`） |
| 13 | `src/arch/arm/mmu.hh` | `0c8a03562b23a455459ea2b30387e36e1fc9eb61924a9453a600d91afcbc708a` | Frozen | `checkPermissions64` 声明 / M07 钩子 |
| 14 | `src/arch/arm/tlb.cc` | `62946059e80f8413ee459b86e04f45d01334ffe12d3705d1837829af2dda55a8` | Frozen+0202b+0202c | `phase3_entry_model`（含 M05）；暖命中消费者事务（`mmuEntryFaultReuseCapped`）；M04 PFN 替换 |
| 15 | `src/arch/arm/tlb.hh` | `1fd58cda19a3c4ee1ca132c1063ff3d49c5cf6874faff661d2be13cbc6881adf` | Frozen | M04/M05 入口钩子声明 |
| 16 | `src/arch/arm/table_walker.cc` | `40883abad5f0dca20bdc2c9c8f46994b23900ee36760ca50e1bf21f7144ab5f8` | Frozen | 页表游走阶段事件（`ptw_start`/`pte_read`/`ptw_request`/`ptw_response`/`pte_decode`/`tlb_fill`） |
| 17 | `src/arch/arm/table_walker.hh` | `89110e2081da62743e4c2325aa656976e945f086959bcd29f18882412e44b611` | Frozen | 游走钩子声明 |
| 18 | `src/arch/arm/pagetable.hh` | `39c3b568c656018423ebf01fadd650e79a9e817f871e8778c8da7d56c3bdfe7c` | Frozen | 描述符/PTE 解码钩子 |
| 19 | `src/arch/arm/faults.cc` | `27d3d4d979490c91bf01947170f2dfe8c5b75fa629d69732c151bdc518f5dccb` | 否（原始） | ARM `DataAbort` 异常类（`ec` @1308、`il` @1337、`iss` @1374、`annotate` @1403、`VirtualDataAbort::invoke` @1444） |

> 注：数据侧 Data Abort 的**观测**不在 `faults.cc` 内，而表现为
> `translation_result(fault_status=Data)` + `squash`（`lsq_unit.cc:1208`）；本构建数据侧
> 不发射独立 `exception_delivery` 事件（M07-C02 T01/T02 与 Control 的 `kind=exception_delivery`
> 计数均为 0）。架构异常投递的观测在 `commit.cc:1266`（取指侧 PrefetchAbort 到 ROB 头时）。

## 3. 快照文件命名

`gem5_source/` 内以 `src_` + 路径（`/`→`_`）扁平化命名，例如
`src_arch_arm_mmu.cc`、`src_cpu_o3_lsq.cc`、`src_cpu_o3_CHAOSPropagation_CHAOSPropagation.cc`。
每文件 SHA256 见 §2（与 `CHAOS/gem5/src/` 原路径逐一对应，可 `diff` 复核）。

## 4. 本研究源码修改 Patch

| 文件 | SHA256 | 内容 |
|---|---|---|
| `source_patches/Frozen_Source.patch` | `18d83cec9ea0158896c09b431f5d3278372575c7b3732a250c1e191da4b3e59a` | **完整故障注入实现**（M01–M08 + 传播追踪 + 配置，92 文件）相对基线 gem5 的累计 diff（"Formal Readiness" 冻结版） |
| `source_patches/gem5_observational_changes.diff` | `c781798417ee607c4b8ce569566f8fcc1f3b841a52a60da44de3abcb75fa1e71` | 0202b 纯观测改动（`mmu.cc` M07 激活归因、`tlb.cc` M04 激活归因） |
| `docs/0202c_source_diff.md` | `e9adb629cb9af5b6550c472e50a1c0f5d51af4fb12db8c0aac7f823e86af0cc8` | 0202c 纯观测改动（5 文件：CHAOSPropagation.hh/.cc、fetch.cc/.hh、tlb.cc） |

## 5. 新增观测事件清单与边界

- **新增事件类型**（0202c）：`ifu_response`（`Fetch::processCacheCompletion`，真实 IFU
  响应）、`ifu_decode`（`Fetch::buildInst` 的 Fetch 侧 DynInst 构建）、字段
  `masked_reason`（`mmu_fault_summary` 显式掩盖机制）。完整规格见
  `docs/0202c_instrumentation_spec.md`。
- **观测代码与原始故障模型的边界**：原始注入点（M01–M08 的 `mmuFaultActivate` /
  `maybeCorrupt*` / M07 `checkPermissions64` grant 反转等）**完全未改动**；新增代码只在
  `mmuTraceEnabled()` 时发射事件/登记关联 ID，trace off 时全部 no-op。8 个 Control
  复现冻结 N（M04 N=20005、M07-C02 N=6、其余 N=3）即 Where/When 语义冻结一致性证据。
- **逐事件实际调用位置**：见 `docs/0202c_source_call_sites.md`（三级：Cache / MMU 翻译 /
  LSQ / Commit / 异常）。

## 6. 复现入口

- gem5 复现：`cd CHAOS/gem5 && scons -j<N> build/ARM/gem5.opt`（版本 25.1.0.1）；
  运行入口 `./resume.sh`（重跑缺失 manifest）→ `python3 campaign/finalize.py`。
- 每样本运行命令：`runs/W5X3_RETRY2/<SampleRunID>/Run_Log/command.txt`；
  rcS 上下文脚本：`campaign/rcs/*.rcS`；完整复现说明见 `docs/REPRODUCTION_V3.md`。

本快照对应 `CHAOS/gem5/src/` 的实际磁盘状态（2026-11-18），逐文件 SHA256 可独立复核。
---

## 附录 A：W5X3-OBS-0222 定向补全（M07-C02 squash-discard 运行时证明）

新增纯观测埋点（**第 4 个构建**），用于在运行时证明 M07-C02-T01/T02 故障请求被
`squashTranslation()` 丢弃、未进入 Cache。

| 项 | 值 |
|---|---|
| 新 Build Hash | `ce80a9c983b31f77c9b4a6626012505fd3484d5c00df5b9399a9d6975ab2b73d` |
| 修改文件 | `CHAOSPropagation.hh`（+7 字段 + 1 方法声明）、`CHAOSPropagation.cc`（+`mmuNoteLsqTranslationFinish`）、`lsq.cc`（`SingleDataRequest::finish` 调用点） |
| 修改后 SHA256 | `bd2704f6…` / `0f49d990…` / `c6a6febf…` |
| Patch | `source_patches/0222_lsq_translation_lifecycle.patch` |
| 新增事件 | `translation_response_received`、`squash_translation_decision`、`squash_translation_invoked`、`translation_request_discarded`、`cache_dispatch_decision` |
| 复跑 | `runs/W5X3_OBS/`（CTRL-OBS-M07-C02 + M07-F0-W14-W5X3-OBS-C02-T01/T02） |
| 结果 | T01/T02 终态 SQUASHED_BEFORE_MEMORY_ACCESS（FULL）；115→117 FULL、2→0 PARTIAL |

新增埋点仍为纯观测（`mmuTraceEnabled()` 内发射事件，trace off 全 no-op），不改
Where/Context/Timing/故障注入语义：8 个 Control 复现冻结 N=6，Guest SIGSEGV 与历史
字节一致。
