    .text
    .global c01_m005_producer
    .global c01_m005_consumer
    .global c02_m005_producer
    .global c02_m005_consumer
    .global c03_m005_producer
    .global c03_m005_consumer
    .global c04_m005_producer
    .global c04_m005_consumer
    .global c05_m005_producer
    .global c05_m005_consumer

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
    mov x6, #0
    .endm
    .macro PAD
    .rept 24
    add x6, x6, #1
    .endr
    .endm
    .macro TAIL reg
    str \reg, [x20], #8
    subs x19, x19, #1
    b.ne 1b
    ldp x19, x20, [sp], #16
    ret
    .endm

    .global c01_m005
c01_m005:
    HEAD
c01_m005_producer:
    add x10, x1, x2
    PAD
c01_m005_consumer:
    eor x11, x10, x3
    TAIL x11

    .global c02_m005
c02_m005:
    HEAD
c02_m005_producer:
    add x10, x1, x2
    PAD
c02_m005_consumer:
    add x11, x3, x10
    TAIL x11

    .global c03_m005
c03_m005:
    HEAD
c03_m005_producer:
    add x10, x1, x2
    PAD
c03_m005_consumer:
    eor x11, x10, x3
    add x11, x4, x5
    TAIL x11

    .global c04_m005
c04_m005:
    HEAD
c04_m005_producer:
    add x10, x1, x2
    PAD
c04_m005_consumer:
    eor x11, x10, x3
    add x12, x10, x4
    eor x13, x11, x12
    TAIL x13

    .global c05_m005
c05_m005:
    HEAD
c05_m005_producer:
    add x10, x1, x2
    mov x4, x3
    cmp x3, x4
    b.ne 2f
    PAD
c05_m005_consumer:
    eor x11, x10, x3
    b 3f
2:
    add x11, x4, x5
3:
    TAIL x11
