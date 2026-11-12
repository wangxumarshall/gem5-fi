# SP05-R01..R05 — Store Commit / Writeback 只读 Hook 设计

- **Agent**：LSU v3.3.3 收口轮 Agent B（只读分析）
- **冻结基线**：HEAD `78ac9ba7`，二进制 `1126e0fd…`，config `8309da72…`（本报告未复核，沿用冻结事实）
- **证据**：`audit_v3_3_3/runs/SP05-R01-fault/` … `SP05-R05-fault/`（summary.json / pilot_meta.json / lsq_fwd_injections.log / trace_v31.jsonl / prop_trace.csv.gz / stats.txt）
- **判定工具**：`tools/lsu_v333_qualified.py`；规则说明 `audit_launch_fix_v333/artifacts/LSU_QUALIFIED_Context_Handling.md` §2
- **约束**：本报告只读；未运行 gem5，未修改 C++/Python/配置/历史证据。文中所有结论均给出源码行号或证据原文。

---

## 1. 结论摘要

1. **`commit_event` 可以用最小只读 Hook 补齐，且 `tools/lsu_v333_qualified.py` 无需任何改动。**
   工具已把 `store_commit` 列为合法的 commit 事件类型（`_COMMIT_TYPES = ("store_commit", "commit", "sq_commit")`，`tools/lsu_v333_qualified.py:470`），唯一拒绝条件是把 `commit_tick_source` 标成 `caller_supplied`。现状正是 `caller_supplied`（R01 注入记录原文：`commit_tick=16377515;commit_tick_source=caller_supplied`），因为 `writebackStores` 把 `curTick()` 同时当作 inject tick 与 commit tick 传了下去（`lsq_unit.cc:1081-1094`，`CHAOSPropagation.cc:1838-1845`）。
   在真实 commit 锚点 `Commit::commitHead`（`commit.cc:1318`）捕获该 store 的 `curTick()`/commit 序号，再在 SP05 注入时以同 ptag 的首节点写出 `store_commit`，即可让工具读到 `commit_tick_source=commit_stage_capture`，`commit_event` 变为 found。

2. **`writeback_event` 在本故障语义下无法被“诚实地”满足；这是字段语义与故障语义的结构性冲突，不是 Hook 质量问题。**
   SP05 的故障本身就是“cache write 未发送”（`mem_sent=0;drain_tick=0;write_skipped=1`）。规则第 7 条明确写着：`sp05_write_skipped (write_skipped=1) proves the writeback did **not** happen and therefore does not satisfy this field`（`LSU_QUALIFIED_Context_Handling.md` §2 SP05 第 7 项），代码同样在 `lsu_v333_qualified.py:572-573` 显式丢弃。任何“补一个 writeback 事件”的做法都是伪造，禁止。
   诚实做法：新增 `store_writeback_suppressed`（写回阶段**结果**观测：请求已存在、`request_sent=0`、`mem_sent=0`、`drain_tick=0`、`stores_to_wb_after` 为真实值），把“未写回”变成一条独立观测。它**不**满足现有 `writeback_event` 规则。

3. **qualified 判定结论（必须诚实）**：
   - 按**现行规则**：5 个 Fault run 由 `QUALIFIED / 10-of-12` 提升为 `QUALIFIED / 11-of-12`，唯一缺失仍是 `writeback_event`，terminal 仍含 `STORE_WRITEBACK_ABSENT`。`PASS` 不可达（除非改动规则）。
   - 只有在规则 owner（Agent D / 计划负责人）显式把第 7 项语义修订为“writeback stage outcome（sent **or** suppressed）”，并接受 `store_writeback_suppressed` 后，才可能升级为 `PASS`。届时 terminal 会是 `APPLICATION_ORACLE;ORACLE_FAIL_SDC`——`PASS` 只表示“因果链被本 run dir 完整记录”，不表示 oracle 通过（该语义与 `LSU_QUALIFIED_Context_Handling.md` §1 优先级表一致）。
   - 无论是否修订，oracle 结果仍是 `ORACLE_FAIL_SDC`（expected=`7df5034c23f3e703`，got 各 run 不同），Hook 不得改变它。

4. **顺序无歧义**：SP05 目标 store 的架构 commit **结构性地必然早于**注入。canWB/选择只会在 `seqNum <= doneSeqNum` 时发生，而 `doneSeqNum` 来自更早一个 cycle 的 Commit stage；同 cycle 内 `writebackStores()` 又先于 `commitStores()` 执行（`iew.cc:1486` vs `1494`），所以最早也要到选择后的下一个 cycle 才可能注入。实测日志同样显示 `Cycle: 42538, Site: commitStores_select` → `Cycle: 42539, Site: writebackStores_prematureComplete`（`SP05-R01-fault/lsq_fwd_injections.log:1-2`）。

---

## 2. 真实 gem5 事件路径（文件:行号 + 函数 + 片段）

阶段序（同一 CPU tick 内 `iew.tick()` 先于 `commit.tick()`，`cpu.cc:388/390`）：

| # | 语义阶段 | 函数 | 位置 | 关键代码 |
|---|---|---|---|---|
| 1 | 指令在 ROB 头退休（**架构 commit**） | `Commit::commitHead` | `CHAOS/gem5/src/cpu/o3/commit.cc:1318` | `chaosPropagation->noteCommit(tid, head_inst.get());` |
| 1a | commit tick 落账 | 同上 | `commit.cc:1329` | `head_inst->commitTick = curTick() - head_inst->fetchTick;` |
| 2 | LSQ 得知“已提交”（可写回） | `LSQUnit::commitStores` | `lsq_unit.cc:989-1018` | `if (x.instruction()->seqNum > youngest_inst) break;` (1000) / `x.canWB() = true;` (1008) / `++storesToWB;` (1010) |
| 2a | 调用点（`youngest_inst = doneSeqNum`） | `iew.cc:1494` | `ldstQueue.commitStores(fromCommit->commitInfo[tid].doneSeqNum,tid);` |
| 2b | SP05 选择点 | `maybeSelectSP05` | `lsq_unit.cc:1011-1015` | `cpu->lsqFwd->maybeSelectSP05(seqNum, sqIdx, sqEntryGeneration, x.size(), …)` |
| 3 | **写回路径**（把 SQ 数据发往 cache） | `LSQUnit::writebackStores` | `lsq_unit.cc:1030-1207` | while 条件 1038-1043（`storesToWB>0 && storeWBIt->canWB() && lsq->cachePortAvailable(false)`） |
| 3a | 0 字节 store（不写内存） | 同上 | `lsq_unit.cc:1053-1059` | `completeStore(storeWBIt++); continue;` |
| 3b | data prefetch 跳过 | 同上 | `lsq_unit.cc:1061-1064` | `storeWBIt++; continue;` |
| 3c | **SP05 提前完成分支** | 同上 | `lsq_unit.cc:1072-1101` | 见 §3 |
| 3d | 标记已 committed、打包、记录写回、**发送** | 同上 | `1117` / `1127` / `1132-1143` / `1195` | `storeWBIt->committed() = true;` / `request->buildPackets();` / `noteStoreWriteback(...)` / `request->sendPacketToCache();` |
| 4 | SQ 条目完成 + `storesToWB--` | `LSQUnit::completeStore` | `lsq_unit.cc:1455-1530` | `store_idx->completed() = true; --storesToWB;` (1462-1463) |
| 4a | SP05 完成记录 | 同上 | `lsq_unit.cc:1510-1515` | `cpu->lsqFwd->consumeSP05Trace(...)` → `noteSP05Complete(...)` |
| 5 | LSQ 分发 | `LSQ::commitStores` / `LSQ::writebackStores` | `lsq.cc:310-313` / `316-326` | 逐 tid 调用 |

**四个阶段必须分开（本设计的语义基础）**：

- **SQ 条目完成（completed）**：`completeStore()` 置 `completed()=true` 并把 `storesToWB` 递减（`lsq_unit.cc:1462-1463`）。它只说明 SQ 资源可回收，**不等于**指令已 commit。
- **指令 commit**：`Commit::commitHead` 退休 ROB 头 + `retireHead`（`commit.cc:1318-1333`）。一个 store 只有在 commit 之后才会被 `commitStores()` 授予 `canWB`（`lsq_unit.cc:1000-1008`）——所以“canWB 的 store 必然已 commit”。
- **写回内存（writeback/send）**：`request->sendPacketToCache()`（`lsq_unit.cc:1195`）才把数据送出 SQ；`noteStoreWriteback()` 在发送前记录（`1132-1143`）。SP05 分支在 `1100` 处 `continue`，永远到不了这里。
- **对后续 Load 可见**：cache/内存侧 `BaseCache::updateBlockData`（`noteStoreMemWrite` 的调用侧）以及更下游 `memory_response`。SP05 的反面证据是 reload 在同一 VA 读回了旧值（R01：`memory_response` `data_fnv=a8c7f832281a39c5`，而 store 的 `store_data_fnv=b6180e0c195fd2e9`）。

---

## 3. SP05 注入点与“跳过写回”的机制

### 3.1 选择（commitStores）

`CHAOSLSQFwd::maybeSelectSP05`（`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:535-563`）：

```cpp
if (probability <= 0.0f || sp05_fired || sp05_selected) return false;
if (!chaos_sp05::isSelectable(size, is_prefetch)) return false;   // size>0 && !prefetch
++eligible_count;
if (!chaos_sp05::shouldSelect(eligible_count, sp05_event_ordinal)) return false;
sp05_selected = true; sp05_target_seq = ...; sp05_target_idx = ...; sp05_target_gen = ...;
```

`shouldSelect` 的注释明确：*“The fault is applied to the Nth store that earns canWB (a live, committed store)”*（`sp05_rules.hh:13-19`）。选择只记录目标身份，**不改变任何 CPU 状态**。

### 3.2 注入（writebackStores，跳过 send）

`lsq_unit.cc:1072-1101`：

```cpp
if (cpu->lsqFwd && !request->isSent() &&
    cpu->lsqFwd->maybeCompleteSP05(inst->seqNum, inst->sqIdx,
                                   inst->sqEntryGeneration, false)) {
    ...
    const Tick sp05_tick = curTick();
    if (cpu->chaosPropagation)
        cpu->chaosPropagation->noteSP05Injection(... mem_sent=false ...);
    completeStore(storeWBIt);
    ...
    continue;                     // <-- 跳过 1117 committed=true / 1127 buildPackets / 1132 store_wb / 1195 sendPacketToCache
}
```

`maybeCompleteSP05`（`CHAOSLSQFwd.cc:575-604`）要求 `sp05_selected`、`!request_sent`、SQ 身份 `(idx,gen)` 完全匹配、`injected < max_faults`，然后 `sp05_fired=true; ++faults_injected_count; sp05_pending_trace=true;`。

`completeStore(storeWBIt)`（`lsq_unit.cc:1095`）保持 `+1/-1` 配对（`storeWBIt` 不回退，`storesToWB` 由 `completeStore` 递减），随后 `consumeSP05Trace`（`lsq_unit.cc:1510-1515`）只消费一次 trace 标记，避免普通完成误记。

**机制后果**：`request` 从未 `sendPacketToCache()`；`storeWBIt->committed()` 保持 false；`buildPackets()` 从未执行；`noteStoreWriteback()`（即 `store_wb` 节点，`prop_trace_to_v31.py:50` 映射为 `store_writeback`）从未调用。因此：

- `drain_tick = 0`（`noteSP05Injection` 硬编码，`CHAOSPropagation.cc:1904`）；
- `mem_sent = 0`（`CHAOSPropagation.cc:1859`、`1898`）；
- 之后的 reload 在同一 VA 读到未写入的旧值（5 个 run 全部 `reload_data_hash=a8c7f832281a39c5`，即零字）。

实测 tick 对齐（R01）：注入/`sp05_write_skipped`/`sp05_complete` 三者均为 `16377515`；同 seq 的 `commit` / `store_writeback` / `store_mem_write` 记录数均为 **0**。

---

## 4. 现有 5 个 run 的字段缺失根因

### 4.1 逐 Context 证据（`python3 tools/lsu_v333_qualified.py SP05 <dir>` 实测输出）

| Context | store_seq | store_pc | sq_entry/gen | store_addr | store_data_fnv | 注入 tick | reload seq/hash | status | missing |
|---|---|---|---|---|---|---|---|---|---|
| R01 | 13328 | 0x40053c | 956/1306 | 0x4919f0 | `b6180e0c195fd2e9` | 16377515 | 13330 / `a8c7f832281a39c5` | QUALIFIED | commit_event, writeback_event |
| R02 | 15122 | 0x40053c | 982/1332 | 0x491ac0 | `9f995d89be67e92d` | 17006605 | 15124 / `a8c7f832281a39c5` | QUALIFIED | 同上 |
| R03 | 16847 | 0x40053c | 1007/1357 | 0x491b88 | `fde383c67ac034f1` | 17493245 | 16849 / `a8c7f832281a39c5` | QUALIFIED | 同上 |
| R04 | 18641 | 0x40053c | 1033/1383 | 0x491c58 | `aa2be3d3d60e3c9d` | 17992205 | 18643 / `a8c7f832281a39c5` | QUALIFIED | 同上 |
| R05 | 20435 | 0x40053c | 1059/1409 | 0x491d28 | `c7d78aff5e06edf9` | 18633230 | 20437 / `a8c7f832281a39c5` | QUALIFIED | 同上 |

5 个 run 的 terminal 均为 `APPLICATION_ORACLE;ORACLE_FAIL_SDC;STORE_COMMIT_ABSENT;STORE_WRITEBACK_ABSENT`；`evidence.commit_tick_source` 均为 `caller_supplied`。

run 参数（`pilot_meta.json` / `summary.json.fault_command`）：

| Context | seed | sp05_event_ordinal |
|---|---|---|
| R01 | 1489155957 | 952 |
| R02 | 1290498198 | 978 |
| R03 | 2768710389 | 1003 |
| R04 | 2741073922 | 1029 |
| R05 | 4098160626 | 1055 |

### 4.2 `commit_event` 缺失根因：**记录不存在**（不是字段为空，也不是被过滤）

1. 目标 store commit 时，tracer 还不知道它是 SP05 目标：`fault_seqs.insert(dyn_seq)` 发生在 `noteSP05Injection`（`CHAOSPropagation.cc:1871`），而 commit 发生在它之前。
2. `noteCommit` 只为 `fault_tracked || replay_tracked` 的指令写 `commit` 节点（`CHAOSPropagation.cc:2536-2553`），因此该 store 没有 commit 节点（实测 5 个 run 均为 0 条）。
3. `noteCommit` 里已有的“fault store commit tick 回填”只查 `fault_store_registry`（`CHAOSPropagation.cc:2524-2534`），而该 registry 条目同样在注入时才创建（`1886`），commit 时查不到，故真实 commit tick 从未被捕获。
4. 注入记录里的 `commit_tick` 是 `writebackStores` 的 `curTick()`：`lsq_unit.cc:1081-1085` 注释直言 *“that tick is not exposed here … the writebackStores observation tick”*；`CHAOSPropagation.cc:1842-1845` 把它标成 `commit_tick_source = commit_tick ? "caller_supplied" : "injection_bound_curTick"`。工具在 `lsu_v333_qualified.py:545-547` 明确拒绝 `caller_supplied`。
   → 结论：**“记录不存在 + 现存 tick 被合法的 caller_supplied 排除”**，二者叠加。

### 4.3 `writeback_event` 缺失根因：**该事件本就不存在（故障语义），且负证据被规则显式排除**

1. 没有 `store_writeback` 记录：SP05 分支在 `lsq_unit.cc:1100` `continue`，永远到不了 `1132-1143` 的 `noteStoreWriteback`（实测每 run 0 条 `store_writeback`、0 条 `store_mem_write`）。正常 store 在同样位置也不会被注册，因此“没有 store_wb”本身不构成独立证明——真正的负证据是 `request` 在 `sendPacketToCache()`（1195）之前被跳过，加上 reload 读回旧值。
2. `sp05_write_skipped` 记录存在（`write_skipped=1;mem_sent=0;drain_tick=0`），但 `LSU_QUALIFIED_Context_Handling.md` §2 SP05 第 7 项与代码 `lsu_v333_qualified.py:572-573`（`writeback_event = None  # skipped write is the fault, not a writeback`）**显式拒绝**用它冒充。
3. `sp05_stage.writeback_tick` 目前等于注入 tick（`CHAOSPropagation.cc:2876` `st.writeback_tick = (uint64_t)e.registered;`）——它表示“`writebackStores` 处理了该条目”（`sp05_rules.hh:88` 的定义），**不是** cache write，因此也不满足规则里“store data reaching memory/writeback queue”的含义。
4. 工具的最后一个可行分支 `stores_to_wb_after > 0 && mem_sent == 1`（`lsu_v333_qualified.py:574-577`）在 SP05 下永远不成立（`stores_to_wb_after=0`）。

---

## 5. 最小只读 Hook 设计

### 5.0 事件格式与 id 的来源（先厘清，避免“Hook 写 event_id”的误解）

C++ 侧只写 CSV 列：`node_id, tick, ptag, kind, dyn_seq, req_id, addr, phys, arch, detail`（`CHAOSPropagation.cc:184-223`）。JSONL 的 `event_id` / `parent_event_id` / `fault_id` 由转换器 `docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py`（`run_pilot.py:48` `from tools.prop_trace_to_v31 import convert`）生成：

- `event_id` = TraceWriter 递增编号；
- `parent_event_id` = `last_by_ptag[ptag]`（转换器 `393` 行），并为每个同 ptag 相邻节点补一条 `ptag_sequence` 边（`591-611` 行）；
- `fault_id` 由 pilot 元数据（`SP05-CFG01`）写入，不来自 Hook。

因此 **Hook 连接父/子的手段 = 给新节点分配同一个 ptag，并保证写入顺序**（commit → injection → writeback_suppressed）。未知 kind 已经能透传（`KIND_MAP.get(kind, kind)`，转换器 `546` 行）；建议同时在 `KIND_MAP`/`UNIT_MAP` 增加条目以固定 unit/sub_unit。

### 5.1 H1 — commit 观测捕获（无 trace 记录，纯内存）

**位置**：`CHAOSPropagation::noteCommit()`，`CHAOSPropagation.cc:2510-2534`（在 `++commit_seq` 之后）。

```cpp
// [SP05 read-only] capture the real architectural commit of every store
// while SP05 is mounted; the target is only selected later (commitStores),
// so the capture cannot wait for the target identity.
if (head_inst->isStore() && o3cpu->lsqFwd && o3cpu->lsqFwd->sp05Mode()) {
    StoreCommitObs o;
    o.commit_tick = curTick();
    o.commit_seq  = commit_seq;          // tracer-wide commit ordinal (line 2515)
    o.pc = pc; o.sq_idx = head_inst->sqIdx;
    o.sq_gen = head_inst->sqEntryGeneration;
    o.size = head_inst->effSize;
    o.execution_attempt_id = head_inst->executionAttemptId;
    o.replay_generation = head_inst->replayGeneration;
    store_commit_obs[head_inst->seqNum] = o;
}
```

- 只读：读取 `DynInst` 字段 + `curTick()`；不触碰 ROB/LSQ/rename 状态，不消耗 RNG。
- `o3cpu->lsqFwd` 是 `o3::CPU` 的公开成员（`cpu.hh:546-548`）；需在 `CHAOSPropagation.cc` 增加 `#include "cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh"`（当前只 include 了 `sp05_rules.hh`）。
- 只在 sp05 模式下执行；其它模型/未挂载时零开销。

### 5.2 H2 — `store_commit` 事件（每 fault run 1 条）

**位置**：`CHAOSPropagation::noteSP05Injection()`（`CHAOSPropagation.cc:1809`）内，**先分配 ptag、先写 commit 节点**，再写现有 `inj_sp05`。

```cpp
const uint64_t ptag = ++next_ptag;                 // 从 1869 行前移
auto co = store_commit_obs.find(dyn_seq);
if (co != store_commit_obs.end()) {
    std::ostringstream c;
    c << "site=commit_commitHead;family=sp05;model=SP05"
      << ";trigger=sp05_target_store_commit"
      << ";store_seq=" << dyn_seq
      << ";store_pc=0x" << std::hex << co->second.pc << std::dec
      << ";sq_entry_id=" << co->second.sq_idx
      << ";sq_entry_generation=" << co->second.sq_gen
      << ";store_size=" << co->second.size
      << ";commit_tick=" << co->second.commit_tick
      << ";commit_seq=" << co->second.commit_seq
      << ";commit_state=ARCHITECTURAL_COMMIT"
      << ";commit_tick_source=commit_stage_capture"
      << ";observation_tick=" << curTick()
      << ";execution_attempt_id=" << co->second.execution_attempt_id
      << ";replay_generation=" << co->second.replay_generation;
    writeNode(ptag, "store_commit", dyn_seq, true, 0, false,
              inst_addr, true, 0, false, 0, false, c.str(),
              co->second.commit_tick);              // node timestamp = real commit tick
}
// ... 现有 inj_sp05（同一 ptag，随之成为父节点子事件）
```

- 记录类型名 `store_commit` 直接命中工具 `_COMMIT_TYPES`（`lsu_v333_qualified.py:470`），`commit_tick_source` 不是 `caller_supplied`（`545-547` 不会跳过），**工具无需改动**即把 `commit_event` 判为 found。
- `writeNode` 的第 14 个参数（`tick`）让节点时间戳等于真实 commit tick（`CHAOSPropagation.cc:184-190`），而发射发生在注入时刻——时间语义正确，父子链由 ptag 顺序保证（commit 先写 → `inj_sp05.parent = store_commit`）。
- 若 `store_commit_obs` 找不到该 seq（例如 trace 关闭或异常路径），**不写** `store_commit`，并在 injection detail 中写 `commit_observed=0;commit_tick=0;commit_tick_source=none`，绝不回填注入 tick。

### 5.3 H3 — `store_writeback_suppressed` 事件（每 fault run 1 条；负证据）

**位置**：`lsq_unit.cc` SP05 分支，`completeStore(storeWBIt)` 之后（约 `1095` 行后），此时 `storesToWB` 已递减。

```cpp
if (cpu->chaosPropagation)
    cpu->chaosPropagation->noteSP05WritebackSuppressed(
        inst->seqNum, inst->sqIdx, inst->sqEntryGeneration,
        request->mainReq()->getSize(),
        /*request_present=*/1, /*request_sent_before=*/0,
        /*request_sent_after=*/request->isSent(),   // false：sendPacketToCache 未执行
        /*mem_sent=*/0, /*write_skipped=*/1, /*drain_tick=*/0,
        /*stores_before=*/sp05_stores_before, /*stores_after=*/storesToWB,
        curTick());
```

detail（同一 ptag，写在 `inj_sp05` 之后）：

```
site=writebackStores_sp05Branch;family=sp05_complete;model=SP05
writeback_state=SUPPRESSED_BEFORE_SEND;writeback_stage_entered=1
request_present=1;request_sent_before=0;request_sent_after=0
mem_sent=0;write_skipped=1;drain_tick=0;visibility_tick=0
visibility_state=NEVER_WRITTEN
store_seq=…;sq_entry_id=…;sq_entry_generation=…;store_size=…
stores_to_wb_before=…;stores_to_wb_after=…;cache_port_available=1
tick=…
```

- 这是**“写回阶段发生了，但 send 被抑制”**的独立观测，也是 `request_sent_after=0` 的直接事实；它与 reload 的 `memory_response`（同 VA 读回旧值）共同构成“写未发生”的双证据。
- **命名刻意不含 `writeback` 的“已完成”语义**：type 为 `store_writeback_suppressed`，不进入工具 `_WRITEBACK_TYPES`，因此不会冒充 `writeback_event`。
- `visibility_tick` 保持 `0`（从未可见），另给 `visibility_state=NEVER_WRITTEN`；不伪造可见 tick。

### 5.4 H4 — 修正现有 `commit_tick` / `sp05_stage.commit_tick` 的诚实性（无新记录）

- `noteSP05Injection` 的 `Tick commit_tick` 入参改为内部查 `store_commit_obs`；删除 `commit_tick ? commit_tick : inject_tick` 回退（`CHAOSPropagation.cc:1838-1845`）与 `lsq_unit.cc:1081-1085` 的“同一 tick 兼任”注释。injection 记录输出真实 `commit_tick`。
- `FaultStoreEntry::store_commit_tick` 在注册时填真实 commit tick（`CHAOSPropagation.cc:1885`），使 `sp05_stage.commit_tick`（`2907`）成为真实架构 commit tick，而不是注入 tick。
- `sp05_stage` 增加 `writeback_state=SUPPRESSED_BEFORE_SEND;request_sent=0`（`CHAOSPropagation.cc:2900-2910` 的 detail 拼接），让 `writeback_tick` 不被误读为 cache write。

### 5.5 字段映射表（统一事件格式）

| 字段 | 含义 | 来源 | 只读 |
|---|---|---|---|
| `fault_id` | `SP05-CFG01` | TraceWriter/pilot 元数据（非 Hook） | 是 |
| `event_id` | JSONL 事件 id | TraceWriter 递增（非 Hook） | 是 |
| `parent_event_id` | 同 ptag 前一节点 | 转换器 `last_by_ptag`（393 行） | 是 |
| `dyn_inst_seq` | store 的动态序号 | `inst->seqNum` / `head_inst->seqNum` | 是 |
| `pc` | store PC | `pcState().instAddr()`（commit 用 `head_inst`；注入用 `inst`） | 是 |
| `sq_entry_id` | SQ 索引 | `inst->sqIdx` / `head_inst->sqIdx` | 是 |
| `sq_entry_generation` | SQ 代际 | `inst->sqEntryGeneration` | 是 |
| `store_addr` | 目标 store VA | `inst->effAddr`（注入点） | 是 |
| `store_data_fnv` | 被丢弃字节的 FNV-1a-64 | `storeWBIt->data()` + `request->_size`（已有 `fnvHex`） | 是 |
| `commit_seq` | tracer 全局 commit 序数 | `noteCommit` 的 `++commit_seq`（`CHAOSPropagation.cc:2516`） | 是 |
| `commit_tick` | **真实**架构 commit tick | H1 `curTick()`（H2 以 `writeNode` tick 参数写入） | 是 |
| `commit_state` | `ARCHITECTURAL_COMMIT` | 常量 | 是 |
| `commit_tick_source` | `commit_stage_capture` | 常量（H4 去掉 caller_supplied） | 是 |
| `writeback_state` | `SUPPRESSED_BEFORE_SEND` | H3 常量 | 是 |
| `mem_sent` | 0 | 分支事实（`sendPacketToCache` 未执行） | 是 |
| `write_skipped` | 1 | 分支事实 | 是 |
| `visibility_tick` | 0（从未可见） | 常量；另 `visibility_state=NEVER_WRITTEN` | 是 |
| `stores_to_wb_before/after` | `completeStore` 前后值 | `lsq_unit.cc` 局部变量 | 是 |
| `request_sent_before/after` | `request->isSent()` | `LSQRequest` 只读查询 | 是 |
| `observation_tick` | 节点写出时的 `curTick()` | H2/H3 | 是 |

### 5.6 父链与顺序

```
store_commit (ptag=P, timestamp=真实 commit tick, parent=null)
  └─ inj_sp05          (parent = store_commit)
       └─ store_writeback_suppressed (parent = inj_sp05)
            └─ sp05_write_skipped    (parent = suppressed)
                 └─ sp05_complete    (parent = skipped)
                      └─ memory_request(reload, store_not_written_yet=1)
                           └─ memory_response(reload 旧值) → register_writeback → consumer_commit → errant_commit
                                                                    └─ sp05_stage (deferred chain record, ptag=P)
```

**commit 在注入之前发生的处理**：不需要特殊分支。SP05 的 `canWB` 来自 `commitStores(doneSeqNum)`，因此 commit 必然已完成；H1 在 commit 时无条件捕获，H2 在注入时取用。验证器只需断言 `commit_tick < inject_tick` 且 `store_commit.timestamp == commit_tick`。若捕获缺失，记录 `commit_observed=0` 并保持 `commit_event` 缺失（不升级）。

---

## 6. Behavior Impact / Binary Impact / Thread-safety / Overhead

### 6.1 行为影响（逐项声明：全部为“否/无变化”）

| 项目 | 结论 | 依据 |
|---|---|---|
| 指令执行顺序 | 不改变 | H1 只读 `DynInst` 字段；H2/H3 在既有分支之后写 trace；不改 ROB/SQ/LQ |
| LSU 调度 / `canWB` / `storesToWB` | 不改变 | H3 只读取 `completeStore` 后的计数；H1 不接触 LSQ |
| store/load 决策、forwarding、replay | 不改变 | 未触碰任何决策点；无新条件分支影响控制流（H2/H3 位于 `continue` 之后） |
| commit 决策 | 不改变 | H1 在 `noteCommit` 内部，commit 已发生 |
| 注入时间/概率/状态 | 不改变 | 不消耗 `std::mt19937`、不调用 `maybeCompleteSP05`；选择的 ordinal 计数路径未变 |
| 新增事件调度 | 无 | 不 `schedule()` 任何 Event；无新 SimObject/参数/配置 |
| 控制组（probability=0） | 仍 0 注入、0 新记录 | `maybeSelectSP05` 在 `probability<=0` 直接返回 false（`CHAOSLSQFwd.cc:542`）；H2/H3 只在选中/注入时发射 |

### 6.2 Binary / 产物影响

- **二进制 SHA 必然变化**：`CHAOSPropagation.cc/.hh`、`lsq_unit.cc`（H1–H4）。冻结的 `1126e0fd…` 及所有引用它的 manifest 必须重新冻结；需按补丁纪律单独提交并重建（`scons -j16 build/ARM/gem5.opt`，clean 必须 `-j16`）。
- Python 侧可选：`docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py` 的 `KIND_MAP`/`UNIT_MAP` 增加 `store_commit`、`store_writeback_suppressed`（未知 kind 已能透传，`546` 行 `KIND_MAP.get(kind, kind)`，所以不加也不会丢记录，但 unit/sub_unit 会是 `Unknown`）。这是 Python-only 改动，无需重编译。
- trace_v31.jsonl：每 fault run **+2 条记录**（`store_commit`、`store_writeback_suppressed`），`event_id` 其后整体平移，`next_ptag` 不变；`chain_events` 计数 +2。现有按 event_type 取值的工具（`lsu_v333_propagation.py`、`lsu_v333_qualified.py`、`lsu_propagation_audit.py`）不受影响；但任何断言“精确行数/事件 id”的测试需同步更新。
- `tools/lsu_v333_qualified.py`：**不需要修改**即可让 `commit_event` 变为 found；`writeback_event` 的规则修订是独立决策（见 §8）。

### 6.3 线程安全

- gem5 O3 是单线程事件驱动仿真；所有 Hook 都在所属 CPU 的 tick 上下文同步执行，不存在并发调用，**无需加锁，也不存在锁顺序问题**。
- `CHAOSPropagation` 是 per-CPU 单实例；SMT 下每个 tid 有独立 `LSQUnit`，但 `dyn_seq` 全局唯一，`unordered_map` 键不会冲突；调用仍串行。
- H3 只拷贝标量（不保留 SQ 迭代器/引用跨 tick），避免 `completeStore` 清空 `storeQueue` 后的悬垂。
- trace 写入是既有单线程 `gzwrite + Z_SYNC_FLUSH` 契约（`CHAOSPropagation.cc:214-219`），新增记录沿用同一路径。

### 6.4 开销

- H1：仅 sp05 模式下，每条 commit 的 store 做一次 `isStore()` 判断 + 一次 `unordered_map` 插入（该 workload 约 2–4k stores；普通指令仅一次 `isStore()`）。相对每 tick 的 O3 仿真可忽略。
- H2/H3：每 run 各 1 条记录 + 1 次 `Z_SYNC_FLUSH`（约百字节）；gzip 同步刷新是本已存在的 per-node 契约。
- H4：零额外记录（仅文本字段）。
- 内存：`store_commit_obs` 最多 O(#stores) 个 64–88B 结构；建议在 H2 发射后 `erase(seq)`，并在超过阈值（例如 1<<20）时打印一次 honest 计数告警，防止超长 run 无限增长。

---

## 7. Validation 方案与预期判定

### 7.1 构建

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/CHAOS/gem5 && scons -j16 build/ARM/gem5.opt
```

（引用 repo-root `build/ARM/gem5.opt`，不要用 `CHAOS/gem5/build/ARM`。）

### 7.2 5 个 SP05 Fault 定向 Pilot（**新 outdir，绝不覆盖历史证据**）

模板（R01；来自 `SP05-R01-fault/summary.json.fault_command` 原文）：

```bash
build/ARM/gem5.opt \
  --outdir=<NEW>/SP05-R01-fault \
  configs/se/lsu_proxy.py \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212 \
  --cpu O3 --variant B0 --probability 1.0 \
  --chaos_propagation --prop_trace_file prop_trace.csv.gz \
  --chaos_lsqfwd --lsq_struct_mode sp05_complete \
  --max_faults 1 --rng_seed 1489155957 --sp05_event_ordinal 952 \
  --sp05_watchdog_cycles 500000000
```

R02–R05 除 `--outdir` / `--rng_seed` / `--sp05_event_ordinal` 外完全相同：

| Context | seed | ordinal |
|---|---|---|
| R01 | 1489155957 | 952 |
| R02 | 1290498198 | 978 |
| R03 | 2768710389 | 1003 |
| R04 | 2741073922 | 1029 |
| R05 | 4098160626 | 1055 |

控制组：同命令把 `--probability 1.0` 改为 `--probability 0.0`，其余（含 seed/ordinal）不变；这与 `SP05-R0k-control/command.txt` 完全一致，其 `control_proof` 必须仍为 `MOUNTED_BUT_DISABLED`、`injection_count=0`、`oracle=True`。

建议输出到 `audit_v3_3_3/trace_closure/runs/SP05-R0k-{fault,control}/`，再用既有 pipeline 生成 `trace_v31.jsonl`（`run_pilot.py:1199` 走 `tools.prop_trace_to_v31.convert`）。

### 7.3 断言（每个事件字段可从 trace 解析、无重复/丢失、不影响 oracle）

1. **存在性**：每个 fault run 恰有 1 条 `store_commit`、1 条 `store_writeback_suppressed`、1 条 `injection`、1 条 `sp05_write_skipped`、1 条 `sp05_complete`、1 条 `sp05_stage`；每个 control run 这些类型均为 0 条（`injection` 也为 0）。
2. **一致性**：`store_commit` 与 injection 的 `dyn_inst_seq / pc / sq_entry_id / sq_entry_generation` 完全相同；`store_writeback_suppressed` 的 `store_seq` 与 `store_size` 与 injection 一致。
3. **顺序**：`commit_tick < inject_tick`；`store_commit.timestamp == commit_tick`；日志 `commitStores_select` cycle < `writebackStores_prematureComplete` cycle（R01 基线为 42538 → 42539）。
4. **父链**：`store_commit.parent_event_id == null`；`injection.parent_event_id == store_commit.event_id`；`sp05_write_skipped.parent_event_id == store_writeback_suppressed.event_id`；同 ptag 存在 `ptag_sequence` 边。
5. **无重复/丢失**：全 trace 中 `(dyn_inst_seq, event_type)` 对上述类型唯一；`sp05_*` 记录仍全部挂在同一 ptag。
6. **诚实性**：`store_commit.commit_tick_source == commit_stage_capture`（不得出现 `caller_supplied`）；`store_writeback_suppressed.mem_sent==0 && request_sent_after==0 && drain_tick==0 && write_skipped==1`；`visibility_tick==0`；`sp05_stage.commit_tick == store_commit.commit_tick`。
7. **qualified 判定**：`python3 tools/lsu_v333_qualified.py SP05 <dir>` 输出 `missing == ["writeback_event"]`、`status == "QUALIFIED"`、`terminal_rule == "APPLICATION_ORACLE;ORACLE_FAIL_SDC;STORE_WRITEBACK_ABSENT"`（规则未修订时）。若规则修订接受负证据，则期望 `missing == []`、`status == "PASS"`。
8. **oracle 不变**：`oracle.log` 的 `expected=7df5034c23f3e703` 与各 run 的 `got=` 必须与冻结基线逐字节相同（R01 `c7a1b3a591c68328`、R02 `34890178967da568`、R03 `225c6839dd319a5c`、R04 `d42d86ee46895884`、R05 `c6e1c98b1480efd4`）；`reload_data_hash` 仍为 `a8c7f832281a39c5`。
9. **回归**：SP05 5 个 Control 的 `injection_count=0` + `oracle=True`；另跑至少一个非 SP05 模型（如 DA04 或 SQ03 的单 Pilot）与 `reg_chain` 金标（`f247ef3fe6f02cfd`），要求 `exit: pass`、无 SIGSEGV。
10. **确定性与无副作用**：同一 seed/ordinal 连跑 3 次，新记录字段逐字节一致；`stats.txt` 中 simTicks / committed instructions 与基线相同（Hook 不改变时序）。

---

## 8. 残余风险与不可行点

1. **`writeback_event` 的规则冲突（最主要）**：在“SP05 = 无写回”的语义下，任何真实写回记录都不存在。若 owner 坚持字段语义为“数据到达 cache/写回队列”，**SP05 永远无法 PASS**，最优就是 `QUALIFIED`（11/12）。这不是 Hook 能修复的，必须由规则 owner 明确修订（建议把字段改名为 `writeback_outcome` 并接受 `SUPPRESSED_BEFORE_SEND`），且修订本身要有独立提交与记录。Agent B 不擅自宣称可 PASS。
2. **负证据的“独立性”边界**：`store_writeback_suppressed` 与注入点同一函数、同一 tick（它们本来就是同一个决策的两面）。它能证明的是“请求存在、未发送、drain=0”，但不能单独证明“内存里仍是旧值”；后者依赖 reload 的 `memory_response`（同 VA、旧哈希）。报告与验证应把两者作为一对证据，不把任一单独当作充分证明。
3. **commit 节点在注入时刻才落盘**：时间戳是真实 commit tick（`writeNode` 的 tick 参数），但“写入文件”发生在注入回调内。若审查方要求“commit 记录必须在 commit 当拍写入磁盘”，可改为在 `commitStores` 选中目标时立即分配 ptag 并发射（H2 前移），代价是 `noteSP05Injection` 需要复用预分配的 ptag；两种方案在证据语义上等价，选用后者时应在计划中写明。
4. **未过滤 LLSC / release store**：`maybeSelectSP05` 只过滤 `size==0`、prefetch（`sp05_rules.hh:24-28`），而 SP05 分支位于 LLSC/release 的队头检查（`lsq_unit.cc:1105-1115`）之前。若某个 ordinal 落在 SC/release store 上，注入还会绕过 TSO 排序规则，改变被建模故障的语义。本 5 个 run 的目标 PC 均为 `0x40053c`（普通 store），但设计应把 `is_llsc / is_release` 写入 `store_commit`/injection 记录，并在后续补丁中把 LLSC/release 排除出可选项（该改动改变注入行为，必须单独评审，不能夹带在本 Hook 中）。
5. **`store_commit_obs` 增长**：仅在 sp05 模式累积；建议发射后 erase + 上限告警（见 §6.4），否则超长 run 内存线性增长。
6. **trace/工具口径变化**：新增 2 条记录会改变 `chain_events`、事件 id、`propagation_stages` 等派生量；`audit_v3_3_3` 的矩阵/报告数字需重算，任何“历史 run 与新 run 直接对比 event id”的做法都不成立（应按 ptag/seq 对齐）。
7. **控制组零记录依赖**：H2/H3 的发射必须严格 gate 在“选择成功 / 注入发生”之后。若误在 capture 阶段写 trace，控制组会出现 `store_commit` 记录并破坏 `MOUNTED_BUT_DISABLED` 的零注入证明；验证断言 1 专门覆盖此点。
8. **是否值得做**：收益是把 `commit_event` 从“caller_supplied 的伪造 tick”变成真实、独立、可校验的 commit 观测（QUALIFIED 10/12 → 11/12，且消除 STORE_COMMIT_ABSENT）；代价是一次 C++ 改动 + 新二进制 SHA + 10 次定向 Pilot 重跑。`writeback_event` 不会因此解决，是否投入取决于 owner 对 §8.1 规则修订的决定。
