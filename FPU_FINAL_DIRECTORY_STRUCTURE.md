# FPU/SIMD 清理后最终目录结构 (FPU_FINAL_DIRECTORY_STRUCTURE.md)

**项目目录**：`/home/sdc/gem5-fi-fpu`（清理后 127M，原始 14G）
**清理时间**：2026-11-26
**权威依据**：`inputs/gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx`（工作表 24–30）

> 结构保持原有命名，未新建平行项目。所有被移出/归档的文件均**移动**（非删除）
> 至同级证据目录 `/home/sdc/gem5-fi-fpu-evidence/`，仅 `gem5/build/`（9.5G 编译
> 中间产物）与 `scripts/__pycache__/` 被删除。

---

## 最终目录

```
/home/sdc/gem5-fi-fpu/
├── gem5/                                  gem5 源码树（基线 226778cf + FPU 补丁，无 build/）
│   └── src/
│       ├── arch/arm/
│       │   ├── fpu_fi.hh                  FPU 语义 hook 接口（新增）
│       │   ├── isa.hh                     #include fpu_fi.hh（修改）
│       │   ├── insts/fplib.cc             M001–M007 hook（7 处 active(1..7)）
│       │   └── isa/insts/neon64.isa       M008–M012 hook（5 处 active(8..12)）
│       └── cpu/o3/
│           ├── FPUInjector.{hh,cc}        注入驱动 + O3 生命周期 Trace（新增）
│           ├── SConscript                 Source('FPUInjector.cc')
│           ├── dyn_inst.cc / rename.cc / inst_queue.cc / iew.cc / commit.cc
│           └── CHAOSFPU/ CHAOSExec/       预存旧注入器（基线内容，默认关闭，未改动）
│
├── inputs/
│   └── gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx     权威 Excel（30 工作表）
│
├── scripts/
│   ├── gen_5x3_workloads.py               生成 60 个 5×3 上下文负载（C01–C05）
│   ├── run_5x3.py                         5×3 主驱动：count/formal/validate
│   ├── run_5x3_r2.py                      R2 修订重跑（C03/C05，写入 counts_r2/runs_r2）
│   ├── analyze_5x3_final_v6.py            最终统计口径/生产者映射分析器
│   └── parse_records.py                   128B guest 记录解析器（通用辅助）
│
├── reports/
│   ├── source_changes.patch               FPU 补丁（12 文件新增/修改）
│   ├── source_and_binary_hashes.txt       关键源码与二进制 SHA256（版本绑定）
│   └── MMU_INTEGRITY.md                   MMU 工作区零写入完整性证明
│
├── docs/
│   └── REPRODUCE.md                       最终 5×3 复现说明
│
├── work/FPU_SIMD_5x3_FORMAL/              最终 5×3 实验（冻结交付物，非原始 Trace）
│   ├── workloads/{src,build}              60 个上下文负载源码 + ELF（复现必需）
│   ├── counts/manifest.json               60 组 count-only 预扫描结果（N/ordinal）
│   ├── counts_r2/manifest.json            24 组 R2 count-only 结果
│   ├── FPU_5x3_Causal_Edges_Final_v6.csv  最终因果边（4453 条）
│   ├── FPU_5x3_Propagation_Evidence_Final_v6.csv  传播证据（180 行）
│   ├── FPU_5x3_Propagation_Summary_Final_v6.json   传播汇总
│   ├── FPU_5x3_Producer_Classification_Audit_v6.csv  生产者分类审计（180 行）
│   ├── FPU_5x3_TargetInput_Provenance_Audit_v6.csv   目标输入来源审计（360 行）
│   ├── FPU_5x3_Run_Manifest.csv / Rerun_Manifest.csv / Full_Statistics.csv /
│   │   Final_FaultControl_Summary.csv / Trace_Index.csv / Trace_Index_R2.csv /
│   │   CountOnly_Manifest.csv / CountOnly_Manifest_R2.csv /
│   │   Classification_Changes.csv / Model_C03_C05_Completion.csv
│   └── *.md                              最终报告（Acceptance_v6、Execution、Preflight、
│                                           Deliverables_Index、Second_Round_*、修订说明、README_v6）
│
├── FPU_PRE_CLEANUP_AUDIT.md               本任务 Phase 1 交付物
├── FPU_FINAL_DIRECTORY_STRUCTURE.md       本文件
├── FPU_FINAL_REPRODUCIBILITY_AUDIT.md     Phase 5 交付物
└── FPU_FINAL_GIT_RELEASE_REPORT.md        Phase 6 交付物
```

---

## 归档位置（证据包）

已移动（非删除）至 `/home/sdc/gem5-fi-fpu-evidence/`：

| 归档路径 | 内容 | 大小 |
|---|---|---|
| `results/` | 已超期 156 对/312 运行（R/T/U 方案）完整结果 | 2.0G |
| `work/FPU_SIMD_5x3_FORMAL/runs/` | 240 个正式运行原始 Trace（events.jsonl 等） | 1.4G |
| `work/.../runs_r2/` | 96 个 R2 修订运行原始 Trace | 429M |
| `work/.../counts/`（60 目录） | 60 组 count-only 原始 Trace | 353M |
| `work/.../counts_r2/`（24 目录） | 24 组 R2 count-only Trace | 108M |
| `work/.../` 中间 v1–v5 交付物 | 早期迭代 CSV/MD/JSON（v6 报告要求保留 v1–v5） | ~3M |
| `work/.../audit/ workloads_pre_r2_backup/` | Excel 审计 dump、R2 前负载备份 | 1.4M |
| `runs/` | pilot/test 试运行 | 32M |
| `logs/` | 编译/阶段日志 | 330K |
| `reproduction/` | 旧方案复现样本（M005-R04/M008-T03/M012-U03） | ~600K |
| `workloads/` | 旧 R01–R05 12 负载 | ~300K |
| `scripts_old/` | 已超期脚本（experiment/gen_workloads/analyze*.py/validate_full/state_proof/final_audit/build_propagation） | ~200K |
| `reports_old/` | 临时 Excel dump、MMU pre/post 清单、156 对执行摘要 | ~1M |
| `tarballs/` | 各轮交付压缩包（21 文件，含 sha256 sidecar） | ~88M |

---

## 清理统计

| 类别 | 数量/大小 |
|---|---|
| 保留（代码 + 冻结交付物） | 127M |
| 归档（证据，移动保留） | 4.4G |
| 删除（`gem5/build/` 编译中间产物 + `__pycache__/`） | 9.5G |
| 项目原始大小 | 14G |

## 关键保留原则

1. **最终方案唯一**：只保留 5×3（180 Fault + 60 Control）方案代码与冻结交付物；旧 156 对方案已整体归档作历史。
2. **故障语义冻结**：12 模型 hook 未改一行；`source_and_binary_hashes.txt` 保留版本绑定。
3. **可追溯不破坏**：所有原始 Trace / 传播链 / 因果图均移动归档并保留 SHA256 索引
   （`FPU_5x3_Trace_Index.csv` / `Trace_Index_R2.csv` 记录 300 个 events.jsonl 绝对路径与字节数）。
4. **不影响他单元**：`/home/sdc/gem5-fi-ding`、`/home/sdc/gem5-fi-mmu*` 零写入（见 `reports/MMU_INTEGRITY.md`）。