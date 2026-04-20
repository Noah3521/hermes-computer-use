"""Unit tests for keyboard-name normalisation.

The core symptom these protect against: xdotool prints `No such key name
'Backspace'. Ignoring it.` to stderr AND returns exit code 0, so the silent-
failure path is load-bearing. Every alias below was a user-facing bug at
some point."""
from __future__ import annotations

import pytest

from hermes_computer_use.server import _normalize_key


@pytest.mark.parametrize("raw, expected", [
    # Single-press
    ("Backspace", "BackSpace"),
    ("backspace", "BackSpace"),
    ("BACKSPACE", "BackSpace"),
    ("Enter", "Return"),
    ("enter", "Return"),
    ("return", "Return"),
    ("Space", "space"),
    ("ESC", "Escape"),
    ("PageUp", "Page_Up"),
    ("page_up", "Page_Up"),
    ("pgdn", "Page_Down"),

    # Chords — '+' separator
    ("ctrl+a", "ctrl+a"),
    ("Ctrl+A", "ctrl+A"),
    ("CTRL+a", "ctrl+a"),
    ("ctrl+shift+t", "ctrl+shift+t"),
    ("ctrl+Backspace", "ctrl+BackSpace"),

    # Chords — '-' separator (common in Emacs/Mac docs)
    ("ctrl-a", "ctrl+a"),
    ("cmd-shift-z", "super+shift+z"),

    # Platform ergonomics — cmd/meta/win/windows → super
    ("cmd+c", "super+c"),
    ("command+v", "super+v"),
    ("meta+l", "super+l"),
    ("win+r", "super+r"),
    ("windows+e", "super+e"),

    # Mac option = alt
    ("option+Left", "alt+Left"),
    ("opt+Right", "alt+Right"),

    # Single letters / punctuation pass-through
    ("a", "a"),
    ("A", "A"),
    ("1", "1"),
    ("/", "/"),

    # Already-canonical form unchanged
    ("BackSpace", "BackSpace"),
    ("Return", "Return"),
    ("super+F4", "super+F4"),
])
def test_key_normalization(raw: str, expected: str) -> None:
    assert _normalize_key(raw) == expected


def test_empty_string_passthrough() -> None:
    assert _normalize_key("") == ""
