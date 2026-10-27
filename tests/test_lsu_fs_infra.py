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

    print("[5] FS-INFRA 24 行：逐行的**精确**残余阻塞（R4-8 / R4-10）")
    # 每一行都必须落在 {FS flags | MODEL_BLOCKED(opt-in)} 之一。
    # [R4-10] T05/T06/T07 的模式**已实现**（R4-10：CHAOSArmTLB 的
    # valid_clear/valid_set/global_flip/asid_subst、perm_subst/memtype_subst/
    # pagesize_subst、false_hit/double_hit/wrong_way），故它们与 T08 一样
    # 落 MODEL_BLOCKED（理由 = landed/compile-unverified，只有
    # --allow-blocked-models 才放行），解析后走 FS flags。此前"absent from
    # MODEL_FLAGS + reason=mode unimplemented"的断言随实现落地而作废——
    # 此处改为钉**新的**语义不变量（模式已在 MODEL_FLAGS + 理由已诚实改写）。
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
    _fs_run, _fs_modeblk, _fs_modelblk, _fs_tierblk, _fs_other = [], [], [], [], []
    for r in FS_INFRA:
        f, g, k = _lc.resolve_cell(_byid[r])
        if f is not None and k == "fs:tlb_probe":
            _fs_run.append(r)
        elif f is None and k.startswith("deferred(mode unimplemented"):
            _fs_modeblk.append(r)
        elif f is None and _lc.MODEL_BLOCKED.get(r.split("-")[0]) == k:
            _fs_modelblk.append(r)   # T05/T06/T07/T08: MODEL_BLOCKED, opt-in
        elif f is None and k.startswith("BLOCKED(armtlb-lookup-tier"):
            # [MDSPEC][R6-FTIER] the lookup path never polls lsuTrigger, so a
            # lookup-mode cell with F != F0 is a loud BLOCKED, not a silent
            # F0 run (six first-wave RunIDs used to collapse to three
            # conditions this way). See tests/test_lsu_ftier_armtlb_lookup.py.
            _fs_tierblk.append(r)
        else:
            _fs_other.append((r, k))
    # [R6-PROPAGATION-V3 2026-10-27] The old split (4 runnable + 8 tier-blocked
    # + 12 MODEL_BLOCKED) is obsolete: the frozen binary carries the real
    # lookup tier and the T05/T06/T07 modes, so 21 of the 24 rows resolve to
    # the FS carrier.  The remaining 3 are T08-F0/F4/F6-W4, which are gated
    # by the explicit T08-a canary (whole model PARTIAL_SUBMODEL_PROVEN).
    expected_run = [r for r in FS_INFRA
                    if r not in ("T08-F0-W4", "T08-F4-W4", "T08-F6-W4")]
    check("21 FS rows resolve to FS flag sets (real tier modes landed)",
          _fs_run == expected_run,
          f"{len(_fs_run)} run: {_fs_run}")
    check("T08 W4/F6 rows are gated by the T08-a partial-submodel rule",
          sorted([r for r, _k in _fs_other] + _fs_modelblk + _fs_modeblk) ==
          ["T08-F0-W4", "T08-F4-W4", "T08-F6-W4"],
          str([r for r, _k in _fs_other] + _fs_modelblk + _fs_modeblk))
    check("no FS-INFRA row is refused with 'mode unimplemented'",
          not _fs_modeblk, str(_fs_modeblk))
    check("T05/T06/T07/T08 removed from MODEL_BLOCKED "
          "(stale compile-unverified gate deleted)",
          all(m not in _lc.MODEL_BLOCKED for m in
              ("T05", "T06", "T07", "T08")))
    check("T08 gate reason is the explicit PARTIAL_SUBMODEL_PROVEN text",
          all("PARTIAL_SUBMODEL_PROVEN" in k and "T08-a" in k
              for r, k in _fs_other if r.startswith("T08")))
    check("T08-W9 remains a hard workload gap (never tlb_probe)",
          all(_lc.resolve_cell(_byid[r], allow_blocked=True,
                               t08a_canary=True)[0] is None
              and _lc.resolve_cell(_byid[r], allow_blocked=True,
                                   t08a_canary=True)[2].startswith(
                                       "BLOCKED_WORKLOAD_GAP")
              for r in ("T08-F0-W9", "T08-F4-W9")))
    check("T05/T06/T07 ARE in MODEL_FLAGS (their modes are routed)",
          all(m in _lc.MODEL_FLAGS for m in ("T05", "T06", "T07")))
    check("T05/T06/T07 default flags carry their sub-model fault type",
          "valid_clear" in _lc.resolve_cell(_byid["T05-F0-W4"])[0]
          and "perm_subst" in _lc.resolve_cell(_byid["T06-F0-W4"])[0]
          and "false_hit" in _lc.resolve_cell(_byid["T07-F0-W4"])[0])

    print("[6] W1(MiBench) 19 行口径订正（R4-8）：静态表已精确化")
    # 用户/编排侧裁决：二进制 + golden + 合法 SE 路径都在盘上 ⇒ 过宽的
    # WL_BLOCKED["MiBench"] 必须订正；只保留精确阻塞。本段把订正后的
    # 集合钉死（任何一行无声解锁/无声保留都会 fail）。
    check("WL_BLOCKED no longer carries the over-broad 'MiBench' key",
          "MiBench" not in _lc.WL_BLOCKED)
    check("WL_BLOCKED still carries the four precise blockers (not "
          "blanket-cleared)",
          # [R4-8-INT] SPEC 键已由 r4-8-spec-residual 收窄为具名身份常量
          # (SPEC_WL_IDENTITY="SPEC CPU2017")，故按常量断言，避免键漂移。
          set(_lc.WL_BLOCKED) == {"TLB-AliasPerm", "Atomic-Litmus", "PARSEC",
                                  _lc.SPEC_WL_IDENTITY},
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
    # [MDSPEC][R6-FTIER] the invariant that matters here is "the MiBench-key
    # removal must not re-route T-cell W1 rows to SE": F0 rows still resolve
    # to the armtlb FS flag set; F!=F0 rows are now honestly BLOCKED by the
    # lookup-tier gate — neither may become an SE --cmd flag set.
    _tw1 = ("T01-F0-W1", "T01-F1-W1", "T01-F2-W1", "T02-F0-W1",
            "T02-F2-W1", "T10-F0-W1", "T10-F1-W1", "T10-F2-W1")
    check("T-model W1 rows are never re-routed to SE (no --cmd)",
          all(_lc.resolve_cell(_byid[r])[0] is None
              or "--cmd" not in _lc.resolve_cell(_byid[r])[0] for r in _tw1))
    check("T-model W1 F0 rows still resolve to the armtlb FS flag set",
          all(_lc.resolve_cell(_byid[r])[0] is not None
              and "--cmd" not in _lc.resolve_cell(_byid[r])[0]
              for r in ("T01-F0-W1", "T02-F0-W1", "T10-F0-W1")))
    # [R6-FIXTOOLS] The real lookup tier landed (6ec7c5aa), so these rows are
    # runnable WITH a real --tlb_lsu_tier flag — never re-routed to SE.
    check("T-model W1 F!=F0 rows carry the real tier (never SE --cmd)",
          all(_lc.resolve_cell(_byid[r])[0] is not None
              and "--tlb_lsu_tier" in _lc.resolve_cell(_byid[r])[0]
              and "--cmd" not in _lc.resolve_cell(_byid[r])[0]
              for r in ("T01-F1-W1", "T01-F2-W1", "T02-F2-W1",
                        "T10-F1-W1", "T10-F2-W1")))
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
