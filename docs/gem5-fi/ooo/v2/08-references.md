# 08 · 文献与来源（11 条）

> 来源：《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（WPS 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract_v2.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「8.文献与来源」R2–R12（表头 R1），6 列 × 11 条。

| 代码 | 标题/资源 | 类型/发表 | 核对方式 | 本工作簿用途 | 定位 |
|---|---|---|---|---|---|
| GEM5-O3 | gem5 stable: configs/common/cores/arm/O3_ARM_v7a.py | 官方源码 | 2026-09-27在线核对 | B0宽度、ROB/IQ、PRF、FU和流水延迟 | https://raw.githubusercontent.com/gem5/gem5/stable/configs/common/cores/arm/O3_ARM_v7a.py |
| GEM5-BASE | gem5 stable: src/cpu/o3/BaseO3CPU.py | 官方源码 | 2026-09-27在线核对 | 默认宽核敏感性、ROB/PRF/SMT与时序参数 | https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/o3/BaseO3CPU.py |
| TC23 | Silent Data Corruptions: Microarchitectural Perspectives | IEEE TC 2023 | 本地PDF全文核对 | ROB直接结果、MiBench、2000次、commit传播分类；FP未覆盖 | Silent_Data_Corruptions_Microarchitectural_Perspectives.pdf |
| MICRO24 | DelayAVF: Calculating Architectural Vulnerability Factors for Delay Faults | MICRO 2024 | 本地PDF全文核对 | Decoder小时延、1007线、BEEBS、ACE干扰/复合；非SDC指标 | MICRO2024 DelayAVF_Calculating_Architectural_Vulnerability_Factors_for_Delay_Faults.pdf |
| IISWC15 | Differential Fault Injection on Microarchitectural Simulators | IISWC 2015 | 本地PDF全文核对 | 组合逻辑限制、单bit方法、IQ支持但无结果 | Differential_Fault_Injection_on_Microarchitectural_Simulators.pdf |
| HPCA24 | gem5-MARVEL: Microarchitecture-Level Resilience Analysis of Heterogeneous SoC Architectures | HPCA 2024 | 本地PDF全文核对 | 框架范围与未报告的rename/ROB边界 | Gem5-MARVEL_Microarchitecture-Level_Resilience_Analysis_of_Heterogeneous_SoC_Architectures.pdf |
| MICRO25 | Harpocrates++: Automated Functional Program Generation Against CPU Faults and Silent Data Corruptions | IEEE Micro 2025 | 本地PDF全文核对 | 定向负载与激活/传播思想；未注入rename/ROB | Harpocrates_Automated_Functional_Program_Generation_Against_CPU_Faults_and_Silent_Data_Corruptions.pdf |
| CHAOS26 | CHAOS: Controlled Hardware fAult injectOr System for gem5 | arXiv 2602.02119, 2026 | 本地PDF全文核对 | 事件概率、单/多bit、stuck-at和HPC早期偏离 | Chaos Controlled Hardware Fault Injector System for Gem5.pdf |
| DATE25 | From Gates to SDCs: Understanding Fault Propagation Through the Compute Stack | DATE 2025 | 本地PDF全文核对 | 门级永久故障到gem5的建模边界；功能单元结果不外推为OOO结构结果 | From_Gates_to_SDCs_Understanding_Fault_Propagation_Through_the_Compute_Stack.pdf |
| CASE | 各单元结构化注入故障模型真实案例作证 | 本地研究笔记 | 2026-09-27核对 | 仅用于生成结构化模型候选和真实案例背景，不作为定量结果 | 各单元结构化注入故障模型真实案例作证.docx |
| ARM-TABLE | ARM64_微架构SDC敏感性_故障注入填充表 | 本地汇总工作簿 | 2026-09-27核对 | 六个OoO单元的现有文章/结果初始汇总 | ARM64_微架构SDC敏感性_故障注入填充表.xlsx |

