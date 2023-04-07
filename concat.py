#!/usr/bin/env python
import sys

orders = ' '.join(sys.argv[1:])
print('below are contents of file(s), each starting with its name and path (prefixed with "---").',orders)
print("\n")
for ln in sys.stdin:
    fn = ln.strip()
    print('---',fn)
    with open(fn,'r') as f:
        for l in f.readlines():
            print(l.strip('\n'))
