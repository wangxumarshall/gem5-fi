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
    check("FS platform is SINGLE-CORE (num_cores=1) — FS-MULTICORE needs a "
          "config change, not just a run",
          "num_cores=1" in src, "num_cores=1 not found")

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

    print("[5] FS-INFRA 24 行：逐行的**精确**残余阻塞（R4-8）")
    # 每一行都必须落在 {FS flags | 精确 MODE-UNIMPL | MODEL_BLOCKED(T08)} 之一。
    # T05/T06/T07 的模式在 CHAOSArmTLB 里**不存在**（只有 bit_flip /
    # stuck_at_zero|one / pfn_to_mapped_page / walk_pairing），故精确理由是
    # "mode unimplemented"而非过宽的"fs-infra"——此处把它钉死，防止任何一行
    # 在无声中被解锁。
    import lsu_campaign as _lc
    _hdr, _cells = _lc.load_matrix(
        ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")
    _byid = {c[_lc.COL_RUNID]: c for c in _cells}
    FS_INFRA = ["T01-F0-W4", "T01-F1-W4", "T01-F2-W4", "T02-F0-W4", "T02-F2-W4",
                "T03-F5-W4", "T04-F0-W4", "T04-F2-W4", "T04-F6-W4",
                "T05-F0-W4", "T05-F2-W4", "T05-F6-W4",
                "T06-F0-W4", "T06-F2-W4", "T06-F6-W4",
                "T07-F0-W4", "T07-F4-W4", "T07-F6-W4",
                "T08-F0-W4", "T08-F4-W4", "T08-F6-W4",
                "T10-F0-W4", "T10-F1-W4", "T10-F2-W4"]
    check("FS-INFRA row list is exactly 24 rows", len(FS_INFRA) == 24)
    check("every FS-INFRA row is present in the matrix",
          all(r in _byid for r in FS_INFRA),
          str([r for r in FS_INFRA if r not in _byid]))
    _fs_run, _fs_modeblk, _fs_t08, _fs_other = [], [], [], []
    for r in FS_INFRA:
        f, g, k = _lc.resolve_cell(_byid[r])
        if f is not None and k == "fs:tlb_probe":
            _fs_run.append(r)
        elif f is None and k.startswith("deferred(mode unimplemented"):
            _fs_modeblk.append(r)
        elif f is None and "compile-unverified" in k:
            _fs_t08.append(r)              # T08: MODEL_BLOCKED, needs opt-in
        else:
            _fs_other.append((r, k))
    check("T01/T02/T03/T04/T10 W4 rows resolve to FS flag sets (12 rows)",
          _fs_run == ["T01-F0-W4", "T01-F1-W4", "T01-F2-W4", "T02-F0-W4",
                      "T02-F2-W4", "T03-F5-W4", "T04-F0-W4", "T04-F2-W4",
                      "T04-F6-W4", "T10-F0-W4", "T10-F1-W4", "T10-F2-W4"],
          str(_fs_run))
    check("T05/T06/T07 (9 rows) carry the PRECISE mode-unimplemented reason, "
          "not the over-broad fs-infra phrasing",
          sorted(_fs_modeblk) == sorted(
              [r for r in FS_INFRA if r.split("-")[0] in ("T05", "T06", "T07")]),
          str(_fs_modeblk))
    check("T08 W4 rows (3) are blocked ONLY by MODEL_BLOCKED (a landed "
          "compile-unverified model awaiting real-run evidence), not by a "
          "workload/mode gap",
          sorted(_fs_t08) == ["T08-F0-W4", "T08-F4-W4", "T08-F6-W4"],
          str(_fs_t08))
    check("no FS-INFRA row resolves to anything else", not _fs_other,
          str(_fs_other))
    check("the FS-INFRA reason is NEVER the bare workload-level fs-infra "
          "phrase for T05/T06/T07 (the R4-8 precision fix)",
          all("workload" not in k for _r, k in _fs_other))
    check("T05/T06/T07 are absent from MODEL_FLAGS (their modes do not exist "
          "in CHAOSArmTLB)",
          all(m not in _lc.MODEL_FLAGS for m in ("T05", "T06", "T07")))
    check("T05/T06/T07 are MODEL_BLOCKED with a mode-unimplemented reason",
          all("mode unimplemented" in _lc.MODEL_BLOCKED[m]
              for m in ("T05", "T06", "T07")))
    check("T08 resolves to FS flags under --allow-blocked-models (the opt-in "
          "that produces the real-run evidence)",
          _lc.resolve_cell(_byid["T08-F0-W4"], allow_blocked=True)[0] is not None
          and "walk_pairing" in _lc.resolve_cell(_byid["T08-F0-W4"],
                                                allow_blocked=True)[0])

    print("[6] W1(MiBench) 19 行口径订正（R4-8）：静态表已精确化")
    # 用户/编排侧裁决：二进制 + golden + 合法 SE 路径都在盘上 ⇒ 过宽的
    # WL_BLOCKED["MiBench"] 必须订正；只保留精确阻塞。本段把订正后的
    # 集合钉死（任何一行无声解锁/无声保留都会 fail）。
    check("WL_BLOCKED no longer carries the over-broad 'MiBench' key",
          "MiBench" not in _lc.WL_BLOCKED)
    check("WL_BLOCKED still carries the four precise blockers (not "
          "blanket-cleared)",
          set(_lc.WL_BLOCKED) == {"TLB-AliasPerm", "Atomic-Litmus", "PARSEC",
                                  "SPEC"},
          str(sorted(_lc.WL_BLOCKED)))
    check("W1 carrier has an SE binary mapping + golden",
          _lc.WL_BINARY.get("MiBench-TC23") == "mibench/bin/w1_all"
          and _lc.GOLDENS.get("mibench/bin/w1_all") == "6dab8ec221c46677")
    w1_bin = ROOT / "workloads" / "mibench" / "bin" / "w1_all"
    check("W1 binary exists on disk (workloads/mibench/bin/w1_all)",
          w1_bin.exists() and w1_bin.stat().st_size > 0,
          f"size={w1_bin.stat().st_size if w1_bin.exists() else 0}")
    W1_ROWS = ["S01-F0-W1", "S01-F1-W1", "S01-F2-W1", "S02-F0-W1", "S02-F2-W1",
               "C01-F0-W1", "C01-F1-W1", "C01-F2-W1", "C02-F0-W1", "C02-F2-W1",
               "C04-F0-W1", "C04-F1-W1", "C04-F2-W1", "S13-F0-W1", "S13-F1-W1",
               "S13-F2-W1", "L01-F0-W1", "L01-F1-W1", "L01-F2-W1"]
    check("W1 口径冲突行数 == 19 (the audit's scope)",
          len(W1_ROWS) == 19)
    _w1_run, _w1_span_block, _w1_other = [], [], []
    for r in W1_ROWS:
        f, g, k = _lc.resolve_cell(_byid[r])
        if f is not None:
            _cmd = f[f.index("--cmd") + 1]
            check(f"{r}: resolved --cmd path exists on disk",
                  Path(_cmd).exists(), _cmd)
            check(f"{r}: resolves to the frozen W1 golden",
                  g == "6dab8ec221c46677", str(g))
            _w1_run.append(r)
        elif "F0-span-unmeasured" in k:
            _w1_span_block.append(r)
        else:
            _w1_other.append((r, k))
    check("17/19 W1 rows resolve runnable (their --cmd path exists)",
          sorted(_w1_run) == sorted([r for r in W1_ROWS
                                     if r not in ("S01-F0-W1", "S02-F0-W1")]),
          str(_w1_run))
    check("the remaining 2 rows are blocked by the PRECISE F0-span-unmeasured "
          "gate (a per-(model,workload) census, NOT a workload block)",
          sorted(_w1_span_block) == ["S01-F0-W1", "S02-F0-W1"],
          str(_w1_span_block))
    check("no W1 row is workload-blocked or otherwise unexplained",
          not _w1_other, str(_w1_other))
    check("T-model W1 rows are UNCHANGED: still resolve to the armtlb FS flag "
          "set (the MiBench-key removal must not re-route them to SE)",
          all(_lc.resolve_cell(_byid[r])[0] is not None
              and "--cmd" not in _lc.resolve_cell(_byid[r])[0]
              for r in ("T01-F0-W1", "T01-F1-W1", "T01-F2-W1", "T02-F0-W1",
                        "T02-F2-W1", "T10-F0-W1", "T10-F1-W1", "T10-F2-W1")))
    check("W1 SE runs get lsu_runner's frozen SE_W1 budget (not --timeout 300, "
          "which would fabricate a Timeout at 7.4h golden)",
          _lc.SE_W1_TIMEOUT == 43200)
    check("wl_binary_path() resolves the W1 carrier to the real path",
          _lc.wl_binary_path("mibench/bin/w1_all").exists()
          and _lc.wl_binary_path("agu_addrmodes") ==
          ROOT / "workloads/directed/agu_addrmodes")

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
