"""

"""
from __future__ import annotations

import sys


USAGE = f"Usage: {sys.argv[0]} ..."
MAXARGS = 1
MINARGS = 1


def main(args: list[str]):
    print(args)


if __name__ == "__main__":
    if not (MINARGS <= len(sys.argv) <= MAXARGS):
        print(USAGE)
        sys.exit(1)

    sys.argv.pop(0)
    main(sys.argv)
