# SDC ED 评估方法——配置驱动的指令流 SDC 检测有效性评估

> 计划：`docs/superpowers/plans/2026-09-19-cpu-profile-driven-sdc-ed.md`（2026-09-19）
> 本文档是指标定义的**单一权威源**：代码注释、工具帮助文本、标定报告中的公式必须与本文逐字一致。
> **定稿状态（2026-09-19，Task 7.2）**：本文按计划执行到 Phase 6.1（ρ_u 标定）、2.3（covUnits
> 归并）与 3.2（FSU 值类剖面）后定稿。已落地：Layer C 三份 CPU 描述 + 解析库、Layer A 分母
> 参数化 + covUnits 7 维向量 + LSU/FSU/L2C 采集升级、ρ_u 11 臂实测回填。deferred：次模选择
> 与 ED 评分器（Phase 5）、lift 主实验（Phase 6.2/6.3）、部署臂（Phase 7.1）等 10 任务——
> 全部按 §7 实施状态表与 §4 诚实边界如实登记，未做的不粉饰为已做。

## 1. 背景与动机

现有 Harpocrates 复现（`docs/harpocrates/method.md`）用 ACE/IBR 度量指令序列的微架构结构覆盖，作为 SDC 检测能力的代理指标。该代理有四个已实证的结构性松量：

1. **读 ≠ 传播到校验输出**：ACE 区间在「被读」时延伸，但被读的值可能进入死计算（乘零丢弃）、别名到同 cache 行（低位地址位）、或只消费向量高 lane 的一部分——ACE 记账、检测为 0。
2. **均匀 bit 显著性**：每结构一个 AVF 标量隐含「所有 bit 等权」，但仓库实测证伪（地址位 vs 数据位、FP 指数 vs 尾数、L2 tag 合法别名域 ECC 盲 39→47%）。
3. **与故障模型脱钩**：IFU 三预测面 0% SDC（squash 自愈，Phase 16）——覆盖率 66% 对 SDC 检测的边际贡献结构性为零。
4. **无 checker 概念**：golden-diff 是理想 checker；部署态校验逻辑分辨能力各异。

**ED（Expected Detection，期望 SDC 检测率）** 是按真实故障分布加权的检测期望，把这四个松量显式建模为权重因子。

## 2. 三层架构

```
Layer A（架构根基，CPU 无关）  单元化结构覆盖模型
   7 单元分解（IFU/OoO/IEX/LSU/FSU/MMU/L2C）+ 采集器协议（A_u 测量方法）
   + ED 评分器（Σ w·ρ·q·A 与次模选择算法）
   不变量：不假设任何具体 CPU 的参数——换 CPU 配置文件，Layer A 代码零改动。
Layer B（实例化，CPU 相关）    权重与先验
   w_u（翻转份额）· ρ_u（SDC 转化率）· ceiling_u（可达性上限）· q_u（checker 可观测率）
   全部由 CPU 描述推导或 SFI 标定回填，代码零硬编码。
Layer C（用户接口）            声明式 CPU 描述（YAML 单一事实源）
   一份描述 → 四消费者：① gem5 实例化 ② CHAOSCov 分母参数化
   ③ ρ_u 初值推导（保护矩阵→臂选择规则）④ w_u 位容量推导
```

用户换一份 YAML，得到的是为那颗 CPU 的翻转物理和保护矩阵量身定制的评估权重与序列筛选结果。产出物是 `(cpu_profile, instruction_stream)` 对，而非通用序列。

## 3. 指标定义

### 3.1 ED 主公式

```
ED(S) = Σ_{u∈units}  w_u · ρ_u · q_u · A_u(S)

w_u     单元 u 的翻转份额 = bits(u) / Σ bits(所有单元)（SRAM 主导，YAML 推导）
ρ_u     单元 u 的 SDC 转化率 = P(激活故障 → SDC)（SFI 战役标定回填）
q_u     checker 可观测率 = P(输出偏离 → 被 checker 分辨)（golden-diff=1.0；部署臂<1）
A_u(S)  序列 S 对单元 u 的激活覆盖（0~1，采集器实测，§3.3）
ceiling_u  可达性上限；有效覆盖 A'_u(S) = min(A_u(S), ceiling_u)
```

**双报告义务**：per-unit 7 维分解（诊断）+ 总分 ED（排序）。任何决策记录必须附分解，禁止只引标量。

**退化自检**：ρ 全 1、w 均匀时 ED ≡ 平均 A_u（评分器单元测试的一致性断言）。

### 3.2 ρ_u 初值、推导规则与实测回填

首轮初值全部来自仓库实测；Phase 6.1 标定战役（11 臂 × N=100，2026-09-19）已回填 `rho_measured`（与初值并列报告，不覆盖用户 override）。完整战役设计与六类分布见 `docs/sdc-ed/calibration-report.md`。

初值表（Layer B 首轮，标定前）：

| 单元 | ρ 初值 | 出处 |
|---|---|---|
| IFU | 0.0 | Phase 16：dir_flip/target_flip/ras_flip 三预测面全 0% SDC |
| OoO | 0.05 | IRF SFI 基线（readwrite_seq detection 0.04）+ 双模式 14.8% wrong-path 差 |
| IEX | 0.05 | 门级/执行级 FU SFI 基线 |
| LSU | 0.05 | lsqfwd formal：P_SDC=4.7% [3.0,7.3] |
| FSU | 0.01（值依赖强，保守） | CHAOSFPU N=20 全 Masked |
| MMU | 0.0（SE 用户态） | addr_map_sub 384/384 Masked；FS 臂实测回填 |
| L2C | 0.45（tag-face）/ 0.0（data-face SECDED） | L2 2x2 arms：39→47% vs 47→0% |

**实测回填表（Task 6.1，taishan-v110，口径 = detection | active = (SDC+Crash)/(N−Inactive−SimErr)，Wilson 95% CI）**：

| 单元 | ρ_measured | Wilson 95% CI | 臂（序列） | 与初值的关系 |
|---|---|---|---|---|
| IFU | 0.00 | —（引用） | deferred：引用 Phase 16 三面 0% | 一致 |
| OoO | 0.05 | [0.0215, 0.1118] | irf × readwrite_seq | 与初值一致（5/100 全 Crash） |
| IEX | 1.00 / 0.82 | [0.9630, 1.0000] / [0.7219, 0.8835] | intadd / intmul × sample_seq | **远超初值**——permanent FU-mask 协议语义（上界），非单次翻转（§4 边界 8） |
| LSU | 0.69 / 0.04 | [0.5937, 0.7722] / [0.0158, 0.0993] | lsq × rand_mem / l1d × rand_mem | 前转通路与数据面分化 >17× |
| FSU | 0.00 | [0.0000, 0.0370] | fpadd+fpmul × rand_fp（N=200） | 200/200 全 Masked；值依赖条件值（非物理免疫） |
| MMU | 0.00 | —（引用） | deferred：引用 addrmap 384/384 Masked | 一致；FS 臂不可用 |
| L2C | 0.50（tag）/ 0.41（data-none）/ 0.00（data-secded） | [0.3639, 0.6361] / [0.2822, 0.5475] / [0, 0.0727] | l2c_{tag,data} × stencil_5pt_kernel | 2×2 复现：tag×secded vs data×secded **CI 无重叠**（ECC 对合法 tag 别名结构性失明） |

**保护矩阵 → ρ 推导规则**（Layer C 自动化）：无保护→跑 SFI 标定臂；data-SECDED→data-face ρ=0、tag/逻辑面保留；parity(SED)→单 bit 检、双 bit 漏（按双位条件概率折算）。2×2 验证臂（l2c data/tag × none/secded）已实证该规则：data-face 单 bit 被 SECDED 全纠（0.00），tag-face 合法别名零 syndrome、ρ 纹丝不动（0.50）。

### 3.3 A_u 采集定义（per-unit）

各单元 A_u 经 `harp.covUnits` 7 维向量归并输出（Task 2.3，commit 9274f1e3：
OoO=irfAvf、IEX=max(ibrIntAdd,ibrIntMul)、LSU=sqAvf、FSU=max(ibrFpAdd,ibrFpMul)、
L2C=max(l1dAvf,l2cAvf)、IFU/MMU=0 占位），供 ed_score.py 消费。

| 单元 | A_u 定义 | 数据源 | 实施状态 |
|---|---|---|---|
| IFU | 预测器状态覆盖 | CHAOSBPU 基建；**SDC 轴 ρ=0，只进 Crash 轴** | deferred（runner 无 BPU 挂载路径；ρ=0 已由既有证据钉死） |
| OoO | ROB 占用带覆盖 × rename 距离分布 | commit.cc tick + PrfRegState birth/last_read | **已落地**（Task 3.4：renameDist 17 桶直方图 + robOccBands 8 带直方图；irfAvf 分量已进 covUnits） |
| IEX | IBR × 门级敏感位覆盖 | inst_queue.cc + CHAOSGateFU 网表差分 | IBR 已进 covUnits（Task 2.1/2.3）；门级差分臂 deferred（Task 4.3） |
| LSU | sqAvf（per-slot 精确）+ 前转覆盖比 + load-use 距离 | lsq_unit.cc | **已落地**（Task 3.1：per-slot 前转/写回双账本 + load-use 直方图；sqAvf 进 covUnits） |
| FSU | IBR(FP) × FP 值类熵 | inst_queue.cc issue 点值类采样 | **已落地**（Task 3.2：issue 点读 PRF 源值，Float/VecElem 标量 1 lane、Vec blob 2 lane，IEEE754 五类直方图 + 归一化熵 `fpValueHist/fpValueEntropy`；IBR(FP) 已进 covUnits） |
| MMU | TLB 条目/页大小多样性 | FS 臂（SE 用户态封顶 ≈0.2×FS 可达） | deferred（FS 镜像未入库，计划 §六预案）；covUnits 占位 0 |
| L2C | block-ACE data-face/tag-face 双账本 | mem/cache/base.cc + targetCache 列表化 | **已落地**（Task 2.2 L1D+L2 双账本 + Task 3.3 tag-face 账本；max(l1d,l2c) 进 covUnits） |

### 3.4 SDC-ACE（bit-array 结构的 A_u 分量升级）

```
SDC-ACE 区间 = [write, last_read_on_path_to_checkable_output)
gap 指标     = (ACE − SDC-ACE) / ACE   （序列设计缺陷证据，喂 advice 引擎）
```

读事件在「校验输出可达集」（harp_wrap epilogue 生成的 `.reach.json` 静态清单）内 → 双计（ACE + SDC-ACE）；可达集外 → 仅 ACE。

### 3.5 序列集选择（次模）

```
选序列集 T: maximize Σ_u w_u·ρ_u·q_u · [1 − Π_{S∈T}(1 − A_u(S))]
约束: per-unit 配额 ∝ w_u·ρ_u·gap_u，gap_u = ceiling_u − A_u
```

贪心边际增益选择，避免在已饱和单元堆叠（单标量 fitness 的已知失败模式）。

### 3.6 部署模式（去 golden）

```
deployment-detection = P(故障 → 在线 checker 报警)（无 golden 对照）
checker 候选：同核复算（时间冗余，transient）/ 校验和自比对（permanent 可用）
```

与 golden-diff 的差值衡量序列在真实部署环境的检测能力。

## 4. 诚实边界（定稿汇总——预注册项随执行结果更新，实施偏差逐项登记）

### 4.1 预注册边界（计划时登记，执行后核实）

| # | 边界 | 说明 | 执行后状态 |
|---|---|---|---|
| 1 | SDC-taint 是「epilogue 可达性」近似 | 不追值依赖控制流；与完整程序切片的差距由负对照量化 | **未触及**——Task 4.1/4.2（SDC-ACE 账本）deferred，本边界目前是纯设计声明 |
| 2 | 组合逻辑翻转份额按 1/3 SRAM 权重折算 | 系数是文献级先验，进 residuals 声明 | 生效中（ed_profile.py COMBINATIONAL_WEIGHT，三份 YAML residuals 自动附加） |
| 3 | gate 网表是合成模型非真实 RTL | Kogge-Stone 1154 门 + 移位加 44418 门（已三层等值验证）；GeFIN RTL 不可得 | 生效中；gate 差分覆盖臂（Task 4.3）deferred，网表仅用于既有注入器 |
| 4 | MMU ρ 依赖 FS 臂 | kernel/disk 镜像未入库时降级为 SE 可达子集 + deferred 登记 | **按预案触发**——FS 镜像不可用，ρ_MMU=0.00（SE）引用 addrmap 384/384 Masked，FS 臂 deferred |
| 5 | ρ 置信区间 | N=100/臂 Wilson CI；区间宽的单元 ED 权重附区间而非点值 | 已生效——11 臂 CI 全部落盘（calibration-report.md §2/§3，YAML rho_measured 逐条附 CI） |
| 6 | ceiling_u 是可达性工程判断 | MMU≈0.2×（384/384 Masked 佐证）；IFU SDC 轴=0（Phase 16）；每个 ceiling 附依据 | 生效中（ed_profile.py DEFAULT_CEILINGS + YAML 显式化留痕） |
| 7 | ED lift 实验若失败 | 预注册判据不许改；残差归因表如实入报告 | **未触及**——Task 6.2 lift 主实验 deferred，判据无从检验 |

### 4.2 执行中新增的边界（标定战役实测发现，calibration-report.md §4 全文）

| # | 边界 | 说明 |
|---|---|---|
| 8 | IEX ρ=1.00/0.82 是 permanent-FU 协议语义 | CHAOSFUPerm 自 first_clock 持续施加同一 mask——测得的是「该指令类在 checksum 路径上的暴露度」上界，非 transient 单 bit SDC 转化率（transient 既有证据是阴性对照 t3-2-exec-negative 全 Masked）。IEX 的 ρ 应理解为该协议下的上界语义 |
| 9 | 非 L2C 单元 detection 几乎全由 Crash 承担 | irf/intadd/intmul/lsq/l1d 五臂 SDC 计数全部为 0（detected 结局均为 Page-table-fault Crash）。严格 SDC 口径下这些单元 ρ≈0（上界 3.7-4.7%）；回填取 detection 口径（Crash 同样是检出）且与初值表口径一致——口径选择已在 calibration-report §1.2 申明 |
| 10 | ρ_u 是「单元×序列」联合属性，非单元常数 | lsq 臂 rand_mem 69% Crash 而既有 lsq-matrix 战役（fp_fwd_kernel）bitflip 100% SDC——前转值喂地址计算则 Crash、喂算术-校验和则 SDC。跨序列迁移未量化（Task 6.3 deferred） |
| 11 | FSU 0% 是标定序列族的条件值 | rand_fp 的 FP 值域落在掩蔽区；既有 formal（t3-1，n=384×16）显示 float 60-66% vs double 14-18% 高度值依赖。ρ_FSU=0.00 非 FSU 物理免疫 |
| 12 | L2C 臂 Inactive 过半 | 随机块采样下 51-52% run 故障未落地（L2 驻留活数据稀疏 + tag 臂无 alias 候选 SKIPPED）；ρ 取条件口径（\| active）。SKIPPED 行已从注入计数剔除 |
| 13 | 工具缺陷修复的连带影响 | harp_eval.py l1d 臂原 gem5 命令带 --quiet 无重定向 → simout.txt 从不生成 → 注入 run 全部误分类 NoOutput（N=2 探针实测复现）。Task 6.1 顺带修复（-r -e --silent-redirect）；此前任何 l1d 臂结论若引用须重验 |
| 14 | 全部速率为 gem5 O3（TaiShan v110 实配）条件概率 | 非产品 FIT；golden-diff oracle（q=1 基线）；单机未复现（single-machine, unconfirmed） |

### 4.3 实施与计划的偏差登记（deferred 项的如实清单）

以下任务在计划中定义、截至定稿未实施（原因如实登记，**不粉饰为已做**）：

| 计划任务 | 内容 | 状态与原因 |
|---|---|---|
| 3.4 | OoO rename 距离分布 + ROB 占用带细化 | **已实施**（2026-09-19：`harp.renameDist` 17 桶 write→首读距离直方图（irfOnRead 区间关闭点采样）+ `harp.robOccBands` 8 带占用直方图（commit tick 经 robAccess() 读 numInstsInROB）；方向验证 sample_seq 86% 样本在 0-12% 带 vs readwrite_seq 铺至 25-37% 带） |
| 4.1/4.2 | epilogue 可达集 + SDC-ACE 三账本 + gap 指标 | deferred——未实施；**这是「核心超越点」中未落地的那一半**：ED 目前消费裸 ACE 账本，SDC-ACE 的松量量化（dead_read 负对照）未做 |
| 4.3 | gate 级敏感覆盖臂（IEX 门级位图） | deferred——未实施；含 1/64 采样降级预案未触发（未开工） |
| 5.1/5.2/5.3 | ed_score.py + 次模选择器 + harp_evolve fitness 替换 | deferred——未实施；**ED 评分器未落地**，ED 公式目前只在本文件与 ed_profile.py 的 w/ρ/ceiling 推导中定义，无端到端评分工具 |
| 6.2 | per-unit lift 主实验（ED 有效性最终裁决） | deferred——未实施；ED-top-K vs 随机 vs legacy 的预注册判据无从检验（依赖 5.1/5.2） |
| 6.3 | 负对照（dead_read_seq）+ 跨 CPU 迁移测试 | deferred——未实施；dead_read_seq.S workload 未生成；neoverse-n2 迁移臂未跑 |
| 7.1 | 部署模式检测臂（去 golden，checker 内嵌） | deferred——未实施；deployment-detection 口径未建立，q_u 目前只有 golden-diff=1.0 基线 |

## 5. 与既有工作的关系

- **不推翻**：ACE/IBR 采集器、harp_eval SFI 协议、19 注入器全部保留——ED 是其上的加权层，legacy 模式双跑对照。
- **相对 Harpocrates 论文的预期超越**（定稿时点状态如实标注）：
  ① 数据流可达 SDC-ACE——**设计完成，实施 deferred**（Task 4.1/4.2）；
  ② per-unit ρ 标定——**已落地**（Task 6.1，11 臂 × N=100，calibration-report.md）；ED 评分器本体 deferred（Task 5.1）；
  ③ 配置驱动跨 CPU——**Layer C 描述与实例化入口已落地**（三份 YAML + profile_taishan.py + CHAOSCov 参数化）；跨 CPU 迁移验证 deferred（Task 6.3）；
  ④ 部署模式检测臂——**deferred**（Task 7.1）。
- 相对论文弱于的项：定稿时点无（7 结构覆盖保留）；超越声明中 ①④ 尚未兑现为代码与数据，上表即差距清单。

## 6. 工具链（定稿时点实存状态）

```
configs/cpu-profiles/*.yaml    声明式 CPU 描述（Layer C）——已入库（三份 + schema.md）
tools/ed_profile.py            YAML 解析 + w/ceiling/ρ初值 推导——已入库（pytest 13/13）
configs/se/profile_taishan.py  --profile 入口（描述驱动实例化）——已入库
CHAOSCov                       采集器——已升级（IBR 分母参数化 / targetCache 列表化
                               L1D+L2 双账本 / SQ per-slot 前转+写回账本 + load-use
                               距离 / L2C tag-face 账本 / **covUnits 7 维单元向量**
                               ——IFU/MMU 占位（ρ 轴定义）、OoO=irfAvf、IEX=max
                               (ibrIntAdd,ibrIntMul)、LSU=sqAvf、FSU=max(ibrFpAdd,
                               ibrFpMul)、L2C=max(l1dAvf,l2cAvf)，ed_score.py 消费）
tools/harp_eval.py             SFI harness——已扩展（l2c_data/l2c_tag 双面臂 +
                               --protection + 六类分类 + l1d 输出捕获修复）
tools/ed_score.py              ED 计算 + per-unit 报告 + 次模选择——deferred（Task 5.1/5.2）
tools/sfi_lift.py              per-unit lift 战役 + Wilson CI + AUC——deferred（Task 6.2）
```

## 7. 实施状态总表（定稿快照，2026-09-19）

计划实定义 23 任务（0.1-7.2；计划标题写「22 任务」系制定时计数笔误，以 checkbox 清单为准）：
**13 done / 10 deferred**。逐任务 commit 溯源见
`docs/superpowers/plans/2026-09-19-cpu-profile-driven-sdc-ed.md` 勾选注记与 AGENT_TASKS.md。

| Phase | 任务 | 状态 |
|---|---|---|
| 0 | 0.1 构建+双锚 / 0.2 method 骨架 | done |
| 1 | 1.1 ed_profile / 1.2 三 YAML / 1.3 --profile 入口 | done |
| 2 | 2.1 IBR 参数化 / 2.2 targetCache 列表化 / 2.3 per-unit 7 维归并 | done |
| 3 | 3.1 LSU per-slot+load-use / 3.2 FSU 值类剖面 / 3.3 L2C 双面账本 | done |
| 3 | 3.4 rename 距离 | deferred |
| 4 | 4.1 可达集 / 4.2 SDC-ACE / 4.3 gate 臂 | deferred |
| 5 | 5.1 ed_score / 5.2 次模选择 / 5.3 evolve 替换 | deferred |
| 6 | 6.1 ρ 标定战役（11 臂） | done |
| 6 | 6.2 lift 主实验 / 6.3 负对照+迁移 | deferred |
| 7 | 7.1 部署臂 | deferred |
| 7 | 7.2 本定稿 + 登记 + 收尾 | done |
