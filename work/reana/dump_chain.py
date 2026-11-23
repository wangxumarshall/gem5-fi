#!/usr/bin/env python3
"""Dump fault-relevant event flow for a given trace, showing populated fields."""
import gzip, re, sys

def kv(line):
    return dict(re.findall(r"(\w+)=([^ ]*)", line))

# Fields of interest, ordered.
FIELDS = ["kind","event_id","tick","fault_id","parent_event_id","source_event_id",
          "origin_event_id","translation_id","walk_id","request_id","lookup_id",
          "tlbi_id","tlb_instance","tlb_entry_id","entry_generation","asid","vmid",
          "va","pa","pfn","dyn_inst_seq","origin_dyn_inst_seq","mode","stage",
          "regime","security_state","outcome","corr","evidence_status","squashed",
          "consumed","old_pfn","new_pfn","old_pa","new_pa","candidate_asid",
          "candidate_pa","candidate_pfn","retained_entry_id","retained_entry_generation",
          "fault_arm_event_id","fault_disarm_event_id","consumption_event_id",
          "match_event_id","lookup_event_id","entry_insert_event_id","ptw_request_id",
          "ptw_response_id","request_pa_before","request_pa_after","permission_before",
          "permission_after","next_table_pa_before","next_table_pa_after",
          "descriptor_before","descriptor_after","descriptor_type","pte_address",
          "state_consumed","result_propagated","exception_delivered","exception_class",
          "fault_state_consumed_event_id","fault_result_propagated_event_id",
          "exception_delivery_event_id","lineage_state","reuse_ordinal","walk_level",
          "is_fetch","is_write","permission_result","hit","cache_name","cache_req_id",
          "memory_attribute","result_pa","result_propagated","fault_va","fault_source",
          "fault_source_level","isv","delivery_target","faulting_inst_squashed",
          "faulting_inst_squash_event_id","op_class","fu_class","queue","field"]

def main(path, filt=None):
    evs=[]
    with gzip.open(path,"rt",errors="replace") as fh:
        for line in fh:
            if not line.startswith("PROP-EVT:"): continue
            evs.append(kv(line))
    # determine fault id(s)
    fids = sorted({e.get("fault_id","0") for e in evs if e.get("fault_id","") not in ("","0")})
    print("# fault_ids:", fids)
    # activation kinds
    for e in evs:
        if e.get("kind") in ("mmu_fault_activate","mmu_fault_arm","refill_pfn_corrupt"):
            print("=== ACTIVATION ===")
            print(" ".join(f"{k}={e.get(k,'')}" for k in FIELDS if e.get(k,'') not in ('','NA')))
    if filt:
        kinds=filt.split(",")
    else:
        kinds=None
    # print events that carry a fault_id, and their immediate parents/children
    keep_ids=set()
    for e in evs:
        if e.get("fault_id","") not in ("","0"):
            keep_ids.add(e.get("event_id"))
            # include linked events
            for lk in ("parent_event_id","source_event_id","origin_event_id","lookup_event_id",
                       "consumption_event_id","match_event_id","entry_insert_event_id",
                       "fault_arm_event_id","fault_disarm_event_id","activation_event_id",
                       "result_event_id","response_event_id","writeback_event_id","commit_event_id",
                       "ptw_request_id","ptw_response_id","fault_state_consumed_event_id",
                       "fault_result_propagated_event_id","exception_delivery_event_id",
                       "origin_squash_event_id","faulting_inst_squash_event_id"):
                v=e.get(lk,"")
                if v: keep_ids.add(v)
    # also include events at same entry identity as activation
    for e in evs:
        if kinds and e.get("kind") not in kinds: continue
        if e.get("event_id") in keep_ids or (kinds is not None):
            print(" ".join(f"{k}={e.get(k,'')}" for k in FIELDS if e.get(k,'') not in ('','NA')))
            print("---")

if __name__=="__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)
