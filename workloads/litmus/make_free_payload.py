#!/usr/bin/env python3
"""make_free_payload.py — 把 **freestanding** litmus（litmus_free）打成 FS 单文件
payload，并可选附一条"heredoc 阶梯"诊断臂（R4-9-FSMC-A）。

与 make_payload.py 的关系：
  * make_payload.py 打的是 libc 静态版三件套（litmus_{atomic,sb,mp}_fs，各
    642 KB）；它们经 base64 heredoc 投放在 2 核 Ruby/O3 恢复态下**解不出来**
    （R4-8-FSMC §3.2 三臂终态一致）。
  * 本脚本打的是 litmus_free（~8 KB，零 libc），并额外能把"到底卡在哪"做成
    可观测的阶梯：同一套 `sh` heredoc + `base64 -d` 机制，按字节数递增，
    每一级打印 start/done 标记 —— guest 的 board.terminal 是逐行落盘的，
    宿主侧带时间戳轮询就能量出"每级用了多久"。

用法：
    python3 workloads/litmus/make_free_payload.py \
        --elf workloads/litmus/litmus_free \
        --out configs/fs/litmus_free.rcS
    python3 workloads/litmus/make_free_payload.py \
        --elf workloads/litmus/litmus_free \
        --out configs/fs/litmus_free_diag.rcS --ladder

产物可复现：同样的输入一定给出同样的字节流与 sha256（打印到 stdout）。
"""
import argparse
import base64
import hashlib
import pathlib
import textwrap

CONTROL_HEADER = """#!/bin/sh
# litmus_free.rcS — W7 Atomic-Litmus 多核 FS payload（R4-9-FSMC-A，freestanding）。
#
# !! GENERATED FILE — 由 workloads/litmus/make_free_payload.py 生成；手改会被
# !! `make payload_free` 覆盖。改行为请改 workloads/litmus/litmus_free.c。
#
# 与 R4-8-FSMC 的 litmus.rcS 的差别只有一个：载荷从 ~1.9 MB 的三个 libc 静态
# ELF（base64 后 2.6 MB）换成 ~8 KB 的零 libc freestanding ELF（base64 后
# ~11 KB）。投放机制**完全相同**（readfile -> sh -> base64 heredoc），所以
# 这次能跑完 = "卡点是载荷字节数 × guest 侧 heredoc 解包路径"，不是机制本身。
#
# 判据（规格 §6 W7 "每轮检查禁出现结果"）：litmus_free 自报 SB/MP/LDXR-STXR
# 三条 oracle 行 + 一行 FINAL=<16hex>（只折叠禁出现计数与轮次，见 .c 文件头
# 第 5 条）。R4-9-FSMC-A 的 golden 就是无故障运行的那条 FINAL。
echo "[litmus_free.rcS] nproc=$(nproc 2>/dev/null || echo ?)"
echo "[litmus_free.rcS] cpuinfo processors=$(grep -c '^processor' /proc/cpuinfo 2>/dev/null || echo ?)"
echo "[litmus_free.rcS] decoding litmus_free"
"""

LADDER = """
# ---- heredoc 阶梯（诊断臂）---------------------------------------------
# 与上面解码 litmus_free 用的是**同一套机制**，只改字节数，用来把"卡点"
# 从"猜"变成"量"：每一级打 start/done 两个标记，宿主侧对 board.terminal
# 带时间戳轮询即得"每级墙钟耗时"。null 级写 /dev/null（隔离解码成本），
# file 级写 /tmp（叠加 guest 磁盘写成本）。纯 shell：echo 是 dash 内建，
# 每级只 fork/exec 一次 base64。
echo "[ladder] BEGIN"
"""


def heredoc(tag: str, b64: str, dest: str) -> str:
    body = "\n".join(textwrap.wrap(b64, 76))
    return (f"base64 -d > {dest} << '{tag}'\n{body}\n{tag}\n")


def ladder_rungs() -> str:
    """返回 (script_text, [(name, decoded_bytes)])。"""
    out = []
    sizes = [
        ("L64K", 64 * 1024, "/dev/null"),
        ("L256K", 256 * 1024, "/dev/null"),
        ("L860K", 860 * 1024, "/dev/null"),   # == R4-8-FSMC 每个二进制的 heredoc 字节数
        ("L860KFILE", 860 * 1024, "/tmp/ladder.bin"),
    ]
    meta = []
    for name, n, dest in sizes:
        # 确定性填充：0..255 循环，避免全零被特殊优化（base64 输出与哈希都稳定）
        blob = bytes((i & 0xFF) for i in range(n))
        b64 = base64.b64encode(blob).decode()
        out.append(f'echo "[ladder] {name} start b64={len(b64)}"\n')
        out.append(heredoc(f"B64_{name}", b64, dest))
        out.append(f'echo "[ladder] {name} done"\n')
        meta.append((name, n))
    out.append('echo "[ladder] END"\n')
    return "".join(out), meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--elf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--guest-name", default="litmus_free")
    ap.add_argument("--ladder", action="store_true",
                    help="附 heredoc 阶梯诊断臂（见 LADDER 注释）")
    args = ap.parse_args()

    blob = pathlib.Path(args.elf).read_bytes()
    if not blob.startswith(b"\x7fELF"):
        raise SystemExit(f"{args.elf} is not an ELF")
    b64 = base64.b64encode(blob).decode()
    parts = [CONTROL_HEADER]
    parts.append(heredoc(f"B64_{args.guest_name}", b64, f"/tmp/{args.guest_name}"))
    parts.append(
        f"chmod +x /tmp/{args.guest_name}\n"
        f'echo "[litmus_free.rcS] sha256=$(sha256sum /tmp/{args.guest_name} | '
        f'cut -d\' \' -f1) size={len(blob)} emb={len(b64)}"\n'
        f'echo "[litmus_free.rcS] ===== running /tmp/{args.guest_name} ====="\n'
        f"/tmp/{args.guest_name}\n"
        f'echo "[litmus_free.rcS] exit=$?"\n'
    )
    rungs = []
    if args.ladder:
        text, meta = ladder_rungs()
        parts.append(LADDER)
        parts.append(text)
        rungs = meta
    parts.append('echo "[litmus_free.rcS] payload finished"\nm5 exit\n')

    # 阶梯必须放在 litmus 之后：先保 oracle，再诊断。
    payload = "".join(parts)
    out = pathlib.Path(args.out)
    out.write_text(payload)
    dig = hashlib.sha256(payload.encode()).hexdigest()
    print(f"[make_free_payload] wrote {out} ({len(payload)} bytes) "
          f"sha256={dig}")
    print(f"[make_free_payload]   ELF {args.elf}: size={len(blob)} "
          f"sha256={hashlib.sha256(blob).hexdigest()}")
    for name, n in rungs:
        print(f"[make_free_payload]   rung {name}: decoded_bytes={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
