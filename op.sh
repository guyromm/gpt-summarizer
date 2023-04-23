#!/bin/bash
cmd=$(jq .id tasks/$1.response)
code=$(cat tasks/$1.apply.code)
echo '* COMMAND EXECUTION LOG' ;
echo "--- command $cmd that was executed:"
jq . tasks/$1.response
echo '--- command '$cmd' return code: '$code ;
cat tasks/$1.apply.log
echo '--- end of command '$cmd' output'
