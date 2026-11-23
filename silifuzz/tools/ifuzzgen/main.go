// Command ifuzzgen generates random valid ARM64 instruction sequences using
// the syzkaller ifuzz arm64 instruction model (vendored under ./ifuzz).
//
// This is the ARM64 counterpart of the "ifuzz" generator used by SiliFuzz
// (paper section 2.4.2): generation-based, coverage-agnostic random valid
// instruction sequences.
//
// Optional targeting filters (default: none, byte-identical to the unfiltered
// generator):
//
//	-allow REGEX   keep only instructions whose ifuzz name matches REGEX
//	-deny REGEX    drop instructions whose ifuzz name matches REGEX
//	-opcodes FILE  keep only opcodes listed in FILE (one 32-bit value per line)
//	-lse           append ARMv8.1 LSE atomic forms (opt-in; default path unchanged)
//	-branch-ext    append forward-displacement branch forms (opt-in)
//	-vec-ext       append valid DUP/UMOV encodings (opt-in)
//	-balance-classes  draw classes uniformly, then encodings within a class
//	-list          print the user-mode instruction table and exit
//
// The filters exist so an experiment can ask ifuzz for a stream aimed at a
// microarchitectural unit (ALU, multiplier, load/store, ...).  They do not
// change the ifuzz encoder or its fixed operand templates.
package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"

	"silifuzz/tools/ifuzzgen/ifuzz/arm64"
	"silifuzz/tools/ifuzzgen/ifuzz/iset"

	gen "silifuzz/tools/ifuzzgen/ifuzz/arm64/generated"
)

type manifestEntry struct {
	Hash      string `json:"hash"`
	Seed      int64  `json:"seed"`
	Insns     int    `json:"insns"`
	Bytes     int    `json:"bytes"`
	Source    string `json:"source"`
	Allow     string `json:"allow,omitempty"`
	Deny      string `json:"deny,omitempty"`
	Opcodes   string `json:"opcodes,omitempty"`
	LSE       bool   `json:"lse,omitempty"`
	BranchExt bool   `json:"branch_ext,omitempty"`
}

type filters struct {
	allow   *regexp.Regexp
	deny    *regexp.Regexp
	opcodes map[uint32]bool
}

func compileFilter(pattern string) (*regexp.Regexp, error) {
	if pattern == "" {
		return nil, nil
	}
	// Instruction names are upper case; make the common case painless while
	// still allowing an explicit (?-i) in the pattern.
	re, err := regexp.Compile("(?i)" + pattern)
	if err != nil {
		return nil, fmt.Errorf("invalid regexp %q: %w", pattern, err)
	}
	return re, nil
}

func loadOpcodes(path string) (map[uint32]bool, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	out := make(map[uint32]bool)
	scanner := bufio.NewScanner(f)
	line := 0
	for scanner.Scan() {
		line++
		text := strings.TrimSpace(scanner.Text())
		if i := strings.IndexByte(text, '#'); i >= 0 {
			text = strings.TrimSpace(text[:i])
		}
		if text == "" {
			continue
		}
		value, err := strconv.ParseUint(text, 0, 32)
		if err != nil {
			return nil, fmt.Errorf("%s:%d: bad opcode %q: %w", path, line, text, err)
		}
		out[uint32(value)] = true
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("%s: no opcodes", path)
	}
	return out, nil
}

func opcodeOf(insn iset.Insn) (uint32, bool) {
	concrete, ok := insn.(*arm64.Insn)
	if !ok || concrete.Pseudo {
		return 0, false
	}
	return concrete.AsUInt32, true
}

// selectInsns applies the optional filters to the user-mode instruction table.
// With no filters it returns the table unchanged, so the default generator's
// random draw sequence is preserved.
func selectInsns(all []iset.Insn, f filters) []iset.Insn {
	if f.allow == nil && f.deny == nil && f.opcodes == nil {
		return all
	}
	out := make([]iset.Insn, 0, len(all))
	for _, insn := range all {
		name, _, pseudo, _ := insn.Info()
		if pseudo {
			continue
		}
		if f.allow != nil && !f.allow.MatchString(name) {
			continue
		}
		if f.deny != nil && f.deny.MatchString(name) {
			continue
		}
		if f.opcodes != nil {
			op, ok := opcodeOf(insn)
			if !ok || !f.opcodes[op] {
				continue
			}
		}
		out = append(out, insn)
	}
	return out
}

func listInsns(all []iset.Insn) {
	for _, insn := range all {
		name, _, pseudo, priv := insn.Info()
		op, ok := opcodeOf(insn)
		if !ok {
			fmt.Printf("%s\t-\t%t\t%t\n", name, pseudo, priv)
			continue
		}
		fmt.Printf("%s\t0x%08x\t%t\t%t\n", name, op, pseudo, priv)
	}
}

func generate(cfg *iset.Config, r *rand.Rand, avail []iset.Insn, groups [][]iset.Insn) []byte {
	if len(avail) == 0 {
		panic("no arm64 instructions available after filtering")
	}
	var text []byte
	for i := 0; i < cfg.Len; i++ {
		var insn iset.Insn
		if groups != nil {
			g := groups[r.Intn(len(groups))]
			insn = g[r.Intn(len(g))]
		} else {
			insn = avail[r.Intn(len(avail))]
		}
		text = append(text, insn.Encode(cfg, r)...)
	}
	return text
}

// groupByClass buckets instructions by their ifuzz class name.
func groupByClass(avail []iset.Insn) [][]iset.Insn {
	index := map[string]int{}
	var groups [][]iset.Insn
	for _, insn := range avail {
		name, _, _, _ := insn.Info()
		i, ok := index[name]
		if !ok {
			i = len(groups)
			index[name] = i
			groups = append(groups, nil)
		}
		groups[i] = append(groups[i], insn)
	}
	return groups
}

func main() {
	n := flag.Int64("n", 1000, "number of instruction sequences to generate")
	seed := flag.Int64("seed", 1, "base RNG seed")
	minInsns := flag.Int("min-insns", 1, "minimum instructions per sequence")
	maxInsns := flag.Int("max-insns", 24, "maximum instructions per sequence")
	out := flag.String("out", "", "output directory (sharded by content hash)")
	manifestPath := flag.String("manifest", "", "optional JSONL manifest path")
	allowPattern := flag.String("allow", "", "keep only instruction names matching this regexp")
	denyPattern := flag.String("deny", "", "drop instruction names matching this regexp")
	opcodePath := flag.String("opcodes", "", "keep only opcodes listed in this file")
	list := flag.Bool("list", false, "print the user-mode instruction table and exit")
	useLSE := flag.Bool("lse", false, "append the ARMv8.1 LSE atomic forms absent from the upstream table")
	useBranch := flag.Bool("branch-ext", false, "append branch forms with a non-zero forward displacement")
	varyRegs := flag.Int("vary-regs", 0, "clone each selectable instruction N times with randomized register fields")
	useVec := flag.Bool("vec-ext", false, "append valid DUP/UMOV encodings that the upstream table leaves unallocated")
	balance := flag.Bool("balance-classes", false, "draw instruction classes uniformly instead of table entries")
	wordsPath := flag.String("words", "", "generate from an explicit word list (hex word + class name per line)")
	classifyPath := flag.String("classify", "", "classify 32-bit instruction words from FILE (raw binary or hex lines) and exit")
	tableJSON := flag.String("table-json", "", "write the active instruction table (name, mask, opcode) as JSON and exit")
	flag.Parse()

	if *useLSE || *useBranch || *useVec {
		gen.RegisterWithVec(*useLSE, *useBranch, *useVec)
	}
	cfg := &iset.Config{Arch: iset.ArchArm64, Mode: iset.ModeLong64, Exec: true}
	all := iset.Arches[cfg.Arch].GetInsns(cfg.Mode, iset.TypeUser)
	if len(all) == 0 {
		fmt.Fprintln(os.Stderr, "no arm64 instructions registered")
		os.Exit(1)
	}
	if *list {
		listInsns(all)
		return
	}
	if *classifyPath != "" {
		Classify(*classifyPath)
		return
	}
	if *tableJSON != "" {
		DumpTable(*tableJSON, all)
		return
	}

	allow, err := compileFilter(*allowPattern)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	deny, err := compileFilter(*denyPattern)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	var opcodes map[uint32]bool
	if *opcodePath != "" {
		opcodes, err = loadOpcodes(*opcodePath)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
	}
	f := filters{allow: allow, deny: deny, opcodes: opcodes}
	avail := selectInsns(all, f)
	if *wordsPath != "" {
		avail, err = loadWords(*wordsPath)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
	}
	if *varyRegs > 0 {
		avail = expandRegs(avail, *varyRegs, rand.New(rand.NewSource(*seed)))
	}
	if len(avail) == 0 {
		fmt.Fprintln(os.Stderr, "filters removed every instruction")
		os.Exit(2)
	}

	if *out == "" {
		fmt.Fprintln(os.Stderr, "-out is required")
		os.Exit(2)
	}
	if *minInsns < 1 || *maxInsns < *minInsns {
		fmt.Fprintln(os.Stderr, "invalid instruction count range")
		os.Exit(2)
	}
	if err := os.MkdirAll(*out, 0o755); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	var manifest *os.File
	var enc *json.Encoder
	if *manifestPath != "" {
		manifest, err = os.Create(*manifestPath)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer manifest.Close()
		enc = json.NewEncoder(manifest)
	}
	seen := make(map[[32]byte]bool, *n)
	written := int64(0)
	for i := int64(0); i < *n; i++ {
		r := rand.New(rand.NewSource(*seed*1000003 + i))
		cfg.Len = *minInsns + r.Intn(*maxInsns-*minInsns+1)
		var groups [][]iset.Insn
		if *balance {
			groups = groupByClass(avail)
		}
		text := generate(cfg, r, avail, groups)
		if len(text) == 0 {
			continue
		}
		var h [32]byte
		h = sha256.Sum256(text)
		if seen[h] {
			continue
		}
		seen[h] = true
		hexh := hex.EncodeToString(h[:])
		dir := filepath.Join(*out, hexh[:2])
		if err := os.MkdirAll(dir, 0o755); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := os.WriteFile(filepath.Join(dir, hexh+".bin"), text, 0o644); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if manifest != nil {
			entry := manifestEntry{Hash: hexh, Seed: *seed*1000003 + i, Insns: cfg.Len,
				Bytes: len(text), Source: "ifuzz", Allow: *allowPattern, LSE: *useLSE, BranchExt: *useBranch,
				Deny: *denyPattern, Opcodes: *opcodePath}
			enc.Encode(entry)
		}
		written++
	}
	fmt.Printf("ifuzzgen: requested=%d written=%d unique=%d out=%s\n",
		*n, written, len(seen), *out)
}

// Classify maps instruction words to the canonical ifuzz table names, which is
// the vocabulary the pair audit uses.  Using ifuzz's own decoder keeps the
// comparison free of objdump aliases (MOV vs MOVZ, CMP vs SUBS, ...).
//
// Input is either a raw little-endian word stream or a text file with one hex
// word per line (comments starting with # are ignored).
func Classify(path string) {
	raw, err := os.ReadFile(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	var words []uint32
	textual := true
	for _, b := range raw {
		if b == 0 || b == '\n' || b == '\r' || b == '\t' || b == ' ' || b == '#' ||
			(b >= '0' && b <= '9') || (b >= 'a' && b <= 'f') || (b >= 'A' && b <= 'F') ||
			b == 'x' || b == 'X' {
			continue
		}
		textual = false
		break
	}
	if textual && len(raw) > 0 {
		for _, line := range strings.Split(string(raw), "\n") {
			if i := strings.IndexByte(line, '#'); i >= 0 {
				line = line[:i]
			}
			line = strings.TrimSpace(line)
			if line == "" {
				continue
			}
			line = strings.TrimPrefix(strings.TrimPrefix(line, "0x"), "0X")
			v, err := strconv.ParseUint(line, 16, 32)
			if err != nil {
				fmt.Fprintf(os.Stderr, "%s: bad word %q\n", path, line)
				os.Exit(2)
			}
			words = append(words, uint32(v))
		}
	} else {
		if len(raw)%4 != 0 {
			fmt.Fprintf(os.Stderr, "%s: %d bytes is not a multiple of 4\n", path, len(raw))
			os.Exit(2)
		}
		for i := 0; i+4 <= len(raw); i += 4 {
			words = append(words, uint32(raw[i])|uint32(raw[i+1])<<8|uint32(raw[i+2])<<16|uint32(raw[i+3])<<24)
		}
	}
	for _, w := range words {
		insn, err := arm64.ParseInsn(w)
		name := insn.Name
		if err != nil {
			name = "unknown"
		}
		fmt.Printf("%08x\t%s\n", w, name)
	}
}

type tableField struct {
	Name  string `json:"name"`
	Start uint   `json:"start"`
	Len   uint   `json:"len"`
}

type tableEntry struct {
	Name     string       `json:"name"`
	Mask     uint32       `json:"mask"`
	Opcode   uint32       `json:"opcode"`
	AsUInt32 uint32       `json:"as_uint32"`
	Fields   []tableField `json:"fields,omitempty"`
	Pseudo   bool         `json:"pseudo"`
	Priv     bool         `json:"priv"`
}

// DumpTable exports the exact table ParseInsn walks, in walk order, so external
// tooling can reproduce classification without spawning a decoder per word.
func DumpTable(path string, all []iset.Insn) {
	entries := make([]tableEntry, 0, len(all))
	for _, insn := range all {
		c, ok := insn.(*arm64.Insn)
		if !ok {
			continue
		}
		fields := make([]tableField, 0, len(c.Fields))
		for _, f := range c.Fields {
			fields = append(fields, tableField{Name: f.Name, Start: f.Start, Len: f.Length})
		}
		entries = append(entries, tableEntry{
			Name: c.Name, Mask: c.OpcodeMask, Opcode: c.Opcode,
			AsUInt32: c.AsUInt32, Fields: fields, Pseudo: c.Pseudo, Priv: c.Priv,
		})
	}
	b, err := json.MarshalIndent(entries, "", " ")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.WriteFile(path, append(b, '\n'), 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("table entries: %d\n", len(entries))
}

// Registers 18..25 hold the data-base pointer and are never written: Rn draws
// from them, every other register field draws from the remaining GPRs.  This
// mirrors the sdcfuzz convention (x6/x7 as data ranges) closely enough for a
// paired experiment while keeping the snapshot's memory operands mapped.
var baseRegs = []uint{18, 19, 20, 21, 22, 23, 24, 25}

var dataRegs = []uint{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 26, 27, 28}

func isRegField(name string) bool {
	switch name {
	case "Rn", "Rd", "Rm", "Rt", "Rt2", "Ra", "Rs":
		return true
	}
	return false
}

func expandRegs(src []iset.Insn, clones int, r *rand.Rand) []iset.Insn {
	out := make([]iset.Insn, 0, len(src)*(clones+1))
	for _, insn := range src {
		concrete, ok := insn.(*arm64.Insn)
		if !ok || concrete.Pseudo || len(concrete.Fields) == 0 {
			out = append(out, insn)
			continue
		}
		kept := 0
		for i := 0; i < clones; i++ {
			c := *concrete
			w := c.AsUInt32
			chosen := map[string]uint{}
			for _, f := range c.Fields {
				if !isRegField(f.Name) {
					continue
				}
				pool := dataRegs
				if f.Name == "Rn" {
					pool = baseRegs
				}
				var reg uint
				for tries := 0; tries < 8; tries++ {
					reg = pool[r.Intn(len(pool))]
					// LDP/STP with Rt == Rt2 is constrained unpredictable.
					if f.Name == "Rt2" && reg == chosen["Rt"] {
						continue
					}
					break
				}
				chosen[f.Name] = reg
				mask := uint32(((1 << f.Length) - 1) << f.Start)
				w = (w &^ mask) | (uint32(reg) << f.Start)
			}
			// A variant only counts if it still decodes to the same class: a
			// field table that does not cover every register bit would
			// otherwise produce words the hardware rejects.
			if w == c.AsUInt32 || w&c.OpcodeMask != c.Opcode {
				continue
			}
			c.AsUInt32 = w
			out = append(out, &c)
			kept++
		}
		if kept == 0 {
			// Encodings without a usable field table cannot be varied; repeat
			// them so every allowed encoding keeps the same sampling weight.
			for i := 0; i < clones; i++ {
				out = append(out, insn)
			}
		}
	}
	return out
}

// loadWords reads "<hex word>\t<class name>" lines and turns them into the
// instruction set for this run.  The masks are exact, so classification of the
// produced bytes is the caller's job (it already holds the real table).
func loadWords(path string) ([]iset.Insn, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []iset.Insn
	scanner := bufio.NewScanner(f)
	line := 0
	for scanner.Scan() {
		line++
		text := strings.TrimSpace(scanner.Text())
		if text == "" || strings.HasPrefix(text, "#") {
			continue
		}
		fields := strings.Fields(text)
		if len(fields) < 2 {
			return nil, fmt.Errorf("%s:%d: expected \"<word> <class>\"", path, line)
		}
		v, err := strconv.ParseUint(strings.TrimPrefix(strings.TrimPrefix(fields[0], "0x"), "0X"), 16, 32)
		if err != nil {
			return nil, fmt.Errorf("%s:%d: bad word %q: %w", path, line, fields[0], err)
		}
		name := strings.Join(fields[1:], " ")
		word := uint32(v)
		out = append(out, &arm64.Insn{Name: name, OpcodeMask: 0xffffffff, Opcode: word, AsUInt32: word})
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("%s: no words", path)
	}
	return out, nil
}
