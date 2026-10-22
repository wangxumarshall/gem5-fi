# R4-8-A06 agent 报告 — A06 load 侧 size 包络补全 + byte-enable 真机 spike + 契约裁定

**分支** `r4-7-a06-full`（worktree `.claude/worktrees/r4-7-a06`，基线 `d5fc8727`）
**日期** 2026-10-22
**二进制** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
（sha256 前缀 `7d52bc1392a10055`，**集成前**的二进制 —— 本报告所有真机数字都出自它，
不含本分支的 C++ 改动）
**状态** C++（load shrink 载体 + 逐因计数）为 **compile-unverified, pending integration**；
本机可跑部分（契约测试 / 回归 / 7 次真机 gem5）全部实测。A06 6 个 RunID 仍 **BLOCKED**。

---

## 0. 本报告的定位与与 R4-6 的关系

R4-6-A06 的结论是：load 侧只落 **strict widen**，理由是"定宽完成合同（shrink ⇒ 堆越界读）"；
byte-enable 只落了 store 侧 `shift_mid` 的**代码**（未真机跑）。R4-8 在这个基础上做三件事：

1. **裁定完整契约**（下文 §1）——把"只禁 shrink"改判为"shrink 必须被**安全实现**"，
   因为规格对方向无限制，而"禁止"是把载体的缺陷写成模型的边界。
2. **把 shrink 真正实现**（§2）——不为 shrink 开新点位，故障仍在 A06 的 size 字段；
   在 gem5 的 load 数据通路上补一个**缓冲下限 + 零填充**（§2.1），使 shrink 的完成
   形态 = 规格预期的**零扩展截断**，而不是越界读。
3. **用真机 gem5 把可达性证到位**（§4）——byte-enable store 侧 `be_subst=1`（R4-6 未跑）、
   store 侧 shrink（8→2）的架构后果（Crash）、load 侧 shrink 护栏（`load_shrink`）
   与"逐因计数在 tier 路由下曾经不可达"这个**工具缺陷**（§3）。

规格引用（下文统一简写）：
- **【03-A06】** `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md` A06 行：
  「AGU/LSU 随访存请求生成的 access-size 与 byte-enable 字段……**把 1/2/4/8/16B size
  或 byte-enable 替换为另一合法组合；保持地址不变**」；子模型
  「A06-a access size 改为另一合法值；A06-b byte-enable 改为另一合法掩码」；
  触发面「子字节或向量访存」；传播链重点观测含「size/**byte-enable**」「**逐字节 store 日志、
  相邻字节 canary、load 扩展方式**」；预期结果（**可证伪假设**）「partial store 最易静默污染
  相邻字节；**load 可能表现为截断/符号扩展错误**」。
- **【主MD】§0.P4** 第 77 行：AGU 的空白是「合法地址替换、寻址模式拼接、**byte-enable 和 ready 时序**」。
- **【主MD】§4 观测点** 第 115 行：AGU 项要求「对照 EA、PA、**size、mask**、异常原因与提交结果」。

---

## 1. 裁定的 A06 契约（faithful contract）

### 1.1 A06-a（access-size 替换）

| op class | 合法目标集 | 依据 |
|---|---|---|
| store | **任意** {1,2,4,8,16}（含变窄/变宽） | 【03-A06】"另一合法组合"无方向限制；短/宽写在字节粒度上架构合法 |
| load | **任意另一合法值** {1,2,4,8,16}（widen **或** shrink），且 `(addr&63)+target ≤ 64` | 同上；`target == 原值` 记为 **NoChange**（不是故障，不写） |

**与 R4-6 的差异及理由（本报告的裁定，非把问题抛回）**：R4-6 把"只准 widen"当作模型边界，
这是把**gem5 载体的缺陷**写成了**模型的边界**。规格对方向无限制，且**期望**的 load 表现形态
恰恰是 shrink 一侧的「**截断**/符号扩展错误」——如果只实现 widen，就把规格点名要观测的现象
天然排除了。因此正确做法是**修载体**，让 shrink 安全且faithful（§2.1）。

### 1.2 A06-b（byte-enable 替换）

| op class | 可达形态 | 依据 / 代价 |
|---|---|---|
| store | **注入**"="另一合法掩码"= 全 1 的内部位清零（`be_mode=shift_mid`），落在 `Request::isMasked()` → `Packet::isMaskedWrite()` 真实通路上；另有 `observe` 只做普查 | 见 §4.2：真机 `be_subst=1` 成立 |
| load | **仅观测**（`observe`）：假想在 load 侧注入掩码是**退化**的——它唯一的功能杠杆是 `LSQRequest::addReq` 的**尾部裁剪**（≡ size 改变，被 §1.1 的完成合同管），非尾部掩码在 load 路径**没有架构消费者** | 代码路径见 §5.1 |

**载体事实（经验证实）**：【03-A06】说"改为另一合法掩码"，但本平台的 ISA 侧掩码域是
**单元素集 {全 1}**（`mem.isa` / `neon64.isa` / `sve_mem.isa` / `sme.isa` 一律
`std::vector<bool>(size, true)`）。本轮**真机实证**：`be_all_true == be_seen`（每一次被注入
请求的掩码都是全 1）。所以"另一合法掩码"在本平台**没有 ISA 来源**，只能由注入器**构造**
（内部位清零 ≥ 2B、尾位清零 ≡ size 改变）。这不是我们的选择，是规格与平台的交集。

### 1.3 传播 / 可观测性

- **L0/L1**：注入日志尾部自描述 `fault_field=` / `be_len=` / `be_ones=` / `be_subst=`
  （尾部追加，与 `lsu_phantom_audit.py` 的 `PRE_LINE_RE` 前缀假设兼容；契约测试 A10b 钉死），
  外加独立 stdout 行 `CHAOS_L0_A06:`（自守：非 A06 形运行逐字节不变）。
- **L3**：`CHAOSPropagation::registerInjection(site="lsq_pushRequest_PRE", …, old_size,
  new_size)`（`lsq.cc`）——size 故障的"故障值"= `new_size`，链路可证；地址注册表登记
  `[new_addr, new_addr+new_size)`。**byte-enable 的观测面在 L0/L1 注入日志，不在 PROP 迹**
  （`inj` 节点无掩码字段）——这是本轮的**诚实边界**，未新增事件 kind（避免动 `lsu_prop_fields.py`
  的 schema 与 campaign 契约）。
- **L5**：carrier 的 FNV-1a 校验和 + canary 判定（§6）。

---

## 2. 实现（本分支的改动）

### 2.1 load shrink 的安全载体（核心，三处）

定宽完成合同的事实链（**实证源码，非推断**）：
1. AArch64 load 的完成宽度按**静态指令**定宽：`arch/arm/isa/templates/mem.isa:487-512`
   `LoadCompleteAcc` 无条件 `getMemLE(pkt, Mem, traceData)`；
2. `arch/generic/memhelpers.hh:87` `getMemLE` → `getMem<LE>` → `mem = pkt->get<MemT>(Order)`
   = 从 packet data 读 `sizeof(MemT)` 字节（**无边界检查**）；
3. 而 load 的目的缓冲区按**（可能被注入的）请求 size** 分配：
   `cpu/o3/lsq_unit.cc` 的 `read()` 中转发路径 `new uint8_t[request->mainReq()->getSize()]`
   与访存路径同式；packet 数据经 `cpu/o3/lsq.cc` 的 `dataStatic(_inst->memData)` 绑定到它。

⇒ `new_size < 静态宽度` 时 `get<MemT>` **越界读**。修法（三处）：
- `cpu/o3/dyn_inst.hh`：新增 `unsigned chaosA06BufBytes = 0`（**仅** shrink 的 load 被赋值；
  0 = 未触碰 ⇒ 非 A06 运行的分配**逐字节不变**）。
- `cpu/o3/lsq.cc`：钩子返回后 `if (isLoad && size < pre_old_size)
  inst->chaosA06BufBytes = pre_old_size;`（trigger / legacy 两条路径都覆盖）。
- `cpu/o3/lsq_unit.cc`：**两个** load 目的缓冲分配点改为
  `a06_buf = max(getSize(), chaosA06BufBytes)`，被抬高时 `memset` 清零
  ⇒ shrink 的 load 以**零扩展截断**完成（正是【03-A06】预期的 load 形态）。

**为什么不直接把 buffer 改成恒定 `MaxDataBytes`**：`lsq_unit.hh:91`
`MaxDataBytes = MaxVecRegLenInBytes` = `1ULL << 16` = **65536 字节**（`arch/generic/vec_reg.hh:115`），
逐 load 分配 64 KiB 是**全局**性能/内存回退，且与 A06 无关。故改为**只在 shrink 时**抬高。

**符号扩展的诚实边界**：零填充 ⇒ 有符号 load 的完成是"零扩展"而非"符号扩展"。
【03-A06】的措辞是「截断**/**符号扩展错误」（or），故零扩展截断落在该措辞内；
若后续要求严格复现"符号扩展错误"，需要在完成点按指令符号性填充，属于**第二个点位**（§7）。

### 2.2 A06-a 判定：`a06LoadWiden` → `a06LoadSize`
合法集从"strict widen"改为"另一合法值"；护栏改为 `NoChange`（不写）+ `Geometry`
（`(addr&63)+target>64`，保住 `BaseCache::satisfyRequest` 的 packet-offset 不变量）；
汇总行新增 `load_nochange`，widen/shrink **分向计数**。

### 2.3 逐因计数在 tier 路由下补可达
`obs_pre_a06_load_{shrink,nochange,notarget,illegal,geom}` 此前**只在 legacy
（`--addrpath_lsu_tier off`）路径**可达：tier 路径的 op-class 过滤块在 `a06_size` 分支**之前**
就 `return size`，逐因 `switch` 永远到不了 ⇒ **F0/F2/F6（campaign 的真实路由）对 load 护栏失明**。
这就是 R4-6-A06「shrink 护栏未能在本轮真机复现」的**结构性原因**。修法：在过滤块内、
`++obs_pre_opclass` 之前补同一 `switch`（两路径互斥，无重复计数）。

**这个结构性缺陷有真机对照实证**：同一"load target = 1（≤ 所有 load 实宽 ⇒ 全部 shrink/equal）"
配置，`tier=off` 给出 `load_shrink=1467`，而 `tier=F0` 下逐因恒 0（见 §4.4 与 R4-6 的 6-seed 零）。

---

## 3. 未落地 / 明确不做

- **byte-enable 的 PROP 字段**（把 `be_len/be_ones/be_subst` 加进 `inj` 节点）：会动
  `lsu_prop_fields.py` 的 `PROP_EVT_FIELDS`/schema 与 campaign 契约，本轮**不越权**；
  L1 观测面留在注入日志。
- **load 侧掩码注入**：见 §1.2 —— 载体原因（load 掩码在本路径无架构消费者），只做观测。
- **carrier 源文件未改**：`workloads/directed/a06_size_be.c` 保持与各 worktree 里既存的未跟踪
  二进制 `workloads/directed/a06_size_be` 同源；改源会破坏这条 provenance（且会改变
  下面记录的 FNV 校验和）。store 掩码的价值级可观测性问题见 §5.2，建议的扩写在 §7。

---

## 4. 真机 spike（7 次，二进制 `7d52bc1392a10055`）

统一前置：`--cmd /tmp/r4-7-a06/a06_size_be --cpu O3 --chaos_addrpath --addrpath_mode byte7_zero
--addrpath_warmup_events 0 --addrpath_span_events 1000`，每次运行用
`flock /tmp/lsu_gem5_slot2.lock` 串行化（≤4 并发约束）。carrier 用
`gcc -O2 -static -Wall -Wextra` 编译：**零告警**，两次运行逐字节一致，原生输出
`ccc1290d633668c4` / `canary=0000000000000001`。

### 4.0 基线（无 A06 参数）
```
1234: ccc1290d633668c4
      canary=0000000000000001
      CHAOS_L0_DECLINE: pre_fired=0 pre_opclass=0 ... post_fired=1 post_nochange=1
```
⇒ SE 运行与原生输出**逐字节一致**（校验和口径可用）。

### 4.1 A06-b byte-enable（R4-6 未跑的那一步，本轮补上）
命令（seed 4242）：`--agu_pre_mode a06_size --agu_size_to 8 --agu_size_to_load 0 --agu_be_mode shift_mid`
```
CHAOS_L0_A06: pre_mode=a06_size size_to=8 load_size_to=0 be_mode=shift_mid
  load_widen=0 load_notarget=0 load_illegal=0 load_shrink=0 load_geom=0
  be_seen=1 be_all_true=1 be_subst=1 be_declined=0
```
注入日志：
```
Tick: 5857775, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x4903e0,
new_addr=0x4903e0, old_size=8, new_size=8, faults_injected: 1, isLoad=0,
isStore=1, fault_field=none, be_len=8, be_ones=8, be_subst=1
```
输出仍为 `ccc1290d633668c4` / `canary=…1`。

**结论**：`be_subst=1` ⇒ **A06-b 的 store 侧"另一合法掩码"注入真机可达**；同时
`be_all_true == be_seen == 1` ⇒ **ISA 掩码域 = {全 1} 的经验证据**（每一次被注入请求的掩码都是全 1）。
**但本 run 的 oracle 未变**——原因与边界见 §5.2（不是"模型没生效"）。

### 4.2 shrink 的证据（为什么必须双向；`be_declined` 的含义）
命令同 4.1 但 `--agu_size_to 2`（seed 4242）：
```
CHAOS_L0_A06: pre_mode=a06_size size_to=2 load_size_to=0 be_mode=shift_mid
  ... be_seen=1 be_all_true=1 be_subst=0 be_declined=1
注入日志: old_size=8, new_size=2, isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0
```
⇒ 该事件是 **store 侧 size 8→2（shrink）**，size 已变 ⇒ 按"一样本一故障"纪律，掩码让位（`be_declined=1`，**计数而非静默**）。

### 4.3 store 侧 shrink 的架构后果 = Crash（真机）
同 4.2 命令、seed 7：
```
Tick: 3347190, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x7ffffefd38,
new_addr=0x7ffffefd38, old_size=8, new_size=2, faults_injected: 1, isLoad=0,
isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0
→ panic: Page table fault when accessing virtual address 0x1050  (tick 3454990, rc=134)
```
**归因对照**（seed 7，只把 store 腿关掉 `--agu_size_to 0`）：`be_seen=0`、rc=0、**无 panic**。
⇒ 崩溃**确由 size 替换引起**：注入点落在**编译器生成的栈 store**（`0x7ffffefd38` 是栈），
把 8B 存成 2B 破坏了被保存的寄存器/返回地址 ⇒ 程序跳到 `0x1050` 取指/访存 ⇒ 架构异常。
这正是【03-A06】"partial store 最易静默污染相邻字节"的**强形态**（此处表现为 Crash）。
⇒ **store 侧 shrink 真机可达且后果真实**；它同时证明"shrink 不是不可能的"，只是
**load 侧**需要 §2.1 的载体下限。

### 4.4 load 侧 shrink 护栏（真机，逐因计数修复前的旧二进制）
legacy 路由 `--addrpath_lsu_tier off --addrpath_max_faults 1 --agu_size_to 0
--agu_size_to_load 1 --agu_be_mode observe`：
```
CHAOS_L0_A06: pre_mode=a06_size size_to=0 load_size_to=1 be_mode=observe
  load_widen=0 load_notarget=0 load_illegal=0 load_shrink=1467 load_geom=0
  be_seen=0 be_all_true=0 be_subst=0 be_declined=0
```
输出仍为 `ccc1290d633668c4` / `canary=…1`（`injected=0`，无崩溃）。
⇒ 护栏**真机在跑**：1467 次 load 候选被判 shrink/equal 而拒斥，零注入、零崩溃。
**同一配置在 `tier=F0` 下逐因恒 0**（即 §2.3 的失明缺陷）。反向 `--agu_size_to_load 16`
给 `load_widen=1`（target>实宽 ⇒ 加宽可达，与 R4-6 seed202 一致）。

### 4.5 汇总（本报告全部真机数字）
| run | 配置要点 | 关键计数 | 校验和 | rc |
|---|---|---|---|---|
| 4.0 | 基线 | post_fired=1 | ccc1290d… | 0 |
| 4.1 | size_to=8 / be=shift_mid | **be_subst=1**, be_all_true=1 | ccc1290d… | 0 |
| 4.2 | size_to=2 / be=shift_mid | be_subst=0, be_declined=1, fault_field=size | ccc1290d… | 0 |
| 4.3 | 同上 seed 7 | 注入 8→2 ⇒ **guest page-table fault** | n/a | **134** |
| 4.3' | 归因对照 size_to=0 | 无注入、无 panic | ccc1290d… | 0 |
| 4.4 | tier=off / load_to=1 | **load_shrink=1467**, injected=0 | ccc1290d… | 0 |
| 4.4' | tier=off / load_to=16 | load_widen=1 | ccc1290d… | 0 |

---

## 5. 载体可达性的代码路径证明（"不是我的负载没触发，而是不可能/需要另一点"）

### 5.1 load 侧掩码为何只能观测
- AArch64 全部访存路径传 `std::vector<bool>(size, true)`（`mem.isa:424,477`；
  `neon64.isa:328,355,411,443`；`sve_mem.isa`；`sme.isa`）⇒ 掩码域 {全 1}（§4.1 经验证实）。
- 掩码在本平台的唯一功能杠杆是 `LSQRequest::addReq`（`lsq.cc:1182-1217`）的**尾部连续 0 裁剪**
  `size - inactiveTailSize` ⇒ ≡ **size 改变**（load 侧被 §1.1 的合同管/已由载体兜住）。
- 非尾部 0 的架构消费者在 **store** 侧：`Request::isMasked()`（`mem/request.hh:727-734`）
  → `Packet::isMaskedWrite()`：`mem/cache/mshr.cc:139-147`（masked write **不进**
  `writesBitmap` ⇒ 不全行合并）、`mem/cache/cache.cc:405`（masked write **不**被
  `promoteWholeLineWrites` 提升为 `WriteLineReq`）。load 路径没有对应消费者。
⇒ load 掩码 = **观测**（普查 `be_len/be_ones/be_all_true`），这不是省事，是无消费者。

### 5.2 为什么 4.1 的 oracle 没变（诚实边界，不是缺陷）
- `shift_mid` 清零的是**该 store 自身范围内**的一个内部字节（`index=(size-1)/2`，
  见契约测试 A7），**不越界**踩相邻 canary ⇒ canary 判定本就不会响。
- 而被清零字节的**读回**很可能走 **store→load 转发**：`lsq_unit.cc` 转发分支
  `memcpy(load_inst->memData, store_it->data()+shift_amt, getSize())` 拷贝的是 SQ 里
  **完整**的 store data（**不看掩码**）⇒ 值级差异被转发掩盖。
- 结论：**store 掩码的价值级可观测性受 oracle/转发窗口限制**，需要"掩码 store → 排空
  SQ → 再读回"的载体形态（§7）。本轮**不宣称** store 掩码是 value-SDC。

### 5.3 load shrink 的"另一点位"边界
§2.1 已把 load shrink 的**截断**实现到完成缓冲层面（零扩展）。若要求严格复现
**符号扩展错误**（`LDRSW` 类），需在完成点按指令符号性填充——那是**另一个点位**
（`completeAcc` 之前的值语义替换），不属于 AGU 的 size 字段，需单独裁定。

---

## 6. 契约测试（真跑，全部本机）

```
$ python3 tests/test_lsu_a06_loadsize.py
PASS A1_a06_not_in_pre_store_only          PASS A2_load_envelope_widen_or_shrink
PASS A2b_shrink_carrier_wired              PASS A2c_carrier_inert_by_default
PASS A3_widen_block_geometry_guard         PASS A4_legal_target_set
PASS A5_load_verdict_before_trigger        PASS A5b_per_reason_counting_in_tier_path
PASS A6_be_decline_counted                 PASS A7_be_mask_interior_only
PASS A8_be_mode_loud_refusal               PASS A9_rejected_alias_intact
PASS A10_evidence_fields                   PASS A10c_load_direction_counters
PASS A10b_log_tail_appended                PASS A11_lsq_wiring
PASS A12_signature_consistent              PASS A13_param_aguSizeToLoad_wired
PASS A13_param_beMode_wired                PASS A14_member_and_init_order
PASS B0_carrier_exists                     PASS B1_carrier_builds_clean
PASS B2_carrier_deterministic              PASS B3_carrier_oracle_lines
PASS C1_a06_route_spec_mode                PASS C2_a06_route_has_load_target
PASS C3_a06_still_blocked                  PASS C4_no_a06s_model_id
PASS C5_alias_absent_from_proxy_choices    PASS C6_be_mode_choices_declared
PASS C7_proxy_be_mode_validation
FAILURES: 无            (30/30 PASS, rc=0)
```
```
$ python3 tests/test_lsu_a06_ruling.py
PASS a06_mode_name_is_spec_legal   PASS a06_runids_blocked
PASS a06_blocked_reason_mentions_loadside   PASS a06s_model_id_absent
SKIP a06s_alias_rejected_at_config   <- gem5 binary absent at
  …/r4-7-a06/CHAOS/gem5/build/ARM/gem5.opt (needs integration build; NOT a pass)
FAILURES: 无
```
> SKIP 是**诚实 skip**（该判据需 gem5 二进制；本 worktree 禁构建），绝不谎报 PASS。

回归（不受影响面）：`test_lsu_hook_{a07,lsq,sq,lsqfwd}` / `test_lsu_chain_check` /
`test_lsu_prop_fields` → **ALL PASS**；`test_lsu_coverage_matrix` / `test_lsu_runid_map` /
`test_lsu_pilot_evidence` → **FAILURES: 无**；`py_compile`（4 个 Python 文件）→ OK。

---

## 7. 集成时必须做的事（orchestrator）

1. **构建**：`cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` —— 零新增 warning/error。
   本分支 C++ 为 **compile-unverified**，风险点已最小化：
   `chaosA06BufBytes` 用类内初始化（与 `memData` 同款，DynInst 逐指令新建）；
   两处分配点只用文件内既有的 `memset`，**未**引入 `std::max`/`<algorithm>`
   （改用显式 `unsigned a06_buf` 比较）；`a06LoadSize` 的调用点与声明同步改名。
2. **跑 §4 的 spike（用**新**二进制）**：至少
   (a) `--agu_size_to 8 --agu_be_mode shift_mid` 应仍给 `be_subst≥1`；
   (b) `--agu_size_to 2` 应给 `load_shrink≥1`（**新增可达**）且**无越界/无 assert**；
   (c) tier 路由（F0/F2/F6）+ 一个"必然拒斥"配置（`--agu_size_to_load 1`）应给
   `load_shrink≥1`（§2.3 修复的直接验收）。
3. **A06-b 价值级可观测**（可选、建议）：扩写 carrier 加"掩码 store → 排空 SQ → 读回"对，
   与 `--agu_be_mode off` 同 seed 对照，差异必须能归因到 `be_subst=1`（否则如实标为"未见价值级后果"）。
4. **解除 BLOCKED 的判据**：§2.1 的 C++ 构建通过 + (b)(c) 实测通过 + byte-enable 至少
   在 (a) 上复现 ⇒ 才可把 A06 6 个 RunID 从 `MODEL_BLOCKED` 摘除。

## 8. 未验证 / 诚实清单

- 本分支全部 C++ 改动 **未编译**（worktree 禁 scons）——§4 的所有数字都出自**集成前**二进制，
  因此 `load_shrink≥1` 与新 stdout 格式**尚未**真机出现；`load_shrink` 的旧二进制数字
  （4.4，1467）只证明"护栏在跑"，不证明"新路径在跑"。
- store 掩码的**价值级**后果未观测到（§5.2）；不宣称 value-SDC。
- 有符号 load 的"符号扩展错误"未实现（§2.1、§5.3）。
- `tests/test_lsu_a06_ruling.py` 的 1 项判据因缺二进制被诚实 SKIP（§6）。
