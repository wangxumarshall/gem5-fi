"""Parallel W1 worker: per-seed exclusivity + safe manifest finalization."""
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "tools", "r6_s_w1_par_seed.sh")


def _code():
    return "\n".join(l for l in open(SCRIPT).read().splitlines()
                     if not l.lstrip().startswith("#"))


def test_script_parses():
    r = subprocess.run(["bash", "-n", SCRIPT], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_per_seed_lock_and_fresh_dir():
    code = _code()
    assert 'exec 9>"$DIR/.lock"' in code
    assert "flock -n 9" in code
    assert "grep -v '^\\.lock$'" in code
    assert "REFUSED: non-fresh output dir" in code


def test_manifest_finalize_uses_argv():
    code = _code()
    assert 'os.environ["END"]' not in code
    assert 'os.environ["RC"]' not in code
    assert "sys.argv[2]" in code and "sys.argv[3]" in code
    assert "manifest finalize failed" in code


def test_records_binary_sha_and_span_env():
    code = _code()
    assert '"binary_sha256"' in code
    assert '"span_extra_env"' in code
