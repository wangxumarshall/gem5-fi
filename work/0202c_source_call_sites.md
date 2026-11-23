# 0202c 源码调用位置清单 (source call-site index)

对应构建：`eb327197c073dddf…`（T01/T02 与 CTRL2 controls 所用）与
`fb1b6f010034f273…`（M05-C03/C04/C05 与 CTRL2B controls 所用；与 eb327 相比仅
`MMU_CONSUMER_REUSE_CAP=16` 一处差异，下列调用位置相同）。

本清单给出**实际发射事件的调用位置**，而非 `CHAOSPropagation` 中的事件函数定义。
行号为当前磁盘残留 `CHAOS/gem5/src/` 快照的行号，SHA256 见文末。

## 1. Cache 侧

| 事件 | 位置 | 所在函数 |
|---|---|---|
| `cache_request` | `src/mem/cache/cache.cc:181` | `Cache::access(PacketPtr, CacheBlk*&, Cycles&, PacketList&)` → `mmuNoteCacheEvent("cache_request", …)`。真实 Request 身份（`request_id==seq`）在此匹配；请求未达 `Cache::access` 则不发此事件。 |
| `cache_lookup` | `src/mem/cache/cache.cc:250` | `Cache::access` |
| `mshr_alloc` | `src/mem/cache/base.cc:724` | `BaseCache::chaosMmuMshrAlloc(PacketPtr, MSHR*)` |
| `cache_response` | `src/mem/cache/base.cc:744`/`:752` | `BaseCache::recvTimingResp(PacketPtr)` |

## 2. MMU 翻译侧（ARM）

| 事件 | 位置 | 所在函数 |
|---|---|---|
| `permission_eval` | `src/arch/arm/mmu.cc:731` | `MMU::checkPermissions64`（观测真实 grant 判定） |
| `mmu_fault_activate`（M07 grant 反转） | `src/arch/arm/mmu.cc:785` | `MMU::checkPermissions64`（`!grant` 且 M07 one-shot 命中 → `mmuFaultActivate`，反转 `grant=true`） |
| `translation_result` | `src/arch/arm/mmu.cc:1380` | `MMU::translateMmuOn` 的 `!delay` 完成块（1369–1393） |
| `lsu_request` | `src/arch/arm/mmu.cc:1388` | `MMU::translateMmuOn`；**仅** `fault==NoFault && req->hasPaddr()` 时发射。是"翻译完成、即将移交 LSQ"的观测，**不是**内存请求已发往 Cache |

## 3. LSQ 侧（O3）

| 环节 | 位置 | 所在函数 |
|---|---|---|
| 翻译完成 | `src/cpu/o3/lsq.cc:988` | `LSQ::SingleDataRequest::finish(Fault, RequestPtr, ThreadContext*, Mode)`；`fault==NoFault` → `State::Request`，否则 `State::Fault`；**若 `_inst->isSquashed()` → `squashTranslation()`（996–997）** |
| 翻译丢弃 | `src/cpu/o3/lsq.hh:609` | `LSQRequest::squashTranslation()`（置 `TranslationSquashed`，已 release 则自毁） |
| 请求派发（load → D-cache） | `src/cpu/o3/lsq_unit.cc:1617` | `LSQUnit::read(LSQRequest*, ssize_t)` → `sendPacketToCache` |
| load 执行入口 | `src/cpu/o3/lsq_unit.cc:715` | `LSQUnit::executeLoad(DynInstPtr)` → `inst->initiateAcc()` |
| initiateAcc | `src/cpu/o3/dyn_inst.cc:413` | `DynInst::initiateAcc()` |
| replay（ReExec，内存序违规） | `src/cpu/o3/lsq_unit.cc:599` | `ld_inst->fault = std::make_shared<ReExec>()` |
| `squash` 事件 | `src/cpu/o3/lsq_unit.cc:1208`（load_queue_uncommitted）、`:1287`（store_queue_uncommitted） | `LSQUnit::squash(InstSeqNum)` → `mmuNoteSquash` |

## 4. Commit 侧（O3）

| 事件 | 位置 | 所在函数 |
|---|---|---|
| 异常投递观测（`exception_delivery`） | `src/cpu/o3/commit.cc:1266` | `Commit::commitHead(DynInstPtr, unsigned)`；**`dynamic_cast<ReExec*>(inst_fault)==nullptr` 时才发射**（ReExec 是 replay 信号，非真实异常） |
| `commit` 事件 | `src/cpu/o3/commit.cc:1356` | `Commit::commitHead` → `mmuNoteCommit`（同处 `noteCommit` @1352） |

## 5. ARM Data Abort / Exception Delivery

| 项 | 位置 |
|---|---|
| `DataAbort` 异常类 | `src/arch/arm/faults.cc`：`DataAbort::ec` @1308、`il` @1337、`routeToMonitor` @1343、`routeToHyp` @1350、`iss` @1374、`annotate` @1403；`VirtualDataAbort::invoke` @1444 |
| 架构异常投递的**观测** | `src/cpu/o3/commit.cc:1266`（见上），**不在 faults.cc 内**。数据侧 Data Abort 的观测表现为 `translation_result(fault_status=Data)` + `squash`；本构建数据侧不发射独立 `exception_delivery` 事件（M07-C02 T01/T02 与 Control 的 `kind=exception_delivery` 计数均为 0） |

## 6. 数据侧 `exception_delivery` 缺省的说明

`exception_delivery` 事件由 `commit.cc:1266` 在为**取指指令**异常（M06 `PrefetchAbort`）到达
ROB 头时发射；数据侧 load/store 的 `DataAbort` 经 `translation_result(Data)` +
`squash`（`lsq_unit.cc:1208`）路径投递，不在 `commitHead` 产生该事件。故 M07-C02 故障
指令"无 exception_delivery"不能单独作为"未发生异常"的判据——Control 的正常拒绝 load
同样无此事件。

## 源码快照 SHA256

（当前磁盘残留 `CHAOS/gem5/src/` 快照；eb327/fb1b6f 构建所用源码未改动，逐文件 SHA256：）

| 文件 | SHA256 |
|---|---|
| `arch/arm/mmu.cc` | `1b042589b8bbab27f992a9c56309756a13858bfcf2bed9cc30f8ac21fbf71447` |
| `arch/arm/faults.cc` | `27d3d4d979490c91bf01947170f2dfe8c5b75fa629d69732c151bdc518f5dccb` |
| `cpu/o3/lsq.cc` | `6aca839cd2ca3d6e8e6c56862c53a6c92cb0449067e8616ba546f413cab060d0` |
| `cpu/o3/lsq_unit.cc` | `185b1fde6aaba14b8042227dc7035c1f2cdfd6c0fa69ba915d0192d6a988d7f3` |
| `cpu/o3/lsq.hh` | `2071bfa2da5393a7f32bf7b0094b57ac7e487813ac8965d8dc193bd627d84e5a` |
| `cpu/o3/commit.cc` | `11e03973929ac38e736ed5a7c500f617702a5d06facc0791143e4ce4732300aa` |
| `mem/cache/cache.cc` | `e94bfeece83de049db5737cba536edabe81a62f5e7d4f6927e8935ed201fa016` |
| `mem/cache/base.cc` | `d60848179b063d3c8648a279f39e85d28d17c7be9adb1a8805e9677cd06d06eb` |

构建哈希：`analysis/control_map.json`（eb327=`eb327197c073dddf…`、fb1b6f=`fb1b6f010034f273…`）。