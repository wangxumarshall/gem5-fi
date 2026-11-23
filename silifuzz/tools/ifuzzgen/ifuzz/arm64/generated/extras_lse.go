// Opt-in extension: ARMv8.1 LSE atomic forms missing from the syzkaller
// ifuzz arm64 user-mode table (upstream registers no CAS/SWP/LDADD entries).
//
// Every word below was produced by the system assembler from real assembly and
// read back with objdump, so the encodings are authoritative rather than
// transcribed.  The forms are *not* part of the default table: main.go appends
// them only under -lse, therefore the unfiltered generator stays byte-identical
// and previously published corpora remain reproducible.
package generated

import (
	. "silifuzz/tools/ifuzzgen/ifuzz/arm64"
)

// lseInsns holds one concrete encoding per (mnemonic, operand shape) form.
// Names use the objdump mnemonic in upper case so that the -allow/-opcodes
// filters and the pair-audit tooling see the same vocabulary as disassembly.
var lseInsns = []*Insn{
	{Name: "LDADD", OpcodeMask: 0xffe0fc00, Opcode: 0xf8200000, AsUInt32: 0xf82000c3},
	{Name: "LDADD", OpcodeMask: 0xffe0fc00, Opcode: 0xf8200000, AsUInt32: 0xf82100c9},
	{Name: "LDADD", OpcodeMask: 0xffe0fc00, Opcode: 0xf8200000, AsUInt32: 0xf82200eb},
	{Name: "LDADDA", OpcodeMask: 0xffe0fc00, Opcode: 0xf8a00000, AsUInt32: 0xf8a000c4},
	{Name: "LDADDL", OpcodeMask: 0xffe0fc00, Opcode: 0xf8600000, AsUInt32: 0xf86000c5},
	{Name: "LDADDAL", OpcodeMask: 0xffe0fc00, Opcode: 0xf8e00000, AsUInt32: 0xf8e000c6},
	{Name: "CAS", OpcodeMask: 0xffe0fc00, Opcode: 0xc8a07c00, AsUInt32: 0xc8a17cc2},
	{Name: "CASA", OpcodeMask: 0xffe0fc00, Opcode: 0xc8e07c00, AsUInt32: 0xc8e17cc2},
	{Name: "CASL", OpcodeMask: 0xffe0fc00, Opcode: 0xc8a0fc00, AsUInt32: 0xc8a1fcc2},
	{Name: "CASAL", OpcodeMask: 0xffe0fc00, Opcode: 0xc8e0fc00, AsUInt32: 0xc8e1fcc2},
	{Name: "SWP", OpcodeMask: 0xffe0fc00, Opcode: 0xf8208000, AsUInt32: 0xf82080c8},
	{Name: "SWPA", OpcodeMask: 0xffe0fc00, Opcode: 0xf8a08000, AsUInt32: 0xf8a080c7},
	{Name: "SWPL", OpcodeMask: 0xffe0fc00, Opcode: 0xf8608000, AsUInt32: 0xf86080c7},
	{Name: "SWPAL", OpcodeMask: 0xffe0fc00, Opcode: 0xf8e08000, AsUInt32: 0xf8e080c7},
	{Name: "LDCLR", OpcodeMask: 0xffe0fc00, Opcode: 0xf8201000, AsUInt32: 0xf82010c3},
	{Name: "LDSET", OpcodeMask: 0xffe0fc00, Opcode: 0xf8203000, AsUInt32: 0xf82030c3},
	{Name: "LDEOR", OpcodeMask: 0xffe0fc00, Opcode: 0xf8202000, AsUInt32: 0xf82020c3},
}

// RegisterLSE re-registers the ARM64 instruction set with the LSE forms
// appended.  Call it only when the caller explicitly asked for LSE.
func RegisterLSE() {
	Register(append(append([]*Insn{}, insns_arm64...), lseInsns...))
}

// LSEInsns exposes the opt-in forms for tooling that needs to enumerate them.
func LSEInsns() []*Insn { return lseInsns }
