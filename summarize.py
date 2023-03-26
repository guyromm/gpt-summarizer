#!/usr/bin/env python
"""
invocation example: 
F=2303.12712.pdf
curl 'https://arxiv.org/pdf/'$F -o $F &&  pdf2txt $F | ./summarize.py $F-gpt4.json
jq -r '.input_chunks[].output' $F-gpt4.json
"""
import sys
import os
import json
import traceback
from transformers import GPT2TokenizerFast

import asyncio
from chatgpt_wrapper.openai.api import AsyncOpenAIAPI
from chatgpt_wrapper.openai.api_shell import ApiShell
from chatgpt_wrapper.config import Config

MAX_TOKENS=4000
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
lines=[]
summaries=[]
def chunker(lines,fr=0):
    #print('chunker fr=',fr)
    tosum=[] ; i=1
    pt=0
    while True:
        if len(summaries):
            prefix = ['You are a reduce function that summarizes text. The current accumulator state is below the "---", followed by a separator ("==="), followed by the input to summarize. Do not repeat statements already in the accumulator, use it as context for the input to summarize. Be terse and avoid repeating terms already present in the accumulator state such as "the text", "the paper", "the author", etc. Avoid repetitions in general.\n\n---\n\n']+["\n\n".join(summaries)]+["\n\n===\n\n"] # v3
        else:
            prefix = ['Summarize the following text. Be terse and avoid terms such as "the text" or "the paper"']
        tosum=prefix+lines[fr:i]            
        tokens = len(tokenizer("\n".join(tosum))['input_ids'])
        if tokens<MAX_TOKENS:
            if i>=len(lines):
                break
            else:
                i+=1
                pt = tokens
        else:
            break
    return prefix,tosum,fr,i



def make_chunks():
    chunks=[]
    for ln in sys.stdin:
        lines.append(ln)
    fr=0 ; i=1
    while fr<len(lines):
        prefix,chunk,fr,i = chunker(lines,fr=fr)
        yield {'text':"\n".join(chunk),"prefix":"\n".join(prefix),'fr':fr,'i':i}
        _=fr ; fr=i ; i=_+i

async def main(reuse=True):
    if os.path.exists(sys.argv[1]):
        cache = json.load(open(sys.argv[1],'r'))
    else:
        cache = {'input_chunks':[]}
    config = Config()
    config.set('chat.model', 'gpt4')
    config.set('disallowed_specials','()')
    gpt = AsyncOpenAIAPI(config)
    shell = ApiShell(config)
    err=None
    input_chunks=[]
    def save(suffix=''):
        fp = open(sys.argv[1]+suffix,'w')
        fp.write(json.dumps({"summaries":summaries,
                             "input_chunks":input_chunks,
                             "err":err}))
        fp.close()
        
    try:
        cnt=0
        for chunk in make_chunks():
            input_chunks.append(chunk)
            chunksize = chunk['i']-chunk['fr']
            if chunksize<1:
                print('error at',chunk['fr'],':',chunk['i'])
                raise Exception('could not fit lines for summarization.')
            shell._print_markdown(f"# {cnt} summarizing {chunksize} lines: {chunk['fr']}:{chunk['i']}/{len(lines)}")
            first = True
            gpt.set_model_temperature(0.0)
            summary=[]
            incache = [c for c in cache['input_chunks'] if c['text']==chunk['text']]
            if len(incache) and incache[0].get('output'):
                    summary=incache[0].get('output')
                    print('cached output:',summary)
            else:
                async for chunk in gpt.ask_stream(chunk['text']):
                    if first:
                        print("")
                        first = False
                    print(chunk, end="")
                    summary.append(chunk)
                    sys.stdout.flush()
            summaries.append("".join(summary))
            input_chunks[-1]['output']="".join(summary)
            print("\n")
            # Work around rate limit if needed.
            save('.tmp')
            await asyncio.sleep(5)
            cnt+=1
    except Exception as e:
        print('an error occured:')
        print(traceback.format_exc())
        err=str(e)
    finally:
        save()
asyncio.run(main())

