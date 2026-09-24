# 08 · 文献与来源

> 源：工作表「8.文献与来源」（12 行 × 6 列：r1 表头 + r2–r12 共 11 条文献/源码数据行；6 列全列逐字转录）。
> 转录规则：单元格文本逐字转录；表格内 `\n` → `<br>`、`|` → `\|`（与 extract.py 的 `md_cell` 一致）；「Excel行」列为行号标注，非源表列。

| Excel行 | 代码 | 标题/资源 | 类型/发表 | 核对方式 | 本工作簿用途 | 定位 |
|---|---|---|---|---|---|---|
| 2 | GEM5-O3 | gem5 stable: configs/common/cores/arm/O3_ARM_v7a.py | 官方源码 | 2026-09-24核对 | LQ/SQ、FU、LSQDepCheckShift、L1D、MSHR、预取器 | https://raw.githubusercontent.com/gem5/gem5/stable/configs/common/cores/arm/O3_ARM_v7a.py |
| 3 | GEM5-BASE | gem5 stable: src/cpu/o3/BaseO3CPU.py | 官方源码 | 2026-09-24核对 | LSQCheckLoads、Store Set、cache ports | https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/o3/BaseO3CPU.py |
| 4 | GEM5-MMU | gem5 stable: ArmMMU.py / ArmTLB.py | 官方源码 | 2026-09-24核对 | Arm TLB默认64项全相联、L2 TLB 1280项5-way | https://raw.githubusercontent.com/gem5/gem5/stable/src/arch/arm/ArmTLB.py |
| 5 | GEM5-SYS | gem5 stable: src/sim/System.py | 官方源码 | 2026-09-24核对 | cache_line_size=64 | https://raw.githubusercontent.com/gem5/gem5/stable/src/sim/System.py |
| 6 | IISWC15 | Differential Fault Injection on Microarchitectural Simulators | IISWC 2015 | 本地PDF | LSQ/SQ和L1D单bit、2000次/结构/负载、MiBench | Differential_Fault_Injection_on_Microarchitectural_Simulators.pdf |
| 7 | TC22 | Soft Error Effects on Arm Microprocessors: Early Estimations versus Chip Measurements | IEEE TC 2022 | 本地PDF | Arm A5/A9 DTLB/L1D，gem5与中子束 | Soft_Error_Effects_on_Arm_Microprocessors_Early_Estimations_versus_Chip_Measurements.pdf |
| 8 | TC23 | Silent Data Corruptions: Microarchitectural Perspectives | IEEE TC 2023 | 本地PDF | Armv8/Armv7 DTLB、LQ/SQ、L1D；2000次/负载 | Silent_Data_Corruptions_Microarchitectural_Perspectives.pdf |
| 9 | HPCA24 | gem5-MARVEL: Microarchitecture-Level Resilience Analysis of Heterogeneous SoC Architectures | HPCA 2024 | 本地PDF | Arm/x86/RISC-V的LQ/SQ/L1D瞬态与永久结果 | Gem5-MARVEL_Microarchitecture-Level_Resilience_Analysis_of_Heterogeneous_SoC_Architectures.pdf |
| 10 | MICRO24 | DelayAVF: Calculating Architectural Vulnerability Factors for Delay Faults | MICRO 2024 | 本地PDF | Ibex LSU与prefetch buffer的小延迟故障；DelayAVF不是SDC率 | MICRO2024 DelayAVF_Calculating_Architectural_Vulnerability_Factors_for_Delay_Faults.pdf |
| 11 | MICRO25 | Harpocrates++: Automated Functional Program Generation Against CPU Faults and Silent Data Corruptions | IEEE Micro 2025 | 本地PDF | SQ/L1D检测率；指标不是SDC率 | Harpocrates_Automated_Functional_Program_Generation_Against_CPU_Faults_and_Silent_Data_Corruptions.pdf |
| 12 | CHAOS26 | CHAOS: Controlled Hardware fAult injectOr System for gem5 | arXiv 2602.02119, 2026 | 本地PDF | 频率、单/多bit、stuck-at与HPC偏差规律 | Chaos Controlled Hardware Fault Injector System for Gem5.pdf |

> 提取注：4 条 gem5 源码条目核对的是上游 stable（2026-09-24）；本仓库 vendored gem5 v25.1.0.1（upstream 62c7bf2），实施前机制核实一律以本仓源码为准（见 09-implementation-plan.md §机制核实）。
