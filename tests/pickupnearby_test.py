# -*- coding: utf-8 -*-
"""client-root/pickupnearby.py against stub modules, on the client's Python
2.7 and on 3: one /pickup_nearby per half second, whatever the key repeat."""
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', 'linux-port-mt2009', 'client-root'))

CLOCK = {'t': 100.0}
SENT = []

app = types.ModuleType('app')
app.GetTime = lambda: CLOCK['t']
net = types.ModuleType('net')
net.SendChatPacket = lambda text: SENT.append(text)
sys.modules['app'] = app
sys.modules['net'] = net
sys.path.insert(0, ROOT)

import pickupnearby  # noqa: E402


class PickupNearbyTest(unittest.TestCase):
    def setUp(self):
        del SENT[:]
        CLOCK['t'] += 10.0
        pickupnearby._state['next'] = 0.0

    def test_first_press_asks_the_server(self):
        self.assertTrue(pickupnearby.Request())
        self.assertEqual(SENT, ['/pickup_nearby'])

    def test_a_held_key_asks_once_per_half_second(self):
        pickupnearby.Request()
        for _ in range(10):
            CLOCK['t'] += 0.04
            self.assertFalse(pickupnearby.Request())
        self.assertEqual(len(SENT), 1)
        CLOCK['t'] += 0.2
        self.assertTrue(pickupnearby.Request())
        self.assertEqual(len(SENT), 2)


if __name__ == '__main__':
    unittest.main()
