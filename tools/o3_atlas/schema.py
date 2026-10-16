# tools/o3_atlas/schema.py
"""Hand-rolled record/family validator.

jsonschema is NOT installed on this host (pip offline) — same situation and
same rationale as tools/manifest_validate.py: this module IS the enforced
spec, kept honest by tests/test_schema.py.
"""
import re

from .corpus import instruction_pages

TIERS = ("implemented", "partial", "unimplemented", "fs-only", "macro-op")
BEHAVIORS = ("absent", "warn-nop", "illegal-fault")  # unimplemented 的三种真实形态
NODES = ("FETCH", "DECODE", "RENAME", "DISPATCH", "ISSUE", "EXECUTE", "MEMORY",
         "WRITEBACK", "COMMIT", "BPU", "FTQ", "REDIRECT")  # 标准节点词表
QUEUES = ("IQ", "LSQ")
INJECTORS = (
    "CHAOSDecode", "CHAOSRenameMap", "CHAOSFreeList", "CHAOSPhysReg", "CHAOSIQ",
    "CHAOSLSQFwd", "CHAOSL1DForward", "CHAOSAddrPath", "CHAOSROB", "CHAOSReg",
    "CHAOSExec", "CHAOSFPU", "CHAOSBPU", "CHAOSRAS", "CHAOSExMon", "CHAOSProbe",
    "CHAOSCommitTrace", "CHAOSMem", "CHAOSCache",
)
ANCHOR_RE = re.compile(r"^[A-Za-z0-9_./+-]+:\d+$")


def _corpus_names():
    return {p.name for p in instruction_pages()}


def _check_anchor_list(errors, container, where):
    for ev in container:
        a = ev.get("anchor", "")
        if not ANCHOR_RE.match(a):
            errors.append(f"{where}: bad anchor format: {a!r}")
        if not str(ev.get("claim", "")).strip():
            errors.append(f"{where}: evidence claim empty")


def validate_family(fam, name, families):
    errs = []
    if not str(fam.get("summary", "")).strip():
        errs.append(f"family {name}: summary missing")
    pipe = fam.get("pipeline", [])
    if not pipe:
        errs.append(f"family {name}: pipeline empty")
    for n in pipe:
        if n not in NODES:
            errs.append(f"family {name}: unknown node {n!r}")
    if fam.get("queue") not in QUEUES:
        errs.append(f"family {name}: queue must be one of {QUEUES}")
    if not str(fam.get("fu", "")).strip():
        errs.append(f"family {name}: fu missing")
    for inj in fam.get("default_injectors", []):
        if inj not in INJECTORS:
            errs.append(f"family {name}: unknown injector {inj!r}")
    for node, a in fam.get("anchors", {}).items():
        if node not in NODES:
            errs.append(f"family {name}: anchor for unknown node {node!r}")
        if not ANCHOR_RE.match(a):
            errs.append(f"family {name}: bad anchor {a!r}")
    return errs


def validate_instruction(rec, families):
    errs = []
    where = rec.get("doc", "<no doc>")
    if where not in _corpus_names():
        errs.append(f"{where}: doc is not a corpus instruction page")
    if not str(rec.get("mnemonic", "")).strip():
        errs.append(f"{where}: mnemonic missing")
    tier = rec.get("tier")
    if tier not in TIERS:
        errs.append(f"{where}: tier {tier!r} not in {TIERS}")
        return errs
    if tier == "unimplemented":
        if rec.get("behavior") not in BEHAVIORS:
            errs.append(f"{where}: unimplemented requires behavior in {BEHAVIORS}")
    else:
        fam = rec.get("family")
        if fam not in families:
            errs.append(f"{where}: family {fam!r} undefined")
        gem5 = rec.get("gem5") or {}
        for k in ("decode_mnemonic", "static_inst"):
            if not str(gem5.get(k, "")).strip():
                errs.append(f"{where}: gem5.{k} required for tier={tier}")
        dec = (gem5.get("anchors") or {}).get("decoder", "")
        if not ANCHOR_RE.match(dec):
            errs.append(f"{where}: gem5.anchors.decoder required for tier={tier}")
    for inj in rec.get("injectors", []):
        if inj not in INJECTORS:
            errs.append(f"{where}: unknown injector {inj!r}")
    if not rec.get("evidence"):
        errs.append(f"{where}: evidence required")
    _check_anchor_list(errs, rec.get("evidence", []), where)
    return errs


def validate_all(families, instructions):
    errs = []
    for name, fam in families.items():
        errs += validate_family(fam, name, families)
    for rec in instructions:
        errs += validate_instruction(rec, families)
    return errs
