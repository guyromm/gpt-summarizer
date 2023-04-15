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
for cb in e:
    if len(sys.argv)>1 and cb.syntax not in (sys.argv[1:]):
        continue
    #print(len(cb.code.split('\n')))
    #print([e for e in dir(cb) if not e.startswith('_')])
    for fn in ['expect_exception', 'expected_output', 'lineno', 'syntax']: #'code',
        print(fn,':',getattr(cb,fn))
    print(cb.code)
    #print(ln,end='')
