#!/usr/bin/env python
from chatgpt_wrapper.openai.api import AsyncOpenAIAPI
from chatgpt_wrapper.config import Config
import asyncio,sys

config = Config()
config.set('chat.model', 'gpt4')
config.set('disallowed_specials','()')

gpt = AsyncOpenAIAPI(config)
gpt.set_model_temperature(0.0)
summary=[]
async def main():
    toask=''
    for ln in sys.stdin:
        toask+=ln

    first=True
    async for chunk in gpt.ask_stream(toask):
        if first:
            print("")
            first=False
        print(chunk,end="")
        summary.append(chunk)
        sys.stdout.flush()
    
asyncio.run(main())
