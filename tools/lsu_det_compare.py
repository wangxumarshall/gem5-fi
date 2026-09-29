#!/usr/bin/env python3
"""lsu_det_compare.py — 注入器家族双跑确定性语义比较（G0-02 通用工具）。

对同一冻结 manifest 的两次串行运行做语义级比较（非仅 exit 0）：
  C1 注入日志逐字节（<log-name>：目标/bit/原值/故障值/时刻/L0/funnel）
  C2 gem5 stdout 规范化（剔除 banner/时间戳/路径/pid/守卫包装行；含负载 oracle 输出）
  C2b 规范化 stdout 非空守卫（防 vacuous PASS）
  C3 stats.txt 语义字段（剔除 host* 主机字段；v25 多空格格式）
  C4 config.ini 逐字节
  C5 守卫 run-finish 退出码均 0
判定：全 PASS → DETERMINISM PASS；注入未发生（C1 无 injected=1）→ vacuous FAIL。
"""
import argparse
import re
import sys

BANNER = re.compile(
    r"gem5 started|gem5 executing on|gem5 compiled|gem5 version|command line|"
    r"Global frequency set|Listening for system call|info: Standard input|"
    r"SPAWNED pid=|run-finish|^\{|^\}$|simulation is exiting|"
    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|real elapsed|user time|system time")
STATS = re.compile(r"^(\S+)\s+([-\d.eE+]+)\s+#")


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def first_diff(a, b):
    la, lb = a.splitlines(), b.splitlines()
    for i in range(max(len(la), len(lb))):
        xa = la[i] if i < len(la) else "<EOF>"
        xb = lb[i] if i < len(lb) else "<EOF>"
        if xa != xb:
            return f"首差异行 {i+1}: run1={xa!r} run2={xb!r}"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--log-name", required=True, help="注入日志文件名，如 lsq_fwd_injections.log")
    ap.add_argument("--r1", required=True)
    ap.add_argument("--r2", required=True)
    ap.add_argument("--g1", required=True, help="run1 守卫包装 stdout 路径")
    ap.add_argument("--g2", required=True)
    args = ap.parse_args()

    results = []

    def check(name, ok, detail=""):
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"\n    {detail}" if detail else ""))

    inj1 = read(f"{args.r1}/{args.log_name}")
    inj2 = read(f"{args.r2}/{args.log_name}")
    check(f"C1 注入日志逐字节（{args.log_name}）", inj1 == inj2,
          "" if inj1 == inj2 else first_diff(inj1, inj2))
    # 注入发生性：以注入记录特征判定——addrpath/lsqfwd 日志行首 "Tick:"，
    # cache 行首 "Tick:"，prefetch 行中 "Tick:"（行首是 Site:）。行内任意位置
    # 含 "Tick: " 即视为存在注入记录；stdout 触发层 injected=1 为旁证。
    vacuous = not re.search(r"Tick: ", inj1)
    n_inj = len(re.findall(r"Tick: ", inj1))
    print(f"[{'WARN' if vacuous else 'INFO'}] 注入发生性: {'未注入(vacuous!)' if vacuous else f'{n_inj} 条注入记录确认'}")

    def norm(p):
        return "\n".join(l for l in read(p).splitlines() if not BANNER.search(l)).strip()
    so1, so2 = norm(args.g1), norm(args.g2)
    check("C2 stdout 规范化", so1 == so2, "" if so1 == so2 else first_diff(so1, so2))
    check("C2b stdout 非空守卫（非 vacuous）", len(so1.splitlines()) >= 3,
          f"规范化行数={len(so1.splitlines())}")
    oracle = [l for l in so1.splitlines()
              if re.match(r"^[0-9a-f]{16}$", l) or re.search(r"PASS|FAIL|ERROR|MISMATCH", l)]
    print(f"[INFO] oracle 相关行 {len(oracle)} 条: {oracle[:3]}")

    def sem(p):
        d = {}
        for line in read(p).splitlines():
            m = STATS.match(line)
            if m and not m.group(1).startswith("host"):
                d[m.group(1)] = m.group(2)
        return d
    st1, st2 = sem(f"{args.r1}/stats.txt"), sem(f"{args.r2}/stats.txt")
    only1, only2 = set(st1) - set(st2), set(st2) - set(st1)
    diffs = [(k, st1[k], st2[k]) for k in set(st1) & set(st2) if st1[k] != st2[k]]
    check("C3 stats.txt 语义字段（剔除 host*）", st1 and not only1 and not only2 and not diffs,
          f"字段数 run1={len(st1)} run2={len(st2)}；仅run1:{sorted(only1)[:4]} "
          f"仅run2:{sorted(only2)[:4]} 值差异:{diffs[:4]}")

    ci1, ci2 = read(f"{args.r1}/config.ini"), read(f"{args.r2}/config.ini")
    check("C4 config.ini 逐字节", ci1 == ci2, "" if ci1 == ci2 else first_diff(ci1, ci2))

    def ec(p):
        m = re.search(r'"exit_code": (\d+)', read(p))
        return int(m.group(1)) if m else None
    e1, e2 = ec(args.g1), ec(args.g2)
    check("C5 退出码均 0", e1 == 0 and e2 == 0, f"run1={e1} run2={e2}")

    print()
    if vacuous:
        print(f"OVERALL: FAIL — {args.run_id} 注入未发生，vacuous 一致不成立")
        sys.exit(2)
    if all(results):
        print(f"OVERALL: DETERMINISM PASS — {args.run_id} C1-C5 语义字段完全复现")
        sys.exit(0)
    print(f"OVERALL: FAIL — {args.run_id} {results.count(False)}/{len(results)} 项失败")
    sys.exit(1)


if __name__ == "__main__":
    main()
