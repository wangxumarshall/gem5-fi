# L32 — R6 逐 RunID 权威状态表（`tools/lsu_r6_status_table.py`）

- 依据：`docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md`（分支 `lsu-mdspec-20261019`，commit 45611d59）§4/§5/§7。
- 基线 worktree：`.claude/worktrees/r6-status`（分支 `r6-status`，base `040688f2`）。
- 唯一提交：`[LSU][MDSPEC][R6-STATUS] ...`（单 patch 单 unit）。

## 目标
从真实证据推导 325 行权威表（JSON + Markdown），并打印 spec §7.1–3 状态计数摘要。
禁止：把缺失/未激活/截断证据说成 Masked/Contained/"无传播"。

## 交付物（本 lane 仅新建以下文件）
1. `tools/lsu_r6_status_table.py` — 生成器（新建）
2. `tests/test_lsu_r6_status_table.py` — 合成夹具单测（新建）
3. `docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json` / `.md` — 产物（新建）
4. `/home/sdc/gem5-fi-ding/runs/lsu/r6_reports/L32.md` — 报告（新建）
5. 本计划文件

## 步骤
- [x] P1 写工具骨架：CLI（--runs-root/--contract/--sha256/--checkpoint/--out-json/--out-md/--registry）
- [x] P2 证据发现：扫描 runs root，`seed*`/`<RunID>` 目录内 `prop_evt.txt.gz`；RunID 归属用精确名或 `_`-token 匹配；控制/阴性目录不计入 325
- [x] P3 逐样本：`lsu_prop_fields.read_events` 判定 truncated；`stats.txt` 非空 = 完整；`inj`(fault_id≠0) = activated
- [x] P4 真检查器：`C.check_chain(events, oracle_outcome=…)` + `C.check_admission(bundle)`（不重写规则）；超线性 → `--max-chain-events` 诚实上限
- [x] P5 状态派生（严格序）：BLOCKED→NOT_RUN→RUNNING→INFRA_FAILED→NO_ACTIVATION→ORACLE_INCOMPLETE→CHAIN_INCOMPLETE(Unknown)→CHAIN_INCOMPLETE(admission)→CHAIN_INCOMPLETE(stream integrity)→PILOT_READY
- [x] P6 输出 JSON+MD + §7 摘要 + 与 contract 类别分歧清单
- [x] P7 单测：合成夹具证明每种状态可达；截断流不计为 complete。真 FAIL → 修 → 真 PASS（3/3 PASS）
- [x] P8 真跑 runs root，引用真实计数；写 L32.md
- [ ] P9 commit + push `-u origin r6-status`

## 验证命令（真实执行并引用输出）
```
python3 tests/test_lsu_r6_status_table.py            # 先 FAIL 后 PASS
python3 tools/lsu_r6_status_table.py --runs-root /home/sdc/gem5-fi-ding/runs/lsu \
  --contract docs/gem5-fi/lsu/mdspec/ready_contract.json \
  --sha256 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt \
  --out-json docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json \
  --out-md   docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md
pytest -q tests/test_lsu_chain_check.py              # 未受影响回归
```

## 采信规则（诚实纪律）
- 无 stream ⇒ `NOT_RUN` / `not measured`。
- 有 stream 无 activated ⇒ `NO_ACTIVATION`。
- 截断或 stats 缺失/空 ⇒ 计 truncated，绝不计 complete。
- `PILOT_READY` 仅当 ≥1 activated 形成完整准入链（或严格 containment）**且** 全部 activated 通过 **且** 无截断/Unknown。
- 冻结二进制未产出前，SHA-256/checkpoint 取自 contract `gate` 块并显式标注 provisional。
