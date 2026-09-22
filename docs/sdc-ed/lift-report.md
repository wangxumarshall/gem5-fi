# SDC-ED Lift 主实验报告（Task 6.2 + 6.3 + 7.1，2026-09-19）

> 数据：`artifacts/sdc-ed-lift/harp-eval-<arm>-<seq>/summary.md`
> 协议：ED-top-3（readwrite/longlive/overwrite，Task 5.2 选择器输出）vs
> random-3（dead_read/sample/rand_mem，seed 20260919 抽样）×
> {IRF, LSU} 两注入臂 × N=50/臂（jobs=16）。
> 预注册判据（计划 Task 6.2，不许改）：ED-top-K 总检测率 > 随机组
> （Wilson CI 不重叠）。

## 1. 主结果：预注册判据未达成（负结果，如实报告）

| 组 | IRF 臂 | LSU 臂 |
|---|---|---|
| ED-top-3 | 4/150 = 0.0267 [0.0104, 0.0666] | 108/150 = 0.7200 [0.6433, 0.7857] |
| random-3 | 8/150 = 0.0533 [0.0273, 0.1017] | 108/150 = 0.7200 [0.6433, 0.7857] |

- IRF 臂：方向与判据相反（random > ED-top），但两组 CI 大量重叠
  ——**差异无统计学意义，判据失败的首要归因是统计功效不足**。
- LSU 臂：两组完全相同 0.72——lsq_fwd 注入器对任何含 store 的序列
  等概率命中（每序列 36/50 Crash），**该臂对序列差异无区分度**
  （注入器特性：store 地址/数据随机化覆盖，序列无关）。

## 2. 残差归因表（per-sequence）

| ED rank | 序列 | IRF detection | 归因 |
|---|---|---|---|
| 1 | readwrite | 2/50 | ED 最高但检测居中——ED 的 OoO 轴贡献被 w·ρ 缩放（0.0036）|
| 2-3 | longlive/overwrite | 1/50 | 同上；三者的 ED 差异 0.0007 在 SDC 噪声下不可分辨 |
| 4 | rand_mem | 2/50 | — |
| 7-8 | sample/dead_read | 3/50 | **方向正确**：ED 最低组检测最高——但 1-3/50 = 0.02-0.06 的极差全部落在 N=50 的 Wilson CI 噪声内（±0.06）|

**功效预算**（预注册给后续实验的样本量要求）：per-sequence detection
~0.04 量级下，要分辨 ED 序间预测差（~2 倍）需 N≥400/序列
（Wilson CI 半宽 < 0.02）；ED-top vs random 的组级比较需 ≥6 序列/组。

## 3. ED-AUC 相关性（6.2 副判据）

6 个实测序列的 ED 值 vs IRF detection：ED rank 1-4 组均值 1.5/50，
rank 7-8 组 3/50——**负相关方向**（ED 高检测低）。诚实解释：当前
库存池的 ED 差异主要由 OoO 轴（w·ρ=0.0036，微权重）驱动，而 IRF
注入臂实测的 detection 由「物理寄存器活跃度 × 消费路径」决定——
两者在本池上脱钩。**ED 的主导 gap（L2C，quota 0.236）无对应注入臂
参与本实验**（l2c 臂需 CHAOSCache 挂载，本实验未跑）——这是实验
设计的已知缺口，不是 ED 定义缺陷。

## 4. 负对照与跨 CPU（Task 6.3）

### 6.3a ACE 松量的检测率量化（IRF 臂直接对比）

| 序列 | irfAvf（裸 ACE）| irfAvfSdc（SDC-ACE）| IRF detection |
|---|---|---|---|
| readwrite（链直达存回） | 0.026969 | 0.050213* | 0.0400 |
| dead_read（读喂死链） | 0.018675 | 0.015105 | 0.0600 |

*commit 流口径（irfAvfCommit 0.053536 的 SDC 子集）。

裸 ACE 差（readwrite > dead_read 1.44 倍）与 detection 差方向相反
（dead_read 0.06 > readwrite 0.04）——**N=50 下同样不显著**，但
SDC-ACE 差（3.3 倍）与 detection 差同向缩小。结论：ACE 松量在
检测率上的量化需要 N≥400（同 §2 功效预算）。

### 6.3b 跨 CPU 迁移（配置驱动的架构级证明）

10 序列在 taishan-v110 vs neoverse-n2 两份 profile 下的 ED 排序
Spearman ρ = **0.8182**（n=10，> 0.5 判据通过）。配置差异直接可见：
- mul_seq ED 从 0.000151 → 0.000013（11 倍差）：N2 的 FU 字段未披露
  → w_IEX 点估计低——**ED 对披露不确定性的敏感性是特性不是缺陷**
  （报告侧 uncertainty 区间已带）
- rand_mem 在 N2 下反超 longlive/overwrite（L2C w 0.7055 > TS 0.5251
  ——N2 的 SECDED 保护矩阵 + 更大 L2 位面）

## 5. 部署模式检测臂（Task 7.1）

checker wrapper（`harp_wrap --checker`）：核心序列跑两遍（影子通道
g_reg2/mem2 同种子同初值），epilogue 自比对输出 CHECKER=OK/FAIL——
无 golden 的 deployment-detection。

- 基线验证：本机（--no-m5ops）与 gem5（m5ops）CHECKER=OK 且
  SUM1==SUM2==基线 golden SUM ✓
- readwrite_seq + CHAOSPhysReg 随机注入（ROI 对齐窗口，N=20）：
  **deployment-detection = 2/20 = 0.10**
- 对照 golden-diff（Task 6.1 标定臂，全程序采样）：0.05（N=100）
- **协议差异如实登记**：checker 扫描的 first-clock 集中在 ROI 活跃
  中段（630k-636k cycle），golden 标定臂跨全程序均匀采样（含非
  活跃期稀释）——两臂 2 倍差主要来自采样协议而非 checker 强度；
  严格比较需统一采样窗口后重跑（后续工作）
- 同核复算对 permanent 的结构性弱点（两次执行走同一 FU 同腐蚀）
  未在本轮量化（CHAOSFUPerm 臂未跑）——登记为 deferred

## 6. 结论与后续

1. **预注册 lift 判据未达成**——归因：功效不足（N=50）+ 库存池 ED
   差异由微权重轴驱动 + L2C 主导 gap 无注入臂。负结果如实入档。
2. 后续（按杠杆排序）：① evolve 生成 ED-gap 定向序列（L2C/LSU 轴
   拉开 ED 差）后重跑 lift；② N≥400/臂的功效预算；③ l2c 注入臂
   加入 lift 协议；④ checker/golden 统一采样窗口的严格比较。
