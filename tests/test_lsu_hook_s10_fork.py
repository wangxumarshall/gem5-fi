#!/usr/bin/env python3
"""test_lsu_hook_s10_fork.py — [MDSPEC][R4-5.7b] S10 根因判别契约测试.

任务 R4-5.7b：定论 S10 census 的 `attempted>0（4/5）而 eligible=0` 属于四类
根因中的哪一类：

  (a) SSIT 无有效项           —— 赋值臂进入时表里没有合法条目
  (b) 没有合法替换候选        —— 有条目但都不是合法替换目标
  (c) 事件时机错误            —— 钩子触发点早于/晚于候选可解析的时刻
  (d) 负载不产生目标事件      —— 这两个负载不存在"另一个在用 store-set"

判别手段（禁跑仿真，静态为主）：把 `attempted` 与 `eligible` 的**分叉点**
逐行追出并化为对运行时状态的谓词，再对该谓词做两件事：

  [I]  用一份**忠实复刻 store_set.cc 四臂控制流**的模型（下称 "模型"，
       逐臂引用源码行），执行合成 violation 轨迹，证明三条结构引理：
       L1 运行中**第一条** training event 必然落在赋值臂且候选集为空
          （SSIT 只被 StoreSet::violation 写；见 §模型 build 注释）；
       L2 赋值臂对同一 (load_PC, store_PC) 对是**一次性**的——一旦训练过，
          该对后续 violation 走 2/3/4 臂，S10 钩子不再被调用；
       L3 `eligible>0` 的充要条件 = 存在**第二条**首次训练的 pair，且在
          其进入赋值臂时 SSIT 已持有与 calcSSID(load_PC) **不同**的活跃
          SSID（即"另一个在用 store-set"）。
  [II] 把 [I] 的结论套到两个 census 负载的**真实产物**（run.out）上：
       attempted == iew.memOrderViolationEvents（4 / 5），eligible == 0，
       与 L1/L2 一起给出定量上界 eligible ≤ attempted − 1 与
       "F2 需 eligible ≥ 50000（intervalEvents(F2)=100000 的一半）"
       这一**数学上不可能**的判定。

诚实边界：本文件的"模型"是 store_set.cc 控制流的**忠实复刻**（逐臂引用行
号），不是 gem5 仿真，也不产生任何真机证据；它证明的是**结构性引理**。
`eligible=0` 属于 (a)/(c)/(d) 中哪一支的**最终实证**由 R4-5.7b 新增的
`CHAOS_LSU_S10_FORK` 诊断行在一次 census 后给出（见 §[III] 的判读表）。

用法：python3 tests/test_lsu_hook_s10_fork.py   （退出码 0 = 全 PASS）
"""
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

FAILED = []
SKIPPED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def skip(name, reason):
    print(f"  SKIP {name} — {reason}")
    SKIPPED.append(name)


def src(path):
    return (ROOT / path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# [模型] store_set.cc StoreSet::violation 四臂控制流的忠实复刻。
#
# 逐臂行号（base 55b89900 的 CHAOS/gem5/src/cpu/o3/store_set.cc）：
#   arm1  `if (!valid_load_SSID && !valid_store_SSID)`   —— 唯一含 S10 钩子的臂
#   arm2  `else if (valid_load_SSID && !valid_store_SSID)`
#   arm3  `else if (!valid_load_SSID && valid_store_SSID)`
#   arm4  `else`                                          —— 两者皆有效，合并
# SSIT 的**唯一**写入者是本函数（insertLoad/insertStore/checkInst/issued/
# squash 都不写 SSIT；已逐函数核对）——这是引理 L1 的全部依据。
# ---------------------------------------------------------------------------

class StoreSetModel:
    """SSIT ⊆ PC→SSID；只保留控制流语义（替换策略/相联度对引理无关）。"""

    LFST_SIZE = 1024

    @staticmethod
    def calc_ssid(pc):
        # store_set.hh `calcSSID(PC) { return ((PC ^ (PC >> 10)) % LFSTSize); }`
        return ((pc ^ (pc >> 10)) % StoreSetModel.LFST_SIZE)

    def __init__(self):
        self.ssit = {}          # pc -> ssid  （仅由 violation 写）
        self.log = []           # 每次 training event 的记录

    # S10 注入侧的候选扫描（store_set.cc 内 lambda：遍历 SSIT 取 isValid）
    def live_ssids(self):
        return list(self.ssit.values())

    def violation(self, store_pc, load_pc):
        """返回一次 training event 的 (arm, eligible)。"""
        vl = load_pc in self.ssit
        vs = store_pc in self.ssit

        rec = {"store_pc": store_pc, "load_pc": load_pc,
               "arm": None, "eligible": False, "cands": []}

        if not vl and not vs:                       # ---- arm 1（S10 钩子）
            new_set = self.calc_ssid(load_pc)
            # 候选 = 活跃 SSIT 的 SSID，排除真值、去重
            cands = []
            for s in self.live_ssids():
                if s != new_set and s not in cands:
                    cands.append(s)
            rec["arm"] = 1
            rec["cands"] = cands
            # chaosS10SsidSubst 返回 false（cands 空）只**取消替换**，不取消
            # 臂 1 本身的插入——store_set.cc 在钩子之后无条件执行
            # `SSIT.findVictim + setSSID + insertEntry`（load 用 load_ssid、
            # store 用 new_set）。故本臂总是写表，eligible 不递增而已。
            if cands:
                rec["eligible"] = True     # onEligible() 在此被调用
            # 注入（或未注入）：load 条目拿 load_ssid、store 条目拿真值
            # new_set。模型只关心 SSIT 的活跃 SSID 集合，故两条目同值。
            self.ssit[load_pc] = new_set
            self.ssit[store_pc] = new_set
            self.log.append(rec)
            return rec

        if vl and not vs:                          # ---- arm 2（钩子不在）
            self.ssit[store_pc] = self.ssit[load_pc]
            rec["arm"] = 2
        elif not vl and vs:                        # ---- arm 3（钩子不在）
            self.ssit[load_pc] = self.ssit[store_pc]
            rec["arm"] = 3
        else:                                      # ---- arm 4（钩子不在）
            m = min(self.ssit[load_pc], self.ssit[store_pc])
            self.ssit[load_pc] = m
            self.ssit[store_pc] = m
            rec["arm"] = 4
        self.log.append(rec)
        return rec

    def run(self, trace):
        for store_pc, load_pc in trace:
            self.violation(store_pc, load_pc)
        return self.log


# ---------------------------------------------------------------------------
def main():
    print("== [I] 模型：store_set.cc 四臂控制流的结构引理 ==")

    # --- L1: 任何轨迹的第一条 training event 都是 arm1 且候选为空（永不 eligible）
    # 轨迹元组 = (store_pc, load_pc)（与 violation() 形参同序）。
    for name, trace in [
        ("single_pair", [(0x2000, 0x1000)] * 4),
        ("two_pairs", [(0x2000, 0x1000), (0x4000, 0x3000)]),
        ("shared_load", [(0x2000, 0x1000), (0x2000, 0x3000)]),
        ("many_pairs", [(0x9000 + 0x40 * i, 0x1000 + 0x40 * i)
                        for i in range(8)]),
    ]:
        m = StoreSetModel()
        log = m.run(trace)
        first = log[0]
        check(f"L1 {name}: 第一条 training event 落 arm1",
              first["arm"] == 1, f"arm={first['arm']}")
        check(f"L1 {name}: 第一条候选集为空 → 永不 eligible",
              first["cands"] == [] and not first["eligible"],
              f"cands={first['cands']}")

    # --- L2: 同一 (load,store) 对重复 violation → arm1 只出现一次
    m = StoreSetModel()
    m.run([(0x1000, 0x2000)] * 4)
    check("L2 同一对重复 4 次：arm1 恰好 1 次",
          sum(1 for r in m.log if r["arm"] == 1) == 1,
          str([r["arm"] for r in m.log]))
    check("L2 同一对重复 4 次：eligible 计数为 0（复现 census 观测）",
          sum(1 for r in m.log if r["eligible"]) == 0)
    check("L2 同一对重复 4 次：后续 3 次走 arm4（钩子不被调用）",
          [r["arm"] for r in m.log] == [1, 4, 4, 4],
          str([r["arm"] for r in m.log]))

    # --- L2b: 同一 store PC、不同（未训练）load PC → arm3（钩子不在该臂）
    # 轨迹元组是 (store_pc, load_pc)，与 violation() 的形参一致。
    m = StoreSetModel()
    m.run([(0x1000, 0x2000), (0x1000, 0x3000)])
    check("L2b 同 store PC、新 load PC 走 arm3（S10 钩子不在此臂）",
          [r["arm"] for r in m.log] == [1, 3], str([r["arm"] for r in m.log]))
    check("L2b 该轨迹 eligible=0（即便有两个不同 load PC）",
          sum(1 for r in m.log if r["eligible"]) == 0)

    # --- L3: 第二条「首次训练」pair（SSID 不同）→ 恰好 1 次 eligible
    m = StoreSetModel()
    m.run([(0x1000, 0x2000), (0x3000, 0x4000)])
    check("L3 两个独立 pair：arm1 出现 2 次、eligible 恰 1 次",
          sum(1 for r in m.log if r["arm"] == 1) == 2
          and sum(1 for r in m.log if r["eligible"]) == 1,
          str([(r["arm"], r["eligible"]) for r in m.log]))
    # 第一对 (store 0x1000, load 0x2000) 的赋值臂真值 = calcSSID(load 0x2000)
    # → 这就是第二对进入赋值臂时的唯一活跃 SSID、也就是它的候选集。
    check("L3 第二对的候选集 = 第一对遗留的活跃 SSID（'另一个在用 store-set'）",
          m.log[1]["cands"] == [StoreSetModel.calc_ssid(0x2000)]
          and m.log[1]["cands"] != [StoreSetModel.calc_ssid(0x4000)],
          str(m.log[1]["cands"]))

    # --- L3b: 8 个独立 pair → eligible ≥ 6（候选集随活跃 SSID 增长）
    m = StoreSetModel()
    m.run([(0x1000 + 0x40 * i, 0x9000 + 0x40 * i) for i in range(8)])
    n_elig = sum(1 for r in m.log if r["eligible"])
    check("L3b 8 个独立 pair：eligible ≥ 6（carrier 设计依据）",
          n_elig >= 6, f"eligible={n_elig}")
    print(f"    （8 独立 pair 轨迹: eligible={n_elig}/8, "
          f"arm 序列={[r['arm'] for r in m.log]}）")

    # -----------------------------------------------------------------------
    print("== [II] 真实产物：两个 census 负载的 funnel 上界 ==")
    evid = Path(os.environ.get(
        "R4_S10_EVIDENCE",
        "/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/"
        "runs/lsu/r4_t57_span"))
    TRIG_RE = re.compile(r"CHAOS_LSU_TRIGGER: injector=(\S+) tier=(\S+) "
                         r"attempted=(\d+) eligible=(\d+) injected=(\d+)")
    observed = []
    if evid.is_dir():
        for f in sorted(evid.glob("*.run.out")):
            m = TRIG_RE.search(f.read_text(errors="replace"))
            if m:
                observed.append((f.stem, int(m.group(3)), int(m.group(4)),
                                 int(m.group(5))))
    if not observed:
        skip("II 证据解析",
             f"census 产物目录不可见：{evid}（本 worktree 无 runs/；"
             "集成侧可用 R4_S10_EVIDENCE=<dir> 重跑本段）")
    for name, attempted, eligible, injected in observed:
        check(f"II {name}: eligible ≤ attempted − 1（L1 的结构上界）",
              attempted > 0 and eligible <= attempted - 1,
              f"attempted={attempted} eligible={eligible}")
        check(f"II {name}: tried>0 而 eligible=0 → S10 在该负载上无可用事件",
              attempted > 0 and eligible == 0,
              f"attempted={attempted} eligible={eligible}")
        check(f"II {name}: F2 cell 数学上不可能（需 eligible ≥ 50000）",
              attempted < 50000,
              f"attempted={attempted}")
        check(f"II {name}: F5/F0 cell 需要 eligible ≥ 1 —— 观测为 0",
              eligible == 0)
        print(f"    （{name}: attempted={attempted} eligible={eligible} "
              f"injected={injected}）")

    # -----------------------------------------------------------------------
    print("== [III] 源码钉：分叉点与诊断行不可漂移 ==")
    ss = src("CHAOS/gem5/src/cpu/o3/store_set.cc")
    arm1 = ss.index("if (!valid_load_SSID && !valid_store_SSID) {")
    arm2 = ss.index("} else if (valid_load_SSID && !valid_store_SSID) {")
    body1 = ss[arm1:arm2]
    check("III 赋值臂存在且 S10 钩子在其中（分叉点的唯一入口）",
          "chaosS10SsidSubst" in body1)
    check("III 第 2 臂无 S10 钩子（L2 的结构依据）",
          "chaosS10SsidSubst" not in
          ss[arm2:ss.index("} else if (!valid_load_SSID && valid_store_SSID) {")])
    check("III 第 3 臂无 S10 钩子（L2b 的结构依据）",
          "chaosS10SsidSubst" not in
          ss[ss.index("} else if (!valid_load_SSID && valid_store_SSID) {"):])
    # L1 的全部依据：SSIT 的写操作（insertEntry / findVictim 后的 setSSID）
    # 只出现在 StoreSet::violation 函数体内——insertLoad/insertStore/checkInst/
    # issued/squash/clear 都不写 SSIT 条目。用函数体切片证明，不用巧合计数。
    vstart = ss.index("StoreSet::violation(Addr store_PC, Addr load_PC)")
    vend = ss.index("void\nStoreSet::checkClear()")
    vbody = ss[vstart:vend]
    n_all = len(re.findall(r"SSIT\.insertEntry", ss))
    n_in = len(re.findall(r"SSIT\.insertEntry", vbody))
    check("III SSIT 的唯一写入者是 violation()（L1 的全部依据）",
          n_all > 0 and n_all == n_in,
          f"insertEntry total={n_all} in violation()={n_in}")
    check("III 赋值臂确认 calcSSID(load_PC) 为真值来源（候选排除的对象）",
          "SSID new_set = calcSSID(load_PC)" in body1)

    cw = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc")
    i_empty = cw.index("if (cands.empty()) {")
    # 只在 cands 空分支**之后**找 onEligible 调用点（文件前面有注释提到
    # onEligible，不能用作分叉点位置）。
    i_elig = cw.index("onEligible()", i_empty)
    check("III cands 空 → return false 先于 onEligible（eligible 不递增）",
          i_empty < i_elig)
    check("III cands 空分支计入 arm1_cand_empty（诊断可观测）",
          "s10_arm1_cand_empty" in cw[i_empty:i_elig])
    check("III arm1 入口计数在守卫之后（arm1_events 语义 = 钩子被调用次数）",
          cw.index("++s10_active->s10_arm1_events") < i_empty)
    check("III 诊断行 CHAOS_LSU_S10_FORK 在 exit 回调中输出（S10 模式）",
          "CHAOS_LSU_S10_FORK" in cw and "if (s10_mode) {" in cw)
    check("III 诊断不改变注入裁决（无新的 return / 无放宽候选）",
          cw[i_empty:i_elig].count("return") == 1)

    hh = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh")
    for member in ("s10_arm1_events", "s10_arm1_cand_empty",
                   "s10_arm1_cand_ok", "s10_max_live_ssids",
                   "s10_max_cands", "s10_arm1_load_pcs"):
        check(f"III 诊断成员存在：{member}", member in hh)

    # -----------------------------------------------------------------------
    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): " + ", ".join(FAILED))
        return 1
    if SKIPPED:
        print(f"ALL PASS（{len(SKIPPED)} 段 SKIP：无真机产物，未冒充实证）")
    else:
        print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
