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


def check_coverage(instructions):
    """记录 doc 集合必须与语料 372 指令页集合严格相等（双向报差）。"""
    corpus = {p.name for p in instruction_pages()}
    have = {r.get("doc", "") for r in instructions}
    errs = []
    for missing in sorted(corpus - have):
        errs.append(f"coverage: corpus page missing from records: {missing}")
    for extra in sorted(have - corpus):
        errs.append(f"coverage: record doc not a corpus page: {extra}")
    return errs


def check_determinism(families, instructions):
    """每条记录/索引双渲染必须 byte-equal（纯函数级确定性）。"""
    from .corpus import category_of
    from .generate import render_index, render_page  # 惰性导入：避免循环依赖

    errs = []
    by_cat = {}
    for rec in instructions:
        by_cat.setdefault(category_of(Path(rec["doc"])), []).append(rec)
    for rec in instructions:
        fam = families.get(rec.get("family")) if rec.get("tier") != "unimplemented" else None
        if render_page(rec, fam) != render_page(rec, fam):
            errs.append(f"determinism: render_page unstable for {rec.get('doc')}")
    for cat, recs in sorted(by_cat.items()):
        if render_index(cat, recs) != render_index(cat, recs):
            errs.append(f"determinism: render_index unstable for {cat}")
    return errs


def main():
    families, instructions = load_data()
    errs = schema.validate_all(families, instructions)
    for where, a in iter_anchors(families, instructions):
        e = check_anchor(a, REPO)
        if e:
            errs.append(f"{where}: {e}")
    errs += check_coverage(instructions)
    errs += check_determinism(families, instructions)
    if errs:
        print("VALIDATION FAILED:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print(f"OK: {len(instructions)} records, {len(families)} families, "
          f"coverage exact, anchors verified, deterministic")


if __name__ == "__main__":
    main()
