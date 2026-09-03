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

## Phase 1/2 结果补记（2026-09-03 晚）

- **Phase 1 完成**：6 formal 提交（d4c9e8b）；CHAOSMem ratio 修复（b7433dd，C2→385/C0→500，真机验证 Tick=first_clock×ratio 精确）；mem formal 有效重跑（d88dcc7）：384/384 Masked——DRAM 后备字节被 L1/L2 掩盖（工作集驻留缓存，后备字节不被读回）。
- **campaign.py --jobs>1 从未工作过**（_do_rep 闭包不可 pickle）——此前所有 formal 都是串行。修为模块级 _PoolRep 类（d88dcc7）。
- **protection_model 全链路打通**（19d8a4b）：campaign→manifest(fault.protection_model)→runner(--protection_model)→config(CHAOSCache/CHAOSMem)。pilot 实证 ladder 生效（`bits=1 -> Corrected`）。
- **L1D 风险反转首证**：raw 97.7% SDC vs secded_poison 0%（n=384 各）。限定：transient_bit_flip 只测 Corrected 档；2/3-bit 档需 local_mbu（Phase 3）。
- **进行中**：§2.7 H.③ l1dfwd post-check escape formal（n=384 后台）。

### 方法论教训（新增）

1. trigger 时序是 cache 类注入的**第一敏感变量**（pilot 5/5 Masked vs formal 97.7% SDC，L1D）；mem 类同理（后备字节是否被读回）。
2. 存储层级的**掩蔽梯度**：L1D 数据错 → SDC 主导；DRAM 后备错 → 全 Masked（上游缓存挡住）。这本身是 §4.1 逃逸分解的一维。
3. protection-aware 对照必须**匹配 fault 模型的位计数**：F1 单 bit 只测 Corrected 档。ECC 粒度轴 {1,2,3-bit} 要用 local_mbu 才能测 Latent/SilentEscape 档。

## Phase 2.2 调查：l1dfwd formal 384/384 Masked 是采样伪影（INSTRUMENTATION BUG）

**现象**：§2.7 H.③ l1dfwd post-check formal n=384 全 Masked（与"post-check ≥ raw 97.7%"的预期相反）。

**排查过程（全部真实实验）**：
1. 定向 mask=0xFF / 0xFFFFFFFFFFFFFFFF，checksum 仍 golden → 疑 hook 无效。
2. `max_faults=0`（无限）+ prob=1.0：**65541 次注入**（每个 load 都到达此 site），程序 Aborted（exit 134，大规模损坏）→ **hook 完全有效，数据确实流入架构态**。
3. 关键证据：max_faults=1 时每次 run 的唯一注入都是 **addr=0x769a0, tick=97358415**（跨 seed/跨 first_clock 恒定）——注入器在窗口打开后总是命中**同一个动态 load**，而这个 load 是被 squash 的（错误路径），损坏被丢弃 → 全 Masked。

**根因**：CHAOSL1DForward 的单故障采样语义 = "第一个过概率门的 eligible load"，而 l1d_reduce 的指令流确定性使第一个 eligible load 恒为同一条（squashed）指令。这不是 protection 语义，是**采样偏差**。

**修复方向**（Phase 2.2 待办）：注入器需要"随机跳过前 N 个 eligible 事件"（poisson/rand-int 偏移，由 rng_seed 驱动），使单故障在 eligible 事件流上均匀采样。同类风险：所有 "hook-on-event + max_faults=1" 的注入器（l1dfwd/lsqfwd/exmon/bpu 等）都有此陷阱——lsqfwd formal 100% DUE 可能部分受益于同样偏差（它的第一个 eligible 转发点可能总是致命的），需要复核。

**诚实结论**：l1dfwd_formal_reduce 的 384/384 Masked **无效**（不测 post-check escape），已作废。修复注入器采样后重跑。

## Phase 2 最终证据（2026-09-03 夜）

**L1D 三层定论（§4.1 逃逸分解的 L1D 部分，n=384 各组，replay 通过）**：
| 通路 | P_SDC [95% CI] | 逃逸机理归类 |
|---|---|---|
| raw（cache 数据字节） | 97.7% [95.6, 98.8] | A（无保护基线） |
| + SECDED（secded_poison） | 0.0% [0.0, 1.0] | F1 单 bit 全被纠正 |
| post-check escape（load 回填） | **90.9% [87.6, 93.4]** | **D（ECC 校验后盲区）** |

→ "给 L1D 数据加 SECDED"对 F1 有效（97.7→0），但 ECC 后通路（fill→PRF）是 90.9% 的逃逸盲区——保护投资应同时考虑 check-after-path。这是 §4.2 排序表的直接证据行。

**采样偏差 bug 族（新发现，影响面待查）**：hook-on-event + max_faults=1 的注入器若"总是第一个 eligible 事件"，确定性流下全部 reps 命中同一动态事件。CHAOSL1DForward 已修（events_to_skip, geometric p=0.1）；lsqfwd（formal 100% DUE）、exmon（pilot 5/5 DUE）、bpu/ras/decode（全 Masked）的结果都需用"不同 seed 注入 addr/tick 是否分散"来复核——分散 = 无此偏差；恒定 = 有。

## Phase 3.0 审计（2026-09-03 深夜）：lsqfwd formal "100% DUE" 是无效结果（argparse 失败被分类为 Crash）

**证据（runs/lsqfwd_formal_fwd/c0000/results.jsonl）**：384/384 reps `exit=2, faults_injected=0, classification=Crash`。exit=2 是 argparse "unrecognized arguments: --lsq_struct_mode"——kp920_proxy.py 的 LSQFwd mount 读取 `args.lsq_struct_mode/args.lsq_lane_skew_k` 但 argparse **从未定义**这两个参数（只有 arm_chaos.py 定义了）。**gem5 根本没跑，0 次注入**，分类器把 exit=2 当 Crash → "100% DUE" 是纯工具错误。

**影响**：commit 8bff9d1 的 "§2.4 LSQFwd formal: byte_flip P_DUE=100% [99,100] — ALL DUE (fwd_checksum 上转发数据错误全部致命)" **结论作废**。此前的"C0 上 5/5 Masked vs C2 上 100% DUE"对比中的 C2 一侧完全无效。

**分类器缺陷**：runner/classify 把非零退出码一刀切当 Crash，未区分 "argparse/usage error (exit 2)"（工具失败，应记 SimulatorError 或 ToolError）与程序真实崩溃。**修复方向**：exit=2（Python argparse usage）应记 SimulatorError 并排除出 N_valid——否则工具错误会伪装成 DUE。

**待办**：
1. kp920_proxy.py 补 `--lsq_struct_mode/--lsq_lane_skew_k` argparse（从 arm_chaos.py 同步）。
2. runner.py/classify.py：exit=2 → SimulatorError（不是 Crash）。
3. lsqfwd formal 重跑。
4. 复查**所有**已提交 formal 的 exit 码分布——凡是 exit=2 占比高的结果都要重审。
