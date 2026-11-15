#!/usr/bin/env python3
"""Check the frozen result invariants (independent of file hashes)."""
import csv
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.normpath(os.path.join(HERE, "..", "results"))
problems = []

matrix = os.path.join(R, "formal", "campaign_package", "40_Sample_Matrix_Completed.csv")
rows = list(csv.DictReader(open(matrix)))
terminal = Counter(r["TerminalState"] for r in rows)
activation = Counter(r["ActivationStatus"] for r in rows)
trace = Counter(r["TraceCompleteness"] for r in rows)
if len(rows) != 40:
    problems.append("40-sample matrix has %d rows" % len(rows))
if terminal != Counter({"SDC": 31, "DETECTED_CONTAINED": 5, "SQUASHED": 4}):
    problems.append("terminal distribution %s" % dict(terminal))
if activation != Counter({"ACTIVATED": 40}):
    problems.append("activation distribution %s" % dict(activation))
if trace != Counter({"COMPLETE": 40}):
    problems.append("trace completeness %s" % dict(trace))

summary = json.load(open(os.path.join(
    R, "repeatability", "analysis", "repeat_campaign", "analysis",
    "Repeatability_Summary.json")))
for key in ("ActivationConsistencyCount", "PropagationConsistencyCount",
            "TerminalConsistencyCount"):
    if summary.get(key) != {"MATCH": 10}:
        problems.append("%s = %s" % (key, summary.get(key)))
if summary.get("CompletedRepeatRuns") != 10:
    problems.append("completed repeat runs = %s" % summary.get("CompletedRepeatRuns"))

control_rows = list(csv.DictReader(open(
    os.path.join(R, "formal", "audit", "Control_Map.csv"))))
controls = {r["ControlRunDir"] for r in control_rows}
if len(control_rows) != 40 or len(controls) != 28:
    problems.append("control map: %d rows / %d unique controls" %
                    (len(control_rows), len(controls)))
if {r["AuditVerdict"] for r in control_rows} != {"PASS"}:
    problems.append("control audit verdicts are not all PASS")

print("formal samples : %d" % len(rows))
print("terminal       : %s" % dict(sorted(terminal.items())))
print("activation     : %s" % dict(activation))
print("trace          : %s" % dict(trace))
print("controls       : %d unique / %d sample mappings" % (len(controls), len(control_rows)))
print("repeat         : activation/propagation/terminal 10/10 MATCH")
if problems:
    print("MMU_RESULT_INVARIANTS=FAIL")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("MMU_RESULT_INVARIANTS=PASS")
