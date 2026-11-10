"""Command line entry point for the local sdcfuzz Phase-0 baseline."""

import argparse
import json
import sys
from pathlib import Path

from . import operand_heuristic as heuristic
from .evaluate import DEFAULT_GEM5, build_index, summarize
from .generator import DEFAULT_ITERATIONS, render_guest
from .templates import TEMPLATES, TEMPLATE_BY_ID


def cmd_list(args):
    print(f"{'id':16s} {'target':6s} {'injector':14s} title")
    for template in TEMPLATES:
        print(f"{template.id:16s} {template.target:6s} "
              f"{template.injector:14s} {template.title}")
    print(f"\n{len(TEMPLATES)} templates")
    return 0


def cmd_generate(args):
    template = TEMPLATE_BY_ID.get(args.id)
    if template is None:
        print(f"unknown template: {args.id}", file=sys.stderr)
        return 2
    operand = None
    if args.operand_heuristic:
        reference = 0
        for op in template.setup:
            if op.kind == "mov" and op.dst == "x12":
                reference = op.imm
        operand = heuristic.choose_operand(reference, count=args.pool,
                                     seed=args.seed)
    source, expected = render_guest(template, args.iterations, operand=operand)
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{template.id}.c"
    path.write_text(source)
    print(f"{path} expected_checksum={expected:016x}"
          + (f" heuristic_operand=0x{operand:016x}" if operand is not None else ""))
    return 0


def cmd_heuristic(args):
    value = heuristic.choose_operand(args.reference, count=args.count, seed=args.seed)
    print(f"selected=0x{value:016x}")
    print(f"carry_chain={heuristic.carry_chain(value, args.reference)} "
          f"toggle_bits={heuristic.toggle_bits(value, args.reference)}")
    return 0


def cmd_evaluate(args):
    index, path, outdir = build_index(
        gem5=args.gem5, outdir=args.outdir, iterations=args.iterations,
        cc=args.cc)
    print(summarize(index))
    print(f"\nindex: {path}")
    print(f"runs:  {outdir}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list", help="list the 19 baseline templates")
    listing.set_defaults(func=cmd_list)

    generate = sub.add_parser("generate", help="render one template to C")
    generate.add_argument("--id", required=True)
    generate.add_argument("--iterations", type=int,
                          default=DEFAULT_ITERATIONS)
    generate.add_argument("--outdir", default="m5out/sdcfuzz-generated")
    generate.add_argument("--operand-heuristic", action="store_true",
                          help="pick the x12 operand with the LOCAL heuristic"
                               " (not upstream D13)")
    generate.add_argument("--pool", type=int, default=64)
    generate.add_argument("--seed", type=lambda x: int(x, 0), default=0x5DC)
    generate.set_defaults(func=cmd_generate)

    selection = sub.add_parser("heuristic",
                               help="show one LOCAL heuristic operand choice"
                                    " (not upstream D13)")
    selection.add_argument("--reference", type=lambda x: int(x, 0), default=0)
    selection.add_argument("--count", type=int, default=64)
    selection.add_argument("--seed", type=lambda x: int(x, 0), default=0x5DC)
    selection.set_defaults(func=cmd_heuristic)

    evaluate = sub.add_parser("evaluate",
                              help="compile and measure all templates")
    evaluate.add_argument("--gem5", default=str(DEFAULT_GEM5))
    evaluate.add_argument("--outdir", default=None)
    evaluate.add_argument("--iterations", type=int,
                          default=DEFAULT_ITERATIONS)
    evaluate.add_argument("--cc", default="aarch64-linux-gnu-gcc")
    evaluate.set_defaults(func=cmd_evaluate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
