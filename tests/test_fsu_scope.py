"""Active-scope (F0/F5) policy, dual-view index, and runner gate tests."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_index as I
import fsu_scope as S
import fsu_seed_runner as R


def test_scope_matches_registry():
    res = S.verify_scope_against_registry()
    assert res["ok"] is True, res["errors"]
    assert res["counts"]["F0"] == 72
    assert res["counts"]["F5"] == 8
    assert res["active_runid_count"] == 80
    assert res["active_seed_target"] == 240


def test_active_frequencies_and_enforcement():
    for f in ("F0", "F5"):
        assert S.is_active_freq(f)
        S.enforce_active_freq(f, f"FSU-X-{f}-W1")
    for f in ("F1", "F2", "F3", "F4", "F6"):
        assert not S.is_active_freq(f)
        with pytest.raises(S.ScopeError) as e:
            S.enforce_active_freq(f, f"FSU-X-{f}-W1")
        assert "frequency outside active scope" in str(e.value)
        assert "DEFERRED_BY_USER" in str(e.value)


def test_scope_status_labels_priority():
    assert S.scope_status("F0", 3) == "ACTIVE_COMPLETE_3_OF_3"
    assert S.scope_status("F0", 0) == "ACTIVE_NOT_RUN"
    assert (S.scope_status("F1", 3)
            == "HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE")
    assert S.scope_status("F2", 0) == "DEFERRED_BY_USER"
    # completed history wins over the deferred label
    assert S.scope_status("F3", 3) != "DEFERRED_BY_USER"


def test_scope_test_mode_cannot_write_formal_root(tmp_path):
    ok, _ = S.formal_out_root_allowed(
        {"scope_test_mode": True}, tmp_path / "runs")
    assert ok is True
    ok, why = S.formal_out_root_allowed(
        {"scope_test_mode": True}, ROOT / "runs/fsu")
    assert ok is False and "formal runs/fsu" in why


def test_runner_rejects_deferred_frequency_before_attempt(tmp_path):
    manifest = {
        "run_id": "FSU-FP04-F1-W4", "model_id": "FP04",
        "freq": "F1", "load_id": "W4", "submodel": "FP04-c",
        "workload": {"binary": str(tmp_path / "wl"), "golden": "a" * 64,
                     "oracle_kind": "array_hash"},
        "injector": {"component": "fsu", "fpu_mode": {"bitseg": "mant_lo"},
                     "rate": {"rate_divisor": 1000000, "jitter_pct": 50,
                              "warmup": 0},
                     "max_faults": 1, "first_clock": 0},
        "limits": {"timeout_s": 1},
    }
    mp = tmp_path / "m.json"
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    out = tmp_path / "runs"
    with pytest.raises(S.ScopeError):
        R.run_seed(mp, 1, out_root=out)
    assert not (out / "FSU-FP04-F1-W4" / "seed1" / "attempt-1").exists()


def test_index_dual_view_counts():
    runids = I._load_runids(ROOT / "docs/gem5-fi/fsu/runids.json")
    rows, summary, active = I.scan(
        runids, ROOT / "runs/fsu",
        ROOT / "docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.json")
    # historical full-registry view
    assert summary["total_runids"] == 173
    assert summary["target_seeds"] == 519
    assert summary["admitted_seeds_total"] == 50
    assert summary["complete_3_of_3"] == 16
    # FR07-W1 now has real-hook seeds; the old proxy attempts stay on disk.
    assert summary["proxy_seeds_total"] == 0
    assert summary["proxy_markers_total"] == 3
    assert summary["proxy_runids"] == []
    # active F0/F5 view
    assert active["active_runids"] == 80
    assert active["active_seed_target"] == 240
    assert active["active_admitted_seeds"] == 41
    assert active["active_proxy_seeds"] == 0
    assert active["active_proxy_markers"] == 3
    assert active["active_complete_runids"] == 13
    assert active["deferred_by_user_runids"] == 90
    assert active["historical_complete_out_of_scope_runids"] == 3
    assert active["historical_complete_out_of_scope_seeds"] == 9
    by_id = {r["runid"]: r for r in rows}
    assert by_id["FSU-FP04-F0-W4"]["scope_class"] == "ACTIVE_SCOPE"
    assert (by_id["FSU-FP04-F1-W4"]["scope_class"]
            == "HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE")
    assert by_id["FSU-FP04-F2-W5"]["scope_class"] == "DEFERRED_BY_USER"
    assert by_id["FSU-FP04-F1-W4"]["status"] == "COMPLETE_3_OF_3"
    # Real-hook certification supersedes the preserved proxy attempts.
    fr07 = by_id["FSU-FR07-F0-W1"]
    assert fr07["status"] == "COMPLETE_3_OF_3"
    assert fr07["seed_completion"] == "3/3"
    assert all(fr07["seeds"][s]["state"] == "admitted" for s in (1, 2, 3))
    assert all("/attempt-2" in fr07["seeds"][s]["attempt"] for s in (1, 2, 3))


def _campaign_payload(run_id):
    return {
        "schema_version": "arm-chaos-fi/v1",
        "campaign_id": "fsu_scope_gate_test",
        "run_id": run_id,
        "grid": {"target_index": [0]},
        "n_per_cell": 1,
        "workload": {"binary": "/bin/true"},
    }


def _write_campaign(path, run_id):
    path.write_text(json.dumps(_campaign_payload(run_id), indent=2),
                    encoding="utf-8")
    return path


def _run_campaign_dry(path):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools/campaign.py"), str(path), "--dry"],
        cwd=ROOT, capture_output=True, text=True, timeout=120)


def test_campaign_gate_accepts_only_active_frequencies():
    for f in ("F0", "F5"):
        assert S.deferred_frequencies_in(
            _campaign_payload(f"FSU-X-{f}-W1")) == []
    for f in ("F1", "F2", "F3", "F4"):
        assert S.deferred_frequencies_in(
            _campaign_payload(f"FSU-X-{f}-W1")) == [f]


@pytest.mark.parametrize("freq", ["F1", "F2", "F3", "F4"])
def test_campaign_rejects_deferred_frequency_before_gem5(tmp_path, freq):
    yaml_path = _write_campaign(tmp_path / "campaign.json",
                                f"FSU-FP04-{freq}-W4")
    r = _run_campaign_dry(yaml_path)
    out = r.stdout + r.stderr
    assert r.returncode != 0
    assert "frequency outside active scope" in out
    assert "DEFERRED_BY_USER" in out
    # gate runs before schema expansion / gem5 and creates no run directory
    assert not (ROOT / "runs/fsu_scope_gate_test").exists()


@pytest.mark.parametrize("freq", ["F0", "F5"])
def test_campaign_accepts_active_frequency(tmp_path, freq):
    yaml_path = _write_campaign(tmp_path / "campaign.json",
                                f"FSU-FP06-{freq}-W4")
    r = _run_campaign_dry(yaml_path)
    out = r.stdout + r.stderr
    assert "frequency outside active scope" not in out
    # The minimal payload intentionally lacks required campaign fields, so it
    # stops at schema validation — proof that it passed the frequency gate.
    assert "schema validation FAILED" in out


def test_proxy_marker_excludes_seed_and_allows_real_rerun(tmp_path):
    seed = tmp_path / "FSU-X-F0-W1" / "seed1"
    attempt = seed / "attempt-1"
    attempt.mkdir(parents=True)
    (attempt / "chain_report.json").write_text(
        json.dumps({"chain": {"faults": {}}, "oracle": {}}), encoding="utf-8")
    (attempt / "audit.json").write_text(json.dumps({"ok": True}),
                                        encoding="utf-8")
    (seed / "AUTHORITATIVE").write_text(str(attempt), encoding="utf-8")
    assert I._seed_state(seed)["state"] == "admitted"

    (seed / "PROXY_EVIDENCE.json").write_text(json.dumps({
        "classification": "PROXY_EVIDENCE",
        "attempt": str(attempt),
        "counts_toward_completion": False,
        "reason": "wrong injection site",
    }), encoding="utf-8")
    st = I._seed_state(seed)
    assert st["state"] == "proxy"
    assert st["counts_toward_completion"] is False
    # Original attempt files are untouched.
    assert (attempt / "chain_report.json").exists()
    assert (attempt / "audit.json").exists()

    # A new, real attempt can become AUTHORITATIVE without deleting the proxy
    # marker; only the marker's own attempt stays excluded.
    real = seed / "attempt-2"
    real.mkdir()
    (real / "chain_report.json").write_text(
        json.dumps({"chain": {"faults": {}}, "oracle": {}}), encoding="utf-8")
    (real / "audit.json").write_text(json.dumps({"ok": True}),
                                     encoding="utf-8")
    (seed / "AUTHORITATIVE").write_text(str(real), encoding="utf-8")
    assert I._seed_state(seed)["state"] == "admitted"
