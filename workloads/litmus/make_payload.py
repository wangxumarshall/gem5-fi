#!/usr/bin/env python3
"""make_payload.py — 把已构建的 litmus 静态 ELF 打包成 FS 单文件 payload。

为什么需要它（R4-8-FSMC）：gem5 的 `--readfile` 每次只投放**一个宿主文件**
给 guest（guest 侧 `m5 readfile` 分 256 KiB 块流式取出，见
CHAOS/gem5/util/m5/src/command/readfile.cc —— 所以没有 2 MiB 之类的上限）。
guest 里没有我们的二进制，宿主又没有 root 去挂载 ubuntu.img 写文件，所以
把 ELF 以 base64 内嵌进 rcS，guest 侧 `base64 -d` 还原。

用法（由 workloads/litmus/Makefile 调用）：
    make -C workloads/litmus payload
即
    python3 workloads/litmus/make_payload.py --dir <dir> --out <rcS> <names...>

产物是可复现的：同一组 ELF 一定生成同一个 rcS（content-addressed 打印
sha256，落在 stdout）。
"""
import argparse
import base64
import hashlib
import pathlib
import textwrap

HEADER = """#!/bin/sh
# litmus.rcS — W7 Atomic-Litmus 多核 FS payload (R4-8-FSMC)。
#
# !! GENERATED FILE — 由 workloads/litmus/make_payload.py 从已构建的静态
# !! ELF 生成；手改会被 `make payload` 覆盖。改行为请改
# !! workloads/litmus/litmus_*.c。
#
# 投放方式：该文件经 gem5 `--readfile` 进 guest（boot_ckpt.rcS 在用户态
# 检查点之后 re-readfile 出本文件并 `sh` 它），脚本自解出三个 litmus 静态
# ELF 到 /tmp 并逐个运行。每个 litmus 自报 oracle 行 + FINAL=<16hex>。
#
# 判据（规格 §6 W7："每轮检查禁出现结果"）：
#   litmus_atomic / litmus_sb / litmus_mp 的 forbidden 计数必须为 0；
#   非 0 即硬件或注入导致的可见违例。
#
# guest 侧只依赖 coreutils 的 base64（Ubuntu base 必装）；不依赖 taskset
# （绑核在 C 里用 sched_setaffinity 做）。
echo "[litmus.rcS] nproc=$(nproc 2>/dev/null || echo ?)"
echo "[litmus.rcS] cpuinfo processors=$(grep -c '^processor' /proc/cpuinfo 2>/dev/null || echo ?)"
echo "[litmus.rcS] deploying litmus binaries from embedded base64"
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="dir holding the built ELFs")
    ap.add_argument("--out", required=True, help="rcS path to write")
    ap.add_argument("--strip-suffix", default="",
                    help="suffix stripped from the host file name to get the "
                         "guest-side name (e.g. _fs)")
    ap.add_argument("names", nargs="+", help="host binary names in run order")
    args = ap.parse_args()

    d = pathlib.Path(args.dir)
    guests = []
    parts = [HEADER]
    for name in args.names:
        exe = d / name
        guest = name
        if args.strip_suffix:
            if not guest.endswith(args.strip_suffix):
                raise SystemExit(f"{name} lacks --strip-suffix "
                                 f"{args.strip_suffix}")
            guest = guest[: -len(args.strip_suffix)]
        guests.append(guest)
        blob = exe.read_bytes()
        if not blob.startswith(b"\x7fELF"):
            raise SystemExit(f"{exe} is not an ELF (build first?)")
        b64 = base64.b64encode(blob).decode()
        parts.append(
            f"base64 -d > /tmp/{guest} << 'B64_{guest}'\n"
            + "\n".join(textwrap.wrap(b64, 76))
            + f"\nB64_{guest}\n"
            f"chmod +x /tmp/{guest}\n"
            f"echo \"[litmus.rcS] /tmp/{guest} "
            f"sha256=$(sha256sum /tmp/{guest} | cut -d' ' -f1) "
            f"size={len(blob)}\"\n"
        )
    parts.append(
        "\n# 运行顺序：atomic 最先（最可能给出可读 oracle），然后 sb，"
        "最后 mp\n"
        "#（mp 在无一致性的 classic 多核上必然挂死 —— 那本身就是证据，"
        "见 R4-8-FSMC 报告）。\n"
        "rc=0\n"
        "for t in " + " ".join(guests) + "; do\n"
        "    echo \"[litmus.rcS] ===== running /tmp/$t =====\"\n"
        "    /tmp/$t\n"
        "    echo \"[litmus.rcS] /tmp/$t exit=$?\"\n"
        "done\n"
        "echo \"[litmus.rcS] payload finished\"\n"
        "m5 exit\n"
    )
    out = pathlib.Path(args.out)
    text = "\n".join(parts)
    out.write_text(text)
    dig = hashlib.sha256(text.encode()).hexdigest()
    print(f"[make_payload] wrote {out} ({len(text)} bytes) sha256={dig}")
    for name in args.names:
        b = (d / name).read_bytes()
        print(f"[make_payload]   {name}: size={len(b)} "
              f"sha256={hashlib.sha256(b).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
