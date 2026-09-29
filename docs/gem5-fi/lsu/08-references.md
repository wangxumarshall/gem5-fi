# 08 · 文献与来源（11 条）

> 来源：《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（Microsoft Excel 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「8.文献与来源」R2–R12（表头 R1），6 列 × 11 条。

| 代码 | 标题/资源 | 类型/发表 | 核对方式 | 本工作簿用途 | 定位 |
|---|---|---|---|---|---|
| GEM5-O3 | gem5 stable: configs/common/cores/arm/O3_ARM_v7a.py | 官方源码 | 2026-09-24核对 | LQ/SQ、FU、LSQDepCheckShift、L1D、MSHR、预取器 | https://raw.githubusercontent.com/gem5/gem5/stable/configs/common/cores/arm/O3_ARM_v7a.py |
| GEM5-BASE | gem5 stable: src/cpu/o3/BaseO3CPU.py | 官方源码 | 2026-09-24核对 | LSQCheckLoads、Store Set、cache ports | https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/o3/BaseO3CPU.py |
| GEM5-MMU | gem5 stable: ArmMMU.py / ArmTLB.py | 官方源码 | 2026-09-24核对 | Arm TLB默认64项全相联、L2 TLB 1280项5-way | https://raw.githubusercontent.com/gem5/gem5/stable/src/arch/arm/ArmTLB.py |
| GEM5-SYS | gem5 stable: src/sim/System.py | 官方源码 | 2026-09-24核对 | cache_line_size=64 | https://raw.githubusercontent.com/gem5/gem5/stable/src/sim/System.py |
| IISWC15 | Differential Fault Injection on Microarchitectural Simulators | IISWC 2015 | 本地PDF | LSQ/SQ和L1D单bit、2000次/结构/负载、MiBench | Differential_Fault_Injection_on_Microarchitectural_Simulators.pdf |
| TC22 | Soft Error Effects on Arm Microprocessors: Early Estimations versus Chip Measurements | IEEE TC 2022 | 本地PDF | Arm A5/A9 DTLB/L1D，gem5与中子束 | Soft_Error_Effects_on_Arm_Microprocessors_Early_Estimations_versus_Chip_Measurements.pdf |
| TC23 | Silent Data Corruptions: Microarchitectural Perspectives | IEEE TC 2023 | 本地PDF | Armv8/Armv7 DTLB、LQ/SQ、L1D；2000次/负载 | Silent_Data_Corruptions_Microarchitectural_Perspectives.pdf |
| HPCA24 | gem5-MARVEL: Microarchitecture-Level Resilience Analysis of Heterogeneous SoC Architectures | HPCA 2024 | 本地PDF | Arm/x86/RISC-V的LQ/SQ/L1D瞬态与永久结果 | Gem5-MARVEL_Microarchitecture-Level_Resilience_Analysis_of_Heterogeneous_SoC_Architectures.pdf |
| MICRO24 | DelayAVF: Calculating Architectural Vulnerability Factors for Delay Faults | MICRO 2024 | 本地PDF | Ibex LSU与prefetch buffer的小延迟故障；DelayAVF不是SDC率 | MICRO2024 DelayAVF_Calculating_Architectural_Vulnerability_Factors_for_Delay_Faults.pdf |
| MICRO25 | Harpocrates++: Automated Functional Program Generation Against CPU Faults and Silent Data Corruptions | IEEE Micro 2025 | 本地PDF | SQ/L1D检测率；指标不是SDC率 | Harpocrates_Automated_Functional_Program_Generation_Against_CPU_Faults_and_Silent_Data_Corruptions.pdf |
| CHAOS26 | CHAOS: Controlled Hardware fAult injectOr System for gem5 | arXiv 2602.02119, 2026 | 本地PDF | 频率、单/多bit、stuck-at与HPC偏差规律 | Chaos Controlled Hardware Fault Injector System for Gem5.pdf |

