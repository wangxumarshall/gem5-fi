# LSU 源码证据 v3（HEAD 6f98088a）

以下代码片段逐行从当前服务器源码读取；行号为当前 HEAD 行号；未修改源码。

## A01

### `cpu/o3/lsq.cc` 行 764-800

```cpp
764: LSQ::pushRequest(const DynInstPtr& inst, bool isLoad, uint8_t *data,
765:         unsigned int size, Addr addr, Request::Flags flags, uint64_t *res,
766:         AtomicOpFunctorPtr amo_op, const std::vector<bool>& byte_enable)
767: {
768:     // This comming request can be either load, store or atomic.
769:     // Atomic request has a corresponding pointer to its atomic memory
770:     // operation
771:     [[maybe_unused]] bool isAtomic = !isLoad && amo_op;
772: 
773:     // LSU W4 A-series PRE hook (W1 ⑦ ruling): pushRequest entry = the AGU's
774:     // raw output, the single mandatory pass-through point BEFORE split
775:     // decision and Request construction. Mutates the by-value addr/size
776:     // copies so every downstream consumer sees the fault. byte_enable is a
777:     // const ref here — BE mutation is NOT offered at this hook (A06 does
778:     // size only; documented in 09 §3-W4).
779:     if (cpu->chaosAddrPathPre) {
780:         const Addr pre_old_addr = addr;
781:         const unsigned int pre_old_size = size;
782:         size = cpu->chaosAddrPathPre->maybeCorruptPre(addr, size, isLoad,
783:                                                       flags);
784:         // [LSU][OBS-L3] register the PRE-family injection with the L3
785:         // propagation tracer (inj + addr_form nodes + addr registry).
786:         // lastPreHookInjected() also covers the flag-only modes (S06/L02
787:         // leave addr/size untouched — a before/after compare here would
788:         // miss them); their chain honestly stops at addr_form (no faulted
789:         // address to track). nullptr tracer / no injection = no-op.
790:         if (cpu->chaosPropagation &&
791:             cpu->chaosAddrPathPre->lastPreHookInjected()) {
792:             cpu->chaosPropagation->registerInjection(
793:                 "lsq_pushRequest_PRE", inst->seqNum, pre_old_addr, addr,
794:                 isLoad, pre_old_size, size);
795:         }
796:     }
797: 
798:     ThreadID tid = cpu->contextToThread(inst->contextId());
799:     auto cacheLineSize = cpu->cacheLineSize();
800:     bool needs_burst = transferNeedsBurst(addr, size, cacheLineSize);
```

### `cpu/o3/lsq.cc` 行 1166-1199

```cpp
1166: void
1167: LSQ::LSQRequest::sendFragmentToTranslation(int i)
1168: {
1169:     numInTranslationFragments++;
1170:     // §2.4 CHAOSAddrPath: corrupt the request vaddr BEFORE translateTiming
1171:     // (AGU address-path fault). HONEST: SE-inert (byte7 zero lands in SE
1172:     // 512MiB range, no fault); FS-only effective. nullptr = no injection.
1173:     if (_inst && _inst->cpu && _inst->cpu->chaosAddrPath) {
1174:         RequestPtr r = req(i);
1175:         const Addr post_old_vaddr = r->getVaddr();
1176:         if (_inst->cpu->chaosAddrPath->maybeCorrupt(r)) {
1177:             // [LSU][OBS-L3] post-hook family: register the injection (inj +
1178:             // addr_form nodes + addr registry; the request size is known
1179:             // here, so both sizes carry it — the corruption is address-only
1180:             // on this hook).
1181:             if (_inst->cpu->chaosPropagation)
1182:                 _inst->cpu->chaosPropagation->registerInjection(
1183:                     "lsq_sendFragmentToTranslation", _inst->seqNum,
1184:                     post_old_vaddr, r->getVaddr(), isLoad(),
1185:                     r->getSize(), r->getSize());
1186:         }
1187:     }
1188:     // [LSU][OBS-L3] mem_req node: this fragment's Request is about to leave
1189:     // for translation/memory — if its vaddr matches the addr registry
1190:     // (PRE family registered at pushRequest; post family just registered
1191:     // above) or its range covers a registered faulted cache byte, record
1192:     // the request node. Placed AFTER the corruption block so both families
1193:     // are covered by one call. nullptr tracer = no-op.
1194:     if (_inst && _inst->cpu && _inst->cpu->chaosPropagation)
1195:         _inst->cpu->chaosPropagation->noteMemRequest(
1196:             "lsq_sendFragmentToTranslation", _inst->seqNum, req(i));
1197:     _port.getMMUPtr()->translateTiming(req(i), _inst->thread->getTC(),
1198:             this, isLoad() ? BaseMMU::Read : BaseMMU::Write);
1199: }
```

### `cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc` 行 139-166

```cpp
139:         } else if (fi_mode == Mode::A01Bit) {
140:             // A01 (03): single-bit flip, low/mid/high band sampling
141:             // (VA is 48-bit in SE: low 0-15 / mid 16-39 / high 40-47).
142:             const uint64_t band = rng() % 3;
143:             const uint64_t bit = (band == 0) ? rng() % 16
144:                                : (band == 1) ? 16 + rng() % 24
145:                                : 40 + rng() % 8;
146:             new_vaddr = vaddr ^ (1ULL << bit);
147:         } else if (fi_mode == Mode::A02DoubleBit) {
148:             // A02 (03): two bits in the SAME event, 50% adjacent / 50%
149:             // non-adjacent (covers both MBU and dispersed error spaces).
150:             if (rng() % 2) {
151:                 const uint64_t b = rng() % 46;
152:                 new_vaddr = vaddr ^ ((1ULL << b) | (1ULL << (b + 1)));
153:             } else {
154:                 uint64_t b1 = rng() % 48, b2 = rng() % 48;
155:                 if (b1 == b2) b2 = (b2 + 1) % 48;
156:                 new_vaddr = vaddr ^ ((1ULL << b1) | (1ULL << b2));
157:             }
158:         } else if (fi_mode == Mode::A03Stuck0 || fi_mode == Mode::A03Stuck1) {
159:             // A03 (03): one EA bit stuck-at-0/1, applied on EVERY event from
160:             // warm-up on (F5 semantics). A correct value already equal to
161:             // the stuck value is a NO-OP application — logged distinctly so
162:             // L5 can subtract it from injected (A03's activated 口径).
163:             if (f5_bit == 64) f5_bit = rng() % 48;
164:             const Addr mask = 1ULL << f5_bit;
165:             new_vaddr = (fi_mode == Mode::A03Stuck0) ? (vaddr & ~mask)
166:                                                      : (vaddr | mask);
```

### `arch/arm/isa/insts/ldr64.isa` 行 111-145

```cpp
111:         def buildEACode(self):
112:             # Address computation code
113:             eaCode = ""
114:             if self.flavor == "fp":
115:                 eaCode += vfp64EnabledCheckCode
116: 
117:             if self.literal:
118:                 eaCode += "EA = RawPC"
119:             else:
120:                 eaCode += SPAlignmentCheckCode + "EA = XBase"
121: 
122:             if self.size == 16:
123:                 if self.top:
124:                     eaCode += " + (isBigEndian64(xc->tcBase()) ? 0 : 8)"
125:                 else:
126:                     eaCode += " + (isBigEndian64(xc->tcBase()) ? 8 : 0)"
127: 
128:             if self.flavor in ("authDA", "authDB"):
129:                 eaCode += ";\n"
130:                 eaCode += "fault = %s(xc->tcBase(), "\
131:                           "EA, 0, &EA);\n" % self.flavor
132:                 if self.writeback:
133:                     eaCode += "XBase = EA;\n"
134:                 eaCode += "EA = EA"
135: 
136:             if not self.post:
137:                 eaCode += self.offset
138:             eaCode += ";"
139: 
140:             if self.user:
141:                 eaCode += " uint8_t userFlag = 0;\n"\
142:                           "  if(isUnpriviledgeAccess(xc->tcBase()))\n"\
143:                           "     userFlag = ArmISA::MMU::UserMode;"
144: 
145:             self.codeBlobs["ea_code"] = eaCode
```

**可实现性结论**：唯一正式Hook=pushRequest；sendFragmentToTranslation是split后逐fragment，不是AGU输出，不选；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## A03

### `cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc` 行 158-166

```cpp
158:         } else if (fi_mode == Mode::A03Stuck0 || fi_mode == Mode::A03Stuck1) {
159:             // A03 (03): one EA bit stuck-at-0/1, applied on EVERY event from
160:             // warm-up on (F5 semantics). A correct value already equal to
161:             // the stuck value is a NO-OP application — logged distinctly so
162:             // L5 can subtract it from injected (A03's activated 口径).
163:             if (f5_bit == 64) f5_bit = rng() % 48;
164:             const Addr mask = 1ULL << f5_bit;
165:             new_vaddr = (fi_mode == Mode::A03Stuck0) ? (vaddr & ~mask)
166:                                                      : (vaddr | mask);
```

### `cpu/o3/chaos_lsu_trigger.hh` 行 150-175

```cpp
150:     onEligible()
151:     {
152:         ++eligible;
153:         if (!first_eligible_tick) first_eligible_tick = curTick();
154:         last_eligible_tick = curTick();   // [LSU][OBS-3]
155:         switch (tier) {
156:           case ChaOSLsuTier::F5: {
157:               if (!armed && eligible > warmup_events) armed = true;
158:               if (!armed) return false;
159:               ++injected;                 // every eligible event from warm-up on
160:               return true;
161:           }
162:           case ChaOSLsuTier::F0: {
163:               if (spent) return false;
164:               if (!armed) {
165:                   armed = true;
166:                   const uint64_t span = span_events ? span_events : 1;
167:                   rng = chaosSampleLCG(rng);
168:                   next_fire = warmup_events + rng % span;
169:               }
170:               if (eligible >= next_fire) { spent = true; ++injected; return true; }
171:               return false;
172:           }
173:           case ChaOSLsuTier::F1:
174:           case ChaOSLsuTier::F2:
175:           case ChaOSLsuTier::F3: {
```

**可实现性结论**：一个SampleRun一个固定故障源；R01-R05同一bit/value；不得描述为物理寄存器永久锁存；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## LQ04

### `cpu/o3/lsq_unit.hh` 行 95-147

```cpp
95:     class LSQEntry
96:     {
97:       private:
98:         /** The instruction. */
99:         DynInstPtr _inst;
100:         /** The request. */
101:         LSQRequest* _request = nullptr;
102:         /** The size of the operation. */
103:         uint32_t _size = 0;
104:         /** Valid entry. */
105:         bool _valid = false;
106: 
107:       public:
108:         ~LSQEntry()
109:         {
110:             if (_request != nullptr) {
111:                 _request->freeLSQEntry();
112:                 _request = nullptr;
113:             }
114:         }
115: 
116:         void
117:         clear()
118:         {
119:             _inst = nullptr;
120:             if (_request != nullptr) {
121:                 _request->freeLSQEntry();
122:             }
123:             _request = nullptr;
124:             _valid = false;
125:             _size = 0;
126:         }
127: 
128:         void
129:         set(const DynInstPtr& new_inst)
130:         {
131:             assert(!_valid);
132:             _inst = new_inst;
133:             _valid = true;
134:             _size = 0;
135:         }
136: 
137:         LSQRequest* request() { return _request; }
138:         void setRequest(LSQRequest* r) { _request = r; }
139:         bool hasRequest() { return _request != nullptr; }
140:         /** Member accessors. */
141:         /** @{ */
142:         bool valid() const { return _valid; }
143:         uint32_t& size() { return _size; }
144:         const uint32_t& size() const { return _size; }
145:         const DynInstPtr& instruction() const { return _inst; }
146:         /** @} */
147:     };
```

### `cpu/o3/lsq_unit.cc` 行 353-380

```cpp
353: void
354: LSQUnit::insertLoad(const DynInstPtr &load_inst)
355: {
356:     assert(!loadQueue.full());
357:     assert(loadQueue.size() < loadQueue.capacity());
358:     ++stats.addedLoadsAndStores;
359: 
360:     DPRINTF(LSQUnit, "Inserting load PC %s, idx:%i [sn:%lli]\n",
361:             load_inst->pcState(), loadQueue.tail(), load_inst->seqNum);
362: 
363:     /* Grow the queue. */
364:     loadQueue.advance_tail();
365: 
366:     load_inst->sqIt = storeQueue.end();
367: 
368:     assert(!loadQueue.back().valid());
369:     loadQueue.back().set(load_inst);
370:     load_inst->lqIdx = loadQueue.tail();
371:     assert(load_inst->lqIdx > 0);
372:     load_inst->lqIt = loadQueue.getIterator(load_inst->lqIdx);
373: 
374:     stats.lqAvgOccupancy = queueOccupancy(loadQueue);
375: 
376:     // hardware transactional memory
377:     // transactional state and nesting depth must be tracked
378:     // in the in-order part of the core.
379:     if (load_inst->isHtmStart()) {
380:         htmStarts++;
```

### `cpu/o3/lsq_unit.cc` 行 775-798

```cpp
775: void
776: LSQUnit::commitLoad()
777: {
778:     assert(loadQueue.front().valid());
779: 
780:     DynInstPtr inst = loadQueue.front().instruction();
781: 
782:     DPRINTF(LSQUnit, "Committing head load instruction, PC %s\n",
783:             inst->pcState());
784: 
785:     // Update histogram with memory latency from load
786:     // Only take latency from load demand that where issued and did not fault
787:     if (!inst->isInstPrefetch() && !inst->isDataPrefetch()
788:             && inst->firstIssue != -1
789:             && inst->lastWakeDependents != -1) {
790:         stats.loadToUse.sample(cpu->ticksToCycles(
791:                     inst->lastWakeDependents - inst->firstIssue));
792:     }
793: 
794:     loadQueue.front().clear();
795:     loadQueue.pop_front();
796: 
797:     stats.lqAvgOccupancy = queueOccupancy(loadQueue);
798: }
```

### `cpu/o3/lsq_unit.cc` 行 986-1000

```cpp
986:     while (loadQueue.size() != 0 &&
987:             loadQueue.back().instruction()->seqNum > squashed_num) {
988:         DPRINTF(LSQUnit,"Load Instruction PC %s squashed, "
989:                 "[sn:%lli]\n",
990:                 loadQueue.back().instruction()->pcState(),
991:                 loadQueue.back().instruction()->seqNum);
992: 
993:         if (isStalled() && loadQueue.tail() == stallingLoadIdx) {
994:             stalled = false;
995:             stallingStoreIsn = 0;
996:             stallingLoadIdx = 0;
997:         }
998: 
999:         // hardware transactional memory
1000:         // Squashing instructions can alter the transaction nesting depth
```

**可实现性结论**：原'提前free+重用'子模型在gem5无安全pop任意entry接口；先做提前失效，重用子模型BLOCKED；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## SQ01

### `cpu/o3/lsq_unit.hh` 行 149-196

```cpp
149:     class SQEntry : public LSQEntry
150:     {
151:       private:
152:         /** The store data. */
153:         char _data[MaxDataBytes];
154:         /** Whether or not the store can writeback. */
155:         bool _canWB = false;
156:         /** Whether or not the store is committed. */
157:         bool _committed = false;
158:         /** Whether or not the store is completed. */
159:         bool _completed = false;
160:         /** Does this request write all zeros and thus doesn't
161:          * have any data attached to it. Used for cache block zero
162:          * style instructs (ARM DC ZVA; ALPHA WH64)
163:          */
164:         bool _isAllZeros = false;
165: 
166:       public:
167:         static constexpr size_t DataSize = sizeof(_data);
168:         /** Constructs an empty store queue entry. */
169:         SQEntry()
170:         {
171:             std::memset(_data, 0, DataSize);
172:         }
173: 
174:         void set(const DynInstPtr& inst) { LSQEntry::set(inst); }
175: 
176:         void
177:         clear()
178:         {
179:             LSQEntry::clear();
180:             _canWB = _completed = _committed = _isAllZeros = false;
181:         }
182: 
183:         /** Member accessors. */
184:         /** @{ */
185:         bool& canWB() { return _canWB; }
186:         const bool& canWB() const { return _canWB; }
187:         bool& completed() { return _completed; }
188:         const bool& completed() const { return _completed; }
189:         bool& committed() { return _committed; }
190:         const bool& committed() const { return _committed; }
191:         bool& isAllZeros() { return _isAllZeros; }
192:         const bool& isAllZeros() const { return _isAllZeros; }
193:         char* data() { return _data; }
194:         const char* data() const { return _data; }
195:         /** @} */
196:     };
```

### `cpu/o3/lsq_unit.cc` 行 1729-1756

```cpp
1729: Fault
1730: LSQUnit::write(LSQRequest *request, uint8_t *data, ssize_t store_idx)
1731: {
1732:     assert(storeQueue[store_idx].valid());
1733: 
1734:     DPRINTF(LSQUnit, "Doing write to store idx %i, addr %#x | storeHead:%i "
1735:             "[sn:%llu]\n",
1736:             store_idx - 1, request->req()->getPaddr(), storeQueue.head() - 1,
1737:             storeQueue[store_idx].instruction()->seqNum);
1738: 
1739:     storeQueue[store_idx].setRequest(request);
1740:     unsigned size = request->_size;
1741:     storeQueue[store_idx].size() = size;
1742:     bool store_no_data =
1743:         request->mainReq()->getFlags() & Request::STORE_NO_DATA;
1744:     storeQueue[store_idx].isAllZeros() = store_no_data;
1745:     assert(size <= SQEntry::DataSize || store_no_data);
1746: 
1747:     // copy data into the storeQueue only if the store request has valid data
1748:     if (!(request->req()->getFlags() & Request::CACHE_BLOCK_ZERO) &&
1749:         !request->req()->isCacheMaintenance() &&
1750:         !request->req()->isAtomic())
1751:         memcpy(storeQueue[store_idx].data(), data, size);
1752: 
1753:     // This function only writes the data to the store queue, so no fault
1754:     // can happen here.
1755:     return NoFault;
1756: }
```

### `cpu/o3/lsq_unit.cc` 行 905-911

```cpp
905:         assert(!inst->memData);
906:         inst->memData = new uint8_t[request->_size];
907: 
908:         if (storeWBIt->isAllZeros())
909:             memset(inst->memData, 0, request->_size);
910:         else
911:             memcpy(inst->memData, storeWBIt->data(), request->_size);
```

**可实现性结论**：原始低/中/高位与单/双bit歧义；R01-R05同一byte/bit；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## SQ03

### `cpu/o3/lsq_unit.hh` 行 149-196

```cpp
149:     class SQEntry : public LSQEntry
150:     {
151:       private:
152:         /** The store data. */
153:         char _data[MaxDataBytes];
154:         /** Whether or not the store can writeback. */
155:         bool _canWB = false;
156:         /** Whether or not the store is committed. */
157:         bool _committed = false;
158:         /** Whether or not the store is completed. */
159:         bool _completed = false;
160:         /** Does this request write all zeros and thus doesn't
161:          * have any data attached to it. Used for cache block zero
162:          * style instructs (ARM DC ZVA; ALPHA WH64)
163:          */
164:         bool _isAllZeros = false;
165: 
166:       public:
167:         static constexpr size_t DataSize = sizeof(_data);
168:         /** Constructs an empty store queue entry. */
169:         SQEntry()
170:         {
171:             std::memset(_data, 0, DataSize);
172:         }
173: 
174:         void set(const DynInstPtr& inst) { LSQEntry::set(inst); }
175: 
176:         void
177:         clear()
178:         {
179:             LSQEntry::clear();
180:             _canWB = _completed = _committed = _isAllZeros = false;
181:         }
182: 
183:         /** Member accessors. */
184:         /** @{ */
185:         bool& canWB() { return _canWB; }
186:         const bool& canWB() const { return _canWB; }
187:         bool& completed() { return _completed; }
188:         const bool& completed() const { return _completed; }
189:         bool& committed() { return _committed; }
190:         const bool& committed() const { return _committed; }
191:         bool& isAllZeros() { return _isAllZeros; }
192:         const bool& isAllZeros() const { return _isAllZeros; }
193:         char* data() { return _data; }
194:         const char* data() const { return _data; }
195:         /** @} */
196:     };
```

### `cpu/o3/lsq_unit.cc` 行 763-769

```cpp
763:     if (store_inst->isStoreConditional() || store_inst->isAtomic()) {
764:         // Store conditionals and Atomics need to set themselves as able to
765:         // writeback if we haven't had a fault by here.
766:         storeQueue[store_idx].canWB() = true;
767: 
768:         ++storesToWB;
769:     }
```

### `cpu/o3/lsq_unit.cc` 行 811-835

```cpp
811: void
812: LSQUnit::commitStores(InstSeqNum &youngest_inst)
813: {
814:     assert(storeQueue.size() == 0 || storeQueue.front().valid());
815: 
816:     /* Forward iterate the store queue (age order). */
817:     for (auto& x : storeQueue) {
818:         assert(x.valid());
819:         // Mark any stores that are now committed and have not yet
820:         // been marked as able to write back.
821:         if (!x.canWB()) {
822:             if (x.instruction()->seqNum > youngest_inst) {
823:                 break;
824:             }
825:             DPRINTF(LSQUnit, "Marking store as able to write back, PC "
826:                     "%s [sn:%lli]\n",
827:                     x.instruction()->pcState(),
828:                     x.instruction()->seqNum);
829: 
830:             x.canWB() = true;
831: 
832:             ++storesToWB;
833:         }
834:     }
835: }
```

### `cpu/o3/lsq_unit.cc` 行 1197-1217

```cpp
1197: void
1198: LSQUnit::completeStore(typename StoreQueue::iterator store_idx)
1199: {
1200:     assert(store_idx->valid());
1201:     store_idx->completed() = true;
1202:     --storesToWB;
1203:     // A bit conservative because a store completion may not free up entries,
1204:     // but hopefully avoids two store completions in one cycle from making
1205:     // the CPU tick twice.
1206:     cpu->wakeCPU();
1207:     cpu->activityThisCycle();
1208: 
1209:     /* We 'need' a copy here because we may clear the entry from the
1210:      * store queue. */
1211:     DynInstPtr store_inst = store_idx->instruction();
1212:     if (store_idx == storeQueue.begin()) {
1213:         do {
1214:             storeQueue.front().clear();
1215:             storeQueue.pop_front();
1216:         } while (storeQueue.front().completed() &&
1217:                  !storeQueue.empty());
```

**可实现性结论**：_committed只在writebackStores assert，不参与关键控制；_canWB控制writebackStores/willWB；_completed控制completeStore/pop；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## LP01

### `cpu/o3/lsq_unit.cc` 行 107-180

```cpp
107: void
108: LSQUnit::completeDataAccess(PacketPtr pkt)
109: {
110:     LSQRequest *request = dynamic_cast<LSQRequest *>(pkt->senderState);
111:     DynInstPtr inst = request->instruction();
112: 
113:     // hardware transactional memory
114:     // sanity check
115:     if (pkt->isHtmTransactional() && !inst->isSquashed()) {
116:         assert(inst->getHtmTransactionUid() == pkt->getHtmTransactionUid());
117:     }
118: 
119:     // if in a HTM transaction, it's possible
120:     // to abort within the cache hierarchy.
121:     // This is signalled back to the processor
122:     // through responses to memory requests.
123:     if (pkt->htmTransactionFailedInCache()) {
124:         // cannot do this for write requests because
125:         // they cannot tolerate faults
126:         const HtmCacheFailure htm_rc =
127:             pkt->getHtmTransactionFailedInCacheRC();
128:         if (pkt->isWrite()) {
129:             DPRINTF(HtmCpu,
130:                 "store notification (ignored) of HTM transaction failure "
131:                 "in cache - addr=0x%lx - rc=%s - htmUid=%d\n",
132:                 pkt->getAddr(), htmFailureToStr(htm_rc),
133:                 pkt->getHtmTransactionUid());
134:         } else {
135:             HtmFailureFaultCause fail_reason =
136:                 HtmFailureFaultCause::INVALID;
137: 
138:             if (htm_rc == HtmCacheFailure::FAIL_SELF) {
139:                 fail_reason = HtmFailureFaultCause::SIZE;
140:             } else if (htm_rc == HtmCacheFailure::FAIL_REMOTE) {
141:                 fail_reason = HtmFailureFaultCause::MEMORY;
142:             } else if (htm_rc == HtmCacheFailure::FAIL_OTHER) {
143:                 // these are likely loads that were issued out of order
144:                 // they are faulted here, but it's unlikely that these will
145:                 // ever reach the commit head.
146:                 fail_reason = HtmFailureFaultCause::OTHER;
147:             } else {
148:                 panic("HTM error - unhandled return code from cache (%s)",
149:                       htmFailureToStr(htm_rc));
150:             }
151: 
152:             inst->fault =
153:             std::make_shared<GenericHtmFailureFault>(
154:                 inst->getHtmTransactionUid(),
155:                 fail_reason);
156: 
157:             DPRINTF(HtmCpu,
158:                 "load notification of HTM transaction failure "
159:                 "in cache - pc=%s - addr=0x%lx - "
160:                 "rc=%u - htmUid=%d\n",
161:                 inst->pcState(), pkt->getAddr(),
162:                 htmFailureToStr(htm_rc), pkt->getHtmTransactionUid());
163:         }
164:     }
165: 
166:     cpu->ppDataAccessComplete->notify(std::make_pair(inst, pkt));
167: 
168:     // [LSU][OBS-L3] response node (+ load taint): the packet just returned
169:     // from the memory system — if it delivers a registered fault (addrpath
170:     // addr registry / cache faulted-byte registry), record the resp node
171:     // and, for register-writeback loads/SC/atomics with NoFault (exactly
172:     // the completeAcc condition below), the taint_reg nodes. Placed before
173:     // the needWB branch so STORE responses are covered too; squashed insts
174:     // are guarded inside. NOTE (documented boundary): when CHAOSL1DForward
175:     // is ALSO attached, its corruption inside the needWB branch happens
176:     // AFTER this snapshot — the L3 chain is not combined-injector-aware in
177:     // v1 (the campaign runs one injector per sample). nullptr = no tracer.
178:     if (cpu->chaosPropagation)
179:         cpu->chaosPropagation->noteMemResponse(inst.get(), pkt,
180:                                                request->needWBToRegister());
```

### `cpu/o3/lsq_unit.cc` 行 1135-1155

```cpp
1135: void
1136: LSQUnit::writeback(const DynInstPtr &inst, PacketPtr pkt)
1137: {
1138:     iewStage->wakeCPU();
1139: 
1140:     // Squashed instructions do not need to complete their access.
1141:     if (inst->isSquashed()) {
1142:         assert (!inst->isStore() || inst->isStoreConditional());
1143:         ++stats.ignoredResponses;
1144:         return;
1145:     }
1146: 
1147:     if (!inst->isExecuted()) {
1148:         inst->setExecuted();
1149: 
1150:         if (inst->fault == NoFault) {
1151:             // Complete access to copy data to proper place.
1152:             inst->completeAcc(pkt);
1153:         } else {
1154:             // If the instruction has an outstanding fault, we cannot complete
1155:             // the access as this discards the current fault.
```

### `cpu/o3/CHAOSL1DForward/CHAOSL1DForward.cc` 行 60-140

```cpp
60:         Tick f = first_clock * period;
61:         if (now < f) return false;
62:         if (last_clock != 0 && now > last_clock * period) return false;
63:         return true;
64:     }
65: 
66:     bool
67:     CHAOSL1DForward::maybeCorrupt(PacketPtr pkt)
68:     {
69:         if (!cpu || probability <= 0.0f) return false;
70:         // Sampling-bias fix (findings.md Phase 2.2): the OLD code corrupted
71:         // the FIRST eligible load after the window opened. With a
72:         // deterministic instruction stream, that is the SAME dynamic
73:         // instruction every rep (observed: addr=0x769a0, tick=97358415
74:         // across ALL seeds — a squashed wrong-path load whose corruption is
75:         // discarded), so a 384-rep formal measured one squashed load, not
76:         // the post-check-escape distribution. Skip a geometric(p=0.1)
77:         // number of eligible events before injecting so the single fault
78:         // lands on a seed-dependent random eligible load.
79:         if (max_faults != 0 && faults_injected_count >= max_faults) return false;
80:         if (!inWindow()) return false;
81:         if (pkt && pkt->hasData() && !pkt->isWrite()) {
82:             // v1.1 Phase 8.2 countOnlyMode: count eligible loads, never
83:             // corrupt.
84:             if (count_only) { ++eligible_count; return false; }
85:             if (events_to_skip > 0) {
86:                 --events_to_skip;
87:                 return false;
88:             }
89:         }
90:         if (!pkt || !pkt->hasData()) return false;
91: 
92:         std::uniform_real_distribution<float> pd(0.0f, 1.0f);
93:         if (pd(rng) > probability) return false;
94: 
95:         // §2.7 post-check escape: XOR a bit of the response packet data
96:         // (post-L1D-read, post-ECC-check). The mask covers up to 8 bytes.
97:         uint64_t mask = fault_mask ? fault_mask : (1ULL << (rng() % 64));
98:         unsigned sz = pkt->getSize();
99:         if (sz == 0) return false;
100:         uint8_t *data = pkt->getPtr<uint8_t>();
101:         // XOR the low 8 bytes (or fewer) of the response data.
102:         uint64_t *p = reinterpret_cast<uint64_t*>(data);
103:         size_t n = sz / 8; if (n == 0) n = 1;
104:         for (size_t i = 0; i < n; i++) p[i] ^= mask;
105: 
106:         faults_injected_count++;
107:         if (write_log) {
108:             *(log_stream->stream()) << "Tick: " << curTick()
109:                 << ", Site: l1d_load_complete, addr=0x" << std::hex
110:                 << pkt->getAddr() << std::dec
111:                 << ", size=" << sz
112:                 << ", mask=0x" << std::hex << mask << std::dec
113:                 << ", faults_injected: " << faults_injected_count
114:                 << std::endl;
115:         }
116:         return true;
117:     }
118: 
119:     void
120:     CHAOSL1DForward::startup() {
121:         SimObject::startup();
122:         auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
123:         if (!o3cpu) {
124:             warn("CHAOSL1DForward: cpu is not an O3CPU; injector disabled.\n");
125:             return;
126:         }
127:                 o3cpu->setChaosL1DFwd(this);
128:         // v1.1 Phase 8.2: print CHAOS_ELIGIBLE_COUNT at sim exit (the
129:         // destructor may not run before gem5's exit path tears everything
130:         // down; the exit callback always fires).
131:         if (count_only) {
132:             registerExitCallback([this]() {
133:                 if (log_stream && log_stream->stream())
134:                     *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT="
135:                         << eligible_count << std::endl;
136:             });
137:         }
138:     }
139: 
140: } // namespace gem5
```

**可实现性结论**：必须修复现有 uint64_t* 8字节访问；size<8时越界；R01-R05同一byte/bit；Trace增加Post-Injection事件；ImplementationStatus=PARTIAL；SourceAuditStatus=VERIFIED。

## SP05

### `cpu/o3/lsq_unit.cc` 行 1104-1133

```cpp
1104: void
1105: LSQUnit::storePostSend()
1106: {
1107:     if (isStalled() &&
1108:         storeWBIt->instruction()->seqNum == stallingStoreIsn) {
1109:         DPRINTF(LSQUnit, "Unstalling, stalling store [sn:%lli] "
1110:                 "load idx:%li\n",
1111:                 stallingStoreIsn, stallingLoadIdx);
1112:         stalled = false;
1113:         stallingStoreIsn = 0;
1114:         iewStage->replayMemInst(loadQueue[stallingLoadIdx].instruction());
1115:     }
1116: 
1117:     if (!storeWBIt->instruction()->isStoreConditional()) {
1118:         // The store is basically completed at this time. This
1119:         // only works so long as the checker doesn't try to
1120:         // verify the value in memory for stores.
1121:         storeWBIt->instruction()->setCompleted();
1122: 
1123:         if (cpu->checker) {
1124:             cpu->checker->verify(storeWBIt->instruction());
1125:         }
1126:     }
1127: 
1128:     if (needsTSO) {
1129:         storeInFlight = true;
1130:     }
1131: 
1132:     storeWBIt++;
1133: }
```

### `cpu/o3/lsq_unit.cc` 行 1197-1255

```cpp
1197: void
1198: LSQUnit::completeStore(typename StoreQueue::iterator store_idx)
1199: {
1200:     assert(store_idx->valid());
1201:     store_idx->completed() = true;
1202:     --storesToWB;
1203:     // A bit conservative because a store completion may not free up entries,
1204:     // but hopefully avoids two store completions in one cycle from making
1205:     // the CPU tick twice.
1206:     cpu->wakeCPU();
1207:     cpu->activityThisCycle();
1208: 
1209:     /* We 'need' a copy here because we may clear the entry from the
1210:      * store queue. */
1211:     DynInstPtr store_inst = store_idx->instruction();
1212:     if (store_idx == storeQueue.begin()) {
1213:         do {
1214:             storeQueue.front().clear();
1215:             storeQueue.pop_front();
1216:         } while (storeQueue.front().completed() &&
1217:                  !storeQueue.empty());
1218: 
1219:         iewStage->updateLSQNextCycle = true;
1220:     }
1221: 
1222:     stats.sqAvgOccupancy = queueOccupancy(storeQueue);
1223: 
1224:     DPRINTF(LSQUnit, "Completing store [sn:%lli], idx:%i, store head "
1225:             "idx:%i\n",
1226:             store_inst->seqNum, store_idx.idx() - 1, storeQueue.head() - 1);
1227: 
1228:     store_inst->storeTick = curTick() - store_inst->fetchTick;
1229: 
1230:     if (isStalled() &&
1231:         store_inst->seqNum == stallingStoreIsn) {
1232:         DPRINTF(LSQUnit, "Unstalling, stalling store [sn:%lli] "
1233:                 "load idx:%li\n",
1234:                 stallingStoreIsn, stallingLoadIdx);
1235:         stalled = false;
1236:         stallingStoreIsn = 0;
1237:         iewStage->replayMemInst(loadQueue[stallingLoadIdx].instruction());
1238:     }
1239: 
1240:     store_inst->setCompleted();
1241: 
1242:     if (needsTSO) {
1243:         storeInFlight = false;
1244:     }
1245: 
1246:     // Tell the checker we've completed this instruction.  Some stores
1247:     // may get reported twice to the checker, but the checker can
1248:     // handle that case.
1249:     // Store conditionals cannot be sent to the checker yet, they have
1250:     // to update the misc registers first which should take place
1251:     // when they commit
1252:     if (cpu->checker &&  !store_inst->isStoreConditional()) {
1253:         cpu->checker->verify(store_inst);
1254:     }
1255: }
```

### `cpu/o3/lsq_unit.cc` 行 1332-1339

```cpp
1332: void
1333: LSQUnit::recvRetry()
1334: {
1335:     if (isStoreBlocked) {
1336:         DPRINTF(LSQUnit, "Receiving retry: blocked store\n");
1337:         writebackBlockedStore();
1338:     }
1339: }
```

### `cpu/o3/lsq_unit.hh` 行 499-520

```cpp
499:     bool stalled;
500:     /** The store that causes the stall due to partial store to load
501:      * forwarding.
502:      */
503:     InstSeqNum stallingStoreIsn;
504:     /** The index of the above store. */
505:     ssize_t stallingLoadIdx;
506: 
507:     /** The packet that needs to be retried. */
508:     PacketPtr retryPkt;
509: 
510:     /** Whehter or not a store is blocked due to the memory system. */
511:     bool isStoreBlocked;
512: 
513:     /** Whether or not a store is in flight. */
514:     bool storeInFlight;
515: 
516:     /** The oldest load that caused a memory ordering violation. */
517:     DynInstPtr memDepViolator;
518: 
519:     /** Flag for memory model. */
520:     bool needsTSO;
```

**可实现性结论**：gem5无独立Store Ack；completeStore控制_completed/storesToWB/释放；不虚构Ack结构；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## FW02

### `cpu/o3/lsq_unit.cc` 行 1444-1510

```cpp
1444:     // Check the SQ for any previous stores that might lead to forwarding
1445:     auto store_it = load_inst->sqIt;
1446:     assert (store_it >= storeWBIt);
1447:     // End once we've reached the top of the LSQ
1448:     while (store_it != storeWBIt && !load_inst->isDataPrefetch()) {
1449:         // Move the index to one younger
1450:         store_it--;
1451:         assert(store_it->valid());
1452:         assert(store_it->instruction()->seqNum < load_inst->seqNum);
1453:         int store_size = store_it->size();
1454: 
1455:         // Cache maintenance instructions go down via the store
1456:         // path but they carry no data and they shouldn't be
1457:         // considered for forwarding
1458:         if (store_size != 0 && !store_it->instruction()->strictlyOrdered() &&
1459:             !(store_it->request()->mainReq() &&
1460:               store_it->request()->mainReq()->isCacheMaintenance())) {
1461:             assert(store_it->instruction()->effAddrValid());
1462: 
1463:             // Check if the store data is within the lower and upper bounds of
1464:             // addresses that the request needs.
1465:             auto req_s = request->mainReq()->getVaddr();
1466:             auto req_e = req_s + request->mainReq()->getSize();
1467:             auto st_s = store_it->instruction()->effAddr;
1468:             auto st_e = st_s + store_size;
1469: 
1470:             bool store_has_lower_limit = req_s >= st_s;
1471:             bool store_has_upper_limit = req_e <= st_e;
1472:             bool lower_load_has_store_part = req_s < st_e;
1473:             bool upper_load_has_store_part = req_e > st_s;
1474: 
1475:             auto coverage = AddrRangeCoverage::NoAddrRangeCoverage;
1476: 
1477:             // If the store entry is not atomic (atomic does not have valid
1478:             // data), the store has all of the data needed, and
1479:             // the load is not LLSC, then
1480:             // we can forward data from the store to the load
1481:             if (!store_it->instruction()->isAtomic() &&
1482:                 store_has_lower_limit && store_has_upper_limit &&
1483:                 !request->mainReq()->isLLSC()) {
1484: 
1485:                 const auto& store_req = store_it->request()->mainReq();
1486:                 coverage = store_req->isMasked() ?
1487:                     AddrRangeCoverage::PartialAddrRangeCoverage :
1488:                     AddrRangeCoverage::FullAddrRangeCoverage;
1489:             } else if (
1490:                 // This is the partial store-load forwarding case where a store
1491:                 // has only part of the load's data and the load isn't LLSC
1492:                 (!request->mainReq()->isLLSC() &&
1493:                  ((store_has_lower_limit && lower_load_has_store_part) ||
1494:                   (store_has_upper_limit && upper_load_has_store_part) ||
1495:                   (lower_load_has_store_part && upper_load_has_store_part))) ||
1496:                 // The load is LLSC, and the store has all or part of the
1497:                 // load's data
1498:                 (request->mainReq()->isLLSC() &&
1499:                  ((store_has_lower_limit || upper_load_has_store_part) &&
1500:                   (store_has_upper_limit || lower_load_has_store_part))) ||
1501:                 // The store entry is atomic and has all or part of the load's
1502:                 // data
1503:                 (store_it->instruction()->isAtomic() &&
1504:                  ((store_has_lower_limit || upper_load_has_store_part) &&
1505:                   (store_has_upper_limit || lower_load_has_store_part)))) {
1506: 
1507:                 coverage = AddrRangeCoverage::PartialAddrRangeCoverage;
1508:             }
1509: 
1510:             if (coverage == AddrRangeCoverage::FullAddrRangeCoverage) {
```

### `cpu/o3/lsq_unit.cc` 行 1510-1560

```cpp
1510:             if (coverage == AddrRangeCoverage::FullAddrRangeCoverage) {
1511:                 // Get shift amount for offset into the store's data.
1512:                 int shift_amt = request->mainReq()->getVaddr() -
1513:                     store_it->instruction()->effAddr;
1514: 
1515:                 // Allocate memory if this is the first time a load is issued.
1516:                 if (!load_inst->memData) {
1517:                     load_inst->memData =
1518:                         new uint8_t[request->mainReq()->getSize()];
1519:                 }
1520:                 if (store_it->isAllZeros())
1521:                     memset(load_inst->memData, 0,
1522:                             request->mainReq()->getSize());
1523:                 else {
1524:                     // §2.4 fwd_source_sub (F5, Phase 4.2 — method1
1525:                     // wrong-source forwarding): give the injector a chance
1526:                     // to copy from an OLDER SQ entry instead of the true
1527:                     // source. Scan further down (older) the SQ for the first
1528:                     // entry with data; if none exists the injector gets
1529:                     // alt_src=nullptr and declines (no eligible event).
1530:                     bool substituted = false;
1531:                     if (cpu->lsqFwd) {
1532:                         const SQEntry *alt = nullptr;
1533:                         auto alt_it = store_it;
1534:                         while (alt_it != storeWBIt) {
1535:                             alt_it--;
1536:                             if (alt_it->size() != 0 && !alt_it->isAllZeros()
1537:                                 && alt_it->data()) {
1538:                                 alt = &(*alt_it);
1539:                                 break;
1540:                             }
1541:                         }
1542:                         if (alt) {
1543:                             substituted = cpu->lsqFwd->maybeSubstituteSource(
1544:                                 load_inst->memData,
1545:                                 (const uint8_t *)(store_it->data()) + shift_amt,
1546:                                 request->mainReq()->getSize(),
1547:                                 (const uint8_t *)(alt->data()),
1548:                                 alt->size(),
1549:                                 request->mainReq()->getVaddr());
1550:                         }
1551:                     }
1552:                     if (!substituted)
1553:                         memcpy(load_inst->memData,
1554:                             store_it->data() + shift_amt,
1555:                             request->mainReq()->getSize());
1556:                 }
1557: 
1558:                 // CHAOSLSQFwd: optionally corrupt the just-forwarded data,
1559:                 // modeling store-buffer forwarding-path corruption (the
1560:                 // reproduce-method2 v3 mechanism on core 179). Hot-path:
```

### `cpu/o3/lsq_unit.cc` 行 1647-1684

```cpp
1647:             } else if (
1648:                     coverage == AddrRangeCoverage::PartialAddrRangeCoverage) {
1649:                 // If it's already been written back, then don't worry about
1650:                 // stalling on it.
1651:                 if (store_it->completed()) {
1652:                     panic("Should not check one of these");
1653:                     continue;
1654:                 }
1655: 
1656:                 // Must stall load and force it to retry, so long as it's the
1657:                 // oldest load that needs to do so.
1658:                 if (!stalled ||
1659:                     (stalled &&
1660:                      load_inst->seqNum <
1661:                      loadQueue[stallingLoadIdx].instruction()->seqNum)) {
1662:                     stalled = true;
1663:                     stallingStoreIsn = store_it->instruction()->seqNum;
1664:                     stallingLoadIdx = load_idx;
1665:                 }
1666: 
1667:                 // Tell IQ/mem dep unit that this instruction will need to be
1668:                 // rescheduled eventually
1669:                 iewStage->rescheduleMemInst(load_inst);
1670:                 load_inst->clearIssued();
1671:                 load_inst->effAddrValid(false);
1672:                 ++stats.rescheduledLoads;
1673: 
1674:                 // Do not generate a writeback event as this instruction is not
1675:                 // complete.
1676:                 DPRINTF(LSQUnit, "Load-store forwarding mis-match. "
1677:                         "Store idx %i to load addr %#x\n",
1678:                         store_it._idx, request->mainReq()->getVaddr());
1679: 
1680:                 // Must discard the request.
1681:                 request->discard();
1682:                 load_entry.setRequest(nullptr);
1683:                 return NoFault;
1684:             }
```

**可实现性结论**：W4构造真实同地址对；记录候选、期望/实际数据来源；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## FW05

### `cpu/o3/lsq_unit.cc` 行 1510-1560

```cpp
1510:             if (coverage == AddrRangeCoverage::FullAddrRangeCoverage) {
1511:                 // Get shift amount for offset into the store's data.
1512:                 int shift_amt = request->mainReq()->getVaddr() -
1513:                     store_it->instruction()->effAddr;
1514: 
1515:                 // Allocate memory if this is the first time a load is issued.
1516:                 if (!load_inst->memData) {
1517:                     load_inst->memData =
1518:                         new uint8_t[request->mainReq()->getSize()];
1519:                 }
1520:                 if (store_it->isAllZeros())
1521:                     memset(load_inst->memData, 0,
1522:                             request->mainReq()->getSize());
1523:                 else {
1524:                     // §2.4 fwd_source_sub (F5, Phase 4.2 — method1
1525:                     // wrong-source forwarding): give the injector a chance
1526:                     // to copy from an OLDER SQ entry instead of the true
1527:                     // source. Scan further down (older) the SQ for the first
1528:                     // entry with data; if none exists the injector gets
1529:                     // alt_src=nullptr and declines (no eligible event).
1530:                     bool substituted = false;
1531:                     if (cpu->lsqFwd) {
1532:                         const SQEntry *alt = nullptr;
1533:                         auto alt_it = store_it;
1534:                         while (alt_it != storeWBIt) {
1535:                             alt_it--;
1536:                             if (alt_it->size() != 0 && !alt_it->isAllZeros()
1537:                                 && alt_it->data()) {
1538:                                 alt = &(*alt_it);
1539:                                 break;
1540:                             }
1541:                         }
1542:                         if (alt) {
1543:                             substituted = cpu->lsqFwd->maybeSubstituteSource(
1544:                                 load_inst->memData,
1545:                                 (const uint8_t *)(store_it->data()) + shift_amt,
1546:                                 request->mainReq()->getSize(),
1547:                                 (const uint8_t *)(alt->data()),
1548:                                 alt->size(),
1549:                                 request->mainReq()->getVaddr());
1550:                         }
1551:                     }
1552:                     if (!substituted)
1553:                         memcpy(load_inst->memData,
1554:                             store_it->data() + shift_amt,
1555:                             request->mainReq()->getSize());
1556:                 }
1557: 
1558:                 // CHAOSLSQFwd: optionally corrupt the just-forwarded data,
1559:                 // modeling store-buffer forwarding-path corruption (the
1560:                 // reproduce-method2 v3 mechanism on core 179). Hot-path:
```

### `cpu/o3/lsq_unit.cc` 行 1647-1684

```cpp
1647:             } else if (
1648:                     coverage == AddrRangeCoverage::PartialAddrRangeCoverage) {
1649:                 // If it's already been written back, then don't worry about
1650:                 // stalling on it.
1651:                 if (store_it->completed()) {
1652:                     panic("Should not check one of these");
1653:                     continue;
1654:                 }
1655: 
1656:                 // Must stall load and force it to retry, so long as it's the
1657:                 // oldest load that needs to do so.
1658:                 if (!stalled ||
1659:                     (stalled &&
1660:                      load_inst->seqNum <
1661:                      loadQueue[stallingLoadIdx].instruction()->seqNum)) {
1662:                     stalled = true;
1663:                     stallingStoreIsn = store_it->instruction()->seqNum;
1664:                     stallingLoadIdx = load_idx;
1665:                 }
1666: 
1667:                 // Tell IQ/mem dep unit that this instruction will need to be
1668:                 // rescheduled eventually
1669:                 iewStage->rescheduleMemInst(load_inst);
1670:                 load_inst->clearIssued();
1671:                 load_inst->effAddrValid(false);
1672:                 ++stats.rescheduledLoads;
1673: 
1674:                 // Do not generate a writeback event as this instruction is not
1675:                 // complete.
1676:                 DPRINTF(LSQUnit, "Load-store forwarding mis-match. "
1677:                         "Store idx %i to load addr %#x\n",
1678:                         store_it._idx, request->mainReq()->getVaddr());
1679: 
1680:                 // Must discard the request.
1681:                 request->discard();
1682:                 load_entry.setRequest(nullptr);
1683:                 return NoFault;
1684:             }
```

**可实现性结论**：原部分重叠拼接错误不可实现；改为错误源选择，保留ID，需研究者确认语义变更；ImplementationStatus=PARTIAL；SourceAuditStatus=VERIFIED。

## MD04

### `cpu/o3/lsq_unit.cc` 行 550-636

```cpp
550: Fault
551: LSQUnit::checkViolations(typename LoadQueue::iterator& loadIt,
552:         const DynInstPtr& inst)
553: {
554:     Addr inst_eff_addr1 = inst->effAddr >> depCheckShift;
555:     Addr inst_eff_addr2 = (inst->effAddr + inst->effSize - 1) >> depCheckShift;
556: 
557:     /** @todo in theory you only need to check an instruction that has executed
558:      * however, there isn't a good way in the pipeline at the moment to check
559:      * all instructions that will execute before the store writes back. Thus,
560:      * like the implementation that came before it, we're overly conservative.
561:      */
562:     while (loadIt != loadQueue.end()) {
563:         DynInstPtr ld_inst = loadIt->instruction();
564:         if (!ld_inst->effAddrValid() || ld_inst->strictlyOrdered()) {
565:             ++loadIt;
566:             continue;
567:         }
568: 
569:         Addr ld_eff_addr1 = ld_inst->effAddr >> depCheckShift;
570:         Addr ld_eff_addr2 =
571:             (ld_inst->effAddr + ld_inst->effSize - 1) >> depCheckShift;
572: 
573:         // LSU W5 L03: violation-detection metadata corruption — flip a bit
574:         // in the comparison address, creating a false violation (extra
575:         // squash/replay) or suppressing a real one (missed ordering
576:         // violation). The ACTUAL load/store addresses are untouched; only
577:         // the violation-check view is corrupted.
578:         if (cpu->lsqFwd && cpu->lsqFwd->violationCorrupt(ld_eff_addr1)) {
579:             DPRINTF(LSQUnit, "CHAOSLSQFwd L03: violation addr corrupted to "
580:                     "%#x (orig view of [sn:%lli])\n",
581:                     ld_eff_addr1, ld_inst->seqNum);
582:         }
583: 
584:         if (inst_eff_addr2 >= ld_eff_addr1 && inst_eff_addr1 <= ld_eff_addr2) {
585:             if (inst->isLoad()) {
586:                 // If this load is to the same block as an external snoop
587:                 // invalidate that we've observed then the load needs to be
588:                 // squashed as it could have newer data
589:                 if (ld_inst->hitExternalSnoop()) {
590:                     if (!memDepViolator ||
591:                             ld_inst->seqNum < memDepViolator->seqNum) {
592:                         DPRINTF(LSQUnit, "Detected fault with inst [sn:%lli] "
593:                                 "and [sn:%lli] at address %#x\n",
594:                                 inst->seqNum, ld_inst->seqNum, ld_eff_addr1);
595:                         memDepViolator = ld_inst;
596: 
597:                         ++stats.memOrderViolation;
598: 
599:                         return std::make_shared<GenericISA::M5PanicFault>(
600:                             "Detected fault with inst [sn:%lli] and "
601:                             "[sn:%lli] at address %#x\n",
602:                             inst->seqNum, ld_inst->seqNum, ld_eff_addr1);
603:                     }
604:                 }
605: 
606:                 // Otherwise, mark the load has a possible load violation and
607:                 // if we see a snoop before it's commited, we need to squash
608:                 ld_inst->possibleLoadViolation(true);
609:                 DPRINTF(LSQUnit, "Found possible load violation at addr: %#x"
610:                         " between instructions [sn:%lli] and [sn:%lli]\n",
611:                         inst_eff_addr1, inst->seqNum, ld_inst->seqNum);
612:             } else {
613:                 // A load/store incorrectly passed this store.
614:                 // Check if we already have a violator, or if it's newer
615:                 // squash and refetch.
616:                 if (memDepViolator && ld_inst->seqNum > memDepViolator->seqNum)
617:                     break;
618: 
619:                 DPRINTF(LSQUnit, "Detected fault with inst [sn:%lli] and "
620:                         "[sn:%lli] at address %#x\n",
621:                         inst->seqNum, ld_inst->seqNum, ld_eff_addr1);
622:                 memDepViolator = ld_inst;
623: 
624:                 ++stats.memOrderViolation;
625: 
626:                 return std::make_shared<GenericISA::M5PanicFault>(
627:                     "Detected fault with "
628:                     "inst [sn:%lli] and [sn:%lli] at address %#x\n",
629:                     inst->seqNum, ld_inst->seqNum, ld_eff_addr1);
630:             }
631:         }
632: 
633:         ++loadIt;
634:     }
635:     return NoFault;
636: }
```

### `cpu/o3/mem_dep_unit.hh` 行 182-218

```cpp
182:     class MemDepEntry
183:     {
184:       public:
185:         /** Constructs a memory dependence entry. */
186:         MemDepEntry(const DynInstPtr &new_inst);
187: 
188:         /** Frees any pointers. */
189:         ~MemDepEntry();
190: 
191:         /** Returns the name of the memory dependence entry. */
192:         std::string name() const { return "memdepentry"; }
193: 
194:         /** The instruction being tracked. */
195:         DynInstPtr inst;
196: 
197:         /** The iterator to the instruction's location inside the list. */
198:         ListIt listIt;
199: 
200:         /** A vector of any dependent instructions. */
201:         std::vector<MemDepEntryPtr> dependInsts;
202: 
203:         /** If the registers are ready or not. */
204:         bool regsReady = false;
205:         /** Number of memory dependencies that need to be satisfied. */
206:         int memDeps = 0;
207:         /** If the instruction is completed. */
208:         bool completed = false;
209:         /** If the instruction is squashed. */
210:         bool squashed = false;
211: 
212:         /** For debugging. */
213: #ifdef GEM5_DEBUG
214:         static int memdep_count;
215:         static int memdep_insert;
216:         static int memdep_erase;
217: #endif
218:     };
```

### `cpu/o3/store_set.hh` 行 76-95

```cpp
76:     typedef Addr SSID;
77: 
78:     class SSITEntry : public CacheEntry
79:     {
80:       private:
81:         SSID _ssid;
82:       public:
83:         using TagExtractor = std::function<Addr(Addr)>;
84: 
85:         SSITEntry(TagExtractor ext) : CacheEntry(ext), _ssid(MaxAddr) {}
86: 
87:         void setSSID(SSID id) { _ssid = id; }
88:         SSID getSSID(void) const { return _ssid; }
89:     };
90: 
91:     /** Default constructor.  init() must be called prior to use. */
92:     StoreSet() : Named("StoreSets"), SSIT("SSIT") {};
93: 
94:     /** Creates store set predictor with given table sizes. */
95:     StoreSet(std::string_view name, uint64_t clear_period,
```

**可实现性结论**：只抑制possibleLoadViolation一次；不混用依赖预测错误；记录正常/故障路径；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## RP01

### `cpu/o3/iew.cc` 行 563-573

```cpp
563: IEW::rescheduleMemInst(const DynInstPtr& inst)
564: {
565:     instQueue.rescheduleMemInst(inst);
566: }
567: 
568: void
569: IEW::replayMemInst(const DynInstPtr& inst)
570: {
571:     instQueue.replayMemInst(inst);
572: }
573: 
```

### `cpu/o3/inst_queue.cc` 行 1323-1339

```cpp
1323: InstructionQueue::rescheduleMemInst(const DynInstPtr &resched_inst)
1324: {
1325:     DPRINTF(IQ, "Rescheduling mem inst [sn:%llu]\n", resched_inst->seqNum);
1326: 
1327:     // Reset DTB translation state
1328:     resched_inst->translationStarted(false);
1329:     resched_inst->translationCompleted(false);
1330: 
1331:     resched_inst->clearCanIssue();
1332:     memDepUnit[resched_inst->threadNumber].reschedule(resched_inst);
1333: }
1334: 
1335: void
1336: InstructionQueue::replayMemInst(const DynInstPtr &replay_inst)
1337: {
1338:     memDepUnit[replay_inst->threadNumber].replay();
1339: }
```

### `cpu/o3/mem_dep_unit.cc` 行 380-404

```cpp
380: void
381: MemDepUnit::reschedule(const DynInstPtr &inst)
382: {
383:     instsToReplay.push_back(inst);
384: }
385: 
386: void
387: MemDepUnit::replay()
388: {
389:     DynInstPtr temp_inst;
390: 
391:     // For now this replay function replays all waiting memory ops.
392:     while (!instsToReplay.empty()) {
393:         temp_inst = instsToReplay.front();
394: 
395:         MemDepEntryPtr inst_entry = findInHash(temp_inst);
396: 
397:         DPRINTF(MemDepUnit, "Replaying mem instruction PC %s [sn:%lli].\n",
398:                 temp_inst->pcState(), temp_inst->seqNum);
399: 
400:         moveToReady(inst_entry);
401: 
402:         instsToReplay.pop_front();
403:     }
404: }
```

**可实现性结论**：记录execution_attempt_id/replay_generation；区分MD04漏报；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## DA04

### `cpu/o3/lsq.cc` 行 764-800

```cpp
764: LSQ::pushRequest(const DynInstPtr& inst, bool isLoad, uint8_t *data,
765:         unsigned int size, Addr addr, Request::Flags flags, uint64_t *res,
766:         AtomicOpFunctorPtr amo_op, const std::vector<bool>& byte_enable)
767: {
768:     // This comming request can be either load, store or atomic.
769:     // Atomic request has a corresponding pointer to its atomic memory
770:     // operation
771:     [[maybe_unused]] bool isAtomic = !isLoad && amo_op;
772: 
773:     // LSU W4 A-series PRE hook (W1 ⑦ ruling): pushRequest entry = the AGU's
774:     // raw output, the single mandatory pass-through point BEFORE split
775:     // decision and Request construction. Mutates the by-value addr/size
776:     // copies so every downstream consumer sees the fault. byte_enable is a
777:     // const ref here — BE mutation is NOT offered at this hook (A06 does
778:     // size only; documented in 09 §3-W4).
779:     if (cpu->chaosAddrPathPre) {
780:         const Addr pre_old_addr = addr;
781:         const unsigned int pre_old_size = size;
782:         size = cpu->chaosAddrPathPre->maybeCorruptPre(addr, size, isLoad,
783:                                                       flags);
784:         // [LSU][OBS-L3] register the PRE-family injection with the L3
785:         // propagation tracer (inj + addr_form nodes + addr registry).
786:         // lastPreHookInjected() also covers the flag-only modes (S06/L02
787:         // leave addr/size untouched — a before/after compare here would
788:         // miss them); their chain honestly stops at addr_form (no faulted
789:         // address to track). nullptr tracer / no injection = no-op.
790:         if (cpu->chaosPropagation &&
791:             cpu->chaosAddrPathPre->lastPreHookInjected()) {
792:             cpu->chaosPropagation->registerInjection(
793:                 "lsq_pushRequest_PRE", inst->seqNum, pre_old_addr, addr,
794:                 isLoad, pre_old_size, size);
795:         }
796:     }
797: 
798:     ThreadID tid = cpu->contextToThread(inst->contextId());
799:     auto cacheLineSize = cpu->cacheLineSize();
800:     bool needs_burst = transferNeedsBurst(addr, size, cacheLineSize);
```

### `cpu/o3/lsq.cc` 行 833-834

```cpp
833:         request->_byteEnable = (byte_enable.size() == size)
834:             ? byte_enable : std::vector<bool>(size, true);
```

### `cpu/o3/lsq.cc` 行 1114-1149

```cpp
1114: void
1115: LSQ::LSQRequest::addReq(Addr addr, unsigned size,
1116:            const std::vector<bool>& byte_enable)
1117: {
1118:     unsigned inactive_tail_size = inactiveTailSize(byte_enable.begin(),
1119:                                                    byte_enable.end());
1120: 
1121:     if (inactive_tail_size != byte_enable.size()) {
1122:         auto req = new Request(
1123:                 addr, size-inactive_tail_size, _flags, _inst->requestorId(),
1124:                 _inst->pcState().instAddr(), _inst->contextId(),
1125:                 std::move(_amo_op));
1126: 
1127:         req->setByteEnable(
1128:                 std::vector<bool>(byte_enable.begin(),
1129:                                   byte_enable.end()-inactive_tail_size));
1130: 
1131:         /* If the request is marked as NO_ACCESS, setup a local access */
1132:         if (_flags.isSet(Request::NO_ACCESS)) {
1133:             req->setLocalAccessor(
1134:                 [this, req](gem5::ThreadContext *tc, PacketPtr pkt) -> Cycles
1135:                 {
1136:                     if ((req->isHTMStart() || req->isHTMCommit())) {
1137:                         auto& inst = this->instruction();
1138:                         assert(inst->inHtmTransactionalState());
1139:                         pkt->setHtmTransactional(
1140:                             inst->getHtmTransactionUid());
1141:                     }
1142:                     return Cycles(1);
1143:                 }
1144:             );
1145:         }
1146: 
1147:         _reqs.emplace_back(req);
1148:     }
1149: }
```

### `cpu/o3/lsq.hh` 行 219-300

```cpp
219:     class LSQRequest : public BaseMMU::Translation, public Packet::SenderState
220:     {
221:       protected:
222:         typedef uint32_t FlagsStorage;
223:         typedef Flags<FlagsStorage> FlagsType;
224: 
225:         enum Flag : FlagsStorage
226:         {
227:             IsLoad              = 0x00000001,
228:             /** True if this request needs to writeBack to register.
229:               * Will be set in case of load or a store/atomic
230:               * that writes registers (SC)
231:               */
232:             WriteBackToRegister = 0x00000002,
233:             Delayed             = 0x00000004,
234:             IsSplit             = 0x00000008,
235:             /** True if any translation has been sent to TLB. */
236:             TranslationStarted  = 0x00000010,
237:             /** True if there are un-replied outbound translations.. */
238:             TranslationFinished = 0x00000020,
239:             Sent                = 0x00000040,
240:             Retry               = 0x00000080,
241:             Complete            = 0x00000100,
242:             /** Ownership tracking flags. */
243:             /** Translation squashed. */
244:             TranslationSquashed = 0x00000200,
245:             /** Request discarded */
246:             Discarded           = 0x00000400,
247:             /** LSQ resources freed. */
248:             LSQEntryFreed       = 0x00000800,
249:             /** Store written back. */
250:             WritebackScheduled  = 0x00001000,
251:             WritebackDone       = 0x00002000,
252:             /** True if this is an atomic request */
253:             IsAtomic            = 0x00004000
254:         };
255:         FlagsType flags;
256: 
257:         enum class State
258:         {
259:             NotIssued,
260:             Translation,
261:             Request,
262:             Fault,
263:             PartialFault,
264:         };
265:         State _state;
266:         void setState(const State& newState) { _state = newState; }
267: 
268:         uint32_t numTranslatedFragments;
269:         uint32_t numInTranslationFragments;
270: 
271: 
272:         void markDelayed() override { flags.set(Flag::Delayed); }
273:         bool isDelayed() { return flags.isSet(Flag::Delayed); }
274: 
275:       public:
276:         LSQUnit& _port;
277:         const DynInstPtr _inst;
278:         uint32_t _taskId;
279:         PacketDataPtr _data;
280:         std::vector<PacketPtr> _packets;
281:         std::vector<RequestPtr> _reqs;
282:         std::vector<Fault> _fault;
283:         uint64_t* _res;
284:         const Addr _addr;
285:         const uint32_t _size;
286:         const Request::Flags _flags;
287:         std::vector<bool> _byteEnable;
288:         uint32_t _numOutstandingPackets;
289:         AtomicOpFunctorPtr _amo_op;
290:         bool _hasStaleTranslation;
291: 
292:       protected:
293:         LSQUnit* lsqUnit() { return &_port; }
294:         LSQRequest(LSQUnit* port, const DynInstPtr& inst, bool isLoad);
295:         LSQRequest(LSQUnit* port, const DynInstPtr& inst, bool isLoad,
296:                 const Addr& addr, const uint32_t& size,
297:                 const Request::Flags& flags_, PacketDataPtr data=nullptr,
298:                 uint64_t* res=nullptr, AtomicOpFunctorPtr amo_op=nullptr,
299:                 bool stale_translation=false);
300: 
```

**可实现性结论**：bit0对应vaddr+0字节；小端不改变mask索引映射；必须实际修改Request mask；不同时改size/address；ImplementationStatus=NEEDS_HOOK；SourceAuditStatus=VERIFIED。

## 附：关键字段使用证据

### SQ03 `_committed` / `_canWB` / `_completed`

- `_committed`：`lsq_unit.cc:884` `assert(!storeWBIt->committed());`；`:903` `storeWBIt->committed() = true;`。仅用于写回断言/记账，不控制释放。
- `_canWB`：`:766` SC/atomic 置位；`:830` `commitStores` 置位；`:858` `writebackStores` while 条件；`:370` `willWB`。控制能否写回。
- `_completed`：`:1201` `store_idx->completed() = true;`；`:1216` pop 循环；`:371` `willWB`；`:1591/:1651` forwarding。控制完成/释放。

### LP01 越界代码（CHAOSL1DForward.cc）

```cpp
uint8_t *data = pkt->getPtr<uint8_t>();
uint64_t *p = reinterpret_cast<uint64_t*>(data);
size_t n = sz / 8; if (n == 0) n = 1;
for (size_t i = 0; i < n; i++) p[i] ^= mask;
```

size<8 时仍访问8字节，必须改为逐字节。

### FW05 错误源选择（CHAOSLSQFwd.cc）

```cpp
unsigned n = copy_size < alt_size ? copy_size : alt_size;
memcpy(load_data, alt_src, n);
```

`alt_src` 是较老 SQ entry 数据；这是可注入的真实错误源选择。



## v3.1 关键补充：A01/A03 Hook位置

当前 `CHAOSAddrPath` 的 `a01_bit`/`a03_stuck` 在 `maybeCorrupt(RequestPtr&)` 中实现，调用点是 `LSQRequest::sendFragmentToTranslation` 的 POST hook（`lsq.cc:1173-1187`）。`pushRequest` 入口的 PRE hook 只调用 `maybeCorruptPre()`（`lsq.cc:779-796`），其模式集合不含 a01/a03。若第三轮要求 pushRequest 作为正式位置，必须新增 PRE 模式；当前不能声称已实现。

## v3.1 关键补充：LQ04 freeLSQEntry

`LSQEntry::clear()` 调用 `_request->freeLSQEntry()`（`lsq_unit.hh:107-125`），`freeLSQEntry()` 释放 `LSQEntryFreed` 标志（`lsq.hh:539`）。提前 clear 会释放仍在途请求资源；不能简单视为字段清零。

## v3.1 关键补充：RP01 双路径

partial-forward 分支调用 `iewStage->rescheduleMemInst(load_inst)`（`lsq_unit.cc:1669`）；随后 `storePostSend`/`completeStore` 若匹配 `stallingLoadIdx` 会调用 `replayMemInst`（`lsq_unit.cc:1104-1115,1230-1238`）。仅抑制 reschedule 不足以保证 replay 被抑制。
