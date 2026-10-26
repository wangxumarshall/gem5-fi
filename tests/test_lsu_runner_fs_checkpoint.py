#!/usr/bin/env python3
"""test_lsu_runner_fs_checkpoint.py — [0202-REBUILD] FS checkpoint 身份契约。

背景（实测缺陷）：`tools/lsu_runner.py` 曾把 B0 checkpoint 硬编码为
`runs/lsu/fs_cpt_boot/cpt.237949797015`。0202 重建生成了**新的**真实
`cpt.<tick>`；把新 cpt 改名/软链成旧名冒充身份是禁止的。故 checkpoint 必须
在 manifest 冻结时显式接收、写进身份、并由命令直接消费（身份与命令同源）。

本套件锁死：
  1. `resolve_fs_checkpoint` 优先级：显式参数 > env `LSU_FS_CHECKPOINT` > 历史默认；
  2. `build_manifest` 把解析后的真实路径写进 `identity.checkpoint`（armtlb 家族），
     且不强制改回 legacy 名；
  3. `build_guard_cmd` 的命令携带**同一个**路径（身份与命令同源）；
  4. 命令行 `--fs-checkpoint` 与已冻结身份分歧时**响亮 SystemExit**（不静默覆盖身份）；
     相同值幂等放行；
  5. SE 家族不受影响（`identity.checkpoint == "none (SE)"`）。

用法：python3 tests/test_lsu_runner_fs_checkpoint.py   （退出码 0=全 PASS）
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_runner as RUN  # noqa: E402

FAILED = []


def check(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name + (("  :: " + str(detail)) if detail and not ok else ""))
    if not ok:
        FAILED.append(name)


def main():
    # [0202] build_manifest 会把真实 SHA 写进身份（冻结时必须）。本套件只测
    # checkpoint 身份接线，故把 `_sha` 打桩——不依赖"二进制此刻是否已编译完"。
    real_sha = RUN._sha
    RUN._sha = lambda p: "0" * 64
    try:
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="0202ckpt_"))

        print("[1] resolve_fs_checkpoint 优先级（显式 > env > 历史默认）")
        os.environ.pop(RUN.FS_CHECKPOINT_ENV, None)
        check("无参回落到历史默认 CPT（向后兼容）",
              RUN.resolve_fs_checkpoint() == RUN.CPT, str(RUN.resolve_fs_checkpoint()))
        os.environ[RUN.FS_CHECKPOINT_ENV] = str(tmp / "env_cpt" / "cpt.555")
        check("env LSU_FS_CHECKPOINT 生效",
              RUN.resolve_fs_checkpoint() == tmp / "env_cpt" / "cpt.555",
              str(RUN.resolve_fs_checkpoint()))
        check("显式参数压过 env",
              RUN.resolve_fs_checkpoint(str(tmp / "cli" / "cpt.777")) == tmp / "cli" / "cpt.777")
        os.environ.pop(RUN.FS_CHECKPOINT_ENV, None)

        print("[2] manifest 身份携带真实 cpt.<tick>（不被强改回 legacy 名）")
        new_cpt = tmp / "cpt.243414599076"
        m = RUN.build_manifest("ITEM-052", "engineering", 0, fs_checkpoint=str(new_cpt))
        check("ITEM-052 属 armtlb 家族", m["family"] == "armtlb", m["family"])
        check("identity.checkpoint == 传入的真实路径",
              m["identity"]["checkpoint"] == str(new_cpt), str(m["identity"]["checkpoint"]))
        check("identity.checkpoint 不含 legacy 名",
              "cpt.237949797015" not in m["identity"]["checkpoint"])

        print("[3] 守卫命令与身份同源")
        _cfg, args = RUN.build_guard_cmd(m, tmp / "out")
        i = args.index("--restore-checkpoint")
        check("--restore-checkpoint == identity.checkpoint",
              args[i + 1] == str(new_cpt) == m["identity"]["checkpoint"], args[i + 1])

        print("[4] env 覆盖贯通 manifest 与命令")
        os.environ[RUN.FS_CHECKPOINT_ENV] = str(tmp / "cpt.111")
        m2 = RUN.build_manifest("ITEM-041", "engineering", 0)
        check("env 写入 identity", m2["identity"]["checkpoint"] == str(tmp / "cpt.111"),
              str(m2["identity"]["checkpoint"]))
        _c2, a2 = RUN.build_guard_cmd(m2, tmp / "out")
        check("env 贯通命令", a2[a2.index("--restore-checkpoint") + 1] == str(tmp / "cpt.111"))
        os.environ.pop(RUN.FS_CHECKPOINT_ENV, None)

        print("[5] 命令行覆盖已冻结身份 → 响亮拒绝（绝不静默分歧）")
        frozen = tmp / "cpt.aaa"
        m3 = RUN.build_manifest("ITEM-052", "engineering", 0, fs_checkpoint=str(frozen))
        refused = False
        try:
            RUN.build_guard_cmd(m3, tmp / "out", fs_checkpoint=str(tmp / "cpt.bbb"))
        except SystemExit:
            refused = True
        check("分歧时 SystemExit", refused)
        _c3, a3 = RUN.build_guard_cmd(m3, tmp / "out", fs_checkpoint=str(frozen))
        check("相同值幂等放行",
              a3[a3.index("--restore-checkpoint") + 1] == str(frozen))

        print("[6] SE 家族不受影响")
        m4 = RUN.build_manifest("ITEM-002", "engineering", 0)
        check("SE family != armtlb", m4["family"] != "armtlb", m4["family"])
        check("SE identity.checkpoint == 'none (SE)'",
              m4["identity"]["checkpoint"] == "none (SE)", str(m4["identity"]["checkpoint"]))
    finally:
        RUN._sha = real_sha

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
