# FSU 第二轮计划：协议复核 → suite 审计统一 → FR03-W5/W6 → F0 试点

> 基线：HEAD `a4de94f8`，origin/fsu 同步，工作区 clean；历史 42/519、14/173；
> 活跃 33/240、11/80；12 suite seed / 48 component；FSU 335 passed，
> 非 FSU 20 passed。分支只允许 `fsu`。

## A. FR03 seed3 协议复核（主 agent + Agent A）

- 保存 attempt-1/2 manifest 完整 diff、配置冻结时间、运行时间。
- attempt-1：execution_completed / evidence_valid / activated / chain_certified
  分开；真实 terminal、oracle、激活 generation、consumer。
- attempt-2：目标从 fixed mantissa SA0 lane0 改为 sign SA1 lane0，属于
  **protocol deviation / supplemental evidence**，不能用重新预注册消除。
- 若判定 attempt-2 不能作为原 seed3，纠正 seed3 AUTHORITATIVE/索引，
  FR03-F5-W3 降为 2/3；解释计数调整。
- 扫描其他正式 seed 是否存在结果驱动换目标；gate 阶段调整单独标注。

## B. 统一 suite 审计契约（Agent A 写工具，主 agent 集成）

- 新增版本化 `schemas/fsu_suite_audit.schema.json`：
  schema_version、suite_id/hash/RunID/seed、expected/actual_programs、
  component_count、component 身份/attempt/哈希、suite_execution_complete、
  suite_evidence_valid、suite_certified、violations、formal_seed_contribution=1。
- `tools/fsu_suite_audit.py` 从原始 component 证据重算：
  程序集合完整/无重复、同一冻结计划、suite_hash 一致、component 证据有效、
  component 失败不被汇总掩盖、篡改任一 component 证据即失败。
- 旧 audit 只读验证或显式迁移报告；记录工具版本/验证时间。
- 重新核验全部 12 suite seed 与普通 seed；从磁盘生成双视图。

## C. FR03-F5-W5（Agent B 准备，主 agent 运行）

- 五程序固定顺序；每 component 一个永久 Vec phys cell。
- readiness：每程序真实 reg_class/precision/lane；合法 phys 范围；
  目标选择算法 + 确定性种子；固定 phys/mask/polarity；generation 仅身份；
  跨 free/realloc/squash；其他 cell 不串扰；读写 exposure 分开；
  全量计数与 bounded trace 守恒；完整链与 oracle 可判定。
- 目标选择只依赖预注册算法和无故障 census，不看 fault-run SDC。
- 先在 runs/fsu-gates 做五程序 gate；通过后冻结 seed1/2/3，再正式运行。
- 不借用 FP06/FP04 认证；component 不计 seed。

## D. FR03-F5-W6（Agent B 准备，主 agent 运行）

- 复用 SVD/FFT/真实稀疏 CG；核对源码/二进制/输入/golden、precision、
  oracle/容差、CG 收敛判据、NaN/Inf/缺失输出处理、golden 不被注入污染。
- FR03 专用三组件 gate → 冻结 → 3 个正式 suite seed。

## E. F0 下一试点（Agent C）

- 剩余 F0 RunID readiness 排序：注入点/故障语义/workload/L0–L5/oracle/
  修复成本/已知缺陷。
- 复核（按真实审计，不假定仍存在）：FQ08-b 无 victim 仍计注入；
  现有 PRF 模型身份/generation；FP08 suppressed_count；FQ08-c squash/
  延迟唤醒风险。
- 先模型行为单测 → 非正式 gate → 1 个正式 seed → 补到 3。
- 只运行注册表已有 F0 RunID；FP06-d 保持 MISSING。

## F. 失败证据清单

- 未提交失败 gate：路径、原因、时间、配置、关键文件 SHA-256。
- 提交适量 manifest/诊断/哈希清单；大文件留服务器并记录位置；
  明确未进 Git 的文件，不把“工作区 clean”当作全部证据已推送。

## 验证与门禁

- 每个代码单元：targeted + 全量 FSU + 非 FSU 回归。
- 正式 suite：component 全部 audit/chain/oracle 通过才 +1 seed。
- 所有计数由 AUTHORITATIVE + audit 重新生成；不预填预期数字。
