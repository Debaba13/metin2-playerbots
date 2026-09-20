# -*- coding: utf-8 -*-
"""The offline shop's "edit the price of similar items", one packet at a time.

Ctrl + right click repriced every line holding the same item and the client
sent one packet per line in a single frame; the server takes one shop action
per 200 ms, so the first line went through and every other one answered "wait
a moment". shoppricepump.py spaces them out.

Runs on the client's Python 2.7 and on 3:

    python tests/shoppricepump_test.py
"""
import os
import sys
import types

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', 'linux-port-mt2009', 'client-root')

sent = []
prices = []
now = [0.0]


class _Window(object):
    def __init__(self):
        pass

    def SetSize(self, w, h):
        pass

    def Show(self):
        pass


def _stub(name, **members):
    module = types.ModuleType(name)
    for key, value in members.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


_stub('app', GetTime=lambda: now[0])
_stub('ui', Window=_Window)
_stub('ikashop', SendEditItem=lambda item_id, price: sent.append((item_id, price)))
_stub('offlineShopBuilder',
      SetPrivateShopItemPrice=lambda vnum, count, price, sockets: prices.append((vnum, price)))

sys.path.insert(0, ROOT)
import shoppricepump  # noqa: E402

FAILS = []


def check(what, expected, actual):
    if expected == actual:
        print('  OK   %s' % what)
    else:
        print('  FAIL %s: expected %r, got %r' % (what, expected, actual))
        FAILS.append(what)


def item(item_id, vnum=50300):
    return {'id': item_id, 'vnum': vnum, 'count': 1, 'sockets': (0, 0, 0)}


def run_updates(seconds, step=0.05):
    # The client calls OnUpdate every frame; time moves in small steps.
    ticks = int(seconds / step)
    for _ in range(ticks):
        now[0] += step
        shoppricepump._pump.OnUpdate()


print('== five lines leave one at a time ==')
del sent[:]
del prices[:]
now[0] = 100.0
shoppricepump.Queue([(item(i), 250000) for i in range(1, 6)])
shoppricepump._pump.OnUpdate()
check('the first packet goes at once', 1, len(sent))
now[0] += 0.1
shoppricepump._pump.OnUpdate()
check('and nothing follows inside the server window', 1, len(sent))
run_updates(0.2)
check('the second follows after the interval', 2, len(sent))
run_updates(2.0)
check('all five arrive', 5, len(sent))
check('each carries the price', [250000] * 5, [p for (_, p) in sent])
check('every line is a different item', [1, 2, 3, 4, 5], [i for (i, _) in sent])
check("the builder's copy is updated too", 5, len(prices))

print('== the interval is at least the server\'s own ==')
check('a quarter of a second, over the 200 ms limit', True, shoppricepump.TICK >= 0.2)

print('== a second click replaces what is left of the first ==')
del sent[:]
now[0] = 200.0
shoppricepump.Queue([(item(10 + i), 1000) for i in range(5)])
shoppricepump._pump.OnUpdate()
check('the first of the first batch went', 1, len(sent))
shoppricepump.Queue([(item(20), 7777)])
run_updates(2.0)
check('and only the new one follows it', 2, len(sent))
check('with the new price', 7777, sent[-1][1])

print('== an empty queue costs nothing ==')
del sent[:]
shoppricepump.Queue([])
run_updates(1.0)
check('nothing is sent', 0, len(sent))

print('')
if FAILS:
    print('FAILED: %d' % len(FAILS))
    sys.exit(1)
print('PASS')
