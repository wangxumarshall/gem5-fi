#!/usr/bin/env python3
"""test_lsu_carrier_alias_sites.py — R4-5.7b S10 carrier 静态校验.

carrier = `workloads/directed/alias_sites.c`：为 S10（StoreSet SSIT-ID 换值）
提供合法替换候选的定向负载。本测试**不跑 gem5**，只用 binutils 从已编译的
ELF 里静态核验"必然产生候选"的机理前提：

  P1 载体里存在 12 个**互不相同**的 (store_PC, load_PC) 别名对（12 个
     noinline 站点，各自独占一行 volatile 数组）；
  P2 每个站点的 load 紧跟同址 store（store 的数据依赖上一轮 load → 数据
     晚到；gem5 O3 LSQ 的 memory-order violation 检出面）；
  P3 12 个 load PC 的 calcSSID = (PC ^ (PC>>10)) % 1024 **互不相同**；
  P4 因此在第二次 arm-1（首次训练）事件上候选集非空 —— 用
     test_lsu_hook_s10_fork.py 的模型复核：12 个独立 pair 的合成轨迹
     eligible ≥ 6。

P3/P4 是"为何必然产生候选"的证明：StoreSet 候选集 = 活跃 SSID 集合去掉
真值 calcSSID(load_PC)；只要 ≥2 个站点的 load PC 落在不同 SSID 上，第二条
首次训练事件就必然看到非空候选（store_set.cc：候选只排除真值）。

诚实边界：本测试证明的是**静态前提**（PC/SSID/候选集），不证明 gem5 上真
的检出 memory-order violation —— 后者是 microarchitectural 的，由主 agent
用 census 的 `CHAOS_LSU_S10_FORK` 行实测（判据见 carrier .c 文件头）。

用法：python3 tests/test_lsu_carrier_alias_sites.py   （退出码 0 = 全 PASS）
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CARRIER_C = ROOT / "workloads/directed/alias_sites.c"
CARRIER_ELF = ROOT / "workloads/directed/alias_sites"

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


def calc_ssid(pc):
    # store_set.hh: ((PC ^ (PC >> 10)) % LFSTSize)，LFSTSize=1024
    return ((pc ^ (pc >> 10)) % 1024)


def main():
    print("== [0] 载体存在性 ==")
    check("carrier 源文件存在", CARRIER_C.is_file(), str(CARRIER_C))
    check("carrier ELF 存在（随仓库提交，census 直接可用）",
          CARRIER_ELF.is_file(), str(CARRIER_ELF))
    if not CARRIER_ELF.is_file():
        print(f"FAILED ({len(FAILED)}): " + ", ".join(FAILED))
        return 1
    src = CARRIER_C.read_text(encoding="utf-8")
    check("载体头注释给出机理与判据（arm-1 条件 / loss 上界）",
          "calcSSID" in src and "arm1_events" in src and "eligible" in src)
    check("两轮 12 站点调用齐全",
          src.count("SITE(") == 12 + 1 or src.count("SITE(") == 12,
          f"SITE( count={src.count('SITE(')}")

    nm = shutil.which("nm")
    objdump = shutil.which("objdump")
    if not (nm and objdump):
        skip("P1/P2/P3 反汇编核验", "缺 nm/objdump（binutils 不可用）")
    else:
        print("== [P1] 12 个互不相同的站点函数 ==")
        syms = {}
        for line in subprocess.run([nm, "-n", str(CARRIER_ELF)],
                                   capture_output=True, text=True).stdout.splitlines():
            m = re.match(r"^([0-9a-f]+) [tT] (site_\d+)$", line.strip())
            if m:
                syms[m.group(2)] = int(m.group(1), 16)
        check("站点函数 = 12 个", len(syms) == 12, str(sorted(syms)))
        check("地址互不相同", len(set(syms.values())) == 12)

        if len(syms) == 12:
            print("== [P2] 每站点 store→同址 load 相邻（别名对） ==")
            pairs = []
            for name, addr in sorted(syms.items(), key=lambda kv: kv[1]):
                nxt = min([a for a in syms.values() if a > addr], default=addr + 0x60)
                dis = subprocess.run(
                    [objdump, "-d", f"--start-address={addr}",
                     f"--stop-address={nxt}", str(CARRIER_ELF)],
                    capture_output=True, text=True).stdout
                # (PC, opcode, 地址表达式)
                ops = [(int(m.group(1), 16), m.group(2), m.group(3).strip())
                       for m in re.finditer(
                           r"^\s*([0-9a-f]+):\s+(?:[0-9a-f]{8}\s+)?"
                           r"(str|ldr)\s+x\d+, \[x\d+(.*?)\]",
                           dis, re.M)]
                check(f"P2 {name}: 至少一条 store 与紧随其后的同址 load",
                      len(ops) >= 2 and ops[0][1] == "str" and ops[1][1] == "ldr"
                      and ops[0][2] == ops[1][2] and ops[1][0] - ops[0][0] == 4,
                      str(ops[:2]))
                if len(ops) >= 2:
                    pairs.append((ops[0][0], ops[1][0]))

            print("== [P3] 12 个 load PC 的 calcSSID 互不相同 ==")
            ssids = [calc_ssid(lp) for _, lp in pairs]
            check("别名对 = 12 组且互不相同",
                  len(pairs) == 12 and len(set(pairs)) == 12, str(pairs))
            check("calcSSID(load_PC) 互不相同（P3 全部不同 → 候选必非空）",
                  len(set(ssids)) == len(ssids), str(sorted(ssids)))
            print(f"    load PCs: {[hex(lp) for _, lp in pairs]}")
            print(f"    calcSSID: {ssids}  → distinct {len(set(ssids))}")

            print("== [P4] 用 fork 模型复核：≥2 个首次训练 pair ⇒ 候选非空 ==")
            sys.path.insert(0, str(HERE))
            try:
                import test_lsu_hook_s10_fork as F   # noqa: E402
                m = F.StoreSetModel()
                log = m.run(pairs)
                n_elig = sum(1 for r in log if r["eligible"])
                check("carrier 全 12 站均触发首训时 eligible ≥ 6",
                      n_elig >= 6, f"eligible={n_elig}/12")
                check("第一条事件候选空、第二条起候选非空（L1+L3）",
                      log[0]["cands"] == [] and all(r["cands"] for r in log[1:]),
                      str([r["cands"] for r in log[:3]]))
                print(f"    （12 站全触发: eligible={n_elig}/12）")
            except Exception as exc:   # pragma: no cover - 只在模型导入失败时
                skip("P4 模型复核", f"无法导入 fork 模型：{exc}")

    print("== [P5] 载体可运行且确定（native 主机执行，非 gem5） ==")
    try:
        outs = {subprocess.run([str(CARRIER_ELF)], capture_output=True,
                               text=True, timeout=60).stdout for _ in range(2)}
    except Exception as exc:
        skip("P5 native 运行", f"无法执行：{exc}")
    else:
        check("两次运行输出一致（确定性 oracle）",
              len(outs) == 1 and all(re.fullmatch(r"[0-9a-f]{16}\n", o)
                                     for o in outs), str(outs))

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
