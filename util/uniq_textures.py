#!/usr/bin/env python3

"""Uses diff to replace duplicate textures with symlinks."""

import argparse
import collections
import os
import re
import subprocess
import sys

Texture = collections.namedtuple("Texture", ["full_path", "size"])

_TEXTURE_RE = re.compile(r"EID_\d+_tex\d+-.+")


def _main(args):
    if not args.path:
        args.path = os.getcwd()
    else:
        args.path = os.path.abspath(os.path.expanduser(args.path))

    textures = set()

    def _check_identical(a: str, b: str) -> bool:
        ret = subprocess.call(
            [args.difftool, a, b], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return ret == 0

    for entry in os.scandir(args.path):
        if entry.is_symlink() or entry.is_dir():
            continue

        match = _TEXTURE_RE.match(entry.name)
        if not match:
            continue

        parent = ""
        full_path = os.path.join(args.path, entry.name)
        size = entry.stat().st_size

        for texture in textures:
            if texture.size != size:
                continue
            if _check_identical(texture.full_path, full_path):
                parent = texture
                break

        if not parent:
            print(entry.name)
            textures.add(Texture(full_path, size))
        else:
            if args.no_change:
                print(f"Duplicate {full_path} == {parent.full_path}")
            else:
                os.unlink(full_path)
                if not args.delete:
                    os.symlink(parent.full_path, full_path)


if __name__ == "__main__":

    def _parse_args():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "path",
            nargs="?",
            metavar="path_to_scan",
            help="Source file to assemble.",
        )

        parser.add_argument(
            "-d",
            "--difftool",
            metavar="path_to_diff_tool",
            default="diff",
            help="Override the `diff` binary.",
        )

        parser.add_argument(
            "-n",
            "--no-change",
            action="store_true",
            help="Just print the unique filenames, do not symlink duplicates.",
        )

        parser.add_argument(
            "--delete",
            action="store_true",
            help="Just delete duplicated files, do not symlink to the original.",
        )

        return parser.parse_args()

    sys.exit(_main(_parse_args()))
