from __future__ import annotations

import sys

from .cli import build_parser, run_cli


def main() -> int:
    """Application entry point."""
    parser = build_parser()
    try:
        args = parser.parse_args()
    except SystemExit:
        raise
    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
