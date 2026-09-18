// The world's timed events, run by the core: a window in which the Moonlight
// chests drop (and outside which they do not drop at all), and windows of
// more experience, drop or yang over the world's own rates - on a weekly
// clock, or switched on from the panel for a number of minutes ("Aktywuj
// teraz"). The panel writes /opt/m2spool/playerbot_events.tsv; this re-reads
// it the way the weights are read, once every five seconds, judges every kind
// once a second with playerbot_events::Evaluate, and:
//
//  - gates the chest odds: g_iMoonlightChestPermille and the stone figure are
//    what playerbot_config.h read from the weights file (the sliders), kept
//    here as the wanted values and put to zero while no chest window is open.
//    Until 2.0.74 the gate shut only once a chest window was written, so a
//    world with no schedule dropped chests all the time, and the operator's
//    word was "usune domyslny drop, a wprowadze tylko jako event" (Tieru,
//    18 September): the event is the only way a chest drops now. Every core
//    gates its own, because CreateDropItem rolls locally - including a core
//    that hosts no bot, which the world clock (CPlayerBotManager::
//    StartWorldClock) runs this for; before it, such a core never gated and
//    dropped at the sliders' rate whatever the schedule said ("mimo
//    harmonogramu blaskow dropia one takze poza nim", NerrVoVy).
//  - moves the rate flags (mob_exp, mob_item, mob_gold and their _buyer
//    twins) through the DB core on ONE core only - the one hosting Joan, map
//    21, which is game1 under both layouts. Three cores each adding fifty
//    percent to a flag they all read would compound it. The base is kept in
//    a flag of its own (m2_event_exp_base ...) so a core restarted inside an
//    event starts from the base and not from the boosted number, and a rate
//    the operator moved during the event is left where they put it.
//  - speaks: BroadcastNotice at the start, every fifteen minutes and at the
//    end, from the leader only, because the notice goes to every core by P2P.
//  - writes playerbot_events_status.tsv beside playerbot_status.tsv for the
//    panel's "active until / next at".
//
// Nothing here changes what the bots do; a chest event is about drops.
namespace {
	const char* const PLAYERBOT_EVENTS_DEFAULT_PATH = "/opt/m2spool/playerbot_events.tsv";
	const char* const PLAYERBOT_EVENTS_STATUS_PATH = "playerbot_events_status.tsv";
	const DWORD PLAYERBOT_EVENTS_RELOAD_INTERVAL = 5000;
	const DWORD PLAYERBOT_EVENTS_CHECK_INTERVAL = 1000;
	const DWORD PLAYERBOT_EVENTS_REMINDER_INTERVAL = 15 * 60 * 1000;
	const DWORD PLAYERBOT_EVENTS_STATUS_INTERVAL = 60000;
	// Joan. game1 hosts it under split and under unified, so exactly one core
	// drives the flags and speaks.
	const long PLAYERBOT_EVENTS_LEADER_MAP = PLAYERBOT_MAP_CHUNJO_M1;

	std::vector<playerbot_events::Window> s_vecPlayerBotEvents;
	time_t s_tPlayerBotEventsMtime = 0;
	long s_lPlayerBotEventsSize = -1;
	DWORD s_dwPlayerBotEventsNextReload = 0;
	DWORD s_dwPlayerBotEventsNextCheck = 0;
	DWORD s_dwPlayerBotEventsNextStatus = 0;
	bool s_bPlayerBotEventsStatusDirty = true;
	bool s_bPlayerBotEventsFileSeen = false;

	struct TPlayerBotEventState {
		bool active = false;
		int value = 0;
		long until = 0;
		DWORD nextReminder = 0;
	};
	TPlayerBotEventState s_aPlayerBotEventState[playerbot_events::KIND_MAX];
	playerbot_events::Status s_aPlayerBotEventStatus[playerbot_events::KIND_MAX];

	// The sliders' figures, captured whenever playerbot_config.h has just
	// written them (the weights generation moved), so the gate can put zero
	// into the engine's variables and still give them back.
	int s_iPlayerBotChestWantedPermille = -1;
	int s_iPlayerBotChestStoneWantedPermille = -1;
	DWORD s_dwPlayerBotEventsWeightsGeneration = (DWORD)-1;
	bool s_bPlayerBotChestGateClosed = false;

	int GetPlayerBotChestWantedPermille(bool stone)
	{
		return stone ? s_iPlayerBotChestStoneWantedPermille : s_iPlayerBotChestWantedPermille;
	}

	bool IsPlayerBotChestGateClosed()
	{
		return s_bPlayerBotChestGateClosed;
	}

	const char* GetPlayerBotEventsPath()
	{
		const char* override_path = getenv("PLAYERBOT_EVENTS_FILE");
		if (override_path && *override_path)
			return override_path;
		return PLAYERBOT_EVENTS_DEFAULT_PATH;
	}

	void ReadPlayerBotEventsFile(const char* szPath)
	{
		s_vecPlayerBotEvents.clear();
		FILE* fp = fopen(szPath, "rb");
		if (!fp)
			return;
		char line[512];
		int ignored = 0;
		while (fgets(line, sizeof(line), fp))
		{
			playerbot_events::Window w;
			if (playerbot_events::ParseLine(line, w))
				s_vecPlayerBotEvents.push_back(w);
			else if (line[0] != '#' && line[0] != '\r' && line[0] != '\n')
				++ignored;
		}
		fclose(fp);
		sys_log(0, "PLAYERBOT_EVENT: %u event lines read from %s (%d ignored)",
				(unsigned int)s_vecPlayerBotEvents.size(), szPath, ignored);
	}

	void RefreshPlayerBotEvents(DWORD dwNow)
	{
		if (dwNow < s_dwPlayerBotEventsNextReload)
			return;
		s_dwPlayerBotEventsNextReload = dwNow + PLAYERBOT_EVENTS_RELOAD_INTERVAL;
		const char* szPath = GetPlayerBotEventsPath();
		struct stat st;
		if (stat(szPath, &st) != 0)
		{
			if (s_lPlayerBotEventsSize >= 0)
			{
				sys_log(0, "PLAYERBOT_EVENT: %s is gone, no events", szPath);
				s_vecPlayerBotEvents.clear();
				s_tPlayerBotEventsMtime = 0;
				s_lPlayerBotEventsSize = -1;
			}
			return;
		}
		if (st.st_mtime == s_tPlayerBotEventsMtime && (long)st.st_size == s_lPlayerBotEventsSize)
			return;
		s_tPlayerBotEventsMtime = st.st_mtime;
		s_lPlayerBotEventsSize = (long)st.st_size;
		s_bPlayerBotEventsFileSeen = true;
		ReadPlayerBotEventsFile(szPath);
	}

	bool IsPlayerBotEventLeader()
	{
		// Joan's core on the first channel: with a second channel on, its
		// game1 hosts map 21 too, and two leaders would say every notice twice.
		return g_bChannel == 1 &&
				SECTREE_MANAGER::instance().GetMap(PLAYERBOT_EVENTS_LEADER_MAP) != NULL;
	}

	const char* PlayerBotEventRateFlag(int kind, bool premium)
	{
		switch (kind)
		{
			case playerbot_events::KIND_EXP: return premium ? "mob_exp_buyer" : "mob_exp";
			case playerbot_events::KIND_DROP: return premium ? "mob_item_buyer" : "mob_item";
			case playerbot_events::KIND_YANG: return premium ? "mob_gold_buyer" : "mob_gold";
		}
		return "";
	}

	const char* PlayerBotEventBaseFlag(int kind, bool premium)
	{
		switch (kind)
		{
			case playerbot_events::KIND_EXP: return premium ? "m2_event_exp_base_buyer" : "m2_event_exp_base";
			case playerbot_events::KIND_DROP: return premium ? "m2_event_drop_base_buyer" : "m2_event_drop_base";
			case playerbot_events::KIND_YANG: return premium ? "m2_event_yang_base_buyer" : "m2_event_yang_base";
		}
		return "";
	}

	// Player-visible, so Polish and ASCII-only like every bot string.
	const char* PlayerBotEventRateWord(int kind)
	{
		switch (kind)
		{
			case playerbot_events::KIND_EXP: return "doswiadczenia";
			case playerbot_events::KIND_DROP: return "szansy na drop";
			case playerbot_events::KIND_YANG: return "yang z potworow";
		}
		return "";
	}

	void FormatPlayerBotEventClock(long until, char* out, size_t len)
	{
		time_t t = (time_t)until;
		struct tm local;
		localtime_r(&t, &local);
		snprintf(out, len, "%02d:%02d", local.tm_hour, local.tm_min);
	}

	enum EPlayerBotEventPhase { EVENT_PHASE_START, EVENT_PHASE_REMINDER, EVENT_PHASE_END };

	void AnnouncePlayerBotEvent(int kind, int value, long until, EPlayerBotEventPhase phase)
	{
		char body[128];
		if (kind == playerbot_events::KIND_CHEST)
			snprintf(body, sizeof(body), "Szkatulki Blasku Ksiezyca dropia z potworow i metinow");
		else
			snprintf(body, sizeof(body), "+%d%% %s", value, PlayerBotEventRateWord(kind));
		char text[256];
		if (phase == EVENT_PHASE_END)
		{
			if (kind == playerbot_events::KIND_CHEST)
				snprintf(text, sizeof(text), "Event zakonczony: Szkatulki Blasku Ksiezyca juz nie dropia.");
			else
				snprintf(text, sizeof(text), "Event zakonczony: %s wraca do normy.", PlayerBotEventRateWord(kind));
		}
		else
		{
			char when[16];
			FormatPlayerBotEventClock(until, when, sizeof(when));
			snprintf(text, sizeof(text), "%s: %s do %s!",
					phase == EVENT_PHASE_START ? "Event" : "Trwa event", body, when);
		}
		BroadcastNotice(text);
		sys_log(0, "PLAYERBOT_EVENT: notice \"%s\"", text);
	}

	// The world's rate times (100 + value) percent, from a base remembered in
	// a flag of its own; asked again after a restart it finds that base and
	// arrives at the same boosted number, which is what makes this safe to
	// repeat.
	void BeginPlayerBotRateEvent(int kind, int value)
	{
		quest::CQuestManager& q = quest::CQuestManager::instance();
		for (int premium = 0; premium < 2; ++premium)
		{
			const std::string flag = PlayerBotEventRateFlag(kind, premium != 0);
			const std::string baseFlag = PlayerBotEventBaseFlag(kind, premium != 0);
			int base = q.GetEventFlag(baseFlag);
			if (base <= 0)
			{
				base = q.GetEventFlag(flag);
				if (base <= 0)
					base = 100;
				q.RequestSetEventFlag(baseFlag, base);
			}
			const int boosted = (int)((long long)base * (100 + value) / 100);
			q.RequestSetEventFlag(flag, boosted);
			sys_log(0, "PLAYERBOT_EVENT: %s begins: %s %d -> %d (+%d%%)",
					playerbot_events::KindName(kind), flag.c_str(), base, boosted, value);
		}
	}

	void EndPlayerBotRateEvent(int kind, int value)
	{
		quest::CQuestManager& q = quest::CQuestManager::instance();
		for (int premium = 0; premium < 2; ++premium)
		{
			const std::string flag = PlayerBotEventRateFlag(kind, premium != 0);
			const std::string baseFlag = PlayerBotEventBaseFlag(kind, premium != 0);
			const int base = q.GetEventFlag(baseFlag);
			if (base <= 0)
				continue;
			const int boosted = (int)((long long)base * (100 + value) / 100);
			const int current = q.GetEventFlag(flag);
			if (current == boosted)
			{
				q.RequestSetEventFlag(flag, base);
				sys_log(0, "PLAYERBOT_EVENT: %s ends: %s %d -> %d",
						playerbot_events::KindName(kind), flag.c_str(), boosted, base);
			}
			else
				sys_log(0, "PLAYERBOT_EVENT: %s ends: %s left at %d (moved during the event; base was %d)",
						playerbot_events::KindName(kind), flag.c_str(), current, base);
			q.RequestSetEventFlag(baseFlag, 0);
		}
	}

	void ApplyPlayerBotChestGate(bool closed)
	{
		const DWORD generation = GetPlayerBotWeightsGeneration();
		if (generation != s_dwPlayerBotEventsWeightsGeneration)
		{
			s_dwPlayerBotEventsWeightsGeneration = generation;
			// The sliders' figure as parsed (playerbot_config.h), never the
			// engine's variable: the parse no longer writes that while this
			// gate is shut, so reading it back here would capture the zero.
			s_iPlayerBotChestWantedPermille = GetPlayerBotChestConfigPermille(false);
			s_iPlayerBotChestStoneWantedPermille = GetPlayerBotChestConfigPermille(true);
		}
		if (closed != s_bPlayerBotChestGateClosed)
		{
			s_bPlayerBotChestGateClosed = closed;
			sys_log(0, "PLAYERBOT_EVENT: moonlight chests %s (kill %d, stone %d permille)",
					closed ? "wait for a chest event" : "drop",
					s_iPlayerBotChestWantedPermille, s_iPlayerBotChestStoneWantedPermille);
		}
		g_iMoonlightChestPermille = closed ? 0 : s_iPlayerBotChestWantedPermille;
		g_iMoonlightChestStonePermille = closed ? 0 : s_iPlayerBotChestStoneWantedPermille;
	}

	void WritePlayerBotEventsStatus()
	{
		const char* tempPath = "playerbot_events_status.tsv.tmp";
		FILE* fp = fopen(tempPath, "wb");
		if (!fp)
			return;
		fprintf(fp, "kind\tscheduled\tactive\tvalue\tuntil\tnext_start\tnext_value\twritten\n");
		const long now = (long)time(NULL);
		for (int kind = 0; kind < playerbot_events::KIND_MAX; ++kind)
		{
			const playerbot_events::Status& st = s_aPlayerBotEventStatus[kind];
			fprintf(fp, "%s\t%d\t%d\t%d\t%ld\t%ld\t%d\t%ld\n", playerbot_events::KindName(kind),
					st.scheduled ? 1 : 0, st.active ? 1 : 0, st.value, st.until, st.nextStart,
					st.nextValue, now);
		}
		fclose(fp);
		rename(tempPath, PLAYERBOT_EVENTS_STATUS_PATH);
	}

	void ManagePlayerBotEvents(DWORD dwNow)
	{
		RefreshPlayerBotEvents(dwNow);
		if (dwNow >= s_dwPlayerBotEventsNextCheck)
		{
			s_dwPlayerBotEventsNextCheck = dwNow + PLAYERBOT_EVENTS_CHECK_INTERVAL;
			const time_t now = time(NULL);
			struct tm local;
			localtime_r(&now, &local);
			const int dayIndex = (local.tm_wday + 6) % 7;
			const int minute = local.tm_hour * 60 + local.tm_min;
			const bool leader = IsPlayerBotEventLeader();
			for (int kind = 0; kind < playerbot_events::KIND_MAX; ++kind)
			{
				const playerbot_events::Status st = playerbot_events::Evaluate(
						s_vecPlayerBotEvents, kind, (long)now, dayIndex, minute);
				playerbot_events::Status& shown = s_aPlayerBotEventStatus[kind];
				if (st.active != shown.active || st.until != shown.until ||
						st.nextStart != shown.nextStart || st.scheduled != shown.scheduled ||
						st.value != shown.value)
					s_bPlayerBotEventsStatusDirty = true;
				shown = st;
				TPlayerBotEventState& state = s_aPlayerBotEventState[kind];
				if (st.active && !state.active)
				{
					state.active = true;
					state.value = st.value;
					state.until = st.until;
					state.nextReminder = dwNow + PLAYERBOT_EVENTS_REMINDER_INTERVAL;
					sys_log(0, "PLAYERBOT_EVENT: %s starts value=%d until=%ld leader=%d",
							playerbot_events::KindName(kind), st.value, st.until, leader ? 1 : 0);
					if (leader)
					{
						if (kind != playerbot_events::KIND_CHEST)
							BeginPlayerBotRateEvent(kind, st.value);
						AnnouncePlayerBotEvent(kind, st.value, st.until, EVENT_PHASE_START);
					}
				}
				else if (!st.active && state.active)
				{
					sys_log(0, "PLAYERBOT_EVENT: %s ends leader=%d", playerbot_events::KindName(kind), leader ? 1 : 0);
					if (leader)
					{
						if (kind != playerbot_events::KIND_CHEST)
							EndPlayerBotRateEvent(kind, state.value);
						AnnouncePlayerBotEvent(kind, state.value, 0, EVENT_PHASE_END);
					}
					state.active = false;
				}
				else if (st.active)
				{
					// A second window or an "activate now" with another figure
					// while one runs: the rate is re-based on the same base.
					if (st.value != state.value && kind != playerbot_events::KIND_CHEST && leader)
					{
						EndPlayerBotRateEvent(kind, state.value);
						BeginPlayerBotRateEvent(kind, st.value);
					}
					state.value = st.value;
					state.until = st.until;
					if (leader && dwNow >= state.nextReminder)
					{
						state.nextReminder = dwNow + PLAYERBOT_EVENTS_REMINDER_INTERVAL;
						AnnouncePlayerBotEvent(kind, st.value, st.until, EVENT_PHASE_REMINDER);
					}
				}
			}
		}
		// Shut whenever no chest event runs, schedule or no schedule.
		const playerbot_events::Status& chest = s_aPlayerBotEventStatus[playerbot_events::KIND_CHEST];
		ApplyPlayerBotChestGate(!chest.active);
		if (s_bPlayerBotEventsStatusDirty || dwNow >= s_dwPlayerBotEventsNextStatus)
		{
			s_bPlayerBotEventsStatusDirty = false;
			s_dwPlayerBotEventsNextStatus = dwNow + PLAYERBOT_EVENTS_STATUS_INTERVAL;
			WritePlayerBotEventsStatus();
		}
	}
}
