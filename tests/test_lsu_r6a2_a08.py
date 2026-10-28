#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A3] A08-a/b 真实通道 / 同周期 EA 互换契约（先红后绿）。

旧状态（R6-A2-STATUS §2.2）：A08 未实现，campaign 仍路由 `a08_subst`
—— 那是 A04-b 同页替换的代理，不是 A08 语义。

本测试钉死真实实现必须满足的结构性契约：
  1. 两个新子模型模式 `a08_channel`（A08-a）与 `a08_pair_swap`（A08-b）
     被 config 接受，并要求 LSU trigger（事件分母）；
  2. campaign A08 路由 a08_channel，seed 奇偶切换到 a08_pair_swap，
     不再路由 a08_subst 代理；
  3. A08-a 在真实 `buildPackets()` 之后把 store 的包命令从 WriteReq
     改为 ReadReq（真实进入 packet，不是只改报告字段），保留
     inst->isLoad()==0 / request->isLoad()==0；
  4. A08-b 的 store 侧在 buildPackets 之前检查同一 4KiB 页与 paddr
     偏移保序后 `setPaddr`（split 分片同步）；
  5. 同周期配对登记在 pushRequest：同 tick、store 先于 load、
     一个 store 只配一次；跨周期缺配对/跨页/请求已结束必须 decline；
  6. 事件记录双方 seq/EA/PA/tick 与拒绝原因；
  7. 不得伪造 cross-request 关联。

用法：python3 tests/test_lsu_r6a2_a08.py （退出码 0=全 PASS）
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def read(rel):
    p = ROOT / rel
    return p.read_text() if p.exists() else ""


def main():
    cpp = read("CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc")
    chh = read("CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh")
    lsq = read("CHAOS/gem5/src/cpu/o3/lsq.cc")
    lsu_unit = read("CHAOS/gem5/src/cpu/o3/lsq_unit.cc")
    proxy = read("configs/se/lsu_proxy.py")
    camp = read("tools/lsu_campaign.py")

    print("[1] modes + config validation")
    check("proxy accepts a08_channel", '"a08_channel"' in proxy)
    check("proxy accepts a08_pair_swap", '"a08_pair_swap"' in proxy)
    check("a08 modes require the LSU trigger",
          "a08_channel" in proxy and "requires" in proxy and
          "_A08_TRIGGER_MODES" in proxy)
    check("injector ctor validates a08 modes",
          "a08_channel" in cpp and "a08_pair_swap" in cpp and
          "lsuTier" in cpp)

    print("[2] campaign routing (no proxy)")
    check("A08 route is a08_channel",
          LC.MODEL_FLAGS["A08"][1][:2] == ["--agu_pre_mode", "a08_channel"],
          str(LC.MODEL_FLAGS["A08"]))
    check("seed parity selects a08_pair_swap",
          re.search(r'if model == "A08" and seed % 2 == 0:\s*\n\s*'
                    r'[^\n]*a08_pair_swap', camp) is not None)
    check("a08_subst is no longer routed by the campaign",
          '"a08_subst"' not in camp)

    print("[3] A08-a real packet command change")
    check("channel swap applied to the built packet",
          "maybeSwapStoreChannel" in cpp and "maybeSwapStoreChannel" in chh)
    check("packet command really becomes a read",
          re.search(r"(ReadReq|MemCmd::ReadReq|createRead)", cpp) is not None)
    check("lsq_unit calls the channel hook at writeback",
          "maybeSwapStoreChannel" in lsu_unit)
    check("request/inst identity is NOT rewritten (store stays a store)",
          'inst->isLoad() =' not in cpp and
          "setIsLoad" not in cpp)

    print("[4] A08-b store-side page check + setPaddr")
    check("paddr swap hook exists",
          "maybeApplyStoreEaSwap" in cpp and
          "maybeApplyStoreEaSwap" in lsu_unit)
    check("same-4KiB-page check present",
          "0xFFF" in cpp and re.search(r">> 12|>>12", cpp) is not None)
    check("paddr offset-preservation check present",
          re.search(r"getPaddr\(\) & 0xFFF", cpp) is not None)
    check("setPaddr used for the store side",
          "setPaddr" in cpp)
    check("split fragment paddrs adjusted",
          "for (auto &r : _reqs)" in cpp or "_reqs" in cpp)

    print("[5] same-tick pairing registry")
    check("pairing keyed by tick", "curTick()" in cpp and "pair" in cpp.lower())
    check("store-before-load ordering enforced",
          "store_after_load" in cpp or "pair_order" in cpp)
    check("one store pairs at most once",
          "paired" in cpp.lower())
    check("cross-cycle decline", "cross_cycle" in cpp or "pair_missing" in cpp)
    check("cross-page decline", "cross_page" in cpp)
    check("ended-request decline",
          re.search(r"(declin\w*).*(ended|sent|squash)", cpp, re.I) is not None)

    print("[6] evidence fields")
    for fld in ("pair_tick", "load_old_ea", "store_old_ea", "old_cmd",
                "new_cmd", "decline_reason"):
        check(f"evidence field {fld}", fld in cpp)

    print("[7] no fabricated cross-request association")
    check("no cross_request_edge emitted by the model",
          "cross_request_edge" not in cpp)

    if FAILED:
        print(f"R6-A3 A08 TEST: {len(FAILED)} FAILURE(S)")
        return 1
    print("R6-A3 A08 TEST: ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
