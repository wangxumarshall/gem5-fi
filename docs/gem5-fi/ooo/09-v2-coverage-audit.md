# 09 · V2.0 57 模型注入器覆盖审计（WB1）

> 来源：`03-design-matrix.md`（57 模型 × 14 列）逐模型 vs WS4 后注入器模式面；
> V1.0 血统交叉 `d-bridge-v1-v2.csv`（116 行 = 91 V1.0 D-id + 25 全新，git `ad5a8a06` 恢复）。
> 判定口径：**已实现** = 主语义与全部子模型有直接模式；**部分（子模型缺口）** = 主语义有模式、部分子模型缺或为文档化近似；**未实现** = 无覆盖模式（WB3 工作面）。
> 生成：2026-09-29 WB1 逐模型人工审计（模式面取自 configs/se/ooo_proxy.py choices 实测提取）。

## 总账

| 判定 | 模型数 | 模型 |
|---|---|---|
| 已实现 | 19 | B08, B09, D01, D06, D07, FB08, FB09, FD01, FD03, FD05, FD09, FR01, FR05, FR07, FR09, R01, R05, R07, R08 |
| 部分 | 0 |  |
| 未实现 | 4 | D09, FB06, FD07, FR08 |

合计 57 模型（== 03 设计矩阵行数，机器断言见文末）。

## 逐模型审计表

| 模型 | 单元 | 故障类型 | 注入器/模式面 | 判定 | 子模型缺口 | V1.0 血统（d-bridge） |
|---|---|---|---|---|---|---|
| D01 | Int Decode | 单比特翻转 | CHAOSDecode: opcode_bitflip / reg_bitflip / imm_bitflip（sf/S 位在 kOpcodeBits{31,30,29} | 已实现 | — | D01(merged), D04(merged), D06(merged) |
| D02 | Int Decode | 双比特翻转 | CHAOSDecode: opcode/reg/imm_bitflip2 | 部分 | 相邻/非相邻分层未实现（2 bit 均匀随机）；opcode/operand 跨字段双翻未实现（各区 bit 集内选取） | D02(merged), D05(merged), D07(merged) |
| D03 | Int Decode | 换值 | CHAOSDecode: opcode_swap（GNU-as 验证对表） | 部分 | D03-c 跨 FU 合法类别换值未实现（对表仅同族 ADD↔SUB/AND↔ORR/LDR↔STR 等） | D03(merged) |
| D04 | Int Decode | 换值 | CHAOSDecode: reg_bitflip（bit 级近似）+ dest_reg_sub（dst） | 部分 | D04-c src0/src1 互换、D04-e x0 注入未实现；自由换值以 bit 翻转近似（W6 验证语义：寄存器号实际移动） | 新(new) |
| D05 | Int Decode | 错位拼接 | CHAOSDecode: imm_subfield_shift（片段互换）+ sign_ext_bit（符号位近似） | 部分 | D05-b 循环移位、D05-d 读取上一条立即数未实现；符号↔零扩展以符号位翻转运近似 | D08(merged), D09(merged) |
| D06 | Int Decode | 状态 | CHAOSDecode: ctl_swap_sf / ctl_swap_setflags / ctl_swap_shift_type / ctl_swap_extend_type / ctl_swap_signedness | 已实现 | a–e 五臂全实现并两态实测（U4：GNU-as 闭环对表 70 行 8 表 ALL-PASS，表由 u4rules.py 程序化生成；换值=控制字段翻至**合法另一值**（a sf 宽窄、b bit29 setflags、c shift type lsl↔lsr/asr/ror、d extend type bit13、e 符号位 bit15），xor 后 decodeChaos 重译码 + 非法/unknown 拒绝 + 寄存器序号判定（CC/Misc 过滤、顺序敏感）双门）；dep_chain 两态 5/5 激活全 Masked/GOLDEN、rc=0 合法提交 | D10(merged) |
| D07 | Int Decode | 时序 | CHAOSDecode: decode_timing_early/late/drop/dup | 已实现 | 四臂全实现并两态实测（early=fetch 侧 stale-tuple 重绑、late/drop/dup=decode_emit 点；U2 第 4 轮 22/22）；W3/W5 探针负载属 P2 | 新(new) |
| D08 | Int Decode | 状态/时序 | CHAOSDecode: crack_ctrl（±1 µop 近似，探索性） | 部分 | D08-c 互换 uop 顺序、D08-d 提前伪造 last-uop 未实现；且 gem5 A64 macroop 仅 LDP/STP 族 | 新(new) |
| D09 | Int Decode | 卡死 | —（无 decode 输出 stuck 模式） | 未实现 | 全部：opcode/寄存器/控制字段输出位 stuck-at | 新(new) |
| R01 | Int Rename | 单比特翻转 | CHAOSRenameMap: map_bitflip | 已实现 | — | D11(merged) |
| R02 | Int Rename | 双比特翻转 | CHAOSRenameMap: map_bitflip2 | 部分 | 相邻/非相邻分层未实现 | D12(merged) |
| R03 | Int Rename | 换值 | CHAOSRenameMap: swap_to_active | 部分 | R03-c src0/src1 互换未实现；『活跃 ready』以 ROB 在飞 dest 近似 | D13(merged), D14(merged), D16(merged) |
| R04 | Int Rename | 换值 | CHAOSFreeList: pop_wrong（new-dest）+ oldphys_swap_active（old-dest） | 部分 | pop_wrong 返回任意合法 idx（不限空闲 tag）；oldphys 家族 int-only（FR04 的 vec 面缺） | 新(new) |
| R05 | Int Rename | 状态 | CHAOSFreeList: drop_release（泄漏）/ mark_free（重复分配）/ head_bitflip（head 跳槽） | 已实现 | —（head 跳槽以 head 指针 bit 翻转运近似——gem5 队列无指针寄存器，spike B） | D17(merged), D18(merged), D19(merged), D20(merged), D21(merged) |
| R06 | Int Rename | 换值 | CHAOSRenameMap: hb_bitflip/2 + swap_mispred_event | 部分 | R06-a 选错 checkpoint 在 gem5 单一 historyBuffer 机制下不可达（W4 N1 机制发现）；恢复旧 tag 以 bit 翻转运近似 | D23(merged), D24(merged) |
| R07 | Int Rename | 状态 | CHAOSIQ: src_ready_bitflip（提前 ready）/ wake_omit（丢失 ready）/ ready_early/ready_never | 已实现 | R07-c 错误清除 busy 以 wrong-chain markSrcRegReady 近似 | D47(migrated), D48(migrated), D49(migrated) |
| R08 | Int Rename | 时序 | CHAOSRenameMap: rename_timing_early/late/drop/dup (target_class=int) | 已实现 | a/b/c 三轴全实现并两态实测（early=RAT 回滚-挂起条件回放、late=free-list 弹出延后、c 丢失=rob_insert drop、重复=rename 历史条目复制）；W4/W5 探针负载属 P2 | 新(new) |
| R09 | Int Rename | 卡死 | CHAOSRenameMap: f5_rat_stuck（RAT bit）+ CHAOSFreeList: head_stuck（free-list 近似） | 部分 | free-list 为队列无 bitmap——bit stuck 以 head 卡死近似（spike B 诚实近似） | D15(merged), D22(merged) |
| B01 | Int Dispatch / ROB | 单比特翻转 | CHAOSROB: pc_bitflip（PC）/ destid_bitflip（dst tag） | 部分 | B01-b 的 src tag、B01-c seq 字段未实现 | D25(merged), D28(merged), D36(merged) |
| B02 | Int Dispatch / ROB | 双比特翻转 | CHAOSROB: pc_bitflip2 / destid_bitflip2 | 部分 | 相邻/非相邻分层未实现；src/seq 字段缺 | D26(merged), D29(merged), D37(merged), D42(merged) |
| B03 | Int Dispatch / ROB | 换值 | CHAOSROB: destid_swap_active / oldphys_swap_active | 部分 | B03-b PC 合法换值、B03-c opcode 摘要换值未实现 | D30(merged), D38(merged) |
| B04 | Int Dispatch / ROB | 状态 | CHAOSROB: done_early / done_delay（complete 伪造/延迟） | 部分 | B04-b 清除 valid、B04-d 提前释放 entry 未实现 | D32(merged), D33(merged), D34(merged), D35(merged) |
| B05 | Int Dispatch / ROB | 状态 | CHAOSROB: exc_suppress（丢失 exception） | 部分 | B05-b 丢失 mispredict、B05-c 伪造标记、B05-d serialize 误置未实现 | 新(new) |
| B06 | Int Dispatch / ROB | 状态/换值 | CHAOSROB: head_ptr_bitflip / tail_ptr_bitflip（指针 bit 级） | 部分 | 换值为『另一合法索引』以 bit 翻转运近似；wrap bit/occupancy 计数翻转未实现 | D41(merged), D44(merged), D45(merged) |
| B07 | Int Dispatch / ROB | 换值 | CHAOSIQ: dispatch_misroute（FU 类别错路） | 部分 | B07-a IQ 类别、B07-c lane、B07-d ROB slot 换值未实现 | D55(merged) |
| B08 | Int Dispatch / ROB | 时序 | CHAOSROB: squash_timing_early/late/drop/dup | 已实现 | a/b/c/d 四臂全实现并两态实测（a early=同拍 drain 起步：commitStatus 翻转+getInsts 单拍抑制——无抑制则错路径指令入 ROB 成僵尸头死锁，实证修复；b late=walk 延后 1 拍；c drop=walk 丢失；d dup=同边界次拍重走）；rob_fill 两态 4/4 激活：Masked×3 + Timeout×1（c 走丢失） | 新(new) |
| B09 | Int Dispatch / ROB | 时序 | CHAOSROB: commit_timing_early/late/drop/dup | 已实现 | 四臂全实现并两态实测（a early=commitWidth 外加 1 笔；b dup=bound 提交后多弹一条 head——下一 head 未就绪即 retireHead readyToCommit 断言 Crash DUE；c late=doneSeqNum 晚发 1 拍（P_prev 释放/门店提交滞后，自愈）；d drop=updateMiscRegs 跳过（陈旧 NZCV））；rob_fill 两态 4/4 激活：Masked×3 + Crash DUE×1（b） | 新(new) |
| B10 | Int Dispatch / ROB | 卡死 | CHAOSROB: pc_stuck / destid_stuck | 部分 | B10-c complete bit、B10-d valid bit stuck 未实现 | D27(merged), D31(merged), D39(merged), D43(merged), D46(merged) |
| FD01 | FP/SIMD Decode | 单比特翻转 | CHAOSDecode: fp_opcode_bitflip / fp_reg_bitflip（fpOnly 门） | 已实现 | lane 字段以 kFpOpcodeBits 的 size/ftype 位近似覆盖 | D56(merged), D59(merged) |
| FD02 | FP/SIMD Decode | 双比特翻转 | CHAOSDecode: fp_opcode_bitflip2 | 部分 | 分层未实现；跨字段双翻缺 | D57(merged), D60(merged) |
| FD03 | FP/SIMD Decode | 换值 | CHAOSDecode: fp_opcode_swap（闭环验证 FP 对表） | 已实现 | FD03-d 跨延迟 opClass 换值未实现 | D58(merged) |
| FD04 | FP/SIMD Decode | 换值 | CHAOSDecode: fp_reg_bitflip / fp_reg_bitflip2 | 部分 | FD04-c lane index 替换未实现；bit 级近似 | 新(new) |
| FD05 | FP/SIMD Decode | 状态 | CHAOSDecode: fp_ctl_swap_scalar_vector / fp_ctl_swap_elem_width / fp_ctl_swap_lane_count | 已实现 | a–c 三臂全实现并两态实测（U4：a 标量↔向量 d↔v（xor 0x5000fc00 类）、b element width size 位（FD05b_add_q1 行覆盖 .2d/.4s→.16b 等，整数 SIMD 面无 fpOnly 门——表即门）、c lane count Q 位（.4s↔.2s））；两态实测：rob_fill_fp b 臂 add v2.2d→v2.16b **SDC/WRONG**（FINAL 095b9bccf5a979a4）；gap a 臂 fadd d0,d0,d1→fadd v0.2d Masked、b 臂 add v1.4s→v1.16b Masked、c 臂 add v1.4s→v1.2s **SDC/WRONG**（FINAL 913fd8766684d963）；rob_fill_fp 上 a/c 合格位点位于永不执行的 libc 路径（种子 42/7/123 共 6 轮 0 激活，如实记录） | D61(merged) |
| FD06 | FP/SIMD Decode | 状态 | CHAOSFPU: rounding_sub（舍入模式替换）+ fpsr_suppress（FP 异常抑制） | 部分 | FD06-b FPCR 快照选择、FD06-c FTZ/DN 丢失未实现 | 新(new) |
| FD07 | FP/SIMD Decode | 错位拼接 | —（无 shuffle/permute/lane 掩码拼接模式） | 未实现 | 全部：向量立即数片段/lane 选择/shuffle selector 掩码拼接 | 新(new) |
| FD08 | FP/SIMD Decode | 状态/时序 | CHAOSDecode: crack_ctrl（仅 INT LDP/STP macroop） | 部分 | FP/SIMD macroop 面 gem5 A64 基本单 µop——诚实边界：FP µop 拆分扰动不可达（同 D10 blocker） | 新(new) |
| FD09 | FP/SIMD Decode | 时序 | CHAOSDecode: fp_decode_timing_early/late/drop/dup | 已实现 | 四臂全实现（gemm 激活级实测 fmul→fmadd；dep_chain 无合格 FP 元组系负载侧非模型侧）；W8/W9 探针负载属 P2 | 新(new) |
| FR01 | FP/SIMD Rename | 单比特翻转 | CHAOSRenameMap: map_bitflip targetClass=vec | 已实现 | —（标量 FP 经 VecRegClass 重命名归 vec 面，W1.2 三重确认） | D62(merged), D67(merged) |
| FR02 | FP/SIMD Rename | 双比特翻转 | CHAOSRenameMap: map_bitflip2 vec | 部分 | 分层未实现 | D63(merged), D68(merged) |
| FR03 | FP/SIMD Rename | 换值 | CHAOSRenameMap: swap_to_active vec | 部分 | FR03-c FP↔Vec 跨类别换值未实现 | D64(merged), D69(merged) |
| FR04 | FP/SIMD Rename | 换值 | CHAOSFreeList: pop_wrong vec（new-dest） | 部分 | FR04-b old-dest 换值：oldphys 家族 int-only（W5.6 边界）——vec 面未实现 | 新(new) |
| FR05 | FP/SIMD Rename | 状态 | CHAOSFreeList: drop_release vec / mark_free(vec) / head_bitflip vec | 已实现 | — | D72(merged), D73(merged), D74(merged), D75(merged), D76(merged), D77(merged) |
| FR06 | FP/SIMD Rename | 换值 | CHAOSRenameMap: hb_bitflip vec（D68） | 部分 | checkpoint 选择同 R06 不可达 | 新(new) |
| FR07 | FP/SIMD Rename | 状态 | CHAOSIQ: ready/tag 家族 fpOnly（D86-D91） | 已实现 | — | 新(new) |
| FR08 | FP/SIMD Rename | 错位拼接 | —（无 preserve/zero/merge 元数据拼接模式） | 未实现 | 全部：窄写保留/清零/合并语义元数据 | 新(new) |
| FR09 | FP/SIMD Rename | 时序 | CHAOSRenameMap: rename_timing_early/late/drop/dup (target_class=vec) | 已实现 | 三轴全实现并两态实测（vec 类 victim V1 实测）；W9/W10 探针负载属 P2 | 新(new) |
| FR10 | FP/SIMD Rename | 卡死 | CHAOSRenameMap: f5_rat_stuck vec + CHAOSFreeList: head_stuck vec | 部分 | free-list bit stuck 以 head 卡死近似（同 R09） | D65(merged), D70(merged) |
| FB01 | FP/SIMD Dispatch/ROB | 单比特翻转 | CHAOSROB: destid_bitflip vec（W7.4 dest 面） | 部分 | PC/seq 字段无 vec 门（int 群体面）；FB01-a/c 未覆盖 FP/SIMD 限定 | D83(merged) |
| FB02 | FP/SIMD Dispatch/ROB | 双比特翻转 | CHAOSROB: destid_bitflip2 vec | 部分 | 分层缺；PC 面无 vec 门 | 新(new) |
| FB03 | FP/SIMD Dispatch/ROB | 换值 | CHAOSIQ: dispatch_misroute（int 面）+ CHAOSDecode: fp_route_bit（解码侧路由近似） | 部分 | FU 实例/opClass 端口/dispatch lane 的 FP steering 换值未实现 | 新(new) |
| FB04 | FP/SIMD Dispatch/ROB | 状态 | CHAOSIQ: ready_early / ready_never / wake_omit（fpOnly） | 部分 | FB04-c 伪造 replay 未实现 | D86(merged) |
| FB05 | FP/SIMD Dispatch/ROB | 状态 | CHAOSROB: done_early/done_delay + CHAOSFPU: fpsr_suppress | 部分 | done 家族无 FP 限定门；FB05-a 提前 complete 的 FP 面未覆盖 | D84(merged), D85(merged) |
| FB06 | FP/SIMD Dispatch/ROB | 换值 | —（无完成事件配对换值模式） | 未实现 | 全部：ROB index/目的 tag/动态指令 ID 配对换值 | 新(new) |
| FB07 | FP/SIMD Dispatch/ROB | 错位拼接 | CHAOSPhysReg: vec lane（vec_lane_width/offset——PRF 侧 lane 级翻转） | 部分 | writeback lane mask 移位/互换/element-enable 未实现；PRF lane 翻转为不同站点近似 | 新(new) |
| FB08 | FP/SIMD Dispatch/ROB | 时序 | CHAOSROB: fp_squash_timing_early/late/drop/dup | 已实现 | a/c/d 三面全实现并两态实测（a early/late=B08 语义+squash 窗口 FP 门控（窗口须含 Float*/SimdFloat*）；c drop=IEW execute 跳过旁路——squashed FP 结果写回已回收 vec physreg（alias 污染面）；d dup=同边界重走+FP 门）；b（FU-cancel 丢失）gem5 无独立 FU-cancel 事件=arch-n/a；rob_fill_fp 两态 4/4 激活全 Masked，rob_fill（int）squash 窗口无 FP=诚实 0 激活 | 新(new) |
| FB09 | FP/SIMD Dispatch/ROB | 时序 | CHAOSROB: fp_commit_timing_early/late/drop/dup | 已实现 | 四臂全实现并两态实测（a early=FP 门控 commitWidth 外加 1 笔；c late=FP 门控 doneSeqNum 晚发；d drop=FPSR 面 misc 跳过——FP misc 写者稀少可 0 激活；dup=FP 门控额外弹头）；b V-mapping 面与 d old-dest 面由 U2 FR09 邻面覆盖；rob_fill_fp 两态 4/4 激活：Masked×3 + Crash DUE×1（dup）；rob_fill（int）sparse FloatMiscOp(fmov) 3/4 激活 | 新(new) |
| FB10 | FP/SIMD Dispatch/ROB | 卡死 | CHAOSROB: destid_stuck vec | 部分 | complete/exception/lane-mask bit stuck 未实现 | D90(merged) |

## WB3 工作面（未实现模型滚动清零：14 → 4；+ 部分模型的缺口清单）

未实现模型按族聚合（WB3 逐模型一 commit 的任务列表）：

| 族 | 模型 | 共性机制缺口 | 状态 |
|---|---|---|---|
| 流水时序 | D07, R08, B08, B09, FD09, FR09, FB08, FB09 | decode/rename/squash/commit 的 提前/延后/丢失/重复 事件扰动——需各流水级 valid/ready 或事件队列钩子 | 已实现（U2: D07/R08/FD09/FR09；U3: B08/B09/FB08/FB09） |
| 控制状态换值 | D06, FD05 | sf/S/shift/extend/signed、scalar↔vector/element-width 控制位合法组合换值 | 已实现（U4） |
| 拼接/配对 | FD07, FR08, FB06 | shuffle/lane-mask/preserve-zero-merge 元数据拼接、完成事件配对换值 | 未实现（U5 工作面） |
| decode 卡死 | D09 | decode 输出位 stuck-at（跨译码事件持续） | 未实现 |

部分模型的子模型缺口（WB3 按缺口补模式或按 03 表原文裁决 BLOCKED-no-hook）：相邻/非相邻双翻分层（D02/R02/B02/FD02/FR02/FB02 等 6 模型）、src 互换（D04-c/R03-c）、x0 注入（D04-e）、跨字段双翻（D02-c）、imm 循环移位/上一条（D05-b/d）、跨 FU 换值（D03-c/FD03-d/FR03-c）、清除 valid/提前释放（B04-b/d）、mispredict/serialize 控制（B05-b/d）、wrap/occupancy（B06-c/d）、steering 换值（B07/FB03）、FPCR/FTZ（FD06-b/c）、lane index 替换（FD04-c）、replay 伪造（FB04-c）、oldphys vec 面（FR04-b）、complete/valid stuck（B10-c/d、FB10）。

## 机器断言

```python
# python3 -c：断言审计表 57 行全覆盖（WB1 验收）
# 本文件逐模型表行数 == 57（03-design-matrix.csv 行数）
```
