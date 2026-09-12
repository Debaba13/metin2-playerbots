#!/bin/sh
# =============================================================================
#  update.sh -- the 2.x (mt2009) line's update on Linux, without the launcher.
#
#  The 1.x line updates a Linux server by refreshing a git checkout of the
#  repository and re-running its installer (installer/install.sh, m2-updater).
#  That path knows nothing about this line: the repository's root VERSION is
#  the 1.x line's, install.sh stages the 1.x tree over whatever it finds, and
#  a 2.x server that ran it ended up with VERSION 1.33.3, the 1.x rates
#  script and a panel that could not talk to its game (l0st3k, 12 September:
#  "checkout z main melduje 1.33.3", rates stuck in state=running for 12 h,
#  no stalls, the panel's update stopping at 40%).
#
#  This line is delivered the way the Windows launcher delivers it: a package
#  zip published on GitHub and named by update-manifest-mt2009.json. This
#  script does exactly that on Linux --
#
#      sh linux-port/tools/update.sh            # from the server folder
#
#  1. reads the manifest (GitHub contents API, then raw as a fallback),
#  2. downloads the server zip it names, checks its SHA-256,
#  3. unpacks it over this folder (files the zip carries are replaced; .env,
#     docker-compose.override.yml and everything else stay as they are),
#  4. runs `docker compose up -d --build' in linux-port/docker.
#
#  Nothing here removes a volume: the database, characters, items and guilds
#  are in volumes, and `down' does not appear in this file in any form.
#
#  `sh update.sh watch' is the updater container's mode: it polls the panel's
#  spool for a request (the same request/update.status/update.log files the
#  1.x m2-updater uses, see linux-port/docker/updater/bin/m2-updater) and runs
#  the sequence above on each one. `sh update.sh check' only prints what is
#  installed and what is published.
#
#  Needs: docker with compose, and either python3 or curl + unzip + sha256sum.
# =============================================================================
set -u

# The server folder is two levels up from this file (Serwer/linux-port/tools).
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=${M2_UPDATE_STACK_DIR:-$(cd "$HERE/../.." && pwd)}
COMPOSE_DIR="$ROOT/linux-port/docker"
REPO=${M2_UPDATE_REPO:-TieruYT/metin2-playerbots}
BRANCH=${M2_UPDATE_BRANCH:-main}
MANIFEST_NAME=update-manifest-mt2009.json
SPOOL=${M2_UPDATE_SPOOL:-/opt/m2update}
POLL=${M2_UPDATE_POLL:-5}
WORK=${TMPDIR:-/tmp}/m2-update.$$

now() { date '+%Y-%m-%d %H:%M:%S'; }
say() { printf '%s [update] %s\n' "$(now)" "$*"; }
die() { say "ERROR: $*"; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# ---- the pieces that need a tool ---------------------------------------------
# GitHub's raw CDN can lag a release by minutes; the contents API does not.
fetch_text() {
    _url=$1
    if have python3; then
        python3 - "$_url" <<'EOF'
import sys, urllib.request
req = urllib.request.Request(sys.argv[1], headers={
    'User-Agent': 'metin2-playerbots-update/2 (+https://github.com/TieruYT/metin2-playerbots)',
    'Accept': 'application/vnd.github.raw+json'})
sys.stdout.write(urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace'))
EOF
    elif have curl; then
        curl -fsSL -A 'metin2-playerbots-update/2' -H 'Accept: application/vnd.github.raw+json' "$_url"
    else
        die "neither python3 nor curl is installed"
    fi
}

fetch_manifest() {
    fetch_text "https://api.github.com/repos/$REPO/contents/$MANIFEST_NAME?ref=$BRANCH" 2>/dev/null \
        || fetch_text "https://raw.githubusercontent.com/$REPO/$BRANCH/$MANIFEST_NAME"
}

# manifest_field FILE KEY -> the server block's field (version, url, sha256).
manifest_field() {
    if have python3; then
        python3 - "$1" "$2" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1], encoding='utf-8-sig'))
print(m.get('server', {}).get(sys.argv[2], ''))
EOF
    else
        # No JSON parser without python: take the server block by hand. The
        # manifest is written by us, two spaces of indentation, one key a line.
        sed -n '/"server"/,/}/p' "$1" | sed -n "s/.*\"$2\": *\"\([^\"]*\)\".*/\1/p" | head -n 1
    fi
}

download() {
    _url=$1; _out=$2
    if have curl; then
        curl -fL --retry 3 -A 'metin2-playerbots-update/2' -o "$_out" "$_url"
    elif have python3; then
        python3 - "$_url" "$_out" <<'EOF'
import sys, urllib.request, shutil
req = urllib.request.Request(sys.argv[1], headers={'User-Agent': 'metin2-playerbots-update/2'})
with urllib.request.urlopen(req, timeout=120) as r, open(sys.argv[2], 'wb') as f:
    shutil.copyfileobj(r, f)
EOF
    else
        die "neither curl nor python3 is installed"
    fi
}

sha256_of() {
    if have sha256sum; then sha256sum "$1" | cut -d' ' -f1
    elif have shasum; then shasum -a 256 "$1" | cut -d' ' -f1
    elif have python3; then python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"
    else die "no sha256sum, shasum or python3 to check the download with"
    fi
}

# The zip is laid out relative to the server folder (VERSION, CHANGELOG.md,
# linux-port/..., launcher/..., tools/...), with backslashes in some entry
# names -- Windows made it. Python's zipfile takes both; unzip needs the
# names normalised, so python is preferred.
unpack_over() {
    _zip=$1; _dst=$2
    if have python3; then
        python3 - "$_zip" "$_dst" <<'EOF'
import os, sys, zipfile
z = zipfile.ZipFile(sys.argv[1]); dst = sys.argv[2]; n = 0
for info in z.infolist():
    name = info.filename.replace('\\', '/')
    if name.endswith('/') or name.startswith('/') or '..' in name.split('/'):
        continue
    target = os.path.join(dst, *name.split('/'))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with z.open(info) as src, open(target, 'wb') as out:
        out.write(src.read())
    if name.endswith('.sh'):
        os.chmod(target, 0o755)
    n += 1
print('unpacked %d files' % n)
EOF
    elif have unzip; then
        unzip -o -q "$_zip" -d "$_dst"
    else
        die "neither python3 nor unzip is installed"
    fi
}

installed_version() { tr -d ' \r\n' < "$ROOT/VERSION" 2>/dev/null || printf 'unknown'; }

# ---- sanity ------------------------------------------------------------------
check_tree() {
    [ -f "$ROOT/VERSION" ] || die "no VERSION in $ROOT -- run this from the server folder (the one with linux-port/ in it)"
    [ -f "$COMPOSE_DIR/docker-compose.yml" ] || die "no linux-port/docker/docker-compose.yml under $ROOT"
    if [ -f "$COMPOSE_DIR/ENGINE" ] && [ "$(tr -d ' \r\n' < "$COMPOSE_DIR/ENGINE")" != "mt2009" ]; then
        die "this folder is not the 2.x (mt2009) line -- its ENGINE marker says $(cat "$COMPOSE_DIR/ENGINE"); the 1.x line updates through installer/install.sh"
    fi
    if [ -d "$ROOT/installer" ] && [ ! -f "$COMPOSE_DIR/ENGINE" ]; then
        die "this looks like a 1.x checkout (installer/ present, no ENGINE marker); this script is for the 2.x package"
    fi
}

# ---- the sequence ------------------------------------------------------------
STEP=0; STEPS=4
STATUS="$SPOOL/update.status"; LOG="$SPOOL/update.log"
WATCHING=0
set_status() {
    [ "$WATCHING" = 1 ] || return 0
    ( umask 007
      { printf 'state=%s\n' "$1"; printf 'time=%s\n' "$(date +%s)"; printf 'step=%s\n' "$STEP"
        printf 'steps=%s\n' "$STEPS"; printf 'message=%s\n' "$2"; } > "$STATUS.new" ) && mv "$STATUS.new" "$STATUS"
    return 0
}
note() { say "$*"; [ "$WATCHING" = 1 ] && printf '%s %s\n' "$(now)" "$*" >> "$LOG" 2>/dev/null; return 0; }
step() { STEP=$((STEP + 1)); note "[$STEP/$STEPS] $*"; set_status running "$*"; }
fail() { note "FAILED: $*"; note "   nothing was removed; the server keeps running the version it had"; set_status failed "$1"; return 1; }

run_update() {
    STEP=0
    rm -rf "$WORK"; mkdir -p "$WORK" || { fail "cannot create $WORK"; return 1; }
    step "reading what is published"
    fetch_manifest > "$WORK/manifest.json" 2>"$WORK/fetch.err" || { fail "the manifest could not be read: $(head -c 200 "$WORK/fetch.err")"; return 1; }
    _ver=$(manifest_field "$WORK/manifest.json" version)
    _url=$(manifest_field "$WORK/manifest.json" url)
    _sha=$(manifest_field "$WORK/manifest.json" sha256 | tr 'A-F' 'a-f')
    [ -n "$_ver" ] && [ -n "$_url" ] && [ -n "$_sha" ] || { fail "the manifest has no server version, url or sha256"; return 1; }
    note "   installed $(installed_version), published $_ver"
    if [ "$(installed_version)" = "$_ver" ] && [ "${FORCE:-0}" != 1 ]; then
        note "   already on $_ver -- nothing to do (FORCE=1 to unpack it again)"
        set_status ok "the server is running version $_ver"
        return 0
    fi
    step "downloading $(basename "$_url")"
    download "$_url" "$WORK/update.zip" || { fail "the download failed"; return 1; }
    _got=$(sha256_of "$WORK/update.zip" | tr 'A-F' 'a-f')
    [ "$_got" = "$_sha" ] || { fail "the download's SHA-256 ($_got) is not the manifest's ($_sha)"; return 1; }
    step "unpacking $_ver over $ROOT"
    unpack_over "$WORK/update.zip" "$ROOT" || { fail "the zip could not be unpacked"; return 1; }
    note "   the folder now says version $(installed_version)"
    step "building and starting the new version (docker compose up -d --build)"
    # By hand the build talks to the terminal; under the panel it goes to the
    # spool's log, which is what the panel's progress page tails.
    if [ "$WATCHING" = 1 ]; then
        ( cd "$COMPOSE_DIR" && docker compose up -d --build ) >> "$LOG" 2>&1
    else
        ( cd "$COMPOSE_DIR" && docker compose up -d --build )
    fi || { fail "the new version was not built or not started -- the log says where it stopped"; return 1; }
    note "the server is now running version $(installed_version)"
    set_status ok "the server is running version $(installed_version)"
    rm -rf "$WORK"
    return 0
}

kv() { sed -n "s/^$2=//p" "$1" 2>/dev/null | head -n 1; }

watch() {
    WATCHING=1
    mkdir -p "$SPOOL" 2>/dev/null
    say "watching $SPOOL/request for the panel (server folder $ROOT, $(installed_version))"
    _done=""
    while :; do
        touch "$SPOOL/watcher" 2>/dev/null
        if [ -f "$SPOOL/request" ]; then
            _id=$(kv "$SPOOL/request" id)
            if [ -n "$_id" ] && [ "$_id" != "$_done" ]; then
                _done=$_id
                note "update requested (the panel was told the published version is $(kv "$SPOOL/request" version))"
                run_update || true
            fi
        fi
        sleep "$POLL"
    done
}

case "${1:-run}" in
    run)   check_tree; run_update ;;
    check) check_tree; fetch_manifest > "$WORK.m" && printf 'installed %s, published %s\n' "$(installed_version)" "$(manifest_field "$WORK.m" version)"; rm -f "$WORK.m" ;;
    watch) check_tree; watch ;;
    *) printf 'usage: sh %s [run|check|watch]\n' "$0"; exit 2 ;;
esac
