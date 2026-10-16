# ARMv8-ISA × O3 微架构链路图谱（o3-atlas）设计文档

- 日期：2026-10-16
- 状态：设计已与用户逐节确认（裁决记录见 §3）
- 下游：`docs/superpowers/plans/` 实现计划（writing-plans 产物）
- 实施分支：`docs/o3-atlas`（从 fi-ding 切出；纯文档 + tools 变更，不触碰任何 C++）

## 1. 背景与目标

用户需求：对 `docs/cpu/armv8-isa/` 中每条指令做深刻理解；使用 LSP 对 gem5 源码做深刻理解；构建每条指令走过的 ARM64 CPU 微架构链路；绘制整个 CPU 微架构的链路图。

**交付产物**：

1. 每指令一页「O3 微架构链路」文档，与原 ISA 语料 1:1 镜像互链（372/372 指令页；另重建 15 个分类索引——全量 387 个文档均得到交代）；
2. 整个 O3 CPU 微架构总链路图（mermaid + graphviz 双格式，附 SVG）；
3. 指令 × CHAOS 注入器命中矩阵（可反查「哪些指令能被某注入器命中」）；
4. 支撑上述产物的机器可校验数据层（YAML）+ 生成器 + 校验器 + clangd 查询工具（沉淀到 `tools/o3_atlas/`）。

**用途**：服务 FI 研究——每条指令流经哪些微架构单元，直接映射「哪些 CHAOS 注入器能命中它」。

## 2. 已核实的现状事实（2026-10-16 本机实测）

| 事实 | 数值/位置 |
|---|---|
| 指令语料 | `docs/cpu/armv8-isa/` 共 387 个 md = 15 个分类索引页 + 372 个指令页（15/372 的精确划分以 Phase 0 分账表固化，任何归属歧义显式列出） |
| 语料内容 | ARM ARM 的 ISA 级抽取（编码/伪代码），无任何微架构内容；索引页为抽取产物、内容粗糙 |
| AArch64 解码器 | `CHAOS/gem5/src/arch/arm/isa/decoder/aarch64.isa`（DSL，不入编译数据库） |
| 指令实现 | `CHAOS/gem5/src/arch/arm/isa/insts/`（29 个 .isa 文件：data64/branch64/ldr64/str64/macromem/pauth/sve/neon/crypto/…） |
| 解码展开产物 | `build/ARM/arch/arm/generated/`：`decoder.cc/.hh` + `inst-constrs-{1,2,3}.cc` + `decode-method.cc.inc` + `generic_cpu_exec_*.cc` 等（StaticInst 类与执行方法所在） |
| O3 CPU 源码 | `CHAOS/gem5/src/cpu/o3/` 81 个文件（fetch/decode/rename/iew/commit/lsq/iq/rob + 全套 CHAOS 注入器） |
| clangd | `/home/sdc/.local/bin/clangd` 已安装 |
| 编译数据库 | repo 根 `build/ARM/compile_commands.json`，共 30,963 条目，其中 90 条为 generated（含 decoder.cc 与 inst-constrs-*.cc；其 file 字段路径基准与落盘路径的差异在 Phase 0 实测敲定） |
| 真机构建 | repo 根 `build/ARM/gem5.opt`（仓库铁律：不引用 CHAOS/gem5/build 下的陈旧副本） |

## 3. 需求裁决记录（用户已确认）

| # | 问题 | 裁决 |
|---|---|---|
| 1 | 指令覆盖范围 | **全量 387、两层深度**：gem5 已实现 → 完整链路页；未实现 → 如实记「解码→Unknown→fault」短链路（表格化，彼此雷同） |
| 2 | 链路深度 | **gem5 O3CPU 为基准**（B0 = O3_ARM_v7a_3），全流水线链路 + 解码身份 + IQ/LSQ/FU 归属 + 代码锚点 + **CHAOS 注入器命中点** |
| 3 | 实现方案 | **方案 A：图谱即数据**——YAML 单一数据源 + 生成器 + 校验器 |

对话中已声明且用户未反对的假设：鲲鹏920 真硬件文档（`docs/cpu/kunpeng920_microarchitecture.md`）仅作对照参考，不是链路基准；新内容中文为主、术语/代码保留英文。

## 4. 架构

```
docs/cpu/o3-atlas/          # 新图谱子系统（原 armv8-isa/ 语料保持只读、零改动）
  README.md                 # 入口 + 统计 + 使用说明
  data/
    families.yaml           # ~25 个格式家族的共享链路骨架
    instructions/*.yaml     # 每分类一个文件，每指令一条记录
  pages/                    # 【生成物，提交入库】每指令一页，文件名与 armv8-isa/ 1:1 镜像
  index/                    # 【生成物】分类索引（重建的干净版）
  diagrams/                 # 【生成物】o3-pipeline.{mmd,dot,svg} + 指令×注入器矩阵
tools/o3_atlas/
  lsp_query.py              # clangd JSON-RPC 客户端（def/ref/hover）
  generate.py               # 数据 → 页面/索引/图（确定性输出）
  validate.py               # 覆盖 + schema + 锚点验真 + 生成确定性
```

**数据流**：分析期（人/agent 用 lsp_query.py 精读源码）→ 填 `data/`（YAML，单一事实源）→ `generate.py` 渲染 pages/index/diagrams → `validate.py` 全量校验。

**核心原则**：

- 原语料零改动；atlas 页面与其按文件名 1:1 互链；
- 覆盖判据 = `pages/` 文件名集合与 372 个指令页文件名集合相等；`index/` 另生成 15 个分类索引页；
- 生成物确定性：连跑两次 `generate.py`，`git diff` 为空；
- 页面 mini 图与总图出自同一生成器，天然零漂移。

## 5. 数据模型

### 5.1 指令记录（`data/instructions/<category>.yaml`，每指令一条）

```yaml
- doc: Arithmetic-ADD_immediate.md      # ↔ armv8-isa 原文，1:1
  mnemonic: ADD (immediate)
  tier: implemented                      # 见 5.3
  gem5:
    decode_mnemonic: add_imm             # decoder 格式名
    static_inst: AddImm64                # 展开产物类名
    anchors:
      decoder: CHAOS/gem5/src/arch/arm/isa/decoder/aarch64.isa:1187
  family: dataproc-immediate             # → families.yaml 骨架引用
  overrides: { fu: IntALU, writes_flags: false }   # 对家族骨架的差量
  injectors: [CHAOSDecode, CHAOSRenameMap, CHAOSFreeList, CHAOSPhysReg, CHAOSIQ, CHAOSROB, CHAOSReg, CHAOSProbe]
  evidence:                              # 供复核的证据锚点
    - claim: "rename 阶段读取源操作数映射"
      anchor: CHAOS/gem5/src/cpu/o3/rename.cc:312
```

> 注：上例锚点行号为格式示意；正式数据中每个锚点必须来自 LSP/源码实读并通过 validate.py 验真。

### 5.2 格式家族（`families.yaml`）

- **标准节点词表**（全体家族共用，节点定义一次、锚点一次审定）：`FETCH / DECODE / RENAME / ISSUE / EXECUTE / MEMORY / WRITEBACK / COMMIT`，另有分支侧线（`BPU / FTQ / RAS / 重定向`）与系统/异常侧线；每节点附 gem5 代码锚点（file:line）。
- 家族字段：`summary`、`pipeline`（引用标准节点序列 + 家族特有注记）、`queue`（IQ/LSQ）、`fu`、`default_injectors`。
- 典型家族：dataproc-immediate、dataproc-shifted-register、load/store-各寻址族、atomic/LSE、exclusive、branch-cond/branch-register/branch-immediate、compare、cond-select、bitfield、pc-relative、system/barrier、crypto-crc 等（最终清单 Phase 0/1 敲定）。

### 5.3 tier 定义（硬字段，每条必填）

| tier | 定义 | 证据要求 |
|---|---|---|
| implemented | gem5 解码并执行 | decoder 锚点 + 生成类锚点 |
| partial | 部分变体实现 | 已实现/未实现变体分列，各附锚点 |
| unimplemented | 解码为 Unknown → IllegalInstFault | decoder 无匹配 + 生成类清单无此类（静态证据） |
| fs-only | 需全系统模式方有真实行为（如 TLBI/AT） | SE 行为与 FS 行为分述 |
| macro-op | gem5 宏展开（macromem 等） | 展开前后指令链路都写 |

### 5.4 注入器命中模型

- 默认命中集（所有指令都过）：`CHAOSDecode / CHAOSRenameMap / CHAOSFreeList / CHAOSPhysReg / CHAOSROB / CHAOSReg / CHAOSProbe`（+ IQ 或 LSQ 二选一）——**该默认集在 Phase 1 用 LSP 逐注入器核实挂载点后固化进 families.yaml（各附锚点），不许想当然**；
- 特征补集：访存类补 `CHAOSLSQFwd / CHAOSL1DForward / CHAOSAddrPath`（+ 访存侧 CHAOSMem/CHAOSCache 标注），分支类补 `CHAOSBPU`（RET/BLRAA 等补 `CHAOSRAS`），浮点类补 `CHAOSFPU`；
- 聚合产物：指令×注入器命中矩阵（生成物）。

### 5.5 诚实约定（对齐仓库铁律）

- 锚点禁止手拍，必须来自 LSP/源码实读，validate.py 逐一验真（文件存在 + 行号 ≤ 总行数 + 行内容非空）；
- 未实现报 `unimplemented` 并附证据，绝不静默跳过或装零；
- 372 条的 implemented/unimplemented 精确分账表是 Phase 0 硬交付，不预造数字；
- 锚点失效 = 校验红灯显式暴露，不是静默烂掉。

## 6. 生成产物

### 6.1 每指令页面（`pages/<原名>.md`，与 armv8-isa 文件名 1:1）

implemented 深模板：页首元信息行（链接原语料、tier、family）→ 一图链路（内嵌 mermaid：总图骨架 + 本指令路径高亮）→ 分站链路说明（每站 1-3 行 + 代码锚点）→ 解码身份 → 队列与执行单元 → CHAOS 注入器命中（清单 + 每项一句话理由）→ 证据锚点清单。

unimplemented 短模板：短链路（fetch→decode→Unknown→IllegalInstFault）+ 证据；并汇入 coverage 索引表。

### 6.2 分类索引（`index/<category>.md`，生成）

重建干净版：本分类全部指令 + tier 徽标 + 链接 + 统计行。原语料 15 个索引页不动。

### 6.3 总图（`diagrams/o3-pipeline.{mmd,dot,svg}`，生成）

骨架 = O3 全流水线（fetch / decode / rename / IEW(issue+exec) / writeback / commit）+ 分支侧线（BPU/FTQ/RAS/重定向）+ 访存侧线（LQ/SQ→L1D→TLB）+ 提交侧（ROB / commit-map）。CHAOS 注入器以独立标记叠加挂载点。支持按 family 参数化高亮生成子图（嵌入每指令页的 mini 图即此产物）。

### 6.4 指令×注入器命中矩阵（`diagrams/injector-matrix.md`，生成）

## 7. LSP 工具（`tools/o3_atlas/lsp_query.py`）

- clangd JSON-RPC over stdio；CLI：`def|ref|hover <file>:<line>:<col>`，输出 JSON；
- **冒烟门（Phase 0 验收项）**：从 `src/cpu/o3` 实际选定至少 3 个已知符号（O3 CPU 类或其成员函数等），经 LSP 定位到预期源文件与行号，实测输出留档；
- 集成细节（compile_commands 路径基准、首次后台索引时长）Phase 0 实测敲定；冒烟不过就修到过为止，**不许静默降级成 grep；任何降级必须显式记录在案**。

## 8. 验证与实证（每 patch 必过，全部真命令）

1. `validate.py` 全绿：覆盖 372/372 指令页 + 15 分类索引、schema 校验、锚点验真、生成确定性（重跑 diff 为空）；
2. **真机抽样实证**：每分类 ≥1 条 implemented 指令，跑 `build/ARM/gem5.opt --debug-flags=Decode,O3CPU ...`（SE 负载），核对静态解码名与 IQ/LSQ 归属断言；该分类无 implemented 指令时，以 1 条 unimplemented 断言的静态证据复核代替；**≤4 并发**（仓库硬上限）；
3. tier 抽验：unimplemented 以 decoder + 生成代码静态证据为准；争议指令写最小 .s 用例实测；
4. 本工程纯文档 + tools，不改 C++、不重建 gem5；工具变更需自测通过；
5. 提交纪律：一 patch 一单元、显式路径 staging（禁 `git add -A`）、非 main 分支、commit message 引用真实命令输出、验证不过不提交。

## 9. 分阶段交付骨架（writing-plans 的输入）

- **Phase 0 基建**：lsp_query.py 冒烟 + schema 定稿 + families.yaml 初版 + generate/validate 骨架 + **372 条精确分账表**（硬交付）；
- **Phase 1 竖切**：Arithmetic 分类端到端 + 1 条真机 trace 实证，锁定页面/图模板与默认注入器集；
- **Phase 2+ 按分类批量**：Load-Store（最重）先行 → Branch → System/Barrier → 其余；每分类一个 patch（数据 + 页 + 校验绿 + 实证输出引用 → commit → push）；
- **收官**：总图 + 注入器矩阵 + README 统计；可选增值：11 个 FI 负载 objdump 扫描 → `workload_hits` 字段（哪些负载用到该指令）。

每个 patch 独立可交付：任何时点停下，图谱都是完整、自洽、校验绿的状态。

## 10. 风险与对策

| 风险 | 对策 |
|---|---|
| 372 条长跑规模 | 格式家族差量复用 + 分类分批 + 每 patch 独立可交付 |
| gem5 源码演进致锚点失效 | validate.py 随时可重验；红灯显式 |
| clangd 集成不顺（路径基准/索引时长） | Phase 0 冒烟门，不过不往后走；降级须显式记录 |
| 真机抽样并发超限 | 抽样批控 ≤4 gem5 进程 |
| 多会话并发操作仓库 | 专用分支 docs/o3-atlas + 显式路径 staging + 及时 push |

## 11. 非目标（明确不做）

- 不修改 `docs/cpu/armv8-isa/` 原语料（含其 15 个粗糙索引页）；
- 不修改 gem5 C++、不触发重建；
- 不做 MinorCPU/TimingSimpleCPU 逐条深挖（基准仅 O3）；
- 不做时延/吞吐等性能建模；
- 语料之外的指令（SVE/NEON 全集等）不入范围；
- 与 OoO FI V2.0 实验轨道的实验数字无关，永不混数。
