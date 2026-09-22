# ρ_u 标定战役报告（Task 6.1）— taishan-v110

> 生成：2026-09-19。工具：`tools/harp_eval.py`（本次任务扩展 l2c_data/l2c_tag
> 双面臂 + 六类分类 + l1d 输出捕获修复）。产物目录：
> `artifacts/sdc-ed-calib/harp-eval-<arm>-<seq>/summary.md`（11 臂，N=100/臂，
> jobs=16，master seed 20260916；secded 臂另跑）。
> 全部 gem5 run 约 1100 次（11×100 注入 + 11 golden + 探针），wall-clock
> 约 35 分钟（jobs=16，未超 60 分钟预算，未降 N）。

## 1. 战役设计

### 1.1 单元 → SFI 臂映射（Task 6.1 任务定义）

| 单元 | 臂（--structure） | 注入器 | 标定序列 | N | 状态 |
|---|---|---|---|---|---|
| OoO | irf | CHAOSPhysReg（phys 定向，随机 physIdx 0-124 + 随机 bit + ROI 窗随机 cycle，transient 单 bit） | readwrite_seq（写后读链，高 IRF 暴露） | 100 | 本役实测 |
| IEX-int | intadd | CHAOSFUPerm（IntAlu 类，随机单 bit mask，permanent 自 first_clock） | sample_seq（int 混合） | 100 | 本役实测 |
| IEX-mul | intmul | CHAOSFUPerm（IntMult 类） | sample_seq | 100 | 本役实测 |
| LSU | lsq | CHAOSLSQFwd（store→load 前转通路，transient 单 bit） | rand_mem（load/store 密集，含同址前转） | 100 | 本役实测 |
| LSU-L1D 面 | l1d | CHAOSCache（l1d data-face，随机块+随机字节，transient 单 bit） | rand_mem | 100 | 本役实测 |
| FSU-add | fpadd | CHAOSFPU（FloatAdd 类写回，随机单 bit mask） | rand_fp（fp 密集） | 100 | 本役实测 |
| FSU-mul | fpmul | CHAOSFPU（FloatMult 类） | rand_fp | 100 | 本役实测 |
| L2C data 面 | l2c_data | CHAOSCache（--target l2 --target_field data） | stencil_5pt_kernel（400KB 工作集 L2-heavy；战役资产恢复） | 100 | 本役实测 |
| L2C tag 面 | l2c_tag | CHAOSCache（--target l2 --target_field tag，false-hit 别名形） | stencil_5pt_kernel | 100 | 本役实测 |
| L2C data×secded | l2c_data --protection secded | 同上 + protectionModel=secded | stencil_5pt_kernel | 100 | 本役实测（2×2 验证臂） |
| L2C tag×secded | l2c_tag --protection secded | 同上 | stencil_5pt_kernel | 100 | 本役实测（2×2 验证臂） |
| IFU | — | CHAOSBPU/CHAOSRAS 资产存在，但 runner（two_level_taishan.py）无 BPU 注入挂载路径（BAC::predict hook 仅 decoupledFrontEnd 模式，SimpleBoard 不兼容，见 arm_chaos.py §S8-4 注释） | — | — | **deferred**：引用 Phase 16 三面 0% 既有证据 |
| MMU | — | CHAOSArmTLB 为 FS-only；SE runner 无法驱动（runner.py 明示 exit） | — | — | **deferred**：引用 SE 侧 384/384 Masked 既有证据；FS 臂镜像不可用（计划 §六预案） |

### 1.2 分类口径

classify.py §9.1 六类：**SimulatorError / Hang / Crash / Inactive / Masked / SDC**。
- detection（论文口径）= (SDC + Crash)/N；
- detection | active = (SDC + Crash)/(N − Inactive − SimulatorError)（条件口径，
  剔除「故障未落地」与「工具坏」两类非有效结局）；
- ρ_u 回填值 = **detection | active**（与 §1.6 初值表的口径一致——初值表的
  「OoO 0.05 ← readwrite_seq detection 0.04」即 detection 口径；ED 的
  ρ·q 乘积在 golden-diff（q=1）下即 detection 概率）。每单元的
  SDC/Crash 拆分在下表如实并列（SDC-only 口径对多数单元为 0，见 §4 发现）。

## 2. 实测结果（11 臂 × N=100）

| 臂 | golden | detection (SDC+Crash)/N | Wilson 95% CI | detection \| active | 六类分布（SDC/Crash/Hang/Masked/Inactive/SimErr） |
|---|---|---|---|---|---|
| irf × readwrite_seq | SUM=3682923676342812808 CRC=8f333d15 | (0+5)/100 = **0.0500** | [0.0215, 0.1118] | 0.0500 [0.0215, 0.1118] | 0/5/0/95/0/0 |
| intadd × sample_seq | SUM=17994817166615565002 CRC=8f333d15 | (0+100)/100 = **1.0000** | [0.9630, 1.0000] | 1.0000 [0.9630, 1.0000] | 0/100/0/0/0/0 |
| intmul × sample_seq | 同上 | (0+71)/100 = **0.7100** | [0.6146, 0.7899] | 0.8161 [0.7219, 0.8835] | 0/71/16/0/0/13 |
| lsq × rand_mem | SUM=6686586968532386500 CRC=8525e1e3 | (0+69)/100 = **0.6900** | [0.5937, 0.7722] | 0.6900 [0.5937, 0.7722] | 0/69/0/31/0/0 |
| l1d × rand_mem | 同上 | (0+4)/100 = **0.0400** | [0.0157, 0.0984] | 0.0404 [0.0158, 0.0993] | 0/4/0/95/0/1 |
| fpadd × rand_fp | SUM=15693161701610300260 CRC=938707ee | (0+0)/100 = **0.0000** | [0.0000, 0.0370] | 0.0000 [0.0000, 0.0370] | 0/0/0/100/0/0 |
| fpmul × rand_fp | 同上 | (0+0)/100 = **0.0000** | [0.0000, 0.0370] | 0.0000 [0.0000, 0.0370] | 0/0/0/100/0/0 |
| l2c_data × stencil | FINAL=6216d7bd62318f00 | (20+0)/100 = **0.2000** | [0.1334, 0.2888] | 0.4082 [0.2822, 0.5475] | 20/0/0/29/51/0 |
| l2c_tag × stencil | 同上 | (24+0)/100 = **0.2400** | [0.1669, 0.3323] | 0.5000 [0.3639, 0.6361] | 24/0/0/24/52/0 |
| l2c_data × stencil × **secded** | 同上 | (0+0)/100 = **0.0000** | [0.0000, 0.0370] | 0.0000 [0.0000, 0.0727] | 0/0/0/49/51/0 |
| l2c_tag × stencil × **secded** | 同上 | (24+0)/100 = **0.2400** | [0.1669, 0.3323] | 0.5000 [0.3639, 0.6361] | 24/0/0/24/52/0 |

### 2.1 L2C 2×2（field × protection）验证

| target_field | protection | P_SDC（全分母） | P_SDC \| active | 复现锚（Phase 14，commit 23d766f） |
|---|---|---|---|---|
| data | none | 0.20 [0.1334, 0.2888] | 0.4082 [0.2822, 0.5475] | 47.0% [37.5,56.7]（n=100 定向块） |
| data | secded | **0.00** [0.0000, 0.0370] | **0.00** [0.0000, 0.0727] | 0.0% [0,3.7]（SECDED 全纠） |
| tag | none | 0.24 [0.1669, 0.3323] | 0.5000 [0.3639, 0.6361] | 38.9% [29.8,49.0] |
| tag | secded | **0.24** [0.1669, 0.3323] | **0.50** [0.3639, 0.6361] | 47.0% [37.5,56.7]（ECC 盲） |

**验证判据**：tag×secded（0.50 [0.3639, 0.6361]）vs data×secded（0.00
[0.0000, 0.0727]）——**Wilson CI 无重叠，分化显著**。tag 合法别名在 SECDED
下 SDC 率纹丝不动（24/100 两臂完全一致——合法 tag 替换零 syndrome，ECC
结构性不可见）；data-face 单 bit 被 SECDED 全纠。与 Phase 14 n=384 formal
（pwf_v12_l2_arms_formal：data×secded SDC=0/384，tag×secded SDC=191/384）
方向与量级一致。本役随机采样（非定向块）Inactive 过半（51-52%），故全分母
P_SDC 低于定向臂——两口径并列如实报告。

### 2.2 IFU 臂（deferred，引用 Phase 16 既有证据）

runner 无 BPU 注入路径（two_level_taishan.py --injector 仅
reg/phys/lsq_fwd；CHAOSBPU 挂载需 decoupledFrontEnd，SimpleBoard 实测不
boot，configs/se/arm_chaos.py:589-593 注释在案）。引用既有证据：

| 预测面 | 证据 | 结果 |
|---|---|---|
| dir_flip（方向） | pwf_v13_bpu_formal（commit 524dc60a/348250de 引首轮） | **384/384 Masked，0% SDC** |
| target_flip（间接目标 F5） | pwf_v12_bpu_target_pilot（commit 348250de） | n=100，**0.0% [0, 3.7]** |
| ras_flip（返回栈 F5） | pwf_v12_bpu_ras_pilot（commit ae8c8f7e/a9a0f7d5） | n=100，**0.0% [0, 3.7]** |

→ ρ_IFU = 0.00（三面全阴性，squash 自愈），与本役无矛盾， ceilings.IFU=0.0
维持。Phase 16 复现锚达成（0% 线）。

### 2.3 MMU 臂（deferred，引用 SE 侧证据；FS 臂登记）

- SE 侧：addrmap_formal_fwd（commit ec971533，fwd_checksum_kernel，n=384）：
  **384/384 Masked，P_SDC=0.0% [0.0, 1.0]**——cache 驻留 SE workload 下
  DRAM/地址映射面不可达。
- FS 侧：CHAOSArmTLB FS 实测存在（progress.md：live_page 19/32 guest
  Oops——DUE 主导而非 SDC），但 FS 镜像未入库（kernel/disk 本地路径），
  按计划 §六预案 **deferred 登记**。ρ_MMU（SE 用户态）= 0.00，FS 臂待回填。

## 3. ρ_u 回填表（rho_measured → taishan-v110.yaml）

口径 = detection | active（§1.2 申明；SDC-only 拆分见 §4）：

| 单元 | ρ 初值（§1.6） | **ρ_measured（本役）** | Wilson 95% CI | 备注 |
|---|---|---|---|---|
| IFU | 0.00 | **0.00** | —（引用） | Phase 16 三面 0%；deferred 臂 |
| OoO | 0.05 | **0.05** | [0.0215, 0.1118] | 5/100 全 Crash（见 §4）；与初值惊人一致 |
| IEX | 0.05 | **1.00**（intadd）/ 0.82（intmul） | [0.9630, 1.0000] / [0.7219, 0.8835] | permanent FU-mask 协议语义（§4.2） |
| LSU | 0.05 | **0.69**（lsq）/ 0.04（l1d 面） | [0.5937, 0.7722] / [0.0158, 0.0993] | 前转通路 vs 数据面分化 |
| FSU | 0.01 | **0.00** | [0.0000, 0.0370] | fpadd/fpmul 双臂全 Masked（值掩蔽） |
| MMU | 0.00（SE） | **0.00**（SE） | —（引用） | addrmap 384/384 Masked；FS deferred |
| L2C | 0.45（tag）/ 0.0（data-secded） | **0.50**（tag）/ 0.41（data-none）/ 0.00（data-secded） | [0.3639, 0.6361] / [0.2822, 0.5475] / [0, 0.0727] | 双面双账本如实分列 |

YAML 回填（`configs/cpu-profiles/taishan-v110.yaml`）以
`rho_measured` 键与 `rho_overrides` 并列（不覆盖），每条附臂名与 CI。

## 4. 发现与诚实边界

### 4.1 SDC/Crash 拆分：非 L2C 单元的 detection 几乎全由 Crash 承担

irf/intadd/intmul/lsq/l1d 五臂的 **SDC 计数全部为 0**——所有 detected 结局
均为 Crash（Page-table-fault panic，注入的直接因果：损坏值进入地址计算 →
非法访问 → gem5 SE panic）。只有 L2C 双臂产出真 SDC（checksum 完成但偏离
golden）。含义：
1. **ρ_u（严格 SDC 口径）**在 OoO/IEX/LSU/FSU 单元 ≈ 0（上界 3.7-4.7%）；
   本框架 ED 若取严格 SDC 口径，非 L2C 单元贡献趋零。回填取 detection
   口径（§1.2 申明）是因为 ED 的下游用途是「序列检出 SDC 故障的能力排序」
   （Crash 同样是检出）且与 §1.6 初值口径一致。
2. **结局的工作负载依赖**：lsq-matrix 战役（fp_fwd_kernel，n=64）bitflip
   100% SDC，而本役 rand_mem 69% Crash——前转值喂地址计算则 Crash、喂
   算术-校验和则 SDC。ρ_u 是「单元×序列」联合属性，非单元常数；本表是
   定向标定序列下的条件值，跨序列迁移（Task 6.3）会量化该差异。

### 4.2 intadd 1.00 / intmul 0.82 是 permanent-FU 协议语义，非单次翻转

CHAOSFUPerm 自 first_clock 起**持续**对同类每条指令结果施加同一 mask
（实测单 run 注入日志 32 条）。任一算术结果位持续损坏 → 地址/循环控制崩溃
→ Crash 近必然。这测得的是「该类指令在 checksum 路径上的暴露度」而非
transient 单 bit 的 SDC 转化。transient 执行级臂的既有证据是阴性对照
t3-2-exec-negative（IntAlu XOR，madd+smulh，n=384×2 全 Masked，commit
76ddb2c9）。IEX 的 ρ 应理解为该协议下的上界语义。

### 4.3 l1d 臂修复（工具缺陷，本役发现并修复）

原 harp_eval.py l1d 臂 gem5 命令带 `--quiet` 无重定向 → simout.txt 从不
生成 → 注入 run 全部误分类 NoOutput（本任务 N=2 探针实测 2/2 NoOutput
复现）。修复为 `-r -e --silent-redirect` 后 l1d 臂正常分类（4 Crash/95
Masked/1 SimErr）。修复属 harp_eval.py 本次 patch 的一部分。

### 4.4 L2C 臂 Inactive 过半的口径

随机块+随机字节+随机 cycle 采样下 51-52% 的 run 故障未落地（L2 512KB 驻
留活数据稀疏 + tag 臂同 set 无 alias 候选时 SKIPPED）。定向臂（Phase 14，
target_block_addr 钉活块）Reach 100%。两口径均已并列；ρ 取条件口径
（| active）。SKIPPED 日志行已从注入计数中剔除（否则 Inactive 虚报）。

### 4.5 fsu 0% 与 CHAOSFPU 掩蔽链

fpadd/fpmul 各 100 次随机单 bit 全 Masked——与初值表依据（CHAOSFPU N=20
全 Masked）一致放大到 N=200。既有 t3-1-fsu-formal（4 精度×位段 n=384×16）
显示 FSU SDC 高度值依赖（float 60-66% vs double 14-18%），harp 序列的
FP 值域（rand_fp 的 d 寄存器普通值）落在掩蔽区。ρ_FSU=0.00 是「本标定
序列族」的条件值，非 FSU 物理免疫（Task 6.3 负对照/值类熵臂会再触及）。

### 4.6 通用边界

- 全部速率为 gem5 O3（TaiShan v110 实配）条件概率，非产品 FIT。
- golden-diff oracle（q=1 基线）；deployment checker 口径是 Phase 7 臂。
- 单机未复现（single-machine, unconfirmed）。
- IFU/MMU 臂为引用既有证据（deferred 登记），非本役新跑。
- intmul 臂 13 SimulatorError（gem5 panic 非 workload 因果文本）按六类
  口径剔除出 detection 分母的条件版；16 Hang 是 DUE 类结局（detection
  口径未计入——论文口径 SDC+Crash；若计 Hang 则 intmul 0.87）。

## 5. 回填动作

- [x] `configs/cpu-profiles/taishan-v110.yaml`：新增 `rho_measured` 块
  （与 `rho_overrides` 并列，逐条附臂名/CI/口径注释）
- [x] `docs/sdc-ed/calibration-report.md`：本文件
- [x] 计划 Task 6.1 checkbox 勾选
