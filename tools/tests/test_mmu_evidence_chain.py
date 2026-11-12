#!/usr/bin/env python3
"""Unit checks for the five strict IFU evidence chains.

The tests use the frozen pilot traces when present (runs/ is untracked); if a
trace is absent the case is skipped honestly, never reported as a pass.
"""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import mmu_trace_validate_v3 as v3  # noqa: E402
import mmu_evidence_chain as chain  # noqa: E402

CASES = [
    ("M03", "R05", "TEST-F1-M03-R05", 0x4005000000, "Execute"),
    ("M04", "R05", "TEST-F1-M04-R05", 0x4008000000, "Execute"),
    ("M05", "R05", "TEST-F1-M05-R05", 0x4010000000, "Execute"),
    ("M07", "R04", "TEST-F1-M07-R04", 0x400d400100, "Execute"),
    ("M07", "R05", "TEST-F1-M07-R05", 0x400d600180, "Execute"),
]


def load_case(case):
    model, context, run, va, mode = case
    run_dir = os.path.join(REPO, "runs", run)
    trace = os.path.join(run_dir, "Trace", "prop_evt.txt.gz")
    oracle = os.path.join(run_dir, "Run_Log", "observed_output.txt")
    if not (os.path.isfile(trace) and os.path.isfile(oracle)):
        raise unittest.SkipTest("frozen trace missing: %s" % run)
    events, _ = v3.load_events(trace)
    with open(oracle, errors="replace") as fh:
        text = fh.read()
    return events, chain.evaluate(model, context, events, va, mode, text)


class StrictChainTest(unittest.TestCase):
    def test_identity_chains_pass(self):
        for case in CASES:
            with self.subTest(context="%s/%s" % (case[0], case[1])):
                _, result = load_case(case)
                self.assertTrue(result["ok"],
                                msg="%s/%s: %s" % (case[0], case[1],
                                                   result["guards"]))
                self.assertEqual(result["missing_kinds"], [])
                self.assertEqual(result["guards"], [])
                self.assertIsNotNone(result["consumption"])
                self.assertNotEqual(
                    result["consumption"]["event_id"],
                    result["activation"]["event_id"],
                    "consumption must be a later event, not activation")

    def test_m03_identity_is_foreign(self):
        _, result = load_case(CASES[0])
        ident = result["identity"]
        self.assertEqual(ident["candidate_entry"], ident["lookup_entry"])
        self.assertEqual(ident["candidate_entry"], ident["result_entry"])
        self.assertNotEqual(ident["candidate_asid"], ident["requester_asid"])
        self.assertTrue(result["terminal_evidence"]
                        ["observed_matches_foreign_pfn"])

    def test_m04_entry_lifetime_consumer(self):
        _, result = load_case(CASES[1])
        ident = result["identity"]
        self.assertEqual(ident["mutated_entry"], ident["consumer_entry"])
        self.assertEqual(ident["mutated_instance"], "itb")
        self.assertTrue(result["terminal_evidence"]
                        ["consumer_uses_substituted_pfn"])
        # The C++ summary counter is 0 for this synthetic fetch; the proof is
        # the entry identity, so the chain must still be ok.
        self.assertTrue(result["ok"])

    def test_m05_partial_source_and_lookup(self):
        _, result = load_case(CASES[2])
        ident = result["identity"]
        self.assertEqual(ident["faulted_insert"], 230)
        self.assertEqual(ident["consumer_event"], 245)
        self.assertEqual(ident["lookup_event"], 244)
        self.assertEqual(ident["consumed_entry"], (699, 52))
        self.assertTrue(result["terminal_evidence"]["result_is_decoy"])

    def test_m07_activation_is_not_the_consumer(self):
        for case in (CASES[3], CASES[4]):
            _, result = load_case(case)
            self.assertEqual(result["activation_basis"],
                             "COTEMPORAL_PERMISSION_EVAL_KEY_MATCH")
            self.assertNotEqual(
                result["consumption"]["event_id"],
                result["activation"]["event_id"])
            self.assertEqual(result["consumption"]["kind"], "lsu_request")
            self.assertEqual(result["consumption"]["mode"], "Execute")

    def test_m07_negative_without_fetch_request(self):
        events, _ = load_case(CASES[3])
        trimmed = [e for e in events if chain.kind(e) != "lsu_request"]
        result = chain.evaluate("M07", "R04", trimmed, 0x400d400100,
                                "Execute", "")
        self.assertFalse(result["ok"])
        self.assertTrue(result["guards"] or result["missing_kinds"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
