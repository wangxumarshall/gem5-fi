# 仓库根 README.md 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建仓库根 `README.md`——面向新读者（工程师/研究者）的 gem5-fi-fuzz 项目全景介绍，覆盖用户指定的四个维度：项目功能、特性、使用场景、解决的问题。

**Architecture:** 纯文档变更：只新增 1 个 Markdown 文件，不修改任何现有文件、不引入代码。事实来源三层：①叙事源 `docs/gem5/project-understanding.md`（权威全景）；②结果登记簿 `findings.md` / `task_plan.md` / `AGENT_TASKS.md`；③命令与路径事实源 `configs/se/`、`tools/`、`workloads/`、`CHAOS/`。README 中每个数字/路径/命令在 Step 4 用真实命令核验后方可定稿。

**Tech Stack:** GitHub Flavored Markdown（含 1 个 mermaid 流程图）；正文简体中文，命令/参数/文件名保持英文原文。

**Spec:** 用户请求（2026-10-20 会话）：「深度理解源码，创建Readme.md，撰写项目介绍包括项目功能、特性、使用场景和解决的问题等」

## Global Constraints

- **诚实纪律（CLAUDE.md 强制）**：README 中每个数字、路径、命令必须真实可核验；宁缺勿错；负结果必须如实呈现（本仓文化：诚实负结果与正结果同等重要）。
- **语言**：简体中文为主，技术标识符保持英文。
- **单提交单元**：本计划文件 + README.md 同一 commit（先例：38d717df「Task 0 脚本 + 评估计划」同 commit）。
- **主工作区 rebase 保护（本计划特有的硬约束）**：主树处于用户进行中的 `git pull --rebase`（main → 9dbbbbba，剩 76 pick，reflog 证据 `pull (start): checkout 9dbbbbba`）。全部提交在隔离 worktree 分支 `docs/root-readme`（基于 9dbbbbba = origin/main）完成并推送；**不得 continue/abort 用户的 rebase；不得 push main；不得在主树留下 tracked 变更**。
- **Commit message** 不以 `Co-Authored-By: Claude <noreply@anthropic.com>` 结尾（CLAUDE.md 明令）。
- **已核验的安全前提**：`git log --all --diff-filter=A -- README.md` 输出为空——任何分支的历史都从未存在过根 README.md，新文件与 76 个待变基 pick 零冲突；`docs/superpowers/plans/2026-10-20-root-readme.md` 为今日新文件名，同样无冲突（执行时复核）。

---

### Task 1: 撰写根 README.md + 事实核验 + 提交推送

**Files:**
- Create: `README.md`（仓库根，约 300 行）
- Create: `docs/superpowers/plans/2026-10-20-root-readme.md`（本计划，随同提交）

**Interfaces:**
- Consumes: 仓库现有文档与源码事实（Step 2 事实清单；探索结论已在会话中，执行时以原文复核为准）
- Produces: 根 `README.md`；远端分支 `origin/docs/root-readme`（恰好 1 个 commit）

- [ ] **Step 1: 创建隔离 worktree（避开主树 rebase）**

```bash
df -h /home/sdc | tail -1   # 确认磁盘余量足够再检出一份 tracked 树
git worktree add /home/sdc/wangxu/gem5-fi-fuzz-readme-wt -b docs/root-readme 9dbbbbba
git status   # 预期：主树仍显示「交互式变基操作正在进行中」——未被破坏
```

- [ ] **Step 2: 锁定事实清单（读权威原文，不采信转述）**

在 worktree 中 Read（执行时逐项打勾核对，数字以原文为准、与下表不符时以原文为准并修正 README 草稿）：

- `docs/gem5/project-understanding.md` — 三带格局数字：L1D 命中数据 97.7% [95.6,98.8] / L1D post-ECC 90.9% / LSQ 错源转发 37.6% / PRF 3.9% / L1I 0%；保护投资排序 l1d 5.46% > l1d_fwd 5.09% > lsq_fwd 4.45% ≫ physreg 0.33%
- `CHAOS/gem5_base_version.md` — 基线 v25.1.0.1-6-g62c7bf2848（stable 分支）
- `CHAOS/README.md` — 上游 CHAOS 4 模块（Reg/PhysReg/Cache/Mem）、三类基础故障（bit_flip/stuck_at_zero/stuck_at_one）、SimObject 机制
- `findings.md` — 19 个注入器清单、F1–F6/PCE 结构化故障模型、SVE/SME 保真度 F3/F4、J1'–J3' 裁决（J1' PASS / J2' 满足 / J3' 不成立）
- `configs/se/arm_chaos.py` — CLI 事实：`--chaos_*` 开关族、`--sve_vl/--sme_vl`（choices 1/2/4/8，单位 128-bit）
- `tools/runner.py`、`tools/campaign.py` — CLI 签名与黄金校验和锚（reg_chain `f247ef3fe6f02cfd`）

必须写进 README 且须核验的关键事实汇总：

| # | 事实 | 值 | 源 |
|---|---|---|---|
| 1 | 项目一句话定位 | 从生产级故障取证走向微架构级故障注入的 SDC 研究基础设施 | docs/gem5/project-understanding.md 开头 |
| 2 | 起因案件 | 鲲鹏 920（192 核 TaiShan-v110）CPU179 核 22 天 19 次致命 panic，归因 LSU 数据返回通路 SDC | docs/cases/ 综合报告 |
| 3 | gem5 基线 | v25.1.0.1-6-g62c7bf2848 | CHAOS/gem5_base_version.md |
| 4 | 上游 CHAOS | eliovinciguerra/CHAOS，4 模块，位级故障 | CHAOS/README.md |
| 5 | 本仓注入器规模 | 顶层 19 个注入器目录；vendored 树 22 类（含 CHAOSCov/FUPerm/GateFU） | CHAOS/ 目录枚举 |
| 6 | 构建命令 | `scons -C CHAOS/gem5 build/ARM/gem5.opt -j16` | progress.md 记录 |
| 7 | 单次注入 | `python3 tools/runner.py <manifest.yaml> --binary <bin>` | tools/runner.py CLI |
| 8 | 战役 | `python3 tools/campaign.py campaigns/<x>.yaml --binary ... --n-per-cell ... --jobs ...` | tools/campaign.py CLI |
| 9 | 分类体系 | 六类有序互斥：SimulatorError→Hang→Crash→Inactive→Masked→SDC | tools/classify.py |
| 10 | 三带格局 | 见上方 Step 2 首条 | docs/gem5/project-understanding.md:94-100 附近 |
| 11 | H5 复现 | byte_lane_skew rot1 → 28/30（93%）PTR_CORRUPT，位谱 100% mantissa / 0% sign | docs/gem5/project-understanding.md |
| 12 | H1 read-trace | reads_before_overwrite 中位 1,975,000；P(SDC\|reads>0)=1.000 | task_plan.md 终态 |
| 13 | 诚实负结果 | H2 天花板效应、J3' 不成立、SDC-ED Round1 未达成、Round2 J2 FAIL（AUC 0.51-0.55）、CE-1 ED 落败于 ACE、真机 3 板扫描真 SDC=0 | findings.md / docs/sdc-ed/ |
| 14 | 子模块 | gem5-fs（已 checkout）；sdcshield（未 init，需 `git submodule update --init`） | .gitmodules + git submodule status |
| 15 | Harpocrates 复现 | 论文核心主张全部复现且无违反 | docs/harpocrates/reproduction-report.md |

- [ ] **Step 3: 撰写 README.md（worktree 中，章节结构固定）**

```text
# gem5-fi-fuzz
   一句话定位 + 四导航链接（project-understanding / findings / task_plan / AGENT_TASKS）

## 1. 背景与解决的问题
   CPU179 故事（19 次 panic → LSU 数据返回通路 SDC）；由此导出的研究问题：
   哪个微架构单元、什么故障形态、多大几率产生 SDC；如何量化保护投资排序。

## 2. 总体架构
   1 个 mermaid 图：campaign YAML → runner → gem5(CHAOS SE/FS) → classify 六分类 → cells.csv/summary.md(Wilson CI)

## 3. 核心功能（7 块）
   ① 19+ 微架构注入器（表格：注入器 | 目标结构 | 代表故障模式）
   ② SE/FS 双模式配置（arm_chaos.py / arm_chaos_cache.py / arm_chaos_fs.py / fs_checkpoint.py）
   ③ campaign 化实验基础设施（runner/campaign/classify/escape_decomp/fisher_test/report/fingerprint/loo）
   ④ 生产故障诊断引擎（tools/diag：ESR 解码、openEuler vmcore 解析、P1-P11/N1-N10 规则）
   ⑤ SDC-ED 评分链与 Harpocrates 资产（ed_profile/ed_score/ed_select、harp_wrap/harp_eval）
   ⑥ SVE/SME 全规格评估（--sve_vl/--sme_vl 128-1024-bit、双通道内核 fixed/random）
   ⑦ DFT 向量打包（dft/manifest.yaml + run_all.sh）

## 4. 特性（6 条）
   结构化故障模型（F5 合法域替换/字节通道偏斜/相位偏移——不止位翻转）；
   read-trace 闭环（reads_before_overwrite 关闭"故障是否传播"问题）；
   六类有序互斥分类 + Wilson 95% CI；预注册假设体系（H0-H8 / J1-J4 / J1'-J3'）；
   manifest v1/v2 schema 种子级可复现；诚实边界制度（负结果入档）

## 5. 快速开始（全部真实命令）
   前置（子模块/工具链）→ 构建 gem5 → verify_gem5_injectors.sh 验证注入器
   → 单次注入（runner.py）→ 战役（campaign.py）→ 裸 gem5 调用示例 → FS 模式与 checkpoint

## 6. 目录结构（表格）

## 7. 关键研究结果
   三带格局表 + FSU 精度谱 + H5 93% + H1 read-trace + 保护投资排序
   + Harpocrates 复现结论 + 诚实负结果清单（单独小节，逐条列出）

## 8. 使用场景（5 类）
   微架构 SDC 机理研究 / 保护投资排序（ECC-parity-该投哪）/ DFT 定向筛查向量 /
   检测工具与度量评估（SDCShield、SDC-ED、Harpocrates 覆盖指标）/ 生产 vmcore 故障诊断与对照

## 9. 文档导航
   docs/ 地图 + 四大登记簿（AGENT_TASKS/task_plan/findings/progress）+ 计划库

## 10. 诚实边界
   gem5 O3 ≠ TaiShan v110 RTL；TSO-vs-弱内存不可建模（O3 LSQ 同源）；
   SE 模式无 MMU（RAT/ROB/PTW 等 FS-only 注入器在 SE 恒 0 注入为已知伪迹）；
   单机未复现/未做硅片验证；结论严格限定可建模维度
```

- [ ] **Step 4: 事实核验（真实命令，输出留作提交依据）**

```bash
cd /home/sdc/wangxu/gem5-fi-fuzz-readme-wt
# 4a. README 引用的全部路径存在（一次性列出）
ls -d CHAOS/README.md CHAOS/gem5_base_version.md configs/se/arm_chaos.py \
  configs/se/arm_chaos_cache.py configs/se/arm_chaos_fs.py configs/se/fs_checkpoint.py \
  configs/cpu-profiles tools/runner.py tools/campaign.py tools/classify.py tools/escape_decomp.py \
  tools/fisher_test.py tools/report.py tools/sdc_fingerprint.py tools/loo_validate.py \
  tools/ed_profile.py tools/ed_score.py tools/ed_select.py tools/verify_gem5_injectors.sh \
  tools/diag workloads/directed workloads/harp workloads/sdcshield campaigns manifests schemas \
  rules/flight-rules.md dft fi_research/EXPERIMENT_DESIGN.md docs/gem5/project-understanding.md \
  docs/sdc-ed docs/harpocrates docs/hypothesis/ARM64-SDC-uArch.md docs/cases gem5-fs cpts tests \
  AGENT_TASKS.md task_plan.md findings.md progress.md
# 4b. 关键数字溯源（README 中每个数字都要能指出处）
grep -n "97.7" docs/gem5/project-understanding.md
grep -n "5.46" docs/gem5/project-understanding.md
# 4c. 命令事实
grep -n "sve_vl" configs/se/arm_chaos.py | head -5
grep -n "f247ef3fe6f02cfd" tools/runner.py | head -3
# 4d. 回归检查（CLAUDE.md 强制：至少一个不受影响的测试 pass）
#     在主树运行——worktree 缺少被 ignore 的 runs/artifacts 数据；主树写入物（__pycache__/.pytest_cache）均被 ignore，不影响 rebase
cd /home/sdc/wangxu/gem5-fi-fuzz && python3 -m pytest tests/test_report.py -q
```

预期：4a 全部路径存在；4b/4c 逐条命中；4d 全部 PASS（纯文档变更不应影响任何测试）。

- [ ] **Step 5: 提交并推送（单 commit：计划 + README）**

```bash
cp /home/sdc/wangxu/gem5-fi-fuzz/docs/superpowers/plans/2026-10-20-root-readme.md \
   /home/sdc/wangxu/gem5-fi-fuzz-readme-wt/docs/superpowers/plans/
cd /home/sdc/wangxu/gem5-fi-fuzz-readme-wt
git add README.md docs/superpowers/plans/2026-10-20-root-readme.md
git commit -m "docs: 创建仓库根 README.md——项目全景介绍（功能/特性/使用场景/解决的问题）

基于三源事实核验：docs/gem5/project-understanding.md 叙事源、findings.md/task_plan.md
结果登记簿、configs+tools+workloads 命令事实源。含诚实负结果清单与诚实边界章节。
回归：pytest tests/test_report.py 全 pass。"
git push -u origin docs/root-readme
```

- [ ] **Step 6: 清理与主树还原**

```bash
git worktree remove --force /home/sdc/wangxu/gem5-fi-fuzz-readme-wt
#   （commit 已推送；--force 仅丢弃 pytest/pycache 等未跟踪产物）
rm -f /home/sdc/wangxu/gem5-fi-fuzz/README.md \
      /home/sdc/wangxu/gem5-fi-fuzz/docs/superpowers/plans/2026-10-20-root-readme.md
cd /home/sdc/wangxu/gem5-fi-fuzz && git status
# 预期：主树仍处「交互式变基操作正在进行中」、工作区干净、无未跟踪残留
git worktree list   # 预期：仅剩主 worktree
```

---

## Self-Review 结论

1. **Spec coverage**：用户四维度——解决的问题→§1；功能→§3；特性→§4；使用场景→§8。均有着落。✓
2. **Placeholder scan**：无 TBD/TODO；验证命令均为可直接执行的真实命令。✓
3. **一致性**：分支名全篇统一 `docs/root-readme`；worktree 路径统一 `/home/sdc/wangxu/gem5-fi-fuzz-readme-wt`。✓
