#!/usr/bin/env python3
"""[OOO][P1] ooo_golden.baseline_key unit test (plan Task 4).

Pins the baseline_key contract:
  * order-insensitive to dict key ordering (canonical JSON);
  * sensitive to EVERY identity field (a different workload/binary/config/
    gem5/msnap period/golden_id must NOT share a golden);
  * spec yaml round-trips through load_spec.

Run: python3 tools/tests/test_ooo_golden_key.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
import ooo_golden  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


BASE = {
    "gem5_sha256": "a" * 64,
    "config_family": "C3",
    "config_sha256": "b" * 64,
    "workload_relpath": "workloads/ooo/coremark/coremark",
    "workload_sha256": "c" * 64,
    "trigger_mode": "cycle",
    "trigger_value": 1000,
    "max_faults": 1,
    "fault_type": "bit_flip",
    "rng_seed": 0,
    "maxinsts": 0,
    "msnap_every": 1000,
    "golden_id": "coremark-golden-v1",
}


def main():
    k1 = ooo_golden.baseline_key(dict(BASE))
    # key-order insensitivity
    reordered = {k: BASE[k] for k in sorted(BASE, reverse=True)}
    check("order-insensitive", k1 == ooo_golden.baseline_key(reordered))
    # every field matters
    for field, alt in [
        ("gem5_sha256", "d" * 64), ("config_sha256", "e" * 64),
        ("workload_relpath", "workloads/ooo/dep_chain/dep_chain"),
        ("workload_sha256", "f" * 64), ("trigger_value", 2000),
        ("msnap_every", 5000), ("golden_id", "depchainint-golden-v1"),
        ("rng_seed", 7), ("maxinsts", 100000),
    ]:
        mutated = dict(BASE)
        mutated[field] = alt
        check(f"sensitive-{field}",
              k1 != ooo_golden.baseline_key(mutated))
    # type discipline: 24-hex key
    check("key-shape", len(k1) == 24 and all(c in "0123456789abcdef" for c in k1),
          k1)
    # yaml round-trip
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "spec.yaml")
        ooo_golden.write_spec_yaml(dict(BASE), p)
        loaded = ooo_golden.load_spec_yaml(p)
        check("yaml-roundtrip", loaded == BASE,
              f"{set(loaded.items()) ^ set(BASE.items())}")
        check("key-from-yaml-spec", ooo_golden.baseline_key(loaded) == k1)

    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
