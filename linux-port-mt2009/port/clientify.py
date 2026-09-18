# -*- coding: utf-8 -*-
"""Our edits to the mt2009 client's C++ (the package's Source Client).

Usage:  python clientify.py <Source Client dir>

The client's source is not in this repository any more than the server's is
(linux-port/fetch-sources.sh): the package ships it, and what is ours is this
list of exact-string edits, applied the way playerbotify.py applies the
server's - idempotent, found already applied, or failing on the anchor it
could not find. The client's files mix CRLF and LF, so an anchor that spans
lines is tried with both, and a one-line anchor takes the line end of the line
it sits on. tools/build-client.ps1 copies the package source to a short path
(MSBuild cannot open "..\\UserInterface\\Locale_inc.h" under a long one), links
the package's Extern and our staged server tree beside it - the client reads
the server's common/*.h, which is where INVENTORY_PAGE_COUNT and the feature
switches come from - runs this, and builds.

What the edits are:
  personality row   textTail.AttachPersonality / DetachPersonality: a bot's
                    personality on a row of its own between its name and its
                    guild. client-root/playerbot_status_tail.py calls it (with
                    hasattr, so a client without it draws nothing). l0st3k
                    wrote it first for client 2.0.13 in a tree we do not have;
                    this is the same interface rebuilt on AttachTitle's model.
  discord presence  l0st3k's Discord application (its name and images are
                    what a friend's Discord shows beside the player) and the
                    button's address - the two strings his exe differs in from
                    the package's, read out of both binaries; the map table and
                    the texts are the package's in both.
  four pages        the client's half of playerbotify.py's
                    apply_four_inventory_pages. The slot map itself comes from
                    the server's common/length.h, which this build compiles
                    against; what is left is the belt's cells passing 255: a
                    quickslot's position and a shop sale's cell are WORDs on
                    the wire now, as on the server.
  co-op game host   the world is entered and every warp followed at the host
                    the player logged in through, with only the port taken
                    from the server: the server's one PROXY_IP cannot be both
                    a friend's route to the host and the host's own 127.0.0.1.
"""
import io
import os
import sys


def read(path):
    with io.open(path, 'rb') as f:
        return f.read()


def write(path, data):
    with io.open(path, 'wb') as f:
        f.write(data)


def edit(path, old, new, marker):
    data = read(path)
    name = os.path.basename(path)
    for eol in (b'\r\n', b'\n'):
        if marker.encode('latin-1').replace(b'\n', eol) in data:
            print('  already: %s' % name)
            return
    old_raw = old.encode('latin-1')
    for eol in (b'\r\n', b'\n'):
        old_b = old_raw.replace(b'\n', eol)
        if data.count(old_b) != 1:
            continue
        at = data.find(old_b)
        if b'\n' not in old_raw:
            end = data.find(b'\n', at)
            eol = b'\r\n' if end > 0 and data[end - 1:end] == b'\r' else b'\n'
        new_b = new.encode('latin-1').replace(b'\n', eol)
        write(path, data[:at] + new_b + data[at + len(old_b):])
        print('  edited:  %s' % name)
        return
    raise SystemExit('clientify: anchor not found exactly once in %s:\n%s' % (path, old))


def apply_personality_row(ui):
    header = os.path.join(ui, 'PythonTextTail.h')
    source = os.path.join(ui, 'PythonTextTail.cpp')
    module = os.path.join(ui, 'PythonTextTailModule.cpp')

    edit(header,
         '\t\t\tCGraphicTextInstance*\t\t\tpLevelTextInstance;',
         '\t\t\tCGraphicTextInstance*\t\t\tpLevelTextInstance;\n'
         '\t\t\t// A playerbot\'s personality, a row of its own between the name and\n'
         '\t\t\t// the guild (clientify.py; textTail.AttachPersonality).\n'
         '\t\t\tCGraphicTextInstance*\t\t\tpPersonalityTextInstance;',
         marker='pPersonalityTextInstance;')
    edit(header,
         '\t\tvoid DetachLevel(DWORD dwVID);',
         '\t\tvoid DetachLevel(DWORD dwVID);\n'
         '\n'
         '\t\tvoid AttachPersonality(DWORD dwVID, const char * c_szText, const D3DXCOLOR& c_rColor);\n'
         '\t\tvoid DetachPersonality(DWORD dwVID);',
         marker='void AttachPersonality(DWORD dwVID')

    # Every text tail is born without the row: the character's and the plain one.
    edit(source,
         '\tpTextTail->pLevelTextInstance=NULL;',
         '\tpTextTail->pLevelTextInstance=NULL;\n'
         '\tpTextTail->pPersonalityTextInstance=NULL;',
         marker='pTextTail->pPersonalityTextInstance=NULL;')
    edit(source,
         '\tpTextTail->pLevelTextInstance = NULL;\n\treturn pTextTail;',
         '\tpTextTail->pLevelTextInstance = NULL;\n'
         '\tpTextTail->pPersonalityTextInstance = NULL;\n'
         '\treturn pTextTail;',
         marker='pTextTail->pPersonalityTextInstance = NULL;\n\treturn pTextTail;')
    edit(source,
         '\tm_TextTailPool.Free(pTextTail);',
         '\tif (pTextTail->pPersonalityTextInstance)\n'
         '\t{\n'
         '\t\tCGraphicTextInstance::Delete(pTextTail->pPersonalityTextInstance);\n'
         '\t\tpTextTail->pPersonalityTextInstance = NULL;\n'
         '\t}\n'
         '\n'
         '\tm_TextTailPool.Free(pTextTail);',
         marker='CGraphicTextInstance::Delete(pTextTail->pPersonalityTextInstance);')

    # The row stands where the guild name would, and the guild goes up a row.
    edit(source,
         '\t\tCGraphicTextInstance * pGuildNameInstance = pTextTail->pGuildNameTextInstance;',
         '\t\t// The playerbot personality row (clientify.py) stands where the guild\n'
         '\t\t// name would, and the guild name and its mark go up a row above it.\n'
         '\t\tfloat fyPersonalityShift = 0.0f;\n'
         '\t\tCGraphicTextInstance * pPersonality = pTextTail->pPersonalityTextInstance;\n'
         '\t\tif (pPersonality)\n'
         '\t\t{\n'
         '\t\t\tpPersonality->SetPosition(pTextTail->x, pTextTail->y - c_fyGuildNamePosition, pTextTail->z);\n'
         '\t\t\tpPersonality->Update();\n'
         '\t\t\tfyPersonalityShift = c_fyGuildNamePosition;\n'
         '\t\t}\n'
         '\n'
         '\t\tCGraphicTextInstance * pGuildNameInstance = pTextTail->pGuildNameTextInstance;',
         marker='float fyPersonalityShift = 0.0f;')
    edit(source,
         'pMarkInstance->SetPosition(pTextTail->x - iWidth/2 - iImageHalfSize, pTextTail->y - c_fyMarkPosition);',
         'pMarkInstance->SetPosition(pTextTail->x - iWidth/2 - iImageHalfSize, pTextTail->y - c_fyMarkPosition - fyPersonalityShift);',
         marker='c_fyMarkPosition - fyPersonalityShift);')
    edit(source,
         'pGuildNameInstance->SetPosition(pTextTail->x + iImageHalfSize, pTextTail->y - c_fyGuildNamePosition, pTextTail->z);',
         'pGuildNameInstance->SetPosition(pTextTail->x + iImageHalfSize, pTextTail->y - c_fyGuildNamePosition - fyPersonalityShift, pTextTail->z);',
         marker='c_fyGuildNamePosition - fyPersonalityShift, pTextTail->z);')

    # Drawn after the level, inside the same character loop.
    edit(source,
         '\t\t\tpTextTail->pLevelTextInstance->Render();',
         '\t\t\tpTextTail->pLevelTextInstance->Render();\n'
         '\t\t}\n'
         '\t\tif (pTextTail->pPersonalityTextInstance)\n'
         '\t\t{\n'
         '\t\t\tpTextTail->pPersonalityTextInstance->Render();',
         marker='pTextTail->pPersonalityTextInstance->Render();')

    edit(source,
         'void CPythonTextTail::Initialize()',
         '// A playerbot\'s personality on a row of its own (clientify.py). It is no\n'
         '// PK information, so EnablePKTitle does not hide it: the player\'s switch is\n'
         '// in playerbot_status_tail.py, which calls this every second for the bots it\n'
         '// has heard of - so the instance is made once and only its text and colour\n'
         '// change after that.\n'
         'void CPythonTextTail::AttachPersonality(DWORD dwVID, const char * c_szText, const D3DXCOLOR & c_rColor)\n'
         '{\n'
         '\tTTextTailMap::iterator itor = m_CharacterTextTailMap.find(dwVID);\n'
         '\tif (m_CharacterTextTailMap.end() == itor)\n'
         '\t\treturn;\n'
         '\n'
         '\tTTextTail * pTextTail = itor->second;\n'
         '\n'
         '\tCGraphicTextInstance *& prPersonality = pTextTail->pPersonalityTextInstance;\n'
         '\tif (!prPersonality)\n'
         '\t{\n'
         '\t\tprPersonality = CGraphicTextInstance::New();\n'
         '\t\tprPersonality->SetTextPointer(ms_pFont);\n'
         '\t\tprPersonality->SetOutline(true);\n'
         '\t\tprPersonality->SetHorizonalAlign(CGraphicTextInstance::HORIZONTAL_ALIGN_CENTER);\n'
         '\t\tprPersonality->SetVerticalAlign(CGraphicTextInstance::VERTICAL_ALIGN_BOTTOM);\n'
         '\t}\n'
         '\n'
         '\tprPersonality->SetValue(c_szText);\n'
         '\tprPersonality->SetColor(c_rColor.r, c_rColor.g, c_rColor.b);\n'
         '\tprPersonality->Update();\n'
         '}\n'
         '\n'
         'void CPythonTextTail::DetachPersonality(DWORD dwVID)\n'
         '{\n'
         '\tTTextTailMap::iterator itor = m_CharacterTextTailMap.find(dwVID);\n'
         '\tif (m_CharacterTextTailMap.end() == itor)\n'
         '\t\treturn;\n'
         '\n'
         '\tTTextTail * pTextTail = itor->second;\n'
         '\n'
         '\tif (pTextTail->pPersonalityTextInstance)\n'
         '\t{\n'
         '\t\tCGraphicTextInstance::Delete(pTextTail->pPersonalityTextInstance);\n'
         '\t\tpTextTail->pPersonalityTextInstance = NULL;\n'
         '\t}\n'
         '}\n'
         '\n'
         'void CPythonTextTail::Initialize()',
         marker='void CPythonTextTail::AttachPersonality(')

    edit(module,
         'PyObject * textTailShowCharacterTextTail(PyObject * poSelf, PyObject * poArgs)',
         '// textTail.AttachPersonality(vid, text, r, g, b) and DetachPersonality(vid):\n'
         '// a playerbot\'s personality on its own row (clientify.py).\n'
         'PyObject * textTailAttachPersonality(PyObject * poSelf, PyObject * poArgs)\n'
         '{\n'
         '\tint iVirtualID;\n'
         '\tif (!PyTuple_GetInteger(poArgs, 0, &iVirtualID))\n'
         '\t\treturn Py_BuildException();\n'
         '\tchar * szText;\n'
         '\tif (!PyTuple_GetString(poArgs, 1, &szText))\n'
         '\t\treturn Py_BuildException();\n'
         '\tfloat fr;\n'
         '\tif (!PyTuple_GetFloat(poArgs, 2, &fr))\n'
         '\t\treturn Py_BuildException();\n'
         '\tfloat fg;\n'
         '\tif (!PyTuple_GetFloat(poArgs, 3, &fg))\n'
         '\t\treturn Py_BuildException();\n'
         '\tfloat fb;\n'
         '\tif (!PyTuple_GetFloat(poArgs, 4, &fb))\n'
         '\t\treturn Py_BuildException();\n'
         '\n'
         '\tCPythonTextTail::Instance().AttachPersonality(iVirtualID, szText, D3DXCOLOR(fr, fg, fb, 1.0f));\n'
         '\treturn Py_BuildNone();\n'
         '}\n'
         '\n'
         'PyObject * textTailDetachPersonality(PyObject * poSelf, PyObject * poArgs)\n'
         '{\n'
         '\tint iVirtualID;\n'
         '\tif (!PyTuple_GetInteger(poArgs, 0, &iVirtualID))\n'
         '\t\treturn Py_BuildException();\n'
         '\n'
         '\tCPythonTextTail::Instance().DetachPersonality(iVirtualID);\n'
         '\treturn Py_BuildNone();\n'
         '}\n'
         '\n'
         'PyObject * textTailShowCharacterTextTail(PyObject * poSelf, PyObject * poArgs)',
         marker='PyObject * textTailAttachPersonality(')
    edit(module,
         '\t\t{ "AttachTitle",\t\t\t\ttextTailAttachTitle,\t\t\t\tMETH_VARARGS },',
         '\t\t{ "AttachTitle",\t\t\t\ttextTailAttachTitle,\t\t\t\tMETH_VARARGS },\n'
         '\t\t{ "AttachPersonality",\t\ttextTailAttachPersonality,\t\tMETH_VARARGS },\n'
         '\t\t{ "DetachPersonality",\t\ttextTailDetachPersonality,\t\tMETH_VARARGS },',
         marker='{ "AttachPersonality",')


def apply_discord_presence(ui):
    # The application id decides the name Discord prints over the presence
    # ("Mt2009" for the package's) and which uploaded images race_N and
    # empire_N resolve to; l0st3k's application carries both.
    edit(os.path.join(ui, 'Discord.h'),
         'constexpr auto DiscordClientID = "1180989036949680258";',
         'constexpr auto DiscordClientID = "1548716643541065798";',
         marker='DiscordClientID = "1548716643541065798";')
    edit(os.path.join(ui, 'PythonNetworkStreamPhaseGame.cpp'),
         'discordPresence.buttonURL = "https://mt2009.pl/";',
         'discordPresence.buttonURL = "https://www.youtube.com/@tieru/";',
         marker='discordPresence.buttonURL = "https://www.youtube.com/@tieru/";')


def apply_four_inventory_pages(ui):
    # The belt runs to 302 with four pages, and a quickslot names a belt cell
    # as readily as a bag one: the position is a WORD in TQuickSlot and in
    # every hand it passes through (AddQuickSlot took a signed char).
    edit(os.path.join(ui, 'GameType.h'),
         'typedef struct SQuickSlot\n{\n\tBYTE Type;\n\tBYTE Position;\n} TQuickSlot;',
         'typedef struct SQuickSlot\n{\n\tBYTE Type;\n'
         '\t// A WORD since the four inventory pages (clientify.py).\n'
         '\tWORD Position;\n} TQuickSlot;',
         marker='\tWORD Position;\n} TQuickSlot;')
    # The network stream calls it through IAbstractPlayer, which declares it.
    edit(os.path.join(ui, 'AbstractPlayer.h'),
         'virtual void\tAddQuickSlot(int QuickslotIndex, char IconType, char IconPosition) = 0;',
         'virtual void\tAddQuickSlot(int QuickslotIndex, char IconType, WORD IconPosition) = 0;',
         marker='virtual void\tAddQuickSlot(int QuickslotIndex, char IconType, WORD IconPosition) = 0;')
    edit(os.path.join(ui, 'PythonPlayer.h'),
         'void\tAddQuickSlot(int QuickslotIndex, char IconType, char IconPosition);',
         'void\tAddQuickSlot(int QuickslotIndex, char IconType, WORD IconPosition);',
         marker='void\tAddQuickSlot(int QuickslotIndex, char IconType, WORD IconPosition);')
    player = os.path.join(ui, 'PythonPlayer.cpp')
    edit(player,
         'void CPythonPlayer::AddQuickSlot(int QuickSlotIndex, char IconType, char IconPosition)',
         'void CPythonPlayer::AddQuickSlot(int QuickSlotIndex, char IconType, WORD IconPosition)',
         marker='void CPythonPlayer::AddQuickSlot(int QuickSlotIndex, char IconType, WORD IconPosition)')
    edit(player,
         '(BYTE)dwGlobalSlotIndex, (BYTE)dwWndType, (BYTE)dwWndItemPos);',
         '(BYTE)dwGlobalSlotIndex, (BYTE)dwWndType, (WORD)dwWndItemPos);',
         marker='(BYTE)dwGlobalSlotIndex, (BYTE)dwWndType, (WORD)dwWndItemPos);')
    edit(player,
         '(BYTE)dwGlobalQuickSlotIndex, (BYTE)dwWndType, (BYTE)dwWndItemPos);',
         '(BYTE)dwGlobalQuickSlotIndex, (BYTE)dwWndType, (WORD)dwWndItemPos);',
         marker='(BYTE)dwGlobalQuickSlotIndex, (BYTE)dwWndType, (WORD)dwWndItemPos);')
    stream_h = os.path.join(ui, 'PythonNetworkStream.h')
    item_cpp = os.path.join(ui, 'PythonNetworkStreamPhaseGameItem.cpp')
    edit(stream_h,
         'bool SendQuickSlotAddPacket(BYTE wpos, BYTE type, BYTE pos);',
         'bool SendQuickSlotAddPacket(BYTE wpos, BYTE type, WORD pos);',
         marker='bool SendQuickSlotAddPacket(BYTE wpos, BYTE type, WORD pos);')
    edit(item_cpp,
         'bool CPythonNetworkStream::SendQuickSlotAddPacket(BYTE wpos, BYTE type, BYTE pos)',
         'bool CPythonNetworkStream::SendQuickSlotAddPacket(BYTE wpos, BYTE type, WORD pos)',
         marker='bool CPythonNetworkStream::SendQuickSlotAddPacket(BYTE wpos, BYTE type, WORD pos)')

    # A shop sale's cell: in a byte, a belt potion sold whatever lay on the
    # bag cell 256 below it. Send() writes the parameter's own size, so the
    # wire is two bytes now, which the server reads (input_main.cpp, SELL2).
    edit(stream_h,
         'bool SendShopSellPacketNew(BYTE bySlot, ITEM_COUNT byCount);',
         'bool SendShopSellPacketNew(WORD bySlot, ITEM_COUNT byCount);',
         marker='bool SendShopSellPacketNew(WORD bySlot, ITEM_COUNT byCount);')
    edit(item_cpp,
         'bool CPythonNetworkStream::SendShopSellPacketNew(BYTE bySlot, ITEM_COUNT byCount)',
         'bool CPythonNetworkStream::SendShopSellPacketNew(WORD bySlot, ITEM_COUNT byCount)',
         marker='bool CPythonNetworkStream::SendShopSellPacketNew(WORD bySlot, ITEM_COUNT byCount)')


def apply_coop_game_host(ui):
    # The server names one address for every client: each core's PROXY_IP in
    # the character list (LOGIN_SUCCESS) and in every warp, 127.0.0.1 on a
    # single-player install. A friend who logged in through the host's public
    # address would be sent to his own 127.0.0.1 on entering the world. Every
    # core of one world stands behind the address the player logged in
    # through, so the client keeps that address (the chosen server's host in
    # serverinfo.py) and takes only the port from the server. On the host's
    # own machine that address is 127.0.0.1, which is also what makes a
    # router without NAT loopback irrelevant.
    stream_h = os.path.join(ui, 'PythonNetworkStream.h')
    edit(stream_h,
         '\t\tvoid ConnectGameServer(UINT iChrSlot);\n',
         '\t\tvoid ConnectGameServer(UINT iChrSlot);\n'
         '\t\t// The host the player logged in through; the world is entered and\n'
         '\t\t// every warp followed there, the port alone being the server\'s\n'
         '\t\t// (clientify.py, co-op).\n'
         '\t\tvoid SetGameHost(const char* c_szHost);\n',
         marker='void SetGameHost(const char* c_szHost);')
    edit(stream_h,
         '\t\tstd::string\tm_stPassword;\n',
         '\t\tstd::string\tm_stPassword;\n'
         '\t\tstd::string\tm_stGameHost;\n',
         marker='\t\tstd::string\tm_stGameHost;')
    stream_cpp = os.path.join(ui, 'PythonNetworkStream.cpp')
    edit(stream_cpp,
         '\tTSimplePlayerInformation&\trkSimplePlayerInfo=m_akSimplePlayerInfo[iChrSlot];\n'
         '\tCNetworkStream::Connect((DWORD)rkSimplePlayerInfo.lAddr, rkSimplePlayerInfo.wPort);\n'
         '}\n',
         '\tTSimplePlayerInformation&\trkSimplePlayerInfo=m_akSimplePlayerInfo[iChrSlot];\n'
         '\tif (!m_stGameHost.empty())\n'
         '\t\tCNetworkStream::Connect(m_stGameHost.c_str(), rkSimplePlayerInfo.wPort);\n'
         '\telse\n'
         '\t\tCNetworkStream::Connect((DWORD)rkSimplePlayerInfo.lAddr, rkSimplePlayerInfo.wPort);\n'
         '}\n'
         '\n'
         'void CPythonNetworkStream::SetGameHost(const char* c_szHost)\n'
         '{\n'
         '\tm_stGameHost = c_szHost ? c_szHost : "";\n'
         '}\n',
         marker='void CPythonNetworkStream::SetGameHost(const char* c_szHost)')
    edit(os.path.join(ui, 'PythonNetworkStreamPhaseGame.cpp'),
         '\tCNetworkStream::PingPort(kWarpPacket.lAddr, kWarpPacket.wPort);\n'
         '\tSleep(2000);\n'
         '\tCNetworkStream::Connect((DWORD)kWarpPacket.lAddr, kWarpPacket.wPort);\n',
         '\t// The core\'s port from the server, the host the player logged in\n'
         '\t// through (SetGameHost, clientify.py).\n'
         '\tif (!m_stGameHost.empty())\n'
         '\t{\n'
         '\t\tCNetworkStream::PingPort(m_stGameHost, kWarpPacket.wPort);\n'
         '\t\tSleep(2000);\n'
         '\t\tCNetworkStream::Connect(m_stGameHost.c_str(), kWarpPacket.wPort);\n'
         '\t}\n'
         '\telse\n'
         '\t{\n'
         '\t\tCNetworkStream::PingPort(kWarpPacket.lAddr, kWarpPacket.wPort);\n'
         '\t\tSleep(2000);\n'
         '\t\tCNetworkStream::Connect((DWORD)kWarpPacket.lAddr, kWarpPacket.wPort);\n'
         '\t}\n',
         marker='CNetworkStream::PingPort(m_stGameHost, kWarpPacket.wPort);')
    edit(os.path.join(ui, 'AccountConnector.cpp'),
         '\t\trkNet.Connect(m_strAddr.c_str(), m_iPort);\n',
         '\t\trkNet.SetGameHost(m_strAddr.c_str());\n'
         '\t\trkNet.Connect(m_strAddr.c_str(), m_iPort);\n',
         marker='rkNet.SetGameHost(m_strAddr.c_str());')


def main(root):
    ui = os.path.join(root, 'UserInterface')
    if not os.path.isfile(os.path.join(ui, 'PythonTextTail.cpp')):
        raise SystemExit('clientify: no UserInterface/PythonTextTail.cpp under %s' % root)
    print('clientify: %s' % root)
    apply_personality_row(ui)
    apply_discord_presence(ui)
    apply_four_inventory_pages(ui)
    apply_coop_game_host(ui)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
