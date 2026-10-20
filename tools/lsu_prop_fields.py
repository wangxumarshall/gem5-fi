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
from pathlib import Path

# 与 CHAOSPropagation.hh 的 PROP_EVT_FIELDS[] 同名同序。
# kind 为事件语义首字段（规格表 11 未列——计划 H0 裁决：v1 已有 kind 概念，
# 无 kind 则事件不可分型；24 规格字段全部在列）。
PROP_EVT_FIELDS = [
    "kind", "run_id", "sample_run_id", "fault_id", "event_id",
    "parent_event_id", "tick", "cycle", "core_id", "thread_id",
    "dyn_inst_seq", "commit_seq", "pc", "opcode", "lq_idx", "sq_idx",
    "request_id", "walk_id", "mshr_id", "fill_id", "pf_request_id",
    "va", "pa", "cache_line", "set", "way", "entry_index", "field",
    "before", "after", "state_before", "state_after", "arch_reg",
    "phys_reg", "detection_layer", "contained", "outcome", "oracle_diff",
    "evidence_status",
]

_PREFIX = "PROP-EVT:"

# kind → 观测层级（v1 kinds 先行；H1-H7 钩子族经 register_kind_layer 注册
# 自己的映射——发射端 kind 命名与层级语义由各族任务定义）。
KIND_LAYER = {
    "inj": "L0", "addr_form": "L1", "mem_req": "L2", "resp": "L3",
    "taint_reg": "L4", "consumer": "L4", "errant_commit": "L4",
    # [MDSPEC][H1] lsq.cc 统一事件（表 9：L1=EA/size/flags 进入 LSQRequest；
    # L2=请求离开 LSQ 去翻译/访存）
    "lsq_push": "L1", "lsq_sendfrag": "L2",
    # [MDSPEC][H2] TLB 翻译统一事件（mmu.cc translateTiming = SE+FS 漏斗；
    # SE 不经 TLB::lookup——tlb.cc:173 实证。tlb_walk/tlb_refill 属 FS
    # 路径，推迟到 FS TLB 轨道，未注册 = 诚实缺席）
    "tlb_translate": "L2",
    # [MDSPEC][H2-fix] 翻译 fault 检测事件（A01 POST 根因：corrupted vaddr
    # 落到未映射地址 → 翻译 fault = Hardware 检测 + contained）
    "tlb_fault": "L2",
    # [MDSPEC][H7] LQ 逐事件（表 9：lq_idx 生命周期；read/completion 属
    # L3 访存发射与返回；insert 在 dispatch 期早于注入注册、结构性缺席）
    "lq_read": "L3", "lq_complete": "L3",
    # [MDSPEC][H3] SQ 生命周期（execute/writeback/complete；drain 属 L3 访存侧）
    "sq_execute": "L3", "sq_writeback": "L3", "sq_complete": "L3",
    # [MDSPEC][H4] cache 结构事件（L1=lookup / L2=hit返回·miss+MSHR+fill+evict
    # / L3=writeback 持久化）
    "cache_access": "L1", "cache_return": "L2", "cache_fill": "L2",
    "cache_evict": "L2", "mshr_alloc": "L2", "mshr_merge": "L2",
    "mshr_fill": "L2", "mshr_free": "L2",
    "cache_writeback": "L3",
    # [MDSPEC][H6] atomic 事件链
    "atomic_op": "L2",
    # [MDSPEC][L5] 链终局（退出回调发射；outcome=detection_layer/contained）
    "chain_end": "L5",
}
_LAYER_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5"]

# 家族必录字段契约（kind → 必须非空的注册表字段；表 9 必监控列）。
# 发射端（C++ 钩子）与本校验共用此表——契约测试 tests/test_lsu_hook_*.py
# 逐族钉死。
REQUIRED_FIELDS = {
    "lsq_push": ["fault_id", "dyn_inst_seq", "pc", "opcode",
                 "lq_idx", "sq_idx", "va"],
    "lsq_sendfrag": ["fault_id", "dyn_inst_seq", "pc", "opcode",
                     "request_id", "va"],
    # [MDSPEC][H2] pa 入口未定留空（诚实 pending；PA 物化由 resp 节点覆盖）
    "tlb_translate": ["fault_id", "dyn_inst_seq", "va", "request_id"],
    # [MDSPEC][H2-fix] 翻译 fault 检测（detection_layer=Hardware；contained
    # 为空 = pending offline join——不预定终局）
    "tlb_fault": ["fault_id", "dyn_inst_seq", "va", "outcome",
                  "detection_layer"],
    # [MDSPEC][H7] LQ 生命周期（va 取注册表 base；pa=响应地址）
    "lq_read": ["fault_id", "dyn_inst_seq", "lq_idx", "va"],
    "lq_complete": ["fault_id", "dyn_inst_seq", "lq_idx", "va", "pa"],
    # [MDSPEC][H3] SQ 生命周期（execute→writeback→complete）
    "sq_execute": ["fault_id", "dyn_inst_seq", "sq_idx", "va",
                   "state_before"],
    "sq_writeback": ["fault_id", "dyn_inst_seq", "sq_idx", "pa"],
    "sq_complete": ["fault_id", "dyn_inst_seq", "sq_idx", "va",
                    "state_after"],
    # [MDSPEC][H4] cache 结构事件（access/return/fill/evict）
    "cache_access": ["fault_id", "va", "pa"],
    "cache_return": ["fault_id", "pa", "field"],
    "pf_issue": ["fault_id", "pf_request_id", "va"],
    # [MDSPEC][H6] atomic 链
    "atomic_op": ["fault_id", "dyn_inst_seq", "va"],
    # [MDSPEC][L5] 链终局（退出回调发射）
    "chain_end": ["fault_id", "outcome", "detection_layer", "contained"],
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


def read_events(path):
    """读 PROP-EVT 流（.gz 或普通文件）。返回 (events, truncated)。"""
    path = Path(path)
    truncated = False
    events = []
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", errors="replace") as f:
            for line in f:
                evt = parse_line(line)
                if evt is not None:
                    events.append(evt)
    except (EOFError, gzip.BadGzipFile, OSError):
        # Z_SYNC_FLUSH 前缀可救；截断标记（abort 样本契约）
        truncated = True
    return events, truncated
