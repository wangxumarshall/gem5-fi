"""Parallel W1 queue: empty-array set -u, reap-time grading, canary preseed.

Regression for the 2026-11-02 abort at `r6s_w1_parallel.sh:187`:
`declare -A RUNNING` under `set -u` makes `${#RUNNING[@]}` fail on bash 5.2.15
("RUNNING: 未绑定的变量"), so the queue died before launching any worker.
"""
import json
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "tools", "r6_s_w1_parallel.sh")


def _code():
    return "\n".join(l for l in open(SCRIPT).read().splitlines()
                     if not l.lstrip().startswith("#"))


def test_script_parses():
    r = subprocess.run(["bash", "-n", SCRIPT], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_empty_associative_array_is_initialised():
    code = _code()
    assert "declare -A RUNNING=()" in code
    # the buggy form expanded the empty array under `set -u`
    assert '"${#RUNNING[@]}" -lt' not in code
    assert "RUNNING_N=0" in code and '"$RUNNING_N" -lt' in code


def test_grading_happens_at_reap_not_only_after_loop():
    code = _code()
    # a worker reaped while at MAXJOBS must still be graded
    assert "reap_one()" in code
    assert 'grade "$rid" "$seed" "$OUTROOT/${rid}_s${seed}" worker "$rc"' in code


def _make_harness(tmp_path, tasks, preseed):
    sz = tmp_path / "bin"
    sz.write_text("fakebin")
    sha = subprocess.run(["sha256sum", str(sz)], capture_output=True,
                         text=True).stdout.split()[0]
    census = tmp_path / "census"
    for model, span in (("S01", 17669290), ("S02", 17669123)):
        d = census / f"{model}-w1"
        d.mkdir(parents=True)
        (d / "manifest.json").write_text(json.dumps(
            {"eligible_span": span, "status": "FINISHED",
             "binary_sha256": sha, "run_id": f"{model}-F0-W1"}))
    canary = tmp_path / "canary" / "F1_s1"
    canary.mkdir(parents=True)
    (canary / "manifest.json").write_text(json.dumps({
        "run_id": "F1", "seed": 1, "binary_sha256": sha, "status": "FINISHED",
        "exit_code": 0, "analysis_tool_head": "test",
        "checks": {"prop_evt.txt.gz_eof": True, "prop_trace.csv.gz_eof": True,
                   "stats_size": 1, "admission_status": "ADMITTED",
                   "admitted": True, "certified": True, "truncated": False,
                   "violations": []}}))
    (canary / ".done").write_text("")

    launcher = tmp_path / "fake_launch.sh"
    launcher.write_text(f"""#!/usr/bin/env bash
set -u
rid=$1; seed=$2; bin=$3; root=$4
D="$root/${{rid}}_s${{seed}}"
mkdir -p "$D/$rid/seed$seed"
{{ flock 7; echo "start $(date +%s%3N) $rid $seed" >> "{tmp_path}/timeline"; }} 7>>"{tmp_path}/timeline.lock"
sleep 3
echo x > "$D/$rid/seed$seed/stats.txt"
python3 - "$D" "$rid" "$seed" <<'PY'
import json, os, sys
d, rid, seed = sys.argv[1:4]
json.dump({{"run_id": rid, "seed": int(seed), "status": "FINISHED",
  "exit_code": 0, "binary_sha256": "{sha}", "analysis_tool_head": "test",
  "kind": "fake"}}, open(os.path.join(d, "manifest.json"), "w"))
json.dump({{"admission_status": "ADMITTED", "conservation": "OK",
  "runs": [{{"chain": {{"oracle_outcome": "Masked", "terminal": "full",
    "provable_to": "L5", "admitted": True, "certified": True,
    "truncated": False}}}}]}}, open(os.path.join(d, rid, "cell_results.json"), "w"))
PY
echo 0 > "$D/.exit_code"; touch "$D/.done"
{{ flock 7; echo "end $(date +%s%3N) $rid $seed" >> "{tmp_path}/timeline"; }} 7>>"{tmp_path}/timeline.lock"
""")
    launcher.chmod(0o755)

    env = dict(os.environ)
    env.update({
        "R6S_W1_BIN": str(sz), "R6S_W1_SHA": sha, "R6S_W1_WT": str(tmp_path),
        "R6S_W1_LAUNCH": str(launcher),
        "R6S_W1_OUTROOT": str(tmp_path / "root"),
        "R6S_W1_CENSUS": str(census), "R6S_W1_CANARY": str(canary),
        "R6S_W1_PRESEED": preseed,
        "R6S_W1_PAUSE": str(tmp_path / "no-pause"),
        "R6S_W1_STATE": str(tmp_path / "state.json"),
        "R6S_W1_SUMMARY": str(tmp_path / "summary.jsonl"),
        "R6S_W1_QLOCK": str(tmp_path / "queue.lock"),
        "R6S_W1_DONE_MARK": str(tmp_path / "DONE"),
        "R6S_W1_TASKS": ",".join(tasks),
        "R6S_W1_TOTAL_EXPECTED": str(len(tasks)),
        "R6S_W1_SKIP_GATE": "1",
        "MAXJOBS": "2",
    })
    return env


def test_queue_runs_empty_array_and_preseed(tmp_path):
    tasks = ["F1:1", "F1:2", "F2:1", "F2:2"]
    env = _make_harness(tmp_path, tasks, preseed="F1#1")
    r = subprocess.run(["bash", SCRIPT], env=env, capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "RUNNING: 未绑定的变量" not in r.stderr
    assert (tmp_path / "DONE").exists()

    recs = [json.loads(l) for l in
            (tmp_path / "summary.jsonl").read_text().splitlines()]
    assert len(recs) == 4                       # 1 preseed + 3 launched
    assert sum(x["source"] == "preseed" for x in recs) == 1
    assert all(x.get("status") == "FINISHED" for x in recs)
    # the canary seed is graded from its own dir and never re-run
    assert not (tmp_path / "root" / "F1_s1").exists()

    ev = [(int(x.split()[1]), x.split()[0]) for x in
          (tmp_path / "timeline").read_text().splitlines()]
    ev.sort()
    cur = mx = 0
    for _, kind in ev:
        cur += 1 if kind == "start" else -1
        mx = max(mx, cur)
    assert mx == 2, mx
