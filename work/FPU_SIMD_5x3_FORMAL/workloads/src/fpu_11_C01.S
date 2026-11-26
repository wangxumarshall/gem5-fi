// 5x3 context workload FPU-M011 C01 (model 11, C01)
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
    mov x10, #11
    str x10, [x8, #8]
    mov x10, #1
    str x10, [x8, #16]
    mov x10, #5
    str x10, [x8, #24]
    str x21, [x8, #32]
    adr x7, v1_data
    ldr q1, [x7]
    adr x7, v2_data
    ldr q2, [x7]
fpu_target_r:
    tbl v0.16b, {v1.16b}, v2.16b
        str q0, [x9]
    mrs x10, fpsr
    str x10, [x8, #56]
    ubfx x11, x10, #27, #1
    str x11, [x8, #104]
    mrs x10, fpcr
    str x10, [x8, #64]
    mrs x10, nzcv
    str x10, [x8, #72]
    mov x10, #7
    str x10, [x8, #80]
    mov x10, #0
    str x10, [x8, #88]
    str xzr, [x8, #96]

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
v1_data: .byte 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175
v2_data: .byte 0, 1, 2, 3, 4, 5, 6, 32, 8, 9, 10, 11, 12, 13, 14, 15
v1b_data: .byte 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175
v2b_data: .byte 16, 17, 18, 19, 20, 21, 22, 32, 24, 25, 26, 27, 28, 29, 30, 31
.section .bss
.align 8
outbuf: .skip 16384
