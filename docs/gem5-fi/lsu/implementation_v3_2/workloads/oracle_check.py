#!/usr/bin/env python3
"""Compare a workload's frozen checksum with a captured stdout file.

Accepts both `checksum=0x<hex>` (W2/W3/W5/W6/W7/W8) and a bare 16-hex line
(W1 AGU-AddrModes and W4 SQ-Forward).
"""
import re
import sys


def find_checksum(text):
    matches = re.findall(r"checksum=0x([0-9a-fA-F]+)", text)
    if matches:
        return matches[-1].lower()
    bare = re.findall(r"^\s*([0-9a-fA-F]{16})\s*$", text, re.MULTILINE)
    return bare[-1].lower() if bare else None


def main():
    if len(sys.argv) != 3:
        print("usage: oracle_check.py <expected_checksum> <stdout_file>")
        return 2
    raw_expected = sys.argv[1].strip().lower()
    expected = find_checksum(raw_expected) or raw_expected.removeprefix("0x")
    text = open(sys.argv[2], encoding="utf-8", errors="replace").read()
    got = find_checksum(text)
    if got is None:
        print("ORACLE_FAIL: no checksum line")
        return 1
    print(f"expected={expected} got={got}")
    print("ORACLE_PASS" if got == expected else "ORACLE_FAIL")
    return 0 if got == expected else 1


if __name__ == "__main__":
    sys.exit(main())
