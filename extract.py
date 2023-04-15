#!/usr/bin/env python
import sys
import re
import exdown
from io import StringIO

s=''
for ln in sys.stdin:
    s+=ln
sio = StringIO(s)
e = exdown.extract_from_buffer(sio)
filenames = sys.argv[2:]
cnt=0
for cb in e:
    if len(sys.argv)>1 and sys.argv[1] and cb.syntax not in (sys.argv[1:]):
        continue
    if len(filenames)>=cnt and filenames[cnt]:
        fn = filenames[cnt]
        fp = open(fn,'w')
        fp.write(cb.code)
        fp.close()
        print('written',len(cb.code),'bytes to',fn)
    else:
        toprint=[]
        for fn in ['expect_exception', 'expected_output', 'lineno', 'syntax']: #'code',
            topr = f'{fn}:{getattr(cb,fn)}'
            toprint.append(topr)
        print('# ==='+','.join(toprint))
        print(cb.code)
    cnt+=1
    #print(ln,end='')
