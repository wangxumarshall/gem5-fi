# CPU-Profile-Driven SDC ED 评估方案——配置驱动的指令流 SDC 检测有效性评估实施计划

> **For agentic workers:** 用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实施。所有步骤用 `- [ ]` checkbox 跟踪。
> **纪律（CLAUDE.md）**：一补丁一单元 → 真机三步自验证（干净增量构建零新警告 + 功能验证引用真实输出 + 不相关回归）→ commit（无 Co-Authored-By 尾注）→ push `feat/sdc-ed-eval`（分支于 fi-fuzz）。

**Goal:** 把现有 ACE/IBR 结构覆盖评估升级为**配置驱动的期望 SDC 检测率（ED, Expected Detection）评估**：用户通过一份声明式 CPU 描述文件（YAML）指定微架构参数与保护矩阵，系统即可对任意 AArch64 指令流序列测出按真实故障分布加权的 ED 值与 per-unit 诊断，并据此筛选/进化出对该 CPU 更能检测出 SDC 故障的指令流。全链以 per-unit SFI lift（ED-top-K vs 随机 vs 旧标量 fitness）实证验证"ED 高的序列真的更能检出 SDC"。

**Architecture（三层分离，核心不变量：换 CPU 配置文件，Layer A 代码零改动）:**

```
Layer A（架构根基，CPU 无关）  单元化结构覆盖模型
   7 单元分解（IFU/OoO/IEX/LSU/FSU/MMU/L2C）+ 采集器协议（A_u 测量方法）
   + ED 评分器（Σ w·ρ·q·A 与次模选择算法）
Layer B（实例化，CPU 相关）    权重与先验
   w_u（翻转份额，位容量推导）· ρ_u（SDC 转化率，SFI 标定回填）
   · ceiling_u（可达性上限）· q_u（checker 可观测率）
Layer C（用户接口）            声明式 CPU 描述（YAML 单一事实源）
   一份描述 → 四消费者：① gem5 实例化 ② CHAOSCov 分母 ③ ρ 初值推导 ④ w 推导
```

**Tech Stack:** C++（gem5 SimObject，SCons）、Python 3（PyYAML 6.0.3 已核实）、AArch64 原生 gcc 12.3.1、gem5.opt（`CHAOS/gem5/build/ARM/gem5.opt`——**当前 build 目录缺失，Phase 0 重建**）。

**Spec（用户需求，2026-09-19 三轮讨论收敛）:**
1. ACE/IBR 的劣势（读≠传播到校验输出、均匀 bit 显著性、与故障模型脱钩、无 checker 概念）必须逐项缝合；
2. 微架构级结构覆盖是架构根基，「按真实故障分布加权的期望检测率」是根上的具体实例；
3. 用户配置具体 CPU 微架构参数，即可高保真仿真该 CPU 上高准确检测 SDC 故障的指令流；
4. 校准锚：FSU 80% / IEX 70% / IFU 66% / OoO 56% / LSU 54% / L2C 40% / MMU 20%（给定覆盖率表，新指标须能对齐并解释）。

---

## 一、指标定义（Layer A 的数学，全部写入代码注释与 method 文档）

### 1.1 ED 主公式

```
ED(S) = Σ_{u∈units}  w_u · ρ_u · q_u · A_u(S)

w_u     单元 u 的翻转份额 = bits(u) / Σ bits(所有单元)   （SRAM 主导，YAML 推导）
ρ_u     单元 u 的 SDC 转化率 = P(激活故障 → SDC)          （SFI 战役标定回填）
q_u     checker 可观测率 = P(输出偏离 → 被 checker 分辨)   （golden-diff=1.0 基线；部署臂<1）
A_u(S)  序列 S 对单元 u 的激活覆盖（0~1，采集器实测，见 §1.3）
ceiling_u  单元 u 的可达性上限（MMU 用户态≈0.2×FS；IFU SDC 轴=0）
有效覆盖 A'_u(S) = min(A_u(S), ceiling_u)
```

**输出双报告：per-unit 分解（诊断用）+ 总分 ED（排序用）。** 单标量只用于排序，任何决策记录必须附 7 维分解。

### 1.2 与校准锚（给定覆盖率表 c_u）的对齐义务

新指标在「当前序列集」（workloads/harp/ 8 个 + 生成序列）上跑出的 per-unit `A_u · reachability` 必须能复现 c_u 表的相对结构（FSU>IEX>IFU>OoO>LSU>L2C>MMU）。对不上的单元即指标缺陷或值依赖未建模——每个偏差写进标定报告（Phase 6），禁止调参硬凑。

### 1.3 A_u 的采集定义（per-unit，全部映射到现有/新增 hook）

| 单元 | A_u 定义 | 数据源 | 现状 |
|---|---|---|---|
| IFU | 预测器状态覆盖（BTB/RAS/方向历史被序列触达的比例） | CHAOSBPU 基建 | SDC 轴 ρ=0（Phase 16 三面 0%），**只进 Crash 轴** |
| OoO | ROB 占用带覆盖 × rename 距离分布 | commit.cc tick + PrfRegState birth/last_read | 占用直方图已有；距离分布是纯 stat |
| IEX | IBR（issue 输入位比）× 门级敏感位覆盖 | inst_queue.cc + CHAOSGateFU 网表差分 | IBR 已有；门级覆盖臂新增 |
| LSU | sqAvf（精化 per-slot）+ 前转覆盖比 + load-use 距离 | lsq_unit.cc（前转 hook 新增） | sqAvf 聚合近似已声明 |
| FSU | IBR(FP) × **FP 值类熵**（normal/subnormal/NaN/Inf/零 分布） | inst_queue.cc issue 点采样 | 值类剖面新增（CHAOSFPU 全 Masked 的直接回应） |
| MMU | TLB 条目/页大小多样性覆盖 | FS 臂（configs/se/fs_checkpoint.py） | SE 用户态封顶 20%，FS 臂扩展 |
| L2C | block-ACE **data-face/tag-face 双账本** | mem/cache/base.cc + targetCache 列表化 | L1D 单账本已有，L2+分面新增 |

### 1.4 SDC-ACE（bit-array 结构的 A_u 升级，本方案的核心超越点）

裸 ACE 的读事件只证明「值被消费」，不证明「值影响校验输出」。升级：

```
SDC-ACE 区间 = [write, last_read_on_path_to_checkable_output)
gap 指标     = (ACE − SDC-ACE) / ACE     （序列设计缺陷的直接证据，喂 advice 引擎）
```

实现路径（复用 read-trace 资产）：反向数据流——从校验输出点（harp_wrap 的 g_reg 终态哈希与 mem CRC 计算处）反推哪些物理寄存器/内存块的读在可达切片上。采集器侧给 IRF/L1D/SQ 的读事件加 `on_checkable_path` 标记（taint 由 CHAOSCov 维护，从 epilogue 的一次性回溯分析获得静态调用图内可达集，运行时按寄存器/块索引查询）。

**诚实边界（写入文档）**：第一版 taint 是「epilogue 可达性」近似（不追值依赖的控制流），与完整程序切片的差距在 Phase 6 负对照实验中量化。

### 1.5 部署模式（去 golden，最终验收臂）

```
deployment-detection = P(故障 → 在线 checker 报警)   （无 golden 对照）
在线 checker 候选：同核复算（时间冗余，对 transient）/ 校验和自比对（对 permanent）
```

与 golden-diff detection 的差值衡量序列在真实部署环境的检测能力。permanent/transient 对 checker 的不同要求在此臂分叉。

### 1.6 ρ_u 初值表（Layer B 首轮，全部来自仓库实测，Phase 6 标定回填）

| 单元 | ρ_u 初值 | 出处（实测） |
|---|---|---|
| IFU | 0.0 | Phase 16：dir_flip/target_flip/ras_flip 三面全 0% SDC |
| OoO | 0.05 | IRF SFI（readwrite_seq detection 0.04 起点）+ 双模式 14.8% 差 |
| IEX | 0.05 | 门级/执行级 FU SFI 基线 |
| LSU | 0.05 | lsqfwd formal：P_SDC=4.7% [3.0,7.3] |
| FSU | 0.01（值依赖强，首轮保守） | CHAOSFPU N=20 全 Masked |
| MMU | 0.0（SE）/ FS 臂实测回填 | addr_map_sub 384/384 Masked |
| L2C | 0.45（tag-face）/ 0.0（data-face SECDED） | L2 2x2 arms：39%→47% vs 47%→0% |

**保护矩阵 → ρ 推导规则**（Layer C 自动化）：无保护→跑 SFI 标定臂；data-SECDED→data-face ρ=0、tag/逻辑面保留；parity(SED)→单 bit 检、双 bit 漏（ρ 按双位条件概率折算）。

---

## 二、CPU 描述文件（Layer C）schema 与首期实例

### 2.1 文件与格式

```
configs/cpu-profiles/
  taishan-v110.yaml     # 首期标定实例（与 two_level_taishan.py 现配一致）
  kunpeng920.yaml       # 底表 §3-§8 转写
  neoverse-n2.yaml      # 底表转写（第二标定实例，跨 CPU 迁移测试用）
  schema.md             # 字段语义与 uncertainty 规则
```

```yaml
cpu: taishan-v110
derived_from: smoke_test/configs/two_level_taishan.py   # 溯源
units:
  IFU:  {btb: {entries: 2048, prot: none}, ras: {entries: 32, prot: none},
         l1i: {size: 64KiB, assoc: 4, prot: ecc_claimed_no_evidence}}
  OoO:  {rob: {entries: 97, prot: none},
         prf_int: {regs: 125, width: 64}, prf_float: {regs: 96, width: 64},
         prf_vec: {regs: 96, width: 128}, lq: {entries: 65}, sq: {entries: 47}}
  IEX:  {fus: {int_add: {count: 3, width: 128, op_lat: 1},
               int_mul: {count: 1, width: 128, op_lat: 3}},
         gate_model: {int_add: kogge_stone_1154g, int_mul: shift_add_44418g}}
  FSU:  {fus: {fp_add: {count: 2, width: 256, op_lat: 2},
               fp_mul: {count: 2, width: 256, op_lat: 4}}}
  LSU:  {l1d: {size: 64KiB, assoc: 4, blk: 64, prot: none},
         forwarding: true, store_set: false}
  MMU:  {l2_tlb: {entries: 1024, prot: none}}
  L2C:  {l2: {size: 512KiB, assoc: 8, prot: none}}     # smoke_test/configs/caches.py 实读（Task 0.1 恢复后核实）
weights_override: {}      # 用户手工覆盖 w_u
rho_overrides: {}         # 用户手工覆盖 ρ_u（覆盖标定值须附理由）
residuals: [mop_cache_absent, l1i_prot_claim_unverified]   # 诚实边界：未建模/未证实项
```

**两条硬规则**：① 未披露字段写 `null` + `uncertainty: true`，不猜值——ED 输出对该单元附区间而非点值；② `residuals` 非空时报告首行必须列出，ED 数字只对 modeled 集合负责。

### 2.2 四消费者管道

```
configs/cpu-profiles/*.yaml
  ① configs/se/profile_taishan.py（新 config 入口，--profile 参数）
     读 YAML → 实例化 O3（PRF/ROB/LQ/SQ/fu_pool）+ cache 层级
  ② CHAOSCov profile 参数（Python 侧解析 YAML → SimObject 参数）
     ibrFuCounts/ibrFuWidths/cacheNumBlocksList/sqEntries/prfWidths 全部来自描述
  ③ tools/ed_score.py 直接读 YAML → w_u 推导 + ρ_u 初值
  ④ 标定战役（Phase 6）读 YAML → 选 SFI 臂（保护矩阵→臂选择规则）
```

---

## 三、File Structure（新增/修改全集）

```
configs/cpu-profiles/taishan-v110.yaml          # 新增 P1
configs/cpu-profiles/kunpeng920.yaml            # 新增 P1（底表转写）
configs/cpu-profiles/neoverse-n2.yaml           # 新增 P1（底表转写）
configs/cpu-profiles/schema.md                  # 新增 P1
configs/se/profile_taishan.py                   # 新增 P1（--profile 入口，包装/复用 two_level_taishan 逻辑）
tools/ed_profile.py                             # 新增 P1（YAML 解析 + w/ρ/ceiling 推导库）
tools/ed_score.py                               # 新增 P5（ED 评分 + 次模选择 + per-unit 报告）
tools/sfi_lift.py                               # 新增 P6（per-unit lift 战役 + Wilson CI + AUC）
CHAOS/gem5/src/CHAOSCov/CHAOSCov.{hh,cc,py}     # 修改 P2/P3/P4（分母参数化 + 新账本）
CHAOS/gem5/src/cpu/o3/lsq_unit.cc               # 修改 P3（前转 per-slot hook + load-use 距离）
CHAOS/gem5/src/cpu/o3/inst_queue.cc             # 修改 P3（FP 值类剖面采样）
CHAOS/gem5/src/mem/cache/base.cc                # 修改 P3（data/tag 双账本已在此，改分发）
smoke_test/configs/two_level_taishan.py         # 修改 P2（--cov-profile 旗标）
workloads/harp/                                 # P6 负对照序列（dead_calc_high_ace.S 等）
docs/sdc-ed/method.md                           # 新增 P0（指标定义 + 诚实边界，随首补丁立骨架）
docs/sdc-ed/calibration-report.md               # 新增 P6
docs/superpowers/plans/2026-09-19-cpu-profile-driven-sdc-ed.md   # 本计划
```

---

## 四、任务分解（7 Phase / 23 任务，一补丁一单元——原写 22 系制定时计数笔误，以 checkbox 清单为准）

### Phase 0 — 环境重建与方法文档骨架（硬阻塞解除）

- [x] **Task 0.1 gem5 增量重建 + 配套 config 恢复 + 双回归锚固定**
  Files: `smoke_test/configs/caches.py`、`smoke_test/configs/fu_pool.py`（**从 sdcfuzz 备份恢复——这两个文件从未被 git 跟踪，仓库克隆后 config 无法 import**）。
  命令: `cd CHAOS/gem5 && scons build/ARM/gem5.opt -j16`（禁止 -j126，OOM 实测）。
  验证: (a) scons done 0 错误；(b) `two_level_taishan.py --binary workloads/directed/reg_chain --mode baseline` exit 0 且 checksum=`f247ef3fe6f02cfd`；(c) `--binary workloads/harp/sample_seq` SUM=`17994817166615565002` CRC=`8f333d15`。两个锚与 runner.py GOLDEN_IDS / Task 1.1 commit 实证一致。**登记基线构建耗时，后续任务共享增量构建。**
  恢复文件核实（与 sdcfuzz/gem5_config/configs/ 备份 diff 一致）：L1I=64KiB 4-way、L1D=64KiB 4-way、L2=512KiB 8-way；FU 池 IntAlu×3/IntMult×1(opLat=3)/FPU×2(FloatAdd opLat=2、FloatMult 4、FMA 5)/SIMD×2/AGU×2+2/System×1。
  完成（commit b882cb24 恢复 config + 6eef63bd 构建收口双锚：reg_chain f247ef3fe6f02cfd / sample_seq SUM=17994817166615565002 CRC=8f333d15）。
- [x] **Task 0.2 `docs/sdc-ed/method.md` 骨架**
  内容: §1.1-1.6 指标定义全文（本计划一、三节）、三层架构图、诚实边界清单（taint 近似、ρ 初值来源、gate 网表非 RTL、ceiling 依据）。
  验证: 文档入库，公式与代码注释逐字一致（后续每个任务同步该文档对应小节）。
  完成（commit f503e047，6 节 + 边界表 7 项；定稿更新见 Task 7.2）。

### Phase 1 — CPU 描述文件与解析库（Layer C 落地）

- [x] **Task 1.1 `tools/ed_profile.py`：YAML 解析 + w/ceiling 推导**
  内容: 读取 cpu-profile YAML；`bits(u)` 按单元位容量累加（SRAM：容量×位宽；PRF：regs×width；FU：门数×平均扇入触发器——**组合逻辑按 1/3 SRAM 权重折算，系数写明并进 residuals**）；输出 w_u 表与 uncertainty 区间。
  验证: 对 taishan-v110.yaml 输出 7 单元 w_u（总和=1.0）；null 字段正确产生区间；`python3 -m pytest tools/tests/test_ed_profile.py`（新增，≥8 用例：全字段/含 null/含 override/residuals 传播）。
  完成（commit da560e02，pytest 13/13 > 要求的 ≥8）。
- [x] **Task 1.2 `configs/cpu-profiles/` 四文件（taishan-v110 + kunpeng920 + neoverse-n2 + schema.md）**
  内容: taishan-v110 与 two_level_taishan.py 逐参数对齐（PRF/ROB/LQ/SQ/fu_pool/L1D/L2——**L2 容量从 config 实读，不凭记忆**）；kunpeng920/neoverse-n2 从 `docs/cpu/arm64/microarchitecture-sdc-sensitivity.md` §3-§8 机械转写，未披露=null+uncertainty；schema.md 写字段语义与两条硬规则。
  验证: (a) `ed_profile.py` 对三份 YAML 全部解析成功且 w_u 归一；(b) 抽查 10 个字段与底表原文逐字一致（列对照表进 commit message）；(c) residuals 非空时解析器输出警告。
  完成（commit 1ceffd45，三份 Σw=1.0000，10 字段抽查对照表在 commit message）。
- [x] **Task 1.3 `configs/se/profile_taishan.py` --profile 入口**
  内容: 新 config 入口，`--profile configs/cpu-profiles/taishan-v110.yaml`；内部把 YAML 单元参数映射到 O3/cache 实例化（复用 two_level_taishan.py 结构）；**默认无 --profile 时行为与 two_level_taishan.py 完全一致**（回归锚）。
  验证: (a) `--profile taishan-v110.yaml --binary workloads/harp/sample_seq` 输出 SUM/CRC 与 two_level_taishan.py 直跑逐字节一致（同构实证：描述文件⇔现配置等价）；(b) 回归：two_level_taishan.py 无新旗标路径跑 reg_chain golden 不变。
  完成（commit bf24913f + 6eef63bd 构建后收口：--profile 与直跑 SUM/CRC 逐字节一致）。

### Phase 2 — CHAOSCov 参数化 + 单元化 stats（Layer A 的分母缝合）

- [x] **Task 2.1 去硬编码：ibrFuCounts/ibrFuWidths/cacheNumBlocks/sqEntries 全部参数化**
  Files: `CHAOSCov.{hh,cc,py}` + `two_level_taishan.py --cov-profile`。
  内容: C++ 侧 `ibr_fu_count/ibr_full_width` 改为 SimObject 参数（VectorParam）；Python 侧从 --cov-profile 读 YAML 填参（无 --cov-profile 时保持现默认值=行为不变）。
  验证: (a) 增量构建零新警告；(b) `--cov --cov-profile taishan-v110.yaml` 跑 sample_seq：**全部 harp.* stats 数值与改动前（硬编码版）完全一致**（参数化无行为变化的实证）；(c) 回归：无 --cov 路径 reg_chain golden 不变。
  完成（commit 6eef63bd，默认 vs profiled 8 stat 逐位一致 + reg_chain 锚不变）。
- [x] **Task 2.2 targetCache 列表化（L1D+L2 双采集）**
  Files: `CHAOSCov.{hh,cc,py}`。
  内容: targetCache 单值 → 列表；每 cache 独立 block-ACE 账本（per-cache aceCycles/Avf stats）；owner 过滤逻辑改为集合匹配。
  验证: (a) 单 cache 配置（仅 L1D）数值与改动前一致；(b) 双 cache（L1D+L2）跑 rand_mem：两账本均有非零事件且 L2 账本事件数 < L1D（层级过滤正确）；(c) 回归 golden 不变。
  完成（commit 7913f11b，单 cache l1dAvf 逐位一致；l2cReads=27 < l1dReads=197；l2cAceCycles=0 的语义——L2 fill 与 read 同周期且无逐出——已在 commit message 诚实记录）。
- [x] **Task 2.3 per-unit stats 归并（7 维覆盖向量输出）**
  Files: `CHAOSCov.cc` finishStats。
  内容: 现有 irfAvf*/l1dAvf/sqAvf/ibr* 归并输出 `harp.cov.units.*` 7 维向量（IFU 占位=Crash 轴、MMU=SE 可达子集），供 ed_score.py 消费；旧 stats 名保留（兼容 harp_eval.py）。
  验证: (a) sample_seq 跑出 7 维向量且 OoO/IEX/LSU 分量与旧标量一致；(b) 回归 golden 不变。
  完成（2026-09-19，`harp.covUnits::` Vector stat：IFU=0（Crash 轴）/OoO=0.014838（=irfAvf ✓）/IEX=0.040698（=max(0.039486,0.040698) ✓）/LSU=0.014102（=sqAvf ✓）/FSU=0/L2C=0.000250（=max(l1dAvf,0) ✓）/MMU=0 占位；reg_chain 回归 f247ef3fe6f02cfd ✓；scons done 零新警告；实现从已定稿的标量 stats 读回（harpStats.*.value()）而非原始账本二次计算——与旧标量构造性一致，不存在双计）。commit 9274f1e3。
  （注：Task 7.2 收尾时清除本条早期登记的「deferred 未实施」行——该行为定稿快照写作时 2.3 尚未合入的临时状态，与 9274f1e3 的实测完成注记矛盾，以完成为准。）

### Phase 3 — 采集精度升级（A_u 的三个新信号）

- [x] **Task 3.1 LSU 前转 per-slot hook + load-use 距离 stat**（消除 method.md 已声明的聚合近似）
  Files: `lsq_unit.cc`（前转匹配处 + load 数据返回处）、`CHAOSCov.{hh,cc}`。
  内容: `LSQUnit::read` 的 store→load 前转成功点加 `harp_cov_on_sq_forward(slot_idx)`；SQ 账本改 per-slot（消除「按序关闭最老开区间」近似）；新增 load-use 距离直方图（load 写回 → 首次 getReg 消费）。
  验证: (a) rand_mem 跑出 sqForwardCycles 与 writeback 账本分离且 sqAvf 数值变化（近似消除的实证，差异写进 commit message）；(b) 回归 golden 不变。
  完成（commit b8ac04eb，rand_mem 实测新账本 sqWritebackAceCycles=1126 非零、旧账本逐位不变、loadUseDist 13 样本）。
- [x] **Task 3.2 FSU 值类剖面（FP value-class 直方图）**（回应 CHAOSFPU 全 Masked 的值依赖）
  Files: `inst_queue.cc`（issue 点采样源操作数）、`CHAOSCov.{hh,cc}`。
  内容: FP issue 事件按源操作数位模式分类（normal/subnormal/NaN/Inf/zero，AArch64 double 布局判别），per-FU-class 直方图 + 值类熵 stat `harp.cov.fsu.value_entropy`。**注意：读操作数值须在 issue 点经 getReg 旁路安全读取——若 IQ 阶段操作数未定（举旗等待），回退 execute 完成点采样并诚实记录口径**。
  验证: (a) rand_fp 跑出五类直方图，normal 占主导（随机指数位生成下 NaN/Inf 有非零占比）；(b) 定向构造 subnormal-heavy 序列（新 workload `workloads/harp/subnormal_seq.S`）直方图相应偏移；(c) 回归 golden 不变。
  完成（2026-09-19，读点安全性实证：ISA execute 经 setRegOperand 直写 PRF、wakeDependents 在 writeback——issue 点（wake 后）源值必驻留 PRF，与 CHAOSFPU 源读 hook 同路径。`harp_fp_class_of` IEEE754 分类器 8 用例单元测试全 OK（normal/subnormal/NaN/Inf/zero/-Inf/sNaN + 10M 随机位模式率校验 sub 0.049%/NaN 0.049%）。rand_fp：FPAdd normal=382/zero=130、熵 0.351；randbits_seq（3000 行随机位模式链）：**subnormal=1、Inf=56 端到端命中**、熵 0.392；分类器对 NaN 由单元测试证明（该负载无 NaN 源）。回归 reg_chain f247ef3fe6f02cfd ✓ 零新警告。诚实边界：Scalar FP 走 RegVal、Vec 走 blob 2-lane（128b 全宽）——subnormal_seq.S 原设计因 fmov 不在白名单改用 ldr 装载随机位模式，定向偏移验证由 randbits 的 rare-bin 命中替代）。commit 7c27f2f2。
  （注：Task 7.2 收尾时清除本条早期登记的「deferred 未实施」行——该行为定稿快照写作时 3.2 尚未合入的临时状态，与 7c27f2f2 的实测完成注记矛盾，以完成为准。）
- [x] **Task 3.3 L2C data-face/tag-face 双账本**
  Files: `mem/cache/base.cc`（事件点补 tag 语义）、`CHAOSCov.{hh,cc}`。
  内容: read/write/evict hook 补 face 维度：数据面=read 命中数据/fill 数据；tag 面=tag 比较参与的事件（lookup 时 tag 匹配行为——在 satisfyRequest/handleFill 的 blk 选择路径上区分）。per-face aceCycles + Avf。**L2 tag-face AVF 高 = 序列触发了合法别名域 = ECC 盲高危区（39-47% 实测线的覆盖侧对应物）**。
  验证: (a) rand_mem 双 face 账本非零且 data-face 事件 >> tag-face（每 access 一次数据事件、一次 tag 参与）；(b) 构造别名触发序列（不同地址同 tag 低位——64KiB 4-way 的冲突序列）tag-face 事件显著上升；(c) 回归 golden 不变。
  完成（commit 0759eb58，tag-face 账本 + conflict_seq 别名触发 workload 实证 tag 事件显著上升；单 L1D 路径逐位一致）。
- [ ] **Task 3.4 OoO rename 距离分布 + ROB 占用带**（纯 stat，不加 hook）
  Files: `CHAOSCov.{hh,cc}`。
  内容: PrfRegState 已有 birth/last_read——finishStats 输出 rename 距离直方图（write→last_read 周期差）；占用直方图细化到 ROB 占用带（commit tick 采样点已有）。
  验证: (a) readwrite_seq（长链）vs overwrite_seq（死写）距离直方图形态分化（长链右移——方向验证）；(b) 回归 golden 不变。
  状态: **deferred（未实施）**——占用直方图已有，rename 距离分布缺。解锁：后续补丁。

### Phase 4 — SDC-ACE 采集（核心超越点，依赖 P2/P3）

> **Phase 4 状态（2026-09-19 定稿）**: 全部 3 任务 deferred（未实施）。SDC-ACE 是本方案「核心超越点」中未落地的那一半——ED 目前消费裸 ACE 账本，「读了但未进校验输出」的松量未量化。解锁：后续补丁（依赖的 Task 2.3 covUnits 已合入，9274f1e3）。

- [ ] **Task 4.1 epilogue 可达集分析（taint 源）**
  Files: `tools/harp_wrap.py`（epilogue 标注——校验和计算消费的 g_reg/mem 索引集合已在包装器内静态可知）、`CHAOSCov.{hh,cc}`。
  内容: 包装器在生成时输出 `.reach.json`（校验点消费的寄存器/内存区域静态清单）；CHAOSCov 启动时加载，运行时读事件查询可达集。
  验证: (a) sample_seq 的 .reach.json 生成且条目数 = NREGS+mem 区域；(b) 回归 golden 不变。
  状态: **deferred（未实施）**。
- [ ] **Task 4.2 IRF/L1D/SQ 三账本 SDC-ACE 化 + gap 指标**
  Files: `CHAOSCov.{hh,cc}`（读事件加 on_path 判定，第二组 ACE 账本）。
  内容: 读事件在可达集内 → 双计（ACE + SDC-ACE）；可达集外 → 仅 ACE。stats: `irfAvfSdc/l1dAvfSdc/sqAvfSdc` + `sdcGap` per 结构。gap 喂 advice 引擎（P5）。
  验证: (a) readwrite_seq（链直达校验和）sdcGap ≈ 0；(b) **负对照 workload `workloads/harp/dead_read_seq.S`（写后读但读出的值乘零丢弃）sdcGap 显著 > 0**——这是 SDC-ACE 价值的一锤定音实验；(c) 回归 golden 不变。
  状态: **deferred（未实施）**——dead_read_seq.S 负对照 workload 未生成。
- [ ] **Task 4.3 gate 级敏感覆盖臂（IEX 门级位图）**
  Files: `CHAOSGateFU` 复用 + `CHAOSCov`。
  内容: 对 issue 的源操作数对跑网表**传播差分**（不注入：对每输入位翻转算结果是否改变 = 逻辑掩蔽函数），per-FU-class 输出敏感位占比 `harp.cov.iex.gate_sens_ratio`。Kogge-Stone 1154 门级 W=4/8/12 边界向量为天然高敏感点，喂 advice（生成进位边界操作数）。
  验证: (a) 全 1/全 0 操作数敏感比 ≈ 0（掩蔽下界）；(b) 随机操作数敏感比 ∈ (0,1) 且加法进位链位段敏感占比高于低连续位段（结构先验方向）；(c) 回归 golden 不变。**性能边界：网表差分每 issue 调用，若 IQ 热路径开销 >5%（实测构建后 profile）则降级为采样 1/64 并记录**。
  状态: **deferred（未实施）**——1/64 采样降级预案未触发（未开工）。

### Phase 5 — ED 评分器与进化整合（Layer A 收口）

> **Phase 5 状态（2026-09-19 定稿）**: 全部 3 任务 deferred（未实施）。ED 公式目前只在 method.md §3.1 与 ed_profile.py 的 w/ρ/ceiling 推导中定义，无端到端评分工具（ed_score.py 未写；其消费对象 covUnits 已由 Task 2.3 备好）。解锁：后续补丁。

- [ ] **Task 5.1 `tools/ed_score.py`：ED 计算 + per-unit 报告**
  内容: 输入（stats.txt + cpu-profile YAML + ρ 表）→ 输出 ED(S)、7 维分解、与 c_u 锚的对齐表、gap 配额（w·ρ·(ceiling−A) 排序的「下一步该补哪个单元」建议）。
  验证: (a) 对 workloads/harp/ 8 序列出 8 份报告；(b) 对齐表：7 单元中 ≥5 个相对序与 c_u 一致（IFU 因 ρ=0 归 Crash 轴除外——预期不一致项写明）；(c) ρ 全 1、w 均匀的退化情形下 ED ≡ 平均 A_u（一致性自检）。
  状态: **deferred（未实施）**。
- [ ] **Task 5.2 次模序列集选择器**
  内容: 给定候选池（生成序列 + 库存序列），`greedy [1−Π(1−A_u(S))]` 选择 K 条 + per-unit 配额约束；输出选择理由（每条序列补了哪个单元的 gap）。
  验证: (a) 合成数据单元测试（构造已知 A_u 的 mock 序列池，验证贪心选择命中理论最优——小规模可穷举对照）；(b) 真实池上跑出 K=10 选择集，覆盖向量 ≥ 单序列最大覆盖（无堆叠实证）。
  状态: **deferred（未实施）**。
- [ ] **Task 5.3 harp_evolve fitness 替换 + advice 规则扩展**
  Files: `tools/harp_evolve.py`、`tools/harp_advice.py`。
  内容: evolve 的 fitness 从标量 ACE → ED（--fitness ed|legacy 双模式保留对照）；advice 新规则：sdcGap 高→引导值消费改造；FSU 值类熵低→引导 subnormal/NaN 生成；L2C tag-face 低→引导冲突序列；rename 距离集中→引导依赖链变长。
  验证: (a) 同 seed 同序列池，ed 与 legacy 两模式各跑 1 代，ED 模式的子代 ED 均值 > 初代（进化方向正确）；(b) advice 规则单元测试（mock detail log → 规则命中）；(c) 回归 golden 不变。
  状态: **deferred（未实施）**。

### Phase 6 — SFI 标定与 lift 验证（真值闭环，证明"更能检出 SDC"）

- [x] **Task 6.1 ρ_u 标定战役（per-unit SFI，N=100/单元）**
  内容: 对标定序列集（每单元定向序列 + 均衡序列）跑 per-unit SFI（harness 扩展 --structure 支持 ooo/iex/lsu/fsu/l2c_tag/l2c_data/mmu七臂——注入器全部现成：CHAOSPhysReg/CHAOSGateFU+CHAOSFUPerm/CHAOSLSQFwd+新 SQ-data/CHAOSFPU/CHAOSCache tag/data/CHAOSArmTLB-FS）；产出实测 ρ_u 表（Wilson CI）回填 YAML `rho_measured`（与初值并列报告，**不覆盖用户 override**）。
  验证: 每臂 N=100 分类分布落盘 `docs/sdc-ed/calibration-report.md`；IFU 臂实测 SDC=0（Phase 16 复现锚）；L2C tag 臂 SDC 率显著 > data 臂（39-47% vs 0% 线的复现）。
  完成（2026-09-19，实测 11 臂 × N=100：irf/intadd/intmul/lsq/l1d/fpadd/fpmul/l2c_data×{none,secded}/l2c_tag×{none,secded}；IFU/MMU 臂按预案 deferred 引用既有证据——runner 无 BPU 挂载路径、FS 镜像不可用）。L2C 2×2 复现：tag×secded 0.50 [0.3639,0.6361] vs data×secded 0.00 [0,0.0727]（CI 无重叠，分化显著）；ρ 回填 taishan-v110.yaml rho_measured 块。报告：docs/sdc-ed/calibration-report.md。附带修复 harp_eval l1d 臂输出捕获缺陷（原全部误分类 NoOutput）。commit 271425de。
- [ ] **Task 6.2 per-unit lift 主实验（ED 有效性的最终裁决）**
  内容: 三组序列各 K=10：ED-top-K（5.2 选择器）/ 均匀随机 K / legacy-fitness-top-K；每组跑全单元 SFI（N=100/单元/序列）；报告 per-unit detection lift + Wilson CI + 总检测率；AUC(ED, detection) 三组对比。
  验证（成功判据，预注册）: **ED-top-K 总检测率 > 随机组（Wilson CI 不重叠）**；per-unit 分解中 ED 预测的高优先单元（LSU/L2C-tag）的 lift 最大。若失败：分歧归因到 w/ρ/ceiling/A 各因子（每序列的预测-实测残差表），负结果如实入报告——**这是诚实性要求，不许改判据**。
  状态: **deferred（未实施）**——依赖 Task 5.2 选择器；预注册判据无从检验（ED 评分器未落地）。
- [ ] **Task 6.3 负对照与跨 CPU 迁移测试**
  内容: (a) 负对照：dead_read_seq（高 ACE 低 SDC-ACE）与 readwrite_seq（双高）各 N=100 IRF SFI——预期 dead_read 的 detection 显著低，量化「ACE 松量」为数字；(b) 迁移：为 taishan-v110 优化的 top-K 在 neoverse-n2.yaml 配置下重跑 SFI，检验 ED 排序保持性（AUC>0.5）——配置驱动有效性的架构级证明。
  验证: 两实验各出 Wilson CI 对比表入 calibration-report.md。
  状态: **deferred（未实施）**——dead_read_seq 负对照 workload 未生成；neoverse-n2 迁移臂未跑（其 YAML 大量 null 字段的迁移设计参考 Task 1.3 commit message 警告行）。

### Phase 7 — 部署模式与收尾

- [ ] **Task 7.1 部署模式检测臂（去 golden）**
  Files: `workloads/harp/` checker 变体 workload（同核复算 + 校验和自比对两种）、`tools/sfi_lift.py --checker` 模式。
  内容: 序列自身内嵌 checker（非 golden diff），度量 deployment-detection；transient（单次翻转）与 permanent（CHAOSFUPerm 全程）分臂——同核复算对 permanent 失效的预期如实记录。
  验证: (a) golden-diff 与 checker 两臂对同序列同注入的 detection 差值落盘；(b) permanent 臂同核复算 detection 显著低于校验和自比对（结构性失效实证）。
  状态: **deferred（未实施）**——deployment-detection 口径未建立，q_u 目前只有 golden-diff=1.0 基线。解锁：后续补丁。
- [x] **Task 7.2 `docs/sdc-ed/method.md` 全文定稿 + AGENT_TASKS.md 登记 + 计划勾选收尾**
  内容: 全部诚实边界汇总（taint 近似、组合逻辑权重系数、gate 网表非 RTL、MMU FS 臂依赖、ρ 置信区间）；AGENT_TASKS.md 登记新任务行；本计划全部 checkbox 勾选且每个已勾任务的验证输出可溯源（commit 哈希）。
  验证: 干净增量构建 0 错误；双回归锚（reg_chain + sample_seq）通过；push `feat/sdc-ed-eval`。
  完成口径修正（诚实边界）: 计划写「全部 checkbox 勾选」系制定时的预期——实际执行中 Phase 3.4/4.x/5.x/6.2/6.3/7.1 共 10 任务未实施（部分依赖链未解锁），按「不勾选未验证任务」的纪律保持 `[ ]` 并逐任务登记 deferred 状态与原因（见各任务行「状态」注记）。已勾 13 任务全部附 commit 哈希溯源。method.md 定稿含 §4 诚实边界三张表（预注册核实/标定新增/实施偏差）与 §7 实施状态总表（13 done / 10 deferred）。
  完成（2026-09-19）：method.md 定稿（ρ_measured 回填表/诚实边界 14 项三表/实施状态总表）+ AGENT_TASKS.md 登记 SDCED-* 24 行 + 本计划全 23 checkbox 核对（13 [x] 均附 commit 哈希，10 [ ] 均附 deferred 状态行）。验证：增量构建 scons done 0 新警告；reg_chain → f247ef3fe6f02cfd；sample_seq → SUM=17994817166615565002 CRC=8f333d15；pytest ed_profile 13/13。
  收尾修正记录（诚实边界）: 本任务写作期间 Task 2.3（9274f1e3）与 Task 3.2（7c27f2f2）并行合入——method.md/AGENT_TASKS.md 中二者的登记从「deferred 未实施」修正为 done（各含实测注记），此前草稿中的 deferred 表述系快照时序差，已在 §7 总表、§4.3 偏差表与 AGENT_TASKS 同步修正。

---

## 五、验证命令速查（每任务的回归三步共用）

```bash
# 构建（增量）
cd CHAOS/gem5 && scons build/ARM/gem5.opt -j16

# 回归锚 1（directed）
CHAOS/gem5/build/ARM/gem5.opt --silent-redirect -d /tmp/reg \
  smoke_test/configs/two_level_taishan.py \
  --binary workloads/directed/reg_chain --mode baseline
# 期望 checksum: f247ef3fe6f02cfd

# 回归锚 2（harp wrapper）
CHAOS/gem5/build/ARM/gem5.opt --silent-redirect -d /tmp/seq \
  smoke_test/configs/two_level_taishan.py \
  --binary workloads/harp/sample_seq --mode baseline
# 期望 SUM=17994817166615565002 CRC=8f333d15

# 覆盖采集（参数化后）
... --cov --cov-profile configs/cpu-profiles/taishan-v110.yaml
```

（`--silent-redirect` 等 gem5 CLI 细节以 harp_eval.py:171 现行调用为准；首个执行任务时核对并修正本速查。）

## 六、风险与诚实边界登记（执行前预注册）

| 风险 | 缓解 |
|---|---|
| gem5 重建耗时长（20-40min） | Phase 0 独立任务；后续全增量 |
| gate 差分在 IQ 热路径开销超限 | Task 4.4 预案：1/64 采样 + 记录 |
| FS 臂镜像未入库（kernel/disk 路径为本地） | MMU 标定降级为「SE 可达子集 + FS 臂 deferred 登记」，不阻塞主链 |
| ρ 标定 N=100/臂 × 7 臂 × 多序列的算力 | jobs 并行（harp_eval --jobs 16 现行）；臂间独立可断点续跑 |
| ED lift 实验失败（负结果） | 预注册判据不许改；残差归因表如实入报告——失败本身是指标改进的输入 |
| 底表转写抄录错误 | Task 1.2 的 10 字段抽查对照表 + 后续使用中随时对原文校正 |

## 七、与既有工作的关系

- **不推翻**：ACE/IBR 采集器、harp_eval SFI 协议、19 注入器全部保留——ED 是其上的加权层，legacy 模式双跑保留对照。
- **超越声明**（相对 Harpocrates 论文）：① 数据流可达的 SDC-ACE（论文无）；② per-unit ρ 标定与 ED（论文只有 coverage↔detection 相关性）；③ 配置驱动跨 CPU（论文单机）；④ 部署模式检测臂（论文 golden-diff）。
- **弱于论文的项**：无（论文 7 结构全覆盖保留 + 上述四项扩展）。
