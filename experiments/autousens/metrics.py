"""ACE / IBR / SAD metric layer for the AutoµSens experiments.

The roadmap document (`sdcfuzz/sdcfuzz-v1.2.md` §5.1) defines the
instruction→structure map over "各微架构结构（寄存器堆、L1D、LSQ、ALU、乘法器、
FP 单元、TLB、ROB 等）的激活模式" and quantifies structural coverage with three
families: **ACE** (register/lifetime coverage), **IBR** (logic-unit input toggle
ratio) and **SAD** (structural activation depth = occupancy of the OoO
structures).  A single "net activation event" per structure is therefore not the
metric the document asks for; this module extracts all three families from one
gem5 ``stats.txt`` dump.

Everything here reads the counters that already exist in the CHAOS gem5 build -
no gem5 change and no rebuild is required.  Missing required counters raise
``MetricError`` instead of silently becoming zero, because a zero SAD occupancy
and a missing SAD counter mean very different things.

Counter inventory (verified on a real dump, 2026-11-17):

ACE   ``core.rfAce.{int,vec}TrackedReads/Writes, {int,vec}AceRatio,
      {int,vec}AceRegCycles, intAceBitCycles(+Low32/High32), vecAceBitCycles,
      {int,vec}OverwriteDrops, {int,vec}SquashDiscards, measuredCycles``;
      ``<l1d|l1i>-cache-0.l1Ace.{trackedDemandReads,trackedDemandWrites,
      trackedFills,lifetimeEnds,aceLineCycles,aceBitCycles,aceRatio}``
IBR   ``core.fuIbr.{inputBits,issuedOps,unitCount,maxInputBits,ibrRatio}::<fu>``
      for ``intAlu,intMult,intDiv,fpAdd,fpMult,fpDiv``; ``excludedOps``
SAD   ``core.sad.{samples,issueWidth,issuedOps,issueRatio}`` and
      ``{ratio,usedSum,capacity}::<rob|iq|lq|sq|intPrf|vecPrf|fu>``
"""

from __future__ import annotations

from pathlib import Path

ACE_RF_SCALARS = (
    "intTrackedReads", "intTrackedWrites", "vecTrackedReads", "vecTrackedWrites",
    "intAceRegCycles", "intAceBitCycles", "intAceBitCyclesLow32",
    "intAceBitCyclesHigh32", "intAceRatio",
    "vecAceRegCycles", "vecAceBitCycles", "vecAceRatio",
    "intOverwriteDrops", "intSquashDiscards",
    "vecOverwriteDrops", "vecSquashDiscards",
    "measuredCycles", "windowBegins", "windowEnds",
)
ACE_CACHE_SCALARS = (
    "trackedDemandReads", "trackedDemandWrites", "trackedFills",
    "lifetimeEnds", "aceLineCycles", "aceBitCycles", "aceRatio",
    "measuredCycles", "windowBegins", "windowEnds",
)
ACE_CACHES = ("l1d", "l1i")

IBR_CLASSES = ("intAlu", "intMult", "intDiv", "fpAdd", "fpMult", "fpDiv")
IBR_PER_CLASS = ("inputBits", "issuedOps", "unitCount", "maxInputBits",
                 "ibrRatio")
IBR_GLOBALS = ("excludedOps", "measuredCycles", "windowBegins", "windowEnds")

SAD_RESOURCES = ("rob", "iq", "lq", "sq", "intPrf", "vecPrf", "fu")
SAD_PER_RESOURCE = ("ratio", "usedSum", "capacity")
SAD_GLOBALS = ("samples", "issueWidth", "issuedOps", "issueRatio",
               "measuredCycles", "windowBegins", "windowEnds")
# Added 2026-11-23: optional for backward compatibility with older dumps.
SAD_GLOBALS_OPTIONAL = ("enabled", "roiCycles", "idleCycles", "activeCycles")

FAMILIES = ("ace", "ibr", "sad")


class MetricError(RuntimeError):
    """A required counter is absent or ambiguous in the dump."""


def _suffix(stats, suffix, strict=True):
    matches = [value for name, value in stats.items() if name.endswith(suffix)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise MetricError(f"statistic *{suffix} matched {len(matches)} fields "
                          "(ambiguous counter)")
    if strict:
        raise MetricError(f"statistic *{suffix} is missing from the dump")
    return None


def _ratio(numerator, denominator):
    return (numerator / denominator) if denominator else None


def _ace(stats, strict):
    rf = {name: _suffix(stats, ".rfAce." + name, strict) for name in ACE_RF_SCALARS}
    caches = {}
    for cache in ACE_CACHES:
        prefix = f".{cache}-cache-0.l1Ace."
        caches[cache] = {name: _suffix(stats, prefix + name, strict)
                         for name in ACE_CACHE_SCALARS}
    derived = {}
    measured = rf.get("measuredCycles")
    if measured:
        int_accesses = ((rf.get("intTrackedReads") or 0.0)
                        + (rf.get("intTrackedWrites") or 0.0))
        vec_accesses = ((rf.get("vecTrackedReads") or 0.0)
                        + (rf.get("vecTrackedWrites") or 0.0))
        derived["rf_int_accesses_per_cycle"] = _ratio(int_accesses, measured)
        derived["rf_vec_accesses_per_cycle"] = _ratio(vec_accesses, measured)
        derived["rf_int_bits_per_cycle"] = _ratio(
            rf.get("intAceBitCycles") or 0.0, measured)
        derived["rf_vec_bits_per_cycle"] = _ratio(
            rf.get("vecAceBitCycles") or 0.0, measured)
        derived["rf_int_read_share"] = _ratio(
            rf.get("intTrackedReads") or 0.0, int_accesses)
        derived["rf_int_discard_share"] = _ratio(
            (rf.get("intOverwriteDrops") or 0.0)
            + (rf.get("intSquashDiscards") or 0.0), int_accesses)
    for cache, values in caches.items():
        measured = values.get("measuredCycles")
        events = ((values.get("trackedDemandReads") or 0.0)
                  + (values.get("trackedDemandWrites") or 0.0))
        if measured:
            derived[f"{cache}_events_per_cycle"] = _ratio(events, measured)
            derived[f"{cache}_line_cycles_per_cycle"] = _ratio(
                values.get("aceLineCycles") or 0.0, measured)
    return {"rf": rf, "caches": caches, "derived": derived}


def _ibr(stats, strict):
    classes = {}
    for fu in IBR_CLASSES:
        classes[fu] = {name: _suffix(stats, f".fuIbr.{name}::{fu}", strict)
                       for name in IBR_PER_CLASS}
    globals_ = {name: _suffix(stats, ".fuIbr." + name, strict)
                for name in IBR_GLOBALS}
    derived = {}
    for fu, values in classes.items():
        derived[f"{fu}_bits_per_op"] = _ratio(values.get("inputBits") or 0.0,
                                              values.get("issuedOps") or 0.0)
        derived[f"{fu}_op_share"] = _ratio(
            values.get("issuedOps") or 0.0, globals_.get("issuedOps"))
    total_bits = sum(values.get("inputBits") or 0.0
                     for values in classes.values())
    derived["bits_per_cycle"] = _ratio(total_bits,
                                       globals_.get("measuredCycles"))
    return {"classes": classes, "globals": globals_, "derived": derived}


def _sad(stats, strict):
    globals_ = {name: _suffix(stats, ".sad." + name, strict)
                for name in SAD_GLOBALS}
    globals_.update({name: _suffix(stats, ".sad." + name, False)
                     for name in SAD_GLOBALS_OPTIONAL})
    resources = {}
    for resource in SAD_RESOURCES:
        resources[resource] = {
            name: _suffix(stats, f".sad.{name}::{resource}", strict)
            for name in SAD_PER_RESOURCE}
    derived = {}
    samples = globals_.get("samples")
    roi_cycles = globals_.get("roiCycles")
    for resource, values in resources.items():
        capacity = values.get("capacity") or 0.0
        derived[f"{resource}_mean_used"] = _ratio(values.get("usedSum") or 0.0,
                                                  samples)
        derived[f"{resource}_capacity"] = capacity
        if capacity and samples:
            derived[f"{resource}_mean_occupancy"] = _ratio(
                (values.get("usedSum") or 0.0) / capacity, samples)
    ratios = [values["ratio"] for values in resources.values()
              if values.get("ratio") is not None]
    if ratios:
        derived["mean_resource_ratio"] = sum(ratios) / len(ratios)
    derived["max_resource_ratio"] = max(ratios) if ratios else None
    # ``samples`` is active cycles; the ROI length (including idle) is
    # roiCycles.  Keep both so callers do not compare active samples against
    # ACE/IBR measuredCycles.
    if roi_cycles is not None:
        derived["active_share"] = _ratio(samples, roi_cycles)
        derived["idle_cycles"] = globals_.get("idleCycles")
    return {"globals": globals_, "resources": resources, "derived": derived}


def extract(stats, strict=True):
    """Extract the three metric families from one statistics dump."""

    windows = {
        "rf_ace": _suffix(stats, ".rfAce.measuredCycles", strict),
        "l1d_ace": _suffix(stats, ".l1d-cache-0.l1Ace.measuredCycles", strict),
        "l1i_ace": _suffix(stats, ".l1i-cache-0.l1Ace.measuredCycles", strict),
        "ibr": _suffix(stats, ".fuIbr.measuredCycles", strict),
        "sad_samples": _suffix(stats, ".sad.samples", strict),
    }
    # New SAD dumps expose roiCycles (ROI length including idle), which is the
    # field comparable to ACE/IBR measuredCycles.  Older dumps fall back to
    # samples (active cycles) to preserve the previous behaviour.
    sad_roi = _suffix(stats, ".sad.roiCycles", False)
    windows["sad_roi"] = sad_roi if sad_roi is not None else windows["sad_samples"]
    window_values = [windows["rf_ace"], windows["l1d_ace"],
                     windows["l1i_ace"], windows["ibr"], windows["sad_roi"]]
    present = [value for value in window_values if value is not None]
    return {
        "windows": windows,
        "window_consistent": len(set(present)) == 1 if present else False,
        "ace": _ace(stats, strict),
        "ibr": _ibr(stats, strict),
        "sad": _sad(stats, strict),
    }


def flatten(metrics):
    """Flatten the nested metric document into ``family.group.metric`` keys."""

    flat = {}
    for name, value in metrics["windows"].items():
        flat[f"window.{name}"] = value
    flat["window.consistent"] = metrics["window_consistent"]
    rf = metrics["ace"]["rf"]
    for name, value in rf.items():
        flat[f"ace.rf.{name}"] = value
    for cache, values in metrics["ace"]["caches"].items():
        for name, value in values.items():
            flat[f"ace.{cache}.{name}"] = value
    for name, value in metrics["ace"]["derived"].items():
        flat[f"ace.derived.{name}"] = value
    for fu, values in metrics["ibr"]["classes"].items():
        for name, value in values.items():
            flat[f"ibr.{fu}.{name}"] = value
    for name, value in metrics["ibr"]["globals"].items():
        flat[f"ibr.globals.{name}"] = value
    for name, value in metrics["ibr"]["derived"].items():
        flat[f"ibr.derived.{name}"] = value
    for name, value in metrics["sad"]["globals"].items():
        flat[f"sad.globals.{name}"] = value
    for resource, values in metrics["sad"]["resources"].items():
        for name, value in values.items():
            flat[f"sad.{resource}.{name}"] = value
    for name, value in metrics["sad"]["derived"].items():
        flat[f"sad.derived.{name}"] = value
    return flat


def activation_pattern(metrics):
    """The coverage vector the roadmap document calls 激活模式.

    One entry per measured structure: ACE ratios for the register files and the
    two L1 caches, IBR ratios per FU class, SAD occupancy ratios per OoO
    resource.  ``None`` means "not measurable with this build" (e.g. no TLB
    counter exists), which is kept distinct from a measured zero.
    """

    pattern = {}
    for key in ("intAceRatio", "vecAceRatio"):
        pattern["ace.rf." + key] = metrics["ace"]["rf"].get(key)
    for cache, values in metrics["ace"]["caches"].items():
        pattern[f"ace.{cache}.aceRatio"] = values.get("aceRatio")
    for fu, values in metrics["ibr"]["classes"].items():
        pattern[f"ibr.{fu}.ibrRatio"] = values.get("ibrRatio")
    for resource, values in metrics["sad"]["resources"].items():
        pattern[f"sad.{resource}.ratio"] = values.get("ratio")
    return pattern


def check_coverage(metrics, minimum=0.0):
    """Return the families/resources that produced *no* measurable activity.

    A structure whose counters are all zero did not get activated by the stream;
    listing them separates "measured zero" from "cannot be measured".
    """

    inactive = []
    for key, value in activation_pattern(metrics).items():
        if value is None:
            inactive.append({"metric": key, "state": "unmeasurable"})
        elif value <= minimum:
            inactive.append({"metric": key, "state": "zero"})
    return inactive


def csv_header(flat):
    return ["stream"] + sorted(flat)


def csv_row(stream_id, flat):
    return [stream_id] + ["" if flat[key] is None else f"{flat[key]:.9g}"
                          for key in sorted(flat)]


def from_stats_path(path, strict=True):
    """Convenience wrapper: read the final dump of a ``stats.txt``."""

    dumps, current = [], None
    for line in Path(path).read_text(errors="replace").splitlines():
        if "Begin Simulation Statistics" in line:
            current = {}
        elif "End Simulation Statistics" in line:
            if current is not None:
                dumps.append(current)
            current = None
        elif current is not None:
            fields = line.split()
            if len(fields) >= 2:
                try:
                    current[fields[0]] = float(fields[1])
                except ValueError:
                    pass
    if not dumps:
        raise MetricError(f"no statistics dump in {path}")
    return extract(dumps[-1], strict=strict)
