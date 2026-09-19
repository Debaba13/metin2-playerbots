// Unit tests for playerbot_persona_rules.h - Iwakura's personality system as
// pure policy.
//
//   docker run --rm -v "$(pwd -W)":/w -w /w gcc:13 bash -c
//     "g++ -Wall -Wextra -o /tmp/t tests/playerbot_persona_rules_test.cpp && /tmp/t"
#include <cassert>
#include <cstdio>

#include "../linux-port/overlays/playerbot/src/game/src/playerbot_persona_rules.h"

using namespace playerbot_persona;

namespace
{
	const uint32_t MIN = 60u * 1000u;
	const uint32_t HOUR = 60u * MIN;

	// Advance a mood in one-minute steps, the way the engine's ticks add up.
	int Play(TMood& m, uint32_t ms, bool hunting, uint32_t roll)
	{
		int events = 0;
		while (ms > 0)
		{
			const uint32_t step = ms > MIN ? MIN : ms;
			events |= AdvanceMood(m, step, hunting, roll);
			ms -= step;
		}
		return events;
	}
}

int main()
{
	// --- moods -------------------------------------------------------------
	{
		// A good drop lifts the mood one level, and not past the top.
		TMood m;
		m.mood = MOOD_SLABY;
		assert(OnValuableDrop(m) && m.mood == MOOD_NORMALNY);
		assert(OnValuableDrop(m) && m.mood == MOOD_BARDZO_DOBRY);
		assert(!OnValuableDrop(m) && m.mood == MOOD_BARDZO_DOBRY);
	}
	{
		// Thirty minutes of hunting with nothing good: one level down. Time
		// in town does not count towards it.
		TMood m;
		m.mood = MOOD_BARDZO_DOBRY;
		assert((Play(m, 29 * MIN, true, 1) & MOOD_EVENT_DROUGHT) == 0);
		assert(m.mood == MOOD_BARDZO_DOBRY);
		// (Two hours, not more: the six-hour rotation would roll the mood
		// again in the middle of the sequence.)
		assert((Play(m, 2 * HOUR, false, 1) & MOOD_EVENT_DROUGHT) == 0);
		assert(m.mood == MOOD_BARDZO_DOBRY);
		assert(Play(m, 1 * MIN, true, 1) & MOOD_EVENT_DROUGHT);
		assert(m.mood == MOOD_NORMALNY);
		// ...and the clock starts again: thirty more minutes for the next step.
		assert((Play(m, 29 * MIN, true, 1) & MOOD_EVENT_DROUGHT) == 0);
		assert(Play(m, 1 * MIN, true, 1) & MOOD_EVENT_DROUGHT);
		assert(m.mood == MOOD_SLABY);
		// SLABY is the floor.
		Play(m, 30 * MIN, true, 1);
		assert(m.mood == MOOD_SLABY);
		// A good drop resets the drought clock.
		TMood n;
		Play(n, 25 * MIN, true, 1);
		OnValuableDrop(n);
		assert(n.droughtMs == 0 && n.mood == MOOD_BARDZO_DOBRY);
	}
	{
		// Every six hours of play the mood is rolled again.
		TMood m;
		m.mood = MOOD_SLABY;
		assert((Play(m, 6 * HOUR - MIN, false, 2) & MOOD_EVENT_ROTATED) == 0);
		assert(Play(m, MIN, false, 2) & MOOD_EVENT_ROTATED);
		assert(m.mood == RollMood(2) && m.playedMs == 0);
		// The three are equally likely.
		int seen[MOOD_COUNT] = { 0, 0, 0 };
		for (uint32_t r = 0; r < 300; ++r)
			++seen[RollMood(r)];
		assert(seen[0] == 100 && seen[1] == 100 && seen[2] == 100);
	}
	{
		// Euphoria: BARDZO DOBRY for three hours and nothing moves it.
		TMood m;
		m.mood = MOOD_SLABY;
		OnEuphoria(m);
		assert(m.mood == MOOD_BARDZO_DOBRY && IsMoodLocked(m));
		assert(!OnCapitulation(m) && m.mood == MOOD_BARDZO_DOBRY);
		Play(m, 3 * HOUR - MIN, true, 0);
		assert(m.mood == MOOD_BARDZO_DOBRY && IsMoodLocked(m));
		// The lock ends, and only then may the drought clock start.
		assert(Play(m, MIN, true, 0) & MOOD_EVENT_UNLOCKED);
		assert(!IsMoodLocked(m) && m.mood == MOOD_BARDZO_DOBRY);
		Play(m, 30 * MIN, true, 0);
		assert(m.mood == MOOD_NORMALNY);
	}
	{
		// A rotation that falls under a lock waits for the lock, then happens.
		TMood m;
		Play(m, 5 * HOUR, false, 0);
		OnEuphoria(m);
		assert((Play(m, 2 * HOUR, false, 0) & MOOD_EVENT_ROTATED) == 0);
		assert(m.mood == MOOD_BARDZO_DOBRY);
		assert(Play(m, HOUR, false, 0) & MOOD_EVENT_ROTATED);
		assert(m.mood == RollMood(0));
	}
	{
		// The capitulation: SLABY for forty-five minutes, whatever drops.
		TMood m;
		m.mood = MOOD_BARDZO_DOBRY;
		assert(OnCapitulation(m) && m.mood == MOOD_SLABY);
		assert(!OnValuableDrop(m) && m.mood == MOOD_SLABY);
		Play(m, 44 * MIN, true, 1);
		assert(m.mood == MOOD_SLABY && IsMoodLocked(m));
		Play(m, MIN, true, 1);
		assert(!IsMoodLocked(m));
		assert(OnValuableDrop(m) && m.mood == MOOD_NORMALNY);
		// A second euphoria renews its three hours.
		TMood n;
		OnEuphoria(n);
		Play(n, 2 * HOUR, false, 0);
		OnEuphoria(n);
		Play(n, 2 * HOUR, false, 0);
		assert(IsMoodLocked(n));
	}
	{
		// A refine to +8 or +9 that fails costs a level; one to +7 does not.
		TMood m;
		m.mood = MOOD_BARDZO_DOBRY;
		assert(!OnBigRefineFailure(m, 7) && m.mood == MOOD_BARDZO_DOBRY);
		assert(OnBigRefineFailure(m, 8) && m.mood == MOOD_NORMALNY);
		assert(OnBigRefineFailure(m, 9) && m.mood == MOOD_SLABY);
		// SLABY is the floor.
		assert(!OnBigRefineFailure(m, 9) && m.mood == MOOD_SLABY);
		// The drought clock is its own business and is left where it was.
		TMood d;
		Play(d, 20 * MIN, true, 0);
		assert(OnBigRefineFailure(d, 8) && d.mood == MOOD_SLABY && d.droughtMs == 20 * MIN);
		// Under euphoria nothing moves - a burn right after a +9 included.
		TMood e;
		OnEuphoria(e);
		assert(!OnBigRefineFailure(e, 9) && e.mood == MOOD_BARDZO_DOBRY);
		// Nor under a capitulation, which is the bottom anyway.
		TMood c;
		c.mood = MOOD_NORMALNY;
		assert(OnCapitulation(c));
		assert(!OnBigRefineFailure(c, 8) && c.mood == MOOD_SLABY);
	}
	{
		// In a party or a dungeon the bot plays NORMALNY whatever it feels.
		TMood m;
		m.mood = MOOD_SLABY;
		assert(EffectiveMood(m, true) == MOOD_NORMALNY);
		assert(EffectiveMood(m, false) == MOOD_SLABY);
		m.mood = MOOD_BARDZO_DOBRY;
		assert(EffectiveMood(m, true) == MOOD_NORMALNY);
		// A value from a damaged flag reads as the middle.
		assert(ClampMood(7) == MOOD_NORMALNY && ClampMood(0) == MOOD_SLABY);
	}
	{
		// SLABY's habits stay inside the document's ranges.
		for (uint32_t r = 0; r < 100000; r += 7)
		{
			const uint32_t p = PauseDuration(r), i = AfkInterval(r), d = AfkDuration(r);
			assert(p >= 2000 && p <= 8000);
			assert(i >= 10 * MIN && i <= 30 * MIN);
			assert(d >= 2 * MIN && d <= 5 * MIN);
		}
	}

	// --- the Grinder's tiers --------------------------------------------------
	{
		assert(GrinderTierFor(1) == 0 && GrinderTierFor(9) == 0);
		assert(GrinderTierFor(10) == 1 && GrinderTierFor(18) == 1);
		assert(GrinderTierFor(19) == 2 && GrinderTierFor(25) == 2);
		assert(GrinderTierFor(26) == 3 && GrinderTierFor(35) == 3);
		assert(GrinderTierFor(36) == 5 && GrinderTierFor(50) == 5);
		assert(GrinderTierFor(51) == 7 && GrinderTierFor(65) == 7);
		assert(GrinderTierFor(66) == GRINDER_TIER_BEYOND && GrinderTierFor(120) == GRINDER_TIER_BEYOND);

		for (uint32_t pid = 4; pid < 2504; ++pid)
		{
			// Nothing held under ten.
			assert(GrinderLockFor(9, pid) == 0);
			// The first village holds at fifteen; M3 at twenty-three.
			assert(GrinderLockFor(10, pid) == 15 && GrinderLockFor(14, pid) == 15);
			assert(GrinderLockFor(19, pid) == 23 && GrinderLockFor(23, pid) == 23);
			// A bot already past its tier's lock holds where it stands.
			assert(GrinderLockFor(17, pid) == 17 && GrinderLockFor(25, pid) == 25);
			// The second village holds between thirty and thirty-five.
			const uint8_t m2 = GrinderLockFor(26, pid);
			assert(m2 >= 30 && m2 <= 35);
			// The valley and the desert between forty and forty-eight.
			const uint8_t valley = GrinderLockFor(36, pid);
			assert(valley >= 40 && valley <= 48);
			// Sohan between fifty-five and sixty-two.
			const uint8_t sohan = GrinderLockFor(51, pid);
			assert(sohan >= 55 && sohan <= 62);
			// Past the last tier a Grinder holds where it is.
			assert(GrinderLockFor(70, pid) == 70);
			// The same pid always gets the same lock - every core asks.
			assert(GrinderLockFor(26, pid) == m2);
		}
		// The spread uses the whole range.
		bool seen30 = false, seen35 = false;
		for (uint32_t pid = 4; pid < 2504; ++pid)
		{
			seen30 = seen30 || GrinderLockFor(26, pid) == 30;
			seen35 = seen35 || GrinderLockFor(26, pid) == 35;
		}
		assert(seen30 && seen35);
	}

	// --- the Law of Advancement -----------------------------------------------
	{
		TAdvanceGear g;
		g.level = 15;
		g.weapon = TGearPiece(7, 10);
		g.armour = TGearPiece(6, 9);
		g.shield = TGearPiece(6, 1);
		assert(AwansGaps(g) == 0);
		// Each piece one grade short is its own gap.
		g.weapon.plus = 6;
		assert(AwansGaps(g) == AWANS_GAP_WEAPON);
		g.weapon.plus = 7;
		g.armour.plus = 5;
		g.shield.plus = 5;
		assert(AwansGaps(g) == (AWANS_GAP_ARMOUR | AWANS_GAP_SHIELD));
		// A bow or a two-hander wants no shield.
		g.armour.plus = 6;
		g.wantsShield = false;
		g.shield = TGearPiece();
		assert(AwansGaps(g) == 0);
		// Nothing worn is a gap.
		g.wantsShield = true;
		assert(AwansGaps(g) == AWANS_GAP_SHIELD);
		g.weapon = TGearPiece();
		assert(AwansGaps(g) & AWANS_GAP_WEAPON);
	}
	{
		// "Zgodnie z obowiazujaca Tierlista": a +9 from level one is no weapon
		// and no armour for level forty. Twenty levels is the window; the
		// special weapons of level thirty count for thirty. A shield is asked
		// for its +6 alone (AWANS_SHIELD_ANY_LEVEL: the world has no others).
		TAdvanceGear g;
		g.level = 40;
		g.weapon = TGearPiece(9, 1);
		g.armour = TGearPiece(9, 1);
		g.shield = TGearPiece(9, 1);
		assert(AwansGaps(g) == (AWANS_GAP_WEAPON | AWANS_GAP_ARMOUR));
		g.weapon = TGearPiece(7, 20);
		g.armour = TGearPiece(6, 26);
		g.shield = TGearPiece(6, 0);
		assert(AwansGaps(g) == 0);
		// The window is inclusive: a weapon of 20 still counts at 40.
		g.level = 41;
		assert(AwansGaps(g) == AWANS_GAP_WEAPON);
		g.weapon = TGearPiece(7, 30, true);
		g.level = 60;
		g.armour = TGearPiece(6, 48);
		assert(AwansGaps(g) == 0);
		g.level = 61;
		assert(AwansGaps(g) == AWANS_GAP_WEAPON);
		g.level = 69;
		assert(AwansGaps(g) == (AWANS_GAP_WEAPON | AWANS_GAP_ARMOUR));
		// A level-0 shield at +6 is still a shield at level seventy; one at +5 is not.
		g.level = 70;
		g.weapon = TGearPiece(7, 55);
		g.armour = TGearPiece(6, 54);
		assert(AwansGaps(g) == 0);
		g.shield.plus = 5;
		assert(AwansGaps(g) == AWANS_GAP_SHIELD);
	}
	{
		// M3's door: weapon +6 and armour +5, or the weapon alone for the
		// Mental Warrior.
		TAdvanceGear g;
		g.level = 20;
		g.weapon = TGearPiece(6, 15);
		g.armour = TGearPiece(5, 18);
		assert(MeetsM3Survival(g, false));
		g.armour.plus = 4;
		assert(!MeetsM3Survival(g, false));
		assert(MeetsM3Survival(g, true));
		g.armour = TGearPiece();
		assert(MeetsM3Survival(g, true));
		g.weapon.plus = 5;
		assert(!MeetsM3Survival(g, true));
	}
	{
		// Three deaths to monsters in half an hour is a Conqueror out of its
		// depth; three spread over more than that is bad luck.
		TDeathWindow w;
		assert(!NoteDeath(w));
		AdvanceDeathWindow(w, 10 * MIN);
		assert(!NoteDeath(w));
		AdvanceDeathWindow(w, 10 * MIN);
		assert(NoteDeath(w));
		TDeathWindow s;
		NoteDeath(s);
		AdvanceDeathWindow(s, 20 * MIN);
		NoteDeath(s);
		AdvanceDeathWindow(s, 15 * MIN);
		assert(!NoteDeath(s));
		// The window keeps only the last three.
		for (int i = 0; i < 10; ++i)
			NoteDeath(s);
		assert(s.count == WEAK_DEATHS);
	}

	// --- the gambler -----------------------------------------------------------
	{
		int seven = 0, eight = 0, nine = 0;
		for (uint32_t r = 0; r < 1000; ++r)
		{
			const uint8_t t = RollGambleTarget(r);
			seven += t == 7;
			eight += t == 8;
			nine += t == 9;
		}
		assert(seven == 600 && eight == 300 && nine == 100);

		// Up to +7 at the anvil, +8 and +9 under a scroll, then stop.
		assert(NextGambleStep(0, 7, false) == GAMBLE_STEP_PLAIN);
		assert(NextGambleStep(6, 7, false) == GAMBLE_STEP_PLAIN);
		assert(NextGambleStep(7, 7, false) == GAMBLE_STEP_DONE);
		assert(NextGambleStep(7, 8, false) == GAMBLE_STEP_SCROLL);
		assert(NextGambleStep(8, 8, false) == GAMBLE_STEP_DONE);
		assert(NextGambleStep(8, 9, false) == GAMBLE_STEP_SCROLL);
		assert(NextGambleStep(9, 9, false) == GAMBLE_STEP_DONE);
		// A scroll fails on the way to +8: back to +7 at the anvil, then sold.
		assert(NextGambleStep(6, 8, true) == GAMBLE_STEP_PLAIN);
		assert(NextGambleStep(7, 8, true) == GAMBLE_STEP_DONE);
		// On the way to +9 a failure drops it to +7: accepted, sold at +7.
		assert(NextGambleStep(7, 9, true) == GAMBLE_STEP_DONE);

		// Forty percent of what it came with, less what it has spent.
		assert(BudgetLeft(10000000, GAMBLE_BUDGET_PERCENT, 0) == 4000000);
		assert(BudgetLeft(10000000, GAMBLE_BUDGET_PERCENT, 3999999) == 1);
		assert(BudgetLeft(10000000, GAMBLE_BUDGET_PERCENT, 5000000) == 0);
		assert(BudgetLeft(10000000, PERFECT_BUDGET_PERCENT, 0) == 8000000);
		assert(BudgetLeft(0, GAMBLE_BUDGET_PERCENT, 0) == 0);
	}

	// --- the stone hunter ---------------------------------------------------------
	{
		// Ten levels either way, both ends included.
		assert(InPogromcaBand(40, 50) && InPogromcaBand(40, 30) && InPogromcaBand(40, 40));
		assert(!InPogromcaBand(40, 51) && !InPogromcaBand(40, 29));
		// Three bots of its own kingdom on the stone are enough.
		assert(!IsPogromcaCrowded(2) && IsPogromcaCrowded(3) && IsPogromcaCrowded(7));
		// Under thirty-five percent it turns on the pack; not at thirty-five.
		assert(IsPogromcaRetreat(34, 100) && !IsPogromcaRetreat(35, 100));
		assert(!IsPogromcaRetreat(0, 0));
		assert(IsPogromcaRetreat(349999, 1000000) && !IsPogromcaRetreat(350000, 1000000));
		// "Wiecej niz 6 razy": the seventh death gives the stone up.
		assert(!PogromcaGivesUp(6) && PogromcaGivesUp(7));
	}

	// --- the Anti-PK protocol -----------------------------------------------------
	{
		// Five deaths in fifteen minutes on the same ground capitulate.
		TPkDeaths w;
		const uint32_t t0 = 1000u;
		assert(!NotePkDeath(w, t0, 64, 100000, 100000));
		assert(!NotePkDeath(w, t0 + 2 * MIN, 64, 101000, 100500));
		assert(!NotePkDeath(w, t0 + 4 * MIN, 64, 99000, 102000));
		assert(!NotePkDeath(w, t0 + 6 * MIN, 64, 100000, 100000));
		assert(NotePkDeath(w, t0 + 8 * MIN, 64, 100200, 99800));
		// ...and the window starts afresh after it.
		assert(w.count == 0);
		assert(!NotePkDeath(w, t0 + 9 * MIN, 64, 100000, 100000));

		// Deaths older than fifteen minutes do not count - exactly fifteen is
		// already too old.
		TPkDeaths old;
		for (uint32_t i = 0; i < 4; ++i)
			assert(!NotePkDeath(old, t0 + i * MIN, 64, 100000, 100000));
		assert(!NotePkDeath(old, t0 + 20 * MIN, 64, 100000, 100000));
		assert(old.count == 1);
		TPkDeaths edge;
		assert(!NotePkDeath(edge, t0, 64, 0, 0));
		assert(!NotePkDeath(edge, t0 + 15 * MIN, 64, 0, 0));
		assert(edge.count == 1);

		// Somewhere else is not the same spot, nor another map.
		TPkDeaths spread;
		assert(!NotePkDeath(spread, t0, 64, 100000, 100000));
		assert(!NotePkDeath(spread, t0 + MIN, 64, 100000, 100000));
		assert(!NotePkDeath(spread, t0 + 2 * MIN, 63, 100000, 100000));
		assert(!NotePkDeath(spread, t0 + 3 * MIN, 64, 110000, 100000));
		assert(!NotePkDeath(spread, t0 + 4 * MIN, 64, 100000, 100000));
		// The two away from here are remembered and are not near: four so far.
		assert(!NotePkDeath(spread, t0 + 5 * MIN, 64, 100000, 100000));
		// And the fifth near one capitulates, the two between them notwithstanding.
		assert(NotePkDeath(spread, t0 + 6 * MIN, 64, 100000, 100000));

		// The clock may wrap under the window.
		TPkDeaths wrap;
		const uint32_t late = 0xFFFFFFFFu - MIN;
		assert(!NotePkDeath(wrap, late, 64, 0, 0));
		assert(!NotePkDeath(wrap, late + 2 * MIN, 64, 0, 0));
		assert(wrap.count == 2);

		// Eight in a thousand, from level thirty, never in a party.
		assert(RollCapitulationFishing(79, 30, false) && !RollCapitulationFishing(80, 30, false));
		assert(!RollCapitulationFishing(0, 29, false) && !RollCapitulationFishing(0, 45, true));
		int hits = 0;
		for (uint32_t r = 0; r < 1000; ++r)
			hits += RollCapitulationFishing(r, 50, false) ? 1 : 0;
		assert(hits == 80);
	}

	// --- which personality claims the bot ----------------------------------------
	{
		TPersonaSignals s;
		assert(DecidePersona(s) == PERSONA_GRINDER);
		s.advanced = true;
		assert(DecidePersona(s) == PERSONA_ZDOBYWCA);
		s.trading = true;
		assert(DecidePersona(s) == PERSONA_HANDLARZ);
		s.perfecting = true;
		assert(DecidePersona(s) == PERSONA_PERFEKCJONISTA);
		s.gambling = true;
		assert(DecidePersona(s) == PERSONA_HAZARDZISTA);
		s.stoneFight = true;
		assert(DecidePersona(s) == PERSONA_POGROMCA);
		s.mining = true;
		assert(DecidePersona(s) == PERSONA_GORNIK);
		s.fishing = true;
		assert(DecidePersona(s) == PERSONA_RYBAK);
		s.inParty = true;
		assert(DecidePersona(s) == PERSONA_TOWARZYSZ);
		s.mercenary = true;
		assert(DecidePersona(s) == PERSONA_NAJEMNIK);
		// The ids the status file and the client carry.
		assert(PERSONA_GRINDER == 0 && PERSONA_TOWARZYSZ == 9 && PERSONA_COUNT == 10);
		assert(PERSONA_TITLE_BASE + PERSONA_TOWARZYSZ == 109);
	}

	std::printf("playerbot_persona_rules: all tests passed\n");
	return 0;
}
