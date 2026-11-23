# Package index

* `code/` — runner, tests, configs, workloads, gem5 observation patch.
* `evidence/causal_chains/` — 180 authoritative chains (JSON/CSV/MD).
* `evidence/rp01/` — 15 RP01 observation chains + canonical stall traces.
* `evidence/controls/` — 60-control evidence indexes.
* `evidence/semantic/` — 6,812-row reconciliation, 1,141,566-row revalidation ledger (gzip), statistics, unit test.
* `evidence/squash/` — six historical squash cells.
* `evidence/manifest/` — 735 server raw-trace rows with SHA256. `reports/FINAL_EVIDENCE_MANIFEST.csv` has a `Scope` column: `PACKAGE` rows resolve from the package root via `RelativePath`; `SERVER_WORKSPACE` rows resolve via `AbsolutePath` on the server.
* `reports/` — FINAL_* authoritative reports; `reports/history/superseded/` — SUPERSEDED.
* `verification/` — executed tests and checksums.
* `SUPPLEMENT.md` — what changed relative to R2 (documentation and archive only; no experiment data changed).
