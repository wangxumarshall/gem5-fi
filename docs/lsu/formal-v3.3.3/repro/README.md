# Reproduction wrapper

The five frozen scripts in `audit_v3_3_3/trace_closure/final_config/` contain:

```bash
ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cd "$ROOT"
```

That path is the original campaign worktree. A fresh clone that runs the scripts unchanged would read the **old** worktree, not itself. `reproduce_from_clone.sh` therefore:

1. verifies the 7-file `SOURCE_MANIFEST.sha256`, the config SHA `8309da72…`, and the binary SHA `62e1b1be…` from the preserved archive;
2. copies each script to `<clone>/.repro/` with only the `ROOT=` line rewritten to the clone path;
3. records the transformed scripts' SHA256 in `.repro/transformed.sha256`;
4. runs `01_launch_campaign.sh --dry-run` (expected: `dry-run: 120 commands; no run dirs written`).

With `--regen`, it copies the archived campaign root into the clone and reruns stages 2–4 (`02_manifest_only.sh`, `03_full_collector.sh`, `FORCE=1 04_final_reports.sh`). This regenerates the collector CSVs and the 8-sheet Excel from the archived raw evidence; **it does not rerun the 120 experiments and does not rebuild the binary**.

The originals are never modified. If the transformed scripts differ from the expected logic, compare them after removing the `ROOT=` line:

```bash
diff <(grep -v '^ROOT=' audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh) \
     <(grep -v '^ROOT=' .repro/01_launch_campaign.sh)
# expected: no output
```
