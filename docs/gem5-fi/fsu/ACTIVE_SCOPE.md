# FSU 活跃频率范围（F0/F5）

> 裁决时间：2026-11-03。本文件是 `configs/fsu/ACTIVE_SCOPE.json` 的人类可读说明。

## 1. 裁决

- **ACTIVE FREQUENCIES = F0, F5**
- F1/F2/F3/F4 及未来发现的其他频率全部 **DEFERRED_BY_USER**。
- 不实现、不 census、不运行新的正式 F1–F4 seed。
- 原始注册表 `docs/gem5-fi/fsu/runids.json` **不修改**：仍为 173 RunID / 519 seed。
- 不删除任何 F1–F4 历史证据，不把历史 seed 改名成 F5，不用旧 rate 参数冒充 F5。

## 2. 两个视图

| 视图 | RunID | 目标 seed | 已完成 seed | 3/3 RunID |
|---|---:|---:|---:|---:|
| 历史全量（source registry） | 173 | 519 | 47 | 15 |
| 当前活跃（F0/F5） | 80 | 240 | 38 | 12 |

活跃范围为 F0 72 + F5 8 = 80；已完成的是 `FSU-FP04-F0-W1`、
`FSU-FP04-F0-W3`、`FSU-FP04-F0-W4`、`FSU-FP04-F0-W5`（W5 suite，每个
suite seed 的 5 个 component run 只计 1）、`FSU-FP06-F5-W1`、
`FSU-FP06-F5-W3`、`FSU-FP06-F5-W4`（W4-rate-v1）、`FSU-FP06-F5-W5`（五程序 F5 suite，
每 suite seed 计 1）与 `FSU-FP04-F0-W6` 与 `FSU-FP06-F5-W6`（SVD/FFT/sparse suite，每 suite seed 计 1）、
`FSU-FR03-F5-W5` 与 `FSU-FR03-F5-W6`（FR03 suite，每 suite seed 计 1）；
`FSU-FR03-F5-W3` 为 2/3（seed3 protocol deviation）。

`FSU-FR07-F0-W1` 的 3 个旧 seed 是 **PROXY_EVIDENCE**：原实现于
`staticInst->execute()` 之后改写 PRF cell，而工作簿要求 “PRF 写入前修改
WB data”。证据与日志完整保留，但计入 `proxy_seeds_total`（当前 3），
**不计入** admitted seed；`scope_status=ACTIVE_PROXY_ONLY`。详见
`FR07-PRF-WB-POSITION-AUDIT.md`。FP06-d 仍 MISSING。

## 3. 标签

- `ACTIVE_SCOPE`：频率属于 F0/F5。
- `DEFERRED_BY_USER`：非活跃频率且未运行；不是失败。
- `HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE`：非活跃频率但历史已完成
  （当前为 F1-W4、F2-W4、F3-W4，共 9 seed）；保持 `COMPLETE_3_OF_3`。
- `HISTORICAL_PARTIAL_OUT_OF_ACTIVE_SCOPE`：预留（当前无）。
- `ACTIVE_PROXY_ONLY`：活跃范围内只有保留的代理证据，未被严格认证。
- `completion_state`：COMPLETE / PARTIAL / FAILED / INVALID_EVIDENCE /
  INCOMPLETE / PROXY_ONLY / NOT_RUN，与 scope 标签正交。

`INDEX.json` 的 `summary` 是历史全量视图，`summary.active_scope` 是活跃
视图；`INDEX.md` 同时输出两个视图。

## 4. 运行门禁

- `tools/fsu_seed_runner.py`、`tools/runner.py`、`tools/campaign.py` 在
  任何 gem5 启动前拒绝非 F0/F5 的正式 RunID，错误包含
  `frequency outside active scope` 与 `DEFERRED_BY_USER`。
- 显式测试模式（`scope_test_mode` / `--scope-test-mode`）只允许验证旧频率
  解析：
  - `fsu_seed_runner` 必须使用非 `runs/fsu` 的临时 out-root；
  - campaign 测试模式把 `runs/` 与 `artifacts/` 重定向到临时目录；
  - 测试模式不能写正式 `runs/fsu`。
- gate、离线回归与历史审计可读取旧证据，但不能产生新的 F1–F4 正式 seed。

## 5. F5 边界

F5 的 8 个 RunID 只属于 FP06（W1/W3/W4/W5/W6）与 FR03（W3/W5/W6）。
FP04 没有 F5；不得创建 `FP04-F5`、不得新增第 174 个 RunID。
F5 的数值语义与实现 readiness 以工作簿与 `F5-READINESS.md` 为准；
FP06-F5-W3 已认证 a/b/c（FP06-d MISSING），FP06-F5-W1/W4/W5/W6 未正式
完成；FR03-F5-W3/W5/W6 保持 PARTIAL/BLOCKED。
