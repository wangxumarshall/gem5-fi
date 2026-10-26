# R0202-T02F2-MSHR-REPAIR — gem5 `assert(mshr)` 根因修复 + 证据耐久性 + T02 explicit seed 1

**结论：PARTIAL。** 用户明确要求修复的两个问题**都已修复并端到端验证**；但
**T02-F2-W4 explicit seed 1 仍为 NOT-ACCEPTED**（6 个 activated fault 中 5 个独立闭合、
1 个按既定规则不得闭合），故六项重跑的前置条件未满足，**未运行**（遵守用户阶段7 约束）。

| 状态项 | 判定 | 证据 |
|---|---|---|
| ROOT_CAUSE_CONFIRMED | **PASS** | §1（断言点代码 + 真实 debug 事务链 + packet.cc flags 三方印证） |
| CACHE_PROTOCOL_FIXED | **PASS** | §2（策略1）：同注入序列下 SIGABRT 消失、exit_code=0、stats.txt 由 0 B → 389,062 B |
| EVIDENCE_DURABILITY_FIXED | **PASS** | §3：截断位置可指出；异常流无伪造 chain_end/terminal；开销 3.81 µs/行 |
| NO_NEW_REGRESSION | **PASS** | §5：92 suites，PASS 74 / FAIL 15 / SKIP 3，**新增失败 0**（15 个与基线同名同集合） |
| T02_STRICT_PASS | **FAIL** | §4：fault 1 `full`；fault 2/3/4/5 `detected_contained`；**fault 6 `provable_to_L4_then_unknown`** ⇒ 样本 `all()` 不成立 |
| SIX_RUN_STRICT_PASS | **BLOCKED** | 用户阶段7 前置条件（T02 严格通过）未满足，**未运行**六项 |
| FORMAL_NOT_STARTED | **PASS** | 未启动 seed 2/3、pilot、screening、confirmatory、325 formal 或其他 RunID |

---

## 1. 根因（阶段1，三方印证）

**gem5 `BaseCache::recvTimingResp` 对 UnCacheable 写的「错误响应」分类错误**：该响应被误
路由到要求 MSHR 的路径后 `assert(mshr)` 失败 ⇒ SIGABRT。这是 **gem5 自身的协议处理缺口**，
与 CHAOS 注入器无关（注入器从不触碰 cache 协议内部；本 run 四个 CHAOS cache 钩子全为
`nullptr`，`config.ini` 仅挂 `chaos_armtlb chaos_propagation`）。

**证据 1 — 断言点**（`CHAOS/gem5/src/mem/cache/base.cc:782-783`）：
`MSHR *mshr = dynamic_cast<MSHR*>(pkt->popSenderState()); assert(mshr);`
其上一分支（`:752-757`）只在 `pkt->isWrite()` 为真时才处理 UC 写。

**证据 2 — 真实 debug 事务链**（`runs/lsu/0202_t02f2_mshr_diag1_20261027T010327/logs/debug2.txt`，
断言 tick `240017009067`）：
```
240016798611 l1d-cache-0: access for WriteReq [1c191000:1c191001] UC
240016798944 l1d-cache-0: sendWriteQueuePacket: write WriteReq [1c191000:1c191001] UC
240016798944 l2-cache-0:  access for WriteReq [1c191000:1c191001] UC
240016802607 l2-cache-0:  sendWriteQueuePacket: write WriteReq [1c191000:1c191001] UC
240016802607 board.iobridge.cpu_side_port: recvTimingReq: WriteReq addr 0x1c191000
240016958118 board.iobridge.mem_side_port: recvTimingResp: BadAddressError addr 0x1c191000
240017009067 l2-cache-0: recvTimingResp: Cache received BadAddressError [1c191000:1c191001] UC with error
240017009067 l2-cache-0: recvTimingResp: Handling response BadAddressError [1c191000:1c191001] UC
```

**证据 3 — flags 事实**（`CHAOS/gem5/src/mem/packet.cc:216`）：
`{ {IsResponse, IsError}, InvalidCmd, "BadAddressError" }` —— **不含 IsWrite**。
⇒ `pkt->isWrite()` 为假，跳过 `handleUncacheableWriteResp`，落到 `assert(mshr)`；
而 UC 写经 write buffer 发出（`sendWriteQueuePacket`「forward as is」，不 push sender
state；`base.cc:2365` 是 MSHR 唯一入栈点）⇒ **永不分配 MSHR** ⇒ 必然失败。
（对照：`WriteError`(220) **保留** IsWrite，故正常的写错误不触发该缺陷。）

**触发方式是 T02 fault model 的正常后果**，非缺陷：T02 只翻 TLB 表项 `pfn`
（`CHAOSArmTLB.cc:679`）且**不重算属性**（符合「PPN 双 bit 翻转」定义，不得修改）。
被翻的是 **UART0 的 D-TLB 表项**（`old_pfn 0x1c090` = PA `0x1C090000`，即 PL011 UART0），
翻成 `0x1c191000` —— 仍落在 `board.iobridge` range `0x0C000000–0x20000000` 内，但 iobus
上无对应设备 ⇒ 命中 iobus 的 default `badaddr_responder`（IsaFake, `ret_bad_addr`）；
属性保留 Device/nonCacheable ⇒ 请求标 UNCACHEABLE ⇒ 走 UC 写路径。

## 2. 修复（策略1，最小协议修复）

**改动**：`CHAOS/gem5/src/mem/cache/chaos_cache_resp.hh`（新增，纯判定函数）+
`CHAOS/gem5/src/mem/cache/base.cc`（同一分类点接入）。
判据由「只看 `pkt->isWrite()`」补全为：

> 写位 **∨** （`isError` ∧ `isUncacheable` ∧ senderState 栈中**无 MSHR**）

并交给既有 `handleUncacheableWriteResp()`（与成功 UC 写响应**同一条**路径）。

**为什么不越红线**：
- 不删/注释/绕过 `assert(mshr)`；不静默吞响应；不伪造 MSHR。
- 分类仍在**同一个 if**、同一个位置完成 —— 是把既有判据补全到它漏掉的一类**真实**响应，
  而非在函数末尾兜底。
- 该错误仍经 `cpuSidePort.schedTimingResp` **上报 CPU**（不被丢弃）。
- 三重限定保证不误伤：UC **读**的 error 响应必然带 MSHR（`allocateMissBuffer`）⇒ 继续走
  MSHR 路径；非 UC 的无 MSHR 错误响应属真异常 ⇒ 仍落到 `assert` **响亮失败**。
- 判定用 `Packet::findNextSenderState<MSHR>()` **只读**探测，不破坏 senderState 栈。

**端到端验证**（新 binary `843d0e94…`，同一注入序列 `239515618626 / 239589696141 /
240016366044`）：**SIGABRT 消失** —— `exit_code=0`（旧为 −6）、`stats.txt=389,062 B`
（旧为 0 B）、`truncated=False`、无任何 Assertion。

## 3. 证据耐久性（阶段4，独立提交）

**实测结论**：发射器现有设计已满足需求 1–5 ——
- L0 `inj` 在可能引发下游失败的操作**之前**持久化：`registerTrace`（`writeNode` +
  `gzflush(Z_SYNC_FLUSH)`）位于 `maybeCorruptLookup` 末尾、**返回 MMU 之前**
  （`CHAOSArmTLB.cc:1151`），而下游失败发生在其后。
- 正常 / SIGINT 退出走退出回调 ⇒ `gzclose` 写 trailer ⇒ 完整流。
- SIGABRT 时进程直接死亡 ⇒ 无 trailer、无 chain_end、无 funnel 摘要，但**每个
  `Z_SYNC_FLUSH` 边界的数据块都在盘上**（真实证据：旧失败流 2620 事件可读、inj 可查）。
- 异常流 `truncated=True`、无伪造 chain_end/terminal、缺失字段为空串（不填 0）。
- 不在崩溃 signal handler 中做任何操作（不存在此类 handler）。

**补上的唯一缺口（需求 6）**：`read_stream(path, detail=None)` 新增可选截断详情
（`reason` / `last_event_id` / `last_event_kind` / `last_tick` / `last_complete_boundary`），
`lsu_chain_check` CLI 输出 `truncation` 字段 ⇒ **可指出截断位置**。
`read_events` 签名与行为不变（向后兼容）。

**性能开销（需求 9，实测）**：每行同步 flush 额外 ≈ **3.81 µs/行**
（4000 行 21.8 ms vs 批量 6.5 ms）；整轮 5178 行 ≈ 0.02 s。gem5 的注入 **tick 由事件队列
决定、与 wall time 无关** ⇒ 不扰动注入时序。

## 4. T02-F2-W4 explicit seed 1 严格验收（阶段6）

运行：`--explicit-seed 1`、单进程、新目录、`DIAGNOSTIC_REPLICATION_ONLY`；
命令含 `--tlb_rng_seed 1` / `--prop_sample_run_id s1`。
**6 个 activated fault**（F2 每 ~1e5 eligible events 注入一次；修复崩溃后 guest 不再早崩，
故按周期继续注入，实测 6 次）。`exit_code=0`、`truncated=False`、Unknown=0、`stats.txt` 非零。

| fault | terminal | provable_to | contained | fault admission | 完整 ancestry（自该 fault 的 `inj`，连续父链） |
|---|---|---|---|---|---|
| 1 | **`full`** | L5 | False | **True** | `inj → tlb_lookup → tlb_pfn → tlb_translate_result → sq_execute → sq_writeback → cache_access → cache_return → mshr_alloc → cache_access → cache_return → mshr_alloc → resp → taint_reg → sq_complete → errant_commit` |
| 2 | **`detected_contained`** | L5 | True | **True** | `inj → tlb_lookup → tlb_pfn → tlb_translate_result → lq_read → cache_access → cache_access → resp → lq_complete → taint_reg → request_fork → cache_access → cache_access → resp → lq_complete → taint_reg → consumer → consumer → squash_masked` |
| 3 | **`detected_contained`** | L5 | True | **True** | `inj → tlb_lookup → tlb_pfn → tlb_translate_result → sq_execute → sq_writeback → cache_access → cache_return → mshr_alloc ×2 → mshr_fill → cache_fill → mshr_free ×2 → resp → taint_reg → request_fork → cache_access → cache_return → mshr_merge → resp → lq_complete → taint_reg ×2 → consumer ×6 → squash_masked` |
| 4 | **`detected_contained`** | L5 | True | **True** | `inj → tlb_lookup → tlb_pfn → tlb_translate_result → sq_execute → sq_writeback → cache_access → cache_return → mshr_alloc ×2 → mshr_fill → cache_fill → mshr_free ×2 → resp → taint_reg → sq_complete → squash_masked` |
| 5 | **`detected_contained`** | L5 | True | **True** | `inj → tlb_lookup → tlb_pfn → tlb_translate_result → sq_execute → sq_writeback → cache_access → cache_return → mshr_alloc ×2 → resp → taint_reg → sq_complete → squash_masked` |
| 6 | `provable_to_L4_then_unknown` | **L4** | False | **False** | `inj → tlb_lookup → tlb_pfn → tlb_translate_result → lq_read → cache_access → cache_return → mshr_alloc ×2 → resp → lq_complete → taint_reg` |

**样本级 `all()` ⇒ `admitted=False`**（`all_activated_faults_closed=False`）。

### 4.1 fault 6 为何不得闭合（诚实结论，未伪造）

- 该链 173 个 `taint_reg`、**0 个 `consumer`**：污染被建立但**从未被任何提交指令消费**；
  注入发生在退出前 ~1e12 ticks（tick `4815906564042` → 退出 `4911383169864`），影响来不及
  产生架构效果。
- 可审计诊断 `CHAOS_TAINT_AT_EXIT`（本提交新增）显示其 ptag **不在**退出时的 `taint_set`
  中 ⇒ 污染已被 **clean overwrite**（提交的无关指令写同一物理寄存器）清除。
- ⇒ 该 fault **既无逃逸（无 `errant_commit`），也无任何检测事件**（无 squash/replay 检测、
  无含住判定）。按既定规则（检测/含住证据必须是非 lifecycle 事件）**不得**闭合。
- **主动拒绝的策略3**：把「污染被 clean overwrite 清除」也记为 containment。该事件
  **不是检测**（没有 detector 发现错误，只是影响自然消失），把它标成 containment 属于
  用户红线所禁止的**伪造 containment**，故**不实施**。这是 T02 停在 5/6 的直接原因。

### 4.2 策略2 的边界（为何它是修复而非放宽）

修复崩溃后暴露的第二个独立根因：发射器**已经在**退出时**判定**含住
（`store_discarded_not_retired`，stdout 有 `CHAOS_DETECT: layer=Hardware RAS contained=1`），
但该判定**只走 stdout + 生命周期 `chain_end`**，链上没有任何非 lifecycle 事件 ——
而该 tracer **自己的 live squash 路径**（`noteMemResponse` 中 `inst->isSquashed()` →
`notePropEvt("squash_masked", detection_layer=L4, contained=1)`）是**发链上事件**的。
策略2 只是把这个**不对称**补齐（退出时的同一判定也发同形事件），
**没有新增任何判定类别、没有放宽 checker、没有改 fault model/oracle**。

## 5. 测试与既有失败集合

| 套件 | 结果 |
|---|---|
| `tests/test_lsu_cache_resp_classify.py`（新增，真实 commandTable flags 驱动） | 修复前**红**（唯一失败项 `BadAddressError/UC/no-mshr ⇒ WriteBuffer`）→ 修复后 **ALL PASS** |
| `tests/test_lsu_evidence_durability.py`（新增，含真实 SIGABRT 产物） | **ALL PASS**（25 项） |
| `tools/lsu_test_runner.py` 全套 | **suites=92 PASS=74 FAIL=15 SKIP=3**；**新增失败 0** |

**既有失败集合（15 个，与基线逐名相同，均为本任务之前既有、非本次引入）**：
`pytest::collect`、`tests/test_lsu_campaign_propagation.py`、`tests/test_lsu_hook_a07.py`、
`test_lsu_hook_c11.py`、`test_lsu_hook_c12.py`、`test_lsu_hook_c14.py`、`test_lsu_hook_c15.py`、
`test_lsu_hook_cpf.py`、`test_lsu_hook_l04.py`、`test_lsu_hook_o0x.py`、`test_lsu_hook_p06.py`、
`test_lsu_hook_s10.py`、`test_lsu_hook_sq.py`、`test_lsu_r6_status_table.py`、
`tests/test_lsu_xlsx_to_md.py`
（成因：陈旧 hook 合成链缺 `parent_event_id`、依赖 gitignored `runs/` 状态、约定标记不匹配。）

## 6. 身份 / 资源 / 原始证据

| 项 | 值 |
|---|---|
| 分支 / HEAD | `fix/0202-six-chain-20261026` |
| 二进制（**新 freeze**） | `CHAOS/gem5/build/ARM/gem5.opt`，SHA256 `b501de2cca321a9abe92d75a5ae303d8ac3a72041afaaeb12dcb92cedf5b2320` |
| 旧二进制（失效） | `a99031a86e8e108b9278af53044d873a8262ea20d73bd7d94c6dba1300b49e0a` |
| 中间二进制（策略1） | `843d0e94f02708723e3773193b91697ce5f317734cb2b5e5a1ab1cc69c953221` |
| checkpoint / golden | `runs/lsu/0202_fs_cpt_boot_20261026T193235/cpt.239515184727` / `b6d81b360a5672d80c27430f39153e2c` |
| 根因诊断原始证据 | `runs/lsu/0202_t02f2_mshr_diag1_20261027T010327/`（含 `logs/debug2.txt`） |
| 策略1 验证证据 | `runs/lsu/0202_t02f2_mshr_fix_20261027T013411/` |
| 策略2 验证证据（T02 6-fault） | `runs/lsu/0202_t02f2_mshr_fix2_20261027T020020/` |
| 构建记录 | `runs/lsu/0202_mshr_build_20261027T012312/`、`runs/lsu/0202_mshr_build2_20261027T015021/` |
| 旧失败证据（未改动） | `runs/lsu/0202_t02f2_legacy_seed1_diag_20261027T000814/` |
| 策略2 运行 wall / 资源 | ~2.5 min；最低 `MemAvailable` 363.1 GiB；并发 1 |
| 编译 | 单实例 `-j8`，增量，exit 0，0 error |

## 7. 仍存在的诚实限制

1. **T02-F2-W4 不可闭合的 fault 6**（§4.1）：F2 多注入下"污染建立但未被消费、随后被
   clean overwrite 清除"的链，在既定规则下**没有**合法的終局证据。这**不是**工具缺陷，
   也不是本次能修的（修它等于伪造 containment）。
2. **fault 数随崩溃修复而增加**：修复前 2 次注入（guest 早崩）；修复后 6 次（按 F2 周期）。
   即"修复 cache 断言"本身**改变**了运行轨迹 —— 这是**正确**行为（模拟器不再崩溃），
   但也意味着 T02 的 fault 集合与旧证据不可直接比较。
3. **`crash_kind=simulator_assert` 标签**：本次运行无任何断言（`exit_code=0`），该标签仍是
   `lsu_l5_classify` 的正则 `|panic|` 命中 `arm_chaos_fs` 自身 "KERNEL PANIC under fault"
   提示行所致（只影响标签，不影响链判定）。已知既有问题，未在本次范围内修改。
4. **六项未运行**：遵守用户阶段7「只有 T02 严格通过后才运行六项」的约束。
   故 `R0202-VERIFY6-EXPLICIT-SEED1.md` **未生成**。

## 8. 停止

- 已完成：根因确认、策略1（协议修复）、策略2（观测通道对称化）、证据耐久性修复、
  重建、全量回归、T02 explicit seed 1 严格验收。
- 未运行：**六项 explicit seed 1**（前置未满足）、seed 2/3、pilot/screening/
  confirmatory/325 formal、其他 RunID。
- 未改动：checker 严格性、T02 fault model / F2 周期 / jitter / oracle / checkpoint、
  旧 raw evidence 与旧报告。
- 结论：**PARTIAL**（两项修复达成；T02 因 1/6 activated fault 在既定规则下不可闭合而未通过）。
