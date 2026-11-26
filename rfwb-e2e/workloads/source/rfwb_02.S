    .text
    .global c01_m002_target
    .global c02_m002_target
    .global c03_m002_target
    .global c04_m002_target
    .global c05_m002_target

    .macro HEAD
    stp x19, x20, [sp, #-16]!
    mov x20, x0
    mov x19, #8
    mov w6, #0x11
    dup v1.16b, w6
    mov w6, #0x22
    dup v2.16b, w6
    mov w6, #0x44
    dup v3.16b, w6
    mov w6, #0x55
    dup v4.16b, w6
1:
    .endm
    .macro TAIL
    str q0, [x20], #16
    subs x19, x19, #1
    b.ne 1b
    ldp x19, x20, [sp], #16
    ret
    .endm

    .global c01_m002
c01_m002:
    HEAD
c01_m002_target:
    eor v0.16b, v1.16b, v2.16b
    TAIL

    .global c02_m002
c02_m002:
    HEAD
c02_m002_target:
    eor v0.16b, v1.16b, v2.16b
    TAIL

    .global c03_m002
c03_m002:
    HEAD
c03_m002_target:
    eor v0.16b, v1.16b, v2.16b
    eor v0.16b, v3.16b, v4.16b
    TAIL

    .global c04_m002
c04_m002:
    HEAD
c04_m002_target:
    eor v0.16b, v1.16b, v2.16b
    eor v3.16b, v0.16b, v4.16b
    addv b5, v3.16b
    TAIL

    .global c05_m002
c05_m002:
    HEAD
c05_m002_target:
    eor v0.16b, v1.16b, v2.16b
    cmeq v3.16b, v0.16b, v4.16b
    addv b5, v3.16b
    umov w6, v5.b[0]
    cbz w6, 2f
    str q0, [x20], #16
    b 3f
2:
    str q0, [x20], #16
3:
    subs x19, x19, #1
    b.ne 1b
    ldp x19, x20, [sp], #16
    ret
