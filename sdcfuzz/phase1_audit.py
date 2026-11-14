"""Audit the ten Phase-1 milestones against a completed gate run.

``scripts/test-phase1.sh`` answers "did the nine regression steps pass".  It
does not answer "which roadmap milestone does each step prove", so a passing
gate can coexist with a missing artifact or a silently degraded assertion.
This audit closes that gap: every Phase-1 milestone from
``docs/roadmap/roadmap.yaml`` is mapped to

  * the source artifacts it claims to deliver,
  * the gate steps that exercise them,
  * the exact assertion line those steps must print,

and the rollup is written as ``phase1_milestones.json``.  A missing file, a
non-zero step, a missing assertion line or a stale gate makes the audit fail.

The audit never re-runs gem5; it reads the gate directory produced by
``scripts/test-phase1.sh``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCHEMA = "sdcfuzz.phase1.milestones.v1"
EXPECTED_STEPS = ("pytest", "autousens", "templates", "sad", "rf-ace",
                  "l1-ace", "fu-ibr", "correctness", "coverage-report")
DEFAULT_MAX_AGE_HOURS = 24.0

# Each milestone: artifacts that must exist, gate steps that must return 0,
# and the assertion line those steps must have printed.  The needles are
# deliberately the *success* lines of the existing scripts, so weakening a
# check without updating it here is detected.
MILESTONES = (
    {
        "id": "p1-ace",
        "title": "RF ACE 与 L1 cache ACE 量化",
        "files": (
            "CHAOS/gem5/src/cpu/o3/rf_ace.hh",
            "CHAOS/gem5/src/cpu/o3/rf_ace.cc",
            "CHAOS/gem5/src/mem/cache/l1_ace.hh",
            "CHAOS/gem5/src/mem/cache/l1_ace.cc",
        ),
        "steps": ("rf-ace", "l1-ace", "correctness"),
        "needles": (
            ("rf-ace", "RF ACE direction and formula checks passed"),
            ("l1-ace", "L1 ACE direction and formula checks passed"),
            ("correctness",
             "Atomic access, mixed-width and ROI snapshot checks passed"),
        ),
    },
    {
        "id": "p1-ibr",
        "title": "FU IBR 输入位覆盖率",
        "files": (
            "CHAOS/gem5/src/cpu/o3/fu_ibr.hh",
            "CHAOS/gem5/src/cpu/o3/fu_ibr.cc",
        ),
        "steps": ("fu-ibr",),
        "needles": (
            ("fu-ibr",
             "IBR width, utilization, formula, disabled, work-ID, "
             "cycle-window and ROI-pairing checks passed"),
            ("fu-ibr", "intAlu IBR="),
            ("fu-ibr", "intMult IBR="),
            ("fu-ibr", "intDiv IBR="),
            ("templates", "fpadd="),
            ("templates", "fpmul="),
        ),
    },
    {
        "id": "p1-autousens",
        "title": "AutoµSens 指令→结构映射与逆向靶向原型",
        "files": ("tools/autousens.py",),
        "steps": ("autousens",),
        "needles": (
            ("autousens", "target l1d:"),
            ("autousens", "target mult:"),
            ("autousens", "target all:"),
            ("autousens", "error handling:"),
        ),
    },
    {
        "id": "p1-coverage",
        "title": "结构覆盖度评估工具",
        "files": (
            "sdcfuzz/coverage.py",
            "sdcfuzz/coverage_report.py",
        ),
        "steps": ("templates", "coverage-report"),
        "needles": (
            ("templates", "coverage: 9/9 structures observed"),
            ("coverage-report", "templates=19 structures=9 covered=9"),
        ),
    },
    {
        "id": "p1-local-corpus",
        "title": "本地 19 条结构语料（支撑件）",
        "files": ("sdcfuzz/templates.py",),
        "steps": ("templates",),
        "needles": (
            ("templates", "all 19 templates cover every mapped "
                          "instruction form"),
        ),
    },
    {
        "id": "p1-local-heuristic",
        "title": "本地操作数启发式（支撑件）",
        "files": (
            "sdcfuzz/operand_heuristic.py",
            "tests/test_sdcfuzz_operand_heuristic.py",
        ),
        "steps": ("pytest",),
        "needles": (("pytest", "passed"),),
    },
    {
        "id": "p1-joint-agg",
        "title": "跨结构加权聚合靶向",
        "files": (),
        "steps": ("autousens",),
        "needles": (("autousens", "target l1d+alu:"),),
    },
    {
        "id": "p1-nsga",
        "title": "NSGA-II 多目标序列集生成",
        "files": ("tools/nsga2.py",),
        "steps": ("autousens",),
        "needles": (
            ("autousens", "pareto: size="),
            ("autousens", "knee="),
        ),
    },
    {
        "id": "p1-sad",
        "title": "SAD 结构激活深度指标",
        "files": (
            "CHAOS/gem5/src/cpu/o3/sad.hh",
            "CHAOS/gem5/src/cpu/o3/sad.cc",
        ),
        "steps": ("sad",),
        "needles": (
            ("sad", "SAD window, formula, direction, disabled and "
                    "cycle-mode checks passed"),
        ),
    },
    {
        "id": "p1-gate",
        "title": "Phase 1 一键验收（9 步）",
        "files": ("scripts/test-phase1.sh",),
        "steps": tuple(EXPECTED_STEPS),
        "needles": (),
    },
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_utc(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_doc(path: str) -> bool:
    return path.startswith("docs/") or path.endswith(".md")


def _evidence_drift(root: Path, gate_commit) -> list | None:
    """Files changed since *gate_commit* that can affect the gate result.

    Doc-only changes are ignored so documentation can cite an older run
    without invalidating it; the timestamp check is what guards freshness.
    Returns ``None`` when the comparison is impossible (no git, unknown
    commit), which the caller treats as a failure rather than a pass.
    """
    if not gate_commit:
        return None
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              text=True, capture_output=True,
                              check=True).stdout.strip()
    except Exception:
        return None
    if head == gate_commit:
        return []
    try:
        changed = subprocess.run(
            ["git", "diff", "--name-only", gate_commit, head],
            cwd=root, text=True, capture_output=True,
            check=True).stdout.splitlines()
    except Exception:
        return None
    return [path for path in changed if path and not _is_doc(path)]


def _step_map(gate: dict) -> dict:
    return {step.get("name"): step for step in gate.get("steps", [])}


def _extra_checks(milestone_id, gate_dir: Path, gate: dict, logs: dict,
                  now: datetime, max_age_hours: float):
    """Milestone-specific checks that need parsed data, not just a needle."""
    checks = []
    if milestone_id == "p1-coverage":
        path = gate_dir / "report" / "coverage_summary.json"
        try:
            summary = json.loads(path.read_text())
        except (OSError, ValueError) as error:
            checks.append(("coverage_summary.json readable", False, str(error)))
        else:
            templates = summary.get("template_count")
            structures = summary.get("structure_count")
            covered = summary.get("covered_structures") or []
            checks.append((
                "coverage_summary counts",
                templates == 19 and structures == 9 and len(covered) == 9,
                f"templates={templates} structures={structures} "
                f"covered={len(covered)}",
            ))
            never = (summary.get("gaps") or {}).get("never_observed") or []
            checks.append(("no never-observed structure", not never,
                           f"never_observed={never}"))
            sad = summary.get("sad") or {}
            checks.append(("SAD attached to coverage report",
                           bool(sad.get("ratio")),
                           f"sad_keys={sorted(sad)}"))
    elif milestone_id == "p1-joint-agg":
        text = logs.get("autousens", "")
        match = re.search(
            r"^target l1d\+alu: .*l1d_net=(\d+) alu_net=(\d+)", text, re.M)
        if match is None:
            checks.append(("l1d+alu net activation", False, "line not found"))
        else:
            l1d, alu = int(match.group(1)), int(match.group(2))
            checks.append(("l1d+alu net activation", l1d > 0 and alu > 0,
                           f"l1d_net={l1d} alu_net={alu}"))
    elif milestone_id == "p1-nsga":
        text = logs.get("autousens", "")
        match = re.search(r"^pareto: size=(\d+) knee=", text, re.M)
        if match is None:
            checks.append(("Pareto front non-empty", False, "line not found"))
        else:
            size = int(match.group(1))
            checks.append(("Pareto front non-empty", size > 0, f"size={size}"))
    elif milestone_id == "p1-gate":
        steps = gate.get("steps", [])
        names = sorted(step.get("name") for step in steps)
        checks.append(("gate records 9 steps", len(steps) == 9,
                       f"steps={len(steps)}"))
        checks.append(("gate step names", names == sorted(EXPECTED_STEPS),
                       ",".join(names)))
        checks.append(("gate verdict", gate.get("passed") is True
                       and gate.get("failures") == 0,
                       f"passed={gate.get('passed')} "
                       f"failures={gate.get('failures')}"))
        generated = _parse_utc(gate.get("generated_utc"))
        if generated is None:
            checks.append(("gate timestamp", False, "missing/invalid"))
        elif max_age_hours > 0:
            age = (now - generated).total_seconds() / 3600.0
            checks.append(("gate freshness", age <= max_age_hours,
                           f"age={age:.1f}h limit={max_age_hours:.0f}h"))
        else:
            checks.append(("gate freshness", True, "disabled"))
        drift = _evidence_drift(ROOT, gate.get("commit"))
        checks.append((
            "no code change since gate",
            drift == [],
            "same commit" if drift == [] else
            ("cannot compare commits" if drift is None else
             f"changed: {', '.join(drift[:4])}"),
        ))
    return checks


def audit(gate_dir: Path, root: Path = ROOT, now=None,
          max_age_hours: float = DEFAULT_MAX_AGE_HOURS) -> dict:
    """Return the milestone report for ``gate_dir`` (never raises on bad data)."""
    gate_dir = Path(gate_dir)
    root = Path(root)
    now = now or datetime.now(timezone.utc)
    gate_path = gate_dir / "phase1_gate.json"
    try:
        gate = json.loads(gate_path.read_text())
    except (OSError, ValueError) as error:
        return {
            "schema": SCHEMA,
            "gate_dir": str(gate_dir),
            "passed": False,
            "error": f"cannot read {gate_path}: {error}",
            "milestones": [],
        }
    steps = _step_map(gate)
    logs = {name: _read(gate_dir / f"{name}.log") for name in steps}

    milestones = []
    for spec in MILESTONES:
        checks = []
        for relative in spec["files"]:
            path = root / relative
            checks.append((f"artifact {relative}", path.is_file(),
                           "present" if path.is_file() else "missing"))
        for name in spec["steps"]:
            step = steps.get(name)
            ok = step is not None and step.get("returncode") == 0
            detail = ("missing step" if step is None
                      else f"rc={step.get('returncode')}")
            checks.append((f"step {name}", ok, detail))
        for name, needle in spec["needles"]:
            ok = needle in logs.get(name, "")
            checks.append((f"assertion in {name}.log", ok,
                           f"'{needle[:48]}'" if ok else
                           f"missing '{needle[:48]}'"))
        checks.extend(_extra_checks(spec["id"], gate_dir, gate, logs, now,
                                    max_age_hours))
        milestones.append({
            "id": spec["id"],
            "title": spec["title"],
            "passed": all(check[1] for check in checks),
            "checks": [{"name": name, "ok": ok, "detail": detail}
                       for name, ok, detail in checks],
        })

    return {
        "schema": SCHEMA,
        "gate_dir": str(gate_dir),
        "gate_commit": gate.get("commit"),
        "gate_generated_utc": gate.get("generated_utc"),
        "generated_utc": now.isoformat(),
        "milestones": milestones,
        "passed": all(milestone["passed"] for milestone in milestones),
    }


def render(report: dict) -> str:
    lines = []
    if report.get("error"):
        lines.append(f"FAIL: {report['error']}")
        return "\n".join(lines)
    width = max(len(m["id"]) for m in report["milestones"])
    lines.append(f"{'milestone':{width}s}  status  title")
    for milestone in report["milestones"]:
        status = "PASS" if milestone["passed"] else "FAIL"
        lines.append(f"{milestone['id']:{width}s}  {status:<6s}  "
                     f"{milestone['title']}")
    failed = [m for m in report["milestones"] if not m["passed"]]
    for milestone in failed:
        lines.append("")
        lines.append(f"{milestone['id']} failures:")
        for check in milestone["checks"]:
            if not check["ok"]:
                lines.append(f"  - {check['name']}: {check['detail']}")
    passed = sum(1 for m in report["milestones"] if m["passed"])
    lines.append("")
    lines.append(f"phase1 milestones: {passed}/{len(report['milestones'])} "
                 f"passed")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gate-dir", type=Path,
                        default=ROOT / "m5out/phase1-gate",
                        help="directory produced by scripts/test-phase1.sh")
    parser.add_argument("--json", type=Path, default=None,
                        help="report path (default <gate-dir>/phase1_milestones.json)")
    parser.add_argument("--max-age-hours", type=float,
                        default=DEFAULT_MAX_AGE_HOURS,
                        help="fail when the gate is older than this (0 disables)")
    args = parser.parse_args(argv)

    report = audit(args.gate_dir, max_age_hours=args.max_age_hours)
    out = args.json or (args.gate_dir / "phase1_milestones.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(render(report))
    print(f"report: {out}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
