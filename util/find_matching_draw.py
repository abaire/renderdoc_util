#!/usr/bin/env python3

import collections
import os
import re
import sys

Draw = collections.namedtuple("Draw", ["color", "depth", "textures", "num_textures"])

_EID_RE = re.compile(r"EID (\d+)\s*(.*)")
_SAMPLER_RE = re.compile(r"uses (.+)\sin sampler (\d+)")


def _parse_data(filename):
    with open(filename, encoding="utf-8") as infile:
        data = infile.read()

    draws = collections.defaultdict(list)
    for match in re.finditer(_EID_RE, data):
        draws[match.group(1)].append(match.group(2))

    formatted = {}
    for eid, values in draws.items():
        color = None
        depth = None
        textures = [None, None, None, None]

        for value in values:
            match = _SAMPLER_RE.match(value)
            if match:
                index = int(match.group(2))
                textures[index] = value[5:-13]  # Skip 'uses' and 'in sampler x'
                continue

            if value.startswith("writes color to"):
                color = value[15:]
                continue

            if value.startswith("writes depth to"):
                depth = value[15:]
                continue

            raise Exception(f'Unknown entry: "{value}"')

        formatted[eid] = Draw(
            color, depth, textures, sum(x is not None for x in textures)
        )

    return formatted


def _main():
    filename = os.path.expanduser(sys.argv[1])
    draws = _parse_data(filename)

    # TODO: Parameterize.
    for eid, draw in draws.items():
        if draw.num_textures < 4:
            continue
        print(f"{eid}: {draw}")
        print("")


if __name__ == "__main__":
    _main()
