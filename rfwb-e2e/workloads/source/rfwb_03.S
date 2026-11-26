    .text
    .global c01_m003_producer
    .global c01_m003_target
    .global c02_m003_producer
    .global c02_m003_target
    .global c03_m003_producer
    .global c03_m003_target
    .global c04_m003_producer
    .global c04_m003_target
    .global c05_m003_producer
    .global c05_m003_target

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

    .global c01_m003
c01_m003:
    HEAD
c01_m003_producer:
    add x10, x1, x2
c01_m003_target:
    eor x11, x10, x3
    add x12, x10, x11
    TAIL x11

    .global c02_m003
c02_m003:
    HEAD
c02_m003_producer:
    add x10, x1, x2
c02_m003_target:
    eor x11, x3, x10
    add x12, x10, x11
    TAIL x11

    .global c03_m003
c03_m003:
    HEAD
c03_m003_producer:
    add x10, x1, x2
c03_m003_target:
    eor x11, x10, x3
    add x11, x4, x5
    TAIL x11

    .global c04_m003
c04_m003:
    HEAD
c04_m003_producer:
    add x10, x1, x2
c04_m003_target:
    eor x11, x10, x3
    add x12, x10, x4
    eor x13, x11, x12
    TAIL x13

    .global c05_m003
c05_m003:
    stp x19, x20, [sp, #-16]!
    mov x20, x0
    mov x19, #8
2:
    add x1, x19, #10
    add x2, x19, #20
    add x3, x19, #30
    add x4, x19, #30
    add x5, x19, #50
c05_m003_producer:
    add x10, x1, x2
    cmp x3, x4
    b.eq 3f
    eor x11, x10, x4
    b 4f
3:
c05_m003_target:
    eor x11, x10, x4
4:
    str x11, [x20], #8
    subs x19, x19, #1
    b.ne 2b
    ldp x19, x20, [sp], #16
    ret
