# SE address semantics (v3.2.5 correction)

Syscall Emulation (SE) has no MMU and no page table. The address the CPU
presents to the memory system is the architectural virtual address; there is
no separately translated physical address. The two coincide only because SE
performs no translation.

Trace field semantics:

- `va` — the `Request::getVaddr()` architectural address (mem_req, inj,
  store-side nodes).
- `pa` — the memory-side address seen by the cache; for `Packet::getAddr()`
  this is block-aligned. It is **not** an FS physical address.
- A store's fault entry is registered by `Request` VA; `mem_req` matching
  therefore compares architectural addresses. Two different VAs that alias
  the same memory location are not recognised as the same byte by this
  matcher (recorded as an open question in
  `LSU_v3.2.5_DA04_Trace_Fix_Evidence.md`).

The earlier “SE vaddr==paddr assumption” wording overstated the model: SE
does not translate, so there is no PA to equal. The comment is corrected in
`CHAOSPropagation.hh` and `CHAOSPropagation.cc`.
