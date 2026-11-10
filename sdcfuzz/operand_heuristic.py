"""Local operand heuristic (NOT the upstream sdcfuzz D13).

The real D13 baseline is NOT this file.  It lives in the upstream sdcfuzz
repository (``gem5_config/workloads/sdc_probe_workload_d13.c``): it generates
random candidates at runtime, applies targeted mutations (XOR mask, +1,
rotate, XOR with the complement), and selects with
``popcount(x ^ (x + 1))`` as the carry-chain proxy, keeping several pure
random operands for coverage breadth.

This module is a *different*, host-side heuristic inspired by the route
document's description (carry chain as a cheap ACE proxy, reject fixed values
that mask faults).  It is kept only as an optional secondary control for
experiments in this repository.  It must not be used as the "D13 arm" of a
comparison, and it has no measured SDC/ACE effect yet.

"""

MASK64 = (1 << 64) - 1

# Pairs differing in fewer than this many bits are treated as logical-masking
# candidates: a single-bit fault in the shared bits would not change the
# result of most consumers.
MIN_TOGGLE_BITS = 8

# Values that behave as constants in real code and therefore tend to mask
# faults (zero, one and the all-ones pattern).
FIXED_VALUES = frozenset({0, 1, MASK64})


def popcount(value):
    return bin(value & MASK64).count("1")


def carry_chain(a, b):
    """Longest consecutive run of active carries while adding a and b.

    Bit i of the result depends on the carry out of bit i-1.  Carry out is
    ``(a & b) | ((a ^ b) & carry_in)``: ``a & b`` generates a carry,
    ``a ^ b`` propagates it.  The returned length counts the bits over which
    the carry stays active, so an all-ones operand plus one yields 64.
    """
    carry = 0
    run = 0
    longest = 0
    for bit in range(64):
        a_bit = (a >> bit) & 1
        b_bit = (b >> bit) & 1
        generate = a_bit & b_bit
        propagate = a_bit ^ b_bit
        carry = generate | (propagate & carry)
        if carry:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return longest


def toggle_bits(a, b):
    return popcount(a ^ b)


def masking_risk(candidate, reference):
    """True when *candidate* is a constant or too similar to *reference*.

    The reference operand itself may legitimately be zero (an accumulator
    seed, for example) without masking every fault: ``x + 0`` still
    propagates.  What matters is that the candidate is not one of the fixed
    constants, not identical to the reference, and differs in enough bits to
    expose a single-bit fault.
    """
    if candidate in FIXED_VALUES:
        return True
    if candidate == reference:
        return True
    return toggle_bits(candidate, reference) < MIN_TOGGLE_BITS


def score(a, b):
    """Ordering key: carry chain first, then toggling, then larger value."""
    return (carry_chain(a, b), toggle_bits(a, b), a)


def select(candidates, reference=0):
    """Pick the highest-scoring operand not flagged as logically masked.

    ``reference`` is the operand the candidate is paired with at runtime
    (for example the accumulator or multiplier input).  Raises ValueError
    when every candidate is masked: silently returning a fixed value would
    hide the masking condition this heuristic exists to avoid.
    """
    ranked = []
    for value in candidates:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"operand must be int, got {type(value)!r}")
        if value < 0 or value > MASK64:
            raise ValueError(f"operand out of 64-bit range: {value}")
        if not masking_risk(value, reference):
            ranked.append(value)
    if not ranked:
        raise ValueError("every candidate was flagged as logically masked")
    return max(ranked, key=lambda value: score(value, reference))


def candidates_for(reference, count=64, seed=0x5DC):
    """Deterministic candidate pool: low/high toggling patterns plus PRNG."""
    if count < 1:
        raise ValueError("count must be positive")
    pool = []
    # Structured patterns that stress carries and toggling in different ways.
    for period in range(1, 9):
        block = (1 << period) - 1
        pattern = 0
        for index in range(0, 64, period):
            pattern |= block << index
        pool.append(pattern & MASK64)
        pool.append((~pattern) & MASK64)
    state = seed & MASK64
    while len(pool) < count:
        # SplitMix64: deterministic and dependency-free.
        state = (state + 0x9E3779B97F4A7C15) & MASK64
        mixed = state
        mixed = ((mixed ^ (mixed >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        mixed = ((mixed ^ (mixed >> 27)) * 0x94D049BB133111EB) & MASK64
        pool.append((mixed ^ (mixed >> 31)) & MASK64)
    return pool[:count]


def choose_operand(reference, count=64, seed=0x5DC):
    """Convenience wrapper: build a deterministic pool and select from it."""
    return select(candidates_for(reference, count=count, seed=seed),
                  reference=reference)
