// "Scal i uporzadkuj" in the engine (playerbot_arrange.h): the bag read into
// the planner's terms (playerbot_arrange_rules.h), and a complete plan applied
// the way MoveItem moves one item - RemoveFromCharacter, then SetItem at the
// new cell - so the grid, the packets to the client and the delayed save are
// the engine's own. Nothing is created from a vnum and nothing is thrown away
// but a stack that another has taken all of, which is what MoveItem's own
// stacking does.
//
// The order of work is the one Codex's audit of 18 September asked for:
// every refusal is made before the first item moves, the plan is complete and
// checked before it is used, and the quickslots are rewritten from what they
// said before, not from whatever the stack pouring left them saying.
//
// Every row the operation changed is written in the same second (FlushRow):
// the delayed save would get there too, but the db core's cache writes each
// item on its own five-minute clock, and in between the database held a bag
// half in its old cells and half in its new, and a stack poured into beside
// the deleted row of the stack it emptied. What is still not promised is a
// db core that dies while those rows are being written: CInputDB::ItemLoad
// then puts an item whose cell is taken into the first free one
// (ITEM_RESTORE), as it does after any interrupted move.
#include "stdafx.h"
#include "playerbot_arrange.h"

#if defined(PLAYERBOT_ENGINE_MT2009)

#include "utils.h"
#include "config.h"
#include "char.h"
#include "item.h"
#include "item_manager.h"
#include "questmanager.h"
#include "questpc.h"
#include "desc_client.h"
#include "playerbot_arrange_rules.h"

#include <chrono>
#include <cstring>
#include <iterator>
#include <map>
#include <set>
#include <unordered_map>
#include <vector>

namespace playerbot_arrange {
namespace {

namespace rules = playerbot_arrange_rules;

static_assert(INVENTORY_PAGE_COLUMN == rules::PAGE_COLUMNS, "the planner's page is five columns wide");
static_assert(INVENTORY_PAGE_ROW == rules::PAGE_ROWS, "the planner's page is nine rows tall");
static_assert(INVENTORY_DEFAULT_MAX_NUM == INVENTORY_DEFAULT_PAGE_COUNT * INVENTORY_PAGE_SIZE,
		"the bag is whole pages");

// A second click inside this is answered, not acted on: the server's own
// limit, whatever the client's button does.
const DWORD PLAYER_COOLDOWN_MS = 2000;

std::unordered_map<DWORD, DWORD> s_mapLastPlayerArrange;

// The order of the bag, category first. Potions lead - "wszelakie potki
// pierwsze a potem reszte" was the operator's rule for the bots' bags (Tieru,
// 15 September), and a player reaches for them most - then what is worn, the
// books, what improves gear, chests and keys, the other usable things, what
// fishing and gathering need, quest items, and the rest.
enum ECategory {
	CAT_POTION = 0,
	CAT_WEAPON,
	CAT_ARMOR,
	CAT_BOOK,
	CAT_UPGRADE,
	CAT_CHEST,
	CAT_USE,
	CAT_GATHER,
	CAT_QUEST,
	CAT_OTHER,
};

// Eliksir Slonca and Eliksir Ksiezyca: ITEM_USE, USE_SPECIAL, switched on and
// off by a use (char_item.cpp). Potions for the purpose of the order.
bool IsAutoPotionVnum(DWORD vnum)
{
	return (vnum >= 72723 && vnum <= 72730) || vnum == 76004 || vnum == 76005 ||
			vnum == 76021 || vnum == 76022 || vnum == 79012 || vnum == 79013;
}

// Sztuka Combo and the Leadership books: ITEM_USE, USE_SPECIAL, read like a
// book.
bool IsGeneralSkillBookVnum(DWORD vnum)
{
	return vnum >= 50301 && vnum <= 50306;
}

void SortKeyOf(LPITEM item, int64_t* key)
{
	const BYTE type = item->GetType();
	const BYTE sub = item->GetSubType();
	const DWORD vnum = item->GetVnum();
	int category = CAT_OTHER;
	int rank = type;
	switch (type) {
	case ITEM_USE:
		rank = 0;
		switch (sub) {
		case USE_POTION:
		case USE_POTION_NODELAY:
			category = CAT_POTION;
			rank = 0;
			break;
		case USE_POTION_CONTINUE:
		case USE_ABILITY_UP:
			category = CAT_POTION;
			rank = 1;
			break;
		case USE_AFFECT:
			// value0 510 is the engine's timed stat buff; 512 and 513 are no
			// potions at all (an exorcism scroll among them).
			category = item->GetValue(0) == 510 ? CAT_POTION : CAT_USE;
			rank = 2;
			break;
		case USE_SPECIAL:
			if (IsAutoPotionVnum(vnum)) {
				category = CAT_POTION;
				rank = 3;
			} else if (IsGeneralSkillBookVnum(vnum)) {
				category = CAT_BOOK;
				rank = 2;
			} else {
				category = CAT_USE;
			}
			break;
		case USE_TUNING:
		case USE_CHANGE_ATTRIBUTE:
		case USE_ADD_ATTRIBUTE:
		case USE_ADD_ATTRIBUTE2:
		case USE_CHANGE_ATTRIBUTE2:
		case USE_ADD_ACCESSORY_SOCKET:
		case USE_PUT_INTO_ACCESSORY_SOCKET:
		case USE_PUT_INTO_BELT_SOCKET:
		case USE_PUT_INTO_RING_SOCKET:
		case USE_CLEAN_SOCKET:
		case USE_CHANGE_COSTUME_ATTR:
		case USE_RESET_COSTUME_ATTR:
			category = CAT_UPGRADE;
			rank = 1;
			break;
		case USE_TREASURE_BOX:
			category = CAT_CHEST;
			break;
		case USE_BAIT:
			category = CAT_GATHER;
			break;
		default:
			category = CAT_USE;
			break;
		}
		break;
	case ITEM_POTION:
	case ITEM_BLEND:
		category = CAT_POTION;
		rank = 2;
		break;
	case ITEM_WEAPON:
		category = CAT_WEAPON;
		rank = sub == WEAPON_ARROW ? 1 : 0;
#ifdef ENABLE_QUIVER_SYSTEM
		if (sub == WEAPON_QUIVER)
			rank = 1;
#endif
		break;
	case ITEM_ARMOR:
		category = CAT_ARMOR;
		rank = sub;
		break;
	case ITEM_BELT:
	case ITEM_RING:
	case ITEM_UNIQUE:
	case ITEM_COSTUME:
		category = CAT_ARMOR;
		rank = 20 + type;
		break;
	case ITEM_SKILLBOOK:
		category = CAT_BOOK;
		rank = 0;
		break;
	case ITEM_SKILLFORGET:
		category = CAT_BOOK;
		rank = 1;
		break;
	case ITEM_METIN:
		category = CAT_UPGRADE;
		rank = 0;
		break;
	case ITEM_MATERIAL:
	case ITEM_RESOURCE:
		category = CAT_UPGRADE;
		rank = 2;
		break;
	case ITEM_TREASURE_BOX:
	case ITEM_TREASURE_KEY:
	case ITEM_GIFTBOX:
		category = CAT_CHEST;
		break;
	case ITEM_FISH:
	case ITEM_ROD:
	case ITEM_PICK:
	case ITEM_HERB_KNIFE:
	case ITEM_CAMPFIRE:
		category = CAT_GATHER;
		break;
	case ITEM_QUEST:
		category = CAT_QUEST;
		break;
	default:
		break;
	}
	key[0] = category;
	key[1] = rank;
	key[2] = type;
	key[3] = sub;
	key[4] = vnum;
	// A book by its skill (vnum 50300 carries the skill in socket 0); every
	// other kind with the full stacks before the partial one.
	key[5] = (type == ITEM_SKILLBOOK || type == ITEM_SKILLFORGET) ? item->GetSocket(0)
			: -(int64_t)item->GetCount();
}

// Whether two bag stacks may pour into each other. The engine's rule
// (MoveItem, AutoStackItem) is the vnum, the stack flag and every socket; this
// asks for the attributes, the flag word and the look as well, so it never
// pours what the engine would not, and never what a player could tell apart.
bool SameStack(LPITEM a, LPITEM b)
{
	if (a->GetVnum() != b->GetVnum() || a->GetOriginalVnum() != b->GetOriginalVnum())
		return false;
	if (!a->IsStackable() || IS_SET(a->GetAntiFlag(), ITEM_ANTIFLAG_STACK) ||
			!b->IsStackable() || IS_SET(b->GetAntiFlag(), ITEM_ANTIFLAG_STACK))
		return false;
	if (a->GetFlag() != b->GetFlag())
		return false;
	for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
		if (a->GetSocket(i) != b->GetSocket(i))
			return false;
	for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		if (a->GetAttributeType(i) != b->GetAttributeType(i) || a->GetAttributeValue(i) != b->GetAttributeValue(i))
			return false;
	if (a->GetMaskVnum() != b->GetMaskVnum() || a->GetSIGVnum() != b->GetSIGVnum())
		return false;
	return true;
}

// An item's row written now, not when the db core's cache gets round to it
// (ITEM_CACHE_FLUSH_SECONDS, five minutes, counted per item): the delayed save
// sends the item, then HEADER_GD_ITEM_FLUSH has the db core write the row -
// FlushPlayerBotItemRow's shape. Measured on the test world before it: an
// arranged bag stood in the database half in its old cells and half in its
// new ones for up to five minutes (81 bags with two items on one cell a
// minute after 400 arranges), and a stack another was poured into kept its
// old count there while the emptied one's row was already deleted
// (DestroyItem writes at once) - a crash inside that window lost the
// units poured. The rows would be written within five minutes anyway; this
// writes them in the same second as the arrange.
void FlushRow(LPITEM item)
{
	if (!item || item->GetID() == 0 || !db_clientdesc)
		return;
	ITEM_MANAGER::instance().FlushDelayedSave(item);
	const DWORD id = item->GetID();
	db_clientdesc->DBPacketHeader(HEADER_GD_ITEM_FLUSH, 0, sizeof(DWORD));
	db_clientdesc->Packet(&id, sizeof(DWORD));
}

// An item a plan was sure of and the engine did not put where it was told. Not
// expected - SetItem refuses only an item with an owner or a cell outside the
// window, and neither can happen here - but an ownerless item is destroyed by
// the next delayed save, so it goes back into the bag, or to its owner's feet.
void Rescue(LPCHARACTER ch, LPITEM item)
{
	if (item->GetOwner())
		return;
	const int cell = ch->GetEmptyInventory(item->GetSize());
	if (cell >= 0) {
		item->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
		sys_err("INVENTORY_ARRANGE: pid=%u name=%s item %u (%s) put back at cell %d",
				ch->GetPlayerID(), ch->GetName(), item->GetID(), item->GetName(), cell);
		return;
	}
	PIXEL_POSITION pos;
	pos.x = ch->GetX();
	pos.y = ch->GetY();
	item->AddToGround(ch->GetMapIndex(), pos);
	item->SetOwnership(ch, 300);
	item->StartDestroyEvent();
	sys_err("INVENTORY_ARRANGE: pid=%u name=%s item %u (%s) had no cell and was put at the owner's feet",
			ch->GetPlayerID(), ch->GetName(), item->GetID(), item->GetName());
}

}  // namespace

TResult ArrangeInventory(LPCHARACTER ch, bool fromPlayer)
{
	TResult result;
	if (!ch || !ch->IsPC() || !ch->IsItemLoaded()) {
		result.code = RESULT_BUSY;
		return result;
	}
	if (ch->IsDead()) {
		result.code = RESULT_DEAD;
		return result;
	}
	// Everything MoveItem asks of the character, and every busy state with
	// nothing excluded: an exchange, a shop and its management, the safebox,
	// the cube, crafting, a refine, the dragon soul and acce windows, a warp.
	// A quest running holds items it has been handed, by pointer or by cell.
	if (!ch->CanHandleItem(false, false, 0) ||
			quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID())->IsRunning()) {
		result.code = RESULT_BUSY;
		return result;
	}
	const DWORD now = get_dword_time();
	if (fromPlayer) {
		std::unordered_map<DWORD, DWORD>::iterator last = s_mapLastPlayerArrange.find(ch->GetPlayerID());
		if (last != s_mapLastPlayerArrange.end() && now - last->second < PLAYER_COOLDOWN_MS) {
			result.code = RESULT_COOLDOWN;
			return result;
		}
		if (s_mapLastPlayerArrange.size() > 4096)
			for (std::unordered_map<DWORD, DWORD>::iterator it = s_mapLastPlayerArrange.begin(); it != s_mapLastPlayerArrange.end();)
				it = now - it->second > PLAYER_COOLDOWN_MS ? s_mapLastPlayerArrange.erase(it) : std::next(it);
		s_mapLastPlayerArrange[ch->GetPlayerID()] = now;
	}
	const std::chrono::steady_clock::time_point started = std::chrono::steady_clock::now();

	// The four pages as the engine holds them. The horse's page, the worn
	// slots, the belt and the dragon soul window are other cells and are not
	// read at all.
	std::vector<rules::Item> items;
	std::vector<LPITEM> handles;
	std::map<uint32_t, LPITEM> handleOf;
	std::map<int, uint32_t> idAtCell;
	for (WORD cell = 0; cell < INVENTORY_DEFAULT_MAX_NUM; ++cell) {
		LPITEM item = ch->GetInventoryItem(cell);
		if (!item)
			continue;
		if (item->GetCell() != cell || item->GetOwner() != ch || item->GetWindow() != INVENTORY ||
				item->GetID() == 0 || handleOf.count(item->GetID())) {
			sys_err("INVENTORY_ARRANGE: pid=%u name=%s refused: item %u (%s) at cell %u says cell %u window %u",
					ch->GetPlayerID(), ch->GetName(), item->GetID(), item->GetName(), cell,
					item->GetCell(), item->GetWindow());
			result.code = RESULT_INCONSISTENT;
			return result;
		}
		rules::Item planned;
		planned.id = item->GetID();
		planned.cell = cell;
		// Six protos on this line say size 0 (none in anybody's bag on the test
		// world). SetItem marks no grid cell for one, so it is no layout this
		// planner could make or trust: it stays where it is, as one cell,
		// and the rest of the bag is arranged round it. Nothing is taller
		// than three here; a proto that says so is a bag left alone.
		const int size = item->GetSize();
		if (size > rules::MAX_HEIGHT) {
			sys_err("INVENTORY_ARRANGE: pid=%u name=%s refused: item %u (%s) is %d cells tall",
					ch->GetPlayerID(), ch->GetName(), item->GetID(), item->GetName(), size);
			result.code = RESULT_INCONSISTENT;
			return result;
		}
		planned.height = size >= 1 ? size : 1;
		planned.count = item->GetCount();
		planned.maxStack = item->GetMaxStack();
		planned.pinned = item->isLocked() || item->IsExchanging() || planned.height != size;
		SortKeyOf(item, planned.key);
		items.push_back(planned);
		handles.push_back(item);
		handleOf[planned.id] = item;
		idAtCell[cell] = planned.id;
		if (planned.pinned)
			++result.pinned;
	}
	result.items = (int)items.size();
	// Units per vnum, to be counted again at the end: pouring moves units
	// between two stacks of one kind and nothing else, so the sums cannot
	// change, and a difference is a loss somebody has to hear about.
	std::map<DWORD, uint64_t> unitsBefore;
	for (size_t i = 0; i < handles.size(); ++i)
		unitsBefore[handles[i]->GetVnum()] += handles[i]->GetCount();

	// Merge groups by comparing the items themselves.
	std::vector<LPITEM> representatives;
	for (size_t i = 0; i < items.size(); ++i) {
		LPITEM item = handles[i];
		if (items[i].pinned || !item->IsStackable() || IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK) ||
				item->GetMaxStack() < 2)
			continue;
		size_t group = 0;
		for (; group < representatives.size(); ++group)
			if (SameStack(representatives[group], item))
				break;
		if (group == representatives.size())
			representatives.push_back(item);
		items[i].mergeGroup = (uint32_t)group + 1;
	}

	const rules::Plan plan = rules::MakePlan(items, INVENTORY_DEFAULT_PAGE_COUNT);
	if (!plan.ok) {
		sys_err("INVENTORY_ARRANGE: pid=%u name=%s refused: the bag is not a legal layout (%d items)",
				ch->GetPlayerID(), ch->GetName(), result.items);
		result.code = RESULT_INCONSISTENT;
		return result;
	}
	result.strategy = plan.strategy;
	if (plan.transfers.empty() && plan.moved == 0) {
		result.code = RESULT_NOTHING;
		return result;
	}

	// The quickslots as they were, to be pointed at the new cells afterwards.
	TQuickslot before[QUICKSLOT_MAX_NUM];
	std::memset(before, 0, sizeof(before));
	for (int i = 0; i < QUICKSLOT_MAX_NUM; ++i) {
		TQuickslot* slot = NULL;
		if (ch->GetQuickslot((BYTE)i, &slot) && slot)
			before[i] = *slot;
	}

	// The pours. The receiver grows first; the giver shrinks, and at nothing
	// SetCount removes and destroys it - MoveItem's stacking, step by step.
	for (const rules::Transfer& transfer : plan.transfers) {
		std::map<uint32_t, LPITEM>::iterator from = handleOf.find(transfer.from);
		std::map<uint32_t, LPITEM>::iterator to = handleOf.find(transfer.to);
		if (from == handleOf.end() || to == handleOf.end() || from->second->GetCount() < transfer.units ||
				to->second->GetCount() + transfer.units > to->second->GetMaxStack()) {
			sys_err("INVENTORY_ARRANGE: pid=%u name=%s pour %u -> %u of %u refused; the bag stays as poured so far",
					ch->GetPlayerID(), ch->GetName(), transfer.from, transfer.to, transfer.units);
			result.code = RESULT_INCONSISTENT;
			return result;
		}
		to->second->SetCount(to->second->GetCount() + transfer.units);
		const ITEM_COUNT left = from->second->GetCount() - transfer.units;
		from->second->SetCount(left);
		if (left == 0) {
			handleOf.erase(from);
			++result.merged;
		}
		result.units += transfer.units;
	}

	// The moves: every item that changes cell leaves its cell first, then each
	// is set down in its new one. Two passes, so a cycle - A into B's cell
	// while B goes into A's - needs no free cell in between.
	std::vector<std::pair<LPITEM, WORD> > movers;
	for (const rules::Placement& placement : plan.placements) {
		std::map<uint32_t, LPITEM>::iterator it = handleOf.find(placement.id);
		if (it == handleOf.end())
			continue;
		if (it->second->GetCell() != (WORD)placement.cell)
			movers.push_back(std::make_pair(it->second, (WORD)placement.cell));
	}
	for (size_t i = 0; i < movers.size(); ++i)
		movers[i].first->RemoveFromCharacter();
	for (size_t i = 0; i < movers.size(); ++i) {
#ifdef ENABLE_HIGHLIGHT_NEW_ITEM
		ch->SetItem(TItemPos(INVENTORY, movers[i].second), movers[i].first, true);
#else
		ch->SetItem(TItemPos(INVENTORY, movers[i].second), movers[i].first);
#endif
		movers[i].first->Save();
	}
	result.moved = (int)movers.size();

	int misplaced = 0;
	std::map<uint32_t, int> finalCell;
	for (const rules::Placement& placement : plan.placements) {
		std::map<uint32_t, LPITEM>::iterator it = handleOf.find(placement.id);
		if (it == handleOf.end())
			continue;
		LPITEM item = it->second;
		if (item->GetOwner() != ch || item->GetCell() != (WORD)placement.cell ||
				ch->GetInventoryItem((WORD)placement.cell) != item) {
			++misplaced;
			Rescue(ch, item);
		}
		finalCell[placement.id] = item->GetOwner() == ch ? item->GetCell() : -1;
	}

	// Every row this changed, written now: the stacks that grew and the items
	// that moved (FlushRow).
	std::set<LPITEM> touched;
	for (const rules::Transfer& transfer : plan.transfers) {
		std::map<uint32_t, LPITEM>::iterator to = handleOf.find(transfer.to);
		if (to != handleOf.end())
			touched.insert(to->second);
	}
	for (size_t i = 0; i < movers.size(); ++i)
		touched.insert(movers[i].first);
	for (std::set<LPITEM>::const_iterator it = touched.begin(); it != touched.end(); ++it)
		if ((*it)->GetOwner() == ch)
			FlushRow(*it);

	// The quickslots: each one that pointed at a stack in the four pages now
	// points where that stack - or the stack it was poured into - stands. One
	// that pointed at an empty cell pointed at nothing, and is removed rather
	// than left to land on whatever stands there now.
	for (int i = 0; i < QUICKSLOT_MAX_NUM; ++i) {
		const TQuickslot& old = before[i];
		if (old.type != QUICKSLOT_TYPE_ITEM || old.pos >= INVENTORY_DEFAULT_MAX_NUM)
			continue;
		TQuickslot* current = NULL;
		ch->GetQuickslot((BYTE)i, &current);
		std::map<int, uint32_t>::const_iterator at = idAtCell.find(old.pos);
		if (at == idAtCell.end()) {
			if (current && current->type == QUICKSLOT_TYPE_ITEM && current->pos == old.pos)
				ch->DelQuickslot((BYTE)i);
			continue;
		}
		uint32_t id = at->second;
		std::map<uint32_t, uint32_t>::const_iterator survivor = plan.survivorOf.find(id);
		if (survivor != plan.survivorOf.end())
			id = survivor->second;
		std::map<uint32_t, int>::const_iterator cell = finalCell.find(id);
		if (cell == finalCell.end() || cell->second < 0)
			continue;
		if (current && current->type == QUICKSLOT_TYPE_ITEM && current->pos == (WORD)cell->second)
			continue;
		TQuickslot slot;
		slot.type = QUICKSLOT_TYPE_ITEM;
		slot.pos = (WORD)cell->second;
		ch->SetQuickslot((BYTE)i, slot);
	}

	std::map<DWORD, uint64_t> unitsAfter;
	for (WORD cell = 0; cell < INVENTORY_DEFAULT_MAX_NUM; ++cell) {
		LPITEM item = ch->GetInventoryItem(cell);
		if (item)
			unitsAfter[item->GetVnum()] += item->GetCount();
	}
	if (unitsAfter != unitsBefore)
		for (std::map<DWORD, uint64_t>::const_iterator it = unitsBefore.begin(); it != unitsBefore.end(); ++it) {
			std::map<DWORD, uint64_t>::const_iterator now = unitsAfter.find(it->first);
			const uint64_t after = now == unitsAfter.end() ? 0 : now->second;
			if (after != it->second)
				sys_err("INVENTORY_ARRANGE: pid=%u name=%s vnum %u held %llu units before and %llu after",
						ch->GetPlayerID(), ch->GetName(), it->first, (unsigned long long)it->second,
						(unsigned long long)after);
		}

	const unsigned int micros = (unsigned int)std::chrono::duration_cast<std::chrono::microseconds>(
			std::chrono::steady_clock::now() - started).count();
	result.micros = micros;
	if (misplaced)
		sys_err("INVENTORY_ARRANGE: pid=%u name=%s %d item(s) were not where the plan put them",
				ch->GetPlayerID(), ch->GetName(), misplaced);
	if (fromPlayer)
		sys_log(0, "INVENTORY_ARRANGE: pid=%u name=%s items=%d moved=%d merged=%d units=%u pinned=%d strategy=%d us=%u",
				ch->GetPlayerID(), ch->GetName(), result.items, result.moved, result.merged, result.units,
				result.pinned, result.strategy, micros);
	result.code = RESULT_DONE;
	return result;
}

}  // namespace playerbot_arrange

#else  // r40250: two pages and no horse page; the bots keep their own tidy pass there.

namespace playerbot_arrange {

TResult ArrangeInventory(LPCHARACTER, bool)
{
	TResult result;
	result.code = RESULT_UNSUPPORTED;
	return result;
}

}  // namespace playerbot_arrange

#endif
