#ifndef __INC_METIN_II_GAME_PLAYERBOT_MANAGER_H__
#define __INC_METIN_II_GAME_PLAYERBOT_MANAGER_H__

class CPlayerBotManager : public singleton<CPlayerBotManager>
{
	public:
		CPlayerBotManager();
		~CPlayerBotManager();

		bool	Spawn(DWORD dwPlayerID, BYTE bEmpire);
		size_t	SpawnRegistered(size_t count, BYTE bEmpire);
		void	SpawnPendingBatch(DWORD dwNow);
		bool	Despawn(DWORD dwPlayerID);

		void	OnPlayerLoaded(LPDESC d);
		void	OnLoadFailed(DWORD dwHandle);
		void	OnDescriptorDestroyed(LPDESC d);
		void	Update();
		// A player's shout, after the channel has it, and a whisper addressed to
		// a bot. Both from patch 0007 in input_main.cpp; playerbot_chat_trade.h
		// decides whether and which bot answers.
		void	OnPlayerShout(LPCHARACTER ch, const char* szText);
		void	OnPlayerWhisper(LPCHARACTER from, LPCHARACTER bot, const char* szText);

		bool	IsManaged(DWORD dwPlayerID) const;
		bool	IsRegistered(DWORD dwPlayerID);
		size_t	GetCount() const;

	private:
		typedef std::map<DWORD, LPDESC> TPlayerBotMap;
		typedef std::map<DWORD, DWORD> THandleToPlayerMap;
		typedef std::set<DWORD> TRegisteredPlayerBotSet;

		bool	LoadRegisteredBots();

		TPlayerBotMap		m_mapBots;
		THandleToPlayerMap	m_mapHandles;
		TRegisteredPlayerBotSet m_setRegisteredBots;
		// Spawns still to be sent, and when the next batch goes. Filled by
		// SpawnRegistered, drained by Update, see PLAYERBOT_SPAWN_WINDOW.
		std::deque<DWORD>	m_dequePendingSpawns;
		DWORD			m_dwNextSpawnBatchTime;
		size_t			m_uSpawnBatchSize;
		BYTE			m_bPendingSpawnEmpire;
		DWORD			m_dwSpawnWindowStarted;
		size_t			m_uSpawnWindowTotal;
		bool			m_bRegistryLoaded;
		bool			m_bRegistryAvailable;
};

#endif
