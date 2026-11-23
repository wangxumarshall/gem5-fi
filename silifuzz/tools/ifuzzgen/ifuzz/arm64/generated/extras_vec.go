// Opt-in extension: valid encodings for the two vector classes whose upstream
// words are unallocated.
//
// The upstream table fixes imm5 to 0 for DUP (element) and MOV (to general),
// and imm5 == 0 is not a legal element index: objdump reports "undefined" and
// the CPU raises SIGILL.  A template that contains dup/umov therefore had no
// representable encoding after validation, which made full class coverage
// impossible.  The words below are assembler output for index 0 and index 3,
// read back with objdump.
package generated

import (
	. "silifuzz/tools/ifuzzgen/ifuzz/arm64"
)

var vecInsns = []*Insn{
	// dup v0.8b, v0.b[0]
	{Name: "DUP (element)", OpcodeMask: 0xff20fc00, Opcode: 0x0e000400, AsUInt32: 0x0e010400,
		Fields: []InsnField{{"imm5", 16, 5}, {"Rn", 5, 5}, {"Rd", 0, 5}}},
	// dup v0.16b, v0.b[0]
	{Name: "DUP (element)", OpcodeMask: 0xff20fc00, Opcode: 0x4e000400, AsUInt32: 0x4e010400,
		Fields: []InsnField{{"imm5", 16, 5}, {"Rn", 5, 5}, {"Rd", 0, 5}}},
	// umov w0, v0.b[0]
	{Name: "MOV (to general)", OpcodeMask: 0xff20fc00, Opcode: 0x0e003c00, AsUInt32: 0x0e013c00,
		Fields: []InsnField{{"imm5", 16, 5}, {"Rn", 5, 5}, {"Rd", 0, 5}}},
	// umov w0, v0.s[0]
	{Name: "MOV (to general)", OpcodeMask: 0xff20fc00, Opcode: 0x0e043c00, AsUInt32: 0x0e053c00,
		Fields: []InsnField{{"imm5", 16, 5}, {"Rn", 5, 5}, {"Rd", 0, 5}}},
}

// RegisterWithVec extends RegisterWith with the vector operand fixes.
func RegisterWithVec(lse, branches, vector bool) {
	out := append([]*Insn{}, insns_arm64...)
	if lse {
		out = append(out, lseInsns...)
	}
	if branches {
		out = append(out, branchInsns...)
	}
	if vector {
		out = append(out, vecInsns...)
	}
	Register(out)
}
