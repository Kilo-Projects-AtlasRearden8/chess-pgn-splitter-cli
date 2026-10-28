"""Tests for PGN parsing, validation, and splitting."""

from __future__ import annotations

from pgn_splitter.cli import build_parser
from pgn_splitter.core import (
    Game,
    ROSTER_TAGS,
    VALID_RESULTS,
    default_output_name,
    format_game,
    parse_games,
    sanitize_filename,
    split_pgn,
    write_games,
)

SINGLE_GAME = """[Event "Test Event"]
[Site "Test City"]
[Date "2026.01.01"]
[Round "1"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 1-0
"""

MULTI_GAME = """[Event "Club Night"]
[Site "Home"]
[Date "2026.02.01"]
[Round "1"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 1-0

[Event "Club Night"]
[Site "Home"]
[Date "2026.02.01"]
[Round "2"]
[White "Carol"]
[Black "Dan"]
[Result "0-1"]

1. d4 d5 0-1
"""


def test_parse_single_game():
    games = parse_games(SINGLE_GAME)
    assert len(games) == 1
    game = games[0]
    assert game.tags["Event"] == "Test Event"
    assert game.tags["White"] == "Alice"
    assert game.tags["Black"] == "Bob"
    assert game.result == "1-0"
    assert "1. e4 e5 2. Nf3 Nc6" in game.movetext
    assert game.is_valid


def test_parse_multiple_games():
    games = parse_games(MULTI_GAME)
    assert len(games) == 2
    assert games[0].tags["White"] == "Alice"
    assert games[1].tags["White"] == "Carol"
    assert games[1].result == "0-1"


def test_split_pgn_alias():
    assert split_pgn(MULTI_GAME) == parse_games(MULTI_GAME)


def test_malformed_tag_is_error():
    text = '[Bad Tag without quotes]\n[White "Alice"]\n[Result "*"]\n\n*'
    games = parse_games(text)
    assert len(games) == 1
    assert not games[0].is_valid
    assert any("malformed tag line" in err for err in games[0].errors)


def test_invalid_result_is_error():
    text = '[White "Alice"]\n[Black "Bob"]\n[Result "2-0"]\n\n*'
    games = parse_games(text)
    assert not games[0].is_valid
    assert any("invalid Result value" in err for err in games[0].errors)


def test_missing_result_is_warning():
    text = '[White "Alice"]\n[Black "Bob"]\n\n*'
    games = parse_games(text)
    assert games[0].is_valid  # missing result is a warning, not an error
    assert any("missing Result tag" in w for w in games[0].warnings)


def test_valid_results():
    for result in ("1-0", "0-1", "1/2-1/2", "*"):
        assert result in VALID_RESULTS


def test_result_mismatch_is_warning():
    text = '[White "Alice"]\n[Black "Bob"]\n[Result "1-0"]\n\n1. e4 e5 0-1'
    games = parse_games(text)
    assert any("does not end with declared result" in w for w in games[0].warnings)


def test_format_game_roster_order():
    game = Game()
    game.tags = {
        "Result": "1-0",
        "White": "Alice",
        "Event": "Club",
        "Annotator": "Kilo",
    }
    game.movetext = "1. e4 e5 1-0"
    output = format_game(game)
    lines = output.splitlines()
    assert lines[0] == '[Event "Club"]'
    assert lines[1] == '[White "Alice"]'
    assert lines[2] == '[Result "1-0"]'
    assert lines[3] == '[Annotator "Kilo"]'
    assert lines[4] == ""
    assert lines[5] == "1. e4 e5 1-0"
    assert output.endswith("\n")


def test_format_game_extra_tags_alphabetical():
    game = Game()
    game.tags = {"Event": "E", "White": "W", "Black": "B", "Result": "1-0", "Zebra": "z", "Alpha": "a"}
    output = format_game(game)
    lines = output.splitlines()
    # Roster first, then extras alphabetically: Event, White, Black, Result,
    # then Alpha, Zebra
    assert lines[4] == '[Alpha "a"]'
    assert lines[5] == '[Zebra "z"]'


def test_sanitize_filename():
    assert sanitize_filename("Spring Open 2026!") == "Spring_Open_2026"
    assert sanitize_filename("") == "unknown"
    assert sanitize_filename("   ", fallback="x") == "x"


def test_default_output_name():
    game = Game()
    game.tags = {
        "Event": "Club Night",
        "Date": "2026.02.01",
        "White": "Alice",
        "Black": "Bob",
        "Result": "1-0",
    }
    name = default_output_name(game, 5)
    assert name.startswith("005_20260201_Club_Night_Alice_vs_Bob.pgn")


def test_write_games(tmp_path):
    games = parse_games(MULTI_GAME)
    written = write_games(games, tmp_path)
    assert len(written) == 2
    for path in written:
        assert path.is_file()
        content = path.read_text(encoding="utf-8")
        assert content.startswith("[Event ")
        assert "\n\n1." in content or content.count("\n\n") >= 1


def test_write_games_creates_directory(tmp_path):
    target = tmp_path / "nested" / "out"
    games = parse_games(SINGLE_GAME)
    written = write_games(games, target)
    assert len(written) == 1
    assert written[0].is_file()


def test_write_games_refuses_existing_without_overwrite(tmp_path):
    games = parse_games(SINGLE_GAME)
    write_games(games, tmp_path)
    try:
        write_games(games, tmp_path)
    except FileExistsError:
        return
    raise AssertionError("expected FileExistsError")


def test_write_games_overwrite(tmp_path):
    games = parse_games(SINGLE_GAME)
    write_games(games, tmp_path)
    write_games(games, tmp_path, overwrite=True)
    assert True


def test_crlf_line_endings_parsed():
    text = SINGLE_GAME.replace("\n", "\r\n")
    games = parse_games(text)
    assert len(games) == 1
    assert games[0].is_valid


def test_empty_input_yields_no_games():
    assert parse_games("") == []
    assert parse_games("\n\n\n") == []


def test_game_without_tags_is_movetext_only():
    text = "1. e4 e5 2. Nf3 *\n"
    games = parse_games(text)
    assert len(games) == 1
    assert games[0].tags == {}
    assert games[0].movetext == "1. e4 e5 2. Nf3 *"


def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["input.pgn"])
    assert args.input == __import__("pathlib").Path("input.pgn")
    assert args.output_dir == __import__("pathlib").Path("split_games")
    assert args.no_validate is False
    assert args.overwrite is False
    assert args.dry_run is False
