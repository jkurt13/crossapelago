from dataclasses import dataclass

from Options import Choice, DeathLink, DefaultOnToggle, OptionSet, PerGameCommonOptions, Range


class Themes(OptionSet):
    """Which word packs the puzzle draws from. Pick one or more: General, Gaming, Movies, Sports.
    With several themes, each gets a roughly equal share of the words."""
    display_name = "Themes"
    valid_keys = frozenset({"General", "Gaming", "Movies", "Sports"})
    default = frozenset({"General"})


class Difficulty(Choice):
    """How hard the words and clues are.
    easy: common words with straightforward clues.
    medium: adds less common words.
    hard: mostly tougher words, with tricky clues."""
    display_name = "Difficulty"
    option_easy = 0
    option_medium = 1
    option_hard = 2
    default = 1


class PuzzleSize(Choice):
    """How big the puzzle is.
    small: ~15 words in a 13x13 grid.
    medium: ~25 words in a 17x17 grid.
    large: ~40 words in a 21x21 grid.
    huge: ~60 words in a 25x25 grid.
    custom: use Word Count below (25x25 grid)."""
    display_name = "Puzzle Size"
    option_small = 0
    option_medium = 1
    option_large = 2
    option_huge = 3
    option_custom = 4
    default = 1


class WordCount(Range):
    """Only used when Puzzle Size is custom: how many words the crossword contains."""
    display_name = "Word Count"
    range_start = 10
    range_end = 60
    default = 25


class StartingLetters(Choice):
    """Which letter keys you start with. You can only type letters you have received.
    wheel_of_fortune: start with the vowels plus R, S, T, L, N.
    vowels: start with A, E, I, O, U.
    none: start with no letters (except what's needed for your guaranteed starting words)."""
    display_name = "Starting Letters"
    option_wheel_of_fortune = 0
    option_vowels = 1
    option_none = 2
    default = 0


class StartingWords(Range):
    """Number of words that are fully solvable at the start (clue given and all letters given).
    Guarantees you are never stuck at the beginning. Minimum is 2, or 1 per 10 words for big puzzles."""
    display_name = "Starting Words"
    range_start = 1
    range_end = 10
    default = 3


class StartingClues(Range):
    """Extra random clues unlocked at the start, on top of the starting words' clues.
    (More clues may be given at the start if the item pool is larger than the number of words.)"""
    display_name = "Extra Starting Clues"
    range_start = 0
    range_end = 30
    default = 3


class RequireClues(DefaultOnToggle):
    """On: a word's check only sends once you have received its clue (clues are hard locks).
    Off: clues are just help; solving a word from its crossings still sends the check."""
    display_name = "Require Clues"


class MilestoneChecks(DefaultOnToggle):
    """Adds four extra checks for solving 25%, 50%, 75% and 100% of the words."""
    display_name = "Milestone Checks"


class SquareChecks(Choice):
    """Adds a check for individual squares. A square's check is sent when a word through it is solved
    (or when you reveal it).
    off: no square checks.
    every_square: every square in the grid is a check (roughly 4x the word count, so it's a lot).
    every_nth: every Nth square, in reading order (N = Square Check Interval)."""
    display_name = "Square Checks"
    option_off = 0
    option_every_square = 1
    option_every_nth = 2
    default = 0


class SquareCheckInterval(Range):
    """With square_checks: every_nth, how far apart the square checks are (3 = every 3rd square)."""
    display_name = "Square Check Interval"
    range_start = 2
    range_end = 10
    default = 3


class TrapChance(Range):
    """Percent chance that each filler item (Reveal Square, Check Word, Coffee Break) is replaced by a trap.
    0 turns traps off."""
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 0


class TrapTypes(OptionSet):
    """Which traps can appear.
    Scramble: shuffles the letters you've typed into unsolved words.
    Eraser: erases your typed letters from one unsolved word.
    Blackout: hides all clues for 30 seconds.
    Sticky Key: disables one of your letters for 60 seconds."""
    display_name = "Trap Types"
    valid_keys = frozenset({"Scramble", "Eraser", "Blackout", "Sticky Key"})
    default = frozenset({"Scramble", "Eraser", "Blackout", "Sticky Key"})


class DeathLinkAmnesty(Range):
    """With Death Link on: how many wrong words you can fill in for free before one sends a death.
    A "wrong word" is when your own typing fills the last empty square of a word and the answer is wrong.
    2 means every 3rd wrong word sends a death. Receiving a death erases everything you've typed into unsolved words."""
    display_name = "Death Link Amnesty"
    range_start = 0
    range_end = 10
    default = 2


@dataclass
class CrosswordOptions(PerGameCommonOptions):
    themes: Themes
    difficulty: Difficulty
    puzzle_size: PuzzleSize
    word_count: WordCount
    starting_letters: StartingLetters
    starting_words: StartingWords
    starting_clues: StartingClues
    require_clues: RequireClues
    milestone_checks: MilestoneChecks
    square_checks: SquareChecks
    square_check_interval: SquareCheckInterval
    trap_chance: TrapChance
    trap_types: TrapTypes
    death_link: DeathLink
    death_link_amnesty: DeathLinkAmnesty
