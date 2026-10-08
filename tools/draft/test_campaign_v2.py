#!/usr/bin/env python3
"""tools/draft/test_campaign_v2.py — MIGRATION_DESIGN.md T1-T10（+fp 隔离）
mock run_single_cell；不跑 gem5。运行：python3 tools/draft/test_campaign_v2.py -v
（单类：python3 tools/draft/test_campaign_v2.py PolicyTests -v）"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS = REPO_ROOT / "tools"
DRAFT = TOOLS / "draft" / "lsu_campaign_v2.py"
MATRIX = REPO_ROOT / "runs/lsu/07-expanded-matrix-backfilled.csv"


def load_draft():
    sys.path.insert(0, str(TOOLS))  # draft 依赖 `from wilson import wilson_ci`
    spec = importlib.util.spec_from_file_location("lsu_campaign_v2", DRAFT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def make_cell(runid="A01-F0-W3", model="A01", freq="F0",
              workload="STREAM+PointerChase (W3)"):
    # CSV 行：col1=RunID col2=Model col3=Unit col7=Freq col9=Workload
    row = [""] * 10
    row[1], row[2], row[3], row[7], row[9] = runid, model, "AGU", freq, workload
    return row


class Args:
    phase = "trial"
    trial_target = 30
    screening_target = 385
    main_target = None
    wilson_stop_hw = 0.02
    max_seeds_per_cell = 1000
    timeout = 300
    fs_checkpoint = None


class PolicyTests(unittest.TestCase):
    def test_T1_key_runids_resolve_2401(self):
        m = load_draft()
        a = Args()
        self.assertEqual(len(m.KEY_RUNIDS), 21)
        for rid in sorted(m.KEY_RUNIDS):
            self.assertEqual(m.resolve_main_target(rid, a), 2401, rid)

    def test_T2_non_key_resolve_385(self):
        m = load_draft()
        a = Args()
        header, cells = m.load_matrix(str(MATRIX))
        runids = {c[m.COL_RUNID] for c in cells}
        self.assertGreaterEqual(len(runids), 300)
        self.assertTrue(m.KEY_RUNIDS <= runids,
                        "KEY runid absent from matrix: %s"
                        % sorted(m.KEY_RUNIDS - runids))
        non_key = runids - m.KEY_RUNIDS
        for rid in non_key:
            self.assertEqual(m.resolve_main_target(rid, a), 385, rid)
        print("T2: matrix runids=%d key=21 non_key=%d"
              % (len(runids), len(non_key)))

    def test_T3_no_nonkey_gets_2401(self):
        m = load_draft()
        a = Args()
        a.main_target = 2401  # 即使错误地传入全局 2401 也不得泄漏给非重点项
        header, cells = m.load_matrix(str(MATRIX))
        for c in cells:
            rid = c[m.COL_RUNID]
            want = 2401 if rid in m.KEY_RUNIDS else 385
            self.assertEqual(m.resolve_main_target(rid, a), want, rid)

    def test_T8_legacy_knobs_do_not_stop(self):
        m = load_draft()
        calls = []

        def mock(cell, args, seed, outdir):
            calls.append(seed)
            return {"outcome": "Masked", "activated": 50, "attempted": 60,
                    "eligible": 55, "injected": 50}

        m.run_single_cell = mock
        with tempfile.TemporaryDirectory() as td:
            a = Args()
            a.phase = "main"
            a.main_target = 5000        # 旧全局 5000：必须被忽略
            a.wilson_stop_hw = 0.5      # 旧序贯停止：必须被忽略
            m.run_cell_adaptive(make_cell(runid="X99-F0-W0"), a, Path(td))
            self.assertEqual(len(calls), 8)    # 385/50 → 8 runs
            calls.clear()
            m.run_cell_adaptive(make_cell(runid="A01-F0-W3"), a, Path(td))
            self.assertEqual(len(calls), 49)   # 2401/50 → 49 runs


if __name__ == "__main__":
    unittest.main(verbosity=2)
