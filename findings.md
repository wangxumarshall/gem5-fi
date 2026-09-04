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

## Phase 3.0 补漏（2026-09-04）：CHAOSExMon 是第 9 个漏网注入器

ExMon formal 前置审计发现它同时带两类 bug（不在 32629f7 的 6 注入器清单里）：① runner 恒传 `--probability 1.0` + maxFaults=1 → 恒命中第一个 would-succeed STXR（pilot 5/5 Crash 疑为伪影）；② `inWindow()` 硬编码 `*1000`（C0 2GHz/C2 2.6GHz 均错位）。已修（7108428）：events_to_skip（geometric 0.1，模式方向 eligible 过滤后消耗）+ cpu Param clockPeriod 修窗口。验证：3 seeds 注入 Tick 分散（12561395/11370975/12817420）、golden f247ef3fe6f02cfd、重建零警告。**待 exmon formal n=384 出数后，pilot "5/5 DUE" 结论作废与否以 formal 为准**。

CHAOSArmSysReg 也有 `*1000`（startup()，FS-only，SE formal 不受影响，已文档标注）——留 Phase 5 FS 管线一并修。

## Phase 3.0 审计（2026-09-03 深夜）：lsqfwd formal "100% DUE" 是无效结果（argparse 失败被分类为 Crash）

**证据（runs/lsqfwd_formal_fwd/c0000/results.jsonl）**：384/384 reps `exit=2, faults_injected=0, classification=Crash`。exit=2 是 argparse "unrecognized arguments: --lsq_struct_mode"——kp920_proxy.py 的 LSQFwd mount 读取 `args.lsq_struct_mode/args.lsq_lane_skew_k` 但 argparse **从未定义**这两个参数（只有 arm_chaos.py 定义了）。**gem5 根本没跑，0 次注入**，分类器把 exit=2 当 Crash → "100% DUE" 是纯工具错误。

**影响**：commit 8bff9d1 的 "§2.4 LSQFwd formal: byte_flip P_DUE=100% [99,100] — ALL DUE (fwd_checksum 上转发数据错误全部致命)" **结论作废**。此前的"C0 上 5/5 Masked vs C2 上 100% DUE"对比中的 C2 一侧完全无效。

**分类器缺陷**：runner/classify 把非零退出码一刀切当 Crash，未区分 "argparse/usage error (exit 2)"（工具失败，应记 SimulatorError 或 ToolError）与程序真实崩溃。**修复方向**：exit=2（Python argparse usage）应记 SimulatorError 并排除出 N_valid——否则工具错误会伪装成 DUE。

**待办**：
1. kp920_proxy.py 补 `--lsq_struct_mode/--lsq_lane_skew_k` argparse（从 arm_chaos.py 同步）。
2. runner.py/classify.py：exit=2 → SimulatorError（不是 Crash）。
3. lsqfwd formal 重跑。
4. 复查**所有**已提交 formal 的 exit 码分布——凡是 exit=2 占比高的结果都要重审。

## Phase 3.0 采样偏差审计结论（2026-09-03 深夜，最终）

**受污染的已提交 formal（first-eligible-event 采样偏差，每 rep 命中同一动态事件）**：
| injector | 证据（跨 run 同 tick） | 已提交结论 | 状态 |
|---|---|---|---|
| CHAOSLSQFwd | cycle 恒 1304（修复前） | "100% DUE" | **已修+重跑**（79f32b1: 4.7%/27.6%） |
| CHAOSL1DForward | tick 恒 97358415 | "384/384 Masked" | **已修+重跑**（7d40912: 90.9% SDC） |
| CHAOSBPU | tick 恒 19250000 | "全 Masked" | **待修重跑** |
| CHAOSRAS | tick 恒 21529200 | "全 Masked" | **待修重跑** |
| CHAOSDecode | tick 恒 19251540 | "全 Masked" | **待修重跑** |
| CHAOSExec | tick 恒 19250385 | "全 Masked" | **待修重跑** |
| CHAOSFPU | tick 恒 974889685 | "全 Masked" | **待修重跑** |
| CHAOSIQ | （log 未采样到，推定同） | "全 Masked" | **待修重跑** |

**影响评估（诚实）**：这些单元的"全 Masked"结论**尚未证伪**——同一事件 384 次都 Masked 说明该事件不敏感，但不能推广到整个事件流。修复（events_to_skip）后重跑才能给出单元级结论。优先级：exec/fpu/bpu/decode/ras/iq 各加 events_to_skip（同一补丁模式，~6 个小补丁）。

**已验证不受影响**：PRF/RAT/ROB formal（注入点由 target_index 定向或 RNG 选寄存器，天然分散）；L1D/mem（随机 block/byte 地址天然分散）。

## Phase 3.0 结案（2026-09-04）

**采样偏差 bug 族全关**（8 注入器全修）：l1dfwd 7387649、lsqfwd 9779097、bpu/ras/decode/exec/fpu/iq 32629f7。

**修正后的 SE 单元格局（n=384 或接近，全部 replay 通过）**：
| 单元 | P_SDC | P_DUE | 主导 | 状态 |
|---|---|---|---|---|
| L1D raw | 97.7% | 0 | SDC | 有效 |
| L1D post-check (l1dfwd) | 90.9% | 0 | SDC | 有效（修复后） |
| L1D+SECDED | 0% | 0 | Masked | 有效 |
| PRF X3 | 3.9% | 92.7% | Crash | 有效（天然分散） |
| RAT X3 | 0.3% | 95.8% | Crash | 有效（天然分散） |
| RAT f5_substitute | 0% | 59.7% | Crash+自愈40% | 有效（§2.2 E 对照） |
| FreeList mark_free | 0% | 72-77% | Crash | 有效（X3/X9 目标无关） |
| Decode dest_reg_sub | 0.3% | **24.1%** | Masked 75.7% | **修正**（旧全 Masked 是伪影） |
| LSQFwd byte_flip | 4.7% | 27.6% | Masked 67.7% | **修正**（旧 100% DUE 是 argparse 伪影） |
| ROB D=0 entry_bitflip | 0% | 0% | Masked | **重跑有效确认**（真挂 CHAOSROB，384/384） |
| IQ wake_omit | 0% | 0%（Hang 75.3%） | **Hang 主导** | **大反转**（修正路由后 289/384 Hang——丢唤醒→死锁；旧"全 Masked"是双重伪影） |
| BPU / Exec | 0% | 0% | Masked | **确认**（单元级有效，路由核实无恙） |
| RAS exc_suppress | 0% | 0% | Masked | n=357（24 Inactive） |
| **ExMon stxr_force_fail** | 0% | **100%** | **DUE** | **有效（修复后分散采样）**——STXR 语义破坏全致命 |
| FPU | 0%（上界5.4%） | 0% | Masked | gemm_float 重跑后 Reach=100% 全 Masked，单元级确认 |
| mem (DRAM 后备) | 0% | 0% | Masked | 有效（被 L1/L2 掩盖） |

**方法学新知**：geometric(p=0.1) 的 skip 对**小 eligible 流**会枯竭（FPU 317/384 Inactive）。选择 skip 分布要匹配事件流规模；对极小流（<20 事件），单故障采样本身弱——应换 workload 或更早 trigger。**手工测试坑**：注入器的 seed 参数是 `--<inj>_rng_seed`，generic `--rng_seed` 不喂它——手工复现必须按 runner 的 cmd 构造。

## Phase 3 网格深化：PRF 位段规律（2026-09-04，pilot 规模）

**X3 位段边界（cholesky, n=100/cell，边界扫描 1210fa6 + pilot 45b2b85）**：
| bit | 0 | 1 | 2 | 3-10 | 11-63 |
|---|---|---|---|---|---|
| P_SDC | 100% | 100% | 0% | 0% | 0% |
| P_DUE | 0% | 0% | 100% | 100% | 100% |

- **边界精确定位 bit1/bit2，无过渡带**。X3 是小整数累加器：bit0-1 偏移仍在合法域（静默传播）；bit2+ 偏移越界（崩溃）。
- **定量解释 random-bit formal**：3.9% SDC ≈ 2/64=3.1%（bit0-1 占随机位比例）——观测与理论吻合，两个独立实验互洽。
- **PRF 位段规律（§2.1 E 细化）**：累加器类寄存器呈"低位窄 SDC 窗 + 高位全 DUE"结构，边界由 workload 数值域决定。指针类寄存器（method2 的 x10）预期边界更低甚至全 DUE——待 ABI-class pilot 验证。
- X9 全 bit Masked（非关键路径，位段无关）。

## Phase 3 工具正确性: comp_map 静默改道 bug（2026-09-04，8e01219 修复）

**发现经过**：启动 freelist formal 时发现 gem5 进程带 `--chaos_rename --rename_mode map_bitflip`——campaign.py 的 comp_map 仍带着 `'freelist/rob/iq' → 'rat'` 占位映射（runner 只有 rat 分支的时代写的），而 runner 早已有了真正的 freelist/rob/iq 分支。**这三个注入器的 campaign 全部被静默改道到 RAT 注入器**。

**证据（真机）**：重放 iq_formal manifest → `comp=rat` → gem5 只挂 CHAOSRenameMap，iq_injections.log 从未存在（Phase 3.0 审计里"IQ log 未采样到"的真因）。rob/iq/freelist 三个 formal 的 faults=1 全来自 rename_injections.log。bpu/decode/ras/exmon 的 manifest component 核实正确（1:1 映射，未受影响）。

**作废结论**：
- "§2.3 ROB D=0 entry_bitflip 全 Masked"（8bff9d1, d4c9e8b）——实为 RAT map_bitflip X0
- "§2.5 IQ wake_omit 全 Masked"（d4c9e8b + Phase 3.0 重跑 c7cc34b）——同上；Phase 3.0 对"IQ"的 events_to_skip 重跑实际重跑的也是 RAT

**教训（第三方审计视角）**："faults_injected=1 + 有分类结果"不足以证明注入器正确——必须核对 faults 的**来源日志**与期望注入器一致。comp_map 这类旁路映射表是 silent mis-routing 的温床；新增 runner 分支后必须同步清理占位映射。

## Phase 3 网格深化 #5: RAT F5 legal_domain_sub formal（2026-09-04）

**method1 主对照（§2.2 E："合法但错误映射（历史残留）是否比非法索引更多 SDC？"）**：

| cell (cholesky, C2, n=384) | P_SDC | P_DUE | 对照 map_bitflip (9659974) |
|---|---|---|---|
| X3 legal_domain_sub (F5) | **0% [0,1.0]** | **59.7% [54.7,64.5]** | 0.3% / 95.8% |
| X9 legal_domain_sub | 0% | 0.5% | 0% / 0% |

- **"历史残留→SDC"假设不支持**：合法域替换 0% SDC（n=377 上界 1%）——张冠李戴的映射不产生静默数据损坏，错误值要么崩（59.7%）、要么被掩盖（40%）。
- **新的结构规律**：合法但错误的映射有 ~40% Masked（错误映射的 physReg 被后续写覆盖/值未消费 → 自愈），非法越界索引 95.8% 必崩。**RAT 错误的可掩盖性由"替换值是否在合法域"决定**——这本身是保护设计素材：域校验（range check）能把 DUE 转成可控崩溃，但拦不住掩盖类。
- 与 PRF 位段规律同构：合法域内的错（PRF 低位 / RAT 合法 tag）→ 静默或自愈；域外错（PRF 高位 / RAT 越界 tag）→ 必崩。**"合法域内错误"是 SDC 与 Masked 的分界概念，跨单元成立**。

## Phase 3 网格深化 #6: H2 窗口扫描（2026-09-04）

**§2.1 H2 pilot（cholesky, C2, X3 bit0, ROB × PhysInt 网格, n=30/cell）**：

| PhysInt \ ROB | 96 | 128 (V110) | 160 |
|---|---|---|---|
| 128/160/192 | 100% SDC | 100% SDC | **全 Masked（0% SDC / 0% DUE, faults=1）** |

- **ROB=160 整行掩蔽**：更深 ROB 下 X3 bit0 翻转在 trigger=50K 处完全被掩盖（30/30 一致，replay 无 frozen，注入确实发生）。
- **PhysInt 轴零效应**：cholesky 寄存器压力未到 PhysInt 瓶颈；掩蔽/传播由 ROB 深度单独决定。
- **机理假说**：~~ROB 深度改变 trigger 时点的寄存器活跃年龄分布~~ **已证伪**——trigger 扫描 {20K, 50K, 80K}（覆盖 cholesky 全程）× ROB=160 × PhysInt {128,160,192} 全部 100% Masked（各 30/30，Reach=100%，faults=1，0 frozen）。掩蔽不是注入时点伪影，是 **ROB 深度本身的稳定阈值效应**（≤128 → 100% SDC；160 → 0%），对 PhysInt 与 trigger 均不敏感。机理 open（候选：深 ROB 下关键路径调度变化使错误被重算覆盖/落在 squash 边界；需 readtrace 级分析）。
- 方法学：结论从"V110 单点 formal"升级为"窗口网格"时，**trigger 固定而微架构变化**会引入活跃度混杂——H2 类实验必须配 trigger 扫描才能下因果结论（本次扫描做了，假说被诚实证伪）。

## Phase 4.1: spec_leak（method1 投机泄漏）定论（2026-09-04）

**模式实现**（1ca0346）：机理 = `Rename::doSquash` 抑制一次 HB 回滚（跳过 setEntry 恢复 + freeingInProgress push），错误路径 µop 的目的寄存器保持映射——其 wrong-path 值泄漏进正确路径。采样偏差修复内置（geometric 0.1）。

**formal 结果（branchy_reduce, C2, n=384/cell）**：
| cell | 结局 | 解读 |
|---|---|---|
| X3 | 100% Masked, Reach=100% | 泄漏值被正确路径重写覆盖 |
| X9 | 100% Masked, Reach=88.5%（44 Inactive） | 同上 |
| X19（callee-saved） | 384/384 Inactive（回滚流不可达） | 长活类不频繁重定义 → squash 流里没有 X19 |

**核心发现——"可达性 × 存活性"互斥**：短命寄存器（X3/X9）回滚可达但泄漏值被重写；长活寄存器（X19）泄漏可存活但回滚流不可达。SE 基准 workload 上单次回滚抑制 **100% Masked（n=384 上界 1%）**。method1 的"投机泄漏→SDC"通路需要 wrong-path 写 X19 类的 workload（mispredict 密集调用流）或 FS 场景——SE 侧定格为阴性。

**rename 子系统最终格局（§2.2/§2.3 四注入点）**：map_bitflip 95.8% DUE / f5_substitute 59.7% DUE + 40% 自愈 / mark_free 72-77% DUE / spec_leak 100% Masked——**全部 0% SDC**。"历史残留→SDC"机理在 SE 基准 workload 族上不成立（需要更精确的触发条件对齐）。

## Phase 4.2: fwd_source_sub 定论（2026-09-04）

**fwd_source_sub formal（fwd_checksum_kernel, C2, n=384）**：**P_SDC=37.6% [32.8,42.6] / P_DUE=57.4% / 0% Masked**——F5/F6 批次首个高 SDC 机理模式。

**核心规律——故障形态 > 故障位置**：同一 LSQ 转发路径、同一 workload 上：
- byte_flip（单 bit）：4.7% SDC / 67.7% Masked
- fwd_source_sub（错源整字）：**37.6% SDC / 0% Masked**（8 倍）

错源转发喂给消费者"合法但完全错误"的值——与 PRF/RAT 网格的"合法域内错误→SDC"规律跨单元互洽。**§4.2 保护排序直接素材**：转发源 age/ID 校验比 ECC 更针对此通路。实现时发现并修复双注入 bug（旧 corrupt hook 在新模式下仍触发——验证期间 unlimited-faults 诊断暴露）。

**Phase 4 进度**：4.1 spec_leak ✅（全 Masked+可达性/存活互斥）、4.2 fwd_source_sub ✅（37.6% SDC）。剩余：LSQFwd phaseOffset（相位敏感性曲线）、IQ src_ready/tag_sub、TLB pfn_to_mapped_page、SysReg value_to_legal、CHAOSMem addr_map_sub。

## Phase 4.3: IQ F5/F6 定论（2026-09-04）

**IQ 三模式图谱（madd_chain + cholesky 双 workload，n=384 或 96×4，全部 0 frozen）**：

| 模式 | workload | P_SDC | P_DUE | 结局 |
|---|---|---|---|---|
| wake_omit（F6 丢唤醒） | cholesky | 0% | 0%（Hang 75.3%） | 死锁 |
| src_ready_bitflip（F5 错源唤醒） | madd_chain | 0% | **100% [99,100]** | 全 Crash |
| wake_phase（F6 相位延迟） | madd_chain | 0% | 100%（offset 1-8 平顶） | 全 Crash |
| wake_phase | cholesky | 0% | 3-8%（平顶，CI 重叠） | Masked 主导 |

**三条定论**：
1. **IQ 唤醒类故障无 SDC 通路**（三模式 × 两 workload 全 0% SDC）——唤醒错乱只产生不可用（死锁/崩溃），不产生静默数据损坏。
2. **结局由 workload 依赖密度决定**：cholesky（调度宽裕）Masked vs madd_chain（依赖链无旁路）100% DUE。
3. **wake_phase 代理不捕获 method3 相位签名**（E3 诚实边界）：两个极端 workload 都无单调相位趋势。method3 的相位竞态在 LSU 转发通路的时序，不在调度唤醒相位——复现它需要 LSQFwd 侧的转发相位偏移。设计文档 §2.5 E 的"相位敏感性曲线"预期在本代理上不成立，根因是代理位置错位。

**Phase 4 进度**：4.1 spec_leak ✅、4.2 fwd_source_sub ✅（37.6% SDC）、4.3 IQ F5/F6 ✅。剩余：TLB pfn_to_mapped_page+targetField（4.4，FS 前置）、SysReg value_to_legal（4.5）、CHAOSMem addr_map_sub（4.6）。

## Phase 4 完整收口（2026-09-04，6/6 模式）

| # | 模式 | 实现 | formal 结果 | 定论 |
|---|---|---|---|---|
| 4.1 | ROB spec_leak | 1ca0346 | branchy X3/X9 全 Masked, X19 不可达 | 可达性×存活互斥；rename 四注入点 0% SDC |
| 4.2 | LSQFwd fwd_source_sub | 05db0e2 | **P_SDC=37.6%** [32.8,42.6], 0 Masked | **故障形态>故障位置（8 倍 SDC）** |
| 4.3 | IQ src_ready_bitflip + wake_phase | 9db60d6 | madd 100% DUE 双模式，相位平顶 | IQ 唤醒类 0% SDC；wake_phase 代理不捕获 method3 相位（E3 边界） |
| 4.4 | TLB pfn_to_mapped_page | e22b775 | 实现+SE 回归 ✅；FS formal 排 Phase 5 | 静默错页通路（活页 pfn 替换） |
| 4.5 | SysReg value_to_legal | e22b775 | 实现+SE 回归 ✅；FS formal 排 Phase 5 | 静默配置错误通路（跨白名单值替换） |
| 4.6 | Mem addr_map_sub | 7d21c07 | 384/384 Masked | **DRAM 层故障形态无关律**（bit 翻转与错位写同为 0% SDC） |

**Phase 4 三大横断规律**：
1. **合法域内错误是 SDC 的核心形态**——fwd_source_sub（37.6%）是唯一高 SDC 模式，错值全程合法；域外错（RAT 越界/PRF 高位）必崩或自愈。
2. **单元×形态×workload 三维决定结局**——同单元不同形态差 8 倍（LSQFwd）；同形态不同 workload 差 20 倍（F5 madd 100% DUE vs cholesky Masked）。
3. **代理边界诚实化**——wake_phase 不捕获 method3 相位签名（相位在 LSU 转发时序非调度唤醒）；DRAM 层错位写在缓存驻留 workload 上不可达（需 STREAM 类暴露）。

**F5/F6 已实现模式总账**：spec_leak / fwd_source_sub / src_ready_bitflip / wake_phase / pfn_to_mapped_page / value_to_legal / addr_map_sub —— 7 个新模式 + 既有 wake_omit/map_bitflip 等，SE 侧全部有 formal 定论，FS 侧（TLB/SysReg）待 Phase 5 checkpoint 管线。
