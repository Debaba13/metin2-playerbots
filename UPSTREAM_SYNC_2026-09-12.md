# Upstream sync: 1.31.2 -> 2.0.14 (2026-09-12)

## Follow-up: translation sweep and a client phone-home call (same day, commit 4b36f31)

After the merge landed, asked to (1) translate every Polish string a player
or admin could see and (2) look for "paywall"-shaped things from upstream
and counter them with our own prior work. Scoped to in-game bot text first
(the admin panel, seban-panel and the mt2009 client's Python UI are each
their own much larger job - deliberately not started here; see below).

**Translation**: audited every `PlayerBotText()`/`FormatPlayerBotText()`
call site against `playerbot_language.h`'s dictionary (all covered) and
swept the whole overlay for loose Polish literals with a broader heuristic
than the merge's own check used. Found one real gap: `playerbot_shop_signs.h`,
upstream's new ~100-string community stall-sign pool (screenshotted off real
2010-2012 Polish server stalls), had never conflicted with anything on our
side - it's wholly new content - so nothing flagged it for translation. It
was also dead code: I'd left it uncalled in the original merge, using our
own simpler Turkish sign generator instead, and flagged that as a judgment
call needing a second look. Translated all eight categories (universal,
books, fish, gear, materials, medals, scrolls, stones) to Turkish, keeping
the joke shapes (the "quitting the game" trope, decorative `@@@`/`>>>`
borders, the "cheaper than next door" lines) and the `%N`/`%I`/`%C`
placeholder mechanics exactly, then wired `PickPlayerBotShopSign` into
`playerbot_town.h`'s actual sign generator ahead of our own
`BuildPlayerBotTurkishShopSign` (same priority upstream gives its own pool),
with the pid/poor-status prefix pulled into a shared
`ApplyPlayerBotShopSignPrefix` so a poor keeper's "Indirim:" prefix still
applies over a community-pool pick instead of the pick being discarded.
Everything else the sweep found was either a `playerbot_language.h`
dictionary key (Polish-as-key is the designed pattern, per
`AI_LANGUAGE_FIX.md`) or a code comment quoting a historical Discord bug
report - not live player-visible text.

**"Paywall"**: found one genuine issue, not the premium/subscription system
I'd guessed at first (that one's the opposite of a paywall - upstream grants
every bot five years of mt2009 premium for free, since the engine reads
bonus rates and extra safebox/shop slots from that flag and a bot has no
real login to set it). The actual finding: `linux-port-mt2009/client-root/
intrologin.py`'s login window POSTs to the original commercial site's
`logon.mt2009.pl/gatekeeper.php` on every client launch, synchronously,
release builds only, and reads nothing back (just prints "success!" to a
console nobody sees) - a pure phone-home with a startup-hang risk on a
firewalled or offline machine, sitting right next to three other buttons on
the same screen that upstream's own `clientrootify.py` already redirected
away from mt2009.pl. Removed it from both the checked-in file and the
patch-definition script (so it stays gone if a future stock client package
is ever re-processed through that tool), and pointed the home-page button
at this fork's own repo instead of upstream's, matching the precedent
already set for the updater (`967cc50`).

**Deliberately not done in this pass**: the admin panel (`files/
admin_panel.py`, 305+ translation calls plus an estimated ~530 more lines of
plain Polish per `CLAUDE.md`'s own note), seban-panel, the itemshop PHP
front end, and the mt2009 client's several dozen other Python UI files. Each
is large enough, and unfamiliar enough to me in this session, to warrant its
own careful pass rather than a rushed one bundled into this sync - flagged
to the user rather than guessed at.


What this was: `git merge upstream/main` (TieruYT/metin2-playerbots,
`https://github.com/TieruYT/metin2-playerbots.git`) into this fork's
`claude/sync-updates-client-o7hk2w`, bringing in 107 upstream commits since our
last sync (merge-base `3e123bf`, "chore(release): 1.31.2") up to upstream
`c6cdad9` ("chore(release): manifest 2.0.14"). 1983 files changed, +67432/-2622.

## The overhaul the user meant

Upstream's "overhaul" is `linux-port-mt2009/`: a second, parallel server/client
line on the mt2009 (Martysama r41023) server files, alongside the original
r40250 line under `linux-port/` — which upstream kept maintaining too (1.33.x
releases interleave with 2.0.x in the log). It is **additive**, not a
replacement: nothing here had to choose between the two lines. The playerbot
overlay (`linux-port/overlays/playerbot/`) is shared between both engines,
gated where needed by `PLAYERBOT_ENGINE_MT2009` (`playerbot_engine_compat.h`).
Read `linux-port-mt2009/README.md` before touching that tree.

Also in this batch: all three kingdoms (Chunjo/Shinsoo/Jinno) instead of
Chunjo only, human nicknames for bots (Iwakura's pool) instead of `bot<n>`,
a community stall-sign pool (`playerbot_shop_signs.h`), and a long list of
`fix(playerbot)` items — see `git log 3e123bf..c6cdad9` for the full list, or
`CHANGELOG.md`.

## Conflicts (6 files, all resolved)

Everything else auto-merged cleanly. The six conflicts were exactly the files
`AI_LANGUAGE_FIX.md` already names as upstream seams to check after a merge —
this is the second time this fork has done this (see commit `90b8839`,
the previous upstream merge), and the same pattern held:

- **README.md / README_EN.md**: one line each (supported-kingdoms blurb).
  Took upstream's wording (three kingdoms, matches what's actually in the
  merged tree now).
- **playerbot_status.h / playerbot_chat_trade.h**: not real conflicts — these
  are thin seam stubs on our side (`#include "playerbot_llm_status.h"` /
  `"playerbot_llm_chat_trade.h"`), full files on upstream's. Kept our stubs;
  ported upstream's *logic* deltas into the LLM overlay files by hand,
  translated to Turkish:
  - Multi-kingdom map-name tables (Yongan/Jayang/Pyongmoo/Bakra, "Klan
    Topraklari" for M3 in all three kingdoms).
  - `playerbot_empire_rules::GetTownServices` instead of a hardcoded M2 check
    for the stable keeper.
  - `GetPlayerBotFishingBank(mapIndex)` instead of one hardcoded bank.
  - `GetPlayerBotStallsOnMap()`-aware town-rest line, `IsPlayerBotM1Map`/
    `IsPlayerBotM2Map` instead of `== PLAYERBOT_MAP_CHUNJO_M1/M2`.
  - `GetPlayerBotShopReasonName()` suffix on the stall status line.
- **playerbot_manager.cpp**: one line — both sides added an include
  (`playerbot_llm_shop.h` ours, `playerbot_shop_signs.h` upstream's). Kept
  both; see below.
- **playerbot_town.h**: one block — the shop-sign generator. Upstream
  generalized it to detect fish/gear/medal/scroll/stone counters (not just
  books/materials/scrap) and draw from the new community sign pool. Extended
  `BuildPlayerBotTurkishShopSign` (our Turkish equivalent) with the same
  categories instead of adopting `PickPlayerBotShopSign` directly — see below.

## A deliberate design choice: two sign pools, not one

`playerbot_shop_signs.h` is new upstream content, not a conflict: ~250 lines
of *authentic* Polish market slang Iwakura collected from 2010-2012 server
screenshots ("NAZWY SKLEPOW"). Translating that pool didn't seem right — it's
specifically preserved community flavor, and a machine translation of that
much idiom risked being both wrong and worse than what it replaced.

Instead: kept it as dead-but-compiled upstream content (included in
`playerbot_manager.cpp`, never called), and taught our own
`BuildPlayerBotTurkishShopSign` (`playerbot_llm_shop.h`) the same seven
categories upstream added (fish/books/materials/gear/medals/scrolls/stones),
in Turkish, in the same short-phrase style the function already had. This is
a judgment call, not a translation gap — flag it if the intent was actually to
carry the Polish flavor text over to Turkish players; it would need a native
speaker's pass on ~100 idioms, not a mechanical one.

## Two translation gaps found and fixed along the way

Not part of the merge itself — found while diffing our `playerbot_llm_status.h`
line-by-line against the file it was forked from, to make sure I wasn't
missing behavior upstream had added since:

1. **`state.bTacticalRetreat` line was still Polish** (`"Uciekam - mam malo
   HP"`) in a file that's supposed to be all-Turkish. Fixed to `"Kaciyorum -
   HP dusuk"`.
2. **The frontier Teleporter-fee branch was missing entirely** — our Turkish
   `BuildPlayerBotStatusText` dropped straight from "no destination" to "found
   a place" with no "waiting on the fare" case, even though the Polish
   original (present since before our last sync) had one. Restored it,
   translated, with upstream's `IsPlayerBotM2Map` generalization.
3. **`PLAYERBOT_MAP_SPIDER_V2` was missing** from
   `GetPlayerBotMapDestinationTurkish`'s table (present in the Polish
   original). Restored.
4. **`GetPlayerBotShopReasonName`** (new upstream function in
   `playerbot_types.h`, merged in cleanly since we'd never touched that area)
   had Polish literal strings with no Turkish counterpart at all, because
   nothing existed on our side to conflict with. Translated it in place —
   this is the kind of gap `AI_LANGUAGE_FIX.md` warns can hide in a clean
   auto-merge: no conflict marker ever points at it.

**If anyone re-does a translation audit, grep for it specifically** — a clean
merge of a file we've never touched is exactly the case that produces no
conflict and no diff-review prompt, so new upstream Polish text can land
undetected. `AI_LANGUAGE_FIX.md`'s quick-search list is a start; it doesn't
cover `playerbot_types.h` today and arguably should.

## Also cleaned up

Three tracked files were leftover debris from an earlier manual merge
(`Metin2-Launcher-GUI.ps1.conflict-backup-20260908-032026`,
`Metin2-Launcher-GUI.ps1.localization-backup-20260908-032649`,
`launcher/Metin2Launcher.psm1.localization-backup-20260908-032649`) — one of
them still had raw `<<<<<<<` markers baked in. Nothing referenced them
(checked against every `.txt`/`.ps1`/`.psm1`/`Dockerfile*` in the repo).
Deleted.

`tools/check-update-covers-build.py` (the tool `CLAUDE.md` says to run before
a release) flagged one real, pre-existing bug while checking this merge:
`linux-port/docker/game/mob_drop_item.m3.append.txt` was gitignored and
never committed, even though `launcher/server-update-files.txt` has always
listed it — so a Windows player's update (which never runs
`prepare-context.sh`, see `CLAUDE.md`'s "An engine patch reaches a player
only as the staged file") would have shipped a manifest entry pointing at a
file that doesn't exist in their checkout. Its sibling,
`special_item_group.moonlight.txt`, was already committed directly at both
the overlay path and the staged Docker-context path — and upstream's own new
mt2009 line does the same for its copy of this exact file. Brought the
r40250 line in line with both: removed the stale `.gitignore` entry, committed
`linux-port/docker/game/mob_drop_item.m3.append.txt` directly. Predates this
merge; not something the sync introduced, just something the sync's own
verification pass surfaced.

## What was verified, and what was not

- `python3 tools/check-update-covers-build.py` (both `--docker linux-port/docker`
  and `--docker linux-port-mt2009/docker` variants): clean, every Dockerfile
  `COPY` source ships or is staged.
- `tests/playerbot_world_rules_test.cpp`: compiles and passes with a plain
  host `g++` (this file has no engine dependency by design). Unaffected by
  this merge either way — included for a basic sanity check that the tree
  still builds *something*.
- Brace/paren balance and cross-reference checks (grep) on every file touched
  by hand, confirming every new symbol used (`IsPlayerBotM1Map`,
  `playerbot_empire_rules::GetTownServices`, `GetPlayerBotFishingBank`,
  `GetPlayerBotStallsOnMap`, `GetPlayerBotShopReasonName`, `PlayerBotNavHash`,
  `SHOP_SIGN_MAX_LEN`) resolves somewhere earlier in
  `playerbot_manager.cpp`'s include chain.
- **Not run**: the actual `g++ -fsyntax-only -m32 -std=c++23` check against
  real engine headers that `CLAUDE.md` prescribes. This session's sandbox has
  no `../m2src-cache` (the reference build tree needs the proprietary r40250
  package, which `CLAUDE.md` says is never in this repository) and no running
  Docker daemon. **Run that check by hand before deploying this branch** —
  it's the one CLAUDE.md documents in "Verifying a change", and it catches
  almost everything a manual merge like this can get wrong. Also worth a
  syntax check: `playerbot_types.h` (touched for the `GetPlayerBotShopReasonName`
  translation) and `playerbot_llm_shop.h`/`playerbot_llm_status.h`/
  `playerbot_llm_chat_trade.h`.
- Nothing here was runtime-tested — no live server, no bots. Everything above
  is "compiles by inspection," not "observed working."

## Follow-ups worth a deliberate look, not rushed here

- `playerbot_shop_signs.h`'s ~100 Polish sign strings: translate to Turkish,
  or confirm the "keep as untranslated flavor" call above is actually wanted.
- A pass over `playerbot_types.h` and any other file that has never conflicted
  with upstream, specifically hunting for new player-visible Polish strings
  that arrived through a clean auto-merge (see gap #4 above for why these are
  easy to miss).
