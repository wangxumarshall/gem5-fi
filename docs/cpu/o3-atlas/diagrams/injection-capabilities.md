# 微架构单元 × 故障注入能力

> 故障模式全集实时解析自 `configs/se/ooo_proxy.py`（与实验工具面同源：工具增删模式，此表与总图徽标自动跟随）。

| 微架构单元 | 注入器 | 模式数 | 故障模式全集 / 能力 | 破坏目标 | 挂载锚点 |
|---|---|---|---|---|---|
| BPU（BPU 分支预测器（BTB·RAS·方向/目标）） | **CHAOSBPU** | 2 | dir_flip, target_flip | 分支预测方向/目标翻转 + RAS 返回地址 | CHAOS/gem5/src/cpu/o3/bac.cc:565 |
| FTQ（FTQ 取指目标队列） | — | 0 | 无注入挂载 | — | CHAOS/gem5/src/cpu/o3/ftq.cc:186 |
| ICACHE（ICache 取指） | — | 0 | 无注入挂载 | — | CHAOS/gem5/src/cpu/o3/fetch.cc:1059 |
| DECODER（Decoder（编码→StaticInst）） | **CHAOSDecode** | 26 | dest_reg_sub, opcode_bitflip, opcode_bitflip2, opcode_swap, reg_bitflip, reg_bitflip2, imm_bitflip, imm_bitflip2, sign_ext_bit, imm_subfield_shift, crack_ctrl, fp_opcode_bitflip, fp_opcode_bitflip2, fp_opcode_swap, fp_reg_bitflip, fp_reg_bitflip2, fp_route_bit, bitflip2_adj, bitflip2_nonadj, bitflip2_cross, fp_bitflip2_adj, fp_bitflip2_nonadj, fp_bitflip2_cross, src_swap, x0_sub, imm_rotate | StaticInst 编码/寄存器号/立即数（解码输出 + rename 目的寄存器替换） | CHAOS/gem5/src/cpu/o3/fetch.cc:1257 |
| RAT（RAT 重命名映射表） | **CHAOSRenameMap** | 14 | map_bitflip, map_bitflip2, map_bitflip2_adj, map_bitflip2_nonadj, swap_to_active, f5_substitute, f4_field_stuck, spec_leak, f5_rat_stuck, stale_read, swap_mispred_event, hb_bitflip, hb_bitflip2, src_tag_swap | RAT 表项（逻辑→物理映射、历史位、源标签） | CHAOS/gem5/src/cpu/o3/rename_map.hh:266 |
| FREELIST（FreeList 空闲物理寄存器表） | **CHAOSFreeList** | 7 | mark_free, pop_wrong, mark_free_event, drop_release, head_bitflip, head_bitflip2, head_stuck | 空闲物理寄存器表（弹出/标记空闲/释放丢弃/栈头位） | CHAOS/gem5/src/cpu/o3/free_list.hh:115 |
| IQ（IQ 发射队列（源标签 CAM·就绪位·唤醒）） | **CHAOSIQ** | 12 | wake_omit, src_ready_bitflip, wake_phase, ready_early, ready_never, ready_never_event, tag_swap, tag_bitflip, tag_bitflip2, tag_stuck, tag_stale_read, dispatch_misroute | IQ 表项源标签 CAM/就绪位/唤醒/派发路由 | CHAOS/gem5/src/cpu/o3/inst_queue.cc:694 |
| LSQ（LSQ（LQ/SQ·store→load 前送·独占监视）） | **CHAOSLSQFwd** | 6 | byte_flip, byte_lane_skew, stale_line_replay, all_zero, fwd_source_sub, phase_offset | store→load 前送数据通路（字节/车道/陈旧行/源替换/相位） | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:338 |
| LSQ（LSQ（LQ/SQ·store→load 前送·独占监视）） | **CHAOSExMon** | 2 | stxr_force_success, stxr_force_fail | 独占监视器（STXR 强制成败/监视器状态） | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:338 |
| FU（FU 池） | **CHAOSExec** | — | 整数结果 XOR 位翻转（exec_fault_mask 参数化） | 整数执行结果（IntAlu/IntMult/IntDiv 结果 XOR） | CHAOS/gem5/src/cpu/o3/dyn_inst.cc:367 |
| FU（FU 池） | **CHAOSFPU** | 6 | , , , , , , , , , , ,| 浮点结果分段（sign/exp/mantissa + FMA 加权/舍入/FPSR） | CHAOS/gem5/src/cpu/o3/dyn_inst.cc:367 |
| TLBPATH（地址通路（翻译前 vaddr·TLB）） | **CHAOSAddrPath** | 2 | byte7_zero, low_bit_flip | 翻译前虚地址（byte7 清零/低位翻转） | CHAOS/gem5/src/cpu/o3/lsq.cc:1176 |
| L1D（L1D 返回通路（ECC 后包数据）） | **CHAOSL1DForward** | — | L1D 返回包数据位翻转（fault_mask 参数化） | L1D 返回包数据（ECC 检查后注入） | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:200 |
| L1D（L1D 返回通路（ECC 后包数据）） | **CHAOSCache** | — | cache 行数据注入（arm_chaos_cache 配置族） | cache 行数据（L1D/L1I/L2） | CHAOS/gem5/src/cpu/o3/lsq_unit.cc:200 |
| DRAM（内存子系统（DRAM 保护模型）） | **CHAOSMem** | — | 参数化注入 | DRAM 侧（保护模型 + 概率位翻转/stuck） | CHAOS/gem5/src/mem/CHAOSMem/CHAOSMem.cc |
| PRF（PRF 物理寄存器堆） | **CHAOSPhysReg** | 3 | phys, arch_frontend, arch_commit | PRF 槽位值（bitflip/stuck，phys/arch_frontend/arch_commit 定位） | CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc:201 |
| ROB（ROB 重排序缓冲（pc·dest·done·exc·指针）） | **CHAOSROB** | 28 | entry_bitflip, exc_suppress, pc_bitflip, pc_bitflip2, pc_stuck, pc_bitflip2_adj, pc_bitflip2_nonadj, destid_bitflip, destid_bitflip2, destid_bitflip2_adj, destid_bitflip2_nonadj, destid_swap_active, destid_stuck, done_early, done_early_event, done_delay,done_delay_event, rob_stale_read, oldphys_bitflip, oldphys_bitflip2, oldphys_swap_active, oldphys_stuck, head_ptr_bitflip, head_ptr_bitflip2, head_ptr_stuck, tail_ptr_bitflip, tail_ptr_bitflip2, tail_ptr_stuck | ROB 表项字段（pc/dest/done/exc/oldphys/头尾指针）+ done 位时序 | CHAOS/gem5/src/cpu/o3/rob.cc:236 |
| ROB（ROB 重排序缓冲（pc·dest·done·exc·指针）） | **CHAOSRAS** | — | 提交期 head fault 清除（异常抑制） | 提交期异常抑制（清除 head 挂起 fault） | CHAOS/gem5/src/cpu/o3/rob.cc:236 |
| ARCHRF（架构寄存器堆（提交态）） | **CHAOSReg** | 4 | bit_flip, stuck_at_zero, stuck_at_one, random | 提交态架构寄存器（GPR/FPR，bitflip/stuck-at/random + 永久化） | CHAOS/gem5/src/CHAOSReg/CHAOSReg.cc:287 |
| OBS（观测器（占基采样·commit 轨迹，只读）） | **CHAOSProbe** | — | 参数化注入 | 观测器：ROB/IQ/FreeList 占基采样（只读） | CHAOS/gem5/src/cpu/o3/commit.cc:1299 |
| OBS（观测器（占基采样·commit 轨迹，只读）） | **CHAOSCommitTrace** | — | 参数化注入 | 观测器：commit 轨迹与 squash 记录（只读） | CHAOS/gem5/src/cpu/o3/commit.cc:1299 |
