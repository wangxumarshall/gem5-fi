# FP04-W4 频率批次总审计（F0/F1/F2/F3，12 个正式 seed）

> 生成时间：2026-11-03。所有数值来自本机真实运行与 `runs/fsu` 的
> AUTHORITATIVE 证据；未使用模板、预测或跨 seed 补齐。
> 门禁证据 `runs/fsu-gates/` **不计入**本文 seed 数。

## 1. 结论

- `FSU-FP04-F0-W4`、`FSU-FP04-F1-W4`、`FSU-FP04-F2-W4`、`FSU-FP04-F3-W4`
  均达到 **3/3**，合计 **12 个合格 seed**。
- 12 个 seed 的 `scheduled = attempted = injected = activated = fault = 687`。
- 全部 687 个 fault 的 chain terminal 为 **`full`**（真实 L5 commit 见证），
  `admitted=true`、`certified=true`、`violations=[]`。
- 12/12 seed 的 `audit.json` 均为 `ok=true`、`failures=[]`；审计检查合计
  **21,579 项，0 失败**。
- 12/12 run-level oracle 为 **SDC**；0 Masked、0 Crash、0 Timeout。
- 当前正式完成数 **12/519**，seed-complete RunID **4/173**；
  `overall coverage_status` 仍为 **NOT_COMPLETE**（见第 8 节）。
- F0 与 F1/F2/F3 使用**不同的 gem5 二进制与 workload**，不能合并为一个
  可重放身份（见第 5 节）。

## 2. 身份

| 项 | F0-W4 | F1/F2/F3-W4 |
|---|---|---|
| workload | 短 W4 `workloads/directed/elemwise_fma_kernel` | W4-rate-v1 `workloads/directed/elemwise_fma_kernel_rate_v1` |
| workload binary SHA-256 | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |
| workload source SHA-256 | `7d24eb75d5dd0f10a32821739bb6ce78b9e0450961e59d5fdef4ae2849699d9d`（`W4-RATE-V1.md` 记录；F0 manifest 未存 source SHA） | `e63dbcf7ce881b34078ef713281823f1ecc2e7d04cf79ecbb1c4be37201ac2c0` |
| golden ARRAYHASH | `ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7` | `e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba` |
| eligible_total（实测） | 57,347 | 2,097,155 |
| 注入选择 | 固定 skip：45,070 / 13,908 / 19,337 | 预注册 ordinal（见第 3 节） |
| gem5 二进制 SHA-256 | `f9a7cd9b4de6a47dbaceaa4dac0b58bbf8ba5bbbe8f1c8241a9e71be7af98c32` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| 源码 HEAD | `8e86d1ba0…`（三 seed 相同） | 逐 seed 不同（见第 5 节）；运行相关代码树相同 |
| 运行工具 SHA-256 | `b3a087a0…`（历史 runner） | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| 模型/子模型 | FP04 / FP04-c（`mant_lo`） | FP04 / FP04-c（`mant_lo`） |

预注册 ordinal 文件：`configs/fsu/W4-rate-v1-ordinals.json`
（SHA-256 `1df384749d9d97095e1f259d67555871e80344708733597da40cbccd2c3e3924`）。

## 3. 逐 seed 结果

| RunID | seed | authoritative attempt | scheduled | injected | activated | fault | terminal | oracle | audit checks | audit.json SHA-256 |
|---|---:|---|---:|---:|---:|---:|---|---|---:|---|
| FSU-FP04-F0-W4 | 1 | `seed1/attempt-2` | 1 | 1 | 1 | 1 | full | SDC | 47 | `ff862f31c3c1e03ee9a8560e44a90a1357ffc0b0d44e424e726b1f6fd307049f` |
| FSU-FP04-F0-W4 | 2 | `seed2/attempt-1` | 1 | 1 | 1 | 1 | full | SDC | 47 | `a2dc048c97f494f99f455cdcd79d3bf9ad67b17d056b7d357bbf3128af751e2d` |
| FSU-FP04-F0-W4 | 3 | `seed3/attempt-1` | 1 | 1 | 1 | 1 | full | SDC | 47 | `f53d863cf1c4e768480b28392157aec8333fa07fbe51f1850b647148a84b5b5c` |
| FSU-FP04-F1-W4 | 1 | `seed1/attempt-1` | 1 | 1 | 1 | 1 | full | SDC | 57 | `62e7347b886820101a31042db2f4b334a29c01a3a5f032bc8629f767fffb64c1` |
| FSU-FP04-F1-W4 | 2 | `seed2/attempt-1` | 2 | 2 | 2 | 2 | full | SDC | 88 | `a53e086511675054b2e4fb67f054323bb757a2ad20419137950f702bdb11b9c0` |
| FSU-FP04-F1-W4 | 3 | `seed3/attempt-1` | 1 | 1 | 1 | 1 | full | SDC | 57 | `d00271c657459494a7c0039102572a6355330a66e0cf6ccd3d926d2a6ad3aa04` |
| FSU-FP04-F2-W4 | 1 | `seed1/attempt-1` | 21 | 21 | 21 | 21 | full | SDC | 677 | `1994e89a5e670415dd1933cdea074b04264fdb255b87bad5702bfe04e12bcb96` |
| FSU-FP04-F2-W4 | 2 | `seed2/attempt-1` | 22 | 22 | 22 | 22 | full | SDC | 708 | `cf5f45cd9e60148f87cad60a2959f7d55c02780cc9bbb4b5c61de4ad7b096fef` |
| FSU-FP04-F2-W4 | 3 | `seed3/attempt-1` | 19 | 19 | 19 | 19 | full | SDC | 615 | `09e3eb3d490be69a5cbce3034bc8efd2573a3afce3b221292622ae8adea4bdb8` |
| FSU-FP04-F3-W4 | 1 | `seed1/attempt-1` | 206 | 206 | 206 | 206 | full | SDC | 6,412 | `29b123d82ceef46baa91bc05f8ee506a2056a14a36a321dd4342a0a57f2db708` |
| FSU-FP04-F3-W4 | 2 | `seed2/attempt-1` | 202 | 202 | 202 | 202 | full | SDC | 6,288 | `238f281b06446d971abe14785f0674821bf1ae7ae29abaa7b29fc43063834dfe` |
| FSU-FP04-F3-W4 | 3 | `seed3/attempt-1` | 210 | 210 | 210 | 210 | full | SDC | 6,536 | `428948a83a017e80e1db9bb8129aea7f2a00d67f03a23b0c7ff606c8f795c6c0` |
| **合计** | | | **687** | **687** | **687** | **687** | **full=687** | **SDC=12/12** | **21,579** | |

每 seed 的 `scheduled == attempted == injected == activated == fault`；
每个 fault 有唯一 L0 root、空 parent、直接 parent 连续、层序 `L0→L1→L2→L3→L4→L5`，
`chain_end` 仅作生命周期收口、不占 L5。

### 3.1 预注册 ordinal（rate seed）

| seed | 数量 | 首 ordinal | 末 ordinal | ordinals SHA-256 |
|---|---:|---:|---:|---|
| F1-seed1 | 1 | 1,394,471 | 1,394,471 | `b8e80e065b4cbe2352f85fc0ca092e625ddb190aa44e5b1d0e2f67f7fc3ef892` |
| F1-seed2 | 2 | 1,027,869 | 1,716,133 | `b751d246742d462a57fed2e6f8f897783babdbe153761aae87bba2691b10e2dc` |
| F1-seed3 | 1 | 1,306,838 | 1,306,838 | `39e0b89571c30645f0ee14a5f53a3a59230f2422480007513230a67de8e2ccaa` |
| F2-seed1 | 21 | 91,644 | 2,094,621 | `1ef3a0a61e16a6e086a5788f3f6ef2e86e6cc0abe0dca98794e18ef2cf80a1a2` |
| F2-seed2 | 22 | 82,214 | 2,058,002 | `783007882a6f784e997d4a738226baf681326427b0312d2192e8286b0ea6c01c` |
| F2-seed3 | 19 | 115,872 | 2,028,008 | `097afed3c24e7d8d23913ed61faa968d3628fa76b6c4bedb41a3f774456629f3` |
| F3-seed1 | 206 | 11,004 | 2,091,182 | `5ed393fc2e10184bf912e82c33ec762680aab236cb33288cb0e2d59753b15397` |
| F3-seed2 | 202 | 10,298 | 2,085,278 | `8c317216bd3f6cb57a95091694427889adf7f00f83cd9b190c89429c97a9282d` |
| F3-seed3 | 210 | 5,409 | 2,088,070 | `15d4a409c3d807aab196116acf1b7a7b027fc1959075d07b70db4bcb502d99ca` |

每个 attempt 的 `ordinals.json` 与预注册条目逐项一致，文件 SHA = manifest
`rate.ordinals_sha256` = 预注册 `ordinals_sha256`。

## 4. 结局分布

| 维度 | 分布 |
|---|---|
| 逐 fault terminal | `full` = 687 |
| run-level oracle | `SDC` = 12 seed |
| 被含住（contained） | 0 fault |
| Crash / Timeout / Masked | 0 |
| seed admitted / certified | 12 / 12 |
| seed violations | 0 |

run-level oracle 与逐 fault terminal 分开记录；本文不把 run-level SDC
当作某个 fault 的链终局，也不用一个 fault 的 L5 认证其他 fault。

## 5. 可重放性与来源

### 5.1 运行相关代码在 rate 批次内未变化

F1/F2/F3 的 9 个 seed 在运行前分别提交了前一个 seed 的证据，因此 manifest
记录的 `source_head` 不同。对 `db21e798…` 到 `2a5f3273…` 验证：

```bash
# 运行时的 HEAD = 2a5f3273（F1 seed3 提交）
git diff --stat db21e798ad154fe7983d937640943190e5d21ee8..HEAD -- \
  CHAOS/gem5/src configs/se tools/fsu_seed_runner.py tools/fsu_chain_check.py \
  tools/fsu_seed_audit.py tools/fsu_seed_doc.py tools/fsu_prop_fields.py \
  tools/classify.py tools/fsu_rate_ordinals.py workloads configs/fsu
# 输出为空
```

即这 9 个 seed 之间只有文档与证据提交，**没有**注入器、配置、runner、
审计器、workload 或预注册 ordinal 的变更。三者的 `gem5_sha256`、
`workload_sha256`、`runner_tool_sha256` 也完全相同。

### 5.2 F0 不可用当前二进制重放

F0 三个 seed 使用 `f9a7cd9b…`，当前仓库二进制为 `e1ee610d…`；F0 的短 W4
与 rate-v1 的 eligible/选择机制也不同。F0 证据内部自洽，但不能与 rate 批次
合并成同一重放身份。F0 seed1 的被淘汰 attempt-1 还使用过第三个二进制
`2ac3663c…`，其原始证据保留、`SUPERSEDED.md` 与 `lineage.json` 记录原因。

### 5.3 已知溯源缺口

- `audit.json` / `audit.md` / `evidence_sha256.json` 不在
  `evidence_sha256.json` 清单内（避免自哈希）；审计文件通过独立重算原始
  事件流验证。
- F0 manifest 未记录 workload source SHA；只能由 `W4-RATE-V1.md` 与当前
  源码哈希佐证。
- `FAILED`/`SUPERSEDED` 的旧 `.done` 仍存在；计数只读取 `AUTHORITATIVE`，
  不按 `.done` glob 计数。

## 6. 失败与重跑 lineage

| RunID/seed | attempt | 状态 | 原因 |
|---|---|---|---|
| FSU-FP04-F0-W4 seed1 | attempt-1 | SUPERSEDED | 发射端 v1 的 `unit="FSU Pipe"` 含空格被 PROP-EVT 截断；`fault_mask` 丢失；L3/L4 重复计数 activated。原始证据保留，未使用。 |
| FSU-FP04-F0-W4 seed1 | attempt-2 | AUTHORITATIVE | 修复后重跑；`unit=FSU_Pipe`、`fault_mask` 落盘、activated=1。 |
| 其余 11 个 seed | attempt-1 | AUTHORITATIVE | 首次 attempt 即通过全部门禁。 |

无其他失败 attempt；门禁证据不计入正式 seed。

## 7. 证据位置

- 权威 attempt：`runs/fsu/<RunID>/seed<N>/AUTHORITATIVE` 指向的目录。
- 完整传播链 Markdown：`runs/fsu/COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seed<N>.md`
  （与 attempt 内 Markdown 字节级相同）。
- 索引：`runs/fsu/COMPLETE_PROPAGATION_PATHS/{INDEX.json,INDEX.md,README.md}`。
- 覆盖状态：`docs/gem5-fi/fsu/COVERAGE_STATUS.md`。
- 实施矩阵：`docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.{json,csv}` 与
  `IMPLEMENTATION_AUDIT.md`。
- 门禁（不计入 seed）：`runs/fsu-gates/F3-multifault-gate*`。

复算命令：

```bash
python3 tools/fsu_seed_audit.py runs/fsu/FSU-FP04-F3-W4/seed1/attempt-1
python3 tools/fsu_index.py
python3 -m pytest tests/test_fsu_chain_check.py tests/test_fsu_implementation_matrix.py \
  tests/test_fsu_index.py tests/test_fsu_rate_ordinals.py tests/test_fsu_regenerate.py \
  tests/test_fsu_seed_audit.py tests/test_fsu_seed_runner.py tests/test_fsu_xlsx_to_md.py -q
```

## 8. 覆盖边界（不得宣布 COMPLETE）

- 正式 seed：12/519；seed-complete RunID：4/173；其余 169 个 RunID 为 0/3。
- frequency_coverage（W4）：F0=3/3，F1=3/3，F2=3/3，F3=3/3。
- submodel_coverage：仅 **FP04-c / mant_lo** 有正式证据；
  `sign`（FP04-a）、`exp_hi/exp_lo`（FP04-b）、`mant_hi/mant_mid`、
  FP04-d NEON lane result、FP32 字段映射、NEON 全 128-bit lane 均未覆盖。
- workload_coverage：W4 REAL；W1/W2 无真实 artifact；W3/W5/W6 PARTIAL；
  W7 无 FP artifact；W9 未绑定；W0/W8/W10 未使用。
- 配置：仍为 C3 默认（ROB=128、IQ=64、4-wide），**不是**工作簿 B0
  （ROB=40、IQ=32、3/3/3、8/8/8）；B0 参数化缺口仍在。
- 因此 `overall coverage_status = NOT_COMPLETE`；F0/F1/F2/F3-W4 的 12 个
  seed 只证明该子模型/该 workload 的频率语义，不证明 FP04 全模型覆盖。
