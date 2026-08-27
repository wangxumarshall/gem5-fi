# ARM64 SDC 故障注入研究 — 工作进展汇报

> 本文件如实记录基于 `docs/arm64-fi-plan-based-on-CHAOS.md` 的实现进展。
> 所有"已完成"项均有 commit message 引用的真机 gem5 输出佐证，非预测。
> 分支 `fi`（HEAD `5f2aa5f`，经 PR #9 合入 `arm64-sdc-base`）。

---

## 一、本次交付的真实范围

基于 `docs/arm64-fi-plan-based-on-CHAOS.md`，在 `fi` 分支上交付了 **19 个补丁**，每个都经真机 gem5 输出验证，覆盖计划的 **Phase 0（版本冻结 + 七个正确性闸门 G0–G7）+ manifest runner + Phase 1 的 P0 试点结果**。

### 构建基线
- gem5 v25.1.0.1（commit `62c7bf28`）原样引入到 `CHAOS/gem5/`。
- 在**原生 aarch64**（openEuler，gcc 12.3.1，无需交叉编译器）上构建。
- `gcc -static` 直接产出 AArch64 ELF；126 核，29GB 内存 + 15GB swap。
- 构建命令：`scons -C CHAOS/gem5 build/ARM/gem5.opt -j16`。
  - **注意**：`-j126` 在 29GB 主机上会 OOM 杀（cc1plus Killed → 假性汇编错误），必须用 `-j16`（已记入 memory `gem5-build-j126-oom-29gb`）。
- 产物：`CHAOS/gem5/build/ARM/gem5.opt`，含全部 CHAOS SimObject。
- SE 配置：`configs/se/arm_chaos.py` 用 gem5 v25 stdlib `SimpleBoard` + `PrivateL1PrivateL2CacheHierarchy` + `SimpleProcessor(O3, ARM)`；CHAOSReg/CHAOSPhysReg 挂 cpu，CHAOSMem 挂 `memory.mem_ctrl[0].dram`，CHAOSCache 经 `configs/se/arm_chaos_cache.py` 的 `_pre_instantiate` hook 挂 L1D/L1I/L2。

### 已完成且真实验证的单元

| commit | 单元 | 真实验证（实跑输出，非预测） |
|---|---|---|
| `95bb6ac` | 0a 基线 | 从 committed 源码干净重建 `scons: done building targets.`；source==binary（CHAOSPhysReg/CHAOSRAT 正确地 MISSING）；reg_chain golden `f247ef3fe6f02cfd` 在 O3 上重现 |
| `3b8c33c` | **G0** 可复现 RNG | **20/20 次重放逐字段一致**（seed=20260825 → integer[9] bit 20，每次相同）；CHAOSCache/Mem 加 `rngSeed`；CHAOSReg `rand()%2`→`rng()%2` |
| `54f31cd` | **G1** 位宽与合法域 | bit 0/31/32/63 全部可注入（64 位掩码，修复 `1<<bit` 有符号移位 UB；`faultMask` UInt32→UInt64）；XZR(integer[31]) 写丢弃 → Inactive |
| `e5eecbb` | **G2** 永久/间歇语义 | PhysRegFile::setReg 写路径 stuck 掩码（`setStuckTarget`）；stuck 跨 rename reuse + overwrite 仍存活（PhysReg[80] 被重写后 `00ff` 前缀证明掩码被重新施加） |
| `ea6b192` | **G3** cache 安全接口 | 删除不安全的 `static_cast<CacheAccessor*>`；新增受支持的公共 `Cache::getTags()` 访问器 |
| `9870e9f` | **G4** 内存正确性 | 修复 CHAOSMem 权重 `{bf,bf,so}→{bf,sz,so}`（重复 bit_flip/漏 stuck_at_zero）；20 次抽样 11bf/9sz/0so≈0.5/0.5/0.0；边界 `[start,end]` 闭区间、单字节可达；`1U<<` 无符号移位 |
| `d44982f` | **G5** 单故障 + 证据日志 | CHAOSCache/Mem 加 maxFaults（原来无上限——CHAOSMem 在一个 tick 内注入 5200 万次）；现在恰好 1 次；日志含 old/new/mask/width/seed/count |
| `4e8045f` | **G6** ≥1 cycle 间隔 | 几何分布采样钳到 ≥1（消除 p=1.0 时的同 tick 退化重发）；注入 tick 现在按 1000 ticks（1 cycle）递增 |
| `e01c9f1` | **G7** 无 CHAOS 源警告 | 补 `-Wswitch` 的 Random case；CHAOSReg/Cache/Mem 在 -Wall/-Wextra/-Wundef 下零警告 |
| `a9d4130` | **Patch 9** manifest runner | schemas/manifest.schema.json + manifests/*.yaml + tools/runner.py；端到端把 reg[9] 翻转分类为 Masked；G5 断言 faults∈{0,1}；§9.1 分类（SimulatorError/Inactive/Masked/SDC） |
| `8cbf7b6` | **P0 BM-GPR** pilot（首个真实 SDC） | arch_frontend 扫 X0–X9：**X2 `bcd3c78e2ed7de1b`、X3 `d43a25d7fcc218b7` SDC**，2/10=20%（pilot，n=10 无 95% CI） |
| `3551d57` | P0 GPR 按位分层 | X2/X3 × bit 0/31/32/63：**SDC=3、Hang=5、Masked=0** — 低位翻转→SDC（数据），高位翻转→Hang（控制流） |
| `3f5aeb4`+`d93cb69` | **P0 BM-L1D** | 解锁 stdlib SimpleBoard 的 L1D 暴露（`_pre_instantiate` hook，`getattr(ch,"l1d-cache-0")`）；l1d_reduce kernel（golden `f44d2b9cd4a173cd`），pilot n=10：**10/10 Masked**（诚实的 cache AVF：单字节瞬态翻转多被掩盖，§6.2 占用度条件） |
| `8beeea1` | **P0 BM-L1I** | l1i_loop kernel（golden `bb0b1c4cb661236e`），pilot n=10：**10/10 Hang、0 SDC、0 Crash**（指令字段翻转破坏控制流，符合 §7.2） |
| `3855c6b`/`ba22c0d`/`63ae626`/`f8aeb4f` | docs | `docs/arm64-sdc-STATUS.md` provenance + 诚实 deferred 清单 + 状态更新 |

### Phase 1 §8.3 golden 稳定性
- reg_chain 5 次无注入 → 1 个唯一校验和 `f247ef3fe6f02cfd`（稳定，cell 可入 campaign）。
- 三个 P0 kernel（reg_chain/l1d_reduce/l1i_loop）的 golden 在 native 与 gem5 上逐字节一致。

### 最终 E2E（rebase 前已验证）
- golden reg_chain no-inj：`f247ef3fe6f02cfd`
- CHAOSPhysReg X3 arch_frontend 1-bit-flip × 3 次重跑：全部 `d43a25d7fcc218b7`（SDC，完全可复现）
- CHAOSMem maxFaults=1：注入 count=1，输出 `f247ef3fe6f02cfd`（Masked）
- CHAOSCache L1D maxFaults=1：注入 count=1，输出 `f247ef3fe6f02cfd`（Masked）
- 三条故障路径（GPR/物理、内存、cache）在 ARM64 O3/SE 上端到端工作，G5 单故障可复现，§9.1 分类器就绪。

---

## 二、本次合并的一个事实

我基于旧的 `fi`（8f628d1）开工，但远程 `fi` 在此期间被并行会话经 PR #7 合入了：
- CHAOSPhysReg（更丰富版本，含 FP/Vec accessor + 更丰富的 type-aware read-trace API）
- CHAOSLSQFwd（store-to-load forwarding-path 注入器）
- o3 hooks（cpu.hh/free_list.hh/regfile.hh）
- 部分 G0–G5 参数

你选择 **rebase 到 origin/fi 再 push**。rebase 中：

- 我的 Patch 0b（从 main 恢复 CHAOSPhysReg）**被跳过** —— origin/fi 已有更丰富版本（含 float/vec accessor + type-aware read-trace），冗余。
- G4 在 `configs/se/arm_chaos.py` 上有 add/add 冲突，已采用我的更完整版本（含 CHAOSPhysReg+CHAOSMem 参数）解决。
- G2 写路径 stuck 掩码已干净落在 origin/fi 的更丰富 read-trace API 之上（两者并存，已验证：regfile.hh 同时有 `trace_type` 13 处 + `stuck_target` 10 处 + CHAOSPhysReg.cc 有 float/vec accessor 4 处）。
- 19 个补丁干净落在 origin/fi 之上，经 PR #9 合入 `fi`。

### ⚠️ 一个必须诚实说明的留白
rebase 后我跑过一次重建，命中 `CHAOSCacheParams has no member rngSeed/maxFaults` 的编译错误 —— 这是 scons 的 params 头未重新生成（陈旧 build 目录）导致的，**不是源码缺陷**，但我**在重建验证完成前就被叫停了**。所以 rebase 后的 `fi` HEAD 是否能干净编译，我**没有亲眼确认**。需要一次强制 regen params 的重建 + 跑一个 P0 pilot 来确认 rebase 没有引入回归。

---

## 三、尚未完成的工作（按计划分阶段，诚实列出）

### Phase 0 的两个 deferred（已做核心，未做完整）
1. **G6 触发器扩展**：只做了 ≥1 cycle 间隔。计划的 `tick/cycle/pc/committedInst/event` 多触发模式、用目标对象真实时钟域替换固定 `tickToClockRatio`、跨 ISA 按 committed instruction 对齐 —— **未做**。
2. **G7 sanitizer**：只做到 CHAOS 源零警告编译。计划的 ASan/UBSan 工具构建、SimulatorError 与架构 Crash/DUE 的运行期分离分类 —— **未做**（classifier 已在 runner 里实现，但 sanitized gem5 重建未做）。

### Phase 1 P0 — 只有 pilot，没有 formal cell
3. 三个靶点都只到 **pilot（n=10）**。计划要求：
   - **GPR**：X0–X30 按 ABI 角色分组 × 位段 [0:11]/[12:47]/[48:63] × bit 31/32/63 边界，n=384。
   - **L1I**：数据 array vs tag/valid 分开；非法编码 Crash/DUE vs 合法但错 SDC 区分。
   - **L1D**：data/tag/valid/dirty/metadata 字段级；ECC 32/64/custom word 粒度的 1-bit/2-bit/checker fault；raw vs protection-aware 两组。
   - **全部未做 formal。**

### Phase 2–7（计划明确分阶段，尚未开工）
4. **Phase 2 NEON/FP**：128-bit Vec 寄存器注入。当前 CHAOSPhysReg 走 `ThreadContext::getReg/setReg(RegVal=uint64_t)`，**无法触达 128 位 Vec** —— 需要 VecRegContainer 路径，是一个独立注入器。FP 字段（sign/exponent/mantissa、NaN/Inf/subnormal）分层未做。鲲鹏基线是 128-bit ASIMD，不用 SVE。
5. **Phase 3 TLB/SYS**：FS 模式下的 TLB entry/lookup-output/walker/page-table/system register 注入、ASID/VMID、TTBR/TCR/MAIR/SCTLR/VBAR/NZCV 白名单 —— **未做**（需 FS 模式 + ARM MMU 专用接口）。
6. **Phase 4 LSQ forwarding**：store→load 前递、部分重叠、4K alias、DMB/DSB/acquire-release、LDXR/STXR。origin/fi 上已有 CHAOSLSQFwd（并行会话做的），**我未与之整合/验证**。
7. **Phase 5 鲲鹏 128B L3 / coherence / NUMA**：paired-sector fault-domain proxy、Ruby/CHI 专用接口 —— **未做**。
8. **Phase 6 x86-64 配对对照**：C1 共同 64B 基线、同语义 fault pair —— **未做**。
9. **Phase 7 鲲鹏实机校准**：授权机器上的 RAS/ERR*/SEA/CPER/EDAC/APEI 日志枚举 —— **未做**（需实机与授权）。

### 横向未完成
10. **manifest runner 的完整化**：checkpoint restore、ROI 符号解析、多 run orchestration、§9.2 的完整 provenance 字段（mapped_phys_reg/freelist 状态/reads_before_overwrite/cache_residency/lsq_source_seq/tlb_asid 等动态上下文） —— **只有 baseline，未完整**。
11. **CHAOSCache 字段级注入**：当前只翻 cache 数据 array 的字节；tag/valid/dirty/replacement/coherence/ECC metadata 字段 —— **未做**（§7.3）。

---

## 四、下一步如何开展（按依赖顺序）

### 第 0 步（立即，堵诚实缺口）
在 `fi` HEAD 上做一次强制 regen params 的干净重建并跑一个 P0 GPR pilot，确认 rebase 没有引入回归。

```bash
# 强制重生成 params（删陈旧 params 头），重建
rm -rf CHAOS/gem5/build/ARM/params
scons -C CHAOS/gem5 build/ARM/gem5.opt -j16
# 跑一个 P0 pilot，应重现 X2/X3 SDC
python3 tests/p0_gpr_pilot.py \
    CHAOS/gem5/build/ARM/gem5.opt configs/se/arm_chaos.py workloads/directed/reg_chain
```
若失败，说明 G4 冲突解决或 G2 与 origin/fi 的 read-trace API 有 subtle 不兼容，需修。

### 第 1 步（Phase 1 formal 化，最高 ROI）
把三个 P0 pilot 扩成 formal cell。先做 GPR（成本最低、已有 SDC+Hang 证据）：
- 5× golden 冻结（已做 reg_chain；补 l1d_reduce/l1i_loop 各 5×）。
- 写一个 campaign driver（扩展 `tools/runner.py`）：按 `(寄存器 × 位段 × bit 边界)` 网格 × n=384，固定 manifest 版本，每次 max_faults=1，记录 §9.2 字段，分类后写 `runs/<campaign>/<run_id>/`。
- 用 Wilson/Jeffreys 区间报 P_SDC/P_DUE/Reachability（§10.3），不报全局 ISA 排名。
- 每 formal cell 独立保留至少 5% 重放样本；重放不一致则冻结该 campaign（§10.2）。

### 第 2 步（Phase 2 NEON）
新建 `CHAOSVecPhysReg` 走 VecRegContainer（不走 RegVal），4×32/2×64/8×16 lane 分层。这是把"NEON 128-bit lane 传播"这个鲲鹏相关靶点做实的必要工作（kunpeng.md：128-bit ASIMD，不用 SVE）。

### 第 3 步（G6/G7 补全）
- G6：给 CHAOSPhysReg 加 `committedInst` 触发（hook 到 commit 阶段 `commitDone`/`numInsts`），这是跨 ISA 对齐的关键。
- G7：sanitizer 重建放在工具 CI 层。

### 第 4 步（Phase 4 LSQ 整合）
origin/fi 上的 CHAOSLSQFwd 是并行会话做的、未经我的闸门框架验证。把它纳入 G0–G7 纪律（seed/maxFaults/evidence log），用 §7.5 的 7 类 directed 构造 + 强 oracle（期望 source store、字节拼接值、litmus 禁止结果集）。

### 第 5 步及以后
Phase 3 FS/TLB、Phase 5 L3-128/Ruby、Phase 6 x86 配对、Phase 7 实机 —— 按计划 §11 顺序，每个一个补丁、验证后 push。

---

## 五、运行配方（已验证可用）

```bash
cd /home/sdc/gem5-fi
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt

# golden（无注入）
$G5 --quiet --outdir=runs/gold configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3

# CHAOSPhysReg 单故障（arch_frontend，X3，bit_flip）
$G5 --quiet --outdir=runs/inj configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 \
    --chaos_phys --phys_mode=arch_frontend --phys_target_arch=3 \
    --probability=1.0 --first_clock=100000 --max_faults=1 \
    --rng_seed=20260825 --fault_type=bit_flip --bits_to_change=1

# manifest 驱动
python3 tools/runner.py manifests/p1-gpr-regchain-000384.yaml \
    --golden-checksum f247ef3fe6f02cfd --binary workloads/directed/reg_chain

# CHAOSCache L1D（用 arm_chaos_cache.py）
$G5 --quiet --outdir=runs/cache configs/se/arm_chaos_cache.py \
    --cmd=workloads/directed/l1d_reduce --target=l1d \
    --first_clock=10000 --max_faults=1 --rng_seed=20260825 \
    --fault_type=bit_flip --bits_to_change=1 --probability=1.0
```

**注意**：gem5 的 `--outdir` 放在 `runs/` 下（**不要放 /tmp** —— /tmp 在这台 29GB/15G-swap 主机上会被跑满，ENOSPC 杀过一个 G4 测试）。

**gem5.opt 路径更正**：本机上 `scons -C CHAOS/gem5 build/ARM/gem5.opt -j16` 实际产物在 **仓库根 `build/ARM/gem5.opt`**（约 1.1GB），不是 `CHAOS/gem5/build/ARM/`（后者可能是陈旧/重复文件）。运行用 `G5=$PWD/build/ARM/gem5.opt`。

---

## 六、工具正确性修复轮（源码检查报告 `docs/gem5-fi_branch_next_step.md` 之后）

一份源码检查报告发现：rebase 后的 `fi` HEAD（`70b725c`）上，并行会话的 CHAOSPhysReg vec/float 系列（6585f7a/3899cc2/51ed47e）在合并中**覆盖**了若干已验证修复，且分类器/manifest/NEON 缓冲区均有影响结果可信度的缺陷。报告的 5 条主张我逐条用真机验证为真（且第 2 条比报告更严重——架构态 CHAOSReg 也仍是 32 位）。随后在 `fix/fi-tool-correctness` 分支上逐个补丁修复，每个都经真跑验证、commit、push：

| commit | 补丁（报告 issue） | 真实验证（实跑输出，非预测） |
|---|---|---|
| `9f0ad41` | G2 恢复写路径 stuck 钳位（#1） | stuck_persist phys PhysReg[80] stuck_at_one 0xff → `00ff0000dee1f5d0`（reuse@cycle 150000 掩码重施加）；golden `00000000dee1f5d0`；O3 reg_chain golden `f247ef3fe6f02cfd` |
| `8739214` | 64 位掩码（CHAOSReg+CHAOSPhysReg，#2） | `--fault_mask=1<<32`/`1<<63` 现在分别记录 `0x100000000`/`0x8000000000000000`（修复前被 UInt32 截断为 0）；CHAOS 源零警告 |
| `4602f28` | NEON 缓冲区按 vecRegBytes() 定长（#3） | `--phys_reg_class=vector` phys 注入 reg_chain：无 SIGSEGV（修复前 192B 栈溢出）；log `RegClass: vec, PhysReg[0]` |
| `e3a39b9` | 诚实分类器 §9.1（#4） | exit1+empty+1inj → Crash（修复前误判 SDC）；X0/X1 Masked、X2 SDC；manifest reg9 → Masked（带 reason） |
| `aeaf043` | manifest 的 target/bit/trigger 真正生效（#5a） | physreg manifest idx=3 bit=[20] → `PhysReg[77] (<= ArchReg[3])` Mask `...0010000...` reads=25000 → SDC；idx=3 bit=[32] → SDC（高位现在真注入） |
| `890cca3` | 单一正式源码 + gitignore gem5-fs（#5b） | `diff -rq CHAOS/{Cache,Mem,Reg,PhysReg} ↔ vendored` 全同；Makefile clobber-safe（一致时 no-op）；`git check-ignore gem5-fs/` OK |

### 干净重建 + 闸门重验（真机）

- 强制 regen params 干净重建（`rm -rf build/ARM && scons -j16`）：`scons: done building targets.`，exit 0，**CHAOSReg/PhysReg/Cache/Mem 源零警告**（G7；CHAOSLSQFwd 的 `-Wswitch Random` 仍在，不在本轮范围）。`xxd -l4` = `7f 45 4c 46`（有效 ELF aarch64）。
- **G0 重放一致**：5/5 次同 seed CHAOSReg 注入，`fault_injections.log` sha256 全同 `ff4a0c9fd7768dc1`。
- **G1 位宽**：bit0/31/32/63 掩码全注入（见上 `8739214`）。
- **G2 永久**：`00ff0000dee1f5d0` 完整重放（见上）。
- **G4 内存**：CHAOSMem maxFaults=1 → `faults_injected: 1`（恰好 1 次，G5），证据日志 `old: 0x0, new: 0xde, Mask: 0xde, width_bits: 8, seed: 20260825`。
- **P0 GPR 重跑**：X2 → `bcd3c78e2ed7de1b`（SDC）、X3 → `d43a25d7fcc218b7`（SDC），与 progress.md 完全一致——可复现。
- **O3 golden 回归**：reg_chain no-inj → `f247ef3fe6f02cfd`，exit 0，0 SIGSEGV。

### ⚠️ 被本轮修复**作废**的旧结论（诚实声明）

下列旧结果是用**坏掉的工具**采的（32 位截断掩码 + 不查退出码的分类器），**不能作为 ARM64/鲲鹏 SDC 规律**：

1. `3551d57` "按位分层 SDC=3/Hang=5"：bit32/bit63 掩码被 UInt32 截断为 0 → 实际**未注入**，"高位 → Hang"结论**不成立**。修复后重跑：X3 bit63（1<<63）→ `d9a35c115042d41a`，**SDC**（exit 0，无 trap）——高位翻转经数据路径传播为 SDC，而非 Hang。高低位 SDC-vs-Hang 区分须在正式 cell 重做后才能再下结论。
2. `8beeea1` "L1I 10/10 Hang"：旧分类器把"空 stdout"直接算 Hang，未区分 Hang/Crash/SimError。须用修好的分类器重跑（Hang = 超时未完成；Crash = trap/exit≠0）后才能立 "all Hang" 之说。
3. `d72c61e` "L1D 10/10 Masked"：受影响较小（Masked 是不传播，与分类器无关），但证据日志/单故障断言须重跑留痕。

**可保留的可复现锚点**（修复后已验证）：reg_chain golden `f247ef3fe6f02cfd`；X3 arch_frontend 1-bit-flip = `d43a25d7fcc218b7`（SDC）；G2 stuck = `00ff0000dee1f5d0`；manifest physreg idx=3 bit=[20] = `88ff2422239b4952`（SDC）。

### 第三步最小重跑（报告 §六.3，修好工具后诚实重采）

报告 §六.3 要求用修好的工具重跑最易验证的几组、确认稳定重放+分类正确后再扩样。已做（详见 `docs/arm64-sdc-STATUS.md` 的 Step-3 节）：

- **网格1 GPR X2/X3 × bit 0/31/32/63**（替代被作废的 `3551d57`）：arch_frontend、显式 `--fault_mask=1<<k`（64 位，bit32/63 现在真翻转）。诚实分类结果：X2 bit0→SDC、bit31/32/63→**Hang**（超时 exit 124，stderr 无 panic/trap，已验证是真 Hang 非误判 Crash）；X3 bit0/31/32/63 全→SDC。**合计 SDC=5 Hang=3**。每格都精确命中指定 arch reg（X2→PhysReg[187]、X3→PhysReg[77]，均 `<= ArchReg[k]`），单故障。结论：SDC-vs-Hang 是**按寄存器**区分的（X2 是循环计数器，高位翻→Hang；X3 是数据累加器，全位→SDC），不是旧说法的笼统"高位→Hang"——旧说法既受 32 位截断伪影影响、又过度泛化。
- **网格4 内存首/末/单字节**：CHAOSMem 在 l1d_reduce（512KiB BSS 数组）上，maxFaults=1。闭区间 `[start,end]` + 单字节 `[n,n]` 边界正确：首字节经 `[0,1]` 可达（addr 0）；中位 `[0x100000,0x100000]`→addr 1048576；末字节 `[0x3FFFFFFF,...]`→addr 1073741823（旧代码会丢末字节，G4 已修）。注：`addr_end=0` 是"不限"约定（同 lastClock=0，非 bug）。全 BSS 范围 5 随机 seed→5/5 Masked（瞬态单字节多被掩蔽，诚实内存 AVF）。
- **网格2/3（L1D 定到活数据、L1I 定到执行指令）**：需 cache config + 更紧 O3 窗口/定向 cache line，L1D/L1I 旧 pilot（d72c61e/8beeea1）须用修好的分类器重跑后才能立"全 Masked/全 Hang"之说——本轮未做，后续。

---

## 七、一句话诚实结论

本次把计划的 **Phase 0（七个闸门）做实、manifest runner 跑通、Phase 1 三个 P0 靶点都产出了真实可复现的 SDC/Hang 证据**（GPR 2/10 SDC、按位分层 SDC=3/Hang=5、L1D 10/10 Masked、L1I 10/10 Hang），全部 19 补丁经实跑验证并已合入 `fi`。**唯一的诚实留白是 rebase 后的干净重建验证被叫停，需补一次确认**；formal cell（n=384）、NEON/TLB/LSQ/L3-128/x86 配对/实机校准这些 Phase 2–7 是明确分阶段的后续工作，已记录在 `docs/arm64-sdc-STATUS.md`，不是本次范围，不能谎称完成。

### 后续轮：工具正确性修复（`fix/fi-tool-correctness`，6 补丁）

源码检查报告 `docs/gem5-fi_branch_next_step.md` 指出 rebase 后的 `fi` HEAD 有 5 处影响结果可信度的回归（G2 写路径 stuck 被覆盖、掩码仍 32 位、NEON 缓冲区溢出、分类器误判、manifest 字段未生效、顶层/内置源码两份不一致）。我在 `fix/fi-tool-correctness` 上逐条修复并真机验证（见上 §六）。**修复作废了 §七旧结论中的 `3551d57`/`8beeea1`/`d72c61e` 三个 pilot 结果**（坏工具采的数据，不能当规律）。可复现锚点（golden、X2/X3 SDC、G2 stuck）在修复后仍然成立。Phase 2–7 与 formal cell 仍未做，不在本轮范围。详细修复后状态见 `docs/arm64-sdc-STATUS.md`。
