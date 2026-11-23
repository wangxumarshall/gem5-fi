/* start.S — freestanding AArch64 entry for the When-v2 workloads.
 * The eligible-event ROI must contain only the designed workload code, so
 * the binary is linked -nostdlib with no libc startup stream. */
    .global _start
    .type _start, %function
_start:
    mov x29, #0
    mov x30, #0
    bl main
    mov x0, #0
    mov x8, #93          /* exit */
    svc #0
    .size _start, .-_start
