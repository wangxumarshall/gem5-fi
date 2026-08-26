# Core 179 微架构级根因与故障注入研究 — 索引

## 阅读顺序
1. **PLAN.md** — 五转储交叉根因定位计划（systematic-debugging 驱动）
2. **DIAGNOSIS_REPORT.md** — 主诊断报告（五转储法证、D1/D2 通路、根因陈述、处置建议）
3. **MICROARCH_SUPPLEMENT.md** — 微架构深化（结合 TSV110 几何、D1/D2/D3 三通路、审稿人压力测试）
4. **FI_DESIGN_SUPPLEMENT.md** — 故障注入方案设计（H5–H7、P-D1/D2/D3、诚实执行状态）
5. **PAPER.md** — 顶会论文草稿（ASPLOS/MICRO/HPCA 级，全文）

## 验证状态（诚实）
- ✅ H5 已 gem5 端到端验证闭环（byte_lane_skew → oops 链复现，多 seed）
- ⚠️ H6/H7 已执行，因 SE 模式 gem5 翻译模型限制无法验证（需 FS 模式）
- ✅ P-D1/D2/D3 三注入器已实现、编译通过、符号入 gem5.opt

## 复现
- 构建：`cd CHAOS/gem5 && taskset -c <healthy cpus> scons build/ARM/gem5.opt -j8`
- H5 复现：见 `fi_research/probes/o3_chaos_smoke.py` + `ptrskew_kernel.c`
- vmcore 法证：见 DIAGNOSIS_REPORT §7 命令索引

## 诚实边界
- 本机即 core179 故障机；编译/运行全程 taskset 隔离 cpu179
- 单/多缺陷裁决需供应商 RTL/DFT（软件不可解）
- 链接阶段曾出现 SDC-affected 瞬态失败（最终 -j1 成功）
