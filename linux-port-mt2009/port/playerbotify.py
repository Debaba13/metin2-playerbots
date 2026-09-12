# -*- coding: utf-8 -*-
"""Wire the playerbot overlay into a staged mt2009 (martysama0134 r41023) tree.

Usage:  python playerbotify.py <staged server dir>   (after linuxify.py)

This is linux-port/overlays/playerbot/patches/0001..0015 (0009, the F9 GM
panel, deliberately left out) re-expressed for the mt2009 engine as exact-string
edits that keep each file's own line endings. The hunks are the r40250 ones;
where the fork's text differs the anchor is the fork's, and where the fork has
no such code (OpenMyShop lives in char_shop.cpp here, speed_server is gone) the
edit says so beside it. Idempotent: applied once, found already applied, or it
fails naming the anchor it could not find.

The overlay sources themselves (playerbot_*.h/.cpp) are copied, not edited;
game/src/Makefile compiles $(wildcard *.cpp), so nothing lists them.
"""
import glob
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.normpath(os.path.join(
    HERE, '..', '..', 'linux-port', 'overlays', 'playerbot', 'src', 'game', 'src'))


def read(path):
    with io.open(path, 'rb') as f:
        return f.read()


def write(path, data):
    with io.open(path, 'wb') as f:
        f.write(data)


def eol_of(data):
    return b'\r\n' if b'\r\n' in data else b'\n'


def edit(path, old, new, marker=None):
    data = read(path)
    eol = eol_of(data)
    old_b = old.encode('latin-1').replace(b'\n', eol)
    new_b = new.encode('latin-1').replace(b'\n', eol)
    mark_b = (marker or new).encode('latin-1').replace(b'\n', eol)
    if mark_b in data:
        print('  already: %s' % os.path.relpath(path))
        return
    n = data.count(old_b)
    if n != 1:
        raise SystemExit('playerbotify: anchor found %d times in %s:\n%s' % (n, path, old))
    write(path, data.replace(old_b, new_b, 1))
    print('  edited:  %s' % os.path.relpath(path))


def copy_overlay(game):
    n = 0
    for src in glob.glob(os.path.join(OVERLAY, 'playerbot_*')):
        dst = os.path.join(game, os.path.basename(src))
        if not os.path.isfile(dst) or read(src) != read(dst):
            shutil.copyfile(src, dst)
            n += 1
    print('  overlay: %d file(s) copied into %s' % (n, os.path.relpath(game)))


def main(root):
    common = os.path.join(root, 'common')
    db = os.path.join(root, 'db', 'src')
    game = os.path.join(root, 'game', 'src')

    copy_overlay(game)

    # The bots' chest pass asks a special item group whether every line comes
    # at once (PCT) or one does, to reserve room for the whole set before the
    # chest is used; the engine keeps m_bType private and has no getter.
    edit(os.path.join(game, 'item_manager.h'),
         '\t\tbool IsSpecial(int idx) const\n'
         '\t\t{\n'
         '\t\t\treturn m_vecItems[idx].isSpecial;\n'
         '\t\t}\n',
         '\t\tbool IsSpecial(int idx) const\n'
         '\t\t{\n'
         '\t\t\treturn m_vecItems[idx].isSpecial;\n'
         '\t\t}\n'
         '\n'
         '\t\t// playerbot: the group type, for the chest pass (playerbotify.py).\n'
         '\t\tBYTE GetGroupType() const { return m_bType; }\n',
         marker='BYTE GetGroupType() const')

    # The overlay's engine switch: playerbot_engine_compat.h maps the r40250
    # names onto this engine's, and a few fragments carry an mt2009 branch.
    edit(os.path.join(game, 'Makefile'),
         'CFLAGS += -w\nCXXFLAGS = -std=c++20\n',
         'CFLAGS += -w\n'
         '# The playerbot overlay is written against r40250; this tells it which\n'
         '# engine it is on (playerbot_engine_compat.h).\n'
         'CFLAGS += -DPLAYERBOT_ENGINE_MT2009\n'
         'CXXFLAGS = -std=c++20\n')

    # ======================================================================
    # 0001 core integration: a descriptor with no socket, loaded by the db
    # core without a login, and the bootstrap that starts the cohort.
    # ======================================================================

    # --- common/tables.h -------------------------------------------------
    # 141 (the r40250 number) is HEADER_GD_MOVE_CHANNEL here; 150 is free.
    edit(os.path.join(common, 'tables.h'),
         '\tHEADER_GD_SPECIAL_SHOP_SEED = 145,\n',
         '\tHEADER_GD_SPECIAL_SHOP_SEED = 145,\n'
         '\tHEADER_GD_BOT_PLAYER_LOAD\t= 150,\n')
    edit(os.path.join(common, 'tables.h'),
         '} TPlayerLoadPacket;\n',
         '} TPlayerLoadPacket;\n'
         '\n'
         'typedef struct SBotPlayerLoadPacket\n'
         '{\n'
         '\tDWORD\tplayer_id;\n'
         '\tBYTE\tempire;\n'
         '} TBotPlayerLoadPacket;\n',
         # Not the inserted text: the account_id edit below changes it, and a
         # marker that is the output of one edit is not one once another edit
         # has touched that output - a re-run inserted the struct twice.
         marker='typedef struct SBotPlayerLoadPacket')
    # The db core loads the special flags with `pid=%d or aid=%d'; a zero
    # aid there matched every bot's own flags (saved under aid 0) at once and
    # SpecialFlagLoad refused the lot. The packet says whose account it is.
    edit(os.path.join(common, 'tables.h'),
         '\tBYTE\tempire;\n} TBotPlayerLoadPacket;\n',
         '\tBYTE\tempire;\n\tDWORD\taccount_id;\n} TBotPlayerLoadPacket;\n')

    # --- db/src/ClientManager.h ------------------------------------------
    edit(os.path.join(db, 'ClientManager.h'),
         '\t\tDWORD\taccount_id;\n\t\tDWORD\tplayer_id;\n',
         '\t\tDWORD\taccount_id;\n\t\tbool\tis_bot;\n\t\tDWORD\tplayer_id;\n')
    edit(os.path.join(db, 'ClientManager.h'),
         '\t\tClientHandleInfo(DWORD argHandle, DWORD dwPID = 0)\n'
         '\t\t{\n'
         '\t\t    dwHandle = argHandle;\n'
         '\t\t    pSafebox = NULL;\n'
         '\t\t    pAccountTable = NULL;\n'
         '\t\t    player_id = dwPID;\n'
         '\t\t};\n'
         '\n'
         '\t\tClientHandleInfo(DWORD argHandle, DWORD dwPID, DWORD accountId)\n'
         '\t\t{\n'
         '\t\t    dwHandle = argHandle;\n'
         '\t\t    pSafebox = NULL;\n'
         '\t\t    pAccountTable = NULL;\n'
         '\t\t    player_id = dwPID;\n'
         '\t\t\taccount_id = accountId;\n'
         '\t\t};\n',
         '\t\tClientHandleInfo(DWORD argHandle, DWORD dwPID = 0)\n'
         '\t\t{\n'
         '\t\t    dwHandle = argHandle;\n'
         '\t\t    pSafebox = NULL;\n'
         '\t\t    pAccountTable = NULL;\n'
         '\t\t    player_id = dwPID;\n'
         '\t\t    account_id = 0;\n'
         '\t\t    is_bot = false;\n'
         '\t\t};\n'
         '\n'
         '\t\tClientHandleInfo(DWORD argHandle, DWORD dwPID, DWORD accountId, bool argIsBot = false)\n'
         '\t\t{\n'
         '\t\t    dwHandle = argHandle;\n'
         '\t\t    pSafebox = NULL;\n'
         '\t\t    pAccountTable = NULL;\n'
         '\t\t    player_id = dwPID;\n'
         '\t\t\taccount_id = accountId;\n'
         '\t\t\tis_bot = argIsBot;\n'
         '\t\t};\n')
    edit(os.path.join(db, 'ClientManager.h'),
         '\tvoid\t\tQUERY_PLAYER_LOAD(CPeer * peer, DWORD dwHandle, TPlayerLoadPacket*);\n',
         '\tvoid\t\tQUERY_PLAYER_LOAD(CPeer * peer, DWORD dwHandle, TPlayerLoadPacket*, bool bIsBot = false);\n')

    # --- db/src/ClientManager.cpp ----------------------------------------
    edit(os.path.join(db, 'ClientManager.cpp'),
         '\t\t\tcase HEADER_GD_PLAYER_SAVE:\n',
         '\t\t\tcase HEADER_GD_BOT_PLAYER_LOAD:\n'
         '\t\t\t\t{\n'
         '\t\t\t\t\tTBotPlayerLoadPacket * pBot = (TBotPlayerLoadPacket *) data;\n'
         '\t\t\t\t\tTPlayerLoadPacket packet;\n'
         '\t\t\t\t\tpacket.account_id = 0;\n'
         '\t\t\t\t\tpacket.player_id = pBot->player_id;\n'
         '\t\t\t\t\tpacket.account_index = 0;\n'
         '\t\t\t\t\tQUERY_PLAYER_LOAD(peer, dwHandle, &packet, true);\n'
         '\t\t\t\t}\n'
         '\t\t\t\tbreak;\n'
         '\n'
         '\t\t\tcase HEADER_GD_PLAYER_SAVE:\n',
         marker='case HEADER_GD_BOT_PLAYER_LOAD:')
    edit(os.path.join(db, 'ClientManager.cpp'),
         '\t\t\t\t\tpacket.account_id = 0;\n\t\t\t\t\tpacket.player_id = pBot->player_id;\n',
         '\t\t\t\t\tpacket.account_id = pBot->account_id;\n\t\t\t\t\tpacket.player_id = pBot->player_id;\n')

    # The db core boots in maintenance (m_bMaintenance(TRUE)): a closed server
    # until a GM in the game types /maintenance 0, and every ordinary login -
    # admin included, it is no implementor - answered "MAINTENA" ("Obecnie
    # trwa przerwa techniczna") at the last step. A single-player world has
    # nobody to open the gate at every boot; it starts open, and the GM
    # command still closes it for an operator who wants that.
    edit(os.path.join(db, 'ClientManager.cpp'),
         '\tm_bMaintenance(TRUE),\n',
         '\tm_bMaintenance(FALSE),\n')

    # --- db/src/ClientManagerPlayer.cpp ----------------------------------
    p = os.path.join(db, 'ClientManagerPlayer.cpp')
    edit(p,
         'void CClientManager::QUERY_PLAYER_LOAD(CPeer * peer, DWORD dwHandle, TPlayerLoadPacket * packet)\n'
         '{\n'
         '\tCPlayerTableCache * c;\n'
         '\tTPlayerTable * pTab;\n'
         '\n'
         '\tCLoginData * pLoginData = GetLoginDataByAID(packet->account_id);\n'
         '\n'
         '\tif (pLoginData)\n',
         'void CClientManager::QUERY_PLAYER_LOAD(CPeer * peer, DWORD dwHandle, TPlayerLoadPacket * packet, bool bIsBot)\n'
         '{\n'
         '\tCPlayerTableCache * c;\n'
         '\tTPlayerTable * pTab;\n'
         '\n'
         '\tCLoginData * pLoginData = GetLoginDataByAID(packet->account_id);\n'
         '\n'
         '\tif (!bIsBot && pLoginData)\n')
    edit(p,
         '\tif ((c = GetPlayerCache(packet->player_id)))\n'
         '\t{\n'
         '\t\tCLoginData * pkLD = GetLoginDataByAID(packet->account_id);\n'
         '\n'
         '\t\tif (!pkLD || pkLD->IsPlay())\n'
         '\t\t{\n'
         '\t\t\tsys_log(0, "PLAYER_LOAD_ERROR: LoginData %p IsPlay %d", pkLD, pkLD ? pkLD->IsPlay() : 0);\n'
         '\t\t\tpeer->EncodeHeader(HEADER_DG_PLAYER_LOAD_FAILED, dwHandle, 0);\n'
         '\t\t\treturn;\n'
         '\t\t}\n'
         '\n'
         '\t\tpTab = c->Get();\n'
         '\n'
         '\t\tpkLD->SetPlay(true);\n'
         '\t\tthecore_memcpy(pTab->aiPremiumTimes, pkLD->GetPremiumPtr(), sizeof(pTab->aiPremiumTimes));\n'
         '\n'
         '\t\tpeer->EncodeHeader(HEADER_DG_PLAYER_LOAD_SUCCESS, dwHandle, sizeof(TPlayerTable));\n'
         '\t\tpeer->Encode(*pTab);\n'
         '\n'
         '\t\tif (packet->player_id != pkLD->GetLastPlayerID())\n',
         '\tif ((c = GetPlayerCache(packet->player_id)))\n'
         '\t{\n'
         '\t\t// A playerbot has no login: nobody sat down at a client, so there is\n'
         '\t\t// no CLoginData to check, mark as playing or bill.\n'
         '\t\tCLoginData * pkLD = NULL;\n'
         '\t\tif (!bIsBot)\n'
         '\t\t{\n'
         '\t\t\tpkLD = GetLoginDataByAID(packet->account_id);\n'
         '\t\t\tif (!pkLD || pkLD->IsPlay())\n'
         '\t\t\t{\n'
         '\t\t\t\tsys_log(0, "PLAYER_LOAD_ERROR: LoginData %p IsPlay %d", pkLD, pkLD ? pkLD->IsPlay() : 0);\n'
         '\t\t\t\tpeer->EncodeHeader(HEADER_DG_PLAYER_LOAD_FAILED, dwHandle, 0);\n'
         '\t\t\t\treturn;\n'
         '\t\t\t}\n'
         '\t\t}\n'
         '\n'
         '\t\tpTab = c->Get();\n'
         '\n'
         '\t\tif (bIsBot)\n'
         '\t\t\tmemset(pTab->aiPremiumTimes, 0, sizeof(pTab->aiPremiumTimes));\n'
         '\t\telse\n'
         '\t\t{\n'
         '\t\t\tpkLD->SetPlay(true);\n'
         '\t\t\tthecore_memcpy(pTab->aiPremiumTimes, pkLD->GetPremiumPtr(), sizeof(pTab->aiPremiumTimes));\n'
         '\t\t}\n'
         '\n'
         '\t\tpeer->EncodeHeader(HEADER_DG_PLAYER_LOAD_SUCCESS, dwHandle, sizeof(TPlayerTable));\n'
         '\t\tpeer->Encode(*pTab);\n'
         '\n'
         '\t\tif (!bIsBot && packet->player_id != pkLD->GetLastPlayerID())\n')
    # The cached path's four queries carry the bot flag through to the result
    # handlers (RESULT_COMPOSITE_PLAYER asks for it).
    edit(p,
         '\t\t\tCDBManager::instance().ReturnQuery(szQuery, QID_QUEST, peer->GetHandle(), new ClientHandleInfo(dwHandle,0,packet->account_id));\n',
         '\t\t\tCDBManager::instance().ReturnQuery(szQuery, QID_QUEST, peer->GetHandle(), new ClientHandleInfo(dwHandle, pTab->id, packet->account_id, bIsBot));\n')
    edit(p,
         '\t\tClientHandleInfo * pkInfo = new ClientHandleInfo(dwHandle, packet->player_id);\n'
         '\t\tpkInfo->account_id = packet->account_id;\n',
         '\t\tClientHandleInfo * pkInfo = new ClientHandleInfo(dwHandle, packet->player_id, packet->account_id, bIsBot);\n')
    edit(p,
         '\t\tCDBManager::instance().ReturnQuery(queryStr, QID_QUEST, peer->GetHandle(), new ClientHandleInfo(dwHandle, packet->player_id,packet->account_id));\n',
         '\t\tCDBManager::instance().ReturnQuery(queryStr, QID_QUEST, peer->GetHandle(), new ClientHandleInfo(dwHandle, packet->player_id, packet->account_id, bIsBot));\n')
    # RESULT_COMPOSITE_PLAYER: the quest branch looks the login up to deliver
    # item awards; a bot has none.
    edit(p,
         '\t\t\t\tRESULT_QUEST_LOAD(peer, pSQLResult, info->dwHandle, info->player_id);\n'
         '\n'
         '\t\t\t\tClientHandleInfo*  temp1 = info.get();\n'
         '\t\t\t\tif (temp1 == NULL)\n'
         '\t\t\t\t\tbreak;\n',
         '\t\t\t\tRESULT_QUEST_LOAD(peer, pSQLResult, info->dwHandle, info->player_id);\n'
         '\n'
         '\t\t\t\tif (info->is_bot)\n'
         '\t\t\t\t\tbreak;\n'
         '\n'
         '\t\t\t\tClientHandleInfo*  temp1 = info.get();\n'
         '\t\t\t\tif (temp1 == NULL)\n'
         '\t\t\t\t\tbreak;\n')
    edit(p,
         '\tif (!CreatePlayerTableFromRes(pRes, &tab))\n'
         '\t{\n'
         '\t\tpeer->EncodeHeader(HEADER_DG_PLAYER_LOAD_FAILED, pkInfo->dwHandle, 0);\n'
         '\t\treturn;\n'
         '\t}\n'
         '\n'
         '\tCLoginData * pkLD = GetLoginDataByAID(pkInfo->account_id);\n',
         '\tif (!CreatePlayerTableFromRes(pRes, &tab))\n'
         '\t{\n'
         '\t\tpeer->EncodeHeader(HEADER_DG_PLAYER_LOAD_FAILED, pkInfo->dwHandle, 0);\n'
         '\t\treturn;\n'
         '\t}\n'
         '\n'
         '\tif (pkInfo->is_bot)\n'
         '\t{\n'
         '\t\tmemset(tab.aiPremiumTimes, 0, sizeof(tab.aiPremiumTimes));\n'
         '\t\tpeer->EncodeHeader(HEADER_DG_PLAYER_LOAD_SUCCESS, pkInfo->dwHandle, sizeof(TPlayerTable));\n'
         '\t\tpeer->Encode(tab);\n'
         '\t\treturn;\n'
         '\t}\n'
         '\n'
         '\tCLoginData * pkLD = GetLoginDataByAID(pkInfo->account_id);\n')

    # --- game/src/desc.h / desc.cpp --------------------------------------
    edit(os.path.join(game, 'desc.h'),
         '\t\tbool\t\t\tSetup(LPFDWATCH _fdw, socket_t _fd, const struct sockaddr_in & c_rSockAddr, DWORD _handle, DWORD _handshake);\n',
         '\t\tbool\t\t\tSetup(LPFDWATCH _fdw, socket_t _fd, const struct sockaddr_in & c_rSockAddr, DWORD _handle, DWORD _handshake);\n'
         '\t\t// A playerbot: a descriptor with no socket behind it. Everything\n'
         '\t\t// sent to it is dropped; everything read from it never happens.\n'
         '\t\tbool\t\t\tSetupBot(DWORD _handle, BYTE bEmpire);\n'
         '\t\tbool\t\t\tIsBot() const\t\t{ return m_bBot; }\n')
    edit(os.path.join(game, 'desc.h'),
         '\t\tbool\t\t\tm_bDestroyed;\n',
         '\t\tbool\t\t\tm_bDestroyed;\n'
         '\t\tbool\t\t\tm_bBot;\n')
    p = os.path.join(game, 'desc.cpp')
    edit(p,
         'void DESC::Initialize()\n{\n\tm_bDestroyed = false;\n',
         'void DESC::Initialize()\n{\n\tm_bDestroyed = false;\n\tm_bBot = false;\n')
    edit(p,
         'int DESC::ProcessInput()\n',
         'bool DESC::SetupBot(DWORD _handle, BYTE bEmpire)\n'
         '{\n'
         '\tm_bBot = true;\n'
         '\tm_dwHandle = _handle;\n'
         '\tm_stHost = "playerbot";\n'
         '\tm_accountTable.bEmpire = bEmpire;\n'
         '\n'
         '\tm_SockAddr.sin_family = AF_INET;\n'
         '\tm_SockAddr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);\n'
         '\tm_SockAddr.sin_port = 0;\n'
         '\n'
         '\tSetPhase(PHASE_LOGIN);\n'
         '\treturn true;\n'
         '}\n'
         '\n'
         'int DESC::ProcessInput()\n')
    edit(p,
         'void DESC::BufferedPacket(const void * c_pvData, int iSize)\n{\n\tif (m_iPhase == PHASE_CLOSE)\n\t\treturn;\n',
         'void DESC::BufferedPacket(const void * c_pvData, int iSize)\n{\n\tif (m_bBot)\n\t\treturn;\n\n\tif (m_iPhase == PHASE_CLOSE)\n\t\treturn;\n')
    edit(p,
         'void DESC::Packet(const void * c_pvData, int iSize)\n{\n\tassert(iSize > 0);\n\n\tif (m_iPhase == PHASE_CLOSE)\n\t\treturn;\n',
         'void DESC::Packet(const void * c_pvData, int iSize)\n{\n\tassert(iSize > 0);\n\n\tif (m_bBot)\n\t\treturn;\n\n\tif (m_iPhase == PHASE_CLOSE)\n\t\treturn;\n')
    edit(p,
         'void DESC::LargePacket(const void * c_pvData, int iSize)\n{\n\tbuffer_adjust_size(m_lpOutputBuffer, iSize);\n',
         'void DESC::LargePacket(const void * c_pvData, int iSize)\n{\n\tif (m_bBot)\n\t\treturn;\n\n\tbuffer_adjust_size(m_lpOutputBuffer, iSize);\n')

    # --- game/src/desc_manager.h / desc_manager.cpp ----------------------
    edit(os.path.join(game, 'desc_manager.h'),
         '\t\tLPDESC\t\t\tAcceptP2PDesc(LPFDWATCH fdw, socket_t s);\n',
         '\t\tLPDESC\t\t\tAcceptP2PDesc(LPFDWATCH fdw, socket_t s);\n'
         '\t\tLPDESC\t\t\tCreateBotDesc(BYTE bEmpire);\n')
    p = os.path.join(game, 'desc_manager.cpp')
    edit(p,
         '#include "ClientPackageCryptInfo.h"\n',
         '#include "ClientPackageCryptInfo.h"\n#include "playerbot_manager.h"\n')
    edit(p,
         'void DESC_MANAGER::ConnectAccount(const std::string& login, LPDESC d)\n',
         'LPDESC DESC_MANAGER::CreateBotDesc(BYTE bEmpire)\n'
         '{\n'
         '\tLPDESC newd = M2_NEW DESC;\n'
         '\n'
         '\tif (!newd->SetupBot(++m_iHandleCount, bEmpire))\n'
         '\t{\n'
         '\t\tM2_DELETE(newd);\n'
         '\t\treturn NULL;\n'
         '\t}\n'
         '\n'
         '\tm_map_handle.emplace(newd->GetHandle(), newd);\n'
         '\tm_set_pkDesc.emplace(newd);\n'
         '\n'
         '\tsys_log(0, "SYSTEM: new playerbot descriptor handle=%u empire=%u",\n'
         '\t\t\tnewd->GetHandle(), bEmpire);\n'
         '\treturn newd;\n'
         '}\n'
         '\n'
         'void DESC_MANAGER::ConnectAccount(const std::string& login, LPDESC d)\n')
    edit(p,
         'void DESC_MANAGER::DestroyDesc(LPDESC d, bool bEraseFromSet)\n'
         '{\n'
         '\tif (bEraseFromSet)\n'
         '\t\tm_set_pkDesc.erase(d);\n',
         'void DESC_MANAGER::DestroyDesc(LPDESC d, bool bEraseFromSet)\n'
         '{\n'
         '\tconst bool bIsBot = d->IsBot();\n'
         '\tCPlayerBotManager::instance().OnDescriptorDestroyed(d);\n'
         '\n'
         '\tif (bEraseFromSet)\n'
         '\t\tm_set_pkDesc.erase(d);\n')
    edit(p,
         '\t// Explicit call to the virtual function Destroy()\n'
         '\td->Destroy();\n'
         '\n'
         '\tM2_DELETE(d);\n'
         '\t--m_iSocketsConnected;\n',
         '\t// Explicit call to the virtual function Destroy()\n'
         '\td->Destroy();\n'
         '\n'
         '\tM2_DELETE(d);\n'
         '\n'
         '\t// A bot never counted as a socket (CreateBotDesc does not raise it).\n'
         '\tif (!bIsBot)\n'
         '\t\t--m_iSocketsConnected;\n')

    # --- game/src/input_db.cpp -------------------------------------------
    p = os.path.join(game, 'input_db.cpp')
    edit(p,
         '#include "unique_item.h"\n\n#include "monarch.h"\n',
         '#include "unique_item.h"\n'
         '#include "playerbot_manager.h"\n'
         '#include "playerbot_empire_rules.h"\n'
         '\n'
         '#include <cstdlib>\n'
         '\n'
         '#include "monarch.h"\n')
    edit(p,
         '\t\t\tch->GetPoint(POINT_DEF_GRADE),\n'
         '\t\t\tch->GetGMLevel());\n'
         '\n'
         '\tch->QuerySafeboxSize();\n'
         '}\n',
         '\t\t\tch->GetPoint(POINT_DEF_GRADE),\n'
         '\t\t\tch->GetGMLevel());\n'
         '\n'
         '\tif (!d->IsBot())\n'
         '\t\tch->QuerySafeboxSize();\n'
         '\n'
         '\tif (d->IsBot())\n'
         '\t\tCPlayerBotManager::instance().OnPlayerLoaded(d);\n'
         '}\n')
    edit(p,
         '\t\tpLoc++;\n'
         '\t}\n'
         '}\n'
         '\n'
         'void CInputDB::P2P(const char * c_pData)\n',
         '\t\tpLoc++;\n'
         '\t}\n'
         '\n'
         '\t// MapLocations is the first point at which this core knows which maps it\n'
         '\t// hosts. Spawn the initial descriptors here; OnPlayerLoaded then starts the\n'
         '\t// regular manager update event.  Keeping this in Update() creates a startup\n'
         '\t// deadlock, because there is no update event before the first bot has been\n'
         '\t// loaded.\n'
         '\t//\n'
         '\t// Each kingdom\'s four maps sit on one core (m2-render-config: Shinsoo on\n'
         '\t// first, Chunjo on game1, Jinno on game2), so a core starts the kingdoms\n'
         '\t// whose village map it holds and no others. The budget is the operator\'s\n'
         '\t// single number, split between the kingdoms that have registered identities.\n'
         '\tif (CPlayerBotManager::instance().GetCount() == 0)\n'
         '\t{\n'
         '\t\tint autoSpawnCount = 350;\n'
         '\t\tconst char* configuredCount = std::getenv("PLAYERBOT_AUTOSPAWN_COUNT");\n'
         '\t\tif (configuredCount && *configuredCount)\n'
         '\t\t\tautoSpawnCount = std::atoi(configuredCount);\n'
         '\t\t// The ceiling is the launcher slider\'s; the real guard is below:\n'
         '\t\t// SplitPopulation caps each kingdom at the identities it has, and\n'
         '\t\t// SpawnRegistered at what LoadRegisteredBots accepted.\n'
         '\t\tconst int autoSpawnCeiling = 2500;\n'
         '\t\tif (autoSpawnCount < 0)\n'
         '\t\t\tautoSpawnCount = 0;\n'
         '\t\telse if (autoSpawnCount > autoSpawnCeiling)\n'
         '\t\t{\n'
         '\t\t\tsys_log(0, "PLAYERBOT: autospawn asked=%d, cut to the ceiling %d",\n'
         '\t\t\t\t\tautoSpawnCount, autoSpawnCeiling);\n'
         '\t\t\tautoSpawnCount = autoSpawnCeiling;\n'
         '\t\t}\n'
         '\n'
         '\t\tint registered[playerbot_empire_rules::EMPIRE_COUNT];\n'
         '\t\tint want[playerbot_empire_rules::EMPIRE_COUNT];\n'
         '\t\tCPlayerBotManager::instance().CountRegisteredPerEmpire(\n'
         '\t\t\t\tregistered, playerbot_empire_rules::EMPIRE_COUNT);\n'
         '\t\t// M2_PLAYERBOT_KINGDOMS=0 used to reach only the seed: a world that had\n'
         '\t\t// once run with 1 kept its Shinsoo and Jinno identities registered, and\n'
         '\t\t// every core went on starting them ("ustawilem KINGDOMS=0, a boty i tak\n'
         '\t\t// pojawiaja sie w Jinno i Shinsoo"). The switch comes to the core\n'
         '\t\t// through the game service\'s environment now, and a 0 leaves the two\n'
         '\t\t// new kingdoms with no budget. Their bots stay in the database as they\n'
         '\t\t// are; a 1 later starts them again.\n'
         '\t\tconst char* kingdomsSwitch = std::getenv("M2_PLAYERBOT_KINGDOMS");\n'
         '\t\tif (kingdomsSwitch && *kingdomsSwitch && std::atoi(kingdomsSwitch) == 0)\n'
         '\t\t{\n'
         '\t\t\tsys_log(0, "PLAYERBOT: M2_PLAYERBOT_KINGDOMS=0, Shinsoo (%d) and Jinno (%d) are not started",\n'
         '\t\t\t\t\tregistered[playerbot_empire_rules::EMPIRE_SHINSOO],\n'
         '\t\t\t\t\tregistered[playerbot_empire_rules::EMPIRE_JINNO]);\n'
         '\t\t\tregistered[playerbot_empire_rules::EMPIRE_SHINSOO] = 0;\n'
         '\t\t\tregistered[playerbot_empire_rules::EMPIRE_JINNO] = 0;\n'
         '\t\t}\n'
         '\t\tplayerbot_empire_rules::SplitPopulation(autoSpawnCount, registered, want);\n'
         '\n'
         '\t\tfor (int empire = playerbot_empire_rules::EMPIRE_SHINSOO;\n'
         '\t\t\t\tempire <= playerbot_empire_rules::EMPIRE_JINNO; ++empire)\n'
         '\t\t{\n'
         '\t\t\tconst long lVillage = playerbot_empire_rules::GetHomeMap(\n'
         '\t\t\t\t\tempire, playerbot_empire_rules::MAP_ROLE_M1);\n'
         '\t\t\tif (lVillage == 0 || !map_allow_find(lVillage) || want[empire] <= 0)\n'
         '\t\t\t\tcontinue;\n'
         '\t\t\tconst size_t spawned = CPlayerBotManager::instance().SpawnRegistered(\n'
         '\t\t\t\t\t(size_t)want[empire], (BYTE)empire);\n'
         '\t\t\tsys_log(0, "PLAYERBOT: autospawn empire=%d village=%ld requested=%d registered=%d started=%u",\n'
         '\t\t\t\t\tempire, lVillage, want[empire], registered[empire],\n'
         '\t\t\t\t\t(unsigned int)spawned);\n'
         '\t\t}\n'
         '\t}\n'
         '}\n'
         '\n'
         'void CInputDB::P2P(const char * c_pData)\n')
    edit(p,
         '\tcase HEADER_DG_PLAYER_LOAD_FAILED:\n'
         '\t\t//sys_log(0, "PLAYER_LOAD_FAILED");\n'
         '\t\tbreak;\n',
         '\tcase HEADER_DG_PLAYER_LOAD_FAILED:\n'
         '\t\t//sys_log(0, "PLAYER_LOAD_FAILED");\n'
         '\t\tif (DESC_MANAGER::instance().FindByHandle(m_dwHandle) &&\n'
         '\t\t\t\tDESC_MANAGER::instance().FindByHandle(m_dwHandle)->IsBot())\n'
         '\t\t\tCPlayerBotManager::instance().OnLoadFailed(m_dwHandle);\n'
         '\t\tbreak;\n')

    # --- game/src/input_login.cpp / input.h ------------------------------
    edit(os.path.join(game, 'input_login.cpp'),
         '\tch->StartRecoveryEvent();\n\tch->StartCheckSpeedHackEvent();\n',
         '\tch->StartRecoveryEvent();\n\tif (!d->IsBot())\n\t\tch->StartCheckSpeedHackEvent();\n')
    # The manager enters the game through CInputLogin::Entergame itself.
    edit(os.path.join(game, 'input.h'),
         '\t\tvirtual BYTE\tGetType() { return INPROC_LOGIN; }\n'
         '\n'
         '\tprotected:\n'
         '\t\tvirtual int\tAnalyze(LPDESC d, BYTE bHeader, const char * c_pData);\n',
         '\t\tvirtual BYTE\tGetType() { return INPROC_LOGIN; }\n'
         '\t\t// Public for the playerbot manager, which enters a bot the way a\n'
         '\t\t// client would once its character has loaded.\n'
         '\t\tvoid\t\tEntergame(LPDESC d, const char * data);\n'
         '\n'
         '\tprotected:\n'
         '\t\tvirtual int\tAnalyze(LPDESC d, BYTE bHeader, const char * c_pData);\n')
    edit(os.path.join(game, 'input.h'),
         '\t\tvoid\t\tCharacterDelete(LPDESC d, const char * data);\n'
         '\t\tvoid\t\tEntergame(LPDESC d, const char * data);\n'
         '\t\tvoid\t\tEmpire(LPDESC d, const char * c_pData);\n',
         '\t\tvoid\t\tCharacterDelete(LPDESC d, const char * data);\n'
         '\t\tvoid\t\tEmpire(LPDESC d, const char * c_pData);\n',
         marker='\t\tvoid\t\tCharacterDelete(LPDESC d, const char * data);\n\t\tvoid\t\tEmpire(LPDESC d, const char * c_pData);\n')

    # --- game/src/cmd.cpp / cmd_gm.cpp -----------------------------------
    edit(os.path.join(game, 'cmd.cpp'),
         'ACMD (do_clear_affect);\n',
         'ACMD (do_clear_affect);\n'
         'ACMD (do_playerbot_spawn);\n'
         'ACMD (do_playerbot_despawn);\n'
         'ACMD (do_playerbot_spawn_many);\n'
         'ACMD (do_playerbot_despawn_many);\n'
         'ACMD (do_playerbot_rank);\n')
    edit(os.path.join(game, 'cmd.cpp'),
         '\t{ "do_clear_affect", do_clear_affect, \t0, POS_DEAD,\t\tGM_WIZARD},\n',
         '\t{ "do_clear_affect", do_clear_affect, \t0, POS_DEAD,\t\tGM_WIZARD},\n'
         '\t{ "bot_spawn",\tdo_playerbot_spawn,\t0,\t\t\tPOS_DEAD,\tGM_IMPLEMENTOR\t},\n'
         '\t{ "bot_despawn",\tdo_playerbot_despawn,\t0,\t\t\tPOS_DEAD,\tGM_IMPLEMENTOR\t},\n'
         '\t{ "bot_spawn_many", do_playerbot_spawn_many, 0,\t\tPOS_DEAD,\tGM_IMPLEMENTOR\t},\n'
         '\t{ "bot_despawn_many", do_playerbot_despawn_many, 0,\t\tPOS_DEAD,\tGM_IMPLEMENTOR\t},\n'
         '\t{ "bot_rank",\tdo_playerbot_rank,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n')
    p = os.path.join(game, 'cmd_gm.cpp')
    edit(p,
         '#include "desc.h"\n#include "../../common/CommonDefines.h"\n',
         '#include "desc.h"\n#include "playerbot_manager.h"\n#include "../../common/CommonDefines.h"\n')
    edit(p,
         '// END_OF_ADD_COMMAND_SLOW_STUN\n\nACMD(do_stun)\n',
         '// END_OF_ADD_COMMAND_SLOW_STUN\n\n' + BOT_COMMANDS + '\nACMD(do_stun)\n',
         marker='ACMD(do_playerbot_spawn)\n')

    # ======================================================================
    # 0002 economy: five times the yang on the ground.
    # ======================================================================
    edit(os.path.join(game, 'char_battle.cpp'),
         '\t\tiGold *= iGoldMultipler;\n\n\t\tint iSplitCount;\n',
         '\t\tiGold *= iGoldMultipler;\n'
         '\t\tiGold *= 5; // 5x Yang Drop Multiplier for bot economy & blacksmith upgrades\n'
         '\n\t\tint iSplitCount;\n')

    # ======================================================================
    # 0010 every kill's yang straight to the purse, player or bot.
    # ======================================================================
    edit(os.path.join(game, 'char_battle.cpp'),
         '\tbool isAutoLoot =\n'
         '\t\t(pkAttacker->GetPremiumRemainSeconds(PREMIUM_AUTOLOOT) > 0 ||\n',
         '\tbool isAutoLoot =\n'
         '\t\t// Playerbot patch 0010: every kill\'s yang goes straight to the killer\'s\n'
         '\t\t// purse, for players and bots alike - the Third Hand and the premium\n'
         '\t\t// are still honoured but no longer needed, so no bot has to wear one.\n'
         '\t\t(true ||\n'
         '\t\t pkAttacker->GetPremiumRemainSeconds(PREMIUM_AUTOLOOT) > 0 ||\n')

    # ======================================================================
    # 0003 / 0005 quiet the per-swing traces (hundreds of bots, one syslog).
    # ======================================================================
    edit(os.path.join(game, 'refine.cpp'),
         '\tsys_log(0, "REFINE: FIND %u %s", vnum, it == m_map_RefineRecipe.end() ? "FALSE" : "TRUE");\n',
         '\t// (the "REFINE: FIND" trace is gone: one line per lookup, hundreds of bots)\n')
    edit(os.path.join(game, 'char_skill.cpp'),
         '\t\tsys_log(0, "cooltime is not over delta %u", dwNextSkillUsableTime - dwCur);\n',
         '\t\tsys_log(1, "cooltime is not over delta %u", dwNextSkillUsableTime - dwCur);\n')
    edit(os.path.join(game, 'char_skill.cpp'),
         '\tsys_log(0, "%s: USE_SKILL: %d pkVictim %p", GetName(), dwVnum, get_pointer(pkVictim));\n',
         '\tsys_log(1, "%s: USE_SKILL: %d pkVictim %p", GetName(), dwVnum, get_pointer(pkVictim));\n')
    edit(os.path.join(game, 'questmanager.cpp'),
         '\t\tsys_log(0, "CQuestManager::Kill QUEST_KILL_EVENT (pc=%d, npc=%d)", pc, npc);\n',
         '\t\tsys_log(1, "CQuestManager::Kill QUEST_KILL_EVENT (pc=%d, npc=%d)", pc, npc);\n')

    # ======================================================================
    # 0004 the private-shop guard. The fork keeps OpenMyShop in char_shop.cpp
    # and tests the polymorph state there already, so there is nothing to do;
    # the anchor below only proves that.
    # ======================================================================

    # ======================================================================
    # 2.0.12 a bot's counter opens from the start. This engine grants a private
    # shop at level 15 and 800 kills (PLAYER_STATS_MONSTER_FLAG), a rule for
    # people: a world of two thousand bots opened no counter for hours after
    # every restart while each one earned them again ("2500 botow, 0 sklepow").
    # ======================================================================
    edit(os.path.join(game, 'char_shop.cpp'),
         'bool CHARACTER::CanOpenShop()\n'
         '{\n'
         '\treturn GetLevel() >= 15 && GetSpecialFlag(PLAYER_STATS_MONSTER_FLAG) >= 800;\n'
         '}\n',
         'bool CHARACTER::CanOpenShop()\n'
         '{\n'
         '\t// A playerbot trades from the start: the level and the eight hundred kills\n'
         '\t// are a rule for people, and a world of two thousand bots opened no\n'
         '\t// counter for hours after every restart while each one earned them again.\n'
         '\tif (GetDesc() && GetDesc()->IsBot())\n'
         '\t\treturn true;\n'
         '\treturn GetLevel() >= 15 && GetSpecialFlag(PLAYER_STATS_MONSTER_FLAG) >= 800;\n'
         '}\n')

    # ======================================================================
    # 2.0.13 item.use for quests (gm_profile.quest switches an elixir on by
    # the engine's own use path) and a full elixir at creation.
    # ======================================================================
    edit(os.path.join(game, 'questlua_item.cpp'),
         '\tALUA(item_set_socket)\n',
         '\t// The item the quest selected, used by its owner through the engine\'s own\n'
         '\t// UseItem - the path a click on it takes. Added for gm_profile.quest, whose\n'
         '\t// elixir has to be switched on by that path and no other: only UseItem\n'
         '\t// makes the AFFECT_AUTO_*_RECOVERY affect the elixir works through, and\n'
         '\t// a socket0 written by hand makes an elixir that says "on" and does\n'
         '\t// nothing (char_item.cpp, the auto-recovery branch).\n'
         '\tALUA(item_use0)\n'
         '\t{\n'
         '\t\tCQuestManager& q = CQuestManager::instance();\n'
         '\t\tLPITEM item = q.GetCurrentItem();\n'
         '\t\tLPCHARACTER ch = q.GetCurrentCharacterPtr();\n'
         '\t\tif (!item || !ch || item->GetOwner() != ch || item->GetWindow() != INVENTORY)\n'
         '\t\t{\n'
         '\t\t\tlua_pushboolean(L, false);\n'
         '\t\t\treturn 1;\n'
         '\t\t}\n'
         '\t\t// Not UseItem: that one refuses everything while a quest script is\n'
         '\t\t// running ("You cannot use this item if you\'re using quests"), and a\n'
         '\t\t// quest script is what is asking - measured as six refused elixir\n'
         '\t\t// uses on the first test. UseItemEx is the use itself; the one gate\n'
         '\t\t// of UseItem\'s that is about the item rather than the moment is kept.\n'
         '\t\tif (!item->CanUsedBy(ch))\n'
         '\t\t{\n'
         '\t\t\tlua_pushboolean(L, false);\n'
         '\t\t\treturn 1;\n'
         '\t\t}\n'
         '\t\tlua_pushboolean(L, ch->UseItemEx(item, NPOS));\n'
         '\t\treturn 1;\n'
         '\t}\n'
         '\n'
         '\tALUA(item_set_socket)\n')
    edit(os.path.join(game, 'questlua_item.cpp'),
         '\t\t\t{ "set_socket",\t\titem_set_socket\t\t},\n',
         '\t\t\t{ "set_socket",\t\titem_set_socket\t\t},\n'
         '\t\t\t{ "use",\t\titem_use0\t\t},\n')
    edit(os.path.join(game, 'item_manager.cpp'),
         '\t\t\titem->SetSocket(1, item->GetValue(0), false);\n'
         '\t\t\titem->SetSocket(2, item->GetValue(0), bIsNewItem);\n',
         '\t\t\t// Socket 1 is the capacity used, socket 2 the capacity there is\n'
         '\t\t\t// (AutoRecoveryItemProcess, idx_of_amount_of_used / _full), and the\n'
         '\t\t\t// use path refuses an elixir whose two are equal as empty. The\n'
         '\t\t\t// package set both to the full capacity here, so every elixir this\n'
         '\t\t\t// engine ever created was born used up; a loaded one gets its saved\n'
         '\t\t\t// sockets back a moment later and never noticed. A new one starts\n'
         '\t\t\t// with nothing used (2.0.13).\n'
         '\t\t\titem->SetSocket(1, bIsNewItem ? 0 : item->GetValue(0), false);\n'
         '\t\t\titem->SetSocket(2, item->GetValue(0), bIsNewItem);\n')

    # ======================================================================
    # 2.0.13 the item finder searches the playerbots' stalls too. It walked
    # only the offline (ikarus) shops; a stall is a classic private shop.
    # ======================================================================
    p = os.path.join(game, 'ikarus_shop_manager.cpp')
    edit(p,
         '#include "ikarus_shop.h"\n'
         '#include "ikarus_shop_manager.h"\n',
         '#include "ikarus_shop.h"\n'
         '#include "ikarus_shop_manager.h"\n'
         '#include "shop.h"\n')

    edit(p,
         '\tbool CShopManager::SearchItemsByCategory(DWORD category, ikashop::CShopManager::SHOP_HANDLE shop)\n'
         '\t{\n'
         '\t\tif (!shop)\n'
         '\t\t\treturn false;\n',
         '\t// The category switch below asks a shop three questions - HasItem,\n'
         '\t// HasItemType, HasSoulStoneSocket - and used to ask them of an offline\n'
         '\t// shop only. A playerbot\'s stall is a classic private shop\n'
         '\t// (CHARACTER::OpenMyShop with no duration), and the finder answered\n'
         '\t// "Znaleziono 0 sklepow" on a square with three hundred of them\n'
         '\t// (sizowski, 2.0.12). The switch is a template now, asked of an offline\n'
         '\t// shop and of a keeper\'s counter alike (CPlayerBotStallView).\n'
         '\ttemplate <class SHOP, class FILTERS>\n'
         '\tstatic bool PlayerBotMatchShopCategory(DWORD category, SHOP shop, const FILTERS& m_shopSearchFilters)\n'
         '\t{\n'
         '\t\tif (!shop)\n'
         '\t\t\treturn false;\n')

    edit(p,
         '\t\t\t\t\tfor (auto filter : it->second)\n'
         '\t\t\t\t\t{\n'
         '\t\t\t\t\t\tif (shop->HasItem(filter.itemVnum, filter.socket0))\n'
         '\t\t\t\t\t\t\treturn true;\n'
         '\t\t\t\t\t}\n'
         '\t\t\t\t}\n'
         '\n'
         '\t\t\t}\n'
         '\t\t}\n'
         '\t\treturn false;\n'
         '\t}\n',
         '\t\t\t\t\tfor (auto filter : it->second)\n'
         '\t\t\t\t\t{\n'
         '\t\t\t\t\t\tif (shop->HasItem(filter.itemVnum, filter.socket0))\n'
         '\t\t\t\t\t\t\treturn true;\n'
         '\t\t\t\t\t}\n'
         '\t\t\t\t}\n'
         '\n'
         '\t\t\t}\n'
         '\t\t}\n'
         '\t\treturn false;\n'
         '\t}\n'
         '\n'
         '\tbool CShopManager::SearchItemsByCategory(DWORD category, ikashop::CShopManager::SHOP_HANDLE shop)\n'
         '\t{\n'
         '\t\treturn PlayerBotMatchShopCategory(category, shop, m_shopSearchFilters);\n'
         '\t}\n'
         '\n'
         '\t// A keeper\'s counter seen through the three questions the category\n'
         '\t// switch asks. The lines are the classic shop\'s item vector; the item\n'
         '\t// behind each line is the keeper\'s own (CShop::SHOP_ITEM::pkItem), so\n'
         '\t// type, sockets and bonus lines are read from it as the offline shop\n'
         '\t// reads them from its table.\n'
         '\tclass CPlayerBotStallView\n'
         '\t{\n'
         '\tpublic:\n'
         '\t\texplicit CPlayerBotStallView(LPCHARACTER keeper) : m_keeper(keeper) {}\n'
         '\n'
         '\t\tbool HasItem(DWORD itemVnum, int socket0 = 0)\n'
         '\t\t{\n'
         '\t\t\tconst std::vector< ::CShop::SHOP_ITEM>& lines = Lines();\n'
         '\t\t\tfor (size_t i = 0; i < lines.size(); ++i)\n'
         '\t\t\t{\n'
         '\t\t\t\tLPITEM item = lines[i].pkItem;\n'
         '\t\t\t\tif (item && item->GetVnum() == itemVnum &&\n'
         '\t\t\t\t\t\t(socket0 == 0 || item->GetSocket(0) == (long) socket0))\n'
         '\t\t\t\t\treturn true;\n'
         '\t\t\t}\n'
         '\t\t\treturn false;\n'
         '\t\t}\n'
         '\n'
         '\t\tbool HasItemType(BYTE type, BYTE subtype, bool checkAttribute)\n'
         '\t\t{\n'
         '\t\t\tconst std::vector< ::CShop::SHOP_ITEM>& lines = Lines();\n'
         '\t\t\tfor (size_t i = 0; i < lines.size(); ++i)\n'
         '\t\t\t{\n'
         '\t\t\t\tLPITEM item = lines[i].pkItem;\n'
         '\t\t\t\tif (!item || item->GetType() != type || item->GetSubType() != subtype)\n'
         '\t\t\t\t\tcontinue;\n'
         '\t\t\t\tif (checkAttribute && item->GetAttributeType(0) == 0)\n'
         '\t\t\t\t\tcontinue;\n'
         '\t\t\t\treturn true;\n'
         '\t\t\t}\n'
         '\t\t\treturn false;\n'
         '\t\t}\n'
         '\n'
         '\t\tbool HasSoulStoneSocket(BYTE level)\n'
         '\t\t{\n'
         '\t\t\tconst std::vector< ::CShop::SHOP_ITEM>& lines = Lines();\n'
         '\t\t\tfor (size_t i = 0; i < lines.size(); ++i)\n'
         '\t\t\t{\n'
         '\t\t\t\tLPITEM item = lines[i].pkItem;\n'
         '\t\t\t\tif (item && item->GetVnum() >= (28030 + 100 * level) && item->GetVnum() <= (28043 + 100 * level))\n'
         '\t\t\t\t\treturn true;\n'
         '\t\t\t}\n'
         '\t\t\treturn false;\n'
         '\t\t}\n'
         '\n'
         '\tprivate:\n'
         '\t\tconst std::vector< ::CShop::SHOP_ITEM>& Lines()\n'
         '\t\t{\n'
         '\t\t\tstatic const std::vector< ::CShop::SHOP_ITEM> s_none;\n'
         '\t\t\t::CShop* shop = m_keeper ? m_keeper->GetMyShop() : NULL;\n'
         '\t\t\treturn shop ? shop->GetItemVector() : s_none;\n'
         '\t\t}\n'
         '\n'
         '\t\tLPCHARACTER m_keeper;\n'
         '\t};\n'
         '\n'
         '\t// The keepers with a counter open on this map within the finder\'s reach,\n'
         '\t// matched like the offline shops above. The client marks a result by the\n'
         '\t// entity\'s VID and its position; a keeper is an entity like any other.\n'
         '\ttemplate <class FILTERS>\n'
         '\tstatic void PlayerBotSearchStalls(LPCHARACTER ch, DWORD category, const FILTERS& filters,\n'
         '\t\t\tstd::vector<TSubPacketGCShopSearchItemShop>& foundShops)\n'
         '\t{\n'
         '\t\tconst CHARACTER_MANAGER::NAME_MAP& pcs = CHARACTER_MANAGER::instance().GetPCMap();\n'
         '\t\tfor (CHARACTER_MANAGER::NAME_MAP::const_iterator it = pcs.begin();\n'
         '\t\t\t\tit != pcs.end() && foundShops.size() < 400; ++it)\n'
         '\t\t{\n'
         '\t\t\tLPCHARACTER keeper = it->second;\n'
         '\t\t\tif (!keeper || keeper == ch || !keeper->GetMyShop() ||\n'
         '\t\t\t\t\tkeeper->GetMapIndex() != ch->GetMapIndex() ||\n'
         '\t\t\t\t\tch->DistanceTo(keeper->GetX(), keeper->GetY()) > 7500)\n'
         '\t\t\t\tcontinue;\n'
         '\t\t\tCPlayerBotStallView view(keeper);\n'
         '\t\t\tif (!PlayerBotMatchShopCategory(category, &view, filters))\n'
         '\t\t\t\tcontinue;\n'
         '\t\t\tTSubPacketGCShopSearchItemShop found{};\n'
         '\t\t\tfound.shopVid = keeper->GetVID();\n'
         '\t\t\tfound.x = keeper->GetX();\n'
         '\t\t\tfound.y = keeper->GetY();\n'
         '\t\t\tfoundShops.push_back(found);\n'
         '\t\t}\n'
         '\t}\n')

    edit(p,
         '\n'
         '\t\tch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Searching ended. Found %d shops."), foundShops.size());\n',
         '\n'
         '\t\t// The playerbots\' stalls, after the offline shops.\n'
         '\t\tif (foundShops.size() < 400)\n'
         '\t\t\tPlayerBotSearchStalls(ch, itemVnum, m_shopSearchFilters, foundShops);\n'
         '\n'
         '\t\tch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Searching ended. Found %d shops."), foundShops.size());\n')

    # ======================================================================
    # 2.0.12 no wait between two books of one skill. The package puts 21 hours
    # between reads (SKILLBOOK_LEARN_DELAY); this world reads the next book at
    # once, for a player as for a bot - the operator's rule, asked for on the
    # Discord ("ksiegi co 24h").
    # ======================================================================
    edit(os.path.join(root, 'common', 'length.h'),
         '\tSKILLBOOK_LEARN_DELAY = 21 * 3600,\n',
         '\tSKILLBOOK_LEARN_DELAY = 0, // 21 hours in the package; this world reads the next book at once (2.0.12)\n')

    # ======================================================================
    # 0006 the Moonlight chest and three books from every stone.
    # ======================================================================
    p = os.path.join(game, 'config.cpp')
    edit(p,
         'int\t\t\ttest_server = 0;\n',
         'int\t\t\ttest_server = 0;\n'
         '// The Moonlight Treasure Chest as an event: thousandths of a chance that a\n'
         '// kill drops one, and a separate figure for a Metin stone. Zero is off. Read\n'
         '// from CONFIG so an operator turns it up or off without a rebuild.\n'
         'int\t\t\tg_iMoonlightChestPermille = 0;\n'
         'int\t\t\tg_iMoonlightChestStonePermille = 0;\n')
    edit(p,
         '\t\tTOKEN("test_server")\n',
         '\t\tTOKEN("moonlight_chest_permille")\n'
         '\t\t{\n'
         '\t\t\tstr_to_number(g_iMoonlightChestPermille, value_string);\n'
         '\t\t\tcontinue;\n'
         '\t\t}\n'
         '\n'
         '\t\tTOKEN("moonlight_chest_stone_permille")\n'
         '\t\t{\n'
         '\t\t\tstr_to_number(g_iMoonlightChestStonePermille, value_string);\n'
         '\t\t\tcontinue;\n'
         '\t\t}\n'
         '\n'
         '\t\tTOKEN("test_server")\n')
    p = os.path.join(game, 'item_manager.cpp')
    edit(p,
         '#include "item_manager.h"\n',
         '#include "item_manager.h"\n'
         '\n'
         'extern int g_iMoonlightChestPermille;\n'
         'extern int g_iMoonlightChestStonePermille;\n')
    edit(p,
         '\tif (pkKiller->IsHorseRiding() &&\n'
         '\t\t\tGetDropPerKillPct(1000, 1000000, iDeltaPercent, "horse_skill_book_drop") >= number(1, iRandRange))\n',
         '\t// One skill book from every Metin stone, whatever its table rolled - the\n'
         '\t// table gives one at a quarter to a full chance, and a stone is where a\n'
         '\t// character learns from, so the count is topped up to one rather than\n'
         '\t// added to. Each book takes its skill the way the table\'s own does.\n'
         '\tif (pkChr->IsStone())\n'
         '\t{\n'
         '\t\tint books = 0;\n'
         '\t\tfor (size_t i = 0; i < vec_item.size(); ++i)\n'
         '\t\t\tif (vec_item[i] && vec_item[i]->GetVnum() == 50300)\n'
         '\t\t\t\t++books;\n'
         '\t\tfor (; books < 1; ++books)\n'
         '\t\t{\n'
         '\t\t\titem = CreateItem(50300, 1, 0, true);\n'
         '\t\t\tif (item) vec_item.emplace_back(item);\n'
         '\t\t}\n'
         '\t}\n'
         '\n'
         '\t// The Moonlight Treasure Chest event. What a chest holds is decided by\n'
         '\t// special_item_group.txt; how often one appears is decided here, from\n'
         '\t// CONFIG, per kill and per stone.\n'
         '\t{\n'
         '\t\tconst int chestPermille = pkChr->IsStone()\n'
         '\t\t\t\t? g_iMoonlightChestStonePermille : g_iMoonlightChestPermille;\n'
         '\t\tif (chestPermille > 0 && number(1, 1000) <= chestPermille)\n'
         '\t\t{\n'
         '\t\t\titem = CreateItem(50011, 1, 0, true);\n'
         '\t\t\tif (item) vec_item.emplace_back(item);\n'
         '\t\t}\n'
         '\t}\n'
         '\n'
         '\tif (pkKiller->IsHorseRiding() &&\n'
         '\t\t\tGetDropPerKillPct(1000, 1000000, iDeltaPercent, "horse_skill_book_drop") >= number(1, iRandRange))\n')

    # ======================================================================
    # 0007 the chat reaches the bots: a shout, a whisper, a counter to read.
    # ======================================================================
    p = os.path.join(game, 'input_main.cpp')
    edit(p,
         '#include "char_manager.h"\n',
         '#include "char_manager.h"\n#include "playerbot_manager.h"\n')
    edit(p,
         '\tif (pkChr == ch)\n'
         '\t\treturn (iExtraLen);\n'
         '\n'
         '\tLPDESC pkDesc = NULL;\n',
         '\tif (pkChr == ch)\n'
         '\t\treturn (iExtraLen);\n'
         '\n'
         '\t// A whisper to a playerbot is answered by the bot rather than delivered\n'
         '\t// to a descriptor with no client behind it.\n'
         '\tif (pkChr && pkChr->GetDesc() && pkChr->GetDesc()->IsBot() &&\n'
         '\t\t\tch->GetDesc() && !ch->GetDesc()->IsBot())\n'
         '\t{\n'
         '\t\tchar szBotText[CHAT_MAX_LEN + 1];\n'
         '\t\tstrlcpy(szBotText, data + sizeof(TPacketCGWhisper), MIN(iExtraLen + 1, (int) sizeof(szBotText)));\n'
         '\t\tCPlayerBotManager::instance().OnPlayerWhisper(ch, pkChr, szBotText);\n'
         '\t\treturn (iExtraLen);\n'
         '\t}\n'
         '\n'
         '\tLPDESC pkDesc = NULL;\n')
    edit(p,
         '\t\tif (pinfo->type == CHAT_TYPE_SHOUT)\n'
         '\t\t{\n'
         '\t\t\tSendShout(chatbuf, ch->GetEmpire());\n'
         '\t\t}\n',
         '\t\tif (pinfo->type == CHAT_TYPE_SHOUT)\n'
         '\t\t{\n'
         '\t\t\tSendShout(chatbuf, ch->GetEmpire());\n'
         '\n'
         '\t\t\t// The playerbots hear it too: one with the thing on its counter, or\n'
         '\t\t\t// one short of it, whispers back.\n'
         '\t\t\tif (ch->GetDesc() && !ch->GetDesc()->IsBot())\n'
         '\t\t\t\tCPlayerBotManager::instance().OnPlayerShout(ch, buf);\n'
         '\t\t}\n')
    edit(os.path.join(game, 'shop.h'),
         '\t\tvirtual bool\tIsSellingItem(DWORD itemID);\n',
         '\t\tvirtual bool\tIsSellingItem(DWORD itemID);\n'
         '\n'
         '\t\t// What the counter holds, for the playerbots that shop at it: the\n'
         '\t\t// vector is protected, and a bot has no client to be sent the packet.\n'
         '\t\tconst std::vector<SHOP_ITEM>&\tGetItemVector() const { return m_itemVector; }\n')

    # ======================================================================
    # 0008 a warp NPC ignores a bot (it makes the map change itself).
    # ======================================================================
    edit(os.path.join(game, 'char.cpp'),
         '\t\t\t\tif (m_bUseWarp)\n'
         '\t\t\t\t\tpkChr->WarpSet(m_lTargetX, m_lTargetY);\n'
         '\t\t\t\telse\n',
         '\t\t\t\tif (m_bUseWarp)\n'
         '\t\t\t\t{\n'
         '\t\t\t\t\t// A playerbot has no client to hand over. WarpSet tells the\n'
         '\t\t\t\t\t// client to reconnect to whichever core hosts the target map,\n'
         '\t\t\t\t\t// and a descriptor with nobody behind it cannot answer that.\n'
         '\t\t\t\t\t// Its own travel code makes the same move server-side a few\n'
         '\t\t\t\t\t// metres short of here; this only has to stay out of the way.\n'
         '\t\t\t\t\tif (pkChr->GetDesc() && pkChr->GetDesc()->IsBot())\n'
         '\t\t\t\t\t\treturn;\n'
         '\t\t\t\t\tpkChr->WarpSet(m_lTargetX, m_lTargetY);\n'
         '\t\t\t\t}\n'
         '\t\t\t\telse\n')

    # ======================================================================
    # 0011 a boss blinks to its victim only on its own map.
    # ======================================================================
    edit(os.path.join(game, 'char_state.cpp'),
         '\t\tif (IsMonster() && GetMobRank() >= MOB_RANK_BOSS && GetVictim())\n',
         '\t\t// Playerbot patch 0011: and on this map. The blink below moves the boss\n'
         '\t\t// with Show(victim->GetMapIndex(), ...), so a victim that has meanwhile\n'
         '\t\t// changed map would take the boss with it.\n'
         '\t\tif (IsMonster() && GetMobRank() >= MOB_RANK_BOSS && GetVictim() &&\n'
         '\t\t\t\tGetVictim()->GetMapIndex() == GetMapIndex())\n')

    # ======================================================================
    # 0014 the channel status counts players, not bots.
    # ======================================================================
    edit(os.path.join(game, 'desc_manager.cpp'),
         '\t\t\tif (d->GetCharacter())\n'
         '\t\t\t{\n'
         '\t\t\t\t++iTotalCount;\n'
         '\t\t\t\t++aiEmpireUserCount[d->GetEmpire()];\n',
         '\t\t\t// A playerbot has a descriptor and a character like anybody else,\n'
         '\t\t\t// and this count is what the channel list and the login limit read.\n'
         '\t\t\tif (d->GetCharacter() && !d->IsBot())\n'
         '\t\t\t{\n'
         '\t\t\t\t++iTotalCount;\n'
         '\t\t\t\t++aiEmpireUserCount[d->GetEmpire()];\n')
    edit(os.path.join(game, 'p2p.h'),
         '\t\tint\t\t\t\tGetCount();\n\t\tint\t\t\t\tGetEmpireUserCount(int idx);\n',
         '\t\tint\t\t\t\tGetCount();\n\t\tint\t\t\t\tGetEmpireUserCount(int idx);\n'
         '\t\t// How many of the characters logged in on the other cores of this\n'
         '\t\t// channel are playerbots (0 = every empire).\n'
         '\t\tint\t\t\t\tCountPlayerBots(int empire) const;\n')
    p = os.path.join(game, 'p2p.cpp')
    edit(p,
         '#include "p2p.h"\n',
         '#include "p2p.h"\n#include "playerbot_manager.h"\n')
    edit(p,
         'int P2P_MANAGER::GetCount()\n'
         '{\n'
         '\t//return m_map_pkCCI.size();\n'
         '\treturn m_aiEmpireUserCount[1] + m_aiEmpireUserCount[2] + m_aiEmpireUserCount[3];\n'
         '}\n'
         '\n'
         'int P2P_MANAGER::GetEmpireUserCount(int idx)\n'
         '{\n'
         '\tassert(idx < EMPIRE_MAX_NUM);\n'
         '\treturn m_aiEmpireUserCount[idx];\n'
         '}\n',
         '// The playerbots on the other cores are subtracted here rather than kept\n'
         '// out of the incremental counters above: a login can arrive before this\n'
         '// core has loaded the bot registry, and a counter that skipped the login\n'
         '// but not the logout would drift below zero for the life of the process.\n'
         'int P2P_MANAGER::CountPlayerBots(int empire) const\n'
         '{\n'
         '\tint n = 0;\n'
         '\tfor (TPIDCCIMap::const_iterator it = m_map_dwPID_pkCCI.begin();\n'
         '\t\t\tit != m_map_dwPID_pkCCI.end(); ++it)\n'
         '\t{\n'
         '\t\tconst CCI* pkCCI = it->second;\n'
         '\t\tif (pkCCI->bChannel != g_bChannel)\n'
         '\t\t\tcontinue;\n'
         '\t\tif (empire != 0 && pkCCI->bEmpire != empire)\n'
         '\t\t\tcontinue;\n'
         '\t\tif (CPlayerBotManager::instance().IsRegisteredBotPID(pkCCI->dwPID))\n'
         '\t\t\t++n;\n'
         '\t}\n'
         '\treturn n;\n'
         '}\n'
         '\n'
         'int P2P_MANAGER::GetCount()\n'
         '{\n'
         '\t//return m_map_pkCCI.size();\n'
         '\treturn m_aiEmpireUserCount[1] + m_aiEmpireUserCount[2] + m_aiEmpireUserCount[3]\n'
         '\t\t- CountPlayerBots(0);\n'
         '}\n'
         '\n'
         'int P2P_MANAGER::GetEmpireUserCount(int idx)\n'
         '{\n'
         '\tassert(idx < EMPIRE_MAX_NUM);\n'
         '\treturn m_aiEmpireUserCount[idx] - CountPlayerBots(idx);\n'
         '}\n')
    edit(os.path.join(game, 'desc_client.cpp'),
         '\t\tDBPacket(HEADER_GD_UPDATE_CHANNELSTATUS, 0, &channelStatus, sizeof(channelStatus));\n',
         '\t\t// What the channel list will say and why, once per update.\n'
         '\t\tsys_log(0, "CHANNEL_STATUS: port=%d players=%d local=%d full_at=%d busy_at=%d status=%d",\n'
         '\t\t\t\tmother_port, iTotal, iLocal, g_iFullUserCount, g_iBusyUserCount,\n'
         '\t\t\t\t(int)channelStatus.bStatus);\n'
         '\n'
         '\t\tDBPacket(HEADER_GD_UPDATE_CHANNELSTATUS, 0, &channelStatus, sizeof(channelStatus));\n')

    # ======================================================================
    # 0015 the ItemShop link's country code has a default.
    # ======================================================================
    edit(os.path.join(game, 'cmd_general.cpp'),
         '\t\tchar country_code[3];\n',
         '\t\t// Uninitialised on every locale the switch below does not name; the\n'
         '\t\t// shop reads the code only as a language hint, so "en" is the fallback.\n'
         '\t\tchar country_code[3] = "en";\n')

    print('playerbotify: done')


BOT_COMMANDS = r'''ACMD(do_playerbot_spawn)
{
	char arg1[256], arg2[256];
	two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));

	if (!*arg1 || !*arg2)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: bot_spawn <player_id> <empire: 1-3>");
		return;
	}

	DWORD dwPlayerID = 0;
	int iEmpire = 0;
	str_to_number(dwPlayerID, arg1);
	str_to_number(iEmpire, arg2);

	if (dwPlayerID == 0 || iEmpire <= 0 || iEmpire >= EMPIRE_MAX_NUM)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Invalid player id or empire (use 1, 2 or 3).");
		return;
	}

	if (!CPlayerBotManager::instance().Spawn(dwPlayerID, static_cast<BYTE>(iEmpire)))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Cannot spawn playerbot %u (already active or invalid).", dwPlayerID);
		return;
	}

	ch->ChatPacket(CHAT_TYPE_INFO, "Playerbot %u load requested. Active/pending: %u",
			dwPlayerID, static_cast<unsigned int>(CPlayerBotManager::instance().GetCount()));
}

ACMD(do_playerbot_despawn)
{
	char arg1[256];
	one_argument(argument, arg1, sizeof(arg1));

	if (!*arg1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: bot_despawn <player_id>");
		return;
	}

	DWORD dwPlayerID = 0;
	str_to_number(dwPlayerID, arg1);

	if (!CPlayerBotManager::instance().Despawn(dwPlayerID))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Playerbot %u is not active.", dwPlayerID);
		return;
	}

	ch->ChatPacket(CHAT_TYPE_INFO, "Playerbot %u despawned. Active/pending: %u",
			dwPlayerID, static_cast<unsigned int>(CPlayerBotManager::instance().GetCount()));
}

ACMD(do_playerbot_spawn_many)
{
	char arg1[256], arg2[256], arg3[256];
	one_argument(two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2)), arg3, sizeof(arg3));

	DWORD dwFirstPlayerID = 0;
	int iCount = 0;
	int iEmpire = 0;
	str_to_number(dwFirstPlayerID, arg1);
	str_to_number(iCount, arg2);
	str_to_number(iEmpire, arg3);

	if (dwFirstPlayerID == 0 || iCount <= 0 || iCount > 500 || iEmpire <= 0 || iEmpire >= EMPIRE_MAX_NUM)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: bot_spawn_many <first_player_id> <count: 1-500> <empire: 1-3>");
		return;
	}

	int iStarted = 0;
	for (int i = 0; i < iCount; ++i)
		if (CPlayerBotManager::instance().Spawn(dwFirstPlayerID + i, static_cast<BYTE>(iEmpire)))
			++iStarted;

	ch->ChatPacket(CHAT_TYPE_INFO, "Playerbot range %u-%u: requested %d, started %d, active/pending %u.",
			dwFirstPlayerID, dwFirstPlayerID + iCount - 1, iCount, iStarted,
			static_cast<unsigned int>(CPlayerBotManager::instance().GetCount()));
}

ACMD(do_playerbot_despawn_many)
{
	char arg1[256], arg2[256];
	two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));

	DWORD dwFirstPlayerID = 0;
	int iCount = 0;
	str_to_number(dwFirstPlayerID, arg1);
	str_to_number(iCount, arg2);

	if (dwFirstPlayerID == 0 || iCount <= 0 || iCount > 500)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: bot_despawn_many <first_player_id> <count: 1-500>");
		return;
	}

	int iStopped = 0;
	for (int i = 0; i < iCount; ++i)
		if (CPlayerBotManager::instance().Despawn(dwFirstPlayerID + i))
			++iStopped;

	ch->ChatPacket(CHAT_TYPE_INFO, "Playerbot range %u-%u: requested %d, stopped %d, active/pending %u.",
			dwFirstPlayerID, dwFirstPlayerID + iCount - 1, iCount, iStopped,
			static_cast<unsigned int>(CPlayerBotManager::instance().GetCount()));
}

ACMD(do_playerbot_rank)
{
	struct TBotRankEntry
	{
		DWORD pid;
		std::string name;
		BYTE level;
		long x;
		long y;
		bool inPT;

		bool operator < (const TBotRankEntry& other) const
		{
			return level > other.level;
		}
	};

	std::vector<TBotRankEntry> ranks;
	for (DWORD pid = 1; pid <= 4000; ++pid)
	{
		LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(pid);
		if (bot && CPlayerBotManager::instance().IsManaged(pid))
		{
			TBotRankEntry e;
			e.pid = pid;
			e.name = bot->GetName();
			e.level = bot->GetLevel();
			e.x = bot->GetX();
			e.y = bot->GetY();
			e.inPT = (bot->GetParty() != NULL);
			ranks.push_back(e);
		}
	}

	std::sort(ranks.begin(), ranks.end());

	ch->ChatPacket(CHAT_TYPE_INFO, "=== TOP 10 ACTIVE PLAYERBOTS (Total Active: %u) ===", static_cast<unsigned int>(ranks.size()));
	for (size_t i = 0; i < std::min((size_t)10, ranks.size()); ++i)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "#%u %s (Lv %u) - Pos: (%ld, %ld) %s",
				static_cast<unsigned int>(i + 1), ranks[i].name.c_str(), ranks[i].level, ranks[i].x, ranks[i].y, ranks[i].inPT ? "[PT]" : "[Solo]");
	}
}
'''


if __name__ == '__main__':
    if len(sys.argv) != 2 or not os.path.isdir(os.path.join(sys.argv[1], 'game', 'src')):
        raise SystemExit(__doc__)
    main(os.path.abspath(sys.argv[1]))
