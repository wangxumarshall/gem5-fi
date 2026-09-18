# SDC ED 评估方法——配置驱动的指令流 SDC 检测有效性评估

> 计划：`docs/superpowers/plans/2026-09-19-cpu-profile-driven-sdc-ed.md`（2026-09-19）
> 本文档是指标定义的**单一权威源**：代码注释、工具帮助文本、标定报告中的公式必须与本文逐字一致。

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

### 3.2 ρ_u 初值与推导规则

首轮初值全部来自仓库实测；Phase 6 标定战役（N=100/单元）回填 `rho_measured`（与初值并列报告，不覆盖用户 override）。

| 单元 | ρ 初值 | 出处 |
|---|---|---|
| IFU | 0.0 | Phase 16：dir_flip/target_flip/ras_flip 三预测面全 0% SDC |
| OoO | 0.05 | IRF SFI 基线（readwrite_seq detection 0.04）+ 双模式 14.8% wrong-path 差 |
| IEX | 0.05 | 门级/执行级 FU SFI 基线 |
| LSU | 0.05 | lsqfwd formal：P_SDC=4.7% [3.0,7.3] |
| FSU | 0.01（值依赖强，保守） | CHAOSFPU N=20 全 Masked |
| MMU | 0.0（SE 用户态） | addr_map_sub 384/384 Masked；FS 臂实测回填 |
| L2C | 0.45（tag-face）/ 0.0（data-face SECDED） | L2 2x2 arms：39→47% vs 47→0% |

**保护矩阵 → ρ 推导规则**（Layer C 自动化）：无保护→跑 SFI 标定臂；data-SECDED→data-face ρ=0、tag/逻辑面保留；parity(SED)→单 bit 检、双 bit 漏（按双位条件概率折算）。

### 3.3 A_u 采集定义（per-unit）

| 单元 | A_u 定义 | 数据源 |
|---|---|---|
| IFU | 预测器状态覆盖 | CHAOSBPU 基建；**SDC 轴 ρ=0，只进 Crash 轴** |
| OoO | ROB 占用带覆盖 × rename 距离分布 | commit.cc tick + PrfRegState birth/last_read |
| IEX | IBR × 门级敏感位覆盖 | inst_queue.cc + CHAOSGateFU 网表差分 |
| LSU | sqAvf（per-slot 精确）+ 前转覆盖比 + load-use 距离 | lsq_unit.cc |
| FSU | IBR(FP) × FP 值类熵 | inst_queue.cc issue 点值类采样 |
| MMU | TLB 条目/页大小多样性 | FS 臂（SE 用户态封顶 ≈0.2×FS 可达） |
| L2C | block-ACE data-face/tag-face 双账本 | mem/cache/base.cc + targetCache 列表化 |

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

## 4. 诚实边界（预注册，随结果更新）

| # | 边界 | 说明 |
|---|---|---|
| 1 | SDC-taint 是「epilogue 可达性」近似 | 不追值依赖控制流；与完整程序切片的差距由 Phase 6 负对照量化 |
| 2 | 组合逻辑翻转份额按 1/3 SRAM 权重折算 | 系数是文献级先验，进 residuals 声明 |
| 3 | gate 网表是合成模型非真实 RTL | Kogge-Stone 1154 门 + 移位加 44418 门（已三层等值验证）；GeFIN RTL 不可得 |
| 4 | MMU ρ 依赖 FS 臂 | kernel/disk 镜像未入库时降级为 SE 可达子集 + deferred 登记 |
| 5 | ρ 置信区间 | N=100/臂 Wilson CI；区间宽的单元 ED 权重附区间而非点值 |
| 6 | ceiling_u 是可达性工程判断 | MMU≈0.2×（384/384 Masked 佐证）；IFU SDC 轴=0（Phase 16）；每个 ceiling 附依据 |
| 7 | ED lift 实验若失败 | 预注册判据不许改；残差归因表如实入报告 |

## 5. 与既有工作的关系

- **不推翻**：ACE/IBR 采集器、harp_eval SFI 协议、19 注入器全部保留——ED 是其上的加权层，legacy 模式双跑对照。
- **相对 Harpocrates 论文的超越**：① 数据流可达 SDC-ACE；② per-unit ρ 标定与 ED；③ 配置驱动跨 CPU；④ 部署模式检测臂。
- 相对论文弱于的项：无（7 结构覆盖保留 + 四项扩展）。

## 6. 工具链

```
configs/cpu-profiles/*.yaml    声明式 CPU 描述（Layer C）
tools/ed_profile.py            YAML 解析 + w/ceiling 推导
tools/ed_score.py              ED 计算 + per-unit 报告 + 次模选择
tools/sfi_lift.py              per-unit lift 战役 + Wilson CI + AUC
configs/se/profile_taishan.py  --profile 入口（描述驱动实例化）
CHAOSCov                       采集器（分母参数化 + SDC-ACE 账本）
```
