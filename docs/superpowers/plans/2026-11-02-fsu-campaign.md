# FSU 故障注入全流程计划（2026-11-02）

唯一基线：`origin/fi-ding`（`46ce66cdb9c22f5e591b43b97b68c7d526704211`，2026-10-30）。
唯一分支：`fsu`；唯一工作目录：`/home/sdc/gem5-fi-fsu`。
每个任务对应一次提交，验证通过后才提交并推送 `origin/fsu`。

## 阶段 A：环境与文档

- [x] A1 环境清单：记录 OS/CPU/内存/磁盘/Python/openpyxl/pytest/scons/gcc、
      `origin/fi-ding` 起点、`fsu` 工作区、负载与在跑进程。
      - 验证：`docs/gem5-fi/fsu/PHASE-A-ENV.md` 内容与实测命令输出一致。
- [ ] A2 源 Excel 落位并校验 SHA-256。
      - 期望：`4A5B358CB6E12D93F5B25ED0B422C6100A30540C0693482C04AF904669B22CD6`
      - 目标路径：`docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx`
      - **状态：BLOCKED —— 服务器上未找到该文件（见 PHASE-A-ENV.md 搜索记录）。**
- [ ] A3 实现 `tools/fsu_xlsx_to_md.py`（12 表无损转换 + 回读逐格校验 + 负向测试）。
- [ ] A4 生成转换报告（源 SHA、12 表尺寸、173 RunID、表7/表9 集合、
      非空单元格、公式/隐藏/合并计数、回读校验结果）。
- [ ] A5 173 RunID 机器可读清单（JSON/CSV）。

## 阶段 B：实现审计

- [ ] B1 以最新 `origin/fi-ding` 真实代码审计 30 个模型的支持状态。
- [ ] B2 建立 RunID × 模型 × 频率 × 负载 × hook × workload × oracle × 观测字段矩阵。
- [ ] B3 试点 RunID 端到端（golden → census → 单次注入 → 链报告 → 审计）。
- [ ] B4 所有缺口实现并测试；禁止用相近模型结果替代。

## 阶段 C：三 seed 执行

- [ ] C1 单实例资源实测，确定并发上限，campaign 支持 resume。
- [ ] C2 每个 RunID 三个独立 seed；失败 attempt 保留 lineage。
- [ ] C3 每 seed 生成 `runs/fsu/COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seed<N>.md`。
- [ ] C4 生成 README.md/INDEX.md/INDEX.json，逐 RunID 标记 COMPLETE_3_OF_3。

## 阶段 D：最终审计

- [ ] D1 173/173 RunID、519/519 seed（或列出真实阻塞项）。
- [ ] D2 全部链审计（parent 连续、tick 单调、L5 见证、哈希、截断检查）。
- [ ] D3 交付二进制/源码/工具版本与失败重跑 lineage。

## 阻塞与纪律

- 缺少 Excel 时只做文档、转换器与静态检查，不启动大规模 scons/gem5。
- 不干扰 0202 上的 sdcshield 任务；不杀他人进程。
- 禁止 `git reset --hard` / `git clean -fd` / 强推。
- 所有结论必须来自实测命令输出；不得用模板或“预计”冒充完成。
