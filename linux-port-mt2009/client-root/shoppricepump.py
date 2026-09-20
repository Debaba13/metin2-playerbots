# The offline shop's "edit the price of similar items", one at a time.
#
# Ctrl + right click on a line of the shop's edit grid repriced every line
# holding the same item, and offlineshopmanage.py sent one packet per line in
# the frame it was clicked in. The server takes one shop action per 200 ms
# (PulseManager, ePulse::IkaShopTouchItem), so the first line was repriced and
# every other one answered "wait a moment" - reported by uxietoszef and again
# by Nagash on 20 September, with a screenshot of the refusals.
#
# The same edits leave from here, one every TICK seconds. Twenty lines take
# about five seconds; the per-minute weight limit (2500, an edit weighs 5) is
# nowhere near it either way.
#
# Python 2.7 as the client has it.

import app
import ui
import ikashop
import offlineShopBuilder

# A shade over the server's own 200 ms, so a slow frame cannot land two
# packets inside one of its windows.
TICK = 0.25


class ShopPricePump(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.edits = []
		self.nextTick = 0.0
		self.SetSize(0, 0)
		self.Show()

	def Queue(self, edits):
		# A second click replaces what is left of the first: the lines were
		# read out of the shop as it was then.
		self.edits = list(edits)
		self.nextTick = 0.0

	def OnUpdate(self):
		if not self.edits:
			return
		now = app.GetTime()
		if now < self.nextTick:
			return
		self.nextTick = now + TICK
		(itemData, itemPrice) = self.edits.pop(0)
		ikashop.SendEditItem(itemData["id"], itemPrice)
		offlineShopBuilder.SetPrivateShopItemPrice(
			itemData["vnum"], itemData["count"], itemPrice, itemData["sockets"])


_pump = None


def Queue(edits):
	global _pump
	if _pump is None:
		_pump = ShopPricePump()
	_pump.Queue(edits)
