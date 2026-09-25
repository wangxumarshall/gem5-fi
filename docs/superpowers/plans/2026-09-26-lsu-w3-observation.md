# LSU W3 — 观测层 L0–L5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans / subagent-driven-development。

**Goal:** 一次已知注入运行 vs 无故障参照的 L0–L5 全链可产出（09 W3 出口判据，M1 另一半）。

**Architecture:** 复用优先（09 W3 原文）：L4=CHAOSCommitTrace+commit-diff 两遍法（已在 C3/C4-LSU 可挂，W0 已放行 --ctrace）；L1=CHAOSMicroSnap 快照+离线 diff（已挂 commit 锚点）；L0 activated=扩展 chaos_l0.hh 的 per-item read-back 口径（W2 R2 移交）；L5=分类闭合断言（tools 侧）+ W2 已知项（abort 运行漏斗行缺失→分类器兼读注入日志）。

**Spec:** `docs/gem5-fi/lsu/04-observation-points.md`（L0–L5 六层权威）+ `09-implementation-plan.md` W3 + `05-frequency-and-sampling.md` r12–r15（统计口径）。

## Global Constraints

- 分支 fi-ding；显式路径 staging；commit 无尾注；push 被拒先 rebase。
- 04 L0 权威口径：attempted/eligible/activated 分开；**activated=故障被下游读取/使用**；未 activated 不进 SDC 率分母。
- L5 守恒式（04 L5）：`Activated = Masked + Detected + SDC + Crash + Timeout`——回填工具内建断言。
- 复用件零改动优先：CHAOSCommitTrace/CHAOSMicroSnap 已在 lsu_proxy.py 克隆面（--chaos_ctrace/--chaos_msnap）；W2 已放行 runner --ctrace C4-LSU。
- 回归锚：reg_chain `f247ef3fe6f02cfd` + mini_check `07568da9f3ad5665` 双 golden 不变。

## 已核实事实（W1 §2.1 + W2 实证）

- chaos_l0.hh（165 行 header-only）：ChaOSL0State per-item（active/target_key/reads_before_overwrite/overwritten/overwritten_at_cycle）+ chaosL0Register/chaosL0CountRead/chaosL0Overwrite/chaosL0Sync + exit 回调一行打印（CHAOS_L0: ...）——**无三计数漏斗**（W1）。
- W2 漏斗：CHAOS_LSU_TRIGGER: attempted/eligible/injected（chaos_lsu_trigger.hh，CHAOSAddrPath 消费者已打印）。
- W2 已知项：abort 运行 exit callback 不达 → 漏斗行缺失；L5 分类器须兼读 addrpath_injections.log（注入计数）。
- CHAOSCommitTrace：commit 每指令一行 CSV（tools/commit_diff.py 消费）；CHAOSMicroSnap：每 msnap_every 提交指令一行 µarch 快照（tools/micro_diff.py 按 snap_seq 对齐）。两者 READ-ONLY 硬门：挂载后 workload 终校验和逐字节不变。

## File Structure

```
CHAOS/gem5/src/cpu/o3/chaos_l0.hh        [Modify — 三计数漏斗结构（W2 R2 落地）]
CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/*    [Modify — L0 注册/read-back 钩子]
tools/lsu_l5_classify.py                 [Create — L5 闭合分类器（漏斗+注入日志+golden 比对）]
```

---

### Task 1: L0 activated（read-back 口径落地）

**Files:** Modify `chaos_l0.hh`、`CHAOSAddrPath.cc`

- [ ] Step 1: chaos_l0.hh 加 `ChaOSL0Funnel`（与 ChaOSL0State 并列）：`struct ChaOSL0Funnel { uint64_t attempted=0, eligible=0, injected=0, activated=0; void line(const char*) const; }`（一行打印 `CHAOS_L0_FUNNEL: injector= attempted= eligible= injected= activated=`）。W2 触发层的三计数迁移/桥接到此（chaos_lsu_trigger.hh 的计数保留，注入器在 exit 时合并打印——两行并存，W2 行已量产）。
- [ ] Step 2: CHAOSAddrPath L0 注册：注入时 `chaosL0Register(target_key=新 vaddr)`；激活判定=被腐蚀的 Request 翻译完成且未被 squash——LSQ 侧在 `initiateTranslation` 完成回调（lsq.cc TranslationFinished 路径）对已注册 key 计 `chaosL0CountRead`。最小实现：CHAOSAddrPath 记录注入的 vaddr，exit 时对照注入日志中"该 vaddr 的翻译是否完成"——若最小实现不可判，则诚实降级：activated=「注入后运行未在翻译前 squash」按 Request 存活近似，注释声明近似口径。
- [ ] Step 3: 验证：F0 mini_check 单发运行 → `CHAOS_L0_FUNNEL ... injected=1 activated=?`（值随负载，字段齐全即过）；无注入运行无 FUNNEL 行（默认 off 零回归）。

### Task 2: L1–L4（复用件接线验证 + LSU 字段扩展清单）

- [ ] Step 4: C4-LSU 上 --chaos_ctrace + --chaos_msnap 无注入运行 → 双 golden 不变（READ-ONLY 硬门）+ commit_trace.csv.gz/micro_snap.csv.gz 产出。
- [ ] Step 5: 已知注入（F0 addrpath）运行 vs 无故障参照（同 seed --no-inject）→ commit_diff.py 产出首分歧 commit 序号；micro_diff.py 产出首分歧 snap——即 L1（µarch 首偏）与 L4（架构首分歧）双锚。
- [ ] Step 6: L1 的 LSU 字段扩展（AGU EA/TLB 映射/SQ 守恒/Cache tag-data-state/exclusive monitor/prefetch queue——04 L1 必采清单）：CHAOSMicroSnap 现有字段盘点 → 差额清单写入 09 §3-W3 备注（各注入器单元 W4-W8 内逐字段补——不在此批量）。

### Task 3: L5 闭合分类器

- [ ] Step 7: `tools/lsu_l5_classify.py`：输入一次运行的 (outdir, golden)；读 stdout 漏斗行（CHAOS_LSU_TRIGGER/CHAOS_L0_FUNNEL）+ 注入日志（abort 兜底）+ workload 校验和 vs golden + exit 码/超时 → 输出 `Activated = Masked + Detected + SDC + Crash + Timeout` 闭合校验的五分类行（Injected-not-activated 单列）。Crash 双拆分（gem5 断言≠架构崩溃）按 stderr panic/assert 行（v1.4 已有口径）。
- [ ] Step 8: 验证：F0 Masked 运行（mini_check, checksum==golden）→ 分类 Masked、闭合式过；F3 DUE 运行（l1d_reduce abort）→ 分类 Crash（gem5 断言拆分标 DUE）、漏斗从注入日志恢复、闭合式过。
- [ ] Step 9: 回归：双 golden + B0 断言（默认全 off）；commit（chaos_l0.hh + CHAOSAddrPath + tools/lsu_l5_classify.py + 本计划）。

## Self-Review
- 覆盖 09 W3 六条：L0（Task1）/L1（Task2 Step5-6）/L2-L3（复用 probe 面——04 L2/L3 的必采量属各注入器单元，此处诚实列为 W4-W8 逐字段，不虚报完成）/L4（Task2 Step5）/L5（Task3）+验证（Step8 一次已知注入全链）。
- 诚实边界：L2（请求形成/排序）与 L3（缓存/一致性）的**新观测点**不在 W3 批量新建——现有 CHAOSCommitTrace/CHAOSMicroSnap/probe 面覆盖的部分先接通，专用观测随 W4-W8 注入器逐个落地（09 W3 原文同此粒度）。
