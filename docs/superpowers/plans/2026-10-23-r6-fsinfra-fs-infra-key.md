# R6-FSINFRA — 更正 `runid_map` 陈旧 fs-infra 工作负载键（lane L33）

Worktree `.claude/worktrees/r6-fsinfra`（branch `r6-fsinfra`），起点 HEAD `040688f2`。
岗位文件：`tools/lsu_runid_map.py`、`tests/test_lsu_runid_map.py`、
`docs/gem5-fi/lsu/mdspec/R6-FSINFRA-EVIDENCE.md`（新增）、
`docs/gem5-fi/lsu/mdspec/runid_map.json`（台账再生成）。

## 背景（事实）

`tools/lsu_runid_map._resolve_workload` 以**模型无关**方式发出
`workload:workload-level:blocked(fs-infra: TLB workload needs FS)`
（来源 `lsu_campaign.WL_BLOCKED["TLB-AliasPerm"]`，`lsu_campaign.py:237`）。24 个 T 系列
W4 行全部携带该键。它对 `resolve_cell` 的 armtlb FS 特例一无所知，且该"需 FS ⇒
blocked"断言已被真机反驳（`R5-FS-PILOT-EVIDENCE.md`、`R5-ADMISSION-CLOSEOUT.md`
§4.3/§6、`blockers_for_approval.md` §FS-INFRA）。

## 判据（不自立口径）

- 反驳证据：T01/T02/T03/T04/T05/T06/T07/T08/T10 的 W4 行真机 `activated=1`
  （16 行有产物；见 `R6-FSINFRA-EVIDENCE.md`）。
- 残余阻塞（引用 `blockers_for_approval.md` §FS-INFRA 解除条件）：逐格 30 activated
  pilot；**无任何一格**达到（试点均 1 seed）⇒ **不解锁任何一行**（不放宽阈值）。
- T05–T08 另有独立 `lsu_campaign.MODEL_BLOCKED` 阻塞，不经 runid_map，本 lane 不动。

## 任务（一 unit = 一 commit）

- [x] T1 `tools/lsu_runid_map.py`：对 armtlb FS 行，把陈旧键替换为逐行更正键
      （命名反驳 + 证据锚点 + 真实残余阻塞），新增 `fs_workload` 留证字段。
- [x] T2 `tests/test_lsu_runid_map.py`：先写 RED（陈旧字面量仍在 / 无更正键 /
      无证据锚点），实现后 GREEN；钉 24 行不 mass-clear、16 行有证据、8 行如实报"无 pilot"。
- [x] T3 新增 `docs/gem5-fi/lsu/mdspec/R6-FSINFRA-EVIDENCE.md`（逐行证据锚点，耐久）。
- [x] T4 再生成 `docs/gem5-fi/lsu/mdspec/runid_map.json`（台账 = 工具输出；
      顺带补上 HEAD 台账缺失的 `pilot` 字段）。

## 验证（真实命令，引真实输出）

- RED：`python3 tests/test_lsu_runid_map.py` → 6 FAIL（陈旧字面量仍在 24 行等）。
- GREEN：同命令 → `FAILURES: 无`。
- 回归：`python3 tools/lsu_ready_contract.py` → `READY=241 PARTIAL=0 BLOCKED=84`，
  `FS-INFRA=24`（**状态/分母/分类均不变**，无 READY 新增）。
- 全套件：`python3 tools/lsu_test_runner.py` → `suites=56 ENV=5 FAIL=14`（与基线
  逐项相同，NEW FAIL=[]）。

## 结果

0 行状态变更（24 行仍 BLOCKED）。更正的是**键的内容**：从被反驳的"需 FS"改为
"FS 载体可用且已实证 + 真实残余阻塞（逐格 pilot 广度 < 解除条件）"，并逐行记录证据路径。
未删任何 RunID、未放宽任何阈值、未把任何未被链门禁准入的行标为 READY。
