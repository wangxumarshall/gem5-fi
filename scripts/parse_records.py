import struct, sys
MAGIC=0x3149554650465046
def records(path):
    b=open(path,'rb').read()
    out=[]; i=0
    while True:
        i=b.find(struct.pack('<Q',MAGIC), i)
        if i<0: break
        d=b[i:i+128]
        if len(d)<96: break
        v=struct.unpack('<12Q', d[:96])
        out.append(dict(magic=v[0],model=v[1],ctx=v[2],mode=v[3],iter=v[4],
                        raw0=v[5],raw1=v[6],fpsr=v[7],fpcr=v[8],nzcv=v[9],
                        lane=v[10],status=v[11]))
        i+=128
    return out
if __name__=='__main__':
    for p in sys.argv[1:]:
        rs=records(p)
        print(p, len(rs))
        for r in rs[:5]:
            print(' ', {k:(hex(v) if k in ('raw0','raw1','fpsr','fpcr','nzcv') else v) for k,v in r.items()})
