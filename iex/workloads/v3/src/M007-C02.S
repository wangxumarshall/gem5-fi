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
	ldr x9, =0x0000000080000000
	ldr x10, =0x0000000000000000
	ldr x11, =0xA5A5A5A5A5A5A5A5
	ldr x12, =iex_output
	mov x20, #128
.Lloop:
	.global iex_roi_start
iex_roi_start:
	ldr x9, =0x0000000080000000
	ldr x10, =0x0000000000000000
	.global iex_target_pc
iex_target_pc:
	clz x0, x9
	eor x1, x0, x11
	str x0, [x12]
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
iex_context: .asciz "IEX-M007-C02"
	.ltorg
