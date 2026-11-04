"""FR07 v2 PRF-WB data-boundary hook: wiring, schema, and evidence tests."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_seed_runner as R
import fsu_index as I

GATES = [
    "FSU-FR07-F0-W1-HOOK-FP32-GATE.json",
    "FSU-FR07-F0-W1-HOOK-FP64-GATE.json",
    "FSU-FR07-F0-W3-HOOK-LANE-GATE.json",
    "FSU-FR07-F0-W1-HOOK-DUALBIT-GATE.json",
    "FSU-FR07-F0-W1-HOOK-SQUASH-GATE.json",
]


def _src(path):
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_runner_emits_hook_flag():
    assert R._fpu_filter_args({"prf_wb_hook": True}) == ["--fpu_prf_wb_hook"]
    assert R._fpu_filter_args({"prf_wb_hook": False}) == []
    with pytest.raises(ValueError):
        R._fpu_filter_args({"prf_wb_hook": "yes"})


def test_gate_manifests_are_well_formed():
    schema = json.loads((ROOT / "schemas/manifest.schema.json").read_text())
    jsonschema = pytest.importorskip("jsonschema")
    # FSU gate manifests intentionally carry only the runner's subset; the
    # new hook must be a legal fpu_mode and the mask must be explicit.
    def find_fpu(node):
        if isinstance(node, dict):
            props = node.get("properties", {})
            if "fpu_mode" in props:
                return props["fpu_mode"]
            for v in node.values():
                got = find_fpu(v)
                if got is not None:
                    return got
        elif isinstance(node, list):
            for v in node:
                got = find_fpu(v)
                if got is not None:
                    return got
        return None

    fpu_schema = find_fpu(schema)
    assert fpu_schema is not None
    for name in GATES:
        p = ROOT / "configs/fsu" / name
        assert p.is_file(), name
        m = json.loads(p.read_text())
        fpu = m["injector"]["fpu_mode"]
        assert fpu["prf_wb_hook"] is True, name
        assert m["injector"].get("fault_mask"), name
        jsonschema.validate(fpu, fpu_schema)


def test_negative_gates_are_explicit():
    for name in ("FSU-FR07-F0-W3-HOOK-PREC-MISMATCH-NEG.json",
                 "FSU-FR07-F0-W1-HOOK-NONFP-NEG.json"):
        m = json.loads((ROOT / "configs/fsu" / name).read_text())
        assert m["injector"]["fpu_mode"]["prf_wb_hook"] is True
        assert "Negative gate" in m["notes"]


def test_cpp_hook_is_wired_at_the_write_boundary():
    cc = _src("CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc")
    hh = _src("CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.hh")
    cpu = _src("CHAOS/gem5/src/cpu/o3/cpu.cc")
    dyn = _src("CHAOS/gem5/src/cpu/o3/dyn_inst.cc")
    iew = _src("CHAOS/gem5/src/cpu/o3/iew.cc")
    assert 'fi.injection_site = "prf_wb_data"' in cc
    assert 'fi.hook_version = "2"' in cc
    assert "shadowForWrite(" in hh and "interceptScalarWrite(" in hh
    assert "interceptVectorWrite(" in hh
    assert "chaosFPU->shadowForWrite(" in cpu
    assert "chaosFPU->interceptScalarWrite(" in cpu
    assert "chaosFPU->interceptVectorWrite(" in cpu
    assert "maybeArm(this)" in dyn
    assert "cancelPendingArm()" in dyn
    assert "noteSquash(this)" in dyn
    assert "noteProducerWakeup(" in iew
    # countOnly census must still use the legacy eligible stream.
    assert "if (prf_wb_hook && !count_only) return finalizeWb(dyn_inst);" in cc
    # The squash path retires the taint so a reallocated PRF index cannot be
    # attributed to the dead fault.
    assert "f.squashed = true;" in cc
    assert "f.consumed || f.squashed" in cc


def test_old_proxy_seeds_stay_excluded():
    rows, summary, active = I.scan(
        I._load_runids(ROOT / "docs/gem5-fi/fsu/runids.json"),
        ROOT / "runs/fsu",
        ROOT / "docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.json")
    fr07 = next(r for r in rows if r["runid"] == "FSU-FR07-F0-W1")
    assert fr07["status"] == "COMPLETE_3_OF_3"
    assert summary["proxy_seeds_total"] == 0
    # The old execute-post-write attempts are still preserved on disk.
    assert summary["proxy_markers_total"] == 3
