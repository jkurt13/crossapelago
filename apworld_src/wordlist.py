"""Word packs.

Packs live in words/<pack>.txt as `ANSWER|tier|clue|hard clue`. They are read with pkgutil so they
load from inside a zipped .apworld too.
"""
from __future__ import annotations

import pkgutil
from dataclasses import dataclass
from functools import lru_cache

PACKS = ("general", "gaming", "movies", "sports")
MIN_LEN, MAX_LEN = 3, 10


@dataclass(frozen=True)
class Entry:
    answer: str
    tier: int          # 1 easy, 2 medium, 3 hard
    clue: str
    hard_clue: str     # falls back to clue
    pack: str


def parse_pack(name: str, text: str) -> tuple[list[Entry], list[str]]:
    """Returns (entries, problems). Bad lines are skipped and reported."""
    entries: list[Entry] = []
    problems: list[str] = []
    seen: set[str] = set()
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            problems.append(f"{name}:{n}: expected ANSWER|tier|clue")
            continue
        answer, tier, clue = parts[0].upper(), parts[1], parts[2]
        hard = parts[3] if len(parts) > 3 and parts[3] else clue
        if not answer.isalpha() or not answer.isascii():
            problems.append(f"{name}:{n}: {answer!r} must be letters A-Z only")
            continue
        if not MIN_LEN <= len(answer) <= MAX_LEN:
            problems.append(f"{name}:{n}: {answer} must be {MIN_LEN}-{MAX_LEN} letters")
            continue
        if tier not in ("1", "2", "3"):
            problems.append(f"{name}:{n}: {answer} tier must be 1, 2 or 3")
            continue
        if answer in seen:
            problems.append(f"{name}:{n}: duplicate {answer}")
            continue
        if not clue:
            problems.append(f"{name}:{n}: {answer} has no clue")
            continue
        seen.add(answer)
        entries.append(Entry(answer, int(tier), clue, hard, name))
    return entries, problems


@lru_cache(maxsize=None)
def load_pack(name: str) -> tuple[Entry, ...]:
    data = pkgutil.get_data(__package__, f"words/{name}.txt")
    if data is None:
        return ()
    entries, _ = parse_pack(name, data.decode("utf-8"))
    return tuple(entries)


def load_words() -> list[tuple[str, str]]:
    """Back-compat helper: every General answer with its normal clue."""
    return [(e.answer, e.clue) for e in load_pack("general")]
