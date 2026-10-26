# R4-10 证据报告：A06 六 RULING 独立复核 + UNRESOLVED 残余收敛

- worktree `.claude/worktrees/r4-10-spec`，分支 `r4-10-spec`，基线 `lsu-mdspec-20261019` @ `d63a5dd8`
- 日期 2026-10-22
- 约束遵守：**未构建 gem5**（仅真跑既有二进制做 census/spike）；**未跑正式 campaign**；
  **未改 `docs/gem5-fi/lsu/mdspec/*`**（共享证据）。
- 真机二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
  （sha256 前缀 `54c2c78ce4c84bb2`）。configs 取本 worktree。

---

## 0. 基线台账的**实际**残余（复核后订正任务书的口径）

- 基线 `ready_contract`：`READY=241 / PARTIAL=0 / BLOCKED=84`；
  `RULING=6 / FS-INFRA=24 / MODE-UNIMPL=3 / UNRESOLVED=4 / FS-MULTICORE=35 / LICENSE=12`。
- **A06 六格**（A06-F0/F2/F6 × W3/W5）：`resolve_cell` 全部返回 BLOCKED 理由串（RULING）。
- **UNRESOLVED 4 的实际成员** = `S01-F0-W1`、`S02-F0-W1`、`S10-F2-W5`、`S10-F2-W9`
  （`ready_contract.md` L80/87/121/122）。**其中只有 2 个属 S10**；任务书括注的
  "S10-F0/F2/F5 × W5/W9"与实测不符 —— S10-F0-W5/W9 与 S10-F5-W5/W9 在基线已为 **READY**。
- **本轨两条真机 census 复跑**（S10-F0-W5/W9）用于**独立验证**基线结论，非重做。

---

## 1. 任务 A：A06 六 RULING —— 三条路径的**真实规格语义**与裁决

规格依据：`...方案-03-位置x模型矩阵.md` A06 行（A06-a「access size 改为另一合法值」；
A06-b「byte-enable 改为另一合法掩码」；触发=子字节或向量访存；预期 load 形态
「截断/符号扩展错误」）。

### 1.1 load-side fixed-width completion contract **究竟要求什么**（源码实证链）

1. `arch/arm/isa/templates/mem.isa:499`（`LoadCompleteAcc`）：`getMemLE(pkt, Mem, traceData);`
   —— `Mem` 是**静态指令操作数类型**（如 `uint64_t`），与 request/注入后的 size 无关。
2. `arch/generic/memhelpers.hh:80`（`getMem`）：`mem = pkt->get<MemT>(Order);`
3. `mem/packet_access.hh:55`（`Packet::getRaw<T>`）：
   ```
   assert(flags.isSet(STATIC_DATA|DYNAMIC_DATA));
   assert(sizeof(T) <= size);        // line 55
   return *(T*)data;
   ```
   此处 `size` 是 **Packet 的 size 字段**（`packet.hh:397 unsigned size;`），由
   `packet.hh:908 size = req->getSize();` 从 Request 设置。

**结论**：合同 = 「静态访问宽度 × 完成缓冲 × packet size 三者等宽」。packet size 直接
等于（可能被注入的）request size。因此 **request size < 静态宽度 ⇒ packet size <
`sizeof(MemT)` ⇒ 断言在**任何读之前**触发**。断言与**目的缓冲区**（`LSQUnit::read`
里 `new uint8_t[getSize()]` / `dyn_inst.hh` 的 `memData`）无关。

### 1.2 byte-enable 的**可实现边界**

- **ISA 侧掩码域 = 单元素集 {全 1}**：AArch64 全部访存路径传
  `std::vector<bool>(size, true)`（`mem.isa`/`neon64.isa`/`sve_mem.isa`/`sme.isa`）。
  ⇒ 规格所说"另一合法掩码"**在本平台没有 ISA 来源**，只能由注入器**构造**。
- **唯一的架构杠杆在 store 侧**：`Request::isMasked()` → `Packet::isMaskedWrite()`
  → `MSHR::TargetList::add`（masked write 不进 `writesBitmap`）/ `BaseCache::
  promoteWholeLineWrites`（masked write 不被提升为 `WriteLineReq`）。
- **load 侧掩码无架构消费者**：掩码在本路径唯一作用是 `LSQRequest::addReq` 的**尾部连续 0
  裁剪**（≡ size 改变，被 §1.1 合同管）。⇒ load 掩码**只能观测**，不能 faithful 注入。
- **store 侧可实现且已真机验证**：`--agu_be_mode shift_mid`（全 1 内部位清零），
  R4-6/R4-8 真机给出 `be_subst=1`；`be_all_true == be_seen`（掩码恒全 1 的经验证据）。

### 1.3 shrink 是否**真的结构性不可达** —— 独立复核裁决

**裁决：维持"结构性不可达 + 响亮拒绝"（源码控制流证明，非 carrier 未命中）。**

- 证明：§1.1 的三段链**每一步都是无条件语句**（`LoadCompleteAcc` 不查 request size；
  `getMem` 不做边界检查；`getRaw` 只有那条断言）。⇒ shrink 的注入**必然**命中断言。
- 真机旁证（R4-8-INT 已记录，本轮未重跑）：`--agu_size_to_load 1` →
  `SIGABRT: Assertion 'sizeof(T) <= size' failed (T = unsigned long)`（rc=134）。
- R4-8-A06 草案的"提高目的缓冲区（`chaosA06BufBytes`）即可安全 shrink"**前提被证伪**：
  它 floor 的是目的缓冲区，而断言 key 的是 **packet size**。该 buffer-floor 代码
  （`dyn_inst.hh:365` + `lsq.cc:824` + `lsq_unit.cc:1726/1936` 两处）在 `a06_size` 下
  **结构性不可达**（唯一会写 `chaosA06BufBytes` 的条件 `isLoad && size < pre_old_size`
  永不成立，因为 shrink 在 verdict 阶段已被拒）。
- **faithful shrink 的代价**：需保持 `pkt->size ≥ 静态宽度`、在 **commit 处**做截断/符号扩展
  —— 即改 `arch/generic/memhelpers.hh` 的 ISA-generic 完成语义，或另设**值语义点位**。
  这**不是** AGU 的 size 字段 ⇒ **SPEC-SCOPE 裁决项**（见 §3）。

### 1.4 本轮修复的实现保真度缺陷（诚实口径）

| 编号 | 缺陷 | 修复 |
|---|---|---|
| D1 | `ShrinkUnsafe` 落 `default: break;`，**无逐因计数**，与"declined loudly, counted"声明不符 | 新增 `obs_pre_a06_load_shrink_unsafe`，两处 switch 各一；汇总行输出 `load_shrink_unsafe=` |
| D2 | `obs_pre_a06_load_shrink` 现为**死计数**（唯一自增点不可达）却仍打印 `load_shrink=0` —— 静默零 | 如实标注为结构性死计数（保留字段以求稳定） |
| D3 | `CHAOSAddrPath.hh` 195–205 称"load 接受 FULL 包络 + 靠 buffer floor 保底"，与 207–220 的"shrink 已拒绝"矛盾 | 注释订正；buffer-floor 标注"保留但结构性不可达" |

### 1.5 六格逐项裁决

| RunID | 裁决 | 证据 | 状态 |
|---|---|---|---|
| A06-F0-W3 | 可实现部分已实现；load SHRINK 结构性拒绝 | §1.1/§1.3 证明链；widen/byte-enable 真机 activated=1 | 仍 BLOCKED（SPEC-SCOPE + F0 跨度未实测） |
| A06-F0-W5 | 同上 | 同上 | 同上 |
| A06-F2-W3 | 同上 | 同上 | 同上 |
| A06-F2-W5 | 同上 | 同上 | 同上 |
| A06-F6-W3 | 同上 | 同上 | 同上 |
| A06-F6-W5 | 同上 | 同上 | 同上 |

---

## 2. 任务 B：UNRESOLVED 4 的收敛

### 2.1 S10-F0-W5 / S10-F0-W9 —— **独立实测复跑，维持 READY**

真机 census（`--lsqfwd_span_events 1000000` 使 draw 不落，teardown `eligible=` 即整条流长）：
```
# S10-F0-W5 (sq_forward)
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=4 eligible=3 injected=0 ...
CHAOS_LSU_S10_FORK: ... arm1_cand_ok=3 max_live_ssids=3 max_cands=3
# S10-F0-W9 (gap_bfs)
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=5 eligible=4 injected=0 ...
CHAOS_LSU_S10_FORK: ... arm1_cand_ok=4 max_live_ssids=4 max_cands=4
```
⇒ **逐格 span 实测值 3 / 4 复现成立（不是估计）**，与 `LSQFWD_F0_SPAN` 一致；
`arm1_cand_ok>0 / max_live_ssids>0` 同时**复证 StoreSet SSIT 平台修复在当前二进制生效**。

### 2.2 S10-F5-W5 / S10-F5-W9 —— 维持 READY（基线已真机 activated）

### 2.3 S10-F2-W5 / S10-F2-W9 —— 显式裁决 = **(iii) 规格要求结构性拒绝**

- 证据（源码 + 实测）：`chaos_lsu_trigger.hh:203` `case F2: return 100000;`（规格钉死）；
  `:211 next_fire = from + iv/2 + rng % iv` ⇒ **首次触发下界 = iv/2 = 50000**；
  实测流长 3 / 4 ⇒ 差 **4 个数量级**，任何 seed 都不落。
- (i) 不成立：改 interval = 改故障模型语义（F2 字面 = 每 ~1e5 eligible events 注入一次）。
- (ii) 仅经由**规格级**重划 cell（新长载体 + 其 golden/oracle）方可，非本轨可单方决定。
- 已由契约测试钉死（`test_lsu_hook_s10.py`：理由须点名 `SPEC-FIXED` + `may NOT be re-tuned`
  + 数字下界 `50000`）。

### 2.4 S01-F0-W1 / S02-F0-W1 —— F0 逐格 span **实测中**（见 §4）

基线 BLOCKED 理由 = `F0-span-unmeasured`（`mibench/bin/w1_all` 的 eligible 流长未实测）。
本轮已发起真机 census（`workloads/mibench/bin/w1_all`，S01=`--lsq_struct_mode byte_flip`），
teardown `eligible=` 即位流长。**结果见 §4**。

---

## 3. 待主 agent 构建清单（本轨禁 scons）

1. **C++ 改动（compile-unverified）**：`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{hh,cc}`
   —— 新增 `obs_pre_a06_load_shrink_unsafe` 计数器 + 汇总字段 + 注释订正。
   构建命令：`cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`（零新增 warning/error）。
2. **构建后真机 spike（用**新**二进制）**：
   (a) `--agu_pre_mode a06_size --agu_size_to_load 1`（load shrink）应给
       `CHAOS_L0_A06: ... load_shrink_unsafe≥1 load_shrink=0` 且 **rc=0 无 SIGABRT**
       （旧二进制此处 rc=134）；
   (b) 同一 A06 路由的 widen 配置应给 `load_widen≥1`，byte-enable `be_subst≥1` 不回归。
3. **台账重生成**（本轨禁改 mdspec）：`python3 tools/lsu_ready_contract.py` → 更新
   `ready_contract.{json,md}` / `coverage_matrix.md` / `blocked_triage.md` / `runid_map.json`。
   预期变化：S01/S02-F0-W1 由 UNRESOLVED → READY（若 §4 实测通过）⇒ `UNRESOLVED 4→2`。

---

## 4. S01 / S02 F0 跨度实测 —— **状态：真机 census 已发起，未在本次预算内收敛**

`workloads/mibench/bin/w1_all` 是**十个 benchmark 的单进程套件**（日志
`[w1] start ten-benchmark suite (single process, workdir isolated)`），在本机 O3 配置下
单次全量运行 **> 40 分钟仍未结束**（进程实测 99.7% CPU 持续运行，非挂起）。
本轨按预算**不阻塞等待**，如实登记为**未闭环**（**未**把估计值写成实测值）。

真机 census 命令（逐字，可复现；跑完后 teardown 的 `CHAOS_LSU_TRIGGER ... eligible=` 即位流长）：
```bash
flock /tmp/lsu_gem5_slot3.lock -c 'cd <THIS_WORKTREE> && \
  <prebuilt 54c2c78ce4c84bb2> --outdir=/tmp/r4-10-spec/c_s01w1 configs/se/lsu_proxy.py \
  --cmd <THIS_WORKTREE>/workloads/mibench/bin/w1_all --cpu O3 \
  --chaos_lsqfwd --lsq_struct_mode byte_flip \
  --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 1000000 --rng_seed 1'
```
（S02 同形，额外 `--bits_to_change 2`。）
⇒ 主 agent 侧只需：等该 run 结束 → 读 `eligible=` → 写入
`LSQFWD_F0_SPAN[("S01","mibench/bin/w1_all")]` / `[("S02","mibench/bin/w1_all")]`
→ 契约测试加两行钉死（`UNRESOLVED 4→2`）。**本轨未写任何估计值。**

---

## 5. 未闭环项 / 最小外部资源清单

| 项 | 类别 | 精确原因 | 最小外部资源 |
|---|---|---|---|
| A06 load SHRINK | SPEC-SCOPE | 平台 ISA-generic 完成语义不支持"注入后 request 窄于静态宽度" | 规格二选一：(A) A06-a load 侧仅保留 widen；(B) 立项改 `memhelpers.hh` 完成语义/新增值语义点位 |
| A06 F0 跨度 | 实测未做 | 本轨预算用于 S10/UNRESOLVED；A06 载体 `agu_addrmodes`/`sq_forward` 存在 | 1 次 census（EARLY_BIAS 告警 eligible 1677 ≫ span 1000，需大 span） |
| A06 pilot | 样本不足 | 基线仅 1 seed | 3-seed pilot（构建后） |
| S10-F2-W5/W9 | 结构性（iii） | 见 §2.3 | 规格裁决 (ii) 长载体 or 显式 n/a |
