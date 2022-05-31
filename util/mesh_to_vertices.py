#!/usr/bin/env python3

"""Uses diff to replace duplicate textures with symlinks."""

import argparse
from contextlib import redirect_stdout
import csv
import os
from typing import List
import sys

_COMPONENTS = [".x", ".y", ".z", ".w"]

def _print_vertex(info: dict):
    info = {k.strip(): v for k, v in info.items()}

    def _extract(prefix: str) -> List[str]:
        if f"{prefix}.x" not in info:
            return None

        ret = []
        for key in [prefix + c for c in _COMPONENTS]:
            if key not in info:
                break
            ret.append(info[key])
        return ret

    def _process_input(register: str, setter: str):
        values = _extract(register)
        if not values:
            return
        params = ", ".join(values)
        print(f"  host_.{setter}({params});")
    
    _process_input("v1", "SetWeight")
    _process_input("v2", "SetNormal")
    _process_input("v3", "SetDiffuse")
    _process_input("v4", "SetSpecular")
    _process_input("v5", "SetFogCoord")
    _process_input("v6", "SetPointSize")
    _process_input("v7", "SetBackDiffuse")
    _process_input("v8", "SetBackSpecular")
    _process_input("v9", "SetTexCoord0")
    _process_input("v10", "SetTexCoord1")
    _process_input("v11", "SetTexCoord2")
    _process_input("v12", "SetTexCoord3")
    
    _process_input("v0", "SetVertex")
            

def _process_file(filename):
    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",", quotechar="|")
        for row in reader:
            _print_vertex(row)
            print("")


def _main(args):
    args.input = os.path.realpath(os.path.expanduser(args.input))

    if not args.output:
        _process_file(args.input)
        return 0

    output = os.path.realpath(os.path.expanduser(args.output))
    with open(output, "w") as out_file:
        with redirect_stdout(out_file):
            _process_file(args.input)


if __name__ == "__main__":

    def _parse_args():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "input",
            metavar="csv_file",
            help="Exported CSV from renderdoc's mesh viewer.",
        )

        parser.add_argument(
            "output",
            nargs="?",
            help="File to write to instead of stdout.",
        )

        return parser.parse_args()

    sys.exit(_main(_parse_args()))
