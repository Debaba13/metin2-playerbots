# -*- coding: utf-8 -*-
"""The .env.example of the mt2009 stack.

Usage:  python envify.py

Renders linux-port-mt2009/docker/.env.example from linux-port/docker/.env.example:
the same keys with the same defaults (the launcher writes .env from it and
Add-MissingDotEnvKeys in start-server.ps1 tops an older .env up from it), plus
what only this stack reads:

  * M2_APT_MIRROR - the Ubuntu mirror the image build installs packages from,
    for a network where archive.ubuntu.com crawls or times out (this one).

Idempotent: re-run after editing the r40250 original.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', 'linux-port', 'docker', '.env.example'))
DST = os.path.normpath(os.path.join(HERE, '..', 'docker', '.env.example'))

EXTRA = """
# -----------------------------------------------------------------------------
#  mt2009 build only (rendered by linux-port-mt2009/port/envify.py)
# -----------------------------------------------------------------------------

# The Ubuntu package mirror the image build installs from. Empty means the
# Gdansk mirror (http://ubuntu.task.gda.pl/ubuntu/), which is fast from Poland;
# Ubuntu's own archive.ubuntu.com served a few kilobytes a second here on the
# day 2.0 came out and every first build sat at deps 7/7 for twenty minutes.
# Another country wants a closer mirror, e.g. http://mirrors.edge.kernel.org/ubuntu/
# or http://archive.ubuntu.com/ubuntu/ for the official one.
M2_APT_MIRROR=
"""


def main():
    s = io.open(SRC, encoding='utf-8', newline='').read()
    assert '\r' not in s, 'expected LF line endings'
    assert 'M2_APT_MIRROR' not in s, 'the r40250 example carries M2_APT_MIRROR now; drop it from EXTRA'
    head = ('# Rendered for the mt2009 stack by linux-port-mt2009/port/envify.py from\n'
            '# linux-port/docker/.env.example. Edit the original, then re-run it.\n')
    out = head + s.rstrip('\n') + '\n' + EXTRA
    io.open(DST, 'w', encoding='utf-8', newline='').write(out)
    print('envify: %s (%d keys)' % (os.path.relpath(DST), sum(1 for l in out.splitlines() if l.startswith('M2_'))))


if __name__ == '__main__':
    main()
