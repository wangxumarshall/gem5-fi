    .text
    .global c01_m004_target
    .global c02_m004_target
    .global c03_m004_target
    .global c04_m004_target
    .global c05_m004_target

    .macro HEAD
    stp x19, x20, [sp, #-16]!
    mov x20, x0
    mov x19, #8
1:
    add x1, x19, #10
    add x2, x19, #20
    add x3, x19, #30
    add x4, x19, #40
    add x5, x19, #50
    .endm
    .macro TAIL reg
    str \reg, [x20], #8
    subs x19, x19, #1
    b.ne 1b
    ldp x19, x20, [sp], #16
    ret
    .endm

    .global c01_m004
c01_m004:
    HEAD
c01_m004_target:
    add x10, x1, x2
    eor x11, x3, x4
    TAIL x11

    .global c02_m004
c02_m004:
    HEAD
c02_m004_target:
    eor x10, x1, x2
    add x11, x3, x4
    TAIL x11

    .global c03_m004
c03_m004:
    HEAD
c03_m004_target:
    add x10, x1, x2
    add x6, x3, x4
    add x7, x6, x5
    eor x11, x7, x1
    TAIL x11

    .global c04_m004
c04_m004:
    HEAD
c04_m004_target:
    add x10, x1, x2
    eor x11, x10, x3
    add x12, x11, x4
    TAIL x12

    .global c05_m004
c05_m004:
    stp x19, x20, [sp, #-16]!
    mov x20, x0
    mov x19, #8
2:
    add x1, x19, #10
    add x2, x19, #20
    add x3, x19, #30
    add x4, x19, #30
    cmp x3, x4
    b.eq 3f
    add x11, x1, x2
    b 4f
3:
c05_m004_target:
    add x10, x1, x2
    eor x11, x10, x3
4:
    str x11, [x20], #8
    subs x19, x19, #1
    b.ne 2b
    ldp x19, x20, [sp], #16
    ret
