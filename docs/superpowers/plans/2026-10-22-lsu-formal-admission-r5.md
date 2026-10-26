# R5：LSU 正式实验准入收官（恢复 → 修复 → 复测 → 裁决）

- 分支：`r4-10-spec`（worktree `.claude/worktrees/r4-10-spec`）
- 基线 HEAD：`b113fab4`
- 日期：2026-10-22
- 权威规格：`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md` + 4 个子文档（-03/-07/-09/-10）
- 约束：one-patch-per-unit；每单位 = 一个 commit；构建/实验严格串行；不改共享证据 `docs/gem5-fi/lsu/mdspec/*` 除非本计划明确列出；不得覆盖源 xlsx。

## 0. 现场恢复（真实证据，非口头结论）

- 主仓库 `/home/sdc/gem5-fi-ding`：分支 `fi-ding`，HEAD `6f98088a`；工作树有 69 个 `docs/gem5-fi/lsu/**` 跟踪文件被删除 + 176 个未跟踪文件（`artifacts/` 141、`campaigns/` 28 等）。**本计划的全部工作不落在主工作树**，避免与其他会话冲突。
- `r4-10-spec` 是 `fi-ding` 的后代（0 behind / 148 ahead），且与 `origin/r4-10-spec` 完全同步（0/0）。
- 运行中任务：`/tmp/r4-10-spec/census.sh` → gem5 PID 2133313（S01-F0-W1 span census，`w1_all`），2026-10-22 17:44 启动；经两轮 512 s 采样线性增长（~492 B/s，~17 行/s，99.8% CPU）→ **正常推进，不停滞、不失败**。ETA 约 2026-10-23 01:00–01:15，或触发 `SE_W1=43200 s` 超时。**不杀、不干预。**
- 资源：load 1.2；MemAvailable 26 GiB；`/home` 可用 77 G。**不启动 stress-ng / 无意义 CPU backfill。**

## 1. 权威准入复现（不沿用旧数字）

```
$ python3 tools/lsu_ready_contract.py
[ready_contract] total=325 READY=241 PARTIAL=0 BLOCKED=84 self_consistent=True
[ready_contract] blocked_by_category={'RULING':6,'FS-INFRA':24,'MODE-UNIMPL':3,'UNRESOLVED':4,'FS-MULTICORE':35,'LICENSE':12}
```

325 集合核对（独立脚本）：ready_contract / runid_map / 规格 -07 / 规格 -09 四集合两两对称差 = 0，union = intersection = 325。源 xlsx sha256 = `389546f0…` 与主文档头一致。

## 2. 三路审计结论（Agent A/B/C，只读）

**已证实的真实缺陷（必须修）**

| # | 缺陷 | 证据 | 影响 |
|---|---|---|---|
| D1 | `tests/test_lsu_hook_tlb.py`（2 失败）、`tests/test_lsu_hook_cpf.py`（13 失败） | 直接运行 rc=0 但 `FAILED(2)/(13)`：夹具缺 `corr`，而 `tools/lsu_prop_fields.py` 自 commit `acc19511`（R4-4 评审 Important-1）起把 `corr` 列为全部入链事件必录 | 两个 hook 契约套件静默红 |
| D2 | 门禁 `pytest tests/ -q` **只收集 21 个测试**；~50 个 `tests/test_lsu_hook_*.py` 是 `main()` 独立脚本，**从不被收集** | `pytest --collect-only -q` → 21；D1 的红因此长期不可见 | 门禁"全测试"名不副实 |
| D3 | "唯一正式启动命令" 实为 `--phase trial --max-seeds-per-cell 3`，却被命名为 `formal_325` | `tools/lsu_ready_contract.py:103-113`、`SEEDS_PER_CELL=3` | 与用户硬性要求冲突（trial ≠ 正式） |
| D4 | 该命令未被任何测试机器校验 | `grep FORMAL_OUTDIR tests/` 无命中 | 条件 4 不成立 |
| D5 | 命令硬编码 `$PWD/CHAOS/gem5/build/ARM/gem5.opt`（CLAUDE.md 明令的过期重复路径） | 主树该路径为悬空符号链接 | 命令不可直接运行 |
| D6 | 已提交的 GO 门禁块记录 `pytest_rc=1`（2 failed, 19 passed），随后该块在工作树被删（未提交） | `git show HEAD:…ready_contract.json` 含 gate；工作树无 | 准入证据被静默抹除 |
| D7 | 准入台账互相矛盾：`blocked_triage.md`（标题 126 / 头 100 / 表 106）、`blockers_for_approval.md`（126=77+49）、契约（84）；18 个 RunID 台账 BLOCKED 但契约 READY | Agent C `/tmp/agentC-scratch/blocked_cmp.py` | 用户据以裁决的台账陈旧 42 项 |
| D8 | `tests/test_lsu_hook_s10_span.py` 被 `tools/lsu_campaign.py:935` 引用但**不存在** | grep | interval↔header 锁定无强制 |
| D9 | `ready_contract.json` 的 gate 块被本轮主 agent 的只读重生成清零（mtime 19:58） | `git status` → `M ready_contract.json` | 需以确定性方式重建 |

**分类裁决（Agent C）**

| 类别 | n | 是否可自解 |
|---|---|---|
| LICENSE (W11 SPEC) | 12 | 真外部（授权） |
| FS-MULTICORE | 35 | 混合：一半为 `num_cores=1` 硬编码配置（可自解），一半真外部（litmus/PARSEC 语义） |
| FS-INFRA (T*-W4) | 24 | `round4_findings.md:1529` 自述"**非外部阻塞**…缺的是工时"；根因 `CHAOSArmTLB.walker=None` 已修（`e4dcd5da` 为 HEAD 祖先）；但 FS 载体在预算内不终止 → 无 L5 |
| MODE-UNIMPL (T08-W9) | 3 | T08-a 已实现并真机证明；T08-b/c/d 未实现（`3db770fb` **非** HEAD 祖先） |
| RULING (A06) | 6 | 规格级裁决 |
| UNRESOLVED | 4 | S01/S02-F0-W1 待 census 收敛；S10-F2-W5/W9 结构性不可达（F2 首抽下界 50000 ≫ 实测流 3/4，改 interval 即改故障模型语义，禁止） |

## 3. 工作单元（一 unit 一 commit）

- [ ] **U1** 修复 D1：两个 hook 套件夹具对齐 `corr` 契约（RED→GREEN，引用真实输出）
- [ ] **U2** 修复 D2：门禁改为真实运行全部独立 hook 套件（新增 runner + gate 接入），并修 D8 缺失测试引用
- [ ] **U3** 修复 D3/D4/D5：正式启动命令改为 `--phase screening --screening-target 385`、正确的 `LSU_GEM5_BIN`、并由新测试机器校验
- [ ] **U4** 修复 D7：由 `tools/lsu_blocked_triage.py` 确定性重生成台账，消除 42 项漂移与三处总数矛盾
- [ ] **U5** 修复 D6/D9：确定性重建 `ready_contract.json`（含真实 gate 块，如实记录测试结果）
- [ ] **U6** FS-INFRA(24) 逐项处理：核实根因修复状态与真实运行证据；能解则解，不能解则产出逐项不可达证据（配置+代码路径+真实运行）
- [ ] **U7** FS-MULTICORE(35) 逐项拆分：可自解的 `num_cores=1` 部分处理；真外部部分给出证据并请求规格裁决
- [ ] **U8** MODE-UNIMPL(3)：评估合并 `r4-10-fsinfra`（T05/T06/T07）与 T08-b/c/d 是否在本轮范围；否则给出逐项不可达证据
- [ ] **U9** UNRESOLVED(4)：census 收敛后写 `LSQFWD_F0_SPAN` 行并契约钉死；S10-F2 登记结构性拒绝
- [ ] **U10** 终局：重跑权威准入 + 325 机器核对 + 正式命令校验 + 独立审查 agent 复核 + 汇报

## 4. 状态日志

| 时间 | 事件 |
|---|---|
| 2026-10-22 20:0x | 现场恢复完成；权威准入复现 241/84；三路审计返回 D1–D9 |
