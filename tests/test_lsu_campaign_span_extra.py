"""LSU_LSQFWD_F0_SPAN_EXTRA: strict, auditable F0 span injection.

The W1 census measures an eligible stream that is not yet in the committed
LSQFWD_F0_SPAN table. The launcher injects it via JSON; a malformed value must
abort loudly instead of silently running with the wrong span.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "tools")

PROBE = r"""
import lsu_campaign as c
print(c.LSQFWD_F0_SPAN_EXTRA)
print(c._lsqfwd_tier_flags("S01", "F0", "mibench/bin/w1_all"))
"""


def _run(extra=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = TOOLS
    env.pop("LSU_LSQFWD_F0_SPAN_EXTRA", None)
    if extra is not None:
        env["LSU_LSQFWD_F0_SPAN_EXTRA"] = extra
    return subprocess.run([sys.executable, "-c", PROBE], cwd=REPO, env=env,
                          capture_output=True, text=True)


def test_no_override_keeps_entry_absent():
    r = _run()
    assert r.returncode == 0, r.stderr
    assert "{}" in r.stdout
    assert "None" in r.stdout


def test_valid_override_injects_span_flags():
    r = _run('{"S01:mibench/bin/w1_all": 12345}')
    assert r.returncode == 0, r.stderr
    assert "('S01', 'mibench/bin/w1_all'): 12345" in r.stdout
    assert "'--lsqfwd_span_events', '12345'" in r.stdout
    assert "'--lsqfwd_warmup_events', '1'" in r.stdout


def test_malformed_key_aborts_loudly():
    r = _run('{"S01": 5}')
    assert r.returncode != 0
    assert "invalid LSU_LSQFWD_F0_SPAN_EXTRA" in (r.stderr + r.stdout)
    assert "MODEL:workload_binary" in (r.stderr + r.stdout)


def test_nonpositive_span_aborts_loudly():
    r = _run('{"S01:mibench/bin/w1_all": 0}')
    assert r.returncode != 0
    assert "must be > 0" in (r.stderr + r.stdout)


def test_non_object_aborts_loudly():
    r = _run('[1, 2]')
    assert r.returncode != 0
    assert "expected a JSON object" in (r.stderr + r.stdout)
