import hashlib
import json
from pathlib import Path

ROOT = Path("docs/gem5-fi/lsu/implementation_v3_2")
ARCH = ROOT / "FW05_Workload_Archive"
PILOTS = ROOT / "pilots_v3_2_7"
PILOT_SHA = "0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_archive_binary_is_exact_pilot_binary():
    assert sha(ARCH / "bin/fw05_forward") == PILOT_SHA


def test_all_five_manifests_use_the_same_workload():
    shas = set()
    for d in sorted(PILOTS.glob("FW05-R0*")):
        shas.add(json.loads((d / "manifest.json").read_text())["workload"]["sha256"])
    assert shas == {PILOT_SHA}


def test_archive_has_required_parts():
    for rel in ("src/fw05_forward.c", "bin/fw05_forward", "build.sh",
                "run_pilot.sh", "golden/fw05_forward.golden", "README.md",
                "PROVENANCE.md", "SHA256SUMS"):
        assert (ARCH / rel).is_file(), rel
