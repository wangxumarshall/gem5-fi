#!/usr/bin/env python3
"""A01-F0-W3 双跑确定性比较（G0-02，用户指令 §3/§4 语义级比较）。

比较项：
  C1 注入日志 addrpath_injections.log 逐字节（目标/bit/原值/故障值/时刻/L0/funnel）
  C2 gem5 stdout 规范化（剔除 banner/时间戳/路径/pid 行后）——含负载 oracle 输出
  C3 stats.txt 语义字段（剔除 host_* 主机相关字段后的 name→value 全集）
  C4 config.ini 逐字节（实验语义配置）
  C5 守卫 run-finish 退出码
判定：C1-C5 全 PASS 才是 DETERMINISM PASS；任一 FAIL → FAIL 并输出差异首行。
"""
import re
import sys

R1 = "runs/lsu/det/A01-F0-W3/run1"
R2 = "runs/lsu/det/A01-F0-W3/run2"
G1 = "/tmp/det_run1_guard.out"
G2 = "/tmp/det_run2_guard.out"

results = []


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"\n    {detail}" if detail else ""))


def first_diff(a, b, label):
    la, lb = a.splitlines(), b.splitlines()
    for i in range(max(len(la), len(lb))):
        xa = la[i] if i < len(la) else "<EOF>"
        xb = lb[i] if i < len(lb) else "<EOF>"
        if xa != xb:
            return f"{label} 首个差异行 {i+1}: run1={xa!r} run2={xb!r}"
    return ""


# C1 注入日志
inj1, inj2 = read(f"{R1}/addrpath_injections.log"), read(f"{R2}/addrpath_injections.log")
check("C1 注入日志逐字节（目标/bit/原值/故障值/时刻/L0/funnel）", inj1 == inj2,
      "" if inj1 == inj2 else first_diff(inj1, inj2, "注入日志"))
# 非空性守卫：注入确实发生（vacuous 一致不算通过）
vacuous = "injected=1" not in inj1
print(f"[{'WARN' if vacuous else 'INFO'}] 注入发生性: run1 {'未注入(vacuous!)' if vacuous else 'injected=1 确认'}")

# C2 stdout 规范化（剔除 gem5 banner/时间戳/pid/outdir 路径/守卫包装行）
BANNER = re.compile(
    r"gem5 started|gem5 executing on|gem5 compiled|gem5 version|command line|"
    r"Global frequency set|Listening for system call|info: Standard input|"
    r"SPAWNED pid=|run-finish|^\{|^\}$|cargo|simulation is exiting|"
    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|real elapsed|user time|system time")
def norm_stdout(p):
    return "\n".join(l for l in read(p).splitlines() if not BANNER.search(l)).strip()
so1, so2 = norm_stdout(G1), norm_stdout(G2)
check("C2 stdout 规范化（负载 oracle + B0 参数打印）", so1 == so2,
      "" if so1 == so2 else first_diff(so1, so2, "stdout"))
# 负载 oracle 结论行必须存在（非空守卫）：agu_addrmodes 的 oracle = 16位hex 结果 hash
oracle_lines = [l for l in so1.splitlines()
                if re.search(r"^[0-9a-f]{16}$|PASS|FAIL|OK|ERROR|checksum|MISMATCH", l)]
check("C2b 负载 oracle 结论行存在（非 vacuous）", len(oracle_lines) > 0,
      f"oracle 行 {len(oracle_lines)} 条: {oracle_lines[:3]}")

# C3 stats.txt 语义字段
def stats_semantic(p):
    pairs = {}
    for line in read(p).splitlines():
        # gem5 v25 stats: 驼峰字段名 + 多空格 + 值 + 多空格 + # 注释
        m = re.match(r"^(\S+)\s+([-\d.eE+]+)\s+#", line)
        if m and not m.group(1).startswith("host"):
            pairs[m.group(1)] = m.group(2)
    return pairs
st1, st2 = stats_semantic(f"{R1}/stats.txt"), stats_semantic(f"{R2}/stats.txt")
only1 = set(st1) - set(st2)
only2 = set(st2) - set(st1)
diffs = [k for k in set(st1) & set(st2) if st1[k] != st2[k]]
check("C3 stats.txt 语义字段（剔除 host_*）",
      not only1 and not only2 and not diffs,
      f"仅run1字段:{sorted(only1)[:5]} 仅run2:{sorted(only2)[:5]} 值差异:{[(k, st1[k], st2[k]) for k in sorted(diffs)[:5]]}")
print(f"[INFO] stats 语义字段数: run1={len(st1)} run2={len(st2)}；关键值 sim_ticks={st1.get('sim_ticks')} sim_insts={st1.get('sim_insts')}")

# C4 config.ini 逐字节
ci1, ci2 = read(f"{R1}/config.ini"), read(f"{R2}/config.ini")
check("C4 config.ini 逐字节（实验语义配置）", ci1 == ci2,
      "" if ci1 == ci2 else first_diff(ci1, ci2, "config.ini"))

# C5 退出码（守卫 run-finish 事件）
def exit_code(p):
    m = re.search(r'"exit_code": (\d+)', read(p))
    return int(m.group(1)) if m else None
e1, e2 = exit_code(G1), exit_code(G2)
check("C5 守卫退出码（两次均 0）", e1 == 0 and e2 == 0, f"run1={e1} run2={e2}")

print()
if vacuous:
    print("OVERALL: FAIL（注入未发生，vacuous 一致不成立）")
    sys.exit(1)
if all(results):
    print("OVERALL: DETERMINISM PASS — C1-C5 全部一致，注入语义字段完全复现")
    sys.exit(0)
print(f"OVERALL: FAIL — {results.count(False)}/{len(results)} 项检查失败")
sys.exit(1)
