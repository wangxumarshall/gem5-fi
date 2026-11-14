"""Phase-2 orchestration: avalanche, RL, power patterns, FI, correlation.

Usage::

  python3 -m sdcfuzz.phase2 all
  python3 -m sdcfuzz.phase2 avalanche
  python3 -m sdcfuzz.phase2 rl-train --episodes 200
  python3 -m sdcfuzz.phase2 power-gen
  python3 -m sdcfuzz.phase2 power-run
  python3 -m sdcfuzz.phase2 fi --runs 20
  python3 -m sdcfuzz.phase2 correlate

Artifacts live under ``m5out/phase2-*``; the gate script
``scripts/test-phase2.sh`` runs the full chain and then
``scripts/verify-phase2.py`` audits the five Phase-2 milestones.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from . import avalanche, evaluate, generator, isa, power, power_sdc, rl
from .paths import default_cc, default_gem5
from .templates import TEMPLATE_BY_ID, Template

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "m5out"
AVALANCHE_DIR = OUT / "phase2-avalanche"
RL_DIR = OUT / "phase2-rl"
POWER_DIR = OUT / "phase2-power"

STREAM_META = {
    "type1-udiv": ("type1", "div"),
    "type1-fpadd": ("type1", "fpadd"),
    "type1-fpmul": ("type1", "fpmul"),
    "type2-udiv": ("type2", "div"),
    "type2-fpadd": ("type2", "fpadd"),
    "type2-fpmul": ("type2", "fpmul"),
    "type3-fpadd": ("type3", "fpadd"),
    "type3-fpmul": ("type3", "fpmul"),
    "type3-l1d": ("type3", "l1d"),
}
FP_STREAMS = ("type1-fpadd", "type1-fpmul", "type2-fpadd", "type2-fpmul",
              "type3-fpadd", "type3-fpmul")


def _checksum(text: str):
    values = re.findall(r"^[0-9a-f]{16}$", text, re.MULTILINE)
    return values[-1] if values else None


def cmd_avalanche(args):
    return avalanche.main(["--iterations", str(args.iterations),
                           "--out", str(AVALANCHE_DIR / "avalanche.json")])


def cmd_rl(args):
    return rl.main(["--episodes", str(args.episodes),
                    "--steps", str(args.steps), "--seed", str(args.seed),
                    "--outdir", str(RL_DIR)])


def cmd_power_gen(args):
    streams = power.default_streams()
    payload = {"schema": "sdcfuzz.power.streams.v1",
               "weights": power.POWER_WEIGHTS, "streams": {}}
    src_dir = POWER_DIR / "src"
    bin_dir = POWER_DIR / "bin"
    src_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name, stream in streams.items():
        pattern, structure = STREAM_META[name]
        features = power.power_features(stream)
        template = power.as_template(stream, name, structure)
        memory = None
        if structure == "fpmul":
            from . import isa
            memory = isa.initial_memory()
            memory[1] = isa.double_bits(1.0 + 2.0 ** -52)
        source, expected = generator.render_guest(template, stream.iterations,
                                                  memory=memory)
        source_path = src_dir / f"{name}.c"
        source_path.write_text(source)
        payload["streams"][name] = {
            "pattern": pattern, "structure": structure,
            "iterations": stream.iterations, "reps": stream.reps,
            "expected_checksum": f"{expected:016x}",
            "source": str(source_path),
            "power": features.as_dict(),
        }
    (POWER_DIR / "streams.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"power streams: {len(streams)} -> {POWER_DIR/'streams.json'}")
    return 0


def _run_guest(guest: Path, outdir: Path, extra=(), timeout: int = 180):
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [str(default_gem5()), "--quiet", "-d", str(outdir),
           str(ROOT / "configs/se/arm_chaos.py"), "--cpu", "O3",
           "--cmd", str(guest), "--kp920_proxy"] + list(extra)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          env=evaluate.gem5_environment())
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    (outdir / "gem5.log").write_text(text)
    return proc.returncode, _checksum(text), text


def _build_power_guests():
    cc = default_cc()
    src_dir = POWER_DIR / "src"
    bin_dir = POWER_DIR / "bin"
    guests = {}
    for name in STREAM_META:
        source = src_dir / f"{name}.c"
        if not source.exists():
            raise SystemExit(f"missing {source}; run power-gen first")
        guests[name] = evaluate.build_guest(cc, source, bin_dir / name)
    return guests


def cmd_power_run(args):
    streams = power.default_streams()
    guests = _build_power_guests()
    measurements = {"schema": "sdcfuzz.power.measurements.v1", "streams": {}}
    for name, stream in streams.items():
        pattern, structure = STREAM_META[name]
        m5out = POWER_DIR / "runs" / name
        shutil.rmtree(m5out, ignore_errors=True)
        rc, checksum, text = _run_guest(guests[name], m5out)
        mcpat = power.mcpat_power(m5out)
        features = power.power_features(stream)
        measurements["streams"][name] = {
            "pattern": pattern, "structure": structure,
            "golden": checksum, "returncode": rc,
            "power": features.as_dict(),
            "mcpat": mcpat,
        }
        print(f"  {name:14s} golden={checksum} mcpat={mcpat.get('status')} "
              f"{mcpat.get('dynamic_power_w', '-')}", flush=True)
    (POWER_DIR / "power_measurements.json").write_text(
        json.dumps(measurements, indent=2) + "\n")
    return 0


def _fi_one(task):
    name, guest, golden, seed, outdir, probability = task
    try:
        rc, checksum, text = _run_guest(
            Path(guest), Path(outdir),
            ["--chaos_fpu", f"--probability={probability}",
             "--max_faults=1", "--first_clock=1000",
             f"--rng_seed={seed}", "--fpu_bit_segment=all"], timeout=60)
    except subprocess.TimeoutExpired:
        return name, "Hang", 1
    log = Path(outdir) / "fpu_injections.log"
    injected = 0
    if log.exists():
        injected = sum(1 for line in log.read_text(errors="replace").splitlines()
                       if "Site:" in line)
    if injected == 0:
        return name, "Inactive", 0
    if checksum is None:
        if "panic:" in text or "fatal:" in text:
            return name, "SimulatorError", injected
        return name, "Crash", injected
    if golden and checksum != golden:
        return name, "SDC", injected
    return name, "Masked", injected


def cmd_fi(args):
    measurements = json.loads(
        (POWER_DIR / "power_measurements.json").read_text())
    guests = _build_power_guests()
    tasks = []
    for name in FP_STREAMS:
        golden = measurements["streams"][name]["golden"]
        for run in range(args.runs):
            tasks.append((name, str(guests[name]), golden, 20000 + run,
                          str(POWER_DIR / "fi" / name / f"r{run:03d}"),
                          args.probability))
    counts = {}
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for name, category, injected in pool.map(_fi_one, tasks):
            row = counts.setdefault(name, {"SDC": 0, "Masked": 0, "Crash": 0,
                                           "Hang": 0, "Inactive": 0,
                                           "SimulatorError": 0})
            row[category] = row.get(category, 0) + 1
    payload = {"schema": "sdcfuzz.power.fi.v1", "streams": {}}
    for name, row in counts.items():
        valid = sum(value for key, value in row.items()
                    if key not in ("Inactive", "SimulatorError"))
        payload["streams"][name] = {
            "sdc": row.get("SDC", 0), "n": valid, "cats": row,
            "golden": measurements["streams"][name]["golden"],
        }
        print(f"  {name:14s} SDC={row.get('SDC', 0)}/{valid} "
              f"masked={row.get('Masked', 0)}", flush=True)
    (POWER_DIR / "fi_results.json").write_text(
        json.dumps(payload, indent=2) + "\n")
    return 0


def _ops(rows):
    return tuple(isa.Op(**row) for row in rows)


def _load_stream(path: Path):
    payload = json.loads(path.read_text())
    return avalanche.Stream(setup=_ops(payload["setup"]),
                            body=_ops(payload["body"]),
                            iterations=int(payload.get("iterations", 10)),
                            reps=int(payload.get("reps", 16)))


def cmd_rl_validate(args):
    """Real CHAOSFPU validation of the best FP stream found by the policy."""
    best_path = RL_DIR / "best_fp_stream.json"
    if not best_path.exists():
        raise SystemExit("missing best_fp_stream.json; run rl-train first")
    stream = _load_stream(best_path)
    # Match the FP read budget of the power streams.
    stream = avalanche.Stream(setup=stream.setup, body=stream.body,
                              iterations=100, reps=16)
    template = Template("rl-best-fp", "policy-selected FP stream", "mixed",
                        "CHAOSFPU", setup=stream.setup, body=stream.body)
    source, _ = generator.render_guest(template, stream.iterations)
    src = RL_DIR / "validation" / "best_fp.c"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(source)
    guests = {"rl-best-fp": evaluate.build_guest(
        default_cc(), src, RL_DIR / "validation" / "best_fp")}
    baseline = TEMPLATE_BY_ID["fp-add"]
    baseline_source, _ = generator.render_guest(baseline,
                                                stream.iterations)
    baseline_src = RL_DIR / "validation" / "fp-add.c"
    baseline_src.write_text(baseline_source)
    guests["fp-add-baseline"] = evaluate.build_guest(
        default_cc(), baseline_src, RL_DIR / "validation" / "fp-add")

    tasks = []
    for name, guest in guests.items():
        m5out = RL_DIR / "validation" / f"{name}-golden"
        shutil.rmtree(m5out, ignore_errors=True)
        _, golden, _ = _run_guest(guest, m5out)
        if not golden:
            raise SystemExit(f"golden run failed for {name}")
        for run in range(args.runs):
            tasks.append((name, str(guest), golden, 30000 + run,
                          str(RL_DIR / "validation" / name / f"r{run:03d}"),
                          args.probability))
    counts = {}
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for name, category, _ in pool.map(_fi_one, tasks):
            row = counts.setdefault(name, {})
            row[category] = row.get(category, 0) + 1
    payload = {"schema": "sdcfuzz.rl.validation.v1", "streams": {}}
    for name, row in counts.items():
        valid = sum(value for key, value in row.items()
                    if key not in ("Inactive", "SimulatorError"))
        payload["streams"][name] = {"sdc": row.get("SDC", 0), "n": valid,
                                    "cats": row}
    a = payload["streams"]["rl-best-fp"]
    b = payload["streams"]["fp-add-baseline"]
    payload["fisher_p"] = power_sdc.fisher_2x2(
        a["sdc"], a["n"] - a["sdc"], b["sdc"], b["n"] - b["sdc"])
    payload["delta"] = (a["sdc"] / a["n"] if a["n"] else 0.0) - (
        b["sdc"] / b["n"] if b["n"] else 0.0)
    (RL_DIR / "validation.json").write_text(
        json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["streams"], indent=2))
    print(f"fisher_p={payload['fisher_p']:.4g} delta={payload['delta']:+.3f}")
    return 0


def cmd_mcpat_select(args):
    """Candidate-level McPAT feedback: rank generated streams by power + SDC."""
    candidates = []
    measurements = json.loads(
        (POWER_DIR / "power_measurements.json").read_text())["streams"]
    fi = json.loads((POWER_DIR / "fi_results.json").read_text())["streams"]
    for name, row in measurements.items():
        mcpat = row.get("mcpat", {})
        if mcpat.get("status") != "ok":
            continue
        sdc_row = fi.get(name, {})
        rate = (sdc_row.get("sdc", 0) / sdc_row["n"]
                if sdc_row.get("n") else 0.0)
        candidates.append({"stream": name, "source": "power-pattern",
                           "sdc_rate": rate, "n": sdc_row.get("n", 0),
                           "mcpat_power_w": mcpat["dynamic_power_w"]})
    best_fp = RL_DIR / "validation" / "rl-best-fp-golden"
    if best_fp.exists():
        mcpat = power.mcpat_power(best_fp)
        if mcpat.get("status") == "ok":
            validation = json.loads(
                (RL_DIR / "validation.json").read_text())["streams"]["rl-best-fp"]
            rate = validation["sdc"] / validation["n"] if validation["n"] else 0
            candidates.append({"stream": "rl-best-fp",
                               "source": "rl-policy",
                               "sdc_rate": rate, "n": validation["n"],
                               "mcpat_power_w": mcpat["dynamic_power_w"]})
    if not candidates:
        raise SystemExit("no candidates with McPAT power")
    peak = max(row["mcpat_power_w"] for row in candidates)
    for row in candidates:
        row["score"] = 0.5 * row["sdc_rate"] + 0.5 * (
            row["mcpat_power_w"] / peak)
    candidates.sort(key=lambda row: (-row["score"], row["stream"]))
    payload = {"schema": "sdcfuzz.rl.mcpat_selection.v1",
               "selected": candidates[0], "candidates": candidates,
               "rule": "0.5*SDC_rate + 0.5*(McPAT_power/peak_power)"}
    (RL_DIR / "mcpat_selection.json").write_text(
        json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["selected"], indent=2))
    return 0


def cmd_correlate(args):
    return power_sdc.main([
        "--power", str(POWER_DIR / "power_measurements.json"),
        "--fi", str(POWER_DIR / "fi_results.json"),
        "--out", str(POWER_DIR / "correlation.json"),
    ])


def cmd_all(args):
    for label, function in (
            ("avalanche", cmd_avalanche),
            ("rl", cmd_rl),
            ("rl-validate", cmd_rl_validate),
            ("power-gen", cmd_power_gen),
            ("power-run", cmd_power_run),
            ("fi", cmd_fi),
            ("mcpat-select", cmd_mcpat_select),
            ("correlate", cmd_correlate)):
        print(f"=== {label} ===", flush=True)
        code = function(args)
        if code:
            return code
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=40,
                        help="avalanche iterations per template")
    parser.add_argument("--episodes", type=int, default=200,
                        help="RL training episodes")
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--runs", type=int, default=20,
                        help="fault-injection runs per FP power stream")
    parser.add_argument("--probability", type=float, default=0.001)
    parser.add_argument("--jobs", type=int, default=4)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, function in (("all", cmd_all), ("avalanche", cmd_avalanche),
                           ("rl-train", cmd_rl), ("rl-validate",
                                                  cmd_rl_validate),
                           ("mcpat-select", cmd_mcpat_select),
                           ("power-gen", cmd_power_gen),
                           ("power-run", cmd_power_run), ("fi", cmd_fi),
                           ("correlate", cmd_correlate)):
        child = sub.add_parser(name)
        child.set_defaults(func=function)
        # Allow the options after the subcommand as well as before it.
        if name in ("all", "avalanche"):
            child.add_argument("--iterations", type=int,
                               default=argparse.SUPPRESS)
        if name in ("all", "rl-train"):
            child.add_argument("--episodes", type=int,
                               default=argparse.SUPPRESS)
            child.add_argument("--steps", type=int,
                               default=argparse.SUPPRESS)
            child.add_argument("--seed", type=int,
                               default=argparse.SUPPRESS)
        if name in ("all", "fi", "rl-validate"):
            child.add_argument("--runs", type=int,
                               default=argparse.SUPPRESS)
            child.add_argument("--probability", type=float,
                               default=argparse.SUPPRESS)
            child.add_argument("--jobs", type=int,
                               default=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
