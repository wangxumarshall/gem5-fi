# SDC 过程三分类重统计(2026-09-11)

> **框架**:SDC 的本质是过程——错误架构结果 + RAS 链路零告警 + 穿透保护路径——不取决于最终表现形式。
> 对每个 (单元, 故障模型, workload) cell:
> - **C1 无影响** = Masked/N_valid
> - **C2 过程中被检出** = (Corrected+DetectedContained)/N_valid —— 仅真建模了保护的单元非零
> - **C3 未检出但有问题** = (SDC+Crash+Hang)/N_valid,子项 **3a** 静默错 = SDC、**3b** 崩溃暴露 = Crash、**3c** 挂起暴露 = Hang
> - N_valid = N_total − Inactive − SimulatorError(工具伪影在分母外);**有效率** = N_valid/(N_total−Inactive),**伪影率** = 1−有效率
> - 数据源:每个数字可溯源到 runs/<campaign>/c*/results.jsonl;H7 formal 来自 artifacts/p20_h7_formal/results.txt(shell 跑批,标注)。
> - **重分类修正**:原 iq_f5f6_pilot/iq_f5_formal_madd/iq_f6_phase_curve 的 778 条 "Crash"(exit∈{1,2}+faults=0)实为 gem5 配置错误(madd_chain 二进制名错),本表按 SimulatorError 处理(详见 findings)。

## 类别2 保护机制审计(三态)

| 状态 | 单元 | 依据 |
|---|---|---|
| **有保护建模**(C2 按实际 rep 统计) | L1D/L1I/L2(CHAOSCache protectionModel)、DRAM(CHAOSMem)、DTLB(CHAOSArmTLB)、PTW(ptwEcc) | 代码 grep 全仓库核实,仅这 4 注入器实现 protectionModel |
| **N/A**(真机大概率也不保护) | Exec、FPU、Decode、AGU、BPU、ExMon、RAS | 组合逻辑/控制状态机,商用非安全关键芯片普遍不加 ECC(行业共识) |
| **未实现**(行业标准有,我们没做) | NoC/CHI/HCCS | 链路级 CRC+重传是行业标准;主动 scope-cut |
| **未知/待证实** | PRF、RAT、FreeList、ROB、IQ、LSQFwd、L1DForward、SysReg、L3 tag/一致性目录 | 鲲鹏 V110 是否保护无法确定;N1 代理假设"未列=无保护"仅因 ARM 公开手册没提,**不代表真没有**,未经实机验证 |

## 逐单元三分类表

### PRF 物理寄存器堆(`physreg`)— 82 cells,6229 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p15_h2_fc_scan/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 10 | 10 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| p15_h2_repro/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 10 | 10 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| p15_h2_repro/c0001 | transient_bit_flip/idx=3 | cholesky | C2 | none | 10 | 10 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pilot_physreg_x3/c0000 | transient_bit_flip/idx=3 | regchain | C0 | none | 3 | 3 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0000 | transient_bit_flip/idx=0 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0001 | transient_bit_flip/idx=0 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0002 | transient_bit_flip/idx=0 | cholesky | C2 | none | 50 | 50 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_abiclass_pilot/c0003 | transient_bit_flip/idx=1 | cholesky | C2 | none | 50 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| prf_abiclass_pilot/c0004 | transient_bit_flip/idx=1 | cholesky | C2 | none | 50 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| prf_abiclass_pilot/c0005 | transient_bit_flip/idx=1 | cholesky | C2 | none | 50 | 50 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_abiclass_pilot/c0006 | transient_bit_flip/idx=2 | cholesky | C2 | none | 50 | 50 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0007 | transient_bit_flip/idx=2 | cholesky | C2 | none | 50 | 50 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0008 | transient_bit_flip/idx=2 | cholesky | C2 | none | 50 | 50 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_abiclass_pilot/c0009 | transient_bit_flip/idx=4 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0010 | transient_bit_flip/idx=4 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0011 | transient_bit_flip/idx=4 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0012 | transient_bit_flip/idx=5 | cholesky | C2 | none | 50 | 50 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0013 | transient_bit_flip/idx=5 | cholesky | C2 | none | 50 | 50 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0014 | transient_bit_flip/idx=5 | cholesky | C2 | none | 50 | 50 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_abiclass_pilot/c0015 | transient_bit_flip/idx=6 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0016 | transient_bit_flip/idx=6 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0017 | transient_bit_flip/idx=6 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0018 | transient_bit_flip/idx=7 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0019 | transient_bit_flip/idx=7 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0020 | transient_bit_flip/idx=7 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0021 | transient_bit_flip/idx=19 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0022 | transient_bit_flip/idx=19 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0023 | transient_bit_flip/idx=19 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0024 | transient_bit_flip/idx=29 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0025 | transient_bit_flip/idx=29 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0026 | transient_bit_flip/idx=29 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0027 | transient_bit_flip/idx=30 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0028 | transient_bit_flip/idx=30 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_abiclass_pilot/c0029 | transient_bit_flip/idx=30 | cholesky | C2 | none | 50 | 50 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_bitseg_boundary/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_bitseg_boundary/c0001 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_boundary/c0002 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_boundary/c0003 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_boundary/c0004 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_boundary/c0005 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_boundary/c0006 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_pilot/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_bitseg_pilot/c0001 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_pilot/c0002 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_pilot/c0003 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_pilot/c0004 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_pilot/c0005 | transient_bit_flip/idx=3 | cholesky | C2 | none | 100 | 100 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_bitseg_pilot/c0006 | transient_bit_flip/idx=9 | cholesky | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_bitseg_pilot/c0007 | transient_bit_flip/idx=9 | cholesky | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_bitseg_pilot/c0008 | transient_bit_flip/idx=9 | cholesky | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_bitseg_pilot/c0009 | transient_bit_flip/idx=9 | cholesky | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_bitseg_pilot/c0010 | transient_bit_flip/idx=9 | cholesky | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_bitseg_pilot/c0011 | transient_bit_flip/idx=9 | cholesky | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_formal_cholesky/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 384 | 384 | 3.4 | 未知/待证实 | 96.6 | 3.9 | 92.7 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| prf_formal_cholesky/c0001 | transient_bit_flip/idx=9 | cholesky | C2 | none | 384 | 384 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_trigger_scan/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_trigger_scan/c0001 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_trigger_scan/c0002 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_trigger_scan_80k/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_trigger_scan_80k/c0001 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_trigger_scan_80k/c0002 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0001 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0002 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0003 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0004 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0005 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0006 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0007 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_h2_window_pilot/c0008 | transient_bit_flip/idx=3 | cholesky | C2 | none | 30 | 30 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_ptrchase_phys_pilot/c0000 | transient_bit_flip/idx=0 | ptrchaselong | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_ptrchase_pilot/c0000 | transient_bit_flip/idx=0 | ptrchaselong | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_ptrchase_pilot/c0001 | transient_bit_flip/idx=0 | ptrchaselong | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_ptrchase_pilot/c0002 | transient_bit_flip/idx=0 | ptrchaselong | C2 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| prf_regchain_pilot/c0000 | transient_bit_flip/idx=3 | regchain | C0 | none | 5 | 5 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| prf_regchain_pilot/c0001 | transient_bit_flip/idx=9 | regchain | C0 | none | 5 | 5 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_prf_x3_formal/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 384 | 384 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_prf_x3_formal/c0001 | transient_bit_flip/idx=3 | cholesky | C2 | none | 384 | 384 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_lane_pilot/c0000 | transient_bit_flip | neon | C0 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_lane_pilot/c0001 | transient_bit_flip | neon | C0 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_lane_pilot/c0002 | transient_bit_flip | neon | C0 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_lane_pilot/c0003 | transient_bit_flip | neon | C0 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### FPU/向量执行(`fsu`)— 21 cells,3342 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fpu_formal_gemm/c0000 | transient_bit_flip/idx=0 | gemmfloat | C2 | none | 384 | 384 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| fpu_formal_neon/c0000 | transient_bit_flip/idx=0 | neon | C2 | none | 384 | 67 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| fpu_neon_pilot/c0000 | transient_bit_flip/idx=0 | neon | C0 | none | 5 | 5 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| p12_setB_fpu/c0000 | transient_bit_flip | elemwisefma | C0 | none | 20 | 20 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| p17_repro_fpu_svd/c0000 | transient_bit_flip/bitseg=mant_hi | svditerative | C0 | none | 100 | 100 | 8.0 | N/A(共识不保护) | 92.0 | 92.0 | 0.0 | 0.0 | 100.0 | — |
| p82_legacy_smoke/c0000 | transient_bit_flip | cholesky | C0 | none | 5 | 5 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| p82_uniform_smoke/c0000 | transient_bit_flip | cholesky | C0 | none | 5 | 5 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| p84_recurring_smoke/c0000 | recurring_result_stuck | cholesky | C0 | none | 3 | 3 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_fmaw_rec_pilot/c0000 | transient_bit_flip/fma_weighted | elemwisefma | C0 | none | 100 | 100 | 1.0 | N/A(共识不保护) | 99.0 | 99.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_modes_pilot/c0000 | transient_bit_flip/bitseg=sign | elemwisefma | C0 | none | 100 | 100 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_modes_pilot/c0001 | transient_bit_flip/bitseg=exp_hi | elemwisefma | C0 | none | 100 | 100 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_modes_pilot/c0002 | transient_bit_flip/bitseg=exp_lo | elemwisefma | C0 | none | 100 | 100 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_modes_pilot/c0003 | transient_bit_flip/bitseg=mant_hi | elemwisefma | C0 | none | 100 | 100 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_modes_pilot/c0004 | transient_bit_flip/bitseg=mant_mid | elemwisefma | C0 | none | 100 | 100 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_modes_pilot/c0005 | transient_bit_flip/bitseg=mant_lo | elemwisefma | C0 | none | 100 | 100 | 1.0 | N/A(共识不保护) | 99.0 | 99.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_pilot/c0000 | transient_bit_flip | elemwisefma | C0 | none | 100 | 100 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_recurring_pilot/c0000 | recurring_result_stuck/recurring | elemwisefma | C0 | none | 100 | 100 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_svd_formal/c0000 | transient_bit_flip/bitseg=mant_hi | svditerative | C0 | none | 384 | 384 | 7.6 | N/A(共识不保护) | 92.4 | 92.4 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_fpu_svd_formal/c0001 | transient_bit_flip/bitseg=mant_lo | svditerative | C0 | none | 384 | 384 | 16.9 | N/A(共识不保护) | 83.1 | 83.1 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_fpu_svd_c2_formal/c0000 | transient_bit_flip/bitseg=mant_hi | svditerative | C2 | none | 384 | 384 | 0.0 | N/A(共识不保护) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_fpu_svd_c2_formal/c0001 | transient_bit_flip/bitseg=mant_lo | svditerative | C2 | none | 384 | 384 | 8.9 | N/A(共识不保护) | 91.1 | 91.1 | 0.0 | 0.0 | 100.0 | — |

### RAT 重命名表(`rat`)— 21 cells,4455 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p12_setB_specleak/c0000 | intermittent_burst/idx=10 | specleakprobe | C0 | none | 20 | 18 | 94.4 | 未知/待证实 | 5.6 | 5.6 | 0.0 | 0.0 | 100.0 | — |
| p17_repro_specleak/c0000 | intermittent_burst/idx=10 | specleakprobe | C0 | none | 100 | 96 | 84.4 | 未知/待证实 | 15.6 | 15.6 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_rob_specleak_depth/c0000 | intermittent_burst/idx=10 | specleakprobe | C2 | none | 128 | 124 | 80.6 | 未知/待证实 | 19.4 | 8.1 | 11.3 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| pwf_v11_rob_specleak_depth/c0001 | intermittent_burst/idx=10 | specleakprobe | C2 | none | 128 | 122 | 77.0 | 未知/待证实 | 23.0 | 9.8 | 13.1 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| pwf_v11_rob_specleak_depth/c0002 | intermittent_burst/idx=10 | specleakprobe | C2 | none | 128 | 126 | 75.4 | 未知/待证实 | 24.6 | 5.6 | 19.0 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| pwf_v11_rob_specleak_formal/c0000 | intermittent_burst/idx=10 | specleakprobe | C0 | none | 128 | 121 | 83.5 | 未知/待证实 | 16.5 | 16.5 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_rob_specleak_formal/c0001 | intermittent_burst/idx=9 | specleakprobe | C0 | none | 128 | 0 | — | 未知/待证实 | — | — | — | — | — | — |
| pwf_v11_rob_specleak_formal/c0002 | intermittent_burst/idx=3 | specleakprobe | C0 | none | 128 | 128 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_rob_specleak_pilot/c0000 | intermittent_burst/idx=10 | specleakprobe | C0 | none | 100 | 93 | 86.0 | 未知/待证实 | 14.0 | 14.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_specleak_x10_c2_formal/c0000 | intermittent_burst/idx=10 | specleakprobe | C2 | none | 384 | 372 | 82.8 | 未知/待证实 | 17.2 | 5.9 | 11.3 | 0.0 | 100.0 | ✓(2/2 guest-real page-fault) |
| pwf_v12_specleak_x10_formal/c0000 | intermittent_burst/idx=10 | specleakprobe | C0 | none | 384 | 368 | 85.1 | 未知/待证实 | 14.9 | 14.9 | 0.0 | 0.0 | 100.0 | — |
| rat_cholesky_pilot/c0000 | transient_bit_flip/idx=3 | cholesky | C0 | none | 3 | 3 | 33.3 | 未知/待证实 | 66.7 | 0.0 | 66.7 | 0.0 | 100.0 | — |
| rat_cholesky_pilot/c0001 | transient_bit_flip/idx=9 | cholesky | C0 | none | 3 | 3 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| rat_f5_formal_cholesky/c0000 | legal_domain_sub/idx=3 | cholesky | C2 | none | 384 | 377 | 40.3 | 未知/待证实 | 59.7 | 0.0 | 57.6 | 2.1 | 98.2 | ✓(2/2 guest-real page-fault) |
| rat_f5_formal_cholesky/c0001 | legal_domain_sub/idx=9 | cholesky | C2 | none | 384 | 384 | 99.5 | 未知/待证实 | 0.5 | 0.0 | 0.5 | 0.0 | 100.0 | — |
| rat_formal_cholesky/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 384 | 383 | 3.9 | 未知/待证实 | 96.1 | 0.3 | 80.4 | 15.4 | 99.7 | ✓(2/2 guest-real page-fault) |
| rat_formal_cholesky/c0001 | transient_bit_flip/idx=9 | cholesky | C2 | none | 384 | 384 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| specleak_branchy_pilot/c0000 | intermittent_burst/idx=3 | branchyreduce | C2 | none | 5 | 5 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| specleak_formal_branchy/c0000 | intermittent_burst/idx=3 | branchyreduce | C2 | none | 384 | 384 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| specleak_formal_branchy/c0001 | intermittent_burst/idx=9 | branchyreduce | C2 | none | 384 | 340 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| specleak_formal_x19/c0000 | intermittent_burst/idx=19 | branchyreduce | C2 | none | 384 | 0 | — | 未知/待证实 | — | — | — | — | — | — |

### 发射队列(`iq`)— 17 cells,2235 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iq_cholesky_pilot/c0000 | transient_bit_flip/idx=0 | cholesky | C0 | none | 5 | 5 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| iq_f5_formal_madd/c0000 | legal_domain_sub/idx=0 | maddchain | C2 | none | 384 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| iq_f5f6_pilot/c0000 | legal_domain_sub/idx=0 | maddchain | C2 | none | 5 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| iq_f5f6_pilot/c0001 | intermittent_burst/idx=0 | maddchain | C2 | none | 5 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| iq_f6_phase_curve/c0000 | intermittent_burst/idx=0 | maddchain | C2 | none | 96 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| iq_f6_phase_curve/c0001 | intermittent_burst/idx=0 | maddchain | C2 | none | 96 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| iq_f6_phase_curve/c0002 | intermittent_burst/idx=0 | maddchain | C2 | none | 96 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| iq_f6_phase_curve/c0003 | intermittent_burst/idx=0 | maddchain | C2 | none | 96 | 0 | — | 未知/待证实 | — | — | — | — | 0.0 | — |
| iq_f6_phase_curve_cholesky/c0000 | intermittent_burst/idx=0 | cholesky | C2 | none | 96 | 96 | 94.8 | 未知/待证实 | 5.2 | 0.0 | 5.2 | 0.0 | 100.0 | — |
| iq_f6_phase_curve_cholesky/c0001 | intermittent_burst/idx=0 | cholesky | C2 | none | 96 | 96 | 96.9 | 未知/待证实 | 3.1 | 0.0 | 3.1 | 0.0 | 100.0 | — |
| iq_f6_phase_curve_cholesky/c0002 | intermittent_burst/idx=0 | cholesky | C2 | none | 96 | 96 | 91.7 | 未知/待证实 | 8.3 | 0.0 | 8.3 | 0.0 | 100.0 | — |
| iq_f6_phase_curve_cholesky/c0003 | intermittent_burst/idx=0 | cholesky | C2 | none | 96 | 96 | 94.8 | 未知/待证实 | 5.2 | 0.0 | 5.2 | 0.0 | 100.0 | — |
| iq_formal_cholesky/c0000 | transient_bit_flip/idx=0 | cholesky | C2 | none | 384 | 384 | 24.7 | 未知/待证实 | 75.3 | 0.0 | 0.0 | 75.3 | 100.0 | — |
| pwf_v12_iq_formal/c0000 | transient_bit_flip | staleplausible | C0 | none | 384 | 384 | 36.5 | 未知/待证实 | 63.5 | 0.0 | 0.0 | 63.5 | 100.0 | — |
| pwf_v12_iq_omit_pilot/c0000 | transient_bit_flip | staleplausible | C0 | none | 100 | 100 | 42.0 | 未知/待证实 | 58.0 | 0.0 | 0.0 | 58.0 | 100.0 | — |
| pwf_v12_iq_pilot/c0000 | legal_domain_sub | staleplausible | C0 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_iq_pilot/c0001 | intermittent_burst | staleplausible | C0 | none | 100 | 100 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### L1I 指令(`l1i`)— 16 cells,2736 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| l1i_formal_loop/c0000 | stuck_at_zero/idx=0 | l1iloop | C0-CACHE | none | 384 | 383 | 99.2 | 0(本cell=none臂) | 0.8 | 0.0 | 0.8 | 0.0 | 99.7 | — |
| l1i_formal_loop/c0001 | stuck_at_one/idx=0 | l1iloop | C0-CACHE | none | 384 | 382 | 99.7 | 0(本cell=none臂) | 0.3 | 0.0 | 0.0 | 0.3 | 99.5 | — |
| pwf_v12_l1i_fields_pilot/c0000 | transient_bit_flip/l1i_field=opcode | l1iloop | C0-CACHE | none | 100 | 100 | 98.0 | 0(本cell=none臂) | 2.0 | 0.0 | 2.0 | 0.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0001 | transient_bit_flip/l1i_field=opcode | l1iloop | C0-CACHE | sed | 100 | 100 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0002 | transient_bit_flip/l1i_field=rn | l1iloop | C0-CACHE | none | 100 | 99 | 99.0 | 0(本cell=none臂) | 1.0 | 1.0 | 0.0 | 0.0 | 99.0 | — |
| pwf_v12_l1i_fields_pilot/c0003 | transient_bit_flip/l1i_field=rn | l1iloop | C0-CACHE | sed | 100 | 100 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0004 | transient_bit_flip/l1i_field=rm | l1iloop | C0-CACHE | none | 100 | 100 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0005 | transient_bit_flip/l1i_field=rm | l1iloop | C0-CACHE | sed | 100 | 100 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0006 | transient_bit_flip/l1i_field=rd | l1iloop | C0-CACHE | none | 100 | 100 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0007 | transient_bit_flip/l1i_field=rd | l1iloop | C0-CACHE | sed | 100 | 100 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0008 | transient_bit_flip/l1i_field=imm12 | l1iloop | C0-CACHE | none | 100 | 100 | 98.0 | 0(本cell=none臂) | 2.0 | 1.0 | 0.0 | 1.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0009 | transient_bit_flip/l1i_field=imm12 | l1iloop | C0-CACHE | sed | 100 | 100 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l1i_fields_pilot/c0010 | transient_bit_flip/l1i_field=cond | l1iloop | C0-CACHE | none | 100 | 98 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 98.0 | — |
| pwf_v12_l1i_fields_pilot/c0011 | transient_bit_flip/l1i_field=cond | l1iloop | C0-CACHE | sed | 100 | 100 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_l1i_formal/c0000 | transient_bit_flip/l1i_field=imm12 | l1iloop | C0-CACHE | none | 384 | 382 | 98.4 | 0(本cell=none臂) | 1.6 | 0.5 | 1.0 | 0.0 | 99.5 | — |
| pwf_v13_l1i_formal/c0001 | transient_bit_flip/l1i_field=cond | l1iloop | C0-CACHE | none | 384 | 381 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 99.2 | — |

### L2(`l2`)— 15 cells,2640 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| l2_formal_reduce/c0000 | transient_bit_flip/idx=0 | l1dreduce | C0-CACHE | none | 384 | 384 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| p12_setB_l2/c0000 | transient_bit_flip | stencil5pt | C0-CACHE | none | 20 | 20 | 50.0 | 0(本cell=none臂) | 50.0 | 50.0 | 0.0 | 0.0 | 100.0 | — |
| p17_repro_l2/c0000 | transient_bit_flip | stencil5pt | C0-CACHE | none | 100 | 100 | 44.0 | 0(本cell=none臂) | 56.0 | 56.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_l2_formal/c0000 | transient_bit_flip | stencil5pt | C0-CACHE | none | 384 | 384 | 51.0 | 0(本cell=none臂) | 49.0 | 49.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_l2_pilot/c0000 | transient_bit_flip | stencil5pt | C0-CACHE | none | 100 | 100 | 51.0 | 0(本cell=none臂) | 49.0 | 49.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_l2_size_sweep/c0000 | transient_bit_flip | stencil5pt | C0-CACHE | none | 128 | 128 | 50.0 | 0(本cell=none臂) | 50.0 | 50.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_l2_size_sweep/c0001 | transient_bit_flip | stencil5pt | C0-CACHE | none | 128 | 128 | 47.7 | 0(本cell=none臂) | 52.3 | 52.3 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_l2_size_sweep/c0002 | transient_bit_flip | stencil5pt | C0-CACHE | none | 128 | 128 | 50.8 | 0(本cell=none臂) | 49.2 | 49.2 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l2_arms_formal/c0000 | transient_bit_flip/field=data | stencil5pt | C0-CACHE | secded | 384 | 384 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l2_arms_formal/c0001 | transient_bit_flip/field=tag | stencil5pt | C0-CACHE | secded | 384 | 373 | 47.7 | 0.0 | 52.3 | 51.2 | 1.1 | 0.0 | 97.1 | — |
| pwf_v12_l2_arms_pilot/c0000 | transient_bit_flip/field=data | stencil5pt | C0-CACHE | none | 100 | 100 | 53.0 | 0(本cell=none臂) | 47.0 | 47.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l2_arms_pilot/c0001 | transient_bit_flip/field=data | stencil5pt | C0-CACHE | secded | 100 | 100 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l2_arms_pilot/c0002 | transient_bit_flip/field=tag | stencil5pt | C0-CACHE | none | 100 | 95 | 61.1 | 0(本cell=none臂) | 38.9 | 38.9 | 0.0 | 0.0 | 95.0 | — |
| pwf_v12_l2_arms_pilot/c0003 | transient_bit_flip/field=tag | stencil5pt | C0-CACHE | secded | 100 | 100 | 53.0 | 0.0 | 47.0 | 47.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_l2_victim_pilot/c0000 | transient_bit_flip/victim | stencil5pt | C0-CACHE | none | 100 | 100 | 47.0 | 0(本cell=none臂) | 53.0 | 53.0 | 0.0 | 0.0 | 100.0 | — |

### DRAM 后备(`memory`)— 12 cells,2445 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| addrmap_formal_fwd/c0000 | stuck_at_one/idx=0 | fwdchecksum | C2 | none | 384 | 384 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| mem_formal_cholesky/c0000 | transient_bit_flip/idx=0 | cholesky | C2 | none | 384 | 384 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| mem_regchain_pilot/c0000 | transient_bit_flip/idx=0 | regchain | C0 | none | 5 | 5 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| p12_setB_dram/c0000 | transient_bit_flip/addrwin | streamtriad | C0 | none | 20 | 20 | 15.0 | 0(本cell=none臂) | 85.0 | 85.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_dram_addrmap_pilot/c0000 | stuck_at_one/addrwin | streamtriad | C0 | none | 100 | 100 | 12.0 | 0(本cell=none臂) | 88.0 | 88.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_dram_formal/c0000 | transient_bit_flip/addrwin | streamtriad | C0 | none | 384 | 384 | 14.6 | 0(本cell=none臂) | 85.4 | 85.4 | 0.0 | 0.0 | 100.0 | — |
| pwf_v11_dram_pilot/c0000 | transient_bit_flip/addrwin | streamtriad | C0 | none | 100 | 100 | 13.0 | 0(本cell=none臂) | 87.0 | 87.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_dram_ecc_pilot/c0000 | transient_bit_flip/addrwin | streamtriad | C0 | none | 100 | 100 | 13.0 | 0(本cell=none臂) | 87.0 | 87.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_dram_ecc_pilot/c0001 | transient_bit_flip/addrwin | streamtriad | C0 | secded | 100 | 100 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_dram_ecclogic_pilot/c0000 | transient_bit_flip/ecc_logic_fault,addrwin | streamtriad | C0 | secded | 100 | 100 | 15.0 | 0.0 | 85.0 | 85.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_dram_c2_formal/c0000 | transient_bit_flip/addrwin | streamtriad | C2 | none | 384 | 384 | 69.8 | 0(本cell=none臂) | 30.2 | 30.2 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_dram_ecclogic_formal/c0000 | transient_bit_flip/ecc_logic_fault,addrwin | streamtriad | C0 | secded | 384 | 384 | 16.7 | 0.0 | 83.3 | 83.3 | 0.0 | 0.0 | 100.0 | — |

### 整数执行(`exec`)— 10 cells,2609 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| exec_formal_cholesky/c0000 | transient_bit_flip/idx=0 | cholesky | C2 | none | 384 | 384 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| exec_formal_regchain/c0000 | transient_bit_flip/idx=0 | regchain | C2 | none | 384 | 384 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| exec_regchain_pilot/c0000 | transient_bit_flip/idx=0 | regchain | C0 | none | 5 | 5 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_exec_chol_pilot/c0000 | transient_bit_flip | cholesky | C0 | none | 100 | 99 | 37.4 | N/A(共识不保护) | 62.6 | 10.1 | 52.5 | 0.0 | 99.0 | 未抽查(exit=-6 全体,同 fwdsrc 签名) |
| pwf_v12_exec_formal/c0000 | transient_bit_flip | elemwiseint | C0 | none | 384 | 384 | 10.4 | N/A(共识不保护) | 89.6 | 69.5 | 20.1 | 0.0 | 100.0 | 未抽查(exit=-6 全体,同 fwdsrc 签名) |
| pwf_v12_exec_formal/c0001 | recurring_result_stuck | elemwiseint | C0 | none | 384 | 384 | 0.0 | N/A(共识不保护) | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | 未抽查(exit=-6 全体,同 fwdsrc 签名) |
| pwf_v12_exec_pilot/c0000 | transient_bit_flip | elemwiseint | C0 | none | 100 | 100 | 12.0 | N/A(共识不保护) | 88.0 | 68.0 | 20.0 | 0.0 | 100.0 | 未抽查(exit=-6 全体,同 fwdsrc 签名) |
| pwf_v12_exec_pilot/c0001 | recurring_result_stuck | elemwiseint | C0 | none | 100 | 100 | 0.0 | N/A(共识不保护) | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | 未抽查(exit=-6 全体,同 fwdsrc 签名) |
| pwf_v13_exec_c2_formal/c0000 | transient_bit_flip | elemwiseint | C2 | none | 384 | 384 | 47.9 | N/A(共识不保护) | 52.1 | 0.0 | 52.1 | 0.0 | 100.0 | 未抽查(exit=-6 全体,同 fwdsrc 签名) |
| pwf_v13_exec_chol_formal/c0000 | transient_bit_flip | cholesky | C0 | none | 384 | 380 | 39.7 | N/A(共识不保护) | 60.3 | 8.7 | 51.6 | 0.0 | 99.0 | 未抽查(exit=-6 全体,同 fwdsrc 签名) |

### LSQ 转发(`lsq_fwd`)— 8 cells,1162 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fwdphase_curve_1/c0000 | delay_omission/idx=0 | fwdchecksum | C2 | none | 96 | 96 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | 未抽查(exit=-6 全体) |
| fwdphase_curve_2/c0000 | delay_omission/idx=0 | fwdchecksum | C2 | none | 96 | 96 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | 未抽查(exit=-6 全体) |
| fwdphase_curve_4/c0000 | delay_omission/idx=0 | fwdchecksum | C2 | none | 96 | 96 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | 未抽查(exit=-6 全体) |
| fwdphase_curve_8/c0000 | delay_omission/idx=0 | fwdchecksum | C2 | none | 96 | 96 | 0.0 | 未知/待证实 | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | 未抽查(exit=-6 全体) |
| fwdsrc_formal_fwd/c0000 | stuck_at_zero/idx=0 | fwdchecksum | C2 | none | 384 | 378 | 5.0 | 未知/待证实 | 95.0 | 37.6 | 57.4 | 0.0 | 98.4 | 未抽查(exit=-6 全体) |
| lsqfwd_formal_fwd/c0000 | transient_bit_flip/idx=0 | fwdchecksum | C2 | none | 384 | 381 | 67.7 | 未知/待证实 | 32.3 | 4.7 | 27.6 | 0.0 | 99.2 | 未抽查(exit=-6 全体) |
| lsqfwd_fwd_pilot/c0000 | transient_bit_flip/idx=0 | fwdchecksum | C0 | none | 5 | 5 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| lsqfwd_regchain_pilot/c0000 | transient_bit_flip/idx=0 | regchain | C0 | none | 5 | 0 | — | 未知/待证实 | — | — | — | — | — | — |

### 分支预测(`bpu`)— 7 cells,1741 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bpu_branchy_pilot/c0000 | transient_bit_flip/idx=0 | branchyreduce | C0 | none | 5 | 5 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| bpu_formal/c0000 | transient_bit_flip/idx=0 | branchyreduce | C2 | none | 384 | 384 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| bpu_formal_regchain/c0000 | transient_bit_flip/idx=0 | regchain | C2 | none | 384 | 384 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_bpu_ras_pilot/c0000 | delay_omission | branchyreduce | C0 | none | 100 | 100 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v12_bpu_target_pilot/c0000 | local_mbu | branchyreduce | C0 | none | 100 | 100 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_bpu_formal/c0000 | local_mbu | branchyreduce | C0 | none | 384 | 384 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| pwf_v13_bpu_formal/c0001 | delay_omission | branchyreduce | C0 | none | 384 | 384 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### 页表遍历(`ptw`)— 6 cells,496 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p20_h7_formal(shell)/ecc_false | two_bit_corrupt/kernel_walk_only | FS-kernel-boot | C0-FS | secded+logic-fault-sim | 384 | 384 | 51.0 | 0.0 | 49.0 | 0.0 | 49.0 | 0.0 | 100.0 | H7 formal 49% 致死(exit=134=gem5 panic-abort 报 guest 内核态故障;含 8 kernel panic + 6 abort,单发核实过) |
| p20_h7_formal(shell)/ecc_true | two_bit_corrupt/kernel_walk_only | FS-kernel-boot | C0-FS | ptwEcc | 100 | 100 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| ptw_h7_pilot_fs/c0000 | transient_bit_flip/idx=0 | cholesky | C0-FS | none | 3 | 3 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| ptw_h7_pilot_fs/c0001 | transient_bit_flip/idx=0 | cholesky | C0-FS | secded | 3 | 3 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| ptw_h7_pilot_fs/c0002 | stuck_at_zero/idx=0 | cholesky | C0-FS | none | 3 | 3 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| ptw_h7_pilot_fs/c0003 | stuck_at_zero/idx=0 | cholesky | C0-FS | secded | 3 | 3 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### L1D 数据(`l1d`)— 3 cells,773 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| l1d_formal_reduce/c0000 | transient_bit_flip/idx=0 | l1dreduce | C0-CACHE | none | 384 | 384 | 2.3 | 0(本cell=none臂) | 97.7 | 97.7 | 0.0 | 0.0 | 100.0 | — |
| l1d_formal_reduce_secded/c0000 | transient_bit_flip/idx=0 | l1dreduce | C0-CACHE | secded_poison | 384 | 384 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| l1d_reduce_pilot/c0000 | transient_bit_flip/idx=0 | l1dreduce | C0-CACHE | none | 5 | 5 | 0.0 | 0(本cell=none臂) | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |

### 译码(`decode`)— 2 cells,389 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| decode_formal/c0000 | transient_bit_flip/idx=0 | cholesky | C2 | none | 384 | 382 | 75.7 | N/A(共识不保护) | 24.3 | 0.3 | 23.6 | 0.5 | 99.5 | ✓(1/1 guest-real page-fault) |
| decode_regchain_pilot/c0000 | transient_bit_flip/idx=0 | regchain | C0 | none | 5 | 5 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### 独占监视器(`exmon`)— 2 cells,389 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| exmon_formal_spinlock/c0000 | transient_bit_flip/idx=0 | spinlockchecksum | C2 | none | 384 | 384 | 0.0 | N/A(共识不保护) | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | ✓(1/1 gem5-assertion-mediated) |
| exmon_spinlock_pilot/c0000 | transient_bit_flip/idx=0 | spinlockchecksum | C0 | none | 5 | 5 | 0.0 | N/A(共识不保护) | 100.0 | 0.0 | 100.0 | 0.0 | 100.0 | — |

### FreeList(`freelist`)— 2 cells,768 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| freelist_formal_cholesky/c0000 | transient_bit_flip/idx=3 | cholesky | C2 | none | 384 | 372 | 28.0 | 未知/待证实 | 72.0 | 0.0 | 70.4 | 1.6 | 96.9 | ✓(1/1 guest-real page-fault) |
| freelist_formal_cholesky/c0001 | transient_bit_flip/idx=9 | cholesky | C2 | none | 384 | 376 | 23.1 | 未知/待证实 | 76.9 | 0.0 | 72.9 | 4.0 | 97.9 | ✓(1/1 guest-real page-fault) |

### L1D post-check 通路(`l1d_fwd`)— 2 cells,385 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| l1dfwd_formal_reduce/c0000 | transient_bit_flip/idx=0 | l1dreduce | C2 | none | 384 | 384 | 9.1 | 未知/待证实 | 90.9 | 90.9 | 0.0 | 0.0 | 100.0 | — |
| p81_campaign_smoke/c0000 | transient_bit_flip | oraclesmoke | C0 | none | 1 | 1 | 0.0 | 未知/待证实 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | — |

### RAS(异常抑制)(`ras`)— 2 cells,389 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ras_formal_cholesky/c0000 | transient_bit_flip/idx=0 | cholesky | C2 | none | 384 | 357 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 99.2 | — |
| ras_regchain_pilot/c0000 | transient_bit_flip/idx=0 | raschecksum | C0 | none | 5 | 5 | 100.0 | N/A(共识不保护) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### ROB(`rob`)— 2 cells,389 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rob_cholesky_pilot/c0000 | transient_bit_flip/idx=0 | cholesky | C0 | none | 5 | 5 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| rob_formal_cholesky/c0000 | transient_bit_flip/idx=0 | cholesky | C2 | none | 384 | 384 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### 系统寄存器(`sysreg`)— 2 cells,10 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sysreg_f5_pilot/c0000 | legal_domain_sub/idx=0 | cholesky | C0-FS | none | 5 | 5 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| sysreg_f5_pilot/c0001 | transient_bit_flip/idx=0 | cholesky | C0-FS | none | 5 | 5 | 100.0 | 未知/待证实 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### 数据 TLB(`l1_tlb`)— 2 cells,386 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tlbf5_formal_fs/c0000 | legal_domain_sub/idx=0 | cholesky | C0-FS | none | 384 | 384 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |
| tlbf5_pilot/c0000 | legal_domain_sub/idx=0 | cholesky | C0-FS | none | 2 | 2 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

### L3/互连代理(`l3`)— 1 cells,100 reps

| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pwf_v13_l3_paired_pilot/c0000 | transient_bit_flip/paired | fwdchecksum | C0-CACHE | none | 100 | 100 | 100.0 | 0(本cell=none臂) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | — |

## 工具伪影二次核实记录(2026-09-11,/tmp/verify 重放,stderr 全保留)

| 单元 | 重放 reps | 退出信号 | 裁定 |
|---|---|---|---|
| physreg(fwdsrc cell) | 2 | rc=134,gem5 panic 报 `Page table fault @ 0x0/0x7fbffefc10` | **guest 真实故障**(stuck_at_zero→坏指针→页表错),SIGABRT 是 gem5-SE 报告无 handler 的 guest fault 的方式——Crash 分类**正确** |
| rat(spec_leak) | 2 | 同上,`Page table fault @ 0x21130` | **guest 真实故障**,Crash 正确 |
| freelist(mark_free) | 1 | `Page table fault @ 0x47ffff6afa0` | **guest 真实故障**,Crash 正确 |
| decode | 1 | `Page table fault @ 0x8001ff2c20` | **guest 真实故障**,Crash 正确 |
| exmon(stxr_force_fail) | 1 | rc=134,gem5 `Assertion extraDataValid() failed`(request.hh:912) | **gem5 断言中介**:注入破坏 STXR 协议→gem5 内部断言暴露;真机对应锁协议破坏(livelock/abort)。按 DUE 计,标注"gem5-assertion-mediated" |
| iq(F5/F6 旧 3 campaign) | 1 + 全量扫描 | 原 778 条 Crash = exit1/2+faults=0 | **工具伪影**(madd_chain 二进制名错→gem5 配置错误;2026-09-04 版分类器误标 Crash)。本表已改计 SimulatorError;真 IQ 结局以 v1.2 修复后数据为准 |

## 诚实边界

1. **iq_f5f6_pilot/iq_f5_formal_madd/iq_f6_phase_curve 作废**:778 reps 的 "Crash" 全是 exit∈{1,2}+faults=0 的 gem5 配置错误(二进制名 madd_chain 应为 madd_chain_kernel)。本表重计为 SimulatorError(伪影率因此上升)。**IQ 单元的可信数字 = v1.2 修复后的 pwf_v12_iq_*(wake_omit 63.5% DUE formal)**。
2. **SIGABRT 疑点已核实但非全量**:核实了 6 单元 8 reps(physreg/rat/freelist/decode/exmon + iq-artifact)。exec/lsq_fwd 的 exit=-6 全体与 fwdsrc 同签名(Page table fault 家族),未逐一重放——标注"未抽查"。
3. **fs_mode cells**(tlbf5/sysreg/ptw boot)的 Masked = 内核存活 oracle,3a 静默面未知(FS 无法区分安静算错)。
4. **H7 formal 为 360s 截断观察窗**(censored):survivor = 窗口内无 panic,非全程存活。
5. **类别2 的"未知/待证实"**(9 单元)是 N1 代理假设,未经实机验证——引用时必须带上这个限定。
6. **runner.py 待办**:results.jsonl 未保存 stderr 原文与退出原因文本,本次回溯靠重放。建议加 `exit_reason` 字段(取 stderr 首个 panic/assert 行,~50 字符)——已列 task_plan 待办,未顺手改。
