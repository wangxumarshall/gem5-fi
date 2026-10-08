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


class AccountingTests(unittest.TestCase):
    def _run(self, m, mock_results, runid="A01-F0-W3", freq="F0",
             trial_target=15):
        seq = list(mock_results)

        def mock(cell, args, seed, outdir):
            return seq[seed - 1] if seed <= len(seq) else seq[-1]

        m.run_single_cell = mock
        a = Args()
        a.phase = "trial"
        a.trial_target = trial_target
        a.max_seeds_per_cell = 3   # 小 cap 保测试秒级
        with tempfile.TemporaryDirectory() as td:
            m.run_cell_adaptive(make_cell(runid=runid, freq=freq), a, Path(td))
            return json.loads((Path(td) / runid / "cell_results.json")
                              .read_text())

    def test_T5_simfail_excluded_from_sdc_denominator(self):
        m = load_draft()
        r = self._run(m, [
            {"outcome": "SDC", "activated": 5, "attempted": 6,
             "eligible": 5, "injected": 5},
            {"outcome": "Crash", "crash_kind": "simulator_assert",
             "activated": 10, "attempted": 10, "eligible": 10,
             "injected": 10},
        ])  # 5+10=15 ≥ trial_target=15 → 恰好 2 runs
        self.assertEqual(r["activated"], 15)
        self.assertEqual(r["sim_fail"], 10)
        self.assertEqual(r["classes"]["SDC"], 5)
        self.assertEqual(r["classes"]["Crash"], 0)      # sim_fail 单列
        self.assertEqual(r["sdc_rate"], 1.0)            # 5/(15-10)
        self.assertEqual(r["eligible"], 15)
        self.assertEqual(r["eligible_rate"], 0.9375)    # 15/16
        self.assertEqual(r["activation_rate"], 1.0)     # 15/15
        self.assertEqual(r["conservation"], "OK")       # 5+10 == 15

    def test_T6_zero_denominator_rates_none_not_zero(self):
        m = load_draft()
        r = self._run(m, [
            {"outcome": "Masked", "activated": 0, "attempted": 0,
             "eligible": 0, "injected": 0},
        ], trial_target=5)
        self.assertIsNone(r["sdc_rate"])      # 分母 0 → None，不是 0.0
        self.assertEqual(r["classes"]["Masked"], 0)    # 计数保留
        self.assertEqual(r["stop_reason"], "seed-cap(3)")

    def test_D1_funnel_missing_counts_separately(self):
        m = load_draft()
        r = self._run(m, [
            {"outcome": "Timeout", "activated": 0, "attempted": None,
             "eligible": None, "injected": None},
        ], trial_target=5)
        self.assertEqual(r["funnel_missing_runs"], 3)
        self.assertIsNone(r["eligible_rate"])
        self.assertIsNone(r["activation_rate"])


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.m = load_draft()
        # 封闭 fp：小文件替身（不哈希真实 1.2GB gem5.opt）
        self.tmp = tempfile.TemporaryDirectory()
        tp = Path(self.tmp.name)
        for name in ("g5", "proxy", "l5"):
            (tp / name).write_bytes(b"pad-" + name.encode())
        self.m.G5 = tp / "g5"
        self.m.LSU_PROXY = tp / "proxy"
        self.m.L5 = tp / "l5"
        self.m._FP_CACHE.clear()
        self.out = tp / "runs"
        self.calls = []
        self.m.run_single_cell = self._mock

    def tearDown(self):
        self.tmp.cleanup()

    def _mock(self, cell, args, seed, outdir):
        self.calls.append(seed)
        return {"outcome": "Masked", "activated": 5, "attempted": 6,
                "eligible": 5, "injected": 5}

    def _args(self, target):
        a = Args()
        a.phase = "trial"
        a.trial_target = target
        return a

    def test_T4_no_double_count_on_rerun(self):
        m = self.m
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)  # 6 runs
        self.assertEqual(len(self.calls), 6)
        self.calls.clear()
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)  # 全复用
        self.assertEqual(len(self.calls), 0)
        cell = self.out / "A01-F0-W3"
        self.assertEqual(len(list(cell.glob("seed*/l5_verdict.json"))), 6)
        r = json.loads((cell / "cell_results.json").read_text())
        self.assertEqual(r["n_runs"], 6)
        self.assertEqual(r["activated"], 30)

    def test_T9_resume_extends_without_seed_duplication(self):
        m = self.m
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)  # 6 seeds
        self.calls.clear()
        m.run_cell_adaptive(make_cell(), self._args(40), self.out)  # +2 seeds
        self.assertEqual(self.calls, [7, 8])
        seeds = sorted(json.loads(p.read_text())["seed"] for p in
                       (self.out / "A01-F0-W3").glob("seed*/l5_verdict.json"))
        self.assertEqual(seeds, [1, 2, 3, 4, 5, 6, 7, 8])

    def test_fp_mismatch_stratifies_not_mixes(self):
        m = self.m
        cell = self.out / "A01-F0-W3"
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)
        # 篡改 seed3 的 fp → 前缀止于 2 → 重跑 3..6
        v3 = cell / "seed3" / "l5_verdict.json"
        v = json.loads(v3.read_text())
        v["config_fp"] = "deadbeef00000000"
        v3.write_text(json.dumps(v))
        self.calls.clear()
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)
        self.assertEqual(self.calls, [3, 4, 5, 6])
        self.assertTrue((cell / "seed3" /
                         "l5_verdict.fp_deadbeef00000000.json").exists())
        cur = json.loads((cell / "cell_results.json").read_text())["config_fp"]
        for p in cell.glob("seed*/l5_verdict.json"):
            self.assertEqual(json.loads(p.read_text())["config_fp"], cur)
        # 篡改聚合结果 fp → 下轮分层标记 + 旧文件改名保留
        cr = cell / "cell_results.json"
        r = json.loads(cr.read_text())
        r["config_fp"] = "cafe000000000000"
        cr.write_text(json.dumps(r))
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)
        r2 = json.loads(cr.read_text())
        self.assertTrue(r2["config_fp_isolated"])
        self.assertEqual(r2["prior_config_fp"], "cafe000000000000")
        self.assertTrue(
            (cell / "cell_results.fp_cafe000000000000.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
