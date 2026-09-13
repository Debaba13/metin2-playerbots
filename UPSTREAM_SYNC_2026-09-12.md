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

## Follow-up: admin panel translated to Turkish (same day)

Asked separately to translate `files/admin_panel.py` after the in-game bot
text pass above. First corrected a wrong assumption I'd stated out loud
before checking: the panel's `T` dict (used via Jinja `{{t('key')}}`) already
carried Turkish for almost everything - 404 `"tr"` entries against 422
`"pl"` ones. The actual gap was three other places the panel does i18n that
the `T` dict doesn't cover:

1. **Standalone Python dicts keyed by language string**, each missing a
   `"tr"` branch and falling back to English or Polish: `BOT_PERSONALITY_LABELS`,
   `BOT_AMBITION_LABELS`, `BOT_GOAL_LABELS`, `BOT_ACTION_LABELS` (bot status
   panel labels), `MAP_I18N` (the whole live-map page, ~60 keys), `JOB_NAMES_MAP`.
2. **Dicts split into a `_EN`-suffixed sibling instead of a language key**
   (`X` = Polish, `X_EN` = English, selected by a ternary): added a third
   `_TR` sibling and widened the selector for `PLAYER_SKILLS`/`SKILL_GROUP_NAMES`
   (the full 8-job skill tree), `HUNTING_MOB_NAMES` (55 monster names),
   `BIOLOGIST_NAMES` (7 quest items), and the best-effort item-name
   transliterator (`_ITEM_PL_EXACT`/`_ITEM_PL_WORDS` -> added
   `_ITEM_TR_EXACT`/`_ITEM_TR_WORDS`; there's no stock Turkish item-name file
   to draw from, so this stays word-substitution, not a real per-vnum table -
   same caveat CLAUDE.md already notes for the Polish one).
3. **JS-embedded objects and inline ternaries**: `APPLY_META` (the ~90-entry
   bonus/stat tooltip table) got a `tr:` value added to every entry; eight
   `lg === 'pl' ? X : Y` ternaries in the item-tooltip builder became three-way
   (`lg === 'pl' ? X : lg === 'tr' ? Y : Z`); and one spot with no language
   branching at all - `'ŚR: '`/`'UM: '`/`'Plecak'`/`'Broń 30 Lv'` hardcoded
   into the weapon30 ranking card - got the same three-way treatment.

Also fixed, while reading the status-label code for the above:
**`localize_playerbot_status()` was translating from Polish substrings that
no longer exist.** It predates this fork's switch to Turkish bot speech
(`playerbot_llm_status.h` has spoken Turkish for a while) and was pattern-matching
dead Polish text, so a bot's live status silently leaked raw Turkish into
English/German/pl panel views instead of being translated either way.
Rewrote it around the actual Turkish patterns bots emit
(`"... kiriyorum"`, `"... ile savasiyorum"`, `"...'nin pesindeyim"`, etc.)
with a proper `tr` passthrough and an `en` regex table translating from
Turkish. `GEAR_HISTORY_HOWS` and the `api_bot_gear_history` language
selector got the same `"tr"` treatment.

Verified with `python3 -m py_compile files/admin_panel.py` after every batch
of edits, and a final full re-scan of the file for Polish diacritic
characters not paired with a `tr`/`"tr"` counterpart nearby - the ~185
remaining hits were all confirmed false positives (multi-line dict entries
where `tr:`/`"tr"` sits a few lines away from the flagged `pl` line, or JS's
unquoted `tr:` object-key shorthand which the sweep's `"tr"`-with-quotes
check didn't recognize) by reading the surrounding code directly, not just
the grep. No compiler run, no live UI test - this is a syntax-checked
translation pass on a Flask app with no local server to click through, so
say so plainly: what changed is proven to parse, not observed rendering
correctly in a browser.

**Deliberately not done in this pass** (each is its own job): seban-panel,
the ItemShop PHP front end, and the mt2009 client's other Python UI files.
`item_names_tr.txt`/`item_names_pl.txt` (the actual root cause of the
`kılıç` -> `kylyc`-style corruption reported earlier) are supplied by the
operator's own server package, not part of this repo, and can't be fixed
from here without that file.

## Follow-up: second upstream sync, 2.0.19 -> 2.0.24 (2026-09-13)

Asked to pull the next batch of upstream releases in without losing any of
our work, staying on `claude/sync-updates-client-o7hk2w`, no PR to upstream.
Ten commits / five releases (`v2.0.20`-`v2.0.24`): prize-weapon equipping,
the archer's stone-dagger refine floor, teleport-ring recall, a lossless bag
sort, ItemShop Dragon Coins dropping from metins/bosses, an operator item-
policy file (per-vnum or per-type keep/stall/merchant/drop, read like the
weights), spares going to the safebox past a refine threshold instead of
riding the counter forever, and - notably - the classic panel's passphrase
requirement dropped on the single-player line.

Four real conflicts, all resolved by keeping both sides rather than
picking one:

- **README.md / README_EN.md** - pure feature-list prose, nothing of ours
  in it; took upstream's newer paragraphs whole.
- **playerbot_types.h** - our Turkish `GetPlayerBotShopReasonName()` against
  upstream's new `PLAYERBOT_SHOP_REASON_SPARE` case (the "sell a worse
  duplicate" feature); kept our Turkish for the other cases and translated
  the new one (`"gereksiz kopya"`).
- **admin_panel.py**, twice - upstream's new `item_full_name()` (spells a
  skill book's skill out from `SKILL_ID_NAMES`/`SKILL_ID_NAMES_PL`, flattened
  from `PLAYER_SKILLS`/`PLAYER_SKILLS_EN`) landed right next to our
  `HUNTING_MOB_NAMES_TR` and `PLAYER_SKILLS_TR` additions. Added a third
  `SKILL_ID_NAMES_TR` table, flattened from our `PLAYER_SKILLS_TR`, and gave
  `item_full_name()` a `tr` branch so a Turkish panel view gets skill-book
  names spelled out in Turkish too, not just English. Third conflict was
  `GEAR_HISTORY_HOWS` gaining three new upstream entries
  (`PLAYERBOT_BONUS_ADD/_CHANGE/_MARBLE` for the reworked bonus-line system)
  next to our `"tr"` keys on the existing ones - added Turkish to the three
  new entries the same way.

Beyond the conflicts: translated the brand new admin-panel page this sync
brought in, the Item Policy editor (`ai_items_open/_nav/_intro/_format/
_bad/_live` in the `T` dict - upstream itself only shipped `en`/`pl` for
these, so `tr` was a straight addition, not a fix). The policy file's own
keyword syntax (`keep`/`stall`/`merchant`/`drop`, which upstream already
accepts in Polish too as `zostaw`/`stragan`/`handlarz`/`wyrzuc`) got Turkish
synonyms added on both ends of the pipe - the engine's
`ParsePlayerBotItemPolicyWord()` in `playerbot_config.h` and the panel's own
`AI_ITEM_POLICY_WORDS` validator - so an operator can write `sakla`/
`tezgah`/`satici`/`birak` in the file and have both sides agree on it.

Swept every other file this sync auto-merged cleanly (no conflict, but new
upstream content): all ten touched `playerbot_*.h` fragments plus
`playerbot_manager.cpp`, the mt2009 tree (`playerbotify.py`,
`m2-render-config` - the Dragon Coin plumbing), and seban-panel
(`app.py`/`collector.py` - five new Polish `BOT_ACTIONS` labels for stall-
keeping/fishing/browsing-stalls/luring/resting, and the panel now skips its
setup wizard on the single-player line same as the classic panel). Nothing
found beyond what's listed above - the rest was log-message formats
(`PLAYERBOT_...:` prefixed, operator-facing by convention), internal state
tags, and quoted reporter comments, none of it player-visible UI text.
The five new seban-panel labels are genuinely untranslated (seban-panel has
no i18n layer at all yet, in any language but Polish) - that's the next,
separate task.

**Not run**: the `g++ -fsyntax-only -m32 -std=c++23` check CLAUDE.md
prescribes - same as the first sync, this sandbox has no `../m2src-cache`
reference tree and no running Docker daemon this time either (`docker info`
reaches the client but not a daemon socket). Checked instead: brace/paren
balance on every touched C++ file (all matched), and that every new
constant/function/enum-case upstream introduced actually resolves somewhere
in the include chain (checked by name, file by file) - including one
harmless loose end that's upstream's own, not ours:
`PLAYERBOT_BONUS_MARBLE_LINES` is defined in `playerbot_types.h` but never
read anywhere; the actual "want a 5th line" test uses
`PLAYERBOT_BONUS_MAX_LINES` instead. Left as-is - not something this merge
introduced or broke, and not ours to second-guess upstream's own constant.
**Run the real syntax check by hand before deploying this branch.**

## Follow-up: seban-panel translated to Turkish (2026-09-13)

Asked to translate seban-panel (`linux-port/docker/seban-panel/`) to Turkish,
the same way the classic panel was done earlier - but seban-panel has no
language-switching layer at all (unlike `files/admin_panel.py`'s `T` dict +
`lang()`), so this is a straight swap: every Polish string in `app.py`,
`item_grants.py`, all 19 Jinja templates, and the four `static/*.js` files
now reads in Turkish. No bilingual toggle was built - the user asked for a
direct swap, not a second i18n system.

**Scope**: `app.py` (~2010 lines - map names, bot personality/goal/action
labels, the `APPLY_LABELS` bonus-line table, flash messages, SQL literal
strings shown to the operator, the crashed-table error page's inline HTML),
`item_grants.py` (status labels, validation messages), every template
(`manage.html` and `item_grants.html` were the two big ones, both dense
single-line Jinja), and `heatmap.js`/`news-feed.js`/`live-widget.js`
(`dashboard-charts.js` had nothing to translate).

**A scripted edit corrupted app.py once, caught before it shipped.** A
Python script meant to replace only the `APPLY_LABELS` dict used
`re.search(r'APPLY_LABELS = \{(.*?)\n\}', ...)` - non-greedy but still
DOTALL, so `.*?` matched forward to the *first* `\n}` anywhere in the file
after the dict, not the dict's own close brace (which sits on the same line
as its last entry, no `\n` before it). That swallowed everything in
between and deleted it: the 71/72-swap comment, `PANEL_ENGINE`,
`ENGINE_MT2009`, `ATTR_SKILL_DAMAGE`, `ATTR_AVG_DAMAGE`,
`POINT_TO_APPLY` (a 30-line dict the mt2009 bonus-line lookup depends on),
`EMPIRE_EXPR`, `JOB_NAMES` and the whole `SKILLS` table - 45 net lines
gone, and `python3 -m py_compile` still passed because what was left was
syntactically valid Python that just did less. Caught by line-counting the
file after every edit (`wc -l` against the pre-edit count) rather than
trusting compile success alone; the missing block was pulled back from
`git show HEAD:...` and reinserted, translated, and the rest of the file
was then done with the Edit tool's exact-string matching instead of a
regex that could over-match. Every edit after that point was followed by
`wc -l` and a `py_compile` check.

**Two things translation touched that were not just text:**
- `is_stationary_activity()`'s fishing-detection fallback matched Polish
  substrings (`"łowi"`, `"ryb"`, `"czekam na branie"`) against the bot's
  free-text status - but that status has come from the C++ core's Turkish
  `playerbot_llm_status.h` for a while now (`"Balik tutuyorum - oltayi
  bekliyorum"`), so the fallback had already gone dead before this session
  touched it. Same root cause as the `localize_playerbot_status()` bug
  found in the classic panel a day earlier - a Polish-text-matching
  fallback outliving the switch to Turkish bot speech. Fixed to match
  `"balik"`/`"olta"`/`"fishing"`.
- `static/live-widget.js`'s `activityGroup()` had the identical shape:
  `/łow|low|ryb|fishing|branie/` tested against `bot.action_label`, which
  is `BOT_ACTIONS[...]` from `app.py` - now Turkish ("Balık Tutuyor" for
  action id 14). Fixed to `/bal[ıi]k|tutuyor|fishing/`.
- `character["honor"]["css"]` in the `/player/<pid>` route looked up a CSS
  class by the honor title string (`"Rycerski"`, `"Szlachetny"`, ...) -
  translating `honor_rank()`'s returned titles without updating this
  lookup would have thrown a `KeyError` on every profile page. Caught
  before it shipped by grepping for every reader of a value this session
  translated, not just the definition.

**`gm_commands.txt`** (148 lines, the in-game GM command reference shown
verbatim in `<pre>`) was translated in full too - command syntax
(`/purge`, `<nick>`, vnum placeholders) kept as-is, only the Polish
explanations translated.

**Deliberately left in Polish** (two spots, both querying stored engine
data rather than displaying UI text): `app.py`'s two `'%małż%'`/`"małż"`
matches, which search `log.log`'s `hint` column for the Polish word for
"mussel" - that column holds whatever the game engine's own (Polish, on
this world) item names wrote into it, not a string this panel controls,
so changing the search pattern would just break shellfish-catch detection
instead of translating anything. Same reasoning as the untouched `'%ryb%'`/
`'%fish%'` OR in the weekly fish-ranking query.

**Verification**: `python3 -m py_compile` on every changed `.py` file,
`node --check` on every changed `.js` file, a full diacritic sweep of the
whole `seban-panel/` tree (two intentional exceptions above, plus one
inert dead-code line in `live-widget.js` that already matched nothing
before this session - a `.textContent.includes('Podkład graficzny')`
filter with no matching element anywhere in the current templates), and
`{%`/`%}`/`{{`/`}}` tag-count parity against `git show HEAD:...` for
every one of the 19 templates. All 17 simple templates were rendered
through `render_template()` with representative context and returned
without a Jinja error; `manage.html` and `item_grants.html` were rendered
through the real Flask routes with the DB mocked out. Ran the existing
`test_manage_settings.py` end to end (installed Flask/PyMySQL into this
sandbox to do it) and fixed the assertions that pinned old Polish text
(`SKILLS[(0,1)][3]`, four `MAP_NAMES` entries, `class_profile(6)['gender']`)
to their Turkish replacements. One assertion
(`playerbots_release_status()['tone']`) fails in this sandbox with no
outbound GitHub access - confirmed pre-existing by running the identical
test against the pre-translation file via `git stash`. A second failure,
`TRACKED_MAP_OPTIONS` not matching its hardcoded expected list, is also
pre-existing (reproduces identically against `git stash`) and predates
this session - the list is stale against the Shinsoo/Jinno maps the
2.0.19→2.0.24 sync (and earlier syncs) added to `MAP_BOUNDS`; worth a
follow-up but out of scope for a translation pass. No live browser test -
this is a Flask app with no running server in this sandbox, so "renders
without a Jinja/JS error" is what was verified, not "looks right on
screen."

## Follow-up: third upstream sync, 2.0.24 -> 2.0.28 (2026-09-13)

Brought in 8 upstream commits (TieruYT/metin2-playerbots): the mt2009 line's
new real offline-shop feature (an ikashop stand replaces the classic stall,
2.0.26), a core-crashing 64-bit-yang log-format bug fix, a weapon-scoring
rewrite ("score a weapon by one hit"), and assorted stall/world-reset fixes.
Merge commit: `merge(upstream): sync 2.0.24 -> 2.0.28`.

Before merging, fetched `origin/claude/sync-updates-client-o7hk2w` and found
it 5 commits ahead of what this session had locally (`d90b04f` and earlier) -
unrelated work from another session/process: pointing this fork's own update
checks at `debaba13/metin2-playerbots` instead of upstream (see
`UPDATE_SOURCE_2026-09-13.md`), an mt2009 quest fix, and the manifest file
list glob fix upstream also independently made (see below). Fast-forwarded
onto it before starting the upstream merge.

### The `playerbot_llm_*.h` family is fork-only, not an upstream feature

Before merging, `git diff --stat HEAD upstream/main` looked alarming -
`playerbot_llm_status.h`, `playerbot_llm_bridge.h`, `playerbot_llm_chat_trade.h`,
`playerbot_llm_shop.h` and the whole `mmo-llm-adapter/` Python tree all showed
as full deletions. Checked against the merge-base (`08e3729`, upstream's own
2.0.24 tip) before assuming upstream had ripped out a shared subsystem: none
of these paths exist there, nor on `upstream/main`'s current tip. They are
**this fork's own prior work** (see the `mmo-llm-adapter`/"isolate llm status
and chat seams" commits in this branch's own history, predating even the
2.0.19 sync) - upstream never had them, so the "deletion" in that diff was
never a real conflict; the merge left them untouched, as expected.

Despite the name, `playerbot_llm_status.h` is not an actual LLM/network
integration - it is a full from-scratch Turkish rewrite of upstream's status-
text generator (verified by reading it: plain `snprintf`/`switch` logic, no
HTTP, no API client). The established pattern for this pair (set by the
1.31.2 -> 2.0.14 sync, `0a60803`) is: **keep the thin stub**
(`playerbot_status.h`/`playerbot_chat_trade.h` reduced to one `#include` of
their `_llm_` counterpart) **and port the functional delta by hand** into the
Turkish file, rather than adopting upstream's Polish rewrite wholesale. Reused
that pattern again here rather than reopening the architecture question.

### Conflicts (4)

- **`launcher/server-update-files.mt2009.txt`** - both sides independently
  fixed the same problem: our HEAD side had grown the explicit `playerbot_*.h`
  enumeration to include the fork's own `playerbot_language.h`/`playerbot_llm_*.h`
  files (from the 5-commits-ahead fast-forward above); upstream replaced the
  whole enumeration with a `playerbot_*` glob, matching the r40250 list's
  existing pattern and CLAUDE.md's "never write another list" rule (its own
  commit even names the exact failure mode: a new file, `playerbot_offline_policy.h`,
  missing from the enumerated list broke the packager). Took upstream's glob -
  strictly better, self-maintaining, and it covers every fork-only file
  automatically with no listing needed.
- **`playerbot_manager.cpp`** - both sides added a new `#include` on the same
  line after `playerbot_market.h`: ours `playerbot_language.h` (the Katman 2a
  translation table from `CEVIRI_REHBERI.md`), upstream's
  `playerbot_offline_market.h` (new, the offline-shop buyer side - its own
  header comment requires it directly after `playerbot_market.h`). Kept both,
  offline_market.h first per its stated requirement, language.h after (order-
  independent, confirmed `playerbot_chat_trade.h` calls neither `PlayerBotText`
  nor `FormatPlayerBotText` so nothing forces a stricter order).
- **`playerbot_status.h`** - see above. Diffed upstream's one actual new commit
  here (`e03a3d6`) against the merge-base version to find the real delta: a
  `%d` -> `%lld` fix for `GetGold()` (64-bit on the 2.x line) in the Teleporter-
  fee status line - a core-crashing bug (see next section). Ported that one
  line into `playerbot_llm_status.h`'s equivalent Turkish line and kept the
  stub, discarding upstream's ~570-line Polish rewrite of this file as in the
  precedent sync (it stays retrievable from upstream's own history/repo if
  ever needed - not worth carrying as `#if 0`'d dead code in this tree).
- **`update-manifest-mt2009.json`** - upstream's `chore(release)` commits bump
  `server.version`/`url`/`sha256` to their own `TieruYT/metin2-playerbots`
  v2.0.27 release zip; this fork's manifest deliberately points at
  `debaba13/metin2-playerbots` releases instead (established by the 5-commit
  fast-forward's own `UPDATE_SOURCE_2026-09-13.md`). Kept our side unchanged
  (still naming the v2.0.24 fork release) rather than bump the version number
  to 2.0.27/28 with upstream's sha256, which would point the launcher's
  "install the update" button at a zip this fork has not built or published
  under that name/hash. **This is now a known gap, same shape as the one
  `UPDATE_SOURCE_2026-09-13.md` already documents**: the manifest under-
  reports the version relative to what the code in this branch actually
  contains (2.0.28-equivalent), until someone runs `New-M2UpdatePackage.ps1`
  and publishes a matching `debaba13/metin2-playerbots` release with a real
  sha256 and bumps this file to match.

### The core-crash bug, and what else needed the same fix

`YANG`/`GetGold()` is `long long` on the 2.x line; thirteen log/status lines
across the overlay still passed it to a bare `%d`. Twelve just printed wrong
numbers; the Teleporter-refusal status line had `gold` in the middle of a
format list with `reason=%s` after it, so the 8-byte value ate two argument
slots, everything after it shifted, and `%s` read a map-index integer as a
`char*` - SIGSEGV on every refusal, silently, because the crash happened
before the line could reach any log. All twelve of the non-status-text
instances (in `playerbot_activities.h`, `playerbot_bonus.h`, `playerbot_market.h`,
`playerbot_skills.h`, `playerbot_town.h`, `playerbot_travel.h`) auto-merged
cleanly with no conflict, since our side hadn't touched those exact lines -
verified after the fact by grepping each fixed symbol (`teleporter refuses`,
the new `PLAYERBOT_USE_AFFECT_TIMED_BUFF`/`PLAYERBOT_EXP_ELIXIR_VNUMS`/
`PLAYERBOT_METIN_DETECTOR_VNUMS` constants) to confirm they landed. The
thirteenth instance was the Teleporter status line inside the stubbed-out
`playerbot_status.h` - upstream's fix couldn't reach it because our side
doesn't compile that file's body at all - so it needed the manual port
described above. Also swept every fork-only `playerbot_llm_*.h` file for the
same `GetGold()`-next-to-`%d` shape in case the bug had been copied in
during the original translation; found none beyond the one instance.

### Audited for new player-visible text; found none needing translation

Every upstream commit in this range touching the playerbot overlay was
checked individually (`git log <merge-base>..upstream/main -- <file>` per
file, then `git show <commit> -- <file>`) rather than trusting the merge to
surface everything, since a change that auto-merges cleanly never shows up as
a conflict to review. The new offline-shop files (`playerbot_offline_shop.h`,
`playerbot_offline_market.h`, `playerbot_offline_policy.h`, ~450 lines, all
gated behind `PLAYERBOT_ENGINE_MT2009 && ENABLE_IKASHOP_RENEWAL`, r40250
untouched) contain zero player-visible strings - pure state-machine and
journal logic, `PLAYERBOT_OFFLINE:`-prefixed operator log lines only. A
repo-wide grep of `git diff <merge-base> upstream/main` for any added quoted
string with a Polish diacritic, and separately for any added
`snprintf(status, ...)`/`PlayerBotText(`/`FormatPlayerBotText(` call, turned
up only the one Teleporter line already handled above.

`files/admin_panel.py` got one real upstream change in this range (`30e571b`):
a new `shops` ranking SQL branch reading `player.ikashop_offlineshop` on the
mt2009 engine, reusing the existing (already-translated) map-label dict for
its output - no new strings. `linux-port/docker/seban-panel/` got zero
changes in this range; the large diff `git diff HEAD upstream/main` showed
for it was entirely pre-existing (the direct-Turkish-swap work from the
previous session), confirmed via `git log <merge-base>..upstream/main --
linux-port/docker/seban-panel/` returning empty.

### Verified

- `python3 -m py_compile` on `files/admin_panel.py`, `linux-port-mt2009/port/playerbotify.py`,
  `linux-port-mt2009/port/listify.py`; `python3 -c "import json; json.load(...)"`
  on `update-manifest-mt2009.json`.
- `tests/playerbot_world_rules_test.cpp` (existing) and
  `tests/playerbot_offline_policy_test.cpp` (new, Codex's, kept as-is per
  upstream's own commit) both compiled and ran clean locally with plain g++
  (13.3.0) - the offline-policy test needs no engine headers at all
  (`-I linux-port/overlays/playerbot/src/game/src`, per the build command in
  its own header comment).
- Manual brace/paren-balance and `#ifndef`/`#endif` count check on every
  hand-edited file (`playerbot_manager.cpp`, `playerbot_status.h`,
  `playerbot_llm_status.h`) - all balanced.
- **Not verified**: the real `g++ -fsyntax-only -m32 -std=c++23` check against
  `../m2src-cache/tree/port40250/server` that CLAUDE.md prescribes. Neither
  `m2src-cache` nor a running Docker daemon is present in this sandbox (same
  limitation the 1.31.2 -> 2.0.14 sync's notes recorded) - run it by hand
  before deploying this branch.
- Repo-wide `git grep` for leftover `<<<<<<<`/`=======`/`>>>>>>>` conflict
  markers: none.
