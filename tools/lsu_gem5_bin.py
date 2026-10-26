#!/usr/bin/env python3
"""lsu_gem5_bin.py — golden/阴性对照路径的 gem5 二进制**唯一**解析器（R6-GOLDEN）。

为什么需要它（实测缺陷，2026-10-23）：
未注入 GOLDEN 对照被**主 checkout 的二进制路径**调用而失败 ——
`runs/lsu/r6_tlb_verify/golden/run.log` 实录
`timeout: 无法运行命令 "/home/sdc/gem5-fi-ding/CHAOS/gem5/build/ARM/gem5.opt":
No such file or directory`。该路径属于**另一条 track** 的构建；golden 路径
当时没有走 `$LSU_GEM5_BIN`，而是落到 repo 根/主树的 `build/ARM/gem5.opt`
约定（worktree 的历史里 `build/ARM` 是指向主树 `CHAOS/gem5/build/ARM` 的
符号链接）。于是"对照"从未运行，却可能被当成证据。

本模块把解析收成一处，铁律：
  1. `$LSU_GEM5_BIN` 优先（worktree 运行必须显式指定冻结二进制）；
  2. 未设时回落 **本 worktree 自己**的 `CHAOS/gem5/build/ARM/gem5.opt`
     （本文件所在 checkout 的路径，绝不指向主 checkout）；
  3. 解析结果必须是**存在**的常规可执行文件，否则响亮 `SystemExit`
     ——绝不在缺二进制时静默跑空/跑错（CLAUDE.md 的 stale-binary 教训）。
"""
import os
import sys
from pathlib import Path

# 本文件所在 checkout 的根（worktree 或主树，取决于从哪里导入）
REPO = Path(__file__).resolve().parent.parent

# worktree/主树内 gem5 构建的规范相对路径（CHAOS/gem5/src → build/ARM）
_WORKTREE_REL = Path("CHAOS/gem5/build/ARM/gem5.opt")

# repo 根 build/ 是**主树专用**约定（worktree 里不存在）；golden 路径
# 绝不回落到它，以免跑到别的 track 的二进制。
_MAIN_CHECKOUT_REL = Path("build/ARM/gem5.opt")


def worktree_gem5_path(repo=None):
    """本 checkout 自己的 CHAOS 构建路径（不关心是否存在）。"""
    return (repo or REPO) / _WORKTREE_REL


def main_checkout_gem5_path(repo=None):
    """repo 根 build/ARM/gem5.opt（主树约定；golden 路径禁止回落至此）。"""
    return (repo or REPO) / _MAIN_CHECKOUT_REL


def resolve_default_gem5_bin(env=None, repo=None):
    """非致命默认解析：`$LSU_GEM5_BIN` → 本 checkout 的 CHAOS 构建。

    不做存在性检查（也不 SystemExit）——供 manifest identity/旧套件沿用；
    需要"缺则响亮失败"的 golden 入口请用 `resolve_gem5_bin()`。
    """
    env = os.environ if env is None else env
    cand = env.get("LSU_GEM5_BIN")
    return Path(cand) if cand else worktree_gem5_path(repo)


def resolve_gem5_bin(env=None, repo=None):
    """解析 golden 路径要用的 gem5.opt。

    优先级：`$LSU_GEM5_BIN` → 本 checkout 的 CHAOS 构建。
    两者皆不存在 → `SystemExit`（附尝试过的候选，便于定位）。
    """
    env = os.environ if env is None else env
    repo = repo or REPO
    cand = env.get("LSU_GEM5_BIN")
    tried = []
    if cand:
        p = Path(cand)
        tried.append(("LSU_GEM5_BIN", p))
        if p.exists():
            return p
    wt = worktree_gem5_path(repo)
    tried.append(("worktree CHAOS build", wt))
    if wt.exists():
        return wt
    msg = ["[lsu_gem5_bin] gem5 二进制不可用；已尝试:"]
    for label, p in tried:
        msg.append(f"  - {label}: {p}")
    msg.append("  设置 LSU_GEM5_BIN 指向已构建的 gem5.opt（worktree 构建落在 "
               "CHAOS/gem5/build/ARM/gem5.opt）。绝不回落主树 "
               "build/ARM/gem5.opt（那是另一条 track 的二进制）。")
    raise SystemExit("\n".join(msg))


def describe(path=None, env=None, repo=None):
    """可读的解析结果说明（run_id/日志里引用）。

    `path` 仅作历史占位（解析总以 env/repo 为准，避免"传了路径却没生效"的
    静默分歧）；调用方可只给 `repo=workdir` 让说明与真实调用二进制同源。
    """
    p = resolve_gem5_bin(env, repo)
    src = "LSU_GEM5_BIN" if (env or os.environ).get("LSU_GEM5_BIN") else "worktree-default"
    return f"{p} (source={src})"


if __name__ == "__main__":
    print(describe())
    sys.exit(0)
