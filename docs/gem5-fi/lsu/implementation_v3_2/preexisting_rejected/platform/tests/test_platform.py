import unittest, json, tempfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fault_manager import FaultManager, Mode
from trace_writer import TraceWriter
from trace_validator import validate
from terminal import classify

class TestFaultManager(unittest.TestCase):
    def test_f0_once(self):
        fm=FaultManager(Mode.F0,warmup_events=0,span_events=1,max_faults=1,rng=1)
        hits=[i for i in range(1,6) if fm.on_eligible()]
        self.assertEqual(len(hits),1)
    def test_f5_持续(self):
        fm=FaultManager(Mode.F5,warmup_events=2,max_faults=0,rng=1)
        r=[fm.on_eligible() for _ in range(5)]
        self.assertEqual(r,[False,False,True,True,True])
    def test_f6_single(self):
        fm=FaultManager(Mode.F6,max_faults=1,rng=1)
        self.assertFalse(fm.on_eligible())
        self.assertTrue(fm.on_f6_event())
        self.assertFalse(fm.on_f6_event())

class TestTrace(unittest.TestCase):
    def test_trace_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"t.jsonl"; w=TraceWriter(p,"S-R01","F1","A01")
            e1=w.event("injection",unit="AGU",sub_unit="EA",old_value="0x1000",new_value="0x1008")
            e2=w.event("activation",parent_event_id=e1,dyn_inst_seq=10,execution_attempt_id=0,replay_generation=0,unit="AGU")
            w.edge(e1,e2,producer_inst_seq=10,consumer_inst_seq=10)
            w.close(trace_completeness="COMPLETE")
            self.assertEqual(validate(p),[])
class TestTerminal(unittest.TestCase):
    def test_incomplete_not_masked(self):
        r=classify(exit_code=0,timed_out=False,simulator_error=False,eligible=1,injected=1,
                   oracle_match=True,squashed=False,detected=False,arch_state_bad=False,trace_complete=False)
        self.assertNotEqual(r["terminal_state"],"MASKED")
        self.assertEqual(r["trace_completeness"],"INCOMPLETE")
    def test_sdc(self):
        r=classify(exit_code=0,timed_out=False,simulator_error=False,eligible=1,injected=1,
                   oracle_match=False,arch_state_bad=True,trace_complete=True)
        self.assertEqual(r["terminal_state"],"SDC")

if __name__=="__main__": unittest.main(verbosity=2)
