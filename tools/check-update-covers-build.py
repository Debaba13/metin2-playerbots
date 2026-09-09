#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every file a Dockerfile COPYs must reach the player, or the build dies at the COPY.

An install put together from an update package has only what
launcher/server-update-files.txt lists.  Being tracked by Git is not the same as
being delivered: panel/bin/apply_rates.sh was tracked and still missing on the
machine that reported it, and game/rates/ was the next one along - "failed to
compute cache key ... /rates: not found", with no way to repair it by
reinstalling, because the reinstall uses the same package.

So: read every COPY out of every build context, and check each source against the
shipping list.  A path may legitimately be absent from the list when something on
the player's machine writes it - start-server.ps1 stages the overlay sources, the
panel app and the quest files - and those prefixes are named here explicitly
rather than guessed, so that a new COPY of something nobody stages is an error
and not a silent omission.

Exit code 1 if anything a build reads would not arrive.
"""
import fnmatch
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCKER = os.path.join(ROOT, 'linux-port', 'docker')
LIST = os.path.join(ROOT, 'launcher', 'server-update-files.txt')

# Prefixes, relative to a build context, that are written on the player's machine
# rather than shipped: prepare-context.sh stages them during an install and
# start-server.ps1 refreshes them before every start.
STAGED_PREFIXES = (
    'src/',            # the engine tree, from the operator's own r40250 package
    'app/',            # panel/app, staged from files/
    'schema/',         # panel/schema, staged from files/
    'quest/',          # game/quest, staged from files/*.quest
    'initdb.d/dumps/',  # the SQL dumps, from the operator's own package
)


def shipping_patterns():
    out = []
    with open(LIST, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith('#'):
                out.append(line)
    return out


def is_shipped(path, patterns):
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return pattern
        # "a/b/*" ships the directory, and so everything under it.
        if pattern.endswith('/*') and (path + '/').startswith(pattern[:-1]):
            return pattern
    return None


def copies(dockerfile):
    """Source arguments of every COPY/ADD that reads the build context."""
    out = []
    with open(dockerfile, encoding='utf-8', errors='replace') as handle:
        for raw in handle:
            line = raw.strip()
            if not re.match(r'^(COPY|ADD)\s', line):
                continue
            if '--from=' in line:      # from another stage, not from the context
                continue
            words = [w for w in line.split()[1:] if not w.startswith('--')]
            if len(words) < 2:
                continue
            out.extend(word.strip('"') for word in words[:-1])
    return out


def main():
    patterns = shipping_patterns()
    problems = []
    checked = 0
    for context in sorted(os.listdir(DOCKER)):
        dockerfile = os.path.join(DOCKER, context, 'Dockerfile')
        if not os.path.isfile(dockerfile):
            continue
        for source in copies(dockerfile):
            checked += 1
            if source.startswith(STAGED_PREFIXES):
                continue
            rel = 'linux-port/docker/%s/%s' % (context, source.rstrip('/'))
            if not os.path.exists(os.path.join(ROOT, rel.replace('/', os.sep))):
                problems.append('%s: COPY %s - nie ma tego w repozytorium' % (context, source))
                continue
            if not is_shipped(rel, patterns):
                problems.append('%s: COPY %s - %s nie jedzie w aktualizacji' % (context, source, rel))

    print('sprawdzone instrukcje COPY: %d' % checked)
    if problems:
        print('')
        print('BUDOWA U GRACZA SIE WYWROCI:')
        for problem in problems:
            print('  ' + problem)
        return 1
    print('kazdy plik czytany przez budowe jedzie w aktualizacji albo jest tworzony na miejscu')
    return 0


if __name__ == '__main__':
    sys.exit(main())
