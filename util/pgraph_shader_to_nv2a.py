#!/usr/bin/env python3

"""Converts vertex shaders from xemu-style pgraph traces to nv2a-vsh asm."""

import argparse
import os
import re
import sys
from typing import List

import nv2avsh


_HEX_STRING = r"0x[0-9a-fA-F]+"

_PREFIX = r"nv2a_pgraph_method 0: NV20_KELVIN_PRIMITIVE<0x97> -> "

# Prettified:
# nv2a_pgraph_method 0: NV20_KELVIN_PRIMITIVE<0x97> -> NV097_SET_TRANSFORM_PROGRAM_LOAD<0x1E9C> (0x3C)
# nv2a_pgraph_method 0: NV20_KELVIN_PRIMITIVE<0x97> -> NV097_SET_TRANSFORM_PROGRAM[0]<0xB00> (0x0)

_LOAD = r"NV097_SET_TRANSFORM_PROGRAM_LOAD<0x1E9C>"
_DATA = r"NV097_SET_TRANSFORM_PROGRAM\[\d+]<" + _HEX_STRING + r">"

_ENTRY_RE = re.compile(_PREFIX + r"(" + _LOAD + r"|" + _DATA + r")\s*\(("    + _HEX_STRING
 + r")\)")


def _process_shader(description: str, values: List[int]):
    print(description)

    shader = []
    for slot in range(len(values) // 4):
        offset = slot * 4
        ins_a = values[offset]
        ins_b = values[offset + 1]
        ins_c = values[offset + 2]
        ins_d = values[offset + 3]
        shader.append((ins_a, ins_b, ins_c, ins_d))
        
    source = nv2avsh.disassemble.disassemble(shader, False)
    print("\n".join(source))
    print("\n")

    
def _main(args):
    shaders = []

    source_file = os.path.abspath(os.path.expanduser(args.source_file))
    with open(source_file, encoding="utf-8") as infile:
        content = infile.read()

    accumulator = []
    last_slot = 0
    for match in re.finditer(_ENTRY_RE, content):
        command = match.group(1)
        value = int(match.group(2), 16)
        if command.startswith("NV097_SET_TRANSFORM_PROGRAM_LOAD"):
            if accumulator:
                shaders.append(accumulator)
            accumulator = [f"Shader at 0x{value:x} ({value})"]
            continue
        accumulator.append(value)

    if accumulator:
        shaders.append(accumulator)

    for shader in shaders:
        _process_shader(shader[0], shader[1:])


if __name__ == "__main__":

    def _parse_args():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "source_file",
            help="PGRAPH trace containing the xemu vertex shader(s) to process.",
        )

        return parser.parse_args()

    sys.exit(_main(_parse_args()))
