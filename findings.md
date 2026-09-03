# Findings: 现状证据审计（2026-09-03，写计划前调查）

## 已完成的 formal（n=384, 5% replay, 提交状态）

| campaign | workload | config | P_SDC | P_DUE | 结局 | git |
|---|---|---|---|---|---|---|
| prf_formal_cholesky X3 | cholesky | C2 | 3.9% [2.4,6.3] | 92.7% | Crash 主导 | 5d84b5f ✅ |
| prf X9 | cholesky | C2 | 0% | 0% | Masked | 5d84b5f ✅ |
| rat X3 map_bitflip | cholesky | C2 | 0.3% | 95.8% | Crash 主导 | 9659974 ✅ |
| rat X9 | cholesky | C2 | 0% | 0% | Masked | 9659974 ✅ |
| rob D=0 entry_bitflip | cholesky | C2 | 0% | 0% | Masked | 8bff9d1 ✅ |
| lsqfwd byte_flip | fwd_checksum | C2 | 0% | 100% | DUE | 8bff9d1 ✅ |
| iq wake_omit | cholesky | C2 | 0% | 0% | Masked | 88dbf98 ✅ |
| l1d random block/byte | l1d_reduce | C0-CACHE | **97.7%** [95.6,98.8] | 0% | SDC | 88dbf98 ✅ |
| fpu (Float*/Simd* XOR) | neon_lane | C2 | 0% | 0% | Masked | af64ef7 ✅ |
| exec (IntAlu/Mult/Div) | cholesky | C2 | 0% | 0% | Masked | af64ef7 ✅ |
| **bpu (dir/target_flip)** | branchy_reduce | C2 | 0% | 0% | Masked，384/384 faults=1 | **未提交** |
| **decode** | cholesky | C2 | 0% | 0% | Masked，384/384 faults=1 | **未提交** |
| **ras** | cholesky | C2 | 0% | 0% | Masked，384/384 faults=1 | **未提交** |
| **iq（第二个 campaign？）** | cholesky | C2 | 0% | 0% | Masked | **未提交** |
| **mem（CHAOSMem）** | cholesky | C2 | — | — | **384 全 Inactive，n_valid=0，无效** | **未提交** |

## 发现的 bug / 缺口（按严重度）

1. **CHAOSMem 频率 bug（P0，工具正确性）**：`CHAOSMem.cc:85` `first_tick = first_clock * tick_to_clock_ratio`，`arm_chaos.py:318`/`kp920_proxy.py:318` 传 `tickToClockRatio=1000`（1GHz 假设）。C2-KP 2.6GHz（1 cyc = 385 ticks）下 50000 cycles → 50M ticks > cholesky 总 tick 31.7M → 窗口永不打开 → mem_formal 384/384 Inactive。与 8bff9d1 修的 10 个注入器 inWindow 频率 bug 同类，CHAOSMem 漏网。修法参照：用 mem->clockPeriod() 换算。
2. **protection 对照组缺失（科学缺口）**：§1.2 要求每 cell 两组（none vs secded_poison 等），实际只有 CHAOSCache 的 b9f2435 实现了 protectionModel，L1D formal 只跑了 none。L1D 97.7% SDC 没有 protection-aware 对照 → §4.1 逃逸分解缺 B/C/D 机理区分。
3. **网格远低于设计规格**：多数 formal = target_index=0 + transient_bit_flip 单 cell。设计 §2.1 要求位段 {0,11,31,32,47,63} × ABI 角色 × F1/F2/F3/F4 × 窗口扫描。
4. **F5/F6 子模式全部 deferred**（源码注释确认）：
   - `CHAOSROB.py:22` — "exc_suppress (spec_leak deferred)"；`CHAOSROB.cc:140` spec_leak DEFERRED
   - `CHAOSIQ.py:19` — "wake_omit (src_ready_bitflip/tag_sub deferred)"；phaseOffset 参数已加但模式未实现
   - `CHAOSLSQFwd.py` — 无 fwd_source_sub / phaseOffset 参数（structMode byte_flip/lane_skew 已有）
   - `CHAOSArmTLB.py` — 无 pfn_to_mapped_page (F5) / targetField 属性位（只有整 pfn bit_flip）
   - `CHAOSMem.py:42` — "addr_map_sub needs DRAM coordinate mapping (E3, NOT here)"；eccLogicFault 参数已加
5. **FS 管线未落地**：`configs/fs/kp920_proxy_fs.py` 是 4 行 stub（"V110 params TODO"，只 delegate 到 arm_chaos_fs.py）。checkpoint 流水线（§3.2）未建。fb34343 记录 FS TLB 跨 seed 4/5 超时 —— 正是 checkpoint 要解决的问题。
6. **escape_decomposition.md 有 "? (unit not in map)" 行**（fpu/lsqfwd/example-prf-pilot），ras_escape_analysis.py 的 unit→机理映射表不全；weight(unit) 未实现。
7. **工作区有未提交的 Ruby 测试配置**：`CHAOS/gem5/configs/ruby/CHAOSNoC_test.py`、`ruby_chi_test.py`、`ruby_noctest_launcher.py`（7c854bb/7582e8c pilot 的配置，commit 时被落下）。`CHAOS/gem5/build_ARM_link` 是 build 符号链接，不应提交。
8. **cpu179 是故障机**：所有 formal 的 Honesty note 都写明 n=384 应在健康机复现；目前零复现记录（S6 无进展）。

## 结构性格局（正式结论素材）

- **乱序后端控制/映射类错误 → DUE 主导**（PRF 92.7%、RAT 95.8%、LSQFwd 100%）：method1 现场 "RAT 错 → rename-inconsistency 主导" 在 formal 规模复现。
- **存储结构 → SDC 主导**（L1D 97.7%）：cache 活数据命中几乎必传播，且高度 timing-sensitive（pilot 5/5 Masked vs formal 97.7% SDC，trigger 时序差异）。
- **执行/队列/译码/预测类 → 全 Masked**（IQ/FPU/Exec/Decode/BPU/RAS，两 workload 上 0%，n=384 上界 1.0%）：method1 "整数路径完好" + Veritas 结论在 formal 规模确认。
- 尚不能区分的是：这些 Masked 是真低敏感还是"单 cell 没打中要害"（如 IQ 只测了 wake_omit，没测 src_ready_bitflip/tag_sub —— 后者才是能读 stale 值的模式）。

## 工具面事实（快速参考）

- runner.py 映射 21+ 组件（gpr/physreg/memory/rat/freelist/rob/iq/lsq_fwd/exec/fsu/l1d_fwd/bpu/decode/l1d/l2/l1_tlb/sysreg/exmon/ras/addr_path/ptw）；l1d/l1i/l2 走 C0-CACHE（arm_chaos_cache.py），l1i 有 semanticField 参数。
- campaign.py 产 `runs/<id>/c0000/{manifest.yaml × n, results.jsonl}` + `artifacts/<id>/{heatmap.csv, summary.md}`。
- golden 注册表在 runner.py:59 附近（l1iloop-golden-v1 等）。
- kernels 已建全：branchy_reduce、cholesky_numeric、crc_state、dep_chain、gemm_float、madd_chain、method1_controls、mov_heavy、ptr_chase、spinlock_checksum、struct_field、svd_iterative 等（b93d718 补齐 7 个）。
- 13 个 cpu/o3 注入器目录 + CHAOSMem/CHAOSCache/CHAOSCHI/CHAOSNoC/CHAOSPTW/CHAOSArmTLB/CHAOSArmSysReg 都在源码树。
