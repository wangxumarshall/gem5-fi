# MDSPEC 收口 Pilot 报告（5 RunID，真实运行）

> 二进制：worktree `CHAOS/gem5/build/ARM/gem5.opt` sha256 前缀 `746b0b91d485b00e`（含 H4/H5/H6 全部新钩子）。
> 直驱方式：`gem5.opt --outdir <dir> configs/se/lsu_proxy.py ... --chaos_propagation --prop_run_id <RunID> --prop_sample_run_id pilot-s<N>`
> （campaign 工具链不挂 CHAOSPropagation——见 `tools/lsu_campaign.py` 无 `--chaos_propagation`；pilot 一律显式直驱）。
> **正式 campaign 未启动**；n=1/样本仅验证链与机制，不产正式统计。

## 结果总览（真实输出）

| Pilot | 载体 | gem5 exit | 注入日志（非空证明） | 链终局 | provable_to | beyond | L5 oracle |
|---|---|---|---|---|---|---|---|
| **A01-F0-W3** | agu_addrmodes | 134 (Abort) | FUNNEL attempted=617 eligible=617 injected=1 | `crash_translation_blocked` | L2 | （闭合） | Crash |
| **A04-F0-W3** | agu_addrmodes | 0 | FUNNEL attempted=617 eligible=617 injected=1 | `full` | L5 | （闭合） | Masked |
| **C01-F0-W6** | cache_dirtyevict | 0 | `Tick: 1000000, Cache Block Addr: 474432, Byte Offset: 3, FaultType: bit_flip` | `full` | L5 | （闭合） | SDC |
| **P01-F0-W8** | prefetch_stride | 0 | `Site: P01_stride_bitflip Tick: 80850 pf_addr=0xbcdc0 stride 0 -> 268435456 (bit 28)` | `full` | L5 | （闭合） | SDC |
| **O01-F0-W7** | atomics_probe（SE 载体） | 0 | `Tick: 15408855, Site: isa_handleLockedRead, mode=o01_monitor_addr_bitflip, addr=0x769a0 -> monitor addr=0x7692` | `full` | L5 | （闭合） | SDC |

## 逐层链路（事件种类 → 层级，实测）

- **A01-F0-W3**：inj(L0) → addr_form(L1) → lsq_sendfrag+mem_req+tlb_translate+tlb_fault(L2)
  → **L3+ missing**（gem5 exit 134：corrupted EA 落到未映射地址 → GenericPageTableFault panic，
  运行在 L2 处中止，退出回调不运行）。`tlb_fault` 携带 `detection_layer=Hardware`、`contained=`（空）。
- **A04-F0-W3**：inj→addr_form→lsq_push→lsq_sendfrag→mem_req→tlb_translate→lq_read→resp→lq_complete→taint_reg→consumer×21→errant_commit→chain_end，5 条边全 proven。
- **C01-F0-W6**：inj→cache_access×2→cache_return×2→resp×2→lq_complete→taint_reg→consumer×7→errant_commit→chain_end。
- **P01-F0-W8**：inj→pf_train(L1)→cache_access×26(L1)→cache_return×26+pf_fill×2/mshr_fill×2/fill_id(L2/L3)
  →resp×26+lq_complete×14+pf_demand×26(L3/L4)→taint_reg×14+consumer×481+errant_commit(L4)→chain_end(L5)。632 事件。
- **O01-F0-W7**：inj→exmon_monitor(L1)→cache_access×736/cache_return×736(L2)→exmon_rmw×295(L2)+exmon_stxr×295(L3，
  重试环逐次)→resp×735/taint_reg×1241(L3/L4)→consumer×2113+errant_commit(L4)→chain_end(L5)。6817 事件。

## 诚实边界（不得当作已完成的地方）

1. **P01 的 L2 队列/发射节点未被本次样本观测到**：单次 F0 注入后，被盗 stride 未再生成候选
   （故障被训练过程吸收）→ `pf_queue`/`pf_issue` 无链内事件。**机制可用性由 P03(addr_subst) 真实运行单独证明**
   （pf_queue×4 / pf_issue×4 / pf_fill×9 / pf_demand×31，各请求 pf_request_id 互异且≠fault_id）。
   本样本链终局 full 由 pf_train→cache_return→pf_fill→pf_demand→errant_commit 成立，**未把未观测节点算作已观测**。
2. **O01 用 SE 载体探针**：规格 O01 的负载 `Atomic-Litmus` 是多核 FS 负载（`workloads/directed/atomics_probe.c`
   文件头已实证记录）。本轮以 atomics_probe 验证注入器与链机制；**正式 O01-F0-W7 网格格保持 BLOCKED**（多核 FS），
   L4「后续线程消费」与 litmus forbidden-outcome 在单核 SE 下**不可判别 → Unknown**。
3. **A01 的终局**：`tlb_fault` 的 contained 保持为空，终局由 `--oracle-outcome Crash`（runner/L5 分类器实测）join
   得到 `crash_translation_blocked`；**未对翻译 fault 无条件写 contained=1**，oracle 干净时也不推断 Masked/Contained。
4. **C01 未观测 mshr_alloc**：该样本命中路径（line 已在 cache 内），覆盖矩阵"单元级节点能力"如实标
   `unobserved:mshr_alloc`。
