# PGN Splitter CLI

Split multi-game PGN (Portable Game Notation) chess files into individual game
files with clean headers and validation. A small, tested, local-first command
line tool published by **Asdale Dynamics, LLC** — a fan project with no game
assets included.

## Who this is for

Chess players, club organizers, and anyone working with PGN files who wants to
turn one big multi-game file into one tidy file per game. No chess engine,
no internet connection, no account required — just Python 3 and your PGN file.

## What it does

Reads a PGN file that contains many games, parses each game's tag pairs and
movetext, validates the headers and results, and writes one clean PGN file per
game into an output directory.

## Installation

No installation required. Run with Python 3:

```bash
python3 -m pgn_splitter input.pgn split_games
```

Or run the module file directly:

```bash
python3 pgn_splitter/cli.py input.pgn split_games
```

## Step by step

1. Put your multi-game PGN file in a folder (for example, `tournament.pgn`).
2. Run the splitter:

   ```bash
   python3 -m pgn_splitter tournament.pgn split_games
   ```

3. Open the `split_games` folder — you'll find one clean PGN file per game,
   named from the game's tags (for example:
   `001_20260201_Club_Night_Alice_vs_Bob.pgn`).

## Usage

```
pgn-splitter INPUT.pgn [OUTPUT_DIR] [options]
```

- `INPUT.pgn` — multi-game PGN file to split (required)
- `OUTPUT_DIR` — directory for the split game files (default: `split_games`)

Options:

- `--no-validate` — skip validation (validation runs by default)
- `--overwrite` — replace existing output files
- `--dry-run` — parse and report games without writing files
- `--quiet` — print only the summary

## Output format

Every split game gets clean, normalized headers:

```
[Event "Club Night"]
[Site "Home"]
[Date "2026.02.01"]
[Round "1"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 1-0
```

The seven-tag roster (Event, Site, Date, Round, White, Black, Result) is
written first, followed by any extra tags in alphabetical order. Header lines
and line endings are normalized.

## Validation

The splitter checks:

- Each tag line is well-formed (`[TagName "value"]`)
- The `Result` tag uses a valid value (`1-0`, `0-1`, `1/2-1/2`, `*`)
- The movetext ends with the declared result

Games with warnings are still written; problems are reported but never
silently dropped.

## Tests

```bash
python3 -m pytest
```

All tests live in `tests/test_pgn_splitter.py` and cover parsing, splitting,
validation, header formatting, output naming, and file writing.

## Credits

Built and maintained by **Asdale Dynamics, LLC** (Indiana, formed October
2026) — beginner-friendly AI education, books, and practical open-source
tools. Fan project; no game assets included.

## License

MIT License. Copyright (c) 2026 Asdale Dynamics, LLC. See `LICENSE`.
