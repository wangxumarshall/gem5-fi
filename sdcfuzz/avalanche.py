"""1-bit avalanche test and logical-masking penalty (sdcfuzz-v1.2 §5.2).

The RL reward needs a cheap, deterministic measurement of *logical masking*:
if a single-bit perturbation of a live input never changes any written output,
the stream is hiding faults and should be penalised.  This module implements
that measurement on the same AArch64 subset used by the Phase-0 templates
(``sdcfuzz.isa``); it does not need gem5.

For a stream ``setup + body`` executed ``reps * iterations`` times:

1. snapshot the architectural state after ``setup``;
2. run the body once to get the baseline *written output state* (the registers
   and memory words the body actually writes);
3. for every bit of every source register, flip that bit in the snapshot, run
   the same body, and compare the written output state with the baseline.

Reported metrics
----------------
``word_flip_ratio``
    Fraction of bit-flip trials that changed at least one output word.  This is
    the primary logical-masking signal.
``avalanche_bit_ratio``
    Mean Hamming distance of the changed output words divided by 64 (capped at
    1.0).  A one-bit effect scores 1/64; a full-word effect scores 1.0.
``masking_penalty``
    ``1 - word_flip_ratio`` in [0, 1]; 1 means every trial was masked.
``breadth``
    Mean fraction of output words that changed per trial.

The test is intentionally conservative: a flip that changes the checksum only
through a hash avalanche is *not* counted, because the comparison is on the
architectural output words, not on the FNV checksum.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from . import isa
from .templates import TEMPLATES, TEMPLATE_BY_ID

MASK64 = (1 << 64) - 1


@dataclass(frozen=True)
class Stream:
    """A setup + body pair executed ``reps * iterations`` times."""

    setup: tuple = ()
    body: tuple = ()
    iterations: int = 40
    reps: int = 16
    template_id: str | None = None


@dataclass
class AvalancheResult:
    trials: int
    changed_trials: int
    word_flip_ratio: float
    avalanche_bit_ratio: float
    masking_penalty: float
    breadth: float
    output_words: list[str] = field(default_factory=list)
    source_registers: list[str] = field(default_factory=list)
    per_register: dict = field(default_factory=dict)

    def as_dict(self):
        return {
            "trials": self.trials,
            "changed_trials": self.changed_trials,
            "word_flip_ratio": round(self.word_flip_ratio, 6),
            "avalanche_bit_ratio": round(self.avalanche_bit_ratio, 6),
            "masking_penalty": round(self.masking_penalty, 6),
            "breadth": round(self.breadth, 6),
            "output_words": self.output_words,
            "source_registers": self.source_registers,
            "per_register": self.per_register,
        }


def _is_gpr(name: str) -> bool:
    return isinstance(name, str) and name.startswith("x") and name[1:].isdigit()


def _is_fpr(name: str) -> bool:
    return isinstance(name, str) and name.startswith("d") and name[1:].isdigit()


def _written_words(setup: Sequence[isa.Op], body: Sequence[isa.Op]):
    """Return the output words the body writes: GPRs, FPRs and memory slots."""
    gprs, fprs, mem = set(), set(), set()
    for op in body:
        if op.kind in ("ldr", "ldrf") and op.dst:
            (gprs if op.kind == "ldr" else fprs).add(op.dst)
        elif op.kind == "str":
            if op.off is not None:
                mem.add(op.off // 8)
        elif op.kind == "busy_loop" and op.dst:
            gprs.add(op.dst)
        elif op.kind in ("mov", "add", "sub", "and", "orr", "eor", "add_imm",
                         "add_lsl", "mul", "madd", "udiv", "fadd", "fsub",
                         "fmul", "fdiv") and op.dst:
            (fprs if _is_fpr(op.dst) else gprs).add(op.dst)
    # A body that only reads (or only writes memory) still has an observable
    # state: fall back to the checksum contract's full register/memory set.
    if not gprs and not fprs and not mem:
        gprs = set(isa.GPRS)
        fprs = set(isa.FPREGS)
        mem = set(range(isa.MEM_WORDS))
    return sorted(gprs), sorted(fprs), sorted(mem)


def _source_registers(body: Sequence[isa.Op]):
    """Registers read by the body (falling back to destinations)."""
    sources = set()
    for op in body:
        for field_name in ("a", "b", "c"):
            name = getattr(op, field_name)
            if _is_gpr(name) or _is_fpr(name):
                sources.add(name)
        if op.kind == "busy_loop" and op.dst:
            sources.add(op.dst)
    if not sources:
        for op in body:
            if op.dst and (_is_gpr(op.dst) or _is_fpr(op.dst)):
                sources.add(op.dst)
    return sorted(sources, key=lambda name: (name[0], int(name[1:])))


def _snapshot(state: isa.State):
    return copy.deepcopy(state)


def _flip(state: isa.State, register: str, bit: int):
    if _is_gpr(register):
        value = state.gpr(register)
        state.set_gpr(register, value ^ (1 << bit))
    elif _is_fpr(register):
        bits = isa.double_bits(state.fpr(register))
        state.fregs[register] = isa.bits_double(bits ^ (1 << bit))
    else:
        raise ValueError(f"cannot flip {register!r}")


def _diff(base: isa.State, other: isa.State, gprs, fprs, mem):
    """Return (any_change, hamming_bits, changed_words, total_words)."""
    bits = 0
    changed_words = 0
    total_words = len(gprs) + len(fprs) + len(mem)
    for name in gprs:
        diff = base.gpr(name) ^ other.gpr(name)
        if diff:
            changed_words += 1
            bits += bin(diff).count("1")
    for name in fprs:
        diff = isa.double_bits(base.fpr(name)) ^ isa.double_bits(other.fpr(name))
        if diff:
            changed_words += 1
            bits += bin(diff).count("1")
    for index in mem:
        diff = base.mem[index] ^ other.mem[index]
        if diff:
            changed_words += 1
            bits += bin(diff).count("1")
    return changed_words > 0, bits, changed_words, total_words


def avalanche(stream: Stream, bits: Iterable[int] | None = None,
              transient: bool = False,
              positions: Sequence[int] | None = None,
              pre_roll: int = 0) -> AvalancheResult:
    """Run the 1-bit avalanche test for one stream.

    ``transient=False`` flips a bit in the post-setup input and runs the whole
    body (input-perturbation avalanche).  ``transient=True`` flips a source bit
    after ``p`` body instructions of the first repetition and lets the rest of
    the stream propagate it, which matches a transient fault at an arbitrary
    instruction (the CHAOSFPU model) much more closely.
    """
    if stream.iterations <= 0:
        raise ValueError("iterations must be positive")
    if stream.reps <= 0:
        raise ValueError("reps must be positive")

    base_input = isa.State()
    for op in stream.setup:
        isa.apply(op, base_input)
    if pre_roll:
        isa.run_body(stream.body, base_input, stream.reps * pre_roll)

    baseline = _snapshot(base_input)
    isa.run_body(stream.body, baseline, stream.reps * stream.iterations)

    gprs, fprs, mem = _written_words(stream.setup, stream.body)
    sources = _source_registers(stream.body)
    if not sources:
        raise ValueError("body has no register sources to perturb")

    bit_positions = list(range(64)) if bits is None else list(bits)
    if transient:
        if positions is None:
            positions = sorted({0, len(stream.body) // 2,
                                max(0, len(stream.body) - 1)})
        positions = [min(max(0, int(position)), len(stream.body))
                     for position in positions]
    else:
        positions = [None]
    trials = changed = total_bits = total_changed_words = total_words = 0
    per_register = {}
    for register in sources:
        reg_trials = reg_changed = 0
        for position in positions:
            for bit in bit_positions:
                state = _snapshot(base_input)
                if position is None:
                    _flip(state, register, bit)
                    isa.run_body(stream.body, state,
                                 stream.reps * stream.iterations)
                else:
                    isa.run_body(stream.body[:position], state, 1)
                    _flip(state, register, bit)
                    isa.run_body(stream.body[position:], state, 1)
                    remaining = stream.reps * stream.iterations - 1
                    if remaining > 0:
                        isa.run_body(stream.body, state, remaining)
                changed_any, hamming, changed_words, words = _diff(
                    baseline, state, gprs, fprs, mem)
                trials += 1
                reg_trials += 1
                total_bits += min(64, hamming)
                total_changed_words += changed_words
                total_words += max(1, words)
                if changed_any:
                    changed += 1
                    reg_changed += 1
        per_register[register] = {
            "trials": reg_trials,
            "changed": reg_changed,
            "word_flip_ratio": round(reg_changed / reg_trials, 6)
            if reg_trials else 0.0,
        }

    ratio = changed / trials if trials else 0.0
    return AvalancheResult(
        trials=trials,
        changed_trials=changed,
        word_flip_ratio=ratio,
        avalanche_bit_ratio=(total_bits / trials / 64.0) if trials else 0.0,
        masking_penalty=1.0 - ratio,
        breadth=(total_changed_words / total_words) if total_words else 0.0,
        output_words=[f"gpr:{r}" for r in gprs]
        + [f"fpr:{r}" for r in fprs]
        + [f"mem:{i}" for i in mem],
        source_registers=sources,
        per_register=per_register,
    )


def template_stream(template_id: str, iterations: int = 40,
                    reps: int = 16) -> Stream:
    template = TEMPLATE_BY_ID.get(template_id)
    if template is None:
        raise KeyError(f"unknown template {template_id!r}")
    return Stream(setup=tuple(template.setup), body=tuple(template.body),
                  iterations=iterations, reps=reps, template_id=template_id)


def evaluate_all(iterations: int = 40, bits: Iterable[int] | None = None):
    results = {}
    for template in TEMPLATES:
        result = avalanche(template_stream(template.id, iterations), bits=bits)
        results[template.id] = {
            "target": template.target,
            "injector": template.injector,
            **result.as_dict(),
        }
    # Aggregate by target for the report.
    by_target = {}
    for template_id, row in results.items():
        by_target.setdefault(row["target"], []).append(row)
    summary = {}
    for target, rows in sorted(by_target.items()):
        summary[target] = {
            "templates": [row for row in rows],
            "mean_word_flip_ratio": round(
                sum(row["word_flip_ratio"] for row in rows) / len(rows), 6),
            "mean_masking_penalty": round(
                sum(row["masking_penalty"] for row in rows) / len(rows), 6),
        }
    return results, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", help="single template id")
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--bits", type=int, nargs="*", default=None,
                        help="bit positions to test (default 0..63)")
    parser.add_argument("--out", type=Path,
                        default=Path("m5out/phase2-avalanche/avalanche.json"))
    args = parser.parse_args(argv)

    if args.template:
        result = avalanche(template_stream(args.template, args.iterations),
                           bits=args.bits)
        payload = {"schema": "sdcfuzz.avalanche.v1",
                   "template": args.template,
                   "iterations": args.iterations,
                   **result.as_dict()}
    else:
        results, summary = evaluate_all(args.iterations, args.bits)
        payload = {"schema": "sdcfuzz.avalanche.v1",
                   "iterations": args.iterations,
                   "templates": results, "by_target": summary}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    if args.template:
        print(json.dumps(payload, indent=2))
    else:
        print(f"templates: {len(results)}  -> {args.out}")
        for target, row in summary.items():
            print(f"  {target:6s} masking={row['mean_masking_penalty']:.3f} "
                  f"flip={row['mean_word_flip_ratio']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
