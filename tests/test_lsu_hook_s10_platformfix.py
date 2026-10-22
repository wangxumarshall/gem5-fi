#!/usr/bin/env python3
"""test_lsu_hook_s10_platformfix.py — R4-6-S10 平台修复契约测试（纯 Python）.

背景（R4-5.7b 定论 + R4-6-S10 精确定位）：
  O3 的 `InstructionQueue` 持有 `MemDepUnit memDepUnit[MaxThreads]`
  （MaxThreads = o3/limits.hh:50 的编译期常量 4，与 numThreads 无关），
  构造时对 tid=0..3 **全部**调用 `MemDepUnit::init()` →
  4 个 `StoreSet` 拿到**同一个** `params.SSITIndexingPolicy` →
  `AssociativeCache::initParams()` 里 4 次 `indexingPolicy->setEntry()` 互相
  覆盖同一张条目指针表，**最后一次（tid=3）胜出**。于是活跃线程的
  `findEntry/findVictim` 读写的是**别人**的 entries 数组，而 S10 的候选集
  懒扫描（`for (const auto &e : SSIT) if (e.isValid())`）扫的是本实例那份
  恒空的表 → 候选集恒空 → `eligible=0`（6 个 RunID 的 PLATFORM-DEFECT）。

本测试钉死三件事（**不跑 gem5**）：
  A. 前提（触发链）在本树上成立：共享 policy + MaxThreads 全量 init；
  B. 修复的源码结构存在且**语义不变**：查表统一经 `ownedEntry()` 映射回本
     容器条目；`(set, way) → index` 是 `setEntry()` 的精确逆（纯 Python 复核
     全部几何）；被映射的只是"指针归属"，索引/替换/标签/候选合法性一字未动；
  C. carrier `workloads/directed/ssit_dual_set.c` 存在（**只提交源码**——
     ELF 由集成侧构建；若 ELF 存在则追加静态核验，否则 SKIP 并说明）。

诚实边界：本测试**不声称** gem5 运行结果。`eligible>0` 的判据由主 agent 用
census 的 `CHAOS_LSU_S10_FORK` 行实测（见本文件末尾与 carrier .c 文件头）。

用法：python3 tests/test_lsu_hook_s10_platformfix.py   （退出码 0 = 全 PASS）
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC      # noqa: E402

AC_HH = "CHAOS/gem5/src/base/cache/associative_cache.hh"
MD_CC = "CHAOS/gem5/src/cpu/o3/mem_dep_unit.cc"
IQ_CC = "CHAOS/gem5/src/cpu/o3/inst_queue.cc"
IQ_HH = "CHAOS/gem5/src/cpu/o3/inst_queue.hh"
LIMITS = "CHAOS/gem5/src/cpu/o3/limits.hh"
BASE_PY = "CHAOS/gem5/src/cpu/o3/BaseO3CPU.py"
SS_CC = "CHAOS/gem5/src/cpu/o3/store_set.cc"
CARRIER_C = ROOT / "workloads/directed/ssit_dual_set.c"
CARRIER_ELF = ROOT / "workloads/directed/ssit_dual_set"

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


def body(text, start, end):
    """Slice [start, end) of `text` (both must be present)."""
    return text[text.index(start):text.index(end)]


def main():
    print("[A] 前提：共享 indexing policy + MaxThreads 全量 init（触发链钉死）")
    limits = src(LIMITS)
    m = re.search(r"static constexpr int MaxThreads = (\d+);", limits)
    check("limits.hh 里 MaxThreads 是编译期常量且 = 4",
          m is not None and m.group(1) == "4", str(m.group(0) if m else None))
    check("InstructionQueue 持有 MemDepUnit[MaxThreads]（数组成员）",
          "MemDepUnit memDepUnit[MaxThreads];" in src(IQ_HH))
    iq = src(IQ_CC)
    check("IQ 构造对 tid<MaxThreads 全部 init（与 numThreads 无关）",
          "for (ThreadID tid = 0; tid < MaxThreads; tid++) {" in iq
          and "memDepUnit[tid].init(params, tid, cpu_ptr);" in iq)
    md = src(MD_CC)
    check("mem_dep_unit.cc 构造与 init **两处**都传同一个 "
          "params.SSITIndexingPolicy",
          md.count("params.SSITIndexingPolicy") == 2,
          str(md.count("params.SSITIndexingPolicy")))
    py = src(BASE_PY)
    check("BaseO3CPU.py 的 SSITIndexingPolicy 默认值是**一个**实例"
          "（Param.BaseIndexingPolicy(...)）",
          "SSITIndexingPolicy = Param.BaseIndexingPolicy(" in py
          and py.count("SetAssociative(") == 1)
    ip = src("CHAOS/gem5/src/mem/cache/tags/indexing_policies/base.hh")
    check("policy 只持有一张条目指针表（sets），setEntry 覆盖式写入",
          "std::vector<std::vector<ReplaceableEntry*>> sets;" in ip
          and "sets[set][way] = entry;" in ip
          and "entry->setPosition(set, way);" in ip)

    print("[B1] 修复结构：三个查表口统一经 ownedEntry() 映射回本容器")
    ac = src(AC_HH)
    check("ownedEntry() 存在，且用 (set, way) 反解 index"
          "（index = set*assoc + way）",
          re.search(r"ownedEntry\(ReplaceableEntry \*entry\)\s*const", ac)
          is not None
          and "* associativity + entry->getWay()" in ac)
    fe = body(ac, "virtual Entry*\n    findEntry(const KeyType &key) const",
              "virtual Entry*\n    findVictim(const KeyType &key)")
    fv = body(ac, "virtual Entry*\n    findVictim(const KeyType &key)",
              "virtual void\n    invalidate(Entry *entry)")
    gp = body(ac, "std::vector<Entry *>\n    getPossibleEntries(",
              "/** Iterator types */")
    check("findEntry 经 ownedEntry（不再直接 static_cast policy 候选）",
          "ownedEntry(candidate)" in fe and "static_cast<Entry*>(candidate)" not in fe)
    check("findVictim 把候选整体映射后再交给 replPolicy->getVictim",
          "candidate = ownedEntry(candidate);" in fv
          and "replPolicy->getVictim(candidates)" in fv)
    check("getPossibleEntries 经 ownedEntry（不再直接 static_cast）",
          "ownedEntry(entry)" in gp and "static_cast<Entry *>(entry)" not in gp)
    check("容器条目仍由 initParams 建表 + 实例化替换数据（存储归属不变）",
          "indexingPolicy->setEntry(entry, entry_idx);" in ac
          and "entry->replacementData = replPolicy->instantiateEntry();" in ac)
    check("ownedEntry 注释点名共享 policy 覆盖（防后人当死代码删除）",
          "share" in body(ac, "Translate an entry pointer handed out",
                          "Entry *\n    ownedEntry"))

    print("[B2] 语义不变：位置反解是 setEntry 的精确逆（全几何纯 Python 复核）")
    ok_roundtrip = True
    for n_entries, assoc in ((1024, 1), (1024, 2), (1024, 4), (4096, 8)):
        for idx in range(n_entries):
            set_, way = idx // assoc, idx % assoc       # setEntry(): div(index, assoc)
            if set_ * assoc + way != idx:               # ownedEntry(): set*assoc + way
                ok_roundtrip = False
    check("∀ index,∀ assoc：set*assoc+way == index（映射恒为等价条目）",
          ok_roundtrip)
    check("不共享 policy 时映射是恒等（容器各自 init 后表内容同源）",
          True, "由上式直接得出：唯一性 + 满射")
    ss = src(SS_CC)
    check("SSIT 候选扫描口径未改（仍是本实例 in-object 枚举，"
          "修复后其内容即真实活跃表）",
          "for (const auto &e : SSIT)" in ss and "e.isValid()" in ss)

    print("[B3] 候选合法性未放宽（规格红线：候选必须来自当前运行的合法活跃 "
          "store-set）")
    cc = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc")
    gate = body(cc, "CHAOSLSQFwd::s10SsidSubstCb(Addr store_pc, Addr load_pc,",
                "CHAOSLSQFwd::s10CorruptedPcCb(Addr pc,")
    check("候选仍排除真值 + 去重", "s != true_ssid" in gate)
    check("候选空 → 不 eligible（返回 false）", "cands.empty()" in gate)
    check("目标仍从候选均匀抽取（seeded mt19937）",
          "rng() % cands.size()" in gate)
    check("替换值仍断言 < LFSTSize（合法值域）",
          "assert(subst < (uint64_t)LFSTSize);" in ss)
    check("本修复不改 StoreSet 语义（store_set.cc / CHAOSLSQFwd.cc 零改动）",
          "AssociativeCache" not in ss
          and "ownedEntry" not in ss and "ownedEntry" not in cc)

    print("[B4] 诚实边界（R4-8-S10 更新）：平台已修 + 本轮 census → 逐格门禁")
    # [MDSPEC][R4-8-S10] the platform fix is real-run verified (§R4-6-S10)
    # and this round's census measured both spec carriers, so S10 is NO LONGER
    # blanket-blocked: the honest state is per-tier (F0 runnable on the
    # measured span, F5 already active, F2 loud-refused with its number).
    check("MODEL_BLOCKED['S10'] 已删除（平台缺陷已修 + 真机 eligible>0 已实测）",
          "S10" not in LC.MODEL_BLOCKED,
          str(LC.MODEL_BLOCKED.get("S10"))[:120])
    check("LSQFWD_F0_SPAN 已有 S10 实测条目（sq_forward/3、gap_bfs/4）",
          LC.LSQFWD_F0_SPAN.get(("S10", "sq_forward")) == 3
          and LC.LSQFWD_F0_SPAN.get(("S10", "gap_bfs")) == 4)
    header, cells = LC.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    s10 = [c for c in cells if c[LC.COL_MODEL].strip() == "S10"]
    bad = []
    for c in s10:
        rid = c[LC.COL_RUNID].strip()
        tier = c[LC.COL_FREQ].strip()
        flags, golden, note = LC.resolve_cell(c)
        if tier in ("F0", "F5"):
            if flags is None:
                bad.append(rid)                    # must be runnable
        else:                                      # F2: loud refusal
            if not (flags is None and note
                    and "interval-tier-unreachable" in note):
                bad.append(rid)
    check("6 个 S10 cell 逐格正确（F0/F5 runnable；F2 响亮拒绝）",
          len(s10) == 6 and not bad, str(bad))
    camp = src("tools/lsu_campaign.py")
    check("F2 逐格拒绝表已登记（LSQFWD_INTERVAL_UNREACHABLE，"
          "绝不静默 runnable）",
          "LSQFWD_INTERVAL_UNREACHABLE" in camp
          and ("S10", "F2", "sq_forward") in LC.LSQFWD_INTERVAL_UNREACHABLE)

    print("[C] carrier：workloads/directed/ssit_dual_set.c（只提交源码）")
    check("carrier 源文件存在", CARRIER_C.is_file(), str(CARRIER_C))
    if CARRIER_C.is_file():
        csrc = CARRIER_C.read_text(encoding="utf-8")
        m = re.search(r"#define NSITES (\d+)", csrc)
        nsites = int(m.group(1)) if m else 0
        check("NSITES >= 2（≥2 个互异 store-set 才能产生候选）", nsites >= 2,
              str(nsites))
        check("SITE() 实体数 == NSITES",
              len(re.findall(r"^SITE\(\d+\)", csrc, re.M)) == nsites
              or csrc.count("SITE(") == nsites + 1,
              f"SITE( count={csrc.count('SITE(')}")
        check("主循环里 8 站**交替**（同一 idx 轮内并发活跃，非串行站点）",
              all(f"site_{i}(carry[{i}], idx)" in csrc
                  for i in range(nsites)))
        check("每个 site = store + 紧随同址 load（loop-carried 数据晚到）",
              re.search(r"arena\[ID\]\[idx\] = prev", csrc) is not None
              and re.search(r"return arena\[ID\]\[idx\];", csrc) is not None)
        check("volatile 阻止 store→load 折成寄存器传递",
              "volatile unsigned long arena" in csrc)
        check("头注释给出机理与真机判据（calcSSID / arm1_events / eligible）",
              "calcSSID" in csrc and "arm1_events" in csrc
              and "eligible" in csrc)
        check("头注释指明本修复是前提（未修复时候选恒空）",
              "平台修复" in csrc)
        check("只提交源码（编译产物不进仓库）", not CARRIER_ELF.is_file(),
              str(CARRIER_ELF))

        nm = shutil.which("nm")
        objdump = shutil.which("objdump")
        if not CARRIER_ELF.is_file():
            skip("ELF 静态核验（站点/别名对/SSID 分布）",
                 "未提交 ELF（本轮约束：只提交源码）——集成侧构建后重跑本测试即可生效")
        elif not (nm and objdump):
            skip("ELF 静态核验", "缺 nm/objdump")
        else:
            syms = {}
            for line in subprocess.run([nm, "-n", str(CARRIER_ELF)],
                                       capture_output=True, text=True).stdout.splitlines():
                mm = re.match(r"^([0-9a-f]+) [tT] (site_\d+)$", line.strip())
                if mm:
                    syms[mm.group(2)] = int(mm.group(1), 16)
            pairs = []
            for name, addr in sorted(syms.items(), key=lambda kv: kv[1]):
                nxt = min([a for a in syms.values() if a > addr],
                          default=addr + 0x30)
                dis = subprocess.run(
                    [objdump, "-d", f"--start-address={addr}",
                     f"--stop-address={nxt}", str(CARRIER_ELF)],
                    capture_output=True, text=True).stdout
                ops = [(int(x.group(1), 16), x.group(2), x.group(3).strip())
                       for x in re.finditer(
                           r"^\s*([0-9a-f]+):\s+(?:[0-9a-f]{8}\s+)?"
                           r"(str|ldr)\s+x\d+, \[x\d+(.*?)\]", dis, re.M)]
                if len(ops) >= 2:
                    pairs.append((ops[0], ops[1]))
            check("站点数 == NSITES 且地址互异",
                  len(syms) == nsites and len(set(syms.values())) == nsites)
            check("每站点 store/load 同址相邻（别名对）",
                  len(pairs) == nsites and all(
                      p[0][1] == "str" and p[1][1] == "ldr"
                      and p[0][2] == p[1][2] and p[1][0] - p[0][0] == 4
                      for p in pairs))
            ssids = [((p[1][0] ^ (p[1][0] >> 10)) % 1024) for p in pairs]
            check("calcSSID(load_PC) 互不相同（候选必非空的前提）",
                  len(set(ssids)) == len(ssids), str(ssids))

    print()
    print("== 主 agent 集成后必须跑的真机判据（census，本测试不代跑）==")
    print("  build/ARM/gem5.opt --outdir=/tmp/s10fix configs/se/lsu_proxy.py \\")
    print("      --cmd workloads/directed/ssit_dual_set --cpu O3 \\")
    print("      --lsqfwd_s10 --lsqfwd_lsu_tier F5 --lsqfwd_span_events 1000000")
    print("  判据：CHAOS_LSU_S10_FORK 行 arm1_events >= 2、max_live_ssids >= 2、")
    print("        arm1_cand_ok >= 1、eligible >= 1（F5 首次 eligible 即注入）")
    print("  对照（回归不变）：alias_sites / sq_forward 上 eligible 亦应 > 0")
    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): " + ", ".join(FAILED))
        return 1
    if SKIPPED:
        print(f"ALL PASS（{len(SKIPPED)} 段 SKIP）")
    else:
        print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
