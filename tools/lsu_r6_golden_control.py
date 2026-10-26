#!/usr/bin/env python3
"""lsu_r6_golden_control.py — LSU R6 阴性/黄金对照（uninjected GOLDEN）入口。

它做且只做一件事：在**不注入任何故障**的前提下跑一次 FS B0 采样，并证明
注入路径**未被激活** —— `prop_evt` 流里 0 个 `kind=inj`、无 chain_end-per-fault。

与 campaign 的关系（诚实边界）：
  * 本入口是**对照**，不是 campaign；它不产生样本记账，不写 cell_results。
  * 二进制解析唯一走 `tools/lsu_gem5_bin.py`（`$LSU_GEM5_BIN` → 本 worktree
    CHAOS 构建；缺则响亮 SystemExit）。**绝不**回落主树 build/ARM/gem5.opt。

为什么要有它（实测，2026-10-23）：一个 golden 对照被主树二进制路径调用：
  runs/lsu/r6_tlb_verify/golden/run.log:
    timeout: 无法运行命令
    "/home/sdc/gem5-fi-ding/CHAOS/gem5/build/ARM/gem5.opt": No such file or directory
  对照从未运行。本入口把二进制解析与判据都钉死，并对"跑没跑完"做硬检查。

用法（FS 阴性对照，命令形状与 R6 采样一致）：
  LSU_GEM5_BIN=<worktree>/CHAOS/gem5/build/ARM/gem5.opt \
  LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs \
  python3 tools/lsu_r6_golden_control.py \
      --workdir <worktree-with-configs> \
      --outdir runs/lsu/r6_golden_verify \
      --restore-checkpoint runs/lsu/fs_cpt_boot/cpt.237949797015 \
      --run-id NEGATIVE-GOLDEN --sample-run-id s1 --timeout 3600

退出码：0 当且仅当 gem5 干净结束（m5 exit）且阴性判据 PASS。
"""
import argparse
import gzip
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lsu_gem5_bin as GB  # noqa: E402

REPO = HERE.parent

# 阴性判据关注的"故障链"事件类别（出现即说明注入路径被激活）
FAULT_CHAIN_KINDS = ("inj", "chain_end")


def kind_counts(path):
    """解析 prop_evt 流（`PROP-EVT: kind=X a=b ...`）为 {kind: count}。

    允许 .gz 或明文；缺失/不可读 → 空 dict（由调用方按"未完成"处理，
    绝不静默当成 0 故障的 PASS）。
    """
    p = Path(path)
    if not p.exists():
        return {}
    op = gzip.open if p.name.endswith(".gz") else open
    counts = {}
    try:
        with op(p, "rt", errors="replace") as fh:
            # [R6-STREAM] 逐行流式；禁止整体 read() 解压流（超大流会 OOM）。
            # 正则 `kind=([A-Za-z_]+)` 不含换行，逐行 finditer 与整串
            # finditer 的匹配集合完全一致（语义等价，见 Task 13 报告）。
            for line in fh:
                for m in re.finditer(r"kind=([A-Za-z_]+)", line):
                    k = m.group(1)
                    counts[k] = counts.get(k, 0) + 1
    except (OSError, EOFError):
        # 与旧实现一致：整串读取失败 → 空 dict（由调用方按"未完成"处理）。
        return {}
    return counts


def negative_verdict(counts):
    """阴性判据：无任何故障链事件 → PASS；否则 FAIL。

    诚实口径：counts 为空 dict 时判 PASS 的前提是**运行确已完成**（由调用方
    以 stats.txt + `Exiting @ tick` 核验后传入）；本函数只判事件内容。
    """
    present = {k: counts[k] for k in FAULT_CHAIN_KINDS if counts.get(k)}
    if present:
        return {"verdict": "FAIL",
                "detail": f"fault-chain events present: {present}",
                "total_events": sum(counts.values())}
    return {"verdict": "PASS",
            "detail": "no inj / chain_end — injection path proven inactive",
            "total_events": sum(counts.values())}


def build_cmd(gem5_bin, outdir, checkpoint, kernel, disk, bootloader,
              readfile, run_id, sample_run_id, config="configs/fs/lsu_b0_fs.py",
              ckpt_first_clock=True):
    """组装 FS 阴性对照命令行（命令形状由 R6 采样契约固定）。"""
    cmd = [str(gem5_bin), "--outdir", str(outdir), str(config),
           "--restore-checkpoint", str(checkpoint),
           "--kernel", str(kernel), "--disk", str(disk),
           "--bootloader", str(bootloader), "--cpu", "O3",
           "--readfile", str(readfile)]
    if ckpt_first_clock:
        cmd.append("--ckpt-first-clock")
    cmd += ["--chaos_propagation",
            "--prop_run_id", str(run_id),
            "--prop_sample_run_id", str(sample_run_id)]
    return cmd


def stream_status(path):
    """prop_evt 流的完整性：present / readable / truncated。

    未注入对照里"0 个 inj"只有在**流完整**时才是真阴性。被杀/超时的 run 留下
    未收尾的 gzip —— 写侧只在 exit callback 里 `gzclose`（收尾标记），期间逐
    事件仅 `Z_SYNC_FLUSH` —— 读到最后会抛 EOFError。实测
    `runs/lsu/r6_tlb_negative2/seed1/prop_evt.txt.gz` 238 B（仅表头）
    → `EOFError: Compressed file ended before the end-of-stream marker`。
    """
    p = Path(path)
    st = {"path": str(p), "present": p.exists(), "readable": False,
          "truncated": False, "error": None}
    if not st["present"]:
        return st
    op = gzip.open if p.name.endswith(".gz") else open
    try:
        with op(p, "rt", errors="replace") as fh:
            # [R6-STREAM] 逐行流式消费以触达 gzip 收尾标记；禁止整体 read()
            # （超大流会 OOM，而本函数只关心"能否读到 EOF"）。迭代到文件末尾
            # 同样会触发截断流的 EOFError，故 readable/truncated 语义不变。
            for _ in fh:
                pass
        st["readable"] = True
    except EOFError as e:
        st["truncated"] = True
        st["error"] = f"{type(e).__name__}: {e}"
    except OSError as e:
        st["error"] = f"{type(e).__name__}: {e}"
    return st


def run_completed(outdir, evt_path):
    """gem5 是否**干净跑完**：stats.txt 非空**且** prop_evt 流完整。

    被杀/超时的 run 会留下 0 字节 stats.txt 与截断的 .gz 流 —— 那种流里的
    "0 个 inj" 是**伪阴性**，必须与真阴性区分开（本仓库明确禁止静默零）。
    """
    stats = Path(outdir) / "stats.txt"
    if not stats.exists() or stats.stat().st_size == 0:
        return False, "stats.txt 缺失或为 0 字节（run 未完成/被杀）"
    st = stream_status(evt_path)
    if not st["present"]:
        return False, f"prop_evt 流缺失: {evt_path}"
    if not st["readable"]:
        return False, f"prop_evt 流不可完整读取（截断/损坏）: {st['error']}"
    return True, "stats.txt 非空且 prop_evt 流完整（含 gzip 收尾标记）"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=str(REPO),
                    help="含 configs/ 的 checkout（默认=本 checkout）")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--restore-checkpoint", required=True)
    ap.add_argument("--run-id", default="NEGATIVE-GOLDEN")
    ap.add_argument("--sample-run-id", default="s1")
    ap.add_argument("--timeout", type=int, default=3600,
                    help="硬超时（秒）；超时 → 判 FAIL（未完成）")
    ap.add_argument("--fs-dir", default=None)
    ap.add_argument("--readfile", default="configs/fs/tlb_probe.rcS")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    fs_dir = Path(args.fs_dir or os.environ.get(
        "LSU_FS_DIR", str(workdir / "gem5-fs")))
    outdir = Path(args.outdir).resolve() / args.sample_run_id
    outdir.mkdir(parents=True, exist_ok=True)

    gem5 = GB.resolve_gem5_bin(repo=workdir)
    cfg = str(workdir / "configs/fs/lsu_b0_fs.py")
    cmd = build_cmd(gem5, outdir, args.restore_checkpoint,
                    fs_dir / "vmlinux", fs_dir / "ubuntu.img",
                    fs_dir / "boot.arm64", args.readfile,
                    args.run_id, args.sample_run_id, config=cfg)

    print(f"[golden] gem5     = {GB.describe(repo=workdir)}")
    print(f"[golden] workdir  = {workdir}")
    print(f"[golden] cfg      = {cfg}")
    print(f"[golden] outdir   = {outdir}")
    print(f"[golden] timeout  = {args.timeout}s")
    if args.dry_run:
        print("[golden][dry-run] " + " ".join(cmd))
        return 0

    t0 = time.time()
    try:
        r = subprocess.run(["timeout", str(args.timeout)] + cmd,
                           cwd=str(workdir), capture_output=True, text=True)
        rc = r.returncode
        tail = (r.stdout or "")[-2000:] + (r.stderr or "")[-2000:]
    except FileNotFoundError as e:
        print(f"[golden] FAIL: 无法启动 gem5: {e}")
        return 2
    wall = time.time() - t0
    (outdir / "golden_run.log").write_text(
        f"# cmd: {' '.join(cmd)}\n# rc={rc} wall={wall:.1f}s\n" + tail,
        encoding="utf-8")

    evt = outdir / "prop_evt.txt.gz"
    if not evt.exists():
        evt = outdir / "prop_evt.txt"
    completed, why = run_completed(outdir, evt)
    counts = kind_counts(evt)
    v = negative_verdict(counts)
    sst = stream_status(evt)

    print(f"[golden] rc={rc} wall={wall:.1f}s completed={completed} ({why})")
    print(f"[golden] stream    = {evt} present={sst['present']} "
          f"readable={sst['readable']} truncated={sst['truncated']}")
    print("[golden] kind counts:")
    for k, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"    {n:8d}  {k}")
    if not counts:
        print("    (no events)")

    result = {"run_id": args.run_id, "sample_run_id": args.sample_run_id,
              "gem5_bin": str(gem5), "rc": rc, "wall_s": round(wall, 1),
              "completed": completed, "completed_detail": why,
              "evt_path": str(evt), "stream": sst,
              "kind_counts": counts, **v}
    (Path(args.outdir).resolve() / "golden_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    ok = completed and v["verdict"] == "PASS"
    print(f"[golden] VERDICT = {'PASS' if ok else 'FAIL'} "
          f"({v['verdict']}; completed={completed})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
