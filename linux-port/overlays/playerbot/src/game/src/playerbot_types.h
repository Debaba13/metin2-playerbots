#ifndef __INC_METIN2_PLAYERBOT_TYPES_H__
#define __INC_METIN2_PLAYERBOT_TYPES_H__

// Tuning constants, enums and the per-bot state that the rest of the playerbot
// code is written against.
//
// This is an implementation fragment, not a normal header: it defines objects,
// it relies on the engine headers playerbot_manager.cpp includes above it, and
// its anonymous namespace is deliberately the same one the manager reopens --
// in a single translation unit those merge. Include it exactly once, from
// playerbot_manager.cpp, and nowhere else.

namespace
{
	const int PLAYERBOT_SEARCH_RANGE = 6000;
	const size_t PLAYERBOT_TARGET_CHOICE_WINDOW = 16;
	// Ordinary grinders chain into a nearby free pack before considering a
	// distant high-score target. Claims still spread a crowd over different mobs.
	const int PLAYERBOT_LOCAL_CHAIN_RANGE = 2500;
	// How far below itself a bot still counts a monster as prey. The engine's own
	// experience table settles the number: aiPercentByDeltaLev pays 70% at nine
	// levels down, 50% at ten and one per cent from fifteen. So nine is the last
	// step before the reward halves, and a level-19 bot swinging at one of Joan's
	// level-1 stray dogs earns a hundredth of a kill - which is the "boty bija
	// psy" the Discord keeps reporting. Anything lower is passed over while
	// something worth the swing is in reach, and taken when nothing else is.
	const int PLAYERBOT_TRIVIAL_LEVEL_GAP = 9;
	const int PLAYERBOT_MELEE_RANGE = 250;
	const int PLAYERBOT_MELEE_SPLASH_RANGE = 300;
	const size_t PLAYERBOT_MAX_MELEE_TARGETS = 4;
	const int PLAYERBOT_MAX_TARGET_LEVEL_DELTA = 15;
	const int PLAYERBOT_LOOT_SEARCH_RANGE = 2500;
	const int PLAYERBOT_PICKUP_RANGE = 300;
	// Keep a fresh drop visible for a human-readable moment and pick individual
	// stacks at a believable cadence instead of clearing the floor in one tick.
	const DWORD PLAYERBOT_LOOT_VISIBLE_DELAY_MIN = 1000;
	const DWORD PLAYERBOT_LOOT_VISIBLE_DELAY_MAX = 1800;
	const DWORD PLAYERBOT_LOOT_PICKUP_INTERVAL_MIN = 450;
	const DWORD PLAYERBOT_LOOT_PICKUP_INTERVAL_MAX = 850;
	// Yang is taken almost at once. The pause above exists so a bot does not
	// hoover a field the instant it drops, but a coin pile is one click a player
	// never hesitates over, and three of them in a row had bots standing in a
	// cleared field for six seconds instead of finding the next pack.
	const DWORD PLAYERBOT_LOOT_MONEY_DELAY_MIN = 150;
	const DWORD PLAYERBOT_LOOT_MONEY_DELAY_MAX = 350;
	const DWORD PLAYERBOT_LOOT_MONEY_INTERVAL_MIN = 150;
	const DWORD PLAYERBOT_LOOT_MONEY_INTERVAL_MAX = 300;
	// A combat pickup is a cheap-looking action but an expensive query: Metin2's
	// ForEachAround snapshots every entity in nine neighbouring sectrees before
	// the callback can apply the 3 m pickup radius.  Throttle empty scans as well
	// as successful pickups, otherwise hundreds of fighting bots repeat the same
	// work several thousand times per second.
	const DWORD PLAYERBOT_COMBAT_LOOT_SCAN_INTERVAL_MIN = 750;
	const DWORD PLAYERBOT_COMBAT_LOOT_SCAN_INTERVAL_MAX = 1000;
	const DWORD PLAYERBOT_EMPTY_LOOT_SCAN_INTERVAL_MIN = 750;
	const DWORD PLAYERBOT_EMPTY_LOOT_SCAN_INTERVAL_MAX = 1000;
	const DWORD PLAYERBOT_LOOT_THREAT_SCAN_INTERVAL_MIN = 900;
	const DWORD PLAYERBOT_LOOT_THREAT_SCAN_INTERVAL_MAX = 1300;
	const DWORD PLAYERBOT_LOOT_CLEANUP_INTERVAL = 10000;
	const DWORD PLAYERBOT_INVENTORY_MAINTENANCE_MIN = 30000;
	const DWORD PLAYERBOT_INVENTORY_MAINTENANCE_MAX = 60000;
	const int PLAYERBOT_POTION_HP_PERCENT = 65;
	const int PLAYERBOT_POTION_SP_PERCENT = 30;
	const int PLAYERBOT_RECOVERY_HP_PERCENT = 75;
	const int PLAYERBOT_RECOVERY_INITIAL_HP_PERCENT = 20;
	const int PLAYERBOT_RECOVERY_REST_HEAL_PERCENT = 5;
	const int PLAYERBOT_RETREAT_START_HP_PERCENT = 35;
	const int PLAYERBOT_RETREAT_END_HP_PERCENT = 65;
	const DWORD PLAYERBOT_RETREAT_MOVE_INTERVAL = 1800;
	const DWORD PLAYERBOT_ATTACK_INTERVAL = 1200;
	const DWORD PLAYERBOT_POTION_INTERVAL = 1000;
	// How long a bot lies where it fell. A player sees a body on the ground and
	// then sees it get up; eleven seconds was close to that already and ten is
	// what it is meant to be.
	const DWORD PLAYERBOT_REVIVE_DELAY = 10000;
	const DWORD PLAYERBOT_GEAR_RETRY_INTERVAL = 1000;
	const DWORD PLAYERBOT_EQUIPMENT_CHECK_INTERVAL = 1000;
	const DWORD PLAYERBOT_EQUIPMENT_COMBAT_DELAY = 1700;
	const DWORD PLAYERBOT_GEAR_LOG_INTERVAL = 10000;
	const DWORD PLAYERBOT_WOODEN_ARROW_VNUM = 8000;
	const int PLAYERBOT_ARROW_RESTOCK_THRESHOLD = 100;
	const int PLAYERBOT_ARROW_SMALL_BUNDLE = 100;
	const int PLAYERBOT_ARROW_LARGE_BUNDLE = 200;
	const DWORD PLAYERBOT_POTION_LOG_INTERVAL = 10000;
	// The engine already saves every character on save_event_second_cycle,
	// which config.cpp sets to 120 s, and a level change forces a save below
	// regardless of this timer. At 30 s the bots were adding four extra saves
	// per engine save each - close to thirty a second across the population - for nothing
	// the engine's own cycle does not already cover.
	const DWORD PLAYERBOT_PERSIST_INTERVAL = 120000;

	// What the population cost this minute, counted where it happens and
	// reported once from Update. These are the things that do not log per
	// event and are therefore invisible when the core is hot: A* searches, whole
	// map snapshots for the material errand, and character saves.
	DWORD s_uPlayerBotLoadPlans = 0;
	DWORD s_uPlayerBotLoadScans = 0;
	DWORD s_uPlayerBotLoadSaves = 0;
	DWORD s_uPlayerBotLoadWatchdog = 0;
	DWORD s_dwPlayerBotLoadReportTime = 0;
	const DWORD PLAYERBOT_LOAD_REPORT_INTERVAL = 60000;
	// And how long they took. A count says how often; only the clock says
	// whether it matters. Microseconds from the monotonic clock, wrapping in a
	// DWORD every 71 minutes - which the unsigned subtraction below survives.
	DWORD s_uPlayerBotLoadPlanUs = 0;
	DWORD s_uPlayerBotLoadScanUs = 0;
	DWORD s_uPlayerBotLoadTickUs = 0;
	DWORD s_uPlayerBotLoadTickMaxUs = 0;
	DWORD s_uPlayerBotLoadTicks = 0;
	// The two passes inside the tick that sweep the nine sectrees around a bot
	// - looking for something to hit, and writing the panel snapshot - are
	// counted apart, because a bot with nothing to hit repeats the sweep every
	// tick and there is no event to see it by.
	DWORD s_uPlayerBotLoadTargetSearches = 0;
	DWORD s_uPlayerBotLoadTargetMisses = 0;
	DWORD s_uPlayerBotLoadTargetUs = 0;
	DWORD s_uPlayerBotLoadSnapshotUs = 0;
	// Plans by how far they reach, in grid cells: under 64, under 256, under
	// 1024, and beyond. A short hop to the next monster and a crossing of the
	// whole valley are both "a plan", and only the split says which one is
	// paying for the other.
	DWORD s_uPlayerBotLoadPlanBucket[4] = { 0, 0, 0, 0 };
	DWORD s_uPlayerBotLoadPlanBucketUs[4] = { 0, 0, 0, 0 };
	// Plans a tick turned away because it had already spent its planning time.
	// Deferred is not lost: the bot asks again within two seconds.
	DWORD s_uPlayerBotLoadPlanDeferred = 0;
	DWORD s_uPlayerBotLoadPlanResumed = 0;
	DWORD s_uPlayerBotLoadPlanCached = 0;

	inline DWORD PlayerBotClockUs()
	{
		struct timespec ts;
		clock_gettime(CLOCK_MONOTONIC, &ts);
		return (DWORD)((unsigned long long)ts.tv_sec * 1000000ULL + (unsigned long long)ts.tv_nsec / 1000ULL);
	}

	// Adds the scope's duration to a counter on the way out, whichever of the
	// function's returns is taken.
	struct TPlayerBotLoadTimer
	{
		DWORD& m_acc;
		DWORD m_start;
		explicit TPlayerBotLoadTimer(DWORD& acc) : m_acc(acc), m_start(PlayerBotClockUs()) {}
		~TPlayerBotLoadTimer() { m_acc += PlayerBotClockUs() - m_start; }
	};
	const DWORD PLAYERBOT_RECOVERY_PROTECTION_INTERVAL = 3000;
	const DWORD PLAYERBOT_RECOVERY_REST_HEAL_INTERVAL = 1000;
	const DWORD PLAYERBOT_BUFF_FALLBACK_DURATION = 60000;
	const DWORD PLAYERBOT_SHAMAN_ATTACK_SKILL_INTERVAL = 6000;
	const DWORD PLAYERBOT_STAT_CHECK_INTERVAL = 1000;
	const DWORD PLAYERBOT_SKILL_CHECK_INTERVAL = 1000;
	const DWORD PLAYERBOT_SKILL_BOOK_CHECK_INTERVAL = 8000;
	// How many books of one of its own skills a bot keeps. Ten successful
	// reads take a skill from M1 to G1 and a read succeeds two times in three,
	// so this is one skill's worth with a spare; the rest go on a counter or
	// to the merchant. Before this a bot kept every book for a skill it could
	// not read for weeks, and the bag filled with them.
	const int PLAYERBOT_BOOK_KEEP_PER_SKILL = 12;
	// A bag this short of cells is under pressure: what was worth keeping on
	// the chance of a key or a buyer goes to the merchant, so the chests and
	// the loot still have somewhere to land.
	const int PLAYERBOT_BAG_PRESSURE_FREE_CELLS = 8;
	const DWORD PLAYERBOT_SOUL_STONE_CHECK_INTERVAL = 10000;
	// What UseItemEx leaves in the socket when the 30% roll fails. Defined as a
	// file-local const in char_item.cpp, so it is repeated here.
	const DWORD PLAYERBOT_BROKEN_SOUL_STONE_VNUM = 28960;
	const DWORD PLAYERBOT_PARTY_SHARE_INTERVAL = 20000;
	const DWORD PLAYERBOT_GOAL_PLAN_INTERVAL = 5000;
	// How long the population takes to log in after a start, and how often a
	// batch goes out. The whole cohort used to be asked for in one call, and the
	// database answered in one second: 848 characters entering the world at
	// once, every one of them asking for a route in its first tick against a
	// navigation budget of 32 plans per tick. What could not be planned stood
	// still, the inactivity watchdog reset it, and the reset asked again - 4075
	// resets in the first nine minutes, and one core pinned. A minute's worth of
	// batches is long enough that no tick sees more arrivals than it can plan
	// for, and short enough that nobody watching notices the world filling up.
	const DWORD PLAYERBOT_SPAWN_WINDOW = 60000;
	const DWORD PLAYERBOT_SPAWN_BATCH_INTERVAL = 1000;
	// And how often the world is counted afterwards, to put back what it has
	// lost. The queue used to be filled once at startup and never again: a bot
	// that failed to enter the world, or left it later for any reason, was gone
	// until the next restart. An operator reported a thousand asked for, six
	// hundred and fifty arriving, and three hundred and fifty an hour later -
	// and nothing in the core would have noticed any of that.
	const DWORD PLAYERBOT_TOPUP_INTERVAL = 60000;
	// And the same spread for a bot's own first heavy passes - the refine, the
	// gear pass, the shopping decision - which all had timers of zero and so
	// all ran on the bot's first tick, whichever second it logged in.
	const DWORD PLAYERBOT_FIRST_PASS_SPREAD = 60000;
	const DWORD PLAYERBOT_STATUS_SNAPSHOT_INTERVAL = 2000;
	// A Metin which repeatedly heals all dealt damage is not progress. Sample its
	// lowest observed HP at a deliberately cheap cadence, give a newcomer time to
	// change the outcome, and only then let the bot look for a productive target.
	const DWORD PLAYERBOT_STONE_PROGRESS_CHECK_INTERVAL = 4000;
	// The same three numbers for an ordinary monster. Slightly more patient than
	// the stone timings: a stone stands still and takes what it is given, while
	// a monster that fights back can leave a bot chasing it round a tree for a
	// few seconds without that meaning the fight is hopeless.
	const DWORD PLAYERBOT_FIGHT_INITIAL_GRACE = 20000;
	const DWORD PLAYERBOT_FIGHT_STALL_TIMEOUT = 30000;
	const DWORD PLAYERBOT_FIGHT_FAILED_COOLDOWN = 120000;

	const DWORD PLAYERBOT_STONE_INITIAL_GRACE = 18000;
	const DWORD PLAYERBOT_STONE_SOLO_STALL_TIMEOUT = 26000;
	const DWORD PLAYERBOT_STONE_GROUP_STALL_TIMEOUT = 42000;
	const DWORD PLAYERBOT_STONE_FAILED_COOLDOWN = 90000;
	const int PLAYERBOT_STONE_SUPPORT_RANGE = 2200;
	const DWORD PLAYERBOT_BUFF_INTERVAL = 2000;
	const DWORD PLAYERBOT_SKILL_ATTACK_INTERVAL = 2500;
	// A client-side skill motion is longer than one normal attack tick.  Without
	// this lock a basic bow/dagger hit replaced the skill animation after 600 ms,
	// although the server had already applied the skill damage.
	const DWORD PLAYERBOT_SKILL_ANIMATION_LOCK = 1400;
	const BYTE PLAYERBOT_RESERVE_GEAR_MIN_REFINE = 6;
	// A +7 or better is never NPC fodder. The merchant pays a fifth of the shop
	// price for it, and a bot vendored a Riba +9 for exactly that because it
	// happened to be carrying an axe +9 as well - the "keep only the best spare
	// per slot" rule had no idea what it was throwing away. Anything at this
	// refine goes on a stall instead, where another bot can pay properly.
	// How long after its last swing a bot still counts as hunting. A session is
	// a string of fights with gaps for walking and looting between them, so the
	// window has to outlast a gap without outlasting the walk back to town.
	const DWORD PLAYERBOT_BUFF_COMBAT_WINDOW = 60000;
	// How soon a bot comes back for the next buff once it has found one
	// missing. One cast claims the tick, so five seconds between them meant a
	// Warrior needed ten seconds for aura and berserk and a weapon Sura fifteen
	// for its three enchantments - longer than most of the fights they were
	// buffing for, which is why they were usually seen without them.
	const DWORD PLAYERBOT_BUFF_RECHECK_FAST = 1200;
	// An unfinished town errand is somebody's job until it is done.
	//
	// The 8 September audit traced the loop: the bot needs a merchant, the
	// route is deferred, the inactivity watchdog fires, the visit is thrown
	// away, and a second later the bot is casting an attack skill at whatever
	// stands nearby - with the need it came for still unmet. The watchdog may
	// cancel a stale route; it may not cancel the errand. These carry the
	// errand across the reset and keep the bot out of a fresh grind while it
	// waits for its retry.
	const DWORD PLAYERBOT_SERVICE_RETRY_MIN = 15000;
	const DWORD PLAYERBOT_SERVICE_RETRY_MAX = 40000;
	// How long a service may stay unfinished before it is given up and the
	// ordinary planner takes over again, so nothing can wedge for ever.
	const DWORD PLAYERBOT_SERVICE_GIVE_UP = 900000;
	// A town nobody stays in is a town nobody sees.
	//
	// Joan holds four hundred bots and its square holds a couple of dozen: a bot
	// comes in for an errand and leaves the moment it is done, so the market
	// ring the stalls stand on is empty of customers and of anything to look at.
	// A share of the bots that finish an errand in Joan now stay a while - which
	// is what a player does with a town, and what makes one look inhabited.
	// Bokjung is deliberately excluded: it is crowded already, and the whole
	// point of the M2 census work was to get level-40 bots out of it.
	// Every bot that finishes something in Joan, not half of them: the triggers
	// are rare enough on their own. An angler fishes for fifteen to forty
	// minutes and then rests for three quarters of an hour to two hours, so a
	// session ends about once a minute across the whole angler cohort - at half
	// that is three or four bots on the square at a time, which is not a market.
	const int PLAYERBOT_TOWN_LINGER_PERCENT = 100;
	// Three minutes of walking the counters, not four to ten of standing.
	//
	// The first version parked a bot on one spot of the square and left it
	// there, which filled Joan and made it look like a car park: a hundred
	// people motionless for up to ten minutes. What a town needs is movement,
	// and the market ring is what there is to walk between - so the bot strolls
	// from counter to counter instead, picking a new one every few seconds.
	const DWORD PLAYERBOT_TOWN_LINGER_MIN = 150000;
	const DWORD PLAYERBOT_TOWN_LINGER_MAX = 210000;
	// How long a bot looks at one counter before moving to the next. Long
	// enough to read as looking at something, short enough that the square is
	// never still.
	const DWORD PLAYERBOT_TOWN_BROWSE_MIN = 6000;
	const DWORD PLAYERBOT_TOWN_BROWSE_MAX = 14000;
	// And how long after that a counter it never reached is given up on.
	const DWORD PLAYERBOT_TOWN_BROWSE_GIVE_UP = 20000;
	const BYTE PLAYERBOT_PRECIOUS_REFINE = 6;
	// The lowest refine an ordinary spare may carry and still be worth a counter
	// slot. Below it nobody wants the thing: the market code buys medals,
	// level-30 weapons and big bonus rolls, and a person walking the market sees
	// a row of +1 armours and calls it junk - which it is.
	const BYTE PLAYERBOT_SHOP_MIN_GEAR_REFINE = 4;
	// And the level the piece is for. Of the 487 spares at +4 or +5 in this
	// world's bags, 272 are for level 29 or below - level-26 bodies, level-25
	// and lower weapons, level-17 boots, a handful of level-0 starter pieces -
	// each of them one tier behind what its owner is already wearing and worth
	// nothing to anybody who might walk past. The gear a player crosses a market
	// for starts at level 30.
	const int PLAYERBOT_SHOP_MIN_GEAR_LEVEL = 30;
	// Two slots have nothing at all between the starter tier and level 41:
	// shields and helmets go 0 -> 21 -> 41. The level-21 piece is therefore the
	// best anyone under 41 can wear, which is why it is worth real money on a
	// counter while a level-26 body armour - one tier below the level-34 a bot
	// of that age is already wearing - is not.
	const int PLAYERBOT_SHOP_TOP_SLOT_GEAR_LEVEL = 21;
	// How many lines a counter needs before it is worth a sign. One is not a
	// market stall: a player walks past, opens it, and finds a single spare.
	// Eighteen of the thirty-four stalls this world opened in the fourteen
	// minutes after a restart carried exactly one item.
	//
	// Two rather than three, measured rather than guessed. Three left eight
	// stalls standing where the old rule had left thirty-four - and the seven
	// with three lines or more were the same seven either way, so the extra
	// strictness bought nothing except a quieter market.
	const size_t PLAYERBOT_SHOP_MIN_ITEMS = 2;
	// Unless that one line is the reason somebody would cross the market: a
	// level-30 weapon, a horse medal, a big bonus roll, anything at +6 or better.
	// This is the score at which a single item carries a stall on its own.
	const int PLAYERBOT_SHOP_PRIZE_SCORE = 900;
	// A bonus line big enough to make an item worth selling whatever else it is.
	// A thousand health is roughly what a good armour of the level range adds, so
	// anything at or above it was rolled well rather than ordinarily.
	const int PLAYERBOT_VALUABLE_HP_BONUS = 1000;
	// What a bot asks for a spare. Invented rather than derived: the item tables
	// carry no price for a refined weapon, and these are meant to be affordable
	// to a bot that has been hunting for an hour rather than a jackpot.
	const DWORD PLAYERBOT_SHOP_PRICE_PLUS7 = 150000;
	const DWORD PLAYERBOT_SHOP_PRICE_PLUS8 = 400000;
	const DWORD PLAYERBOT_SHOP_PRICE_PLUS9 = 900000;
	// Refine materials go up at a small markup over the merchant price, so a bot
	// that needs one can buy it from a neighbour instead of farming for it.
	const DWORD PLAYERBOT_SHOP_MATERIAL_MARKUP = 3;
	// A soul stone has no shop price in the proto, so a counter asks this by
	// grade (+0 to +4) until the market has paid something for it.
	const DWORD PLAYERBOT_SHOP_PRICE_SOUL_STONE[5] = { 30000, 60000, 120000, 250000, 500000 };
	// Browsing someone else's stall.
	const DWORD PLAYERBOT_SHOPPING_INTERVAL_MIN = 120000;
	const DWORD PLAYERBOT_SHOPPING_INTERVAL_MAX = 300000;
	// The engine refuses a purchase beyond 2000, so stay inside that.
	const int PLAYERBOT_SHOPPING_RANGE = 1800;
	// Gold a bot will not spend on the market; potions and gear come first.
	const DWORD PLAYERBOT_SHOPPING_GOLD_FLOOR = 200000;
	// How many refine-material cells a bot carries as stock for its own counter.
	// They stack, so this is eight cells out of ninety however many pieces are
	// held - and eight is one full stall, which is as much as it can display.
	const size_t PLAYERBOT_MATERIAL_STOCK_SLOTS = 8;
	// Recipe ids are sparse - four hundred and seven of them scattered up to
	// 759 - and the manager offers no way to iterate, so this is where the walk
	// that collects their materials stops.
	const DWORD PLAYERBOT_REFINE_RECIPE_MAX_ID = 1000;
	// Going shopping, as opposed to buying whatever happens to be within twenty
	// metres. A bot that is short of something walks over to the stall ring and
	// reads the counters; this is how long it may spend on that before it goes
	// back to whatever it was doing. Long enough to cross a town, short enough
	// that a bot which cannot get there loses one errand and not its evening.
	const DWORD PLAYERBOT_MARKET_TRIP_TIMEOUT = 90000;
	// And how far away the stalls may be before it is not worth setting off:
	// the whole of the town, so that a bot which has just finished its errands
	// goes shopping while one that is out hunting stays where it is instead of
	// walking the timeout out and turning round empty-handed. Joan's ring stands
	// round the village guard, outside the town proper - the gate is 5750 from
	// him and the far corner of the service area 10900 - so nine thousand, which
	// was measured from the gate, excluded a bot standing at the blacksmith.
	const int PLAYERBOT_MARKET_TRIP_RANGE = 12000;
	// How often it re-reads the counters while it stands among them. The scan
	// walks every entity in the surrounding sectors, so it is not a per-tick job.
	const DWORD PLAYERBOT_MARKET_BROWSE_INTERVAL = 2000;
	// How close it walks up to the stall it has picked. The engine would let it
	// buy from twenty metres, but a market where the customers stand at the
	// counters looks like a market.
	const int PLAYERBOT_MARKET_STALL_APPROACH = 350;
	const int PLAYERBOT_GEAR_SHARE_RANGE = 2200;
	// Refining only runs while the bot is physically standing at the blacksmith.
	// A real player can click several times during one visit; a three-second cadence
	// permits several attempts without extending the absolute 6-24 s visit.
	const DWORD PLAYERBOT_REFINE_INTERVAL = 3000;
	// Bonus rerolling. Both verified against share/conf/item_proto.txt rather
	// than taken from the feature notes: 71084 is USE_CHANGE_ATTRIBUTE (rerolls
	// every line) and 71085 is USE_ADD_ATTRIBUTE (adds one). Neither can be
	// dropped, sold, traded or put in a stall, so a bot can only ever spend its
	// own gold on them.
	const DWORD PLAYERBOT_BONUS_CHANGE_VNUM = 71084;
	const DWORD PLAYERBOT_BONUS_ADD_VNUM = 71085;
	const DWORD PLAYERBOT_BONUS_STONE_PRICE = 25000;
	// Below this the gear itself is still changing every few levels, so paying to
	// polish its bonus lines is money the bot needs for the next weapon.
	const BYTE PLAYERBOT_BONUS_MIN_LEVEL = 30;
	// What the bot keeps: roughly one strong offensive line, or two decent ones.
	// --- Guilds and who a bot has got on with -------------------------------
	// Forty is what a player needs at the Village Guard, and the fee is what the
	// engine charges in CInputMain::GuildCreate - CreateGuild itself charges
	// nothing, so a caller that is not the packet handler has to pay it.
	const BYTE PLAYERBOT_GUILD_MIN_LEVEL = 40;
	const DWORD PLAYERBOT_GUILD_CREATE_FEE = 200000;
	// What a bot must still have afterwards. Founding a guild and then being
	// unable to buy a potion is not an ambition, it is a bug.
	const DWORD PLAYERBOT_GUILD_GOLD_RESERVE = 100000;
	// One eligible bot in twelve founds one. Any more and the world fills with
	// guilds of one member, which is the opposite of the point.
	const DWORD PLAYERBOT_GUILD_FOUNDER_SHARE = 12;
	const size_t PLAYERBOT_GUILD_NAMES_PER_EMPIRE = 2;
	// The lowest grade, which is what an ordinary member joins at.
	const int PLAYERBOT_GUILD_MEMBER_GRADE = 15;
	const int PLAYERBOT_GUILD_INVITE_RANGE = 3000;
	const DWORD PLAYERBOT_GUILD_INVITES_PER_PASS = 3;
	const DWORD PLAYERBOT_GUILD_CHECK_INTERVAL = 120000;

	// How many acquaintances a bot keeps, and how much any one of them can be
	// worth. Small on purpose: this is looked at on every party check, and a bot
	// that has hunted with two hundred others should remember the handful it got
	// on with rather than all of them.
	const size_t PLAYERBOT_FRIEND_SLOTS = 8;
	const int PLAYERBOT_FRIEND_MAX_AFFINITY = 100;
	const int PLAYERBOT_FRIEND_PARTY_POINTS = 4;
	const int PLAYERBOT_FRIEND_GIFT_POINTS = 10;
	const int PLAYERBOT_FRIEND_TRADE_POINTS = 6;

	const int PLAYERBOT_BONUS_KEEP_SCORE = 240;
	// MAX_NORM_ATTR_NUM in item_manager.h. Named here because the loop that fills
	// an item has to know it, and reading it from the engine header would tie a
	// tuning constant to a build detail.
	const int PLAYERBOT_BONUS_MAX_LINES = 5;
	// What the lines rolled on a piece add to what a stall asks for it.
	//
	// A counter wanted the same 150 000 for boots +7 carrying five bonus lines
	// as for boots +7 carrying none, which is not a market: everything that set
	// the price - the merchant's table, the sale memory, the step limiter - is
	// keyed by vnum and refine, and that pair cannot tell the two apart.
	//
	// Two things carry it. How many lines there are, with a step at four
	// because that is where a piece stops being a drop and starts being
	// somebody's work; and whether any of them is a roll a player stops on -
	// two thousand health, ten percent critical, immunity to stun. The cap is
	// there because the buyers are bots with an hour's hunting in their pocket.
	const int PLAYERBOT_SHOP_BONUS_PER_LINE = 25;
	const int PLAYERBOT_SHOP_BONUS_FOUR_PLUS = 100;
	const int PLAYERBOT_SHOP_BONUS_TOP_LINE = 80;
	const int PLAYERBOT_SHOP_BONUS_MAX_PERCENT = 600;
	// The rolls that finish an item for its slot. Thirty percent average damage
	// on a level-30 weapon, fifteen hundred health on armour or jewellery, five
	// percent critical on jewellery - the numbers a player stops rerolling at.
	const long PLAYERBOT_BONUS_KEEP_AVERAGE = 30;
	const long PLAYERBOT_BONUS_KEEP_HP = 1500;
	const long PLAYERBOT_BONUS_KEEP_CRIT = 5;
	const int PLAYERBOT_BONUS_STONES_PER_VISIT = 3;
	// Effectively once per town visit. A four-second cadence like the refiner's
	// would let one stop at the blacksmith burn a quarter of a million yang.
	const DWORD PLAYERBOT_BONUS_INTERVAL = 300000;
	// Gold the bot refuses to spend on bonuses; potions and gear come first.
	const DWORD PLAYERBOT_BONUS_GOLD_FLOOR = 120000;
	const DWORD PLAYERBOT_INACTIVITY_RESET_TIME = 90000;
	const DWORD PLAYERBOT_WANDER_INTERVAL = 8000;
	const DWORD PLAYERBOT_PARTY_CHECK_INTERVAL = 10000;
	const int PLAYERBOT_PARTY_DESIRED_MAX = 6;
	const int PLAYERBOT_PARTY_COHESION_RADIUS = 2800;
	const int PLAYERBOT_ARCHER_LURE_MIN_PARTY_MEMBERS = 5;
	// The Archer's luring course, as a party role rather than an extra shot.
	//
	// A course is: walk out, tag a pack with one ordinary arrow, read whether it
	// actually came, and bring what came back to the people who can kill it.
	// Every number below bounds a real failure - an Archer that gathers for
	// ever, one that runs further than monsters will follow, one that arrives at
	// a party which has moved on - and none of them is a measured optimum yet.
	//
	// How far a receiver may be from the gathering point and still count as
	// ready. Wider than this and the party is not standing together at all.
	const int PLAYERBOT_LURE_ANCHOR_RADIUS = 2200;
	// Close enough to the receivers to call the monsters delivered.
	const int PLAYERBOT_LURE_HANDOFF_RANGE = 450;
	// How far a course may take the Archer from the gathering point. Beyond it
	// the monsters break off and walk home, which is a sprint for nothing.
	const int PLAYERBOT_LURE_MAX_COURSE_RANGE = 4500;
	// A bow's reach is the one the ordinary attack uses, less a margin for the
	// step the bot takes while the shot is being sent. A second definition of
	// range is how a lure comes to fire from where a fight could not.
	const int PLAYERBOT_LURE_SHOT_RANGE = 760;
	const int PLAYERBOT_LURE_START_HP_PERCENT = 90;
	const int PLAYERBOT_LURE_BREAK_HP_PERCENT = 70;
	const int PLAYERBOT_LURE_MAX_HP_LOSS_PERCENT = 12;
	// Gathering has a deadline, and so has the walk back: a course that stopped
	// making progress must end as a course, not as a bot standing in a field.
	const DWORD PLAYERBOT_LURE_GATHER_TIME = 12000;
	const DWORD PLAYERBOT_LURE_RETURN_TIME = 25000;
	// After the arrow: long enough for a pack to turn round, short enough that
	// one that is not coming does not cost the whole course.
	const DWORD PLAYERBOT_LURE_CONFIRM_DELAY = 1200;
	const DWORD PLAYERBOT_LURE_CONFIRM_TIMEOUT = 4500;
	// How long the Archer stands with the party before the handover is judged.
	const DWORD PLAYERBOT_LURE_HANDOFF_WAIT = 7000;
	// A session that outlives this is abandoned whatever stage it is in, so no
	// party is ever held by a lurer that stopped answering.
	const DWORD PLAYERBOT_LURE_SESSION_TTL = 75000;
	const DWORD PLAYERBOT_LURE_COOLDOWN_MIN = 20000;
	const DWORD PLAYERBOT_LURE_COOLDOWN_MAX = 50000;
	// Groups and monsters per course: what a first course asks for, and the
	// ceiling a party earns by finishing courses without losing anybody.
	const int PLAYERBOT_LURE_FIRST_GROUPS = 2;
	const int PLAYERBOT_LURE_MAX_GROUPS = 4;
	const int PLAYERBOT_LURE_FIRST_BUDGET = 7;
	const int PLAYERBOT_LURE_MAX_BUDGET = 14;
	// Courses in a row without a death or a failed handover before the plan
	// grows by one group.
	const int PLAYERBOT_LURE_GROWTH_STREAK = 3;
	// What still counts as "the party is busy": a new course does not start
	// while this many delivered monsters are still on the receivers.
	const int PLAYERBOT_LURE_BUSY_MONSTERS = 3;
	// How often an Archer that cannot start a course asks again. The busy
	// count is a sector scan, and one per tick per Archer is a real cost
	// for an answer that does not change that fast.
	const DWORD PLAYERBOT_LURE_READY_RECHECK = 2000;
	// Where a pack worth pulling stands. Not the multi-pull's band, which looks
	// for whatever is at a solo bot's feet: a lure is for the packs the party
	// has not reached, so it starts beyond bow range and beyond the ground the
	// party is already fighting over, and it never takes a monster somebody
	// else has claimed.
	const int PLAYERBOT_LURE_MIN_PACK_DISTANCE = 1100;
	const int PLAYERBOT_LURE_MAX_PACK_DISTANCE = 3000;
	const int PLAYERBOT_LURE_ANCHOR_CLEARANCE = 900;
	const int PLAYERBOT_LURE_GROUP_SEPARATION = 700;
	// Above this over the Archer's own level a pack is not brought home, it is
	// an escort of things that kill the Archer on the way.
	const int PLAYERBOT_LURE_MAX_LEVEL_OVER = 3;

	const int PLAYERBOT_PARTY_CHALLENGE_MIN_MEMBERS = 3;
	const int PLAYERBOT_PARTY_CHALLENGE_RADIUS = 3000;
	const int PLAYERBOT_PARTY_READY_HP_PERCENT = 55;
	const int PLAYERBOT_PARTY_LEVEL_BONUS_PER_MEMBER = 5;
	// Strong solo builds sometimes play like an experienced Metin2 tank: wake a
	// few separate packs, bring them together and then clear them with the normal
	// melee splash. The limits deliberately favour survival over maximum XP.
	const DWORD PLAYERBOT_MULTI_PULL_MIN_COOLDOWN = 45000;
	const DWORD PLAYERBOT_MULTI_PULL_MAX_COOLDOWN = 90000;
	const DWORD PLAYERBOT_MULTI_PULL_TIMEOUT = 12000;
	const DWORD PLAYERBOT_MULTI_PULL_ACTION_DELAY = 500;
	const int PLAYERBOT_MULTI_PULL_MIN_HP_PERCENT = 70;
	const int PLAYERBOT_MULTI_PULL_START_HP_PERCENT = 90;
	const int PLAYERBOT_MULTI_PULL_MAX_HP_LOSS_PERCENT = 12;
	const int PLAYERBOT_MULTI_PULL_MAX_AGGRESSORS = 14;
	const int PLAYERBOT_MULTI_PULL_SEARCH_RANGE = 2200;
	const int PLAYERBOT_MULTI_PULL_GROUP_SEPARATION = 600;
	const DWORD PLAYERBOT_MERCHANT_WAIT_MIN = 3000;
	const DWORD PLAYERBOT_MERCHANT_WAIT_MAX = 15000;
	const DWORD PLAYERBOT_BLACKSMITH_WAIT_MIN = 6000;
	const DWORD PLAYERBOT_BLACKSMITH_WAIT_MAX = 24000;
	const DWORD PLAYERBOT_TRAINER_WAIT_MIN = 8000;
	const DWORD PLAYERBOT_TRAINER_WAIT_MAX = 18000;
	// The user-measured gate centre is 603,675 => (60300,169900).  Approach it
	// perpendicularly through two safe points instead of pathing diagonally into
	// either gate pillar.
	const long PLAYERBOT_TOWN_GATE_X = 60300;
	const long PLAYERBOT_TOWN_GATE_OUTSIDE_Y = 169400;
	const long PLAYERBOT_TOWN_GATE_INSIDE_Y = 170400;
	const long PLAYERBOT_MISC_MERCHANT_X = 59000;
	const long PLAYERBOT_MISC_MERCHANT_Y = 171300;
	const long PLAYERBOT_BLACKSMITH_X = 59400;
	const long PLAYERBOT_BLACKSMITH_Y = 171600;
	const long PLAYERBOT_WEAPON_MERCHANT_X = 67600;
	const long PLAYERBOT_WEAPON_MERCHANT_Y = 168600;
	const long PLAYERBOT_ARMOR_MERCHANT_X = 67600;
	const long PLAYERBOT_ARMOR_MERCHANT_Y = 164100;
	const long PLAYERBOT_BIOLOGIST_X = 89800;
	const long PLAYERBOT_BIOLOGIST_Y = 182100;
	const long PLAYERBOT_STABLE_BOY_X = 54900;
	const long PLAYERBOT_STABLE_BOY_Y = 163400;
	// Verified against locale/english/map/{index,Setting.txt,npc.txt,Town.txt} and
	// share/conf/mob_names.txt. Chunjo uses the empire-specific easy monkey
	// dungeon (map 25); map 107 is a different global dungeon whose coordinates
	// do not match the Bokjung portal target.
	// --- Earning the battle horse ------------------------------------------
	// The stable keeper's quest, with the three things this world cannot
	// support taken out - see playerbot_battle_horse.h for which and why.
	const BYTE PLAYERBOT_BATTLE_HORSE_MIN_LEVEL = 35;
	const BYTE PLAYERBOT_BATTLE_HORSE_FROM_HORSE_LEVEL = 10;
	const int PLAYERBOT_BATTLE_HORSE_KILLS = 100;
	const DWORD PLAYERBOT_BATTLE_HORSE_FEE = 500000;
	// The Black Wind band, which is what the desert on this server is stocked
	// with. The quest names 2105 and 2107; neither is spawned anywhere here.
	const DWORD PLAYERBOT_BATTLE_HORSE_MOB_FIRST = 401;
	const DWORD PLAYERBOT_BATTLE_HORSE_MOB_LAST = 404;
	// "Zdjecie Konia", taken away, and "Ksiega Opanc. Konia", handed over.
	const DWORD PLAYERBOT_HORSE_PHOTO_VNUM = 50051;
	const DWORD PLAYERBOT_BATTLE_HORSE_BOOK_VNUM = 50052;
	const char* PLAYERBOT_BATTLE_HORSE_KILLS_FLAG = "playerbot.battle_horse_kills";

	// The level at which a horse stops being transport and becomes a weapon.
	// Below it a bot always dismounts to fight; at or above it the target
	// decides.
	const BYTE PLAYERBOT_BATTLE_HORSE_LEVEL = 11;

	const long PLAYERBOT_MAP_CHUNJO_M1 = 21;
	const long PLAYERBOT_MAP_CHUNJO_M2 = 23;
	const long PLAYERBOT_MAP_CHUNJO_M3 = 24;
	const long PLAYERBOT_MAP_MONKEY_EASY = 25;
	const long PLAYERBOT_MAP_MONKEY_MEDIUM = 108;
	const long PLAYERBOT_MAP_MONKEY_HARD = 109;
	const long PLAYERBOT_M1_TO_M2_PORTAL_X = 87600;
	const long PLAYERBOT_M1_TO_M2_PORTAL_Y = 215100;
	const long PLAYERBOT_M2_ARRIVAL_X = 111800;
	const long PLAYERBOT_M2_ARRIVAL_Y = 216100;
	// How long a bot may stand at a portal without getting any closer to it
	// before travel gives the tick back. Twenty seconds is far longer than any
	// replan takes and far shorter than the hours four bots spent frozen at the
	// Bokjung teleporter.
	// How long a closed stall keeps taking its sign back, and how often. A stall
	// sign is cleared with PacketAround, which reaches whoever is in view at that
	// instant and nobody else - so a player who walks up a second later sees a
	// bot wearing a shop that no longer exists. Six seconds of repeats covers the
	// approach without turning into chatter: seventy closures in twenty-five
	// minutes across the whole world is what this is spread over.
	const DWORD PLAYERBOT_SHOP_SIGN_CLEAR_WINDOW = 6000;
	const DWORD PLAYERBOT_SHOP_SIGN_CLEAR_INTERVAL = 1500;

	// The material errand. A bot short of a refine material scans its map for
	// the nearest living monster whose DROP_ITEM is that material, and walks
	// towards it when none is within ordinary search range. The scan snapshots
	// every entity on the map, so it is rationed per bot; the range is how far a
	// bot will set off for a monster it cannot yet see.
	const DWORD PLAYERBOT_MATERIAL_SCAN_INTERVAL = 90000;
	// How many map snapshots one manager update may take between all the bots.
	// Same idea as the navigation's heavy-plan budget: the scan copies every
	// entity on the map, and the first version let every bot with a shortage do
	// it in the same tick after a restart - measured at 99.9% of a core.
	const int PLAYERBOT_MATERIAL_SCANS_PER_TICK = 6;
	const int PLAYERBOT_MATERIAL_HUNT_RANGE = 40000;
	// What a monster carrying a wanted material adds to its target score. Above
	// the sweet-spot level bonus of a fair fight and below the party-objective
	// one, so it wins among equals and loses to an errand somebody is waiting on.
	const int PLAYERBOT_WANTED_DROP_BONUS = 120000;

	// Stall prices from what the market actually paid. Fewer sales than this and
	// the counter asks its prior alone; the band keeps one wild purchase from
	// moving a price more than this many times either way from that prior.
	const size_t PLAYERBOT_SALE_MEMORY = 8;
	const size_t PLAYERBOT_SALE_MIN_SAMPLES = 2;
	const DWORD PLAYERBOT_SALE_PRICE_CAP_MULT = 4;
	const DWORD PLAYERBOT_SALE_PRICE_CAP_FLAT = 20000;
	// What a counter asks, scaled to what the buyers carry. The merchant's
	// price times three was the prior for everything, and the merchant pays
	// pennies: a material four hundred bots were short of stood at six hundred
	// yang on a market whose customers held a million each, which is not a
	// market, it is a giveaway. The median spendable wallet of the bots that
	// shop is measured once a minute with the ledger, and a unit asks this
	// share of it - a refine material fifteen per mille, a spare at +4 to +6
	// fifteen per refine step above +2, anything else ten - and a whole stack
	// never more than this percent, so the stack stays within reach of a bot
	// with the median wallet. The merchant's markup still applies where it is
	// the higher of the two.
	const DWORD PLAYERBOT_MARKET_MATERIAL_WALLET_PERMILLE = 15;
	const DWORD PLAYERBOT_MARKET_GEAR_WALLET_PERMILLE_PER_REFINE = 15;
	const DWORD PLAYERBOT_MARKET_OTHER_WALLET_PERMILLE = 10;
	const DWORD PLAYERBOT_MARKET_STACK_WALLET_PERCENT = 30;
	// What the merchant pays for a shellfish, and the yardstick for the wallet
	// floor below.
	//
	// The wallet says what the market can afford in total; on its own it cannot
	// tell two materials apart, and with a median wallet of 2.6 million every
	// material landed on the same ~38 000. That is why a shellfish the merchant
	// values at 3 000 and a white pearl he values at 12 000 stood on the
	// counters at the same price. The floor is now scaled by what the merchant
	// pays for this particular thing against this yardstick, in hundredths so a
	// material worth a fifth of a shellfish is not rounded to nothing, and only
	// upwards: nothing gets cheaper, and what is genuinely worth more costs
	// more. The cap keeps one expensive material from pricing itself out of
	// every buyer's reach.
	// Opening prices for the goods whose merchant value says nothing about what
	// they are worth here. A skill book costs the merchant a thousand yang
	// whichever skill it teaches, and a pearl's proto price was set for a world
	// with different wallets - the median bot here carries over a million and a
	// half. These are a starting calibration to be corrected by what actually
	// sells, not equilibrium prices: the market memory blends them away as
	// transactions accumulate.
	const DWORD PLAYERBOT_PRIOR_BOOK_AURA = 250000;        // Aura Miecza (4)
	const DWORD PLAYERBOT_PRIOR_BOOK_ENCHANTED_BLADE = 220000; // Czarowane Ostrze (63)
	const DWORD PLAYERBOT_PRIOR_BOOK_STRONG_BODY = 180000; // Silne Cialo (19)
	const DWORD PLAYERBOT_PRIOR_BOOK_KEY = 140000;         // inne kluczowe dla buildu
	const DWORD PLAYERBOT_PRIOR_BOOK_ORDINARY = 45000;
	const DWORD PLAYERBOT_PRIOR_PEARL_WHITE = 2000000;
	const DWORD PLAYERBOT_PRIOR_PEARL_BLUE = 3000000;
	const DWORD PLAYERBOT_PRIOR_PEARL_RED = 6000000;
	// A horse medal, and everything else the merchant will not buy.
	//
	// item_proto gives 50050 a shop price of zero, so GetPlayerBotNpcSellUnitPrice
	// returns nothing, the markup multiplies nothing, and the counter asked
	// max(1, 0) - one yang - for the one item in this world a bot cannot farm on
	// demand and needs twenty-one of. The Discord watched bots of fifteen to
	// twenty-five put them out at that price. Every chest and casket is in the
	// same position: 50011, 50192 and 50193 all carry a zero price.
	const DWORD PLAYERBOT_PRIOR_HORSE_MEDAL = 400000;
	const DWORD PLAYERBOT_PRIOR_NO_MERCHANT_PRICE = 30000;
	// Under this a number on a counter is not a price, it is an accident - and
	// the accident used to be permanent, see LimitPlayerBotAskStep.
	const DWORD PLAYERBOT_MARKET_ASK_FLOOR = 100;
	const DWORD PLAYERBOT_MARKET_WALLET_REFERENCE_PRICE = 600;
	const DWORD PLAYERBOT_MARKET_WALLET_WORTH_MIN_PERCENT = 100;
	const DWORD PLAYERBOT_MARKET_WALLET_WORTH_MAX_PERCENT = 800;
	// A piece off a counter has to beat what the bot wears, and any spare in
	// its bag for the slot, by this much. Two armours of one vnum and refine
	// differ by their bonus rolls, and "better than worn" bought the second
	// four seconds after the first; a sideways step is not worth the yang.
	const long long PLAYERBOT_MARKET_GEAR_MARGIN_PERCENT = 15;
	const DWORD PLAYERBOT_SALE_RECENT = 600000;
	const DWORD PLAYERBOT_SALE_STALE = 3600000;

	// The market ledger (playerbot_world_memory.h): what the counters hold of
	// a thing and how many bots are short of it, rebuilt this often, and how
	// often it is written to the log.
	const DWORD PLAYERBOT_MARKET_LEDGER_INTERVAL = 60000;
	const DWORD PLAYERBOT_MARKET_REPORT_INTERVAL = 600000;
	// A material goes on a counter only while the counters hold fewer units of
	// it than the bots short of it would buy, with a margin: five units a buyer
	// - one refine's worth and a spare - and half as much again on top. With
	// nobody short of it one stack may stand as a probe; more than that is
	// stock nobody asked for, and it stays in the bag.
	const DWORD PLAYERBOT_MARKET_SUPPLY_PER_BUYER = 5;
	const DWORD PLAYERBOT_MARKET_SUPPLY_MARGIN_PERCENT = 150;
	// Pricing. The prior counts as this many sales when the market's median is
	// blended in: after four sales the two weigh the same, after the full
	// memory of eight the market has two thirds of the say.
	const DWORD PLAYERBOT_MARKET_ANCHOR_N0 = 4;
	// The regulator: (demand + q0) / (supply + q0) to this power, kept within
	// these bounds. q0 is a typical stack, so one buyer against one counter is
	// not a shortage.
	const DWORD PLAYERBOT_MARKET_REGULATOR_Q0 = 5;
	const double PLAYERBOT_MARKET_REGULATOR_EXPONENT = 0.2;
	const double PLAYERBOT_MARKET_REGULATOR_MIN = 0.75;
	// The ceiling on the shortage premium. At 1.35 a material five hundred bots
	// were short of and no counter carried could ask a third more than one
	// nobody wanted, which is not a market answering a shortage.
	const double PLAYERBOT_MARKET_REGULATOR_MAX = 2.0;
	// How fast the market's ask for a thing may drift: this much per interval
	// since it last moved, up to this many intervals at once; and how long an
	// ask is remembered after the last counter carried the thing.
	const DWORD PLAYERBOT_MARKET_STEP_PERCENT = 5;
	const DWORD PLAYERBOT_MARKET_STEP_INTERVAL = 600000;
	const DWORD PLAYERBOT_MARKET_STEP_MAX_STEPS = 6;
	const DWORD PLAYERBOT_MARKET_ASK_STALE = 3600000;

	const DWORD PLAYERBOT_PORTAL_WALK_TIMEOUT = 20000;
	// What counts as having moved. Below this the bot is standing still, whether
	// the navigation deferred the plan, backed off, or quietly reported success.
	const int PLAYERBOT_PORTAL_WALK_PROGRESS = 150;

	const long PLAYERBOT_M2_TO_M1_PORTAL_X = 113000;
	const long PLAYERBOT_M2_TO_M1_PORTAL_Y = 213600;
	const long PLAYERBOT_M1_RETURN_X = 87600;
	const long PLAYERBOT_M1_RETURN_Y = 213100;
	const long PLAYERBOT_M2_MONKEY_PORTAL_X = 161700;
	const long PLAYERBOT_M2_MONKEY_PORTAL_Y = 211900;
	const long PLAYERBOT_MONKEY_EASY_ARRIVAL_X = 852000;
	const long PLAYERBOT_MONKEY_EASY_ARRIVAL_Y = 447700;
	const long PLAYERBOT_MONKEY_RETURN_PORTAL_X = 852000;
	const long PLAYERBOT_MONKEY_RETURN_PORTAL_Y = 447100;
	const long PLAYERBOT_M2_MONKEY_RETURN_X = 161100;
	const long PLAYERBOT_M2_MONKEY_RETURN_Y = 213000;
	// Bokjung has its own Stable Boy.  A medal expedition therefore ends here;
	// there is no artificial M2 -> M1 return trip.
	const long PLAYERBOT_M2_STABLE_BOY_X = 146900;
	const long PLAYERBOT_M2_STABLE_BOY_Y = 232400;
	// Real Bokjung NPC positions from metin2_map_b3/npc.txt. M2 therefore has
	// every routine service needed by a level 20-35 character; only profession
	// trainers and the Biologist still require a trip back to Joan (M1).
	const long PLAYERBOT_M2_WEAPON_MERCHANT_X = 147200;
	const long PLAYERBOT_M2_WEAPON_MERCHANT_Y = 243500;
	const long PLAYERBOT_M2_ARMOR_MERCHANT_X = 148500;
	const long PLAYERBOT_M2_ARMOR_MERCHANT_Y = 242200;
	const long PLAYERBOT_M2_MISC_MERCHANT_X = 141300;
	const long PLAYERBOT_M2_MISC_MERCHANT_Y = 240400;
	const long PLAYERBOT_M2_BLACKSMITH_X = 142000;
	const long PLAYERBOT_M2_BLACKSMITH_Y = 239200;
	// The M2 teleporter leads to Waryong (the infected-animal area commonly
	// called M3).  The return portal is NPC 10021 on map 24.
	const long PLAYERBOT_M2_TO_M3_TELEPORTER_X = 136900;
	const long PLAYERBOT_M2_TO_M3_TELEPORTER_Y = 240300;
	// Town.txt for metin2_map_guild_02 (map 24) points at local (427,92),
	// i.e. global (221900,9200).  The old (179500,1000) was copied from the
	// generic teleporter quest's empire table and lands in the unwalkable north-
	// west border of this map, leaving every arriving bot without a sectree.
	const long PLAYERBOT_M3_ARRIVAL_X = 221900;
	const long PLAYERBOT_M3_ARRIVAL_Y = 9200;
	const long PLAYERBOT_M3_RETURN_PORTAL_X = 222000;
	const long PLAYERBOT_M3_RETURN_PORTAL_Y = 8800;
	const long PLAYERBOT_M2_FROM_M3_X = 145500;
	const long PLAYERBOT_M2_FROM_M3_Y = 240000;
	// Maps opened past Bokjung.  Every coordinate here was read out of
	// locale/english/map/{index,Setting.txt,Town.txt,npc.txt}: the arrival points
	// are the Chunjo entries of Town.txt, the exits are the Teleporter (NPC 9012)
	// each map carries, and departure reuses Bokjung's own Teleporter.
	// Joan's own Teleporter (NPC 9012 in metin2_map_b1/npc.txt).
	const long PLAYERBOT_M1_TELEPORTER_X = 51900;
	const long PLAYERBOT_M1_TELEPORTER_Y = 153600;
	const long PLAYERBOT_MAP_DESERT = 63;
	const long PLAYERBOT_MAP_ORC_VALLEY = 64;
	// Not the map's own empire spawn point, which is where this used to be.
	// map_n_threeway is a three-empire border map and each corner is walled off:
	// from the Chunjo spawn a bot could reach 17 of the map's 532 spawn groups
	// and none of the twelve hunting hubs. Thirteen bots sat there at exactly the
	// entry level, never advancing, while planning routes that could not exist -
	// 7812 of 8259 "unreachable" lines in one session came from that corner.
	//
	// These two are hub coordinates from regen.txt, so they are standable, and
	// they are where the entrance opens onto the map's central island.
	//
	// The rest of the map used to be unreachable from here as well - 161 spawn
	// groups of 532 - because the navigation refused water and every one of the
	// twenty-two bridges in this delta is water with the block bit cleared. With
	// that fixed the whole map is one piece and all 532 groups are reachable, so
	// these coordinates are now simply the way in rather than the only island a
	// bot could use. Measured with tools/analyse_map_bridges.py.
	// Where a Chunjo character actually comes out, which is not where the bots
	// were being put. Orc Valley has four teleporter NPCs in its npc.txt - one
	// per empire at cells (1472,73), (131,746) and (640,1436), and a fourth in
	// the middle of the map at (767,792) that belongs to nobody. The arrival
	// used to be (712,767): the middle one. Every bot in the world therefore
	// materialised on the central island, and since wandering only runs on a
	// tick with nothing to fight - on a map with 4041 spawn points, never - that
	// is where they stayed. Amulet Orka has no spawn within 22000 units of that
	// spot; nor has the Esoteric Guide. Between them 493 bots were short of
	// those two materials while standing on the one island that does not drop
	// them.
	//
	// This is the engine's own answer: Town.txt is read as a general spawn point
	// followed by three empire pairs (SECTREE_MANAGER::LoadMapRegion), and the
	// second pair - empire 2, Chunjo - is cell (144,743). The desert was already
	// set this way, which is how the discrepancy showed up at all.
	const long PLAYERBOT_ORC_VALLEY_ARRIVAL_X = 270400;
	const long PLAYERBOT_ORC_VALLEY_ARRIVAL_Y = 739900;
	const long PLAYERBOT_DESERT_ARRIVAL_X = 221900;
	const long PLAYERBOT_DESERT_ARRIVAL_Y = 502700;
	// Leave through the Chunjo gate NPC beside the arrival point, not through the
	// Teleporter in the middle of the map. The death heatmap showed almost every
	// desert casualty within ~1500 units of that central Teleporter: a bot which
	// had already run out of potions was crossing 75k units of hostile ground to
	// reach it. These gates sit a few steps from where the bot arrived.
	// The bot walks to the exit before it is warped out, so this has to be in the
	// same region as the arrival - an exit on the far side of a wall would strand
	// every bot that ever entered.
	// npc.txt cell (131,746): teleporter 10009, the Chunjo gate, a few steps from
	// where Town.txt puts a Chunjo character down. The desert names its own gate
	// the same way - npc 10010 at cell (149,135) - and that pairing is the one
	// this file follows.
	const long PLAYERBOT_ORC_VALLEY_EXIT_X = 269100;
	const long PLAYERBOT_ORC_VALLEY_EXIT_Y = 740200;
	const long PLAYERBOT_DESERT_EXIT_X = 219700;
	const long PLAYERBOT_DESERT_EXIT_Y = 499900;

	// Two more frontier maps. Mount Sohan (metin2_map_c3) is Black Wind and
	// Wild soldiers at 26 to 36 with three Metin kinds at 25 to 35 - the same
	// band as the desert and the Fanatic islands, so from 26 a bot may go
	// there instead of waiting in Bokjung, and at 30-35 the three maps share
	// the population by pid. The Spider Dungeon (metin2_map_spiderdungeon,
	// "Kuahklo Dong") is knights of 50 to 58 and nothing else: from 48, half
	// of the population takes it instead of Orc Valley. Both used to sit on a
	// core the bots do not run on; m2-render-config moves them. Arrivals are
	// the Chunjo entries of Town.txt, exits the NPC beside each - Sohan's
	// Staruszek (20009) at cell (136,899), the dungeon's Yongbi teleporter
	// (10015) at (88,82) - so a bot never crosses the map to leave.
	const long PLAYERBOT_MAP_SOHAN = 61;
	const long PLAYERBOT_MAP_SPIDER_V1 = 104;
	// The Hwang Temple, metin2_map_milgyo, base (537600,51200), 102400 square.
	//
	// Read out of the server's own spawn files rather than off a wiki, with
	// tools/analyse_map_spawns.py: 5088 spawn points over nineteen kinds, levels
	// 52 to 61, the median at 56. The west half is the Elite Esoterics of 52-55
	// and is where the map is entered; the east half is the Tree Turtle Soldier
	// (57, 612 points), the Bogey (58) and the Esoteric Tormentor (56). Two boss
	// points every two hours roll among the Esoteric Summoner (54), the Frog
	// General (61) and the Yellow Tiger Spectre (75) - no boss hub here, because
	// a hub needs one named race and that roll has three.
	//
	// It has no Metin stones. What its stone.txt carries is sixteen ore veins -
	// ebony, crystal, amethyst, diamond, white gold, shells, heaven's tears -
	// which is what the wiki says too and is the one thing worth checking twice,
	// since every other frontier's stone.txt means stones.
	//
	// The reason to add it is not the level band, which Sohan and V1 already
	// cover from 48. It is the drops: the Frog Tongue (30060), the Frog Legs
	// (30061), the Leaf (30040), the Unknown Talisman+ (30079) and the Curse
	// Book+ (30080) appear in eighteen refine recipes and on no map this world
	// hosts for bots, and the market ledger has been asking for the first of
	// them with a supply of exactly zero. Nothing had to be taught about them:
	// GetPlayerBotRefineMaterialVnums reads the engine's own recipe table, so
	// they became goods the moment a bot could stand where they drop.
	const long PLAYERBOT_MAP_HWANG = 65;
	// The Spider Dungeon is entered from the desert, the way the game has it:
	// NPC 10016 "Kuahlo Dong" in the desert's bottom-right corner (cell 1425,
	// 1477 of metin2_map_n_desert_01) sends a character to (600, 4960) in V1,
	// and V1's exit NPC 10015 puts it back on the desert at (3467, 6329). A
	// bot used to warp from Bokjung's teleporter straight into V1 and straight
	// back, which no player can do. Now the trip is two legs with the desert
	// crossed on foot between them - and crossed, not farmed: the bot fights
	// nothing on the way except a stone worth its level, within this reach.
	const long PLAYERBOT_DESERT_V1_GATE_X = 347300;
	const long PLAYERBOT_DESERT_V1_GATE_Y = 634100;
	const long PLAYERBOT_DESERT_FROM_V1_X = 346700;
	const long PLAYERBOT_DESERT_FROM_V1_Y = 632900;
	const int PLAYERBOT_CROSSING_STONE_RANGE = 2500;
	// An episode of self-defence, so that "it hit me first" cannot become a
	// permanent licence to grind. The clock starts when the bot accepts an
	// attacker as a target and is not renewed by another hit from the same one;
	// the leash is measured from where the episode started. Both are tuning
	// values - measure before trusting them.
	const DWORD PLAYERBOT_DEFENCE_EPISODE_TIME = 10000;
	const int PLAYERBOT_DEFENCE_LEASH = 1000;
	// How far away a party member may be and still be worth defending.
	const int PLAYERBOT_PARTY_DEFENCE_RANGE = 1500;
	// An episode ends for good only when the fighting has actually stopped.
	// Without this a second attacker starts a fresh episode the moment the
	// first one's runs out, and two monsters taking turns are an endless
	// licence to grind - which is exactly what a bound is supposed to prevent.
	const DWORD PLAYERBOT_DEFENCE_QUIET_TIME = 15000;
	// A drop obeys the same level difference as experience: PERCENT_LVDELTA
	// multiplies both. Fifteen levels above a monster leaves one percent of the
	// chance, so "I need this material" must not justify farming something that
	// will effectively never yield it. Lower than the experience floor on
	// purpose - a material is worth more detours than experience is.
	const int PLAYERBOT_MATERIAL_MIN_DROP_PERCENT = 10;
	// The share of a monster's base experience left after the level difference,
	// below which an ordinary monster is not worth a bot's time. A starting
	// heuristic from the audit, not a measurement of experience per hour, and
	// not a rule of the game: quest, material and equipment errands are allowed
	// through it, and self-defence comes before it.
	const int PLAYERBOT_COMBAT_MIN_EXP_PERCENT = 20;
	// How often the monster a bot is already fighting is asked again whether
	// it is still worth fighting. Not every tick: the answer needs the bot's
	// material shortages, which cost a walk of the bag.
	const DWORD PLAYERBOT_COMBAT_RECHECK_INTERVAL = 3000;
	// How close to a world portal a bot walks before its map change is made
	// server-side. See MovePlayerBotToWorldPortal and patch 0008: the engine
	// no longer grabs a bot at the portal, so this only has to cover one
	// tick of running rather than the nine metres it used to.
	const int PLAYERBOT_PORTAL_SWITCH_DISTANCE = 200;
	const DWORD PLAYERBOT_CROSSING_STONE_CHECK_INTERVAL = 3000;
	// map_n_snowm_01, base (358400,153600), 153600 square; the town spawn from
	// its Town.txt (cell 768,768). 43 was the second Jinno village and carried
	// soldiers of 26-36; Sohan proper is the Infected of 49-58 in the south and
	// the ice creatures of 62-66 in the north.
	const long PLAYERBOT_SOHAN_ARRIVAL_X = 435200;
	const long PLAYERBOT_SOHAN_ARRIVAL_Y = 230400;
	const long PLAYERBOT_SOHAN_EXIT_X = 435200;
	const long PLAYERBOT_SOHAN_EXIT_Y = 230900;
	const long PLAYERBOT_SPIDER_ARRIVAL_X = 60000;
	const long PLAYERBOT_SPIDER_ARRIVAL_Y = 496600;
	const long PLAYERBOT_SPIDER_EXIT_X = 60000;
	const long PLAYERBOT_SPIDER_EXIT_Y = 494600;
	const BYTE PLAYERBOT_SOHAN_MIN_LEVEL = 48;
	const BYTE PLAYERBOT_SOHAN_MAX_LEVEL = 75;
	// The ice creatures of the north (62-66) are for bots that have outgrown
	// the Infected.
	const BYTE PLAYERBOT_SOHAN_ICE_MIN_LEVEL = 58;
	const BYTE PLAYERBOT_SPIDER_MIN_LEVEL = 48;
	// The arrival is the temple's own Town.txt cell (161,938); the exit is five
	// hundred units south of it. Both were checked against milgyo's server_attr
	// and stand on open ground - eighty-one of eighty-one free cells within two
	// hundred units, which is the radius the portal switch tests.
	const long PLAYERBOT_HWANG_ARRIVAL_X = 553700;
	const long PLAYERBOT_HWANG_ARRIVAL_Y = 145000;
	const long PLAYERBOT_HWANG_EXIT_X = 553700;
	const long PLAYERBOT_HWANG_EXIT_Y = 145500;
	// Fifty-two is where its weakest Elite Esoteric stands, and fifty-five where
	// the east half begins. Nothing below the first has any business here.
	const BYTE PLAYERBOT_HWANG_MIN_LEVEL = 52;
	const BYTE PLAYERBOT_HWANG_EAST_MIN_LEVEL = 55;

	// Where a frontier map is entered and where it is left, by map. Every
	// place that used to choose between the valley and the desert with a
	// ternary asks here instead, so a third and fourth map is a row, not a
	// sweep through the sources.
	bool GetPlayerBotFrontierArrival(long mapIndex, long& outX, long& outY)
	{
		switch (mapIndex)
		{
			case PLAYERBOT_MAP_ORC_VALLEY: outX = PLAYERBOT_ORC_VALLEY_ARRIVAL_X; outY = PLAYERBOT_ORC_VALLEY_ARRIVAL_Y; return true;
			case PLAYERBOT_MAP_DESERT: outX = PLAYERBOT_DESERT_ARRIVAL_X; outY = PLAYERBOT_DESERT_ARRIVAL_Y; return true;
			case PLAYERBOT_MAP_SOHAN: outX = PLAYERBOT_SOHAN_ARRIVAL_X; outY = PLAYERBOT_SOHAN_ARRIVAL_Y; return true;
			case PLAYERBOT_MAP_SPIDER_V1: outX = PLAYERBOT_SPIDER_ARRIVAL_X; outY = PLAYERBOT_SPIDER_ARRIVAL_Y; return true;
			case PLAYERBOT_MAP_HWANG: outX = PLAYERBOT_HWANG_ARRIVAL_X; outY = PLAYERBOT_HWANG_ARRIVAL_Y; return true;
			default: return false;
		}
	}

	bool GetPlayerBotFrontierExit(long mapIndex, long& outX, long& outY)
	{
		switch (mapIndex)
		{
			case PLAYERBOT_MAP_ORC_VALLEY: outX = PLAYERBOT_ORC_VALLEY_EXIT_X; outY = PLAYERBOT_ORC_VALLEY_EXIT_Y; return true;
			case PLAYERBOT_MAP_DESERT: outX = PLAYERBOT_DESERT_EXIT_X; outY = PLAYERBOT_DESERT_EXIT_Y; return true;
			case PLAYERBOT_MAP_SOHAN: outX = PLAYERBOT_SOHAN_EXIT_X; outY = PLAYERBOT_SOHAN_EXIT_Y; return true;
			case PLAYERBOT_MAP_SPIDER_V1: outX = PLAYERBOT_SPIDER_EXIT_X; outY = PLAYERBOT_SPIDER_EXIT_Y; return true;
			case PLAYERBOT_MAP_HWANG: outX = PLAYERBOT_HWANG_EXIT_X; outY = PLAYERBOT_HWANG_EXIT_Y; return true;
			default: return false;
		}
	}

	// The four maps a bot goes to for good once it has outgrown Bokjung. A
	// mission whose monster is not on one of these, while the bot is, will not
	// be hunted - the bot is not passing through.
	bool IsPlayerBotFrontierMapIndex(long mapIndex)
	{
		return mapIndex == PLAYERBOT_MAP_ORC_VALLEY || mapIndex == PLAYERBOT_MAP_DESERT ||
				mapIndex == PLAYERBOT_MAP_SOHAN || mapIndex == PLAYERBOT_MAP_SPIDER_V1 ||
				mapIndex == PLAYERBOT_MAP_HWANG;
	}

	const char* GetPlayerBotFrontierName(long mapIndex)
	{
		switch (mapIndex)
		{
			case PLAYERBOT_MAP_ORC_VALLEY: return "orc_valley";
			case PLAYERBOT_MAP_DESERT: return "desert";
			case PLAYERBOT_MAP_SOHAN: return "sohan";
			case PLAYERBOT_MAP_SPIDER_V1: return "spider_v1";
			case PLAYERBOT_MAP_HWANG: return "hwang";
			default: return "frontier";
		}
	}
	// Ordinary spawns are levels 18-25 in Orc Valley and 26-30 in the Desert, but
	// the Metins tell a different story: 40/45/50 in the Desert and 45/48/50 in
	// Orc Valley. A stone is only worth breaking between stoneLevel-9 and
	// stoneLevel+10, so Orc Valley starts paying at level 36 and not before -
	// which is why it belongs to the high band even though its monsters do not.
	// Bokjung keeps everyone up to 29.
	const BYTE PLAYERBOT_DESERT_MIN_LEVEL = 30;
	// The desert reaches as far as its own monsters do, which is much further
	// than thirty-six.
	//
	// Counted out of metin2_map_n_desert_01/regen.txt: 14026 spawn points, more
	// than any other map this world hosts and nearly twice Orc Valley's 8122.
	// The Scorpion King at 39 alone stands in 2234 places, the Desert Flying Eye
	// of 37 in 1242, the Poison Spider of 45 in 1548, the Scorpion Archer of 47
	// in 876. Capping the map at thirty-six meant nobody hunted on it past that
	// - the whole band from thirty-six to forty-seven went to Orc Valley - and
	// the richest map in the game was a corridor people walked across on their
	// way to the Spider Dungeon, which is exactly what the panel showed.
	const BYTE PLAYERBOT_DESERT_MAX_LEVEL = 47;
	// One distance decides both halves of this: how far away counts as somewhere
	// else, and how far a forced march goes before the bot may settle again.
	// Twelve thousand is the spacing Orc Valley's hunting hubs were generated
	// at, so it means exactly "one hub over".
	//
	// It has to be that large. An earlier draft reset the anchor whenever the
	// bot strayed thirty metres, which would have let a bot circling one corner
	// of the map for an hour keep claiming it had moved.
	const int PLAYERBOT_RELOCATE_DISTANCE = 12000;
	const DWORD PLAYERBOT_CAMP_TIMEOUT = 300000;
	// How close counts as arrived, and the give-up. A route that cannot be
	// walked must not suppress combat for the rest of the bot's life; three
	// minutes is long enough to cross this delta and short enough that a bot
	// stuck against a wall goes back to hunting.
	const int PLAYERBOT_RELOCATE_ARRIVED = 2000;
	const DWORD PLAYERBOT_RELOCATE_TIMEOUT = 180000;

	const BYTE PLAYERBOT_ORC_VALLEY_MIN_LEVEL = 36;
	const BYTE PLAYERBOT_ORC_VALLEY_MAX_LEVEL = 55;
	// Orc Valley is three maps stacked by level, and the band above treated it
	// as one. The outer islands hold the Esoteric Fanatic (35) and Arahan (38)
	// - the wiki's marked spots, and what a player farms there from the
	// thirties. The three Black Orc camps at (601,625), (774,923) and (933,639)
	// are level 46 S_KNIGHT, a party's work at 40; the central island's
	// Tormentors (49) carry the Curse Book and are a party's work at 45. A bot
	// of 30-35 goes to the Fanatic islands or to the desert by the parity of
	// its pid, so the desert keeps its Black Wind hunters and the horse trial.
	const BYTE PLAYERBOT_ORC_VALLEY_ESOTERIC_MIN_LEVEL = 30;
	const BYTE PLAYERBOT_ORC_VALLEY_ESOTERIC_MAX_LEVEL = 39;
	const BYTE PLAYERBOT_ORC_VALLEY_PARTY_MIN_LEVEL = 40;
	const BYTE PLAYERBOT_ORC_VALLEY_CENTRE_MIN_LEVEL = 45;
	// A camp of level-46 knights is farmed by eight, not six; the engine's own
	// ceiling is PARTY_MAX_MEMBER. Anyone of party level on this map may join
	// one, not only the ten percent party cohort - eight of that cohort at the
	// same level on the same island is a thing that never happens.
	const int PLAYERBOT_ORC_VALLEY_PARTY_MAX = 8;
	// A guild mate counts for twice a remembered friend when a party is being
	// put together, and a leader with a guild picks the camp by the guild's id,
	// so one guild ends up on one camp. That is what the map looked like on the
	// servers this world imitates.
	const int PLAYERBOT_GUILD_PARTY_POINTS = 8;
	// How far a follower may fall behind a leader who is walking to a new camp
	// before it gives the party up. The cohesion radius is for fighting as one
	// formation; a thirty-kilometre relocation with a deferred route in the
	// middle of it is not a reason to disband.
	const int PLAYERBOT_PARTY_STRAGGLER_RADIUS = 9000;

	// The population's memory of where the monsters are: a grid of cells this
	// wide per map, each remembering how many monsters were in reach when a bot
	// looked for something to hit there, and how often a fight started there.
	// Halved every ten minutes so a spot somebody cleared an hour ago is not
	// remembered as full. A hub with fewer looks than this is scored as an
	// average spot - four monsters in reach, which a rich camp beats easily
	// and a crowded one does not, so that unknown ground gets visited.
	const int PLAYERBOT_SPOT_CELL = 6400;
	const DWORD PLAYERBOT_SPOT_DECAY_INTERVAL = 600000;
	const DWORD PLAYERBOT_SPOT_MIN_SAMPLES = 12;
	const int PLAYERBOT_SPOT_UNKNOWN_PERMILLE = 4000;
	const int PLAYERBOT_SPOT_CROWD_RADIUS = 5000;
	// A hub this far away is worth half of one underfoot, and a hub once chosen
	// is kept for this long unless the bot is standing on it with nothing to
	// fight. The first version scored by share alone and re-chose on every
	// wander decision: bots crossed the valley for a slightly better camp,
	// then crossed back - 160 to 334 far plans a minute against 26 to 65
	// before, eight thousand deferrals, and the tick at 57 s of every 60.
	const int PLAYERBOT_HUB_HALF_WORTH_DISTANCE = 20000;
	const DWORD PLAYERBOT_HUB_STICK_TIME = 240000;
	// The Metin expedition. A quarter of the population are Metin hunters by
	// role and the rest broke a stone only when one stood in their way, which
	// is not what a player does: a player decides on an evening of stones and
	// roams the map for them. So every other bot rolls once an hour for a
	// stretch of exactly that - half an hour in which it plans, targets and
	// wanders like a hunter, then goes back to what it was. A quarter of the
	// rolls succeed, so at any moment about one grinder in eight is out for
	// stones; the METIN weight in the panel scales the chance. On the hunting
	// maps the expedition changes hub this often instead of every four
	// minutes, because a stone is found by covering ground.
	const DWORD PLAYERBOT_METIN_EXPEDITION_DURATION = 1800000;
	const DWORD PLAYERBOT_METIN_EXPEDITION_ROLL_INTERVAL = 3600000;
	const int PLAYERBOT_METIN_EXPEDITION_CHANCE_PERCENT = 25;
	const BYTE PLAYERBOT_METIN_EXPEDITION_MIN_LEVEL = 15;
	const DWORD PLAYERBOT_METIN_EXPEDITION_HUB_STICK = 90000;
	const DWORD PLAYERBOT_SPOT_REPORT_INTERVAL = 600000;

	// The Moonlight Treasure Chest and what comes out of it. A chest in the bag
	// is opened on the next pass; the boosters are drunk at the start of a
	// fight and refused by the engine while the last one still runs, so a
	// minute between attempts costs nothing and keeps the log readable.
	const DWORD PLAYERBOT_MOONLIGHT_CHEST_VNUM = 50011;
	// How many of one box a bot has to be holding before the surplus is goods
	// rather than its own supply. Suggested on the Discord: most of what drops
	// should still be opened - that is where the potions and the boosters come
	// from - but an unopened box is the one thing in this market a player can
	// gamble on, and there was never one on a counter.
	const DWORD PLAYERBOT_CHEST_STALL_MIN_STACK = 5;
	// The Forgetting Scroll (ITEM_SKILLFORGET): one level off a skill and the
	// point back. A skill that reached seventeen without turning Master is
	// left there rather than pushed on - every further point is a point the
	// bot never gets back - and a scroll from a counter buys another roll.
	// An armour piece more than this many levels below the bot is outgrown and
	// loses this much score per level past that, so a tier-appropriate piece
	// at a low refine displaces the starter piece at +6 and gets refined.
	const int PLAYERBOT_ARMOR_OUTGROWN_LEVELS = 20;
	// ...as a share of its defence figure per level past that, up to all of
	// it. It was a flat fifteen hundred a level, which took the bonus lines
	// with it: a level-18 plate rolled with fifteen hundred health lost at
	// fifty to a dragon armour with seven more defence and nothing else.
	const long long PLAYERBOT_ARMOR_OUTGROWN_PERCENT_PER_LEVEL = 5;
	const DWORD PLAYERBOT_SKILL_FORGET_SCROLL_VNUM = 70037;
	// Scrap keepers: the share of stall keepers (percent, from the panel) that
	// put their low refines on the counter instead of vendoring them, for the
	// player who wants cheap fodder to burn at the blacksmith. A keeper stops
	// hoarding scrap when its bag is down to this many free cells.
	const int PLAYERBOT_SCRAP_KEEP_FREE_CELLS = 20;
	const DWORD PLAYERBOT_SCRAP_PRICE_MULT = 2;
	// After a Metin stone breaks its drops lie in a ring round it, and the
	// pack it summoned is still on the bot. For this long the bot goes for its
	// own drops within this reach anyway - the way a player dashes for them -
	// rather than leaving them to whoever is not fighting.
	const DWORD PLAYERBOT_METIN_LOOT_DASH_TIME = 20000;
	const int PLAYERBOT_METIN_LOOT_DASH_RANGE = 1500;
	// An archer pulls too, but a bow is not a shield: one group, four attackers.
	const int PLAYERBOT_MULTI_PULL_ARCHER_MAX_AGGRESSORS = 4;
	const BYTE PLAYERBOT_SKILL_MASTER_TRY_LEVEL = 17;
	const DWORD PLAYERBOT_CHEST_INTERVAL = 8000;
	// How long a box the engine has refused is left alone. A refusal can be
	// a bag that happened to be full, so it is a wait rather than a verdict.
	const DWORD PLAYERBOT_CHEST_REFUSED_RETRY = 600000;
	const DWORD PLAYERBOT_BOOSTER_INTERVAL = 60000;
	// The chest's two boosters, and the two grilled fish that work the same
	// way: a Carp for twenty movement speed, a Rudd for ten dexterity, ten
	// minutes each (item_proto USE_ABILITY_UP).
	const DWORD PLAYERBOT_BOOSTER_VNUMS[] = { 71044, 71045, 27866, 27873 };
	// Fishing, the rest of the chain. A dead fish is grilled on a campfire:
	// the Dried Wood (27600, from the Fisherman) burns for forty seconds as a
	// campfire mob (12000) and takes fish handed to it - alive or dead - and
	// hands back the grilled kind. The grilled potions (Crucian 180, Big
	// Crucian 350, Tenchi 230 at once; Mandarin Fish 180 SP, Catfish 500 SP)
	// go into the potion lists.
	const DWORD PLAYERBOT_CAMPFIRE_VNUM = 27600;
	const DWORD PLAYERBOT_CAMPFIRE_MOB_VNUM = 12000;
	const DWORD PLAYERBOT_BAKE_WINDOW = 35000;
	// The race histogram a bot keeps of what it has been fighting: five race
	// flags (animal, undead, devil, orc, mystic), halved every ten minutes,
	// and trusted over the map's aggregate once it holds this many.
	const int PLAYERBOT_RACE_HISTOGRAM_SLOTS = 5;
	const DWORD PLAYERBOT_RACE_HISTOGRAM_DECAY = 600000;
	const DWORD PLAYERBOT_RACE_HISTOGRAM_MIN_SAMPLES = 20;
	// A hub where a wanted material has been seen to drop is worth half as
	// much again to a bot short of it; a cell with this many fights and no
	// drop of it has told the bot all it needs to know.
	const int PLAYERBOT_SPOT_MATERIAL_BONUS_PERCENT = 50;
	const DWORD PLAYERBOT_SPOT_MATERIAL_BARREN_FIGHTS = 200;
	const int PLAYERBOT_BAKE_MIN_FISH = 30;
	const int PLAYERBOT_BAKE_RANGE = 700;
	const DWORD PLAYERBOT_GRILLED_FISH_FIRST_VNUM = 27863;
	const DWORD PLAYERBOT_GRILLED_FISH_LAST_VNUM = 27876;
	// What a shellfish holds, from the engine's own table (char_item.cpp,
	// case 27987): half a Stone Piece, thirty percent nothing, then a white,
	// a blue or a blood pearl. Thousandths. Once the population has opened
	// enough of them, its own count replaces the table.
	const DWORD PLAYERBOT_STONE_PIECE_VNUM = 27990;
	// What a shell actually holds, read out of the engine rather than guessed.
	//
	// char_item.cpp case 27987 rolls 1..100: at or under 50 a Stone Piece, and
	// the rest goes through one of two tables chosen by g_iUseLocale -
	// {80,90,97} when it is false and {95,97,99} when it is true. This world's
	// common.locale says "english", and __LocaleService_Init_English sets
	// g_iUseLocale = TRUE, so the second table is the live one: 45% nothing,
	// 2% white, 2% blue, 1% blood. The numbers here said 10/7/3 - the other
	// table - which made opening a shell look four times more rewarding than it
	// is, and every decision built on that estimate was wrong in the same
	// direction. A server that changes locale changes this; check the flag
	// before trusting the constants.
	const int PLAYERBOT_SHELLFISH_STONE_PERMILLE = 500;
	const int PLAYERBOT_SHELLFISH_WHITE_PERMILLE = 20;
	const int PLAYERBOT_SHELLFISH_BLUE_PERMILLE = 20;
	const int PLAYERBOT_SHELLFISH_RED_PERMILLE = 10;
	const DWORD PLAYERBOT_SHELLFISH_LEARN_SAMPLES = 50;
	// The Blessing Scroll (CHUKBOK_SCROLL to the engine): a refine that fails
	// under it drops the item one level instead of destroying it, at the
	// table's own odds. The blacksmith without one removes the item on every
	// failure - 1584 pieces in one afternoon. Scrolls come from the chest and
	// are scarce, so they are spent where a failure costs most: from +6 up.
	const DWORD PLAYERBOT_BLESSING_SCROLL_VNUM = 25040;
	const BYTE PLAYERBOT_SCROLL_REFINE_MIN_PLUS = 6;
	const DWORD PLAYERBOT_SCROLL_REFINE_INTERVAL = 45000;
	// Neither map sells anything, so a visit is bounded and ends in Bokjung.
	const DWORD PLAYERBOT_FRONTIER_MAX_VISIT_TIME = 2400000;
	// ...but it also has to start. Without a floor the bot re-evaluated its needs
	// on the very first tick after arriving, decided it wanted a shop, and turned
	// straight back around: 271 arrivals on the Desert produced 269 departures,
	// several of them within six seconds, and both maps looked empty because
	// every bot on them was mid-bounce.
	const DWORD PLAYERBOT_FRONTIER_MIN_VISIT_TIME = 120000;
	// Bokjung's market strip. Anchored on the coordinate the return-from-M3 leg
	// already uses, so it is known walkable; each keeper gets a stable offset so
	// the stalls line up instead of stacking on one pixel.
	const long PLAYERBOT_M2_MARKET_X = 145500;
	const long PLAYERBOT_M2_MARKET_Y = 240000;
	const int PLAYERBOT_MARKET_SPREAD = 300;
	// Town legs stop when they are close enough, not on the exact pixel. 220 was
	// tight enough that keepers kept walking around their pitch without ever
	// counting as arrived.
	const int PLAYERBOT_MARKET_ARRIVE = 450;
	// Joan's stall circle, around the village guard. The guard is NPC 11002 and
	// map data puts him in cell (633,640); metin2_map_b1's BasePosition is
	// (0,102400) and world = base + cell*100, which is the same arithmetic that
	// gives PLAYERBOT_M1_TELEPORTER its (51900,153600) from cell (519,512). He
	// stands alone - no other NPC within forty cells - so a ring of stalls round
	// him blocks nobody.
	// Cell (634,639) of metin2_map_b1, whose BasePosition is (0,102400): world =
	// base + cell*100.
	const long PLAYERBOT_M1_GUARD_X = 63400;
	const long PLAYERBOT_M1_GUARD_Y = 166300;
	// How far from the middle a stall may stand. A hundred units is a metre here,
	// so this is a market four to seventeen metres across instead of the
	// two-and-a-half-metre huddle it was.
	//
	// It cannot be wider. shop_manager.cpp refuses a purchase beyond 2000 units,
	// so a buyer reaches twenty metres and no further, and PLAYERBOT_SHOPPING_RANGE
	// is 1800 for the same reason. Spread over forty metres the market looked
	// roomy and stopped working: stalls at opposite ends were out of each other's
	// reach and nobody bought anything at all. The ceiling belongs to the engine,
	// not to us.
	// How many counters Bokjung's ring may hold before a keeper takes its goods
	// to Joan instead. Bokjung is where the bots are, so left alone every stall
	// opens there and the other town's market never happens; a cap is what
	// pushes the overflow somewhere it is worth walking to.
	const int PLAYERBOT_SHOP_M2_MAX_STALLS = 7;
	// How long Bokjung's counters are worth a look after Joan had nothing. Long
	// enough that a bot which crossed for nothing is not sent straight back,
	// short enough that Joan stays the first stop.
	const DWORD PLAYERBOT_MARKET_M2_FALLBACK = 600000;
	// Counters standing in Bokjung right now. Recounted by the market ledger
	// once a minute and incremented the moment one opens, so a burst of
	// keepers in the same minute cannot walk past the cap together. A stale
	// count can only be too high, which errs towards sending a keeper to Joan.
	int s_iPlayerBotStallsInM2 = 0;
	const int PLAYERBOT_SHOP_RING_MIN = 400;
	const int PLAYERBOT_SHOP_RING_RADIUS = 1700;
	// The shop bundle (item 50200) carries LIMIT_NONE in item_proto, so the game
	// itself sells stalls from level one. The floor of twenty was ours, and it is
	// why Joan had no market: five of the five hundred bots standing there were
	// above it, while Bokjung held a hundred and twenty.
	const BYTE PLAYERBOT_SHOP_MIN_LEVEL = 1;
	// How many items go on the counter. The engine allows forty
	// (SHOP_HOST_ITEM_MAX_NUM); this is about what a bot plausibly has spare, and
	// every slot costs an inventory scan when a buyer reads the offer.
	const BYTE PLAYERBOT_SHOP_MAX_ITEMS = 8;
	// A trader's counter. It is the bot's occupation rather than a sideline, so it
	// carries far more and keeps the stall up for a proper shift.
	const BYTE PLAYERBOT_SHOP_MERCHANT_ITEMS = 20;
	const DWORD PLAYERBOT_SHOP_MERCHANT_MIN_DURATION = 600000;   // 10 min
	const DWORD PLAYERBOT_SHOP_MERCHANT_MAX_DURATION = 1200000;  // 20 min
	// One bot in six that has no other calling trades for a living. Enough to give
	// each market a few permanent faces without emptying the hunting grounds.
	const DWORD PLAYERBOT_MERCHANT_SHARE = 6;
	// One in this many of the ordinary adventurers becomes a dropper - an M3,
	// M2 or medal one, drawn evenly. The Metin dropper is a third of the metin
	// hunter role instead, because hunting stones is that role's whole day.
	const DWORD PLAYERBOT_DROPPER_SHARE = 8;
	// A dropper opens its stall on a third of its town visits, against one in
	// ten for an adventurer and every visit for a merchant: it hunts for a
	// living and sells what the hunt brought, not the other way round.
	const int PLAYERBOT_DROPPER_SHOP_ROLL = 333;
	// A bot with every slot filled and nothing on its ladder left to buy has
	// spares and no use for the yang; three in ten of those keep a stall
	// against one in ten of everyone else.
	const int PLAYERBOT_FULL_GEAR_SHOP_ROLL = 300;
	// A stall stands for a while and then the bot goes back to playing. An hour
	// was long enough that a player watching the market never saw one come down,
	// which read as "the shops never close" even before the tick-ordering bug
	// that genuinely kept some of them open.
	const DWORD PLAYERBOT_SHOP_MIN_DURATION = 600000;    // 10 min
	const DWORD PLAYERBOT_SHOP_MAX_DURATION = 1500000;   // 25 min
	// What a bot pays itself for the stall it sets up.
	const DWORD PLAYERBOT_SHOP_BUNDLE_PRICE = 2000;
	const DWORD PLAYERBOT_SHOP_REST_MIN = 1800000;
	const DWORD PLAYERBOT_SHOP_REST_MAX = 5400000;
	const DWORD PLAYERBOT_HORSE_MEDAL_VNUM = 50050;
	const BYTE PLAYERBOT_HORSE_REQUIRED_LEVEL = 25;
	const char* PLAYERBOT_HORSE_MEDALS_FLAG = "playerbot.horse_medals_delivered";
	const char* PLAYERBOT_HORSE_MEDALS_LOOTED_FLAG = "playerbot.horse_medals_looted";
	const char* PLAYERBOT_HORSE_LAST_LOOT_MAP_FLAG = "playerbot.horse_last_loot_map";
	const char* PLAYERBOT_HORSE_LAST_LOOT_TIME_FLAG = "playerbot.horse_last_loot_time";
	const char* PLAYERBOT_HORSE_LAST_DELIVERY_TIME_FLAG = "playerbot.horse_last_delivery_time";
	// Fishing, matched to what the r40250 engine actually does:  the rod occupies
	// WEAR_WEAPON, the bait lives in the rod's socket 2 rather than in the pouch,
	// a cast bites after 10-40 s and then leaves a 6 s window to pull.
	const DWORD PLAYERBOT_FISHING_ROD_VNUM = 27400;   // Wedka+1
	const DWORD PLAYERBOT_FISHING_BAIT_VNUM = 27801;  // Robak
	const DWORD PLAYERBOT_SHELLFISH_VNUM = 27987;     // Malz
	// What a shell can hold: Biala / Niebieska / Krwawa Perla.
	const DWORD PLAYERBOT_PEARL_FIRST_VNUM = 27992;
	const DWORD PLAYERBOT_PEARL_LAST_VNUM = 27994;
	// How many shells a bot keeps whole. Prying one open is a bet against the
	// shell's own worth: twenty-six recipes consume a shellfish as it is, and
	// that is what it sells for. So the first few are never gambled with and
	// only the surplus is opened.
	const int PLAYERBOT_SHELLFISH_KEEP = 4;
	// Hair dye, the engine's own range: 70201 washes the colour out, 70202 to
	// 70206 set PART_HAIR to vnum-70201. char_item.cpp takes it straight from
	// UseItem with no client involved, and the colour is permanent - which is
	// the point of letting a bot use one.
	const DWORD PLAYERBOT_HAIR_DYE_FIRST_VNUM = 70201;
	const DWORD PLAYERBOT_HAIR_DYE_LAST_VNUM = 70206;
	// The item-shop dyes. The engine's switch does not answer for these, so a
	// bot never tries to use one: they are goods and nothing else.
	const DWORD PLAYERBOT_HAIR_DYE_SHOP_FIRST_VNUM = 71075;
	const DWORD PLAYERBOT_HAIR_DYE_SHOP_LAST_VNUM = 71079;

	// A hair dye of either kind - one a bot could use, or one it can only sell.
	// Both are worth money to somebody and neither is scrap.
	bool IsPlayerBotHairDye(DWORD vnum)
	{
		return (vnum >= PLAYERBOT_HAIR_DYE_FIRST_VNUM &&
					vnum <= PLAYERBOT_HAIR_DYE_LAST_VNUM) ||
				(vnum >= PLAYERBOT_HAIR_DYE_SHOP_FIRST_VNUM &&
					vnum <= PLAYERBOT_HAIR_DYE_SHOP_LAST_VNUM);
	}
	const int PLAYERBOT_FISHING_BAIT_BUNDLE = 20;
	const int PLAYERBOT_FISHING_BAIT_RESTOCK = 5;
	// The Rybak (9009) himself, from map_b1 npc.txt cell (675,539) against
	// BasePosition (0,102400). Tackle is bought here.
	const long PLAYERBOT_FISHERMAN_X = 67500;
	const long PLAYERBOT_FISHERMAN_Y = 156300;
	// The bank the bots actually fish from, a short walk downstream of him. The
	// shoreline here runs north-south with the river to the east, so anglers queue
	// along Y and all face +X. This band -- x 67250..67450, y 156900..157350 --
	// was read out of map_b1's server_attr: every cell in it is standable, and
	// open water starts a little east of it (tools/decode_server_attr.py).
	// Where the anglers stand, measured along the river rather than laid out on
	// a grid.
	//
	// A rectangle was the first attempt and it put half of them on the grass:
	// this river bends, its bank running from x 69900 in the north through
	// 67200 in the middle to 67800 in the south, so any rectangle wide enough
	// to hold fifty people reaches inland to where there is no water at all.
	// A photograph from the Discord showed exactly that - a crowd on the lawn
	// with rods, several metres from the bank.
	//
	// So the stands are a table, the way hunting hubs are a table. Every
	// candidate cell along the river was taken out of map_b1's server_attr,
	// sorted by its distance to open water, and kept only if no already-kept
	// stand was within 150 units: 162 places, each one standable, each
	// within 350 units of water, and none closer to another than a metre and a
	// half. Against a live angler population near sixty that is a bank with
	// room to spare, and the first ones taken are the ones at the water's edge.
	//
	// Every coordinate sits on a navigation cell centre - base + n*50 + 25 -
	// because that is the point CPlayerBotNavigation samples when it decides
	// whether a cell may be stood on. Stands generated on the multiples of
	// fifty instead sat on cell corners, so the grid judged them by a
	// neighbouring sample: some were called blocked, the walk snapped them to
	// the nearest cell it did accept, and two anglers ended up eight units
	// apart on the same one.
	//
	// The last two numbers are a point in the water in front of the stand. A
	// bot used to be turned to face due east, which is right for a north-south
	// bank and wrong everywhere this river turns.
	struct TPlayerBotFishingStandPoint { long x; long y; long waterX; long waterY; };
	const TPlayerBotFishingStandPoint PLAYERBOT_FISHING_STANDS[] = {
		{  69775, 155625,  70825, 156675 }, {  69575, 155675,  70625, 156725 },
		{  70175, 155675,  70625, 156125 }, {  70375, 155675,  70525, 155825 },
		{  69925, 155725,  70525, 156325 }, {  69275, 155775,  70325, 156825 },
		{  69425, 155775,  70475, 156825 }, {  69725, 155825,  70325, 156425 },
		{  70275, 155825,  70425, 155825 }, {  68775, 155875,  69825, 156925 },
		{  68925, 155875,  69975, 156925 }, {  69075, 155875,  70125, 156925 },
		{  70075, 155875,  70225, 156025 }, {  69425, 155925,  70025, 156525 },
		{  69575, 155925,  70175, 156525 }, {  68575, 155975,  69625, 157025 },
		{  69875, 155975,  70025, 156125 }, {  70225, 155975,  70375, 155975 },
		{  70375, 155975,  70525, 155975 }, {  68925, 156025,  69525, 156625 },
		{  69075, 156025,  69675, 156625 }, {  69225, 156025,  69225, 156625 },
		{  68275, 156075,  69325, 157125 }, {  68425, 156075,  69475, 157125 },
		{  69575, 156075,  69725, 156225 }, {  69725, 156075,  69725, 156225 },
		{  68725, 156125,  69325, 156725 }, {  68125, 156175,  69175, 157225 },
		{  69075, 156175,  69225, 156325 }, {  69225, 156175,  69225, 156325 },
		{  69375, 156175,  69375, 156325 }, {  68425, 156225,  69025, 156825 },
		{  68575, 156225,  69175, 156825 }, {  69525, 156225,  69675, 156225 },
		{  67975, 156275,  68725, 157025 }, {  68875, 156275,  69025, 156425 },
		{  68225, 156325,  68225, 156925 }, {  69025, 156325,  69175, 156325 },
		{  69175, 156325,  69325, 156325 }, {  69325, 156325,  69475, 156325 },
		{  67575, 156375,  68625, 157425 }, {  67775, 156375,  68525, 157125 },
		{  68575, 156375,  68725, 156525 }, {  68725, 156375,  68725, 156525 },
		{  69475, 156375,  69625, 156375 }, {  68875, 156425,  69025, 156425 },
		{  68325, 156475,  68325, 156625 }, {  69025, 156475,  69175, 156475 },
		{  69175, 156475,  69325, 156475 }, {  67525, 156525,  68425, 157425 },
		{  67675, 156525,  68425, 157275 }, {  68475, 156525,  68625, 156525 },
		{  68625, 156525,  68775, 156525 }, {  68775, 156575,  68925, 156575 },
		{  67325, 156625,  68225, 157525 }, {  67175, 156775,  68225, 157825 },
		{  67325, 156775,  68225, 157675 }, {  67475, 156775,  67925, 157225 },
		{  67175, 156925,  68225, 157975 }, {  67325, 156925,  67925, 157525 },
		{  67575, 156925,  67725, 156925 }, {  67075, 157075,  68125, 158125 },
		{  67325, 157075,  67925, 157675 }, {  67475, 157075,  67625, 157225 },
		{  67075, 157225,  68125, 158275 }, {  67225, 157225,  67825, 157825 },
		{  67475, 157225,  67625, 157225 }, {  67225, 157375,  67825, 157975 },
		{  67375, 157375,  67525, 157525 }, {  67075, 157425,  68125, 157425 },
		{  67225, 157525,  67825, 157525 }, {  67375, 157525,  67525, 157525 },
		{  67075, 157575,  68125, 157575 }, {  67225, 157675,  67825, 157675 },
		{  67375, 157675,  67525, 157675 }, {  67125, 157825,  68025, 156925 },
		{  67275, 157825,  67725, 157375 }, {  67475, 157925,  67625, 157925 },
		{  67125, 157975,  68025, 157075 }, {  67325, 157975,  67925, 157975 },
		{  67475, 158075,  67625, 158075 }, {  67175, 158125,  68225, 158125 },
		{  67325, 158125,  67925, 158125 }, {  67475, 158225,  67625, 158225 },
		{  67625, 158225,  67775, 158225 }, {  67775, 158225,  67925, 158225 },
		{  68725, 158225,  68875, 158225 }, {  68875, 158225,  69025, 158225 },
		{  69025, 158225,  69175, 158225 }, {  69175, 158225,  69025, 158225 },
		{  69325, 158225,  69325, 158075 }, {  69475, 158225,  69475, 158075 },
		{  69625, 158225,  69625, 158075 }, {  69775, 158225,  69775, 158075 },
		{  69925, 158225,  69925, 158075 }, {  70075, 158225,  70225, 158225 },
		{  67275, 158275,  68025, 158275 }, {  67925, 158325,  68075, 158325 },
		{  68075, 158325,  68225, 158325 }, {  68225, 158325,  68375, 158325 },
		{  68375, 158325,  68525, 158325 }, {  68525, 158325,  68675, 158325 },
		{  70225, 158325,  70225, 158175 }, {  67425, 158375,  67725, 158075 },
		{  67675, 158375,  67825, 158375 }, {  68675, 158375,  68825, 158375 },
		{  68825, 158375,  68975, 158375 }, {  68975, 158375,  68675, 158375 },
		{  69125, 158375,  69125, 158075 }, {  69275, 158375,  68975, 158075 },
		{  69425, 158375,  69425, 157775 }, {  69575, 158375,  69575, 157775 },
		{  69725, 158375,  69725, 157775 }, {  69925, 158375,  70225, 158075 },
		{  70075, 158375,  70075, 158075 }, {  67275, 158425,  68025, 157675 },
		{  70375, 158425,  70375, 158275 }, {  67825, 158475,  67975, 158475 },
		{  67975, 158475,  67825, 158475 }, {  68125, 158475,  68125, 158175 },
		{  68275, 158475,  68275, 158175 }, {  68425, 158475,  68425, 158175 },
		{  70225, 158475,  70525, 158175 }, {  67425, 158525,  68175, 157775 },
		{  67575, 158525,  68025, 158075 }, {  68575, 158525,  68575, 158075 },
		{  68725, 158525,  68725, 158075 }, {  68875, 158525,  68875, 158075 },
		{  69025, 158525,  68575, 158075 }, {  69175, 158525,  69175, 157775 },
		{  69325, 158525,  68575, 157775 }, {  69475, 158525,  68575, 157625 },
		{  69625, 158525,  69625, 157475 }, {  69775, 158525,  70525, 157775 },
		{  69925, 158525,  70675, 157775 }, {  70075, 158525,  70075, 157775 },
		{  67225, 158575,  68125, 157675 }, {  70375, 158575,  70825, 158125 },
		{  67725, 158625,  68175, 158175 }, {  67875, 158625,  67875, 158175 },
		{  68025, 158625,  67575, 158175 }, {  68175, 158625,  67575, 158025 },
		{  68325, 158625,  68325, 157875 }, {  70225, 158625,  70975, 157875 },
		{  67425, 158675,  68325, 157775 }, {  67575, 158675,  68325, 157925 },
		{  68475, 158675,  68475, 157775 }, {  68625, 158675,  68625, 157775 },
		{  68775, 158675,  68775, 157775 }, {  68925, 158675,  68025, 157775 },
		{  69075, 158675,  68175, 157775 }, {  69225, 158675,  68175, 157625 },
		{  70025, 158675,  70925, 157775 }, {  70375, 158725,  71125, 157975 },
		{  67825, 158775,  67825, 157875 }, {  67975, 158775,  67975, 157875 },
		{  68125, 158775,  67225, 157875 }, {  68275, 158775,  67375, 157875 },
		{  70225, 158775,  71125, 157875 }, {  67475, 158825,  68525, 157775 },
		{  67625, 158825,  68675, 157775 }, {  70375, 158875,  71425, 157825 }
	};
	const size_t PLAYERBOT_FISHING_STAND_COUNT =
			sizeof(PLAYERBOT_FISHING_STANDS) / sizeof(PLAYERBOT_FISHING_STANDS[0]);
	// The middle of that table and a radius that covers all of it. Only the
	// status line uses these, for the one question it asks about an angler: is
	// it at the river yet, or still on its way. The stands themselves span
	// x 67050..70400 and y 155600..158850, so nothing smaller reaches the ends.
	const long PLAYERBOT_FISHING_BANK_X = 68725;
	const long PLAYERBOT_FISHING_BANK_Y = 157225;
	const int PLAYERBOT_FISHING_BANK_RADIUS = 2600;
	const DWORD PLAYERBOT_FISHING_STAND_CLAIM = 120000;
	// A point well inside the river, used only to turn the bot to face the water.
	const long PLAYERBOT_FISHING_WATER_X = 68000;
	// Where an angler counts as arrived - and it may never be tighter than
	// PLAYERBOT_NAV_ARRIVAL_DISTANCE, which is where the walk itself stops.
	//
	// This was cut to twenty-five to keep anglers a metre apart and that made a
	// dead zone: MovePlayerBot reports success and stops moving at a hundred
	// units from the goal, the fishing pass kept asking for another step, and
	// the bot stood between the two numbers for ever with stuck=0 and nothing in
	// any log. Measured on the live server at seventy-one and seventy-six units
	// from a destination neither bot ever reached.
	//
	// The consequence is honest and worth stating: with stands a hundred and
	// fifty apart and a hundred units of tolerance at each end, two anglers can
	// still end up close. Spacing them further is a separate change to the stand
	// table, not a number to shave here. The static_assert in
	// playerbot_activities.h keeps this from being lowered again.
	const int PLAYERBOT_FISHING_ARRIVE = 100;
	// Independently planned route failures before the bank is written off. Six
	// matches the town-service rescue; anything larger is indistinguishable from
	// never giving up at all.
	const int PLAYERBOT_FISHING_STUCK_LIMIT = 6;
	const DWORD PLAYERBOT_FISHING_PROGRESS_LOG = 15000;
	// fishing::Compute() peaks at time step 15 -- about 3.0 s after the bite for
	// the normal and easy tables.  Pulling in a small band around that catches
	// fish reliably without looking frame-perfect.
	const DWORD PLAYERBOT_FISHING_PULL_MIN_DELAY = 2700;
	const DWORD PLAYERBOT_FISHING_PULL_MAX_DELAY = 3300;
	// A cast that never reports a bite (the engine waits 10-40 s) is abandoned so
	// one wedged event cannot park a bot at the water forever.
	const DWORD PLAYERBOT_FISHING_CAST_TIMEOUT = 60000;
	// And a bot that reaches the water and never casts at all.
	//
	// The cast timeout above covers a line that goes in and never bites. Nothing
	// covered the step before it: an angler standing on its bank with bait in
	// the bag and no rod on its back had no clock of any kind, and one was
	// reported standing there for two hours. A session that has not managed a
	// single cast in this long is over; the ordinary rest interval then keeps
	// the bot away from the water until something has changed.
	const DWORD PLAYERBOT_FISHING_NO_CAST_GIVE_UP = 120000;
	const DWORD PLAYERBOT_FISHING_SESSION_MIN = 900000;    // 15 min
	const DWORD PLAYERBOT_FISHING_SESSION_MAX = 2400000;   // 40 min
	const DWORD PLAYERBOT_FISHING_REST_MIN = 2700000;      // 45 min
	const DWORD PLAYERBOT_FISHING_REST_MAX = 7200000;      // 2 h
	const int PLAYERBOT_HORSE_MOUNT_DISTANCE = 1800;
	const int PLAYERBOT_HORSE_DISMOUNT_DISTANCE = 1000;
	const DWORD PLAYERBOT_HORSE_RIDE_RETRY_INTERVAL = 10000;
	const DWORD PLAYERBOT_HORSE_TRAVEL_MIN_DELAY = 30000;
	const DWORD PLAYERBOT_HORSE_TRAVEL_MAX_DELAY = 300000;
	// Holding a target defers world travel, but only for so long. Where the
	// respawn is dense a bot re-acquires one before the next tick, so an
	// unbounded deferral meant the routing code never ran and an arrival area
	// became somewhere a bot could enter but not leave (issue #10).
	const DWORD PLAYERBOT_TRAVEL_FIGHT_GRACE = 30000;
	// What counts as being in the fight rather than merely locked on to it.
	const DWORD PLAYERBOT_TRAVEL_ENGAGED_WINDOW = 5000;
	const int PLAYERBOT_TRAVEL_ENGAGED_RANGE = 800;
	const DWORD PLAYERBOT_WORLD_TRAVEL_MIN_DELAY = 60000;
	const DWORD PLAYERBOT_WORLD_TRAVEL_MAX_DELAY = 360000;
	// Level 22 is past M1's useful experience range.  These bots still leave in a
	// staggered wave, but do not spend another six minutes farming weak mobs after
	// completing their town errands.
	const DWORD PLAYERBOT_LEVEL22_TRAVEL_MIN_DELAY = 15000;
	const DWORD PLAYERBOT_LEVEL22_TRAVEL_MAX_DELAY = 90000;
	// Refining remains important, but it is a planned town run rather than a reason
	// to bounce M2 -> M1 after every newly affordable +1 attempt.
	const DWORD PLAYERBOT_REMOTE_REFINE_RETURN_MIN_DELAY = 720000;
	const DWORD PLAYERBOT_REMOTE_REFINE_RETURN_MAX_DELAY = 1500000;
	const DWORD PLAYERBOT_MONKEY_MAX_VISIT_TIME = 1800000;
	// Which Monkey Dungeon a level is sent to. The medal is a "kill" drop group
	// (mob_drop_item.txt: one medal per 550 soldiers, 500 fighters, 200 generals)
	// and CreateDropItem scales every kill-group roll by aiPercentByDeltaLev -
	// 1% of the rate once the killer stands fifteen levels above the monster.
	// So a level-45 bot in the easy dungeon (monkeys of 22-29) needed fifty
	// thousand kills for a medal: 140 trips an hour brought back one. The
	// medium dungeon holds monkeys of 35-42 and the hard one 45-54; the bands
	// keep a bot within ten levels of the room it fights in.
	const BYTE PLAYERBOT_MONKEY_MIN_LEVEL = 18;
	const BYTE PLAYERBOT_MONKEY_MEDIUM_MIN_LEVEL = 33;
	const BYTE PLAYERBOT_MONKEY_HARD_MIN_LEVEL = 46;
	const DWORD PLAYERBOT_M3_MAX_VISIT_TIME = 1200000;
	const DWORD PLAYERBOT_MONKEY_REVERSE_PORTAL_BLOCK_TIME = 10000;
	// The third hand. Worn in a unique slot it makes CHARACTER::RewardGold hand
	// a kill's yang straight to the killer instead of scattering coin piles on
	// the ground, which is a bot's whole reason for wanting one: the walk to
	// each pile costs a route plan and the piles it never reaches rot where
	// they fell. The engine asks IsEquipUniqueGroup(UNIQUE_GROUP_AUTOLOOT), and
	// what that group holds on this server is 72016..72018 - not the 71010 the
	// item shop sells, which belongs to no group at all and would do nothing.
	//
	// It is a shop item with a wear clock: ITEM_MANAGER::CreateItem seeds
	// ITEM_SOCKET_UNIQUE_REMAIN_TIME from VALUE0 and unique_expire_event counts
	// it down one minute at a time while the item is worn, so 72018 is three
	// hours of hunting and then nothing. A bot has no item shop to go back to,
	// so its copy is wound back up instead of re-bought - the same answer
	// ManagePlayerBotSkillBooks gives to a book's eighteen-hour wait.
	const DWORD PLAYERBOT_THIRD_HAND_VNUM = 72018;
	const long PLAYERBOT_THIRD_HAND_MINUTES = 525600;
	const long PLAYERBOT_THIRD_HAND_REWIND_BELOW = 10080;
	const DWORD PLAYERBOT_THIRD_HAND_INTERVAL = 300000;
	// How long a bot works one chamber before walking to the portal that leads
	// to the next. Four minutes is two respawns of a room's dozen monsters; the
	// thirty-minute visit therefore covers six or seven of the eleven chambers.
	const DWORD PLAYERBOT_MONKEY_CHAMBER_DWELL = 240000;
	const long PLAYERBOT_MONKEY_EASY_BASE_X = 844800;
	const long PLAYERBOT_MONKEY_EASY_BASE_Y = 435200;
	// The three dungeons are one maze: metin2_map_monkey_dungeon2 and _3 carry
	// the same server_attr, the same regen cells and the same GOTO portals as
	// _12, at another base position. Everything placed in the easy dungeon is
	// therefore a local offset, and a dungeon is its base.
	const long PLAYERBOT_MONKEY_MEDIUM_BASE_X = 128000;
	const long PLAYERBOT_MONKEY_MEDIUM_BASE_Y = 640000;
	const long PLAYERBOT_MONKEY_HARD_BASE_X = 128000;
	const long PLAYERBOT_MONKEY_HARD_BASE_Y = 716800;
	// Six cells south of the exit NPC (10070/10073/10075, cell 72,119 and
	// 72,114 - the arrival is where the easy one always was, the portal is
	// the NPC itself).
	const long PLAYERBOT_MONKEY_ARRIVAL_LOCAL_X = 7200;
	const long PLAYERBOT_MONKEY_ARRIVAL_LOCAL_Y = 12500;
	const long PLAYERBOT_MONKEY_RETURN_LOCAL_X = 7200;
	const long PLAYERBOT_MONKEY_RETURN_LOCAL_Y = 11900;

	bool IsPlayerBotMonkeyMap(long mapIndex)
	{
		return mapIndex == PLAYERBOT_MAP_MONKEY_EASY ||
				mapIndex == PLAYERBOT_MAP_MONKEY_MEDIUM ||
				mapIndex == PLAYERBOT_MAP_MONKEY_HARD;
	}

	bool GetPlayerBotMonkeyBase(long mapIndex, long& outX, long& outY)
	{
		switch (mapIndex)
		{
			case PLAYERBOT_MAP_MONKEY_EASY: outX = PLAYERBOT_MONKEY_EASY_BASE_X; outY = PLAYERBOT_MONKEY_EASY_BASE_Y; return true;
			case PLAYERBOT_MAP_MONKEY_MEDIUM: outX = PLAYERBOT_MONKEY_MEDIUM_BASE_X; outY = PLAYERBOT_MONKEY_MEDIUM_BASE_Y; return true;
			case PLAYERBOT_MAP_MONKEY_HARD: outX = PLAYERBOT_MONKEY_HARD_BASE_X; outY = PLAYERBOT_MONKEY_HARD_BASE_Y; return true;
			default: return false;
		}
	}

	bool GetPlayerBotMonkeyArrival(long mapIndex, long& outX, long& outY)
	{
		long baseX = 0, baseY = 0;
		if (!GetPlayerBotMonkeyBase(mapIndex, baseX, baseY))
			return false;
		outX = baseX + PLAYERBOT_MONKEY_ARRIVAL_LOCAL_X;
		outY = baseY + PLAYERBOT_MONKEY_ARRIVAL_LOCAL_Y;
		return true;
	}

	bool GetPlayerBotMonkeyReturnPortal(long mapIndex, long& outX, long& outY)
	{
		long baseX = 0, baseY = 0;
		if (!GetPlayerBotMonkeyBase(mapIndex, baseX, baseY))
			return false;
		outX = baseX + PLAYERBOT_MONKEY_RETURN_LOCAL_X;
		outY = baseY + PLAYERBOT_MONKEY_RETURN_LOCAL_Y;
		return true;
	}

	// The dungeon a bot of this level earns medals in, or 0 below the band.
	long GetPlayerBotMonkeyMapForLevel(BYTE level)
	{
		if (level < PLAYERBOT_MONKEY_MIN_LEVEL)
			return 0;
		if (level < PLAYERBOT_MONKEY_MEDIUM_MIN_LEVEL)
			return PLAYERBOT_MAP_MONKEY_EASY;
		if (level < PLAYERBOT_MONKEY_HARD_MIN_LEVEL)
			return PLAYERBOT_MAP_MONKEY_MEDIUM;
		return PLAYERBOT_MAP_MONKEY_HARD;
	}

	const char* GetPlayerBotMonkeyName(long mapIndex)
	{
		switch (mapIndex)
		{
			case PLAYERBOT_MAP_MONKEY_EASY: return "easy";
			case PLAYERBOT_MAP_MONKEY_MEDIUM: return "medium";
			case PLAYERBOT_MAP_MONKEY_HARD: return "hard";
			default: return "monkey";
		}
	}
	const long MAP21_BASE_X = 921600;
	const long MAP21_BASE_Y = 204800;

	// One line on a stall's counter. CShop keeps its own item list private, and a
	// bot browsing the market reads this instead - we are the ones who put the
	// items there, so it is exactly what is on sale.
	// The engine's private-shop grid, as SetShopItems lays it out: five columns,
	// and rows down to SHOP_HOST_ITEM_MAX_NUM (forty) cells - the grid itself has
	// nine rows, but the item vector has forty entries and a slot past them is
	// out of bounds. A line occupies its cell and the cells below it, one per
	// unit of the item's size.
	const int PLAYERBOT_SHOP_GRID_COLUMNS = 5;
	const int PLAYERBOT_SHOP_GRID_ROWS = 8;
	const int PLAYERBOT_SHOP_GRID_CELLS = PLAYERBOT_SHOP_GRID_COLUMNS * PLAYERBOT_SHOP_GRID_ROWS;

	struct TPlayerBotShopOffer
	{
		DWORD dwVnum;
		DWORD dwPrice;
		BYTE bRefine;
		// A stall line is a whole stack, priced as one. What a buyer paid for the
		// line only says something about the material once it is divided by this.
		WORD wCount;
		// The item itself, by id. A line is sold once the engine has moved this
		// item to its buyer, and that is the only fact that says so: the sold
		// stack's vnum and refine are still in the keeper's bag whenever it
		// carries a second stack of the same thing - a bought stack lands in its
		// own cell and never merges - and matching by vnum found that second
		// stack and walked a buyer over to a sold slot.
		DWORD dwItemID;
		// Where the line sits in the engine's shop, which is what CShopManager::Buy
		// indexes by. Not the line's index in the table: a private shop is a grid
		// of five columns and eight rows, a weapon is three cells tall and an
		// armour two, and a line whose cell the item above already covers is
		// dropped by SetShopItems with a "not empty position" in syserr - two
		// hundred and eighty of them in an hour. Numbering the lines 0, 1, 2 put
		// every line from the second row under a weapon or an armour, so the
		// engine had nothing at those slots and refused every buyer who walked
		// over for one: two thousand refusals to five hundred purchases.
		BYTE bSlot;
	};

	struct TPlayerBotBiologistMission
	{
		BYTE requiredLevel;
		const char* questName;
		DWORD itemVnum;
		DWORD mobVnum;
		BYTE requiredCount;
		BYTE acceptPercent;
		DWORD rewardGold;
		DWORD rewardExp;
		const char* itemLabel;
	};

	const TPlayerBotBiologistMission PLAYERBOT_BIOLOGIST_MISSIONS[] = {
		{ 4,  "make_herb_lv4",  50701, 173, 5,  90, 1000,  500,    "Kwiat Brzoskwini" },
		{ 7,  "make_herb_lv7",  50702, 175, 5,  90, 3000,  2000,   "Pokrzywa" },
		{ 10, "make_herb_lv10", 50703, 177, 5,  90, 5000,  6500,   "Kwiat Kaki" },
		{ 15, "make_herb_lv15", 50704, 181, 5,  90, 10000, 25000,  "Korzen Gango" },
		{ 20, "make_herb_lv20", 50705, 182, 10, 80, 15000, 95000,  "Bez" },
		{ 25, "make_herb_lv25", 50706, 183, 10, 70, 20000, 200000, "Grzyb Tue" },
		// The Orc Tooth. Ten from the Orcs (601) of the valley, one in twenty
		// kills while the quest is open; sixty percent of what is handed in is
		// accepted, the rest is spoiled, as in the quest without the elixir. The
		// quest's twenty-two hours between hand-ins are not kept - a bot hands
		// in what it carries. Then the second half: Jinunggyi's Soul Stone
		// (30220), one in five hundred Elite Orc kills while the quest waits for
		// it, and the reward is the quest's own, ten movement speed for good.
		{ 30, "collect_quest_lv30", 30006, 601, 10, 60, 0, 0, "Zab Orka" }
	};
	const size_t PLAYERBOT_BIOLOGIST_ORC_TOOTH_INDEX = 6;
	const DWORD PLAYERBOT_ORC_TOOTH_VNUM = 30006;
	// How many specimens are worth a walk to Joan.
	//
	// The hand-in was gated on carrying the whole remaining count - ten Orc
	// Teeth in one bag - and almost nobody ever got there: 700 bots held 2219
	// teeth between them, three apiece, and exactly three had ten. Meanwhile the
	// Biologist's counter stood at 0/10 for the entire world. The hand-in itself
	// has always been one specimen at a time with a 60% accept roll, so a
	// partial load was never a problem for the quest - only for the gate in
	// front of it.
	const int PLAYERBOT_BIOLOGIST_MIN_HANDIN = 4;
	// A herb row this far below the bot is one it will never do: the monsters
	// that carry the early specimens stand in Joan and Bokjung, and a bot of
	// forty lives in the valley. The chain is not one quest but seven, so a row
	// can be stepped over rather than blocking every row behind it - which is
	// what the Discord saw: a Sura of forty-two with "Korzen Gango 0/5" as its
	// stated goal, hitting Orcs, for ever.
	const int PLAYERBOT_BIOLOGIST_OUTGROWN_LEVELS = 10;
	const DWORD PLAYERBOT_JINUNGGYI_STONE_VNUM = 30220;
	const DWORD PLAYERBOT_ELITE_ORC_VNUM = 631;
	const DWORD PLAYERBOT_ORC_TOOTH_REWARD_BOX_VNUM = 50109;
	const int PLAYERBOT_ORC_TOOTH_REWARD_MOV_SPEED = 10;
	const size_t PLAYERBOT_BIOLOGIST_MISSION_COUNT =
			sizeof(PLAYERBOT_BIOLOGIST_MISSIONS) / sizeof(PLAYERBOT_BIOLOGIST_MISSIONS[0]);

	// Canonical ``special.levelup_quest`` entries from questlib.lua.  These are
	// the ordinary Hunting Missions shown to a human player after each level;
	// playerbots use the very same quest flags and kill event, they merely make
	// the menu choice which a fake descriptor cannot click.  The first phase is
	// deliberately bounded to the M1/M2 levels that this AI can currently reach.
	struct TPlayerBotHuntingMission
	{
		DWORD firstMobVnum;
		WORD firstCount;
		DWORD secondMobVnum;
		WORD secondCount;
		BYTE expPercent;
	};

	const BYTE PLAYERBOT_HUNTING_FIRST_LEVEL = 2;
	// The table now runs to 55, which is as far as the hosted maps reach: every
	// row past 25 is questlib's own. Not every row can be done here - the
	// Bestial Arahans, the plagued of the newer Sohan, the strong apes and the
	// demons stand on maps this world does not host - so a bot picks the option
	// that stands where it is, then one that stands anywhere hosted, and a row
	// with neither is passed over rather than left to block every row after
	// it. A row a bot accepted and could not finish inside two hours is passed
	// over the same way: the monster is somewhere the bot is not going.
	const BYTE PLAYERBOT_HUNTING_MAX_LEVEL = 55;
	const int PLAYERBOT_HUNTING_STALL_SECONDS = 7200;
	// A mission this many levels below the bot is outgrown: its monster stands
	// on a map the bot has left for good. Nearly every bot at forty was found
	// holding a mission from fifteen, waiting for a wolf it would never see.
	const int PLAYERBOT_HUNTING_OUTGROWN_LEVELS = 10;
	const TPlayerBotHuntingMission PLAYERBOT_HUNTING_MISSIONS[] = {
		{ 0, 0, 0, 0, 0 }, { 0, 0, 0, 0, 0 },
		{ 171, 10, 172, 5, 10 }, { 171, 20, 172, 10, 10 },
		{ 172, 15, 173, 5, 10 }, { 173, 10, 174, 10, 10 },
		{ 174, 20, 178, 10, 10 }, { 178, 10, 175, 5, 10 },
		{ 178, 20, 175, 10, 10 }, { 175, 15, 179, 5, 10 },
		{ 175, 20, 179, 10, 10 }, { 179, 10, 180, 5, 10 },
		{ 180, 15, 176, 10, 10 }, { 176, 20, 181, 5, 10 },
		{ 181, 15, 177, 5, 10 }, { 181, 20, 177, 10, 10 },
		{ 177, 15, 184, 5, 10 }, { 177, 20, 184, 10, 10 },
		{ 184, 10, 182, 10, 10 }, { 182, 20, 183, 10, 10 },
		{ 183, 20, 352, 15, 10 }, { 352, 20, 185, 10, 0 },
		{ 185, 25, 354, 10, 0 }, { 354, 20, 451, 40, 0 },
		{ 451, 60, 402, 80, 0 }, { 551, 80, 454, 20, 0 },
		{ 552, 80, 456, 20, 0 }, { 456, 30, 554, 20, 0 },
		{ 651, 35, 554, 30, 0 }, { 651, 40, 652, 30, 0 },
		{ 652, 40, 2102, 30, 0 }, { 652, 50, 2102, 45, 0 },
		{ 653, 45, 2051, 40, 0 }, { 751, 35, 2103, 30, 0 },
		{ 751, 40, 2103, 40, 0 }, { 752, 40, 2052, 30, 0 },
		{ 754, 20, 2106, 20, 0 }, { 773, 30, 2003, 20, 0 },
		{ 774, 40, 2004, 20, 0 }, { 756, 40, 2005, 30, 0 },
		{ 757, 40, 2158, 20, 0 }, { 931, 40, 5123, 25, 0 },
		{ 932, 30, 5123, 30, 0 }, { 932, 40, 2031, 35, 0 },
		{ 933, 40, 2031, 40, 0 }, { 771, 50, 2032, 45, 0 },
		{ 772, 30, 5124, 30, 0 }, { 933, 35, 5125, 30, 0 },
		{ 934, 40, 5125, 35, 0 }, { 773, 40, 2033, 45, 0 },
		{ 774, 40, 5126, 20, 0 }, { 775, 50, 5126, 30, 0 },
		{ 934, 45, 2034, 45, 0 }, { 934, 50, 2034, 50, 0 },
		{ 776, 40, 1001, 30, 0 }, { 777, 40, 1301, 35, 0 }
	};

	// Where a hunting-mission monster stands, among the hosted maps: read out of
	// the regen files of the fourteen maps this world hosts. A vnum with no row
	// stands nowhere a bot can go.
	struct TPlayerBotMobHome { DWORD vnum; long map1; long map2; };
	const TPlayerBotMobHome PLAYERBOT_HUNTING_MOB_HOMES[] = {
		{ 552, 23, 0 }, { 456, 23, 0 }, { 554, 23, 0 },
		// Mount Sohan (61): the Infected the rows from 41 ask for.
		{ 901, 61, 0 }, { 902, 61, 0 }, { 903, 61, 0 }, { 904, 61, 0 }, { 905, 61, 0 }, { 906, 61, 0 },
		{ 931, 61, 0 }, { 932, 61, 0 }, { 933, 61, 0 }, { 934, 61, 0 }, { 935, 61, 0 }, { 936, 61, 0 },
		{ 651, 64, 0 }, { 652, 64, 0 }, { 653, 64, 0 },
		{ 751, 64, 0 }, { 752, 64, 0 }, { 754, 64, 0 }, { 756, 64, 0 }, { 757, 64, 0 },
		{ 2102, 63, 0 }, { 2051, 63, 0 }, { 2052, 63, 0 }, { 2106, 63, 0 },
		{ 2003, 63, 0 }, { 2004, 63, 0 }, { 2005, 63, 0 }, { 2158, 63, 0 },
		{ 2103, 63, 64 },
		{ 2031, 104, 0 }, { 2032, 104, 0 }, { 2033, 104, 0 }, { 2034, 104, 0 },
		// The Biologist's Orc Tooth: the Orc and the Elite Orc of the valley.
		{ 601, 64, 0 }, { 631, 64, 0 }
	};

	bool IsPlayerBotHuntingMobHosted(DWORD vnum, long lMapIndex = 0)
	{
		// Everything the first twenty-five rows ask for lives in Joan and Bokjung.
		if (vnum < 500)
			return lMapIndex == 0 || lMapIndex == PLAYERBOT_MAP_CHUNJO_M1 || lMapIndex == PLAYERBOT_MAP_CHUNJO_M2;
		for (size_t i = 0; i < sizeof(PLAYERBOT_HUNTING_MOB_HOMES) / sizeof(PLAYERBOT_HUNTING_MOB_HOMES[0]); ++i)
		{
			const TPlayerBotMobHome& home = PLAYERBOT_HUNTING_MOB_HOMES[i];
			if (home.vnum != vnum)
				continue;
			return lMapIndex == 0 || home.map1 == lMapIndex || home.map2 == lMapIndex;
		}
		return false;
	}

	struct TPlayerBotMapPoint { long x; long y; };
	// A hunting hub with the level band it is for and whether it is a party's
	// work. A solo bot never picks a party hub; a leader with a party of the
	// challenge size may.
	// wBossRace names the boss a hub exists for, or 0. A boss hub is not
	// scored by what the population has seen there - one monster every half
	// hour is a density of nothing, which is why the Orc Chief's and the Spider
	// Queen's hubs were never chosen in a day of logs - but by whether the boss
	// is standing there now, asked of the sector itself.
	struct TPlayerBotHuntingHub { long x; long y; BYTE bMinLevel; BYTE bMaxLevel; bool bNeedsParty; WORD wBossRace; };
	// How long a "boss alive" answer is trusted, and what a hub with a living
	// boss scores: above any camp, so the crowd (the Orc Chief) or the party
	// (the Spider Queen) goes.
	const DWORD PLAYERBOT_RAID_BOSS_CHECK_INTERVAL = 30000;
	// The Bestial Captain (591, level 42, boss) of Bokjung: metin2_map_b3's
	// boss.txt cell (787,688) on base (102400,204800), every hour, ten cells
	// of spread. Bokjung's wandering has no hub table - it rotates spawn
	// clusters - so the Captain is a detour taken while he stands, by anybody
	// of the band. Nine Tails (1901, level 72, boss) is a Sohan hub row.
	const long PLAYERBOT_M2_CAPTAIN_X = 181100;
	const long PLAYERBOT_M2_CAPTAIN_Y = 273600;
	const BYTE PLAYERBOT_M2_CAPTAIN_MIN_LEVEL = 35;
	const long PLAYERBOT_SOHAN_NINE_TAILS_X = 433300;
	const long PLAYERBOT_SOHAN_NINE_TAILS_Y = 216500;
	const int PLAYERBOT_RAID_WORTH = 100000;
	// How many bots one boss is worth calling out. A boss needs a raid, not a
	// province: past this many already on him the hub is scored like any other
	// ground, so the rest of the band goes on hunting instead of queueing.
	const int PLAYERBOT_RAID_CROWD = 12;
	// How long a guild's call stands. Long enough to walk across a frontier
	// map, short enough that a boss killed five minutes ago stops summoning
	// anybody.
	const DWORD PLAYERBOT_RAID_CALL_TIME = 180000;
	// Exact world coordinates of the two rare M2 enemies from
	// metin2_map_b3/boss.txt (map base 102400,204800). They are the classic
	// level-30 weapon hunt: Bestial Archer (533) and Specialist (534).
	const TPlayerBotMapPoint PLAYERBOT_M2_BESTIAL_HOTSPOTS[2] = {
		{ 132300, 259300 }, // Bestial Archer, local 299,545
		{ 129700, 275100 }  // Bestial Specialist, local 273,703
	};
	const TPlayerBotMapPoint PLAYERBOT_METIN_HOTSPOTS[12] = {
		{ 33400, 211800 }, { 29200, 164500 }, { 32900, 161600 },
		{ 39400, 160900 }, { 39400, 187100 }, { 63500, 204100 },
		{ 62600, 213600 }, { 88600, 201000 }, { 94000, 164300 },
		{ 83700, 119300 }, { 67600, 117700 }, { 63500, 133500 }
	};

	enum EPlayerBotRole
	{
		BOT_ROLE_MOB_GRINDER = 0,
		BOT_ROLE_METIN_HUNTER = 1,
		BOT_ROLE_PARTY_FIGHTER = 2
	};

	enum EPlayerBotMerchantCategory
	{
		BOT_MERCHANT_MISC = 0,
		BOT_MERCHANT_WEAPON,
		BOT_MERCHANT_ARMOR
	};

	enum EPlayerBotTownVisitPhase
	{
		BOT_TOWN_PHASE_NONE = 0,
		BOT_TOWN_PHASE_TRAINER,
		BOT_TOWN_PHASE_TRAINER_WAIT,
		BOT_TOWN_PHASE_GATE_IN,
		BOT_TOWN_PHASE_GATE_CROSS_IN,
		BOT_TOWN_PHASE_WEAPON_MERCHANT,
		BOT_TOWN_PHASE_WEAPON_WAIT,
		BOT_TOWN_PHASE_ARMOR_MERCHANT,
		BOT_TOWN_PHASE_ARMOR_WAIT,
		BOT_TOWN_PHASE_MISC_MERCHANT,
		BOT_TOWN_PHASE_MISC_WAIT,
		BOT_TOWN_PHASE_BLACKSMITH,
		BOT_TOWN_PHASE_BLACKSMITH_WAIT,
		BOT_TOWN_PHASE_GATE_OUT,
		BOT_TOWN_PHASE_GATE_CROSS_OUT
	};

	enum EPlayerBotLongTermGoal
	{
		BOT_GOAL_LEVEL_UP = 0,
		BOT_GOAL_SURVIVE,
		BOT_GOAL_CHOOSE_PROFESSION,
		BOT_GOAL_GET_EQUIPMENT,
		BOT_GOAL_RESTOCK,
		BOT_GOAL_REFINE,
		BOT_GOAL_MASTER_SKILL,
		BOT_GOAL_HUNT_METIN,
		BOT_GOAL_PARTY_CHALLENGE,
		BOT_GOAL_BIOLOGIST,
		BOT_GOAL_HUNTING,
		BOT_GOAL_HORSE,
		BOT_GOAL_FISHING
	};

	enum EPlayerBotCurrentAction
	{
		BOT_ACTION_IDLE = 0,
		BOT_ACTION_TRAVEL,
		BOT_ACTION_FIGHT,
		BOT_ACTION_LOOT,
		BOT_ACTION_RECOVER,
		BOT_ACTION_TRAIN,
		BOT_ACTION_SHOP,
		BOT_ACTION_REFINE,
		BOT_ACTION_READ_BOOK,
		BOT_ACTION_SOCKET_STONE,
		BOT_ACTION_PARTY_ASSEMBLE,
		BOT_ACTION_BIOLOGIST,
		BOT_ACTION_STABLE,
		// Standing at an open stall. Distinct from BOT_ACTION_SHOP, which is a
		// visit to an NPC merchant: the panel has to tell the two apart to list
		// who is actually trading. Appended, never inserted - the id goes into
		// the status file the panel reads.
		BOT_ACTION_STALL,
		BOT_ACTION_FISHING,
		// Walking the stall ring looking for something to buy. Distinct from
		// BOT_ACTION_SHOP, which is the NPC merchant round, and from
		// BOT_ACTION_STALL, which is standing behind a counter of one's own.
		BOT_ACTION_MARKET,
		// Bringing monsters to the party. Distinct from BOT_ACTION_FIGHT on
		// purpose: the Archer is not fighting, it tags and runs.
		BOT_ACTION_LURE,
		// Standing about in town with nothing to do. Distinct from
		// BOT_ACTION_RECOVER, which is a bot getting its health back, and from
		// BOT_ACTION_STALL, which is a bot behind a counter. Appended, never
		// inserted - the id goes into the status file the panel reads.
		BOT_ACTION_TOWN_REST
	};

	// Where an Archer is in its course. WAIT_READY is the absence of a session
	// rather than a stage of one, so it is LURE_STAGE_NONE.
	enum EPlayerBotLureStage
	{
		LURE_STAGE_NONE = 0,
		LURE_STAGE_PLAN,
		LURE_STAGE_APPROACH,
		LURE_STAGE_TAG,
		LURE_STAGE_CONFIRM,
		LURE_STAGE_RETURN,
		LURE_STAGE_HANDOFF,
		LURE_STAGE_RECOVER
	};

	enum EPlayerBotPersonality
	{
		BOT_PERSONALITY_STEADY_ADVENTURER = 0,
		BOT_PERSONALITY_METIN_BREAKER,
		BOT_PERSONALITY_TEAM_COMPANION,
		BOT_PERSONALITY_GEAR_SPECIALIST,
		BOT_PERSONALITY_CAREFUL_COLLECTOR,
		// A trader. Every other bot is chasing something - a level, a horse, a
		// better weapon - and they all end up playing the same way. This one keeps
		// a stall because that is what it does, not because it happened to have a
		// spare while passing through town.
		BOT_PERSONALITY_MERCHANT,
		BOT_PERSONALITY_WANDERER,
		// The droppers. Each farms one thing for the market rather than for
		// itself: the Metin dropper keeps the skill books a stone gives instead
		// of vendoring the ones it cannot read, the M3 dropper stays on Waryong
		// for the level-30 weapons whether or not it owns one, the M2 dropper
		// camps the Bestials of Bokjung for theirs, and the medal dropper works
		// the Monkey Dungeon past the point its own horse needs. Appended, never
		// inserted - the id goes into the status file the panel reads.
		BOT_PERSONALITY_METIN_DROPPER,
		BOT_PERSONALITY_M3_DROPPER,
		BOT_PERSONALITY_M2_DROPPER,
		BOT_PERSONALITY_MEDAL_DROPPER
	};

	bool IsPlayerBotDropper(BYTE personality)
	{
		return personality == BOT_PERSONALITY_METIN_DROPPER ||
				personality == BOT_PERSONALITY_M3_DROPPER ||
				personality == BOT_PERSONALITY_M2_DROPPER ||
				personality == BOT_PERSONALITY_MEDAL_DROPPER;
	}

	BYTE GetPlayerBotPersonalityByPID(DWORD dwPID);

	enum EPlayerBotAmbition
	{
		BOT_AMBITION_LEVEL = 0,
		BOT_AMBITION_EQUIPMENT,
		BOT_AMBITION_METINS,
		BOT_AMBITION_HORSE,
		BOT_AMBITION_BIOLOGIST,
		BOT_AMBITION_SKILLS,
		BOT_AMBITION_TRADE
	};

	// One acquaintance. Affinity only: the specification also wants hostility,
	// from PvP kills and stolen bosses, and this world has neither PvP nor a
	// hook that could honestly attribute a stolen kill - so a hostility counter
	// would be a field that is always zero.
	struct TPlayerBotFriend
	{
		DWORD dwPID;
		int iAffinity;
		DWORD dwLastInteractionTime;
		TPlayerBotFriend() : dwPID(0), iAffinity(0), dwLastInteractionTime(0) {}
	};

	struct TPlayerBotAIState
	{
		TPlayerBotAIState() :
			dwTargetVID(0),
			dwSpawnTime(0),
			dwLastBotSkillTime(0),
			dwLastKillerVID(0),
			dwLastDeathTime(0),
			lDeathX(0),
			lDeathY(0),
			bDeathCount(0),
			dwNextAttackTime(0),
			dwNextPotionTime(0),
			dwNextManaPotionTime(0),
			dwNextChestTime(0),
			dwNextBoosterTime(0),
			dwNextScrollRefineTime(0),
			dwNextPotionLogTime(0),
			dwDeathDetectedTime(0),
			dwNextReviveAttemptTime(0),
			dwNextGearAttemptTime(0),
			dwNextEquipmentCheckTime(0),
			dwNextStatCheckTime(0),
			dwNextSkillCheckTime(0),
			dwNextSkillBookTime(0),
			dwNextSoulStoneTime(0),
			dwNextThirdHandTime(0),
			dwNextProgressionChestCheckTime(0),
			dwNextBuffCheckTime(0),
			dwNextSkillCastTime(0),
			dwNextGearLogTime(0),
			dwNextPersistTime(0),
			dwNextRecoveryProtectionTime(0),
			dwNextRecoveryHealTime(0),
			dwRetreatStartedTime(0),
			dwNextRetreatMoveTime(0),
			dwRetreatThreatVID(0),
			dwNextRefineCheckTime(0),
			dwNextBonusCheckTime(0),
			dwNextChatTime(0),
			dwLastStatusChatTime(0),
			dwNextStatusProbeTime(0),
			dwLastStatusTargetVID(0),
			dwNextBiologistCheckTime(0),
			dwNextBiologistActionTime(0),
			dwNextHorseCheckTime(0),
			dwNextHorseActionTime(0),
			dwNextHorseRideCheckTime(0),
			dwNextFishingCheckTime(0),
			dwNextFishingActionTime(0),
			dwFishingCastTime(0),
			dwFishingIdleSince(0),
			dwFishingSessionEndTime(0),
			dwNextFishingProgressLogTime(0),
			dwBakeUntil(0),
			dwNextWorldTravelTime(0),
			dwTravelBlockedSince(0),
			dwNextRemoteRefineReturnTime(0),
			dwDungeonEnteredTime(0),
			dwM3EnteredTime(0),
			dwFrontierEnteredTime(0),
			dwShopOpenedTime(0),
			dwShopCloseTime(0),
			dwNextShopKeepTime(0),
			dwNextShoppingTime(0),
			dwMarketTripUntil(0),
			dwMarketBrowseTime(0),
			dwMarketStallVID(0),
			dwNextShopDebugTime(0),
			dwMonkeyReversePortalBlockUntil(0),
			dwMonkeyChamberTime(0),
			dwNextLootPickupTime(0),
			dwNextLootSearchTime(0),
			dwNextLootThreatCheckTime(0),
			dwNextLootCleanupTime(0),
			dwNextInventoryMaintenanceTime(0),
			dwNextWanderTime(0),
			dwNextPartyCheckTime(0),
			dwNextPartyShareTime(0),
			dwPartyExpireTime(0),
			dwNextLureTime(0),
			dwNextMultiPullTime(0),
			dwMultiPullStartedTime(0),
			dwNextMultiPullActionTime(0),
			dwMultiPullTargetVID(0),
			dwNextShopCheckTime(0),
			dwEmergencyScavengeUntil(0),
			dwTownWaitUntil(0),
			dwStoneFightStartTime(0),
			dwStoneProgressVID(0),
			dwStoneBrokenTime(0),
			dwRaceHistogramStamp(0),
			dwMetinExpeditionUntil(0),
			dwNextMetinExpeditionRoll(0),
			lDesertCrossingTo(0),
			lDesertCrossingX(0),
			lDesertCrossingY(0),
			dwNextCrossingStoneCheck(0),
			dwStoneLastProgressTime(0),
			dwNextStoneProgressCheckTime(0),
			dwNextNavPlanTime(0),
			dwNextNavProgressTime(0),
			dwNextSectreeRescueTime(0),
			dwNavFailedTargetVID(0),
			dwNextGoalPlanTime(0),
			dwGoalStartedTime(0),
			dwActionChangedTime(0),
			dwLastMeaningfulActivityTime(0),
			dwLastCombatActionTime(0),
			iLastStoneHP(0),
			iMultiPullStartHPPercent(0),
			bLastStoneAttackerCount(0),
			bLastPersistedLevel(0),
			bRouteAllowsHorse(false),
			bRecoveringAfterDeath(false),
			bTacticalRetreat(false),
			bMultiPullActive(false),
			bMultiPullGroups(0),
			bMultiPullDesiredGroups(0),
			bLootThreatNearby(false),
			bEquipPending(false),
			bVisitingShop(false),
			bMarketTrip(false),
			bTownNeedMisc(false),
			bTownNeedWeaponMerchant(false),
			bTownNeedArmorMerchant(false),
			bTownNeedBlacksmith(false),
			bTownNeedTrainer(false),
			bVisitingBiologist(false),
			bVisitingStable(false),
			bFishingSession(false),
			bIsFishing(false),
			bTownVisitPhase(BOT_TOWN_PHASE_NONE),
			bComboMotion(MOTION_COMBO_ATTACK_1),
			bStuckCounter(0),
			lLastX(0),
			lDefenceAnchorX(0),
			lDefenceAnchorY(0),
			lLastY(0),
			uRouteIndex(0),
			lRouteDestX(0),
			lRouteDestY(0),
			lRouteMapIndex(0),
			lParkedDestX(0),
			lParkedDestY(0),
			lParkedMapIndex(0),
			lIssuedWaypointX(0),
			lIssuedWaypointY(0),
			lNavProgressX(0),
			lNavProgressY(0),
			iNavLastWaypointDistance(-1),
			iLastMonkeyPortalIndex(-1),
			bNavNoProgressCount(0),
			bNavFailedTargetCount(0),
			bNavDeferredCount(0),
			bBotRole(BOT_ROLE_MOB_GRINDER),
			bPersonality(BOT_PERSONALITY_STEADY_ADVENTURER),
			bAmbition(BOT_AMBITION_LEVEL),
			uMetinHotspotIndex(0),
			bMonkeyChamber(255),
			bMonkeyPrevChamber(255),
			bMonkeySpot(0),
			bLongTermGoal(BOT_GOAL_LEVEL_UP),
			bCurrentAction(BOT_ACTION_IDLE),
			bLastStatusAction(255),
			bLastStatusGoal(255),
			bLastStatusTownPhase(255),
			bLastStatusParty(255),
			dwNextGuildCheckTime(0),
			dwLastKillCreditedVID(0),
			bFoundedGuild(false),
			dwNextMaterialScanTime(0),
			dwMaterialHuntVnum(0),
			dwShopSignClearUntil(0),
			dwNextShopSignClearTime(0),
			dwPortalWalkSince(0),
			iPortalWalkBest(0),
			dwFightProgressVID(0),
			dwDefenceTargetVID(0),
			dwDefenceEpisodeStart(0),
			dwNextCombatRecheckTime(0),
			dwErrandDoneTime(0),
			dwFightStartTime(0),
			dwFightLastProgressTime(0),
			iLastFightHP(0),
			lCampX(0),
			lCampY(0),
			dwCampSince(0),
			dwRelocateSince(0),
			wHuntingHub(0xffff),
			dwHubChosenTime(0),
			dwTownLingerUntil(0),
			dwTownBrowseUntil(0),
			lTownBrowseX(0),
			lTownBrowseY(0),
			dwFirstNavDeferTime(0),
			dwMarketM2AllowedUntil(0),
			dwServiceRetryAt(0),
			dwServiceSince(0),
			dwDepartureSince(0),
			lDepartureMap(0),
			bServicePending(false),
			bLastCombatReason(0),
			dwLureSessionId(0),
			dwLureStageTime(0),
			dwLureCourseTime(0),
			dwLureShotTime(0),
			dwLureNextTime(0),
			dwLureTargetVID(0),
			dwLureReceiverPID(0),
			lLureAnchorX(0),
			lLureAnchorY(0),
			iLureStartHPPercent(0),
			iLureDelivered(0),
			iLureChasing(0),
			bLureStage(LURE_STAGE_NONE),
			bLureGroupsPlanned(0),
			bLureGroupsTagged(0),
			bLureBudget(0),
			bLureTagAttempts(0),
			bLureGoodCourses(0)
		{
		}

		DWORD dwTargetVID;
		DWORD dwSpawnTime;
		DWORD dwLastBotSkillTime;
		DWORD dwLastKillerVID;
		DWORD dwLastDeathTime;
		long lDeathX;
		long lDeathY;
		BYTE bDeathCount;
		DWORD dwNextAttackTime;
		DWORD dwNextPotionTime;
		DWORD dwNextManaPotionTime;
		DWORD dwNextChestTime;
		DWORD dwNextBoosterTime;
		DWORD dwNextScrollRefineTime;
		DWORD dwNextPotionLogTime;
		DWORD dwDeathDetectedTime;
		DWORD dwNextReviveAttemptTime;
		DWORD dwNextGearAttemptTime;
		DWORD dwNextEquipmentCheckTime;
		DWORD dwNextStatCheckTime;
		DWORD dwNextSkillCheckTime;
		DWORD dwNextSkillBookTime;
		DWORD dwNextSoulStoneTime;
		DWORD dwNextThirdHandTime;
		DWORD dwNextProgressionChestCheckTime;
		DWORD dwNextBuffCheckTime;
		DWORD dwNextSkillCastTime;
		DWORD dwNextGearLogTime;
		DWORD dwNextPersistTime;
		DWORD dwNextRecoveryProtectionTime;
		DWORD dwNextRecoveryHealTime;
		DWORD dwRetreatStartedTime;
		DWORD dwNextRetreatMoveTime;
		DWORD dwRetreatThreatVID;
		DWORD dwNextRefineCheckTime;
		DWORD dwNextBonusCheckTime;
		DWORD dwNextChatTime;
		DWORD dwLastStatusChatTime;
		DWORD dwNextStatusProbeTime;
		DWORD dwLastStatusTargetVID;
		DWORD dwNextBiologistCheckTime;
		DWORD dwNextBiologistActionTime;
		DWORD dwNextHorseCheckTime;
		DWORD dwNextHorseActionTime;
		DWORD dwNextHorseRideCheckTime;
		DWORD dwNextFishingCheckTime;
		DWORD dwNextFishingActionTime;
		// When the current line went into the water, so a cast that never reports
		// a bite can be given up on instead of parking the bot at the bank.
		DWORD dwFishingCastTime;
		// When this angler was last ready to fish and did not. Cleared by a cast.
		DWORD dwFishingIdleSince;
		DWORD dwFishingSessionEndTime;
		// A stuck angler used to be invisible: bFishingSession exempts it from the
		// inactivity watchdog, so nothing complained while it stood still for the
		// whole session. This throttles one progress line instead.
		DWORD dwNextFishingProgressLogTime;
		// The campfire is burning and there are fish to hand it.
		DWORD dwBakeUntil;
		DWORD dwNextWorldTravelTime;
		// Since when a live target has been holding world travel back.
		DWORD dwTravelBlockedSince;
		DWORD dwNextRemoteRefineReturnTime;
		DWORD dwDungeonEnteredTime;
		DWORD dwM3EnteredTime;
		DWORD dwFrontierEnteredTime;
		DWORD dwShopOpenedTime;
		DWORD dwShopCloseTime;
		DWORD dwNextShopKeepTime;
		DWORD dwNextShoppingTime;
		// The shopping trip: when it must be over, when the counters may be read
		// again, and which keeper the bot is currently walking up to. The stall is
		// held as a VID rather than a position so that a keeper which packs up
		// mid-walk simply stops being found.
		DWORD dwMarketTripUntil;
		DWORD dwMarketBrowseTime;
		DWORD dwMarketStallVID;
		// What this bot is currently selling, in the order the items sit on the
		// counter - an index here is the index CShopManager::Buy expects. Not in
		// the initialiser list: it default-constructs empty, which is the state a
		// bot with no stall is in.
		std::vector<TPlayerBotShopOffer> vecShopOffers;
		DWORD dwNextShopDebugTime;
		DWORD dwMonkeyReversePortalBlockUntil;
		// Since when this bot has been working its current Monkey Dungeon chamber.
		DWORD dwMonkeyChamberTime;
		DWORD dwNextLootPickupTime;
		DWORD dwNextLootSearchTime;
		DWORD dwNextLootThreatCheckTime;
		DWORD dwNextLootCleanupTime;
		DWORD dwNextInventoryMaintenanceTime;
		DWORD dwNextWanderTime;
		DWORD dwNextPartyCheckTime;
		DWORD dwNextPartyShareTime;
		DWORD dwPartyExpireTime;
		DWORD dwNextLureTime;
		DWORD dwNextMultiPullTime;
		DWORD dwMultiPullStartedTime;
		DWORD dwNextMultiPullActionTime;
		DWORD dwMultiPullTargetVID;
		DWORD dwNextShopCheckTime;
		DWORD dwEmergencyScavengeUntil;
		DWORD dwTownWaitUntil;
		DWORD dwStoneFightStartTime;
		DWORD dwStoneProgressVID;
		DWORD dwStoneBrokenTime;
		// What this bot has fought lately, by race flag; see the world memory.
		WORD awRaceHistogram[PLAYERBOT_RACE_HISTOGRAM_SLOTS] = { 0, 0, 0, 0, 0 };
		DWORD dwRaceHistogramStamp;
		// The Metin expedition: until when this bot hunts stones like a hunter,
		// and when it next rolls for one. See PLAYERBOT_METIN_EXPEDITION_*.
		DWORD dwMetinExpeditionUntil;
		DWORD dwNextMetinExpeditionRoll;
		// The desert crossing: the map and point the bot is really going to,
		// while it walks the desert between two gates. Zero when not crossing.
		long lDesertCrossingTo;
		long lDesertCrossingX;
		long lDesertCrossingY;
		DWORD dwNextCrossingStoneCheck;
		// When this bot last read a book of each skill, for the BOOKS switch.
		DWORD dwStoneLastProgressTime;
		DWORD dwNextStoneProgressCheckTime;
		DWORD dwNextNavPlanTime;
		DWORD dwNextNavProgressTime;
		DWORD dwNextSectreeRescueTime;
		DWORD dwNavFailedTargetVID;
		DWORD dwNextGoalPlanTime;
		DWORD dwGoalStartedTime;
		DWORD dwActionChangedTime;
		DWORD dwLastMeaningfulActivityTime;
		DWORD dwLastCombatActionTime;
		int iLastStoneHP;
		int iMultiPullStartHPPercent;
		BYTE bLastStoneAttackerCount;
		BYTE bLastPersistedLevel;
		bool bRouteAllowsHorse;
		bool bRecoveringAfterDeath;
		bool bTacticalRetreat;
		bool bMultiPullActive;
		BYTE bMultiPullGroups;
		BYTE bMultiPullDesiredGroups;
		bool bLootThreatNearby;
		bool bEquipPending;
		bool bVisitingShop;
		// On a shopping trip: walking to the stalls, or standing among them.
		bool bMarketTrip;
		bool bTownNeedMisc;
		bool bTownNeedWeaponMerchant;
		bool bTownNeedArmorMerchant;
		bool bTownNeedBlacksmith;
		bool bTownNeedTrainer;
		bool bVisitingBiologist;
		bool bVisitingStable;
		// The bot has committed to a fishing trip: it carries a rod in the weapon
		// slot and skips combat and gear swaps until the session ends.
		bool bFishingSession;
		// A line is currently in the water (the engine holds a fishing event).
		bool bIsFishing;
		BYTE bTownVisitPhase;
		BYTE bComboMotion;
		BYTE bStuckCounter;
		long lLastX;
		long lDefenceAnchorX;
		long lDefenceAnchorY;
		long lLastY;
		std::vector<PIXEL_POSITION> vecRoute;
		size_t uRouteIndex;
		long lRouteDestX;
		long lRouteDestY;
		long lRouteMapIndex;
		// The route a fight interrupted, kept so the walk resumes from the
		// nearest waypoint instead of being planned again from scratch. A far
		// plan costs two hundred milliseconds; a valley crossing meets a fight
		// every few seconds.
		std::vector<PIXEL_POSITION> vecParkedRoute;
		long lParkedDestX;
		long lParkedDestY;
		long lParkedMapIndex;
		long lIssuedWaypointX;
		long lIssuedWaypointY;
		long lNavProgressX;
		long lNavProgressY;
		int iNavLastWaypointDistance;
		int iLastMonkeyPortalIndex;
		BYTE bNavNoProgressCount;
		BYTE bNavFailedTargetCount;
		BYTE bNavDeferredCount;
		BYTE bBotRole;
		BYTE bPersonality;
		BYTE bAmbition;
		BYTE uMetinHotspotIndex;
		// The Monkey Dungeon chamber this bot is working, the one it came from
		// (so it walks on rather than back through the portal it arrived by), and
		// which of that chamber's spawn points it is walking to. 255 is "none":
		// a bot outside the dungeon has no chamber.
		BYTE bMonkeyChamber;
		BYTE bMonkeyPrevChamber;
		BYTE bMonkeySpot;
		BYTE bLongTermGoal;
		BYTE bCurrentAction;
		BYTE bLastStatusAction;
		BYTE bLastStatusGoal;
		BYTE bLastStatusTownPhase;
		BYTE bLastStatusParty;
		std::map<DWORD, DWORD> mapFailedLootVIDs;
		std::map<DWORD, DWORD> mapLootSeenSince;
		std::map<DWORD, DWORD> mapFailedStones;
		std::map<DWORD, DWORD> mapFailedTargets;
		std::map<DWORD, DWORD> mapBuffActiveUntil;
		std::vector<PIXEL_POSITION> vecMultiPullCenters;
		// Not in the initialiser list: it default-constructs empty, which is what
		// a bot that has not met anybody yet is.
		std::vector<TPlayerBotFriend> vecFriends;
		DWORD dwNextGuildCheckTime;
		// The last corpse this bot was credited for. The engine has no "you
		// killed it" hook, so a kill is read off a target that has gone from
		// alive to dead under the bot's own blow - and a bot standing over the
		// body must not be credited again on the next tick.
		DWORD dwLastKillCreditedVID;
		// CGuild's constructor adds the master through the database, so
		// GetGuild() is still NULL when the next upkeep pass comes round two
		// minutes later - and the bot would found a second guild under the
		// second name. This is the only thing that knows it already has one.
		bool bFoundedGuild;
		// Where this bot has been standing, since when, and whether it is
		// currently being walked off it. See ManagePlayerBotRelocation.
		// The fight in progress: which monster, since when, the lowest health it
		// has been brought to, and when that last improved. See
		// ShouldPlayerBotAbandonFight.
		// The walk to a portal: when it stopped making progress, and the closest
		// it has been. See MovePlayerBotToWorldPortal.
		// How long to keep taking the stall sign back after a stall closes, and
		// when the next repeat is due. See ManagePlayerBotShopLifetime.
		// The material errand: when this bot may next scan its map, and what it
		// set off after. See StartPlayerBotMaterialHunt.
		DWORD dwNextMaterialScanTime;
		DWORD dwMaterialHuntVnum;
		DWORD dwShopSignClearUntil;
		DWORD dwNextShopSignClearTime;
		DWORD dwPortalWalkSince;
		int iPortalWalkBest;
		DWORD dwFightProgressVID;
		// The attacker this bot is currently defending itself against, since when,
		// and from where. See PLAYERBOT_DEFENCE_EPISODE_TIME.
		DWORD dwDefenceTargetVID;
		DWORD dwDefenceEpisodeStart;
		DWORD dwNextCombatRecheckTime;
		// When this bot last finished a town errand, so the time it then takes
		// to leave the map can be measured rather than guessed at.
		DWORD dwErrandDoneTime;
		DWORD dwFightStartTime;
		DWORD dwFightLastProgressTime;
		int iLastFightHP;
		long lCampX;
		long lCampY;
		DWORD dwCampSince;
		DWORD dwRelocateSince;
		// Index of the last hub the wander chose on a hub map, so the choice is
		// logged when it changes rather than on every decision.
		WORD wHuntingHub;
		DWORD dwHubChosenTime;

		// Until when this bot is spending time in town rather than leaving the
		// moment its errand is done.
		DWORD dwTownLingerUntil;
		// The next counter this bot strolls to, and when to choose another.
		DWORD dwTownBrowseUntil;
		long lTownBrowseX;
		long lTownBrowseY;
		// When this bot first had a route refused for want of planning budget.
		// The audit asked for the queue age: a deferral that has stood for a
		// minute is a different thing from one that has stood for a second.
		DWORD dwFirstNavDeferTime;
		// Until when this bot may look for goods in Bokjung. Zero means "look in
		// Joan first": a shopper crosses to the quieter market, and only after
		// finding nothing there is Bokjung worth the walk for a while.
		DWORD dwMarketM2AllowedUntil;
		// A town errand that has not finished. Set when the watchdog or a failed
		// visit gives up on the attempt, cleared when a visit completes or the
		// need goes away. While it stands the bot is a customer, not a hunter.
		DWORD dwServiceRetryAt;
		DWORD dwServiceSince;
		// Where this bot means to go once the town is done with it, and since
		// when. Survives the visit and the watchdog: the audit's point was that
		// a reset may drop a stale route but not the intent behind it.
		DWORD dwDepartureSince;
		long lDepartureMap;
		bool bServicePending;
		// Why the monster this bot is fighting was allowed - the combat policy's
		// own Reason, kept so the line over the bot's head can say what it is
		// doing *for*, which is the whole point of the audit's status section.
		// Zero until the three-second re-check has run once.
		BYTE bLastCombatReason;

		// The luring course. The session id is what a log line is followed by
		// and what tells one course from the next; the party's own record of who
		// is luring for it lives in playerbot_lure.h, keyed by leader, because a
		// party may only have one lurer and a bot cannot see the other bots'
		// state from here.
		DWORD dwLureSessionId;
		DWORD dwLureStageTime;
		DWORD dwLureCourseTime;
		DWORD dwLureShotTime;
		DWORD dwLureNextTime;
		DWORD dwLureTargetVID;
		DWORD dwLureReceiverPID;
		// Where the party was standing when the course began. Everything is
		// measured from here: how far the Archer may go, and where it comes back
		// to - not the receiver's position, which moves during the fight.
		long lLureAnchorX;
		long lLureAnchorY;
		int iLureStartHPPercent;
		int iLureDelivered;
		int iLureChasing;
		BYTE bLureStage;
		BYTE bLureGroupsPlanned;
		BYTE bLureGroupsTagged;
		BYTE bLureBudget;
		BYTE bLureTagAttempts;
		BYTE bLureGoodCourses;
	};

	typedef std::map<DWORD, TPlayerBotAIState> TPlayerBotAIStateMap;

	// Every bot the manager has ever ticked, alive for the life of the process:
	// a bot that logs out keeps its plans, cooldowns and hobby. It lives here
	// rather than in the manager because the subsystems read it too - refining
	// asks a bot for its personality long before the tick reaches it.
	TPlayerBotAIStateMap s_mapPlayerBotAIStates;

	// Hunting stones right now: by role for life, or by expedition for half an
	// hour. Every rule that used to ask for the role asks this instead.
	bool IsPlayerBotMetinHunting(const TPlayerBotAIState& state, DWORD dwNow)
	{
		return state.bBotRole == BOT_ROLE_METIN_HUNTER ||
				(state.dwMetinExpeditionUntil != 0 && dwNow < state.dwMetinExpeditionUntil);
	}

	// The personality behind a pid, for the rules that get a character and not
	// a state - the travel gates, the stall's scoring. Steady adventurer when
	// the pid is not a bot's.
	BYTE GetPlayerBotPersonalityByPID(DWORD dwPID)
	{
		TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.find(dwPID);
		return it == s_mapPlayerBotAIStates.end()
				? (BYTE)BOT_PERSONALITY_STEADY_ADVENTURER : it->second.bPersonality;
	}

	// Changing goal or action is a state transition, so it lives with the
	// state. Every subsystem does it, and each one used to have to be
	// included after whichever file happened to hold these two.
	void SetPlayerBotGoal(LPCHARACTER ch, TPlayerBotAIState& state, BYTE goal, DWORD dwNow)
	{
		if (state.bLongTermGoal == goal)
			return;
		state.bLongTermGoal = goal;
		state.dwGoalStartedTime = dwNow;
		sys_log(0, "PLAYERBOT_GOAL: pid=%u name=%s goal=%u",
				ch ? ch->GetPlayerID() : 0, ch ? ch->GetName() : "?", (unsigned int)goal);
	}

	void SetPlayerBotAction(TPlayerBotAIState& state, BYTE action, DWORD dwNow)
	{
		if (state.bCurrentAction == action)
			return;
		state.bCurrentAction = action;
		state.dwActionChangedTime = dwNow;
	}
}

#endif
