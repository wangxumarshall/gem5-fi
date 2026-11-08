"""v3.2.9 consistency: Excel v3.2.4 / CSV / manifests / archive."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_v329_consistency as check  # noqa: E402


def test_artifacts_consistent():
    assert check.main() == 0
