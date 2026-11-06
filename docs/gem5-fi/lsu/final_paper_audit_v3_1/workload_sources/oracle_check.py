#!/usr/bin/env python3
import re,sys
def main():
    if len(sys.argv)!=3:
        print("usage: oracle_check.py <expected_checksum> <gem5_stdout>"); return 2
    exp=sys.argv[1].strip().lower().replace('0x','')
    txt=open(sys.argv[2],encoding='utf-8',errors='replace').read()
    m=re.findall(r'checksum=0x([0-9a-fA-F]+)',txt)
    if not m:
        print("ORACLE_FAIL: no checksum line"); return 1
    got=m[-1].lower()
    print(f"expected={exp} got={got}")
    print("ORACLE_PASS" if got==exp else "ORACLE_FAIL"); return 0 if got==exp else 1
if __name__=='__main__': sys.exit(main())
