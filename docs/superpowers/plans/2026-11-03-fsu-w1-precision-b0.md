# FSU D3：W1 身份、指令级解码与 B0 门禁

> 依据：工作簿 W1 定义（主方案 :200）、W1 FP-ScalarProbe、AArch64 编码、
> B0/O3_ARM_v7a_3。一任务一提交，先实证后提交。

## 任务 A：W1 身份审计与真实 artifact ✅
- 现有 fp32_fma_kernel 与 W1 逐项对比：仅 FP32 FMA，无特殊值/4 舍入/
  FPSR/FPCR，判定为 gate-only，不满足 W1。
- 新增 w1_fp_scalar_probe：FP32/FP64 六运算、NaN/Inf/±0/subnormal、
  RN/RP/RM/RZ、FPSR/FPCR 快照、联合 ARRAYHASH。
- gem5 SE 实测 MRS/MSR FPCR/FPSR 可用；native/gem5 golden 3 次一致。

## 任务 B：指令级 precision/lane 解码 ✅
- decoded_fp.hh 纯解码器 + 39 条真实编码向量单测。
- CHAOSFPU decodeGuard：真实动态指令匹配；mismatch 拒绝且不消耗
  eligible/ordinal；事件携带 instruction_bits/decoded_*/manifest_*/
  precision_match/lane_match；审计器跨链验证。
- 负例：FP32+fp64=0、FP64+fp32=0、NEON lane 不匹配=0、标量 lane=0、
  lane_offset 越界 panic。

## 任务 C：B0-core 参数化与 config.ini 门禁 ✅
- B0-core = ROB40/IQ32/3-3-3/dispatch6/8-8-8/PRF 128/192/48/
  LQ-SQ16/fetchBuffer16/squash8。
- ooo_proxy --config_profile B0；runner 在 census/inject 后校验真实
  config.ini；不符 .failed，不写 AUTHORITATIVE。
- 完整 v7a_3 FP FUPool=2 仍未实现，明确列缺口。

## 任务 D：正式 F0-W1（B0）✅
- 3 seed attempt-2，decoded FMOV/FMADD/FDIV fp32，match=1；
  eligible 49,664；terminal 全 full；oracle Masked/SDC/SDC；audit 69 项。
- C3 attempt-1 保留并标记 SUPERSEDED；正式数 18/519、6/173。

## 任务 E：回归与 legacy 兼容 ✅
- 全量 FSU 测试 119 passed。
- 18/18 正式 seed 只读离线审计通过；旧 15 个为 legacy-valid，
  新 3 个为 B0/decode-valid；旧 F0 Markdown 无逐 fault 表时走单 fault 行。
