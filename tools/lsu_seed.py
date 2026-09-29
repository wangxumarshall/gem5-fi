#!/usr/bin/env python3
"""lsu_seed.py — LSU 故障注入稳定 seed 生成器（task_plan.md 调度协议第 5 条）。

规则：seed = SHA256("lsu-fi-v1|" + RunID + "|" + phase + "|" + sample_index)
的低 64 位，按无符号大端整数解释。

"低 64 位"的解释（显式固定，杜绝歧义）：SHA256 的 32 字节 digest 按大端
字节序构成一个 256 位无符号整数，其最低有效 64 位即 digest 的最后 8 字节
digest[24:32]，再按大端解释为无符号 64 位整数。取值范围 [0, 2^64)。

B0/S1–S4 配对实验（P6）必须显式复用 B0 的 seed 清单：即对同一 RunID、
同一样本序号，B0 与 S 变体使用完全相同的 seed（见 --manifest 输出的
seed 列；配对运行时直接引用该清单，不得重新派生）。

用法：
  python3 tools/lsu_seed.py --run-id A01-F0-W3 --phase pilot --sample-index 0
  python3 tools/lsu_seed.py --run-id A01-F0-W3 --phase pilot --samples 30   # 批量
  python3 tools/lsu_seed.py --manifest docs/gem5-fi/lsu/完整任务执行清单.md \
      --phase pilot --samples 30 --output runs/lsu/seed_manifest_pilot.json
"""
import argparse
import hashlib
import json
import re
import sys

DOMAIN = "lsu-fi-v1"


def lsu_seed(run_id: str, phase: str, sample_index: int) -> int:
    """稳定 seed：同输入永远同输出，跨进程/跨机器可复现。"""
    if sample_index < 0:
        raise ValueError("sample_index 必须 >= 0")
    payload = f"{DOMAIN}|{run_id}|{phase}|{sample_index}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[24:32], "big")


def iter_checklist_runids(path):
    """从完整清单提取 ITEM→RunID 映射（顺序保持）。"""
    pat = re.compile(r"^### (ITEM-\d{3}) — (\S+)$", re.M)
    with open(path, encoding="utf-8") as f:
        for m in pat.finditer(f.read()):
            yield m.group(1), m.group(2)


def self_test():
    """内嵌测试向量（预先用独立 python 会话计算写死，非运行时自算自比）。"""
    # 真实向量（独立 python 会话预计算，2026-09-29；首版占位向量未计算即写入，
    # 被 self-test 抓获 FAIL 后以真实值替换——测试先行的价值记录）：
    # python3 -c "import hashlib;d=hashlib.sha256(b'lsu-fi-v1|A01-F0-W3|pilot|0').digest();print(hex(int.from_bytes(d[24:32],'big')))"
    vectors = [
        ("A01-F0-W3", "pilot", 0, 0x8821862DA5F30836),
        ("A01-F0-W3", "pilot", 1, 0x9D96E04F48698893),
        ("A01-F0-W3", "screening", 0, 0x55ED41FBD5BE48C4),
        ("T10-F2-W1", "engineering", 7, 0x554A1BA12EBD9056),
        ("ITEM边界测试", "sensitivity", 12345, None),  # None = 只验证范围与确定性
    ]
    ok = True
    for run_id, phase, idx, expected in vectors:
        s = lsu_seed(run_id, phase, idx)
        if not (0 <= s < 2**64):
            print(f"FAIL 范围: {run_id}/{phase}/{idx} -> {s}")
            ok = False
        if lsu_seed(run_id, phase, idx) != s:
            print(f"FAIL 确定性: {run_id}/{phase}/{idx}")
            ok = False
        if expected is not None and s != expected:
            print(f"FAIL 向量: {run_id}/{phase}/{idx} -> {s:#x} 期望 {expected:#x}")
            ok = False
    # phase 必须影响 seed（不同阶段不得共享样本空间）
    if lsu_seed("A01-F0-W3", "pilot", 0) == lsu_seed("A01-F0-W3", "screening", 0):
        print("FAIL: phase 未影响 seed")
        ok = False
    # sample_index 必须影响 seed
    if lsu_seed("A01-F0-W3", "pilot", 0) == lsu_seed("A01-F0-W3", "pilot", 1):
        print("FAIL: sample_index 未影响 seed")
        ok = False
    print("SELF-TEST: PASS" if ok else "SELF-TEST: FAIL")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id")
    ap.add_argument("--phase",
                    choices=["engineering", "pilot", "screening", "confirmatory",
                             "sensitivity", "reproduction"])
    ap.add_argument("--sample-index", type=int)
    ap.add_argument("--samples", type=int, help="批量：sample_index 0..N-1")
    ap.add_argument("--manifest", help="完整清单路径，为全部 325 RunID 生成 seed 清单")
    ap.add_argument("--output", help="manifest 输出路径（JSON）")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(0 if self_test() else 1)

    if args.manifest:
        rows = []
        for item, run_id in iter_checklist_runids(args.manifest):
            for i in range(args.samples or 30):
                rows.append({"item": item, "run_id": run_id, "phase": args.phase,
                             "sample_index": i,
                             "seed": lsu_seed(run_id, args.phase, i)})
        out = {"domain": DOMAIN, "rule": "sha256('lsu-fi-v1|RunID|phase|sample_index') 低64位(digest[24:32] 大端) —— 见 tools/lsu_seed.py",
               "phase": args.phase, "samples_per_runid": args.samples or 30,
               "count": len(rows), "seeds": rows}
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
            print(f"manifest 写入 {args.output}（{len(rows)} 条）")
        else:
            print(json.dumps(out, ensure_ascii=False))
        return

    if not (args.run_id and args.phase
            and (args.sample_index is not None or args.samples)):
        ap.error("需要 --run-id --phase 与 (--sample-index | --samples)，或 --manifest")

    indices = (range(args.samples) if args.samples is not None
               else [args.sample_index])
    for i in indices:
        print(lsu_seed(args.run_id, args.phase, i))


if __name__ == "__main__":
    main()
