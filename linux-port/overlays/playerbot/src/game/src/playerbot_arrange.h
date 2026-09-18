#ifndef PLAYERBOT_ARRANGE_H
#define PLAYERBOT_ARRANGE_H
// "Scal i uporzadkuj": one request, and the server pours the bag's stacks
// together and lays its four pages out again. The one place this is done, for
// a player's inventory button (/inventory_arrange in cmd_general.cpp, the
// client answering "InventoryArrangeResult") and for the bots' tidy pass
// alike; the plan itself is playerbot_arrange_rules.h, the engine's half is
// playerbot_arrange.cpp. A normal header, included after stdafx.h by the
// engine TUs that call it - not a fragment of the manager.
namespace playerbot_arrange {

enum EResult {
	RESULT_DONE = 0,          // moved or merged something
	RESULT_NOTHING = 1,       // already arranged: nothing to move or merge
	RESULT_BUSY = 2,          // an exchange, a shop, the safebox, a quest, a window
	RESULT_COOLDOWN = 3,      // a player's second click inside two seconds
	RESULT_NO_LAYOUT = 4,     // no legal layout found; nothing changed
	RESULT_DEAD = 5,
	RESULT_INCONSISTENT = 6,  // the bag as the engine holds it is not a legal layout
	RESULT_UNSUPPORTED = 7,   // this engine (r40250) has no four-page bag to arrange
	RESULT_BAD_REQUEST = 8,   // an option the command does not know
};

struct TResult {
	int code = RESULT_UNSUPPORTED;
	int items = 0;           // items in the four pages
	int moved = 0;           // items whose cell changed
	int merged = 0;          // stacks poured into others and gone
	unsigned int units = 0;  // units poured
	int pinned = 0;          // items left where they were (an active auto potion)
	int strategy = 0;        // playerbot_arrange_rules::Strategy
	unsigned int micros = 0; // what the whole operation cost
};

// fromPlayer: a player's click, which waits two seconds between two; the bots'
// pass keeps its own clock.
TResult ArrangeInventory(LPCHARACTER ch, bool fromPlayer);

}  // namespace playerbot_arrange

#endif
