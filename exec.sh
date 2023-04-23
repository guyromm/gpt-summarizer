#!/bin/bash
task="$1"
cat tasks/$1.response \
    | ./process_replies.py &>1 \
    | tee tasks/$1.apply.log ;
echo $? \
    | tee tasks/$1.apply.code \
    | sed -E 's/^/CODE: /g'
