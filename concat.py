#!/usr/bin/env python
import sys
from transformers import GPT2TokenizerFast
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

orders = ' '.join(sys.argv[1:])
#
op=[]
op+=['below are file(s), each beginning with the filename (prefixed with "---"), followed by its contents.\n',orders+'\n']
#print("\n")
tokensizes={}
filesizes={}

for ln in sys.stdin:
    fn = ln.strip()
    op+=['\n--- '+fn+'\n']
    with open(fn,'r') as f:
        flines=''
        for l in f.readlines():
            op+=[l] #print(l.strip('\n'))
            flines+=l
    #print('tokenizing',len(flines),'bytes of',fn)
    tokensizes[fn]=len(tokenizer(''.join(flines))['input_ids'])
    filesizes[fn]=len(flines)
print(''.join(op))    
toklen = len(tokenizer("".join(op))['input_ids'])
if toklen>4000:
    for k,v in tokensizes.items():
        print('concat.py:',k,v,'tokens',filesizes[k],'bytes',file=sys.stderr)
    print(f'concat.py: TOO LONG ({toklen=})',file=sys.stderr)
