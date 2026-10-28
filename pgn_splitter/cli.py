"""Command-line interface for the PGN splitter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import PGNError, default_output_name, parse_games, sanitize_filename, write_games

PROG_NAME = "pgn-splitter"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description="Split a multi-game PGN file into individual game files.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the multi-game PGN file to split.",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        nargs="?",
        default=Path("split_games"),
        help="Directory for the split game files (default: split_games).",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation of parsed games (validation runs by default).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report games without writing any files.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-game reporting; print only the summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.input.is_file():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        text = args.input.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.input}: {exc}", file=sys.stderr)
        return 2

    try:
        games = parse_games(text)
    except PGNError as exc:
        print(f"error: failed to parse PGN: {exc}", file=sys.stderr)
        return 2

    if not games:
        print(f"no games found in {args.input}")
        return 0

    if not args.quiet:
        print(f"found {len(games)} game(s) in {args.input}")
        for index, game in enumerate(games, start=1):
            status = "valid" if game.is_valid else "invalid"
            issues = "; ".join(game.errors + game.warnings)
            tag_line = f'[{game.tags.get("White", "?")}] vs [{game.tags.get("Black", "?")}]'
            print(
                f"  {index:03d}. {status}  {tag_line}  "
                f'result={game.result or "-"}'
                + (f"  ({issues})" if issues else "")
            )

    if args.dry_run:
        print("dry run: no files written")
        return 0

    try:
        written = write_games(
            games,
            args.output_dir,
            name_func=default_output_name,
            overwrite=args.overwrite,
        )
    except FileExistsError as exc:
        print(f"error: {exc} (use --overwrite to replace)", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot write to {args.output_dir}: {exc}", file=sys.stderr)
        return 2

    invalid = sum(1 for game in games if not game.is_valid)
    print(
        f"wrote {len(written)} game file(s) to {args.output_dir}"
        + (f" ({invalid} game(s) had validation issues)" if invalid else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
