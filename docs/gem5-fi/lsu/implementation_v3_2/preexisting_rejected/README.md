# Pre-existing v3.2 artifacts — NOT ACCEPTED

These files were present in `/home/sdc/gem5-fi-ding/docs/gem5-fi/lsu/implementation_v3_2/`
at 2026-11-06 09:43-09:45 (before this worktree's Gate-1 work) and were copied here
for provenance only.

They are **not** Gate-1 or Gate-2 evidence:

1. `pilots/A01F0/addrpath_injections.log` records
   `Site: lsq_sendFragmentToTranslation`. The v3.1 source audit explicitly rejects
   this site for A01: `sendFragmentToTranslation` is a per-fragment post-split
   site, not the AGU raw output. The audited A01 hook is
   `LSQ::pushRequest` entry (`CHAOS/gem5/src/cpu/o3/lsq.cc:764-878`).
2. `pilots/A03F5/addrpath_injections.log` records
   `attempted=2772 eligible=2772 injected=0`. A pilot with zero injections is
   not a pass, regardless of the process exit code.
3. The bundled `platform/` code emits only a subset of Trace v3.1 fields and
   its terminal classifier can report `MASKED` for an incomplete trace, which
   the v3.2 task forbids.
4. The `workloads/*_fixed` binaries are not accompanied by a sanitizer run,
   regenerated golden, or a post-fix baseline bundle.

The accepted implementation is rebuilt from scratch under
`docs/gem5-fi/lsu/implementation_v3_2/` (outside this directory). Nothing here
is used by the platform or by any pilot.
