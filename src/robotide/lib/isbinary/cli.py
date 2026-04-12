
import argparse
from typing import Optional, Sequence

from .check import is_binary_file


def main(args: Optional[Sequence[str]] = None) -> None:
    if args is None:  # pragma: no cover
        import sys

        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Check if a file is binary or not.")

    parser.add_argument("filename", help="Path to a file that should be checked.")

    parsed_args = parser.parse_args(args)

    print("true" if is_binary_file(parsed_args.filename) else "false")


__all__ = ("main",)
