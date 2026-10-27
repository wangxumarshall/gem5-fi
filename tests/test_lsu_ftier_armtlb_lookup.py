#!/usr/bin/env python3
"""[MDSPEC][R6-FTIER] armtlb lookup-mode F 档位契约（不跑仿真）。

缺陷（实测，2026-10-24）：首波 6 个 RunID
  `T01-F0-W4`、`T02-F0-W4`、`T02-F2-W4`、`T04-F0-W4`、`T04-F2-W4`、`T04-F6-W4`
两两**归一化命令行完全相同** —— `resolve_cell` 的 armtlb 分支只对
`WALK_FAULT_TYPES` 追加 `--tlb_lsu_tier`（T02/T04 是 bit_flip /
pfn_to_mapped_page，走 lookup 路径），F 列被整列丢弃，6 格坍缩成 3 个
"独立实验条件"。

两半修复：
  (a) C++（R6-FIXCPP 6ec7c5aa）：CHAOSArmTLB 的 lookup 命中路径新增真实
      gate（lookupTierMounted / lookupTierAllowsInjection），F1-F6 不再
      "半接线"，F0 保持 legacy maxFaults/probability 路径。
  (b) 工具（R6-FIXTOOLS）：本套件钉住的解析侧契约 —— F0 走 legacy（无
      tier 旗标），F1-F6 传真实 `--tlb_lsu_tier <F>`，未知档位响亮 BLOCKED。
      F1-F6 的**运行时可信性**另由 CHAOS_LSU_TIER_CAP 能力标记 + campaign
      核对保证（见 tests/test_lsu_r6_lookup_ftier_tooling.py）。

本套件钉四件事：
  ① 六格不再产出彼此相同的可跑命令；
  ② campaign 为 armtlb 产出的每个 flag 都是运行配置**真能读**的 argparse 选项；
  ③ F0 保持 legacy（无 --tlb_lsu_tier，--tlb_max_faults 1）；
  ④ 未知档位必须**显式 BLOCKED**，理由点名档位，绝不伪装已运行。

用法：python3 tests/test_lsu_ftier_armtlb_lookup.py   （exit 0 = 全 PASS）
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


def _cell(model, freq, runid, wl="TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页）"):
    row = [""] * 12
    row[LC.COL_RUNID] = runid
    row[LC.COL_MODEL] = model
    row[LC.COL_UNIT] = "L1d-TLB"
    row[LC.COL_FREQ] = freq
    row[LC.COL_WORKLOAD] = wl
    return row


def _norm(flags):
    """归一化命令行 = 逐 token 的 flags 元组（None = 该格不产出可跑命令）。"""
    return None if flags is None else tuple(flags)


SIX = [("T01", "F0"), ("T02", "F0"), ("T02", "F2"),
       ("T04", "F0"), ("T04", "F2"), ("T04", "F6")]
SIX_RUNIDS = [f"{m}-{f}-W4" for m, f in SIX]


def main():
    print("[1] 六格不再有彼此相同的可跑命令")
    res = {}
    for (m, f), rid in zip(SIX, SIX_RUNIDS):
        flags, _g, why = LC.resolve_cell(_cell(m, f, rid))
        res[rid] = (flags, why)
        print(f"      {rid}: " + ("runnable" if flags is not None
                                  else f"BLOCKED({(why or '')[:60]}…)"))
    norms = [_norm(res[r][0]) for r in SIX_RUNIDS]
    runnable = [r for r in SIX_RUNIDS if res[r][0] is not None]
    distinct = {n for n in norms if n is not None}
    check("六格里没有两格产出相同的可跑命令"
          f"（runnable={len(runnable)}, distinct={len(distinct)}）",
          len(distinct) == len(runnable),
          f"norms={norms}")

    print("[2] F2/F6 逐格传真实 --tlb_lsu_tier（值 = 请求档位）")
    for rid, want in (("T02-F2-W4", "F2"), ("T04-F2-W4", "F2"),
                      ("T04-F6-W4", "F6")):
        fl = res[rid][0] or []
        i = fl.index("--tlb_lsu_tier") if "--tlb_lsu_tier" in fl else -1
        check(f"{rid} 带 --tlb_lsu_tier {want}", i >= 0 and fl[i + 1] == want,
              str(fl[-6:]))

    print("[3] 反向：F2/F6 不得悄悄改档成 F0（静默退化检查）")
    for rid, f0rid in (("T02-F2-W4", "T02-F0-W4"), ("T04-F2-W4", "T04-F0-W4"),
                       ("T04-F6-W4", "T04-F0-W4")):
        check(f"{rid} 的命令 != {f0rid} 的命令（非静默改档）",
              _norm(res[rid][0]) != _norm(res[f0rid][0]),
              f"{res[rid][0][-4:]} vs {res[f0rid][0][-4:]}")

    print("[4] 未知档位（F7/off）显式 BLOCKED，理由点名 lookup-tier（不伪装）")
    for rid, m, f in (("T04-F7-W4", "T04", "F7"), ("T02-off-W4", "T02", "off")):
        _fl, _g, why = LC.resolve_cell(_cell(m, f, rid))
        why = why or ""
        check(f"{rid} BLOCKED 且理由含 armtlb-lookup-tier-unimplemented 及档位",
              _fl is None and "armtlb-lookup-tier-unimplemented" in why
              and f in why, why[:120])
        check(f"{rid} 理由不是错误的 'mode unimplemented'/不适用",
              not why.startswith("deferred(mode unimplemented")
              and not why.startswith("不适用"), why[:80])

    print("[5] armtlb 产出的每个 flag 都是运行配置真能读的 argparse 选项")
    fs_py = (ROOT / "configs/se/arm_chaos_fs.py").read_text(encoding="utf-8")
    known = set(re.findall(r'add_argument\("(--[A-Za-z0-9_-]+)"', fs_py))
    check("解析到 arm_chaos_fs.py 的 argparse 选项", len(known) > 20,
          str(sorted(known)[:5]))
    check("--tlb_lsu_tier 是真选项（lookup/walk 路径的 tier 确实被读）",
          "--tlb_lsu_tier" in known)
    emitted = set()
    for (m, f), rid in zip(SIX, SIX_RUNIDS):
        flags = res[rid][0]
        if flags:
            emitted |= {t for t in flags if t.startswith("--")}
    # T08 walk 路径（tier 的另一消费者）
    # [R6-PROPAGATION-V3] W9 is a hard workload gap; use the explicit
    # T08-a canary (W4 F0) to exercise the walk/tier routing.
    t08 = LC.resolve_cell(_cell("T08", "F0", "T08-F0-W4",
                                "TLB-AliasPerm 地址翻译探针"),
                          t08a_canary=True)[0] or []
    emitted |= {t for t in t08 if t.startswith("--")}
    unknown = sorted(t for t in emitted if t not in known)
    check(f"armtlb flags 全部是已知选项（unknown={unknown}）", not unknown,
          str(unknown))
    check("T08 walk 路径确实带 --tlb_lsu_tier（tier 的真消费者）",
          "--tlb_lsu_tier" in t08 and "F0" in t08, str(t08[-8:]))

    print("[6] lookup 的 F0 保持 legacy（maxFaults=1）且不带 --tlb_lsu_tier")
    for rid in ("T01-F0-W4", "T02-F0-W4", "T04-F0-W4"):
        flags = res[rid][0] or []
        i = flags.index("--tlb_max_faults") if "--tlb_max_faults" in flags else -1
        check(f"{rid} F0 = --tlb_max_faults 1（单次瞬态）",
              i >= 0 and flags[i + 1] == "1", str(flags))
        check(f"{rid} F0 不携带 --tlb_lsu_tier（逐字节 legacy）",
              "--tlb_lsu_tier" not in flags, str(flags))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
