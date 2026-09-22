# Findings — 2026-09-07 方案全覆盖差距盘点

> 依据：《KUNPENG920SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md》（1069 行，下称"方案"）
> 方法：逐章核对 `fi-wangxu` HEAD（`ebae0eb3`）实际源码 / artifacts / tools，区分"已完成（有实证）"与"待做"。
> 用途：支撑 `docs/superpowers/plans/2026-09-07-kunpeng920-sdc-complete-coverage.md` 的任务分解，确保无遗漏。

## 1. 已完成且仓库内有实证的项（不在新计划中重复）

| 方案条目 | 实证（仓库内） |
|---|---|
| 18 个注入器（§5 各单元 B 段） | `CHAOS/CHAOS{Reg,PhysReg,Cache,Mem,LSQFwd,ArmTLB,AddrPath,PTW,RenameMap,FreeList,ROB,IQ,FPU,Exec,L1DForward,BPU,ExMon,ArmSysReg}`，vendored 副本齐全（`CHAOS/gem5/src/...` 18 处目录核对） |
| F1–F6 + PCE 全故障模型（§3.1） | F3（`7f538c4`）、F5（RAT/freelist/LSQ/TLB pfnOffset/SysReg value_to_legal/Mem addr_map_sub）、F6（LSQFwd phaseOffset + IQ wake_omit/wake_phase `8850fa66`）、PCE（CHAOSL1DForward `1bb18f0`） |
| 附录 D 缺陷 D1–D7 | `0ae28fe`（D2）、`56023c3`（D1+D5+D6）、`58be899`（D4+D5）、`4ed645b`（D3）；D7 mask==0 早退在 8 个注入器 .cc 中核对存在 |
| campaign/runner/classify 九类 + Wilson + manifest v2 | `tools/campaign.py`（并行+双层超时组杀）、`tools/runner.py`（v2 字段、read-trace、fail_count oracle、PA 分类）、`tools/classify.py` |
| protectionModel ECC 后处理（§4.2） | CHAOSCache `applyProtectionModel()` + CHAOSMem secded；`artifacts/l1d-ecc/`（n=384×6：raw-b1/b2/b3 vs secded-b1/b2/b3，1-bit Corrected / 2-bit 含毒化） |
| kp920_proxy 配置（§4.1） | `configs/se/arm_chaos.py`（--kp920_proxy）+ `arm_chaos_fs.py:54` |
| FS checkpoint 流水线（§10.2） | `configs/se/fs_checkpoint.py`（boot 890s → restore 注入，`c82e59a`） |
| kernel 库（部分） | workloads/directed 21 个：reg_chain/l1d_reduce/l1i_loop/neon_lane/fp_fwd_kernel/cholesky_numeric(±both)/accum_kernel(±both)/ptr_chase/fwd_7case×7/branchy_leak/call_ret_heavy/dep_chain/exmon_kernel/fault_kernel |
| formal 结果（部分） | PRF X3 位段 n=96×8（`artifacts/prf-formal`）；LSQ 5 模式 n=64×5（`artifacts/lsq-matrix`）；method1 Fisher n=384×2（`artifacts/m1-formal-*`，p=1.189e-71 PASS）；L1D ECC n=384×6；H1 read-trace n=384×4（P(SDC\|reads>0)=1.000）；H2 窗口扫描 n=96×12（天花板效应诚实标注） |
| §8.1 逃逸分解工具 | `tools/escape_decomp.py` + `docs/paper/tables/t6-escape-decomp.md`（A 机理 3282 事件 100%；B–F no data 如实标注） |
| §8.3 指纹库 + LOO | `tools/sdc_fingerprint.py` + `tools/loo_validate.py` + t7（76 事件 Top-3 100% ≥60% VALID） |
| H5/H6/H7 闭环（§6.1） | main 分支已闭环（方案 6.1 表标"已闭环"） |
| CHAOSROB spec_leak | `5502276`（doSquash hook，branchy_leak numSpecLeak=3） |
| 论文初稿 | `docs/paper/sdc-fi-paper.md`（125 行，8 章）+ tables t1–t7 |
| x86 配对（C1 前置） | `configs/se/x86_chaos.py` + reg_chain_x86（directed RAX/RCX，`46ddf78`+修正） |

## 2. 待做缺口（新计划的任务来源，逐条对应方案章节）

### 2.1 注入器/工具缺口
- **§5.8B CHAOSCache targetField**：现仅 `data` + L1I 语义字段（rd/rn/rm/opcode，`CHAOSCache.cc:347-381`）；**tag/valid/dirty/repl/coh 字段级未实现**；**victim（`base.cc WritebackBlk` hook）未实现**。
- **§5.7B CHAOSArmTLB**：`pfnOffset`（F5 偏移→DUE 方向）已有；**`pfn_to_mapped_page`（翻到另一活页→静默 SDC，最危险路径）未实现**；iTLB 挂载、L2 TLB、`protectionModel` 参数未实现（`CHAOSArmTLB.py` 无该参数，核对 2026-09-07）。
- **§5.11/S5-2 CHAOSRAS**：注入器未写（分析半边 escape_decomp.py 已有，注入半边缺）。
- **§5.9 CHAOSBPU**：hook 在 `BAC::predict`，但 **decoupledFrontEnd 与 stdlib board 不兼容（空 stats 实测）→ 当前不可用**；联合观测 `P(squash 后架构态==golden)` 未做。
- **§4.3/§6.3 H3 跨单元 read-trace**：ReadTrace 仅 CHAOSPhysReg 有；**RAT/ROB 无 read-trace API**（`CHAOSRenameMap/*.cc`、`CHAOSROB/*.cc` grep 无 ReadTrace）。
- **D9（G6 广触发）**：pc/committedInst/event 触发模式未实现。
- **§4.5 manifest dynamic_context**：mapped_phys_reg/freelist_size/cache_residency/lsq_source_seq/tlb_asid/committed_inst_at_inject 未落。
- **§5.4 CHAOSExMon stale_reservation**：单线程 SE 不可达（需多核场景），诚实标注待做。

### 2.2 kernel 缺口（§5 各 D 段）
- **§5.6D**：gemm_float/gemm_double（GEMM popcount 中位 12/28 锚点）、svd_iterative（单比特中位 1–3）、fma_reduction_kernel。
- **§5.10D**：MADD 链、SMULH、ADDS→B.cond 条件链、整数 reduction、indirect_jmp。
- **§5.2D 对照组**：pure_fma/pure_spmv/pure_gather/tri_solve、movbe_kernel（在 fi_research/probes 有 .c 但未入 workloads/directed 正式库）。
- **§5.8D**：struct_field_kernel、crc_state_kernel。

### 2.3 formal campaign 缺口（§4.6 n=384 标准）
- PRF formal 现 n=96/cell（方案要求 384；关键 cell 663）。
- **§5.6 FSU**：CHAOSFPU 机制就位但 **零 formal 数据**（neon_lane FP 头稀少 REJECT 超时）；向量 PRF vs FSU 通路 KS 检验未做。
- **§5.10 Exec 阴性对照 formal**：`P_SDC(Int) << P_SDC(FSU/转发)` 未正式量化。
- **§5.8**：字段级×protection formal、L2 size sweep {256KiB,512KiB,1MiB}（H4）、L1I SED vs SECDED 两组差、PCE vs raw 对比。
- **§5.7 FS formal**：checkpoint 后 TLB pfn→活页 P_SDC / pfn→未映射 P_DUE + ESR DFSC vs `0x96000004`、PTW ptwEcc on/off（H7 formal）、SysReg 白名单 cell。
- **§5.2/5.3 formal**：RAT/freelist/ROB（P_SDC vs 距提交距离 D 曲线、exc_suppress DUE→SDC 转化率、损坏 popcount 中位 >16）。
- **附录 B method2 三根因区分**：PRF/AGU/TLB 三种注入的 ESR/PC/x10 形态比对打分（现仅 SimulatorError≈method2 野指针形态的定性注记）。
- **§6.4/§8.3.3**：F3/F6 相位敏感性曲线（method3 塌方比 ≥5×、三必要条件去一归零）、电压/相位数据。

### 2.4 第 7 章 openEuler 诊断引擎（维度③，整体缺）
- `tools/` 无任何 ESR 解码/journalctl 解析/七步法 CLI（grep journalctl|dmesg 零命中）。
- `sdc-diagnosis` 项目**本机不存在**（find /home/sdc 无此目录）→ 规则引擎需在本仓库自建（方案 7.9 说"引用而非重写"，但载体缺失时以方案第 7 章为规范源自建并标注）。
- core179 六案回放（P1+P5+N3→高置信度）未做工具化验证。
- §7.7 反哺（单元 P_SDC→权重先验、method 签名→规则库版本化）未做。

### 2.5 第 8 章建议产出（维度④）
- §8.1 逃逸分解 B–F 机理无数据（需 PCE formal→D、ecc_logic_fault→E/F）。
- §8.2 保护优先级排序表（formal 数据驱动版）未产出。
- §8.3 DFT 向量打包（method1/2/3 kernel+触发条件+健康/次品签名对照）未产出。
- §8.4 N1 TRM Table 9-1 差距分析未产出。

### 2.6 论文/登记（§9、附录 G）
- 论文 125 行初稿，未达 §9.1 五贡献点全覆盖。
- **AGENT_TASKS.md 不存在**（方案 G.1 要求的单行登记簿）。
- 方案 §6.1 假设表 H0/H3/H4/H8+ 未回填 formal 判定（H1/H2 已回填）。

### 2.7 环境门控项（不可在本机完成，须显式登记不遗漏）
- S4 系统级 CHAOSCHI/CHAOSNoC/CHAOSHCCS（~20 补丁独立子项目，E3/E4）。
- S6 健康机复现（需第二台健康鲲鹏机）。
- S7 实机校准（需授权实机）。
- D10（G7 ASan/UBSan，SConstruct socket configure 环境受阻，deferred CI）。
- CHAOSDecode（P4，方案 §5.11 明示"低优先级，可跳过"）。

## 3. 关键运行事实（复用）

- 构建产物陷阱：`scons -C CHAOS/gem5` 产物落仓库根 `build/ARM/gem5.opt`，须 cp 回 `CHAOS/gem5/build/ARM/`（memory 已记）。
- campaign 与构建绝不并行（H1 首跑作废教训）。
- `-j16` 上限（29GB 主机 OOM）。
- FS checkpoint：`configs/se/fs_checkpoint.py`，restore 后 Atomic（O3-switch 待续）。

---

# 新使命 Findings — SDCShield FI 评估（2026-09-22 起，Phase 8）

## F-SS-1 SDCShield 是什么（sdcshield/ README.md + CLAUDE.md，子模块 07be34e2）
- **本质**：Intel OpenDCDiag(sandstone) 的 ARM64 移植——CPU/系统缺陷检测工具（"硅是否正常工作"）。291 用例（PROD 282 / BETA 4 / SKIP 5，2026-09-17 实测），检测机制 = 计算/拷贝后与 golden **逐字节 memcmp**（`memcmp_or_fail`/`report_fail`）——"不崩溃但算错位"正是 SDC 检测。
- **软件形态**：meson C/C++ 项目；每测试 fork 子进程 + 每 CPU worker 线程（ForkMode: no_fork / fork_each_test 默认 / exec_each_test）；`-n 1` 可单线程确定性运行；运行期读 /proc（EDAC ce/ue、中断）、sysfs 拓扑、getauxval(HWCAP)。
- **用例域**（与 FI 位点映射相关）：memcpy/cachebounce/lock+cmpxchg/SIMD/FMA 穷举/bigint/CRC32/zlib/zstd/isal_igzip/Eigen GEMM+SVD/OpenBLAS GEMM（mdim 16..4096 扫 L1→DRAM）/SLEEF/pocketfft/ipsec×46/openssl_sha*/arm64_sdc 触发配方（power_virus_dit、ooo_dep_chain_arm、lsu_store_forward_arm、l2c_cross_cache_line_arm、mmu_split_tlb_arm、movbe 探针组、sve512_*）/IST placeholder。
- **检测信号**：report_fail/memcmp_or_fail → 测试 `result: fail`（YAML 日志）+ 整体非零退出；`-F` 首检即停。smi_count/ist 是 placeholder 诚实 skip；mce_check 是真 EDAC 后端测试（/proc/interrupts EDAC ce/ue 计数）。
- **关键先例**：`sdcshield/scripts/eigen-sve-double/gem5/` 已做过 **gem5 SE 模式功能验证**（eigen_svd_cdouble_sve @ VL=512，宿主 VL=256）——SE 跑 sdcshield 有直接先例（细节待查，见 F-SS-2）。
- **文献锚点**（README 载）：SEVI >92% SDC 事故由 FMA 指令贡献 → vendored 库选型：向量 FMA GEMM > 哈希/加密 > 压缩 > SVE 超越函数（31 篇文献综合，docs/paper/SDC_RESEARCH_SYNTHESIS_CN.md）。
- **多线程 ULP 假阳性已知**：eigen_svd_double/eigen_sparse 全核多线程偶发 ULP 级 fail（需 -n 1）——gem5 确定性执行下预期消失（需 no-injection 对照实证）。
- **子模块纪律**：sdcshield 自身 CLAUDE.md 要求 DCO（Signed-off-by 强制，CI 拒绝无 DCO 提交）；x86-64 路径不动。

## F-SS-3 SE 探针实验（2026-09-22，本日实测）——真框架二进制能否在 gem5 SE 跑
- **sdcshield 最小构建成功**（本机 openEuler 24.03 SP3 aarch64 = 基准平台）：`PKG_CONFIG_PATH=./third-party/eigen5 meson setup builddir --buildtype=release && ninja -C builddir` 403/403 通过；系统 zlib 1.2.13/zstd 1.5.5/gmp 6.3.0/isal 就位，openblas/sleef/acl 优雅跳过 → **350 个用例可运行**（含 fma/mesh_upi 全系/memcpy 系/crc32/zstd19/zlib/bigint/lock 等）
- **原生参考**（宿主直接跑）：`sdcshield -e fma -t 100 -n 1 -f no` → `exit: pass`，退出码 0——探针的 golden 对照
- **探针配置**：`fi_research/probes/se_sdcshield_probe.py`（AtomicSimpleCPU + numThreads=8 + 单 Process 挂 8 槽 + system.multiThread=True；机制：Process::initState 只激活 contextIds[0]，其余 TC 保持 Halted 供 clone(CLONE_THREAD) 取用）
- **第 1 次失败（如实）**：`BaseCPU::registerThreadContexts: Assertion system->multiThread || numThreads == 1 failed`（src/cpu/base.cc:495）→ 修复=System 加 `multiThread = True`，重跑中
- `-f no`（ForkMode::no_fork）是 SE 必需（fork syscall 无 handler）；`-n 1` 钉单 worker 线程

## F-SS-4 雅典 Harpocrates 论文 × 本仓 SDC-ED 方法论（Explore agent 报告消化，2026-09-22）
**论文身份**：P1 = Harpocrates, ISCA'24（Karystinos/Chatzopoulos/Fragkoulis/Papadimitriou/Gizopoulos@雅典 + Gurumurthi@AMD）；P2 = Harpocrates++, IEEE Micro'26（同组）。PDF 在 docs/papers/ref/，笔记在 sdcshield/docs/paper/ref/research-notes/experiments/E08/E09。
**论文 FI 设置**：gem5 v22+GeFIN，x86-64 OoO；6–7 结构（IRF/L1D/int加/int乘/SSE-FP加/SSE-FP乘，P2 加 LSQ-SQ）；位阵列=瞬态单比特（bit/cycle 均匀随机），FU=门级永久 stuck-at；K=10 seed×N=100；检出=偏离 fault-free golden（P1 FPGA 臂用 DIFT 污点 oracle，更严）；检测率口径分母剔除无效注入。
**本仓复现（docs/harpocrates/method.md + reproduction-report.md）**：CHAOS gem5 25.1.0.1，ArmO3CPU=Taishan v110，**AArch64 SE 模式**；7 结构瞬态单比特 + FU 两级（CHAOSFUPerm 执行级永久 + 合成门级 netlist Kogge-Stone 1154 门/移位乘 44418 门）。
**ED 度量**（docs/sdc-ed/method.md:44）：`ED(S)=Σ_u w_u·ρ_u·q_u·A_u(S)`，w=位占比、ρ=SDC 转化率（SFI 标定回填）、q=checker 可观测性（golden-diff=1.0，部署 checker<1）、A=激活覆盖；七维 covUnits。ρ 标定实测（N=100）：irf 0.05 / intadd 1.0（永久语义上界）/ intmul 0.82 / lsq 0.69 / l1d 0.04 / **fsu 0.00（200/200 Masked，值依赖）** / mmu 0.00（SE）/ l2c_tag 0.50 / l2c_data-none 0.41 / l2c_data-secded 0.00；**非 L2C 单元的"检出"几乎全是 Crash，真 SDC 只出现在 L2C 臂**（SDC/Crash 必须拆口径）。
**harp_wrap --checker 先例**（tools/harp_wrap.py:140-252，SDCED-7.1）：双通道同种子复算+self 比对 epilogue（CHECKER=FAIL 即检出），无 golden 部署检测臂；实测 0.10 vs golden-diff 0.05（采样窗口协议差，未统一——比较口径前必须统一窗口）；**结构盲区：永久 FU 故障破坏两通道同样→漏检；该 permanent×checker 子臂 deferred 从未跑**——sdcshield 评估可补此缺口（sdcshield golden 是否每次迭代重算=同样的永久盲区问题，需逐测试核查）。
**公平性纪律（_lift 两轮 + CE 系列教训）**：预注册判据不可改、阴性结果如实归档；N≥400/序列 + Wilson 95% CI；raw 与 active 双口径（active 分母剔除 Inactive/SimErr）；臂-采集配置一致性先验证（l2_assoc 16 vs 8 教训）；比较检出口径前统一采样窗口；SDC 与 Crash 拆分（崩溃≠算错）；wrapper/工具底噪必须测（无注入对照臂）；重负载超时标定（conflict_seq 曾撞 300s 默认超时→改 1200s/900s）；timeout 判 Hang。
**已知缺陷**（度量层四缺陷）：wrapper 底噪 / max 映射钝化 / 足迹盲区（地址足迹型 L2 激活 covUnits 看不见）/ evolve 分母耦合——sdcshield 评估设计须避免同型坑。
**SE 边界**：AddrPath(D2)/PTW(D3) 钩子 SE 不触发（translateMmuOff），MMU ρ 的 FS 臂缺；D-FS-O3-switch deferred（atomic-only 分类已验证可行）。
**本仓论文**：docs/paper/sdc-fi-paper.md 已删（80df3c51），终态在 853133cb（155 行 8 章，五贡献）。

## F-SS-5 CHAOS 基础设施地图（Explore agent A 报告消化，2026-09-22）
**⚠ 阻塞级事实：本仓 gem5.opt 陈旧**——`CHAOS/gem5/build/ARM/gem5.opt`（2026-08-27）只含 **7 个 CHAOS 类**（nm 实证：Reg/PhysReg/Mem/Cache/LSQFwd/AddrPath/PTW）；源码树有 **21 注入器 + CHAOSCov**。姊妹仓 `/home/sdc/wangxu/gem5-fi-fuzz/CHAOS/gem5/build/ARM/gem5.opt`（2026-09-21，1.13GB）全 22 类齐。**任何注入实验前必须先取全量二进制（拷贝或重建）**。
**SE 主配置** `configs/se/arm_chaos.py`：stdlib SimpleBoard + PrivateL1PrivateL2(64K/64K/512K) + DDR3_1600 1GiB + SimpleProcessor(默认 **O3**，可选 Timing/Atomic/Minor)；`--kp920_proxy`=V110（ROB128/PhysInt160/PhysFloat192/LQ48/SQ42/宽4/2.6GHz）；15 个 `--chaos_*` 臂直接实例化挂 board；workload 经 `set_se_binary_workload`。cache 臂走 `arm_chaos_cache.py`（--target l1d/l1i/l2 + --target_field data/tag/valid/dirty/victim/... + --protection_model none/sed/secded/secded_poison/parity_interleaved）。
**注入触发**：构造时 geometric(probability) 间隔 + attackCheck 周期事件，first_clock/maxFaults/lastClock；**CHAOSReg 有 PCTarget 参数**（PC 触发，arm_chaos.py 未接 CLI）；hook 型（FPU 源读/L1DForward 等）用 per-event probability。
**FS 流水线** `configs/se/fs_checkpoint.py`：boot 阶段 Atomic boot 至 KernelBooted → save_checkpoint；inject 阶段 set_kernel_disk_workload(checkpoint=...) restore，**restore 后恒为 Atomic**（stdlib 无 clean switchCpus，D-FS-O3-switch deferred）；FS 臂仅 armtlb/sysreg/ptw。`arm_chaos_fs.py`：全 boot 版，`--readfile`(m5 readfile) 是唯一的 guest 用户态工作负载发射机制；dmesg/PL011 terminal 是结果回收通道（oops grep）；**本仓无任何 FS 流程运行过 guest 用户态工作负载**。fs_bigLITTLE.py **无 switchCpus**（cpu_types 无 O3）。FS 实测：boot 890s，restore+run ~13s/run（fs_tlb_formal.sh，n=96 级别可行）。
**工具链**：runner.py（manifest→gem5 命令→注入日志计数→golden/fail_count oracle→分类；**FS 组件 sysreg/ptw/l1_tlb/l2_tlb 在 SE runner 中直接拒绝**）；classify.py 六类（SimulatorError/Hang/Crash/Inactive/Masked/SDC）+ 九类 ECC 扩展（Corrected/DetectedContained/Latent——来自注入日志标记**非工作负载侧**）——**不存在工作负载侧 Detected 类**（harp_wrap CHECKER= 无工具解析，SDCED-7.1 是 ad-hoc 跑的）；campaign.py（YAML 轴→笛卡尔 cell→N/cell（pilot 100/formal 384）→cells.csv 带 Wilson CI；SE-only；G0 replay 是 no-op pass）。GOLDEN_IDS 14 个；oracle 格式：`FINAL=<16hex>` 或 `iters=N fails=M`。
**注入器×CPU 依赖**（源码 dynamic_cast 实证）：**任意 CPU 可用**：CHAOSReg（架构寄存器，ThreadContext 级）、CHAOSMem（DRAM+ECC）、CHAOSCache（cache 字段级+保护模型）、CHAOSExMon（ARM local monitor）、CHAOSArmTLB/CHAOSArmSysReg/CHAOSPTW（需 FS 才有意义）；**O3-only**（14 个）：PhysReg/AddrPath/LSQFwd/RenameMap/FreeList/ROB/IQ/RAS/Exec/FPU/L1DForward/BPU/FUPerm/GateFU + CHAOSCov。CHAOSBPU 需 decoupledFrontEnd（stdlib 板不可用——CE-3 已引用既有证据收口）。
**工作负载**：workloads/directed ~30 个静态 aarch64 ELF（reg_chain/gemm/svd/fma/movbe/...）+ workloads/harp/（12 序列）；golden 三方一致纪律（native==gem5）；**无"任意二进制包 checker"的通用包装设施**（harp_wrap 只包指令序列）。
**env.sh**：`/home/sdc/gem5-deps/env.sh` 本机不存在；当前 gem5.opt 本机可直跑（ldd 无缺失）。构建纪律：scons 产物落仓库根 build/ 须 cp 回 CHAOS/gem5/build/；campaign 与构建绝不并行。
**sdcshield fma 测试语义实证**（agent 引源码）：fma.cpp NEON FMA vs `fmaf` 软件参考逐元素比对——**in-run 双通道参考模型**（永久 FU 故障双通道同损→结构性盲区，正是 harp_wrap deferred 子臂的问题）；框架退出码 0=pass/1=failed。

## F-SS-6 SE 真二进制探针终局（2026-09-22，全部实测，Phase 8.5 裁决依据）
- **探针基建可行**（`fi_research/probes/se_sdcshield_probe.py`，多 CPU 模式）：cpu0=sdcshield + cpu1..6=/bin/true（退出后 TC 进 Halted 池供 clone(CLONE_THREAD) 取用）+ Process 唯一 pid + system.multi_thread；/bin/true 对照 **exit 0 @ tick 116.5M**——gem5 SE 动态链接对简单二进制健康（~116M tick 全花在 ld.so 模拟上）。
- **sdcshield 真二进制 SE 被实证阻断**（三重独立证据）：
  1. **确定性 pre-main 崩溃**：fma/memcpy0/--dump-cpu-info 三种入参同 tick（123,543,000±3k）同地址（0x343662696c2f7703）page fault——Exec trace 实证崩溃循环：`ldr x4,[x11],#16`（16 字节步长指针数组迭代）从含字符串 "sr/lib64" 的内存装入"指针"→`cbz x4`→解引用失败；guest 从未输出 `command-line:` 首行 → **main() 未达**，崩溃在 ld.so/静态 ctor 区（sdcshield 链 10 个库：libcrypto/libstdc++/libgmp/libzstd/libz/...）
  2. **prctl 是 fatal 级未实现**（syscall_emul.cc:79）：solo 模式（无 helper）跑到 `fatal: syscall prctl (#167) unimplemented` ——即使修好 1 也会撞此墙（glibc/框架线程命名调用）
  3. **信号 syscall 被忽略**（rt_sigaction/rt_sigprocmask warn-only）——框架的崩溃处理通道（--on-crash）在 SE 无保真度
- **修复属 gem5 SE 开发**（prctl stub ~5 行 + pre-main 崩溃根因）——记为可选 stretch 任务，不作为主战役前置。
- **solo vs 多 CPU 模式崩溃点不同**（page fault vs prctl）——guest 指令流有配置相关分歧（未根因，登记）；不影响上述三重阻断结论。
- **结论**：真二进制唯一可运行环境 = **FS（真 Linux：prctl/信号/线程全真）**；SE 的可行载体 = **提取式检测语义内核**（sdcshield 自身 SE 先例即 standalone 提取二进制；本仓 workloads/directed 30 个静态 ELF 全此模式）。

## F-SS-7 设计裁决（Phase 8.5/8.6，基于 F-SS-1..6 全部实证）
**裁决一（FS vs SE）= SE 为主战场（O3，提取式双通道内核）+ FS 为保真验证臂（真二进制，小 N）**
依据：① SDC 高发位点 FSU 13.6-69.5%/PRF 饱和/LSQ-fwd 37.6-90.9%/L1D-fwd 90.9% 全部 O3-only（SE 独有）；② 检出率需 N≥100-400/cell（SE 秒级 vs FS 分钟级，repo 14,400 runs 先例）；③ 真二进制 SE 实证阻断（F-SS-6）；④ FS-only 位点（TLB/PTW/SysReg）DUE 主导（TLB live-page 19/32 oops）——对 SDC 检出贡献小但为完整性必补；⑤ 方法论先例（雅典 SE、本仓复现 SE、sdcshield SE 先例）。
**裁决二（位点×故障模型）**：Tier1 主力 N=400（FPU 位段/PhysReg/LSQFwd F5+F6/L1DForward PCE/Exec/Cache data+secded/Mem+ecc_logic_fault）；Tier2 永久对照 N=100-200（FUPerm——补 harp_wrap deferred 缺口，量化 in-run 参考盲区）；Tier3 DUE 臂 N=100（ROB/RAT/freelist/IQ；BPU 引用既有证据）；FS 臂 N=32-100（TLB pfn5/PTW/SysReg/Cache/Mem × 真二进制）。基线故障模型=瞬态单比特 one-fault-per-run（雅典口径）。
**双通道 oracle 设计**（内核级）：内部校验通道（原测试 fail 计数=Detected）+ 独立全状态 checksum（escape/masked 判别）——比真二进制更强（真二进制无独立输出通道，escape/masked 不可分）。
**测试选择 ~12-14**（按检测域）：fma/fma_patterns/fpu_special_values/eigen GEMM+SVD/pocketfft（浮点向量）；crc32/adcx-bigint/isal_igzip（整数哈希压缩）；memcpy_l1d/lsu_store_forward/l2c_cross_cache_line/movbe/agu_stress（访存转发）；sve512_f64_chain（SVE，sve_vl_se 对齐）；zstd19/zlib（压缩）。
**指标**：P_detect=Detected/(Detected+Escape)（Wilson 95%）；raw+active 双口径；SDC/DUE/Crash/Hang/Inactive/SimErr 全分类；无注入 FP 底噪臂（须全绿）；SE-FS 交叉一致性对照。
- **先例**（`sdcshield/scripts/eigen-sve-double/gem5/{README.md,se_sve.py,run_sve.sh}`）：
  - CHAOS 树 = **gem5 25.1.0.1**；SE 配置为 ~70 行 canonical：AtomicSimpleCPU + 2GiB SimpleMemory + ArmISA(sve_vl_se=N)——**跑的是提取的独立测试二进制**（test_packet_xd/xcd/math_xd/e2e），不是 sdcshield 框架二进制
  - 动态链接二进制在 gem5 SE 直接可用（无 libstdc++.a 也能跑）；构建产物落仓库根 build/ARM/gem5.opt（1.1GB）
  - VL=512 验证矩阵全 PASS；gem5 验证是**功能语义级**（非性能）
- **全框架二进制 SE 可行性（源码实证，本日分析）**：
  - `syscall_emul.hh:1765+ doClone`：**支持 CLONE_THREAD**（共享页表 pTable->shared=true；前提=系统有空闲 ThreadContext，否则 -EAGAIN）→ 需 SE 配置预留多线程上下文（多 CPU 或 CPU.numThreads>1）
  - futex 已实现（arm64 表 base+98 futexFunc）；fork/vfork 在表中但无 handler（默认 unimplemented）
  - **AT_HWCAP/HWCAP2 由 gem5 从模拟 ISA 填充**（`src/arch/arm/process.cc:217-233`：fp/asimd/sve/dit/aes/pmull...）→ sdcshield 的 HWCAP 特性门控在 SE 可用
  - 风险点：SE 文件 syscall 直接打**宿主机**文件系统 → /proc/cpuinfo、/sys 拓扑读到的是宿主 128 核 Kunpeng920 的（拓扑失真，须 -n 1 钉死）；/proc/self/pagemap、forkfd 等路径未验证
  - sdcshield 有 `no-fork` ForkMode（sandstone_opts.cpp:895 "no"/"no-fork" 分支）——可绕开 fork；但 worker 线程恒为 pthread_create（sandstone_thread.cpp:123），-n 1 仍有 main+1 worker ≥2 线程
