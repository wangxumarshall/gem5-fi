#!/usr/bin/env python3
"""lsu_runner.py — V2.0 清单 ITEM → 不可变 run manifest → 守卫命令（P1 runner 契约）。

调度协议（task_plan.md 清单调度协议 1-7）的实现：
  1. 从 完整任务执行清单.md 解析 ITEM-001..325（唯一实验项集合，不读 Excel 行）
  2. 生成不可变 run manifest（调度协议第 3 条全字段；缺字段/不一致 → BLOCKED 报错退出，
     绝不用默认值补全）
  3. 构造守卫命令：家族 mount/tier/seed flags 复用 tools/lsu_campaign.py 的映射
     （MODEL_FLAGS/MODEL_BLOCKED/FAMILY_*——One mapping, no drift）
  4. F0 两遍法（F-012）：事件归一化家族（addrpath/lsqfwd/prefetch）先跑计数 pass
     （span=INT64_MAX 永不注入，读 CHAOS_LSU_TRIGGER eligible=N），正式 run span=N
     == Excel F0 全流均匀语义；cache/exmon/armtlb 为 legacy 机制无 span
  5. 执行经 tools/lsu_guard.py（experiment 锁单实例、60s 采样、max-seconds timeout）

用法：
  生成 manifest：python3 tools/lsu_runner.py --item ITEM-001 --phase engineering \
                     --sample-index 0 --output runs/lsu/manifests/ITEM-001_eng_s0.json
  校验+dry-run： python3 tools/lsu_runner.py --manifest <path> --dry-run
  执行：          python3 tools/lsu_runner.py --manifest <path> --execute [--outdir-root runs/lsu]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_campaign as LC  # 家族映射唯一来源（no drift）
from lsu_seed import lsu_seed

CHECKLIST = REPO / "docs/gem5-fi/lsu/完整任务执行清单.md"
LSU_PROXY = REPO / "configs/se/lsu_proxy.py"
GUARD = REPO / "tools/lsu_guard.py"
FS_CONFIG = LC.FS_CONFIG
FS_CARRIER_RC = LC.FS_CARRIER_RC
CPT = REPO / "runs/lsu/fs_cpt_boot/cpt.237949797015"  # G0-06 固化的 B0 FS checkpoint
TIMEOUTS = {"SE": 600, "FS": 1800}  # G0-09：SE=golden10×，FS 绝对上限
PHASES = ["engineering", "pilot", "screening", "confirmatory", "sensitivity", "reproduction"]

ITEM_RE = re.compile(r"^### (ITEM-\d{3}) — (\S+)$", re.M)
FIELD_RE = re.compile(r"^- \*\*(.+?)：\*\* ?(.*)$", re.M)
W_RE = re.compile(r"(MiniCheck|MiBench|BEEBS|AGU-AddrModes|TLB-AliasPerm|SQ-Forward|"
                  r"Cache-DirtyEvict|Atomic-Litmus|Prefetch-Stride|GAP|STREAM|SPEC|SQLite|PARSEC)")


def parse_items():
    """清单 → {ITEM: {run_id, fields...}}（唯一实验项集合）。"""
    text = CHECKLIST.read_text(encoding="utf-8")
    blocks, matches = [], list(ITEM_RE.finditer(text))
    for i, m in enumerate(matches):
        seg = text[m.start():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        fields = dict(FIELD_RE.findall(seg))
        blocks.append((m.group(1), m.group(2), fields))
    return blocks


def detect_workload_key(fields):
    """负载字段 → W 键（与 campaign WL_BINARY/WL_BLOCKED 对齐）。"""
    wl = fields.get("负载", "") + " " + fields.get("负载/oracle", "")
    m = W_RE.search(wl)
    return m.group(1) if m else None


def build_manifest(item_id, phase, sample_index, extra=None):
    blocks = parse_items()
    hit = [b for b in blocks if b[0] == item_id]
    if not hit:
        sys.exit(f"ERROR: {item_id} 不在清单（ITEM-001..325）")
    _, run_id, fields = hit[0]
    runid_m = re.match(r"([A-Z]\d+)-(F\d)-(W\d+)", run_id)
    if not runid_m:
        sys.exit(f"ERROR: RunID 格式 {run_id}")
    model, freq, wtag = runid_m.groups()
    wl_key = detect_workload_key(fields)

    # 模型级映射（唯一来源 campaign.py）；BLOCKED → 拒绝生成 manifest（不补默认值）
    if model in LC.MODEL_BLOCKED:
        sys.exit(f"BLOCKED: {model} → {LC.MODEL_BLOCKED[model]}（清单执行规则 4："
                 f"不得静默近似；如需解除须补实现 + Decision Request）")
    if model not in LC.MODEL_FLAGS:
        sys.exit(f"BLOCKED: {model} NOT-MAPPED（47 可运行模型之外）")
    family, extra_flags = LC.MODEL_FLAGS[model]

    # workload 解析
    if family == "armtlb":
        carrier = "fs:tlb_probe"
        wl_binary = None
        golden = LC.TLB_PROBE_GOLDEN
    else:
        wl_binary = None
        for key, bin_name in LC.WL_BINARY.items():
            if wl_key and key in wl_key:
                wl_binary = bin_name
                break
        if wl_binary is None:
            sys.exit(f"BLOCKED: workload '{wl_key}' 无 SE 二进制（W1/W4/W7/W11/W13 → "
                     f"DR-001，BLOCKED 不替换）")
        golden = LC.GOLDENS[wl_binary]
        carrier = f"se:{wl_binary}"

    seed = lsu_seed(run_id, phase, sample_index)
    manifest = {
        "immutable": True,
        "item": item_id,
        "run_id": run_id,
        "excel_location": fields.get("Excel 定位", "n/a"),
        "model_id": model,
        "unit": fields.get("单元", "n/a"),
        "fault_type": fields.get("故障类型", "n/a"),
        "submodels": fields.get("故障表现形式/子模型", "n/a"),
        "frequency": freq,
        "workload": fields.get("负载", "n/a"),
        "carrier": carrier,
        "trigger_condition": fields.get("触发条件", "n/a"),
        "phase": phase,
        "sample_index": sample_index,
        "seed": seed,
        "seed_rule": "tools/lsu_seed.py（sha256('lsu-fi-v1|RunID|phase|idx') 低64位大端）",
        "identity": {
            "git_commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                         capture_output=True, text=True).stdout.strip(),
            "gem5_opt_sha256": _sha(REPO / "build/ARM/gem5.opt"),
            "lsu_proxy_sha256": _sha(LSU_PROXY),
            "lsu_campaign_sha256": _sha(REPO / "tools/lsu_campaign.py"),
            "workload_sha256": _sha(REPO / "workloads/directed" / wl_binary) if wl_binary else None,
            "checkpoint": str(CPT) if family == "armtlb" else "none (SE)",
        },
        "config": {"cpu": "O3", "variant": "B0", "maxinsts": 0},
        "family": family,
        "injector_flags": list(extra_flags),
        "golden": golden,
        "timeout_seconds": TIMEOUTS["FS" if family == "armtlb" else "SE"],
        "f0_span_rule": ("两遍法（F-012）：计数 pass 定 N，正式 span=N" if freq == "F0"
                         and family in ("addrpath", "lsqfwd", "prefetch") else
                         ("legacy 机制（无 span）" if family in ("cache", "exmon", "armtlb")
                          else "n/a")),
        "guard": "tools/lsu_guard.py experiment 锁单实例 + 60s 采样 + max-seconds",
    }
    if extra:
        manifest.update(extra)
    return manifest


def _sha(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_guard_cmd(manifest, outdir, span=None):
    """manifest → 守卫 gem5 命令参数（不含守卫包装层）。"""
    fam, freq = manifest["family"], manifest["frequency"]
    if fam == "armtlb":
        args = ["--kernel", str(LC.FS_KERNEL), "--disk", str(LC.FS_DISK),
                "--bootloader", str(LC.FS_BOOTLOADER), "--cpu", "O3",
                "--restore-checkpoint", str(CPT),
                "--readfile", str(FS_CARRIER_RC), "--ckpt-first-clock",
                "--chaos_armtlb", "--tlb_first_clock", "1000",
                "--tlb_probability", "1.0", "--tlb_max_faults", "1"] + manifest["injector_flags"]
        args += ["--tlb_rng_seed", str(manifest["seed"])]
        config = str(FS_CONFIG)
    else:
        args = ["--cmd", str(REPO / "workloads/directed" / manifest["carrier"].split(":")[1]),
                "--cpu", "O3", "--variant", "B0"]
        args += LC.FAMILY_MOUNT[fam]
        tier = LC.FAMILY_TIER_FLAGS[fam](freq)
        if span is not None:
            # F0 两遍法：把 tier flags 里的 span 值替换为实测 N
            tier = [str(span) if (tier[i - 1].endswith("span_events")) else v
                    for i, v in enumerate(tier)]
        args += tier
        args += manifest["injector_flags"]
        args += [LC.FAMILY_SEED[fam], str(manifest["seed"])]
        config = str(LSU_PROXY)
    return config, args


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--item")
    g.add_argument("--manifest")
    ap.add_argument("--phase", choices=PHASES)
    ap.add_argument("--sample-index", type=int)
    ap.add_argument("--output")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--outdir-root", default="runs/lsu")
    args = ap.parse_args()

    if args.item:
        if not (args.phase and args.sample_index is not None and args.output):
            ap.error("--item 需要 --phase --sample-index --output")
        m = build_manifest(args.item, args.phase, args.sample_index)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(m, ensure_ascii=False, indent=1))
        print(f"manifest 冻结: {args.output}")
        print(json.dumps({k: m[k] for k in
                          ("item", "run_id", "family", "carrier", "seed", "timeout_seconds")},
                         ensure_ascii=False))
        return

    m = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    tag = f"{m['item']}_{m['phase']}_s{m['sample_index']}"
    outdir = Path(args.outdir_root) / m["phase"] / tag
    two_pass = m["frequency"] == "F0" and m["family"] in ("addrpath", "lsqfwd", "prefetch")

    if args.dry_run:
        print(f"[dry-run] {tag} family={m['family']} carrier={m['carrier']} "
              f"golden={m['golden']} timeout={m['timeout_seconds']}s "
              f"two_pass={two_pass}")
        cfg, c = build_guard_cmd(m, outdir, span="<N:计数pass实测>" if two_pass else None)
        print(f"[dry-run] 守卫命令: gem5.opt --outdir={outdir} {cfg} " + " ".join(c))
        return

    if not args.execute:
        ap.error("需要 --dry-run 或 --execute")

    # F0 两遍法：计数 pass
    span = None
    if two_pass:
        cnt_dir = outdir.parent / (tag + "_count")
        cfg, c = build_guard_cmd(m, cnt_dir, span=2**63 - 1)
        r = subprocess.run(["python3", str(GUARD), "run", "--type", "experiment",
                            "--desc", f"COUNT {tag}", "--log",
                            str(outdir.parent / (tag + "_count_rsrc.log")),
                            "--interval", "60", "--max-seconds", str(m["timeout_seconds"]),
                            "--", str(REPO / "build/ARM/gem5.opt"),
                            "--outdir", str(cnt_dir), cfg] + c,
                           capture_output=True, text=True)
        n = re.search(r"CHAOS_LSU_TRIGGER: .*eligible=(\d+)", r.stdout)
        if not n or int(n.group(1)) <= 0:
            sys.exit(f"ERROR: 计数 pass 失败（eligible=0 或缺失）: {r.stdout[-500:]}")
        span = int(n.group(1))
        print(f"[two-pass] 全流 eligible N={span} → 正式 span={span}")

    cfg, c = build_guard_cmd(m, outdir, span=span)
    r = subprocess.run(["python3", str(GUARD), "run", "--type", "experiment",
                        "--desc", f"RUN {tag}", "--log",
                        str(outdir.parent / (tag + "_rsrc.log")),
                        "--interval", "60", "--max-seconds", str(m["timeout_seconds"]),
                        "--", str(REPO / "build/ARM/gem5.opt"),
                        "--outdir", str(outdir), cfg] + c)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
