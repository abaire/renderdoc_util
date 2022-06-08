#!/usr/bin/env python3

"""Converts xemu vertex shaders to nv2a-vsh assembly."""

import argparse
import os
import re
import sys
from typing import List

import nv2avsh


_HEX_STRING = r"0x[0-9a-fA-F]+"
#  /* Slot 0: 0x00000000 0x0046AC00 0x69FEB800 0x28A00000 */
_SLOT_RE = re.compile(
    r"\s*/\*\s+Slot\s+(\d+):\s+("
    + _HEX_STRING
    + r")\s+("
    + _HEX_STRING
    + r")\s+("
    + _HEX_STRING
    + r")\s+("
    + _HEX_STRING
    + r")"
)


def _main(args):
    shaders = set()

    source_file = os.path.abspath(os.path.expanduser(args.source_file))
    with open(source_file, encoding="utf-8") as infile:
        content = infile.read()

    accumulator = []
    last_slot = 0
    for match in re.finditer(_SLOT_RE, content):
        slot = int(match.group(1))
        ins_a = int(match.group(2), 16)
        ins_b = int(match.group(3), 16)
        ins_c = int(match.group(4), 16)
        ins_d = int(match.group(5), 16)

        if slot == 0:
            if accumulator:
                shaders.add(tuple(accumulator))
                accumulator = []
        elif slot != last_slot + 1:
            raise Exception(
                f"Missing instruction (expected slot {last_slot + 1} but found {slot})"
            )

        accumulator.append((ins_a, ins_b, ins_c, ins_d))
        last_slot = slot

    if accumulator:
        shaders.add(tuple(accumulator))

    for index, shader in enumerate(shaders):
        print(f"; Shader {args.source_file} - {index+1}")
        source = nv2avsh.disassemble.disassemble(shader, False)
        print("\n".join(source))
        print("\n")


if __name__ == "__main__":

    def _parse_args():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "source_file",
            help="File containing the xemu vertex shader(s) to process.",
        )

        return parser.parse_args()

    sys.exit(_main(_parse_args()))
