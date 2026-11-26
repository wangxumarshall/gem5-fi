    .text
    .global c01_m001_producer
    .global c01_m001_marker
    .global c02_m001_producer
    .global c02_m001_marker
    .global c03_m001_producer
    .global c03_m001_marker
    .global c04_m001_producer
    .global c04_m001_marker
    .global c05_m001_producer
    .global c05_m001_marker

    .macro LOOP_HEAD
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

    .macro LOOP_TAIL reg
    str \reg, [x20], #8
    subs x19, x19, #1
    b.ne 1b
    ldp x19, x20, [sp], #16
    ret
    .endm

    .global c01_m001
c01_m001:
    LOOP_HEAD
c01_m001_producer:
    add x10, x1, x2
c01_m001_marker:
    add x12, x10, x3
    eor x11, x10, x3
    LOOP_TAIL x11

    .global c02_m001
c02_m001:
    LOOP_HEAD
c02_m001_producer:
    add x10, x1, x2
c02_m001_marker:
    add x12, x10, x3
    add x11, x10, x3
    LOOP_TAIL x11

    .global c03_m001
c03_m001:
    LOOP_HEAD
c03_m001_producer:
    add x10, x1, x2
c03_m001_marker:
    add x12, x10, x3
    add x10, x4, x5
    eor x11, x10, x3
    LOOP_TAIL x11

    .global c04_m001
c04_m001:
    LOOP_HEAD
c04_m001_producer:
    add x10, x1, x2
c04_m001_marker:
    add x12, x10, x3
    eor x11, x10, x3
    add x12, x10, x4
    eor x13, x11, x12
    LOOP_TAIL x13

    .global c05_m001
c05_m001:
    stp x19, x20, [sp, #-16]!
    mov x20, x0
    mov x19, #8
2:
    add x1, x19, #30
    mov x2, #0
    add x3, x19, #30
    add x4, x19, #40
    add x5, x19, #50
c05_m001_producer:
    add x10, x1, x2
c05_m001_marker:
    add x12, x10, x3
    cmp x10, x3
    b.eq 3f
    eor x11, x10, x4
    b 4f
3:
    add x11, x10, x4
4:
    str x11, [x20], #8
    subs x19, x19, #1
    b.ne 2b
    ldp x19, x20, [sp], #16
    ret
