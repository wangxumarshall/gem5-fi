"""Oracle interface: compare the frozen expected checksum with real gem5 stdout."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CHECKSUM_RE = re.compile(r"checksum=0x([0-9a-fA-F]+)")


def normalize(value: str) -> str:
    return str(value).strip().lower().removeprefix("0x")


def extract_checksum(text: str) -> str | None:
    matches = CHECKSUM_RE.findall(text)
    return matches[-1].lower() if matches else None


def check_oracle(expected: str, stdout_text: str) -> dict:
    want = normalize(expected)
    got = extract_checksum(stdout_text)
    if got is None:
        return {"status": "MISSING", "expected": want, "got": None,
                "reason": "no checksum=0x... line in stdout"}
    status = "PASS" if got == want else "FAIL"
    return {"status": status, "expected": want, "got": got}


def check_oracle_file(expected: str, stdout_path: Path) -> dict:
    return check_oracle(expected, Path(stdout_path).read_text(encoding="utf-8", errors="replace"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("expected", help="frozen golden checksum (with or without 0x)")
    ap.add_argument("stdout", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    result = check_oracle_file(args.expected, args.stdout)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"expected={result['expected']} got={result['got']}")
        print(f"ORACLE_{result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
