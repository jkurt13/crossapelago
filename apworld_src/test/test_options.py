from test.bases import WorldTestBase

from ..wordlist import PACKS, load_pack, parse_pack
import pkgutil


class CrosswordTestBase(WorldTestBase):
    game = "Crossapelago"


class TestDefault(CrosswordTestBase):
    def test_medium_size(self) -> None:
        self.assertEqual(len(self.world.words), 25)


class TestWordPacks(CrosswordTestBase):
    def test_packs_are_clean(self) -> None:
        for pack in PACKS:
            text = pkgutil.get_data("worlds.crossapelago", f"words/{pack}.txt").decode("utf-8")
            entries, problems = parse_pack(pack, text)
            self.assertEqual(problems, [], pack)
            self.assertGreater(len(entries), 150, pack)


class TestEverySquare(CrosswordTestBase):
    options = {"square_checks": "every_square"}

    def test_square_locations_exist(self) -> None:
        squares = [loc for loc in self.multiworld.get_locations(self.player) if loc.name.startswith("Square ")]
        cells = {(r, c) for w in self.world.words for r, c, _ in w.cells()}
        self.assertEqual(len(squares), len(cells))


class TestEveryNth(CrosswordTestBase):
    options = {"square_checks": "every_nth", "square_check_interval": 4, "milestone_checks": False}

    def test_square_count(self) -> None:
        squares = [loc for loc in self.multiworld.get_locations(self.player) if loc.name.startswith("Square ")]
        cells = {(r, c) for w in self.world.words for r, c, _ in w.cells()}
        self.assertEqual(len(squares), len(cells) // 4)


class TestHarsh(CrosswordTestBase):
    options = {"puzzle_size": "custom", "word_count": 10, "starting_letters": "none", "starting_words": 1,
               "starting_clues": 0, "square_checks": "every_nth"}


class TestHugeEverySquare(CrosswordTestBase):
    options = {"puzzle_size": "huge", "square_checks": "every_square", "require_clues": False}

    def test_fits_grid(self) -> None:
        self.assertEqual(len(self.world.words), 60)
        cells = {(r, c) for w in self.world.words for r, c, _ in w.cells()}
        self.assertLessEqual(max(r for r, _ in cells), 24)
        self.assertLessEqual(max(c for _, c in cells), 24)


class TestSmallEasy(CrosswordTestBase):
    options = {"puzzle_size": "small", "difficulty": "easy"}

    def test_small_and_easy(self) -> None:
        self.assertEqual(len(self.world.words), 15)
        tiers = {e.answer: e.tier for e in load_pack("general")}
        self.assertTrue(all(tiers.get(w.answer, 1) <= 2 for w in self.world.words))


class TestGamingHard(CrosswordTestBase):
    options = {"themes": ["Gaming"], "difficulty": "hard", "puzzle_size": "large"}

    def test_mostly_gaming_and_hard_clues(self) -> None:
        gaming = {e.answer: e for e in load_pack("gaming")}
        themed = [w for w in self.world.words if w.answer in gaming]
        self.assertGreaterEqual(len(themed), len(self.world.words) * 0.9)
        self.assertTrue(all(w.clue == gaming[w.answer].hard_clue for w in themed))


class TestMixedThemes(CrosswordTestBase):
    options = {"themes": ["Gaming", "Movies", "Sports"]}

    def test_each_theme_shows_up(self) -> None:
        answers = {w.answer for w in self.world.words}
        for pack in ("gaming", "movies", "sports"):
            self.assertTrue(answers & {e.answer for e in load_pack(pack)}, pack)


class TestTraps(CrosswordTestBase):
    options = {"square_checks": "every_nth", "trap_chance": 100, "trap_types": ["Scramble", "Blackout"]}

    def test_only_chosen_traps(self) -> None:
        names = [i.name for i in self.multiworld.itempool if i.player == self.player]
        traps = [n for n in names if n.endswith(" Trap")]
        self.assertTrue(traps)
        self.assertEqual(set(traps), {"Scramble Trap", "Blackout Trap"})
        self.assertNotIn("Reveal Square", names)
        self.assertNotIn("Coffee Break", names)


class TestTrapsOffByDefault(CrosswordTestBase):
    options = {"square_checks": "every_nth"}

    def test_no_traps(self) -> None:
        self.assertFalse([i for i in self.multiworld.itempool if i.name.endswith(" Trap")])


class TestDeathLinkSlotData(CrosswordTestBase):
    options = {"death_link": True, "death_link_amnesty": 4}

    def test_slot_data(self) -> None:
        data = self.world.fill_slot_data()
        self.assertTrue(data["death_link"])
        self.assertEqual(data["death_link_amnesty"], 4)
