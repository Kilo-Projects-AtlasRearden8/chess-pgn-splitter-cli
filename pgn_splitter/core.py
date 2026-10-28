"""Core PGN parsing, validation, and splitting logic.

A PGN (Portable Game Notation) file stores one or more chess games. Each game
starts with tag pairs like ``[Event "..."]`` followed by the movetext. Games are
usually separated by blank lines. This module parses a multi-game PGN file into
individual :class:`Game` objects, validates headers and results, and writes each
game out as a clean standalone PGN file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Standard result values in PGN.
VALID_RESULTS = frozenset({"1-0", "0-1", "1/2-1/2", "*"})

# The seven-tag roster, in the conventional output order.
ROSTER_TAGS = ("Event", "Site", "Date", "Round", "White", "Black", "Result")

# A well-formed tag line: [TagName "value"] with optional escaped quotes.
TAG_LINE_RE = re.compile(r'^\[([A-Za-z][A-Za-z0-9_]*)\s+"((?:[^"\\]|\\.)*)"\]\s*$')


@dataclass
class Game:
    """A single parsed PGN game."""

    tags: dict[str, str] = field(default_factory=dict)
    movetext: str = ""
    line_start: int = 0
    line_end: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def result(self) -> str:
        """Value of the Result tag, or empty string when absent."""
        return self.tags.get("Result", "")

    @property
    def is_valid(self) -> bool:
        """True when no hard validation errors were recorded."""
        return not self.errors


class PGNError(Exception):
    """Raised for unrecoverable PGN processing problems."""


def parse_games(text: str) -> list[Game]:
    """Split PGN text into a list of :class:`Game` objects.

    A game is a tag section followed by a movetext section. The blank line
    between tags and movetext belongs to the same game; games are separated
    when a blank line follows movetext or when a new tag line appears after
    movetext has begun.
    """
    lines = text.splitlines()
    games: list[Game] = []
    current: dict | None = None
    section: str | None = None  # "tags" | "moves"

    def start_game(line_no: int) -> dict:
        return {
            "tags": {},
            "moves": [],
            "start": line_no,
            "end": line_no,
            "errors": [],
            "warnings": [],
        }

    def flush(game: dict | None) -> None:
        if game is None:
            return
        g = Game(line_start=game["start"], line_end=game["end"])
        for name, value in game["tags"].items():
            g.tags[name] = value
        g.errors.extend(game["errors"])
        g.warnings.extend(game["warnings"])
        g.movetext = " ".join(game["moves"]).strip()
        _validate(g)
        games.append(g)

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped == "":
            if section == "tags":
                section = "moves"
            elif section == "moves":
                flush(current)
                current = None
                section = None
            continue

        if stripped.startswith("["):
            match = TAG_LINE_RE.match(stripped)
            if match:
                if section == "moves":
                    flush(current)
                    current = None
                if current is None:
                    current = start_game(idx)
                    section = "tags"
                name, value = match.group(1), match.group(2)
                if name in current["tags"]:
                    current["warnings"].append(f"duplicate tag {name!r}")
                current["tags"][name] = value
                current["end"] = idx
                section = "tags"
            else:
                if current is None:
                    current = start_game(idx)
                    section = "tags"
                current["errors"].append(
                    f"line {idx}: malformed tag line: {stripped!r}"
                )
                current["end"] = idx
            continue

        # Movetext line.
        if current is None:
            current = start_game(idx)
            section = "moves"
        elif section == "tags":
            section = "moves"
        current["moves"].append(stripped)
        current["end"] = idx

    flush(current)
    return games


def _validate(game: Game) -> None:
    """Run validation checks on a parsed game, recording errors and warnings."""
    result = game.tags.get("Result")

    if result is None:
        game.warnings.append("missing Result tag")
    elif result not in VALID_RESULTS:
        game.errors.append(f'invalid Result value: {result!r}')

    if result in ("1-0", "0-1", "1/2-1/2") and game.movetext:
        if not game.movetext.rstrip().endswith(result):
            game.warnings.append(
                f"movetext does not end with declared result {result}"
            )


def split_pgn(text: str) -> list[Game]:
    """Public alias for :func:`parse_games`."""
    return parse_games(text)


def sanitize_filename(value: str, fallback: str = "unknown") -> str:
    """Turn a tag value into a safe filesystem-friendly name component."""
    cleaned = re.sub(r'[^\w\s-]', "", value).strip()
    cleaned = re.sub(r"[\s-]+", "_", cleaned)
    return cleaned or fallback


def default_output_name(game: Game, index: int) -> str:
    """Build a default output filename from a game's tags."""
    event = sanitize_filename(game.tags.get("Event", ""), "untitled")
    white = sanitize_filename(game.tags.get("White", ""), "white")
    black = sanitize_filename(game.tags.get("Black", ""), "black")
    date = sanitize_filename(game.tags.get("Date", "").replace(".", ""), "nd")
    return f"{index:03d}_{date}_{event}_{white}_vs_{black}.pgn"


def format_game(game: Game) -> str:
    """Render a game with clean, normalized headers.

    The seven-tag roster is written first (Event, Site, Date, Round, White,
    Black, Result), followed by any extra tags in alphabetical order. A blank
    line separates headers from movetext.
    """
    ordered: list[tuple[str, str]] = []
    for tag in ROSTER_TAGS:
        if tag in game.tags:
            ordered.append((tag, game.tags[tag]))
    for tag in sorted(game.tags):
        if tag not in ROSTER_TAGS:
            ordered.append((tag, game.tags[tag]))

    header = "\n".join(f'[{name} "{value}"]' for name, value in ordered)
    parts = [header]
    if game.movetext:
        parts.append("")
        parts.append(game.movetext)
    return "\n".join(parts) + "\n"


def write_games(
    games: list[Game],
    output_dir: str | Path,
    name_func=default_output_name,
    overwrite: bool = False,
) -> list[Path]:
    """Write each game to its own PGN file in ``output_dir``.

    Returns the list of written file paths. Raises :exc:`FileExistsError` if a
    target file already exists and ``overwrite`` is false.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for index, game in enumerate(games, start=1):
        target = output_dir / name_func(game, index)
        if target.exists() and not overwrite:
            raise FileExistsError(f"output file already exists: {target}")
        target.write_text(format_game(game), encoding="utf-8")
        written.append(target)
    return written
