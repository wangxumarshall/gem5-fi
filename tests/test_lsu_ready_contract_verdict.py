#!/usr/bin/env python3
"""契约测试：ready-gate 的 GO/NO-GO 裁决 + 正式 campaign 命令口径。

钉住三条不变量（2026-10-22 R4-10 收口，用户指令：禁止误报 GO）：
  1. BLOCKED>0 或测试失败或资源不足 → NO-GO（不得因改名/分类制造 GO）
  2. 正式命令必须是 `--phase screening`（固定样本量政策），
     **不得**出现 `--phase trial`（pilot）或 `--max-seeds-per-cell 3`
  3. 21 个重点 RunID → 2401；其余 → 385

先算后测（`python3 tools/lsu_ready_contract.py --gate` 已产出 json）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import lsu_ready_contract as rc  # noqa: E402

DOC = json.loads((REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json").read_text())

fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond:
        fails.append(name)


# --- 1. 裁决存在且当前为 NO-GO（BLOCKED=84>0 是既成事实，不得被改写为 GO）---
v = DOC.get("verdict")
check("verdict_present", isinstance(v, dict), "ready_contract.json 缺 verdict")
check("verdict_is_nogo_now", v and v["verdict"] == "NO-GO",
      f"当前 BLOCKED={DOC['status'].get('BLOCKED')} 却报 {v and v['verdict']}")
check("nogo_reason_cites_blocked", v and any("BLOCKED" in r for r in v["reasons"]),
      f"NO-GO 未给出 BLOCKED 理由：{v and v['reasons']}")

# --- 2. 正式命令口径 ---
# [R6-GATE] 链门生效后 READY 可降至 0（无链证据即不准入），正式命令随之可为空
# ——契约中已有的命令仍须满足口径（无异类命令）；**生成器**口径另行独立钉死，
# 不受 READY 计数影响。
cmds = [r["command"] for r in DOC["entries"] if r.get("command")]
check("no_trial_phase", not any("--phase trial" in c for c in cmds),
      "正式命令仍含 pilot 口径 --phase trial")
check("no_3seed_cap", not any("--max-seeds-per-cell 3 " in c for c in cmds),
      "正式命令仍是 3-seed pilot")
check("all_screening_phase", all(f"--phase {rc.FORMAL_PHASE}" in c for c in cmds),
      f"存在非 {rc.FORMAL_PHASE} phase 的命令")
# 生成器口径（独立于契约当前 READY 计数）
gen_focus = rc._command("A01-F0-W3", "addrpath")     # 在 FOCUS_RUNIDS 内
gen_norm = rc._command("A02-F0-W3", "addrpath")      # 非重点
check("gen_no_trial_phase", "--phase trial" not in gen_focus
      and "--phase trial" not in gen_norm, gen_focus)
check("gen_screening_phase", f"--phase {rc.FORMAL_PHASE}" in gen_focus
      and f"--phase {rc.FORMAL_PHASE}" in gen_norm, gen_focus)
check("gen_focus_target_2401",
      f"--screening-target {rc.FOCUS_TARGET}" in gen_focus, gen_focus)
check("gen_normal_target_385",
      f"--screening-target {rc.SCREENING_TARGET}" in gen_norm, gen_norm)

# --- 3. 重点 RunID 采样规则 ---
by_id = {r["run_id"]: r for r in DOC["entries"]}
focus = [r for r in DOC["entries"] if r["run_id"] in rc.FOCUS_RUNIDS and r.get("command")]
check("focus_count_matches_list", len(rc.FOCUS_RUNIDS) == 21, len(rc.FOCUS_RUNIDS))
for r in focus:
    check(f"focus_target_{r['run_id']}",
          f"--screening-target {rc.FOCUS_TARGET}" in r["command"], r["command"])
normal = [r for r in DOC["entries"]
          if r["run_id"] not in rc.FOCUS_RUNIDS and r.get("command")]
for r in normal[:5]:
    check(f"normal_target_{r['run_id']}",
          f"--screening-target {rc.SCREENING_TARGET}" in r["command"], r["command"])

# --- 4. 合成：全绿才 GO（负向 —— 不得把生成器改成恒 GO）---
fake = json.loads(json.dumps(DOC))
fake["status"] = {"READY": 325, "PARTIAL": 0, "BLOCKED": 0}
fake["blocked_by_category"] = {}
fake["gate"] = {"binary_sha256": "deadbeef", "pytest_rc": 0,
                "disk_free_gb": 999.0, "mem_avail_gb": 99.0}
check("synthetic_all_clear_is_go", rc.verdict(fake)["verdict"] == "GO",
      "全条件满足时未判 GO")
fake2 = json.loads(json.dumps(fake))
fake2["status"] = {"READY": 324, "PARTIAL": 0, "BLOCKED": 1}
check("synthetic_one_blocked_is_nogo", rc.verdict(fake2)["verdict"] == "NO-GO",
      "BLOCKED>0 却判 GO")

print()
if fails:
    print(f"FAILED: {len(fails)} -> {fails}")
    sys.exit(1)
print("ALL PASS")
