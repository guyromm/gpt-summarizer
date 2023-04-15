#!/usr/bin/env python
from chatgpt_wrapper.backends.openai.api import OpenAIAPI
from chatgpt_wrapper.core.config import Config
import sys

config = Config()
config.set('chat.model', 'gpt4')
config.set('disallowed_specials','()')

gpt = OpenAIAPI(config)
temp =  float(sys.argv[1]) if len(sys.argv)>1 else 0.0
gpt.set_model_temperature(temp)
#summary=[]
def main():
    toask=''
    for ln in sys.stdin:
        toask+=ln

    first=True
    st,summary,conv = gpt.ask_stream(toask)
    
main()
