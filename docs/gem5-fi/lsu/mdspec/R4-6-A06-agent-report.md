# R4-6-A06 agent 报告 — A06 load 侧 size 注入 + byte-enable 观测/注入（spike 化）

**分支** `r4-6-a06-loadsize`（worktree `.claude/worktrees/r4-a06`，基线 `ce7523ed`）
**日期** 2026-10-22
**规格** 03 矩阵 A06 行（A06-a = access size 改为另一合法值；A06-b = byte-enable
改为另一合法掩码；触发 = 子字节或向量访存；负载 W3/W5）
**状态** 代码 + carrier + 契约测试**已落地**；C++ 为 **COMPILE-UNVERIFIED**；
**A06 6 个 RunID 保持 BLOCKED**（spike 的真实 gem5 运行未做）。

---

## 1. 接口复核结论（全部基于源码实证）

### 1.1 load 侧当前为何被 REJECT（具体行与判据）

- 裁决文本分支：`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc`
  的 `maybeCorruptPre` 内 op-class 过滤块（原 `:394-420`：`pre_store_only` 名单含
  `"a06_size"` ⇒ 任何 `isLoad` 请求在 **trigger 决策之前**被拒，计 `obs_pre_opclass`，
  仅当 F6 `f6_pending` 已 armed 时刷一条
  `REJECT: reason=load_candidate_under_store_only_model` 日志）。
  分支内还有第二层 belt-and-braces：`} else if (pre_mode == "a06_size") { if (isLoad) { ++obs_pre_opclass; return size; } ... }`。
- **判据不是"load 一律非法"，而是"定宽完成合同"**（2026-10-15 审计根因 C）：
  - `LSQ::pushRequest(size)` 的 size 决定 `LSQRequest::_size` → `Request::_size` →
    `Packet::createRead(req())` 的 packet 宽度（`lsq.cc:1362-1369`），并且决定
    **load 目的缓冲区**的分配长度：`load_inst->memData = new uint8_t[request->mainReq()->getSize()]`
    （`lsq_unit.cc:1915-1917`）。
  - 而 ARM 的 load 完成是**按静态指令定宽**的：`arch/arm/isa/templates/mem.isa:487-512`
    `LoadCompleteAcc` 无条件 `getMemLE(pkt, Mem, traceData)` —— 从 packet 拷
    `sizeof(Mem)` 字节，宽度与 request size 无关。
  - ⇒ `new_size < 静态宽度` 就是**堆越界读**（同一事实的旁证：
    `lsq_unit.cc:211` 的注释 "a mismatch would read out of bounds"）。这是硬约束。
- byte-enable 侧同源：`LSQRequest::addReq`（`lsq.cc:1182-1217`）把掩码的**尾部连续 0**
  折算为 `size - inactive_tail_size` ⇒ 尾部 0 掩码 ≡ size 收缩 ⇒ 同一禁区。

### 1.2 load 的 access size 在 gem5 AArch64 中的流动

`静态指令 Mem 操作数宽度`（`LoadInitiateAcc` → `initiateMemRead(xc, traceData, EA, Mem, flags)`，
`mem.isa:434-457`）→ `DynInst::initiateMemRead(addr,size,flags,byte_enable)`
（`dyn_inst.cc:420-431`，`assert(byte_enable.size()==size)`）→ `CPU::pushRequest` →
**`LSQ::pushRequest`（本钩子所在点；此处的 `size` 就是原静态宽度）** → `LSQRequest::_size`
→ `Request` → `Packet` → `LSQUnit::read`/`writeback` → `StaticInst::completeAcc`（定宽读回）。
另有 `inst->effSize = size`（`lsq.cc:917`）与 `LSQUnit::tryToForward` 用 `request->mainReq()->getSize()`
做范围判定（`lsq_unit.cc:1680-1690`）。

### 1.3 byte-enable 载体可达性（诚实结论）

- **载体存在但 ISA 侧恒为全 1**：AArch64 全部访存路径传 `std::vector<bool>(size, true)`——
  `mem.isa:424,477`、`neon64.isa:328,355,411,443`、`sve_mem.isa`（多处）、`sme.isa`。
  ⇒ 掩码域在本平台是**单元素集 {全 1}**，规格所说"另一合法掩码"**没有 ISA 来源**。
- **掩码唯一的真实杠杆**是 `addReq` 的尾部裁剪（≡ size 改变，load 侧被合同禁止）。
- **非尾部掩码确有架构后果，但只在 store 侧**：`Request::isMasked()`（`request.hh:727-734`）
  → `Packet::isMaskedWrite()`（`packet.hh:1450-1454`）→ `Packet::writeData`
  （`packet.hh:1320-1336`，逐字节掩码拷贝）/ `MSHR::TargetList::add`（`mshr.cc:139`）/
  `base.cc:1090`。所以 A06-b 的诚实落地形态 = **store 侧内部位清零掩码注入 + 双 op-class 的掩码观测**，
  load 侧只做观测（其掩码在本路径无架构消费者）。

### 1.4 与路由 / 传播必录字段的衔接

- 路由：`tools/lsu_campaign.py` `MODEL_FLAGS["A06"]`（PRE 家族，`--agu_pre_mode ...`）
  与 `MODEL_BLOCKED["A06"]`；config 面 `configs/se/lsu_proxy.py`（`--agu_pre_mode` choices、
  preMode/aguSizeTo 直连 SimObject）。
- 传播：PRE 家族的 inj/addr_form 节点由 `lsq.cc` 调
  `CHAOSPropagation::registerInjection(site="lsq_pushRequest_PRE", seq, old_addr, new_addr, is_load, old_size, new_size)`
  产出（`CHAOSPropagation.cc:431-473`），**inj 节点已带 `old_size`/`new_size`**，地址注册表登记
  `[new_addr, new_addr+new_size)` —— **size 故障的"故障值"就是 new_size，链路可证**。
  本改动未新增事件 kind（`lsu_prop_fields.py` 的 PROP_EVT_FIELDS/KIND_LAYER 不变），
  仅在注入日志**尾部追加**自描述字段（`fault_field=` / `be_len=` / `be_ones=` / `be_subst=`），
  与 `lsu_phantom_audit.py` 的 `PRE_LINE_RE` 前缀假设兼容（契约测试 A10b 钉死尾部追加）。

## 2. 落地内容

### A06-a：load 侧 size 注入（可注入 + 可追踪的 amplifier）

**形状**：`pre_mode = a06_size` 从"store-only"扩为**按 op-class 的合法包络**：

| op class | 合法目标集合 | 说明 |
|---|---|---|
| store | `{1,2,4,8,16}` 任意（行为不变） | 短写架构合法 |
| load | **strict widen**：`--agu_size_to_load ∈ {2,4,8,16}` 且 `> 原 size` 且 `(addr&63)+target ≤ 64` | 定宽完成合同只禁 shrink |

拒绝理由逐类计数并可日志留证（F6 armed 时）：
`load_widen_target_unset` / `load_widen_target_illegal` /
`load_size_shrink_violates_fixed_width_completion` / `load_widen_block_geometry`；
新 stdout 行 `CHAOS_L0_A06:` 汇总（自守：仅 a06_size 形运行打印，其它配置 stdout 逐字节不变）。

**合格性判定放在 trigger 决策之前**（F-049：写不进去的 op 不算 eligible），
保证注定被拒的 load 不会吃掉 F6 的一次性 shot。

**放大器与可观测性（诚实分级）**：
1. **转发降级/replay（规格自认的可观测面）**：widen 使 `req_e = req_s + getSize()` 变大，
   `LSQUnit::tryToForward` 的 `store_has_upper_limit` 不再成立（`lsq_unit.cc:1668-1690`）⇒
   全量转发分支不可达 ⇒ 部分覆盖进入 "Load-store forwarding mis-match" 分支：
   `rescheduleMemInst` + `request->discard()` + `return NoFault`（`lsq_unit.cc:1880-1905`）
   ⇒ 该 load 被 **replay**。规格 A06 的 W5 负载原文即点名 "转发探针 … replay"。
2. **访存几何改变（L2 面可观测）**：single↔split（`transferNeedsBurst` 用钩子后的 size，
   `lsq.cc:866-868`）、MSHR/fragment/需求行集合变化。
3. **不保证 value-level SDC**：完成宽度取 `sizeof(Mem)` 的低字节，且部分覆盖走 replay 而非
   陈旧合并 ⇒ 最终寄存器值通常仍等于内存正确值。**本报告不宣称 load widen 是 value-SDC**；
   按规格激活口径（"故障值被下游实际读取/选择/消费"）它属"被 `tryToForward` 与 packet 构建
   实际选择"的 Injected-activated-as-replay；L5 oracle 是否记 SDC 由 pilot 实测决定。

**关键文件/行**：`CHAOSAddrPath.hh`（`A06LoadVerdict`/`a06LoadWiden`/`agu_size_to_load`）、
`CHAOSAddrPath.cc`（`a06LoadWiden`/`a06LoadVerdictReason` ~`:364-412`；判定块在
`if (lsuTrigger)` 之前；`a06_size` 分支 ~`:552-610`）。

### A06-b：byte-enable 观测 + 注入钩子

- `--agu_be_mode {off|observe|shift_mid}`（要求 `--agu_pre_mode a06_size`，否则 config 期
  `p.error` + 注入器 ctor `panic`；"一个样本一个故障"的 loud 约束）。
- `observe`：对被注入请求做掩码普查（`be_len/be_ones/be_all_true`）写注入日志 +
  `CHAOS_L0_A06:` 汇总（经验证据面；预期全 1）。
- `shift_mid`：替换为"另一合法掩码"= 全 1 且**内部位清零**（`index=(size-1)/2`，要求 `size≥2`）。
  内部位 ⇒ `inactiveTailSize==0` ⇒ **请求 size 不变** ⇒ 不触 C2 定宽合同；**仅 store** 注入
  （`isMaskedWrite()` 有真实部分写后果）；load 侧与 size 已被 A06-a 用掉的事件一律
  `obs_be_declined` 计数拒斥（不静默丢弃）。
- 接线：`LSQ::pushRequest` 现在把**可变副本** `pre_byte_enable` 传给钩子，并用它重建
  `LSQRequest::_byteEnable`（`lsq.cc`）；size 改变时按大小重建全 1（掩码/size 一致性），
  即 size 与掩码替换在请求级互斥（已在注释中明写）。

## 3. carrier + spike 验证路径

- carrier：`workloads/directed/a06_size_be.c`（只提交源码；内联汇编固定访存宽度，不受 -O2
  影响）：子字节/半字 store + 逐字节 canary、同地址 store→load 转发对（1B 与 8B）、
  非对齐子字节/字 load、向量（16B, `str q`/`ldr q`）；软件 oracle = FNV-1a 校验和 + canary 判定。
- 本机实测（真跑，非预测）：`gcc -O2 -static -Wall -Wextra` **零告警**，两次运行输出一致：
  ```
  $ gcc -O2 -static -Wall -Wextra -o /tmp/a06_size_be workloads/directed/a06_size_be.c ; echo rc=$?
  rc=0
  $ /tmp/a06_size_be
  ccc1290d633668c4
  canary=0000000000000001
  ```
- 契约测试：`tests/test_lsu_a06_loadsize.py`（27 项，全 PASS；见 §5）。

## 4. 主 agent 集成后必须跑的确切命令 + 判据

**(0) 构建（C++ 改动，本 worktree 禁 scons）**
```bash
cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt    # 零新增 warning/error
```
判据：build 成功；无本改动引入的 warning（尤其 `-Wreorder`：`agu_size_to_load`/`be_mode`
的声明序与 ctor 初始化序一致，契约测试 A14 已静态钉死）。

**(1) 契约测试 + 回归（无需构建部分先跑）**
```bash
python3 tests/test_lsu_a06_loadsize.py     # 期望 FAILURES: 无，rc=0
python3 tests/test_lsu_a06_ruling.py       # 期望 FAILURES: 无（裁决断言未变，见 §6）
python3 tests/test_lsu_hook_a07.py         # 期望 ALL PASS（本改动调整了其中 1 项判据）
```

**(2) A06-a load 侧 spike（W5 SQ-Forward 面；一样本一故障）**
```bash
build/ARM/gem5.opt --outdir=/tmp/a06_load_w5 configs/se/lsu_proxy.py \
  --cmd workloads/directed/a06_size_be --cpu O3 --chaos_addrpath \
  --addrpath_mode byte7_zero --agu_pre_mode a06_size \
  --agu_size_to 2 --agu_size_to_load 8 \
  --addrpath_lsu_tier F0 --addrpath_warmup_events 0 --addrpath_span_events 1000 \
  --addrpath_rng_seed 4242
```
判据（全部**必须实测**，任一不符即 spike 未通过）：
1. stdout 有 `CHAOS_L0_A06: pre_mode=a06_size size_to=2 load_size_to=8 be_mode=off
   load_widen=<≥1> load_shrink=<≥1> ...` ⇒ **load 侧确实注入了**（`load_widen ≥ 1`）
   且 shrink 候选被显式拒斥（`load_shrink ≥ 1`，证明合同护栏在跑）。
2. 注入日志出现 `Site: lsq_pushRequest_PRE ... isLoad=1 ... fault_field=size` 行，
   且 `new_size=8 > old_size`（1/2/4 的 load 被加宽）。
3. 无 `assert`/`SIGSEGV`：`grep -c "panic\|assert" /tmp/a06_load_w5/*.log` 为 0；
   进程 exit_code == 0（`m5out` 的 `run-finish` 事件）。
4. 传播链（prop trace）里该 seq 有 `inj`（含 `old_size=1;new_size=8`）+ `addr_form`
   + 后续 `mem_req`/`resp`/`taint_reg` 节点 ⇒ L2/L3 面可追踪。
5. 若出现 `Load-store forwarding mis-match`（`--debug-flags=LSQUnit`）即为第 2 类
   激活（replay）的直证；无该行也不判失败（几何可能落在 single→single 情形），
   但**必须在报告里如实标注该 run 的激活形态**。

**(3) A06-b spike（store 侧掩码）**
```bash
build/ARM/gem5.opt --outdir=/tmp/a06_be_w3 configs/se/lsu_proxy.py \
  --cmd workloads/directed/a06_size_be --cpu O3 --chaos_addrpath \
  --addrpath_mode byte7_zero --agu_pre_mode a06_size \
  --agu_size_to 8 --agu_size_to_load 0 --agu_be_mode shift_mid \
  --addrpath_lsu_tier F0 --addrpath_warmup_events 0 --addrpath_span_events 1000 \
  --addrpath_rng_seed 4243
```
判据：stdout `CHAOS_L0_A06: ... be_mode=shift_mid be_seen≥1 be_all_true=be_seen
be_subst≥1 be_declined≥1`（`be_all_true == be_seen` 即"ISA 掩码恒全 1"的经验证据）；
注入日志 `be_subst=1` 行存在；无 assert；且 **canary 判定/校验和与未注入基线比对**
（`--agu_be_mode off` 同 seed 跑对照）——差异必须归因到掩码（`be_subst=1`）而非其它。

**(4) 解除 BLOCKED 的裁决条件**
只有 (2) 全 5 条 + (3) 全条通过，才可把 A06 6 个 RunID 从 `MODEL_BLOCKED` 摘除；
在此之前**保持 BLOCKED**（当前代码只到 COMPILE-UNVERIFIED）。

## 5. 未落地项 / 明确不做

- **A06-a 的 value-level SDC 不保证**（§2 已述）：widen 的架构后果是转发降级/replay 与
  几何改变，不是寄存器值错。若 MDSPEC 要求 A06-a load 侧必须产生 value SDC，需要
  **第二点位**（例如在 `LSQUnit::writeback`/`completeAcc` 前替换 `memData` 的宽度语义），
  那是另一个单元，本次未做（不越权）。
- **A06-b 的 load 侧掩码注入未做**：载体原因（§1.3）——load 掩码在本路径无架构消费者，
  强行注入只会退化成 size 改变（合同禁区），故只做观测。
- 未 push；未改 `docs/gem5-fi/lsu/mdspec/` 既有共享证据文件（只新增本报告）。
- `tools/lsu_p4fix_validate.sh` 仍带 2026-10-15 时代的陈旧断言（用被拒别名
  `a06s_store_size` 做注入用例，并把 `a06_size` 断言为 "RETIRED"，两者都与
  2026-10-19 裁决/当前路由矛盾）。**该文件不在本任务范围**，未改；主 agent 集成时
  应一并改正或废弃，否则它会给出与现状相反的假信号。

## 6. 对既有测试的调整（理由）

- `tests/test_lsu_hook_a07.py`：唯一失败项是 `lsq.cc PRE 调用点传 inst->seqNum` 的
  **逐字符空白**匹配——A06-b 给 `maybeCorruptPre` 加了第 6 个实参导致换行。
  已把该判据改为**空白无关的正则**（参数序不变：addr, size, isLoad, flags, seqNum, ...），
  语义与强度不变（仍钉死"调用点传 seqNum"）。
- `tests/test_lsu_a06_ruling.py`：**未改**。其 4 项判据（模型名承载 `a06_size`、
  A06 在 MODEL_BLOCKED 且理由含 "load"、无 A06S 泄入、`a06s_store_size` config 期被拒）
  在本改动后仍成立（`MODEL_FLAGS["A06"]` 仍含 `a06_size`，choices 仍不含别名）。
  注意：该测试需要 gem5 二进制，本 worktree 无构建，未在本机运行（诚实标注）。

## 7. 本机实测证据（真实输出）

```
$ python3 tests/test_lsu_a06_loadsize.py
PASS A1_a06_not_in_pre_store_only ... PASS C7_proxy_be_mode_validation
FAILURES: 无            (rc=0, 27/27 PASS)

$ python3 tests/test_lsu_hook_a07.py    -> ALL PASS (rc=0)
$ python3 tests/test_lsu_hook_lsq.py    -> ALL PASS (rc=0)
$ python3 tests/test_lsu_hook_sq.py     -> ALL PASS (rc=0)
$ python3 tests/test_lsu_hook_lsqfwd.py -> ALL PASS (rc=0)
$ python3 tests/test_lsu_chain_check.py -> ALL PASS (rc=0)
$ python3 tests/test_lsu_coverage_matrix.py / test_lsu_runid_map.py / test_lsu_pilot_evidence.py
                                        -> FAILURES: 无 (rc=0)
$ python3 tests/test_lsu_prop_fields.py -> ALL PASS (rc=0)
$ python3 -m py_compile {tests/test_lsu_a06_loadsize.py,tools/lsu_campaign.py,
    configs/se/lsu_proxy.py,CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py} -> OK
```
