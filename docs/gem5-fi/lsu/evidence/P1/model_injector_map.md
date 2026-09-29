# P1 证据：V2.0 64 模型 ↔ 既有注入器映射现状（V1.0 资产桥接分析）

生成：2026-09-29 15:35（Session 001，P1）
来源：`tools/lsu_campaign.py` MODEL_FLAGS/MODEL_BLOCKED（git-verified 2026-09-26，V1.0 轨道 W4-W8 交付）
与 `完整任务执行清单.md` 64 模型集合的对照。

## 关键结论

1. **V1.0 68 模型 = V2.0 64 模型 + 4 个删除行**：S12/T09/C13/O08 为 V1.0 标记"不适用(B0无保护)"的行，V2.0 Excel 已删除。二者差异完全闭合，无其他模型集变化。
2. **V2.0 64 模型实现状态（继承 V1.0 git-verified 映射）**：
   - **47 可运行**（MODEL_FLAGS 有注入器命令映射）
   - **17 缺口**，分四类：
     - 消费侧损坏未实现（notify-only 事件源已接，chaosLsuF6Notify 仅调用点）：S10, L04, C11, C12, C14, C15（6）
     - 无干净钩子：A07（R4 ready 握手）, P06（prefetch-as-demand 标记）, O04（RMW 数据路径需 cache 侧 SwapResp 钩子）, O09（RMW 操作数路径）（4）
     - CHAOSArmTLB 模式未实现：T05（valid/global/ASID）, T06（权限合法替换）, T07（命中伪造/way 选择）, T08（walk 配对）（4）
     - 多核语义（需多核 FS）：O05（RMW 顺序）, O06（barrier 完成）, O07（order-tag 交换）（3）
   - 47 + 17 = 64 ✓
3. **~10 个近似映射**（V1.0 时代 approx 决策，V2.0 需复核是否继承或补实现）：
   A03（stuck1 由 seed 奇偶近似）、S03（byte_lane_skew 近似 stuck-lane 族）、S09（concat/assembly 用 skew 近似）、C05（tag 重标注=C04）、C10（PLRU→valid 近似）、P04（drop/dup 近似）、P07（fill way/tag→CHAOSCache tag 近似）、P09（pf dirty evict→dirty 近似）、T10（PPN 低/中/高分段子模型未参数化，用 T01 bit_flip+seed 驱动 bit）、O03（status-flip 语义近似）
4. **注入器家族→挂载点**（全部已实现并在 lsu_proxy.py 暴露）：
   - addrpath 家族（A01-A03 bit 级 + A04-A06/A08/S04-S07/S11/S13/L01/L02 PRE 族 on LSQ::pushRequest 钩子）→ CHAOSAddrPath
   - lsqfwd 家族（S01-S03/S08/S09 + L03 flag）→ CHAOSLSQFwd
   - cache 家族（C01-C10, P07, P09）→ CHAOSCache on l1d-cache-0（legacy firstClock 机制；lsuTier 参数已接线未消费）
   - prefetch 家族（P01-P05, P08）→ CHAOSPrefetch（5 native modes）
   - exmon 家族（O01-O03）→ CHAOSExMon（legacy window 路径）
   - armtlb 家族（T01-T04, T10）→ CHAOSArmTLB（FS-only，configs/fs/lsu_b0_fs.py + tlb_probe.rcS 载体，golden=md5 of 1MiB zeros）
5. **触发层**：chaos_lsu_trigger.hh 事件归一化 F0-F6 已实现（W2 46e912b5）；cache/exmon 家族仍走 legacy 时钟窗机制（tier 未消费）——tier 参数"wire-ready, NOT consumed"，为已知近似。

## P1 待办影响（缺口处置选项）

- 17 缺口模型对应的 ITEM 在补实现前只能 BLOCKED/DEFERRED，不得静默近似（清单执行规则 4）。
- T05-T08（TLB 模式）与 A07/P06/O04/O09（钩子）为 C++ 补实现工作；S10/L04/C11/C12/C14/C15 为消费侧损坏逻辑；O05-O07 依赖多核 FS 平台（W7/W13 载体，与 DR-001 联动）。
- 近似映射 10 项需逐项裁决：V2.0 继承 V1.0 approx（记录在案）或补精确实现——建议并入 DR-002 提请用户。

**ITEM 级量化（2026-09-29 15:37 统计）**：
- 缺口 17 模型 → **85 ITEM（26.2%）**：A07×6（ITEM-028..033）、T05-T08×19、S10/L04/C11/C12/C14/C15（ITEM-109..113、169..204 等）、O04/O05/O06/O07/O09（ITEM-291..316 等）
- 近似 10 模型 → **49 ITEM（15.1%）**
- **精确可运行 191 ITEM（58.8%）**（85+49+191=325 ✓；其中主负载为 W1/W11/W13 的部分另受 DR-001 约束，交集待统计）

## 证据

- `tools/lsu_campaign.py:103-242`（MODEL_FLAGS/MODEL_BLOCKED/FAMILY_*，含 git commit 出处注释）
- `configs/se/lsu_proxy.py:152-420+`（全部注入器参数面）
- `docs/gem5-fi/lsu/evidence/P0/g0_04_g0_05_check.md`（64 模型集合与 B0 参数）
