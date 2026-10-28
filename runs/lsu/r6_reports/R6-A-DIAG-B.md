# R6-A-DIAG-B — A04 / A05 / A06 只读诊断（Lane B）

- Lane: B（只读诊断）。Date: 2026-10-28。
- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`
- Branch/HEAD: `fix/r6-a-unit-20261028` / `eab58f3514cc4844898671d2f38d77e478917df8`（起点 `659fa4cf`）。
- 当前二进制: `CHAOS/gem5/build/ARM/gem5.opt`，SHA-256 `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`；`binary_source_head=1f344a5b66da30267c578536e00a1ad4ad56bb31`，已核验为 HEAD 祖先。
- `git diff --stat 1f344a5b..HEAD -- CHAOS/gem5/src configs/se tools workloads` 为空 ⇒ 本报告引用的 C++/config/tools 行号即当前二进制源码。
- 方法：只读 `grep/rg`、`sed`、`Read`、`python3`（JSON/openpyxl）、`git log/show/diff`、`stat/sha256sum`、`zcat/gzip -t`、`objdump/nm`、`strings`；未构建、未启动 gem5、未修改任何证据目录。唯一写入文件为本报告。

---

## 0. 权威状态源的互相矛盾（先钉死口径）

同一个 A04/A05 单元在不同权威产物中状态不一致，**不能混用**：

| 来源 | A04 | A05 | A06 | 口径 |
|---|---|---|---|---|
| `docs/gem5-fi/lsu/mdspec/coverage_matrix.md:23-31` | `PASS` | `PASS` | `BLOCKED` | 节点级覆盖（pilot 观测到全部 kind），不是 RunID 准入 |
| `docs/gem5-fi/lsu/mdspec/runid_map.json:569-850`（A04 各 entry `"status"`） | `PARTIAL` | `PARTIAL` | `BLOCKED` | MDSPEC 规格实现状态 |
| `docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md:27-41` | `evidence_state=NOT_RUN, eligibility=RUNNABLE, blocker=NONE` | 同左 | `NOT_RUN, BLOCKED, RULING` | 磁盘事实 × 上游阻塞两轴（2026-10-25） |
| XLSX `7.展开执行矩阵` rows 14-28 | `R6证据状态=UNPROVEN` | `UNPROVEN` | `BLOCKED` | 2026-10-27 回填 |
| `docs/gem5-fi/lsu/mdspec/ready_contract.md:27-41` | `BLOCKED`（`CHAIN-UNPROVEN` / `CHAIN-EVIDENCE-MISSING`） | 同左 | `BLOCKED RULING` | 契约准入 |

结论：coverage 的 `PASS` 只是“节点实现+曾在 pilot 出现”，**不是** RunID 证据完成；本报告按 `docs/superpowers/plans/2026-10-28-r6-a-unit.md:20-25` 的固定类别（READY_FOR_CANARY / POLICY_EXCLUDED_F6 / BLOCKED_WORKLOAD_GAP / BLOCKED_RULING / NOT_IMPLEMENTED / IMPLEMENTED_NOT_ROUTED / ROUTED_NOT_RUN / REVIEW_REQUIRED）给建议。A06 的 `RULING` 类别与解除条件见 `blocked_triage.md:11,28,60-65`。

---

## 1. A04 — 同对象内 / 同页内合法地址换值

### 1.1 规格

`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md:14`（A04 行）：

> 把EA替换成同一已分配对象或同页内另一个对齐合法地址；禁止替换成未映射地址。实施细则：**不生成任意随机位串，而是从当前运行中选择另一个满足对齐、范围、编码和生命周期约束的合法值；保存 source/target 及候选集合**。每次运行只替换一个字段或一个选择结果，**非法候选、空闲项和已经释放的事务不得使用**。

触发列：`地址属于带oracle对象时`；子模型：`A04-a 同对象内合法地址替换；A04-b 同页内合法地址替换`（`03:14`；`07:23-28`；`runid_map.json:574`）。

### 1.2 实现事实

- 模式名 `a04_subst`，campaign 路由 `tools/lsu_campaign.py:358`（`--agu_pre_mode a04_subst`）。
- 实现 `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc:585-595`：

```cpp
if (pre_mode == "a04_subst" || pre_mode == "a08_subst") {
    const Addr page = addr & ~(Addr)0xFFF;
    Addr cand;
    do {
        cand = page | ((Addr)(rng() % 256) << 4);
    } while (cand == addr);
    addr = cand;
}
```

- 头文件自述这是代理：`CHAOSAddrPath.hh:42-45`“same-4KiB-page legal substitution — "same object" needs the W9 oracle table, documented proxy”。
- 注入主路径在 `LSQ::pushRequest` PRE 钩子；`lsq.cc:795-826` 把 PRE 结果登记到 `CHAOSPropagation::registerInjection`，并（仅 shrink load）设置 `chaosA06BufBytes`。

### 1.3 候选生成器与约束审计

| 规格约束 | 实现 | 结论 |
|---|---|---|
| 同一已分配对象（A04-a） | **无对象表/无边界检查**，只取同页随机 16B 槽 | **未实现** |
| 同页内另一合法地址（A04-b） | `addr & ~0xFFF` + `((rng()%256)<<4)`，循环排除原值 | 已实现（代理） |
| 对齐 | 固定 16B 对齐，不按访问 size 推导 | 对齐严格≥自然对齐（1/2/4/8/16 均可），但非规格化规则 |
| 页边界 | 16B 槽 + size≤16 ⇒ `[cand,cand+size)` 必在同一 4KiB 页 | 满足 |
| 禁止未映射 | 只保证同页；SE/FS 页粒度映射下原页已映射 ⇒ 同页候选也已映射；**无显式检查** | 结构性满足，未显式验证 |
| guard page | 候选恒在同页，guard page 是另一页 ⇒ **A04-b 结构上不会碰 guard page** | 满足但 guard 检测不可能触发 |
| 对象生命周期/空闲项 | 无 liveness/alloc 表 | **未实现** |
| 保存 source/target 及候选集合 | 注入日志/PROP 只有 `old_addr/new_addr`；候选集合**未保存** | 部分 |
| 每次一个字段/选择 | 每次仅改 addr | 满足 |
| 触发=`地址属于带oracle对象时` | **无 oracle 对象过滤**；op-class 过滤只对 L01/L02/Sxx 等生效（`CHAOSAddrPath.cc:496-511`），A04 无过滤 | **未实现** |

候选 `do/while` 在 16B 对齐时最多重抽 1/256；原地址非 16B 对齐时必不相等，不会死循环。

### 1.4 子模型可达性

- **A04-a（同对象）：NOT_IMPLEMENTED**。代码没有对象表，`a04_subst` 恒为同页代理；`CHAOSAddrPath.hh:42-45` 自述需要 W9 oracle object table（当前不存在于本树）。
- **A04-b（同页）：IMPLEMENTED**，`a04_subst` 可达；但“合法/已分配”只由同页代理保证，不保证在带 oracle 的对象内，也不保证对象内槽位已初始化。

### 1.5 W3 与 W0 的 oracle 差异

| 项 | W3 `agu_addrmodes` | W0 `mini_check` |
|---|---|---|
| golden | `728e604ffcec539d`（`runid_map.json` A04-F0-W3 workload.golden；旧运行实际输出同值） | `07568da9f3ad5665`（`runid_map` A04-F0-W0） |
| oracle 形态 | 64×8B 数组（符号 `array` = `0x493000`，`nm` 实测），10 种寻址模式 + 页末 8B 读（`workloads/directed/agu_addrmodes.c:1-72`）；末尾 FNV-1a 校验和 | 64×8B `data`（`nm`: `0x4919a0`/`0x496e80`）+ 指针链 + volatile round-trip + mmap 8192B 的 page1/page2，page2 `PROT_NONE`（`workloads/directed/mini_check.c:1-72`）；末尾 FNV-1a |
| guard page | 无 | 有，但 SE 下 `mprotect` 被忽略（`mini_check.c:17-22` 自述；A05/A06 的 `run.err` 实测 SE 打印 `ignoring syscall mprotect`，同一 SE 语义） |
| A04-b 对 guard 的影响 | 无 guard | 同页替换**永不跨到 page2**，guard 不可能触发；SE 下即使跨页也可写 |
| 地址/对象边界 | 数组 512B 在 4KiB 页（`array` 0x493000-0x493200，`output` 0x493200-0x493400 同页），候选可落到 `output` 或同页其它数据 | 数组 512B 在 .bss 页，候选可落到同页其它全局/mmap 之外的已映射页 |
| 每地址 oracle | **无**；只有末校验和（“每地址附软件 oracle”未实现为逐地址断言） | **无**；同左 |

因此 W3/W0 都是“末校验和”oracle；W0 的 guard page 在 SE 下退化，且与 A04-b 同页语义正交。W3 更适合观察“同页错误元素”的 SDC；W0 的指针链会放大错误索引，但两者都不能证明“地址属于 oracle 对象”。

### 1.6 A04 旧 pilot 的关键反证（详见 §4）

旧 pilot 注入 `0x48e870 → 0x48ec40`（同页 `0x48e000`，16B 对齐，`ldrb` at PC `0x40bfec`）。`0x40bfec` 属 glibc `__tunable_get_val`，`0x48e870` 不是 `array`（`0x493000`）。⇒ 按规格触发列“地址属于带 oracle 对象时”，该样本应为 **Injected-not-activated**，而不是 activated；当前实现无此过滤。

---

## 2. A05 — base/index、SXTW/UXTW、shift、pre/post-index 四子模型

### 2.1 规格

`03:15`（A05 行）：

> 互换base与index；SXTW↔UXTW；shift量替换为另一合法值；pre-index↔post-index仅改变更新时点。实施细则：**保持各输入片段本身不变，只修改片段来源、顺序、移位量或拼接选择**……**每次运行只启用一种拼接规则**，记录每个输出字节/子字段的真实来源。

触发列：`命中对应AArch64寻址模式`；子模型：`A05-a base/index互换；A05-b SXTW/UXTW互换；A05-c shift错误；A05-d pre/post-index错误`（`03:15`；`07:29-31`；`runid_map.json:856`）。

### 2.2 四子模型逐项结论

| 子模型 | 状态 | 证据 |
|---|---|---|
| A05-a base/index 互换 | **NOT_IMPLEMENTED** | 只有 `a05_shift`；无子模型参数（`CHAOSAddrPath.hh:261` choices 无 a05-a/b/d）；头文件明说 base/index/extend-swap “NOT expressible from the final addr — deferred, R5”（`CHAOSAddrPath.hh:43-45`） |
| A05-b SXTW/UXTW 互换 | **NOT_IMPLEMENTED** | 同上；且当前 W3 主函数反汇编**没有 sxtw/uxtw 寻址指令**（`objdump --disassemble=main` 164 行仅 2 处 `[x,x]` 向量寻址、无 sxtw/uxtw；C 源码的 UXTW/SXTW 循环被 -O2 强度削减成 post-index 指针步进） |
| A05-c shift 错误 | **IMPLEMENTED（近似）+ ROUTED；本轮未触发** | `CHAOSAddrPath.cc:596-601` 把最终 EA 低字节循环左移 `d∈[1,7]`；campaign `--agu_pre_mode a05_shift`（`lsu_campaign.py:359`）。旧 `r6_n6_A05-F0-W3_s1` 有真实注入 `0x4000d0→0x4000a1`（低字节 0xd0 左移 1 = 0xa1），但落在 `__libc_setup_tls` 的 `ldr x2,[x0,#32]`（base+imm，**不是** shifted-register 寻址） |
| A05-d pre/post-index 错误 | **NOT_IMPLEMENTED** | 无基址写回时点钩子/参数；最终 EA 钩子无法表达“写回 before/after” |

补充：`runid_map.json:172,197,222` 自己记录“注入近似：当前仅 a05_shift，未覆盖 base/index 与 extend、pre/post 全部子模型；传播仍缺”。

### 2.3 路由与频率

- 路由：`tools/lsu_campaign.py:359` 固定 `--agu_pre_mode a05_shift`；`configs/se/lsu_proxy.py:551-552` choices 含该值；`lsu_proxy.py:1193` 传 `preMode`。
- **没有 fault_type/子模型参数**：A05 的四个子模型名只存在于 runid_map/XLSX 文档；CLI 只能选 `a05_shift`。
- F0/F2 只影响触发时机（`chaos_lsu_trigger.hh`：F0 一次、F2 平均 100,000 eligible），**不影响子模型选择**。
- `lsu_campaign.py:1124-1150` 对 A05 使用 `warmup=0, span=1000`（A07 才用逐 workload census）；旧运行触发 `CHAOS_LSU_TRIGGER_ALARM: EARLY_BIAS ... eligible=2800 → span=1000`。

### 2.4 触发条件未实现（关键）

`CHAOSAddrPath.cc:496-511` 的 eligibility 只有 `pre_load_only/pre_store_only`（L01/L02/Sxx）与 `a06_load_declined`；A05 无任何“命中对应寻址模式”的过滤。旧 `A05-F0-W3` 实际注入的指令 `0x400f18 ldr x2,[x0,#32]`（`objdump` 实测，函数 `__libc_setup_tls`）是 base+imm，不是 shifted-register；因此该注入不符合 A05-c 的触发语义。当前代码同样如此。

### 2.5 无效果注入（noop）缺陷

`CHAOSAddrPath.cc:600-602`：

```cpp
const uint64_t d = 1 + rng() % 7;
const Addr lo = addr & 0xFF;
addr = (addr & ~(Addr)0xFF) | ((lo << d | lo >> (8 - d)) & 0xFF);
```

若原低字节为 `0x00`/`0xFF`（以及对某些 d 为 `0x55`/`0xAA` 等），旋转后地址不变，但代码仍 `++l0_funnel.injected; ++faults_injected_count`（`:799-801`），形成 “injected 但未改值” 的 noop。findings `F-049` 记录旧 A05-F0-W3 有 2 个 noop（`findings.md:65`）。

### 2.6 辅助 canary 的可行方式（本报告不运行）

- **A05-c 可用当前二进制做有界辅助 canary**：`--agu_pre_mode a05_shift --addrpath_lsu_tier F0 --addrpath_warmup_events 1 --addrpath_span_events <census>`，以注入日志 `old_addr/new_addr` 验证“仅低字节变化 + 被下游读取”；必须标注 auxiliary，且**不得**计入 3 个正式 seed。注意它仍不能证明“指令使用 shifted 寻址”。
- **A05-a/b/d 当前无法 canary**：需要新的 AGU 操作数级钩子（base/index/extend/shift/pre-post 与基址写回），final-EA PRE 钩子拿不到。可以另建 asm 形态的 canary 负载（显式 `ldr x,[xN,xM,lsl #3]`、`ldr w,[xN,wM,sxtw]`、`ldr x,[xN],#8`），但这是代码/负载改动，且**不能冒充 W3 正式载体**。
- **3 个正式 seed 不能冒充 4 子模型**：当前只有 `a05_shift`，3 seed 最多重复命中 A05-c；a/b/d 无路由，覆盖率恒为 1/4。

---

## 3. A06 裁决审计（access-size / byte-enable）

### 3.1 规格原文与“唯一性”缺口

`03:16`（A06 行）：

> 把1/2/4/8/16B size或byte-enable替换为另一合法组合；保持地址不变。……一次运行只改变一个状态位或一种状态转换；清零、伪造、提前置位和延后清除分别统计，不在同一样本叠加。

> 预期结果：partial store最易静默污染相邻字节；**load可能表现为截断/符号扩展错误**。

子模型：`A06-a access size改为另一合法值；A06-b byte-enable改为另一合法掩码`；触发：`子字节或向量访存`（`03:16`；`07:32-37`；`runid_map.json:997`；XLSX sheet 7 rows 23-28）。

规格**没有**规定：
1. size 方向的边界（load shrink 是否在模型内；“另一合法值”是否包含变窄）；
2. 目标值的选择规则（固定 target、按 seed 采样、还是确定性函数）；
3. “另一合法掩码”的合法性定义（子集/连续/至少一字节/不得跨对象/尾部清零是否算）；
4. load 侧掩码是否有意义（平台 ISA 掩码域只有全 1）；
5. “子字节或向量访存”的判定口径（size<8？16B vector？LDP/STP？）。

### 3.2 既有裁决记录时间线（事实）

| 日期/文件 | 内容 | 性质 |
|---|---|---|
| `docs/superpowers/plans/2026-10-19-lsu-mdspec-port-and-l05.md:58-68`（§2 A06 专项裁决） | store 侧 size 安全；load 侧 shrink 不安全；load widen 未验证；A06-b 需在 packet 构建层另立钩子；**A06 全部 6 RunID 标 BLOCKED**；解除条件=§2.c 路径 (i) 或 (ii) spike + 测试，且“另提裁决” | **权威裁决**（BLOCKED 的起点） |
| `docs/gem5-fi/lsu/mdspec/R4-8-A06-report.md:49` | “本报告的裁定”：load 侧任意另一合法值（含 shrink），A06-b store 内部位清零 | **agent 自裁**，随后被 R4-10 推翻其 shrink 载体前提 |
| `R4-8-A06-report.md:306` | 解除 BLOCKED 判据：C++ 构建通过 + shrink 实测 + byte-enable 复现 | agent 提案 |
| `docs/gem5-fi/lsu/mdspec/R4-10-GO-CORRECTION.md:5,13,24,60` | R4-8-GO **不是 GO**；NO-GO；RULING 6 = A06 load 侧裁决封锁 | **NO-GO 纠正** |
| `docs/gem5-fi/lsu/mdspec/R4-10-INTEGRATION-REPORT.md:31` | load SHRINK 结构性不可达成立；**需规格裁决**：A06-a load 侧仅保留 widen，或立项改完成语义 | 独立复核，仍待裁决 |
| `docs/gem5-fi/lsu/mdspec/runid_map.json:1036` 等 | `SPEC-SCOPE ruling item (MDSPEC §2.d ruling 2026-10-19, A06 load-side contract)` | 仍为 BLOCKED 理由 |
| `blocked_triage.md:11,28,60-65`；`ready_contract.md:36-41` | RULING 6；解除条件 §2.c spike + 测试 | 契约层仍 BLOCKED |
| `docs/gem5-fi/lsu/mdspec/R6-RULINGS-2026102{3,4}.md` | 裁决 D–I 均针对 T 单元/checker，**无 A06 裁决** | 无新增用户裁决 |

结论：**A06 至今没有用户/权威裁决把语义收紧为唯一**。R4-8 的自裁被 R4-10 否定；R4-10 明确“需规格裁决”。

### 3.3 当前实现包络（当前二进制含这些字符串）

`strings` 核验当前二进制含 `a06_size`、`a04_subst`、`a05_shift`、`load_size_block_shrink_unsafe`、`shift_mid`、`be_subst`、`CHAOS_L0_A06`；代码：

- `a06LoadSize`（`CHAOSAddrPath.cc:396-412`）：target 必须 ∈{1,2,4,8,16}；`NoTarget/Illegal/NoChange/Geometry/ShrinkUnsafe`；**shrink 一律 ShrinkUnsafe**（`agu_size_to_load < size`）。
- `a06_size` 分支（`:603-675`）：store 任意合法 target（` :671-672`）；load 仅 Success（widen）注入；load shrink 计数拒绝。
- A06-b（`:771-800`）：`be_mode=shift_mid` 只在 **store、size 未变、size≥2** 时把 `byte_enable[(size-1)/2]` 清 0；load 与 size 变化一律 `be_declined`；`observe` 只普查。
- 触发过滤：**没有**“子字节或向量”判定；A06 的 eligibility 只有 op-class 与 `a06_load_declined`（`:496-511`）。
- 注入日志：`fault_field`/`be_len`/`be_ones`/`be_subst`（`:815-845`）；PROP 的 `inj`/`addr_form` detail 含 `old_size/new_size`，但 `prop_evt` 列里没有 size/mask 字段（`CHAOSPropagation.cc:797-843`；旧 trial 的 `prop_trace` 可见 `old_size=8;new_size=2`）。

### 3.4 互斥语义（需人裁决的选项）

**A06-a load 侧**
- **A**：load 只做 widen，shrink 明确 out-of-scope（接受“规格预期截断”不在本平台建模）。→ 可在现有 carrier + 触发过滤补全后解锁。
- **B**：load shrink 属于模型，必须实现“定宽完成 + 截断”语义。→ 需要 §2.c 路径 (ii)：在 LSQRequest 构建层注入 size、完成路径按宽度分支（或修 packet size），属 LSQ/AGU 重设计，当前 BLOCKED。
- **C**：load 侧不做 size，只做 store size（与 A06 的 load 预期矛盾）。→ 需裁决明确缩小模型范围。

**A06-b**
- **A**：store 侧“全 1 内部位清零”是唯一可实现的“另一合法掩码”；load 只 observe（无架构消费者）。→ 可解锁（需补路由/证据字段）。
- **B**：允许任意非空真子集（连续/任意/多 bit）并规定确定性选择规则。→ 需扩展注入器与证据。
- **C**：尾部清零（≡ `addReq` 尾裁剪 ≡ size 变化）也算 byte-enable 故障。→ 与 A06-a 重叠，违反“一次只改一种状态”；需明确排除。
- **D**：load 侧掩码注入。→ 平台 load 路径无消费者，注入将不可观测（no-effect），不应作为模型。

**目标选择**
- **A**：每 RunID/campaign 固定 target（当前 store=2、load=8）并文档化。
- **B**：按 seed 确定性选取 `target ∈ {1,2,4,8,16}\{orig}`。
- **C**：每样本 RNG 抽样。
规格只写“另一合法值”，未规定；需要裁决以定义“3 seed 能否覆盖”和“子模型覆盖”的口径。

**触发口径**
- “子字节或向量访存”是否 = size<8 或 16B vector/LDP/STP？当前 A06 试跑注入的是 8B store（`stp` 拆分），**不满足**该触发；需要明确的 eligibility 规则。

### 3.5 只缺路由/hook/证据字段的部分（若裁决为 A06-a=A + A06-b=A）

- **campaign 路由**：`MODEL_FLAGS["A06"]`（`lsu_campaign.py:372-373`）只传 `--agu_size_to 2 --agu_size_to_load 8`，**没有 `--agu_be_mode`** ⇒ A06-b IMPLEMENTED_NOT_ROUTED；也没有子模型选择/分配规则。
- **触发过滤**：缺“子字节或向量访存”判定（需要 opcode/静态宽度/vector 标志；当前 PRE 钩子只有 addr/size/isLoad/flags）。
- **store no-op**：`size = agu_size_to` 不检查 `target==orig`（`:671-672`），size 等于原值时仍计数注入（F-049 的 A06 noop 类）。
- **store geometry**：load 有 `(addr&63)+target>64` 守卫（`:404-405`）；store 无跨 64B 行守卫。
- **证据字段**：`prop_evt` 无 size/mask 列；byte mask 位向量未记录；逐字节 store 日志、相邻字节 canary、load 扩展方式未落地；A06-a 的 `obs_pre_a06_load_shrink` 恒 0（`:657-663`），实际拒绝在 `_shrink_unsafe`。
- **L5 事件**：链止于 L3/L4 因为 `lsu_chain_check` 的 L5 只认“非生命周期 + detection_layer + outcome + corr”的显式检测事件（`tools/lsu_chain_check.py:46-115,439-535`）；`chain_end` 不占 L5。缺 CHAOSCommitTrace v2 / oracle-diff 事件（`runid_map.json` missing_hooks）。
- **F0 跨度**：A06-F0 用 `warmup=0, span=1000`（`lsu_campaign.py:1124-1150`），试跑 `eligible=1677/1637` ⇒ `EARLY_BIAS` 告警；需逐 workload census + `warmup=1, span=N`。
- **F2 结构零**：F2 平均间隔 100,000 eligible；W3/W5 eligible≈1.6-2.8k（`F-047`，`findings.md:63`）⇒ 即便裁决解锁 F0，F2 四格在本载体上仍结构性不可激活。

### 3.6 裁决结论

**保持 BLOCKED_RULING**。理由：语义不唯一（§3.4 的 load shrink 方向、掩码合法性、选择规则、触发口径）；权威裁决记录仍是 2026-10-19 的“BLOCKED + 另提裁决”，R4-8 自裁被 R4-10 否定，R6 用户裁决未覆盖 A06。仅当用户裁决明确选择（例如 A06-a=A、A06-b=A、固定 target、触发=size<8/vector）后，才转入“只缺路由/hook/证据字段”的实现清单（§3.5）。

### 3.7 旧 A06 trial 事实（非本轮证据）

- `A06-F0-W3`：`.../lsu-mdspec-20261019/runs/lsu/trial_r48_a06/A06-F0-W3/seed1`；旧二进制 compiled Oct 22 16:25（当前旧 worktree 文件已被 Oct 25 构建覆盖，**确切 SHA=UNKNOWN**）；workload `agu_addrmodes`，`a06_size --agu_size_to 2 --agu_size_to_load 8`，F0 span 1000 warmup 0，seed 1。
- 真实注入：`old_size=8 → new_size=2`，PC `0x402b98`（`ptmalloc_init.part.0` 的 `stp x0,x0,[x0,#16]`），addr `0x490190`，`be_mode=off`；oracle 输出仍 `728e604ffcec539d`（Masked）。
- 链：L0→L1→L2→L3(`sq_execute`)，L3→L4 missing；terminal `provable_to_L3_then_unknown`；无 L4/L5、无 admission/certification。
- `CHAOS_L0_A06: load_widen=0 load_nochange=833 load_geom=17 be_seen=1 be_subst=0` ⇒ 该 trial 没有 load 侧注入，也没有 A06-b。
- `A06-F0-W5`：同型，`sq_forward`，addr `0x4901a0`，链到 L3，Masked。
- R4-8 报告中的 `be_subst=1`/load widen spike 原始产物在 `/tmp/r4-7-a06`（已不存在），**仓库 runs 根内没有这些原始证据**；只能作为报告文字引用，不能作为本轮完成证据。

---

## 4. 旧证据只读核查（全部不得作为本轮完成证据）

### 4.1 A04-F0-W3 pilot（旧 worktree）

路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_pilot/A04-F0-W3/s1`

| 项 | 事实 | 证据 |
|---|---|---|
| RunID/seed | `A04-F0-W3`, `sample_run_id=pilot-s1`, `addrpath_rng_seed=20260826` | `run.out` command line |
| 二进制 | compiled Oct 20 17:26；文件现被 Oct 25 `e8052842…` 覆盖 ⇒ **run-time SHA=UNKNOWN**；不是当前 `3db54541…` | `run.out`; `sha256sum`; `stat` |
| workload/mode | `agu_addrmodes`, `a04_subst`, F0 span 1000 warmup 0 max_faults 1 | `run.out` |
| 真实注入 | `Tick 4770920`, `ldrb`, `old_addr=0x48e870 → new_addr=0x48ec40`（同页 0x48e000，16B 对齐，delta 976），`isLoad=1` | `addrpath_injections.log` |
| 触发合规 | PC `0x40bfec` = `__tunable_get_val` 的 `ldrb w0,[x0,#88]`；`array` 符号 = `0x493000` ⇒ **不在 oracle 对象内** | `objdump/nm` |
| 流完整性 | `gzip -t prop_evt.txt.gz` OK；`prop_trace.csv.gz` OK；33 events；`truncated=false` | `gzip -t`; `lsu_chain_check.py` |
| 链 | L0→L1→L2→L3→L4 proven；L4→L5 missing；terminal `provable_to_L4_then_unknown`（含 `taint_reg`、`errant_commit`、多个 `consumer`） | `lsu_chain_check.py` 输出 |
| L5/containment | 无显式 L5 检测事件；无 containment | 同上 |
| admission/certification | **无** `chain_report.json`、无 `cell_results.json`、无 manifest、无 admitted/certified 记录 | `find -printf` |
| oracle | `run.out` **没有** checksum 行（与 A05/A06 不同）；无 l5 verdict ⇒ oracle 结局不可从该 pilot 直接取得 | `run.out` |

### 4.2 A05-F0-W3 seed1（权威 runs 根，但旧二进制）

路径：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n6_A05-F0-W3_s1/A05-F0-W3/seed1`

| 项 | 事实 | 证据 |
|---|---|---|
| manifest | RunID `A05-F0-W3`, seed 1, `sample_run_id=s1`; binary `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`; `binary_source_head=f77bb0ab…`; `analysis_tool_head=e13ed86b…` | `manifest.json` |
| 真实 SHA | manifest 声明与实际旧 worktree 文件一致（`e805…`），但**不是当前 `3db54541…`** | `sha256sum` |
| workload/mode | `agu_addrmodes`, `a05_shift`, tier F0, warmup 0, span 1000, seed 1 | `run.out` |
| 真实注入 | `Tick 3128510`, `ldr`, `old_addr=0x4000d0 → new_addr=0x4000a1`；低字节 0xd0 左旋 1 = 0xa1 | `addrpath_injections.log` |
| 触发合规 | PC `0x400f18` = `__libc_setup_tls` 的 `ldr x2,[x0,#32]`（base+imm）⇒ **不是 shifted-register 寻址** | `objdump` |
| 流 | 11 events（12 行含表头）；`gzip -t` OK; `truncated=false`; exit 0; golden `728e604ffcec539d` | `prop_evt`; `gzip -t`; `run.out` |
| 链 | L0→L1→L2→L3→L4 proven（`taint_reg`），L4→L5 missing；`provable_to_L4_then_unknown` | `chain_report.json` |
| admission/certification | `admitted=false`, `certified=false`, `admission_gate_status=GATE-REFUSED`；violations: no_closed_chain_and_no_containment / ready_by_activated_only / ready_by_rc0 / ready_by_chain_end_only | `cell_results.json` |
| 其他 | `CHAOS_LSU_TRIGGER_ALARM EARLY_BIAS`（attempted=2800 eligible=2800 fired_at=412 span=1000）；L0 read-back `reads=0`；activation 由 trigger/inj 计数，非“下游消费”判定 | `run.out`; `cell_results.json` |

### 4.3 A06 trial（旧 worktree）

见 §3.7。两份 `A06-F0-W3/W5` 均有 `chain_report.json`/`chain_summary.md`（L3 terminal），无 `admitted/certified` 字段；`gzip -t` OK；`truncated=false`；oracle Masked；旧二进制 SHA=UNKNOWN（Oct 22 构建被 Oct 25 覆盖）。

### 4.4 旧 trial 汇总（`/home/sdc/gem5-fi-ding/artifacts/lsu-trial/cells`）

| cell | n_runs | attempted | activated | classes | stop |
|---|---|---|---|---|---|
| A04-F0-W3 | 5 | 13933 | 5 | Masked 5 | seed-cap(5) |
| A04-F0-W0 | 5 | 15957 | 5 | Masked 5 | seed-cap(5) |
| A04-F2-W3 | 5 | 13935 | 0 | all 0 | seed-cap(5) |
| A05-F0-W3 | 5 | 13933 | 5 | Masked 5 | seed-cap(5) |
| A05-F2-W3 | 5 | 13935 | 0 | all 0 | seed-cap(5) |
| A06-F0-W3 | 5 | 11145 | 5 | Masked 4 + Crash 1 | seed-cap(5) |
| A06-F0-W5 | 5 | 12845 | 5 | Masked 5 | seed-cap(5) |

这些是 `phase=trial` 的聚合，不是当前二进制/3-seed 证据；F2 的 0/5 与 `F-020/F-047` 的结构性零一致。

---

## 5. 建议分类（按 2026-10-28 A 计划固定类别）

| RunID | 建议类别 | 理由（事实） |
|---|---|---|
| A04-F0-W3 | **READY_FOR_CANARY（有条件）** | `a04_subst` 已路由、当前二进制含该模式；但触发“oracle 对象”过滤缺失、F0 span/warmup 非 census ⇒ canary 只能作诊断；3-seed 前必须补过滤/跨度（§1.6） |
| A04-F0-W0 | **READY_FOR_CANARY（有条件）** | 同上；W0 的 guard page 在 SE 下退化（mprotect 忽略），A04-b 不跨页 |
| A04-F2-W3 | **REVIEW_REQUIRED（结构性零）** | F2 间隔 100k ≫ W3 eligible≈2.8k；trial 0/5；见 `F-020/F-047` |
| A04-F2-W0 | **REVIEW_REQUIRED（结构性零）** | 同上；W0 eligible≈3.2k < F2 首发阈值 5×10^4 |
| A05-F0-W3 | **READY_FOR_CANARY（有条件；仅 a05_shift）** | 路由存在；旧 run 真实注入但触发寻址模式未实现；3 seed 不能覆盖 4 子模型 |
| A05-F2-W3 | **REVIEW_REQUIRED（结构性零）** | 同 A04-F2-W3 |
| A06-F0-W3 | **BLOCKED_RULING** | §3 语义不唯一 + 触发/证据字段缺失；旧 trial 注入 8B store，不满足“子字节/向量” |
| A06-F0-W5 | **BLOCKED_RULING** | 同左 |
| A06-F2-W3 | **BLOCKED_RULING + 结构性零** | 裁决 + F2 间隔 ≫ eligible（≈1.7k） |
| A06-F2-W5 | **BLOCKED_RULING + 结构性零** | 同上（≈1.6k） |
| A04-F6-W3/W0 | **POLICY_EXCLUDED_F6** | XLSX `R6证据状态=POLICY_EXCLUDED_F6`（rows 18-19）；`R6-FREQUENCY-POLICY.json` A04 representative group |
| A05-F6-W3 | **POLICY_EXCLUDED_F6** | XLSX row 22；policy representative |
| A06-F6-W3/W5 | **POLICY_EXCLUDED_F6** | XLSX rows 27-28；policy representative |

说明：A04/A05 的 `coverage_matrix PASS` 不改变上述建议；正式准入仍看 `PILOT_READY ∧ RUNNABLE`（`R6-STATUS-TABLE.md:31`）。

---

## 6. 缺失的 hook / 证据字段（汇总）

1. **触发资格（模型语义的一部分，当前完全缺失）**
   - A04：oracle 对象/页归属、对象边界、liveness（`CHAOSAddrPath.cc:496-511` 无 A04 过滤）。
   - A05：AArch64 寻址模式判定与操作数级 base/index/extend/shift/pre-post（final-EA 钩子无此信息）。
   - A06：子字节/向量访存判定（当前只按 load/store op-class）。
2. **子模型选择**
   - A04-a/b、A05-a/b/c/d、A06-a/b 均无子模型参数/seed 规则；3 seed 无法覆盖。
3. **A05 操作数钩子**：base/index/extend/shift/pre-post 与基址写回时点；当前 `a05_shift` 只是最终 EA 低字节旋转。
4. **A04 对象表**：W9 oracle object table（候选来源/范围/生命周期）；候选集合持久化；距离/同 line/对象归属字段。
5. **A06 载体**：load shrink 的路径 (ii)（LSQRequest 构建层 + 完成宽度分支）或等价 packet-size 修复；store geometry 守卫；store `target==orig` 的 NoChange 守卫。
6. **传播 L5**：显式检测/commit/oracle-diff 事件（`CHAOSCommitTrace` v2 等）；当前 `chain_end` 不占 L5（`lsu_chain_check.py:46-66`）。
7. **证据字段**：PROP 的 size/mask/byte-enable 位向量、逐字节 store 日志、相邻 canary、load 扩展方式、A05 寻址模式/基址写回、A04 替代距离/同 line/候选集合。
8. **F0 跨度**：A04/A05/A06 的逐 (model, workload) census + `warmup=1, span=N`（A07 已有范式，`lsu_campaign.py:1082-1104,1124-1150`）。
9. **F2 政策**：W3/W0/W5 的 eligible 长度不足以触发 100k 间隔；需要明确 POLICY_EXCLUDED / 长流改指 / 保留 BLOCKED。
10. **no-op 守卫**：A05 低字节为 0x00/0xFF 等旋转不变；A06 store target==orig；两者当前都会计入 injected/activated。

---

## 7. 拟修改文件清单（按单一 owner 串行）

### 7.1 共享实现（多模型交叉，必须单一 owner 串行）

| 文件 | 影响 | 说明 |
|---|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{cc,hh,py,SConscript}` | A01–A08（全部 AGU） | 子模型参数、触发过滤、no-op 守卫、A04 候选、A05/A06 语义 |
| `CHAOS/gem5/src/cpu/o3/lsq.cc` | 全部 LSU（A/L/S） | PRE 钩子调用、`registerInjection`、byte-enable 重建、`chaosA06BufBytes` |
| `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`, `dyn_inst.hh` | 全部 LSU + AGU | 仅当 A06 走 load shrink 路径 (ii) 时 |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{cc,hh}` | 全部单元 | L5/commit/oracle 事件、size/mask 字段、地址注册 |
| `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh` | 全部 LSU | F0/F2 语义、EARLY_BIAS、funnel |
| `configs/se/lsu_proxy.py` | 全部模型 | 新参数（子模型、触发、A06-b）、choices/校验 |
| `workloads/directed/agu_addrmodes.c`（+ binary） | A01–A08 W3 | 逐地址 oracle/对象表/asm 形态；任何改动都改 golden |
| `workloads/directed/mini_check.c`（+ binary） | A04 W0 | 对象表/guard 语义；SE 的 mprotect 退化需如实记录 |

### 7.2 工具/门禁（共享）

| 文件 | 影响 |
|---|---|
| `tools/lsu_campaign.py` | `MODEL_FLAGS`、`MODEL_BLOCKED`、`ADDRPATH_F0_SPAN`、F2 政策、A06-b 路由 |
| `tools/lsu_runid_map.py` | `SPEC_IMPL_LANDED`、status/blocker |
| `tools/lsu_chain_check.py`, `tools/lsu_prop_fields.py` | L5 kind/字段（全单元共享） |
| `tools/lsu_admission.py`, `tools/lsu_ready_contract.py`, `tools/lsu_freq_policy.py` | 准入/频率政策（全单元共享） |
| `tests/test_lsu_a06_loadsize.py`, `tests/test_lsu_a06_ruling.py`, `tests/test_lsu_hook_addrpath*.py`, `tests/test_lsu_chain_check.py` | 契约回归 |

### 7.3 文档/状态（主 agent）

`docs/gem5-fi/lsu/mdspec/runid_map.json`、`coverage_matrix.md`、`ready_contract.{md,json}`、`R6-STATUS-TABLE.{md,json}`、`blocked_triage.md`、`docs/superpowers/plans/2026-10-28-r6-a-unit.md`、XLSX 回填。

**所有权提示**：`CHAOSAddrPath.*` 被 A01–A08 共用；`lsu_campaign.py` / `CHAOSPropagation.*` / `chaos_lsu_trigger.hh` / `lsu_chain_check.py` 被 A + T + L/S/C 全部单元共用。任何改动必须由单一 owner 串行完成，A/B/C 三条 lane 不得并行改同一文件。

---

## 8. UNKNOWN / 限制

- A04/A06 旧运行的**精确二进制 SHA = UNKNOWN**：旧 worktree 的 `gem5.opt` 已被 Oct 25 的 `e8052842…` 覆盖，`run.out` 只留 compiled 时间（A04: Oct 20 17:26；A06: Oct 22 16:25），无 manifest。
- A04 pilot 的 `run.out` 无 checksum 行；无 l5 verdict/chain_report ⇒ 该 pilot 的 oracle 结局不可直接确认（本报告不推断为 Masked/SDC）。
- R4-8 报告的 `be_subst=1` 与 load widen spike 原始文件在 `/tmp/r4-7-a06`（已不存在），仓库无原始证据；本报告只把它当 agent 文字记录。
- 未运行任何 gem5/campaign/pytest；未用旧证据冒充本轮完成证据。
- 负载二进制与源码一致性：`agu_addrmodes`/`mini_check` 为 static aarch64；`nm`/`objdump` 用于确认符号与指令，未做再编译。

---

## 9. 关键命令与真实输出（摘）

```text
$ sha256sum CHAOS/gem5/build/ARM/gem5.opt
3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2

$ sha256sum /home/sdc/gem5-fi-ding/.claude/worktrees/r6-fiding-merge-20261026/CHAOS/gem5/build/ARM/gem5.opt
e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959

$ nm -n workloads/directed/agu_addrmodes | grep -E ' array$| output$| main$'
00000000004004f0 T main
0000000000493000 b array
0000000000493200 b output

$ nm -n workloads/directed/mini_check | grep -E ' data$| main$'
00000000004004f0 T main
00000000004919a0 b data
0000000000496e80 b data

$ objdump -d workloads/directed/agu_addrmodes --disassemble=main | grep -E 'sxtw|uxtw'
(no output; 164-line main disassembly has no sxtw/uxtw)

$ objdump -d workloads/directed/agu_addrmodes --start-address=0x400f10 --stop-address=0x400f20
  400f18:  f9401002  ldr x2, [x0, #32]      ; __libc_setup_tls (A05 run injected here)

$ objdump -d workloads/directed/agu_addrmodes --start-address=0x40bfe8 --stop-address=0x40bff0
  40bfec:  39416000  ldrb w0, [x0, #88]    ; __tunable_get_val (A04 pilot injected here)

$ objdump -d workloads/directed/agu_addrmodes --start-address=0x402b90 --stop-address=0x402ba0
  402b98:  a9010000  stp x0, x0, [x0, #16] ; ptmalloc_init (A06 trial injected here)
```

```text
$ gzip -t .../A04-F0-W3/s1/prop_evt.txt.gz && echo EVT_OK
EVT_OK
$ python3 tools/lsu_chain_check.py .../A04-F0-W3/s1/prop_evt.txt.gz --run-id A04-F0-W3
"terminal": "provable_to_L4_then_unknown", "provable_to": "L4",
"truncated_stream": false, "total_events": 33

$ gzip -t .../r6_n6_A05-F0-W3_s1/A05-F0-W3/seed1/prop_evt.txt.gz && echo GZIP_EVT_OK
GZIP_EVT_OK
$ gzip -t .../r6_n6_A05-F0-W3_s1/A05-F0-W3/seed1/prop_trace.csv.gz && echo GZIP_TRACE_OK
GZIP_TRACE_OK
```

A05 `cell_results.json`：`admitted=false`, `certified=false`, `admission_gate_status="GATE-REFUSED"`, terminal `provable_to_L4_then_unknown`；A06 trial：`terminal=provable_to_L3_then_unknown`。

---

## 10. 结论摘要

1. **A04**：`a04_subst` 是同页 16B 随机代理；A04-a 未实现，A04-b 可达但无对象/liveness/触发过滤；旧 pilot 的 PC 属 glibc `__tunable_get_val`、注入地址 0x48e870 在 glibc 数据段，不是 oracle 数组（0x493000）⇒ 旧样本按规格触发列应为 Injected-not-activated。W3/W0 都是末校验和 oracle；W0 guard page 在 SE 下退化且 A04-b 不跨页。
2. **A05**：A05-a/b/d = NOT_IMPLEMENTED（final-EA 钩子无法表达，需操作数级钩子）；A05-c = 近似实现且已路由（低字节旋转），但触发寻址模式未实现、旧注入落在 base+imm libc 指令；3 seed 不能覆盖 4 子模型；辅助 canary 只能对 c 做有界验证。
3. **A06**：语义不唯一（load shrink 方向、byte-enable 合法掩码、目标选择、触发口径），权威状态仍是 BLOCKED_RULING；R4-8 自裁被 R4-10 否定；当前实现 store size 任意 + load 仅 widen + store 内部位掩码 + load observe，A06-b 未路由；旧 trial 注入 8B store，不满足“子字节/向量”。**保持 BLOCKED_RULING**。
4. **旧证据**：三份均为真实注入、gzip 完整、非截断；链分别到 L4（A05/A04 pilot）或 L3（A06）；均无 L5/containment/admission/certification；均非当前二进制，不能作为本轮完成证据。
5. **F2 结构零**：A04/A05/A06 的 F2-W3/W0/W5 在其载体上 eligible ≪ 100k，结构性不可激活（F-020/F-047），应 REVIEW_REQUIRED/政策处理，不应烧 3 seed 伪装完成。
