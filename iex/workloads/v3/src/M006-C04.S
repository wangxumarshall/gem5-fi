	.arch armv8-a
	.text
	.global _start
	.type _start,%function
_start:
	bl iex_run
	bl iex_print_mem
	.global iex_run
	.type iex_run,%function
iex_run:
	ldr x9, =0x0000000000000000
	ldr x10, =0x0000000000000000
	ldr x11, =0xA5A5A5A5A5A5A5A5
	ldr x12, =iex_output
	ldr x5, =0x00000000000000C1
	ldr x6, =0x0000000000000031
	mov x20, #128
.Lloop:
	.global iex_roi_start
iex_roi_start:
	ldr x9, =0x0000000000000000
	ldr x10, =0x0000000000000000
	ldr x5, =0x00000000000000C1
	ldr x6, =0x0000000000000031
	.global iex_target_pc
iex_target_pc:
	subs x2, x9, x10
	.global iex_consumer_pc
iex_consumer_pc:
	csel x0, x5, x6, eq
	eor x1, x0, x11
	add x2, x1, #17
	ror x3, x2, #7
	add x4, x3, x3, lsl #1
	str x4, [x12]
	eor x1, x4, x11
	str x1, [x12, #8]
	add x12, x12, #16
	.global iex_iter_pc
iex_iter_pc:
	sub x20, x20, #1
	cbnz x20, .Lloop
	.global iex_roi_end
iex_roi_end:
	ret
	.section .rodata
	.global iex_context
iex_context: .asciz "IEX-M006-C04"
	.ltorg
