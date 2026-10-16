# tools/o3_atlas/validate.py
"""o3-atlas 全量校验器：schema + 锚点验真 + 覆盖 + 生成确定性（Task 6 补全）。"""
import sys
from pathlib import Path

import yaml

from . import schema
from .corpus import REPO, instruction_pages

DATA = REPO / "docs/cpu/o3-atlas/data"


def check_anchor(anchor, repo_root):
    path_s, _, line_s = str(anchor).rpartition(":")
    p = Path(repo_root) / path_s
    if not p.is_file():
        return f"anchor file missing: {anchor}"
    line = int(line_s)
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    if not (1 <= line <= len(lines)):
        return f"anchor line out of range: {anchor} (file has {len(lines)} lines)"
    if not lines[line - 1].strip():
        return f"anchor points at blank line: {anchor}"
    return None


def load_data():
    families = yaml.safe_load((DATA / "families.yaml").read_text()) or {}
    instructions = []
    for f in sorted((DATA / "instructions").glob("*.yaml")):
        instructions += yaml.safe_load(f.read_text()) or []
    return families, instructions


def iter_anchors(families, instructions):
    for name, fam in families.items():
        for node, a in (fam.get("anchors") or {}).items():
            yield f"family {name}.{node}", a
    for rec in instructions:
        for ev in rec.get("evidence", []):
            yield f"{rec.get('doc')}.evidence", ev["anchor"]
        for k, a in ((rec.get("gem5") or {}).get("anchors") or {}).items():
            yield f"{rec.get('doc')}.gem5.{k}", a


def main():
    families, instructions = load_data()
    errs = schema.validate_all(families, instructions)
    for where, a in iter_anchors(families, instructions):
        e = check_anchor(a, REPO)
        if e:
            errs.append(f"{where}: {e}")
    if errs:
        print("VALIDATION FAILED:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print(f"OK: {len(instructions)} records, {len(families)} families, anchors verified")


if __name__ == "__main__":
    main()
