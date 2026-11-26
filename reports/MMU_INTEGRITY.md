# MMU zero-write integrity check

Protected workspace: `/home/sdc/gem5-fi-mmu-impl-v2`

The FPU campaign only performed read-only checks there:
`git rev-parse`, `git branch --show-current`, `git status --porcelain`,
`git show-ref`, `find` and `sha256sum`.

- Preflight inventory: `reports/MMU_PREFLIGHT_20261116_152217.txt`
- Postflight inventory: `reports/MMU_POSTFLIGHT_20261116_165105.txt`
- HEAD both times: `7794df8796c9455cb03217db7e5f6ebe53946fc2`
- Branch/refs and `git status --porcelain` lines: identical pre/post.
- Every SHA-256 under `MMU_FINAL/` and every top-level `MMU_FINAL*.zip`
  hash: identical pre/post.
- No MMU process was started, stopped, or inspected destructively.
- No file was created, deleted, renamed, compiled, or checked out under the
  MMU workspace by this FPU campaign.

The MMU working tree already contained unrelated pre-existing deleted files
at the FPU preflight; those deletions are present identically before and
after this campaign and were not touched.
