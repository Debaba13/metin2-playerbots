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
         'void CInputDB::P2P(const char * c_pData)\n',
         # A later edit writes into this block (the medal droppers below), so it
         # is found by one sentence of its own rather than by all of it.
         marker='\t// MapLocations is the first point at which this core knows which maps it\n')
    # The operator's medal droppers on top of the population, scheduled per
    # kingdom before the ordinary cohort (CPlayerBotManager::SpawnMedalDropperCohort).
    edit(p,
         '\t\tplayerbot_empire_rules::SplitPopulation(autoSpawnCount, registered, want);\n'
         '\n'
         '\t\tfor (int empire = playerbot_empire_rules::EMPIRE_SHINSOO;\n'
         '\t\t\t\tempire <= playerbot_empire_rules::EMPIRE_JINNO; ++empire)\n'
         '\t\t{\n'
         '\t\t\tconst long lVillage = playerbot_empire_rules::GetHomeMap(\n'
         '\t\t\t\t\tempire, playerbot_empire_rules::MAP_ROLE_M1);\n'
         '\t\t\tif (lVillage == 0 || !map_allow_find(lVillage) || want[empire] <= 0)\n'
         '\t\t\t\tcontinue;\n',
         '\t\tplayerbot_empire_rules::SplitPopulation(autoSpawnCount, registered, want);\n'
         '\t\t// The operator\'s medal droppers, on top of the population: this many in\n'
         '\t\t// each kingdom, their experience stopped at the level they farm\n'
         '\t\t// (CPlayerBotManager::SpawnMedalDropperCohort). Zero by default.\n'
         '\t\tint medalDroppers = 0;\n'
         '\t\tint medalDropperLevel = 25;\n'
         '\t\tconst char* configuredDroppers = std::getenv("PLAYERBOT_MEDAL_DROPPERS");\n'
         '\t\tif (configuredDroppers && *configuredDroppers)\n'
         '\t\t\tmedalDroppers = std::atoi(configuredDroppers);\n'
         '\t\tif (medalDroppers < 0)\n'
         '\t\t\tmedalDroppers = 0;\n'
         '\t\telse if (medalDroppers > 200)\n'
         '\t\t\tmedalDroppers = 200;\n'
         '\t\tconst char* configuredDropperLevel = std::getenv("PLAYERBOT_MEDAL_DROPPER_LEVEL");\n'
         '\t\tif (configuredDropperLevel && *configuredDropperLevel)\n'
         '\t\t\tmedalDropperLevel = std::atoi(configuredDropperLevel);\n'
         '\t\t// Under eighteen no Monkey Dungeon takes a bot at all.\n'
         '\t\tif (medalDropperLevel < 18)\n'
         '\t\t\tmedalDropperLevel = 18;\n'
         '\t\telse if (medalDropperLevel > 120)\n'
         '\t\t\tmedalDropperLevel = 120;\n'
         '\n'
         '\t\tfor (int empire = playerbot_empire_rules::EMPIRE_SHINSOO;\n'
         '\t\t\t\tempire <= playerbot_empire_rules::EMPIRE_JINNO; ++empire)\n'
         '\t\t{\n'
         '\t\t\tconst long lVillage = playerbot_empire_rules::GetHomeMap(\n'
         '\t\t\t\t\tempire, playerbot_empire_rules::MAP_ROLE_M1);\n'
         '\t\t\tif (lVillage == 0 || !map_allow_find(lVillage))\n'
         '\t\t\t\tcontinue;\n'
         '\t\t\tif (medalDroppers > 0 && registered[empire] > 0)\n'
         '\t\t\t\tCPlayerBotManager::instance().SpawnMedalDropperCohort(\n'
         '\t\t\t\t\t\t(size_t)medalDroppers, (BYTE)empire, (BYTE)medalDropperLevel);\n'
         '\t\t\tif (want[empire] <= 0)\n'
         '\t\t\t\tcontinue;\n',
         marker='(CPlayerBotManager::SpawnMedalDropperCohort). Zero by default.')
    # The spawn plan: the window the cohort arrives over, and a second cohort
    # joining one at a time over hours (CPlayerBotManager::SetSpawnWindow,
    # ScheduleLateJoiners). Read beside the medal droppers, scheduled after
    # the cohort of each kingdom, because the late ones are "the next
    # identities after the scheduled".
    edit(p,
         '\t\telse if (medalDropperLevel > 120)\n'
         '\t\t\tmedalDropperLevel = 120;\n'
         '\n'
         '\t\tfor (int empire = playerbot_empire_rules::EMPIRE_SHINSOO;\n',
         '\t\telse if (medalDropperLevel > 120)\n'
         '\t\t\tmedalDropperLevel = 120;\n'
         '\t\t// The spawn plan: the window the cohort arrives over, and a second\n'
         '\t\t// cohort joining one at a time over hours (CPlayerBotManager::\n'
         '\t\t// SetSpawnWindow, ScheduleLateJoiners). A minute and nobody by default.\n'
         '\t\tint spawnWindowMinutes = 1;\n'
         '\t\tconst char* configuredWindow = std::getenv("PLAYERBOT_SPAWN_WINDOW_MINUTES");\n'
         '\t\tif (configuredWindow && *configuredWindow)\n'
         '\t\t\tspawnWindowMinutes = std::atoi(configuredWindow);\n'
         '\t\tif (spawnWindowMinutes < 1)\n'
         '\t\t\tspawnWindowMinutes = 1;\n'
         '\t\telse if (spawnWindowMinutes > 180)\n'
         '\t\t\tspawnWindowMinutes = 180;\n'
         '\t\tCPlayerBotManager::instance().SetSpawnWindow((DWORD)spawnWindowMinutes * 60U * 1000U);\n'
         '\t\tint lateJoiners = 0;\n'
         '\t\tconst char* configuredLate = std::getenv("PLAYERBOT_LATE_JOINERS");\n'
         '\t\tif (configuredLate && *configuredLate)\n'
         '\t\t\tlateJoiners = std::atoi(configuredLate);\n'
         '\t\tif (lateJoiners < 0)\n'
         '\t\t\tlateJoiners = 0;\n'
         '\t\telse if (lateJoiners > autoSpawnCeiling)\n'
         '\t\t\tlateJoiners = autoSpawnCeiling;\n'
         '\t\tint lateJoinHours = 24;\n'
         '\t\tconst char* configuredLateHours = std::getenv("PLAYERBOT_LATE_JOIN_HOURS");\n'
         '\t\tif (configuredLateHours && *configuredLateHours)\n'
         '\t\t\tlateJoinHours = std::atoi(configuredLateHours);\n'
         '\t\tif (lateJoinHours < 1)\n'
         '\t\t\tlateJoinHours = 1;\n'
         '\t\telse if (lateJoinHours > 168)\n'
         '\t\t\tlateJoinHours = 168;\n'
         '\t\t// Split between the kingdoms like the cohort, over the identities\n'
         '\t\t// the cohort leaves them.\n'
         '\t\tint registeredLeft[playerbot_empire_rules::EMPIRE_COUNT];\n'
         '\t\tint lateWant[playerbot_empire_rules::EMPIRE_COUNT];\n'
         '\t\tfor (int e = 0; e < playerbot_empire_rules::EMPIRE_COUNT; ++e)\n'
         '\t\t\tregisteredLeft[e] = registered[e] > want[e] ? registered[e] - want[e] : 0;\n'
         '\t\tplayerbot_empire_rules::SplitPopulation(lateJoiners, registeredLeft, lateWant);\n'
         '\n'
         '\t\tfor (int empire = playerbot_empire_rules::EMPIRE_SHINSOO;\n',
         marker='CPlayerBotManager::instance().SetSpawnWindow(')
    edit(p,
         '\t\t\tsys_log(0, "PLAYERBOT: autospawn empire=%d village=%ld requested=%d registered=%d started=%u",\n'
         '\t\t\t\t\tempire, lVillage, want[empire], registered[empire],\n'
         '\t\t\t\t\t(unsigned int)spawned);\n'
         '\t\t}\n'
         '\t}\n'
         '}\n',
         '\t\t\tsys_log(0, "PLAYERBOT: autospawn empire=%d village=%ld requested=%d registered=%d started=%u",\n'
         '\t\t\t\t\tempire, lVillage, want[empire], registered[empire],\n'
         '\t\t\t\t\t(unsigned int)spawned);\n'
         '\t\t\tif (lateWant[empire] > 0)\n'
         '\t\t\t\tCPlayerBotManager::instance().ScheduleLateJoiners(\n'
         '\t\t\t\t\t\t(size_t)lateWant[empire], (BYTE)empire,\n'
         '\t\t\t\t\t\t(DWORD)lateJoinHours * 60U * 60U * 1000U);\n'
         '\t\t}\n'
         '\t}\n'
         '}\n',
         marker='CPlayerBotManager::instance().ScheduleLateJoiners(')
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

    # GetRefineLevel compares the plus in the base name with the plus in the
    # locale name and writes a syserr line when they differ - and "Mikstura
    # Ataku +15" (71034/76018) is a potion whose Korean name ends in a bare
    # "+": 2773 lines in twelve minutes on one core, one per look at a bag
    # holding it (sizowski, 12 September). Only equipment is refined. The
    # anchor carries no newline: item.cpp has mixed line endings.
    edit(os.path.join(game, 'item.cpp'),
         '\tconst char* locale_name = GetName();',
         '\t// A potion is not refined: "Mikstura Ataku +15" carries a plus in\n'
         '\t// its Polish name and a bare "+" in the Korean one, and the check\n'
         '\t// below wrote a syserr line for every look at a bag holding it.\n'
         '\tif (GetType() != ITEM_WEAPON && GetType() != ITEM_ARMOR)\n'
         '\t\treturn rtn;\n'
         '\tconst char* locale_name = GetName();')
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
         '}\n',
         # apply_gm_gameplay puts the GM's lines above these, so the whole
         # block is no longer there on a second run; this sentence still is.
         marker='A playerbot trades from the start')
    # 2.0.55 a player's counter opens at level fifteen too. The eight hundred
    # kills were the public server's gate for a private shop, and on a world
    # of one player they only kept a new character from trading ("jezeli
    # chcemy edytowac otwarcie tobolka i nie zabijac 800 mobow ... Liczbe 800
    # na 0", gregoszky, 14 September). The line sits below the bot's and the
    # GM's early returns, so both still read as they did.
    edit(os.path.join(game, 'char_shop.cpp'),
         '\treturn GetLevel() >= 15 && GetSpecialFlag(PLAYER_STATS_MONSTER_FLAG) >= 800;\n',
         '\t// playerbot: no kill count for a player either - the eight hundred\n'
         '\t// kills were the public server\'s gate (gregoszky, 14 September).\n'
         '\treturn GetLevel() >= 15;\n',
         marker='no kill count for a player either')

    # ======================================================================
    # 2.0.16 the Metin stone's skill book stops fifteen levels above it.
    # ======================================================================
    edit(os.path.join(game, 'item_manager.cpp'),
         'bool ITEM_MANAGER::CreateDropItem(LPCHARACTER pkChr, LPCHARACTER pkKiller, std::vector<LPITEM> & vec_item)\n',
         '// How far above a Metin stone a killer may be and still get the stone\'s\n'
         '// guaranteed skill book (the top-up in CreateDropItem below).\n'
         'static const int PLAYERBOT_METIN_BOOK_LEVEL_DELTA = 15;\n'
         '\n'
         'bool ITEM_MANAGER::CreateDropItem(LPCHARACTER pkChr, LPCHARACTER pkKiller, std::vector<LPITEM> & vec_item)\n')
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
    # Znacznikiem jest sam dolaczany naglowek, nie caly wstawiony tekst:
    # pozniejsza edycja (hooki sklepow offline) wsuwa miedzy te linie
    # playerbot_offline_policy.h, wiec wstawiony tekst przestaje sie zgadzac -
    # i drugi przebieg dokladal shop.h po raz drugi, a tamta edycja tracila
    # kotwice i zatrzymywala skrypt. Dokladnie pulapka opisana w README.
    edit(p,
         '#include "ikarus_shop.h"\n'
         '#include "ikarus_shop_manager.h"\n',
         '#include "ikarus_shop.h"\n'
         '#include "ikarus_shop_manager.h"\n'
         '#include "shop.h"\n',
         marker='#include "shop.h"\n')

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
         '\t\t\t// The client marks a result only when the VID is one of its own\n'
         '\t\t\t// offline-shop entities - ikashop keeps that list from its spawn\n'
         '\t\t\t// packet - so a keeper\'s VID lists the stall and marks nothing:\n'
         '\t\t\t// "found 16 shops, none highlighted, none on the map" (sizowski,\n'
         '\t\t\t// 12 September). What a keeper can get is a SPECIAL_EFFECT packet, sent\n'
         '\t\t\t// to the searcher alone, on every keeper found. Not the level-up one:\n'
         '\t\t\t// SE_LEVELUP_ON_14_FOR_GERMANY is, on this client, the German promo\n'
         '\t\t\t// text ("Noch 1 Level-Up! ... siehe www.metin2.de") drawn over the\n'
         '\t\t\t// character - 2.0.15 hung it over every stall found (vasils.). The\n'
         '\t\t\t// firework is a plain effect on every client.\n'
         '\t\t\tif (ch->GetDesc())\n'
         '\t\t\t{\n'
         '\t\t\t\tTPacketGCSpecialEffect effect{};\n'
         '\t\t\t\teffect.header = HEADER_GC_SEPCIAL_EFFECT;\n'
         '\t\t\t\teffect.type = SE_CHINA_FIREWORK;\n'
         '\t\t\t\teffect.vid = keeper->GetVID();\n'
         '\t\t\t\tch->GetDesc()->Packet(&effect, sizeof(effect));\n'
         '\t\t\t}\n'
         '\t\t}\n'
         '\t}\n')

    edit(p,
         '\n'
         '\t\tch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Searching ended. Found %d shops."), foundShops.size());\n',
         '\n'
         '\t\t// The playerbots\' stalls, after the offline shops. They are listed\n'
         '\t\t// and lit up, not drawn on the map, and the line says so.\n'
         '\t\tif (foundShops.size() < 400)\n'
         '\t\t{\n'
         '\t\t\tconst size_t offlineShops = foundShops.size();\n'
         '\t\t\tPlayerBotSearchStalls(ch, itemVnum, m_shopSearchFilters, foundShops);\n'
         '\t\t\tif (foundShops.size() > offlineShops)\n'
         '\t\t\t\tch->ChatPacket(CHAT_TYPE_INFO, "Stragany botow z tym towarem: %d - kazdy oznaczony fajerwerkiem.",\n'
         '\t\t\t\t\t\t(int)(foundShops.size() - offlineShops));\n'
         '\t\t}\n'
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
         'int\t\t\tg_iMoonlightChestStonePermille = 0;\n'
         '// A Dragon Coin voucher (Kupon SM) from a Metin stone or a boss, in\n'
         '// thousandths. Zero is off. The ItemShop currency, with a way into the game.\n'
         'int\t\t\tg_iDragonCoinStonePermille = 0;\n'
         'int\t\t\tg_iDragonCoinBossPermille = 0;\n')
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
         '\t\tTOKEN("dragon_coin_stone_permille")\n'
         '\t\t{\n'
         '\t\t\tstr_to_number(g_iDragonCoinStonePermille, value_string);\n'
         '\t\t\tcontinue;\n'
         '\t\t}\n'
         '\n'
         '\t\tTOKEN("dragon_coin_boss_permille")\n'
         '\t\t{\n'
         '\t\t\tstr_to_number(g_iDragonCoinBossPermille, value_string);\n'
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
         'extern int g_iMoonlightChestStonePermille;\n'
         'extern int g_iDragonCoinStonePermille;\n'
         'extern int g_iDragonCoinBossPermille;\n')
    edit(p,
         '\tif (pkKiller->IsHorseRiding() &&\n'
         '\t\t\tGetDropPerKillPct(1000, 1000000, iDeltaPercent, "horse_skill_book_drop") >= number(1, iRandRange))\n',
         '\t// One skill book from every Metin stone, whatever its table rolled - the\n'
         '\t// table gives one at a quarter to a full chance, and a stone is where a\n'
         '\t// character learns from, so the count is topped up to one rather than\n'
         '\t// added to. Each book takes its skill the way the table\'s own does. And\n'
         '\t// not from a stone the killer has outgrown: the engine\'s own tables\n'
         '\t// fade a drop out by level difference (aiPercentByDeltaLev), this\n'
         '\t// top-up ignored it, and a player of forty-six farmed level-five stones\n'
         '\t// for a guaranteed book each ("Drop z metinow", 12 September). Fifteen\n'
         '\t// levels over the stone is where the top-up ends.\n'
         '\tif (pkChr->IsStone() && pkKiller &&\n'
         '\t\t\tpkKiller->GetLevel() <= pkChr->GetLevel() + PLAYERBOT_METIN_BOOK_LEVEL_DELTA)\n'
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
         '\t// A Dragon Coin voucher (Kupon SM 50, vnum 80017) from a Metin stone\n'
         '\t// or a boss, so the ItemShop currency has a way into the game. Off (0)\n'
         '\t// by default; the permille is CONFIG, per stone and per boss, small on\n'
         '\t// purpose ("niech tych kuponow za duzo nie dropi").\n'
         '\t{\n'
         '\t\tconst int coinPermille = pkChr->IsStone()\n'
         '\t\t\t\t? g_iDragonCoinStonePermille\n'
         '\t\t\t\t: (pkChr->GetMobRank() >= MOB_RANK_BOSS ? g_iDragonCoinBossPermille : 0);\n'
         '\t\tif (coinPermille > 0 && number(1, 1000) <= coinPermille)\n'
         '\t\t{\n'
         '\t\t\titem = CreateItem(80017, 1, 0, true);\n'
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

    apply_playerbot_offline_shops(game, db)
    apply_refine_quality_of_life(game)
    apply_affect_remove_collect(game)
    apply_fishing_min_level(game)
    apply_playerbot_party_invites(game)
    apply_playerbot_pvp_challenges(game)
    apply_playerbot_monkey_doors(game)
    apply_party_pickup_to_owner(game)
    apply_gm_gameplay(game)
    apply_gm_panel(game)
    apply_costume_block(game)
    apply_costume_hair_allowed(game)
    apply_mark_login_quiet(game)
    apply_horse_rider_links(game)
    apply_gm_transfer_bots(game)
    apply_refine_log_way(game)
    apply_auto_hunt(game)
    apply_auto_hunt_offsets(game)
    apply_hwang_curse_removed(game)
    print('playerbotify: done')


def apply_hwang_curse_removed(game):
    # The Hwang Temple's curse, and with it the only reason for Maska Sabaha.
    # CHARACTER::Damage turned every blow at a monster on map 65 into a DODGE
    # unless a roll beat 50 plus POINT_BREAK_TEMPLE_CURSE, which the mask's
    # apply 146 lifts by 100 - so a player without the mask missed half his
    # blows there ("bedziemy musieli usunac wymog i ten item", Tieru, 15
    # September, after NerrVoVy's report). The mask's sources go too: the drop
    # lines and the loot box in the share step shareify.py renders, the
    # introduction quest's reward there as well, and the shop line in apply.sh.
    edit(os.path.join(game, 'char_battle.cpp'),
         '\tif (pAttacker && IsNPC() && GetMapIndex() == 65) // only hwang temple\n'
         '\t{\n'
         '\t\tint chance_to_break = (IsRaceFlag(RACE_FLAG_ATT_TEMPLE) ? 0 : 50) + pAttacker->GetPoint(POINT_BREAK_TEMPLE_CURSE);\n'
         '\t\tif (number(1, 100) > chance_to_break)\n'
         '\t\t{\n'
         '\t\t\tif (test_server)\n'
         '\t\t\t{\n'
         '\t\t\t\tpAttacker->ChatDebug("temple curse break chance %d", chance_to_break);\n'
         '\t\t\t}\n'
         '\n'
         '\t\t\tSendDamagePacket(pAttacker, 0, DAMAGE_DODGE);\n'
         '\t\t\treturn false;\n'
         '\t\t}\n'
         '\t}\n'
         '\n',
         '\t// Playerbot: the Hwang Temple has no curse and so no Maska Sabaha - its\n'
         '\t// monsters are hit like any others (playerbotify apply_hwang_curse_removed).\n'
         '\n',
         marker='\t// Playerbot: the Hwang Temple has no curse and so no Maska Sabaha')


def apply_auto_hunt(game):
    # Auto Lowy dla gracza (Tieru, 15 wrzesnia: "autolowy dla gracza, dla
    # botow niepotrzebne ... dla kazdego za darmo bez wymagan"). Okno klienta
    # (client-root/uiautohunt.py) samo chodzi, bije i pije mikstury, ale nie ma
    # w Pythonie zadnej listy potworow wokol postaci - skrypty z sieci skanuja
    # po milion VID-ow na klatke. Serwer zna sektor, wiec odpowiada jednym VID-em:
    # "/autohunt_target <zasieg> <metiny 0/1> <x> <y>" -> "AutoHuntTarget <vid>".
    # Limit komend (ENABLE_ANTI_CMD_FLOOD, 5 na 500 ms) ogranicza tempo pytan.
    edit(os.path.join(game, 'cmd_general.cpp'),
         '#include "log.h"\n',
         '#include "log.h"\n'
         '#include "sectree_manager.h"\n'
         '#include "battle.h"\n',
         marker='#include "battle.h"\n')
    edit(os.path.join(game, 'cmd_general.cpp'),
         "//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f\n",
         AUTO_HUNT_COMMAND + "\n//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f\n",
         marker='ACMD(do_autohunt_target)\n')
    edit(os.path.join(game, 'cmd.cpp'),
         'ACMD(do_check_mob);\n',
         'ACMD(do_check_mob);\n'
         'ACMD(do_autohunt_target);\n',
         marker='ACMD(do_autohunt_target);\n')
    edit(os.path.join(game, 'cmd.cpp'),
         '\t{ "check_mob", do_check_mob, \t0, POS_DEAD,\t\tGM_IMPLEMENTOR },\n',
         '\t{ "check_mob", do_check_mob, \t0, POS_DEAD,\t\tGM_IMPLEMENTOR },\n'
         '\t{ "autohunt_target",\tdo_autohunt_target,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n',
         marker='{ "autohunt_target",')
    # The pick-up by kind ("nie podnos broni, zbroi", Tieru, 15 wrzesnia):
    # "/autohunt_loot <zasieg> <rodzaje> <x> <y>" -> "AutoHuntLoot <vid> <x> <y>".
    edit(os.path.join(game, 'cmd_general.cpp'),
         "//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f\n",
         AUTO_HUNT_LOOT_COMMAND + "\n//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f\n",
         marker='ACMD(do_autohunt_loot)\n')
    edit(os.path.join(game, 'cmd.cpp'),
         'ACMD(do_autohunt_target);\n',
         'ACMD(do_autohunt_target);\n'
         'ACMD(do_autohunt_loot);\n',
         marker='ACMD(do_autohunt_loot);\n')
    edit(os.path.join(game, 'cmd.cpp'),
         '\t{ "autohunt_target",\tdo_autohunt_target,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n',
         '\t{ "autohunt_target",\tdo_autohunt_target,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n'
         '\t{ "autohunt_loot",\tdo_autohunt_loot,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n',
         marker='{ "autohunt_loot",')


def apply_auto_hunt_offsets(game):
    # Auto Lowy nic nie podnosily, jakkolwiek ustawione (Tieru, 15 wrzesnia,
    # 23:10, klient 2.0.9). Klient liczy pozycje od rogu swojej mapy - jego
    # strumien sieciowy odejmuje baze mapy od kazdej pozycji z serwera, minimapa
    # pokazuje "334, 857" w Bokjung o bazie 102400, 204800 - a "AutoHuntLoot"
    # niosl GetX()/GetY() swiata, wiec przedmiot stal dla klienta zawsze o baze
    # mapy od postaci i nigdy nie byl w zasiegu podniesienia. Punkt startu szedl
    # w druga strone tak samo i serwer odrzucal go jako dalszy niz 10000, wiec
    # zasieg lowow liczyl sie od postaci, nie od startu. Oba ida teraz jako
    # przesuniecie od postaci.
    path = os.path.join(game, 'cmd_general.cpp')
    edit(path,
         '\t\t// A point further than the sectrees round the character reach is a\n'
         '\t\t// stale hunt from another place: hunt round the character instead.\n'
         '\t\tif (DISTANCE_APPROX(x - anchorX, y - anchorY) <= 10000)\n'
         '\t\t{\n'
         '\t\t\tanchorX = x;\n'
         '\t\t\tanchorY = y;\n'
         '\t\t}\n',
         '\t\t// The client counts a position from its own map\'s corner and the\n'
         '\t\t// server from the world\'s (the client\'s network stream takes the\n'
         '\t\t// map\'s base off every position it receives), so the start point\n'
         '\t\t// comes as an offset from where the character stands. One further\n'
         '\t\t// than the sectrees round the character reach is a stale hunt from\n'
         '\t\t// another place: hunt round the character instead.\n'
         '\t\tif (DISTANCE_APPROX(x, y) <= 10000)\n'
         '\t\t{\n'
         '\t\t\tanchorX += x;\n'
         '\t\t\tanchorY += y;\n'
         '\t\t}\n',
         marker='// comes as an offset from where the character stands. One further\n')
    edit(path,
         '\t\t// The same rule as the target: a stale point hunts round the character.\n'
         '\t\tif (DISTANCE_APPROX(x - anchorX, y - anchorY) <= 10000)\n'
         '\t\t{\n'
         '\t\t\tanchorX = x;\n'
         '\t\t\tanchorY = y;\n'
         '\t\t}\n',
         '\t\t// The same rule as the target: an offset from the character, and a\n'
         '\t\t// stale one hunts round the character.\n'
         '\t\tif (DISTANCE_APPROX(x, y) <= 10000)\n'
         '\t\t{\n'
         '\t\t\tanchorX += x;\n'
         '\t\t\tanchorY += y;\n'
         '\t\t}\n',
         marker='// The same rule as the target: an offset from the character, and a\n')
    edit(path,
         '\tch->ChatPacket(CHAT_TYPE_COMMAND, "AutoHuntLoot %u %ld %ld",\n'
         '\t\t\t(unsigned int) (DWORD) f.m_pkBest->GetVID(), (long) f.m_pkBest->GetX(), (long) f.m_pkBest->GetY());\n',
         '\t// The item\'s place as an offset from the character, which the client adds\n'
         '\t// to its own position: in the world\'s coordinates every item stood a\n'
         '\t// map\'s base away from a client that counts from its map\'s corner, and\n'
         '\t// the pick-up never came within reach (Tieru, 15 September).\n'
         '\tch->ChatPacket(CHAT_TYPE_COMMAND, "AutoHuntLoot %u %ld %ld",\n'
         '\t\t\t(unsigned int) (DWORD) f.m_pkBest->GetVID(),\n'
         '\t\t\t(long) (f.m_pkBest->GetX() - ch->GetX()), (long) (f.m_pkBest->GetY() - ch->GetY()));\n',
         marker='// The item\'s place as an offset from the character, which the client adds\n')


AUTO_HUNT_COMMAND = r'''// The player's auto-hunt (client-root/uiautohunt.py) asks which monster to go
// for. The client has no list of the characters round it - the scripts that
// do this without the server scan a million VIDs a frame - and the sectree
// has one. Monsters, and Metin stones when the window asks for them; only what
// battle_is_attackable lets this character hit; within the range of the point
// the hunt started from. What is already hitting the hunter comes first, then
// the nearest. The answer is "AutoHuntTarget <vid>", zero for nothing.
struct FAutoHuntTarget
{
	LPCHARACTER	m_ch;
	int		m_iAnchorX;
	int		m_iAnchorY;
	int		m_iRange;
	bool		m_bStones;
	LPCHARACTER	m_pkBest;
	int		m_iBestScore;

	FAutoHuntTarget(LPCHARACTER ch, int anchorX, int anchorY, int range, bool stones)
		: m_ch(ch), m_iAnchorX(anchorX), m_iAnchorY(anchorY), m_iRange(range), m_bStones(stones),
		m_pkBest(NULL), m_iBestScore(0x7fffffff)
	{
	}

	void operator () (LPENTITY ent)
	{
		if (!ent->IsType(ENTITY_CHARACTER))
			return;

		LPCHARACTER victim = (LPCHARACTER) ent;
		if (victim == m_ch || victim->IsDead())
			return;
		if (!victim->IsMonster() && !(m_bStones && victim->IsStone()))
			return;
		if (DISTANCE_APPROX(victim->GetX() - m_iAnchorX, victim->GetY() - m_iAnchorY) > m_iRange)
			return;
		if (!battle_is_attackable(m_ch, victim))
			return;

		int score = DISTANCE_APPROX(victim->GetX() - m_ch->GetX(), victim->GetY() - m_ch->GetY());
		if (victim->GetVictim() == m_ch)
			score /= 4;
		if (score < m_iBestScore)
		{
			m_iBestScore = score;
			m_pkBest = victim;
		}
	}
};

ACMD(do_autohunt_target)
{
	char arg1[256], arg2[256], arg3[256], arg4[256];
	const char * rest = two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));
	two_arguments(rest, arg3, sizeof(arg3), arg4, sizeof(arg4));

	if (!ch->GetSectree() || ch->IsDead())
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AutoHuntTarget 0");
		return;
	}

	int range = 2000;
	int stones = 0;
	str_to_number(range, arg1);
	str_to_number(stones, arg2);
	range = MAX(300, MIN(range, 5000));

	int anchorX = ch->GetX();
	int anchorY = ch->GetY();
	if (*arg3 && *arg4)
	{
		int x = 0;
		int y = 0;
		str_to_number(x, arg3);
		str_to_number(y, arg4);
		// A point further than the sectrees round the character reach is a
		// stale hunt from another place: hunt round the character instead.
		if (DISTANCE_APPROX(x - anchorX, y - anchorY) <= 10000)
		{
			anchorX = x;
			anchorY = y;
		}
	}

	FAutoHuntTarget f(ch, anchorX, anchorY, range, stones != 0);
	ch->GetSectree()->ForEachAround(f);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "AutoHuntTarget %u",
			f.m_pkBest ? (unsigned int) (DWORD) f.m_pkBest->GetVID() : 0);
}
'''


AUTO_HUNT_LOOT_COMMAND = r'''// The auto-hunt's pick-up by kind (client-root/uiautohunt.py). The client's
// own PickCloseItem takes whatever lies nearest and cannot tell a sword from a
// potion, and the window offers "do not pick up weapons, armour, ..." (Tieru,
// 15 September). So the client asks "/autohunt_loot <range> <kinds> <x> <y>"
// and is answered "AutoHuntLoot <vid> <x> <y>": the nearest item on the ground
// this character may take, of a kind the window keeps, within the range of
// the point the hunt started from - zero for nothing. The client walks there
// and sends the ordinary pick-up packet, which CHARACTER::PickupItem judges as
// it judges anybody's. Yang goes with every kind.
enum
{
	AUTOHUNT_LOOT_WEAPON = 1 << 0,
	AUTOHUNT_LOOT_ARMOUR = 1 << 1,
	AUTOHUNT_LOOT_JEWELLERY = 1 << 2,
	AUTOHUNT_LOOT_POTION = 1 << 3,
	AUTOHUNT_LOOT_BOOK = 1 << 4,
	AUTOHUNT_LOOT_STONE = 1 << 5,
	AUTOHUNT_LOOT_OTHER = 1 << 6,
};

static int AutoHuntLootKind(LPITEM item)
{
	switch (item->GetType())
	{
		case ITEM_WEAPON:
			return item->GetSubType() == WEAPON_ARROW ? AUTOHUNT_LOOT_OTHER : AUTOHUNT_LOOT_WEAPON;
		case ITEM_ARMOR:
			switch (item->GetSubType())
			{
				case ARMOR_BODY:
				case ARMOR_HEAD:
				case ARMOR_SHIELD:
					return AUTOHUNT_LOOT_ARMOUR;
				default:
					return AUTOHUNT_LOOT_JEWELLERY;
			}
		case ITEM_RING:
		case ITEM_BELT:
			return AUTOHUNT_LOOT_JEWELLERY;
		case ITEM_USE:
			switch (item->GetSubType())
			{
				case USE_POTION:
				case USE_POTION_NODELAY:
				case USE_ABILITY_UP:
					return AUTOHUNT_LOOT_POTION;
				default:
					return AUTOHUNT_LOOT_OTHER;
			}
		case ITEM_SKILLBOOK:
		case ITEM_SKILLFORGET:
			return AUTOHUNT_LOOT_BOOK;
		case ITEM_METIN:
			return AUTOHUNT_LOOT_STONE;
		default:
			return AUTOHUNT_LOOT_OTHER;
	}
}

struct FAutoHuntLoot
{
	LPCHARACTER m_ch;
	int m_iAnchorX;
	int m_iAnchorY;
	int m_iRange;
	int m_iKinds;
	LPITEM m_pkBest;
	int m_iBestDistance;

	FAutoHuntLoot(LPCHARACTER ch, int anchorX, int anchorY, int range, int kinds)
		: m_ch(ch), m_iAnchorX(anchorX), m_iAnchorY(anchorY), m_iRange(range), m_iKinds(kinds),
		m_pkBest(NULL), m_iBestDistance(0x7fffffff)
	{
	}

	void operator () (LPENTITY ent)
	{
		if (!ent->IsType(ENTITY_ITEM))
			return;

		LPITEM item = (LPITEM) ent;
		if (item->GetOwner() || !item->GetSectree())
			return;
		if (item->GetType() != ITEM_ELK && !(AutoHuntLootKind(item) & m_iKinds))
			return;
		if (DISTANCE_APPROX(item->GetX() - m_iAnchorX, item->GetY() - m_iAnchorY) > m_iRange)
			return;
		if (!item->IsOwnership(m_ch))
			return;

		const int distance = DISTANCE_APPROX(item->GetX() - m_ch->GetX(), item->GetY() - m_ch->GetY());
		if (distance < m_iBestDistance)
		{
			m_iBestDistance = distance;
			m_pkBest = item;
		}
	}
};

ACMD(do_autohunt_loot)
{
	char arg1[256], arg2[256], arg3[256], arg4[256];
	const char * rest = two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));
	two_arguments(rest, arg3, sizeof(arg3), arg4, sizeof(arg4));

	int range = 2000;
	int kinds = 0;
	str_to_number(range, arg1);
	str_to_number(kinds, arg2);
	range = MAX(300, MIN(range, 5000));

	if (!ch->GetSectree() || ch->IsDead() || kinds <= 0)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AutoHuntLoot 0 0 0");
		return;
	}

	int anchorX = ch->GetX();
	int anchorY = ch->GetY();
	if (*arg3 && *arg4)
	{
		int x = 0;
		int y = 0;
		str_to_number(x, arg3);
		str_to_number(y, arg4);
		// The same rule as the target: a stale point hunts round the character.
		if (DISTANCE_APPROX(x - anchorX, y - anchorY) <= 10000)
		{
			anchorX = x;
			anchorY = y;
		}
	}

	FAutoHuntLoot f(ch, anchorX, anchorY, range, kinds);
	ch->GetSectree()->ForEachAround(f);
	if (!f.m_pkBest)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AutoHuntLoot 0 0 0");
		return;
	}
	ch->ChatPacket(CHAT_TYPE_COMMAND, "AutoHuntLoot %u %ld %ld",
			(unsigned int) (DWORD) f.m_pkBest->GetVID(), (long) f.m_pkBest->GetX(), (long) f.m_pkBest->GetY());
}
'''


def apply_refine_log_way(game):
    # Jak zrobiono ulepszenie - do nawiasu w historii ekwipunku panelu
    # ("Ulepszenie udane (Kowal)", "(Zwoj Blogoslawienstwa)", "(Kowal w Wiezy
    # Demonow)", Tieru 15.09). DoRefine zapisywal w log.refinelog "POWER" i dla
    # zwyklego kowala, i dla kowala z Wiezy Demonow (bMoneyOnly, sciezka
    # REFINE_TYPE_MONEY_ONLY w CInputMain::Refine), a DoRefineWithScroll
    # "SCROLL" dla kazdego zwoju - kolumna setType to SET, ktory trzy dluzsze
    # nazwy tego silnika po prostu gubil - wiec Zwoj Blogoslawienstwa i Zwoj
    # Boga Smokow wygladaly tak samo. Kowal z Wiezy pisze DEVILTOWER, zwoj
    # SCROLL:<vnum> (vnum brany, zanim SetCount zniszczy ostatni zwoj);
    # logschemify zamienia kolumne na varchar.
    path = os.path.join(game, 'char_item.cpp')
    data = read(path)
    old = b'IsRefineThroughGuild() ? "GUILD" : "POWER"'
    new = b'IsRefineThroughGuild() ? "GUILD" : (bMoneyOnly ? "DEVILTOWER" : "POWER")'
    if new in data:
        print('  already: %s' % os.path.relpath(path))
    else:
        n = data.count(old)
        if n != 3:
            raise SystemExit('playerbotify: expected 3 refine ways in %s, found %d' % (path, n))
        write(path, data.replace(old, new))
        print('  edited:  %s' % os.path.relpath(path))
    edit(path,
         '\tsuccess_prob += pkItemScroll->GetValue(1);\n',
         '\t// The scroll by its vnum for the refine log, taken while it exists:\n'
         '\t// SetCount below destroys the last one.\n'
         '\tchar szRefineWay[48];\n'
         '\tsnprintf(szRefineWay, sizeof(szRefineWay), "SCROLL:%u", pkItemScroll->GetVnum());\n'
         '\tszRefineType = szRefineWay;\n'
         '\n'
         '\tsuccess_prob += pkItemScroll->GetValue(1);\n',
         marker='snprintf(szRefineWay, sizeof(szRefineWay), "SCROLL:%u"')


def apply_costume_hair_allowed(game):
    """A hairstyle is a costume the operator wants worn.

    apply_costume_block refuses every ITEM_COSTUME at the top of CanEquipNow, and
    a hairstyle from the ItemShop is one (COSTUME_HAIR, 395 vnums in
    world.item_proto): "po aktualizacji ktora wylaczyla mozliwosc zakladania
    kostiumow, wylaczona zostala tez mozliwosc zakladania fryzur z IS" (hunmar,
    15 September). The block stays for every other kind of costume.
    """
    edit(os.path.join(game, 'char_item.cpp'),
         '\tif (item && item->GetType() == ITEM_COSTUME)\n'
         '\t{\n'
         '\t\tChatPacket(CHAT_TYPE_INFO, "Kostiumy sa na tym serwerze wylaczone.");\n',
         '\t// A hairstyle passes (playerbotify.py, apply_costume_hair_allowed).\n'
         '\tif (item && item->GetType() == ITEM_COSTUME && item->GetSubType() != COSTUME_HAIR)\n'
         '\t{\n'
         '\t\tChatPacket(CHAT_TYPE_INFO, "Kostiumy sa na tym serwerze wylaczone.");\n',
         marker='playerbotify.py, apply_costume_hair_allowed).')


def apply_mark_login_quiet(game):
    """The guild-mark connection's login is not an unknown packet.

    The client opens a second connection for the guild marks and, once the
    handshake has put it in PHASE_LOGIN, sends HEADER_CG_MARK_LOGIN (100)
    before its MARK_IDXLIST. CInputHandshake answers that header only while the
    connection is still in the handshake, so in the login phase it fell through
    to the default branch: "login phase does not handle this packet! header
    100" in syserr on every mark download - 92 lines on the test world, 202 in
    two days on sizowski's, and a report that read them as the cause of his
    login trouble (16 September). The branch already did nothing but log
    (SetPhase(PHASE_CLOSE) is commented out), so this only takes the line away;
    the MARK_IDXLIST that follows is handled as before.
    """
    edit(os.path.join(game, 'input_login.cpp'),
         '\t\t// @fixme120\n'
         '\t\tcase HEADER_CG_ITEM_USE:\n'
         '\t\tcase HEADER_CG_TARGET:\n'
         '\t\t\tbreak;\n'
         '\n'
         '\t\tdefault:\n'
         '\t\t\tsys_err("login phase does not handle this packet! header %d", bHeader);\n',
         '\t\t// @fixme120\n'
         '\t\tcase HEADER_CG_ITEM_USE:\n'
         '\t\tcase HEADER_CG_TARGET:\n'
         '\t\t\tbreak;\n'
         '\n'
         '\t\t// The guild-mark connection\'s login, sent once the handshake has put it\n'
         '\t\t// here (playerbotify.py, apply_mark_login_quiet): nothing to do, and\n'
         '\t\t// nothing worth a syserr line on every mark download.\n'
         '\t\tcase HEADER_CG_MARK_LOGIN:\n'
         '\t\t\tbreak;\n'
         '\n'
         '\t\tdefault:\n'
         '\t\t\tsys_err("login phase does not handle this packet! header %d", bHeader);\n',
         marker='playerbotify.py, apply_mark_login_quiet)')


def apply_costume_block(game):
    """No costume goes on a character on this line.

    Players handed one through the panels put it on and could not take it off
    again, and the character showed as a bare weapon (reported to Tieru,
    14 September); the operator's call was to switch costumes off rather than
    delete them. EquipItem, a drag onto the costume slot and the item's own
    use all pass through CanEquipNow, so the refusal sits at its top. A costume
    already worn stays where it is, and nothing is deleted.
    """
    edit(os.path.join(game, 'char_item.cpp'),
         'bool CHARACTER::CanEquipNow(const LPITEM item, const TItemPos& srcCell, const TItemPos& destCell) /*const*/\n'
         '{\n',
         'bool CHARACTER::CanEquipNow(const LPITEM item, const TItemPos& srcCell, const TItemPos& destCell) /*const*/\n'
         '{\n'
         '\t// playerbot: costumes are off on this line (playerbotify.py, apply_costume_block).\n'
         '\tif (item && item->GetType() == ITEM_COSTUME)\n'
         '\t{\n'
         '\t\tChatPacket(CHAT_TYPE_INFO, "Kostiumy sa na tym serwerze wylaczone.");\n'
         '\t\treturn false;\n'
         '\t}\n',
         marker='playerbotify.py, apply_costume_block).')


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



def apply_playerbot_offline_shops(game, db):
    # Native offline playerbot shops (Codex handoff 2026-09-13).
    edit(os.path.join(game, 'ikarus_shop_manager.h'),
         '\t\tvoid PutsAuction(const TAuctionInfo& auction);\n\t\tvoid PutsAuctionOffer(const TAuctionOfferInfo& offer);\n\n\t\tvoid PrepareShopSearchFilters();\n\n\t\tSHOP_HANDLE GetShopByOwnerID(DWORD pid);\n\t\tSAFEBOX_HANDLE GetShopSafeboxByOwnerID(DWORD pid);\n\t\tAUCTION_HANDLE GetAuctionByOwnerID(DWORD pid);\n\n\t\t//offers\n',
         '\t\tvoid PutsAuction(const TAuctionInfo& auction);\n\t\tvoid PutsAuctionOffer(const TAuctionOfferInfo& offer);\n\n\t\tvoid PrepareShopSearchFilters();\n\n\t\t// Read-only native ledger, including owners currently absent from this map.\n\t\tconst SHOPMAP& GetPlayerBotOfflineShops() const { return m_mapShops; }\n\t\tSHOP_HANDLE GetShopByOwnerID(DWORD pid);\n\t\tSAFEBOX_HANDLE GetShopSafeboxByOwnerID(DWORD pid);\n\t\tAUCTION_HANDLE GetAuctionByOwnerID(DWORD pid);\n\n\t\t//offers\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\n#ifdef ENABLE_IKASHOP_RENEWAL\n\n#include "ikarus_shop.h"\n#include "ikarus_shop_manager.h"\n#include "shop.h"\n\ntemplate<class DerivedType, class BaseType>\nDerivedType DerivedFromBase(const BaseType& base) {\n\tstatic_assert(std::is_base_of<BaseType, DerivedType>::value); // DerivedType must be inherited by BaseType\n',
         '\n#ifdef ENABLE_IKASHOP_RENEWAL\n\n#include "ikarus_shop.h"\n#include "ikarus_shop_manager.h"\n#include "playerbot_offline_policy.h"\n#include "shop.h"\n\ntemplate<class DerivedType, class BaseType>\nDerivedType DerivedFromBase(const BaseType& base) {\n\tstatic_assert(std::is_base_of<BaseType, DerivedType>::value); // DerivedType must be inherited by BaseType\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\tif (ownerCh)\n\t\t{\n\t\t\tNotifyOwnerItemSold(ownerCh, shopItem->GetVnum(), shopItem->GetInfo().count, shopItem->GetPrice().GetTotalYangAmount());\n\t\t}\n\n\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopEditItemDBPacket(DWORD ownerid, DWORD itemid, const TPriceInfo& price)\n\t{\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_EDIT_ITEM;\n\n\t\tTSubPacketGDEditItem subpack{};\n\t\tsubpack.ownerid = ownerid;\n',
         '\t\tif (ownerCh)\n\t\t{\n\t\t\tNotifyOwnerItemSold(ownerCh, shopItem->GetVnum(), shopItem->GetInfo().count, shopItem->GetPrice().GetTotalYangAmount());\n\t\t}\n\n\t\t// The one place that knows a line has gone. A playerbot keeper is off\n\t\t// hunting while its counter sells, and the goods belong to the shop\n\t\t// entity rather than to its bag, so nothing on the AI side can notice\n\t\t// this by looking at the owner. Recorded here, drained on the owner\'s\n\t\t// own tick (playerbot_offline_shop.h).\n\t\tplayerbot_offline::NoteSold(ownerid, itemid, shopItem->GetVnum(), shopItem->GetInfo().count, shopItem->GetPrice().GetTotalYangAmount());\n\t\tplayerbot_offline::Complete(buyerid, playerbot_offline::Buy, itemid);\n\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopEditItemDBPacket(DWORD ownerid, DWORD itemid, const TPriceInfo& price)\n\t{\n\t\tplayerbot_offline::Sent(ownerid, playerbot_offline::Edit, itemid);\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_EDIT_ITEM;\n\n\t\tTSubPacketGDEditItem subpack{};\n\t\tsubpack.ownerid = ownerid;\n',
         # Named rather than left to default to the whole replacement: this
         # block has been extended once already, and a marker that changes
         # with the text makes a re-run over an already-ported tree hunt for
         # an anchor that is no longer there.
         marker='playerbot_offline::NoteSold(')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopRemoveItemDBPacket(DWORD ownerid, DWORD itemid)\n\t{\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_REMOVE_ITEM;\n\n\t\tTSubPacketGDRemoveItem subpack{};\n\t\tsubpack.ownerid = ownerid;\n',
         '\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopRemoveItemDBPacket(DWORD ownerid, DWORD itemid)\n\t{\n\t\tplayerbot_offline::Sent(ownerid, playerbot_offline::Remove, itemid);\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_REMOVE_ITEM;\n\n\t\tTSubPacketGDRemoveItem subpack{};\n\t\tsubpack.ownerid = ownerid;\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\t\t{\n\t\t\t\tSendShopForceHardCloseDBPacket(ownerid);\n\t\t\t}\n\t\t}\n\n\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopAddItemDBPacket(DWORD ownerid, const TShopItem& iteminfo)\n\t{\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_ADD_ITEM;\n\n\t\tTSubPacketGDAddItem subpack{};\n\t\tsubpack.ownerid = ownerid;\n',
         '\t\t\t{\n\t\t\t\tSendShopForceHardCloseDBPacket(ownerid);\n\t\t\t}\n\t\t}\n\n\t\tplayerbot_offline::Complete(ownerid, playerbot_offline::Remove, itemid);\n\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopAddItemDBPacket(DWORD ownerid, const TShopItem& iteminfo)\n\t{\n\t\tplayerbot_offline::Sent(ownerid, playerbot_offline::Add, iteminfo.id);\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_ADD_ITEM;\n\n\t\tTSubPacketGDAddItem subpack{};\n\t\tsubpack.ownerid = ownerid;\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\tif(!shop)\n\t\t\treturn false;\n\n\t\t// adding item to shop\n\t\t\n\t\treturn shop->AddItem(iteminfo);\n\t}\n\n\tbool ikashop::CShopManager::RecvShopChangeNameClientPacket(LPCHARACTER ch, const char* szName)\n\t{\n\t\tif (!ch || !ch->GetIkarusShop())\n',
         '\t\tif(!shop)\n\t\t\treturn false;\n\n\t\t// adding item to shop\n\t\t\n\t\tbool ok = shop->AddItem(iteminfo);\n\t\tplayerbot_offline::Complete(ownerid, playerbot_offline::Add, iteminfo.id, ok);\n\t\treturn ok;\n\t}\n\n\tbool ikashop::CShopManager::RecvShopChangeNameClientPacket(LPCHARACTER ch, const char* szName)\n\t{\n\t\tif (!ch || !ch->GetIkarusShop())\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopLockBuyItemDBPacket(LPCHARACTER buyer, DWORD ownerid, ITEM_HANDLE item, long long TotalPriceSeen) //patch seen price check\n\t{\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader = SUBHEADER_GD_BUY_LOCK_ITEM;\n\n\t\tTSubPacketGDLockBuyItem subpack{};\n\t\tsubpack.guestid = buyer->GetPlayerID();\n',
         '\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopLockBuyItemDBPacket(LPCHARACTER buyer, DWORD ownerid, ITEM_HANDLE item, long long TotalPriceSeen) //patch seen price check\n\t{\n\t\tplayerbot_offline::Sent(buyer->GetPlayerID(), playerbot_offline::Buy, item->GetID());\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader = SUBHEADER_GD_BUY_LOCK_ITEM;\n\n\t\tTSubPacketGDLockBuyItem subpack{};\n\t\tsubpack.guestid = buyer->GetPlayerID();\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\tdb_clientdesc->DBPacket(HEADER_GD_NEW_OFFLINESHOP, 0, buff.read_peek(), buff.size());\n\t}\n\n\tbool CShopManager::RecvShopLockedBuyItemDBPacket(DWORD buyerid, DWORD ownerid,DWORD itemid)\n\t{\n\t\tauto SendDBFeedback = [&](auto success){\n\t\t\tSendShopBuyDBPacket(buyerid, ownerid, itemid, success);\n\t\t\treturn success;\n\t\t};\n\n\t\tauto shop = GetShopByOwnerID(ownerid);\n\t\tauto ch\t= CHARACTER_MANAGER::instance().FindByPID(buyerid);\n',
         '\t\tdb_clientdesc->DBPacket(HEADER_GD_NEW_OFFLINESHOP, 0, buff.read_peek(), buff.size());\n\t}\n\n\tbool CShopManager::RecvShopLockedBuyItemDBPacket(DWORD buyerid, DWORD ownerid,DWORD itemid)\n\t{\n\t\t// Internal negative lock acknowledgement; DB sends owner=0 on refusal.\n\t\tif (ownerid == 0) { playerbot_offline::Complete(buyerid, playerbot_offline::Buy, itemid, false); return false; }\n\t\tauto SendDBFeedback = [&](auto success){\n\t\t\tSendShopBuyDBPacket(buyerid, ownerid, itemid, success);\n\t\t\tif (!success) playerbot_offline::Complete(buyerid, playerbot_offline::Buy, itemid, false);\n\t\t\treturn success;\n\t\t};\n\n\t\tauto shop = GetShopByOwnerID(ownerid);\n\t\tauto ch\t= CHARACTER_MANAGER::instance().FindByPID(buyerid);\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopCreateNewDBPacket(const TShopInfo& shop, const TShopItem* items)\n\t{\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_SHOP_CREATE_NEW;\n\n\t\tTSubPacketGDShopCreateNew subpack{};\n\t\tsubpack.shop = shop;\n',
         '\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopCreateNewDBPacket(const TShopInfo& shop, const TShopItem* items)\n\t{\n\t\tplayerbot_offline::Sent(shop.ownerid, playerbot_offline::Create, 0);\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_SHOP_CREATE_NEW;\n\n\t\tTSubPacketGDShopCreateNew subpack{};\n\t\tsubpack.shop = shop;\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\t\t\t\tbreak;\n\n\t\t\t\tshop->AddItem(items[i], false);\n\t\t\t}\n\t\t}\n\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopChangeNameDBPacket(DWORD ownerid, const char* name)\n\t{\n',
         '\t\t\t\t\tbreak;\n\n\t\t\t\tshop->AddItem(items[i], false);\n\t\t\t}\n\t\t}\n\t\tplayerbot_offline::Complete(info.ownerid, playerbot_offline::Create, 0);\n\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopChangeNameDBPacket(DWORD ownerid, const char* name)\n\t{\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopSafeboxGetItemDBPacket(DWORD ownerid, DWORD itemid)\n\t{\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_SAFEBOX_GET_ITEM;\n\n\t\tTSubPacketGDSafeboxGetItem subpack{};\n\t\tsubpack.ownerid\t= ownerid;\n',
         '\t\treturn true;\n\t}\n\n\tvoid CShopManager::SendShopSafeboxGetItemDBPacket(DWORD ownerid, DWORD itemid)\n\t{\n\t\tplayerbot_offline::Sent(ownerid, playerbot_offline::WithdrawItem, itemid);\n\t\tTPacketGDNewIkarusShop pack{};\n\t\tpack.bSubHeader\t= SUBHEADER_GD_SAFEBOX_GET_ITEM;\n\n\t\tTSubPacketGDSafeboxGetItem subpack{};\n\t\tsubpack.ownerid\t= ownerid;\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\n\t\t\tTEMP_BUFFER buffer;\n\t\t\tbuffer.write(&pack, sizeof(pack));\n\t\t\tbuffer.write(&subpack, sizeof(subpack));\n\t\t\tdb_clientdesc->DBPacket(HEADER_GD_NEW_OFFLINESHOP, 0, buffer.read_peek(), buffer.size());\n\t\t\treturn result;\n\t\t};\n\n\t\t// searching safebox\n\t\tauto safebox = GetShopSafeboxByOwnerID(ownerid);\n',
         '\n\t\t\tTEMP_BUFFER buffer;\n\t\t\tbuffer.write(&pack, sizeof(pack));\n\t\t\tbuffer.write(&subpack, sizeof(subpack));\n\t\t\tdb_clientdesc->DBPacket(HEADER_GD_NEW_OFFLINESHOP, 0, buffer.read_peek(), buffer.size());\n\t\t\tplayerbot_offline::Complete(ownerid, playerbot_offline::WithdrawItem, itemid, result);\n\t\t\treturn result;\n\t\t};\n\n\t\t// searching safebox\n\t\tauto safebox = GetShopSafeboxByOwnerID(ownerid);\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\tauto shop = GetShopByOwnerID(ownerid);\n\t\tif (!shop)\n\t\t\treturn false;\n\n\t\tshop->ModifyItemPrice(itemid, price);\n\t\treturn true;\n\t}\n\n\t//FILTER\n\tbool CShopManager::RecvShopFilterRequestClientPacket(LPCHARACTER ch, const TFilterInfo& filter)\n',
         '\t\tauto shop = GetShopByOwnerID(ownerid);\n\t\tif (!shop)\n\t\t\treturn false;\n\n\t\tshop->ModifyItemPrice(itemid, price);\n\t\tplayerbot_offline::Complete(ownerid, playerbot_offline::Edit, itemid);\n\t\treturn true;\n\t}\n\n\t//FILTER\n\tbool CShopManager::RecvShopFilterRequestClientPacket(LPCHARACTER ch, const TFilterInfo& filter)\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t\tch->GetDesc()->Packet(&subpack, sizeof(subpack));*/\n\t}\n\n\tvoid ikashop::CShopManager::NotifyOwnerItemSold(LPCHARACTER ch, DWORD item_vnum, ITEM_COUNT item_count, YANG price)\n\t{\n\t\tif (!ch)\n\t\t\treturn;\n\n\t\tTSubPacketGCShopNotifyItemSold subpack{};\n\n\t\tTPacketGCNewIkarusShop pack{};\n',
         '\t\tch->GetDesc()->Packet(&subpack, sizeof(subpack));*/\n\t}\n\n\tvoid ikashop::CShopManager::NotifyOwnerItemSold(LPCHARACTER ch, DWORD item_vnum, ITEM_COUNT item_count, YANG price)\n\t{\n\t\tif (!ch || !ch->GetDesc())\n\t\t\treturn;\n\n\t\tTSubPacketGCShopNotifyItemSold subpack{};\n\n\t\tTPacketGCNewIkarusShop pack{};\n')
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '\t}\n\n\n\tvoid CShopManager::SendPopupMessage(LPCHARACTER ch, const std::string& message)\n\t{\n\t\tikashop::TSubPacketGCPopupMessage subpack{};\n\t\tstr_to_cstring(subpack.localeString, message.data());\n\n\t\tTPacketGCNewIkarusShop pack{};\n\t\tpack.header = HEADER_GC_NEW_OFFLINESHOP;\n',
         '\t}\n\n\n\tvoid CShopManager::SendPopupMessage(LPCHARACTER ch, const std::string& message)\n\t{\n\t\tif (!ch || !ch->GetDesc()) return;\n\t\tikashop::TSubPacketGCPopupMessage subpack{};\n\t\tstr_to_cstring(subpack.localeString, message.data());\n\n\t\tTPacketGCNewIkarusShop pack{};\n\t\tpack.header = HEADER_GC_NEW_OFFLINESHOP;\n')
    edit(os.path.join(db, 'ClientManagerIkarusShop.cpp'),
         '\t// searching shop\n\tauto shop = m_offlineshopShopCache.Get(subpack.ownerid);\n\tif(!shop)\n\t{\n\t\tsys_err("cannot find buy target item %u (owner %u , buyer %u) ", subpack.itemid, subpack.ownerid, subpack.guestid);\n\t\treturn false;\n\t}\n\n\t// searching item\n\tauto itemIter = shop->itemsmap.find(subpack.itemid);\n\tif(itemIter == shop->itemsmap.end())\n\t{\n\t\tsys_err("cannot find buy target item %u (owner %u , buyer %u) ", subpack.itemid, subpack.ownerid, subpack.guestid);\n\t\treturn false;\n\t}\n\n\tauto item = itemIter->second;\n\n',
         '\t// searching shop\n\tauto shop = m_offlineshopShopCache.Get(subpack.ownerid);\n\tif(!shop)\n\t{\n\t\tsys_err("cannot find buy target item %u (owner %u , buyer %u) ", subpack.itemid, subpack.ownerid, subpack.guestid);\n\t\tSendIkarusShopBuyLockedItemPacket(peer, 0, subpack.guestid, subpack.itemid);\n\t\treturn false;\n\t}\n\n\t// searching item\n\tauto itemIter = shop->itemsmap.find(subpack.itemid);\n\tif(itemIter == shop->itemsmap.end())\n\t{\n\t\tsys_err("cannot find buy target item %u (owner %u , buyer %u) ", subpack.itemid, subpack.ownerid, subpack.guestid);\n\t\tSendIkarusShopBuyLockedItemPacket(peer, 0, subpack.guestid, subpack.itemid);\n\t\treturn false;\n\t}\n\n\tauto item = itemIter->second;\n\n')
    edit(os.path.join(db, 'ClientManagerIkarusShop.cpp'),
         '\t\t\tikashop::ENotificationType::SELLER_SOLD_ITEM, subpack.ownerid, item->vnum, "", itemPrice);\n#endif\n\t}\n\n\telse\n\t\tsys_err("cannot find buy target item %u (owner %u , buyer %u) ", subpack.itemid, subpack.ownerid, subpack.guestid);\n\treturn true;\n}\n\nbool CClientManager::RecvIkarusShopBuyItemPacket(CPeer* peer, const char* data)\n{\n',
         '\t\t\tikashop::ENotificationType::SELLER_SOLD_ITEM, subpack.ownerid, item->vnum, "", itemPrice);\n#endif\n\t}\n\n\telse\n\t{\n\t\tSendIkarusShopBuyLockedItemPacket(peer, 0, subpack.guestid, subpack.itemid);\n\t\tsys_err("cannot find buy target item %u (owner %u , buyer %u) ", subpack.itemid, subpack.ownerid, subpack.guestid);\n\t}\n\treturn true;\n}\n\nbool CClientManager::RecvIkarusShopBuyItemPacket(CPeer* peer, const char* data)\n{\n')

def apply_refine_quality_of_life(game):
    # Refine QoL, napisane i przetestowane w grze na mt2009/2.0.29 przez
    # Pawla "Pabloo" (Discord, 13 wrzesnia), przeniesione tutaj bez zmian w
    # zachowaniu. Dwie rzeczy, obie po stronie serwera:
    #
    #   * m_iRefineAdditionalCell nie byl inicjowany w konstruktorze postaci,
    #     wiec pierwsza sesja ulepszania czytala komorke zwoju ze smiecia.
    #   * "nie zamykaj okna": po probie serwer sam otwiera okno ulepszania
    #     jeszcze raz (RefineInformation), zamiast zostawiac gracza z zamknietym.
    #
    # Nie ma tu auto-refine: kazda proba nadal wymaga pakietu od gracza, a cala
    # logika ulepszania zostaje po stronie serwera. Zabezpieczenie jednej
    # sekundy zostaje - przeniesione ZA podstawowe walidacje, bo przy keep-open
    # wczesniejsze ClearRefineMode() + return zamykalo okno i zostawialo sesje
    # refine w zlym stanie. Nowe sprawdzenia NPC/dystansu z 2.0.29 zostaja
    # nietkniete, a REFINE_TYPE_MONEY_ONLY (Wieza Demona) celowo nie dostaje
    # keep-open.
    #
    # Przelacznik to flaga specjalna "refine.keep_open": przezywa relog, jest
    # wysylana do klienta i wlacza sie komenda /refine_keep_open 1.
    # UWAGA: kliencka polowa (dwa checkboxy i potwierdzanie Enterem w
    # uirefine.py) NIE jedzie w tej paczce - linux-port/client-root nie zawiera
    # uirefine.py ani special_flags.py, wiec to osobna zmiana klienta i osobne
    # wydanie klienta.
    edit(os.path.join(game, 'char.h'),
         '\t\tDWORD\t\t\tGetRefineNPCVID() { return m_dwRefineNPCVID; }\n',
         '\t\tDWORD\t\t\tGetRefineNPCVID() { return m_dwRefineNPCVID; }\n'
         '\t\tint\t\t\t\tGetRefineAdditionalCell() const { return m_iRefineAdditionalCell; }\n')
    # Bez tego pierwsza sesja ulepszania w zyciu postaci czyta niezainicjowana
    # komorke: osobny, samodzielny fix bezpieczenstwa.
    edit(os.path.join(game, 'char.cpp'),
         '\tm_bUnderRefine = false;\n\n\t// REFINE_NPC\n\tm_dwRefineNPCVID = 0;\n',
         '\tm_bUnderRefine = false;\n\tm_iRefineAdditionalCell = -1;\n\n\t// REFINE_NPC\n\tm_dwRefineNPCVID = 0;\n')
    edit(os.path.join(game, 'cmd.cpp'),
         'ACMD(do_setblockmode);\n',
         'ACMD(do_setblockmode);\nACMD(do_refine_keep_open);\n')
    edit(os.path.join(game, 'cmd.cpp'),
         '\t{ "setblockmode",\tdo_setblockmode,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n',
         '\t{ "setblockmode",\tdo_setblockmode,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n'
         '\t{ "refine_keep_open",\tdo_refine_keep_open,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n')
    edit(os.path.join(game, 'cmd_general.cpp'),
         'ACMD(do_setblockmode)\n{\n\tchar arg1[256];\n\tone_argument(argument, arg1, sizeof(arg1));\n\n'
         '\tif (*arg1)\n\t{\n\t\tBYTE flag = 0;\n\t\tstr_to_number(flag, arg1);\n\t\tch->SetBlockMode(flag);\n\t}\n}\n',
         'ACMD(do_setblockmode)\n{\n\tchar arg1[256];\n\tone_argument(argument, arg1, sizeof(arg1));\n\n'
         '\tif (*arg1)\n\t{\n\t\tBYTE flag = 0;\n\t\tstr_to_number(flag, arg1);\n\t\tch->SetBlockMode(flag);\n\t}\n}\n'
         '\n'
         '// Refine QoL: "nie zamykaj okna". skipSave=false, bo wybor ma przezyc relog.\n'
         'ACMD(do_refine_keep_open)\n{\n\tchar arg1[256];\n\tone_argument(argument, arg1, sizeof(arg1));\n\n'
         '\tif (*arg1)\n\t{\n\t\tBYTE flag = 0;\n\t\tstr_to_number(flag, arg1);\n'
         '\t\tch->SetSpecialFlag("refine.keep_open", flag ? 1 : 0, false);\n\t}\n}\n')
    edit(os.path.join(game, 'constants.cpp'),
         '\tif (flag == "shop_unlock_slot")\n\t\treturn true;\n',
         '\tif (flag == "refine.keep_open")\n\t\treturn true;\n\n'
         '\tif (flag == "shop_unlock_slot")\n\t\treturn true;\n')
    # Stan sesji zapamietany na wejsciu, bo ClearRefineMode() kasuje i NPC, i
    # komorke zwoju, a keep-open musi znac oba. Cooldown znika stad i wraca
    # nizej, za walidacjami.
    edit(os.path.join(game, 'input_main.cpp'),
         '\t// fix bug: if fast clicked with autowindow open it could somehow upgrade with jumping above refine level like from +4 to +6 without taking money or upgrade items for +5\n'
         '\tint iPulse = thecore_pulse();\n'
         '\tif (iPulse - ch->GetRefineTime() < PASSES_PER_SEC(1))\n'
         '\t{\n'
         '\t\tch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("WAIT_BEFORE_NEXT_REFINE"));\n'
         '\t\tch->ClearRefineMode();\n'
         '\t\treturn;\n'
         '\t}\n\n',
         '\t// Refine QoL (Pabloo): stan sesji zapamietany zanim cokolwiek ja wyczysci.\n'
         '\tconst bool bKeepRefineOpen = ch->GetSpecialFlag("refine.keep_open") != 0;\n'
         '\tconst int iRefineAdditionalCell = ch->GetRefineAdditionalCell();\n'
         '\tconst DWORD dwRefineNPCVID = ch->GetRefineNPCVID();\n\n')
    edit(os.path.join(game, 'input_main.cpp'),
         '\tch->SetRefineTime();\n\n\tif (p->type == REFINE_TYPE_NORMAL ||\n',
         '\t// fix bug: if fast clicked with autowindow open it could somehow upgrade with jumping above refine level like from +4 to +6 without taking money or upgrade items for +5\n'
         '\t// Za walidacjami, nie przed nimi: przy keep-open wczesniejszy return\n'
         '\t// zamykal okno i zostawial sesje refine w zlym stanie.\n'
         '\tconst int iPulse = thecore_pulse();\n'
         '\tif (iPulse - ch->GetRefineTime() < PASSES_PER_SEC(1))\n'
         '\t{\n'
         '\t\tch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("WAIT_BEFORE_NEXT_REFINE"));\n'
         '\t\tch->ClearRefineMode();\n'
         '\t\treturn;\n'
         '\t}\n\n'
         '\tch->SetRefineTime();\n\n\tif (p->type == REFINE_TYPE_NORMAL ||\n')
    # Po ClearRefineMode(): okno otwarte ponownie, jesli gracz o to prosil i
    # jesli przedmiot nadal istnieje. Przy zwoju dodatkowo sprawdzamy, czy w
    # zapamietanej komorce nadal lezy poprawny zwoj - to naprawia przypadek
    # zuzycia ostatniego Zwoju Blogoslawienstwa.
    edit(os.path.join(game, 'input_main.cpp'),
         '\t}\n\n\tch->ClearRefineMode();\n}\n\n#ifdef ENABLE_ACCE_COSTUME_SYSTEM\n',
         '\t}\n\n\tch->ClearRefineMode();\n\n'
         '\tif (bKeepRefineOpen)\n'
         '\t{\n'
         '\t\tLPITEM refreshedItem = ch->GetInventoryItem(p->pos);\n\n'
         '\t\tif (refreshedItem)\n'
         '\t\t{\n'
         '\t\t\tif (p->type == REFINE_TYPE_NORMAL ||\n'
         '\t\t\t\tp->type == REFINE_TYPE_FISHER ||\n'
         '\t\t\t\tp->type == REFINE_TYPE_HERB_KNIFE ||\n'
         '\t\t\t\tp->type == REFINE_TYPE_PICKAXE)\n'
         '\t\t\t{\n'
         '\t\t\t\tLPCHARACTER refineCh = CHARACTER_MANAGER::instance().Find(dwRefineNPCVID);\n\n'
         '\t\t\t\tif (refineCh)\n'
         '\t\t\t\t{\n'
         '\t\t\t\t\tint distance = DISTANCE_APPROX((ch->GetX() - refineCh->GetX()), (ch->GetY() - refineCh->GetY()));\n\n'
         '\t\t\t\t\tif (distance <= 2000)\n'
         '\t\t\t\t\t{\n'
         '\t\t\t\t\t\tch->SetRefineNPC(refineCh);\n\n'
         '\t\t\t\t\t\tif (!ch->RefineInformation(p->pos, p->type))\n'
         '\t\t\t\t\t\t\tch->SetRefineNPC(NULL);\n'
         '\t\t\t\t\t}\n'
         '\t\t\t\t}\n'
         '\t\t\t}\n'
         '\t\t\telse if (p->type == REFINE_TYPE_SCROLL ||\n'
         '\t\t\t\tp->type == REFINE_TYPE_NO_REDUCTION_WHEN_FAIL ||\n'
         '\t\t\t\tp->type == REFINE_TYPE_UP_TO_3TH_LEVEL ||\n'
         '\t\t\t\tp->type == REFINE_TYPE_BDRAGON)\n'
         '\t\t\t{\n'
         '\t\t\t\tLPITEM refineScroll = NULL;\n\n'
         '\t\t\t\tif (iRefineAdditionalCell >= 0)\n'
         '\t\t\t\t\trefineScroll = ch->GetInventoryItem(iRefineAdditionalCell);\n\n'
         '\t\t\t\tif (refineScroll &&\n'
         '\t\t\t\t\trefineScroll->GetType() == ITEM_USE &&\n'
         '\t\t\t\t\trefineScroll->GetSubType() == USE_TUNING &&\n'
         '\t\t\t\t\trefineScroll->GetVnum() != refreshedItem->GetVnum())\n'
         '\t\t\t\t{\n'
         '\t\t\t\t\tch->RefineInformation(p->pos, p->type, iRefineAdditionalCell);\n'
         '\t\t\t\t}\n'
         '\t\t\t}\n'
         '\t\t}\n'
         '\t}\n'
         '}\n\n#ifdef ENABLE_ACCE_COSTUME_SYSTEM\n')


def apply_affect_remove_collect(game):
    # web_admin.quest takes its own speed effects off before adding a new one,
    # and it does it by name rather than with remove_all_collect - that would
    # also strip the potions, buffs and blessings a player earned. It calls
    # affect.remove_collect; this engine binds remove_all_collect and nothing
    # else, so that call was a nil value. The quest died on it, never reached
    # the line that writes its result, and left the panel's queue row holding
    # the quest's own claim stamp for ever - which the panel then showed as
    # "Cos poszlo nie tak (w1x257t780)" (Sammy Suricate, 13 September). Bind
    # the function it actually calls.
    edit(os.path.join(game, 'questlua_affect.cpp'),
         '\tALUA(affect_remove_all_collect)\n',
         '\t// playerbot/panel: affect.remove_collect (playerbotify.py).\n'
         '\t//\n'
         '\t// This engine binds remove_all_collect and not this one, so web_admin.quest\n'
         '\t// - which takes its own speed effects off by name before adding a new one,\n'
         '\t// rather than stripping everything the player earned - died on a nil\n'
         '\t// function, never wrote its result, and left the queue row holding the\n'
         "\t// quest's claim stamp for ever.\n"
         '\t//\n'
         '\t// affect_add_collect above sums into one affect per point type\n'
         '\t// (FindAffect(AFFECT_COLLECT, point_type)), so there is exactly one to take\n'
         '\t// off. r40250 matches on the value because there every call makes its own\n'
         '\t// affect; here that would never match an accumulated one, so the value is\n'
         '\t// accepted and ignored.\n'
         '\tALUA(affect_remove_collect)\n'
         '\t{\n'
         '\t\tif (!lua_isnumber(L, 1))\n'
         '\t\t{\n'
         '\t\t\tsys_err("invalid argument");\n'
         '\t\t\treturn 0;\n'
         '\t\t}\n'
         '\n'
         '\t\tLPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();\n'
         '\n'
         '\t\tif (ch == NULL)\n'
         '\t\t\treturn 0;\n'
         '\n'
         '\t\tBYTE point_type = (BYTE) lua_tonumber(L, 1);\n'
         '\n'
         '\t\tif (point_type >= POINT_MAX_NUM || point_type < 1)\n'
         '\t\t\treturn 0;\n'
         '\n'
         '\t\tCAffect* pkAff = ch->FindAffect(AFFECT_COLLECT, point_type);\n'
         '\n'
         '\t\tif (pkAff)\n'
         '\t\t\tch->RemoveAffect(pkAff);\n'
         '\n'
         '\t\treturn 0;\n'
         '\t}\n'
         '\n'
         '\tALUA(affect_remove_all_collect)\n',
         marker='ALUA(affect_remove_collect)')
    edit(os.path.join(game, 'questlua_affect.cpp'),
         '\t\t\t{ "remove_all_collect",\taffect_remove_all_collect\t},\n',
         '\t\t\t{ "remove_collect",\t\taffect_remove_collect\t\t},\n'
         '\t\t\t{ "remove_all_collect",\taffect_remove_all_collect\t},\n',
         marker='{ "remove_collect",')


def apply_playerbot_pvp_challenges(game):
    # Wyzwanie na pojedynek dociera do bota.
    #
    # CPVPManager::Insert to zgoda obustronna: pierwsze wywolanie tworzy CPVP i
    # mowi ofierze "%s challenged you to a battle", drugie - z drugiej strony -
    # dochodzi do Agree() i walka rusza. Gracz pisze /pvp <vid>; bot nie ma
    # klienta, ktory odpisze tym samym, wiec wyzwanie bota wisialo bez
    # odpowiedzi w nieskonczonosc.
    #
    # Hak siedzi na KONCU Insert, ktory jest osiagany dokladnie raz na nowy
    # pojedynek: galaz wyzej (Find + Agree) wraca wczesniej, gdy para juz
    # istnieje. Dzieki temu odpowiedz bota - ktora tez jest Insert - nie zapisze
    # sama siebie jako nowego wyzwania.
    #
    # Czasu tu nie stemplujemy: ile bot czeka przed zgoda, to sprawa jego
    # zachowania, a nie silnika.
    edit(os.path.join(game, 'pvp.cpp'),
         '#include "war_map.h"\n',
         '#include "war_map.h"\n#include "playerbot_pvp_policy.h"\n',
         marker='#include "playerbot_pvp_policy.h"\n')
    edit(os.path.join(game, 'pvp.cpp'),
         '\t// END_OF_NOTIFY_PVP_MESSAGE\n}\n',
         '\t// END_OF_NOTIFY_PVP_MESSAGE\n'
         '\n'
         '\t// Bot nie ma klienta, ktory odpisze /pvp - zostawiamy wyzwanie\n'
         '\t// jego tickowi (AcceptPlayerBotPvpChallenge).\n'
         '\tif (pkVictim->GetDesc() && pkVictim->GetDesc()->IsBot())\n'
         '\t\tplayerbot_pvp::NoteChallenge(pkChr->GetPlayerID(), pkVictim->GetPlayerID());\n'
         '}\n',
         marker='playerbot_pvp::NoteChallenge(')


def apply_fishing_min_level(game):
    # Lowienie od 30 poziomu zamiast od 50 (prosba operatora).
    #
    # CHARACTER::fishing() na tej linii odmawia ponizej piecdziesiatki i to jest
    # jedyne miejsce, ktore o tym decyduje po stronie silnika - reszta bramek
    # (mapa, przepustka, przyneta) zostaje bez zmian. Nakladka pyta o ten sam
    # prog przez PLAYERBOT_FISHING_MIN_LEVEL w dwoch miejscach (activities.h,
    # travel.h), zeby bot ponizej progu nie szedl nad wode, ktora i tak by go
    # odprawila; te dwie liczby musza sie zgadzac.
    # The staged char.cpp carries this comment in English, as the engine edits
    # all do; the Polish one here no longer matched it and stopped the script.
    edit(os.path.join(game, 'char.cpp'),
         '\tif (GetLevel() < 50)\n\t\treturn;\n',
         '\t// Fishing from thirty - see PLAYERBOT_FISHING_MIN_LEVEL.\n'
         '\tif (GetLevel() < 30)\n\t\treturn;\n',
         marker='\t// Fishing from thirty - see PLAYERBOT_FISHING_MIN_LEVEL.\n')


def apply_playerbot_monkey_doors(game):
    # Drzwi GOTO w Lochu Malp przenosza bota najwyzej raz na czas pobytu w
    # komorze.
    #
    # Loch to jedenascie komor polaczonych wylacznie NPC typu GOTO, a
    # warp_npc_event przenosi kazdego w promieniu trzystu jednostek, dwa razy na
    # sekunde. Bot, ktory przejdzie przez drzwi, laduje obok drzwi prowadzacych
    # prosto z powrotem - i jesli zatrzyma sie tam, zeby walczyc, to zdarzenie
    # odsylalo go tam, skad przyszedl, po kilku sekundach. Zmierzone na 303
    # powrotach do komory wejsciowej: mediana 65 s, 29% w ciagu pietnastu
    # sekund, a swiadome przejscie nie jest mozliwe przed uplywem czasu pobytu.
    # Stad "caly loch w jednej linii": 905 przejsc na mapie 108, prawie
    # wszystkie 0<->7 i 0<->1.
    #
    # Czas blokady i czas pobytu to jedna stala (playerbot_monkey_policy.h), bo
    # tylko wtedy przejscie wybrane przez bota nigdy nie trafi na blokade, a
    # odbicie zawsze. Gracza to nie dotyczy.
    edit(os.path.join(game, 'char.cpp'),
         '#include "pvp.h"\n#include "party.h"\n',
         '#include "pvp.h"\n#include "party.h"\n#include "playerbot_monkey_policy.h"\n',
         marker='#include "playerbot_monkey_policy.h"\n')
    edit(os.path.join(game, 'char.cpp'),
         '\t\t\t\t\tpkChr->Show(pkChr->GetMapIndex(), m_lTargetX, m_lTargetY);\n'
         '\t\t\t\t\tpkChr->Stop();\n',
         '\t\t\t\t\t// A door moves a playerbot once per chamber dwell and no more.\n'
         '\t\t\t\t\t// A bot comes through a door beside the door that leads straight\n'
         '\t\t\t\t\t// back, and one that stopped there to fight was returned by this\n'
         '\t\t\t\t\t// event within seconds - the bot never chose it, and the dungeon\n'
         '\t\t\t\t\t// was walked in one line. See playerbot_monkey_policy.h.\n'
         '\t\t\t\t\tif (pkChr->GetDesc() && pkChr->GetDesc()->IsBot())\n'
         '\t\t\t\t\t{\n'
         '\t\t\t\t\t\tconst DWORD now = get_dword_time();\n'
         '\t\t\t\t\t\tif (playerbot_monkey::IsGotoCrossingBlocked(pkChr->GetPlayerID(), now))\n'
         '\t\t\t\t\t\t\treturn;\n'
         '\t\t\t\t\t\tplayerbot_monkey::NoteGotoCrossing(pkChr->GetPlayerID(), now);\n'
         '\t\t\t\t\t}\n'
         '\t\t\t\t\tpkChr->Show(pkChr->GetMapIndex(), m_lTargetX, m_lTargetY);\n'
         '\t\t\t\t\tpkChr->Stop();\n',
         marker='playerbot_monkey::NoteGotoCrossing(')


def apply_playerbot_party_invites(game):
    # Zaproszenie gracza do party dociera do bota.
    #
    # CHARACTER::PartyInvite konczy sie wyslaniem HEADER_GC_PARTY_INVITE na
    # deskryptor zapraszanego. Bot ma deskryptor, ale nie ma za nim klienta,
    # wiec pakiet nie dociera do nikogo, nikt nie klika "Akceptuj" i po
    # dziesieciu sekundach zdarzenie zaproszenia wygasa - zapraszanie bota nie
    # robilo dotad dosłownie nic i nie zostawialo po sobie sladu.
    #
    # Silnik nie moze odpowiedziec za bota, bo akceptacja jest metoda LIDERA
    # (leader->PartyInviteAccept(guest)) i musi sie wykonac, dopoki zdarzenie
    # zyje. Wiec silnik tylko zapisuje, ze bot zostal zaproszony, a odpowiada
    # tick bota (AcceptPlayerBotPartyInvite) - tam, gdzie mieszkaja wszystkie
    # inne decyzje botow. Warunki dolaczenia zostaja silnikowe: to samo
    # krolestwo, roznica trzydziestu poziomow i wolne miejsce w osmioosobowej
    # druzynie.
    edit(os.path.join(game, 'char.cpp'),
         '#include "pvp.h"\n#include "party.h"\n',
         '#include "pvp.h"\n#include "party.h"\n#include "playerbot_party_policy.h"\n',
         marker='#include "playerbot_party_policy.h"\n')
    edit(os.path.join(game, 'char.cpp'),
         '\tTPacketGCPartyInvite p;\n'
         '\tp.header = HEADER_GC_PARTY_INVITE;\n',
         '\t// Bot nie ma klienta, ktory nacisnie "Akceptuj" - zostawiamy\n'
         '\t// zaproszenie jego tickowi i nie wysylamy pakietu w prozne.\n'
         '\tif (pchInvitee->GetDesc() && pchInvitee->GetDesc()->IsBot())\n'
         '\t{\n'
         '\t\tplayerbot_party::NoteInvite(GetPlayerID(), pchInvitee->GetPlayerID(),\n'
         '\t\t\t\t(uint32_t) get_global_time());\n'
         '\t\treturn;\n'
         '\t}\n'
         '\n'
         '\tTPacketGCPartyInvite p;\n'
         '\tp.header = HEADER_GC_PARTY_INVITE;\n',
         marker='playerbot_party::NoteInvite(')
    # Dlaczego bot nie odpowiedzial na zaproszenie, musi powiedziec log.
    #
    # Kazda odmowa ponizej konczy sie ChatPacket do zapraszajacego i return, a
    # gracz, ktory tej linii nie przeczyta, zglasza tylko "bot mnie
    # zignorowal". W 102 plikach syslog nie ma ani jednego przyjecia
    # zaproszenia, a zadna z bramek silnika nie tlumaczy stu procent - wiec
    # zamiast kolejnej hipotezy niech nastepny test poda powod.
    edit(os.path.join(game, 'char.cpp'),
         'void CHARACTER::PartyInvite(LPCHARACTER pchInvitee)\n{\n',
         'void CHARACTER::PartyInvite(LPCHARACTER pchInvitee)\n{\n'
         '\tif (pchInvitee && pchInvitee->GetDesc() && pchInvitee->GetDesc()->IsBot())\n'
         '\t\tsys_log(0, "PLAYERBOT_PARTY: invite pid=%u name=%s bot_pid=%u bot=%s '
         'errcode=%d my_party=%d bot_party=%d my_level=%d bot_level=%d",\n'
         '\t\t\t\tGetPlayerID(), GetName(), pchInvitee->GetPlayerID(), pchInvitee->GetName(),\n'
         '\t\t\t\t(int) IsPartyJoinableCondition(this, pchInvitee),\n'
         '\t\t\t\tGetParty() ? 1 : 0, pchInvitee->GetParty() ? 1 : 0,\n'
         '\t\t\t\t(int) GetLevel(), (int) pchInvitee->GetLevel());\n',
         marker='PLAYERBOT_PARTY: invite pid=')


def apply_gm_gameplay(game):
    """A GM character on this line is its owner playing the game.

    The engine treats a GM as staff: Ikarus refuses every shop operation to
    anybody above GM_PLAYER (CheckGMLevel), IsLevelViewable hides the level,
    and both SetLevel and the login block force PK_MODE_PROTECT. On a
    single-player world the GM characters of the admin account are the
    player's own characters, so a GM could look at a bot's shop and not buy
    from it, and nobody saw its level. The badge (AFF_YMIR) stays, and so does
    every other check - money, room, anti-flags, the level protection below
    PK_PROTECT_LEVEL. CanOpenShop waives the kill count for a GM as it does
    for a bot. From the audit of 14 September (gm_gameplayify.py).
    """
    edit(os.path.join(game, 'ikarus_shop_manager.cpp'),
         '#define ENABLE_IKASHOP_GM_PROTECTION\n'
         'static bool CheckGMLevel(LPCHARACTER ch) \n'
         '{\n'
         '\treturn\n'
         '#ifdef ENABLE_IKASHOP_GM_PROTECTION\n'
         '\t\tch->GetGMLevel() == GM_PLAYER || test_server;\n'
         '#else\n'
         '\t\ttrue;\n'
         '#endif\n'
         '}',
         '// playerbot: a GM plays the single-player world, and Ikarus serves it\n'
         '// like anybody (playerbotify.py, apply_gm_gameplay).\n'
         'static bool CheckGMLevel(LPCHARACTER ch)\n'
         '{\n'
         '\treturn ch != nullptr;\n'
         '}')
    edit(os.path.join(game, 'char.cpp'),
         '\t\tif (!test_server && IsGM())\n'
         '\t\t\treturn false;\n'
         '\n'
         '\t\treturn true;',
         '\t\t// playerbot: a GM\'s level shows like anybody\'s.\n'
         '\t\treturn true;')
    edit(os.path.join(game, 'char.cpp'),
         '\t\telse if (GetGMLevel() != GM_PLAYER)\n'
         '\t\t\tSetPKMode(PK_MODE_PROTECT);\n',
         '\t\t// playerbot: a GM is protected by its level like anybody, not by rank.\n')
    edit(os.path.join(game, 'char.cpp'),
         '\t\t\tm_afAffectFlag.Set(AFF_YMIR);\n'
         '\t\t\tm_bPKMode = PK_MODE_PROTECT;',
         '\t\t\tm_afAffectFlag.Set(AFF_YMIR);\n'
         '\t\t\t// playerbot: the GM badge stays, the forced protection does not.')
    edit(os.path.join(game, 'char_shop.cpp'),
         'bool CHARACTER::CanOpenShop()\n'
         '{\n',
         'bool CHARACTER::CanOpenShop()\n'
         '{\n'
         '\t// playerbot: a GM opens a stall without the kill count.\n'
         '\tif (GetGMLevel() > GM_PLAYER)\n'
         '\t\treturn true;\n',
         marker='a GM opens a stall without the kill count')


def apply_party_pickup_to_owner(game):
    # CHARACTER::PickupItem's party branch - a party member picking up an item
    # another member owns - put the item into the owner's bag with two faults
    # of its own (Kenny, 2.0.47; reported by mkls6649). It went straight to an
    # empty cell, where the owner's own pickup first calls AutoStackItem, so
    # every potion a party member picked up for somebody took a slot of its
    # own. And it told the owner that the member who picked it up "receives"
    # it: GetName() there is the picker's, and with bots in a player's party
    # the picker is nearly always a bot. The stack goes first now, exactly as
    # in the owner's own branch, and whatever a full stack cannot take goes on
    # to the empty cell as before; both messages name the owner.
    edit(os.path.join(game, 'char_item.cpp'),
         '\t\tint iEmptyCell = -1;\n'
         '\t\tif (!(owner && (iEmptyCell = owner->GetEmptyInventoryEx(item)) != -1))\n',
         '\t\t// A stackable the owner already carries joins that stack first, as the\n'
         "\t\t// owner's own pickup above does: straight to an empty cell, every potion\n"
         '\t\t// a party member picked up for somebody took a slot of its own. What a\n'
         '\t\t// full stack cannot take goes on to the empty cell below.\n'
         '\t\tauto finalItem = owner->AutoStackItem(item);\n'
         '\t\tif (finalItem)\n'
         '\t\t{\n'
         '\t\t\tif (owner == this)\n'
         '\t\t\t\tChatPacketRecieveItem(this, finalItem, 1);\n'
         '\t\t\telse\n'
         '\t\t\t{\n'
         '\t\t\t\towner->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s receives %s."), owner->GetName(), finalItem->GetName());\n'
         '\t\t\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("Item Trade: %s, %s"), owner->GetName(), finalItem->GetName());\n'
         '\t\t\t}\n'
         '\t\t\tif (finalItem->GetType() == ITEM_QUEST)\n'
         '\t\t\t\tquest::CQuestManager::instance().PickupItem(owner->GetPlayerID(), finalItem);\n'
         '\t\t\treturn true;\n'
         '\t\t}\n'
         '\n'
         '\t\tint iEmptyCell = -1;\n'
         '\t\tif (!(owner && (iEmptyCell = owner->GetEmptyInventoryEx(item)) != -1))\n',
         marker='\t\tauto finalItem = owner->AutoStackItem(item);\n')
    edit(os.path.join(game, 'char_item.cpp'),
         '\t\t\towner->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s receives %s."), GetName(), item->GetName());\n',
         '\t\t\towner->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s receives %s."), owner->GetName(), item->GetName());\n')


def apply_gm_panel(game):
    # Panel GM (F9) i "Zapisane miejsca" od OskarPWA. Na linii r40250 to jest
    # patch 0009; tutaj ta sama rzecz jako edycje na tekscie, bo jego cmd_gm.cpp
    # i cmd.cpp to nasze pliki przepuszczone przez edytor (koreanskie komentarze
    # nie wracaja z tej podrozy), wiec nie daja sie ani zdiffowac, ani skopiowac
    # w calosci.
    #
    # Komendy botadmin_* - okno F10 jego klienta - sa pominiete: wolaja
    # GetBotLines, GetAchievementWinner i GetActivitySummary z managera jego
    # forka, ktorych nasz CPlayerBotManager nie ma. Panel F9 nie dotyka zadnej
    # z nich.
    #
    # Sam kod komend lezy obok, w port/gm_panel_commands.cpp.txt: cztery tysiace
    # linii C++ w literale pythonowym nie dawalyby sie ani czytac, ani diffowac.
    # Plik trzymany jest z CRLF, a edit() sam zamienia kazde \n na koncowki
    # pliku docelowego - stad normalizacja do LF tutaj, inaczej wyszlyby
    # podwojne CR.
    fragment = read(os.path.join(HERE, 'gm_panel_commands.cpp.txt'))
    fragment = fragment.replace(b'\r\n', b'\n').decode('latin-1')

    # Deklaracje biora sie z samych definicji, zeby komenda dopisana kiedys do
    # fragmentu nie mogla zostac bez deklaracji - to jedyna para w tej zmianie,
    # ktora moze sie rozjechac po cichu.
    names = [line[5:-1] for line in fragment.split('\n')
             if (line.startswith('ACMD(do_gmpanel_') or line.startswith('ACMD(do_botadmin'))
             and line.endswith(')')]
    if len(names) != 37:
        raise SystemExit('playerbotify: %d komend panelu we fragmencie, '
                         'oczekiwano 37 (31 gmpanel_* + 6 botadmin*)' % len(names))

    # Poziom GM jest wyborem Oskara i zostaje: wszystko dla HIGH_WIZARD poza
    # nadawaniem rang (IMPLEMENTOR) oraz mapa i zapisanymi miejscami, ktore sa
    # sama nawigacja (LOW_WIZARD). Tabela cmd_info[] jest jedynym miejscem, w
    # ktorym te progi zyja - kazda komenda sprawdza sie o nia przed wykonaniem.
    # Okno F10 chodzi po calej populacji botow i potrafi dac im przedmiot,
    # wiec caly blok botadmin* siedzi na IMPLEMENTORZE - tak, jak zapowiada
    # komentarz Oskara nad tymi komendami.
    levels = {'do_gmpanel_addgm': 'GM_IMPLEMENTOR',
              'do_gmpanel_warp_map': 'GM_LOW_WIZARD',
              'do_gmpanel_waypoint': 'GM_LOW_WIZARD'}
    for name in names:
        if name.startswith('do_botadmin'):
            levels[name] = 'GM_IMPLEMENTOR'
    decls = ''.join('ACMD(%s);\n' % name for name in names)
    rows = ''.join('\t{ "%s",\t%s,\t0,\t\t\tPOS_DEAD,\t%s\t},\n'
                   % (name[3:], name, levels.get(name, 'GM_HIGH_WIZARD'))
                   for name in names)

    # Panel tworzy przedmioty prosto do skrytki i do sklepu z monetami, czyli
    # wola CSafebox::IsValidPosition, IsEmpty i Add. cmd_gm.cpp widzi stad samo
    # "class CSafebox;" z char.h, wiec bez tego naglowka piec wywolan w
    # do_gmpanel_createitem to "invalid use of incomplete type". Kotwica jest
    # naglowkiem silnika, nie naszym - taka przezyje kazda pozniejsza edycje.
    edit(os.path.join(game, 'cmd_gm.cpp'),
         '#include "BanManager.h"\n',
         '#include "BanManager.h"\n'
         '#include "safebox.h"\n',
         marker='#include "safebox.h"\n')

    # Fragment idzie na koniec kodu, przed linia z podpisem pakietu - ona jest
    # znacznikiem konca pliku, nie kodem.
    edit(os.path.join(game, 'cmd_gm.cpp'),
         "//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f\n",
         fragment + "\n//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f\n",
         marker='ACMD(do_gmpanel_lookup)\n')
    edit(os.path.join(game, 'cmd.cpp'),
         'ACMD(do_check_mob);\n',
         'ACMD(do_check_mob);\n' + decls,
         marker='ACMD(do_gmpanel_lookup);\n')
    edit(os.path.join(game, 'cmd.cpp'),
         '\t{ "check_mob", do_check_mob, \t0, POS_DEAD,\t\tGM_IMPLEMENTOR },\n',
         '\t{ "check_mob", do_check_mob, \t0, POS_DEAD,\t\tGM_IMPLEMENTOR },\n\n'
         + rows,
         marker='{ "gmpanel_lookup",')

    # Klient dowiaduje sie, ze siedzi na postaci GM-a, z jednej komendy czatu.
    # Wyslana od razu w SetPlayerProto psuje uscisk dloni Select->Game (na tym
    # etapie PlayerLoad deskryptor nie jest jeszcze zwiazany z postacia ani
    # przelaczony w PHASE_GAME), wiec idzie zwyklym zdarzeniem kilka sekund
    # pozniej. Nasz SetPlayerProto ma tu samo SetGMLevel() bez klamer - jego
    # wersja ma klamry, wiec kotwica jest nasza, nie jego.
    edit(os.path.join(game, 'char.cpp'),
         '#define ENABLE_GM_FLAG_FOR_LOW_WIZARD\n'
         'void CHARACTER::SetPlayerProto(const TPlayerTable * t)\n'
         '{\n'
         '\tif (!GetDesc() || !*GetDesc()->GetHostName())\n'
         '\t\tsys_err("cannot get desc or hostname");\n'
         '\telse\n'
         '\t\tSetGMLevel();\n',
         '#define ENABLE_GM_FLAG_FOR_LOW_WIZARD\n'
         '\n'
         'EVENTFUNC(gmpanel_flag_event)\n'
         '{\n'
         '\tchar_event_info* info = dynamic_cast<char_event_info*>( event->info );\n'
         '\tif (info == NULL)\n'
         '\t{\n'
         '\t\tsys_err("gmpanel_flag_event> <Factor> Null pointer");\n'
         '\t\treturn 0;\n'
         '\t}\n'
         '\n'
         '\tLPCHARACTER ch = info->ch;\n'
         '\n'
         '\tif (ch == NULL)\n'
         '\t\treturn 0;\n'
         '\n'
         '\t// Says only "you are a GM", nothing about the level or about which\n'
         '\t// commands that unlocks: the F9 panel is gated on this client-side,\n'
         '\t// and every action it sends is still checked against the real\n'
         '\t// gm_level in cmd_info[] before the server does anything.\n'
         '\tch->ChatPacket(CHAT_TYPE_COMMAND, "SetGMFlag");\n'
         '\treturn 0;\n'
         '}\n'
         '\n'
         'void CHARACTER::SetPlayerProto(const TPlayerTable * t)\n'
         '{\n'
         '\tif (!GetDesc() || !*GetDesc()->GetHostName())\n'
         '\t\tsys_err("cannot get desc or hostname");\n'
         '\telse\n'
         '\t{\n'
         '\t\tSetGMLevel();\n'
         '\t\t// Sending this here directly breaks the client\'s Select->Game\n'
         '\t\t// phase handshake - defer it past the login with the engine\'s own\n'
         '\t\t// one-shot event mechanism instead.\n'
         '\t\tif (GetGMLevel() > GM_PLAYER)\n'
         '\t\t{\n'
         '\t\t\tchar_event_info* info = AllocEventInfo<char_event_info>();\n'
         '\t\t\tinfo->ch = this;\n'
         '\t\t\tevent_create(gmpanel_flag_event, info, PASSES_PER_SEC(3));\n'
         '\t\t}\n'
         '\t}\n',
         marker='EVENTFUNC(gmpanel_flag_event)\n')

    # Klient pyta /gmpanel_check_gm przy kazdym wejsciu do gry (game.py,
    # OnUpdate po ~300 klatkach), a F9 i F10 wysylaja /gmpanel_open i
    # /botadmin. Z progiem HIGH_WIZARD/IMPLEMENTOR w cmd_info[] zwykly gracz
    # dostawal po kazdym teleporcie i logowaniu "Ta komenda nie istnieje." -
    # to samo, co po nacisnieciu F9 (NerrVoVy, 15.09). Te trzy komendy tylko
    # otwieraja okno albo zapalaja flage, wiec cmd_info[] wpuszcza je od
    # GM_PLAYER, a prog sprawdza sama komenda i zwyklemu graczowi nie
    # odpowiada nic. Kazda akcja panelu dalej sprawdza swoj prog w cmd_info[].
    for name, level in (('gmpanel_open', 'GM_HIGH_WIZARD'),
                        ('gmpanel_check_gm', 'GM_HIGH_WIZARD'),
                        ('botadmin', 'GM_IMPLEMENTOR')):
        edit(os.path.join(game, 'cmd.cpp'),
             '\t{ "%s",\tdo_%s,\t0,\t\t\tPOS_DEAD,\t%s\t},\n' % (name, name, level),
             '\t{ "%s",\tdo_%s,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n' % (name, name))
    edit(os.path.join(game, 'cmd_gm.cpp'),
         'ACMD(do_gmpanel_open)\n\n{\n\n\tch->ChatPacket(CHAT_TYPE_COMMAND, "OpenGMPanelWindow");\n',
         'ACMD(do_gmpanel_open)\n\n{\n\n'
         '\t// Registered for GM_PLAYER, so a player pressing F9 hears nothing\n'
         '\t// instead of "no such command"; the threshold is kept here.\n'
         '\tif (ch->GetGMLevel() < GM_HIGH_WIZARD)\n'
         '\t\treturn;\n'
         '\tch->ChatPacket(CHAT_TYPE_COMMAND, "OpenGMPanelWindow");\n',
         marker='a player pressing F9 hears nothing')
    edit(os.path.join(game, 'cmd_gm.cpp'),
         'ACMD(do_gmpanel_check_gm)\n\n{\n\n\tch->ChatPacket(CHAT_TYPE_COMMAND, "SetGMFlag");\n',
         'ACMD(do_gmpanel_check_gm)\n\n{\n\n'
         '\t// The client asks this on every entry into the game, GM or not.\n'
         '\tif (ch->GetGMLevel() < GM_HIGH_WIZARD)\n'
         '\t\treturn;\n'
         '\tch->ChatPacket(CHAT_TYPE_COMMAND, "SetGMFlag");\n',
         marker='The client asks this on every entry into the game')
    edit(os.path.join(game, 'cmd_gm.cpp'),
         'ACMD(do_botadmin)\n{\n\tch->ChatPacket(CHAT_TYPE_COMMAND, "OpenPlayerbotAdminWindow");\n',
         'ACMD(do_botadmin)\n{\n'
         '\t// F10 from a player: silence, the same as F9 (do_gmpanel_open).\n'
         '\tif (ch->GetGMLevel() < GM_IMPLEMENTOR)\n'
         '\t\treturn;\n'
         '\tch->ChatPacket(CHAT_TYPE_COMMAND, "OpenPlayerbotAdminWindow");\n',
         marker='F10 from a player: silence')


def apply_horse_rider_links(game):
    # Crash rdzenia w CHARACTER::HorseSummon (sizowski, 15.09: dwa w szesc
    # godzin przy ~2000 botow, oba z tym samym stosem CPlayerBotManager::Update
    # -> CHARACTER::StartRiding -> CHARACTER::HorseSummon+0x6e).
    #
    # Kon i jezdziec trzymaja wskazniki na siebie nawzajem: m_chHorse u
    # jezdzca, m_chRider u konia. Destroy() konia mial je rozlaczyc, ale mt2009
    # pyta tam "IsPC() && GetRider()", a jezdzca ma tylko kon (NPC) - warunek
    # nie jest prawdziwy nigdy. Kon zniszczony czymkolwiek innym niz
    # HorseSummon(false) wlasnego jezdzca zostawia mu wiszace m_chHorse, a
    # najblizsze StartRiding() wola HorseSummon(false), ktore siega do
    # zwolnionej pamieci.
    #
    # Co takiego konia niszczy: obszarowka. battle_is_attackable konczy sie na
    # CPVPManager::CanAttack, a ten odmawia tylko CHAR_TYPE_NPC/WARP/GOTO i
    # kazdemu innemu NPC odpowiada "tak" - wiec umiejetnosc z rozpryskiem bije
    # konia, ktory idzie za botem po zsiadnieciu na mapie lowieckiej
    # (SetPlayerBotRidingForTravel odsyla go tylko w strefie bezpiecznej).
    #
    # Dwie zmiany: Destroy rozlacza konia od jezdzca, ktory wciaz go trzyma -
    # to zamyka crash bez wzgledu na to, co konia zniszczylo - a przywolany kon
    # (taki, ktory ma jezdzca) nie jest celem niczyjego ciosu.
    edit(os.path.join(game, 'char.cpp'),
         '\tHorseSummon(false);\n'
         '\n'
         '\tif (IsPC() && GetRider())\n'
         '\t\tGetRider()->ClearHorseInfo();\n',
         '\tHorseSummon(false);\n'
         '\n'
         '\t// Playerbot: a horse destroyed by anything but its own rider\'s\n'
         '\t// HorseSummon(false) - a splash skill, most often - left the rider\n'
         '\t// holding m_chHorse, and the rider\'s next StartRiding() called\n'
         '\t// HorseSummon(false) on freed memory. "IsPC() && GetRider()" was never\n'
         '\t// true: only a horse has a rider.\n'
         '\tif (GetRider() && GetRider()->GetHorse() == this)\n'
         '\t\tGetRider()->ClearHorseInfo();\n',
         marker='true: only a horse has a rider.')
    edit(os.path.join(game, 'pvp.cpp'),
         '\tswitch (pkVictim->GetCharType())\n'
         '\t{\n'
         '\t\tcase CHAR_TYPE_NPC:\n'
         '\t\tcase CHAR_TYPE_WARP:\n'
         '\t\tcase CHAR_TYPE_GOTO:\n'
         '\t\t\treturn false;\n'
         '\t}\n',
         '\tswitch (pkVictim->GetCharType())\n'
         '\t{\n'
         '\t\tcase CHAR_TYPE_NPC:\n'
         '\t\tcase CHAR_TYPE_WARP:\n'
         '\t\tcase CHAR_TYPE_GOTO:\n'
         '\t\t\treturn false;\n'
         '\t}\n'
         '\n'
         '\t// Playerbot: a summoned horse is its rider\'s and nobody\'s target. The\n'
         '\t// switch above lets every other NPC through, so a splash skill beside\n'
         '\t// a dismounted rider killed the horse following it - and a horse\n'
         '\t// destroyed that way is what CHARACTER::Destroy failed to unlink.\n'
         '\tif (pkVictim->GetRider())\n'
         '\t\treturn false;\n',
         marker='a summoned horse is its rider')


def apply_gm_transfer_bots(game):
    # /transfer <bot> (Mat, RetroGracz38, NerrVoVy, 14.09): silnik robi
    # tch->WarpSet(), czyli kaze klientowi przelaczyc sie na rdzen mapy
    # docelowej i zdejmuje postac z sektora. Bot nie ma klienta, wiec zostawal
    # poza mapa, az ratunek stawial go w punkcie startowym jego wlasnej mapy -
    # "robi tp, ale jakby na start mapy". Bot na tym rdzeniu zmienia teraz mape
    # ta sama droga co AI (CPlayerBotManager::TransferBot), a o bocie na innym
    # rdzeniu GM dostaje odpowiedz zamiast "Transfer requested." - na mape
    # rdzenia, ktory go nie hostuje, bot nie przejdzie nigdy.
    edit(os.path.join(game, 'cmd_gm.cpp'),
         '\t\t\tTPacketGGTransfer pgg;\n',
         '\t\t\t// Playerbot: a bot on another core stays there - it cannot stand\n'
         '\t\t\t// on a map its own core does not host, and a WarpSet only takes it\n'
         '\t\t\t// off its sectree.\n'
         '\t\t\tif (CPlayerBotManager::instance().IsRegisteredBotPID(pkCCI->dwPID))\n'
         '\t\t\t{\n'
         '\t\t\t\tch->ChatPacket(CHAT_TYPE_INFO, "Bot %s jest na innym rdzeniu (mapa %ld) i nie przejdzie na mape tego rdzenia.", arg1, pkCCI->lMapIndex);\n'
         '\t\t\t\treturn;\n'
         '\t\t\t}\n'
         '\n'
         '\t\t\tTPacketGGTransfer pgg;\n',
         marker='a bot on another core stays there')
    edit(os.path.join(game, 'cmd_gm.cpp'),
         '\t//tch->Show(ch->GetMapIndex(), ch->GetX(), ch->GetY(), ch->GetZ());\n'
         '\ttch->WarpSet(ch->GetX(), ch->GetY(), ch->GetMapIndex());\n',
         '\t//tch->Show(ch->GetMapIndex(), ch->GetX(), ch->GetY(), ch->GetZ());\n'
         '\t// Playerbot: a bot has no client to reconnect, so it changes map the\n'
         '\t// way its own AI changes every other one.\n'
         '\tif (tch->GetDesc() && tch->GetDesc()->IsBot())\n'
         '\t{\n'
         '\t\tCPlayerBotManager::instance().TransferBot(tch, ch);\n'
         '\t\treturn;\n'
         '\t}\n'
         '\ttch->WarpSet(ch->GetX(), ch->GetY(), ch->GetMapIndex());\n',
         marker='CPlayerBotManager::instance().TransferBot(tch, ch);')


if __name__ == '__main__':
    if len(sys.argv) != 2 or not os.path.isdir(os.path.join(sys.argv[1], 'game', 'src')):
        raise SystemExit(__doc__)
    main(os.path.abspath(sys.argv[1]))
