"""Seeded freeform crossword generator.

Places words one at a time so each new word crosses at least one existing word,
never touches other letters side-by-side, and stays inside a max bounding box.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

ACROSS, DOWN = "across", "down"


@dataclass
class Placed:
    answer: str
    clue: str
    row: int
    col: int
    direction: str
    number: int = 0

    def cells(self):
        dr, dc = (0, 1) if self.direction == ACROSS else (1, 0)
        for i, ch in enumerate(self.answer):
            yield self.row + dr * i, self.col + dc * i, ch


class _Grid:
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cells: dict[tuple[int, int], str] = {}
        self.owner: dict[tuple[int, int], set[str]] = {}  # directions occupying each cell
        self.min_r = self.max_r = self.min_c = self.max_c = 0

    def fits(self, answer: str, row: int, col: int, direction: str) -> int:
        """Returns number of crossings if the placement is valid, else -1."""
        dr, dc = (0, 1) if direction == ACROSS else (1, 0)
        pr, pc = dc, dr  # perpendicular offset
        n = len(answer)
        # bounding box check
        end_r, end_c = row + dr * (n - 1), col + dc * (n - 1)
        if (max(self.max_r, end_r) - min(self.min_r, row) + 1 > self.max_size or
                max(self.max_c, end_c) - min(self.min_c, col) + 1 > self.max_size):
            return -1
        # cells directly before and after the word must be empty
        if (row - dr, col - dc) in self.cells or (end_r + dr, end_c + dc) in self.cells:
            return -1
        crossings = 0
        for i, ch in enumerate(answer):
            r, c = row + dr * i, col + dc * i
            existing = self.cells.get((r, c))
            if existing is not None:
                if existing != ch or direction in self.owner[(r, c)]:
                    return -1
                crossings += 1
            else:
                # new letter: no neighbours on either perpendicular side
                if (r + pr, c + pc) in self.cells or (r - pr, c - pc) in self.cells:
                    return -1
        return crossings if crossings > 0 else -1

    def place(self, p: Placed):
        for r, c, ch in p.cells():
            self.cells[(r, c)] = ch
            self.owner.setdefault((r, c), set()).add(p.direction)
            self.min_r, self.max_r = min(self.min_r, r), max(self.max_r, r)
            self.min_c, self.max_c = min(self.min_c, c), max(self.max_c, c)


def _try_build(words, target, max_size, rng: random.Random) -> list[Placed]:
    pool = words[:]
    rng.shuffle(pool)
    # start with a longish word
    pool.sort(key=lambda w: -len(w[0]) + rng.random() * 4)
    first = pool.pop(0)
    grid = _Grid(max_size)
    placed = [Placed(first[0], first[1], 0, 0, ACROSS)]
    grid.place(placed[0])
    rng.shuffle(pool)

    used = {first[0]}
    stalls = 0
    idx = 0
    while len(placed) < target and stalls < len(pool):
        answer, clue = pool[idx % len(pool)]
        idx += 1
        if answer in used:
            stalls += 1
            continue
        options = []
        for (r, c), ch in grid.cells.items():
            for i, a in enumerate(answer):
                if a != ch:
                    continue
                for direction in (ACROSS, DOWN):
                    sr, sc = (r, c - i) if direction == ACROSS else (r - i, c)
                    x = grid.fits(answer, sr, sc, direction)
                    if x > 0:
                        options.append((x, sr, sc, direction))
        if not options:
            stalls += 1
            continue
        stalls = 0
        best = max(o[0] for o in options)
        # favour more crossings for a denser grid, but keep some variety
        choices = [o for o in options if o[0] == best] if rng.random() < 0.7 else options
        _, sr, sc, direction = rng.choice(choices)
        p = Placed(answer, clue, sr, sc, direction)
        grid.place(p)
        placed.append(p)
        used.add(answer)

    # normalise coordinates so the top-left is (0, 0)
    for p in placed:
        p.row -= grid.min_r
        p.col -= grid.min_c
    return placed


def number_words(placed: list[Placed]) -> None:
    starts = sorted({(p.row, p.col) for p in placed})
    numbers = {pos: i + 1 for i, pos in enumerate(starts)}
    for p in placed:
        p.number = numbers[(p.row, p.col)]
    placed.sort(key=lambda p: (p.direction != ACROSS, p.number))


def generate(words: list[tuple[str, str]], target: int, rng: random.Random,
             max_size: int = 21, attempts: int = 40) -> list[Placed]:
    best: list[Placed] = []
    for _ in range(attempts):
        result = _try_build(words, target, max_size, rng)
        if len(result) > len(best):
            best = result
        if len(best) >= target:
            break
    number_words(best)
    return best
