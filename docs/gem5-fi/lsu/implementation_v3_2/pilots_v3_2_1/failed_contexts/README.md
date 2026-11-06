# Failed R01-R05 contexts (not accepted)

These are real run attempts, not passes.

- `FW02-R02`: the process aborted before a suppression was recorded; no
  Pilot metadata/trace summary exists. This context did NOT trigger the F6
  fault. Raw run log is `run.log` where available.
- `FW02-R03`: one suppression was recorded, but the process aborted before a
  clean summary; the JSONL is INVALID/PARTIAL and is not accepted.

They are retained to show the failures honestly; they are not counted in the
accepted-pilot table.
