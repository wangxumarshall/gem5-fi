#!/usr/bin/env python3
"""profile_taishan.py — CPU 描述驱动的 SE 仿真入口（SDC ED 计划 Task 1.3）。

单一事实源管线（docs/sdc-ed/method.md §2）：
    configs/cpu-profiles/*.yaml  →  本脚本  →  gem5 O3 + cache 实例化

用法：
    # 描述驱动（结构参数从 YAML 来；未声明字段沿用 two_level_taishan.py 值）
    gem5.opt configs/se/profile_taishan.py \
        --profile configs/cpu-profiles/taishan-v110.yaml \
        --binary workloads/harp/sample_seq --mode baseline

    # 无 --profile：行为与 two_level_taishan.py 完全一致（回归锚路径）
    gem5.opt configs/se/profile_taishan.py --binary ... --mode baseline

实现方式（为什么是源码文本替换）：
  two_level_taishan.py 是模块级脚本（argparse → build → simulate 一气
  呵成），无法先 import 再改属性——exec 时仿真已经跑完。因此本脚本
  读其源码文本，对固定参数赋值行做**受控字面量替换**：每个替换模式
  必须恰好命中一次，否则报错退出（目标文件演化时立即暴露，绝不静默
  错配）。替换后 exec 修改版源码。覆盖清单打印到 stderr 供审计。

诚实边界：
  - 只替换 YAML 声明的字段；其余参数（时钟 2.6GHz/内存/DDR3/cache
    延迟细节）沿用原值，差异集 = 打印的覆盖清单。
  - null 字段（未披露）：报错，不猜值（schema.md 硬规则 1）。跑仿真
    请用实配口径 profile（taishan-v110.yaml，全字段无 null）。
"""

import argparse
import os
import re
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TS_CFG = os.path.join(REPO, "smoke_test/configs/two_level_taishan.py")

# YAML 字段 → two_level_taishan.py 源码中的赋值模式（受控替换表）
# 模式必须恰好命中一次（re.subn 计数校验）。
OVERRIDE_PATTERNS = {
    "OoO.rob.entries":      r"cpu\.numROBEntries = \d+",
    "OoO.prf_int.regs":     r"cpu\.numPhysIntRegs = \d+",
    "OoO.prf_float.regs":   r"cpu\.numPhysFloatRegs = \d+",
    "OoO.prf_vec.regs":     r"cpu\.numPhysVecRegs = \d+",
    "LSU.lq.entries":       r"cpu\.LQEntries = \d+",
    "LSU.sq.entries":       r"cpu\.SQEntries = \d+",
    "IFU.fetch_width":      r"cpu\.fetchWidth = \d+",
}


def _get(units, path, yaml_path):
    """读 units.<a>.<b>.<c>；null → ValueError（不猜值）。"""
    node = units
    for key in path.split("."):
        node = (node or {}).get(key)
    if node is None:
        raise ValueError(
            f"profile {yaml_path}: units.{path} is null/undisclosed — "
            "schema.md rule 1: never guess. Use an implementation-calibre "
            "profile (e.g. taishan-v110.yaml).")
    return node


def build_patched_source(yaml_path):
    """读 two_level_taishan.py 源码，按 YAML 覆盖参数行，返回 (源码, 覆盖清单)。"""
    with open(yaml_path) as f:
        prof = yaml.safe_load(f)
    units = prof.get("units", {})
    with open(TS_CFG) as f:
        src = f.read()

    applied = []
    skipped_null = []

    def note_null(field):
        skipped_null.append(field)

    def sub_one(pattern, repl):
        nonlocal src
        src2, n = re.subn(pattern, repl, src)
        if n != 1:
            raise SystemExit(
                f"ERROR: pattern '{pattern}' matched {n} times (need exactly "
                f"1) in {TS_CFG} — the target config evolved; update "
                f"OVERRIDE_PATTERNS in profile_taishan.py.")
        src = src2

    # 各覆盖字段（YAML 声明才替换；null 跳过并记录——沿用原值，诚实警告）
    if (units.get("OoO", {}).get("rob", {}) or {}).get("entries") is not None:
        v = _get(units, "OoO.rob.entries", yaml_path)
        sub_one(OVERRIDE_PATTERNS["OoO.rob.entries"], f"cpu.numROBEntries = {v}")
        applied.append(f"OoO.rob.entries -> numROBEntries = {v}")
    else:
        note_null("OoO.rob.entries")
    for field, param in (("prf_int", "numPhysIntRegs"),
                         ("prf_float", "numPhysFloatRegs"),
                         ("prf_vec", "numPhysVecRegs")):
        if (units.get("OoO", {}).get(field, {}) or {}).get("regs") is not None:
            v = _get(units, f"OoO.{field}.regs", yaml_path)
            sub_one(OVERRIDE_PATTERNS[f"OoO.{field}.regs"],
                    f"cpu.{param} = {v}")
            applied.append(f"OoO.{field}.regs -> {param} = {v}")
        else:
            note_null(f"OoO.{field}.regs")
    if (units.get("LSU", {}).get("lq", {}) or {}).get("entries") is not None:
        v = _get(units, "LSU.lq.entries", yaml_path)
        sub_one(OVERRIDE_PATTERNS["LSU.lq.entries"], f"cpu.LQEntries = {v}")
        applied.append(f"LSU.lq.entries -> LQEntries = {v}")
    else:
        note_null("LSU.lq.entries")
    if (units.get("LSU", {}).get("sq", {}) or {}).get("entries") is not None:
        v = _get(units, "LSU.sq.entries", yaml_path)
        sub_one(OVERRIDE_PATTERNS["LSU.sq.entries"], f"cpu.SQEntries = {v}")
        applied.append(f"LSU.sq.entries -> SQEntries = {v}")
    else:
        note_null("LSU.sq.entries")
    if (units.get("IFU", {}) or {}).get("fetch_width") is not None:
        v = _get(units, "IFU.fetch_width", yaml_path)
        sub_one(OVERRIDE_PATTERNS["IFU.fetch_width"], f"cpu.fetchWidth = {v}")
        applied.append(f"IFU.fetch_width -> fetchWidth = {v}")
    else:
        note_null("IFU.fetch_width")

    return src, applied, skipped_null


def main():
    ap = argparse.ArgumentParser(
        description="CPU-profile-driven SE simulation entry")
    ap.add_argument("--profile", default=None,
                    help="CPU 描述 YAML；缺省 = two_level_taishan.py 原行为")
    ap.add_argument("--list-overrides", action="store_true",
                    help="只打印覆盖清单不仿真（dry-run 审计）")
    known, passthrough = ap.parse_known_args()

    if known.profile is None:
        # 回归锚路径：原样执行 two_level_taishan.py
        sys.argv = [TS_CFG] + passthrough
        exec(compile(open(TS_CFG).read(), TS_CFG, "exec"),
             {"__name__": "__main__", "__file__": TS_CFG})
        return

    src, applied, skipped_null = build_patched_source(known.profile)
    if known.list_overrides:
        print(f"# profile: {known.profile}")
        for line in applied or ["(no overrides — YAML declares none)"]:
            print(f"#   {line}")
        for line in skipped_null:
            print(f"#   UNDISCLOSED (kept two_level_taishan value): {line}")
        return
    for line in applied:
        print(f"[profile] {line}", file=sys.stderr)
    for line in skipped_null:
        print(f"[profile] UNDISCLOSED, kept default: {line}", file=sys.stderr)

    sys.argv = [TS_CFG] + passthrough
    exec(compile(src, TS_CFG + " <profiled>", "exec"),
         {"__name__": "__main__", "__file__": TS_CFG})


if __name__ == "__main__":
    main()
