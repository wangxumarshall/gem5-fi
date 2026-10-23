# R6 冻结清单（唯一权威 gem5.opt）— 2026-10-23

> **本文件冻结后，所有 pilot 必须在启动前与结束后核对下表 SHA-256。**
> **禁止在 pilot 期间原位重建或替换该二进制。** 任何生产代码修改 → 重新构建 → 更新本文件 → 重跑受影响 RunID；
> **不得使用旧二进制的结果作为最终准入证据。**

| 项 | 值 |
|---|---|
| 集成分支 | `lsu-mdspec-20261019` |
| 集成 HEAD | `508c716ec44a22068353c1e287de06bafa9a38e6` |
| 二进制绝对路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` |
| **SHA-256（完整）** | `6469bad23ed035fde43b92bcd24570f24de7a4bf12faddce3fee7fe6562aef4e` |
| SHA-256（前 16 位，供快速核对） | `6469bad23ed035fd` |
| 文件大小 | `1145423376` 字节 |
| 构建时间 | `2026-10-23 16:28:29 +0800` |
| 构建命令 | `cd <worktree>/CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` |
| 构建日志 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_reports/R6_UNIFIED_BUILD.log` |
| 核验方式 | 主 agent 亲自执行 `sha256sum`，与转述值逐字符一致（独立核验，非采信） |

## 完整回归（冻结时点，HEAD `508c716e`）

`python3 tools/lsu_test_runner.py` → `suites=61 ENV=1 FAIL=13 PASS=45 SKIP=2`

- **NEW FAIL = 0**（FAIL 集与基线 `66ab98a2` 的 13 项逐条相同）
- 未将任何 FAIL 改写为 SKIP/ENV
- 基线 13 项：`pytest::collect, test_lsu_campaign_propagation.py, hook_a07, hook_c11, hook_c12, hook_c14, hook_c15, hook_cpf, hook_l04, hook_o0x, hook_p06, hook_s10, hook_sq`

## 证据根（权威口径）

```bash
LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding
```
**禁止**在没有 `runs/lsu/` 的 worktree 根上生成权威计数（该错误曾把 `unproven`/`evidence_missing` 语义颠倒）。

## checkpoint 身份

`/home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`（FS 载体）
多核 FS 另需 2 核 CHI checkpoint，经环境变量 `LSU_FS_MC_CHECKPOINT`（**非** `--fs-checkpoint`）。

## 引用本清单的既有产物

- `docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md`（准入规范）
- `runs/lsu/r6_reports/STATUS.md`（滚动状态）
