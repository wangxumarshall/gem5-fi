# method2 three-arm FS pilot (§2.10 C, Phase 5.6)

Checkpoint restore (cpt.237933688473) + m2_ptrchase.rcS (scheduler-walk
workload) + O3/V110, seeds 20260826-28, single fault per run.

| arm | injector | injection evidence | outcome (fs oracle) |
|---|---|---|---|
| PRF (read-out) | CHAOSPhysReg phys (active-only) | PhysReg[2] Active, held by in-flight; seed-28 mapped from ArchReg[3] | 3/3 kernel survives (Masked) |
| AGU (address path) | CHAOSAddrPath byte7_zero | old 0xffffffc009483f60 -> new 0xffffc008d03be0 (canonical->non-canonical) | **3/3 KERNEL OOPS (Crash/DUE)** |
| TLB (translation) | CHAOSArmTLB pfn_to_mapped_page | (Phase 4.4 anchor: live-page substitution fires) | kernel survives (Masked) |

## The AddrPath Oops signature (method2 field match)

dmesg (3/3 identical): `kfree+0x4` <- `release_user_cpus_ptr+0x1c` <-
`free_task` <- `__put_task_struct` <- RCU — the KERNEL SCHEDULER
task-release path (the find_busiest_group family the method2 field
signature lives in); x0=0x0 (kfree NULL deref) at the injected
non-canonical address region. This is the method2 'garbage pointer ->
translation fault' signature reproduced from the ADDRESS-PATH root cause.

## Three-root-cause differentiation (§2.10 E match scoring)

- **AGU arm matches the field signature** (kernel Oops in the scheduler
  path, deterministic 3/3): the byte7_zero address corruption is the
  root cause that reproduces the field's x10-garbage-pointer outcome.
- **PRF arm does NOT** (single flips absorbed; and userspace chase is
  forwarding-masked — SE conclusion): at FS steady state, single PRF
  flips are absorbed by the kernel.
- **TLB live-page arm does NOT crash** (silent wrong-page, 0% Crash —
  the Phase 5.4 formal): its risk is silent, not the field's Oops.

Pilot-grade n=3; formal n=384 per arm is the follow-up (now fully
campaign-izable: the KERNEL_OOPS exit event is handled).
