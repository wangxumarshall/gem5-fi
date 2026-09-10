# H7 boot-phase two-arm pilot (PTW clear_valid, ECC off/on)

Boot-phase checkpoint cpt.100000000 (100M ticks, walk-dense early boot);
restore + PTW clear_valid at checkpoint+50K; 2 seeds per arm; short
observation window (1200s — full boot continuation exceeds the fault
machine's wall-time budget).

| arm | runs | verdict |
|---|---|---|
| ECC off | 2 | timeout, no Oops — injection landed (faults=1) but the kernel neither died nor finished booting in the window (PTE error slows/wedges boot continuation) |
| ECC on | 2 | rc=0 — boot continuation COMPLETED cleanly with the fault injected (ECC corrected the PTE error) |

Direction reading (pilot-grade, honest): the ECC-on arm completes boot
under the same fault that stalls the ECC-off arm — consistent with the
fi-h6-h7 branch's original H7 expectation (ECC-on spurious~0 / off
spurious>0), but at pilot scale with a short window. A full formal
(needs the longer window or a healthier machine) is the follow-up.
