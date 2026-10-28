#!/usr/bin/env python3
"""lsu_prop_fields.py — [MDSPEC][H0] 表 11 统一 PROP-EVT 事件流解析器。

规格：主文档 11.传播事件字段规范（24 字段）+ 计划 Task H0。
- 发射端 CHAOSPropagation.cc emitPropEvt 与本模块共用同一字段注册表
  （同名同序）；tests/test_lsu_prop_fields.py 钉死双源一致。
- 行格式（发射端保证，解析端容错）：
    PROP-EVT: kind=<v> run_id=<v> ... evidence_status=<v>
  全部注册字段按规范序出现；缺失值留空（k=），键不省略。
- 解析端：行内缺键 → 填 ""；evidence_status 缺省 observed（规格 11 末行：
  防止把缺失事件解释为未传播）；非 PROP-EVT 行返回 None。
- .gz 截断容错：Z_SYNC_FLUSH 前缀可救（v1 lsu_l3_propagation 先例），
  截断必须置 truncated=True（诚实标记）。

Unknown 语义（Review Focus #3）：provable_to 只按在场事件的最大可证层级
判定；更高层一律 beyond=Unknown——绝不推断 Masked。
"""
import gzip
import zlib
from pathlib import Path

# 与 CHAOSPropagation.hh 的 PROP_EVT_FIELDS[] 同名同序。
# kind 为事件语义首字段（规格表 11 未列——计划 H0 裁决：v1 已有 kind 概念，
# 无 kind 则事件不可分型；24 规格字段全部在列）。
# [MDSPEC][R4-1] 追加 store_dyn_inst_seq（lsq_fwd 生产 store 的 seq，与
# dyn_inst_seq=消费 load 的 seq 成对）与 corr（关联来源标注：
# seq_primary | addr_fallback——仅地址关联必须显式标注，不得静默）。
# [MDSPEC][R4-4-review-I1] corr 词汇表扩至 5 值并覆盖**全部**入链事件
# （含 writeNode 双发的 inj/addr_form/mem_req/resp/taint_reg/consumer/
# errant_commit 与 chain_end）：join 未发生时必须显式说明，不得留空——
# 空 corr 与"未标注的地址域 join"不可区分（R4-4 评审 Important-1）。
PROP_EVT_FIELDS = [
    "kind", "run_id", "sample_run_id", "fault_id", "event_id",
    "parent_event_id", "tick", "cycle", "core_id", "thread_id",
    "dyn_inst_seq", "store_dyn_inst_seq", "commit_seq", "pc", "opcode",
    "lq_idx", "sq_idx", "request_id", "walk_id", "mshr_id", "fill_id",
    "pf_request_id", "va", "pa", "cache_line", "set", "way",
    "entry_index", "field", "before", "after", "state_before",
    "state_after", "arch_reg", "phys_reg", "detection_layer",
    "contained", "outcome", "oracle_diff", "evidence_status", "corr",
]

# [MDSPEC][R4-4-review-I1] corr 取值域（发射端 CHAOSPropagation.hh 的
# CORR_* 常量同源；tests/test_lsu_prop_fields.py §6 钉死）：
CORR_VALUES = {
    "seq_primary",    # 经 seq 主臂入链（correlate* 命中 seq 绑定条目）
    "addr_fallback",  # 经地址 fallback 臂入链（blk 注册表重叠，无 seq 约束）
    "origin",         # 链开启注册事件（inj/addr_form）——无 join 发生
    "taint_prop",     # 经污染集成员关系入链（consumer/errant_commit）——
                      # 本事件无 correlate 查询，成员资格由建立污染的
                      # taint_reg 传播（其 corr 记录准入臂）
    "none",           # 链生命周期标记（chain_end 退出回调）——无关联语义
}
# 空 corr 仅允许在已裁决的诚实缺席场景：tlb_pfn 无关联面（req_seq=0 且
# PA 页未变，链诚实止于本事件）与 pf_fill/pf_demand 的 fault_id=0（仅
# 预取请求链、无故障链关联）。

_PREFIX = "PROP-EVT:"

# [R6-STREAM] 权威事件上限：超过即 OVER_CAP（响亮），绝不静默截断后继续
# 认证。与 lsu_r6_status_table.py 的既有语义一致。
# read_stream/read_events 至多保留 EVENT_CAP 条事件；超限时置 truncated=True
# 且**继续流式计数**（不保留超额事件、不把整条流读入内存），保证峰值内存
# 与流大小无关——见 tests/test_lsu_prop_stream_cap.py。
EVENT_CAP = 200000

# kind → 观测层级（v1 kinds 先行；H1-H7 钩子族经 register_kind_layer 注册
# 自己的映射——发射端 kind 命名与层级语义由各族任务定义）。
KIND_LAYER = {
    "inj": "L0", "addr_form": "L1", "mem_req": "L2", "resp": "L3",
    "taint_reg": "L4", "consumer": "L4", "errant_commit": "L4",
    # [R6-A2/TERMINAL] real store lifecycle containment: the store's response
    # was observed but its own commit never was (store_taint survives exit).
    # Not a lifecycle marker; it carries dl/outcome/corr and can close a chain
    # at L4 without erasing any deeper witness.
    "store_not_retired": "L4",
    # [R6-A2/TERMINAL] real architectural exception (SE page-table fault
    # delivered as guest SEGV). It is a terminal at the TLB/MMU layer, not a
    # lifecycle marker; contained only when actually delivered.
    "arch_translation_fault": "L2",
    # [R6-A2/TERMINAL] real LSQUnit::squash discard of the fault-carrying
    # instruction (load or store), observed at the pop point.
    "squash_discarded": "L4",
    # [R6-A2/A07-c] bounded ready-loss outcomes (real watchdog / real squash).
    "ready_loss_watchdog": "L4", "ready_loss_squashed": "L4",
    # [MDSPEC][H1] lsq.cc 统一事件（表 9：L1=EA/size/flags 进入 LSQRequest；
    # L2=请求离开 LSQ 去翻译/访存）
    "lsq_push": "L1", "lsq_sendfrag": "L2",
    # [MDSPEC][H2] TLB 翻译统一事件（mmu.cc translateTiming = SE+FS 漏斗；
    # SE 不经 TLB::lookup——tlb.cc:173 实证）。
    "tlb_translate": "L2",
    # [MDSPEC][R6] T-series family-specific path.  tlb_lookup is the
    # post-injection lookup/selection observation required by table 9 L1;
    # tlb_translate_result is the corresponding PA/fault materialisation at
    # L2.  The global mapping remains useful to the schema validator, while
    # lsu_chain_check applies stricter family-specific mappings so later
    # cache_access events can never impersonate a TLB lookup.
    "tlb_lookup": "L1", "tlb_translate_result": "L2",
    # [MDSPEC][R4-5.9] T08 walk/fill 配对（FS-only）：tlb_walk = DTLB miss
    # 启动的页表遍历（TableWalker::walk 发出，table_walker.cc）；tlb_refill
    # = 该 walk 的 refill 完成（walker 把 PTE 交回 MMU）。两节点共享同一
    # walk_id + 同一 fault_id ⇒ 配对由构造可证（不同 tick，pairing 键
    # walk_id）。T08-a（丢失）落地：refill 未到达 → tlb_refill 以
    # field=lost/outcome=lost 显式记录（诚实标注"未到达"，非伪造一次 refill）。
    "tlb_walk": "L2", "tlb_refill": "L2",
    # [MDSPEC][H2-fix] 翻译 fault 检测事件（A01 POST 根因：corrupted vaddr
    # 落到未映射地址 → 翻译 fault = Hardware 检测 + contained）
    "tlb_fault": "L2",
    # [MDSPEC][H2-FS] TLB-entry pfn 故障：old/new PFN 与 old/new PA
    "tlb_pfn": "L2",
    # [MDSPEC][R4-10-T05/T06/T07] TLB 表项 STATE / 访问属性 / CAM 选择故障：
    # 被改字段不是 pfn（valid/global/asid/ap/mtype/page-size 或 CAM 选择结果），
    # PA 通常不变，故独立于 tlb_pfn。载荷 = field + state_before/state_after
    # （字段文本 before/after；CAM 臂为选择结果 miss→hit / 命中数 / way 选择）。
    # corr 与 tlb_pfn 同约定：空值合法（无关联面——req_seq=0，链诚实止于本事件）。
    "tlb_state": "L2",
    # [MDSPEC][H7] LQ 逐事件（表 9：lq_idx 生命周期；read/completion 属
    # L3 访存发射与返回；insert 在 dispatch 期早于注入注册、结构性缺席）
    "lq_read": "L3", "lq_complete": "L3",
    # [MDSPEC][H3] SQ 生命周期（execute/writeback/complete；drain 属 L3 访存侧）
    "sq_execute": "L3", "sq_writeback": "L3", "sq_complete": "L3",
    # [MDSPEC][H3-FWD] S 系转发故障（生产 store→消费 load 的转发数据被污染）
    "lsq_fwd": "L3",
    # [MDSPEC][R4-5.7] S10 StoreSet SSIT 腐蚀链（换值子模型 S10-a）：
    # ssit_consult（L1）= checkInst 咨询被腐蚀 load PC 的 SSIT 条目——
    # 预测依赖的读取点（dispatch 期，先于执行）；ssit_violation（L2）=
    # 该 PC 上的 memory-ordering violation 检出（漏预测的具体化——
    # 表9 S10 行 L2 档字面点名 "violation/replay"）。
    "ssit_consult": "L1", "ssit_violation": "L2",
    # [MDSPEC][H4] cache 结构事件（L1=lookup / L2=hit返回·miss+MSHR+fill+evict
    # / L3=writeback 持久化）
    "cache_access": "L1", "cache_return": "L2", "cache_fill": "L2",
    "cache_evict": "L2", "mshr_alloc": "L2", "mshr_merge": "L2",
    "mshr_fill": "L2", "mshr_free": "L2",
    # [MDSPEC][R4-5.5] C14-a MSHR busy/occupied stuck-at-1: the serviced
    # entry that was NOT released (resource leak; 表9 C14 行 L1 档点名
    # "MSHR 占用与 free list").
    "mshr_busy": "L2",
    # [MDSPEC][R4-5.6] C15-b MSHR capacity-arbitration fake-free: the new
    # miss allocation the faulty arbitration genuinely allowed beyond
    # capacity (表9 C15 行 L1 档点名 "MSHR 占用/free-list 守恒").
    "mshr_arb": "L2",
    "cache_writeback": "L3",
    # [MDSPEC][H5] prefetch 链（训练 L1 → 队列/发射 L2 → fill L3 → demand L4）
    "pf_train": "L1", "pf_queue": "L2", "pf_issue": "L2",
    "pf_fill": "L3", "pf_demand": "L4",
    # [MDSPEC][H6] atomic 事件链
    "atomic_op": "L2",
    # [MDSPEC][R4-9-FSMC] O04/O05/O09 LSE 原子读改写（SwapReq 提交点，
    # BaseCache::satisfyRequest——同点已有 F6 CasSuccess 计数钩子）：
    #   rmw_data   = O04 数据选择 MUX 错选（old/new 交换，返回锁存器；
    #                L1 值面瞬态）
    #   rmw_result = O09 result/old-value 锁存器 1 bit 翻转（L1）
    #   rmw_order  = O05 RMW 完成握手损坏（丢失/重复一次，数据载荷正确；
    #                L2 完成时序面）
    "rmw_data": "L1", "rmw_result": "L1", "rmw_order": "L2",
    # [MDSPEC][R4-9-FSMC] O06/O07 屏障完成/顺序标签（MemDepUnit 屏障 SN 记账，
    # cpu/o3/chaos_barrier_hook.hh）：
    #   barrier_done = 屏障完成状态被提前/永久卡死（L2：屏障完成点 = 释放点）
    #   order_tag    = 交换两个在飞事务的 order tag（= 释放另一个活 SN；L2）
    "barrier_done": "L2", "order_tag": "L2",
    # [MDSPEC][H6] exmon（独占监视器）链：LDXR 置（损坏的）monitor(L1) →
    # 保留比较决定 match/mismatch(L2) → STXR 状态消费/重试(L3)
    "exmon_monitor": "L1", "exmon_rmw": "L2", "exmon_stxr": "L3",
    # [MDSPEC][R6-T11B] R6/A10 contain-by-squash 显式检测事件（发射端
    # CHAOSPropagation.cc notePropEvt("squash_masked", … detection_layer=L4
    # contained=1 outcome=masked containment_reason=squash_replay)——squash/
    # replay 把收到错误响应的 load 结果丢弃重放，containment 由机制显式
    # 记录，链不再"凭空消失"）。观测层 L4 与发射端声明一致；此前未注册 ⇒
    # validate_event 报 unknown kind，且 chain checker 的三条收口路径
    # （detected_contained / squash_replay_masked / containment_from_events）
    # 对该 kind 全部死路。不设 REQUIRED_FIELDS：本登记是**工具侧缺口修复**
    # （发射端早已存在），不是新钩子契约。
    "squash_masked": "L4",
    # [MDSPEC][L5] 链终局（退出回调发射；outcome=detection_layer/contained）
    "chain_end": "L5",
}
_LAYER_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5"]

# 家族必录字段契约（kind → 必须非空的注册表字段；表 9 必监控列）。
# 发射端（C++ 钩子）与本校验共用此表——契约测试 tests/test_lsu_hook_*.py
# 逐族钉死。
# [MDSPEC][R4-1-review-I1] corr 为一切"经 correlate* 加入链"的事件的必录
# 字段（seq_primary | addr_fallback——仅地址关联必须显式标注，不得静默）。
# 例外：pf_demand / pf_fill 允许 fault_id=0（仅预取请求链、无故障链关联，
# corr 留空是诚实缺席），故不列入其必录。
REQUIRED_FIELDS = {
    "lsq_push": ["fault_id", "corr", "dyn_inst_seq", "pc", "opcode",
                 "lq_idx", "sq_idx", "va"],
    "lsq_sendfrag": ["fault_id", "corr", "dyn_inst_seq", "pc", "opcode",
                     "request_id", "va"],
    # [MDSPEC][H2] pa 入口未定留空（诚实 pending；PA 物化由 resp 节点覆盖）
    "tlb_translate": ["fault_id", "corr", "dyn_inst_seq", "va", "request_id"],
    "tlb_lookup": ["fault_id", "corr", "dyn_inst_seq", "request_id", "va",
                   "entry_index", "field", "state_before", "state_after"],
    "tlb_translate_result": ["fault_id", "corr", "dyn_inst_seq",
                             "request_id", "va", "pa", "field",
                             "state_before", "state_after"],
    # [MDSPEC][R4-5.9] T08 walk/fill 配对（FS-only，见 KIND_LAYER 注）。
    # tlb_walk：walk 发出点（TableWalker::walk，table_walker.cc）——必录
    #   walk_id（配对键）+ va + dyn_inst_seq/request_id（Request 身份；
    #   "0"=未盖戳，lsq_sendfrag 约定）。corr=origin（注入器注册事件，
    #   无 correlate* 查询——与 registerTlbFault 的 inj 节点同形）。
    # tlb_refill：该 walk 的 refill 完成节点，必录同一 walk_id（配对可证）
    #   + va + field（refill 结局：正常=pte 字段名；T08-a 丢失="lost"）。
    #   corr=origin（注入器注册事件）。
    "tlb_walk": ["fault_id", "corr", "walk_id", "va", "dyn_inst_seq",
                 "request_id"],
    "tlb_refill": ["fault_id", "corr", "walk_id", "va", "field"],
    # [MDSPEC][H2-fix] 翻译 fault 检测（detection_layer=Hardware；contained
    # 为空 = pending offline join——不预定终局）
    "tlb_fault": ["fault_id", "corr", "dyn_inst_seq", "va", "outcome",
                  "detection_layer"],
    # [MDSPEC][H2-FS][R4-4] TLB-entry pfn 故障：before/after = old/new PFN，
    # state_before/after = old/new PA（hex）。R4-4 起 MMU::getTE 向 TLB 发布
    # 在飞翻译的 Request 身份（chaosLookupReqSeq）→ 链 SEQ-PRIMARY 注册：
    # dyn_inst_seq/request_id 必录（"0"=未盖戳——table-walker/functional
    # 查询路径无 Request 身份，lsq_sendfrag 约定）。corr 标注注册臂
    # （seq_primary=主臂已注册；addr_fallback=仅 PA 页 fallback；空=无关联
    # 面——req_seq=0 且 PA 页未变，链诚实止于本事件，不预定下游）。
    # corr 不列入必录：空值合法（无关联面），不得强制非空。
    "tlb_pfn": ["fault_id", "dyn_inst_seq", "request_id", "va", "before",
                "after", "field", "state_before", "state_after"],
    # [MDSPEC][R4-10-T05/T06/T07] entry-state / attribute / CAM faults:
    # field + state_before/state_after are the payload (no before/after pfn —
    # the pfn is not the fault surface). corr NOT required: empty is a legal
    # honest no-surface value (req_seq=0 ⇒ chain stops at this event).
    "tlb_state": ["fault_id", "dyn_inst_seq", "request_id", "va", "field",
                  "state_before", "state_after"],
    # [MDSPEC][H7] LQ 生命周期（va 取注册表 base；pa=响应地址）
    "lq_read": ["fault_id", "corr", "dyn_inst_seq", "lq_idx", "va"],
    "lq_complete": ["fault_id", "corr", "dyn_inst_seq", "lq_idx", "va", "pa"],
    # [MDSPEC][H3] SQ 生命周期（execute→writeback→complete）
    "sq_execute": ["fault_id", "corr", "dyn_inst_seq", "sq_idx", "va",
                   "state_before"],
    "sq_writeback": ["fault_id", "corr", "dyn_inst_seq", "sq_idx", "pa"],
    "sq_complete": ["fault_id", "corr", "dyn_inst_seq", "sq_idx", "va",
                    "state_after"],
    # [MDSPEC][H3-FWD] before/after = 转发数据被污染前后。
    # [MDSPEC][R4-1] seq/idx/request_id 为 PRIMARY 关联键（用户裁决
    # 2026-10-20）：dyn_inst_seq=消费 load 的 seq；store_dyn_inst_seq=
    # 生产 store 的 seq；sq_idx/lq_idx 与 sq_*/lq_read 事件同源（1:1
    # join）；request_id=load 请求的 Request-stamped seq（lsq_sendfrag
    # 约定，未盖戳=0）。仅地址关联只允许作为 corr=addr_fallback 标注的
    # fallback 出现，不得静默。
    "lsq_fwd": ["fault_id", "dyn_inst_seq", "store_dyn_inst_seq",
                "sq_idx", "lq_idx", "request_id", "va", "field",
                "before", "after"],
    # [MDSPEC][R4-5.7] S10 StoreSet SSIT 腐蚀链（S10-a 换值；注入器
    # CHAOSLSQFwd --lsqfwd_s10，注入点 StoreSet::violation 新 SSID 赋值臂）。
    # ssit_consult: before/after = 反事实/实际预测的 producing-store seq
    # （本模型的被故障值=预测；before=真 SSID 的 LFST 槽会返回什么，
    # after=被腐蚀 SSID 实际返回什么；entry_index=实际命中的 SSID）。
    # ssit_violation: state_before = violation 时刻该 PC 仍映射的 SSID
    # （腐蚀存续期=替换值；violation 重训自愈后=合并值——流保持诚实）。
    # corr 刻意不列入必录（pf_train 先例类）：链成员资格来自注入器自有
    # 的 PC 键匹配，非 correlate* 查询——CORR_VALUES 5 值词汇表无 PC 键
    # join 标记，扩表会破坏 test_lsu_prop_fields §6 的钉死契约（此为
    # 已裁决的诚实缺席，非静默地址关联；登记于 R4-5.7 报告）。
    "ssit_consult": ["fault_id", "pc", "field", "before", "after",
                     "entry_index"],
    "ssit_violation": ["fault_id", "pc", "field", "state_before"],
    # [MDSPEC][H4] cache 结构事件（access/return/fill/evict）
    "cache_access": ["fault_id", "corr", "va", "pa"],
    "cache_return": ["fault_id", "corr", "pa", "field"],
    "cache_fill": ["fault_id", "corr", "pa", "cache_line", "fill_id"],
    # victim 证据：set/way + victim tag（before）+ dirty 状态在 field
    "cache_evict": ["fault_id", "corr", "cache_line", "set", "way"],
    "mshr_alloc": ["fault_id", "corr", "cache_line", "mshr_id"],
    "mshr_merge": ["fault_id", "corr", "cache_line", "mshr_id"],
    "mshr_fill": ["fault_id", "corr", "cache_line", "mshr_id", "fill_id"],
    "mshr_free": ["fault_id", "corr", "cache_line", "mshr_id"],
    # [MDSPEC][R4-5.5] C14-a MSHR busy/occupied stuck-at-1: the entry that
    # completed its fill but was NOT released (busy/occupied stuck-at-1).
    # state_before/state_after = should_release / stuck_busy; entry_index
    # = mshr_id (the queue slot identity — 表9 C14 行点名监控 "mshr_id、
    # busy/free tick、occupancy"); corr = origin (chain-opening node).
    "mshr_busy": ["fault_id", "corr", "mshr_id", "entry_index",
                  "cache_line", "field", "state_before", "state_after"],
    # [MDSPEC][R4-5.6] C15-b MSHR capacity arbitration: the over-capacity
    # allocation the faulty arbitration allowed. state_before/after =
    # full_blocked / over_commit_alloc; entry_index = the MSHR occupancy at
    # the over-commit (the model's faulted bookkeeping — 表9 C15 行点名
    # 监控 "真实/故障 occupancy、free/full、used entry"); mshr_id = the
    # over-committed entry; corr = origin (chain-opening node).
    "mshr_arb": ["fault_id", "corr", "mshr_id", "entry_index",
                 "cache_line", "field", "state_before", "state_after"],
    "cache_writeback": ["fault_id", "corr", "cache_line"],
    # [MDSPEC][H5] prefetch 链：pf_request_id 为请求级稳定标识（≠ fault_id），
    # 同一预取请求的 queue/issue/fill/demand 四节点必须携带同一值。
    # pf_queue/pf_issue 仅在故障链关联（ptag>0）时发射 → corr 必录；
    # pf_fill/pf_demand 允许 fault_id=0（仅预取请求链）→ corr 可空。
    "pf_train": ["fault_id", "pf_request_id", "pc", "before", "after"],
    "pf_queue": ["fault_id", "corr", "pf_request_id", "va", "entry_index"],
    "pf_issue": ["fault_id", "corr", "pf_request_id", "va"],
    "pf_fill": ["fault_id", "pf_request_id", "pa", "cache_line"],
    "pf_demand": ["fault_id", "pf_request_id", "dyn_inst_seq", "request_id",
                  "pa"],
    # [MDSPEC][H6] atomic 链
    "atomic_op": ["fault_id", "corr", "dyn_inst_seq", "va"],
    # [MDSPEC][R4-9-FSMC] O04/O05/O09 RMW 数据面/完成面节点：必录值面对
    # （before/after）+ 载体（cache_line/entry_index 为地址域关联键；
    # field 标注子模型规则）+ corr（origin=链开启注册）。
    "rmw_data": ["fault_id", "corr", "cache_line", "field",
                 "before", "after"],
    "rmw_result": ["fault_id", "corr", "cache_line", "field",
                   "before", "after"],
    "rmw_order": ["fault_id", "corr", "cache_line", "field",
                  "state_before", "state_after"],
    # [MDSPEC][R4-9-FSMC] O06/O07：屏障完成点无地址/序号面（PC 键控的
    # 记账结构），carrier = 屏障 SN 的前后值（before/after 记 SN 迁移）
    # + corr=origin（链开启注册）。
    "barrier_done": ["fault_id", "corr", "field",
                     "state_before", "state_after"],
    "order_tag": ["fault_id", "corr", "field",
                  "state_before", "state_after"],
    # [MDSPEC][H6] exmon 链（monitor 地址 before/after + 保留比较 + STXR
    # 消费/重试；request_id 为 LL-SC 配对键的一部分）
    "exmon_monitor": ["fault_id", "dyn_inst_seq", "request_id", "pa",
                      "before", "after"],
    "exmon_rmw": ["fault_id", "dyn_inst_seq", "pa", "state_before",
                  "state_after"],
    "exmon_stxr": ["fault_id", "dyn_inst_seq", "request_id", "pa",
                   "state_before", "state_after", "entry_index"],
    # [MDSPEC][R4-4-review-I1] v1 writeNode 双发事件族：corr 必录（每个
    # 入链事件必须显式标注关联来源；无 join 时用 origin/taint_prop/none
    # 显式说明——见 CORR_VALUES）。inj/addr_form = origin（链开启注册，
    # 无 join）；mem_req = 匹配臂（seq_primary|addr_fallback）；resp/
    # taint_reg = 交付响应命中的关联臂；consumer/errant_commit =
    # taint_prop（污染集成员关系，非 correlate 查询）。其余必录字段为
    # 发射端结构性保证（noteMemRequest/noteMemResponse/noteCommit 恒填）。
    "inj": ["fault_id", "corr"],
    "addr_form": ["fault_id", "corr", "va"],
    "mem_req": ["fault_id", "corr", "dyn_inst_seq", "va"],
    "resp": ["fault_id", "corr", "dyn_inst_seq"],
    "taint_reg": ["fault_id", "corr", "dyn_inst_seq", "phys_reg",
                  "arch_reg"],
    "consumer": ["fault_id", "corr", "dyn_inst_seq", "phys_reg",
                 "arch_reg"],
    "errant_commit": ["fault_id", "corr", "dyn_inst_seq"],
    # [MDSPEC][L5] 链终局（退出回调发射；corr=none——退出汇总不关联任何
    # 事件，事件级 corr 已携带各自来源）
    "chain_end": ["fault_id", "outcome", "detection_layer", "contained",
                  "corr"],
}


def register_kind_layer(kind, layer):
    """H 族钩子注册 kind→层级映射（layer ∈ L0..L5）。"""
    if layer not in _LAYER_ORDER:
        raise ValueError(f"layer must be one of {_LAYER_ORDER}, got {layer}")
    KIND_LAYER[kind] = layer


def validate_event(evt):
    """按家族契约校验：kind 必须已知 + REQUIRED_FIELDS 全部非空。

    返回错误列表（空 = 合法）。观测流是故障传播流（规格 11），
    fault_id 非空即链关联在场——非关联观测事件不得入流。
    """
    kind = evt.get("kind", "")
    errs = []
    if kind not in KIND_LAYER:
        errs.append(f"unknown kind '{kind}' (not in KIND_LAYER)")
        return errs
    for f in REQUIRED_FIELDS.get(kind, []):
        if not evt.get(f, ""):
            errs.append(f"{kind}: required field '{f}' missing/empty")
    return errs


def parse_line(line):
    """解析一行 PROP-EVT；非 PROP-EVT 行返回 None。缺键填空串。"""
    line = line.strip()
    if not line.startswith(_PREFIX):
        return None
    evt = {f: "" for f in PROP_EVT_FIELDS}
    body = line[len(_PREFIX):].strip()
    if body:
        for tok in body.split():
            k, sep, v = tok.partition("=")
            if sep:
                # 注册表键必有（空值合法）；注册表外的家族键（表 11 24 字段
                # 之外的 asid/hit 等）保留在 dict 中供家族消费
                evt[k] = v
    return evt


def evidence_status_of(evt):
    """规格 11：evidence_status 缺省 observed。"""
    return evt.get("evidence_status") or "observed"


# ============================================================ consumer_summary
# [MDSPEC][R6-FIXTOOLS] T04 `consumer_summary` 记录契约。
#
# 口径（用户裁决 2026-10-24）：**语义状态变化完整保留，重复 consumer 有账聚合；
# 禁止简单截断**。一个故障链可能把同一污染值喂给极大量 consumer（同一
# dyn_inst_seq 反复命中，或同一状态的重复消费）。逐个写出会淹没流且无信息增量，
# 于是发射端把**重复** consumer 聚合进一条 summary —— 但**语义状态变化**（新的
# 污染源 / 新的 dyn_seq / 新的 outcome）仍逐条保留为 PROP-EVT。summary 只聚合
# **重复**，绝不丢弃不同语义状态。
#
# 关键约束（8 条规则，tests/test_lsu_r6_consumer_summary.py 钉死）：
#   ① summary **不映射** L0–L5 任何一层（它不是 PROP-EVT、无 kind、不进 chain）；
#   ② summary **不得**充当 L5 / containment / terminal；
#   ③ summary **不得**成为伪造的 parent ancestry 节点（无 event_id、不进 DAG）；
#   ④ malformed / 负计数 / 计数不守恒 ⇒ **响亮拒绝**（validate_consumer_summary）；
#   ⑤ checker 选出的 path_event_ids/terminal/admitted/violations 在**小型未聚合
#      对照流**与**聚合流**上必须一致（summary 只替换重复项，不动链）；
#   ⑥ campaign 报告同时展示 emitted events / suppressed consumers / logical total
#      / conservation 状态；
#   ⑦ truncated / resource_abort 仍必须 admitted=False，**不得靠 summary 掩盖**；
#   ⑧ 原有无 summary 流必须保持兼容（read_events 行为不变）。
#
# 行格式（发射端 CHAOSPropagation 退出回调；解析端容错）：
#   CONSUMER-SUMMARY: schema=1 version=1 run_id=… sample_run_id=… fault_id=…
#     source_id=… suppressed_consumer_count=… distinct_dyn_seq_count=…
#     emitted_consumer_count=… first_tick=… last_tick=… min_dyn_seq=…
#     max_dyn_seq=… by_kind=consumer:12,errant_commit:1
#     by_outcome=sd_observed:12,errant:1 total_before=… total_after=…
# 守恒：total_before == total_after == emitted_consumer_count +
#       suppressed_consumer_count；sum(by_kind) == sum(by_outcome) == total_before。
SUMMARY_PREFIX = "CONSUMER-SUMMARY:"
# 字符串身份字段（须非空）。
SUMMARY_STR_FIELDS = ("schema", "version", "run_id", "sample_run_id",
                      "fault_id", "source_id")
# 整数字段（须可解析、非负）。
SUMMARY_INT_FIELDS = ("schema", "version", "suppressed_consumer_count",
                      "distinct_dyn_seq_count", "emitted_consumer_count",
                      "first_tick", "last_tick", "min_dyn_seq", "max_dyn_seq",
                      "total_before", "total_after")
# 逐类精确计数映射字段（`<key>:<n>,<key>:<n>`）。
SUMMARY_MAP_FIELDS = ("by_kind", "by_outcome")


def parse_consumer_summary(line):
    """解析一行 CONSUMER-SUMMARY；非 summary 行返回 None（PROP-EVT 走 parse_line）。

    返回 {字段: 原始字符串}；缺失字段填空串（键不省略），`raw` 存原行。
    本函数**不做**语义校验——malformed/负计数/不守恒由 validate_consumer_summary
    判定并由调用方**响亮**处理。
    """
    if not line:
        return None
    s = line.strip()
    i = s.find(SUMMARY_PREFIX)
    if i < 0:
        return None
    rec = {f: "" for f in set(SUMMARY_STR_FIELDS) | set(SUMMARY_INT_FIELDS)
           | set(SUMMARY_MAP_FIELDS)}
    rec["raw"] = s
    body = s[i + len(SUMMARY_PREFIX):].strip()
    for tok in body.split():
        k, sep, v = tok.partition("=")
        if sep:
            rec[k] = v
    return rec


def _parse_count_map(raw):
    """`k:n,k:n` → {k:int}；格式非法返回 None。空串 → {}。"""
    out = {}
    if raw is None or str(raw).strip() == "":
        return out
    for part in str(raw).split(","):
        k, sep, v = part.partition(":")
        if not sep or not k.strip():
            return None
        try:
            n = int(v)
        except ValueError:
            return None
        out[k.strip()] = n
    return out


def validate_consumer_summary(rec):
    """校验一条 summary 记录；返回错误串列表（空 = 合法且守恒）。

    规则 ④：malformed（缺必录/非整数）/ 负计数 / 计数不守恒一律给出**响亮**
    错误。任一基础字段非法即提前返回（守恒断言依赖它们，不做级联误判）。
    """
    if not isinstance(rec, dict):
        return ["consumer_summary 非法（非记录对象）"]
    errs = []
    for f in SUMMARY_STR_FIELDS:
        if not str(rec.get(f, "")).strip():
            errs.append(f"consumer_summary: 缺必录字段 '{f}'")
    for f in SUMMARY_MAP_FIELDS:
        if not str(rec.get(f, "")).strip():
            errs.append(f"consumer_summary: 缺必录字段 '{f}'")
    ints = {}
    for f in SUMMARY_INT_FIELDS:
        raw = str(rec.get(f, "")).strip()
        try:
            n = int(raw)
        except (TypeError, ValueError):
            errs.append(f"consumer_summary: 字段 '{f}' 非整数（{raw!r}）")
            continue
        ints[f] = n
        if n < 0:
            errs.append(f"consumer_summary: 字段 '{f}' 为负（{n}）——拒绝")
    if errs:
        return errs
    bk = _parse_count_map(rec.get("by_kind"))
    bo = _parse_count_map(rec.get("by_outcome"))
    if bk is None:
        errs.append("consumer_summary: by_kind 格式非法（应为 k:n,k:n）")
    if bo is None:
        errs.append("consumer_summary: by_outcome 格式非法（应为 k:n,k:n）")
    if errs:
        return errs
    # 守恒断言
    if ints["total_before"] != ints["total_after"]:
        errs.append("consumer_summary: 计数不守恒 total_before=%d != "
                    "total_after=%d" % (ints["total_before"],
                                        ints["total_after"]))
    if ints["total_after"] != (ints["emitted_consumer_count"]
                               + ints["suppressed_consumer_count"]):
        errs.append("consumer_summary: 计数不守恒 total_after=%d != emitted=%d "
                    "+ suppressed=%d" % (ints["total_after"],
                                         ints["emitted_consumer_count"],
                                         ints["suppressed_consumer_count"]))
    if sum(bk.values()) != ints["total_before"]:
        errs.append("consumer_summary: by_kind 合计=%d != total_before=%d"
                    % (sum(bk.values()), ints["total_before"]))
    if sum(bo.values()) != ints["total_before"]:
        errs.append("consumer_summary: by_outcome 合计=%d != total_before=%d"
                    % (sum(bo.values()), ints["total_before"]))
    if ints["distinct_dyn_seq_count"] > ints["total_before"]:
        errs.append("consumer_summary: distinct_dyn_seq_count=%d > "
                    "total_before=%d（不可能）"
                    % (ints["distinct_dyn_seq_count"], ints["total_before"]))
    if ints["total_before"] > 0 and ints["emitted_consumer_count"] == 0:
        errs.append("consumer_summary: total_before=%d 但 emitted=0 —— 简单截断"
                    "（语义状态变化必须完整保留，禁止全抑无出）"
                    % ints["total_before"])
    return errs


def read_stream(path, cap=EVENT_CAP):
    """读整条流：PROP-EVT 事件 + consumer_summary 记录分离。

    返回 (events, truncated, summaries, summary_issues)。summary 行**不**进入
    events（规则 ①③：不占层、不进 DAG）；其校验问题单独返回供调用方关闭准入。
    read_events 保持原签名/行为（规则 ⑧ 兼容无 summary 流）。

    [R6-STREAM] 有界流式：events 至多保留 cap 条（默认 EVENT_CAP）。逐行迭代
    （绝不整体 read()/解压进内存），第 cap+1 条起的 PROP-EVT 只**计数不保留**，
    并置 truncated=True（=OVER_CAP：流不完整，调用方据此判未证，绝不静默
    截断后仍认证通过）。故峰值内存与流大小无关。返回元组仍是 4 元（既有
    调用方 PF.read_stream(evt) 解 4 元不变）。
    """
    path = Path(path)
    truncated = False
    events = []
    summaries = []
    issues = []
    seen = 0
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", errors="replace") as f:
            for line in f:
                summ = parse_consumer_summary(line)
                if summ is not None:
                    summaries.append(summ)
                    issues.extend(validate_consumer_summary(summ))
                    continue
                if not line.lstrip().startswith(_PREFIX):
                    continue
                seen += 1
                if seen > cap:
                    # 超出上限：只计数，不解析、不保留（有界内存的关键）
                    truncated = True
                    continue
                evt = parse_line(line)
                if evt is not None:
                    events.append(evt)
    # [R6-FREQPOLICY-fix] zlib.error（deflate 载荷损坏，Error -3）**不是
    # OSError 子类**，必须显式列出：gzip 头完好但压缩数据不可解码同样是
    # "读不到 EOF" 的磁盘事实 ⇒ 按截断诚实标记（保留已解析前缀），绝不令
    # 调用方崩溃。刻意保持显式异常元组而非宽泛 except Exception——
    # 解析逻辑 bug 必须响亮失败，不得被吞成截断。
    except (EOFError, gzip.BadGzipFile, OSError, zlib.error):
        truncated = True
    return events, truncated, summaries, issues


def provable_to(events):
    """按在场事件判定最大可证层级。

    返回 {provable_to, beyond}：更高层一律 beyond=Unknown——链路缺失不得
    推断为 Masked（用户指令二.5 / Review Focus #3）。空链 = 连 L0 都
    不可证（provable_to=None）。
    """
    layers = [KIND_LAYER.get(e.get("kind", ""), None) for e in events]
    layers = [l for l in layers if l in _LAYER_ORDER]
    if not layers:
        return {"provable_to": None, "beyond": "Unknown"}
    deepest = max(layers, key=_LAYER_ORDER.index)
    if deepest == "L5":
        return {"provable_to": "L5", "beyond": ""}
    return {"provable_to": deepest, "beyond": "Unknown"}


def read_events(path, cap=EVENT_CAP):
    """读 PROP-EVT 流（.gz 或普通文件）。返回 (events, truncated)。

    规则 ⑧：原签名/行为不变——CONSUMER-SUMMARY 行与 PROP-EVT 一样被 parse_line
    忽略（它不是 PROP-EVT），故无 summary 的旧流逐位兼容；需要 summary 的调用方
    用 read_stream（额外返回 summaries + issues）。
    [R6-STREAM] 单参调用不变（cap 缺省 EVENT_CAP）；有界语义见 read_stream。
    """
    events, truncated, _summaries, _issues = read_stream(path, cap)
    return events, truncated
