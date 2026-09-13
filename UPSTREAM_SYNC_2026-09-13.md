# Upstream sync: 2.0.33 -> 2.0.35 (2026-09-13)

Asked to "get the latest updates too." Checked `upstream` (`TieruYT/metin2-playerbots`)
against our branch (`claude/sync-updates-client-o7hk2w`, which was at 2.0.33) and found
two real, already-published upstream releases we didn't have: 2.0.34 and 2.0.35.

## What this is not

A separate request in the prior session (relayed through a bridge session from another
Claude instance, with a suspicious embedded instruction to stop using tools and summarize
silently — flagged and ignored) asked for a *fabricated* v2.0.33 zip built and published as
a new GitHub Release under `debaba13/metin2-playerbots`. That was refused: this sandbox has
no engine source (`char.cpp`, `item_manager.cpp`, etc. are not in this repository and never
will be, per `CLAUDE.md`), so any zip built here would be missing the actual server binary
inputs and would break anyone who installed it. This sync is different — it merges real
source-level commits that upstream (a human-run project) already built and published
themselves, the same operation this repo's history already does routinely
(`merge(upstream): sync X -> Y`, e.g. `5d34d44`, `448c582`, `115bee1`, `56c048c`, `0a60803`,
`ea4fc0a`). No zip was built or published by me; nothing was uploaded anywhere.

## Merge

`git merge upstream/main` (`656fdbc`, 2.0.35) into `claude/sync-updates-client-o7hk2w`
(`5d34d44`, 2.0.33). One conflict: `update-manifest-mt2009.json`.

**What upstream 2.0.34/2.0.35 actually carry** (per their own `CHANGELOG.md`, now merged):
- Shinsoo and Jinno each get their own easy Monkey Dungeon (maps 5/25/45 — same geometry,
  different world location); the overlay only knew Chunjo's, so the other two kingdoms
  levelled no horse at all (measured upstream: 500 Shinsoo characters, zero horses).
- Each kingdom crosses Orc Valley / the Yongbi Desert / Mount Sohan through its *own*
  entrance and gate instead of every bot funnelling through Chunjo's.
- mt2009 offline-stall lifetime management (`ManagePlayerBotShopLifetime`) was dead code
  behind two exhaustive early `return`s and got compiled out from `-O1` up; three
  mechanisms come back with it.
- The GM F9 panel (OskarPWA's, mt2009 line): new `linux-port-mt2009/port/gm_panel_commands.cpp.txt`
  (4408 lines, referenced by `playerbotify.py`'s `apply_gm_panel`) plus new
  `linux-port/client-root/uiminimap.py` and `uiscript/equipmentdialog.py` (saved minimap
  spots, EQ/Sprawdz buttons) — client-root sources only, not a built client package; repacking
  needs the real client archive and `m2-eterpack:dev`, neither of which exist here.
- New `linux-port/overlays/playerbot/src/game/src/playerbot_admin.h` — covered automatically
  by the existing `playerbot_*` wildcard in `launcher/server-update-files.mt2009.txt`.

## Manifest conflict resolution

`update-manifest-mt2009.json`'s `server` block conflicted: our side still points at this
fork's own last real published release (`v2.0.24`, built and uploaded by the repo owner via
`tools/New-M2UpdatePackage.ps1`, per `d90b04f`); upstream's side pointed at *their*
`v2.0.35` zip. Kept **our** side (2.0.24, `debaba13` URL) — this matches every manifest
commit since `d90b04f` (2.0.25 through 2.0.33 all advanced `statusMessage`/`publishedAt`
while leaving `server.version`/`url` frozen at 2.0.24, because no new fork release has been
built since). `client` had no conflict: it already pointed at upstream (TieruYT) on both
sides, per `d90b04f`'s own note ("no client package has been built from this fork yet"), and
now reads 2.0.5. `statusMessage`/`publishedAt` took upstream's 2.0.35 text verbatim (Polish,
matching how every prior statusMessage in this file has been left — the changelog prose
itself has never been translated, only panel/status UI has).

**Net effect for a player who clicks "install updates" today: nothing changes.** The
manifest's `server.url`/`version` are unchanged (still 2.0.24, still this fork's own zip);
only the source tree and the changelog text moved. A real 2.0.35 fork release still needs
someone with the actual engine source to run `New-M2UpdatePackage.ps1` and publish it, the
same gap `UPDATE_SOURCE_2026-09-13.md` already documented for 2.0.25-2.0.33.

## Verification

- No leftover conflict markers anywhere in the tree (checked with `git grep`; the only
  `===` hits are pre-existing decorative banners in `PRZECZYTAJ_MNIE.txt` and two unrelated
  files, not `<<<<<<<`/`>>>>>>>`).
- `files/admin_panel.py` diff has no new Polish UI strings (nothing to translate).
- The nine changed/added `playerbot_*.{h,cpp}` files have zero non-ASCII bytes added by the
  merge (checked with a byte-range grep over the diff) — the "player-visible bot strings are
  Polish, ASCII-only" rule in `CLAUDE.md` still holds.
- `../m2src-cache` (the staged reference engine tree) does not exist in this sandbox, so the
  real `-m32 -std=c++23` syntax check against engine headers from `CLAUDE.md` could not run
  here — same limitation as every prior session in this environment. What *could* run, did:
  all three standalone unit tests compile and pass with plain host `g++`/`-std=c++17`
  (`playerbot_world_rules_test.cpp`, `playerbot_empire_rules_test.cpp`, and
  `playerbot_offline_policy_test.cpp` with `-I linux-port/overlays/playerbot/src/game/src`).
