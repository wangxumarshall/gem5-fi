# RP01 内部 Watchdog 终止路径 Trace Flush 设计（LSU v3.3.3 收口轮）

- 角色：Agent C（只读分析）
- 工作目录：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
- 基线：HEAD `78ac9ba7`；冻结二进制 `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`；config `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
- 说明：本文件是**设计文档**，不是实现。所有"现有行为"结论均引用源码行号或证据原文；所有"建议"均显式标注为建议。本轮未运行 gem5，未改动任何 C++/Python/配置/历史证据。
- 证据根：`audit_v3_3_3/runs/RP01-R01-fault/` … `RP01-R05-fault/`、`RP01-R01-control/`

---

## 1. 结论摘要

**能否获得完整终止前 trace？**

- **已经可以获得、且当前并未丢失的是"终止前的全部历史节点"**：`prop_trace.csv.gz` 采用裸 zlib 流 + 每节点 `gzflush(Z_SYNC_FLUSH)`（`CHAOSPropagation.cc:66,74-77,219`），因此 watchdog 触发前的 5283–6099 个节点（R01–R05）全部落盘。实测 R01 最后一个节点是 `node_id=5282, tick=16968875, kind=sq_lifecycle`，而 watchdog 在 `tick=7700000000` 触发；二者之间的 7.68e9 tick 内**没有任何节点产生**（模型确实已停摆），不是"数据被缓冲后丢失"。
- **当前拿不到的是"终止记录集"**：watchdog 走 `fatal()` → `::exit(1)`（`logging.cc:69`），既不会执行 gem5 的 C++ exit callback（`core.cc:153-157` 只由 Python `atexit` 调用，`simulate.py:262-265`），也不会执行 `stats.dump`。因此 RP01 的 `CHaOS_RP01_STATUS`、`writeDeferredChainRecords()`、`gzclose`、`stats.txt` 写入全部被跳过。
- 结论：**"终止前 trace 内容"可达且已可得；"终止事件本身的 trace 记录"当前完全缺失，但可通过在 `fatal()` 之前插入一次幂等 flush 补齐**。补齐后仍应保持 `TRACE_INCOMPLETE` 语义（异常终止），不得升级为 COMPLETE。

---

## 2. 真实 Watchdog 终止路径（文件:行号 + 代码）

### 2.1 触发点

`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:612-629`：

```cpp
void
CHAOSLSQFwd::rp01Watchdog()
{
    if (write_log && log_stream && log_stream->stream()) {
        *(log_stream->stream())
            << "CHAOS_RP01_WATCHDOG=EXPIRED fired=" << (rp01_fired ? 1 : 0)
            << " injected=" << faults_injected_count
            << " eligible=" << eligible_count
            << " tick=" << curTick() << std::endl;
    }
    // A watchdog expiry is a failed simulation, not a normal MAX_TICK
    // exit: abort loudly so the process exit status is non-zero ...
    fatal("CHAOS_RP01_WATCHDOG_EXPIRED tick=%llu injected=%d eligible=%d",
          (unsigned long long)curTick(), (int)faults_injected_count,
          (int)eligible_count);
}
```

事件在构造期挂载（`CHAOSLSQFwd.cc:213-219`）：

```cpp
if (probability > 0.0f && p.rp01WatchdogCycles) {
    rp01_watchdog_event = new EventFunctionWrapper(
        [this]() { this->rp01Watchdog(); }, "RP01 watchdog", true);
    schedule(rp01_watchdog_event,
             cpu->clockEdge(Cycles(p.rp01WatchdogCycles)));
}
```

### 2.2 `fatal()` 的真实语义

- `fatal(...)` 宏：`CHAOS/gem5/src/base/logging.hh:232` → `exit_message(::gem5::Logger::getFatal(), ...)`。
- `Logger::print` 先输出到 `std::cerr`，再由 `ExitLogger` 追加 `Memory Usage: %ld KBytes`（`logging.cc:56-60`）。
- `Logger::exit_helper()`（`logging.hh:127`）→ `exit()`（noreturn）→ `FatalLogger::exit()`（`logging.cc:65-71`）：

```cpp
class FatalLogger : public ExitLogger
{
  public:
    using ExitLogger::ExitLogger;
  protected:
    void exit() override { ::exit(1); }
};
```

即：**不是 `panic()`（panic 基类 `exit()` 为空，会落到 `::abort()`），不是 `exitSimLoop()`，不是自定义退出**；它是直接 `::exit(1)`。

### 2.3 `::exit(1)` 跳过了什么

- gem5 的"退出回调"是 C++ 的 `registerExitCallback`（`sim/core.cc:143-145`）→ 由 `doExitCleanup()`（`core.cc:153-157`）统一 `process()`；而 `doExitCleanup` 与 `stats.dump` 都注册在 **Python 的 `atexit`** 模块上（`src/python/m5/simulate.py:262,265`）。`::exit(1)` 只运行 C 层 atexit/静态析构，**不会执行 Python `atexit`**，所以二者都不会跑。
- SimObject 析构也不可靠（源码自带注释，`CHAOSPropagation.hh:74-81`：*"the destructor is a backstop only — gem5's exit path does not reliably run SimObject destructors"*）。`CHAOSPropagation::~CHAOSPropagation()`（`CHAOSPropagation.cc:100-110`）的兜底 `gzclose` 同样不会发生。

### 2.4 证据原文（RP01-R01-fault）

`stderr.log`：

```
src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:627: fatal: CHAOS_RP01_WATCHDOG_EXPIRED tick=7700000000 injected=1 eligible=26
Memory Usage: 1249556 KBytes
```

`summary.json`：`"exit_code": 1, "timed_out": false, "terminal": "HANG_WATCHDOG", "terminal_reason": "INTERNAL_WATCHDOG_DEADLINE"`。
`tick=7700000000` = `20,000,000` cycles × `385` ticks/cycle（B0）。

五个 fault run 的 watchdog tick 全部是 `7700000000`；eligible 分别为 26/77/128/179/230（R01–R05）。**这证明 watchdog 是"模型内部、由 gem5 事件队列准点触发"，不是外部 kill。**

---

## 3. Trace Buffer 生命周期与缺失证据根因

### 3.1 生命周期（tracer 一侧）

| 阶段 | 代码位置 | 行为 |
|---|---|---|
| 构造 | `CHAOSPropagation.cc:66` | `gzopen(path, "wb")` 打开裸 zlib 流（非 `simout.create` 的 gz streambuf） |
| 头部 | `:70-77` | 写 CSV header 后立即 `gzflush(Z_SYNC_FLUSH)` |
| 每节点 | `writeNode()` `:190-220` | `gzwrite` 一行后 `gzflush(Z_SYNC_FLUSH)`（`:219`） |
| 每条边 | `writeEdgeRow()` `:301-304` | 同上，逐行 flush |
| 正常退出 | exit callback `:92-97` | 先 `writeDeferredChainRecords()`（`:2914-2927`），再 `gzclose` 写 gzip trailer |
| 析构兜底 | `:100-110` | 仅在 exit callback 未跑时兜底 `gzclose`（实际不会跑） |

**关键结论：trace 不是内存缓冲，是"逐节点同步刷盘的流"。** 内存里只剩 `fault_store_registry` 的延迟链记录（由 `writeDeferredChainRecords` 在退出时补写）。

### 3.2 三类缺失证据的根因（逐项）

| 现象 | 根因（精确） | 证据 |
|---|---|---|
| `stats.txt` 0 字节 | 文件在**启动时**就被创建/截断：`stats.addStatVisitor`（`main.py:575-578`）→ `initText`（`text.cc:814-825`）→ `simout.findOrCreate`（`output.cc:262-268`）→ `OutputDirectory::create/open` 以 `std::ios::trunc` 打开（`output.cc:210-240`）。真正的写盘只发生在 `stats.dump`（`simulate.py:262`，Python atexit）。`fatal→::exit(1)` 跳过 atexit ⇒ 文件保持 0 字节。**这是"dump 未执行"，不是统计缺陷。** | 5 个 fault run 全部 0 字节；对照 run `RP01-R01-control/stats.txt` = 258195 字节（正常退出） |
| `trace_v31.jsonl` 不存在 | **与 abort 无关**：该文件只由 `run_pilot` 驱动生成；RP01 在矩阵中被分派到 `direct` 驱动（`tools/lsu_v332_matrix.py` `driver_for`/`required_outputs`，`:257-272`），`required_outputs` 只在 `run_pilot` 时追加 `trace_v31.jsonl`。启动器在 watchdog marker 存在时也显式豁免它（`tools/lsu_v333_launch.py:240-255, 296-302`）。 | 对照 run 同样没有 `trace_v31.jsonl`；`RP01-R01-control/` 目录列表无此文件 |
| `prop_trace.csv.gz` 偏小/截断 | ① 运行在 skip 后立即停摆，trace 自然只到 `tick≈17–23M`（对照 run 到 `tick=36,219,260`）；② 缺 exit callback 的延迟链记录与 gzip trailer。**不是前缀数据丢失**：`zlib.decompressobj(16+MAX_WBITS)` 可完整解出 5283–6099 行，`eof=False`（仅缺 trailer）。 | 见 3.3 实测表 |

### 3.3 实测证据表（只读解析，未修改）

| Run | gz 字节 | gzip eof | 节点数 | 最后 node_id | 最后 tick | watchdog tick | 节点种类 |
|---|---|---|---|---|---|---|---|
| R01-fault | 140394 | False | 5283 | 5282 | 16,968,875 | 7,700,000,000 | lq_lifecycle 2565 / sq_lifecycle 2714 / fwd 4 |
| R02-fault | 146399 | False | 5487 | 5486 | 18,361,420 | 7,700,000,000 | lq 2667 / sq 2816 / fwd 4 |
| R03-fault | 152378 | False | 5691 | 5690 | 20,013,455 | 7,700,000,000 | lq 2769 / sq 2918 / fwd 4 |
| R04-fault | 158383 | False | 5895 | 5894 | 21,406,000 | 7,700,000,000 | lq 2871 / sq 3020 / fwd 4 |
| R05-fault | 164344 | False | 6099 | 6098 | 23,041,865 | 7,700,000,000 | lq 2973 / sq 3122 / fwd 4 |
| R01-control | 352891 | **True** | 12817 | 12816 | 36,219,260 | n/a（正常退出） | lq 8530 / sq 4276 / fwd 11 |

Python `gzip.open` 在读取 fault run 时会抛 `EOFError: Compressed file ended before the end-of-stream marker was reached`；`tools/lsu_v333_qualified.py:179,240` 正是靠这一点把 `complete` 置为 False。

**另一个重要事实：RP01 的 skip 事件在 trace 里完全没有节点。** `maybeSkipPartialReplay`（`CHAOSLSQFwd.cc:633-760`）只写 stdout + `lsq_fwd_injections.log`，不调用任何 `CHAOSPropagation::note*`；tracer 中 `noteFunnel` 的调用者只有 `CHAOSAddrPath.cc:531` 与 `CHAOSCache.cc:285`。因此即便退出回调正常执行，RP01 也不会有 `injection`/`funnel` 节点。**flush 必须显式新增 RP01 终止节点，不能指望"补跑退出回调"就有记录。**

---

## 4. 最小安全 Flush 设计

### 4.1 位置与调用顺序

`CHAOSLSQFwd::rp01Watchdog()`（`CHAOSLSQFwd.cc:613`）内，**在 `fatal(...)`（`:627`）之前**：

```
1. emitRp01Status()                      // 写 CHAOS_RP01_STATUS（与退出回调共用，幂等）
2. collect WatchdogTerminalInfo          // 只读快照
3. if (cpu->chaosPropagation)
       cpu->chaosPropagation->flushWatchdogTerminal(info);
4. fatal(...)                            // 保持 exit_code=1 语义不变
```

若 tracer 未挂载（`cpu->chaosPropagation == nullptr`），步骤 3 跳过，步骤 1 仍提供日志级终止记录；不要因 tracer 缺失而改变终止行为。

### 4.2 新增 API（`CHAOSPropagation.hh`）

```cpp
struct WatchdogTerminalInfo {          // 纯 POD 快照，全部为只读拷贝
    const char *trigger;               // "CHAOS_RP01_WATCHDOG"
    const char *reason;                // "INTERNAL_WATCHDOG_DEADLINE"
    const char *terminal_state;        // "HANG_WATCHDOG"
    Tick  armed_tick;                  // 调度时刻（构造期 clockEdge）
    Tick  fired_tick;                  // curTick()
    uint64_t deadline_cycles;          // rp01WatchdogCycles
    uint64_t fault_id;                 // faults_injected_count（1）
    uint64_t injected;                 // faults_injected_count
    uint64_t eligible_count;           // CHAOSLSQFwd::eligible_count
    uint64_t event_ordinal;            // rp01_event_ordinal
    bool     replay_eligible;          // rp01_fired
    bool     replay_decision_skip;     // rp01_fired
    bool     replay_skip;              // rp01_fired
    // 最近一次 eligible 事件（新增只读簿记，见 4.4）
    uint64_t last_eligible_seq, last_eligible_pc;
    uint64_t last_lq_idx, last_lq_gen, last_store_seq, last_replay_gen;
    Tick     last_eligible_tick;
    // LQ/SQ 只读快照（见 4.3）
    uint64_t lq_loads, lq_free, sq_stores, sq_free;
    uint64_t lq_head_seq, sq_head_seq;
    bool     lsu_stalled;
    uint64_t commit_seq;               // tracer 的提交计数（累计）
    uint64_t last_commit_dyn_seq;      // 建议新增（见 4.4）
    Tick     last_commit_tick;
    Tick     last_trace_tick;          // 最后落盘节点的 tick（建议新增）
};

void flushWatchdogTerminal(const WatchdogTerminalInfo &info);  // 幂等
```

### 4.3 事件表（字段 / 来源 / 只读性 / 当前是否可得）

| # | 记录 | 来源（源码） | 只读性 | 现在可得? |
|---|---|---|---|---|
| 1 | Watchdog Trigger | `rp01Watchdog()` 入口 + `CHAOSLSQFwd.cc:214-219` 调度点 | 只读（拷贝常量/成员） | 是（仅 stderr/log） |
| 2 | Trigger Reason | 常量 `INTERNAL_WATCHDOG_DEADLINE` | 只读 | 是（summary） |
| 3 | Fault ID | `faults_injected_count`（`CHAOSLSQFwd.hh:205`），另加 `rp01_fired_id`（`:260-262`） | 只读 | 是（log/stdout） |
| 4 | 最后有效 Event ID | `CHAOSPropagation::next_node_id - 1`（`CHAOSPropagation.hh:489`，类内私有，flush 方法内可直接读） | 只读 | 是（实测 5282–6098） |
| 5 | 最后动态指令 | `commit_seq` + `last_commit_dyn_seq/pc`（`noteCommit`，`CHAOSPropagation.cc:2511-2517`）；LQ/SQ head seq（`lsq_unit.hh:636-644`） | 只读 | commit 计数可得；dyn seq/pc 需新增 2 个只读成员 |
| 6 | Replay Eligibility | `eligible_count`、`rp01_event_ordinal`、最近一次 eligible 身份 | 只读 | 部分（fired 事件可得；"最后 eligible"需新增簿记） |
| 7 | Replay Decision | `rp01_fired` + `rp01_rules.hh::shouldSkip` 的输入（`shouldSkip` 纯函数，`rp01_rules.hh:74-81`） | 只读 | 是 |
| 8 | Replay Skip | `rp01_fired` / `rp01_fired_id` / `rp01_fired_pc`（`CHAOSLSQFwd.hh:259-261`） | 只读 | 是 |
| 9 | LQ/SQ 状态 | `cpu->o3IEW().ldstQueue`（`iew.hh:362`，public）；`LSQ::thread`（`lsq.hh:987`）；`numLoads/numStores/numFreeLoadEntries/numFreeStoreEntries/getLoadHeadSeqNum/getStoreHeadSeqNum/isStalled`（`lsq_unit.hh:354-363, 636-644`）；容量 `LQEntries/SQEntries`（`lsq.hh:973-981`） | **纯 getter** | 是 |
| 10 | 进展状态 | `curTick() - last_trace_tick`（建议新增成员）、`commit_seq`、`LSU stalled`、两 head seq | 只读 | 部分（可由实测 tick 差推导，但 trace 内无记录） |
| 11 | Trace Flush Start | 新节点 `trace_flush_start`，记录 `prev_last_event_id` | 只读 + 新节点 id | 否（需实现） |
| 12 | Trace Flush Complete | 新节点 `trace_flush_complete`，记录 `flushed_event_id`、`nodes_written`、`gzflush_ok` | 只读 + 新节点 id | 否（需实现） |
| 13 | Final Terminal State | 新节点 `watchdog_terminal`，`terminal_state=HANG_WATCHDOG;terminal_source=MODEL_INTERNAL_WATCHDOG` | 只读 + 新节点 id | 否（需实现） |

每条新节点都走现有 `writeNode()`（`CHAOSPropagation.cc:190-220`），自动获得 `gzflush(Z_SYNC_FLUSH)` 与递增 `node_id`，不引入第二套写路径。

建议的三条节点（`kind` 名不与现有 parser 冲突，见 6.4）：

```
trace_flush_start   detail="trigger=CHAOS_RP01_WATCHDOG;prev_last_event_id=5282;fired_tick=7700000000"
watchdog_terminal   detail="terminal_state=HANG_WATCHDOG;terminal_source=MODEL_INTERNAL_WATCHDOG;
                            trigger_reason=INTERNAL_WATCHDOG_DEADLINE;fault_id=1;injected=1;
                            eligible=26;event_ordinal=26;last_valid_event_id=5283;
                            last_eligible_seq=16293;last_eligible_pc=4195680;lq_idx=774;lq_gen=1283;
                            store_seq=16292;replay_gen=1;replay_eligible=1;replay_decision=SKIP;
                            replay_skip=1;lq_loads=..;lq_free=..;sq_stores=..;sq_free=..;
                            lq_head_seq=..;sq_head_seq=..;lsu_stalled=..;last_commit_seq=..;
                            silent_ticks=7683031125;commit_seq=.."
trace_flush_complete detail="flushed_event_id=5285;nodes_written=3;gzflush=1;final=1"
```

### 4.4 需要新增的只读簿记（不在任何注入判据中）

1. `CHAOSPropagation::last_node_tick`：在 `writeNode()` 尾部与 `writeEdgeRow()` 尾部更新；只用于 `silent_ticks`。
2. `CHAOSPropagation::last_commit_dyn_seq/last_commit_tick`：在 `noteCommit()`（`:2511`）中记录 `head_inst->seqNum` 与 `curTick()`。
3. `CHAOSLSQFwd::last_eligible_*`：在 `maybeSkipPartialReplay()` 的 `++eligible_count` 之后记录 `id`、`load_pc`、`curTick()`。**这是可观测性写入，不参与 `shouldSkip` 判定**（判定输入仍只有 `eligible_count/ordinal/count_only/rp01_fired`，`rp01_rules.hh:74-81`）。

### 4.5 是否改变 replay 决策 / 调度 / 注入行为

**不改变。证明链：**

- flush 只在 `rp01Watchdog()` 中调用；该方法本身已经是"终止路径"，其后唯一的动作是 `fatal`。此时模型已被判定为停摆（`rp01_fired=1`、ROB 卡死），任何读操作都不可能改变已经发生的历史。
- 所有读取都是 getter 或成员拷贝：`numLoads()/numStores()` 返回 `loadQueue.size()/storeQueue.size()`（`lsq_unit.hh:360-364`）；`getLoadHeadSeqNum()` 返回 `loadQueue[head()].instruction->seqNum`（`lsq_unit.hh:636-638`）；`isStalled()` 返回 `stalled`（`:644`）。无锁、无副作用。
- 不抽随机数、不改 `max_faults`、不改 `rp01_fired`、不重排事件、不重新调度任何 Event。
- 新增簿记只写"本类自己的观测字段"，与 `rp01_rules.hh` 的纯函数判定完全解耦；`shouldSkip` 的签名与语义不变。

### 4.6 幂等 / 再入 / 双写

- `flushWatchdogTerminal()` 首行：

```cpp
if (!write_log || !gz_file || terminal_flushed) return;
terminal_flushed = true;   // 先置位，再写，防递归/再入
```

- 即使未来同一 run 有第二个 watchdog（当前不会：SQ03/SP05/RP01 模式互斥，`CHAOSLSQFwd.cc:155-219`），第二次调用直接返回。
- **不调用 `gzclose`**。理由：① 保持 `gz_file` 有效，若终止路径未来改成 `exitSimLoop`，退出回调仍能补写 deferred 记录并正常 close；② 保留"无 trailer ⇒ parser `complete=False`"这一层保守性（`lsu_v333_qualified.py:179,240`），避免把异常终止的 trace 误标为结构完整。flush 结束时额外调用一次 `gzflush(gz_file, Z_SYNC_FLUSH)` 即可保证字节落盘。
- 若 `writeDeferredChainRecords()` 被调用两次：每条 `FaultStoreEntry` 有 `chain_record_emitted` 守卫（`CHAOSPropagation.cc:2922-2923`），不会重复。RP01 本身不注册 store fault（`fault_store_registry` 为空），该步骤对 RP01 是 no-op。
- `emitRp01Status()` 建议同样加 `rp01_status_emitted` 一次性守卫，退出回调与 watchdog 共用；当前退出回调在 abort 路径永不执行，不存在双写（`CHAOSLSQFwd.cc:221-236`）。

---

## 5. Terminal 分类规则（internal / external / python）

现有工具已经实现了三种分类，flush 只允许写入 **MODEL_INTERNAL_WATCHDOG**，不得代写另外两种。

`tools/lsu_v332_matrix.py:452-469`（原文）：

```python
def terminal_source(*, timed_out: bool = False, exit_code=None,
                    watchdog: bool = False, text: str = "") -> str:
    """Never conflate the model's own watchdog with an external kill.
    * Python/subprocess timeout in this driver   -> PYTHON_TIMEOUT
    * the inner runner's wall-clock timeout      -> EXTERNAL_TIMEOUT
    * A03_WATCHDOG_EXPIRED / CHAOS_RP01_WATCHDOG -> MODEL_INTERNAL_WATCHDOG
    * otherwise                                  -> NORMAL
    """
    if timed_out:
        return TERMINAL_SOURCE_PYTHON_TIMEOUT
    if exit_code == 124 or "TIMEOUT: external wall-clock limit" in (text or ""):
        return TERMINAL_SOURCE_EXTERNAL_TIMEOUT
    if watchdog:
        return TERMINAL_SOURCE_MODEL_WATCHDOG
    return TERMINAL_SOURCE_NORMAL
```

判定依据：

| 分类 | 判据（工具） | 本 run 事实 | 归属 |
|---|---|---|---|
| MODEL_INTERNAL_WATCHDOG | `timed_out=False`，`exit_code != 124`，watchdog marker 存在（`CHAOS_RP01_WATCHDOG`，`lsu_v332_matrix.py:1102-1106`） | exit 1；marker 在 stderr/log；stderr 精确报 `CHAOSLSQFwd.cc:627` | R01–R05 fault |
| EXTERNAL_TIMEOUT | `exit_code == 124` 或文本含 `TIMEOUT: external wall-clock limit`（由 `run_subprocess` 在 `TimeoutExpired` 时写入，`:598-612`） | 未发生 | 若发生，**不得**有模型内 terminal 节点 |
| PYTHON_TIMEOUT | 驱动自身 `timed_out=True`（`subprocess.TimeoutExpired`），优先级最高（`:462`） | 未发生（RP01_TIMEOUT=300s，实测 elapsed≈21s，`:125`） | 若发生，**不得**有模型内 terminal 节点 |
| NORMAL | 以上皆否 | 对照 run：exit 0、oracle PASS | `RP01-R01-control` |

补充规则（重要）：

1. **flush 只由模型内部事件触发**。外部超时/Python 超时是"进程被杀"，C++ 侧没有机会执行任何代码，因此这两类**物理上不可能**产生 `watchdog_terminal` 节点。工具必须继续用 exit code / `timed_out` 判定，**禁止**从缺失节点的现象反推或伪造模型内终止记录。
2. `tools/lsu_v333_qualified.py:786-789` 的优先级是 `watchdog_fired → MODEL_INTERNAL_WATCHDOG`，其次 `timed_out → EXTERNAL_TIMEOUT`；`lsu_v332_matrix.py:463-465` 的注释明确"外部 kill 的既成事实优先于模型写下的 marker"。两者一致，flush 不改变这一优先级。
3. 新节点里的 `terminal_source` 字段只是**模型自述**；工具仍应以进程级事实（exit code / timed_out）为准，二者冲突时以进程级为准并记为证据冲突。

---

## 6. 侧效应 / 死锁 / 锁顺序 / 幂等性审计

### 6.1 并发与锁

- `CHAOSPropagation` 目录内 `grep -rn "mutex\|lock_guard"` 无结果：tracer **零锁**。
- SE 模式下 O3 CPU 的 LSQ hook（`lsq_unit.cc` 的 `maybeSkipPartialReplay` 调用点）与 watchdog 事件都在同一事件队列/同一线程执行；gem5 的 `EventFunctionWrapper` 不会跨线程并行执行该 CPU 的事件。
- 因此：**无锁可竞争，不存在锁顺序反转，也不存在 flush 与写节点之间的数据竞争**。gzFile 是普通文件句柄，`gzwrite/gzflush` 在单线程顺序调用下安全。

### 6.2 阻塞/死锁风险

- flush 只做内存读取 + 写本地文件；不等待其它 SimObject、不 drain、不获取端口、不触发事件。
- `writeDeferredChainRecords()` 只遍历 `fault_store_registry`（RP01 为空），不回调模型。
- 唯一外部依赖是磁盘写入，数据量 < 1 KB；相对于每节点已经执行的 `gzflush`，该开销可忽略。

### 6.3 对 oracle / 判定 / 统计的影响

- **oracle**：RP01 fault run 的 oracle 是"无 checksum 行"（`oracle.log` = `ORACLE_FAIL: no checksum line`）。flush 不打印任何 16-hex 行、不触碰模拟状态，oracle 结论不变。
- **判定**：新增节点 kind 不在 `_PROP_KINDS = ("resp","taint_reg","prop_edge","consumer","commit")`（`lsu_v333_qualified.py:165`）中，`_scan_prop_trace` 对未知 kind 直接 `continue`（`:202-203`），不会污染 resp/commit 检索。`tools/lsu_v333_propagation.py` 的 `MECHANISM_EVENTS`/`DIVERGENCE_EVENTS` 也不含新 kind，RP01 行仍按 `PARTIAL_WATCHDOG` 标注（`:836`）。
- **stats.txt 仍是 0 字节**：flush 不调用 `stats.dump`（C++ 不可达），本轮设计**不修复**该现象。若要修复，需要另一条路径（见第 8 节）。

### 6.4 与现有证据完整性判定的交互

- `lsu_v333_qualified.py:771-783`：`trace_complete = complete and not watchdog_fired and timed_out is not True`。即使未来有人误加 `gzclose` 使 gzip `eof=True`，watchdog 仍强制 `trace_complete=False`，落 `TRACE_INCOMPLETE`。
- `lsu_v333_launch.py:563-569`：终止为 `HANG_WATCHDOG` 且 qualified 为 `TRACE_INCOMPLETE` 时，状态固定为 `TRACE_INCOMPLETE / TERMINAL_WATCHDOG_TRACE_CUT`；不会因新增节点升级。
- 因此新增 `trace_flush_complete` **不会**把 run 标成 COMPLETE；它只说明"终止记录已完整落盘"。**语义必须保持：TRACE_INCOMPLETE = 运行异常终止；flush complete = 终止元数据已落盘。两者不矛盾。**

---

## 7. Validation 方案与预期判定（定向 Pilot）

前提：这是设计文档，下列命令**尚未执行**；通过标准是"实现后必须逐条成立"。命令与现有矩阵驱动一致（`tools/lsu_v332_matrix.py:1411-1433`）。

### 7.1 运行命令（5 Fault + 5 Control）

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
python3 tools/lsu_v332_matrix.py \
  --models RP01 --roles fault,control --contexts 1,2,3,4,5 \
  --force
```

（该驱动对 RP01 使用 `RP01_TIMEOUT=300` 与 `direct` 子进程；不改变冻结 SHA 校验。）

### 7.2 断言清单（对每个 fault run）

| A | 断言 | 检验方式 | 预期 |
|---|---|---|---|
| A1 | 终止记录集齐全 | 解析 `prop_trace.csv.gz`，要求存在且仅各一条 `trace_flush_start`、`watchdog_terminal`、`trace_flush_complete` | 1/1/1 |
| A2 | flush 顺序 | node_id 严格递增：start < terminal < complete | 成立 |
| A3 | `prev_last_event_id` 一致 | `trace_flush_start.detail.prev_last_event_id` == 该 run 旧 trace 的最后一个 node_id（R01=5282, R02=5486, R03=5690, R04=5894, R05=6098） | 完全一致 |
| A4 | 最后有效 Event ID 一致 | `watchdog_terminal.last_valid_event_id` == start 节点自身的 node_id − 1 | 成立 |
| A5 | 无重复 | 三类终止节点各 1 条；`CHAOS_RP01_STATUS` 恰好 1 行；无重复 `chain_record` | 成立 |
| A6 | terminal 分类正确 | `terminal_source=MODEL_INTERNAL_WATCHDOG`；进程 exit 1、`timed_out=false`；stderr 仍含 `CHAOSLSQFwd.cc:627: fatal: CHAOS_RP01_WATCHDOG_EXPIRED` | 成立 |
| A7 | 内容自洽 | `fault_id == injected == 1`；`eligible` 与 stdout 的 `RP01_ELIGIBLE ordinal` 最大序号一致；`last_eligible_seq` == `RP01_SKIP_REPLAY` 行的 load_seq | 成立 |
| A8 | LQ/SQ 非空自洽 | `lq_loads + lq_free <= LQEntries`；`sq_stores + sq_free <= SQEntries`；`lq_head_seq`/`sq_head_seq` 单调合理（不为 0） | 成立 |
| A9 | 进展状态真实 | `silent_ticks = fired_tick − last_trace_tick > 0`（预计 ≈ 7.68e9） | 成立 |
| A10 | oracle 不变 | `oracle.log` 仍为 `ORACLE_FAIL: no checksum line`；`summary.json.oracle=false` | 成立 |
| A11 | TRACE_INCOMPLETE 不升级 | `lsu_v333_launch.py` 记录 `TerminalState=HANG_WATCHDOG`、`Status=TRACE_INCOMPLETE`、`TerminalReason=TERMINAL_WATCHDOG_TRACE_CUT` | 成立 |
| A12 | gzip 前缀仍可解 | `zlib.decompressobj` 解出节点数 ≥ 旧节点数 + 3；`eof=False`（若决定不 close） | 成立 |

失败判据：任何一条不成立 ⇒ flush 实现不合格；不得用"工具解析通过"替代 A3/A4 的逐值核对。

### 7.3 Control 断言（5 个 control）

| B | 断言 | 预期 |
|---|---|---|
| B1 | 无终止节点 | control 的 trace 中没有 `trace_flush_start/watchdog_terminal/trace_flush_complete`（watchdog 在 p=0 时未挂载，`CHAOSLSQFwd.cc:213-214`，且 control 根本未挂 `--chaos_lsqfwd`，见 `command.txt`） |
| B2 | 正常退出证据不变 | `exit_code=0`、`terminal=MASKED`、`oracle=true`、`stats.txt` 非 0、gzip `eof=True` |
| B3 | oracle 不受影响 | golden `0xf3b1c554273d23f7` PASS |

### 7.4 回归（必须）

- 至少一个非 RP01 的 watchdog 模型（SQ03/SP05）与一个完全正常模型（如 FW02/SQ01）各跑 1 次：`exit: pass`、无 SIGSEGV、trace 节点数与改动前一致（flush 代码路径不可达）。
- `tools/lsu_v333_qualified.py` 与 `tools/lsu_v333_launch.py` 全量重跑（只读输入不变），确认 RP01 行仍为 `TRACE_INCOMPLETE / TERMINAL_WATCHDOG_TRACE_CUT`。

---

## 8. 物理不可得项与残余限制

| 项 | 是否可得 | 原因 | 最小可行替代 |
|---|---|---|---|
| 终止前历史节点 | **已可得** | 逐节点 `Z_SYNC_FLUSH`（`CHAOSPropagation.cc:219`） | 无需替代 |
| 终止事件元数据 | 实现 flush 后可得 | 当前只在 fatal 前写日志，不写 trace | 第 4 节 flush |
| `stats.txt` 内容 | **不可得（本设计内）** | `stats.dump` 在 Python atexit；C++ `fatal` 不可达 | ① 保留 0 字节并在报告中如实标注；② 可选补丁：在 `lsu_proxy.py` 用 `m5.stats.periodicStatDump(N)` 周期落盘（代价：语义变为周期快照，需单独设计/验证）；③ 备选"Option B"：把 `fatal` 换成 `exitSimLoopNow(..., exit_code=1)`，让 atexit 正常执行——但这会改变终止路径与退出码传播，**本轮未验证，不得作为最小改动** |
| `trace_v31.jsonl` | 不可得（direct 驱动） | 由 `run_pilot` 生成，RP01 不走该驱动 | 若确需，需新增 `prop_trace → trace_v31` 转换步骤；不得把"文件缺失"误判为 flush 失败 |
| gzip trailer / gzip 结构完整 | 本设计选择不生成 | 保留 `complete=False` 的保守语义 | 保持 `eof=False`；以显式 `watchdog_terminal` 节点表达"终止记录完整" |
| 终止时刻 ROB/IQ 逐条内容 | 不可得（现有公开 API 不足） | `ROB::readHeadSeqNum()` 已被注释（`rob.hh:235-239`），`numInstsInROB` 为 private（`rob.hh:341`） | 记录 LQ/SQ head seq + 计数（`lsq_unit.hh:354-363`）；若必须，需要单独增加只读 accessor（超出最小改动） |
| 最后一条提交指令的精确 PC | 部分可得 | `noteCommit` 有 `head_inst`，但当前只存 `commit_seq` 计数（`CHAOSPropagation.cc:2516`）；`last_commit_pc` 未保存 | 建议新增 `last_commit_dyn_seq/last_commit_pc/last_commit_tick` 三个只读成员（`noteCommit` 内更新，零行为影响） |
| 外部/Python 超时的模型内记录 | **物理不可得** | 进程被 SIGKILL，C++ 无执行机会 | 工具按 exit 124 / `timed_out` 分类；禁止伪造 |

**残余限制（必须写进交付说明）：**

1. flush 后的 trace 仍然**不是**一次正常完成的 trace：没有 gzip trailer、没有后续架构推进、没有 checksum。`TRACE_INCOMPLETE` 必须保留。
2. RP01 的 skip 事件本身不会出现在 trace 的既有 kind 体系中（只有新增的 `watchdog_terminal` 承载它）；不要期待 `injection` 节点。
3. `silent_ticks` 很大（≈7.68e9）是**真实停摆**的证据，不是丢数据；报告时应把它作为"无进展"判据，而不是 trace bug。
4. 若 watchdog 在 tracer 未挂载时触发，只能得到日志级 `CHAOS_RP01_STATUS`，trace 侧无终止节点；工具需允许"无 tracer 的 RP01"这一组合并如实标注，而不是伪造成 trace 完整。

---

## 附录 A：关键源码位置索引

| 主题 | 位置 |
|---|---|
| RP01 watchdog 定义 / fatal | `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:612-629`（fatal 在 627） |
| watchdog 挂载 | 同上 `:213-219` |
| RP01 退出回调（当前不执行） | 同上 `:221-236` |
| RP01 skip 判定与记录 | 同上 `:633-760`；`rp01_rules.hh:46-81` |
| fatal / panic 实现 | `CHAOS/gem5/src/base/logging.hh:127,232`；`logging.cc:56-71` |
| exit callback 注册/执行 | `CHAOS/gem5/src/sim/core.cc:143-157`；`src/python/m5/simulate.py:262-265` |
| trace 打开 / 逐节点 flush / 退出关闭 | `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc:66,70-77,92-97,190-220,301-304` |
| 延迟链记录 | 同上 `:2914-2927` |
| 连接点（globaltracer 指针） | `CHAOS/gem5/src/cpu/o3/cpu.hh:497-503,531-532` |
| LQ/SQ 只读状态 | `src/cpu/o3/iew.hh:362`；`lsq.hh:973-981,987`；`lsq_unit.hh:354-363,636-644` |
| stats 文件创建/写入 | `src/python/m5/main.py:575-578`；`src/base/stats/text.cc:814-825`；`src/base/output.cc:210-240` |
| 外部/Python 超时 | `tools/lsu_v332_matrix.py:125,452-469,566-620` |
| 证据完整性 / TRACE_INCOMPLETE | `tools/lsu_v333_launch.py:240-255,296-302,496-503,563-569`；`tools/lsu_v333_qualified.py:165,168-202,240,682-696,771-789`；`tools/lsu_v333_propagation.py:836` |

## 附录 B：本报告引用的实测证据

- `audit_v3_3_3/runs/RP01-R01-fault/{stderr.log,stdout.log,summary.json,pilot_meta.json,prop_trace.csv.gz,lsq_fwd_injections.log,oracle.log}`（其余 R02–R05 同构）
- `audit_v3_3_3/runs/RP01-R01-control/{command.txt,stats.txt(258195B),prop_trace.csv.gz(eof=True,12817 nodes),summary.json}`
- 上述文件均只读打开；未写入、未覆盖、未移动。
