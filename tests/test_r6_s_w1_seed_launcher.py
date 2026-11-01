"""The W1 launcher must finalize manifests without shell-export bugs.

Regression guard for the 2026-10-30/31 defects: an unterminated quote in the
finish block, and RC/END read from os.environ without being exported (which
raised KeyError and left manifests at RUNNING).
"""
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "tools", "r6_s_w1_seed.sh")


def test_script_parses():
    r = subprocess.run(["bash", "-n", SCRIPT], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_finish_block_uses_argv_not_environ():
    # Ignore comment lines: the header documents the historical defect.
    code = "\n".join(l for l in open(SCRIPT).read().splitlines()
                     if not l.lstrip().startswith("#"))
    assert 'os.environ["END"]' not in code
    assert 'os.environ["RC"]' not in code
    # values are passed positionally and parsed from sys.argv
    assert 'sys.argv[2]' in code and 'sys.argv[3]' in code
    # a failed finalize must not leave a .done marker
    assert "manifest finalize failed" in code
    assert "exit 6" in code


def test_quoted_heredoc_in_finish_block():
    text = open(SCRIPT).read()
    idx = text.index("manifest finalize failed")
    block = text[max(0, idx - 800):idx]
    assert "<<'PY'" in block, "finish-block heredoc must be quoted to avoid expansion"
