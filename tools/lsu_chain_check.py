#!/usr/bin/env python3
"""lsu_chain_check.py — [MDSPEC][C1] L0→L5 传播链完整性检查器。

规格（表 9 完整性/传播终止判定列，全部 RunID 共文）：
"完整：存在 L0 fault_applied，且每条边由共享键与时间/可达性同时证明，最终
到达 (1) errant commit/错误内存副作用/软件 oracle 差异，或 (2) 明确检测并
contained，或 (3) 明确 squash/replay/mask 且无错误副作用。若链在某节点后
缺事件，只能标'截至该节点可证，后续 Unknown'，不得推断 Masked。"

实现（计划 Task C1 Interfaces）：
- check_chain(events, spec_nodes=None) → {edges, terminal}
- 边证明规则：必须在 parent_event_id DAG 的**同一条祖先路径**上依次
  找到 L0,L1,...；所选事件 tick 单调。禁止把两个分支或乱序阶段上的
  独立证人拼成一条链。
- TLB family 使用表 9 专用层级：L1 只认 tlb_lookup；下游
  cache_access 属 L3，绝不能冒充 DTLB lookup。
- 终止判定：
  * full                    —— L0→L5 全边 proven，且同一祖先链包含
                                errant_commit 与**真实检测事件**（[R6-GATE-D1]
                                非生命周期 kind + detection_layer + outcome +
                                链关联 corr；生命周期 chain_end 永不充当 L5）
  * provable_to_Ln_then_unknown —— 在 Ln 后缺事件（绝不推断 Masked）
  * detected_contained      —— 存在**真实检测事件**（_explicit_l5）且 contained=1
  * squash_replay_masked    —— 存在显式 squash/replay/mask 证据事件
  （后两者只认显式事件，缺席不猜测——诚实纪律）
- L5（检测/结局）事件当前由 runner/reclass 离线 join 产出；PROP-EVT 流内
  无 L5 kind 时链至 L4 止，L4→L5 标 missing（→ Unknown，非 Masked）。

[R6-FIXB] containment 选项 2 的**完整性前提**：含住主张（"故障止于 Ln，
之后无传播"）是对**缺席**的断言，只在**完整收口**的证据流上可证。PROP-EVT
的收口标记是退出回调发射的生命周期 chain_end（abort/崩溃样本没有 ——
CHAOSPropagation.cc 实证注释）。故 `containment_from_events` 对未收口流或
调用方标记 `truncated` 的流一律返回 None；`check_admission` 在存在含住候选
却拿不出束时响亮点名 containment_on_unclosed_stream /
containment_on_truncated_stream。真实 T06/T08-F0-W4 的流即 abort 截断
（read_events → truncated=True），旧口径据此判含住准入是缺陷 #5；收口后
二者一律不准入，而完整运行的真实含住（如 T05-F0-W4）仍可准入。

用法：python3 tools/lsu_chain_check.py <prop_evt.txt[.gz]> [--run-id X]
（退出码 0=检查完成；结果打印 JSON；对多 fault_id 分别判定）
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_prop_fields as P  # noqa: E402

# 规格层级序（表 9 传播路径：L0 注入 → L1 单元内部 → L2 请求/翻译 →
# L3 cache/内存 → L4 架构可见 → L5 检测/结局）
LAYERS = ["L0", "L1", "L2", "L3", "L4", "L5"]

# [R6-GATE-D1] L5 = 检测/结局层。它的**唯一**合法证据是"真实检测事件"：
# 一个非生命周期 kind 的事件，同时携带 非空 detection_layer、非空 outcome、
# 以及链关联 corr（即该事件确实由 correlate*/污染集成员关系关联进本故障链）。
# chain_end 由 CHAOSPropagation 退出回调发射，是**链生命周期标记**（规范
# 词汇表 _CORR 中 corr=none，无关联语义），故结构性**永不**充当 L5：它不占
# 任何层级（_layer_of → None）。这样 ready_by_chain_end_only 由构造堵死，
# 而不再只是一条文案（D1）。真实流实证：T04/T02 的 chain_end 为
# outcome=errant_commit_seen / detection_layer=None / corr=none，其真实检测
# 点是 errant_commit（未富化 ⇒ 只到 L4）；T05/T08 的 tlb_translate_result 才
# 是带 dl+contained+outcome+corr 的真实检测事件。
_LIFECYCLE_KINDS = frozenset({"chain_end"})

# 链关联 corr 取值（lsu_prop_fields.CORR_VALUES 去掉生命周期值 "none"）。
_CHAIN_CORR = frozenset({"seq_primary", "addr_fallback", "origin",
                         "taint_prop"})

_EMPTY_DETECTION = ("", "None", "none", "Unknown", "unknown")
_EMPTY_OUTCOME = ("", "run_end", "unknown", "Unknown")

# contained 字段的"真"取值（发射端写 1；解析端容忍文本形式）。
_CONTAINED_VALUES = ("1", "true", "True", "yes", "Yes")


def _explicit_l5(evt):
    """真实检测事件 = 非生命周期 kind + detection_layer + outcome + 链关联 corr。

    生命周期 chain_end 恒为 False（corr=none）——这是 D1 的结构性保证。
    """
    if evt.get("kind", "") in _LIFECYCLE_KINDS:
        return False
    if str(evt.get("detection_layer", "")).strip() in _EMPTY_DETECTION:
        return False
    if str(evt.get("outcome", "")).strip() in _EMPTY_OUTCOME:
        return False
    return str(evt.get("corr", "")).strip() in _CHAIN_CORR


_L4_TERMINAL_KINDS = {"errant_commit"}  # L4 终局：首个错误提交（v1/H0）

# [MDSPEC][R6-T11B] "squash 类"收口证据的 kind 标记：R6/A10 的
# contain-by-squash（`squash_masked`：收到错误响应的 load 被 squash 丢弃并
# 重放）与任何 squash/replay/mask 收口共享同一语义类别。errant_commit 逃逸
# 优先权护栏**只**对这一类生效（见 `_terminal` / `containment_from_events`）。
_SQUASH_KIND_MARKERS = ("squash", "replay", "mask")


def _is_squash_witness(evt):
    """该事件是否属于 squash/replay/mask 类收口证据（contain-by-squash）。"""
    kind = str(evt.get("kind", ""))
    return any(k in kind for k in _SQUASH_KIND_MARKERS)

# 闭合终局（链已收敛 → beyond=""）。其余（provable_to_*_then_unknown /
# detected_translation_outcome_pending / no_l0_fault_applied）为开放终局，
# beyond="Unknown"。此集合与 _terminal 的返回值必须一致——
# tests/test_lsu_chain_check.py 钉死该自洽性。
CLOSED_TERMINALS = {
    "full",
    "detected_contained",
    "squash_replay_masked",
    "crash_translation_blocked",
    "timeout_translation_blocked",
    "sdc_translation_blocked",
}


_TLB_SIGNATURE_KINDS = {
    "tlb_lookup", "tlb_pfn", "tlb_state", "tlb_walk", "tlb_refill",
    "tlb_translate_result",
}

_TLB_KIND_LAYER = {
    "inj": "L0",
    "tlb_lookup": "L1",
    "tlb_pfn": "L2", "tlb_state": "L2", "tlb_walk": "L2",
    "tlb_refill": "L2", "tlb_translate": "L2",
    "tlb_translate_result": "L2", "tlb_fault": "L2",
    # Table 9 T-series L3 is the request/cache/memory side after translation.
    "lsq_sendfrag": "L3", "mem_req": "L3", "lq_read": "L3",
    "lq_complete": "L3", "sq_execute": "L3", "sq_writeback": "L3",
    "sq_complete": "L3", "resp": "L3", "cache_access": "L3",
    "cache_return": "L3", "cache_fill": "L3", "cache_evict": "L3",
    "mshr_alloc": "L3", "mshr_merge": "L3", "mshr_fill": "L3",
    "mshr_free": "L3", "cache_writeback": "L3",
    "taint_reg": "L4", "consumer": "L4", "errant_commit": "L4",
    # [MDSPEC][R6-T11B] R6/A10 contain-by-squash 显式检测事件
    # （CHAOSPropagation.cc notePropEvt("squash_masked", … detection_layer=L4
    # contained=1 outcome=masked containment_reason=squash_replay)）。观测层
    # = 发射端声明的 detection_layer=L4（与 errant_commit 的观测角色同层）。
    # 此前未注册 ⇒ `_event_has_prefix` 对该 kind 恒拒 ⇒ detected_contained
    # / squash_replay_masked / containment_from_events 三条收口路径全部死路
    # （T02-F2-W4 seed2 被误判 provable_to_L5_then_unknown 而拒准入）。
    "squash_masked": "L4",
    "chain_end": "L5",
}


# [R6-GATE-D4] 族判定：RunID 前缀 = 单元族（台账模型号：T=tlb / L=Load Queue /
# S=Store Queue / C=L1d-Cache / A=AGU / P=prefetch / O=atomic）。族决定 L1 的
# 合法观察点，故 cache 结构事件（cache_access …）不得冒充非 cache 族的 L1。
_UNIT_FAMILY = {"T": "tlb", "L": "lq", "S": "sq", "C": "cache",
                "A": "agu", "P": "pf", "O": "atomic"}


def _family_of(chain_events):
    """Infer the unit family (table-9 path / L1 identity differ per family)."""
    for evt in chain_events:
        run_id = evt.get("run_id", "")
        fam = _UNIT_FAMILY.get(run_id[:1])
        if fam:
            return fam
        if evt.get("kind", "") in _TLB_SIGNATURE_KINDS:
            return "tlb"
    return "generic"


def _obs_layer_of(evt, family="generic"):
    """Observation layer of a kind (family-specific map).  Independent of the
    D1 L5 promotion below, so prefix proofs keep working for detection
    events (whose observation layer is L2 for the T-series)."""
    kind = evt.get("kind", "")
    if family == "tlb":
        return _TLB_KIND_LAYER.get(kind)
    return P.KIND_LAYER.get(kind)


def _layer_of(evt, family="generic"):
    # [R6-GATE-D1] 生命周期 chain_end 不占任何层级；真实检测事件占 L5
    # （检测/结局层，spec 表 9 "L5 检测/结局"）。
    if evt.get("kind", "") in _LIFECYCLE_KINDS:
        return None
    if _explicit_l5(evt):
        return "L5"
    return _obs_layer_of(evt, family)


def _tick(evt):
    try:
        return int(evt.get("tick", "0") or 0)
    except ValueError:
        return 0


def _group_by_fault(events):
    """按 fault_id 分组（fault_id=0 的非链事件不参与链证明）。"""
    groups = {}
    for e in events:
        fid = e.get("fault_id", "")
        if not fid or fid == "0":
            continue
        groups.setdefault(fid, []).append(e)
    return groups


def _ancestry(evt, by_id):
    """Return root→evt along parent_event_id; cycles/missing parents stop."""
    out = []
    seen = set()
    cur = evt
    while cur is not None:
        eid = cur.get("event_id", "")
        marker = eid if eid != "" else id(cur)
        if marker in seen:
            break
        seen.add(marker)
        out.append(cur)
        parent = cur.get("parent_event_id", "")
        cur = by_id.get(parent) if parent != "" else None
    out.reverse()
    return out


def _ordered_prefix(path, family):
    """Select one tick-monotone L0→... subsequence from one DAG ancestry."""
    selected = []
    want = 0
    last_tick = -1
    for evt in path:
        layer = _layer_of(evt, family)
        if layer not in LAYERS:
            continue
        idx = LAYERS.index(layer)
        tick = _tick(evt)
        if idx == want and tick >= last_tick:
            selected.append(evt)
            want += 1
            last_tick = tick
            if want == len(LAYERS):
                break
    return selected


def _walk_best_ordered_path(chain_events, family):
    """Best contiguous layer prefix on any single parent DAG ancestry.

    这是**逐事件祖先遍历**的参考实现（Θ(n·depth)）：对每个事件各做一次
    `_ancestry` + `_ordered_prefix`。它是 `_best_ordered_path` 的语义基准
    （等价性由 tests/test_lsu_chain_check.py [20] 逐条钉死），也是线性实现
    在**无法证明等价**的输入（重复非空 event_id、父图有环）上的回退。
    """
    by_id = {e.get("event_id", ""): e for e in chain_events
             if e.get("event_id", "") != ""}
    best = []
    for evt in chain_events:
        selected = _ordered_prefix(_ancestry(evt, by_id), family)
        if len(selected) > len(best):
            best = selected
    return best


class _ChainCycle(Exception):
    """父图有环（`_ancestry` 的 seen-set 会在此截断，线性稳态不存在）。"""


def _linear_best_ordered_path(chain_events, family):
    """O(n) 版 `_walk_best_ordered_path` —— 返回**同一批事件对象**。

    [R6-LINCHECK] 缺陷（实测）：`_walk_best_ordered_path` 对**每个事件**各做
    一次祖先遍历 ⇒ Θ(n·depth)。真实 T04 seed1（568,093 事件、祖先深度
    ≈12,800）在其上跑不完（20k 前缀实测 25.5 s，整文件 >16 CPU-分钟未完成），
    此前只有 `lsu_campaign.py` 的临时替换绕开；**权威 checker 本身仍是
    Θ(n·depth)**。这里把它正式并入权威 checker。

    原理：`_ordered_prefix` 是**前向贪心**扫描，
        ancestry(child) = ancestry(parent) + [child]
    ⇒   prefix(child)  = step(prefix_state(parent), child)
    状态 = (下一层下标, 上一见证 tick, 已选事件元组)。对父 DAG 做一次
    记忆化自底向上传播即得每个事件祖先的前缀，均摊 O(1)；胜者仍取**原始
    列表序中第一个达到最大长度**者（`>` 而非 `>=`），故并列与
    `path_event_ids` / 由 `path[-1]` 导出的终局都与旧实现一致。

    复用本模块自身的 `LAYERS` / `_layer_of` / `_tick`，层映射不可能漂移；
    只有搜索策略改变。**正确性不依赖优化可适用**：任何可能不等价的输入
    （链内出现两个不同对象携带同一非空 event_id —— 旧 `_ancestry` 的
    seen-set 以 event_id 为标记；或父图有环）一律回退 `_walk_best_ordered_path`。
    """
    n_layers = len(LAYERS)
    by_id = {}
    for e in chain_events:
        eid = e.get("event_id", "")
        if eid == "":
            continue
        prev = by_id.get(eid)
        if prev is not None and prev is not e:
            # 同一 event_id 对应两个不同对象：`_ancestry` 的 event_id 标记
            # 语义与 id() 稳态不等价 —— 交由参考实现（绝不猜测）。
            return _walk_best_ordered_path(chain_events, family)
        by_id[eid] = e
    state = {}          # id(evt) -> (want_layer_idx, last_tick, selected_tuple)
    busy = set()

    def resolve(evt):
        stack = []
        cur = evt
        while True:
            key = id(cur)
            st = state.get(key)
            if st is not None:
                break
            if key in busy:               # 环：`_ancestry` 会在此截断
                raise _ChainCycle()
            busy.add(key)
            stack.append(cur)
            pid = cur.get("parent_event_id", "")
            nxt = by_id.get(pid) if pid != "" else None
            if nxt is None:
                st = (0, -1, ())          # 根：`_ordered_prefix` 的初态
                break
            cur = nxt
        while stack:
            node = stack.pop()
            want, last_tick, sel = st
            if want < n_layers:           # `_ordered_prefix` 满层即止
                layer = _layer_of(node, family)
                if layer in LAYERS:
                    idx = LAYERS.index(layer)
                    tick = _tick(node)
                    if idx == want and tick >= last_tick:
                        st = (want + 1, tick, sel + (node,))
            state[id(node)] = st
            busy.discard(id(node))
        return st

    best = []
    for e in chain_events:
        try:
            sel = resolve(e)[2]
        except _ChainCycle:
            return _walk_best_ordered_path(chain_events, family)
        if len(sel) > len(best):
            best = sel
    return list(best)


def _best_ordered_path(chain_events, family):
    """Best contiguous layer prefix on any single parent DAG ancestry.

    [R6-LINCHECK] 入口 = O(n) 线性搜索；仅在可证不等价时才回退参考实现
    （见 `_linear_best_ordered_path`）。语义与旧的 Θ(n·depth) 遍历逐条一致。
    """
    return _linear_best_ordered_path(chain_events, family)


def _event_has_prefix(chain_events, target, family):
    """Whether target descends from a contiguous L0..target-layer prefix.

    [R6-GATE-D1] Uses the *observation* layer of the target (not the L5
    promotion) so a detection event is still proven to descend from the
    unit's own L0→L_obs prefix.
    """
    layer = _obs_layer_of(target, family)
    if layer not in LAYERS:
        return False
    target_idx = LAYERS.index(layer)
    by_id = {e.get("event_id", ""): e for e in chain_events
             if e.get("event_id", "") != ""}
    ancestry = _ancestry(target, by_id)
    # The target itself is the witness of its own observation layer, so the
    # monotone prefix only needs to reach target_idx - 1 before it (D1: a
    # promoted detection event must not disqualify itself from being prefixed).
    selected = _ordered_prefix([e for e in ancestry if e is not target], family)
    if len(selected) < target_idx:
        return False
    if target_idx == 0:
        return True
    return _tick(target) >= _tick(selected[target_idx - 1])


def _errant_commit_escape(chain_events, family, by_id, path):
    """[MDSPEC][R6-T11B] 同一链上是否存在"以 errant_commit 收口的可证连续
    L0→L5 单祖先路径"（真逃逸终局，规格终局 (1)）。

    用户裁决 2026-10-25c：errant_commit 逃逸证据**压过** contain-by-squash
    证据（终局 (2)/(3)）——否则错误提交的样本会被 squash_masked 事件改标
    detected_contained 并经 containment 准入（READY 虚增）。两类等价证据：

      * (a) 所选最佳路径自身经 errant_commit 收口（与 `_terminal` 的 full
        判据同源：path[-1] 是显式 L5 检测事件，且其单祖先上含 errant_commit）；
      * (b) 任一 errant_commit 检测事件把一条单祖先连续 L0→L5 前缀收口
        （其祖先含 L0..L4 见证）——不依赖路径选择的先到先得，防止并列
        长度下 squash 支路抢先掩住真逃逸支路。

    悬空 errant_commit（死分支、祖先无 L4 见证 ⇒ 前缀止于 L0..L3，
    T02-F2-W4 seed2 的 event 83）不收口任何链 ⇒ 不阻断 squash 路径。
    oracle=Crash 单独不构成否决：Crash 姐妹样本经 full 链正常准入，
    oracle 结局本身不是逃逸证据。
    """
    # (a) 所选最佳路径的 full 判据（与下方 deepest=="L5" 分支同源）
    if path and len(path) == len(LAYERS):
        chosen = _ancestry(path[-1], by_id)
        if (any(e.get("kind") in _L4_TERMINAL_KINDS for e in chosen)
                and _explicit_l5(path[-1])):
            return True
    # (b) 任一 errant_commit 检测事件收口一条连续 L0→L5 前缀
    for e in chain_events:
        if e.get("kind", "") != "errant_commit" or not _explicit_l5(e):
            continue
        if len(_ordered_prefix(_ancestry(e, by_id), family)) == len(LAYERS):
            return True
    return False


def _edges_for(chain_events, family):
    """Prove edges only from one contiguous, tick-monotone DAG path."""
    path = _best_ordered_path(chain_events, family)
    by_layer = {}
    for evt in path:
        by_layer[_layer_of(evt, family)] = [evt]
    edges = {}
    for i in range(len(LAYERS) - 1):
        a, b = LAYERS[i], LAYERS[i + 1]
        proven = len(path) > i + 1
        edges[f"{a}->{b}"] = "proven" if proven else "missing"
        if proven:
            e1, e2 = path[i], path[i + 1]
            shared = ["fault_id", "parent_event_path"]
            if (e1.get("dyn_inst_seq") and e2.get("dyn_inst_seq")
                    and e1["dyn_inst_seq"] == e2["dyn_inst_seq"]):
                shared.append("dyn_inst_seq")
            edges[f"{a}->{b}_witness"] = {
                "from": f"{a}:{e1.get('kind')}@t{e1.get('tick')}",
                "to": f"{b}:{e2.get('kind')}@t{e2.get('tick')}",
                "shared_keys": shared,
            }
    return edges, by_layer, path


def _terminal(chain_events, edges, by_layer, path, family,
              oracle_outcome=None):
    """终止判定（规格三终局 + Unknown 兜底；缺席不猜测）。

    [H2-fix] tlb_fault = Hardware 检测，表示**翻译阶段阻断**，它本身
    **不是**终局：不得据此无条件写 contained=1。终局由"翻译阻断证据 +
    runner/oracle 结局（L5 五类）"联合决定：

      oracle=Crash/Timeout/SDC  → <kind>_translation_blocked（闭合：确实
                                  产生了错误结局，翻译阻断是其机理）
      oracle=Detected/Contained → detected_contained（闭合）
      oracle=Masked（oracle 干净）→ provable_to_L2_then_unknown
                                  （**绝不**因 oracle 干净就推断 Masked/
                                  Contained —— 规格表 9 判定列钉死）
      oracle 缺失/INCONCLUSIVE  → detected_translation_outcome_pending
                                  （开放，beyond=Unknown）

    "Handled"（guest 自行处理翻译故障后继续）在本事件流内**不可判别**
    ——干净 oracle 无法区分"被吸收"与"没造成影响"，故只能标 Unknown
    （诚实：不引入不可观测的语义）。
    """
    translation_blocked = False
    for e in chain_events:
        if (e.get("kind") == "tlb_fault"
                and e.get("detection_layer") == "Hardware"
                and _event_has_prefix(chain_events, e, family)):
            translation_blocked = True
            if e.get("contained") == "1":
                # 显式 contained 证据（非推断）优先于 oracle 兜底
                return "detected_contained"
    if translation_blocked:
        if oracle_outcome in ("Crash", "Timeout", "SDC"):
            return f"{oracle_outcome.lower()}_translation_blocked"
        if oracle_outcome == "Detected/Contained":
            return "detected_contained"
        if oracle_outcome in ("Masked",):
            # oracle 干净 ≠ 链完整 ≠ Masked：只按可证层级报告
            pass
        else:
            return "detected_translation_outcome_pending"
    # 显式 contained 检测（L5 证据事件）
    # [R6-FIXB] 这里必须用 **_explicit_l5**（真实检测事件：非生命周期 kind +
    # detection_layer + outcome + 链关联 corr），而不是读**原始**
    # `detection_layer`/`contained`。旧口径会把退出回调发射的 chain_end 自带的
    # `contained=1`（corr=none，无关联语义）当成含住证据——P6 实证：真实
    # T01-F0-W4/seed2 里 errant_commit(dl=L5 outcome=errant_commit corr=taint_prop)
    # 已足以证明 full，却被 chain_end(contained=1) 拉低成 detected_contained；
    # 删除 chain_end 即翻回 full。生命周期标记绝不参与终局判定。
    # [MDSPEC][R6-T11B] errant_commit 优先权护栏（用户裁决 2026-10-25c）：
    # 同一链上存在"以 errant_commit 收口的可证 L0→L5 路径"（真逃逸）时，
    # **squash 类**含住证据（squash/replay/mask，即 contain-by-squash）让位
    # ——逃逸证据压过 contain-by-squash，防 READY 虚增。悬空 errant_commit
    # 不收口任何链、不触发本护栏（见 _errant_commit_escape）。
    # 作用域**只限 squash 类**：其它收口证据（如 tlb_fault/tlb_translate_result
    # 的翻译阻断、walk_refill_lost 等）与逃逸证据互不隶属，行为保持原样，
    # 不做无根据地扩大（避免把合法含住样本一并拉下）。
    by_id = {e.get("event_id", ""): e for e in chain_events
             if e.get("event_id", "") != ""}
    errant_escape = _errant_commit_escape(chain_events, family, by_id, path)
    for e in chain_events:
        if (str(e.get("contained", "")).strip() in _CONTAINED_VALUES
                and _explicit_l5(e)
                and _event_has_prefix(chain_events, e, family)):
            if errant_escape and _is_squash_witness(e):
                continue          # squash 含住让位于真逃逸（见上）
            return "detected_contained"
    # 显式 squash/replay/mask（L5 证据事件）—— 真逃逸在场时整体让位
    if not errant_escape:
        for e in chain_events:
            if (_is_squash_witness(e)
                    and _event_has_prefix(chain_events, e, family)):
                return "squash_replay_masked"
    # 逐边最深可证层级
    deepest = LAYERS[len(path) - 1] if path else None
    if deepest is None:
        return "no_l0_fault_applied"
    # full（规格终局 1：到达 errant commit + 显式链终局）要求 L0→L5
    # 全路径连续。abort 样本若没有 chain_end，就只能诚实停在 L4；不得
    # 单靠 errant_commit 补造 L5。
    # The ordered prefix records only one representative per layer (often a
    # taint_reg for L4), so inspect the chosen L5 event's ancestry for the
    # errant_commit rather than requiring it to be that representative.  This
    # still forbids cross-branch splicing: both witnesses are on one ancestry.
    l4_terminal = False
    explicit_l5 = False
    if deepest == "L5":
        chosen_ancestry = _ancestry(path[-1], by_id)
        l4_terminal = any(e.get("kind") in _L4_TERMINAL_KINDS
                          for e in chosen_ancestry)
        explicit_l5 = _explicit_l5(path[-1])
    if deepest == "L5" and l4_terminal and explicit_l5:
        return "full"
    if deepest == "L0" and not by_layer.get("L1"):
        return "provable_to_L0_then_unknown"
    return f"provable_to_{deepest}_then_unknown"


def check_chain(events, spec_nodes=None, oracle_outcome=None):
    """主入口：events = lsu_prop_fields 解析的事件列表。

    oracle_outcome: runner/分类器的 L5 结局（Masked/Detected/Contained/
    SDC/Crash/Timeout/INCONCLUSIVE），用于把"翻译阶段阻断"join 成终局。
    缺省 None ⇒ 翻译阻断保持 pending（不猜测）。

    返回 {faults: {fault_id: {edges, terminal, provable_to, beyond}},
          spec_nodes, oracle_outcome}。
    """
    result = {"faults": {}, "spec_nodes": spec_nodes or LAYERS,
              "oracle_outcome": oracle_outcome}
    for fid, chain in _group_by_fault(events).items():
        family = _family_of(chain)
        edges, by_layer, path = _edges_for(chain, family)
        term = _terminal(chain, edges, by_layer, path, family, oracle_outcome)
        provable = LAYERS[len(path) - 1] if path else None
        result["faults"][fid] = {
            "edges": edges,
            "terminal": term,
            "provable_to": provable,
            # beyond=Unknown 仅用于开放终局（"可证至 Ln 后未知" / 翻译阻断
            # 待 join）；闭合终局 beyond 为空——链已收敛，无"后续未知"。
            # 绝不 Masked。
            "beyond": "" if term in CLOSED_TERMINALS else "Unknown",
            "event_count": len(chain),
            "family": family,
            "path_event_ids": [e.get("event_id", "") for e in path],
        }
    return result


# ==================================================================== R6-GATE
# Formal-admission HARD GATE (Agent B, R6).  `check_chain` proves edges and
# reports an honest terminal; `check_admission` turns that into a binding
# admission verdict for one *activated* sample so that `ready_contract.json`
# can never mark a RunID READY on the strength of `activated=1`, `RC=0`, or a
# bare `chain_end`.  An activated sample is admitted ONLY IF either
#   (1) a family-specific COMPLETE L0→L5 chain on one parent-event DAG, or
#   (2) propagation stops at a layer with an explicit containment layer +
#       reason + per-layer metrics, and every later layer is N/A(contained).
# Everything else fails LOUDLY with a named rule (see GATE_VIOLATIONS).
GATE_VIOLATIONS = (
    "unknown_in_activated_chain",
    "tlb_l1_faked_by_cache_access",
    "tlb_l1_missing",
    "cache_access_faked_l1",
    "cache_l1_missing",
    "cross_branch_edge",
    "cross_request_edge",
    "time_reversed_edge",
    "ready_by_activated_only",
    "ready_by_rc0",
    "ready_by_chain_end_only",
    "missing_mandatory_metric",
    "contained_without_later_na",
    "no_closed_chain_and_no_containment",
    # [R6-FIXB] 含住主张须建立在**完整收口**的证据流上（缺陷 #5：T06/T08-F0-W4
    # 的 prop_evt 流被 abort 截断，却据此判含住准入）。
    "containment_on_unclosed_stream",
    "containment_on_truncated_stream",
    # [MDSPEC][R6-T11B] 真 errant_commit 逃逸压过 contain-by-squash：同一链另有
    # "以 errant_commit 收口的可证 L0→L5 路径"时，squash 类含住不得据此准入
    # （防 READY 虚增；见用户裁决 2026-10-25c）。
    "errant_escape_outranks_containment",
    # [MDSPEC][R6-FIXA2] cross-request lineage bridge missing/malformed/
    # unverifiable — the ONLY legal carrier of a request transition, so a bad
    # one is a named hard-gate failure (never a silent pass, never a loosened
    # cross_request_edge rule).
    "invalid_lineage_bridge",
    # [MDSPEC][R6-FIXTOOLS] a consumer_summary record that is malformed / has
    # negative counts / does not conserve is a named hard-gate failure. A
    # summary NEVER counts as L5/containment/terminal and never becomes a
    # parent-ancestry node (it is not a PROP-EVT and carries no event_id); it
    # only carries the aggregation accounting for repeated consumers.
    "malformed_consumer_summary",
)


def consumer_summary_accounting(summaries, summary_issues=None):
    """[MDSPEC][R6-FIXTOOLS] Aggregate the consumer_summary records of one run.

    Returns {n_summaries, emitted_events, suppressed_consumers, logical_total,
             distinct_dyn_seq, conservation, issues}. `conservation` is "ok"
    only when every record validates AND the batch totals conserve
    (suppressed + emitted == logical_total); otherwise "violation". An empty
    summary list is the honest "no aggregation happened" case (conservation
    "n/a", zeros) — never a silent pass of a bad record.
    """
    issues = list(summary_issues or [])
    if not summaries:
        return {"n_summaries": 0, "emitted_events": 0,
                "suppressed_consumers": 0, "logical_total": 0,
                "distinct_dyn_seq": None,
                "conservation": "n/a" if not issues else "violation",
                "issues": issues}
    emitted = suppressed = total = 0
    distinct = 0
    for s in summaries:
        try:
            emitted += int(str(s.get("emitted_consumer_count", "0") or 0))
            suppressed += int(str(s.get("suppressed_consumer_count", "0") or 0))
            total += int(str(s.get("total_before", "0") or 0))
            distinct += int(str(s.get("distinct_dyn_seq_count", "0") or 0))
        except (TypeError, ValueError):
            issues.append("consumer_summary_accounting: 非整数计数字段")
    ok = (not issues) and (emitted + suppressed == total)
    if emitted + suppressed != total:
        issues.append("consumer_summary_accounting: 批次不守恒 "
                      f"emitted({emitted})+suppressed({suppressed}) != "
                      f"logical_total({total})")
    return {"n_summaries": len(summaries), "emitted_events": emitted,
            "suppressed_consumers": suppressed, "logical_total": total,
            "distinct_dyn_seq": distinct,
            "conservation": "ok" if ok else "violation", "issues": issues}


# cache/memory kinds that must never stand in for the TLB family's L1 DTLB
# lookup (table 9 T-series L1 is the post-injection lookup observation).
_FORCED_L1_KINDS = frozenset({
    "cache_access", "cache_return", "cache_fill", "cache_evict",
    "mshr_alloc", "mshr_merge", "mshr_fill", "mshr_free", "mshr_busy",
    "mshr_arb", "cache_writeback",
})

# Per-layer mandatory metrics: a field that MUST be present (non-empty) on the
# layer's witness on the admitted path.  Absence is a LOUD failure, never a
# silent zero.  "default" applies to every family; family keys override.
MANDATORY_METRICS = {
    "default": {
        "L0": ("fault_id", "event_id"),
        "L1": ("event_id",),
        "L2": ("event_id",),
        "L3": ("event_id",),
        "L4": ("event_id",),
        "L5": ("outcome", "detection_layer", "contained"),
    },
    # Table 9 T-series: L1 must carry the DTLB lookup payload, L2 the PA.
    "tlb": {
        "L1": ("event_id", "dyn_inst_seq", "field", "state_before",
               "state_after"),
        "L2": ("event_id", "va"),
    },
}


def _metrics_for(family):
    tbl = dict(MANDATORY_METRICS["default"])
    if family in MANDATORY_METRICS:
        tbl.update(MANDATORY_METRICS[family])
    return tbl


def _has_unknown(events):
    """Any Unknown evidence in an activated sample (mission-forbidden #1)."""
    for e in events:
        if e.get("fault_id", "") in ("", "0"):
            continue
        if e.get("kind") == "unknown":
            return e
        if str(e.get("evidence_status", "")).strip().lower() == "unknown":
            return e
    return None


def _layer_spans(chain_events, family):
    """min/max tick per layer over the whole chain event set."""
    lo, hi = {}, {}
    for e in chain_events:
        layer = _layer_of(e, family)
        if layer not in LAYERS:
            continue
        t = _tick(e)
        if layer not in lo or t < lo[layer]:
            lo[layer] = t
        if layer not in hi or t > hi[layer]:
            hi[layer] = t
    return lo, hi


def _legacy_edge_count(chain_events, family):
    """Edge count a pairwise (DAG-blind) checker would prove: two witnesses of
    adjacent layers are joined whenever their ticks are non-decreasing."""
    lo, hi = _layer_spans(chain_events, family)
    n = 0
    for i in range(len(LAYERS) - 1):
        a, b = LAYERS[i], LAYERS[i + 1]
        if a in lo and b in hi and lo[a] <= hi[b]:
            n += 1
        else:
            break
    return n


def _deepest_index(chain_events, family):
    return max((LAYERS.index(_layer_of(e, family)) for e in chain_events
                if _layer_of(e, family) in LAYERS), default=-1)


def _splice_detected(chain_events, family, path):
    """True when pairwise joining proves more edges than the single DAG path
    can, i.e. the 'chain' is stitched from witness events on different
    branches (mission-forbidden #3, cross-branch case)."""
    dag = len(path) - 1
    if dag >= _deepest_index(chain_events, family):
        return False
    return _legacy_edge_count(chain_events, family) > dag


def _creq_mismatch(e1, e2):
    """Adjacent witnesses claiming different request identities (both stamped,
    non-zero) => cross-request stitch (mission-forbidden #3)."""
    r1 = str(e1.get("request_id", "")).strip()
    r2 = str(e2.get("request_id", "")).strip()
    return (r1 != "" and r2 != "" and r1 != "0" and r2 != "0" and r1 != r2)


# ---------------------------------------------------------------------------
# [MDSPEC][R6-FIXA2] Explicit lineage bridge (kind=request_fork).
#
# Ruling A (R6-RULINGS-20261023): a chosen ancestry may cross a request
# identity boundary in EXACTLY TWO ways — (i) a normal parent edge whose two
# witnesses share the same stamped request_id, or (ii) an edge carried by a
# fully specified, source-verifiable bridge event.  Everything else stays
# `cross_request_edge` (never a silent pass, never a loosened gate).
#
# A bridge is whitelisted ONLY when all of the following hold (each failure is
# reported loudly as `invalid_lineage_bridge`):
#   * every mandatory field is present and non-empty;
#   * source_event_id / dest_event_id resolve to REAL events of this chain;
#   * the DAG is actually connected: bridge.parent_event_id == source_event_id
#     and dest_event.parent_event_id == bridge.event_id;
#   * the endpoints really are the declared requests (source_event.request_id ==
#     old_request_id, dest_event.request_id == new_request_id, old != new);
#   * chain identity (fault_id, corr) and the bridge layer match the
#     destination event — drift between the emitter's map and this checker's
#     map is DETECTED, not silently tolerated;
#   * the declared shared propagation object [shared_addr, +shared_size) is
#     really addressed by BOTH endpoint events (the verifiable evidence that
#     the two requests are reading the same polluted object).
_BRIDGE_KINDS = frozenset({"request_fork", "lineage_bridge"})
_BRIDGE_FIELDS = ("fault_id", "corr", "old_request_id", "new_request_id",
                  "source_event_id", "dest_event_id", "bridge_layer",
                  "bridge_reason", "shared_addr", "shared_size")


def _hexint(value):
    """Parse a hex address field; None when absent/unparsable."""
    s = str(value).strip()
    if not s:
        return None
    try:
        return int(s, 16)
    except ValueError:
        return None


def _evt_in_range(evt, base, size):
    """Does `evt` address [base, base+size) through any of its own address
    fields?  This is how the bridge's declared shared object is *verified*
    against real event evidence (never trusted from the bridge alone)."""
    if size <= 0:
        return False
    hi = base + size
    for key in ("va", "pa", "cache_line"):
        v = _hexint(evt.get(key, ""))
        if v is not None and base <= v < hi:
            return True
    return False


def _validate_bridges(chain_events, by_id, family):
    """Return ({event_id: bridge}, [issue...]) for every bridge in the chain.

    Only bridges in the returned map may carry a request transition.
    """
    valid, issues = {}, []
    for eid, b in sorted((e.get("event_id", ""), e)
                         for e in chain_events
                         if e.get("kind", "") in _BRIDGE_KINDS):
        miss = [f for f in _BRIDGE_FIELDS if not str(b.get(f, "")).strip()]
        if miss:
            issues.append(f"invalid_lineage_bridge: bridge {eid} 缺必录字段 "
                          f"{miss}——假 bridge 不得放行跨请求边")
            continue
        src = by_id.get(str(b.get("source_event_id", "")))
        dst = by_id.get(str(b.get("dest_event_id", "")))
        if src is None or dst is None:
            issues.append(f"invalid_lineage_bridge: bridge {eid} 声明的来源/"
                          f"目标事件不存在（source_event_id="
                          f"{b.get('source_event_id')!r} dest_event_id="
                          f"{b.get('dest_event_id')!r}）——不得放行跨请求边")
            continue
        if (str(b.get("parent_event_id", "")) != str(b["source_event_id"])
                or str(dst.get("parent_event_id", "")) != str(eid)):
            issues.append(f"invalid_lineage_bridge: bridge {eid} 与 source/dest "
                          f"事件的父子边不连（parent={b.get('parent_event_id')!r}"
                          f" dest.parent={dst.get('parent_event_id')!r}）")
            continue
        if str(b["old_request_id"]) == str(b["new_request_id"]):
            issues.append(f"invalid_lineage_bridge: bridge {eid} 两端 request_id "
                          f"相同（{b['old_request_id']!r}）——非跨请求，不得充当 bridge")
            continue
        if str(src.get("request_id", "")).strip() != str(b["old_request_id"]).strip():
            issues.append(f"invalid_lineage_bridge: bridge {eid} source 事件 "
                          f"{b['source_event_id']} 实际 request_id="
                          f"{src.get('request_id')!r}≠old_request_id="
                          f"{b['old_request_id']!r}")
            continue
        if str(dst.get("request_id", "")).strip() != str(b["new_request_id"]).strip():
            issues.append(f"invalid_lineage_bridge: bridge {eid} dest 事件 "
                          f"{b['dest_event_id']} 实际 request_id="
                          f"{dst.get('request_id')!r}≠new_request_id="
                          f"{b['new_request_id']!r}")
            continue
        if (str(b["fault_id"]).strip() != str(dst.get("fault_id", "")).strip()
                or str(b["corr"]).strip() != str(dst.get("corr", "")).strip()):
            issues.append(f"invalid_lineage_bridge: bridge {eid} chain identity "
                          f"与目标事件不一致（fault_id={b['fault_id']!r}"
                          f"/corr={b['corr']!r} vs 目标 fault_id="
                          f"{dst.get('fault_id')!r}/corr={dst.get('corr')!r}）")
            continue
        if str(b["bridge_layer"]).strip() != str(_obs_layer_of(dst, family) or ""):
            issues.append(f"invalid_lineage_bridge: bridge {eid} 声明层 "
                          f"{b['bridge_layer']!r}≠目标事件观察层 "
                          f"{_obs_layer_of(dst, family)!r}")
            continue
        base, size = _hexint(b["shared_addr"]), _hexint(b["shared_size"])
        if base is None or size is None or size <= 0:
            issues.append(f"invalid_lineage_bridge: bridge {eid} 共享对象区间非法"
                          f"（shared_addr={b['shared_addr']!r} shared_size="
                          f"{b['shared_size']!r}）")
            continue
        if not _evt_in_range(src, base, size):
            issues.append(f"invalid_lineage_bridge: bridge {eid} 声明的共享对象 "
                          f"[{base:#x},+{size:#x}) 未被 source 事件 "
                          f"{b['source_event_id']} 实际访问——来源不可核验")
            continue
        if not _evt_in_range(dst, base, size):
            issues.append(f"invalid_lineage_bridge: bridge {eid} 声明的共享对象 "
                          f"[{base:#x},+{size:#x}) 未被 dest 事件 "
                          f"{b['dest_event_id']} 实际访问——地址/line 不一致")
            continue
        valid[eid] = b
    return valid, issues


def _carried_by_bridge(e1, e2, ancestry, valid_bridges):
    """True when the ancestry segment e1..e2 contains a VALIDATED bridge that
    carries e1's request to e2's request — the only legal way to cross a
    request identity boundary."""
    if not valid_bridges:
        return False
    ids = [e.get("event_id", "") for e in ancestry]
    try:
        i, j = ids.index(e1.get("event_id", "")), ids.index(e2.get("event_id", ""))
    except ValueError:
        return False
    if j < i:
        i, j = j, i
    for k in range(i, j):
        b = valid_bridges.get(ancestry[k].get("event_id", ""))
        if b is None:
            continue
        if (str(b.get("dest_event_id", "")) == str(ancestry[k + 1].get("event_id", ""))
                and str(b.get("new_request_id", "")).strip()
                == str(e2.get("request_id", "")).strip()):
            return True
    return False


def _ancestry_request_breaks(chain_events, family, path, ancestry=None):
    """[R6-GATE-D3] Adjacent witnesses on the *chosen ancestry* whose stamped,
    non-zero `request_id` differs WITHOUT a validated lineage bridge carrying
    the transition.

    The per-edge check below only sees the ≤6 layer representatives, so a
    stream whose DAG walks resp(req=A) → resp(req=B) → … under one fault_id
    slipped through (real T04: event 47 req=304 → event 48 req=310, both L3).
    Walking the whole ancestry catches cross-request stitching anywhere on the
    proven path (mission-forbidden #3).
    """
    if not path:
        return []
    by_id = {e.get("event_id", ""): e for e in chain_events
             if e.get("event_id", "") != ""}
    anc = ancestry if ancestry is not None else _ancestry(path[-1], by_id)
    valid, _ = _validate_bridges(chain_events, by_id, family)
    return [(a, b) for a, b in zip(anc, anc[1:])
            if _creq_mismatch(a, b)
            and not _carried_by_bridge(a, b, anc, valid)]
    """[R6-GATE-D3] Adjacent witnesses on the *chosen ancestry* whose stamped,
    non-zero `request_id` differs.

    The per-edge check below only sees the ≤6 layer representatives, so a
    stream whose DAG walks resp(req=A) → resp(req=B) → … under one fault_id
    slipped through (real T04: event 47 req=304 → event 48 req=310, both L3).
    Walking the whole ancestry catches cross-request stitching anywhere on the
    proven path (mission-forbidden #3).
    """
    if not path:
        return []
    by_id = {e.get("event_id", ""): e for e in chain_events
             if e.get("event_id", "") != ""}
    anc = _ancestry(path[-1], by_id)
    return [(a, b) for a, b in zip(anc, anc[1:]) if _creq_mismatch(a, b)]


def _time_reversed_gap(chain_events, family, path):
    """A deeper-layer witness whose tick precedes the last proven witness =
    reversed-in-time stitch (mission-forbidden #3)."""
    if not path:
        return None
    deepest = _deepest_index(chain_events, family)
    if len(path) - 1 >= deepest:
        return None
    b = LAYERS[len(path)]                 # first missing layer of the prefix
    ta = _tick(path[-1])
    by_layer = {}
    for e in chain_events:
        if _layer_of(e, family) == b:
            by_layer.setdefault(b, []).append(e)
    if any(_tick(e) < ta for e in by_layer.get(b, [])):
        return (f"time_reversed_edge: {b} 见证 tick 早于已证 {LAYERS[len(path) - 1]}"
                f" 见证（{ta}）——逆时拼接禁止")
    return None


def _truncated_flag(bundle):
    """[R6-FIXB] 调用方（读流方）是否已判定证据流被截断。

    兼容 `truncated` / `evidence_truncated`（lsu_prop_fields.read_events 的
    截断旗标、campaign 的 evidence_truncated 记号）两种既有命名；缺省 False
    ⇒ 由带内收口标记（chain_end 有无）自证，绝不静默放行。
    """
    for k in ("truncated", "evidence_truncated"):
        if bundle.get(k):
            return True
    return False


def _containment_issues(bundle, run_id):
    """Option-2 containment: returns issue list, or None when not claimed."""
    c = bundle.get("containment")
    if not isinstance(c, dict):
        return None
    issues = []
    layer = str(c.get("layer", ""))
    if layer not in LAYERS:
        issues.append(f"contained_without_later_na: {run_id} containment.layer="
                      f"{layer!r} 非法（须 ∈ {LAYERS}）")
    else:
        later = LAYERS[LAYERS.index(layer) + 1:]
        na = [str(x) for x in (c.get("na_layers") or [])]
        if sorted(na) != sorted(later):
            issues.append(f"contained_without_later_na: {run_id} containment"
                          f".layer={layer} 后续层必须全部 N/A(contained) 且等于"
                          f" {later}，实录 na_layers={na}")
    if not str(c.get("reason", "")).strip():
        issues.append(f"missing_mandatory_metric: {run_id} containment 缺 reason"
                      f"（显式含住理由为必录）")
    m = c.get("metrics")
    if not isinstance(m, dict) or not m:
        issues.append(f"missing_mandatory_metric: {run_id} containment 缺逐层"
                      f"指标 metrics")
    return issues


def _stream_closed(chain_events):
    """[R6-FIXB] 证据流是否以**生命周期标记** chain_end 收口。

    chain_end 由 CHAOSPropagation 的**退出回调**发射（每故障链一条），所以
    "该链有没有 chain_end"恰好等价于"该样本是否走到正常退出"——C++ 侧铁证
    （CHAOSPropagation.cc 的 emitDetectSignal 注释）："a crash/abort sample
    never reaches the exit callback, **so the gz chain_end is absent**"。
    真实 T06/T08-F0-W4 的 prop_evt 流即 abort 截断（read_events → truncated=True），
    故无 chain_end。

    含住（"故障止于 Ln，之后无传播"）是对**缺席**的断言——只有流本身完整时
    才可证。未经收口的流无法区分"更深的层未出现"与"证据被截断"。
    """
    return any(e.get("kind", "") in _LIFECYCLE_KINDS for e in chain_events)


def _key_evidence_ok(evt):
    """[R6-FIXB] 零字节关键证据护栏：见证必须有事件身份 + 类型 + 检测载荷。

    缺 event_id / kind / detection_layer / outcome 的"空壳"事件不得充当
    含住见证（零字节关键证据不得准入）。
    """
    return all(str(evt.get(f, "")).strip()
               for f in ("event_id", "kind", "detection_layer", "outcome"))


def _obs_deepest_index(chain_events, family):
    """最深的**观测层**索引（生命周期标记链末 chain_end 不占层、不计入）。

    [R6-FIXB] 含住主张的"之后无更深传播"判定必须用观测层且排除生命周期标记：
    chain_end 是退出回调的收口标记（`_obs_layer_of` 的 kind 映射表里虽写着
    L5，语义上不占层）。旧口径把 chain_end 当成 L5 更深见证 ⇒ **已收口的
    正常样本反而永远无法证明含住**（只有截断样本"没有 chain_end"才解得开）
    ——这本身正是缺陷 #5 的另一面。
    """
    return max((LAYERS.index(l) for l in
                (_obs_layer_of(x, family) for x in chain_events
                 if x.get("kind", "") not in _LIFECYCLE_KINDS)
                if l in LAYERS), default=-1)


def _containment_candidate(chain_events, family):
    """[R6-FIXB] 返回**本该**支撑含住主张的真实检测事件（或 None）。

    判定与 `containment_from_events` 完全一致（contained + _explicit_l5 +
    关键证据齐 + 前缀可证 + 无更深层见证），**只差"流已收口/未截断"这一条**。
    用途：当束拿不出来时，用来把拒绝理由**响亮**地点名是"流未收口/被截断"
    而不是"根本没有含住证据"。
    """
    for e in chain_events:
        if str(e.get("contained", "")).strip() not in _CONTAINED_VALUES:
            continue
        if not _explicit_l5(e) or not _key_evidence_ok(e):
            continue
        if not _event_has_prefix(chain_events, e, family):
            continue
        layer = _obs_layer_of(e, family)
        if layer not in LAYERS:
            continue
        if _obs_deepest_index(chain_events, family) > LAYERS.index(layer):
            # 该层之后仍有见证 ⇒ 传播并未止于此，含住主张不成立
            continue
        return e
    return None


def containment_from_events(events, run_id="?", fault_id=None, truncated=False):
    """[R6-GATE-D2] 由**显式证据**推导 option-2 containment 束（绝不猜测）。

    合法含住证据 = 某事件 contained=1 且满足 `_explicit_l5`（真实检测事件：
    **非生命周期 kind** + 非空 detection_layer + 非空 outcome + 链关联 corr），
    关键字段齐备（非零字节），且该事件确实从单元自身 L0→L_obs 前缀可证
    （_event_has_prefix），且**没有**更深的层见证（否则故障并未止于该层——
    含住主张不成立），且**证据流已收口**（存在生命周期 chain_end，且调用方
    未标记 truncated）——对"之后无传播"的断言只在完整流上可证。

    [R6-FIXB] 生命周期 chain_end 恒不满足 `_explicit_l5`（corr=none），故
    "chain_end 制造含住"由构造堵死；截断/未收口流一律返回 None。
    返回 {layer, reason, metrics, na_layers} 或 None（无证据/主张不成立）。
    """
    return _containment_for_fault(events, run_id, fault_id, truncated)


def _containment_for_fault(events, run_id, fault_id=None, truncated=False):
    """[0202-T02F2] **单 fault** 的显式含住束（唯一实现）。

    取证只在本 fault 自己的链上进行，绝不跨 fault 取用证据。`fault_id=None` 仅在
    流内**恰有一个** activated fault 时可用；多 fault 时返回 None ——"事件数最多"
    的选择在多 fault 下无定义，调用方必须显式给出 fault_id（禁止静默重选，这正是
    本轮修掉的三处不一致之一）。
    """
    faults = _group_by_fault(events)
    if not faults:
        return None
    if fault_id is not None and fault_id in faults:
        fid, chain = fault_id, faults[fault_id]
    elif fault_id is None and len(faults) == 1:
        fid, chain = next(iter(faults.items()))
    else:
        return None          # 多 fault 且未指明 ⇒ 拒绝静默重选
    family = _family_of(chain)
    if truncated or not _stream_closed(chain):
        return None
    e = _containment_candidate(chain, family)
    if e is None:
        return None
    # [MDSPEC][R6-T11B] contain-by-squash 让位于真逃逸（用户裁决 2026-10-25c）：
    # 同一链另有"以 errant_commit 收口的可证 L0→L5 路径"时，squash 类含住
    # 束一律不产出——否则该样本会被贴着 `contained` 路径准入（READY 虚增）。
    # 悬空 errant_commit 不触发（见 `_errant_commit_escape`）。
    if _is_squash_witness(e):
        by_id = {x.get("event_id", ""): x for x in chain
                 if x.get("event_id", "") != ""}
        path = _best_ordered_path(chain, family)
        if _errant_commit_escape(chain, family, by_id, path):
            return None
    layer = _obs_layer_of(e, family)
    return {
        "layer": layer,
        "reason": (f"{run_id} fault {fid} 显式含住：kind={e.get('kind')} "
                   f"field={e.get('field', '')!r} detection_layer="
                   f"{e.get('detection_layer')} outcome={e.get('outcome')}"),
        "metrics": {layer: {"kind": e.get("kind", ""),
                            "field": e.get("field", ""),
                            "outcome": e.get("outcome", ""),
                            "contained": e.get("contained", ""),
                            "event_id": e.get("event_id", ""),
                            "tick": e.get("tick", "")}},
        "na_layers": LAYERS[LAYERS.index(layer) + 1:],
    }


def _missing_metrics(path, family):
    tbl = _metrics_for(family)
    out = []
    for evt in path:
        layer = _layer_of(evt, family)
        for f in tbl.get(layer, ()):
            if not str(evt.get(f, "")).strip():
                out.append((layer, f, evt.get("kind")))
    return out


def _crutch_violations(res, bundle, events):
    """Name the three forbidden READY crutches when the chain is not admitted."""
    run_id = res["run_id"]
    v = res["violations"]
    v.append(f"no_closed_chain_and_no_containment: {run_id} 既无 family-specific "
             f"L0→L5 完整链，也无显式 containment——不得判 READY")
    v.append(f"ready_by_activated_only: {run_id} activated={bundle.get('activated')}"
             f" 本身不是 READY 依据（须完整链或 containment）")
    if bundle.get("rc") == 0:
        v.append(f"ready_by_rc0: {run_id} RC=0 不是 READY 依据（进程正常退出"
                 f"≠链完整）")
    if any(str(e.get("kind")) == "chain_end" for e in events):
        v.append(f"ready_by_chain_end_only: {run_id} 仅存在 chain_end 事件，"
                 f"不构成 L5 结终局证据——不得据此判 READY")


def _adjudicate_single_fault(bundle):
    """**单一 fault** 的准入裁决（内部核；不做样本级聚合）。

    [0202-T02F2] 原 `check_admission` 的主体原样保留在此 —— 它的全部逐路径检查
    （L1 冒充 / bridge / 跨 request / 逆时 / 必录指标 / 含住束校验）都建立在
    "这一个 fault 的链与路径"上，因此对**单 fault 切片**调用即得到该 fault 的
    独立裁决，无需重写任何规则。样本级 `check_admission` 在此之上做保守 `all()`。

    bundle = {run_id, activated, events (PROP-EVT list), [rc],
              [oracle_outcome], [containment], [summary_issues],
              [consumer_summary_accounting]}
    """
    run_id = str(bundle.get("run_id", "?"))
    try:
        act = int(bundle.get("activated") or 0)
    except (TypeError, ValueError):
        act = 0
    events = list(bundle.get("events") or [])
    run_id = str(bundle.get("run_id", "?"))
    try:
        act = int(bundle.get("activated") or 0)
    except (TypeError, ValueError):
        act = 0
    events = list(bundle.get("events") or [])
    res = {"run_id": run_id, "applicable": act > 0, "admitted": None,
           "path": None, "terminal": None, "family": None, "path_layers": [],
           "violations": [], "reasons": [], "n_events": len(events)}
    if act <= 0:
        res["reasons"].append("activated=0：非 activated 样本，门禁不适用")
        return res
    viol = res["violations"]
    # [MDSPEC][R6-FIXTOOLS] consumer_summary validation. A malformed /
    # negative-count / non-conserving summary is a LOUD hard-gate failure and
    # can never be masked by an otherwise-good chain (rule ④⑦). A WELL-FORMED
    # summary contributes no violation, so a small un-aggregated stream and its
    # aggregated counterpart admit identically (rule ⑤).
    for msg in (bundle.get("summary_issues") or []):
        viol.append(f"malformed_consumer_summary: {run_id} {msg}")
    acct = bundle.get("consumer_summary_accounting")
    if isinstance(acct, dict) and acct.get("conservation") == "violation":
        for msg in (acct.get("issues") or ["计数不守恒"]):
            viol.append(f"malformed_consumer_summary: {run_id} {msg}")
    u = _has_unknown(events)
    if u is not None:
        viol.append(f"unknown_in_activated_chain: {run_id} activated={act} 存在"
                    f" Unknown 事件 kind={u.get('kind')!r} event_id="
                    f"{u.get('event_id')!r}——activated 样本中任何 Unknown 一律"
                    f"不得 READY")
    verdict = check_chain(events, oracle_outcome=bundle.get("oracle_outcome"))
    faults = verdict["faults"]
    if not faults:
        _crutch_violations(res, bundle, events)
        res["admitted"] = False
        return res
    fid, f = max(faults.items(),
                 key=lambda kv: len(kv[1]["path_event_ids"]))
    family = f["family"]
    res["terminal"] = f["terminal"]
    res["family"] = family
    chain = [e for e in events if e.get("fault_id", "") == fid]
    path = _best_ordered_path(chain, family)
    res["path_layers"] = [_layer_of(e, family) for e in path]

    # (2) L1 impersonation — family-specific, loud.
    l1 = next((e for e in path if _layer_of(e, family) == "L1"), None)
    l1kind = l1.get("kind") if l1 else None
    if family == "tlb":
        if l1kind != "tlb_lookup":
            imp = sorted({e.get("kind") for e in chain
                          if e.get("kind") in _FORCED_L1_KINDS})
            if imp:
                viol.append(f"tlb_l1_faked_by_cache_access: {run_id} TLB 族 L1 "
                            f"必须为 tlb_lookup，实际 L1={l1kind!r}；cache 族事件"
                            f" {imp} 不得冒充 DTLB lookup")
            else:
                viol.append(f"tlb_l1_missing: {run_id} TLB 族缺 tlb_lookup L1"
                            f"（实际 L1={l1kind!r}）")
    elif family == "cache":
        # [R6-GATE-D4] cache 族（H4 表 9：L1=lookup）L1 必须是 cache_access。
        if l1kind != "cache_access":
            viol.append(f"cache_l1_missing: {run_id} cache 族 L1 必须为 "
                        f"cache_access（lookup），实际 L1={l1kind!r}")
    elif l1kind in _FORCED_L1_KINDS:
        # [R6-GATE-D4] 非 cache 族的 L1 是单元自身的观察点（lsq_push /
        # addr_form / pf_train / exmon_monitor …）；cache 结构事件不得冒充。
        viol.append(f"cache_access_faked_l1: {run_id} {family} 族 L1 不得由 "
                    f"cache 结构事件冒充（实际 L1={l1kind!r}）——表 9 该族 L1 是"
                    f"单元自身观察点")

    # (3) edge stitching integrity — branch / request / time.
    # [MDSPEC][R6-FIXA2] Lineage bridges are validated FIRST; only a fully
    # specified, source-verifiable bridge may carry a request transition, and
    # every rejected bridge is named loudly (never silently ignored).
    by_id = {e.get("event_id", ""): e for e in chain
             if e.get("event_id", "") != ""}
    chosen_ancestry = _ancestry(path[-1], by_id) if path else []
    valid_bridges, bridge_issues = _validate_bridges(chain, by_id, family)
    viol.extend(bridge_issues)
    if _splice_detected(chain, family, path):
        viol.append(f"cross_branch_edge: {run_id} fault {fid} 成对拼接比单 DAG "
                    f"路径多证出边——边见证分散在多个分支，禁止跨分支拼接")
    for i in range(len(path) - 1):
        e1, e2 = path[i], path[i + 1]
        lay = f"{LAYERS[i]}->{LAYERS[i + 1]}"
        if _creq_mismatch(e1, e2) and not _carried_by_bridge(
                e1, e2, chosen_ancestry, valid_bridges):
            viol.append(f"cross_request_edge: {run_id} fault {fid} {lay} 见证 "
                        f"request_id 不一致（{e1.get('request_id')!r}≠"
                        f"{e2.get('request_id')!r}）——禁止跨请求拼接")
        if _tick(e2) < _tick(e1):
            viol.append(f"time_reversed_edge: {run_id} fault {fid} {lay} 见证"
                        f"时间倒挂（{_tick(e1)}→{_tick(e2)}）——禁止逆时拼接")
    tr = _time_reversed_gap(chain, family, path)
    if tr:
        viol.append(f"{tr}（{run_id} fault {fid}）")
    # [R6-GATE-D3] 跨请求拼接：整条所选祖先上任意相邻见证 request_id 不一致。
    breaks = _ancestry_request_breaks(chain, family, path,
                                     ancestry=chosen_ancestry)
    if breaks:
        a, b = breaks[0]
        viol.append(f"cross_request_edge: {run_id} fault {fid} 所选祖先上 "
                    f"{len(breaks)} 处相邻见证 request_id 不一致（首例 event "
                    f"{a.get('event_id')}:{a.get('kind')} req="
                    f"{a.get('request_id')!r} → event {b.get('event_id')}:"
                    f"{b.get('kind')} req={b.get('request_id')!r}）——整条祖先"
                    f"禁止跨请求拼接")

    # (4) per-layer mandatory metrics on the proven path — LOUD when missing.
    for layer, field, kind in _missing_metrics(path, family):
        viol.append(f"missing_mandatory_metric: {run_id} fault {fid} {layer} 见证"
                    f" kind={kind!r} 缺必录指标 '{field}'——逐层指标缺失必须"
                    f"响亮失败")

    # (1)/(2) admission decision.
    opt1 = (f["terminal"] == "full")
    cont_issues = _containment_issues(bundle, run_id) or []
    claimed = isinstance(bundle.get("containment"), dict)
    # [R6-FIXB] 含住主张（含调用方自带的束）须建立在**完整收口**的证据流上：
    # 截断流（gzip EOF / 零字节关键证据，调用方显式标记）或未经 chain_end
    # 收口的流（abort 样本）一律不得凭 containment 准入，且**响亮**点名。
    # 不给 full 链添此限制（full 由真实检测事件 + 全边可证给出，与收口无关）。
    if not opt1 and (claimed or _containment_candidate(chain, family)
                     is not None):
        # [MDSPEC][R6-T11B] 真逃逸压过 contain-by-squash（用户裁决
        # 2026-10-25c）：同一链存在"以 errant_commit 收口的可证 L0→L5 路径"
        # 时，**squash 类**含住不得充当准入依据（否则错误提交的样本被贴着
        # `contained` 路径准入 = READY 虚增）。opt1（full）不受影响——真逃逸
        # 样本经 full 链正常准入。悬空 errant_commit 不触发（见
        # `_errant_commit_escape`）；非 squash 类含住（翻译阻断等）保持原状。
        _cand = _containment_candidate(chain, family)
        _esc = None
        if _cand is not None and _is_squash_witness(_cand):
            _by_id = {e.get("event_id", ""): e for e in chain
                      if e.get("event_id", "") != ""}
            _esc = _errant_commit_escape(chain, family, _by_id, path)
        if _esc:
            cont_issues.append(
                f"errant_escape_outranks_containment: {run_id} fault {fid} 同一链"
                f"存在以 errant_commit 收口的可证 L0→L5 逃逸路径——逃逸证据压过"
                f" contain-by-squash，squash 含住不得据此准入")
        elif _truncated_flag(bundle):
            cont_issues.append(
                f"containment_on_truncated_stream: {run_id} 证据流被标记为截断"
                f"（gzip EOF / 零字节关键证据）——含住是对'该层之后无传播'的"
                f"断言，截断流上不可证，不得据此准入")
        elif not _stream_closed(chain):
            cont_issues.append(
                f"containment_on_unclosed_stream: {run_id} fault {fid} 存在显式"
                f"含住检测证据，但证据流未经生命周期 chain_end 收口（崩溃/"
                f"截断样本：exit 回调未运行 ⇒ chain_end 缺失）——'之后无传播'"
                f"不可证，不得据此准入")
    if cont_issues:
        viol.extend(cont_issues)
    opt2 = claimed and not cont_issues
    if opt1:
        res["path"] = "full_chain"
    elif opt2:
        res["path"] = "contained"
    else:
        _crutch_violations(res, bundle, events)
    res["admitted"] = bool((opt1 or opt2) and not viol)
    return res


def evaluate_faults(events, run_id="?", truncated=False, oracle_outcome=None,
                    summary_issues=None, consumer_summary_accounting=None,
                    chain_fn=None, containment_override=None, rc=None):
    """[0202-T02F2] **逐个 activated fault 独立评估**（唯一来源）。

    对一个运行里出现的每个 `fault_id`（≠0），**只切出该 fault 自己的事件**评估：
      - `terminal` / `provable_to` / `edges`（来自 check_chain 的逐 fault 判定）；
      - `selected_ancestry`：从该 fault 自己的 `inj` 到最深可证事件的连续父链；
      - `containment`：只由该 fault 自己的链派生的显式含住束（`_containment_for_fault`）；
      - `admission`：该 fault 独立成立（完整 L0→L5 **或** 合法显式含住）且自身无违规；
      - `violations`。
    绝不跨 fault 取用证据（切片即隔离）。
    """
    _chain = chain_fn or check_chain
    groups = _group_by_fault(events)
    # [兼容] 调用方显式提供的单一含住束只在**单 fault** 流上生效（历史行为逐字节
    # 保持）；多 fault 下它二义，`evaluate_sample` 会改用逐 fault 派生并留痕。
    _single = len(groups) == 1
    out = {}
    for fid in sorted(groups, key=lambda k: int(k) if str(k).isdigit() else 1 << 30):
        chain = groups[fid]
        verdict = _chain(chain, oracle_outcome=oracle_outcome)
        f = verdict["faults"].get(fid, {})
        family = f.get("family") or _family_of(chain)
        if _single and isinstance(containment_override, dict):
            cont = containment_override
        else:
            cont = _containment_for_fault(chain, run_id, fid, truncated)
        r = _adjudicate_single_fault({
            "run_id": run_id, "activated": 1, "events": chain,
            "oracle_outcome": oracle_outcome, "containment": cont,
            # 截断旗标与 rc 必须传进**单 fault 核**：两者都是历史响亮违规
            # （containment_on_truncated_stream / ready_by_rc0）的触发条件。
            "truncated": bool(truncated), "rc": rc,
            "summary_issues": summary_issues,
            "consumer_summary_accounting": consumer_summary_accounting})
        by_id = {e.get("event_id", ""): e for e in chain if e.get("event_id", "") != ""}
        # 祖先链取自**判定所用的那条路径**（path_event_ids 的末事件回溯），因此
        # 与顶层 terminal 同源，且自动继承调用方选定的路径实现（如 campaign 的
        # 线性 check_chain_fast），不再重复跑一遍 _best_ordered_path。
        pids = list(f.get("path_event_ids") or [])
        last = pids[-1] if pids else None
        anc = _ancestry(by_id[last], by_id) if (last and last in by_id) else []
        out[str(fid)] = {
            "fault_id": str(fid),
            "activated": any(e.get("kind") == "inj" for e in chain),
            "n_events": len(chain),
            "terminal": f.get("terminal"),
            "provable_to": f.get("provable_to"),
            "beyond": f.get("beyond"),
            "edges": {k: v for k, v in (f.get("edges") or {}).items()
                      if not k.endswith("_witness")},
            "family": family,
            # 历史准入排序键：已证有序路径长度（path_event_ids），保留以让顶层
            # 选择与旧行为逐字节一致（祖先链深度是另一个量，不可混用）。
            "n_path": len(f.get("path_event_ids") or []),
            "path_event_ids": list(f.get("path_event_ids") or []),
            "selected_ancestry": [
                {"event_id": e.get("event_id", ""), "kind": e.get("kind", ""),
                 "parent_event_id": e.get("parent_event_id", ""),
                 "request_id": e.get("request_id", ""),
                 "corr": e.get("corr", "")} for e in anc],
            "ancestry_root_is_own_inj": bool(anc) and anc[0].get("kind") == "inj",
            "contained": cont is not None,
            "containment": cont,
            "admission": bool(r.get("admitted")),
            "path": r.get("path"),
            "path_layers": r.get("path_layers") or [],
            "violations": list(r.get("violations") or []),
            "reasons": list(r.get("reasons") or []),
        }
    return out


def evaluate_sample(events, run_id="?", truncated=False, oracle_outcome=None,
                    summary_issues=None, consumer_summary_accounting=None,
                    caller_containment=None, chain_fn=None, rc=None):
    """[0202-T02F2] 样本级裁决 = **所有 activated fault 的 `all()`**。

    保守口径（用户 2026-10-27 规则）：任一个实际 activated fault 既未形成连续
    parent-event 的完整 L0→L5，也未形成真实、非 lifecycle、字段完整的提前含住，
    则整个样本 **不得 admitted**。禁止"任选一条通过即可"。

    顶层 `terminal` 取**最长可证路径那个 fault** 的 terminal（一条固定的、写明的
    规则，与准入排序同源），不再使用 `sorted(faults)[0]` 那种与准入不同的选择器。
    """
    per = evaluate_faults(events, run_id=run_id, truncated=truncated,
                          oracle_outcome=oracle_outcome,
                          summary_issues=summary_issues,
                          consumer_summary_accounting=consumer_summary_accounting,
                          chain_fn=chain_fn,
                          containment_override=caller_containment, rc=rc)
    act = [f for f in per.values() if f["activated"]]
    viol, reasons = [], []
    for f in act:
        viol.extend(f["violations"])
        reasons.extend(f["reasons"])
    # 样本级检查（与单 fault 时代一致，作用于整条流）
    u = _has_unknown(events)
    if u is not None:
        viol.append(f"unknown_in_activated_chain: {run_id} 存在 Unknown 事件 "
                    f"kind={u.get('kind')!r} event_id={u.get('event_id')!r}——"
                    f"activated 样本中任何 Unknown 一律不得 READY")
    for msg in (summary_issues or []):
        viol.append(f"malformed_consumer_summary: {run_id} {msg}")
    if isinstance(consumer_summary_accounting, dict) and \
            consumer_summary_accounting.get("conservation") == "violation":
        for msg in (consumer_summary_accounting.get("issues") or ["计数不守恒"]):
            viol.append(f"malformed_consumer_summary: {run_id} {msg}")
    # 有事件却没有 inj 的 fault 组：不正常，响亮记录（不静默忽略）
    for f in per.values():
        if not f["activated"] and f["n_events"]:
            viol.append(f"fault_without_inj: {run_id} fault {f['fault_id']} 有 "
                        f"{f['n_events']} 条事件但无 inj（非 activated fault 却出现在链里）")
    if len(act) > 1 and isinstance(caller_containment, dict):
        reasons.append("caller_containment_ignored_multifault: 多 fault 样本下调用方"
                       "提供的单一含住束二义，已改用逐 fault 派生（禁止静默重选）")
    admitted = bool(act) and all(f["admission"] for f in act) and not viol
    if not act:
        admitted = False
        reasons.append("no_activated_fault: 流内没有 activated fault")
    # 顶层选择：**已证有序路径最长**的 activated fault —— 与历史准入排序键逐字一致
    # （旧代码：max(faults.items(), key=len(path_event_ids))；平局取先出现者）。
    ranked = sorted(act, key=lambda f: (-f.get("n_path", 0), f["fault_id"]))
    top = ranked[0] if ranked else None
    # 顶层 `path` 与 `terminal` 同源（最长可证路径那个 fault），不使用与准入不同的
    # 选择器；逐 fault 的真实闭合方式在 `per_fault`（mixed 情况下顶层只是一个抓手）。
    if admitted and top is not None:
        path = "full_chain" if top["terminal"] == "full" else "contained"
    else:
        path = None
    return {
        "run_id": run_id,
        "n_events": len(events),
        "activated_faults": [f["fault_id"] for f in act],
        "per_fault": per,
        "admitted": admitted,
        "path": path,
        "terminal": (top or {}).get("terminal"),
        "provable_to": (top or {}).get("provable_to"),
        "beyond": (top or {}).get("beyond"),
        "top_fault_id": (top or {}).get("fault_id"),
        "family": (top or {}).get("family"),
        "path_layers": (top or {}).get("path_layers") or [],
        "violations": viol,
        "reasons": reasons,
        "all_activated_faults_closed": bool(act) and all(f["admission"] for f in act),
    }


def check_admission(bundle):
    """Hard gate verdict for ONE activated sample（**保守 `all()`** 版本）。

    [0202-T02F2] 改为消费 `evaluate_sample` 的 per-fault 结果：样本 admitted 当且仅当
    **每个 activated fault** 都独立闭合（完整 L0→L5 或合法显式含住）且无违规。
    返回键集与历史一致（run_id/applicable/admitted/path/terminal/family/
    path_layers/violations/reasons/n_events）；per-fault 细节在 `evaluate_sample`。
    """
    run_id = str(bundle.get("run_id", "?"))
    try:
        act = int(bundle.get("activated") or 0)
    except (TypeError, ValueError):
        act = 0
    events = list(bundle.get("events") or [])
    if act <= 0:
        return {"run_id": run_id, "applicable": False, "admitted": None,
                "path": None, "terminal": None, "family": None,
                "path_layers": [], "violations": [],
                "reasons": ["activated=0：非 activated 样本，门禁不适用"],
                "n_events": len(events)}
    ev = evaluate_sample(events, run_id=run_id,
                         truncated=_truncated_flag(bundle),
                         oracle_outcome=bundle.get("oracle_outcome"),
                         summary_issues=bundle.get("summary_issues"),
                         consumer_summary_accounting=bundle.get("consumer_summary_accounting"),
                         caller_containment=bundle.get("containment"),
                         rc=bundle.get("rc"))
    return {"run_id": run_id, "applicable": True, "admitted": ev["admitted"],
            "path": ev["path"], "terminal": ev["terminal"], "family": ev["family"],
            "path_layers": ev["path_layers"], "violations": ev["violations"],
            "reasons": ev["reasons"], "n_events": ev["n_events"]}


def main():
    if len(sys.argv) < 2:
        print("usage: lsu_chain_check.py <prop_evt.txt[.gz]> [--run-id X] "
              "[--oracle-outcome Masked|SDC|Crash|Timeout|"
              "Detected/Contained]", file=sys.stderr)
        return 2
    argv = sys.argv[1:]
    oracle = None
    if "--oracle-outcome" in argv:
        i = argv.index("--oracle-outcome")
        oracle = argv[i + 1]
        del argv[i:i + 2]
    path = Path(argv[0])
    events, truncated = P.read_events(path)
    verdict = check_chain(events, oracle_outcome=oracle)
    verdict["truncated_stream"] = truncated
    verdict["total_events"] = len(events)
    print(json.dumps(verdict, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
