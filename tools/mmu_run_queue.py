#!/usr/bin/env python3
"""Run a JSON queue of FS jobs with a hard concurrency cap (default 2).

Each job: {"id": "...", "cmd": [...], "log": "...", "timeout": 2400}
The driver never reuses an existing run id (the runner/wrapper refuses
overwrite); it records one JSON status line per job.  Intended for the
closure sprint's serial 2-at-a-time FS schedule.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor


def run_job(job):
    started = time.time()
    env = dict(os.environ)
    env.update(job.get("env") or {})
    with open(job["log"], "w") as log:
        try:
            rc = subprocess.run(job["cmd"], stdout=log,
                                stderr=subprocess.STDOUT,
                                timeout=job.get("timeout", 2400),
                                env=env).returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            rc = 124
            timed_out = True
            log.write("\n[queue] TIMEOUT %ss\n" % job.get("timeout", 2400))
    return {
        "id": job["id"],
        "rc": rc,
        "timed_out": timed_out,
        "elapsed_sec": round(time.time() - started, 1),
        "log": job["log"],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--status", default=None)
    args = ap.parse_args(argv)
    with open(args.jobs) as fh:
        jobs = json.load(fh)
    status_path = args.status or (args.jobs + ".status.json")
    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for res in pool.map(run_job, jobs):
            results.append(res)
            print(json.dumps(res), flush=True)
            with open(status_path, "w") as fh:
                json.dump(results, fh, indent=2)
    return 0 if all(r["rc"] == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
