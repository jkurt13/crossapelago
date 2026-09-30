# Crossapelago — a crossword for Archipelago — v0.7.0

A crossword you play in the browser as part of an [Archipelago](https://archipelago.gg) multiworld.
Other players send you letter keys and clues; solving words sends out checks.

**Play:** https://jkurt13.github.io/crossapelago/

## Files
- `index.html` — the web client (this is what GitHub Pages serves).
- `crossapelago.apworld` — drop into your Archipelago `custom_worlds` folder.
- `Crossapelago.yaml` — options template.
- `apworld_src/` — source of the apworld (word packs in `apworld_src/words/`).
- `client/` — source of the web client. After editing `client/index.template.html`, run `python client/build_client.py` to rebuild `index.html`.

## Publish on GitHub Pages (one-time)
1. On github.com, create a new **public** repository named `crossapelago`. Don't add a README; this folder has one.
2. Upload this folder's contents to the repo, either way:
   - **Web:** on the new repo's page, click "uploading an existing file", drag in everything from this folder (including `.nojekyll`), and commit.
   - **GitHub Desktop:** File → Add local repository → pick this folder → "create a repository" → Publish, un-ticking "Keep this code private".
3. In the repo, go to **Settings → Pages**. Under "Build and deployment", pick **Deploy from a branch**, branch **main**, folder **/ (root)**, then Save.
4. After a minute or two the site is live at `https://jkurt13.github.io/crossapelago/`.

To update the site later, upload the changed files again (or commit and push in GitHub Desktop). Pages redeploys on its own.

### Sharing with friends
- **Copy link** in the page header copies a link with the server and slot filled in. The password is never included.
- You can also build links by hand: `https://jkurt13.github.io/crossapelago/?server=archipelago.gg:38281&slot=Jacob`.
- The hosted page can reach **archipelago.gg** rooms and **servers on your own computer** (`localhost`).
- Browsers block an https page from reaching a server on another machine on your LAN (e.g. `192.168.x.x`). For that, download `index.html` and open the file directly.

## Play
1. Install the apworld, then use the Launcher's "Generate Template Options" to get the YAML, or use the one below.
2. Generate and host as usual.
3. Open `index.html`, enter the server address (e.g. `archipelago.gg:38281`) and your slot name, then press Connect.
   - Keyboard: type letters, Backspace, arrow keys, Tab / Shift+Tab to change words, Space to switch direction.
   - **Reveal Square** fills the selected square. **Check Word** marks the wrong letters in the current word.
   - **Demo** plays a small offline puzzle.

```yaml
name: YourName
game: Crossapelago
Crossapelago:
  themes: [General]           # any of: General, Gaming, Movies, Sports
  difficulty: medium          # easy | medium | hard
  puzzle_size: medium         # small (15 words) | medium (25) | large (40) | huge (60) | custom
  word_count: 25              # only used when puzzle_size is custom (10-60)
  starting_letters: wheel_of_fortune   # wheel_of_fortune (AEIOU+RSTLN) | vowels | none
  starting_words: 3           # words fully solvable at start (floor: 2, or 1 per 10 words)
  starting_clues: 3           # extra random clues at start
  require_clues: true         # false = clues are just help, not locks
  milestone_checks: true      # +4 checks at 25/50/75/100% of words solved
  square_checks: off          # off | every_square | every_nth
  square_check_interval: 3    # N for every_nth (2-10)
  trap_chance: 0              # % of filler replaced by traps (0 = off)
  trap_types: [Scramble, Eraser, Blackout, Sticky Key]
  death_link: false
  death_link_amnesty: 2       # free wrong words before one sends a death (2 = every 3rd)
```

## How it works
- **Generation:** the puzzle is built from the seed in Python (`generator.py`) and sent to the client through `slot_data`.
- **Word packs** are in `words/*.txt`, one line per word: `ANSWER|tier|clue|hard clue`.
  - Sizes: General ~770 words, Gaming ~235, Movies ~230, Sports ~250.
  - Tier 1 is common, tier 2 medium, tier 3 tricky.
  - To add words, edit these files and rebuild the apworld. The `TestWordPacks` test flags bad lines: wrong length, non-letters, duplicates.
- **Difficulty:**
  - easy: tier 1 words.
  - medium: tiers 1 and 2.
  - hard: mostly tiers 2 and 3, with the hard clues.
  - If a theme runs short for the requested size, it borrows from the neighboring tier first, then from General.
- **Themes:** with several themes, each pack contributes a roughly equal share. Themed packs win duplicate answers over General (e.g. GOLF gets its Sports clue).
- **Sizes:** small 15 words / 13×13, medium 25 / 17×17, large 40 / 21×21, huge 60 / 25×25, custom = `word_count` / 25×25.
- **Items:**
  - `Letter A`–`Letter Z`: you can only type letters you've received.
  - `N Across Clue` / `N Down Clue`.
  - `Reveal Square` / `Check Word`: consumable "useful" filler.
  - Traps (optional, `trap_chance`):
    - `Scramble Trap` shuffles your typed letters.
    - `Eraser Trap` wipes your typed letters from the unsolved word with the most filled in.
    - `Blackout Trap` hides all clues for 30 s.
    - `Sticky Key Trap` jams one of your letters for 60 s, preferring letters you still need.
  - Item groups `Letters`, `Clues`, `Tools` and `Traps` work with `!hint`.
- **Checks:**
  - `N Across` / `N Down`: fire when the word is correct and its clue is unlocked.
  - `25% Solved` … `100% Solved`: milestone checks, location group `Milestones`.
  - `Square R<row> C<col>` (optional): location group `Squares`.
    - Fires when a word through the square is solved, or when the square is revealed. Checks don't fire on a single correct letter, so you can't fish for them by trying every letter.
    - `every_nth` takes every Nth square in reading order.
    - Blue dots mark these squares in the client.
- **Goal:** solve every word.
- **Logic:**
  - A word needs its clue plus every letter in it.
  - Milestone P% needs enough words to be in logic: ceil(P% × words).
  - A square needs any one of its words to be in logic.
- **Pool sizing:**
  - Progression items can fill at most ~80% of the word checks, square checks, and the 25% and 50% milestones. The 75% and 100% milestones come too late to count.
  - The rest is filler: Reveal/Check tools up to about 1 per 2 words, then `Coffee Break` junk. Without that cap, every-square seeds would hand out dozens of reveals.
  - Any extra clues (or common letters, for tiny puzzles) are given at the start.
- **Timed traps wait for you.**
  - Blackout and Sticky Key only count down while the crossword tab is visible and focused. While you're in another game they're paused, shown as "(paused)" in the pills above the grid.
  - Traps that land while you're away change the tab title to "(Trap!)", and a "While you were away: ..." banner lists them when you come back.
  - Remaining trap time is saved on the server (checked about every 5 s and whenever you switch away), so reloading or switching devices doesn't skip a trap.
- **DeathLink:**
  - A mistake is when your own keystroke fills the last empty square of a word and the word is wrong. Traps never count.
  - Every (amnesty + 1)th mistake sends a death. The progress line shows `DeathLink n/3 mistakes`.
  - A received death erases every typed letter in unsolved words. Solved words and revealed squares stay.
  - Like timed traps, a death waits until you're focused on the crossword. The tab title shows "(DeathLink!)" in the meantime.
  - Pending deaths are saved on the server, so reloading doesn't dodge one. Your own deaths aren't applied back to you.
- **Auto-reconnect:**
  - If the connection drops, the page retries at 2, 4, 8, 15, then every 30 s, and keeps your board as it is.
  - If Chrome unloads the tab or the PC sleeps, the page reconnects when you come back, without pressing Connect. The server, slot and password for that tab are kept in the tab's session storage, which clears when the tab is closed.
  - A refused login (wrong slot or password) stops the retries.
- **Traps fire once.** The item index processed so far (`trapIndex`) is saved with the tool usage, so reconnecting or opening another browser never replays old traps. Traps wait for that saved value before firing.
- **Tool usage** (used counts and revealed squares) is saved in the server's data storage under `crossword_<team>_<slot>`, so it carries across browsers and devices. Typed letters are only saved in the browser.
- **Hosting:** the client uses the raw AP WebSocket protocol, with no libraries, so it's a single static file.
  - From an `https://` page it uses `wss://`, plus `ws://` for `localhost` / `127.0.0.1`, which browsers allow.
  - When opened as a local file it also tries `ws://` for LAN addresses.

## v0.7.0 — renamed to Crossapelago
- The game name is now `Crossapelago`, used in YAMLs as `game: Crossapelago`. The apworld is `crossapelago.apworld`.
- The site is at `jkurt13.github.io/crossapelago/`.
- Item and location names and IDs are unchanged. Seeds made with the old name need the old apworld.
- **Tested:**
  - AP general tests plus 53 world tests pass.
  - Built with AP's builder, the manifest reads Crossapelago v0.7.0.
  - The packaged file generated alongside Hollow Knight.
  - The renamed page connected and solved a word, and that sent an item to the Hollow Knight player.

## Tested (v0.6.0 — DeathLink, reconnect)
- **Two-player room (Alice + Bob, both DeathLink, amnesty 1):**
  - Alice's 1st wrong word was free; her 2nd sent a death.
  - Bob was away: the death stayed pending, his 5 typed letters stayed, and his title read "(DeathLink!)". On focus, the letters were wiped and a banner named Alice.
  - Alice didn't receive her own death.
  - A 2nd death sent while Bob was away was still delivered after he reloaded in a fresh browser.
- **Server killed and restarted:** the client showed "Reconnecting in …" and came back on its own. After a tab reload it auto-connected.
- **Crossword-only seeds:** now keep more filler and guarantee at least 1 solvable starting word per 4. They're tighter than multiworlds because no other games' locations can hold their items.
  - Default solo: 40/40 generated (was 39/40).
  - The extreme solo test (10 words, no letters): 20/20 (was about 50%).
  - Multiworld settings are unchanged, and default + Hollow Knight passed 8/8.

## Tested (away handling)
- **While away** (tab unfocused), a Sticky Key trap stayed at 60 s and a Blackout at 30 s.
  - The tab title flagged "(Trap!)", and the banner was held back.
- **On return**, the "While you were away" banner listed the traps, and both timers started counting down.
- **Reloading in a fresh browser** restored the remaining Sticky time from the server.

## Tested (v0.5.0 — traps)
- **World tests:** 49, all passing. New ones check that only the chosen trap types appear, and that traps are off by default.
- **Full playthrough, trap_chance 100** (35 traps in a solo game):
  - Each trap did its job:
    - Scramble shuffled 6 typed letters.
    - Eraser wiped a word.
    - Blackout greyed out the clues.
    - Sticky Key blocked its letter and marked the key.
  - The puzzle, squares, milestones and goal still completed.
- **Reconnect:** after 8 traps fired, a fresh browser with no saved data reconnected and replayed 0 traps. The saved index was restored from the server.

## Tested (hosting)
- The page was served over HTTPS, the way GitHub Pages serves it.
  - Connected to a `wss://` server with a certificate and to a plain `ws://localhost` server. Both solved a word, and the server logged the checks.
  - The download links for the apworld and YAML template both resolve.
  - Copy link produced `?server=…&slot=…`, and those parameters prefill the fields.
  - Phone width has no sideways scrolling.

## Tested (v0.4.0)
- **Stress test:** every theme × difficulty × size combo, 6 seeds each. Every one reached its full word count, and all except huge + hard (Movies or Sports) stayed inside the chosen theme. Each builds in about 2 s or less.
- **World tests:** 41 tests in `test/test_options.py`, all passing. They cover:
  - word-pack lint;
  - sizes;
  - easy picks only easy-tier words;
  - Gaming + hard picks gaming words with hard clues;
  - mixed themes all appear.
- **Built with AP's own "Build APWorlds" tool**, so the manifest is valid. Earlier versions showed an "invalid or missing manifest" warning; that's fixed.
- **Full playthrough:** Gaming + Sports, hard, large, every 3rd square — 40 words, 66 squares, 4 milestones and the goal all registered on a real MultiServer.

## Tested (v0.3.0)
- **Option tests:** `worlds/crossapelago/test/test_options.py` covers default, every_square, every_nth, a harsh solo setup, and 60 words with every_square. It runs AP's standard world checks on each: 23 tests, all pass.
- **Generation:**
  - Every square-check setting passes solo, including harsh starts that used to fail.
  - every_square + Hollow Knight: all passed.
- **Full playthrough with every_nth, interval 3:**
  - All 34 square checks, 4 milestones, 25 words and the goal registered on a real MultiServer.
  - A revealed square sent its check.
- **Starting clues** (25 words, default options): 13 with square checks off, 6 with every_nth or every_square. 6 is just the 3 guaranteed words plus the 3 extra clues the options ask for.

## Tested (v0.2.0)
- **AP test suite:** `test/general` passes for this world.
- **Generation**, run across many seeds:
  - Solo, default settings: 10/10.
  - Multiworld with APQuest or Hollow Knight: all passed.
- **Full playthrough on a real MultiServer:**
  - All four milestones and the goal registered.
  - Check Word marked a wrong letter, and Reveal filled a square.
  - Tool usage was restored in a fresh browser from server storage.

## Known limits
- With square checks off, 25-word puzzles still start with about 13 of 25 clues unlocked. Turn on `every_nth` to fix this.
- Crossword-only games (solo, or only crosswords) start with more free words than the same settings in a multiworld. That's the price of reliable generation.
- Typed letters live in each browser. A DeathLink or trap still applies on another device, but there may be nothing there to wipe.

## Adding more check types
The IDs are listed at the top of `__init__.py`.
1. Add the location names to `location_name_to_id` and an option.
2. Create them in `create_regions` with a rule.
3. In `index.html`'s `evaluate()`, detect the condition and send the ID.
