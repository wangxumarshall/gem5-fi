# 第三轮实测发现（campaign 全链路 / SQ / mshr / FS）

> 基线 `092ad663`。本轮只登记**实测得出**的结论；未完成的项逐条写明，不得当作完成证据。

## 1. campaign 全链路（用户第一节）

已实现并验证：

| 项 | 状态 | 证据 |
|---|---|---|
| SE 路径挂 CHAOSPropagation | ✅ | `c27bb782` + smoke（A01/P01，`campaign_smoke_report.md`） |
| FS 路径**解析**传播参数 | ✅ 本轮 | `configs/se/arm_chaos_fs.py` 新增 `--chaos_propagation/--prop_trace_file/--prop_run_id/--prop_sample_run_id`；缺对象或 `--cpu` 非 O3 时 **SystemExit**（不静默出空文件） |
| FS 路径 CHAOSPropagation 对象创建 | ✅ 本轮 | 追加于 Simulator 构造前，挂 `processor.get_cores()[0].core` |
| FS 资源复用 | ✅ 本轮 | `LSU_FS_DIR`（worktree 无 gem5-fs 子模块）→ 复用主树 `gem5-fs/`；`require_fs_assets()` 缺失时带提示硬失败 |
| 每样本 chain_report.json + 摘要 | ✅ 本轮 | `write_chain_report()`（oracle join）+ `run_cell_adaptive` 汇总 `<cell>/chain_report.json` 与 `chain_summary.md` |
| Crash/Abort/Timeout 保留前缀并标 truncated | ✅ 本轮 | Timeout 分支**先**写 chain_report 再返回；测试用**真正未结束**的 gzip 流（Z_SYNC_FLUSH 无 trailer）验证 `truncated=True` 且事件前缀计入 |
| SE/FS 命令构造测试 + 真入口 smoke | ✅ 本轮 | `tests/test_lsu_campaign_propagation.py` 17 项全绿（含 FS 命令断言）；FS 真入口 smoke 见下 |

**FS 真入口 smoke 实测**（`LSU_FS_DIR` 复用主树镜像 + 主树 B0 checkpoint
`runs/lsu/fs_cpt_boot/cpt.237949797015`）：
- 命令行被接受，`--chaos_propagation` 生效（打印 attached 行）；
- 产出 `armtlb_injections.log`（**注入非空**：`Tick: 237950940537, Site: arm_tlb_lookup_hit,
  VA: 0xffffffc009483fa8, old_pfn: 0x81d75, new_pfn: 0x100000000081d75, Mask: 0x100000000000000`）；
- 产出 `prop_evt.txt.gz`，**首行为 39 字段注册表头**（tracer 已启动）；
- **但 PROP-EVT 事件数 = 0**。

## 2. 新发现的结构性缺口（本轮实测，尚未实现）

**G1 — `CHAOSArmTLB` 从不向 CHAOSPropagation 注册链**（与上轮发现的 S 系同型）。
`grep registerInjection|notePropEvt CHAOS/gem5/src/arch/arm/CHAOSArmTLB/` = **0**。
CHaOSPropagation 只发射**已关联**事件，故头部就绪、事件为空。
**为何不是 15 行小改**：注入钩子是 `maybeCorrupt(ArmISA::TlbEntry*, Addr va)`——**只有 VA，没有
`Request`/`seqNum`**；而下游关联面（`tlb_translate`/`tlb_fault` 用 `correlateRequest(seq, va, size)`）
需要 dyn_seq。且 TLB 故障改的是 **PFN（PA 侧）**，登记 VA 范围无法让后续 cache 事件关联。
→ 需要设计步骤：在 `tlb.cc::lookup` 调用点把 Request/seq 传入，或新增"VA→PA 变更"登记面。

**G2 — `CHAOSLSQFwd`（S01/S02/S03/S08/S09）同上**（上轮已记录，本轮确认仍是主因，
与 `sq_execute` 缺观测相关）。

**G3 — `sq_execute` 未观测的根因（本轮缩小，未定论）**：
`sq_execute` 与 `sq_writeback`/`sq_complete` 用的是**同一个关联键**
（`correlateRequestBySeq(inst->seqNum)` → `addr_registry`），而后两者在 S04/S05 真实运行中
**成功落流** → 键本身有效。故剩余假设只有两个：(a) `executeStore` 触发时该注册项尚不可见
（dispatch vs issue 时序）；(b) 被注入指令是 load（`executeStore` 只在 store 上跑）。
**需要一次 `--debug-flags=LSQUnit` 定向运行**（检查被注入 seq 的 "Executing store" 行是否存在、
与 lsq_push 的先后），本轮未做。

**G4 — FS smoke 被**我自己的外层 `timeout 1700` **终止（exit 143 = SIGTERM）**，
不是实现失败、也**不是** campaign 的 per-sample `--fs-timeout` 路径**：
- 终止时该样本尚未跑完 → **没有**写出 `chain_report.json` / `cell_results.json`；
  本轮新增的"超时保前缀"路径因此**未在 FS 上得到验证**（仅在单元测试中验证过）。
- 磁盘上确有的 FS 产物：`armtlb_injections.log`（1 次注入）、`prop_evt.txt.gz`
  （229 B，仅 39 字段表头，0 事件）、`prop_trace.csv.gz`、gem5 自带 config/stats。
- 无残留 gem5 进程（SIGTERM 已传导，`pgrep -c gem5.opt` = 0）。
**下一步（已确认可行）**：外层超时须 > campaign `--fs-timeout`（1800s），
建议 2400s；完整 restore + tlb_probe 载荷单样本耗时 > 28 min 量级。

## 3. 本轮修掉的真实缺陷（由测试发现，非猜测）

1. `write_chain_report()` 在 outdir 不存在时崩溃 → 已加 `mkdir(parents=True)`（测试项
   "无流 → stream_present=False" 触发）。
2. 测试原以**正常闭合**的 gzip 断言 `truncated=True` → 假设错误；改为构造**真正未结束**
   的 gzip 流（`Z_SYNC_FLUSH` 无 trailer），与真实 abort 形态一致。

## 4. 未完成（本轮明确不做完，不伪装）

- 第二节 2：Cache `mshr_alloc` 的可重复载体、S 系注入器接入、SQ 四节点端到端关联。
- 第三节：49 个 MODE-UNIMPL（一项都未实现）。
- 第四节：A06 spike、FS-MULTICORE、LICENSE 适配。
- 第五节：READY/PARTIAL/BLOCKED 新口径与每 RunID 命令契约（部分已在
  `mode_unimpl_plan.md`/`blockers_for_approval.md` 铺垫，未成文为逐 RunID 契约表）。
