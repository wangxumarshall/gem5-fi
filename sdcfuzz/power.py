"""Power-stress taxonomy and a McPAT-in-the-loop adapter (sdcfuzz-v1.2 §5.3).

Three pattern families are generated as ordinary ``isa.Op`` streams so they can
be rendered by the existing generator and measured in gem5:

``Type-I``   continuous high power: repeat the highest-power instruction for a
             structure (or ``udiv``/``fdiv`` globally), building current and
             temperature.
``Type-II``  power oscillation: alternate a low-power instruction with a
             high-power one; ``period`` and ``duty`` are the knobs the RL
             policy can tune (di/dt droop).
``Type-III`` hotspot concentration: repeat the AutoµSens top instruction of a
             single structure in a tight window, so one unit is activated while
             the rest idles.

The fast, dependency-free ``power_features`` model is a weighted instruction
trace (peak / average / variance / slope).  For evidence we also provide
``mcpat_power``, which invokes the upstream ``pypat`` wrapper around the local
McPAT binary on a gem5 ``m5out`` directory and parses ``out.ptrace``.  If McPAT
is unavailable the adapter returns a structured error and the proxy remains the
documented fallback; the report records which path was used.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import isa
from .avalanche import Stream
from .templates import Template

# Relative dynamic-energy weights per modelled instruction.  They are a
# *relative* proxy calibrated against the McPAT dynamic-power ranking of the
# same streams (see docs/sdcfuzz/phase2-verification.md); they are not joules.
POWER_WEIGHTS = {
    "mov": 0.2,
    "add": 0.5, "sub": 0.5, "and": 0.5, "orr": 0.5, "eor": 0.5,
    "add_imm": 0.5, "add_lsl": 0.6,
    "mul": 1.5, "madd": 2.0, "udiv": 4.0,
    "fadd": 1.0, "fsub": 1.0, "fmul": 1.5, "fdiv": 6.0,
    "ldr": 1.2, "ldrf": 1.2, "str": 1.0,
    "busy_loop": 0.5,
}

# Highest-power instruction per structure (Type-I / Type-III defaults).
STRUCTURE_TOP = {
    "alu": ("add", "x8", "x8", "x12"),
    "mult": ("mul", "x8", "x8", "x12"),
    "div": ("udiv", "x8", "x8", "x12"),
    "fpadd": ("fadd", "d0", "d0", "d1"),
    "fpmul": ("fmul", "d0", "d0", "d1"),
    "l1d": ("ldr", "x8", None, None),
    "l1i": ("add_imm", "x8", None, None),
}

DEFAULT_WINDOW = 4


@dataclass
class PowerFeatures:
    length: int
    average: float
    peak: float
    variance: float
    slope: float
    stress: float

    def as_dict(self):
        return {
            "length": self.length,
            "average": round(self.average, 6),
            "peak": round(self.peak, 6),
            "variance": round(self.variance, 6),
            "slope": round(self.slope, 6),
            "stress": round(self.stress, 6),
        }


def trace(stream: Stream) -> list[float]:
    """Per-dynamic-instruction relative energy trace."""
    unit = [POWER_WEIGHTS.get(op.kind) for op in stream.body]
    if any(weight is None for weight in unit):
        missing = sorted({op.kind for op in stream.body
                          if op.kind not in POWER_WEIGHTS})
        raise ValueError(f"no power weight for {missing}")
    return [weight for _ in range(stream.reps * stream.iterations)
            for weight in unit]


def _rolling_peak(values: list[float], window: int) -> float:
    if not values:
        return 0.0
    if len(values) <= window:
        return sum(values) / len(values)
    current = sum(values[:window])
    best = current
    for index in range(window, len(values)):
        current += values[index] - values[index - window]
        best = max(best, current)
    return best / window


def power_features(stream: Stream, window: int = DEFAULT_WINDOW) -> PowerFeatures:
    values = trace(stream)
    if not values:
        raise ValueError("empty power trace")
    average = sum(values) / len(values)
    peak = _rolling_peak(values, window)
    variance = statistics.pvariance(values) if len(values) > 1 else 0.0
    quarter = max(1, len(values) // 4)
    start = sum(values[:quarter]) / quarter
    end = sum(values[-quarter:]) / quarter
    slope = (end - start) / average if average else 0.0
    # Normalise by the heaviest modelled instruction (fdiv = 6.0).
    stress = (0.5 * min(1.0, average / 6.0)
              + 0.3 * min(1.0, peak / 6.0)
              + 0.2 * min(1.0, variance / 4.0))
    return PowerFeatures(length=len(values), average=average, peak=peak,
                         variance=variance, slope=slope, stress=stress)


def _op(kind: str, dst=None, a=None, b=None, imm=None, width=64, off=None):
    return isa.Op(kind, dst=dst, a=a, b=b, imm=imm, width=width, off=off)


def _setup_for(structure: str):
    if structure in ("fpadd", "fpmul"):
        return (isa.Op("ldrf", dst="d0", off=0),
                isa.Op("ldrf", dst="d1", off=8))
    if structure == "l1d":
        return (_op("mov", dst="x8", imm=0),)
    if structure == "l1i":
        return (_op("mov", dst="x8", imm=0),)
    return (_op("mov", dst="x8", imm=0xFFFFFFFFFFFFFFFF),
            _op("mov", dst="x12", imm=3))


def _top_op(structure: str):
    kind, dst, a, b = STRUCTURE_TOP[structure]
    if kind == "add_imm":
        return _op(kind, dst=dst, imm=1)
    if kind == "ldr":
        return isa.Op("ldr", dst=dst, off=0)
    return _op(kind, dst=dst, a=a, b=b)


def type1_continuous(structure: str = "div", iterations: int = 200) -> Stream:
    """Repeat the highest-power instruction (continuous current/temperature)."""
    if structure not in STRUCTURE_TOP:
        raise KeyError(structure)
    body = (_top_op(structure),)
    return Stream(setup=_setup_for(structure), body=body,
                  iterations=iterations, reps=16)


def type2_oscillation(structure: str = "fpmul", period: int = 8,
                      duty: float = 0.5, iterations: int = 25) -> Stream:
    """Alternate low-power and high-power instructions with a tunable pattern."""
    if structure not in STRUCTURE_TOP:
        raise KeyError(structure)
    if period < 2 or period % 2:
        raise ValueError("period must be an even integer >= 2")
    if not 0.0 < duty < 1.0:
        raise ValueError("duty must be in (0, 1)")
    high = _top_op(structure)
    low = _op("mov", dst="x13", imm=0)
    high_count = max(1, min(period - 1, round(period * duty)))
    body = tuple([low] * (period - high_count) + [high] * high_count)
    # Keep the low/high boundary inside the body; the template repeats 16x.
    return Stream(setup=_setup_for(structure), body=body,
                  iterations=iterations, reps=16)


def type3_hotspot(structure: str = "fpadd", copies: int = 32,
                  iterations: int = 7) -> Stream:
    """Repeat one structure's top instruction in a tight hotspot window."""
    if structure not in STRUCTURE_TOP:
        raise KeyError(structure)
    body = tuple(_top_op(structure) for _ in range(copies))
    return Stream(setup=_setup_for(structure), body=body,
                  iterations=iterations, reps=16)


def as_template(stream: Stream, template_id: str, target: str,
                injector: str = "CHAOS") -> Template:
    """Wrap a power stream as a Template so ``generator.render_guest`` can use it."""
    return Template(template_id, f"power pattern {template_id}", target,
                    injector, setup=tuple(stream.setup),
                    body=tuple(stream.body))


# ---------------------------------------------------------------------------
# McPAT adapter
# ---------------------------------------------------------------------------

def mcpat_home() -> Path:
    override = os.environ.get("MCPAT_HOME")
    if override:
        return Path(override)
    return Path.home() / "wangxu/silifuzz/third_party/mcpat"


def _parse_table(path: Path):
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError(f"{path}: not a two-line table")
    header = lines[0].split()
    values = [float(value) for value in lines[1].split()]
    if len(header) != len(values):
        raise ValueError(f"{path}: header/value length mismatch")
    return dict(zip(header, values))


def mcpat_power(m5out: Path, timeout: int = 180) -> dict:
    """Run pypat+McPAT on *m5out* and return the dynamic-power breakdown."""
    m5out = Path(m5out).resolve()
    home = mcpat_home()
    if not (home / "mcpat").exists():
        return {"status": "unavailable", "reason": f"mcpat binary missing in {home}"}
    if not (m5out / "stats.txt").exists() or not (m5out / "config.json").exists():
        return {"status": "unavailable",
                "reason": "m5out needs stats.txt and config.json"}
    cmd = [sys.executable, "-m", "pypat", str(m5out),
           "--template-profile", "arm64-kunpeng920",
           "--outfile", str(m5out / "conv.xml"), "--print-level", "1"]
    try:
        proc = subprocess.run(cmd, cwd=str(home), capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "cmd": " ".join(cmd)}
    ptrace = m5out / "out.ptrace"
    if proc.returncode != 0 or not ptrace.exists():
        return {"status": "error", "returncode": proc.returncode,
                "stderr": (proc.stderr or "")[-1200:],
                "stdout": (proc.stdout or "")[-1200:],
                "cmd": " ".join(cmd)}
    components = _parse_table(ptrace)
    dynamic = sum(components.values())
    area = None
    if (m5out / "out.area").exists():
        try:
            area = sum(_parse_table(m5out / "out.area").values())
        except ValueError:
            area = None
    return {"status": "ok", "dynamic_power_w": round(dynamic, 6),
            "components": {key: round(value, 6)
                           for key, value in components.items()},
            "area_mm2": round(area, 6) if area is not None else None,
            "mcpat_home": str(home)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def default_streams():
    return {
        "type1-udiv": type1_continuous("div"),
        "type1-fpadd": type1_continuous("fpadd"),
        "type1-fpmul": type1_continuous("fpmul"),
        "type2-udiv": type2_oscillation("div"),
        "type2-fpadd": type2_oscillation("fpadd"),
        "type2-fpmul": type2_oscillation("fpmul"),
        "type3-fpadd": type3_hotspot("fpadd"),
        "type3-fpmul": type3_hotspot("fpmul"),
        "type3-l1d": type3_hotspot("l1d"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=Path("m5out/phase2-power/streams.json"))
    parser.add_argument("--m5out", type=Path,
                        help="if set, run McPAT on this gem5 output directory")
    args = parser.parse_args(argv)

    if args.m5out:
        print(json.dumps(mcpat_power(args.m5out), indent=2))
        return 0

    streams = default_streams()
    payload = {"schema": "sdcfuzz.power.streams.v1",
               "weights": POWER_WEIGHTS, "streams": {}}
    for name, stream in streams.items():
        features = power_features(stream)
        payload["streams"][name] = {
            "setup": [op.__dict__ for op in stream.setup],
            "body": [op.__dict__ for op in stream.body],
            "iterations": stream.iterations,
            "reps": stream.reps,
            **features.as_dict(),
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"streams: {len(streams)} -> {args.out}")
    for name, row in payload["streams"].items():
        print(f"  {name:14s} avg={row['average']:.2f} peak={row['peak']:.2f} "
              f"var={row['variance']:.2f} slope={row['slope']:+.2f} "
              f"stress={row['stress']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
