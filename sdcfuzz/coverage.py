"""Static ACE/IBR coverage contract for the local 19-template corpus.

The contract answers one question honestly: for each instruction form the base
templates execute, which observable metric proves that the form is covered?
It is deliberately a *mapping*, not a claim that every dynamic instruction is
accounted for; the companion ``scripts/test-template-coverage.py`` runs every
template in gem5 and checks that all mapped counters are actually non-zero.

Metric groups are kept coarse enough to be stable across builds:

* ``rf``    — integer physical-register reads/writes (RF ACE)
* ``vec``   — vector/FP physical-register low-64-bit lane reads/writes
* ``l1d``   — L1D demand reads/writes (L1 ACE)
* ``l1i``   — L1I demand reads (L1 ACE)
* ``alu``   — intAlu input bits (FU IBR)
* ``mult``  — intMult input bits (FU IBR)
* ``div``   — intDiv input bits (FU IBR)
* ``fpadd`` — fpAdd input bits (FU IBR)
* ``fpmul`` — fpMult input bits (FU IBR)

``busy_loop`` is a composite template operation (mov/add/subs/branch); its
required ``rf``/``alu`` metrics come from the integer operations in the loop.
Branches themselves are control operations and are intentionally not part of
FU IBR.
"""

# A metric is satisfied when at least one of its counters is non-zero.
METRIC_COUNTERS = {
    "rf": ("rf_reads", "rf_writes"),
    "vec": ("vec_reads", "vec_writes"),
    "l1d": ("l1d_reads", "l1d_writes"),
    "l1i": ("l1i_reads",),
    "alu": ("alu_bits",),
    "mult": ("mult_bits",),
    "div": ("div_bits",),
    "fpadd": ("fpadd_bits",),
    "fpmul": ("fpmul_bits",),
}

# Op.kind -> metrics that must be observed when that kind is executed.
OP_METRICS = {
    "mov": ("rf", "alu"),
    "add": ("rf", "alu"),
    "sub": ("rf", "alu"),
    "and": ("rf", "alu"),
    "orr": ("rf", "alu"),
    "eor": ("rf", "alu"),
    "add_imm": ("rf", "alu"),
    "add_lsl": ("rf", "alu"),
    "mul": ("rf", "mult"),
    "madd": ("rf", "mult"),
    "udiv": ("rf", "div"),
    "ldr": ("rf", "l1d"),
    "str": ("rf", "l1d"),
    "ldrf": ("vec", "l1d"),
    "fadd": ("vec", "fpadd"),
    "fmul": ("vec", "fpmul"),
    "busy_loop": ("rf", "alu"),
}


def template_metrics(template):
    """Return ``{metric: sorted(op kinds)}`` required by one template."""
    required = {}
    for op in tuple(template.setup) + tuple(template.body):
        try:
            metrics = OP_METRICS[op.kind]
        except KeyError as error:
            raise KeyError(
                f"template {template.id}: op kind {op.kind!r} has no ACE/IBR "
                "coverage mapping") from error
        for metric in metrics:
            required.setdefault(metric, set()).add(op.kind)
    return {metric: sorted(kinds) for metric, kinds in sorted(required.items())}


def template_counters(template):
    """Return the concrete counter names one template must make non-zero."""
    counters = set()
    for metric in template_metrics(template):
        counters.update(METRIC_COUNTERS[metric])
    return counters


def missing_from_table(templates):
    """Op kinds used by *templates* but absent from ``OP_METRICS``."""
    used = set()
    for template in templates:
        for op in tuple(template.setup) + tuple(template.body):
            used.add(op.kind)
    return sorted(used - set(OP_METRICS))


def coverage_failures(template, counters):
    """Return ``[(metric, op kinds, observed)]`` for unsatisfied metrics."""
    failures = []
    observed = template_metrics(template)
    for metric, kinds in observed.items():
        value = sum(counters.get(counter, 0.0)
                    for counter in METRIC_COUNTERS[metric])
        if value <= 0:
            failures.append((metric, kinds, value))
    return failures
