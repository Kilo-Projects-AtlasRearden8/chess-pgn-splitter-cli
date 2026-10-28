"""PGN Splitter - split multi-game PGN files into individual game files."""

from .core import Game, PGNError, default_output_name, format_game, parse_games, split_pgn, write_games

__all__ = [
    "Game",
    "PGNError",
    "default_output_name",
    "format_game",
    "parse_games",
    "split_pgn",
    "write_games",
]

__version__ = "1.0.0"
