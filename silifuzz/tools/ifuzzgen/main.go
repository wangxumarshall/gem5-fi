// Command ifuzzgen generates random valid ARM64 instruction sequences using
// the syzkaller ifuzz arm64 instruction model (vendored under ./ifuzz).
//
// This is the ARM64 counterpart of the "ifuzz" generator used by SiliFuzz
// (paper section 2.4.2): generation-based, coverage-agnostic random valid
// instruction sequences.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"

	"silifuzz/tools/ifuzzgen/ifuzz/iset"

	_ "silifuzz/tools/ifuzzgen/ifuzz/arm64/generated"
)

type manifestEntry struct {
	Hash   string `json:"hash"`
	Seed   int64  `json:"seed"`
	Insns  int    `json:"insns"`
	Bytes  int    `json:"bytes"`
	Source string `json:"source"`
}

func generate(cfg *iset.Config, r *rand.Rand) []byte {
	avail := iset.Arches[cfg.Arch].GetInsns(cfg.Mode, iset.TypeUser)
	if len(avail) == 0 {
		panic("no arm64 instructions registered")
	}
	var text []byte
	for i := 0; i < cfg.Len; i++ {
		insn := avail[r.Intn(len(avail))]
		text = append(text, insn.Encode(cfg, r)...)
	}
	return text
}

func main() {
	n := flag.Int64("n", 1000, "number of instruction sequences to generate")
	seed := flag.Int64("seed", 1, "base RNG seed")
	minInsns := flag.Int("min-insns", 1, "minimum instructions per sequence")
	maxInsns := flag.Int("max-insns", 24, "maximum instructions per sequence")
	out := flag.String("out", "", "output directory (sharded by content hash)")
	manifestPath := flag.String("manifest", "", "optional JSONL manifest path")
	flag.Parse()
	if *out == "" {
		fmt.Fprintln(os.Stderr, "-out is required")
		os.Exit(2)
	}
	if *minInsns < 1 || *maxInsns < *minInsns {
		fmt.Fprintln(os.Stderr, "invalid instruction count range")
		os.Exit(2)
	}
	cfg := &iset.Config{Arch: iset.ArchArm64, Mode: iset.ModeLong64, Exec: true}

	var manifest *os.File
	var enc *json.Encoder
	if *manifestPath != "" {
		var err error
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
		text := generate(cfg, r)
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
				Bytes: len(text), Source: "ifuzz"}
			enc.Encode(entry)
		}
		written++
	}
	fmt.Printf("ifuzzgen: requested=%d written=%d unique=%d out=%s\n",
		*n, written, len(seen), *out)
}
