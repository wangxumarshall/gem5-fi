# MDSPEC Pilot 报告：A01-F0-W3（n=5 activated，串行 workers=1）

> 计划 Task C2 交付。**正式 campaign 未启动**——本 pilot 仅验证观测链与指标机制。

## 运行配置

- RunID：A01-F0-W3（AGU 单比特翻转 · F0 单发 · AGU-AddrModes）
- 命令：`lsu_proxy --cmd workloads/directed/agu_addrmodes --cpu O3 --chaos_addrpath --addrpath_mode a01_bit --addrpath_max_faults 1 --addrpath_rng_seed <S> --chaos_propagation --prop_run_id A01-F0-W3 --prop_sample_run_id pilot-s<N>`
- 种子：20260826..20260830（s1..s5）；串行（≤4 并发硬上限内）；gem5.opt sha256=`76d32730878a0f9c…`
- golden 对照：无注入 FINAL=`728e604ffcec539d`（A0.3 基线）

## 平台发现（Phase B 实证，影响本 pilot 全部样本）

SE 负载 F0 触发=首个 eligible 事件，恒为运行时启动 store 微操（`strqbfpxi_uop`，dyn_inst_seq=133）——跨 4 负载 + 3 seed + warmup 20-500 实证。A01-F0-W3 的 5/5 样本均命中此启动 store。

## 逐样本结果（真实输出）

| 样本 | seed | gem5 exit | 结局 | 链判定（lsu_chain_check.py） | FINAL vs golden |
|---|---|---|---|---|---|
| s1 | 20260826 | 134 | **Crash**（GenericPageTableFault panic @ faults.cc:103——corrupted EA 落到未映射地址，A3 先例同签名 guest_arch_fault 合法结局） | provable_to_L2_then_unknown（5 事件） | n/a（workload 终止） |
| s2 | 20260827 | 134 | **Crash**（同上） | provable_to_L2_then_unknown（5 事件） | n/a |
| s3 | 20260828 | 0 | 正常完成 | provable_to_L2_then_unknown（5 事件） | **逐位一致** `728e604ffcec539d` |
| s4 | 20260829 | 134 | **Crash**（同上） | provable_to_L2_then_unknown（5 事件） | n/a |
| s5 | 20260830 | 0 | 正常完成 | provable_to_L2_then_unknown（5 事件） | **逐位一致** |

## 传播链证据（5/5 样本同构）

```
L0: inj（fault_id=1, dyn_inst_seq=133, tick=401940）
L1: addr_form（old→new EA，parent=inj）
L2: mem_req + lsq_sendfrag（pc=4091a0, opcode=strqbfpxi_uop, request_id=133）
    + tlb_translate（SE 经 translateSe 漏斗）
L2→L3: **Unknown**——启动 store 的访存侧完成事件（sq_complete/resp）未落流
```

链检查器输出（每样本）：`terminal=provable_to_L2_then_unknown, beyond=Unknown`（**绝不推断 Masked**——规格表 9 判定列钉死）。

## 诚实发现与遗留

1. **启动 store 的 L2→L3 证据缺口**：sq_complete 钩子位于 completeStore（writeback ACK 路径），在 a04 PRE 族样本（h36_sqf）实证落流；但 a01 POST 族 5/5 样本均未出现。可能根因：启动 store 的排放路径差异或注册时序——待正式实验前的专项排查（不阻塞 pilot 判定，链诚实止于 L2+Unknown）。
2. **s3/s5 oracle-clean ≠ Masked**：FINAL 与 golden 逐位一致 + 链止于 L2 → 规格口径=「截至 L2 可证，后续 Unknown」。离线 oracle 干净是 L5 证据面信息，不回填传播链判定（离线分类不替代传播证据——用户指令二.5）。
3. **结局分布（n=5 非正式统计）**：Crash 3 / oracle-clean 2；Crash 全部为 corrupted EA 未映射 → guest page fault。

## 结论

- **链机制验证通过**：PROP-EVT 流（表 11 全字段）L0→L1→L2 逐边 proven（共享 fault_id 键 + tick 时间序双证明）；链检查器正确输出 Unknown（不推断 Masked）。
- **结局分类机制验证通过**：Crash（gem5 exit 134 + panic 签名）与 oracle-clean（FINAL 对照）均可机判。
- **首次 divergence 定位**：dyn_inst_seq=133（启动 store），pc=0x4091a0，tick=401940——所有样本的首个（唯一）注入点。
- **正式 campaign 未启动**：385 activated/RunID 量产需用户另行批准（计划 §6 声明）。
