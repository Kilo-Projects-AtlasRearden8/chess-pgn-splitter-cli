# STATUS

## What was built

A Python CLI that splits multi-game PGN (Portable Game Notation) chess files
into individual game files with clean headers and validation.

Package: `pgn_splitter/`
- `__init__.py` — public API and version
- `core.py` — PGN parser, validation, header formatting, and file writing
- `cli.py` — command-line interface (`python -m pgn_splitter`)
- `__main__.py` — module entry point

Tests: `tests/test_pgn_splitter.py` — 20 tests covering parsing, splitting,
validation, header ordering/format, output naming, and file writing.

Other files: `LICENSE` (MIT), `README.md`, `.gitignore`.

## How to run it

```bash
# From the project folder
python3 -m pgn_splitter <input.pgn> [output_dir]

# Example
python3 -m pgn_splitter tournament.pgn split_games
```

Options: `--no-validate`, `--overwrite`, `--dry-run`, `--quiet`.

Run tests:

```bash
python3 -m pytest
```

## Verification results

- `python3 -m pytest` — 20 passed, 0 failed
- End-to-end CLI run on a 2-game sample PGN wrote 2 clean output files with
  correctly ordered headers and normalized line endings
- CRLF line endings parse correctly
- MIT `LICENSE` contains the exact copyright line:
  `Copyright (c) 2026 Asdale Dynamics, LLC`
- `README.md` credits Asdale Dynamics, LLC

No `.github/workflows` files were added. No git remote, no push, no publish.

## Known gaps

- No `setup.py`/`pyproject.toml` for pip installation (runs as a module only)
- No code formatter/linter configuration (ruff/black) wired in
- Validation warnings are advisory; invalid games are still written (by design)
- Output filename collisions are only avoided with `--overwrite`
