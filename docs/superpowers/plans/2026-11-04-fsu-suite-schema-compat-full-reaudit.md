# FSU 统一 suite 审计 schema 兼容 + 全量当前工具复审

日期：2026-11-04　分支：`fsu`　基线 HEAD：`aad5ab63`

## 目标

1. 修复 `tools/fsu_suite_audit.py` 对旧 FR03/W6-FR03 `seed_plan` 的解析失败。
2. 版本化、可追溯地规范化旧字段，禁止为满足 schema 猜默认值。
3. 由当前工具重算全部 21 个 suite seed / 87 个 component / 全部非 suite 权威 seed。
4. 索引与严格认证计数只采用当前重算结果，旧 `audit_v2.json` 仅作只读历史回显。
5. 计数下降时如实报告并保留证据。

## 一、schema 适配（主线，owner：main）

- [ ] 新建 `tools/fsu_seed_plan_schema.py`
  - [ ] `detect_schema()`：`f5-v1` / `fr03-v1` / `None`（无 seed_plan 的旧 F0 suite）。
  - [ ] 别名规范化：`fault_mask↔mask`、`vec_lane_offset↔lane_offset`、`fault_type↔polarity`。
        十进制/十六进制统一为整数；两别名同时存在且值不同 → fail closed。
  - [ ] FR03 复用 `tools/fsu_fr03_suite_gate.py` 的 `normalise_seed_plan` + `compute_suite_hash`
        （唯一真实哈希实现，禁止另写一套）。
  - [ ] F5 复用 `tools/fsu_suite.py` 现有实现，保证已认证 15 个 seed 的 `seed_plan_entry` 逐字节不变。
  - [ ] `warmup/sample` 契约：F5 给出真实整数+单位（eligible event ordinal / ordinary eligible
        events）；FR03 明确 `not_applicable`，证据来自实际命令与 `inject/config.ini`，不填 0。
  - [ ] 每条规范化字段记录来源（frozen config / component manifest / actual command / config.ini）。
- [ ] `tools/fsu_suite_audit.py`
  - [ ] 按 schema 选择哈希函数与 manifest 绑定键：F5 用 `seed_plan_entry`，FR03 用
        `target_plan_entry`（由 `resolve_component_plan` 生成）。
  - [ ] 新增 `seed_plan_schema`、`warmup_sample`、`physical_identity`、`missing_evidence`、
        `recompute_status` 输出。
  - [ ] FR03 物理身份四源交叉：frozen plan / manifest.effective_injector /
        component_manifest.component_fr03_target / 实际命令 + config.ini。
  - [ ] 缺证据 → `missing_evidence`，不计为通过，也不臆测。
  - [ ] `suite_hash` 漂移照实报（已知 FR03-W5 seed1：运行标签 FR03-c vs 冻结 FR03-a）。
- [ ] `schemas/fsu_suite_audit.schema.json` 同步新字段与 `missing_evidence:` 类别。

## 二、全量当前复审（owner：A subagent，接口由 main 固定）

- [ ] 新建 `tools/fsu_full_audit.py`
  - [ ] 逐个 suite seed 调 `fsu_suite_audit.audit_seed`。
  - [ ] 逐个非 suite `AUTHORITATIVE` attempt 调 `fsu_seed_audit.audit_attempt`。
  - [ ] 汇总 87 个 component 的重算结果。
  - [ ] 输出四分类：`current_verified` / `legacy_report_only` /
        `current_verification_failed` / `missing_evidence`。
  - [ ] 报告记录 `schema_version`、tool git SHA、验证时间、输入文件 SHA。
  - [ ] 不写回任何 seed 目录内的证据。
- [ ] `tests/test_fsu_seed_plan_schema.py` 回归：
  - [ ] FR03-W5/W6 真实旧配置；FP04/FP06/FR07 suite 不受影响。
  - [ ] 字段冲突、缺 component、program 重复、per-program precision/mask 不匹配、
        component 证据哈希变化、旧成功报告与当前失败冲突。
- [ ] `tests/test_fsu_full_audit.py`。

## 三、索引改用当前重算（owner：main）

- [ ] `tools/fsu_index.py`
  - [ ] `_v2_suite_state` 不再信任 `audit_v2.json` 的 `suite_certified`；
        改为调用 `fsu_suite_audit.audit_seed`，旧 v2 仅回显。
  - [ ] 非 suite `AUTHORITATIVE` seed 改为调用 `fsu_seed_audit.audit_attempt`，
        不再只读旧 `audit.json.ok`。
  - [ ] 增加 `recompute_status`、`recompute_tool`、`legacy_report_only` 标记。
  - [ ] 提供显式 `--no-recompute` 仅用于离线诊断，并在输出中标注 `legacy_report_only`。

## 四、验证

- [ ] 复现命令由失败变为可重算：
      `python3 tools/fsu_suite_audit.py runs/fsu/FSU-FR03-F5-W5/seed1 --quiet`
- [ ] `python3 tools/fsu_full_audit.py` 生成真实四分类计数。
- [ ] `python3 tools/fsu_index.py` 双视图计数刷新。
- [ ] `python3 -m pytest tests/test_fsu_seed_plan_schema.py tests/test_fsu_suite_audit.py
      tests/test_fsu_full_audit.py tests/test_fsu_suite.py tests/test_fsu_index.py -q`
- [ ] 相关非 FSU 回归 20 passed 基线复核。
- [ ] 小步提交并推送 `origin/fsu`。

## 五、FR01/FR02（B）与 FQ08/FP08/FP05（C）

见两个 subagent 的独立文件所有权；正式运行只由 main 执行，门禁不计正式 seed。
