# 2026-10-27 — 0202 T02-F2-W4：seed 身份表达 + F2 多 fault 判定一致性 + 整数 seed 1 诊断复现

**分支**：`fix/0202-six-chain-20261026`（base HEAD `7130f985`，clean）
**Host**：`cathelper-k8s-worker2`
**权威 binary**：`CHAOS/gem5/build/ARM/gem5.opt`，SHA256
`a99031a86e8e108b9278af53044d873a8262ea20d73bd7d94c6dba1300b49e0a`（与接管值逐字节一致）
**checkpoint**：`runs/lsu/0202_fs_cpt_boot_20261026T193235/cpt.239515184727`
**并发**：gem5 固定 1 进程。

## 只读复核结论（Phase 1）

- 分支/HEAD/clean/binary SHA/checkpoint/golden/六项 raw evidence 全部核对通过。
- 0101 的 R6 campaign 用**整数** seed：`lsu_campaign.py:2884` "Seeds are 1..N per cell"、
  `:2923` outdir `seed{seed}`（1-based）、`:2536` `--tlb_rng_seed str(seed)`；真实证据
  `docs/gem5-fi/lsu/mdspec/R4-8-SPEC-residual-report.md:170` 实测命令行含 `--tlb_rng_seed 1`
  且落在 `.../seed1/`。
- 0202 的 runner 用**哈希** seed：`lsu_runner.py:175` `seed = lsu_seed(run_id, phase,
  sample_index)`，`:264` `--tlb_rng_seed str(manifest["seed"])`，dir `s{sample_index}`（0-based）。
- ⇒ 0202 的 T02-F2-W4 与 0101 的 seed1 是**不同样本**（不同 RNG seed ⇒ 不同注入点），
  两者结论不可互相替代。
- 多 fault 判定现状（`tools/lsu_chain_check.py`）：`check_admission` 取
  `max(faults.items(), key=len(path_event_ids))`（最长可证路径）；`containment_from_events`
  取 `max(faults.items(), key=len(chain))`（事件数最多）；`lsu_campaign.py:2052-2057` 顶层
  terminal 取 `sorted(faults)[0]`（排序第一）。三者可指向**不同 fault**。

## 范围与红线

- 不改 checker 严格性、不跨分支/跨 fault 拼链、不以 `chain_end` 充当 terminal。
- 不改现有失败 raw evidence；不覆盖 `R0202-VERIFY6.*`；不换 seed 求 PASS（本次只允许显式整数
  seed `1`，因为目的是复现 0101 历史 seed1）。
- 不跑 seed 2/3、pilot、screening、confirmatory、325 formal 或其他 RunID。
- 不改 fault model / F2 周期 / jitter / oracle / checkpoint / binary；**暂不改 C++**。

## 补丁单元（每单元一个 commit）

### U6 — `lsu_runner.py` 显式 RNG seed 覆盖（seed 身份表达）
- 新增 `--explicit-seed <int>`。未给出时 **完全保持** `lsu_seed(run_id, phase, sample_index)`
  行为；给出时 injector 实收该整数。
- manifest 同时记录 `sample_index`、`seed`、`seed_source=derived|explicit`、seed 生成规则、
  显式 seed 原值（`explicit_seed`）。
- dry-run 命令 / manifest / 实际 gem5 命令行三处 seed 必须一致。
- **不得**再把 `sample_index=0` 对外称作"数值 seed1"。
- 非法/负数/冲突（同时给 derived 语义与 explicit）→ 响亮失败。
- 测试：derived 正反 + explicit 正反。
- 单独 commit，不与 U7 混合。

### U7 — F2 多 fault 准入口径统一（保守 all()）
- 规则：一个运行中**每个实际 activated fault** 都必须独立形成（a）连续 parent-event 的完整
  L0→L5，或（b）真实、非 lifecycle、字段完整的提前 containment。**任一未闭合 ⇒ 整样本不
  admitted**（不得改成"任选一条通过即可"）。
- 统一 per-fault evaluator，输出每 fault 的 `fault_id/activated/selected ancestry/terminal/
  provable_to/contained/admission/violations`；样本级 `admitted = all(...)`。
- `check_admission`、`containment_from_events`、顶层 terminal、报告生成**消费同一份** per-fault
  结果，禁止各自重新选择 fault。
- 禁止：跨 fault 拼链、跨 sibling branch 拼链、用别的 fault 的 L5 补当前 fault、`chain_end`
  充当 terminal。
- 真实 `squash_masked` containment 仍可通过，条件：位于当前 fault 的连续 ancestry 上、
  `contained=1`、非空 `containment_reason`、合法 corr/request、非 lifecycle。
- 测试（≥7）：两 fault 均完整→PASS；一完整+一真实 containment→PASS；一完整+一 L4 unknown→FAIL；
  一完整+另一仅 chain_end containment→FAIL；L4 与 errant_commit 为 sibling branches→不得拼接；
  不同 fault 的 L4/L5→不得拼接；单 fault 旧行为不回归。
- 对现有六项 raw evidence 离线复判，输出 old→new diff；任何升级必须逐事件解释；任何降级如实记录。
- 单独 commit。

## 执行顺序

1. Phase 2：在**不改代码**前提下，用当前 T02-F2-W4 raw stream 复现三种选择不一致，保存修改前
   逐 fault verdict + 六项总 verdict 作为回归基线（`runs/lsu/0202_t02f2_diag_pre_baseline.json`）。
2. U6（测试先行）→ 验证 → commit。
3. U7（测试先行）→ 六项离线复判 diff → commit。
4. Phase 5：显式整数 seed `1` 单进程诊断运行，输出到
   `runs/lsu/0202_t02f2_legacy_seed1_diag_<ts>/`，标 `DIAGNOSTIC_REPLICATION_ONLY`；
   运行前确认命令含 `--tlb_rng_seed 1`。
5. Phase 6：逐 activated fault 严格验收。
6. Phase 7/8：按情况 A/B/C 结论；报告 `docs/gem5-fi/lsu/evidence/0202/R0202-T02F2-SEED1-DIAG.md`
   + JSON/CSV；推送非 main 分支。

## 停止条件

- 需要改 C++ 才能闭合 ⇒ 先停并提交 DECISION REQUEST。
- 发现 parent-event 发射器确定性错误 ⇒ 最小测试证明 + DECISION REQUEST。
- 完成后停止，不跑其他 seed/RunID。
