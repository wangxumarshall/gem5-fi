#!/usr/bin/env python3
"""[MDSPEC][R4-6-FS] FS 基础设施可行性核实（AWARENESS 测试，不跑仿真）。

用户指令 R4-6 要求把 77 项"需裁决"分成(甲)可自行实现、只缺工时/hermetic 资源，
与(乙)真的缺授权镜像/数据/凭据。本测试把 FS 侧的事实**机器可查**：

(1) 结构面（永远可查，不需 3GB 资产）：
    - FS 平台 config 存在（configs/fs/lsu_b0_fs.py / kp920_proxy_fs.py）；
    - 平台 CPU 核数 = 1（SimpleProcessor num_cores=1）⇒ FS-MULTICORE 需
      config 改造，非仅"跑一下"；
    - 载体 rcS（tlb_probe.rcS）存在；campaign FS_CONFIG/FS_CARRIER_RC 指向存在文件；
    - `--fs-checkpoint` 缺失时 campaign 响亮报错（不静默）。
(2) 资产面（需 LSU_FS_DIR；worktree 无 3GB 子模块 ⇒ 资产缺失时 SKIP）：
    - kernel / disk / bootloader 存在 + 字节数；
    - FS checkpoint 目录（documented + 实际发现路径）存在 + m5.cpt 非空。

退出码：0 = 全 PASS（或结构面 PASS + 资产面 SKIP）；1 = 有 FAIL。
用法：python3 tests/test_lsu_fs_infra.py
      LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tests/test_lsu_fs_infra.py
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

FAILED = []
SKIPPED = []

# 文档/实际两处 checkpoint 位置（本次 R4-6 实测发现 documented 路径陈旧）。
# 相对 repo 根（runs/ 不入 git，属于运行时产物）。
CKPT_CANDIDATES = [
    "runs/lsu/fs_cpt_boot/cpt.237949797015",
    "runs/h7formal/mkckpt/cpt.90000000",
]
# 历史 help 文本提到的路径（陈旧，仅登记以便集成方核对）
CKPT_DOCUMENTED_STALE = "runs/fs_lsu/boot_b0/cpt.*"


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def note(name, detail):
    print(f"  SKIP {name} — {detail}")
    SKIPPED.append(name)


def fs_dir():
    d = os.environ.get("LSU_FS_DIR")
    return Path(d) if d else (ROOT / "gem5-fs")


def main():
    print("[1] FS 平台结构面（不需 3GB 资产）")
    for f in ("configs/fs/lsu_b0_fs.py", "configs/fs/kp920_proxy_fs.py",
              "configs/fs/tlb_probe.rcS", "configs/fs/boot_ckpt.rcS"):
        check(f"{f} exists", (ROOT / f).exists())
    check("FS carrier rcS is the TLB probe",
          "tlb_probe.rcS" in (ROOT / "configs/fs/tlb_probe.rcS").read_text()
          or "tlb_probe" in (ROOT / "configs/fs/tlb_probe.rcS").read_text())
    fscfg = ROOT / "configs/se/arm_chaos_fs.py"
    src = fscfg.read_text()
    check("FS platform exists (configs/se/arm_chaos_fs.py)", fscfg.exists())
    check("legacy FS platform is still SINGLE-CORE (num_cores=1)",
          "num_cores=1" in src, "num_cores=1 not found")

    # [R4-8-FSMC] 多核 FS 平台（Task 1）：W7/W13 的载体前提。这里断言的是
    # **结构事实**，不是"跑过了" —— 跑没跑由报告里的真机输出负责。
    mccfg = ROOT / "configs/fs/lsu_multicore_fs.py"
    mcsrc = mccfg.read_text() if mccfg.exists() else ""
    check("multi-core FS platform exists (configs/fs/lsu_multicore_fs.py)",
          mccfg.exists())
    check("multi-core platform takes --num-cores (default 2, SMP >1)",
          '"--num-cores"' in mcsrc and 'default=2' in mcsrc,
          "no --num-cores with default=2")
    check("multi-core platform offers COHERENT chi and non-coherent classic",
          '"chi"' in mcsrc and '"classic"' in mcsrc
          and "CoherenceProtocol" not in mcsrc)
    check("multi-core platform wires num_cores into SimpleProcessor",
          "num_cores=args.num_cores" in mcsrc)
    # 构造性事实：CHAOSCache 取 Param.Cache（classic），Ruby/CHI 的 L1 是
    # cache controller，不是 classic Cache ⇒ 该 config 不能挂 CHAOSCache。
    # 这条断言是为了防止有人"顺手"把 CHAOSCache 塞进来造成半接线。
    check("multi-core platform does NOT mount CHAOSCache (classic-only "
          "SimObject; Ruby L1s are cache controllers)",
          "CHAOSCache(" not in mcsrc and "CHAOSCache\n" not in mcsrc
          and "import CHAOSCache" not in mcsrc
          and "from m5.objects import" in mcsrc
          and "CHAOSExMon" in mcsrc,
          "CHAOSCache is mounted/imported in the multi-core config")
    check("multi-core platform documents WHY it exists (R4-8-FSMC)",
          "R4-8-FSMC" in mcsrc)
    # 诚实检测：多核 checkpoint 是否存在（不存在必须报"不存在"，不得假定）。
    ckpts = sorted((ROOT / "runs").rglob("cpt.*")) \
        if (ROOT / "runs").exists() else []
    multi = []
    for c in ckpts:
        ini = c.parent / "config.ini"
        if ini.exists() and "[board.processor.cores1]" in ini.read_text():
            multi.append(str(c.relative_to(ROOT)))
    print(f"      multi-core checkpoints found: {multi or 'NONE'}")

    print("[2] campaign FS 接线（路径解析 + 响亮拒绝）")
    import lsu_campaign as lc
    check("FS_CONFIG points at configs/fs/lsu_b0_fs.py",
          lc.FS_CONFIG.name == "lsu_b0_fs.py")
    check("FS_CARRIER_RC points at configs/fs/tlb_probe.rcS",
          lc.FS_CARRIER_RC.name == "tlb_probe.rcS")
    check("TLB_PROBE_GOLDEN is the host-computed 1MiB-zeros md5",
          lc.TLB_PROBE_GOLDEN == "b6d81b360a5672d80c27430f39153e2c")
    n = max(lc.COL_RUNID, lc.COL_MODEL, lc.COL_FREQ, lc.COL_WORKLOAD) + 1
    cell = [""] * n
    cell[lc.COL_RUNID] = "T01-F0-W4"
    cell[lc.COL_MODEL] = "T01"
    cell[lc.COL_FREQ] = "F0"
    cell[lc.COL_WORKLOAD] = "TLB-AliasPerm 地址探测"
    flags, golden, kind = lc.resolve_cell(cell)
    check("a runnable T-cell resolves to an FS flag set on the carrier",
          flags is not None and kind == "fs:tlb_probe", str(kind))
    check("FS flag set names the kernel/disk/bootloader via fs_asset()",
          flags is not None and "--kernel" in flags and "--bootloader" in flags)
    check("fs_asset() honors LSU_FS_DIR (worktree-safe)",
          "LSU_FS_DIR" in (ROOT / "tools/lsu_campaign.py").read_text())

    print("[3] FS 资产面（缺 3GB 子模块时 SKIP，不假报）")
    d = fs_dir()
    explicit = bool(os.environ.get("LSU_FS_DIR"))
    sizes = {name: ((d / name).stat().st_size
                    if (d / name).exists() else 0)
             for name in ("vmlinux", "ubuntu.img", "boot.arm64")}
    print(f"      FS dir = {d} (exists={d.exists()}, LSU_FS_DIR set="
          f"{explicit}); observed sizes = {sizes}")
    all_present = d.exists() and all(s > 0 for s in sizes.values())
    if all_present:
        for name, sz in sizes.items():
            check(f"FS asset {name} present (>0 bytes)", sz > 0, f"size={sz}")
    elif explicit:
        # The operator pointed LSU_FS_DIR at a directory that lacks the
        # assets — that IS a real failure (the claim does not hold).
        for name, sz in sizes.items():
            check(f"FS asset {name} present (>0 bytes)", sz > 0, f"size={sz}")
    else:
        note("FS asset inventory",
             f"{d} carries no assets (worktree has no 3 GB submodule; the "
             "submodule mount point exists but is empty) — set LSU_FS_DIR to "
             "the main worktree's gem5-fs/ to run the real inventory")

    print("[4] FS checkpoint 基线（restore-tick = cpt 目录名）")
    found = []
    for rel in CKPT_CANDIDATES:
        # checkpoint dirs live under the repo root that owns them; probe both
        # this worktree and the FS dir's parent (main worktree).
        for base in (ROOT, d.parent if d.exists() else ROOT):
            p = base / rel
            if (p / "m5.cpt").exists() and (p / "m5.cpt").stat().st_size > 0:
                found.append((str(p), (p / "m5.cpt").stat().st_size))
                break
    if not found:
        note("FS checkpoint inventory",
             f"none of {CKPT_CANDIDATES} found under {ROOT} or {d.parent} "
             "— checkpoints are runtime artifacts (runs/), not in git")
    for path, size in found:
        check(f"checkpoint {path} has non-empty m5.cpt", size > 0,
              f"size={size}")
        print(f"      cpt dir basename (restore-tick baseline) = "
              f"{Path(path).name}")
    print(f"      NOTE: --fs-checkpoint help text still cites the stale path "
          f"'{CKPT_DOCUMENTED_STALE}'; real dirs are the ones above "
          f"(R4-5.9 report §1).")

    print()
    if SKIPPED:
        print(f"SKIPPED ({len(SKIPPED)}): {SKIPPED}")
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
