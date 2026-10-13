# SVE/SME 全规格 FI 评估——PR #237 种子随机化的 gem5 故障注入验证 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 CHAOS/gem5 SE-O3 上以故障注入验证 sdcshield PR #237 的 4 个 SVE/SME 测试（`fpu_special_values_sve`、`sve512_stencil_axis_arm`、`sme_fmopa_stress_arm`、`sme_za_tileview_arm`）的 SDC 检出效果与种子随机化（fixed→random）的多样性收益；并把 SVE/SME 全向量长度规格（128/256/512/1024-bit）参数化支持起来。

**Architecture:** 复用 2026-09-22-sdcshield-fi-eval.md 的**双通道内核协议**（通道 A = 原测试校验语义 → Detected；通道 B = 独立 FNV checksum → Escape/Masked 判别），新增 fixed/random 双输入模式（argv 控制，对应 PR #237 前后版本）与 `--sve_vl/--sme_vl` 全规格配置。注入主力 CHAOSPhysReg（`--phys_reg_class=vector` + `--vec_lane_width`）与 CHAOSFPU（sign/exp/mantissa 位段）。

**Tech Stack:** 本仓 gem5.opt（已就位：拷贝自 gem5-fi-fuzz 2026-09-08 构建，19 注入器类，python 注册完好——探针实证）；静态 aarch64 C 内核（clang 17 `-march=armv9-a+sve+sme`，SME 汇编须 clang）；tools/{runner,campaign,classify}.py。

## 已实证事实（计划依据，全部本会话真机输出）

- **F0 二进制**：本仓原 gem5.opt（8/29）python objects 注册表损坏（`ImportError: CHAOSExMon`）而 C++ 符号在——已拷贝 fuzz 仓二进制（19 类）恢复，探针跑通。后台 scons 全量重建进行中（产物落仓库根 `build/ARM/`，完成后须 cp 回 `CHAOS/gem5/build/ARM/` 核对择优——本计划用 fuzz 二进制推进，不阻塞）。
- **F1 SVE/SME 可执行**：SVE（默认 VL=128bit=1 quadword）与 SME（smstart/rdsvl/smstop，SVL=128）在 O3 SE 上全部执行成功（探针 `/tmp/sve_sme_probe`）。
- **F2 SE VL 入口**：`ArmISA.sve_vl_se`/`sme_vl_se`（`ArmISA.py:192-197`，quadword 单位；`isa.cc:133` SE 分支读取）——SimpleBoard generic System 正走此路径。全规格 = 1/2/4/8（128/256/512/1024 bit）。
- **F3 gem5 SVE 保真度缺陷（已登记，须规避）**：`mov z.d, #imm`（向量立即数 MOV）**不生效**（st1d 读回全 0）；fmla/fmul/fadd/ld1d/st1d/ptrue 正确。kernel 代码禁用该指令（intrinsic `svdup_*` 生成 DUP 编码，不受影响）。
- **F4 gem5 SME FMOPA 双舍入**：`sme.isa` 的 FMOPA = `fplibMul`+`fplibAdd`（两次舍入），真硬件为单舍入 FMA → fmopa kernel 的跨环境 golden 采用**仿真内基线**（无注入 hash），通道 A 自校验在仿真内闭合；该语义偏差如实记录。
- **F5 环境**：系统 protobuf 25.1 + hdf5 已装（dnf）；scons 须 `source ~/gem5-deps/env.sh`。
- **F6 注入接口**：`--phys_reg_class=vector --vec_lane_width {8,16,32,64}`（CHAOSPhysReg，buffer 按 vecRegBytes() 适配实际 VL）；`--fpu_bit_segment {sign,exp,mantissa}`（CHAOSFPU）。

## Global Constraints

- **一补丁一单元**：每 Task = 一个 commit；完成一个（验证→commit→push）再下一个。
- **三步真机自验证**：零新警告 + 功能验证引用真实 gem5 输出 + 回归锚（`reg_chain` golden `f247ef3fe6f02cfd` 或既有内核 golden 不变）。
- **分支**：主仓 `feat/sve-sme-fi`（从 `fi-wx-verify-sdcshield` 切出），绝不 push main；commit 不以 Co-Authored-By 结尾；gem5 子模块只读。
- **诚实边界**：kernel 是测试的提取式等价物（fracture/fork 框架语义不在 SE 范围——种子随机化的**输入多样性效果**由 fixed/random 模式对比承载）；gem5 语义偏差（F3/F4）全部记录在案。
- **kernel 输出协议**（双通道，与 2026-09-22 计划一致）：`SDCSHIELD_FAILS=<uint>`（通道 A）+ 独立行 `<16-hex>` FNV checksum（通道 B）；exit = `g_fails ? 1 : 0`。argv：`[fixed|random] [seed]`（random 默认 seed=1）。
- **campaign 与构建绝不并行**（后台 scons 完成前不跑 formal campaign；pilot/开发跑允许）。

## 预注册判据（J1'–J3'，裁决时不得改）

- **J1'（工具有效性）**：4 个 kernel 无注入对照（每模式 N=5）100% 全绿——`SDCSHIELD_FAILS=0` 且 checksum==golden 且 exit 0；random 模式不同 seed 的 checksum **必须互不相同**（随机化生效的必要条件）。
- **J2'（检出能力）**：4 kernel × {PhysReg-vector, FPU} 注入 pilot（n=10/格）至少一个格 `Detected > 0`（fpu_special 类预期 `P_detect → 1.0`——逐 lane byte-exact）；全部为 0 则如实报告为 SE 到达性盲区并归因。
- **J3'（多样性收益，核心交付）**：存在注入配置 C 使 fixed 模式 Masked/Escape 而 random（≥5 seed 并集）下 Detected——即 random 累计检出集合 ⊋ fixed；若不成立，如实报告（该注入空间内输入模式不影响检出面）。

---

### Task 0: 分支与二进制验证脚本

**Files:** Create `tools/verify_gem5_injectors.sh`（19 类核对 + reg_chain 锚 + SVE/SME 探针锚）

- [ ] Step 1: `git checkout -b feat/sve-sme-fi`（主仓，基于 fi-wx-verify-sdcshield）
- [ ] Step 2: 写脚本：`nm -C` 核对 19 类（fuzz 二进制实际集合：Reg/PhysReg/Mem/Cache/LSQFwd/AddrPath/PTW/RenameMap/FreeList/ROB/IQ/RAS/Exec/FPU/L1DForward/BPU/ExMon/ArmTLB/ArmSysReg）；reg_chain golden 锚；`sve_sme_probe` 三行输出锚（SVE VL/SME SVL 非零 + fmula 数值）
- [ ] Step 3: 跑通引用真实输出 → commit → push

### Task 1: arm_chaos.py 全规格 `--sve_vl/--sme_vl` 参数

**Files:** Modify `configs/se/arm_chaos.py`（新增 2 个 CLI 参数 + 应用到 `cpu0.isa[0]`）

- [ ] Step 1: 参数定义 `--sve_vl`/`--sme_vl`（choices=[1,2,4,8]，default=1，quadword 单位）；O3/Timing/Minor 均应用 `for isa in cpu0.isa: isa.sve_vl_se = args.sve_vl`（Atomic 无 isa 对象——实测确定）
- [ ] Step 2: 验证：`--sve_vl 4` 下探针输出 `SVE VL = 64 bytes (512 bits)`；`--sme_vl 4` 下 `SME SVL = 64 bytes`；四个规格各跑一遍（1/2/4/8 → 16/32/64/128 bytes）——引用全部真实输出
- [ ] Step 3: commit → push

### Task 2: SVE/SME 语义保真度探针套件（登记 F3/F4）

**Files:** Create `workloads/sdcshield/sve_sme_semantics.c` + `workloads/sdcshield/Makefile`

- [ ] Step 1: 探针覆盖：dup 立即数（预期正常）、`mov z,#imm`（预期全 0，F3 登记规避）、fmla merging 谓词语义、ld1d/st1d 全 lane（VL=512）、SME ZA readout（`smstart za` + ZERO/ZA store 指令 + `smstop`）、FMOPA 数值 vs fmaf（双舍入差异 F4 的定量记录）
- [ ] Step 2: `--sve_vl 4 --sme_vl 4` 下跑通，输出每项 pass/deviation → commit → push（findings 记录 gem5 偏差清单）

### Task 3: kernel `fpu_special_values_sve_dual`（VL 自适应）

**Files:** Create `workloads/sdcshield/fpu_special_sve_dual.c`；Modify `tools/runner.py`（GOLDEN_IDS 登记）

- [ ] Step 1: 移植 `sdcshield/tests/cpu/sve/fma2/fpu_special_values_sve.cpp` 检测语义：12 固定 IEEE 特殊值 + 4 随机有限值（random 模式，xorshift32 seed 可复现；fixed 模式 = PR #237 前的纯 12 值表）；svmla 逐 lane vs fmaf（NaN 类判断 + 非 NaN byte-exact）；g_fails 计数 + FNV checksum。指令用 intrinsics（`svmla_f32_x` 等——编译器生成 DUP 非 MOV-imm，规避 F3）
- [ ] Step 2: 无注入对照：fixed/random×5seed 全绿 + random checksum 互异（J1' 前半）；`--sve_vl {1,2,4,8}` 四规格跑通（全规格覆盖）
- [ ] Step 3: commit → push

### Task 4: kernel `sve512_stencil_axis_dual`

**Files:** Create `workloads/sdcshield/stencil_axis_dual.c`

- [ ] Step 1: 移植 PR #237 版 stencil：随机 src（random 模式）+ 标量参考（1/8 网格精确性论证同 PR）；fixed 模式 = 原 `{1..16}` src + 解析式 `1.5*ITERS*(j+1)`；iterations 降为仿真可承受（先标定单跑 ≤120s）；通道 A `result[j] != expected[j]` 计 fail + 通道 B checksum
- [ ] Step 2: `--sve_vl 4` 下无注入对照全绿（两种模式）；`--sve_vl {1,2,8}` 记录 skip/适配行为（stencil 语义为 512 设计——其他规格如实记录适配或 skip）
- [ ] Step 3: commit → push

### Task 5: kernel `sme_fmopa_stress_dual`（SVL=512）

**Files:** Create `workloads/sdcshield/sme_fmopa_dual.c`（clang 编译，SME asm）

- [ ] Step 1: SMSTART/FMOPA asm 内核（移植 sdcshield SME kernel）+ ZA readout；操作数 random 模式（`|a|,|b|<0.5625` xorshift 生成）/fixed 模式（原公式）；**通道 A = 仿真内自参考**（同一输入的软件 fmaf 链仅作记录性对照——因 F4 双舍入偏差，检出判定用通道 B checksum vs 基线）；golden = 无注入基线 hash（两模式分别标定）
- [ ] Step 2: `--sme_vl 4` 无注入对照全绿 + random seed 互异；`--sme_vl {1,2,8}` 规格记录
- [ ] Step 3: commit → push

### Task 6: kernel `sme_za_tileview_dual`（SVL=512）

**Files:** Create `workloads/sdcshield/sme_za_tileview_dual.c`

- [ ] Step 1: ZA tile-view 排列内核（transpose/slice-shift/rot 的 readout memcmp vs 排列 golden——纯数据排列无舍入问题，通道 A 可用排列参考）；random/fixed 输入同 Task5 模式
- [ ] Step 2: 无注入对照全绿 + 规格记录 → commit → push

### Task 7: FI pilot（J2'）

- [ ] Step 1: 每内核标定注入触发窗口（first_clock 置于内核计算段）；
- [ ] Step 2: 4 kernel × {PhysReg-vector(vec_lane_width=64), FPU(mantissa)} × {fixed, random} × n=10 → 分类（Detected/Escape/Masked/Hang/Inactive）——runner/campaign 工具链；引用汇总表
- [ ] Step 3: commit（manifests + 结果 JSON）→ push

### Task 8: 多样性对比 campaign（J3'，核心交付）

- [ ] Step 1: 注入配置网格（从 pilot 中选 Detected 或 Masked 有信号的格）× fixed × random-5seed（n=20/格，Wilson CI）
- [ ] Step 2: 分析：random 累计检出集合 vs fixed；输出对比表 + 判据 J3' 裁决
- [ ] Step 3: commit → push

### Task 9: 收口

- [ ] findings.md 增补 SVE/SME 章节（F3/F4 偏差清单、J1'-J3' 裁决、诚实边界）；AGENT_TASKS.md 登记任务行
- [ ] commit → push；向用户汇报（含 sdcshield PR #237 的回写建议）

## Self-Review

- 用户三项要求全覆盖：全规格支持（Task 1 + 各 kernel 规格记录）、4 测试 FI 验证（Task 3-8）、随机化效果（fixed/random 对比 = J3'）✓
- 已实证事实全部来自本会话真实输出；gem5 偏差（F3/F4）有规避与登记 ✓
- 每 Task 有具体验证命令与判据 ✓
