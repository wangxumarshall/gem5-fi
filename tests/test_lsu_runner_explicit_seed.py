#!/usr/bin/env python3
"""test_lsu_runner_explicit_seed.py — [0202-T02F2] 显式 RNG seed 身份契约。

背景（实测）：0202 的 runner 用**哈希** seed（`lsu_seed(run_id, phase, sample_index)`），
0101 的 R6 campaign 用**整数** seed（`--tlb_rng_seed 1`，见
docs/gem5-fi/lsu/mdspec/R4-8-SPEC-residual-report.md:170 实测命令行 + `.../seed1/`）。
两者是**不同样本**。为能显式复现 0101 的整数 seed1，runner 必须能把 RNG seed 作为
**独立于 sample_index 的身份**表达，且不得把 `sample_index=0` 对外称作"数值 seed1"。

本套件锁死：
  1. 未给显式 seed ⇒ `lsu_seed(run_id, phase, sample_index)` 行为**逐字节不变**；
  2. 给显式 seed ⇒ 实际 injector 收到该整数（命令含 `--tlb_rng_seed <n>`）；
  3. manifest 同时记录 sample_index / seed / seed_source / seed 规则 / 显式原值；
  4. dry-run 命令、manifest、实际 gem5 命令三处 seed 一致；
  5. 显式 seed 与 sample_index 同时给出 ⇒ 响亮冲突失败；负数/非法 ⇒ 响亮失败；
  6. 显式 seed 贯通 `--prop_sample_run_id`（与 campaign 的 `s<整数seed>` 惯例一致）；
  7. 对外标签不得把 `sample_index=0` 表述为 seed1。

用法：python3 tests/test_lsu_runner_explicit_seed.py   （退出码 0=全 PASS）
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_runner as RUN          # noqa: E402
from lsu_seed import lsu_seed     # noqa: E402

FAILED = []


def check(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name
          + (("  :: " + str(detail)) if detail and not ok else ""))
    if not ok:
        FAILED.append(name)


def cli(*args):
    return subprocess.run([sys.executable, str(ROOT / "tools" / "lsu_runner.py"), *args],
                          capture_output=True, text=True)


def main():
    real_sha = RUN._sha
    RUN._sha = lambda p: "0" * 64
    tmp = Path(tempfile.mkdtemp(prefix="0202seed_"))
    cpt = str(tmp / "cpt.239515184727")
    try:
        print("[1] 未给显式 seed：derived 行为逐字节不变")
        m = RUN.build_manifest("ITEM-049", "engineering", 0)
        want = lsu_seed("T02-F2-W4", "engineering", 0)
        check("seed == lsu_seed(run_id,'engineering',0)", m["seed"] == want,
              f"{m['seed']} != {want}")
        check("seed_source == 'derived'", m.get("seed_source") == "derived", m.get("seed_source"))
        check("sample_index 记录为 0", m.get("sample_index") == 0, m.get("sample_index"))
        check("explicit_seed 未设置（None）", m.get("explicit_seed") is None, m.get("explicit_seed"))
        _c, args = RUN.build_guard_cmd(m, tmp / "o")
        check("命令携带 derived seed", args[args.index("--tlb_rng_seed") + 1] == str(want))

        print("[2] 显式 seed=1：injector 实收 1")
        m2 = RUN.build_manifest("ITEM-049", "engineering", None, explicit_seed=1)
        check("seed == 1", m2["seed"] == 1, m2["seed"])
        check("seed_source == 'explicit'", m2.get("seed_source") == "explicit", m2.get("seed_source"))
        check("explicit_seed 原值记录为 1", m2.get("explicit_seed") == 1, m2.get("explicit_seed"))
        check("seed 规则文本仍在", bool(m2.get("seed_rule")), m2.get("seed_rule"))
        _c2, a2 = RUN.build_guard_cmd(m2, tmp / "o2")
        check("命令携带 --tlb_rng_seed 1", a2[a2.index("--tlb_rng_seed") + 1] == "1", a2)
        check("prop_sample_run_id == s1（与 campaign 整数惯例一致）",
              a2[a2.index("--prop_sample_run_id") + 1] == "s1",
              a2[a2.index("--prop_sample_run_id") + 1])

        print("[3] dry-run / manifest / 命令三处一致（CLI 端到端）")
        man_p = tmp / "m_explicit.json"
        r = cli("--item", "ITEM-049", "--phase", "engineering",
                "--explicit-seed", "1", "--fs-checkpoint", cpt, "--output", str(man_p))
        check("CLI 生成 manifest rc=0", r.returncode == 0, r.stderr[-300:])
        on_disk = json.loads(man_p.read_text())
        check("落盘 manifest seed==1", on_disk["seed"] == 1, on_disk["seed"])
        check("落盘 manifest seed_source==explicit", on_disk["seed_source"] == "explicit")
        dr = cli("--manifest", str(man_p), "--dry-run")
        check("dry-run rc=0", dr.returncode == 0, dr.stderr[-300:])
        check("dry-run 命令含 --tlb_rng_seed 1", "--tlb_rng_seed 1" in dr.stdout,
              dr.stdout[-300:])

        print("[4] derived 与 explicit 互斥 / 非法值响亮失败")
        r = cli("--item", "ITEM-049", "--phase", "engineering", "--sample-index", "0",
                "--explicit-seed", "1", "--fs-checkpoint", cpt, "--output", str(tmp / "x.json"))
        check("同时给 sample-index 与 explicit-seed ⇒ 非 0 退出",
              r.returncode != 0, r.stdout[-200:] + r.stderr[-200:])
        bad = False
        try:
            RUN.build_manifest("ITEM-049", "engineering", None, explicit_seed=-1)
        except SystemExit:
            bad = True
        check("显式负 seed ⇒ SystemExit", bad)
        r = cli("--item", "ITEM-049", "--phase", "engineering",
                "--explicit-seed", "notanint", "--fs-checkpoint", cpt, "--output", str(tmp / "y.json"))
        check("非整数 seed ⇒ 非 0 退出", r.returncode != 0)
        r = cli("--item", "ITEM-049", "--phase", "engineering",
                "--fs-checkpoint", cpt, "--output", str(tmp / "z.json"))
        check("既无 sample-index 也无 explicit-seed ⇒ 非 0 退出", r.returncode != 0)

        print("[5] 不得把 sample_index=0 称作 seed1")
        r0 = cli("--item", "ITEM-049", "--phase", "engineering", "--sample-index", "0",
                 "--fs-checkpoint", cpt, "--output", str(man_p.parent / "m_derived.json"))
        check("derived CLI rc=0", r0.returncode == 0, r0.stderr[-200:])
        md = json.loads((man_p.parent / "m_derived.json").read_text())
        blob = json.dumps(md, ensure_ascii=False).lower()
        check("derived manifest 不把 sample_index 0 表述为 'seed1'",
              "seed1" not in blob and "seed 1" not in blob, blob[:200])
        check("derived manifest seed 是 64 位哈希（非 0/1）", md["seed"] not in (0, 1), md["seed"])
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
