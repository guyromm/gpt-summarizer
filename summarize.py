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
import hashlib

MAX_TOKENS=4000
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
lines=[]
summaries=[]

def chunker(lines,fr=0,cache={}):
    print('chunker fr=',fr,len(summaries),'summaries',sum([len(s) for s in summaries]),'overall summary bytes')
    #raise Exception(cache['input_chunks'])
    # should we use the cached chunk?
    ic = [i for i in cache.get('input_chunks',[]) if i['fr']==fr]
    if len(ic):
        i=ic[0]['i']
    else:
        i=1
    tosum=[]
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



async def make_chunks(gpt,save,cache):
    global summaries
    chunks=[]
    for ln in sys.stdin:
        lines.append(ln)
    fr=0 ; i=1
    while fr<len(lines):
        prefix,chunk,fr,i = chunker(lines,fr=fr,cache=cache)
        if i-fr<1:
            pf = "\n".join(prefix).split('\n---\n')[1].split('\n===\n')[0]
            prompt = "Summarize the text below '---', summary must be half as long as original.\n\n====\n\n"+pf
            hs = hashlib.md5(prompt.encode('utf-8')).hexdigest()
            print('* PREFIX') ; print(prompt) ; print('prefix len:',len(prompt),'tokens=',len(tokenizer(prompt)['input_ids']))
            if not cache.get('cache'): cache['cache']={}
            if cache['cache'].get(hs):
                summary=cache['cache'].get(hs)
            else:
                summary=[]
                first=False

                async for chunk in gpt.ask_stream(prompt):
                    if first:
                        print("")
                        first = False
                    print(chunk, end="")
                    summary.append(chunk)
                    sys.stdout.flush()
                cache['cache'][hs]=summary
                save(cache,'.tmp',True)
            summaries=["".join(summary)]
            prefix,chunk,fr,i = chunker(lines,fr=fr,cache=cache)
            #raise Exception('mid-summary:',summary)
        print('yielding',fr,i,i-fr)
        yield {'text':"\n".join(chunk),"prefix":"\n".join(prefix),'fr':fr,'i':i}
        _=fr ; fr=i ; i=_+i
    if not i-fr:
        print('CHUNKSIZE',i,fr)

def save(cache,suffix='',loss_ok=False):
    print('save(',suffix,loss_ok,')')
    fn = sys.argv[1]+suffix
    if not loss_ok and os.path.exists(sys.argv[1]+suffix):
        with open(fn,'r') as f:
            j = json.load(f)
            l = len(j.get('input_chunks',[]))
            if l>len(cache.get('input_chunks',[])):
                print('got input chunks cached on disk:',l,'input chunks in mem:',len(cache.get('input_chunks',[])))
                raise Exception('overwriting more input chunks than i have already.')

    fp = open(fn,'w')
    # {"summaries":summaries,
    #                      "input_chunks":input_chunks,
    #                      "err":err}
    fp.write(json.dumps(cache))
    fp.close()
    print('save(',fn,'): done')
        
async def main(reuse=True):
    if os.path.exists(sys.argv[1]):
        cache = json.load(open(sys.argv[1],'r'))
    else:
        cache = {'input_chunks':[]}
    print('input chunks loaded (',len(cache.get('input_chunks')),')')    
    config = Config()
    config.set('chat.model', 'gpt4')
    config.set('disallowed_specials','()')
    gpt = AsyncOpenAIAPI(config)
    shell = ApiShell(config)
    err=None
    print('input chunks pre-ze (',len(cache.get('input_chunks')),')')
    input_chunks=[]
    print('input chunks zeroed (',len(cache.get('input_chunks')),')')
    
    try:
        cnt=0
        gpt.set_model_temperature(0.0)
        async for chunk in make_chunks(gpt,save,cache):
            input_chunks.append(chunk)

            chunksize = chunk['i']-chunk['fr']
            if chunksize<1:
                print('error at',chunk['fr'],':',chunk['i'])
                raise Exception('could not fit lines for summarization.')
            shell._print_markdown(f"# {cnt} summarizing {chunksize} lines: {chunk['fr']}:{chunk['i']}/{len(lines)}")
            first = True

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
            save(cache,'.tmp',True)
            #await asyncio.sleep(5)
            cnt+=1
    except Exception as e:
        print('an error occured:')
        print(traceback.format_exc())
        err=str(e)
    finally:
        print('in finally') 
        save(cache)
asyncio.run(main())

