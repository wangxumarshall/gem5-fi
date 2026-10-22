# R4-8-SPEC 残余：W11（SPEC 12 行）+ 残余阻塞行（MODE-UNIMPL 3 / UNRESOLVED）

> 执行者：Agent 5（并行收口团队）。worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/r4-8-spec`，
> 分支 `r4-8-spec-residual`，基线 `d5fc8727`（= `lsu-mdspec-20261019` tip）。
> 约束：禁 build；gem5 仅用**预构建只读二进制**（`.../lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`,
> sha256 前缀 `7d52bc1392a10055`）；每次 gem5 调用 `flock /tmp/lsu_gem5_slot2.lock`；预算 ≤8 run；
> 输出到 `/tmp/r4-8-spec/**`，绝不写共享 `runs/`。

## Goal

对 W11 12 行给出**证据化逐行裁决**（替代载体审计 a/b/c），并把残余阻塞集合
（MODE-UNIMPL 3 / UNRESOLVED）从**工具重新推导**（不信 239/86 或任何报告），
能实现的一件一 patch 落地，用测试钉住订正后的阻塞集合。

## 事实基线（本轮从工具重新推导，命令见证据文件）

- `python3 tools/lsu_runid_map.py`（临时输出）→ 325 RunID，`BLOCKED=86/PARTIAL=239`（与提交版计数相同，
  但 **12 条理由文本**与提交版 `runid_map.json` 不一致 → 提交版 map 陈旧）。
- UNRESOLVED（map 判 PARTIAL 而 campaign `resolve_cell` 拒跑）= **19**（全为 W1/MiBench，
  属 Agent 3 口径订正范围）；另有 12 条矩阵行不在 map 中（T09/S12/C13 的 B0 不适用 + O08 multicore）。
- 12 个 W11 cell 的 spec 负载名逐字相同：`SPEC CPU2017 采样区间`（表 7）。

## 任务分解（每项 = 一个 commit）

- [x] **T0** 本计划文件（`docs/superpowers/plans/2026-10-22-r4-8-spec-residual.md`）。
- [x] **T1+T2**（合并为一个 unit，因测试即该 unit 的契约）：`tools/lsu_campaign.py` 的
      SPEC 键收窄为规格钦定身份 `SPEC CPU2017`，并抽出 `SPEC_WL_IDENTITY` 常量消除
      `resolve_cell` 里 `key == "SPEC"` 的字面量漂移（收窄键时若不改该字面量，
      T10-F{0,1,2}-W11 会**静默**改为解析到 `fs:tlb_probe` 载体 —— 被新测试 A4 抓到）；
      `tests/test_lsu_w11_spec_residual.py` 钉住 A/B/C 三组断言。
- [ ] **T3** `docs/gem5-fi/lsu/mdspec/runid_map.json` 重生成（订正 12 条陈旧理由文本）。
- [ ] **T4** T08-W9 残余：真机 FS pilot（F6-W9，必要时 F4-W9）+ `MODEL_BLOCKED["T08"]` 证据化订正。
- [ ] **T5** 证据文件 `docs/gem5-fi/lsu/mdspec/R4-8-SPEC-residual-report.md`。

## 判据（每项的验证命令）

- T1/T2/T3：`python3 tests/test_lsu_w11_spec_residual.py`（退出码 0）+ `pytest tests/test_lsu_runid_map.py tests/test_lsu_coverage_matrix.py`
  真实输出。
- T4：`armtlb_injections.log` 含 `Site: arm_tlb_walk_issue_drop` + `prop_evt.txt.gz` 中
  `kind=tlb_walk`/`kind=tlb_refill` 同 `walk_id`、refill `field=lost`（R4-5.9 判据）。
- 回归：至少一条不受影响族测试（`tests/test_lsu_runid_map.py` 或 `test_lsu_coverage_matrix.py`）真 pass。
