#!/usr/bin/env python
import json
import os
import subprocess
from typing import Dict
import difflib
import io
import sys

def apply_diff(diff: str) -> None:
    diff_lines = diff.splitlines()
    if not diff_lines:
        return

    file_name = diff_lines[0][4:]
    with open(file_name, "r") as f:
        original_content = f.readlines()

    patched_content = list(difflib.restore(diff_lines, 2))
    with open(file_name, "w") as f:
        f.writelines(patched_content)

def process_diff(contents: str, reasoning: str, id: int) -> Dict[str, str]:
    apply_diff(contents)
    return {
        "command": "diff",
        "contents": contents,
        "reasoning": reasoning,
        "id": id,
    }

def process_file_write(contents: Dict[str, str], reasoning: str, id: int) -> Dict[str, str]:
    for file_name, file_content in contents.items():
        if os.path.exists(file_name):
            exc = open(file_name,'r').read()
            if exc==file_content:
                raise Exception(f"file {file_name} contents is identical to what is about to be written.") 
        with open(file_name, "w") as f:
            f.write(file_content)

    return {
        "command": "file_write",
        "contents": contents,
        "reasoning": reasoning,
        "id": id,
    }

def process_shell(contents: str, reasoning: str, id: int) -> Dict[str, str]:
    result = subprocess.run(contents, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    rt = {
        "command": "shell",
        "contents": contents,
        "reasoning": reasoning,
        "id": id,
        "output": result.stdout,
        "error": result.stderr,
    }
    print(json.dumps(rt))
    return rt

def process_reply(reply_data: Dict) -> Dict[str, str]:
    command = reply_data["command"]
    contents = reply_data["contents"]
    reasoning = reply_data["reasoning"]
    id = reply_data["id"]

    if command == "shell":
        return process_shell(contents, reasoning, id)
    elif command == "diff":
        return process_diff(contents, reasoning, id)
    elif command == "file_write":
        return process_file_write(contents, reasoning, id)
    else:
        raise ValueError(f"Invalid command: {command}")


if __name__=='__main__':
    j = json.load(sys.stdin)
    process_reply(j)
