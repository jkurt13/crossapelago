from __future__ import annotations

from typing import Any, Mapping

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World

from .generator import ACROSS, Placed, generate
from .options import CrosswordOptions, Difficulty, PuzzleSize, SquareChecks, StartingLetters
from .wordlist import Entry, load_pack

GAME = "Crossword Randomizer"
BASE_ID = 7_654_300_000
MAX_NUMBER = 150

# ---- ID scheme (keep in sync with the web client) --------------------------
# Items:     Letter A-Z            BASE+1 .. BASE+26
#            "N Across Clue"       BASE+100+N
#            "N Down Clue"         BASE+300+N
#            Reveal Square         BASE+997   (useful, consumable)
#            Check Word            BASE+998   (useful, consumable)
#            Coffee Break          BASE+999   (junk filler)
#            Scramble/Eraser/Blackout/Sticky Key Trap  BASE+990..993
# Locations: "N Across"            BASE+1000+N
#            "N Down"              BASE+1300+N
#            "P% Solved"           BASE+9000+P  (P = 25, 50, 75, 100)
#            "Square R<row> C<col>" BASE+5000+row*50+col  (0-based row/col, grid max 25x25)
LETTERS = [chr(ord("A") + i) for i in range(26)]
REVEAL = "Reveal Square"
CHECK = "Check Word"
FILLER = "Coffee Break"
USEFUL_FILLER = (REVEAL, CHECK)
TRAPS = {"Scramble": "Scramble Trap", "Eraser": "Eraser Trap", "Blackout": "Blackout Trap", "Sticky Key": "Sticky Key Trap"}
MILESTONES = (25, 50, 75, 100)
GRID_MAX = 25
# puzzle_size -> (word count, max grid side)
SIZE_PRESETS = {
    PuzzleSize.option_small: (15, 13),
    PuzzleSize.option_medium: (25, 17),
    PuzzleSize.option_large: (40, 21),
    PuzzleSize.option_huge: (60, 25),
}
# difficulty -> (preferred tiers, fallback tiers)
DIFFICULTY_TIERS = {
    Difficulty.option_easy: ({1}, {2}),
    Difficulty.option_medium: ({1, 2}, {3}),
    Difficulty.option_hard: ({2, 3}, {1}),
}
MIN_THEME_SHARE = 100  # when mixing themes, each pack contributes at least this many candidates


def letter_item(ch: str) -> str:
    return f"Letter {ch}"


def clue_item(number: int, direction: str) -> str:
    return f"{number} {direction.capitalize()} Clue"


def word_location(number: int, direction: str) -> str:
    return f"{number} {direction.capitalize()}"


def milestone_location(pct: int) -> str:
    return f"{pct}% Solved"


def square_location(row: int, col: int) -> str:
    return f"Square R{row + 1} C{col + 1}"


def milestone_target(pct: int, total_words: int) -> int:
    return -(-pct * total_words // 100)  # ceil


item_name_to_id: dict[str, int] = {letter_item(ch): BASE_ID + 1 + i for i, ch in enumerate(LETTERS)}
location_name_to_id: dict[str, int] = {}
for n in range(1, MAX_NUMBER + 1):
    item_name_to_id[clue_item(n, "across")] = BASE_ID + 100 + n
    item_name_to_id[clue_item(n, "down")] = BASE_ID + 300 + n
    location_name_to_id[word_location(n, "across")] = BASE_ID + 1000 + n
    location_name_to_id[word_location(n, "down")] = BASE_ID + 1300 + n
item_name_to_id[REVEAL] = BASE_ID + 997
for _i, _trap in enumerate(TRAPS.values()):
    item_name_to_id[_trap] = BASE_ID + 990 + _i
item_name_to_id[CHECK] = BASE_ID + 998
item_name_to_id[FILLER] = BASE_ID + 999
for _pct in MILESTONES:
    location_name_to_id[milestone_location(_pct)] = BASE_ID + 9000 + _pct
for _r in range(GRID_MAX):
    for _c in range(GRID_MAX):
        location_name_to_id[square_location(_r, _c)] = BASE_ID + 5000 + _r * 50 + _c


class CrosswordItem(Item):
    game = GAME


class CrosswordLocation(Location):
    game = GAME


class CrosswordWeb(WebWorld):
    theme = "partyTime"
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "How to set up and play Crossword Randomizer.",
        "English",
        "setup_en.md",
        "setup/en",
        ["jkurt13"],
    )]


class CrosswordWorld(World):
    """A randomly generated crossword. Other players send you clues and letter keys;
    every word you solve sends out a check."""

    game = GAME
    web = CrosswordWeb()
    options_dataclass = CrosswordOptions
    options: CrosswordOptions
    item_name_to_id = item_name_to_id
    location_name_to_id = location_name_to_id
    item_name_groups = {
        "Letters": {letter_item(ch) for ch in LETTERS},
        "Clues": {n for n in item_name_to_id if n.endswith(" Clue")},
        "Tools": set(USEFUL_FILLER),
        "Traps": set(TRAPS.values()),
    }
    location_name_groups = {
        "Milestones": {milestone_location(p) for p in MILESTONES},
        "Squares": {n for n in location_name_to_id if n.startswith("Square ")},
    }
    origin_region_name = "Crossword"

    words: list[Placed]
    start_letters: set[str]
    start_clues: set[str]
    squares: list[tuple[int, int]]

    # ---- generation steps -------------------------------------------------
    def build_word_pools(self) -> list[list[tuple[str, str]]]:
        """Candidate pools, most preferred first. Later pools only get used if a puzzle can't be built
        from the earlier ones: preferred tiers of the chosen themes -> all tiers -> General as backup."""
        themes = sorted(self.options.themes.value) or ["General"]
        packs = [t.lower() for t in themes]
        preferred, fallback = DIFFICULTY_TIERS[self.options.difficulty.value]
        hard = self.options.difficulty == Difficulty.option_hard

        def pick(entries: list[Entry], tiers: set[int]) -> list[Entry]:
            return [e for e in entries if e.tier in tiers]

        # themed packs win duplicates over General (e.g. GOLF with a sports clue)
        seen: set[str] = set()
        by_pack: dict[str, list[Entry]] = {}
        for pack in sorted(packs, key=lambda p: p == "general"):
            by_pack[pack] = [e for e in load_pack(pack) if e.answer not in seen]
            seen |= {e.answer for e in by_pack[pack]}

        def balanced(tiers: set[int]) -> list[Entry]:
            lists = [pick(v, tiers) for v in by_pack.values()]
            for lst in lists:
                self.random.shuffle(lst)
            if len(lists) > 1:
                share = max(MIN_THEME_SHARE, min(len(lst) for lst in lists))
                lists = [lst[:share] for lst in lists]
            return [e for lst in lists for e in lst]

        def as_pairs(entries: list[Entry]) -> list[tuple[str, str]]:
            return [(e.answer, e.hard_clue if hard else e.clue) for e in entries]

        pools = [as_pairs(balanced(preferred)), as_pairs(balanced(preferred | fallback))]
        if "general" not in packs:
            backup = pick(list(load_pack("general")), preferred)
            pools.append(pools[-1] + as_pairs([e for e in backup if e.answer not in seen]))
        return pools

    def generate_early(self) -> None:
        if self.options.puzzle_size == PuzzleSize.option_custom:
            target, max_size = self.options.word_count.value, GRID_MAX
        else:
            target, max_size = SIZE_PRESETS[self.options.puzzle_size.value]
        pools = self.build_word_pools()
        for pool in pools:
            self.words = generate(pool, target, self.random, max_size=max_size)
            if len(self.words) >= target:
                break
        used_letters = {ch for w in self.words for ch in w.answer}

        cells = sorted({(r, c) for w in self.words for r, c, _ in w.cells()})
        if self.options.square_checks == SquareChecks.option_every_square:
            self.squares = cells
        elif self.options.square_checks == SquareChecks.option_every_nth:
            n = self.options.square_check_interval.value
            self.squares = [cell for i, cell in enumerate(cells) if i % n == n - 1]
        else:
            self.squares = []

        start_letters: set[str] = set()
        if self.options.starting_letters == StartingLetters.option_wheel_of_fortune:
            start_letters |= set("AEIOURSTLN")
        elif self.options.starting_letters == StartingLetters.option_vowels:
            start_letters |= set("AEIOU")

        # Guarantee N words are solvable immediately: pick the words needing the fewest extra letters.
        start_clues: set[str] = set()
        candidates = self.words[:]
        self.random.shuffle(candidates)
        crossword_only = all(self.multiworld.game[p] == GAME for p in self.multiworld.player_ids)
        floor = -(-len(self.words) // (4 if crossword_only else 10))
        guaranteed = max(self.options.starting_words.value, 2, floor)
        for _ in range(min(guaranteed, len(candidates))):
            candidates.sort(key=lambda w: len(set(w.answer) - start_letters))
            w = candidates.pop(0)
            start_letters |= set(w.answer)
            start_clues.add(clue_item(w.number, w.direction))

        remaining = [clue_item(w.number, w.direction) for w in self.words
                     if clue_item(w.number, w.direction) not in start_clues]
        self.random.shuffle(remaining)
        extra = min(self.options.starting_clues.value, len(remaining))
        start_clues.update(remaining[:extra])
        remaining = remaining[extra:]

        # Item pool can't exceed location count: hand out extra clues at the start if needed.
        # Keep ~20% of slots as filler so small/solo seeds have room to breathe.
        pool_size = len(remaining) + len(used_letters - start_letters)
        # Late milestones (75%/100%) can't hold much in a solo seed, so only 25%/50% count as room.
        early_slots = len(self.words) + len(self.squares) + (2 if self.options.milestone_checks else 0)
        # Crossword-only seeds (solo, or only crosswords) have no other games to spread items into,
        # so keep more slack: a third of the early slots stay filler instead of a fifth.
        crossword_only = all(self.multiworld.game[p] == GAME for p in self.multiworld.player_ids)
        max_progression = early_slots - early_slots // (3 if crossword_only else 5)
        overflow = max(0, pool_size - max_progression)
        start_clues.update(remaining[:overflow])
        overflow -= min(overflow, len(remaining))
        # Still too many (tiny puzzle, few starting letters): give the most common letters at the start.
        if overflow:
            counts = {ch: sum(w.answer.count(ch) for w in self.words) for ch in used_letters - start_letters}
            for ch in sorted(counts, key=lambda c: (-counts[c], c))[:overflow]:
                start_letters.add(ch)

        self.start_letters = start_letters & used_letters
        self.start_clues = start_clues

    def location_count(self) -> int:
        return (len(self.words) + len(self.squares) +
                (len(MILESTONES) if self.options.milestone_checks else 0))

    def create_regions(self) -> None:
        region = Region(self.origin_region_name, self.player, self.multiworld)
        for w in self.words:
            name = word_location(w.number, w.direction)
            region.locations.append(CrosswordLocation(self.player, name, location_name_to_id[name], region))
        for r, c in self.squares:
            name = square_location(r, c)
            region.locations.append(CrosswordLocation(self.player, name, location_name_to_id[name], region))
        if self.options.milestone_checks:
            for pct in MILESTONES:
                name = milestone_location(pct)
                region.locations.append(CrosswordLocation(self.player, name, location_name_to_id[name], region))
        goal = CrosswordLocation(self.player, "Puzzle Complete", None, region)
        goal.place_locked_item(CrosswordItem("Victory", ItemClassification.progression, None, self.player))
        region.locations.append(goal)
        self.multiworld.regions.append(region)

    def create_item(self, name: str) -> CrosswordItem:
        if name == FILLER:
            cls = ItemClassification.filler
        elif name in TRAPS.values():
            cls = ItemClassification.trap
        elif name in USEFUL_FILLER:
            cls = ItemClassification.useful
        elif name.endswith(" Clue") and not self.options.require_clues:
            cls = ItemClassification.useful
        else:
            cls = ItemClassification.progression
        return CrosswordItem(name, cls, item_name_to_id[name], self.player)

    def get_filler_item_name(self) -> str:
        # Reveals are a bit more common than word checks.
        return REVEAL if self.random.random() < 0.6 else CHECK

    def create_items(self) -> None:
        for name in sorted(self.start_letters):
            self.push_precollected(self.create_item(letter_item(name)))
        for name in sorted(self.start_clues):
            self.push_precollected(self.create_item(name))

        pool = [self.create_item(letter_item(ch))
                for ch in sorted({c for w in self.words for c in w.answer} - self.start_letters)]
        pool += [self.create_item(clue_item(w.number, w.direction)) for w in self.words
                 if clue_item(w.number, w.direction) not in self.start_clues]
        # Tools are capped at ~1 per 2 words so big square-check pools don't hand out a reveal per square;
        # anything beyond that is Coffee Break junk.
        tool_budget = -(-len(self.words) // 2)
        traps = [TRAPS[t] for t in sorted(self.options.trap_types.value) if t in TRAPS]
        trap_chance = self.options.trap_chance.value if traps else 0
        while len(pool) < self.location_count():
            if trap_chance and self.random.randint(1, 100) <= trap_chance:
                pool.append(self.create_item(self.random.choice(traps)))
            elif tool_budget > 0:
                pool.append(self.create_item(self.get_filler_item_name()))
                tool_budget -= 1
            else:
                pool.append(self.create_item(FILLER))
        self.multiworld.itempool += pool

    def solvable_words(self, state) -> int:
        return sum(1 for needed in self.requirements if state.has_all(needed, self.player))

    def set_rules(self) -> None:
        self.requirements = requirements = []
        for w in self.words:
            needed = [letter_item(ch) for ch in sorted(set(w.answer))]
            if self.options.require_clues:
                needed.append(clue_item(w.number, w.direction))
            loc = self.get_location(word_location(w.number, w.direction))
            loc.access_rule = lambda state, needed=needed: state.has_all(needed, self.player)
            requirements.append(needed)
        words_at: dict[tuple[int, int], list[list[str]]] = {}
        for w, needed in zip(self.words, requirements):
            for r, c, _ in w.cells():
                words_at.setdefault((r, c), []).append(needed)
        for r, c in self.squares:
            options = words_at[(r, c)]
            self.get_location(square_location(r, c)).access_rule = \
                lambda state, options=options: any(state.has_all(n, self.player) for n in options)
        if self.options.milestone_checks:
            for pct in MILESTONES:
                target = milestone_target(pct, len(self.words))
                self.get_location(milestone_location(pct)).access_rule = \
                    lambda state, target=target: self.solvable_words(state) >= target
        everything = {letter_item(ch) for w in self.words for ch in w.answer}
        if self.options.require_clues:
            everything |= {clue_item(w.number, w.direction) for w in self.words}
        everything = sorted(everything)
        self.get_location("Puzzle Complete").access_rule = \
            lambda state: state.has_all(everything, self.player)
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

    def fill_slot_data(self) -> Mapping[str, Any]:
        width = max(w.col + (len(w.answer) if w.direction == ACROSS else 1) for w in self.words)
        height = max(w.row + (1 if w.direction == ACROSS else len(w.answer)) for w in self.words)
        return {
            "version": 3,
            "id_base": BASE_ID,
            "milestones": list(MILESTONES) if self.options.milestone_checks else [],
            "squares": [[r, c] for r, c in self.squares],
            "require_clues": bool(self.options.require_clues),
            "death_link": bool(self.options.death_link),
            "death_link_amnesty": self.options.death_link_amnesty.value,
            "themes": sorted(self.options.themes.value) or ["General"],
            "difficulty": self.options.difficulty.current_key,
            "width": width,
            "height": height,
            "words": [
                {"number": w.number, "direction": w.direction, "row": w.row, "col": w.col,
                 "answer": w.answer, "clue": w.clue}
                for w in self.words
            ],
        }
