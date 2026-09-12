#ifndef __INC_METIN2_PLAYERBOT_BONUS_H__
#define __INC_METIN2_PLAYERBOT_BONUS_H__

// The bonus lines on a worn item, and what a bot is willing to spend to change
// them.
//
// Gear is only half a bot's power and these are the other half: a
// level-appropriate weapon rolled into five resistances is genuinely worse
// than the plain one it replaced. Two engine items do the work and neither can
// be dropped, sold, traded or shopped, so there is no market to walk to - a bot
// pays for one the way it pays for its stall.
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, after playerbot_economy.h - it uses that file's idea of what
// a bot is short of - and before playerbot_town.h, which is where a bot decides
// to go and do this.

namespace
{
	// --- Bonus lines ---------------------------------------------------------
	// Gear is only half a bot's power; the four bonus lines are the other half. A
	// level-appropriate weapon rolled into four resistances is genuinely worse
	// than the one it replaced, and until now nothing ever looked at them.
	//
	// The scoring below is deliberately coarse. It exists to tell "worth keeping"
	// from "roll it again", not to model the damage formula: every line is scored
	// as points-per-typical-roll so that a +2000 HP line and a +15 attack line
	// can be compared at all.
	bool IsPlayerBotCaster(LPCHARACTER ch)
	{
		return ch && (ch->GetJob() == JOB_SHAMAN || ch->GetJob() == JOB_SURA);
	}

	bool IsPlayerBotOffensiveSlot(BYTE wearCell)
	{
		return wearCell == WEAR_WEAPON;
	}

	// What one line is worth to this bot, in points per typical roll.
	//
	// Three of the world's own tables decide it and none of it is taste. A
	// player sent in a spreadsheet of "which bonus is worth having on which
	// piece, on which map"; this is that spreadsheet checked against our files,
	// which disagree with it in several places worth knowing about.
	//
	//  * `player.item_attr` says what may roll where and how high. Health does
	//    not roll on a helmet or an earring, critical does not roll on a wrist
	//    or an earring, attack value rolls on a body and nowhere else, and
	//    block only on a shield. That is why the finishing rule below is per
	//    slot: the old one asked a helmet for health and attack value, so no
	//    helmet in the world could ever be finished and every one of them was
	//    rerolled for as long as its owner had gold.
	//  * `battle.cpp` says what a line does. BLOCK stops a melee hit outright
	//    and 73% of this world's monsters are melee. DODGE and RESIST_BOW only
	//    answer a ranged attacker, and ranged monsters are 0-24% of a map. An
	//    elemental resistance is applied at thirty percent of its own number,
	//    so fifteen points of it is four and a half percent. And the five
	//    weapon-type resistances never fire against a monster at all: that
	//    branch reads the attacker's WEAR_WEAPON and a monster wears none, so
	//    "odpornosc na miecze" is a line for fighting players.
	//  * `tools/analyse_map_races.py` says what each map is made of, which is
	//    what makes a race line worth having - or not, on the three maps whose
	//    monsters no item can be strong against.
	//
	// The scoring stays coarse on purpose: it tells "worth keeping" from "roll
	// it again", it does not model the damage formula.
	int ScorePlayerBotBonusLine(LPCHARACTER ch, BYTE wearCell, BYTE type, short value)
	{
		// A negative roll exists (movement speed on some sets) and is worth less
		// than nothing, so it must not be able to prop up a bad item's total.
		if (value <= 0)
			return 0;

		const bool bCaster = IsPlayerBotCaster(ch);

		switch (type)
		{
			// The two damage lines are not the same line for every character,
			// and weighting them alike had one class rerolling away the only
			// bonus that does anything for it.
			//
			// Measured over every attribute on this world's items: average
			// damage rolls up to 46 and skill damage only to 18. At twelve and
			// ten a maximum average roll scored 460 against a maximum skill
			// roll's 216, so average damage won by more than two to one - for
			// everybody, a Shaman included, whose damage is very nearly all
			// skills. A caster that rolled the best skill-damage line in the
			// game would throw it away on the next pass.
			//
			// So the weights are per build, and chosen against those two
			// ceilings rather than by feel: a caster's best skill roll (18 x 30
			// = 540) beats its best average roll (46 x 6 = 276), and for
			// everyone else the order stays as it was.
			case APPLY_SKILL_DAMAGE_BONUS:
				return bCaster ? value * 30 : value * 12;
			case APPLY_NORMAL_HIT_DAMAGE_BONUS:
				return bCaster ? value * 6 : value * 10;

			// "Silny przeciwko Orkom" and its five siblings - the line the
			// player's table is really about, and the one this pass used to
			// throw away. It fell through to the default and was worth its own
			// number, so twenty percent against orcs scored twenty points and
			// lost to six points of movement speed, while the equipment pass was
			// paying twelve thousand for the same line. The bot bought the
			// shield for it and rerolled it off at the next blacksmith.
			//
			// It multiplies the whole attack - normal hits and skills alike -
			// against every monster of that race, so where the map is that race
			// it beats any other line a shield or an earring can roll. Where it
			// is not, it is worth keeping only because bots change maps.
			case APPLY_ATTBONUS_ANIMAL:
			case APPLY_ATTBONUS_UNDEAD:
			case APPLY_ATTBONUS_DEVIL:
			case APPLY_ATTBONUS_HUMAN:
			case APPLY_ATTBONUS_ORC:
			case APPLY_ATTBONUS_MILGYO:
			{
				int racePercent = 0;
				const int race = GetPlayerBotFightingRace(ch, &racePercent);
				const int onMap = (race != PLAYERBOT_RACE_NONE &&
						GetPlayerBotRaceApplyType(race) == type)
						? PLAYERBOT_BONUS_RACE_ON_MAP * racePercent / 100 : 0;
				return value * std::max(onMap, PLAYERBOT_BONUS_RACE_OFF_MAP);
			}
			// Worth having and worth nothing to chase: "Silny przeciwko
			// Potworom" raises damage against every monster and against Metin
			// stones, which is the whole of what a bot ever fights. It is not in
			// player.item_attr at all, so no reroll can produce one;
			// item_attr_rare carries it at ten, and the pieces that have it keep
			// it.
			case APPLY_ATTBONUS_MONSTER:        return value * 14;

			case APPLY_CRITICAL_PCT:            return value * 10;
			case APPLY_PENETRATE_PCT:           return value * 10;
			// Attack speed is a straight multiplier on everything a bot does and
			// it rolls only to eight, so a maximum roll is eight percent more of
			// every swing, every shot and every skill. It was worth sixty-four
			// points, less than a mediocre health roll.
			case APPLY_ATT_SPEED:               return value * 15;
			// Life stolen per hit is what keeps a grinder off the potions and
			// out of town, which is the errand that costs a bot the most time.
			case APPLY_STEAL_HP:                return value * 12;
			// Rolls on a body and nowhere else, to fifty.
			case APPLY_ATT_GRADE_BONUS:         return value * 5;
			case APPLY_CAST_SPEED:              return bCaster ? value * 8 : value;
			case APPLY_MAX_HP_PCT:              return value * 15;
			case APPLY_DEF_GRADE_BONUS:
				return IsPlayerBotOffensiveSlot(wearCell) ? value * 2 : value * 6;
			// A bot walks kilometres between hubs and the horse is not always
			// under it, but speed is not power: a real line, not a great one.
			case APPLY_MOV_SPEED:               return value * 4;

			// The four stats, which roll to twelve on a weapon and a shield. A
			// point of the school's own stat is attack; a point of vitality is
			// health no reroll can take away. They used to be worth their own
			// number, so a maximum roll of the best stat in the game scored
			// twelve and lost to two percent of anything.
			case APPLY_CON:                     return value * 20;
			case APPLY_STR:                     return bCaster ? value * 8 : value * 25;
			case APPLY_INT:                     return bCaster ? value * 25 : value * 8;
			case APPLY_DEX:                     return value * 12;

			// A blocked hit is a hit that did not happen, and it answers melee -
			// 73% of the monsters in this world. Fifteen percent of every hit is
			// the roll a player keeps a shield for, after immunity to stun.
			case APPLY_BLOCK:                   return value * 20;
			// Dodge and arrow resistance answer a ranged attacker only, and
			// ranged monsters are between nothing and a quarter of a map: real,
			// and a fraction of what block is worth.
			case APPLY_DODGE:                   return value * 6;
			case APPLY_RESIST_BOW:              return value * 4;
			// battle_hit reads the attacker's WEAR_WEAPON to choose which of
			// these applies and a monster wears no weapon, so against anything a
			// bot fights these five do nothing whatever. Left at a point a line
			// rather than zero, because a line is still a line.
			case APPLY_RESIST_SWORD:
			case APPLY_RESIST_TWOHAND:
			case APPLY_RESIST_DAGGER:
			case APPLY_RESIST_BELL:
			case APPLY_RESIST_FAN:              return value;
			// An elemental resistance is applied at thirty percent of its own
			// number and only against a monster carrying that attack flag, so
			// the fifteen of a maximum roll is four and a half percent off the
			// hits of about half of one map. The player's table wanted a
			// resistance chosen per map; measured, the whole axis is too small
			// to plan a piece of gear around.
			case APPLY_RESIST_FIRE:
			case APPLY_RESIST_ELEC:
			case APPLY_RESIST_WIND:
			case APPLY_RESIST_ICE:
			case APPLY_RESIST_EARTH:
			case APPLY_RESIST_DARK:
			case APPLY_RESIST_MAGIC:            return value * 3;
			case APPLY_REFLECT_MELEE:           return value * 6;

			// A stunned monster does not hit back, which is worth more to a bot
			// than to a player: nothing here retreats from a fight it is winning.
			case APPLY_STUN_PCT:                return value * 10;
			case APPLY_SLOW_PCT:                return value * 6;
			case APPLY_POISON_PCT:              return value * 8;

			// The economy lines. A bot's drops are its gear, its refines, its
			// stall and its fares, so twenty percent more of them is a real
			// upgrade; experience is what the whole population is for.
			case APPLY_ITEM_DROP_BONUS:         return value * 8;
			case APPLY_EXP_DOUBLE_BONUS:        return value * 8;
			case APPLY_GOLD_DOUBLE_BONUS:       return value * 4;
			case APPLY_HP_REGEN:
			case APPLY_SP_REGEN:                return value * 2;

			// Big absolute numbers that have to be scaled down to compare with the
			// percentage lines above.
			case APPLY_MAX_HP:                  return value / 4;
			// The immunities roll as a 1, so they used to fall through to the
			// default and be worth one point - less than a point of movement
			// speed. Immunity to stun is the roll a player keeps a shield for
			// the rest of the game, and a bot was rerolling it away.
			case APPLY_IMMUNE_STUN:             return 400;
			case APPLY_IMMUNE_SLOW:             return 250;
			case APPLY_IMMUNE_FALL:             return 120;
			// Mana is what stops a bot keeping its buffs up - 213 of 1300 held
			// less than the 300 SP a mastered aura costs - and it rolls to
			// eighty, so this is one of the few lines that can fix that.
			case APPLY_MAX_SP:                  return bCaster ? value * 2 : value / 2;
			// Everything else - stamina, poison reduction, mana burn - is real but
			// minor for a bot that only grinds. Never zero: a line is still a line.
			default:                            return value;
		}
	}

	// The one roll that finishes an item, and it is a different roll for every
	// slot because `player.item_attr` lets a different set of lines onto every
	// slot.
	//
	// Everything above is a score, and a score can always be beaten by another
	// score - which means a perfect item is one unlucky comparison away from
	// being rerolled. These are the rolls a player stops on.
	//
	// The old rule asked a helmet for fifteen hundred health and either attack
	// value or arrow resistance, and asked an earring and a wrist for health and
	// critical. None of those five lines can roll on those slots at all - health
	// rolls on body, wrist, foots and neck, critical on weapon, foots and neck,
	// attack value on a body and nowhere else - so a helmet, an earring and a
	// wrist could never be finished, and were rerolled for as long as their
	// owner had gold. What each of them is actually worn for is here instead:
	// attack speed or arrow dodge on a helmet, the race line and item drop on an
	// earring, penetration and stolen life on a wrist.
	//
	// An item that has one is never rerolled again. It may still have a line
	// ADDED, because that cannot lose what is already there.
	bool HasPlayerBotFinishedBonus(LPCHARACTER ch, LPITEM item, BYTE wearCell)
	{
		if (!item)
			return false;

		long hp = 0, attGrade = 0, resistBow = 0, crit = 0, penetrate = 0;
		long average = 0, skill = 0, block = 0, dodge = 0, attSpeed = 0;
		long steal = 0, drop = 0, mov = 0, race = 0;
		bool immuneStun = false;
		// The race this bot is being paid for; a line against any other race is
		// not what a piece is kept for, however high it rolled.
		const BYTE wantedRace = GetPlayerBotRaceApplyType(GetPlayerBotFightingRace(ch));
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const BYTE type = item->GetAttributeType(i);
			const long value = item->GetAttributeValue(i);
			if (value <= 0)
				continue;
			if (wantedRace != APPLY_NONE && type == wantedRace)
				race = value;
			switch (type)
			{
				case APPLY_IMMUNE_STUN:             immuneStun = true; break;
				case APPLY_MAX_HP:                  hp = value; break;
				case APPLY_ATT_GRADE_BONUS:         attGrade = value; break;
				case APPLY_RESIST_BOW:              resistBow = value; break;
				case APPLY_CRITICAL_PCT:            crit = value; break;
				case APPLY_PENETRATE_PCT:           penetrate = value; break;
				case APPLY_NORMAL_HIT_DAMAGE_BONUS: average = value; break;
				case APPLY_SKILL_DAMAGE_BONUS:      skill = value; break;
				case APPLY_BLOCK:                   block = value; break;
				case APPLY_DODGE:                   dodge = value; break;
				case APPLY_ATT_SPEED:               attSpeed = value; break;
				case APPLY_STEAL_HP:                steal = value; break;
				case APPLY_ITEM_DROP_BONUS:         drop = value; break;
				case APPLY_MOV_SPEED:               mov = value; break;
				default: break;
			}
		}

		switch (wearCell)
		{
			case WEAR_SHIELD:
				// Immunity to stun first, as it always was; then the two lines a
				// shield is otherwise kept for, and both of them roll here and
				// nowhere else worth speaking of.
				return immuneStun || block >= PLAYERBOT_BONUS_KEEP_BLOCK ||
						race >= PLAYERBOT_BONUS_KEEP_RACE;
			case WEAR_WEAPON:
				// Any weapon, not only the level-30 family: with the vnum test
				// here a bow of forty-five with a 40% average was "unfinished"
				// and rerolled towards the line score until the average was
				// gone ("boty zmixowaly wysokie srednie 35+ na duzo mniejsze").
				//
				// The caster's clause is not generosity: item_addon.cpp draws
				// the skill line and then sets the average to minus twice it, so
				// a weapon cannot carry both and a Shaman that only ever stopped
				// on the average line never stopped at all.
				return average >= PLAYERBOT_BONUS_KEEP_AVERAGE ||
						(IsPlayerBotCaster(ch) && skill >= PLAYERBOT_BONUS_KEEP_SKILL);
			case WEAR_BODY:
				return hp >= PLAYERBOT_BONUS_KEEP_HP &&
						(attGrade > 0 || resistBow > 0 ||
						 steal >= PLAYERBOT_BONUS_KEEP_STEAL);
			case WEAR_HEAD:
				// No health, no attack value, no arrow resistance rolls here.
				return attSpeed >= PLAYERBOT_BONUS_KEEP_ATT_SPEED ||
						dodge >= PLAYERBOT_BONUS_KEEP_DODGE ||
						race >= PLAYERBOT_BONUS_KEEP_RACE;
			case WEAR_FOOTS:
				return hp >= PLAYERBOT_BONUS_KEEP_HP &&
						(attSpeed >= PLAYERBOT_BONUS_KEEP_ATT_SPEED ||
						 crit >= PLAYERBOT_BONUS_KEEP_CRIT ||
						 dodge >= PLAYERBOT_BONUS_KEEP_DODGE ||
						 mov >= PLAYERBOT_BONUS_KEEP_MOV);
			case WEAR_WRIST:
				// Critical does not roll on a wrist; penetration does.
				return hp >= PLAYERBOT_BONUS_KEEP_HP &&
						(penetrate >= PLAYERBOT_BONUS_KEEP_CRIT ||
						 steal >= PLAYERBOT_BONUS_KEEP_STEAL ||
						 drop >= PLAYERBOT_BONUS_KEEP_DROP ||
						 race >= PLAYERBOT_BONUS_KEEP_RACE);
			case WEAR_NECK:
				return hp >= PLAYERBOT_BONUS_KEEP_HP &&
						crit >= PLAYERBOT_BONUS_KEEP_CRIT;
			case WEAR_EAR:
				// Neither health nor critical rolls on an earring. What does is
				// the race line, item drop and movement speed.
				return race >= PLAYERBOT_BONUS_KEEP_RACE ||
						drop >= PLAYERBOT_BONUS_KEEP_DROP ||
						mov >= PLAYERBOT_BONUS_KEEP_MOV;
			default:
				return false;
		}
	}

	// The rolls a piece is priced up for: the top of what a line can be, or near
	// enough that a player keeps the item for it. A deliberately shorter list
	// than ScorePlayerBotBonusLine - the question here is not "is this line
	// good" but "is this the line somebody pays extra for" - and every number
	// is the lv5 column of `player.item_attr`, so it is the top of what this
	// world can actually roll rather than the top of what the wiki lists.
	//
	// Two entries used to name lines that cannot roll here at all: health as a
	// percentage is in no attribute table, and "strong against monsters" is only
	// in the rare one, where it is ten and not twenty.
	bool IsPlayerBotTopBonusLine(BYTE type, long value)
	{
		switch (type)
		{
			case APPLY_MAX_HP:                  return value >= 2000;
			case APPLY_MAX_SP:                  return value >= 80;
			case APPLY_CON:
			case APPLY_INT:
			case APPLY_STR:
			case APPLY_DEX:                     return value >= 12;
			case APPLY_CRITICAL_PCT:            return value >= 10;
			case APPLY_PENETRATE_PCT:           return value >= 10;
			case APPLY_SKILL_DAMAGE_BONUS:      return value >= 15;
			case APPLY_NORMAL_HIT_DAMAGE_BONUS: return value >= 20;
			// Twenty on the five ordinary races, ten on human, which rolls half
			// as high and half as often.
			case APPLY_ATTBONUS_ANIMAL:
			case APPLY_ATTBONUS_ORC:
			case APPLY_ATTBONUS_MILGYO:
			case APPLY_ATTBONUS_UNDEAD:
			case APPLY_ATTBONUS_DEVIL:          return value >= 20;
			case APPLY_ATTBONUS_HUMAN:          return value >= 10;
			case APPLY_ATTBONUS_MONSTER:        return value >= 10;
			case APPLY_ATT_GRADE_BONUS:         return value >= 50;
			case APPLY_ATT_SPEED:               return value >= 8;
			case APPLY_MOV_SPEED:               return value >= 20;
			case APPLY_STEAL_HP:                return value >= 10;
			case APPLY_BLOCK:
			case APPLY_DODGE:                   return value >= 15;
			case APPLY_ITEM_DROP_BONUS:
			case APPLY_EXP_DOUBLE_BONUS:        return value >= 20;
			case APPLY_IMMUNE_STUN:
			case APPLY_IMMUNE_SLOW:             return true;
			default:                            return false;
		}
	}

	// What the lines on an item add to its asking price, as a percentage.
	//
	// No character is asked for, on purpose: this is what any buyer pays, not
	// what one bot would wear, so the caster and weapon-slot weightings of
	// ScorePlayerBotItemBonuses are left out of it.
	int GetPlayerBotBonusPricePercent(LPITEM item)
	{
		if (!item)
			return 0;
		int lines = 0;
		int top = 0;
		int prize = 0;
		const bool bLevel30 = IsPlayerBotSpecialLevel30Weapon(item);
		const int count = item->GetAttributeCount();
		for (int i = 0; i < count && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const BYTE type = item->GetAttributeType(i);
			const long value = item->GetAttributeValue(i);
			if (type == 0 || value <= 0)
				continue;
			++lines;
			if (IsPlayerBotTopBonusLine(type, value))
				++top;
			// The roll a level-30 weapon is bought for. A top line is worth its
			// eighty percent on anything; on this set, a damage line in the
			// upper half of what can roll is the whole reason the piece changes
			// hands, and the price says so. See PLAYERBOT_PRIZE_AVERAGE_DAMAGE.
			if (bLevel30 &&
					((type == APPLY_NORMAL_HIT_DAMAGE_BONUS && value >= PLAYERBOT_PRIZE_AVERAGE_DAMAGE) ||
					 (type == APPLY_SKILL_DAMAGE_BONUS && value >= PLAYERBOT_PRIZE_SKILL_DAMAGE)))
				++prize;
		}
		if (lines == 0)
			return 0;
		const int percent = lines * PLAYERBOT_SHOP_BONUS_PER_LINE +
				(lines >= 4 ? PLAYERBOT_SHOP_BONUS_FOUR_PLUS : 0) +
				top * PLAYERBOT_SHOP_BONUS_TOP_LINE +
				prize * PLAYERBOT_SHOP_BONUS_PRIZE_LINE;
		return std::min(percent, PLAYERBOT_SHOP_BONUS_MAX_PERCENT);
	}

	int ScorePlayerBotItemBonuses(LPCHARACTER ch, LPITEM item, BYTE wearCell)
	{
		if (!ch || !item)
			return 0;
		int score = 0;
		const int count = item->GetAttributeCount();
		for (int i = 0; i < count && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			score += ScorePlayerBotBonusLine(ch, wearCell,
					item->GetAttributeType(i), item->GetAttributeValue(i));
		}
		return score;
	}

	// An item the engine will actually accept a stone on. UseItemEx refuses an
	// equipped item outright ("if (item2->IsEquipped()) return false"), costumes,
	// and anything without an attribute set, so a bot has to take the piece off
	// first - exactly as a player does.
	bool CanPlayerBotRerollItem(LPITEM item)
	{
		return item && item->GetType() != ITEM_COSTUME && !item->isLocked() &&
				!item->IsExchanging() && item->GetAttributeSetIndex() != -1 &&
				item->GetRefineLevel() >= PLAYERBOT_BONUS_MIN_REFINE;
	}

	// The stones cannot be dropped, sold, traded or shopped, so there is no market
	// to walk to: the bot pays for one the same way it pays for its stall.
	bool BuyPlayerBotBonusStone(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch)
			return false;
		if (ch->CountSpecifyItem(vnum) > 0)
			return true;
		if (ch->GetGold() - GetPlayerBotReservedGold(ch) <
				(int)(PLAYERBOT_BONUS_GOLD_FLOOR + PLAYERBOT_BONUS_STONE_PRICE))
			return false;
		if (ch->GetEmptyInventory(1) < 0)
			return false;
		if (!ch->AutoGiveItem(vnum, 1, -1, false))
			return false;
		PlayerBotChangeGold(ch, -(int)PLAYERBOT_BONUS_STONE_PRICE);
		return true;
	}

	bool ConsumePlayerBotBonusStone(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch)
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM stone = ch->GetInventoryItem(cell);
			if (!stone || stone->GetVnum() != vnum)
				continue;
			if (stone->GetCount() > 1)
				stone->SetCount(stone->GetCount() - 1);
			else
				ITEM_MANAGER::instance().RemoveItem(stone, "PLAYERBOT_BONUS");
			return true;
		}
		return false;
	}

	// Worn gear only. Spares in the bag are sold or put in a stall long before
	// they are worth polishing, and rerolling them would spend the gold the bot
	// needs for its next real upgrade.
	bool ManagePlayerBotBonusReroll(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || dwNow < state.dwNextBonusCheckTime)
			return false;
		state.dwNextBonusCheckTime = dwNow + PLAYERBOT_BONUS_INTERVAL;
		if (ch->GetLevel() < PLAYERBOT_BONUS_MIN_LEVEL)
			return false;
		if (ch->GetGold() - GetPlayerBotReservedGold(ch) <
				(int)(PLAYERBOT_BONUS_GOLD_FLOOR + PLAYERBOT_BONUS_STONE_PRICE))
			return false;

		const BYTE wearSlots[] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_HEAD, WEAR_SHIELD,
			WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR
		};

		int stonesUsed = 0;
		for (size_t i = 0; i < sizeof(wearSlots) / sizeof(wearSlots[0]) &&
				stonesUsed < PLAYERBOT_BONUS_STONES_PER_VISIT; ++i)
		{
			const BYTE wearCell = wearSlots[i];
			LPITEM item = ch->GetWear(wearCell);
			if (!CanPlayerBotRerollItem(item))
				continue;

			const int count = item->GetAttributeCount();
			const int score = ScorePlayerBotItemBonuses(ch, item, wearCell);

			// An empty line is free power: add before rerolling, always. Only once
			// the item is full does the quality of what it rolled start to matter,
			// and USE_CHANGE_ATTRIBUTE needs at least one line to work on anyway.
			// Five, not four: MAX_NORM_ATTR_NUM is 5 and AddAttribute happily
			// fills the fifth, so stopping at four left a line on the table.
			const bool bWantAdd = count < PLAYERBOT_BONUS_MAX_LINES;
			// An item that has landed the roll its slot is bought for is finished.
			// It can still gain a line - that cannot lose what is already there -
			// but it is never rerolled, whatever the score says.
			// A level-30 weapon is rerolled until it lands its average line,
			// whatever the score says: the score is a sum of good lines and a
			// weapon full of them at twelve percent average was "good enough"
			// to the score and not to anybody who looked at it.
			const bool bWantChange = !bWantAdd && !HasPlayerBotFinishedBonus(ch, item, wearCell) &&
					(score < PLAYERBOT_BONUS_KEEP_SCORE ||
					 IsPlayerBotSpecialLevel30WeaponVnum(item->GetVnum()));
			if (!bWantAdd && !bWantChange)
				continue;

			const DWORD stoneVnum = bWantAdd ? PLAYERBOT_BONUS_ADD_VNUM
					: PLAYERBOT_BONUS_CHANGE_VNUM;
			if (!BuyPlayerBotBonusStone(ch, stoneVnum))
				continue;

			// The piece has to come off for the engine to touch it, and it has to go
			// back on afterwards - a bot walking around with its weapon in the bag
			// would be worse than any bonus line it could win.
			if (!ch->UnequipItem(item))
				continue;

			if (bWantAdd)
				item->AddAttribute();
			else
				item->ChangeAttribute();

			ConsumePlayerBotBonusStone(ch, stoneVnum);
			++stonesUsed;

			const int newScore = ScorePlayerBotItemBonuses(ch, item, wearCell);
			if (!PlayerBotEquipItem(ch, item))
			{
				sys_err("PLAYERBOT_BONUS: could not re-equip pid=%u name=%s vnum=%u slot=%u",
						ch->GetPlayerID(), ch->GetName(), item->GetVnum(),
						(unsigned int)wearCell);
				continue;
			}

			sys_log(0, "PLAYERBOT_BONUS: %s pid=%u name=%s vnum=%u slot=%u lines=%d->%d score=%d->%d gold=%d",
					bWantAdd ? "added" : "rerolled", ch->GetPlayerID(), ch->GetName(),
					item->GetVnum(), (unsigned int)wearCell, count,
					item->GetAttributeCount(), score, newScore,
					(int)(ch->GetGold() / 1000));
		}

		// The level-30 weapons in the bag are goods, and a level-30 weapon
		// sells for its average line (PLAYERBOT_PRIZE_AVERAGE_DAMAGE). A stone
		// costs a fortieth of what the finished piece asks, so the ones that
		// have not rolled it yet are worked on here too - no unequipping, the
		// engine only refuses a worn item.
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS &&
				stonesUsed < PLAYERBOT_BONUS_STONES_PER_VISIT; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->IsEquipped() || !IsPlayerBotSpecialLevel30Weapon(item) ||
					!CanPlayerBotRerollItem(item))
				continue;
			const int count = item->GetAttributeCount();
			const bool bWantAdd = count < PLAYERBOT_BONUS_MAX_LINES;
			if (!bWantAdd && HasPlayerBotFinishedBonus(ch, item, WEAR_WEAPON))
				continue;
			const DWORD stoneVnum = bWantAdd ? PLAYERBOT_BONUS_ADD_VNUM
					: PLAYERBOT_BONUS_CHANGE_VNUM;
			if (!BuyPlayerBotBonusStone(ch, stoneVnum))
				break;
			const int score = ScorePlayerBotItemBonuses(ch, item, WEAR_WEAPON);
			if (bWantAdd)
				item->AddAttribute();
			else
				item->ChangeAttribute();
			ConsumePlayerBotBonusStone(ch, stoneVnum);
			++stonesUsed;
			sys_log(0, "PLAYERBOT_BONUS: %s goods pid=%u name=%s vnum=%u lines=%d->%d score=%d->%d gold=%d",
					bWantAdd ? "added" : "rerolled", ch->GetPlayerID(), ch->GetName(),
					item->GetVnum(), count, item->GetAttributeCount(), score,
					ScorePlayerBotItemBonuses(ch, item, WEAR_WEAPON), (int)(ch->GetGold() / 1000));
		}
		return stonesUsed > 0;
	}
}

#endif
