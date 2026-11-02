# FSU 故障注入全流程计划（2026-11-02）

唯一基线：`origin/fi-ding`（`46ce66cdb9c22f5e591b43b97b68c7d526704211`，2026-10-30）。
唯一分支：`fsu`；唯一工作目录：`/home/sdc/gem5-fi-fsu`。
每个任务对应一次提交，验证通过后才提交并推送 `origin/fsu`。

## 阶段 A：环境与文档

- [x] A1 环境清单：记录 OS/CPU/内存/磁盘/Python/openpyxl/pytest/scons/gcc、
      `origin/fi-ding` 起点、`fsu` 工作区、负载与在跑进程。
      - 验证：`docs/gem5-fi/fsu/PHASE-A-ENV.md` 内容与实测命令输出一致。
- [x] A2 源 Excel 落位并校验 SHA-256。
      - 来源：`/home/sdc/fsu-input/gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx`
      - 实测 SHA-256：`4a5b358cb6e12d93f5b25ed0b422c6100a30540c0693482c04af904669b22cd6`（与期望一致）
      - 落位：`docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx`（chmod 444，只读）
- [x] A3 实现 `tools/fsu_xlsx_to_md.py`（12 表无损转换 + 回读逐格校验 + 负向测试）。
      - 验证：`python3 -m pytest tests/test_fsu_xlsx_to_md.py -q` → `24 passed`。
- [x] A4 生成转换报告（源 SHA、12 表尺寸、173 RunID、表7/表9 集合、
      非空单元格、公式/隐藏/合并计数、回读校验结果）。
      - 验证：真实工作簿转换 `ALL PASS`，报告 `docs/gem5-fi/fsu/CONVERSION_REPORT.md`。
- [x] A5 173 RunID 机器可读清单（JSON/CSV）。
      - 验证：`runids.json` count=173；`runids.csv` 同源。

## 阶段 B：实现审计

- [x] B1 以最新 `origin/fi-ding` 真实代码审计 30 个模型的支持状态。
      - 结论：0 IMPLEMENTED；13 PARTIAL（FQ01/FQ02/FQ04/FQ08、
        FR01/FR02/FR03/FR07、FP04/FP05/FP06/FP07/FP08）；17 MISSING。
      - 工作簿“直接已有”的 FR01/FP04 经审计降级为 PARTIAL。
- [x] B2 建立 RunID × 模型 × 频率 × 负载 × hook × workload × oracle × 观测字段矩阵。
      - 产物：`docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.{json,csv}`、
        `IMPLEMENTATION_AUDIT.md`；173 行唯一 RunID；测试 5 项通过。
- [x] B3 试点 RunID 端到端（golden → census → 单次注入 → 链报告 → 审计）。
      - 试点：**FSU-FP04-F0-W4**（FP04 + elemwise_fma_kernel + ARRAYHASH/ULP）。
      - 结果：三 seed 全部 admitted；逐 seed 审计 ok=true/failures=[]；
        门禁 1–10 全部 PASS；见 `docs/gem5-fi/fsu/evidence/PILOT_3_OF_3.md`。
- [ ] B4 所有缺口实现并测试；禁止用相近模型结果替代。
      - 试点已落地 FSU_PROP 发射端（L0–L5 + activated）；
        其余 29 个模型/172 个 RunID 的缺口仍按单点提交逐步实现。

## 阶段 C：三 seed 执行

- [x] C0 FSU_PROP-EVT v1 字段规范 + 直接 parent 链审计器（工具先于 C++ 发射端落地）。
      - 产物：`tools/fsu_prop_fields.py`、`tools/fsu_chain_check.py`、
        `tests/test_fsu_chain_check.py`（18 项合成流测试通过）。
      - 边界：仅工具与合成事件；真实 FSU 事件流仍需 C++ 发射端。
- [x] C0a 权威 gem5 构建（Python 3.11.9，`-j4`，exit 0）与 baseline golden。
      - 二进制 `f9a7cd9b…98c32`（发射端最终版）；golden 两次一致。
- [ ] C1 单实例资源实测，确定并发上限，campaign 支持 resume。
      - 构建与单 seed 已实测；并发上限与 resume 调度仍待实现。
- [x] C2-pilot 试点 `FSU-FP04-F0-W4` 三个独立 seed 完成（3/3）。
      - seed1 attempt-1 因字段问题保留 lineage；attempt-2 为 AUTHORITATIVE。
      - 其余 172 个 RunID 尚未启动。
- [x] C3-pilot 试点三份 seed Markdown 生成并逐 seed 审计通过。
- [x] C4-pilot 生成 README.md/INDEX.md/INDEX.json；该 RunID 标记 COMPLETE_3_OF_3。

## 阶段 D0/D0.5：试点收口与覆盖语义校正

- [x] D0 三份权威 seed 的 audit.json/audit.md 持久化；
      `certified` 由链审计 + 完整证据门禁计算（非硬编码）；
      chain_report/Markdown/证据哈希/INDEX 从 raw 证据重建；
      raw prop_evt/stats/run.out/run.err/注入日志哈希不变；
      seed1 attempt-1 保留 lineage，attempt-2 为 AUTHORITATIVE；
      closeout 报告 `docs/gem5-fi/fsu/FP04-F0-W4-PILOT-CLOSEOUT.md`。
- [x] D0.5 seed_completion 与 coverage_status 分离：
      `FSU-FP04-F0-W4` = 3/3 + `PILOT_SUBMODEL_ONLY`（工作簿要求 a/b/c/d，
      试点仅 FP04-c/mant_lo/W4/F0）；其余 172 个 RunID 为 0/3。
- [ ] D1 频率语义门禁：读表 5 与 FP04 行，建立 F0–F5 → 代码/runner 映射；
      F1/F2/F3 增加合成测试与真实小型门禁（eligible 口径、注入次数/间隔/
      选择规则、manifest/事件字段、replay），禁止只改 `--fsu_freq` 标签。

## 阶段 D：最终审计

- [ ] D1 173/173 RunID、519/519 seed（或列出真实阻塞项）。
- [ ] D2 全部链审计（parent 连续、tick 单调、L5 见证、哈希、截断检查）。
- [ ] D3 交付二进制/源码/工具版本与失败重跑 lineage。

## 阻塞与纪律

- 缺少 Excel 时只做文档、转换器与静态检查，不启动大规模 scons/gem5。
- 不干扰 0202 上的 sdcshield 任务；不杀他人进程。
- 禁止 `git reset --hard` / `git clean -fd` / 强推。
- 所有结论必须来自实测命令输出；不得用模板或“预计”冒充完成。
