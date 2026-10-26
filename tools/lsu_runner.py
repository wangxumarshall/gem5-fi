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
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_campaign as LC  # 家族映射唯一来源（no drift）
import lsu_gem5_bin as GB  # [R6-GOLDEN] 二进制解析唯一来源
from lsu_seed import lsu_seed

L5 = REPO / "tools/lsu_l5_classify.py"

CHECKLIST = REPO / "docs/gem5-fi/lsu/完整任务执行清单.md"
LSU_PROXY = REPO / "configs/se/lsu_proxy.py"
GUARD = REPO / "tools/lsu_guard.py"
FS_CONFIG = LC.FS_CONFIG
FS_CARRIER_RC = LC.FS_CARRIER_RC
CPT = REPO / "runs/lsu/fs_cpt_boot/cpt.237949797015"  # G0-06 固化的 B0 FS checkpoint（历史默认）
# [0202-REBUILD] checkpoint 身份唯一解析入口。重建后的 B0 checkpoint 是新生成的
# 真实 `cpt.<tick>`；**绝不**把新 cpt 改名/软链成旧名来冒充身份。
FS_CHECKPOINT_ENV = "LSU_FS_CHECKPOINT"


def resolve_fs_checkpoint(explicit=None):
    """[0202-REBUILD] B0 FS checkpoint 解析（唯一来源）。

    优先级：显式参数（`--fs-checkpoint`）→ 环境变量 `LSU_FS_CHECKPOINT` → 历史默认
    (`CPT`)。解析结果写进 `manifest.identity.checkpoint`，并由 `build_guard_cmd`
    直接消费——身份与命令同源，不会静默分歧。
    """
    cand = explicit or os.environ.get(FS_CHECKPOINT_ENV)
    return Path(cand) if cand else CPT


def g5_path():
    """[LSU][OBS-3] gem5 二进制路径：LSU_GEM5_BIN 覆盖 → **本 checkout** 的
    CHAOS 构建（`CHAOS/gem5/build/ARM/gem5.opt`）。

    [R6-GOLDEN] 此前默认回落到 repo 根 `build/ARM/gem5.opt` —— 那是**主树专用**
    约定（历史里 `build/ARM` 是指向主树 `CHAOS/gem5/build/ARM` 的符号链接）。
    worktree 里该路径不存在，而未设 `LSU_GEM5_BIN` 的 golden 运行会因此指向
    别的 track 的二进制（实测失败：
    `runs/lsu/r6_tlb_verify/golden/run.log` → timeout: 无法运行命令
    .../CHAOS/gem5/build/ARM/gem5.opt: No such file or directory）。
    默认值改为本 checkout 的 CHAOS 构建；冻结 sha256 仍记入 manifest identity，
    绝不重编/替换。
    """
    return GB.resolve_default_gem5_bin()
# G0-09 分级口径（2026-10-11 W1 timeout 修复，无人值守决策树步骤 10）：
#   SE 短流（W0/W2/W3/W5/W9 等）golden ≤61s → 600s（10×）不变；
#   W1 w1_all 长流 golden 实测 7.44-7.51h（F-050 三副本，规范哈希五方全等）
#   → 600s 会把每个 W1 运行判为伪 Timeout——SE_W1=43200s（12h 预算，
#   与 golden 链式控制器 --max-seconds 一致）。
#   [0202-REBUILD] FS 由 1800 → **2700**：实测 0202 无注入 golden（同一 checkpoint +
#   tlb_probe.rcS 全 10 轮载荷）wall = 2274 s（19:54:47 → 20:32:41），**> 1800** ——
#   1800 会把干净跑完的整载荷 run 判成 Timeout 并截断证据。2700 是仓库既定
#   "已知良好预算"（campaign FS_TIMEOUT_DEFAULT=2700，测试
#   tests/test_lsu_campaign_timeout.py 钉死），此处与之对齐，不静默降低。
TIMEOUTS = {"SE": 600, "SE_W1": 43200, "FS": 2700}

def _wl_path(wl_binary):
    """[LSU][W1-REG] 负载二进制路径：9 个 directed 载体在 workloads/directed/，
    W1 w1_all 在 workloads/mibench/bin/——directed 优先、workloads 根回退。"""
    p = REPO / "workloads/directed" / wl_binary
    return p if p.exists() else REPO / "workloads" / wl_binary
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


SEED_RULE_DERIVED = "tools/lsu_seed.py（sha256('lsu-fi-v1|RunID|phase|idx') 低64位大端）"
SEED_RULE_EXPLICIT = ("显式整数 seed（--explicit-seed）：直接作为 --tlb_rng_seed 下发，"
                      "不派生；用于复现 0101 campaign 的整数 seed 系列（seed1==1）")


def run_tag(manifest):
    """运行目录标签。derived 用 sample_index（`s<idx>`），explicit 用 seed 原值
    （`x<seed>`）——两者是**不同的身份轴**，不得混用同一个标签（避免把
    `sample_index=0` 误读成"数值 seed1"）。"""
    if manifest.get("seed_source") == "explicit":
        return f"{manifest['item']}_{manifest['phase']}_x{manifest['explicit_seed']}"
    return f"{manifest['item']}_{manifest['phase']}_s{manifest['sample_index']}"


def build_manifest(item_id, phase, sample_index, extra=None, carrier_text=None,
                   fs_checkpoint=None, explicit_seed=None):
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

    # [0202-REBUILD][R6-FTIER] F 档路由：armtlb lookup 家族 F1–F6 必须真实挂载
    # lookup tier，否则该次运行在物理上退化为 F0——把 F0 结果标成 F2/F6 是禁止的
    # （实测：修复前 T02-F2-W4 / T04-F2-W4 / T04-F6-W4 的 injector_flags 与各自
    # F0 兄弟逐字节相同，即经 runner 必然坍缩）。映射复用 campaign 的唯一来源
    # （`_armtlb_lookup_tier_flags`，One mapping, no drift）；未知档位 → 响亮拒绝，
    # 绝不静默改档。
    if family == "armtlb":
        _tier_flags = LC._armtlb_lookup_tier_flags(freq)
        if _tier_flags is None:
            sys.exit("BLOCKED: " + LC._armtlb_lookup_tier_block_reason(model, freq))
        extra_flags = list(extra_flags) + _tier_flags

    # workload 解析
    if family == "armtlb":
        carrier = "fs:tlb_probe"
        wl_binary = None
        golden = LC.TLB_PROBE_GOLDEN
    else:
        # 完整负载文本匹配（与 unit_pilot.eligible 同口径）。此前用提取键
        # `key in wl_key` 方向反了："GAP/Graph500" in "GAP" 恒 False →
        # ITEM-002(A01-F0-W9) sys.exit(BLOCKED) 杀死整个 AGU unit_pilot
        # （事故 F-018，2026-09-29 19:48）。
        wl_text = fields.get("负载", "") + " " + fields.get("负载/oracle", "")
        if carrier_text:
            # [LSU][W1-RERUN] D-2026-10-09-重跑：RunID 不变、载体改指（清单负载
            # 字段保持原样归档，campaign 记录改指事实——不篡改权威清单）。
            wl_text = carrier_text
        wl_binary = None
        for key, bin_name in LC.WL_BINARY.items():
            if key in wl_text:
                wl_binary = bin_name
                break
        if wl_binary is None:
            sys.exit(f"BLOCKED: workload '{wl_text[:40]}' 无 SE 二进制（W1/W4/W7/W11/W13 → "
                     f"DR-001，BLOCKED 不替换）")
        golden = LC.GOLDENS[wl_binary]
        carrier = f"se:{wl_binary}"

    # [0202-T02F2] seed 身份：derived（sample_index → 哈希）与 explicit（整数原值）
    # 是**互斥**的两条轴。同时给出即冲突（响亮失败），不能一边说 sample_index
    # 一边让别人以为是那个数值 seed。
    if explicit_seed is not None and sample_index is not None:
        sys.exit("ERROR: --sample-index 与 --explicit-seed 互斥（前者派生哈希 seed，"
                 "后者直接指定整数 RNG seed；0101 campaign 的整数 seed1 == 1，"
                 "而 0202 sample_index=0 派生出的是 64 位哈希，二者不是同一个 seed）")
    if explicit_seed is not None:
        try:
            explicit_seed = int(explicit_seed)
        except (TypeError, ValueError):
            sys.exit(f"ERROR: --explicit-seed 必须为整数，收到 {explicit_seed!r}")
        if explicit_seed < 0:
            sys.exit(f"ERROR: --explicit-seed 不得为负（收到 {explicit_seed}）")
        seed = explicit_seed
        seed_source = "explicit"
        seed_rule = SEED_RULE_EXPLICIT
    else:
        if sample_index is None:
            sys.exit("ERROR: 需要 --sample-index（派生 seed）或 --explicit-seed（显式整数 seed）之一")
        seed = lsu_seed(run_id, phase, sample_index)
        seed_source = "derived"
        seed_rule = SEED_RULE_DERIVED
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
        "seed_source": seed_source,
        "seed_rule": seed_rule,
        "explicit_seed": (int(explicit_seed) if explicit_seed is not None else None),
        "identity": {
            "git_commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                         capture_output=True, text=True).stdout.strip(),
            "gem5_opt_sha256": _sha(g5_path()),
            "lsu_proxy_sha256": _sha(LSU_PROXY),
            "lsu_campaign_sha256": _sha(REPO / "tools/lsu_campaign.py"),
            "workload_sha256": _sha(_wl_path(wl_binary)) if wl_binary else None,
            "checkpoint": (str(resolve_fs_checkpoint(fs_checkpoint))
                           if family == "armtlb" else "none (SE)"),
        },
        "config": {"cpu": "O3", "variant": "B0", "maxinsts": 0},
        "family": family,
        "injector_flags": list(extra_flags),
        "golden": golden,
        "timeout_seconds": TIMEOUTS[
            "FS" if family == "armtlb"
            else ("SE_W1" if wl_binary and str(wl_binary).endswith("w1_all")
                  else "SE")],
        "f0_span_rule": ("两遍法（F-012）：计数 pass 定 N，正式 span=N" if freq == "F0"
                         and family in ("addrpath", "lsqfwd", "prefetch") else
                         ("legacy 机制（无 span）" if family in ("cache", "exmon", "armtlb")
                          else "n/a")),
        "guard": "tools/lsu_guard.py experiment 锁单实例 + 60s 采样 + max-seconds",
    }
    # [R6-FREQPOLICY] 频率策略 overlay：run_policy/required_seeds/include_in_
    # statistics 只读自带（tools/lsu_freq_policy.py 为唯一来源），runner 绝不
    # 重推导规则。overlay 可选——模块/JSON 缺失（异常）时跳过、键缺失；run_id
    # 不在 overlay（query 返回 SHORT dict、无 run_policy 键）时降级 "UNKNOWN"：
    # 两种情况都不阻塞 manifest 冻结。查询 seed 恒为 1——所携带三字段均为
    # run_id 级属性，与 seed 无关。
    try:
        import lsu_freq_policy as _FP
        _q = _FP.query(_FP.load_policy(), run_id, 1)
        manifest["run_policy"] = _q.get("run_policy", "UNKNOWN")
        manifest["required_seeds"] = _q.get("required_seeds")
        manifest["include_in_statistics"] = _q.get("include_in_statistics")
    except Exception:
        pass                                          # overlay optional; never block manifest freeze
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


def build_guard_cmd(manifest, outdir, span=None, fs_checkpoint=None):
    """manifest → 守卫 gem5 命令参数（不含守卫包装层）。"""
    fam, freq = manifest["family"], manifest["frequency"]
    if fam == "armtlb":
        # [0202-REBUILD] checkpoint 取自 manifest 身份（冻结时写入的真实路径）；
        # 命令行 `--fs-checkpoint` 只在身份缺失时补位，且不得与已冻结身份分歧。
        ckpt = manifest.get("identity", {}).get("checkpoint")
        if not ckpt or ckpt == "none (SE)":
            ckpt = str(resolve_fs_checkpoint(fs_checkpoint))
        elif fs_checkpoint is not None and str(resolve_fs_checkpoint(fs_checkpoint)) != ckpt:
            sys.exit("ERROR: --fs-checkpoint %s 与 manifest identity.checkpoint %s 不一致"
                     "（不得用命令行覆盖已冻结的 checkpoint 身份）"
                     % (resolve_fs_checkpoint(fs_checkpoint), ckpt))
        args = ["--kernel", str(LC.FS_KERNEL), "--disk", str(LC.FS_DISK),
                "--bootloader", str(LC.FS_BOOTLOADER), "--cpu", "O3",
                "--restore-checkpoint", str(ckpt),
                "--readfile", str(FS_CARRIER_RC), "--ckpt-first-clock",
                "--chaos_armtlb", "--tlb_first_clock", "1000",
                "--tlb_probability", "1.0", "--tlb_max_faults", "1"] + manifest["injector_flags"]
        args += ["--tlb_rng_seed", str(manifest["seed"])]
        # [0202-REBUILD][H0] 传播流必须挂载：不挂 CHAOSPropagation 就没有
        # prop_evt.txt.gz → 无 L0→L5 链证据（实测缺陷：T01-F0-W4 首跑只有
        # funnel/分类，无任何事件流）。复用 campaign 的唯一实现
        # `LC.propagation_flags(runid, seed)`（每事件带 run_id + sample_run_id，
        # One source, no drift）。
        args += LC.propagation_flags(manifest["run_id"], manifest["seed"])
        config = str(FS_CONFIG)
    else:
        args = ["--cmd", str(_wl_path(manifest["carrier"].split(":")[1])),
                "--cpu", "O3", "--variant", "B0"]
        args += LC.FAMILY_MOUNT[fam]
        # [R4-1-review-I2] tier flags are per (model, tier, workload); an
        # unmeasured lsqfwd F0 (model, workload) pair returns None → refuse
        # loudly (never silently reuse another pair's span in a guard run).
        wl_bin = manifest["carrier"].split(":")[1]
        tier = LC.FAMILY_TIER_FLAGS[fam](manifest.get("model_id", ""), freq,
                                         wl_bin)
        if tier is None:
            sys.exit("BLOCKED: F0 span unmeasured for (model %s, workload "
                     "%s, family %s) — measure its eligible stream and set "
                     "LSQFWD_F0_SPAN in tools/lsu_campaign.py"
                     % (manifest.get("model_id"), wl_bin, fam))
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
    ap.add_argument("--sample-index", type=int,
                    help="派生 seed 轴：seed = lsu_seed(run_id, phase, sample_index)。"
                         "注意 sample_index=0 **不是**「数值 seed1」。")
    ap.add_argument("--explicit-seed", type=int, default=None,
                    help="[0202-T02F2] 显式整数 RNG seed（直接作为 --tlb_rng_seed 下发），"
                         "用于复现 0101 campaign 的整数 seed 系列（seed1==1）。"
                         "与 --sample-index 互斥。")
    ap.add_argument("--output")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--outdir-root", default="runs/lsu")
    ap.add_argument("--fs-checkpoint", default=None,
                    help="[0202-REBUILD] 本次运行真实的 B0 FS checkpoint 目录 "
                         "(cpt.<tick>)。缺省时取 env LSU_FS_CHECKPOINT，再无则历史默认。"
                         "冻结进 manifest.identity，执行时不得与身份分歧。")
    args = ap.parse_args()

    if args.item:
        if not (args.phase and args.output):
            ap.error("--item 需要 --phase --output")
        if args.sample_index is None and args.explicit_seed is None:
            ap.error("--item 需要 --sample-index（派生 seed）或 --explicit-seed（显式整数 seed）")
        if args.sample_index is not None and args.explicit_seed is not None:
            ap.error("--sample-index 与 --explicit-seed 互斥（seed 身份只能有一条轴）")
        m = build_manifest(args.item, args.phase, args.sample_index,
                           fs_checkpoint=args.fs_checkpoint,
                           explicit_seed=args.explicit_seed)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(m, ensure_ascii=False, indent=1))
        print(f"manifest 冻结: {args.output}")
        print(json.dumps({k: m[k] for k in
                          ("item", "run_id", "family", "carrier", "seed", "timeout_seconds")},
                         ensure_ascii=False))
        return

    m = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    tag = run_tag(m)
    outdir = Path(args.outdir_root) / m["phase"] / tag
    two_pass = m["frequency"] == "F0" and m["family"] in ("addrpath", "lsqfwd", "prefetch")

    if args.dry_run:
        print(f"[dry-run] {tag} family={m['family']} carrier={m['carrier']} "
              f"golden={m['golden']} timeout={m['timeout_seconds']}s "
              f"two_pass={two_pass}")
        cfg, c = build_guard_cmd(m, outdir, span="<N:计数pass实测>" if two_pass else None,
                                 fs_checkpoint=args.fs_checkpoint)
        print(f"[dry-run] 守卫命令: gem5.opt --outdir={outdir} {cfg} " + " ".join(c))
        return

    if not args.execute:
        ap.error("需要 --dry-run 或 --execute")

    # F0 两遍法：计数 pass
    span = None
    if two_pass:
        cnt_dir = outdir.parent / (tag + "_count")
        cfg, c = build_guard_cmd(m, cnt_dir, span=2**63 - 1,
                                 fs_checkpoint=args.fs_checkpoint)
        r = subprocess.run(["python3", str(GUARD), "run", "--type", "experiment",
                            "--desc", f"COUNT {tag}", "--log",
                            str(outdir.parent / (tag + "_count_rsrc.log")),
                            "--interval", "60", "--max-seconds", str(m["timeout_seconds"]),
                            "--", str(g5_path()),
                            "--outdir", str(cnt_dir), cfg] + c,
                           capture_output=True, text=True)
        n = re.search(r"CHAOS_LSU_TRIGGER: .*eligible=(\d+)", r.stdout)
        if not n or int(n.group(1)) <= 0:
            sys.exit(f"ERROR: 计数 pass 失败（eligible=0 或缺失）: {r.stdout[-500:]}")
        span = int(n.group(1))
        print(f"[two-pass] 全流 eligible N={span} → 正式 span={span}")

    cfg, c = build_guard_cmd(m, outdir, span=span, fs_checkpoint=args.fs_checkpoint)
    guard_out = outdir.parent / (tag + "_guard.out")
    with open(guard_out, "w") as gf:
        r = subprocess.run(["python3", str(GUARD), "run", "--type", "experiment",
                            "--desc", f"RUN {tag}", "--log",
                            str(outdir.parent / (tag + "_rsrc.log")),
                            "--interval", "60", "--max-seconds", str(m["timeout_seconds"]),
                            "--", str(g5_path()),
                            "--outdir", str(outdir), cfg] + c,
                           stdout=gf, stderr=subprocess.STDOUT)
    # L5 分类（P1 收尾集成）：守卫合并流同时作 stdout/stderr（panic 栈在合并流中）
    gtxt = guard_out.read_text(errors="replace")
    ec = re.search(r'"exit_code": (-?\d+)', gtxt)
    gem5_exit = int(ec.group(1)) if ec else r.returncode
    cls = subprocess.run(["python3", str(L5), "--run-dir", str(outdir),
                          "--stdout", str(guard_out), "--stderr", str(guard_out),
                          "--golden", str(m["golden"]), "--exit", str(gem5_exit)],
                         capture_output=True, text=True)
    jm = re.search(r"LSU_L5: (\{.*\})", cls.stdout)
    verdict = json.loads(jm.group(1)) if jm else {"error": f"classifier failed: {cls.stderr[-300:]}"}
    verdict["gem5_exit"] = gem5_exit
    (outdir / "l5_verdict.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=1))
    print(f"L5: outcome={verdict.get('outcome')} crash_kind={verdict.get('crash_kind')} "
          f"activated={verdict.get('activated')} ({outdir.name}/l5_verdict.json)")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
