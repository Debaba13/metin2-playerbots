# Pointing the update check at this fork instead of upstream (2026-09-13)

Asked to make "is there a new version?" ask this repository (`debaba13/metin2-playerbots`)
rather than upstream (`TieruYT/metin2-playerbots`), and to write down how.

## What actually checks for an update, and where each one looked

Four independent places fetch something from GitHub to answer "is there a
newer version," and each had its own hard-coded `TieruYT/metin2-playerbots`:

| What | File | What it does |
|---|---|---|
| The GUI launcher's update button | `launcher/Metin2Launcher.psm1` | Fetches `update-manifest.json` (r40250) or `update-manifest-mt2009.json` (mt2009) from `raw.githubusercontent.com`, by `ENGINE`. |
| The mt2009 line's own updater container | `linux-port-mt2009/tools/update.sh` | Same manifest, fetched through GitHub's contents API (`$REPO`/`$BRANCH`, both already environment-overridable — only the *defaults* pointed upstream). |
| The advanced (Seban) panel's "new version available" badge | `linux-port/docker/seban-panel/app.py` (`PLAYERBOTS_RELEASE_URL`) | GitHub's `releases/latest` API. |
| Container labels | `linux-port/docker/panel/Dockerfile`, `linux-port/docker/wsbridge/Dockerfile` | `org.opencontainers.image.source` — cosmetic, not a live check, changed for consistency. |

All four now point at `debaba13/metin2-playerbots`. The two manifest fetches
(launcher and `update.sh`) also had to change **branch**, not just owner: this
fork's actual work lives on `claude/sync-updates-client-o7hk2w`, not `main` —
pointing at `main` would have found this fork's own (older) `main`, which does
not carry the mt2009 line, the Turkish translation, or any of this session's
fixes.

## The one thing this does *not* fix yet

`update-manifest-mt2009.json` (and `update-manifest.json`) are **data**, not
code — they were last written by `chore(release)` commits and their
`server.url` / `client.url` fields still point at
`github.com/TieruYT/metin2-playerbots/releases/download/...`. Pointing the
*check* at this repo means the launcher now reads *this repo's copy* of that
JSON file, but that copy still names TieruYT's release assets, because nobody
has published a release under `debaba13/metin2-playerbots` with our own
`metin2-server-update-*.zip`. Concretely: "check for updates" will correctly
report the version this repo's `VERSION` file says (once a release commit
updates the manifest here, rather than only upstream); "install the update"
will still download upstream's stock zip until this fork publishes its own
release (`New-M2UpdatePackage.ps1` + a GitHub Release with the zip attached) —
which is a real gap, not a decision to leave it that way.

## Not touched, deliberately

- `installer/install.ps1` / `install.sh` (`M2_REPO_URL`, default clone source
  for a *fresh* r40250 install from scratch) — a different surface (bootstrap,
  not "check an existing install for updates"), and the r40250 line is not
  what this session worked on. Change it the same way if a fresh-install
  clone of this fork is ever wanted.
- Historical/attribution mentions of TieruYT in `README.md`, `CHANGELOG.md`,
  `docs/*.md`, `PACZKA_INFO.txt`, `.github/workflows/sync-upstream.yml` — these
  describe where the project came from and how it stays synced with upstream,
  which is still true and should not be rewritten.
