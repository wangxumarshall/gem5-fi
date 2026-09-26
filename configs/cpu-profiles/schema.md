# CPU 描述文件 schema（Layer C）

> 单一事实源：一份 YAML 同时驱动 ① gem5 实例化（configs/se/profile_taishan.py）
> ② CHAOSCov 分母参数 ③ ρ 初值推导（ed_profile.py）④ w_u 位容量推导。
> 字段语义的权威定义在 `docs/sdc-ed/method.md` §2；本文件是操作手册。

## 两条硬规则

1. **未披露字段不猜值**：写 `null` + `uncertainty: true`。解析器（ed_profile.py）
   对该单元的 w_u 附区间/警告，ED 报告对该单元附 uncertainty 标记。
   禁止用「同代 CPU 大概是多少」填充——这是底表（§2 总表）大量「未披露」
   格子的诚实处理。
2. **residuals 非空时报告首行必须列出**：ED 数字只对 modeled 集合负责。
   `ed_profile.py` 自动附加的 residuals（组合逻辑 1/3 系数、null 字段
   点估计警告）与手写 residuals 合并去重。

## 顶层字段

| 字段 | 必填 | 语义 |
|---|---|---|
| `cpu` | ✓ | 实例名（报告标识） |
| `derived_from` | ✓ | 溯源（config 文件或底表文档）——审计用 |
| `units` | ✓ | 7 单元映射（IFU/OoO/IEX/LSU/FSU/MMU/L2C） |
| `ceilings` |  | 可达性上限覆盖（缺省表见 ed_profile.py DEFAULT_CEILINGS） |
| `rho_overrides` |  | ρ 手工覆盖（优先级最高；覆盖标定值须附理由注释） |
| `residuals` |  | 未建模/未证实项清单（诚实边界） |

## units.* 子结构

### 通用字段语义

- `size`：`64KiB`/`512KiB`/`32MiB` 后缀字符串或整数 bytes
- `entries`：表项数；`null` = 未披露
- `width`：位宽（PRF 寄存器宽 / BTB tag 宽 / FU 输入路径宽）
- `prot`：保护矩阵枚举，见下表
- `count`：FU 实例数（IBR 分母）
- `op_lat`：操作延迟周期（IBR 多周期展开口径）
- `modeled: false`：结构存在但本方案未建模（进 residuals）
- `uncertainty: true`：值未披露（配合 null）

### prot 枚举 → ρ 推导规则（ed_profile.py PROT_RHO）

| prot 值 | ρ 因子 | 依据 |
|---|---|---|
| `none` | 1.0 | 无保护，单 bit 翻转直接改状态 |
| `parity` / `sed` / `parity_interleaved` | 0.5 | 单 bit 检、双 bit 漏（TRM "might cause data corruption"） |
| `secded` | 0.0（data-face） | L2 2x2 实测 47%→0% 全修 |
| `ecc_claimed_no_evidence` | 0.5 | 厂商声称无架构化证据（920 案例） |
| `mmutc_sed` / `tag_parity_data_sed` / `tag_data_tq_secded` | 按面拆分 | 组合值，tag/逻辑面保留敏感性 |

L2C 特殊语义：**双面账本**——`secded` 时 data-face ρ=0、tag-face 保留
0.45（L2 2x2 实测：tag 合法别名 39→47% ECC 盲）；`none` 时 1.0×0.45。

### 位容量推导（w_u 分子，ed_profile.py unit_bits）

| 结构 | 位计 |
|---|---|
| cache（l1i/l1d/l2） | size × 8 |
| 表项结构（btb/ras/tlb/rob/lq/sq） | entries × width（ROB 按 260b/entry 保守） |
| PRF | regs × width |
| FU（组合逻辑） | count × width × 64 × **1/3**（COMBINATIONAL_WEIGHT，文献级先验，恒进 residuals） |

### 单元 ↔ gem5 参数映射（消费者 ①）

| YAML 路径 | gem5 O3/cache 参数 |
|---|---|
| `OoO.rob.entries` | `numROBEntries` |
| `OoO.prf_int.regs` | `numPhysIntRegs` |
| `OoO.prf_float.regs` / `prf_vec.regs` | `numPhysFloatRegs` / `numPhysVecRegs` |
| `LSU.lq.entries` / `sq.entries` | `LQEntries` / `SQEntries` |
| `IEX.fus.int_add.count` 等 | fu_pool FUDesc count / opLat |
| `IFU.fetch_width` | `fetchWidth`（同 decode/rename/commit 各宽度） |
| `LSU.l1d.size/assoc` | L1DCache size/assoc |
| `L2C.l2.size/assoc/lat` | L2Cache size/assoc/延迟 |

**注意**：披露口径（kunpeng920.yaml）与实配口径（taishan-v110.yaml）数值
不同（ROB 128 vs 97、mul 4 vs 3、L2 10 vs 8）。跑仿真用实配口径；w_u/ρ
推导用披露口径——两者差异是模型保真度 residual 的一部分，报告须并列。

## 编辑检查单（新增/修改 profile 时）

- [ ] 每个 null 字段都有 `uncertainty: true`
- [ ] `prot` 值在枚举表内
- [ ] `derived_from` 指向真实存在的文件
- [ ] 未建模结构（mop_cache/l3_slc）有 `modeled: false` 且进 residuals
- [ ] `python3 tools/ed_profile.py <file>` 渲染无异常、Σw=1.0000
- [ ] 底表转写的字段抽查 10 个与原文逐字一致（commit message 附对照表）
