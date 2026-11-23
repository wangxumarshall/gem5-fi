# Fresh-clone verification record

* Release branch: `lsu`
* Fresh clone: `git clone --depth 1 --branch lsu git@github.com:wangxumarshall/gem5-fi.git`
* Clone HEAD: `49bd331e516addf5ca19a8a51ec42566724582e0` (final tests)
* Experiment source: `780099c805867ad194d74a81c3b6273aa0be8e5a`
* Final tag: `LSU_SE_PAPER_FINAL_FROZEN_20261119_SUPP1`
* gem5 source commit: `2bbf2907668f78e0b67473caf5a63153b70bede3`

## Build

```text
cd CHAOS/gem5
scons build/ARM/gem5.opt -j16
scons: done building targets.
```

Built binary: `CHAOS/gem5/build/ARM/gem5.opt` (1.1 GB).
Build log: `/var/tmp/lsu_cleanup_backup_20261123/metadata/gem5_clone_build.log`.

## Tests

```text
python3 -m pytest lsu-e2e/code/tests/test_arm64_semantics.py \
                   lsu-e2e/code/tests/test_strict_edges.py -q
50 passed
```

## Representative fault and control

From the clone, using the freshly built binary:

```text
./lsu-e2e/run_representative.sh fault
./lsu-e2e/run_representative.sh control
```

Both exited 0 and produced:

```text
prop_trace.csv.gz
commit_trace.csv.gz
micro_snap.csv.gz
stdout.log
```

Fault: `A01-C03-T01`, `injected=1`. Control: `injected=0`.
Captured stdout logs are in
`/var/tmp/lsu_cleanup_backup_20261123/metadata/smoke/`.

The final commit `49bd331e` differs from the build-validated commit
`e28b81cb` only by removing superseded LSU package archives from the
repository root; no source, config, workload, or test file changed.
