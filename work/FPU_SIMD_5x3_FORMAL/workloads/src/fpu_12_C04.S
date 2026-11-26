// 5x3 context workload FPU-M012 C04 (model 12, C04)
.text
.global _start
_start:
    msr fpsr, xzr
    msr fpcr, xzr
    adr x20, outbuf
    mov x21, #0
    mov x22, #100
loop_top:
    add x8, x20, x21, lsl #7
    add x9, x8, #40
    ldr x10, =0x3149554650465046
    str x10, [x8, #0]
    mov x10, #12
    str x10, [x8, #8]
    mov x10, #4
    str x10, [x8, #16]
    mov x10, #5
    str x10, [x8, #24]
    str x21, [x8, #32]
    adr x7, v0old_data
    ldr q0, [x7]
    adr x7, v1_data
    ldr q1, [x7]
fpu_target_r:
    xtn2 v0.16b, v1.8h
        add v2.16b, v0.16b, v0.16b
        add v3.16b, v2.16b, v0.16b
        str q3, [x9]
        str q2, [x8, #96]
    mrs x10, fpsr
    str x10, [x8, #56]
    ubfx x11, x10, #27, #1
    str x11, [x8, #104]
    mrs x10, fpcr
    str x10, [x8, #64]
    mrs x10, nzcv
    str x10, [x8, #72]
    mov x10, #-1
    str x10, [x8, #80]
    mov x10, #0
    str x10, [x8, #88]

    add x21, x21, #1
    cmp x21, x22
    b.ne loop_top
    mov x2, x22
    lsl x2, x2, #7
    adr x1, outbuf
write_exit:
    mov x0, #1
    mov x8, #64
    svc #0
    mov x0, #0
    mov x8, #93
    svc #0

.section .data
.align 4
v1_data: .byte 0x20, 0x12, 0x21, 0x12, 0x22, 0x12, 0x23, 0x12, 0x24, 0x12, 0x25, 0x12, 0x26, 0x12, 0x27, 0x12
v0old_data: .byte 1, 2, 3, 4, 5, 6, 7, 8, 255, 255, 255, 255, 255, 255, 255, 255
v0oldb_data: .byte 1, 2, 3, 4, 5, 6, 7, 8, 170, 170, 170, 170, 170, 170, 170, 170
.section .bss
.align 8
outbuf: .skip 16384
