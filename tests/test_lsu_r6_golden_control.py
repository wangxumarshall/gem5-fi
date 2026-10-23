#!/usr/bin/env python3
"""test_lsu_r6_golden_control.py — [LSU][MDSPEC][R6-GOLDEN] 阴性/黄金对照入口契约。

背景（实测缺陷，2026-10-23）：一个未注入（uninjected）GOLDEN 对照被
**错的主树二进制路径**调用而失败，真实证据留在
`runs/lsu/r6_tlb_verify/golden/run.log`：

    timeout: 无法运行命令
    "/home/sdc/gem5-fi-ding/CHAOS/gem5/build/ARM/gem5.opt": No such file or directory

该路径是**主 checkout**（另一条 track）的二进制；golden 路径没有走
`$LSU_GEM5_BIN`，而是落到 repo 根/主树的 `build/ARM/gem5.opt` 约定，
于是对照从未真正运行 —— 不产生任何证据，却被当成"控制组"。

本套件钉死六件事：
  1. golden 路径二进制解析**必须**遵 `$LSU_GEM5_BIN` → **本 worktree 自己的**
     `CHAOS/gem5/build/ARM/gem5.opt`；两者皆缺时**响亮 SystemExit**，绝不
     静默回落到主树/repo 根 `build/ARM/gem5.opt`；且 `repo=` 必须决定
     "本 checkout 构建"的位置（golden `--workdir` 契约）；
  2. golden 路径源码里**不得**残留主树绝对路径（文首那条实测失败命令）；
  3. `lsu_unit_pilot.py` / `lsu_runner.py`（SE golden 执行链）不得硬编码
     `REPO/"build/ARM/gem5.opt"` 而不看 `$LSU_GEM5_BIN`（须走统一解析器）；
  4. 阴性判据：`prop_evt` 出现任何 `kind=inj`（或 chain_end）→ FAIL；
     0 个 `inj` → PASS（注入路径被证明未激活）；
  5. `prop_evt` 流的**完整性**：完整 gzip 可读；截断流（无 end-of-stream
     标记，实测 negative2 形态）须识别为 truncated 且**不得**判"完成"——
     否则"0 个 inj"是伪阴性；
  6. 命令组装：带齐 `--chaos_propagation/--prop_run_id/--prop_sample_run_id`
     且引用传入二进制、不含主树路径。

用法：python3 tests/test_lsu_r6_golden_control.py   （退出码 0=全 PASS）
"""
import ast
import gzip
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_gem5_bin as GB               # noqa: E402
import lsu_r6_golden_control as GC      # noqa: E402

FAILED = []

# 实测失败命令里的主树绝对路径（另一条 track 的二进制）
MAIN_CHECKOUT_BIN = "/home/sdc/gem5-fi-ding/CHAOS/gem5/build/ARM/gem5.opt"

# "golden 路径" = 实现 golden/阴性对照调用及其二进制解析的源码文件
GOLDEN_SOURCES = [
    "tools/lsu_gem5_bin.py",
    "tools/lsu_r6_golden_control.py",
    "tools/lsu_unit_pilot.py",
    "tools/lsu_runner.py",
    "tools/lsu_golden3.sh",
]


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def _docstring_consts(tree):
    """模块/类/函数 docstring 对应的 ast.Constant 节点集合。"""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef,
                             ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None) or []
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                out.add(id(body[0].value))
    return out


def code_const_hits(txt, needle):
    """代码常量（非 docstring 字符串）里出现 needle 的行标签列表。

    docstring / 注释里的**纪实引用**（记录那次真机失败的命令）不算命中。
    """
    tree = ast.parse(txt)
    docs = _docstring_consts(tree)
    return [f"line {n.lineno}" for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in docs and needle in n.value]


def hardcoded_main_checkout_hits(path):
    """在**可执行代码**常量里找主树绝对路径（docstring/注释里的纪实引用不算）。

    .py 走 ast（只查非 docstring 的字符串常量）；.sh 走逐行去注释。
    返回命中描述列表（空=干净）。
    """
    path = Path(path)
    txt = path.read_text(errors="replace")
    if path.suffix == ".py":
        try:
            ast.parse(txt)
        except SyntaxError as e:
            return [f"语法错误: {e}"]
        return code_const_hits(txt, MAIN_CHECKOUT_BIN)
    hits = []
    for i, line in enumerate(txt.splitlines(), 1):
        code = line.split("#", 1)[0]
        if MAIN_CHECKOUT_BIN in code:
            hits.append(f"line {i}")
    return hits


def main():
    print("[1] 二进制解析：$LSU_GEM5_BIN 优先，缺则响亮失败，绝不回落主树")
    try:
        got = GB.resolve_gem5_bin({"LSU_GEM5_BIN": "/nonexistent/gem5.opt"})
        check("缺文件必须 SystemExit", False, "返回了 " + str(got))
    except SystemExit:
        check("缺文件必须 SystemExit", True)

    # 若本 worktree 已构建，env 覆盖必须原样生效
    wt_bin = GB.worktree_gem5_path()
    if wt_bin.exists():
        check("env 覆盖生效",
              GB.resolve_gem5_bin({"LSU_GEM5_BIN": str(wt_bin)}) == wt_bin,
              str(wt_bin))
    else:
        print("SKIP env 覆盖生效（本 worktree 未构建 %s）" % wt_bin)

    # 默认候选必须指向**本 worktree** 的 CHAOS 构建，而不是主树/repo 根
    check("默认候选 = worktree CHAOS 构建",
          GB.worktree_gem5_path() == ROOT / "CHAOS/gem5/build/ARM/gem5.opt",
          str(GB.worktree_gem5_path()))
    check("默认候选不是 repo 根 build/",
          GB.worktree_gem5_path() != ROOT / "build/ARM/gem5.opt",
          str(GB.worktree_gem5_path()))

    # g5_path()（SE 链委托的对象）必须遵 $LSU_GEM5_BIN，否则回落本 checkout
    check("g5 默认解析遵 LSU_GEM5_BIN",
          GB.resolve_default_gem5_bin({"LSU_GEM5_BIN": "/x/gem5.opt"})
          == Path("/x/gem5.opt"))
    check("g5 默认解析回落本 checkout CHAOS 构建",
          GB.resolve_default_gem5_bin({}) == GB.worktree_gem5_path())

    # golden --workdir 契约：repo= 参数必须决定"本 checkout 构建"的位置
    fake = ROOT / "runs/lsu/r6_golden_verify/_unittest_repo"
    fb = fake / "CHAOS/gem5/build/ARM/gem5.opt"
    fb.parent.mkdir(parents=True, exist_ok=True)
    fb.write_text("#!/bin/sh\n")
    try:
        check("resolve_gem5_bin 用传入 repo 定位构建",
              GB.resolve_gem5_bin({}, fake) == fb, str(fb))
    finally:
        shutil.rmtree(fake, ignore_errors=True)

    print("[2] golden 路径源码不得残留主树绝对路径（代码常量；文档/注释引用不算）")
    for rel in GOLDEN_SOURCES:
        p = ROOT / rel
        if not p.exists():
            check(f"{rel} 存在", False, "缺文件")
            continue
        hits = hardcoded_main_checkout_hits(p)
        check(f"{rel} 无主树硬编码", not hits, "; ".join(hits))

    print("[3] SE golden 执行链须走统一解析器（不得裸硬编码 build/ARM/gem5.opt）")
    for rel in ("tools/lsu_unit_pilot.py", "tools/lsu_runner.py"):
        txt = (ROOT / rel).read_text(errors="replace")
        check(f"{rel} 无裸 build/ARM 硬编码",
              not code_const_hits(txt, "build/ARM/gem5.opt"),
              "; ".join(code_const_hits(txt, "build/ARM/gem5.opt")))
        check(f"{rel} 走统一解析器",
              ("lsu_gem5_bin" in txt or "LSU_GEM5_BIN" in txt
               or "g5_path(" in txt),
              "未引用 lsu_gem5_bin/LSU_GEM5_BIN/g5_path")

    print("[4] 阴性判据：0 个 inj → PASS；有 inj → FAIL")
    pass_counts = {"tlb_lookup": 3, "cache_access": 5}
    check("无 inj 判 PASS", GC.negative_verdict(pass_counts)["verdict"] == "PASS",
          str(GC.negative_verdict(pass_counts)))
    fail_counts = {"inj": 1, "chain_end": 1}
    check("有 inj 判 FAIL", GC.negative_verdict(fail_counts)["verdict"] == "FAIL",
          str(GC.negative_verdict(fail_counts)))
    check("空流判 PASS", GC.negative_verdict({})["verdict"] == "PASS")

    print("[5] prop_evt 解析：space-separated kind=X 计数正确")
    tmp = ROOT / "runs/lsu/r6_golden_verify/_unittest_prop_evt.txt.gz"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    try:
        with gzip.open(tmp, "wt") as fh:
            fh.write("# prop-evt v1: kind run_id sample_run_id\n")
            fh.write("PROP-EVT: kind=inj run_id=X sample_run_id=s1\n")
            fh.write("PROP-EVT: kind=tlb_lookup run_id=X sample_run_id=s1\n")
            fh.write("PROP-EVT: kind=tlb_lookup run_id=X sample_run_id=s1\n")
        c = GC.kind_counts(tmp)
        check("计数 inj=1", c.get("inj") == 1, str(c))
        check("计数 tlb_lookup=2", c.get("tlb_lookup") == 2, str(c))
        st_ok = GC.stream_status(tmp)
        check("完整流 readable 且不截断",
              st_ok["readable"] and not st_ok["truncated"], str(st_ok))
    finally:
        tmp.unlink(missing_ok=True)

    # 截断流（无 gzip 收尾标记）必须被识别 —— 伪阴性防线
    # 实测同形物：runs/lsu/r6_tlb_negative2/seed1/prop_evt.txt.gz (238 B, 仅表头)
    tdir = ROOT / "runs/lsu/r6_golden_verify/_unittest_outdir"
    tdir.mkdir(parents=True, exist_ok=True)
    full = gzip.compress(b"PROP-EVT: kind=tlb_lookup run_id=X sample_run_id=s1\n")
    trunc = tdir / "prop_evt.txt.gz"
    (tdir / "stats.txt").write_text("simTicks 1\n")
    try:
        trunc.write_bytes(full[:len(full) // 2])
        st = GC.stream_status(trunc)
        check("截断流识别为 truncated",
              st["truncated"] and not st["readable"], str(st))
        ok, why = GC.run_completed(tdir, trunc)
        check("stats 非空但流截断 → 判未完成", ok is False and "截断" in why, why)
        trunc.write_bytes(full)
        ok2, why2 = GC.run_completed(tdir, trunc)
        check("完整流 + 非空 stats → 判完成", ok2 is True, why2)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
    gone = GC.stream_status(ROOT / "runs/lsu/r6_golden_verify/_nope.txt.gz")
    check("缺失流 present=False", not gone["present"], str(gone))

    print("[6] 命令组装：带齐传播标志且引用正确二进制")
    cmd = GC.build_cmd("/abs/gem5.opt", "/out", "/cpt", "/kern", "/disk",
                       "/boot", "configs/fs/tlb_probe.rcS",
                       "NEGATIVE-GOLDEN", "s1", "configs/fs/lsu_b0_fs.py")
    joined = " ".join(cmd)
    check("含 --chaos_propagation", "--chaos_propagation" in cmd, joined)
    check("含 --prop_run_id", "--prop_run_id" in cmd and "NEGATIVE-GOLDEN" in cmd)
    check("含 --prop_sample_run_id", "--prop_sample_run_id" in cmd)
    check("含 --restore-checkpoint", "--restore-checkpoint" in cmd)
    check("首元素是传入二进制", cmd[0] == "/abs/gem5.opt")
    check("不含主树路径", MAIN_CHECKOUT_BIN not in joined)

    print()
    if FAILED:
        print(f"FAILURES: {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
