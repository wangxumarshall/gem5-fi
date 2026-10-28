#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A2] A04-a object registry / A04-b same-page contract.

Pins:
  1. campaign route is a04_same_object (not the retired a04_subst proxy);
  2. seed parity selects A04-a (object) / A04-b (same page);
  3. A04-a has an explicit registry and a LOUD refusal when it is empty;
  4. the two W0/W3 symbols used by the registry exist (oracle_data/array);
  5. A04-b aligns the target to the ACCESS width, not a fixed 16B grid.

Usage: python3 tests/test_lsu_r6a2_a04.py
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def main():
    cpp = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc").read_text()
    camp = (ROOT / "tools/lsu_campaign.py").read_text()
    proxy = (ROOT / "configs/se/lsu_proxy.py").read_text()
    py = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py").read_text()

    print("[1] route + config surfaces")
    check("A04 route is a04_same_object",
          "a04_same_object" in LC.MODEL_FLAGS["A04"][1],
          str(LC.MODEL_FLAGS["A04"]))
    check("proxy accepts both A04 submodels",
          '"a04_same_object"' in proxy and '"a04_same_page"' in proxy)
    check("SimObject has aguObjectSpec param", "aguObjectSpec" in py)

    print("[2] seed parity: odd=object, even=same-page")
    check("campaign A04 parity block",
          'if model == "A04":' in camp
          and 'flags[i + 1] = "a04_same_page"' in camp
          and '"--agu_object_spec"' in camp)

    print("[3] A04-a loud refusal + same-object target")
    check("empty registry fatal",
          "aguObjectSpec (id:symbol:size:elem" in cpp
          and "refusing to fall back to" in cpp)
    check("target stays inside object",
          "off + size <= a04_obj->size" in cpp
          and "a04_tgt_off = addr - a04_obj->base" in cpp)

    print("[4] registry symbols exist in the current ELFs")
    for elf, sym in (("workloads/directed/agu_addrmodes", "array"),
                     ("workloads/directed/mini_check", "oracle_data")):
        r = subprocess.run(["readelf", "-sW", str(ROOT / elf)],
                           capture_output=True, text=True)
        check(f"{elf}: OBJECT {sym}",
              re.search(rf"\bOBJECT\b.*\b{sym}\b", r.stdout) is not None)

    print("[5] A04-b uses access-width alignment")
    check("page candidate step == size",
          "for (Addr o = 0; o + size <= 4096; o += size)" in cpp)

    if FAILED:
        print(f"R6-A2 A04 TEST: {len(FAILED)} FAILURE(S)")
        return 1
    print("R6-A2 A04 TEST: ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
