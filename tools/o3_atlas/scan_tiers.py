# tools/o3_atlas/scan_tiers.py
"""Enumerate gem5's implemented A64 instructions and match corpus titles to them.

Sources (build artifacts, machine-local):
- decoder-ns.hh.inc : class declarations (3790 incl. A32/T32)
- decoder-ns.cc.inc : constructor definitions; first string literal = mnemonic

Candidate lists are HINTS for confirmation, not an oracle — final tier
decisions land in data/instructions/*.yaml with evidence anchors.
"""
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

from .corpus import REPO

GEN = REPO / "build/ARM/arch/arm/generated"

# ARM ARM 别名（title 级）→ 主定义。语料 title 形如 "ADD (immediate)"。
ALIASES = {
    "MOV (register)": "ORR (shifted register)",
    "MOV (bitmask immediate)": "ORR (immediate)",
    "MOV (wide immediate)": "MOVZ",
    "MOV (inverted wide immediate)": "MOVN",
    "MOV (to/from SP)": "ADD (immediate)",
    "MVN (register)": "ORN (shifted register)",
    "NEG (shifted register)": "SUB (shifted register)",
    "NEG (immediate)": "SUB (immediate)",
    "CMP (shifted register)": "SUBS (shifted register)",
    "CMP (immediate)": "SUBS (immediate)",
    "CMP (extended register)": "SUBS (extended register)",
    "CMN (shifted register)": "ADDS (shifted register)",
    "CMN (immediate)": "ADDS (immediate)",
    "CMN (extended register)": "ADDS (extended register)",
    "TST (shifted register)": "ANDS (shifted register)",
    "TST (immediate)": "ANDS (immediate)",
    "CSET": "CSINC", "CSETM": "CSINV", "CINC": "CSINC",
    "CINV": "CSINV", "CNEG": "CSNEG",
    "SXTB": "SBFM", "SXTH": "SBFM", "SXTW": "SBFM",
    "UXTB": "UBFM", "UXTH": "UBFM", "UXTW": "UBFM",
    "ASR (immediate)": "SBFM", "LSL (immediate)": "UBFM",
    "LSR (immediate)": "UBFM", "ROR (immediate)": "EXTR",
    "ASR (register)": "ASRV", "LSL (register)": "LSLV",
    "LSR (register)": "LSRV", "ROR (register)": "RORV",
    "BFI": "BFM", "BFXIL": "BFM", "SBFIZ": "SBFM", "UBFIZ": "UBFM",
    "NGC": "SBC", "NGCS": "SBCS", "NEGS": "SUBS",
    "MNEG": "MSUB", "SMNEGL": "SMSUBL", "UMNEGL": "UMSUBL",
}

# 形式 → 类名后缀线索（Agent 探索：XImm=imm、SReg=shifted、EReg=extended、
# _IMM/_PRE/_POST/_REG/_LIT=寻址、Cc=置标志）
_FORM_SUFFIX = (
    ("immediate", ("Imm", "_IMM")),
    ("shifted register", ("SReg",)),
    ("extended register", ("EReg",)),
    ("register", ("Reg",)),
    ("literal", ("_LIT",)),
    ("no offset", ("NoOffset",)),
)


def class_names():
    text = (GEN / "decoder-ns.hh.inc").read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"^\s*class ([A-Za-z0-9_]+)", text, re.M))


@lru_cache(maxsize=1)  # 4.3MB 解析一次；372 标题复用（gen_stubs 依赖此缓存）
def constructor_mnemonics():
    """类 → 构造函数首字符串字面量（= 助记符）。LdpStp 动态助记符特例硬编码。"""
    text = (GEN / "decoder-ns.cc.inc").read_text(encoding="utf-8", errors="replace")
    result = {}
    for m in re.finditer(r"([A-Za-z0-9_]+)::\1\(", text):
        cls = m.group(1)
        # 构造体短；其后 400 字符窗口内找首个 Base("mnemonic"
        tail = text[m.end():m.end() + 400]
        mm = re.search(r':\s*[A-Za-z0-9_:]+\(\s*"([^"]+)"', tail)
        if mm:
            result.setdefault(cls, set()).add(mm.group(1))
    # 特例：LdpStp(const char *mnemonic, ...) 的助记符来自解码点
    # formats/aarch64.isa:1690-1737（"ldp"/"stp"/"ldnp"/"stnp"/"ldpsw"）
    result["LdpStp"] = {"ldp", "stp", "ldnp", "stnp", "ldpsw"}
    return {k: sorted(v) for k, v in result.items()}


def _split_title(title):
    canon = ALIASES.get(title, title)
    if " (" in canon:
        base, form = canon.split(" (", 1)
        return _norm_base(base), form.rstrip(")")
    return _norm_base(canon), ""


def _norm_base(base):
    """组合标题取首项（"CPYP , CPYM, CPYE"→"cpyp"；"CRC32B, ..."→"crc32b"），
    点号条件后缀剥离（"B.cond"→"b"）。"""
    base = base.split(",")[0].strip()
    if "." in base:
        base = base.split(".")[0]
    return base.lower()


def _suffix_matches(cls, form):
    for f, suffixes in _FORM_SUFFIX:
        if form == f:
            return any(s in cls for s in suffixes)
    return False


def _a64_like(cls):
    """A64 类名形先验：[XW]<Form>（AddXImm/BCond64/STXRX64/LDRX64_IMM…）。
    仅作排序加权（A32/T32 类共存在于生成文件），不是过滤器。"""
    return bool(re.search(r"[XW](Imm|SReg|EReg|Reg|1Reg|2Reg|Cond)", cls)
                or cls.endswith("64"))


def candidates_for(title):
    base, form = _split_title(title)
    mnem = constructor_mnemonics()
    out = []
    for cls in sorted(mnem):
        if base not in mnem[cls]:
            continue
        form_match = _suffix_matches(cls, form) if form else False
        why = f'mnemonic "{base}"'
        if form:
            why += f' + form "{form}" → suffix {"命中" if form_match else "不匹配"}'
        out.append({"class": cls, "mnemonic": base, "form": form,
                    "form_match": form_match, "a64_like": _a64_like(cls),
                    "why": why})
    out.sort(key=lambda x: (-x["form_match"], -x["a64_like"], x["class"]))
    return out


def main():
    if len(sys.argv) < 2:
        print("usage: scan_tiers.py \"<TITLE>\" [--all]", file=sys.stderr)
        sys.exit(2)
    if sys.argv[-1] == "--all":
        from .corpus import instruction_pages, title_of
        report = {title_of(p): candidates_for(title_of(p))[:5]
                  for p in instruction_pages()}
        json.dump(report, sys.stdout, indent=1, ensure_ascii=False)
        print()
    else:
        json.dump(candidates_for(sys.argv[1]), sys.stdout, indent=2, ensure_ascii=False)
        print()


if __name__ == "__main__":
    main()
