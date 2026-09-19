#ifndef __INC_PLAYERBOT_PERSONA_RULES_H__
#define __INC_PLAYERBOT_PERSONA_RULES_H__

// Iwakura's "SYSTEM OSOBOWOSCI v2.0" (19 September) as pure policy: the moods
// of his Bot Mood System, the Grinder's tiers and their experience locks, his
// Law of Advancement, the gambler's risk and the order in which the
// personalities claim a bot. No engine types, unit-tested
// (tests/playerbot_persona_rules_test.cpp); the engine's half is
// playerbot_mood.h and playerbot_persona.h.
//
// His document says a personality is not a bot's for life: it is what the bot
// is doing about its situation right now - a full bag makes a trader, a Metin
// in sight a stone breaker, a purse too heavy for the road a perfectionist or
// a gambler. So a personality here is an answer computed again every planning
// pass from signals the engine side gathers, and the old personality drawn
// by pid at login lives on underneath only as a character that tilts the odds
// (the operator's choice, 19 September).
//
// Every clock below counts elapsed play, not wall time: the engine side
// advances it by the time between two ticks, so what a bot remembers across a
// logout is how long it still has to run, and a bot that moves to another core
// takes the same numbers with it through its quest flags.
#include <cstdint>

namespace playerbot_persona
{
	// ---------------------------------------------------------------------
	// Personalities. Appended, never inserted: the id goes into the status
	// file both panels read and into the title the client draws.
	// ---------------------------------------------------------------------
	enum EPersona
	{
		PERSONA_GRINDER = 0,
		PERSONA_ZDOBYWCA,
		PERSONA_HANDLARZ,
		PERSONA_HAZARDZISTA,
		PERSONA_PERFEKCJONISTA,
		PERSONA_POGROMCA,
		PERSONA_GORNIK,
		PERSONA_RYBAK,
		PERSONA_NAJEMNIK,
		PERSONA_TOWARZYSZ,
		PERSONA_COUNT
	};

	// What the status file carries for a persona or a mood while the operator
	// has the system switched off.
	const unsigned int PERSONA_NONE = 255;

	// The title command carries the old personality as 0..10 and a persona as
	// this plus its id. A client older than the persona names refuses an id it
	// does not know and draws nothing, which is better than drawing the wrong
	// name: every persona id would otherwise land on an old personality's.
	const unsigned int PERSONA_TITLE_BASE = 100;

	// ---------------------------------------------------------------------
	// Moods (BMS). The document's three, in order, so a mood can go up or
	// down by one.
	// ---------------------------------------------------------------------
	enum EMood
	{
		MOOD_SLABY = 0,
		MOOD_NORMALNY,
		MOOD_BARDZO_DOBRY,
		MOOD_COUNT
	};

	// What holds a mood where it is. Euphoria (a refine to +8 or +9) holds
	// BARDZO DOBRY for three hours and nothing changes it; the capitulation of
	// the anti-PK protocol holds SLABY for forty-five minutes.
	enum EMoodLock
	{
		MOOD_LOCK_NONE = 0,
		MOOD_LOCK_EUPHORIA,
		MOOD_LOCK_CAPITULATION
	};

	const uint32_t MOOD_ROTATION_MS = 6u * 3600u * 1000u;      // "co rowne 6 godzin rozgrywki"
	const uint32_t MOOD_DROUGHT_MS = 30u * 60u * 1000u;        // "przez 30 minut ... pecha"
	const uint32_t MOOD_EUPHORIA_MS = 3u * 3600u * 1000u;      // "przez rowne 3 godziny"
	const uint32_t MOOD_CAPITULATION_MS = 45u * 60u * 1000u;   // "na 45 minut"

	// What Advance reports, as bits.
	const int MOOD_EVENT_ROTATED = 1;
	const int MOOD_EVENT_DROUGHT = 2;
	const int MOOD_EVENT_UNLOCKED = 4;

	struct TMood
	{
		uint8_t mood;
		uint8_t lockKind;
		// How long the lock still holds, how long the bot has played since the
		// last rotation, and how long it has hunted since its last good drop.
		uint32_t lockLeftMs;
		uint32_t playedMs;
		uint32_t droughtMs;

		TMood() : mood(MOOD_NORMALNY), lockKind(MOOD_LOCK_NONE), lockLeftMs(0),
			playedMs(0), droughtMs(0) {}
	};

	inline uint32_t SaturatingAdd(uint32_t a, uint32_t b)
	{
		return a > 0xFFFFFFFFu - b ? 0xFFFFFFFFu : a + b;
	}

	inline bool IsMoodLocked(const TMood& m)
	{
		return m.lockKind != MOOD_LOCK_NONE && m.lockLeftMs > 0;
	}

	inline uint8_t ClampMood(unsigned int value)
	{
		return value >= MOOD_COUNT ? (uint8_t)MOOD_NORMALNY : (uint8_t)value;
	}

	// A fresh mood out of a roll: the document's rotation is "calkowicie
	// losowy", so the three are equally likely.
	inline uint8_t RollMood(uint32_t roll)
	{
		return (uint8_t)(roll % MOOD_COUNT);
	}

	// Play time passes. The lock runs down first; the drought clock runs only
	// while the bot is hunting - a trader in town or an angler at the water is
	// not "unlucky" for standing there - and never under a lock, which the
	// document says nothing may worsen. A rotation due under a lock waits for
	// the lock to end rather than being lost, and then happens at once.
	inline int AdvanceMood(TMood& m, uint32_t dtMs, bool hunting, uint32_t roll)
	{
		int events = 0;
		if (m.lockKind != MOOD_LOCK_NONE)
		{
			if (m.lockLeftMs > dtMs)
				m.lockLeftMs -= dtMs;
			else
			{
				m.lockLeftMs = 0;
				m.lockKind = MOOD_LOCK_NONE;
				events |= MOOD_EVENT_UNLOCKED;
			}
		}
		m.playedMs = SaturatingAdd(m.playedMs, dtMs);
		if (!IsMoodLocked(m) && hunting)
		{
			m.droughtMs = SaturatingAdd(m.droughtMs, dtMs);
			if (m.droughtMs >= MOOD_DROUGHT_MS)
			{
				m.droughtMs = 0;
				if (m.mood > MOOD_SLABY)
				{
					--m.mood;
					events |= MOOD_EVENT_DROUGHT;
				}
			}
		}
		if (!IsMoodLocked(m) && m.playedMs >= MOOD_ROTATION_MS)
		{
			m.mood = RollMood(roll);
			m.playedMs = 0;
			m.droughtMs = 0;
			events |= MOOD_EVENT_ROTATED;
		}
		return events;
	}

	// Something from the document's list of valuable items came to hand: one
	// level up, and the drought clock starts again. Under a lock nothing moves
	// - euphoria is already at the top, and a capitulation is a lock the
	// document calls forced.
	inline bool OnValuableDrop(TMood& m)
	{
		m.droughtMs = 0;
		if (IsMoodLocked(m) || m.mood >= MOOD_BARDZO_DOBRY)
			return false;
		++m.mood;
		return true;
	}

	// A refine that landed on +8 or +9. A second one inside the three hours
	// starts the three hours again.
	inline void OnEuphoria(TMood& m)
	{
		m.mood = MOOD_BARDZO_DOBRY;
		m.lockKind = MOOD_LOCK_EUPHORIA;
		m.lockLeftMs = MOOD_EUPHORIA_MS;
		m.droughtMs = 0;
	}

	// A refine to +8 or +9 that failed - burned at the anvil, or brought down
	// a grade under a scroll, which the document calls burning as well
	// ("spalenie Zwojem ... zrzucilo przedmiot"): one level down (Iwakura, 19
	// September: "spalenie itemu na +8/+9 obniza mood o 1"). A lock holds, as
	// it holds against the drought - euphoria is three hours nothing may
	// worsen, and a capitulation is already at the bottom.
	const uint8_t MOOD_BIG_REFINE_PLUS = 8;

	inline bool OnBigRefineFailure(TMood& m, uint8_t targetPlus)
	{
		if (targetPlus < MOOD_BIG_REFINE_PLUS || IsMoodLocked(m) || m.mood <= MOOD_SLABY)
			return false;
		--m.mood;
		return true;
	}

	// The fifth death at a player's hands inside a quarter of an hour. The
	// euphoria lock outranks it: the document says nothing may change that
	// mood for its three hours, and a capitulation is a change.
	inline bool OnCapitulation(TMood& m)
	{
		if (m.lockKind == MOOD_LOCK_EUPHORIA && m.lockLeftMs > 0)
			return false;
		m.mood = MOOD_SLABY;
		m.lockKind = MOOD_LOCK_CAPITULATION;
		m.lockLeftMs = MOOD_CAPITULATION_MS;
		m.droughtMs = 0;
		return true;
	}

	// The mood the bot plays by. In a party or a dungeon it can still change
	// in the background, but the bot plays NORMALNY until it leaves.
	inline uint8_t EffectiveMood(const TMood& m, bool inGroupOrDungeon)
	{
		return inGroupOrDungeon ? (uint8_t)MOOD_NORMALNY : m.mood;
	}

	// SLABY's two habits: a pause of 2-8 seconds between one pack and the
	// next, and every 10-30 minutes a stop of 2-5 minutes - the player gone to
	// the kitchen.
	const uint32_t PAUSE_MIN_MS = 2000u;
	const uint32_t PAUSE_MAX_MS = 8000u;
	const uint32_t AFK_EVERY_MIN_MS = 10u * 60u * 1000u;
	const uint32_t AFK_EVERY_MAX_MS = 30u * 60u * 1000u;
	const uint32_t AFK_MIN_MS = 2u * 60u * 1000u;
	const uint32_t AFK_MAX_MS = 5u * 60u * 1000u;

	inline uint32_t RollBetween(uint32_t low, uint32_t high, uint32_t roll)
	{
		return high <= low ? low : low + roll % (high - low + 1u);
	}

	inline uint32_t PauseDuration(uint32_t roll) { return RollBetween(PAUSE_MIN_MS, PAUSE_MAX_MS, roll); }
	inline uint32_t AfkInterval(uint32_t roll) { return RollBetween(AFK_EVERY_MIN_MS, AFK_EVERY_MAX_MS, roll); }
	inline uint32_t AfkDuration(uint32_t roll) { return RollBetween(AFK_MIN_MS, AFK_MAX_MS, roll); }

	// ---------------------------------------------------------------------
	// The Grinder's tiers. What the document gives is a place and a band for
	// each tier and, for the first three, the level the bot holds itself at:
	// fifteen in the first village, twenty-three on the cursed ground of M3
	// (the level-30 weapons), thirty to thirty-five in the second village.
	// Past that it names only "the best level" of a map - 36 to 50 for the
	// valley and the desert - and Mount Sohan with no band at all, so those
	// locks are spread by pid over the upper part of the map's band, which is
	// where a player farming it would stand. Past the last tier a Grinder
	// holds wherever it is. The Monkey Dungeon is not a band of its own but a
	// choice of ground inside the others.
	//
	// The map placement in the travel code is by level already, so a bot held
	// at its tier's lock stays on that tier's map without being told to.
	// ---------------------------------------------------------------------
	struct TGrinderTier
	{
		uint8_t tier;
		uint8_t minLevel;
		uint8_t maxLevel;
		uint8_t lockMin;
		uint8_t lockMax;
	};

	const TGrinderTier GRINDER_TIERS[] = {
		{ 1, 10, 18, 15, 15 },  // first village
		{ 2, 19, 25, 23, 23 },  // M3, the cursed animals and the level-30 weapons
		{ 3, 26, 35, 30, 35 },  // second village
		{ 5, 36, 50, 40, 48 },  // Orc Valley and the Yongbi Desert
		{ 7, 51, 65, 55, 62 },  // Mount Sohan
	};
	const unsigned int GRINDER_TIER_COUNT = sizeof(GRINDER_TIERS) / sizeof(GRINDER_TIERS[0]);
	// Under this the bot is still learning to walk: no lock at all.
	const uint8_t GRINDER_FREE_BELOW = 10;
	// The tier number the document never names, for everything past Sohan.
	const uint8_t GRINDER_TIER_BEYOND = 8;

	inline uint32_t MixPid(uint32_t pid, uint32_t salt)
	{
		uint32_t h = pid ^ salt;
		h ^= h >> 16;
		h *= 0x85ebca6bu;
		h ^= h >> 13;
		h *= 0xc2b2ae35u;
		h ^= h >> 16;
		return h;
	}

	inline uint8_t GrinderTierFor(uint8_t level)
	{
		if (level < GRINDER_FREE_BELOW)
			return 0;
		for (unsigned int i = 0; i < GRINDER_TIER_COUNT; ++i)
			if (level >= GRINDER_TIERS[i].minLevel && level <= GRINDER_TIERS[i].maxLevel)
				return GRINDER_TIERS[i].tier;
		return GRINDER_TIER_BEYOND;
	}

	// The level a Grinder of this level holds at: the tier's lock, spread by
	// pid inside the tier's lock range, or the bot's own level when it has
	// already passed that (it holds where it stands). Zero is no lock.
	inline uint8_t GrinderLockFor(uint8_t level, uint32_t pid)
	{
		if (level < GRINDER_FREE_BELOW)
			return 0;
		for (unsigned int i = 0; i < GRINDER_TIER_COUNT; ++i)
		{
			const TGrinderTier& t = GRINDER_TIERS[i];
			if (level < t.minLevel || level > t.maxLevel)
				continue;
			const uint8_t lock = (uint8_t)(t.lockMin +
					MixPid(pid, 0x4c4f434bu) % (uint32_t)(t.lockMax - t.lockMin + 1));
			return lock < level ? level : lock;
		}
		return level;
	}

	// ---------------------------------------------------------------------
	// The Law of Advancement ("Prawo Awansu"): a Grinder never moves on to a
	// harder tier without a weapon at +7, an armour at +6 and a shield at +6,
	// and "zgodnie z obowiazujaca Tierlista" - each of them a piece for about
	// the bot's own level, not a +9 bought at level ten. A piece counts while
	// its level limit is within AWANS_LEVEL_WINDOW of the bot; the special
	// weapons of level thirty (his PVE 4-5 list) are good for longer, which is
	// what every player of this world does with them.
	// ---------------------------------------------------------------------
	const uint8_t AWANS_WEAPON_PLUS = 7;
	const uint8_t AWANS_ARMOUR_PLUS = 6;
	const uint8_t AWANS_SHIELD_PLUS = 6;
	const uint8_t AWANS_LEVEL_WINDOW = 20;
	const uint8_t AWANS_PREMIUM_LEVEL_WINDOW = 30;
	// A shield is asked for its +6 and not for its level. The document wants
	// one "jak najbardziej zblizona do aktualnego poziomu", and this world
	// cannot supply that: the merchants sell the level-0 Bojowa Tarcza and
	// nothing else, and measured on m2zip on 19 September the whole world held
	// 1353 shields of level 0, 68 of 21, 95 of 41, two of 61 - so a window
	// would have held every bot past forty at its lock for good. The
	// equipment pass still wears the best shield the bot finds.
	const bool AWANS_SHIELD_ANY_LEVEL = true;
	// M3's entry for a Grinder: a weapon at +6 and an armour at +5. The Mental
	// Warrior's Strong Body stands in for the armour, so it goes in with the
	// weapon alone.
	const uint8_t M3_WEAPON_PLUS = 6;
	const uint8_t M3_ARMOUR_PLUS = 5;

	struct TGearPiece
	{
		bool present;
		uint8_t plus;
		uint8_t levelLimit;
		// A piece that stays good past the ordinary window.
		bool premium;
		TGearPiece() : present(false), plus(0), levelLimit(0), premium(false) {}
		TGearPiece(uint8_t p, uint8_t limit, bool prem = false) :
			present(true), plus(p), levelLimit(limit), premium(prem) {}
	};

	struct TAdvanceGear
	{
		uint8_t level;
		TGearPiece weapon;
		TGearPiece armour;
		TGearPiece shield;
		// A bow and a two-handed weapon leave the shield slot empty for good.
		bool wantsShield;
		TAdvanceGear() : level(1), wantsShield(true) {}
	};

	// What is missing, as bits: zero is the law met.
	const int AWANS_GAP_WEAPON = 1;
	const int AWANS_GAP_ARMOUR = 2;
	const int AWANS_GAP_SHIELD = 4;

	inline bool IsPieceCurrent(const TGearPiece& p, uint8_t level)
	{
		const unsigned int window = p.premium ? AWANS_PREMIUM_LEVEL_WINDOW : AWANS_LEVEL_WINDOW;
		return p.present && (unsigned int)p.levelLimit + window >= (unsigned int)level;
	}

	inline int AwansGaps(const TAdvanceGear& g)
	{
		int gaps = 0;
		if (!IsPieceCurrent(g.weapon, g.level) || g.weapon.plus < AWANS_WEAPON_PLUS)
			gaps |= AWANS_GAP_WEAPON;
		if (!IsPieceCurrent(g.armour, g.level) || g.armour.plus < AWANS_ARMOUR_PLUS)
			gaps |= AWANS_GAP_ARMOUR;
		const bool shieldCurrent = g.shield.present &&
				(AWANS_SHIELD_ANY_LEVEL || IsPieceCurrent(g.shield, g.level));
		if (g.wantsShield && (!shieldCurrent || g.shield.plus < AWANS_SHIELD_PLUS))
			gaps |= AWANS_GAP_SHIELD;
		return gaps;
	}

	inline bool MeetsM3Survival(const TAdvanceGear& g, bool mentalWarrior)
	{
		if (!g.weapon.present || g.weapon.plus < M3_WEAPON_PLUS)
			return false;
		return mentalWarrior || (g.armour.present && g.armour.plus >= M3_ARMOUR_PLUS);
	}

	// A Conqueror that dies this often to monsters has outgrown its gear:
	// "bot za czesto ginie i traci expa". It goes back to grinding, held at
	// the level it has reached.
	const uint8_t WEAK_DEATHS = 3;
	const uint32_t WEAK_WINDOW_MS = 30u * 60u * 1000u;

	// The last WEAK_DEATHS deaths to monsters, as ages in the same elapsed-play
	// clock the moods use. NoteDeath returns true when this death makes the
	// bot weak.
	struct TDeathWindow
	{
		uint32_t agoMs[WEAK_DEATHS];
		uint8_t count;
		TDeathWindow() : count(0)
		{
			for (unsigned int i = 0; i < WEAK_DEATHS; ++i)
				agoMs[i] = 0;
		}
	};

	inline void AdvanceDeathWindow(TDeathWindow& w, uint32_t dtMs)
	{
		uint8_t kept = 0;
		for (uint8_t i = 0; i < w.count; ++i)
		{
			const uint32_t age = SaturatingAdd(w.agoMs[i], dtMs);
			if (age < WEAK_WINDOW_MS)
				w.agoMs[kept++] = age;
		}
		w.count = kept;
	}

	inline bool NoteDeath(TDeathWindow& w)
	{
		if (w.count == WEAK_DEATHS)
		{
			for (unsigned int i = 1; i < WEAK_DEATHS; ++i)
				w.agoMs[i - 1] = w.agoMs[i];
			w.count = WEAK_DEATHS - 1;
		}
		w.agoMs[w.count++] = 0;
		return w.count >= WEAK_DEATHS;
	}

	// ---------------------------------------------------------------------
	// The gambler (Hazardzista). Each item it takes to the anvil gets its own
	// ambition - +7 six times in ten, +8 three, +9 one - and is worked the
	// document's way: the plain blacksmith up to +7, the Blessing Scroll for
	// +8 and +9 and nothing else. A scroll that fails hands the item back a
	// grade down; after that the item is taken back to +7 at the anvil and
	// sold as it is, whatever it was meant to reach.
	// ---------------------------------------------------------------------
	const int GAMBLE_BUDGET_PERCENT = 40;
	const int PERFECT_BUDGET_PERCENT = 80;
	const uint8_t GAMBLE_SAFE_PLUS = 7;

	inline uint8_t RollGambleTarget(uint32_t roll)
	{
		const uint32_t r = roll % 100u;
		return r < 60u ? 7 : (r < 90u ? 8 : 9);
	}

	enum EGambleStep
	{
		GAMBLE_STEP_PLAIN = 0,   // the ordinary blacksmith
		GAMBLE_STEP_SCROLL,      // under a Blessing Scroll
		GAMBLE_STEP_DONE         // for sale as it stands
	};

	inline EGambleStep NextGambleStep(uint8_t plus, uint8_t target, bool scrollFailed)
	{
		if (scrollFailed)
			return plus < GAMBLE_SAFE_PLUS ? GAMBLE_STEP_PLAIN : GAMBLE_STEP_DONE;
		if (plus < GAMBLE_SAFE_PLUS)
			return GAMBLE_STEP_PLAIN;
		if (plus < target)
			return GAMBLE_STEP_SCROLL;
		return GAMBLE_STEP_DONE;
	}

	// What a gambler or a perfectionist may still spend: its share of the
	// purse it came in with, less what it has already spent. Never negative.
	inline long long BudgetLeft(long long goldAtStart, int sharePercent, long long spent)
	{
		const long long budget = goldAtStart > 0 ? goldAtStart * sharePercent / 100 : 0;
		return spent >= budget ? 0 : budget - spent;
	}

	// ---------------------------------------------------------------------
	// The stone hunter (Pogromca metinow). A Metin in sight within ten levels
	// either way claims the bot; three bots of its own kingdom on one already
	// are enough and it goes back to what it was doing; below 35% health it
	// turns on the stone's monsters and then comes back; and a stone that has
	// killed it more than six times is given up.
	// ---------------------------------------------------------------------
	const int POGROMCA_LEVEL_BAND = 10;
	const int POGROMCA_KINGDOM_CROWD = 3;
	const int POGROMCA_RETREAT_HP_PERCENT = 35;
	const unsigned int POGROMCA_MAX_DEATHS = 6;

	inline bool InPogromcaBand(int botLevel, int stoneLevel)
	{
		const int delta = stoneLevel - botLevel;
		return delta <= POGROMCA_LEVEL_BAND && delta >= -POGROMCA_LEVEL_BAND;
	}

	inline bool IsPogromcaCrowded(int sameKingdomBots)
	{
		return sameKingdomBots >= POGROMCA_KINGDOM_CROWD;
	}

	inline bool IsPogromcaRetreat(int hp, int maxHp)
	{
		return maxHp > 0 && (long long)hp * 100 < (long long)maxHp * POGROMCA_RETREAT_HP_PERCENT;
	}

	inline bool PogromcaGivesUp(unsigned int deathsAtStone)
	{
		return deathsAtStone > POGROMCA_MAX_DEATHS;
	}

	// ---------------------------------------------------------------------
	// The Anti-PK protocol. One death at a player's hands is an incident; the
	// fifth inside fifteen minutes on the same ground is harassment, and the
	// bot capitulates: SLABY for forty-five minutes (OnCapitulation), the
	// ground given up for as long, and - outside a party, from level thirty -
	// an eight percent chance of an hour at the water instead.
	// ---------------------------------------------------------------------
	const unsigned int PK_DEATHS = 5;
	// Deaths remembered, more than the five that count: a death somewhere
	// else in between must not push one of the five out of the window.
	const unsigned int PK_MEMORY = 10;
	const uint32_t PK_WINDOW_MS = 15u * 60u * 1000u;
	const long PK_SPOT_RADIUS = 5000;
	const uint32_t PK_CAPITULATION_MS = MOOD_CAPITULATION_MS;
	const uint32_t PK_FISHING_PERMILLE = 80u;
	const int PK_FISHING_MIN_LEVEL = 30;
	const uint32_t PK_FISHING_MS = 60u * 60u * 1000u;

	struct TPkDeaths
	{
		unsigned int count;
		uint32_t atMs[PK_MEMORY];
		long map[PK_MEMORY];
		long x[PK_MEMORY];
		long y[PK_MEMORY];
		TPkDeaths() : count(0)
		{
			for (unsigned int i = 0; i < PK_MEMORY; ++i)
			{
				atMs[i] = 0;
				map[i] = 0;
				x[i] = 0;
				y[i] = 0;
			}
		}
	};

	inline bool IsPkSameSpot(long mapA, long xA, long yA, long mapB, long xB, long yB)
	{
		if (mapA != mapB)
			return false;
		const long long dx = (long long)xA - xB;
		const long long dy = (long long)yA - yB;
		return dx * dx + dy * dy <= (long long)PK_SPOT_RADIUS * PK_SPOT_RADIUS;
	}

	// A death at a player's hands at nowMs (a millisecond clock that may wrap):
	// deaths older than the window are forgotten, this one is kept, and the
	// answer is whether it makes the fifth inside the window on the same ground
	// - in which case the window starts afresh, so the next capitulation needs
	// five more.
	inline bool NotePkDeath(TPkDeaths& w, uint32_t nowMs, long mapIndex, long x, long y)
	{
		unsigned int kept = 0;
		for (unsigned int i = 0; i < w.count; ++i)
		{
			if ((uint32_t)(nowMs - w.atMs[i]) >= PK_WINDOW_MS)
				continue;
			w.atMs[kept] = w.atMs[i];
			w.map[kept] = w.map[i];
			w.x[kept] = w.x[i];
			w.y[kept] = w.y[i];
			++kept;
		}
		w.count = kept;
		if (w.count == PK_MEMORY)
		{
			for (unsigned int i = 1; i < PK_MEMORY; ++i)
			{
				w.atMs[i - 1] = w.atMs[i];
				w.map[i - 1] = w.map[i];
				w.x[i - 1] = w.x[i];
				w.y[i - 1] = w.y[i];
			}
			w.count = PK_MEMORY - 1;
		}
		w.atMs[w.count] = nowMs;
		w.map[w.count] = mapIndex;
		w.x[w.count] = x;
		w.y[w.count] = y;
		++w.count;
		unsigned int near = 0;
		for (unsigned int i = 0; i < w.count; ++i)
			if (IsPkSameSpot(w.map[i], w.x[i], w.y[i], mapIndex, x, y))
				++near;
		if (near < PK_DEATHS)
			return false;
		w = TPkDeaths();
		return true;
	}

	// The eight percent: from level thirty, never in a party ("przez pobyt w PT
	// nie ma 8% szansy").
	inline bool RollCapitulationFishing(uint32_t roll, int level, bool inParty)
	{
		return !inParty && level >= PK_FISHING_MIN_LEVEL && roll % 1000u < PK_FISHING_PERMILLE;
	}

	// ---------------------------------------------------------------------
	// Which personality claims the bot. A contract is the strongest claim, a
	// party the next - both are commitments to somebody else - then the two
	// sessions that hold a tool in the weapon hand, the stone under the
	// hammer, the two errands at the anvil, the full bag, and last what the
	// bot does when nothing asks: grind, or level if it has earned it.
	// ---------------------------------------------------------------------
	struct TPersonaSignals
	{
		bool mercenary;   // hired and paid for, as the strong side
		bool inParty;     // a party of any kind, the mercenary's excepted
		bool fishing;
		bool mining;
		bool stoneFight;
		bool gambling;
		bool perfecting;
		bool trading;
		bool advanced;
		TPersonaSignals() : mercenary(false), inParty(false), fishing(false), mining(false),
			stoneFight(false), gambling(false), perfecting(false), trading(false), advanced(false) {}
	};

	inline uint8_t DecidePersona(const TPersonaSignals& s)
	{
		if (s.mercenary)
			return PERSONA_NAJEMNIK;
		if (s.inParty)
			return PERSONA_TOWARZYSZ;
		if (s.fishing)
			return PERSONA_RYBAK;
		if (s.mining)
			return PERSONA_GORNIK;
		if (s.stoneFight)
			return PERSONA_POGROMCA;
		if (s.gambling)
			return PERSONA_HAZARDZISTA;
		if (s.perfecting)
			return PERSONA_PERFEKCJONISTA;
		if (s.trading)
			return PERSONA_HANDLARZ;
		return s.advanced ? (uint8_t)PERSONA_ZDOBYWCA : (uint8_t)PERSONA_GRINDER;
	}
}

#endif
