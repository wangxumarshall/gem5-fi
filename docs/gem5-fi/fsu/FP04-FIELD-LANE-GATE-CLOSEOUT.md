# FP04 字段 / FP32 / NEON lane 门禁收口（D3）

> 生成时间：2026-11-03。本文所有数值来自本机真实 gem5 运行；三个 GATE
> RunID **不计入** 173 RunID 注册表，也不计入 519 个正式 seed。
> 原始证据：`runs/fsu-gates/F0-W4-SIGN-gate/`、
> `runs/fsu-gates/F0-W1-FP32-SIGN-gate/`、
> `runs/fsu-gates/F0-W3-NEON-LANE2-gate/`。

## 1. 结论

- 已实现 FP64 六字段（sign/exp_hi/exp_lo/mant_hi/mant_mid/mant_lo）、
  FP32 六字段位表、8/16/32/64-bit lane 选择与完整 128-bit lane 写入。
- 3 个真实门禁 × 3 seed = **9 个 gate seed** 全部 `admitted`、
  `certified`、`violations=[]`、`audit.ok=true`；每个 fault 均 `full`。
- 字段/ lane 证据是真实的：FP64 sign 只翻 bit 63；FP32 sign 只翻 bit 31
  且高 96 位不变；NEON lane 2 只改绝对 bit 95，`LANEHASH0/1/3` 与 golden
  完全相同，仅 `LANEHASH2` 改变。
- 9 个 gate seed 的 `audit_checks` 均为 65 项、0 失败。
- 门禁本身不计入正式完成数（门禁阶段基线为 12/519、4 个 RunID 3/3）；
  随后 F0-W3 正式试点使完成数变为 **15/519**、5 个 RunID 3/3（见 6.1）。

## 2. 身份与 golden

| 项 | 值 |
|---|---|
| gem5 二进制 | `CHAOS/gem5/build/ARM/gem5.opt` |
| gem5 SHA-256 | `5647208d1fdf9ea131bcae60e0479fc5a0d477dce2fee0930bc8d04d40f47e73` |
| 构建 | Python 3.11.9；`PYTHON_CONFIG=/opt/python3.11/bin/python3.11-config scons -j16` |
| 短 W4 workload | `workloads/directed/elemwise_fma_kernel` |
| 短 W4 binary SHA-256 | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` |
| FP32 scalar workload | `workloads/directed/fp32_fma_kernel` |
| FP32 scalar binary SHA-256 | `bf3d26a4a2bcdd53b6a5dd1b04d540056b60e73108ff01e7fe01ece106c98eaf` |
| NEON FP32 workload | `workloads/directed/neon_fp32_lane_kernel` |
| NEON FP32 binary SHA-256 | `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92` |

无注入 golden 各连续 3 次，stdout 逐字节一致：

| workload | ARRAYHASH | ULP | stdout SHA-256（3 次相同） |
|---|---|---|---|
| 短 W4 | `ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7` | 0 | `457c78dcbd899dfa…` |
| FP32 scalar | `cb66197d92c7656b9359b312e93180eaaf3c1e774d9264d7d0b595189bce8c2e` | 0 | `2e31ec2e224c57bc…` |
| NEON FP32 | 同上 | 0 | `c700ade0802ee216…` |

golden 原始 stdout/stderr/time 与 `SHA256SUMS` 保存在各 gate 的 `golden/`。

## 3. 门禁结果（3 × 3 seed）

| GATE RunID | seed | field | precision | lane | abs bit | lane_mask | eligible | skip | terminal | oracle | audit checks |
|---|---:|---|---|---|---:|---|---:|---:|---|---|---:|
| FSU-FP04-F0-W4-GATE | 1 | sign | fp64 | 64@0 | 63 | `…8000000000000000` | 57,347 | 45,070 | full | SDC | 65 PASS |
| FSU-FP04-F0-W4-GATE | 2 | sign | fp64 | 64@0 | 63 | 同上 | 57,347 | 13,908 | full | SDC | 65 PASS |
| FSU-FP04-F0-W4-GATE | 3 | sign | fp64 | 64@0 | 63 | 同上 | 57,347 | 19,337 | full | SDC | 65 PASS |
| FSU-FP04-F0-W1-GATE | 1 | sign | fp32 | 32@0 | 31 | `…0000000080000000` | 524,292 | 337,767 | full | SDC | 65 PASS |
| FSU-FP04-F0-W1-GATE | 2 | sign | fp32 | 32@0 | 31 | 同上 | 524,292 | 469,010 | full | SDC | 65 PASS |
| FSU-FP04-F0-W1-GATE | 3 | sign | fp32 | 32@0 | 31 | 同上 | 524,292 | 253,229 | full | SDC | 65 PASS |
| FSU-FP04-F0-W3-GATE | 1 | sign | fp32 | 32@2 | 95 | `…8000000000000000` | 16,384 | 15,571 | full | SDC | 65 PASS |
| FSU-FP04-F0-W3-GATE | 2 | sign | fp32 | 32@2 | 95 | 同上 | 16,384 | 14,938 | full | SDC | 65 PASS |
| FSU-FP04-F0-W3-GATE | 3 | sign | fp32 | 32@2 | 95 | 同上 | 16,384 | 15,149 | full | SDC | 65 PASS |

每个 fault 的事件链均为 `fault_applied → carrier_state → operand_read →
execute → prf_writeback → commit`，`commit` 为真实 `detection_layer=L5`、
`outcome=errant_commit`；`chain_end` 不冒充 L5。

审计证据 SHA-256：

| GATE RunID | seed | audit.json | seed Markdown | chain_report.json | prop_evt.txt.gz |
|---|---:|---|---|---|---|
| FSU-FP04-F0-W4-GATE | 1 | `6aae7a99d4c08989bd67ddf0d3a053e9faded146cad35827bdea3a2d04a3e579` | `82d1bc6c1432f438db450c189e38f57b36887229eb6636c41329b09acb5b1f86` | `5c5eb33b932f316b4ee82b6051b396a95b6201b7c9239b3af44ff71b9548f4e9` | `7ee70f90ae00307c6ccfa019889c7dafdd8b7fbdbd8481a6feb54552e8dc87d1` |
| FSU-FP04-F0-W4-GATE | 2 | `9784bd2044e1b564c4a80aa01b657f220a650712b0e9d9d64c269da71b433889` | `6940fd89b1fba9c1c25b13fa0ebe46fa6f5548f06b22d90ea1ef2ef21cc07c25` | `ea4055aa4d7f3c3600e1b0c35e700aae77a491e37354429b1195e065fb04d1ce` | `3a5d9c41627cec20c4e8dc29aae6f16012e6270728646935632b363de22398ad` |
| FSU-FP04-F0-W4-GATE | 3 | `2d04406427907c837683995a04f8393d2b3476035d5ae85ad7a4456fde6f546e` | `33543cabbacfccf7aa6f961bf16a974c68ac91f9e694992c9d60a411449b4f3b` | `a52c7706a042b77f7382bd36903748eafcd751c18cfa93bdb90daf6a301f8186` | `49127de38b79b68c1b315bf88ca6f459ea1f97f8c9576b8f9cae1ea7b7944043` |
| FSU-FP04-F0-W1-GATE | 1 | `57d9993031cca4a6be3bb6650c8608d9aadd7fe804cef4d13126a7d31e868a18` | `1f0f19752d904d0b451727989a87f96586f37b85a80c738037c6b7bec0e2e64a` | `d9f410c7a5fd05bd36fe50a3db8b93d02d0454b56342bfc52790f95ef49ac41f` | `2c4ce53c0133fd6b3d77fd61c9897d2a0e77ae5b4448f5f8cdf407c0ef502fbe` |
| FSU-FP04-F0-W1-GATE | 2 | `19cef8a46cfb6861ce693091d37d51256084b04e135a304d0f77a770de219c4e` | `14c8d1fa64126148a9aaddd2bd775d9ce41de3ac7de72cd86a918e43760fc3d1` | `2f6818245ae6f0fc596e27c5eea229bd9e5aca9405a2342863ddd81cc38525e9` | `7cdc77dbbd96d0ac346a1dee815a4f99b3333fa378b59c18124669c9f0ecaed3` |
| FSU-FP04-F0-W1-GATE | 3 | `379defdd2b83b4d3d8d1e335f0122b795b5bff6ed8fa6debc86fdeb37f265d13` | `fe3593fb98b4e630f4b70464336c443b92cdc89c631020cfb12e852c7e7a98b8` | `22d84ee6156c17161607802f97f39b065fe3c42a47ed299e55e09b1f53168bf4` | `5c33256e317b7561208ac11416e44fa55d381b86c7973cfb629cdae8313d0fd3` |
| FSU-FP04-F0-W3-GATE | 1 | `e554232efaa08bc312d6764e10508e07796a11ceb8d6ef8a0a3e23afe6c3b680` | `55fae404d2da8b31bb9194b8434363aa831f5b57194d38ebab54e424b347eacf` | `6fac7c0ec0c6f50fae667184bf3c4132debb9bee2f25e2cd8a3fcade9b38fcc9` | `12812c4ad9caff68e1992d0a6730059d3778b3ff8f4c925a56936c0ffb750787` |
| FSU-FP04-F0-W3-GATE | 2 | `426dd6adb2da47f71000fd34097349f0586e109cb2fd0742e2d3ef17482bde84` | `d56a7e8900080076c9ee7f59a901b5bf67c682f5b00bd3f381eac4f19e41e333` | `73e51f63919bf62056356b17ed45209302cc3f4ad9a0ab59423825160fc27cba` | `c667365a49cc1db4396fdca58d99eb0a278d4213a72ed4bdeebbc35b93a7b925` |
| FSU-FP04-F0-W3-GATE | 3 | `ed25b2ffaf65b23775b2bffba85f85668908a06eaf6eb50efb75e61a946811a6` | `54e2ae59c69072670c0f8874025926064105925bba6bb9169a45a64f51a084fd` | `f85fe6a1bcd58d7a0836287468b771c0d81fe23c060097f44dbbbf64a39c0244` | `a85f3d52e43e0615f61f3d58d695481c2ab4f73e3125555d4038e6bc4017047a` |

## 4. 字段 / lane 隔离证据

### 4.1 FP64 sign（bit 63）

根事件示例（W4 gate seed1）：

```
field=sign precision=fp64 reg_class=vec
bit_indices=63 bit_in_lane=63 lane_width=64 lane_offset=0
fault_mask=0x8000000000000000
lane_mask=0x00000000000000008000000000000000
before=0x4080580000000000 after=0xc080580000000000
full_before=0x00000000000000004080580000000000
full_after =0x0000000000000000c080580000000000
```

`full_before ^ full_after` 恰为 bit 63；其余 127 位不变。

### 4.2 FP32 sign（bit 31）

根事件示例（W1 gate seed1）：

```
field=sign precision=fp32 bit_indices=31 bit_in_lane=31
lane_width=32 lane_offset=0 fault_mask=0x0000000080000000
before=0x3ec41894 after=0xbec41894
full_before=0x…000000003ec41894 full_after=0x…00000000bec41894
```

低 32 位仅 bit 31 改变，高 96 位保持不变；证明没有把 FP64 低位结果
当作 FP32 证据。

### 4.3 NEON 4×32-bit lane 2（绝对 bit 95）

根事件示例（W3 gate seed1）：

```
field=sign precision=fp32 bit_indices=95 bit_in_lane=31
lane_width=32 lane_offset=2 fault_mask=0x0000000080000000
lane_mask=0x00000000800000000000000000000000
full_before=0x3f9170e73e7ff79e3e7efbb53f1b9433
full_after =0x3f9170e7be7ff79e3e7efbb53f1b9433
```

`full_before ^ full_after` 恰为 bit 95；lane0/1/3 字节不变。
被注入 run 的逐 lane 输出（seed1）：

```
LANEHASH0=2c95d7c4ae2806d6   （与 golden 相同）
LANEHASH1=92fd48a26f468d96   （与 golden 相同）
LANEHASH2=f4747d97d8a8ef30   （改变）
LANEHASH3=d9639e1314922560   （与 golden 相同）
```

三个 seed 均只改变 `LANEHASH2`；这是“只改目标 lane”的端到端真实证据。

## 5. Fail-closed 负例（真实 gem5 进程）

| 配置 | 结果 |
|---|---|
| `precision=fp64` + `lane_width=32` + `bitseg=sign` | rc=134，panic: field 'sign' range [63,63] does not fit lane_width 32 |
| `lane_width=32` + `lane_offset=4` | rc=134，panic: lane_offset 4 out of [0,4) |
| `bitseg=sign` + 显式 `fault_mask` | rc=134，panic: bitseg cannot be combined with explicit fault_mask/modes |
| `lane_offset>0` + 纯标量 workload | 不 panic；标量指令不计入 eligible（countOnly 与注入流同一谓词），不会产生不可见故障 |

## 6. 正式 RunID 裁决

- 工作簿的字段轴**不在 RunID 字符串中**；20 个 `FSU-FP04-*` RunID 的子模型
  列都包含 FP04-a/b/c/d。字段是 RunID 下的 submodel/manifest 维度。
- 4 个 W4 RunID（F0/F1/F2/F3-W4）已各 3/3，但只实测 mant_lo；没有空余的
  W4 种子槽位可再表达 sign/exp/mant_hi。
- 因此本轮**不新增第 174 个 RunID**：GATE 证据只证明能力，不计入 519。
- 已执行正式试点：仍未被使用的真实 RunID `FSU-FP04-F0-W3`
  （NEON-LaneProbe）。新 NEON FP32 workload 的 golden、eligible 与完整链
  均真实；3 个正式 seed 全部审计通过（见 6.1）。该 RunID 标为 3/3，但
  覆盖仍仅限“lane2 + sign”，不得宣称 FP04 全模型覆盖。

### 6.1 正式 FSU-FP04-F0-W3 结果

`configs/fsu/FSU-FP04-F0-W3.json`（manifest 已提交）使用
`workloads/directed/neon_fp32_lane_kernel`，`submodel=FP04-d`，
`precision=fp32`、`lane_width=32`、`lane_offset=2`、`bitseg=sign`。
三个正式 seed 的 eligible 均为 16,384：

| seed | eligible | skip | terminal | oracle | audit checks | audit.json | seed Markdown | chain_report.json | prop_evt.txt.gz |
|---:|---:|---:|---|---|---:|---|---|---|---|
| 1 | 16,384 | 15,571 | full | SDC | 65 PASS | `58bcc6f3920e602dea7fc7c944675da1bed1be42dd502dbb08d065d8ffc4c29e` | `800f9931478f35b15e96d586ad0e76eacc5049212a191046c922c38e87e90f59` | `e1777329aeda44eeb8574ecc47a4b063db96fc26faebc68af2b5da936af86af8` | `c672d09bf1862255cf59ab093d3b95ec1e863a03ada072af0febd02a0718618a` |
| 2 | 16,384 | 14,938 | full | SDC | 65 PASS | `7b52105b02a55801890baddeeee0bedf1fefd4b1cf9e167068772eec13b34bfd` | `d861e3af0ea45cdcdf2cad5e9224b65005f2315b028838587547ce38ffa58ded` | `9b967be56276460814bcce1f7f7666ba5b0f807c2dd1217381ac298b222432a0` | `b87a881711f3f6f0250370d2f31019717aaa481518320fc59ebdb77a31b67202` |
| 3 | 16,384 | 15,149 | full | SDC | 65 PASS | `e6d46ef07451e0f32138ac1b4665a7f32271ca0248d61fcd71ae7f0834a82fda` | `caee21ca6f909a1059abc428b4f0a43b7a8ca6452d4e4c82ba3f159a090f7535` | `c1799e47a75791133742d43fd82a9e13d0ec27a5aebcc6c9430990104184e6b6` | `ce373aa84090ec3c993a4bfea6ab75c9b0f001e1e1ee90cc9f18a342a4d4c8c3` |

三个 seed 的根事件均为 `field=sign`、`precision=fp32`、`lane_width=32`、
`lane_offset=2`、`bit_indices=95`、`fault_mask=0x0000000080000000`、
`lane_mask=0x00000000800000000000000000000000`；`full_before ^ full_after`
恰为 bit 95。`LANEHASH0/1/3` 与 golden 相同，仅 `LANEHASH2` 改变。

正式完成数因此从 **12/519** 变为 **15/519**；seed-complete RunID 从
**4/173** 变为 **5/173**。`overall coverage_status` 仍为 **NOT_COMPLETE**。

## 7. 边界

- `precision` 是 manifest 显式选择，不是从指令自动推导；workload 与
  manifest 精度必须由实验者保证一致。未知/不匹配配置目前不会自动识别。
- FP16、SVE 宽于 128-bit、FPCR/FPSR 架构状态、FMA 中间值仍未实现。
- 门禁证据不是正式 seed；`overall coverage_status` 仍为 NOT_COMPLETE。
