#!/usr/bin/env python
import sys

orders = ' '.join(sys.argv[1:])
print('below are file(s), each beginning with the filename (prefixed with "---"), followed by its contents.',orders)
print("\n")
for ln in sys.stdin:
    fn = ln.strip()
    print('---',fn)
    with open(fn,'r') as f:
        for l in f.readlines():
            print(l.strip('\n'))
