# tools/o3_atlas/gen_stubs.py
"""Generate the 372-record stub ledger (tier 分账表) — reproducible first pass.

Evidence chain per record:
- implemented/macro-op/fs-only : scan_tiers 候选类在 formats/aarch64.isa 的
  `new <Class>(` 解码点（真实行号锚点）+ family 规则表
- unimplemented/warn-nop       : formats/aarch64.isa 的 WarnUnimplemented 解码点
- unimplemented/absent         : 候选为空（A64 解码树无匹配）

分类任务（计划 Task 10-24）在此基础上深填 overrides/evidence；本生成器
只产出可复核的第一过，不冒充终判。
"""
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import yaml

from .corpus import REPO, category_of, instruction_pages, title_of
from .scan_tiers import ALIASES, candidates_for

FORMATS = REPO / "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa"
DECODER_ANCHOR = "CHAOS/gem5/src/arch/arm/isa/formats/aarch64.isa"
DECODE_ROOT_LINE = 3820  # def format Aarch64()：A64 解码树根

FAMILIES_YAML = REPO / "docs/cpu/o3-atlas/data/families.yaml"

_MUL = {"MADD", "MSUB", "MUL", "MNEG", "SMADDL", "SMSUBL", "SMULL", "SMNEGL",
        "UMADDL", "UMSUBL", "UMULL", "UMNEGL", "SMULH", "UMULH"}
_DIV = {"SDIV", "UDIV"}
_EXCEPTION = {"SVC", "HVC", "SMC", "BRK", "HLT", "DCPS1", "DCPS2", "DCPS3"}
_FS_HUB = {"TLBI", "AT", "DC"}
# 系统枢纽显式覆盖：hub 类构造携带共享助记符（如 TlbiOp64("msr",...)），
# scan 无法按标题助记符匹配；类名来自已验证的解码行（formats/aarch64.isa）
_HUB_OVERRIDE = {
    "TLBI": ("Tlbi64LocalHub", "Tlbi64ShareableHub"),
    "AT": ("At64Hub",),
    "DC": ("Dczva", "Dccvau", "Dccvac", "Dccivac", "Dcivac"),
}
_ATOMIC_PREFIX = ("LDADD", "LDCLR", "LDEOR", "LDSET", "LDSMAX", "LDSMIN",
                  "LDUMAX", "LDUMIN", "STADD", "CAS", "SWP")
_EXCLUSIVE_PREFIX = ("LDXR", "LDAXR", "LDXP", "LDAXP", "STXR", "STLXR",
                     "STXP", "STLXP")
_ACQREL_PREFIX = ("LDAR", "LDAPR", "STLR", "STLLR")


@lru_cache(maxsize=1)
def _decode_sites():
    """类 → A64 解码树首个 `new Cls(` 行号（一次遍历）。"""
    sites = {}
    pat = re.compile(r"new ([A-Za-z0-9_]+)\(")
    for i, line in enumerate(FORMATS.read_text(encoding="utf-8",
                                               errors="replace").splitlines(), 1):
        for m in pat.finditer(line):
            sites.setdefault(m.group(1), i)
    return sites


@lru_cache(maxsize=1)
def _warn_nop():
    """mnemonic → WarnUnimplemented 解码行号。"""
    lines = FORMATS.read_text(encoding="utf-8", errors="replace").splitlines()
    out = {}
    for i, line in enumerate(lines, 1):
        if "new WarnUnimplemented(" in line:
            window = " ".join(lines[i - 1:i + 4])
            m = re.search(r'"([a-z0-9_. ]+)"', window)
            if m:
                out.setdefault(m.group(1), i)
    return out


def _canon(title):
    return ALIASES.get(title, title)


# 别名 → 家族（别名跟随主定义形状，而非语料类别）
_ALIAS_FAMILY = {
    "MOV (register)": "dataproc-shifted-reg",
    "MOV (bitmask immediate)": "logical-imm",
    "MOV (wide immediate)": "logical-imm",
    "MOV (inverted wide immediate)": "logical-imm",
    "MOV (to/from SP)": "dataproc-imm",
    "MVN (register)": "logical-reg",
    "NEG (shifted register)": "dataproc-shifted-reg",
    "NEG (immediate)": "dataproc-imm",
    "CMP (shifted register)": "compare", "CMP (immediate)": "compare",
    "CMP (extended register)": "compare",
    "CMN (shifted register)": "compare", "CMN (immediate)": "compare",
    "CMN (extended register)": "compare",
    "TST (shifted register)": "compare", "TST (immediate)": "compare",
    "CSET": "cond-select", "CSETM": "cond-select", "CINC": "cond-select",
    "CINV": "cond-select", "CNEG": "cond-select",
    "SXTB": "extend", "SXTH": "extend", "SXTW": "extend",
    "UXTB": "extend", "UXTH": "extend", "UXTW": "extend",
    "ASR (immediate)": "bitfield", "LSL (immediate)": "bitfield",
    "LSR (immediate)": "bitfield", "ROR (immediate)": "bitfield",
    "ASR (register)": "dataproc-2src", "LSL (register)": "dataproc-2src",
    "LSR (register)": "dataproc-2src", "ROR (register)": "dataproc-2src",
    "BFI": "bitfield", "BFXIL": "bitfield",
    "SBFIZ": "bitfield", "UBFIZ": "bitfield",
    "NGC": "dataproc-shifted-reg", "NGCS": "dataproc-shifted-reg",
    "NEGS": "dataproc-imm",
    "MNEG": "mul", "SMNEGL": "mul", "UMNEGL": "mul",
}


def _lsq_family(base):
    if base.startswith(_EXCLUSIVE_PREFIX):
        return "exclusive"
    if base in ("LDP", "LDNP", "LDPSW", "STP", "STNP"):
        return "ldst-pair"
    if base.startswith(_ATOMIC_PREFIX):
        return "atomic-lse"
    if base.startswith(_ACQREL_PREFIX):
        return "acquire-release"
    if base in ("PRFM", "PRFUM"):
        return "prefetch"
    if base.startswith("LD"):
        return "load"
    if base.startswith("ST"):
        return "store"
    return "load"


def family_for(title, category):
    """title → families.yaml 家族名（别名先归一到主定义再判）。"""
    if title in _ALIAS_FAMILY:
        return _ALIAS_FAMILY[title]
    canon = _canon(title)
    base = canon.split(" (")[0]
    if base in _MUL:
        return "mul"
    if base in _DIV:
        return "div"
    if category == "Arithmetic":
        if "immediate" in canon:
            return "dataproc-imm"
        if "extended" in canon:
            return "dataproc-extended-reg"
        return "dataproc-shifted-reg"
    if category == "Logical":
        return "logical-imm" if "immediate" in canon else "logical-reg"
    if category == "Compare":
        return "compare"
    if category == "Conditional-Select":
        return "cond-select"
    if category == "Count":
        return "count"
    if category == "PC-Relative":
        return "pc-relative"
    if category == "Cryptographic":
        return "dataproc-2src"
    if category == "Pointer-Authentication":
        return "dataproc-1src" if base != "PACGA" else "dataproc-2src"
    if category == "Branch":
        if base in ("B", "BL"):
            return "branch-imm"
        if base.startswith(("BR", "BLR", "RET")) or "AA" in base:
            return "branch-reg"
        return "branch-cond"
    if category == "Barrier-Hint":
        if base in ("DSB", "DMB", "ISB"):
            return "barrier"
        if base in ("PRFM", "PRFUM"):
            return "prefetch"
        return "hint"
    if category == "System":
        if base in ("MRS", "MSR"):
            return "system-reg"
        if base in _EXCEPTION:
            return "exception"
        return "system-hub"
    if category in ("Load-Store", "Atomic"):
        return _lsq_family(base)
    if category == "Bit-Manipulation":
        if base in ("CLZ", "CLS"):
            return "count"
        if base.startswith(("SXT", "UXT")):
            return "extend"
        if base in ("ADR", "ADRP"):
            return "pc-relative"
        return "bitfield"
    if category == "Other":
        if base in ("CSET", "CSETM", "CINC", "CINV", "CNEG"):
            return "cond-select"
        if base.startswith(("SXT", "UXT")):
            return "extend"
        if base in ("RMIF", "SETF8", "SETF16", "AXFLAG", "XAFLAG", "CFINV"):
            return "flag"
        if base in ("BFXIL", "SBFIZ", "UBFIZ"):
            return "bitfield"
        if base in ("CLZ", "CLS"):
            return "count"
        if base == "CLREX":
            return "hint"
        if base in ("PRFM", "PRFUM"):
            return "prefetch"
        return "dataproc-1src"  # 兜底；Task 24 逐条复核
    return "dataproc-1src"


def generate_all():
    families = yaml.safe_load(FAMILIES_YAML.read_text(encoding="utf-8"))
    sites = _decode_sites()
    warn_nop = _warn_nop()
    recs = []
    for page in instruction_pages():
        title = title_of(page)
        category = category_of(page)
        base_raw = title.split(" (")[0]
        base = _canon(title).split(" (")[0]
        cands = candidates_for(title)
        hit = next((c for c in cands if c["class"] in sites), None)
        hub_cls = next((c for c in _HUB_OVERRIDE.get(base_raw, ())
                        if c in sites), None)
        rec = {"doc": page.name, "mnemonic": title}
        if hub_cls and not hit:
            anchor = f"{DECODER_ANCHOR}:{sites[hub_cls]}"
            fam = family_for(title, category)
            rec.update({
                "tier": "fs-only",
                "family": fam,
                "gem5": {"decode_mnemonic": base_raw.lower(),
                         "static_inst": hub_cls,
                         "anchors": {"decoder": anchor}},
                "injectors": list(families[fam]["default_injectors"]),
                "evidence": [{
                    "claim": f"A64 解码树 return new {hub_cls}(...)（系统枢纽，"
                             f"构造共享 msr 框架助记符）；SE 行为受限，真实语义需 FS",
                    "anchor": anchor}],
            })
        elif hit:
            anchor = f"{DECODER_ANCHOR}:{sites[hit['class']]}"
            tier = "implemented"
            if hit["class"] == "LdpStp":
                tier = "macro-op"
            elif base in _FS_HUB:
                tier = "fs-only"
            fam = family_for(title, category)
            rec.update({
                "tier": tier,
                "family": fam,
                "gem5": {"decode_mnemonic": hit["mnemonic"],
                         "static_inst": hit["class"],
                         "anchors": {"decoder": anchor}},
                "injectors": list(families[fam]["default_injectors"]),
                "evidence": [{
                    "claim": f"A64 解码树 return new {hit['class']}(...)；"
                             f"family={fam} 骨架引用（分类任务深填）",
                    "anchor": anchor}],
            })
        elif base.lower() in warn_nop or base_raw.lower() in warn_nop:
            mnem = base.lower() if base.lower() in warn_nop else base_raw.lower()
            rec.update({
                "tier": "unimplemented", "behavior": "warn-nop",
                "evidence": [{
                    "claim": f"解码为 WarnUnimplemented（\"{mnem}\"）——警告 + NOP 语义",
                    "anchor": f"{DECODER_ANCHOR}:{warn_nop[mnem]}"}]})
        else:
            rec.update({
                "tier": "unimplemented", "behavior": "absent",
                "evidence": [{
                    "claim": "A64 解码树无匹配（scan_tiers 候选为空："
                             "生成代码无此助记符类）",
                    "anchor": f"{DECODER_ANCHOR}:{DECODE_ROOT_LINE}"}]})
        recs.append(rec)
    recs.sort(key=lambda r: r["doc"])
    return recs, families


def main():
    recs, _ = generate_all()
    by_cat = {}
    for r in recs:
        by_cat.setdefault(category_of(Path(r["doc"])), []).append(r)
    out_dir = REPO / "docs/cpu/o3-atlas/data/instructions"
    out_dir.mkdir(parents=True, exist_ok=True)
    for cat, rows in sorted(by_cat.items()):
        (out_dir / f"{cat}.yaml").write_text(
            yaml.safe_dump(rows, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8")
    # 分账表（tier × category）
    print("| category | implemented | macro-op | fs-only | unimplemented(absent) |"
          " unimplemented(warn-nop) | total |")
    print("|---|---|---|---|---|---|---|")
    grand = Counter()
    for cat in sorted(by_cat):
        c = Counter(r["tier"] + ("(" + r.get("behavior", "") + ")"
                                 if r["tier"] == "unimplemented" else "")
                    for r in by_cat[cat])
        grand.update(c)
        print(f"| {cat} | {c['implemented']} | {c['macro-op']} | {c['fs-only']} "
              f"| {c['unimplemented(absent)']} | {c['unimplemented(warn-nop)']} "
              f"| {len(by_cat[cat])} |")
    print(f"| **合计** | {grand['implemented']} | {grand['macro-op']} "
          f"| {grand['fs-only']} | {grand['unimplemented(absent)']} "
          f"| {grand['unimplemented(warn-nop)']} | {sum(grand.values())} |")


if __name__ == "__main__":
    main()
