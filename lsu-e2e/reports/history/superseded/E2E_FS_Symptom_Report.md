# Full-System symptom campaign — environment assessment

**Status: BLOCKED FOR THIS ROUND (no Kernel Panic evidence claimed).**

The 180 SE samples were not replaced, and no FS result is presented as a
Kernel Panic.  The assessment below is evidence-backed.

## 1. Assets present on 0101

| Asset | Path | Size |
|---|---|---|
| ARM Linux kernel | `/home/sdc/gem5-fi-ding/gem5-fs/vmlinux` | 227 MiB |
| Ubuntu disk image | `/home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img` | 2.2 GiB |
| Bootloader | `/home/sdc/gem5-fi-ding/gem5-fs/boot.arm64` | present |
| DTB | `/home/sdc/gem5-fi-ding/gem5-fs/armv8_gem5_v1_1cpu.dtb` | present |
| FS config | `repo/configs/fs/lsu_b0_fs.py` (shim to `configs/se/arm_chaos_fs.py`) | present |

The frozen LSU worktree's `gem5-fs/` submodule is empty; the assets were read
from the existing `gem5-fi-ding/gem5-fs/` tree without modifying it.

## 2. What was executed

```
gem5.opt --outdir=e2e_extension/results/fs/boot_ctrl \
  repo/configs/fs/lsu_b0_fs.py \
  --kernel=/home/sdc/gem5-fi-ding/gem5-fs/vmlinux \
  --disk=/home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img \
  --bootloader=/home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 \
  --root-partition=/dev/vda1 --cpu=O3 --mem-size=2GiB
```

The simulation instantiated the FS platform and began a real ARM kernel boot.
The serial console (`board.terminal`, 9,069 bytes) records:

```
[0.000000] Booting Linux on physical CPU 0x0000000000 [0x410fd070]
[0.000000] Linux version 5.15.36 ... #1 SMP PREEMPT Thu Apr 28 13:51:08 PDT 2022
[0.000000] Kernel command line: root=/dev/vda1 rw console=ttyAMA0 earlycon=pl011,0x1c090000
...
[0.012000] pci 0000:00:01.0: [1af4:1000] type 00 class 0xff0000
```

After **15 minutes wall-clock**, simulated time had reached only **0.012 s**
and the boot was still in early PCI enumeration.  No userspace, no login and
no `m5 exit` were reached.  The process was stopped rather than left running;
`stats.txt` is empty because the run did not exit normally.

O3 full-system boot at this host rate is therefore not a practical route to a
representative steady-state symptom campaign in this round.

## 3. LSU model coverage in the FS config

`configs/se/arm_chaos_fs.py` mounts:

* `CHAOSAddrPath` (FS modes `byte7_zero`, `low_bit_flip`, `sub_inflight_addr`),
* `CHAOSArmTLB`, `CHAOSArmSysReg`, `CHAOSPTW`, `CHAOSPhysReg`.

It does **not** mount the frozen 12-model LSQ stack used by the 180 SE runs:
`CHAOSLSQFwd` (SQ01/SQ03/SP05/FW02/FW05/DA04/RP01), `CHAOSLQ04`,
`CHAOSMD04`, `CHAOSL1DForward` (LP01).  The FS `CHAOSAddrPath` API
(`mode`/`firstClock`) is also not the frozen SE `a01_bit3_load` PRE-hook API.

Consequently, an FS run of this config would not be the same fault model as
the SE samples, and no semantic parity is claimed.

## 4. What is blocked

* No FS workload with a representative LSU fault was executed.
* No Kernel Panic, kernel Oops, or application crash in FS is reported.
* No `E2E-FS-SYMPTOM` RunID exists in the 180-sample matrices.

## 5. Recommended next steps (not executed this round)

1. Use the existing Atomic-boot → checkpoint → O3-restore pipeline
   (`boot_ckpt.rcS`, `--restore-checkpoint`) so the O3 run starts at a
   steady-state checkpoint instead of paying the full O3 boot cost.
2. Port the frozen LSQ hooks (or a documented FS equivalent) into the FS
   config/SimObjects while preserving the frozen injector semantics.
3. Create independent `E2E-FS-SYMPTOM` runs, with a kernel-log capture and a
   real `Kernel Panic` classifier; do not map `gem5` fatal or watchdog to
   Kernel Panic.
4. Keep the FS campaign separate from the SE 180; never overwrite the frozen
   When-v2 results.

## 6. Evidence files

* `results/fs/boot_ctrl/board.terminal` — real kernel boot log.
* `results/fs/boot_ctrl/run.log` — gem5 banner/config messages.
* `results/fs/boot_ctrl/config.ini` — instantiated platform configuration.
* `results/fs/boot_ctrl/device.dtb` — generated DTB.

No claim of a Kernel Panic is made from these files.
