import json
import os
import hmac
import socket
import time
import re
import uuid
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta
from functools import wraps

import pymysql
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SEBAN_SESSION_SECRET", "change-this-before-public-use")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
    # Cookies are scoped to the host, not the port. A dedicated name prevents
    # the classic Tieru panel on :7788 from overwriting this panel on :7789.
    SESSION_COOKIE_NAME=os.environ.get("SEBAN_SESSION_COOKIE_NAME", "seban_panel_session"),
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)

# The village names come from the engine's own quests: new_quest_lv52 reads
# the first villages as { "Yongan", "Joan", "Pyongmoo" } by kingdom, and
# new_quest_lv7 names the second ones Jayang, Bokjung and Bakra.
MAP_NAMES = {
    1: "Shinsoo M1 — Yongan", 3: "Shinsoo M2 — Jayang", 4: "Shinsoo Klan Toprakları",
    5: "Shinsoo Maymun Zindanı", 44: "Jinno Klan Toprakları", 45: "Jinno Maymun Zindanı",
    21: "Chunjo M1 — Joan", 23: "Chunjo M2 — Bokjung",
    24: "Chunjo Klan Toprakları", 25: "Kolay Maymun Zindanı",
    41: "Jinno M1 — Pyongmoo", 43: "Jinno M2 — Bakra",
    61: "Sohan Dağı", 63: "Yongbi Çölü", 64: "Ork Vadisi", 104: "Örümcek Zindanı V1",
    65: "Hwang Tapınağı", 71: "Örümcek Zindanı V2",
    108: "Orta Maymun Zindanı", 109: "Zor Maymun Zindanı",
}
MAP_BOUNDS = {
    1: (409600, 896000, 102400, 128000), 3: (307200, 819200, 102400, 102400),
    4: (128000, 0, 51200, 51200), 5: (768000, 435200, 76800, 76800),
    41: (921600, 204800, 102400, 128000), 43: (819200, 204800, 102400, 102400),
    44: (230400, 0, 51200, 51200), 45: (921600, 435200, 76800, 76800),
    21: (0, 102400, 102400, 128000), 23: (102400, 204800, 102400, 102400),
    24: (179200, 0, 51200, 51200), 25: (844800, 435200, 76800, 76800),
    61: (358400, 153600, 153600, 153600), 63: (204800, 486400, 153600, 153600),
    64: (256000, 665600, 153600, 153600), 104: (51200, 486400, 76800, 76800),
    65: (537600, 51200, 102400, 102400), 71: (665600, 435200, 102400, 102400),
    108: (128000, 640000, 76800, 76800), 109: (128000, 716800, 76800, 76800),
}
TRACKED_MAP_OPTIONS = tuple((index, MAP_NAMES[index]) for index in MAP_BOUNDS)
MAP_RESPAWN_OPTIONS = (
    (1, "Shinsoo M1 — Yongan"), (3, "Shinsoo M2 — Jayang"), (21, "Chunjo M1 — Joan"),
    (23, "Chunjo M2 — Bokjung"), (41, "Jinno M1 — Pyongmoo"), (43, "Jinno M2 — Bakra"),
    (4, "Shinsoo Klan Toprakları"), (24, "Chunjo Klan Toprakları"), (44, "Jinno Klan Toprakları"),
    (5, "Shinsoo Maymun Zindanı"), (45, "Jinno Maymun Zindanı"),
    (25, "Kolay Maymun Zindanı"), (61, "Sohan Dağı"), (63, "Yongbi Çölü"), (64, "Ork Vadisi"),
    (104, "Örümcek Zindanı V1"), (71, "Örümcek Zindanı V2"), (108, "Orta Maymun Zindanı"), (109, "Zor Maymun Zindanı"),
)
# Monkey Dungeons and Spider Dungeon V1 ship no stone.txt, so only their mob
# respawns can be configured. The explicit allowlist also protects the helper.
MAP_STONE_RESPAWN_IDS = frozenset(index for index, _name in MAP_RESPAWN_OPTIONS if index not in {5, 25, 45, 104, 71, 108, 109})
STATUS_GLOBS = (os.environ.get("PLAYERBOTS_STATUS_GLOB", "/opt/metin2/var/channel1/*/playerbot_status.tsv"),)
RATES_SPOOL = Path("/opt/m2spool")
UPDATE_SPOOL = Path("/opt/m2update")
UPDATE_WATCHER_MAX_AGE_SECONDS = 90
PLAYERBOTS_RELEASE_URL = "https://api.github.com/repos/debaba13/metin2-playerbots/releases/latest"
PLAYERBOTS_RELEASE_CACHE_SECONDS = 900
_playerbots_release_cache = {"checked_at": 0.0, "latest": None, "error": None}
SERVER_SETTINGS_READY_MAX_AGE_SECONDS = 20
SERVER_SETTINGS_STALE_SECONDS = 600
GAME_HOST = os.environ.get("PLAYERBOTS_GAME_HOST", "metin2-game")
GAME_LOGIN_PORT = int(os.environ.get("PLAYERBOTS_LOGIN_PORT", "11000"))
GAME_WORLD_PORT = int(os.environ.get("PLAYERBOTS_WORLD_PORT", "13000"))
RATE_NAMES = ("exp", "drop", "yang")
AI_WEIGHTS_FILE = RATES_SPOOL / "playerbot_weights.tsv"
AI_WEIGHT_KEYS = (
    ("RESTOCK", "İksirler", "🧪"), ("REFINE", "Demirci", "🔨"),
    ("SKILL", "Yetenek Kitapları", "📖"), ("HORSE", "At", "🐎"),
    ("BIOLOG", "Biyolog", "🧬"), ("METIN", "Metinler", "🗿"),
    ("PARTY", "Gruplar", "👥"), ("HUNTING", "Avlanma Görevleri", "🏹"),
    ("LEVEL", "Canavar Avlama", "⚔️"), ("FISHING", "Balık Tutma", "🎣"),
    ("TRADE", "Tezgahlar", "🏪"),
)
AI_WEIGHT_MIN, AI_WEIGHT_MAX, AI_WEIGHT_NEUTRAL = 25, 250, 100
# These values share the live weight file with goal weights, but the core treats
# them as switches or direct settings rather than 25–250% goal weights.
AI_LIVE_DEFAULTS = {"CHAT": 1, "BOOKS": 1, "NIGHT": 1, "SCRAP": 0, "REST": 100, "CHEST": None, "CHEST_STONE": None}
AI_SPECIAL_WEIGHT_KEYS = frozenset(AI_LIVE_DEFAULTS)
BIOLOGIST_COMPLETE_STATE = 557528158
# Tieru 1.29.10 adds the Orc Tooth task after the six classic Biologist
# missions. The database lookup below also discovers future missions as soon
# as the game has created their quest rows, while this list keeps the complete
# progress scale correct before anyone has started a new task.
BIOLOGIST_FALLBACK_MISSIONS = (
    "make_herb_lv4", "make_herb_lv7", "make_herb_lv10", "make_herb_lv15",
    "make_herb_lv20", "make_herb_lv25", "collect_quest_lv30",
)
PANEL_VERSION_FILE = Path(__file__).parent / "VERSION"
GM_JOB_OPTIONS = ((0, "Savaşçı"), (1, "Ninja"), (2, "Sura"), (3, "Şaman"))
# Race IDs are stored in player.job.  0–3 retain the classic class/gender
# pair; IDs 4–7 are the alternate client portraits and character models.
GM_GENDER_OPTIONS = (("classic", "Sınıf İçin Klasik"), ("male", "Erkek"), ("female", "Kadın"))
GM_RACE_BY_CLASS_GENDER = {
    (0, "classic"): 0, (1, "classic"): 1, (2, "classic"): 2, (3, "classic"): 3,
    (0, "male"): 0, (0, "female"): 4,
    (1, "male"): 5, (1, "female"): 1,
    (2, "male"): 2, (2, "female"): 6,
    (3, "male"): 7, (3, "female"): 3,
}
CLASS_PROFILES = {
    0: {"name": "Savaşçı", "gender": "Erkek", "portrait": "warrior_m.bmp"},
    4: {"name": "Savaşçı", "gender": "Kadın", "portrait": "warrior_w.bmp"},
    1: {"name": "Ninja", "gender": "Kadın", "portrait": "assassin_w.bmp"},
    5: {"name": "Ninja", "gender": "Erkek", "portrait": "assassin_m.bmp"},
    2: {"name": "Sura", "gender": "Erkek", "portrait": "sura_m.bmp"},
    6: {"name": "Sura", "gender": "Kadın", "portrait": "sura_w.bmp"},
    3: {"name": "Şaman", "gender": "Kadın", "portrait": "shaman_w.bmp"},
    7: {"name": "Şaman", "gender": "Erkek", "portrait": "shaman_m.bmp"},
}
GM_JOB_STARTS = {0: (6, 4, 3, 3, 600, 200), 1: (4, 3, 6, 3, 650, 200), 2: (5, 3, 3, 6, 650, 200), 3: (3, 5, 3, 5, 700, 200)}
GM_EMPIRE_STARTS = {1: (469300, 964200, 1), 2: (55700, 157900, 21), 3: (969600, 278400, 41)}
GM_NAME_PATTERN = r"(?:[A-Za-z0-9_]{2,24}|\[[A-Za-z0-9_]{1,6}\][A-Za-z0-9_]{2,16})"
EMPIRES = {1: {"name": "Shinsoo", "flag": "shinsoo.png"}, 2: {"name": "Chunjo", "flag": "chunjo.png"}, 3: {"name": "Jinno", "flag": "jinno.png"}}
try:
    PANEL_VERSION = os.environ.get("SEBAN_PANEL_VERSION") or PANEL_VERSION_FILE.read_text(encoding="utf-8").strip()
except OSError:
    PANEL_VERSION = os.environ.get("SEBAN_PANEL_VERSION", "dev")
DEFAULT_SETTINGS = {
    "panel_name": "Metin2 Singleplayer", "stuck_minutes": "5", "theme": "ocean", "monitor_mode": "vps",
    # Existing installations without this key stay usable. Fresh installations
    # receive setup_complete=0 from the collector and enter the setup wizard.
    "setup_complete": "1", "auth_enabled": "0", "auth_password_hash": "",
}
try:
    ITEM_DEFS = json.loads((Path(__file__).parent / "static" / "item_defs.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    ITEM_DEFS = {}
# EPlayerBotPersonality (playerbot_types.h): MERCHANT to 5, WANDERER 6.
# This table used to have 5 as the wanderer and end there, so a keeper read
# as a wanderer, and the five personalities appended since then read as
# nothing at all.
BOT_PERSONALITIES = {0: "Kararlı Maceracı", 1: "Metin Kırıcı", 2: "Takım Arkadaşı", 3: "Ekipman Ustası", 4: "Dikkatli Toplayıcı", 5: "Tüccar", 6: "Gezgin", 7: "Metin Dropper'ı", 8: "M3 Dropper'ı", 9: "M2 Dropper'ı", 10: "Madalya Dropper'ı"}
BOT_AMBITIONS = {0: "Seviye", 1: "Ekipman", 2: "Metinler", 3: "At", 4: "Biyolog", 5: "Yetenekler"}
BOT_GOALS = {0: "Seviye Kazanma", 1: "Hayatta Kalma", 2: "Meslek Seçme", 3: "Ekipman Edinme", 4: "Stok Tamamlama", 5: "Ekipman Geliştirme", 6: "Yetenek Geliştirme", 7: "Metin Avlama", 8: "Grup Hedefleri", 9: "Biyolog Görevi", 10: "Avlanma Görevi", 11: "At Geliştirme"}
BOT_ACTIONS = {0: "Sonraki Hamleyi Planlıyor", 1: "Yolculukta", 2: "Savaşıyor", 3: "Ganimet Topluyor", 4: "İyileşiyor", 5: "Meslek Seçiyor", 6: "Ticaret Yapıyor", 7: "Ekipman Geliştiriyor", 8: "Yetenek Kitabı Okuyor", 9: "Ruh Taşı Takıyor", 10: "Grup Topluyor", 11: "Biyolog Görevi Yapıyor", 12: "Seyis'i Ziyaret Ediyor", 13: "Tezgah İşletiyor", 14: "Balık Tutuyor", 15: "Tezgahlara Bakıyor", 16: "Canavar Çekiyor", 17: "Şehirde Dinleniyor", 18: "Maden Kazıyor"}
# Actions where a bot stands still on purpose: stall, rod, browsing stalls,
# an NPC counter, blacksmith, trainer, resting, mining. Without this every
# keeper read as "Possibly stuck" - and the status-text flag only caught anglers.
STATIONARY_ACTIONS = {5, 6, 7, 13, 14, 15, 17, 18}
ITEM_TYPE_NAMES = (
    "ITEM_NONE", "ITEM_WEAPON", "ITEM_ARMOR", "ITEM_USE", "ITEM_AUTOUSE", "ITEM_MATERIAL", "ITEM_SPECIAL", "ITEM_TOOL", "ITEM_LOTTERY", "ITEM_ELK",
    "ITEM_METIN", "ITEM_CONTAINER", "ITEM_FISH", "ITEM_ROD", "ITEM_RESOURCE", "ITEM_CAMPFIRE", "ITEM_UNIQUE", "ITEM_SKILLBOOK", "ITEM_QUEST", "ITEM_POLYMORPH",
    "ITEM_TREASURE_BOX", "ITEM_TREASURE_KEY", "ITEM_SKILLFORGET", "ITEM_GIFTBOX", "ITEM_PICK", "ITEM_HAIR", "ITEM_TOTEM", "ITEM_BLEND", "ITEM_COSTUME", "ITEM_DS",
    "ITEM_SPECIAL_DS", "ITEM_EXTRACT", "ITEM_SECONDARY_COIN", "ITEM_RING", "ITEM_BELT", "ITEM_PET", "ITEM_MEDIUM", "ITEM_GACHA", "ITEM_SOUL", "ITEM_PASSIVE",
)
APPLY_LABELS = {
    1: ("Maks. Can", ""), 2: ("Maks. Mana", ""), 3: ("Dayanıklılık", ""), 4: ("Zeka", ""), 5: ("Güç", ""), 6: ("Çeviklik", ""), 7: ("Saldırı Hızı", "%"), 8: ("Hareket Hızı", "%"), 9: ("Büyü Hızı", "%"), 10: ("Can Yenilenmesi", "%"), 11: ("Mana Yenilenmesi", "%"), 12: ("Zehire Karşı Direnç", "%"), 13: ("Bayıltma Şansı", "%"), 14: ("Yavaşlatma Şansı", "%"), 15: ("Kritik Vuruş Şansı", "%"), 16: ("Delici Vuruş Şansı", "%"), 17: ("Saldırı Değeri", ""), 18: ("İnsanlara Karşı Güçlü", "%"), 19: ("Hayvanlara Karşı Güçlü", "%"), 20: ("Orklara Karşı Güçlü", "%"), 21: ("Mistiklere Karşı Güçlü", "%"), 22: ("Yarı Ölülere Karşı Güçlü", "%"), 23: ("Şeytanlara Karşı Güçlü", "%"), 24: ("Can Çalma Şansı", "%"), 25: ("Mana Çalma Şansı", "%"), 26: ("Mana Yakma Şansı", "%"), 27: ("Vurulunca Mana Kazanma Şansı", "%"), 28: ("Blok Şansı", "%"), 29: ("Ok Kaçırma Şansı", "%"), 30: ("Kılıca Karşı Direnç", "%"), 31: ("İki Elli Silaha Karşı Direnç", "%"), 32: ("Hançere Karşı Direnç", "%"), 33: ("Çana Karşı Direnç", "%"), 34: ("Yelpazeye Karşı Direnç", "%"), 35: ("Oka Karşı Direnç", "%"), 36: ("Ateşe Karşı Direnç", "%"), 37: ("Yıldırıma Karşı Direnç", "%"), 38: ("Büyüye Karşı Direnç", "%"), 39: ("Rüzgara Karşı Direnç", "%"), 40: ("Fiziksel Hasar Yansıtma Şansı", "%"), 41: ("Lanet Yansıtma Şansı", "%"), 42: ("Zehirlenme Süresini Kısaltma", "%"), 43: ("Öldürünce Mana Kazanma Şansı", "%"), 44: ("Tecrübe Bonusu", "%"), 45: ("Yang Bonusu", "%"), 46: ("Eşya Düşme Bonusu", "%"), 47: ("İksir Bonusu", "%"), 48: ("Öldürünce Can Kazanma Şansı", "%"), 49: ("Bayılmaya Karşı Direnç", ""), 50: ("Yavaşlamaya Karşı Direnç", ""), 51: ("Devrilmeye Karşı Direnç", ""), 52: ("Yetenek Bonusu", "%"), 53: ("Yay Menzili", "%"), 54: ("Saldırı Değeri", ""), 55: ("Savunma Değeri", ""), 56: ("Büyü Saldırı Değeri", ""), 57: ("Büyü Savunma Değeri", ""), 58: ("Lanet Şansı", "%"), 59: ("Maks. Dayanıklılık", ""), 60: ("Savaşçılara Karşı Güçlü", "%"), 61: ("Ninjalara Karşı Güçlü", "%"), 62: ("Sura'ya Karşı Güçlü", "%"), 63: ("Şamanlara Karşı Güçlü", "%"), 64: ("Canavarlara Karşı Güçlü", "%"), 70: ("Maks. Can", "%"), 71: ("Yetenek Hasarı", "%"), 72: ("Ortalama Hasar", "%"), 73: ("Yetenek Hasarına Karşı Direnç", "%"), 74: ("Ortalama Hasara Karşı Direnç", "%"), 75: ("Tecrübe Bonusu", "%"), 76: ("Düşme Bonusu", "%"), 77: ("Can Çalma Şansı", "%"), 78: ("Savaşçı Saldırılarına Karşı Direnç", "%"), 79: ("Ninja Saldırılarına Karşı Direnç", "%"), 80: ("Sura Saldırılarına Karşı Direnç", "%"), 81: ("Şaman Saldırılarına Karşı Direnç", "%"), 82: ("Enerji", "%"), 83: ("Savunma Değeri", ""), 84: ("Kostüm Bonusu", "%"), 85: ("Büyü Saldırısı", "%"), 86: ("Fiziksel ve Büyü Saldırısı", "%"), 87: ("Buza Karşı Direnç", "%"), 88: ("Toprağa Karşı Direnç", "%"), 89: ("Karanlığa Karşı Direnç", "%"), 90: ("Kritik Vuruşa Karşı Direnç", "%"), 91: ("Delici Vuruşa Karşı Direnç", "%"), 1138: ("Terör", "%"), 1139: ("Dayanıklılık Yenilenmesi", "%"), 1140: ("Canavarlara Karşı Hançer Saldırısı", ""), 1141: ("Canavarlara Karşı Saldırı Değeri", ""), 1142: ("Canavarlara Karşı Direnç", "‰"), 1143: ("Hasar Emilimi", "%"), 1144: ("Canavarlardan Hasar Emilimi", "%"), 1145: ("Sersemletme Bağışıklığını Kırma", ""), 1146: ("Tapınak Lanetini Kırma", ""), 1147: ("Yetenek Süresi", "%"), 1148: ("Ork Vadisi Canavarlarına Karşı Güçlü", "%"), 1149: ("Metin Taşlarına Karşı Güçlü", "%"), 1150: ("Boss'lara Karşı Güçlü", "%"), 1151: ("Canavarlara Karşı Büyü Saldırısı", "%"), 1152: ("Kılıç Direncini Kırma", "%"), 1153: ("İki Elli Silah Direncini Kırma", "%"), 1154: ("Hançer Direncini Kırma", "%"), 1155: ("Çan Direncini Kırma", "%"), 1156: ("Yelpaze Direncini Kırma", "%"), 1157: ("Yay Direncini Kırma", "%"), 1158: ("Toplama Şansı", "%"), 1159: ("Öğrenme Şansı", "%"), 1160: ("İnsanlara Karşı Direnç", "%"), 1161: ("Büyü Saldırısı", ""), 1162: ("Yakma Şansı", "%"), 1163: ("Hasarın Manaya Dönüşümü", "%"), 1164: ("Nadir Düşme Şansı", "%"), 1165: ("Canavarlara Karşı Büyü Saldırı Değeri", ""), 1166: ("Sabitleme Şansı", "%"), 1167: ("Özel Saldırı", ""), 1168: ("Ölüm Cezası", "%")}
# 71 and 72 are in the table above, in the right order: common/length.h
# carries the numbers in its own comments - APPLY_SKILL_DAMAGE_BONUS is 71,
# APPLY_NORMAL_HIT_DAMAGE_BONUS is 72. A "fix" used to stand here that
# overwrote the table and explained it as "the fields are swapped in this
# build" - nothing swaps them. The justification was untrue, and the
# overwrite only reached item descriptions, so the ranking - which reads
# from a separate query - kept showing them swapped long after.
# Which engine the panel looks at (PLAYERBOTS_ENGINE). mt2009 keeps an
# item's bonus lines as POINT_* numbers: the two damage lines are 121 and
# 122 there, every attrtype goes through POINT_TO_APPLY before APPLY_LABELS,
# account.account has no empire column and player.player no bank_value.
PANEL_ENGINE = os.environ.get("PLAYERBOTS_ENGINE", "r40250").strip().lower()
ENGINE_MT2009 = PANEL_ENGINE == "mt2009"
ATTR_SKILL_DAMAGE = 121 if ENGINE_MT2009 else 71
ATTR_AVG_DAMAGE = 122 if ENGINE_MT2009 else 72
POINT_TO_APPLY = {6: 1, 8: 2, 13: 3, 15: 4, 12: 5, 14: 6, 17: 7, 19: 8, 21: 9, 32: 10, 33: 11,
 37: 12, 38: 13, 39: 14, 40: 15, 41: 16, 43: 17, 44: 18, 45: 19, 46: 20, 47: 21,
 48: 22, 63: 23, 64: 24, 65: 25, 66: 26, 67: 27, 68: 28, 69: 29, 70: 30, 71: 31,
 72: 32, 73: 33, 74: 34, 75: 35, 76: 36, 77: 37, 78: 38, 79: 39, 81: 41, 82: 42,
 83: 43, 84: 44, 85: 45, 86: 46, 87: 47, 88: 48, 89: 49, 90: 50, 28: 51, 34: 52,
 95: 53, 96: 54, 22: 55, 23: 56, 42: 57, 10: 58, 54: 59, 55: 60, 56: 61, 57: 62,
 53: 63, 114: 64, 115: 65, 116: 66, 117: 67, 118: 68, 119: 69, 120: 70, 121: 71,
 122: 72, 123: 73, 124: 74, 125: 75, 126: 76, 59: 78, 60: 79, 61: 80, 62: 81,
 128: 82, 16: 83, 130: 84, 131: 85, 132: 86, 133: 87, 134: 88, 135: 89, 136: 90,
 137: 91,
 # mt2009 points with no APPLY id at all (length.h 138..168 - the engine
 # applies them straight from the item). A pseudo key of 1000 + point, so
 # the label tables can name them; without it the panel wrote "Bonus #139".
 138: 1138, 139: 1139, 140: 1140, 141: 1141, 142: 1142, 143: 1143, 144: 1144, 145: 1145, 146: 1146, 147: 1147, 148: 1148, 149: 1149, 150: 1150, 151: 1151, 152: 1152, 153: 1153, 154: 1154, 155: 1155, 156: 1156, 157: 1157, 158: 1158, 159: 1159, 160: 1160, 161: 1161, 162: 1162, 163: 1163, 164: 1164, 165: 1165, 166: 1166, 167: 1167, 168: 1168}
# The kingdom of a character: the index, then (r40250 only) the account.
EMPIRE_EXPR = "COALESCE(NULLIF(pi.empire,0),0)" if ENGINE_MT2009 else "COALESCE(NULLIF(pi.empire,0),a.empire,0)"

JOB_NAMES = ("Savaşçı", "Ninja", "Sura", "Şaman")
SKILLS = {
    # Exact vnum/name pairs from Tieru's current panel. The old mapping put
    # display names next to the wrong VNUMs, hence correct icons looked wrong.
    (0, 1): ((1, "Üç Yönlü Kesiş"), (2, "Kılıç Dönüşü"), (3, "Berserk"), (4, "Kılıç Aurası"), (5, "Hamle")),
    (0, 2): ((16, "Ruh Darbesi"), (17, "Ezme"), (18, "Kılıç Darbesi"), (19, "Güçlü Beden"), (20, "Vuruş")),
    (1, 1): ((31, "Pusu"), (32, "Hızlı Saldırı"), (33, "Dönen Hançer"), (34, "Gizlenme"), (35, "Zehir Bulutu")),
    (1, 2): ((46, "Tekrarlı Atış"), (47, "Ok Yağmuru"), (48, "Ateş Oku"), (49, "Sessiz Adım"), (50, "Zehirli Ok")),
    (2, 1): ((61, "Parmak Darbesi"), (62, "Ejder Girdabı"), (63, "Büyülü Bıçak"), (64, "Korku"), (65, "Büyülü Zırh"), (66, "Büyü Bozma")),
    (2, 2): ((76, "Karanlık Darbe"), (77, "Alev Darbesi"), (78, "Alev Ruhu"), (79, "Karanlık Koruma"), (80, "Ruh Darbesi"), (81, "Karanlık Küre")),
    (3, 1): ((91, "Uçan Tılsım"), (92, "Ateş Eden Ejder"), (93, "Ejder Kükremesi"), (94, "Kutsama"), (95, "Yansıtma"), (96, "Ejder Yardımı")),
    (3, 2): ((106, "Yıldırım Fırlatma"), (107, "Yıldırım Çağırma"), (108, "Fırtına Pençesi"), (109, "Şifa"), (110, "Çeviklik"), (111, "Saldırı Artışı")),
}
try:
    ITEM_ICONS = json.loads((Path(__file__).parent / "static" / "item_icons.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    ITEM_ICONS = {}
try:
    EXP_LEVELS = json.loads((Path(__file__).parent / "static" / "exp_levels.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    EXP_LEVELS = [0]
try:
    GM_COMMANDS = (Path(__file__).parent / "gm_commands.txt").read_text(encoding="utf-8", errors="replace")
except OSError:
    GM_COMMANDS = "Komut dosyası bulunamadı."


# MyISAM does not survive an unclean stop, and this panel's front page reads
# the busiest table in the whole world - log.log, for the fishing ranking.
# When it is damaged, every query against it throws, Flask shows its own
# "Internal Server Error", and that page's screenshot is what reaches
# Discord - no table name, no cause, nothing to act on (archonek, 10
# September: "I click and an error pops up"; the classic panel worked fine,
# because its front page never touches log.log). An update does not fix
# this: the damage sits in the data on the volume, not in the image.
#
# Error numbers: 1194 "is marked as crashed and should be repaired",
# 1195 and 144 "last repair failed", 145 the same for older servers.
CRASHED_TABLE_ERRNOS = (144, 145, 1194, 1195)


@app.errorhandler(pymysql.err.OperationalError)
def handle_crashed_table(error):
    errno = error.args[0] if error.args else 0
    message = str(error.args[1]) if len(error.args) > 1 else str(error)
    if errno not in CRASHED_TABLE_ERRNOS:
        # Not our concern - let Flask show its own 500 and log the trace.
        raise error
    table = ""
    match = re.search(r"Table '([^']+)'", message)
    if match:
        table = match.group(1).replace("./", "").replace("/", ".")
    named = ("<code>%s</code> Tablosu" % escape(table)) if table else "Veritabanı Tablolarından Biri"
    body = """<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>Bozuk Veritabanı Tablosu</title>
<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:52em;margin:3em auto;padding:0 1.5em;line-height:1.6;color:#222}
h1{font-size:1.5em}code{background:#f2f2f2;padding:.15em .35em;border-radius:3px}
pre{background:#f2f2f2;padding:1em;border-radius:5px;overflow-x:auto}
.note{background:#fff8e1;border-left:4px solid #e0a800;padding:.8em 1em;margin:1.5em 0}</style>
</head><body>
<h1>Bozuk Veritabanı Tablosu</h1>
<p>%s bozuk olarak işaretlenmiş, bu yüzden panel onu okuyamıyor.
Oyun motoru MyISAM tabloları kullanır ve bunlar ani bir durmayı
kaldıramaz - Docker'ın yazma sırasında kapanması ya da elektrik kesintisi yeterlidir.</p>
<div class="note"><strong>Sunucu güncellemesi bunu düzeltmez.</strong>
Bozukluk diskteki verilerdedir, programda değil - yeni sürüm de aynı
dosyaları okur.</div>
<h2>Nasıl Onarılır</h2>
<p>Sunucu klasöründe, <code>linux-port\\docker</code> alt klasöründe
PowerShell açın (launcher'da SUNUCU KLASÖRÜ butonu) ve şunu çalıştırın:</p>
<pre>docker compose exec mariadb mysqlcheck -uroot -p --auto-repair --databases log player account common</pre>
<p>Şifre soracak - bu aynı klasördeki <code>.env</code> dosyasındaki
<code>M2_DB_ROOT_PASSWORD</code>'tur. Büyük log tablosunun onarımı birkaç dakika sürebilir.</p>
<h2>Onarım Başarısız Olursa</h2>
<p><code>log</code> veritabanı sadece geçmiş bilgisidir: kimin ne aldığı,
geliştirdiği ve söylediği. Oyun onu okumaz ve hiçbir karakter, eşya ya da bot
ona bağlı değildir. Eğer <code>mysqlcheck</code> başarısız olduğunu bildirirse,
bu tabloları dünyaya zarar vermeden boşaltabilirsiniz:</p>
<pre>docker compose exec mariadb mariadb -uroot -p -e "TRUNCATE log.log; TRUNCATE log.levellog; TRUNCATE log.shout_log;"</pre>
<div class="note">Bunu <code>player</code>, <code>account</code>
ya da <code>common</code> veritabanları için YAPMAYIN - orada karakterler, hesaplar ve botlar var.</div>
<p style="margin-top:2em;color:#666;font-size:.9em">Veritabanı hatası: %s (%s)</p>
</body></html>""" % (named, errno, escape(message))
    return body, 500



def db():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "mariadb"), port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, autocommit=True,
    )


def rows(sql, params=()):
    with db() as con:
        with con.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def one(sql, params=()):
    result = rows(sql, params)
    return result[0] if result else {}


def game_text(value):
    if isinstance(value, bytes):
        for encoding in ("cp1250", "utf-8", "latin1"):
            try:
                return value.decode(encoding)
            except UnicodeDecodeError:
                pass
        return value.decode("cp1250", "replace")
    return value or ""


def cp1250_hex_text(value):
    """Decode a Polish item name without trusting the log table's charset."""
    try:
        return bytes.fromhex(str(value or "")).decode("cp1250")
    except (TypeError, ValueError, UnicodeDecodeError):
        return ""


def map_name(index):
    """Name only maps which this Playerbots world actually runs."""
    index = int(index or 0)
    return MAP_NAMES.get(index, f"Aktif dünyanın dışında (harita #{index})")


def changelog_entries():
    """Read version notes from the repository file for the public in-panel log."""
    path = Path(__file__).parent / "CHANGELOG.md"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    entries, current = [], None
    for line in lines:
        if line.startswith("## "):
            if current:
                entries.append(current)
            heading = line[3:].strip()
            timestamp, separator, version = heading.partition(" · ")
            current = {"timestamp": timestamp if separator else "Önceki sürüm", "version": version if separator else heading, "changes": []}
        elif current and line.startswith("- "):
            current["changes"].append(line[2:].strip())
    if current:
        entries.append(current)
    return entries


def settings():
    values = dict(DEFAULT_SETTINGS)
    try:
        for row in rows("SELECT name,value FROM player.web_seban_settings"):
            if row["name"] in values:
                values[row["name"]] = str(row["value"])
    except pymysql.MySQLError:
        pass
    return values


def write_settings(values):
    """Persist panel-only configuration without relying on environment secrets."""
    with db() as con:
        with con.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_settings (
              name VARCHAR(64) NOT NULL PRIMARY KEY, value VARCHAR(255) NOT NULL,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB""")
            cur.executemany(
                "INSERT INTO player.web_seban_settings (name,value) VALUES (%s,%s) ON DUPLICATE KEY UPDATE value=VALUES(value)",
                tuple(values.items()),
            )


def validate_display_settings(form):
    name = form.get("panel_name", "").strip()[:48]
    try:
        stuck = max(1, min(120, int(form.get("stuck_minutes", "5"))))
    except (TypeError, ValueError):
        stuck = 5
    theme, monitor_mode = form.get("theme", "ocean"), form.get("monitor_mode", "vps")
    if not name:
        return None, "Panel adı boş olamaz."
    if theme not in ("ocean", "ember", "forest") or monitor_mode not in ("vps", "docker"):
        return None, "Geçersiz görünüm veya izleme ayarları."
    return {"panel_name": name, "stuck_minutes": str(stuck), "theme": theme, "monitor_mode": monitor_mode}, None


def skill_rank(master_type, level):
    master_type, level = int(master_type or 0), int(level or 0)
    if master_type >= 3 or level >= 40:
        return "P"
    if master_type == 2 or level >= 30:
        return f"G{max(1, level - 29)}"
    if master_type == 1 or level >= 20:
        return f"M{max(1, level - 19)}"
    return str(level)


def experience_progress(level, exp):
    level, exp = int(level or 0), max(0, int(exp or 0))
    required = int(EXP_LEVELS[min(max(level, 0), len(EXP_LEVELS) - 1)] or 0)
    return {"current": exp, "required": required, "percent": min(100, round(exp * 100 / required, 1)) if required else 100}


def honor_rank(value):
    """The core stores alignment in tenths; return the in-game value and colour."""
    points = int(float(value or 0) / 10)
    bands = (
        (12000, "Şövalye Ruhlu", "knightly"), (8000, "Asil", "noble"),
        (4000, "İyi", "good"), (1000, "Dostane", "friendly"),
        (0, "Nötr", "neutral"), (-3999, "Saldırgan", "aggressive"),
        (-7999, "Sahtekar", "dishonest"), (-11999, "Kötü Niyetli", "malicious"),
        (-20000, "Acımasız", "cruel"),
    )
    for threshold, title, css in bands:
        if points >= threshold:
            return {"points": points, "title": title, "css": css}
    return {"points": points, "title": "Acımasız", "css": "cruel"}


def live_label(field, value):
    labels = {"personality": BOT_PERSONALITIES, "ambition": BOT_AMBITIONS, "goal": BOT_GOALS, "action": BOT_ACTIONS}.get(field, {})
    value = int(value or 0)
    return labels.get(value, f"#{value}")


def is_stationary_activity(status, action=None):
    try:
        if int(action or 0) in STATIONARY_ACTIONS:
            return True
    except (TypeError, ValueError):
        pass
    text = str(status or "").casefold()
    return any(marker in text for marker in ("balik", "olta", "fishing"))


def apply_text(apply_type, value):
    key = int(apply_type or 0)
    if ENGINE_MT2009:
        key = POINT_TO_APPLY.get(key, key)
    name, suffix = APPLY_LABELS.get(key, (f"Bonus #{apply_type}", ""))
    value = int(value or 0)
    return f"{name} {value:+d}{suffix}"


def item_base_stats(vnum):
    """Client-side item properties displayed by the in-game tooltip."""
    proto = ITEM_DEFS.get(str(int(vnum or 0)), {})
    if not proto:
        return []
    stats, item_type = [], int(proto.get("type") or 0)
    level = int(proto.get("level") or 0)
    if level:
        stats.append(f"Gerekli seviye: {level}")
    value = lambda index: int(proto.get(f"value{index}") or 0)
    if item_type == 1:  # ITEM_WEAPON: magic 1/2, physical 3/4.
        attack_min, attack_max = value(3), value(4)
        magic_min, magic_max = value(1), value(2)
        if attack_min or attack_max:
            stats.append(f"Saldırı değeri: {attack_min}–{attack_max}" if attack_min != attack_max else f"Saldırı değeri: {attack_max}")
        if magic_min or magic_max:
            stats.append(f"Büyü saldırı değeri: {magic_min}–{magic_max}" if magic_min != magic_max else f"Büyü saldırı değeri: {magic_max}")
    elif item_type == 2:  # ITEM_ARMOR, including body armour and shields.
        defense = value(1)
        if defense:
            stats.append(f"Savunma değeri: {defense}")
    return stats


def empire_info(empire):
    try:
        return EMPIRES.get(int(empire), {"name": "—", "flag": ""})
    except (TypeError, ValueError):
        return {"name": "—", "flag": ""}


def empire_flag_path(empire):
    return empire_info(empire)["flag"]

def class_profile(job):
    try:
        return CLASS_PROFILES.get(int(job), CLASS_PROFILES[0])
    except (TypeError, ValueError):
        return CLASS_PROFILES[0]


def parse_skills(raw, job, group):
    if isinstance(raw, memoryview): raw = raw.tobytes()
    if isinstance(raw, str): raw = raw.encode("latin1", "ignore")
    raw = raw or b""
    result = []
    for vnum, name in SKILLS.get((int(job or 0) % 4, int(group or 0)), ()):
        offset = vnum * 6
        master, level = (raw[offset] if offset < len(raw) else 0), (raw[offset + 1] if offset + 1 < len(raw) else 0)
        rank = skill_rank(master, level)
        if level:
            # Tieru's icon pack has the master artwork in *_m.png.  It is used
            # for every mastered stage (M, G and P); there are no *_p.png files.
            result.append({"vnum": vnum, "name": name, "level": level, "master_type": master, "rank": rank, "icon_suffix": "_m" if master >= 1 or level >= 20 else ""})
    return result


SKILL_NAMES = {vnum: name for skill_set in SKILLS.values() for vnum, name in skill_set}
_season_cache = {"at": 0.0, "weekly": [], "records": {}}


def news_feed_events():
    """Curate rare achievements from the native game log with stable IDs."""
    # Filter in SQL before the limit.  A busy server produces thousands of
    # ordinary +0–+3 refines per minute; taking its newest 900 rows first made
    # rare achievements disappear from the feed altogether.
    raw = rows("""SELECT l.time,l.how,l.hint,HEX(l.hint) AS hint_hex,l.what,l.who,p.name,
        HEX(proto.locale_name) AS item_name_hex
      FROM log.log l JOIN player.player p ON p.id=l.who
      LEFT JOIN player.item i ON i.id=l.what
      LEFT JOIN player.item_proto proto ON proto.vnum=i.vnum
      WHERE l.time >= NOW() - INTERVAL 12 HOUR
        AND (
          (l.how='REFINE SUCCESS' AND (l.hint LIKE '%%+7%%' OR l.hint LIKE '%%+8%%' OR l.hint LIKE '%%+9%%'))
          OR l.how='SKILLUP'
          OR (l.how='GET' AND LOWER(CONVERT(l.hint USING utf8mb4)) COLLATE utf8mb4_general_ci LIKE '%%małż%%')
        )
      ORDER BY l.time DESC LIMIT 900""")
    events, seen = [], set()
    for row in raw:
        # `how` is VARBINARY on mt2009 and arrives as bytes; str() of that is
        # "b'GET'" and matches nothing below.
        how, name = game_text(row.get("how")), game_text(row.get("name"))
        # log.log's hint column is declared big5 while the engine writes CP1250
        # into it (see CLAUDE.md), so letting the driver decode the column gives
        # mojibake for anything past ASCII - "Skorzane" came back as
        # "SkAtrzane". HEX(l.hint) sidesteps whatever charset MySQL believes the
        # column has and returns the untouched bytes, which really are CP1250 -
        # the same trick this function already uses for item_proto.locale_name
        # below. Falls back to the driver's own decode if the hex round trip
        # fails. Patch by seban latino, 13 September.
        hint = cp1250_hex_text(row.get("hint_hex")) or game_text(row.get("hint"))
        key = f"{how}:{row.get('who')}:{row.get('what')}:{row.get('time')}"
        if key in seen or not name:
            continue
        message = None
        if how == "REFINE SUCCESS":
            match = re.search(r"\+([789])(?:\s|$)", hint)
            if match:
                item_name = cp1250_hex_text(row.get("item_name_hex")) or hint.strip()
                message = f"{name}, {item_name} eşyasını geliştirdi"
        elif how == "SKILLUP":
            match = re.search(r"SkillUp:\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)", hint)
            if match:
                vnum, master, level = map(int, match.groups())
                rank = skill_rank(master, level)
                if (rank.startswith("M") and rank != "M1") or rank.startswith("G") or rank == "P":
                    message = f"{name}, {SKILL_NAMES.get(vnum, f'#{vnum} yeteneğini')} {rank} seviyesine geliştirdi"
        elif how == "GET" and "małż" in hint.casefold():
            message = f"{name} balık tutarken Midye buldu"
        if message:
            seen.add(key)
            events.append({"key": key, "time": row["time"].strftime("%H:%M") if hasattr(row.get("time"), "strftime") else str(row.get("time"))[11:16], "message": message, "refine_tier": int(match.group(1)) if how == "REFINE SUCCESS" and match else 0})
    return list(reversed(events[-30:]))


def live_statuses():
    result = {}
    for pattern in STATUS_GLOBS:
        for path in Path("/").glob(pattern.lstrip("/")):
            try:
                if datetime.now().timestamp() - path.stat().st_mtime > 25:
                    continue
                for line in path.read_text(encoding="cp1250", errors="replace").splitlines()[1:]:
                    values = line.split("\t", 13)
                    if len(values) == 14:
                        result[int(values[0])] = {"personality": int(values[1]), "ambition": int(values[2]), "role": int(values[3]), "in_party": bool(int(values[4])), "goal": int(values[5]), "action": int(values[6]), "updated_ms": int(values[7]), "map_index": int(values[8]), "x": int(values[9]), "y": int(values[10]), "hp": int(values[11]), "max_hp": int(values[12]), "status": values[13]}
            except (OSError, ValueError):
                continue
    return result


def live_map_counts():
    counts = {}
    for entry in live_statuses().values():
        index = entry["map_index"]
        counts[index] = counts.get(index, 0) + 1
    return [{"map_index": index, "character_count": count} for index, count in sorted(counts.items(), key=lambda item: -item[1])]


def live_bots():
    statuses = live_statuses()
    if not statuses:
        return []
    ids = list(statuses)
    placeholders = ",".join(["%s"] * len(ids))
    roster = rows(f"""
        SELECT p.id, p.name, p.level, p.job, p.horse_level FROM player.player p
        LEFT JOIN account.account a ON a.id=p.account_id
        WHERE p.id IN ({placeholders}) AND (LEFT(a.login,10)='playerbot_' OR p.name LIKE 'bot%%')
    """, ids)
    threshold = max(1, min(120, int(settings().get("stuck_minutes", "5"))))
    historical = {}
    try:
        prior = rows("""SELECT s.pid,s.map_index,s.x,s.y FROM player.web_seban_bot_position_snapshot s
          JOIN (SELECT pid, MAX(captured_at) captured_at FROM player.web_seban_bot_position_snapshot
                WHERE captured_at <= NOW() - INTERVAL %s MINUTE GROUP BY pid) old
          ON old.pid=s.pid AND old.captured_at=s.captured_at WHERE s.pid IN (""" + placeholders + ")", (threshold, *ids))
        historical = {row["pid"]: row for row in prior}
    except pymysql.MySQLError:
        pass
    result = []
    for bot in roster:
        state = statuses.get(bot["id"])
        if state and state["map_index"] in MAP_BOUNDS:
            old = historical.get(bot["id"])
            stuck = bool(old and old["map_index"] == state["map_index"] and (old["x"] - state["x"]) ** 2 + (old["y"] - state["y"]) ** 2 < 40000 and not is_stationary_activity(state.get("status"), state.get("action")))
            # The free-text status is diagnostic and can be stale; action is the authoritative core state.
            result.append({
                **bot, **state,
                "personality_label": live_label("personality", state["personality"]),
                "ambition_label": live_label("ambition", state["ambition"]),
                "goal_label": live_label("goal", state["goal"]),
                "action_label": live_label("action", state["action"]),
                "stuck": stuck,
                "fighting_metin": int(state.get("goal") or 0) == 7 and int(state.get("action") or 0) == 2,
            })
    return result


def read_rates():
    values = {name: 100 for name in RATE_NAMES}
    status = read_rate_status()
    if all(str(status.get(name, "")).isdigit() for name in RATE_NAMES):
        return {name: int(status[name]) for name in RATE_NAMES}
    try:
        for row in rows("SELECT name, value FROM player.web_admin_rates"):
            if row["name"] in values:
                values[row["name"]] = int(row["value"])
    except (KeyError, ValueError, pymysql.MySQLError):
        pass
    return values


def read_rate_status():
    result = {}
    try:
        for line in (RATES_SPOOL / "rates.status").read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                result[key.strip()] = value.strip()
    except OSError:
        pass
    return result


def read_map_regen_status():
    status_file = RATES_SPOOL / "map-regens.status"
    result = {"state": "idle", "message": "Kaydedilmiş değişiklik yok", "values": {}, "stones": {}}
    try:
        for line in status_file.read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = line.partition("=")
            if not separator:
                continue
            if key.startswith("map_stone_") and key[10:].isdigit():
                result["stones"][int(key[10:])] = value
            elif key.startswith("map_") and key[4:].isdigit():
                result["values"][int(key[4:])] = value
            else:
                result[key] = value
    except OSError:
        pass
    return result


def read_spool_values(path):
    """Read a small key=value status file written by a fixed helper."""
    result = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                result[key.strip()] = value.strip()
    except OSError:
        pass
    return result


def update_status():
    """State exposed by Tieru's isolated updater through its tiny spool."""
    result = read_spool_values(UPDATE_SPOOL / "update.status")
    try:
        age = max(0, int(time.time() - (UPDATE_SPOOL / "watcher").stat().st_mtime))
    except OSError:
        age = None
    result["watcher_age"] = age
    result["watcher_ready"] = age is not None and age < UPDATE_WATCHER_MAX_AGE_SECONDS
    result["state"] = result.get("state", "idle")
    try:
        step, steps = int(result.get("step", 0)), int(result.get("steps", 5))
        result["percent"] = max(0, min(100, round(step * 100 / max(steps, 1))))
    except ValueError:
        result["percent"] = 0
    if result["state"] == "running":
        result["percent"] = max(5, result["percent"])
    result["message"] = result.get("message", "Güncelleyici bir talep bekliyor." if result["watcher_ready"] else "Güncelleyici çalışmıyor.")
    try:
        result["log"] = (UPDATE_SPOOL / "update.log").read_text(encoding="utf-8", errors="replace").splitlines()[-18:]
    except OSError:
        result["log"] = []
    return result


def installed_playerbots_version():
    """Prefer the version confirmed by the updater, then the configured baseline."""
    current = update_status()
    if current.get("state") == "ok":
        match = re.search(r"version ([0-9]+(?:\.[0-9]+)+)", current.get("message", ""))
        if match:
            return match.group(1)
    return os.environ.get("PLAYERBOTS_VERSION", "ayarlanmamış")


def version_key(value):
    match = re.fullmatch(r"v?([0-9]+(?:\.[0-9]+)+)", str(value or "").strip(), re.I)
    return tuple(int(part) for part in match.group(1).split(".")) if match else None


def latest_playerbots_release():
    """Read GitHub's latest release, cached so page loads never hammer the API."""
    now = time.time()
    if now - _playerbots_release_cache["checked_at"] < PLAYERBOTS_RELEASE_CACHE_SECONDS:
        return dict(_playerbots_release_cache)
    result = {"checked_at": now, "latest": None, "error": None}
    try:
        request_github = Request(PLAYERBOTS_RELEASE_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": "Metin2-Singleplayer-Panel"})
        with urlopen(request_github, timeout=3) as response:
            payload = json.load(response)
        tag = str(payload.get("tag_name") or "").strip()
        if not version_key(tag):
            raise ValueError("GitHub geçerli bir sürüm numarası döndürmedi.")
        result["latest"] = tag.lstrip("vV")
    except (OSError, ValueError, HTTPError, URLError, json.JSONDecodeError) as exc:
        result["error"] = str(exc)[:120] or "GitHub'a bağlanılamadı."
    _playerbots_release_cache.clear()
    _playerbots_release_cache.update(result)
    return dict(result)


def playerbots_release_status():
    installed = installed_playerbots_version().strip()
    latest_info = latest_playerbots_release()
    latest = latest_info.get("latest")
    installed_key, latest_key = version_key(installed), version_key(latest)
    if installed_key and latest_key:
        behind = installed_key < latest_key
        return {"installed": installed, "latest": latest, "behind": behind,
                "tone": "outdated" if behind else "current",
                "label": f"{latest} Mevcut" if behind else "Güncel"}
    return {"installed": installed, "latest": latest, "behind": False, "tone": "unknown",
            "label": "GitHub kontrol edilmedi" if latest_info.get("error") else "Yerel sürüm yok"}


def update_csrf_token():
    token = session.get("seban_update_csrf")
    if not token:
        token = uuid.uuid4().hex
        session["seban_update_csrf"] = token
    return token


def queue_tieru_update():
    """Request only the updater's fixed sequence; no command, URL or path crosses this boundary."""
    current = update_status()
    if not current["watcher_ready"]:
        raise RuntimeError("Güncelleyici hazır değil. Yönetici updater servisini başlatmalı.")
    if current.get("state") == "running":
        raise RuntimeError("Güncelleme zaten devam ediyor. Bitmesini bekleyin.")
    version = installed_playerbots_version().strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version):
        version = "0"
    request_id = "seban-" + uuid.uuid4().hex
    UPDATE_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = UPDATE_SPOOL / (request_id + ".new")
    try:
        temporary.write_text(f"id={request_id}\nversion={version}\ntime={int(time.time())}\n", encoding="utf-8")
        temporary.chmod(0o660)
        # replace is atomic. The worker records the id before doing work, so a
        # completed request never runs twice after a container recreation.
        os.replace(temporary, UPDATE_SPOOL / "request")
    finally:
        temporary.unlink(missing_ok=True)


def read_ai_weights():
    """Read Tieru's live Playerbots goal weights; absent entries are neutral."""
    values = {key: AI_WEIGHT_NEUTRAL for key, _, _ in AI_WEIGHT_KEYS}
    values.update(AI_LIVE_DEFAULTS)
    try:
        for line in AI_WEIGHTS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            fields = line.split("#", 1)[0].split()
            if len(fields) >= 2 and fields[0].upper() in values:
                try:
                    key, raw_value = fields[0].upper(), fields[1]
                    if key in ("CHAT", "BOOKS", "NIGHT"):
                        values[key] = 0 if raw_value.lower() in ("0", "off", "no") else 1
                    elif key in ("SCRAP", "REST"):
                        values[key] = max(0, min(100, int(raw_value)))
                    elif key in ("CHEST", "CHEST_STONE"):
                        values[key] = max(0, min(1000, int(raw_value)))
                    else:
                        values[key] = max(AI_WEIGHT_MIN, min(AI_WEIGHT_MAX, int(raw_value)))
                except ValueError:
                    pass
    except OSError:
        pass
    return values


def preserved_ai_weight_lines():
    """Keep new core keys this panel does not know about yet on every save."""
    known = {key for key, _, _ in AI_WEIGHT_KEYS} | AI_SPECIAL_WEIGHT_KEYS
    preserved = []
    try:
        for line in AI_WEIGHTS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            fields = line.split("#", 1)[0].split()
            if len(fields) != 2:
                continue
            key, value = fields[0].upper(), fields[1]
            if key not in known and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", key) and re.fullmatch(r"-?\d{1,10}", value):
                preserved.append(f"{key}\t{value}")
    except OSError:
        pass
    return preserved


def write_ai_weights(values):
    """Atomically replace known values without erasing newer-core settings."""
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    content = [
        "# Metin2 Playerbots — Seban Panel tarafından ayarlanan hedef ağırlıkları.",
        "# 25 = nadiren · 100 = varsayılan · 250 = sık.",
        "# Çekirdek dosyayı her beş saniyede okur; yeniden başlatma gerekmez.", "",
    ]
    content.extend(f"{key}\t{values[key]}" for key, _, _ in AI_WEIGHT_KEYS)
    content.append(f"CHAT\t{1 if values.get('CHAT', 1) else 0}")
    content.append(f"BOOKS\t{1 if values.get('BOOKS', 1) else 0}")
    content.append(f"NIGHT\t{1 if values.get('NIGHT', 1) else 0}")
    content.append(f"SCRAP\t{max(0, min(100, int(values.get('SCRAP', 0))))}")
    content.append(f"REST\t{max(0, min(100, int(values.get('REST', 100))))}")
    for key in ("CHEST", "CHEST_STONE"):
        if values.get(key) is not None:
            content.append(f"{key}\t{max(0, min(1000, int(values[key])))}")
    content.extend(preserved_ai_weight_lines())
    temporary = AI_WEIGHTS_FILE.with_suffix(".tsv.new")
    temporary.write_text("\n".join(content) + "\n", encoding="utf-8")
    os.replace(temporary, AI_WEIGHTS_FILE)


def port_open(port):
    try:
        with socket.create_connection((GAME_HOST, port), timeout=0.4):
            return True
    except OSError:
        return False


def restart_progress():
    result = {}
    try:
        for line in (RATES_SPOOL / "server-settings.status").read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep:
                result[key] = value
        result["percent"] = max(0, min(100, int(result.get("percent", 0))))
        result["stage"] = result.get("message", "Sunucu durumu bekleniyor")
        if (RATES_SPOOL / "server-settings.request").exists() and result.get("state") != "running":
            result.update(state="running", percent=5, stage="Talep sunucuyu bekliyor")
        return result
    except (OSError, ValueError):
        pass
    status = read_rate_status()
    auth, world = port_open(GAME_LOGIN_PORT), port_open(GAME_WORLD_PORT)
    state = status.get("state", "unknown")
    if state == "running":
        if not auth:
            return {"percent": 25, "stage": "Oyun süreçleri durduruluyor", "state": state}
        if not world:
            return {"percent": 65, "stage": "Giriş sunucusu çalışıyor — dünya başlatılıyor", "state": state}
        return {"percent": 85, "stage": "Kanal ve servisler kontrol ediliyor", "state": state}
    if state == "ok" and auth and world:
        return {"percent": 100, "stage": "Sunucu çalışıyor", "state": state}
    if state == "failed":
        return {"percent": 100, "stage": status.get("message", "Yeniden başlatma başarısız oldu"), "state": state}
    return {"percent": 100 if auth and world else 40, "stage": "Sunucu çalışıyor" if auth and world else "Servisler bekleniyor", "state": state}


# On the mt2009 line a rate is not a rewritten table but six event flags the
# engine multiplies by (mob_exp / mob_item / mob_gold and their "_buyer"
# twins for premium accounts): rows of player.quest with dwPID = 0, read by the
# db core at boot and pushed to every game core. The game container has no
# database client, so the panel writes the rows and the restart it queues
# below is what makes the cores read them. See files/admin_panel.py, which
# also tries the in-game helper first; this console is a restart console.
MT2009_RATE_FLAGS = {
    "exp":  ("mob_exp",  "mob_exp_buyer"),
    "drop": ("mob_item", "mob_item_buyer"),
    "yang": ("mob_gold", "mob_gold_buyer"),
}


def persist_rates_mt2009(values):
    with db() as connection, connection.cursor() as cursor:
        for name, flags in MT2009_RATE_FLAGS.items():
            for flag in flags:
                cursor.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, %s, '', %s)",
                               (flag, int(values[name])))
        # The classic panel's table too, so both pages show the same numbers.
        try:
            for name in RATE_NAMES:
                cursor.execute("INSERT INTO player.web_admin_rates (name, value) VALUES (%s, %s) "
                               "ON DUPLICATE KEY UPDATE value=VALUES(value)", (name, int(values[name])))
        except pymysql.MySQLError:
            pass
        connection.commit()


def queue_rate_restart(values):
    if ENGINE_MT2009:
        persist_rates_mt2009(values)
    stamp = int(time.time() * 1000)
    request_data = "\n".join((
        f"id=seban-{stamp}",
        f"exp={values['exp']}",
        f"drop={values['drop']}",
        f"yang={values['yang']}",
        f"time={int(time.time())}",
        "",
    ))
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = RATES_SPOOL / "request.new"
    temporary.write_text(request_data, encoding="utf-8")
    os.replace(temporary, RATES_SPOOL / "request")
    (RATES_SPOOL / "rates.status").write_text(
        "state=running\ntime=%s\nexp=%s\ndrop=%s\nyang=%s\nmessage=restart requested by Seban Panel\n" %
        (int(time.time()), values["exp"], values["drop"], values["yang"]), encoding="utf-8")


def server_settings_status():
    """Report whether the game-side restart helper is alive, not just queued."""
    ready = read_spool_values(RATES_SPOOL / "server-settings.ready")
    request = RATES_SPOOL / "server-settings.request"
    status = read_spool_values(RATES_SPOOL / "server-settings.status")
    try:
        ready_age = max(0, int(time.time() - (RATES_SPOOL / "server-settings.ready").stat().st_mtime))
    except OSError:
        ready_age = None
    try:
        request_age = max(0, int(time.time() - request.stat().st_mtime))
    except OSError:
        request_age = None
    worker_ready = ready.get("capability") == "server-settings" and ready_age is not None and ready_age <= SERVER_SETTINGS_READY_MAX_AGE_SECONDS
    result = {"ready": worker_ready, "ready_age": ready_age, "pending": request.exists(), "request_age": request_age,
              "can_clear": bool(request_age is not None and request_age >= SERVER_SETTINGS_STALE_SECONDS and not worker_ready)}
    if worker_ready:
        result["message"] = "Sunucu ayarları yardımcısı hazır."
    elif result["pending"]:
        result["message"] = "Talep oyun yardımcısı tarafından alınmıyor. Entegrasyon kurulumunu kontrol edin; 10 dakika sonra yalnızca bekleyen talep silinebilir."
    else:
        # Telling the operator to install something this build never ships is
        # not help, and the warning fired on every visit to the console even
        # though both buttons that matter work without the helper.
        result["message"] = ("Bu sunucu sürümü Seban'ın motor entegrasyonunu içermiyor, "
                             "bu yüzden harita respawn değişikliği kullanılamıyor. Sunucu yeniden "
                             "başlatma ve oran değişikliği normal şekilde çalışır ve hiçbir şey gerektirmez.")
    return result


RESTART_STALE_SECONDS = 600


def restart_in_flight():
    status = read_rate_status()
    if status.get("state") != "running":
        return False
    try:
        started = int(status.get("time", "0"))
    except (TypeError, ValueError):
        return False
    return 0 < time.time() - started < RESTART_STALE_SECONDS


def queue_server_settings(action, values=None, changes=None):
    """Publish a complete request only while the game-side helper is present."""
    support = server_settings_status()
    if not support["ready"]:
        # The settings helper (integration/m2-server-settings) is not part of
        # this image, so the map respawn half of the console has nothing to
        # carry it out and is refused with the message above. A plain restart,
        # and a rates-only apply, never needed it: the game container has
        # always watched the rates spool, and that is the path both buttons
        # took before 1.38 - refusing them here would put the dead restart
        # button of 1.30.19 back on every install without the helper.
        # An empty respawn field arrives as "reset", for every map, from a
        # form nobody touched - so "no respawn change" is "nothing but resets".
        respawn_changes = {key: value for key, value in (changes or {}).items() if value != "reset"}
        if action == "restart" or (action == "apply" and values and not respawn_changes):
            if restart_in_flight():
                raise FileExistsError("a restart is already under way")
            queue_rate_restart(values if action == "apply" else read_rates())
            return
        raise RuntimeError(support["message"])
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    request_id = "seban-" + uuid.uuid4().hex
    lines = [f"id={request_id}", f"action={action}", "source=panel"]
    if action == "apply":
        lines.extend(f"{key}={values[key]}" for key in RATE_NAMES)
        lines.extend(f"map_{key}={value}" for key, value in (changes or {}).items())
    temporary = RATES_SPOOL / (request_id + ".new")
    try:
        temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temporary.chmod(0o660)
        # A hard link is an atomic, exclusive publication on the shared volume.
        os.link(temporary, RATES_SPOOL / "server-settings.request")
    finally:
        temporary.unlink(missing_ok=True)


def queue_map_regen_changes(changes):
    stamp = int(time.time() * 1000)
    request_data = [f"id=seban-map-{stamp}", f"time={int(time.time())}"]
    request_data.extend(f"map_{map_index}={value}" for map_index, value in changes.items())
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = RATES_SPOOL / "map-regens.request.new"
    temporary.write_text("\n".join(request_data) + "\n", encoding="utf-8")
    os.replace(temporary, RATES_SPOOL / "map-regens.request")
    (RATES_SPOOL / "map-regens.status").write_text(
        "state=running\ntime=%s\nmessage=Respawn değişiklik seti kaydedildi; çekirdekler yeniden başlatılacak.\n" % int(time.time()),
        encoding="utf-8",
    )


def queue_map_regen_change(map_index, action, seconds=None):
    """Backward-compatible single-map queue entry."""
    queue_map_regen_changes({int(map_index): "reset" if action == "reset" else int(seconds)})


def biologist_missions():
    """Known Biologist missions plus names already emitted by the game."""
    names = set(BIOLOGIST_FALLBACK_MISSIONS)
    try:
        discovered = rows("""SELECT DISTINCT szName FROM player.quest
                           WHERE szName REGEXP '^(make_herb_lv[0-9]+|collect_quest_lv[0-9]+)$'""")
        names.update(row["szName"] for row in discovered if row.get("szName"))
    except pymysql.MySQLError:
        pass

    def mission_order(name):
        match = re.search(r"([0-9]+)$", name)
        return (int(match.group(1)) if match else 0, name)

    return tuple(sorted(names, key=mission_order))


# ---------------------------------------------------------------------------
# What makes a character a bot, in one place instead of eight.
#
# The name used to be the test: everything this project creates is called
# bot<something>, so `name LIKE 'bot%'` found them all. Rename them - which is
# exactly what the Discord keeps asking for, human nicknames instead of
# botarek7 - and every ranking, the live map, the world statistics and the
# season page quietly stop counting them.
#
# The core never asks the name. CPlayerBotManager::LoadRegisteredBots accepts a
# character only when its account login is exactly playerbot_NNN, and renaming a
# character does not touch an account login. So that is what is asked here too,
# with the old name test kept beside it, so a hand-made bot on an ordinary
# account stays visible exactly as before.
#
# The classic panel has had this since it was bitten by the same thing; this is
# the same predicate, spelled for the aliases these queries use.
def bot_identity(alias="p"):
    ref = (alias + ".") if alias else ""
    return ("(EXISTS (SELECT 1 FROM account.account ba"
            " WHERE ba.id = " + ref + "account_id"
            " AND LEFT(ba.login, 10) = 'playerbot_')"
            " OR " + ref + "name LIKE 'bot%%')")


BOT_IS = bot_identity("p")
BOT_IS_BARE = bot_identity("")


def bot_ranking(kind, sort_by="avg"):
    base = BOT_IS
    if kind == "gold":
        return rows(f"SELECT p.id,p.name,p.level,p.gold,CONCAT(FORMAT(p.gold,0),' Yang') AS detail FROM player.player p WHERE {base} ORDER BY p.gold DESC,p.level DESC LIMIT 100")
    if kind == "weapon":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)) AS detail
            FROM player.player p LEFT JOIN player.item i ON i.owner_id=p.id AND i.window='EQUIPMENT' AND i.pos=4
            LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum WHERE {base}
            ORDER BY MOD(COALESCE(i.vnum,0),10) DESC,i.vnum DESC,p.level DESC LIMIT 100""")
    if kind == "armor":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)) AS detail
            FROM player.player p LEFT JOIN player.item i ON i.owner_id=p.id AND i.window='EQUIPMENT' AND i.pos=0
            LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum WHERE {base}
            ORDER BY MOD(COALESCE(i.vnum,0),10) DESC,i.vnum DESC,p.level DESC LIMIT 100""")
    if kind == "weapon30":
        weapon30_order = {
            "avg": "avg_damage DESC, skill_damage DESC, p.level DESC",
            "skill": "skill_damage DESC, avg_damage DESC, p.level DESC",
            "upgrade": "MOD(i.vnum,10) DESC, avg_damage DESC, skill_damage DESC, p.level DESC",
        }.get(sort_by, "avg_damage DESC, skill_damage DESC, p.level DESC")
        # avg_damage reads APPLY_NORMAL_HIT_DAMAGE_BONUS (72), and
        # skill_damage APPLY_SKILL_DAMAGE_BONUS (71) - exactly as
        # common/length.h names them. Up to 1.33.0 the aliases were swapped,
        # so ORDER BY picked the first hundred by the wrong column, and
        # fixing the sort alone in Python would not have helped.
        result = rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)) AS item_name,
            IF(GREATEST(CASE WHEN i.attrtype0={ATTR_SKILL_DAMAGE} THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1={ATTR_SKILL_DAMAGE} THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2={ATTR_SKILL_DAMAGE} THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3={ATTR_SKILL_DAMAGE} THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4={ATTR_SKILL_DAMAGE} THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5={ATTR_SKILL_DAMAGE} THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6={ATTR_SKILL_DAMAGE} THEN i.attrvalue6 ELSE -999 END)=-999,0,GREATEST(CASE WHEN i.attrtype0={ATTR_SKILL_DAMAGE} THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1={ATTR_SKILL_DAMAGE} THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2={ATTR_SKILL_DAMAGE} THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3={ATTR_SKILL_DAMAGE} THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4={ATTR_SKILL_DAMAGE} THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5={ATTR_SKILL_DAMAGE} THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6={ATTR_SKILL_DAMAGE} THEN i.attrvalue6 ELSE -999 END)) AS skill_damage,
            IF(GREATEST(CASE WHEN i.attrtype0={ATTR_AVG_DAMAGE} THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1={ATTR_AVG_DAMAGE} THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2={ATTR_AVG_DAMAGE} THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3={ATTR_AVG_DAMAGE} THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4={ATTR_AVG_DAMAGE} THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5={ATTR_AVG_DAMAGE} THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6={ATTR_AVG_DAMAGE} THEN i.attrvalue6 ELSE -999 END)=-999,0,GREATEST(CASE WHEN i.attrtype0={ATTR_AVG_DAMAGE} THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1={ATTR_AVG_DAMAGE} THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2={ATTR_AVG_DAMAGE} THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3={ATTR_AVG_DAMAGE} THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4={ATTR_AVG_DAMAGE} THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5={ATTR_AVG_DAMAGE} THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6={ATTR_AVG_DAMAGE} THEN i.attrvalue6 ELSE -999 END)) AS avg_damage
            FROM player.item i JOIN player.player p ON p.id=i.owner_id LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum
            WHERE {base} AND ((i.vnum BETWEEN 290 AND 299) OR (i.vnum BETWEEN 1170 AND 1179) OR (i.vnum BETWEEN 2150 AND 2159) OR (i.vnum BETWEEN 3210 AND 3219) OR (i.vnum BETWEEN 5110 AND 5119) OR (i.vnum BETWEEN 7160 AND 7169))
            ORDER BY {weapon30_order} LIMIT 100""")
        # 71 is APPLY_SKILL_DAMAGE_BONUS and 72 is APPLY_NORMAL_HIT_DAMAGE_BONUS in
        # common/length.h, and the query names them so. A swap used to live
        # here, justified by "this build stores them the other way round" -
        # it does not, and the ranking showed the two columns exchanged.
        return sorted(
            result,
            key=lambda row: (
                (int(row.get("avg_damage") or 0), int(row.get("skill_damage") or 0), int(row.get("level") or 0)) if sort_by == "avg" else
                (int(row.get("skill_damage") or 0), int(row.get("avg_damage") or 0), int(row.get("level") or 0)) if sort_by == "skill" else
                (int(row.get("vnum") or 0) % 10, int(row.get("avg_damage") or 0), int(row.get("skill_damage") or 0), int(row.get("level") or 0))
            ),
            reverse=True,
        )
    if kind == "playtime":
        return rows(f"SELECT p.id,p.name,p.level,p.gold,p.playtime AS score,CONCAT(FLOOR(p.playtime/60),' h') AS detail FROM player.player p WHERE {base} ORDER BY p.playtime DESC,p.level DESC LIMIT 100")
    if kind == "bosses":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(*) AS score,
            CONCAT(COUNT(*),' boss öldürüldü · 7 gün') AS detail
            FROM log.log l JOIN player.player p ON p.id=l.who
            WHERE {base} AND l.how='BOSS_KILL' AND l.time >= NOW() - INTERVAL 7 DAY
            GROUP BY p.id,p.name ORDER BY score DESC,p.level DESC,p.name LIMIT 100""")
    if kind == "items":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(i.id) AS score,CONCAT(COUNT(i.id),' eşya') AS detail
            FROM player.player p LEFT JOIN player.item i ON i.owner_id=p.id AND i.window='INVENTORY'
            WHERE {base} GROUP BY p.id ORDER BY score DESC,p.level DESC LIMIT 100""")
    if kind == "horse":
        return rows(f"SELECT p.id,p.name,p.level,p.gold,p.horse_level AS score,CONCAT('At Lv ',p.horse_level) AS detail FROM player.player p WHERE {base} ORDER BY p.horse_level DESC,p.level DESC LIMIT 100")
    if kind == "biologist":
        missions = biologist_missions()
        marks = ",".join(["%s"] * len(missions))
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(DISTINCT q.szName) AS score,CONCAT(COUNT(DISTINCT q.szName),' / {len(missions)} görev') AS detail
            FROM player.player p LEFT JOIN player.quest q ON q.dwPID=p.id AND q.szName IN ({marks}) AND q.szState='__status' AND q.lValue=%s
            WHERE {base} GROUP BY p.id ORDER BY score DESC,p.level DESC LIMIT 100""", (*missions, BIOLOGIST_COMPLETE_STATE))
    # The "hunting" ranking was removed along with its tab: levelup.quest
    # does not run on this engine line, so the query always returned a
    # hundred rows of zero. A stale ?type=hunting link falls through to
    # the default level ranking since "hunting" is no longer in kinds.
    if kind == "shops":
        keeper_ids = [pid for pid, state in live_statuses().items() if int(state.get("action") or 0) == 13]
        if not keeper_ids:
            return []
        placeholders = ",".join(["%s"] * len(keeper_ids))
        return rows(f"SELECT p.id,p.name,p.level,p.gold,'Tezgah açık' AS detail FROM player.player p WHERE p.id IN ({placeholders}) ORDER BY p.level DESC LIMIT 100", keeper_ids)
    if kind == "skills":
        # Every bot with a profession, not the four hundred highest by level.
        # A skill ranking sorted by level first answers a different question:
        # a bot of thirty with a Master skill stood behind four hundred
        # fifties with none and never showed up at all. Scoring is in Python
        # anyway, because skill_level is a blob, so the whole set has to come back.
        roster = rows(f"SELECT p.id,p.name,p.level,p.gold,p.job,p.skill_group,p.skill_level FROM player.player p WHERE {base} AND p.skill_group>0 ")
        for bot in roster:
            best = max(parse_skills(bot.get("skill_level"), bot.get("job"), bot.get("skill_group")), key=lambda skill: (3 if skill["rank"] == "P" else 2 if skill["rank"].startswith("G") else 1 if skill["rank"].startswith("M") else 0, skill["level"]), default=None)
            bot["score"] = (3 if best and best["rank"] == "P" else 2 if best and best["rank"].startswith("G") else 1 if best and best["rank"].startswith("M") else 0, best["level"] if best else 0)
            bot["detail"] = f"{best['name']} · {best['rank']}" if best else "Geliştirilmiş yetenek yok"
        return sorted(roster, key=lambda bot: (bot["score"], bot["level"]), reverse=True)[:100]
    if kind == "plus9":
        # item_proto, not a number, decides which vnums are equipment:
        # "under 12000" was meant to screen out materials and screened out
        # every shield (13xxx) and all jewellery with them. type 1 is
        # ITEM_WEAPON, 2 is ITEM_ARMOR - exactly the set whose refine
        # ladder runs base+0..9.
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)) AS detail
            FROM player.item i JOIN player.player p ON p.id=i.owner_id LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum
            WHERE {base} AND ip.type IN (1,2) AND MOD(i.vnum,10)=9 ORDER BY i.vnum DESC,p.level DESC LIMIT 100""")
    return rows(f"SELECT p.id,p.name,p.level,p.gold,p.level AS score,'Seviye' AS detail FROM player.player p WHERE {base} ORDER BY p.level DESC,p.exp DESC LIMIT 100")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        current = settings()
        if current.get("setup_complete") != "1":
            return redirect(url_for("setup"))
        if current.get("auth_enabled") != "1":
            return view(*args, **kwargs)
        if not session.get("seban_admin"):
            return redirect(url_for("login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def globals_for_templates():
    tieru_url = os.environ.get("TIERU_PANEL_URL", "http://127.0.0.1:7788")
    def item_icon(vnum):
        try:
            value = int(vnum)
        except (TypeError, ValueError):
            return None
        # Most upgrade series use the same client icon for +0 through +9.
        # Prefer an explicit mapping, then fall back to the base VNUM safely.
        icon = ITEM_ICONS.get(str(value)) or ITEM_ICONS.get(str(value - value % 10))
        return url_for("static", filename=f"icons/{quote(icon)}") if icon else None
    current_settings = settings()
    def job_name(job):
        return class_profile(job)["name"]
    def class_portrait(job):
        return url_for("static", filename=f"class-portraits/{class_profile(job)['portrait']}")
    def empire_flag(empire):
        flag = empire_flag_path(empire)
        return url_for("static", filename=f"empires/{flag}") if flag else ""
    return {"tieru_url": tieru_url, "panel_brand": current_settings.get("panel_name", "Metin2 Singleplayer"), "settings": current_settings, "map_name": map_name, "item_icon": item_icon, "job_name": job_name, "class_profile": class_profile, "class_portrait": class_portrait, "empire_info": empire_info, "empire_flag": empire_flag}
@app.route("/login", methods=["GET", "POST"])
def login():
    current = settings()
    if current.get("auth_enabled") != "1":
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        password_hash = current.get("auth_password_hash", "")
        if password_hash and check_password_hash(password_hash, request.form.get("password", "")):
            session.clear()
            session["seban_admin"] = True
            session.permanent = True
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Yanlış şifre.", "error")
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    current = settings()
    if current.get("setup_complete") == "1":
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        values, error = validate_display_settings(request.form)
        password = request.form.get("panel_password", "")
        enable_auth = request.form.get("auth_enabled") == "1"
        if enable_auth and len(password) < 8:
            error = "Panel şifresi en az 8 karakter olmalı."
        if error:
            flash(error, "error")
        else:
            values.update({"setup_complete": "1", "auth_enabled": "1" if enable_auth else "0", "auth_password_hash": generate_password_hash(password) if enable_auth else ""})
            write_settings(values)
            if enable_auth:
                session["seban_admin"] = True
            flash("Yapılandırma kaydedildi.")
            return redirect(url_for("dashboard"))
    return render_template("setup.html", current=current)


@app.route("/")
@login_required
def dashboard():
    totals = one("""
        SELECT
          (SELECT COUNT(*) FROM player.player) AS characters,
          (SELECT COUNT(*) FROM account.account) AS accounts,
          (SELECT COUNT(*) FROM player.item) AS item_stacks,
          (SELECT COALESCE(SUM(gold),0) FROM player.player WHERE name NOT IN ('[SA]Admin','Test')) AS yang
    """)
    bots = one("SELECT COUNT(*) AS count FROM player.player WHERE account_id BETWEEN 4 AND 1003")
    # The collector creates this table with its first snapshot; before that -
    # the first minutes of a fresh installation - the dashboard has no host
    # metrics to show, not an error to raise.
    try:
        system = one("SELECT * FROM player.web_seban_system_snapshot ORDER BY captured_at DESC LIMIT 1")
    except pymysql.MySQLError:
        system = {}
    map_rows = live_map_counts()
    for row in map_rows:
        row["name"] = map_name(row["map_index"])
    top = rows("SELECT id, name, level, exp, job, map_index, playtime FROM player.player WHERE " + BOT_IS_BARE + " ORDER BY level DESC, exp DESC LIMIT 10")
    global_top_id = top[0]["id"] if top else None
    live = live_statuses()
    live_roster = live_bots()
    try:
        bot_guilds = one("""SELECT COUNT(*) AS count FROM player.guild g
                           JOIN player.player p ON p.id=g.master WHERE """ + BOT_IS).get("count", 0)
    except pymysql.MySQLError:
        bot_guilds = 0
    restart_status = read_rate_status()
    restart_time = restart_status.get("time")
    try:
        restart_label = datetime.fromtimestamp(int(restart_time)).strftime("%d.%m.%Y, %H:%M:%S")
    except (TypeError, ValueError, OSError):
        restart_label = "Veri yok"
    release_status = playerbots_release_status()
    world_summary = {
        "bots": len(live_roster),
        "average_level": round(sum(int(bot.get("level") or 0) for bot in live_roster) / len(live_roster), 1) if live_roster else 0,
        "party_bots": sum(1 for bot in live_roster if bot.get("in_party")),
        "max_level": max((int(bot.get("level") or 0) for bot in live_roster), default=0),
        "horse_average": round(sum(int(bot.get("horse_level") or 0) for bot in live_roster) / len(live_roster), 1) if live_roster else 0,
        "horse_max": max((int(bot.get("horse_level") or 0) for bot in live_roster), default=0),
        "guilds": bot_guilds,
        "last_restart": restart_label,
        "version": release_status["installed"],
        "release": release_status,
        "rates": read_rates(),
    }
    for bot in top:
        if bot["id"] in live:
            bot["map_index"] = live[bot["id"]]["map_index"]
    quick_rankings = []
    quick_rankings.append({"title": "Seviye", "subtitle": "en yüksek seviyeler", "items": [{"id": row["id"], "name": row["name"], "value": f"Lv {row['level']}"} for row in top]})
    playtime = bot_ranking("playtime")[:10]
    quick_rankings.append({"title": "Oyun Süresi", "subtitle": "en uzun süre çevrimiçi", "items": [{"id": row["id"], "name": row["name"], "value": row["detail"]} for row in playtime]})
    gold = bot_ranking("gold")[:10]
    quick_rankings.append({"title": "Yang", "subtitle": "karakterde en fazla", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row.get('gold') or 0):,}".replace(",", " ")} for row in gold]})
    weapon30 = bot_ranking("weapon30")[:10]
    quick_rankings.append({"title": "30 Lv Silah", "subtitle": "ortalama / yetenek", "items": [{"id": row["id"], "name": row["name"], "value": f"Ort. {int(row.get('avg_damage') or 0)}% · Yet. {int(row.get('skill_damage') or 0)}%"} for row in weapon30]})
    metins = rows("""SELECT p.id,p.name,COUNT(*) AS score FROM log.log l JOIN player.player p ON p.id=l.who
                     WHERE """ + BOT_IS + """ AND l.how='STONE_KILL' AND l.time >= NOW() - INTERVAL 7 DAY
                     GROUP BY p.id,p.name ORDER BY score DESC,p.name LIMIT 10""")
    quick_rankings.append({"title": "Metinler", "subtitle": "kırılan · son 7 gün", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} adet"} for row in metins]})
    bosses = bot_ranking("bosses")[:10]
    quick_rankings.append({"title": "Bosslar", "subtitle": "öldürülen · son 7 gün", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} adet"} for row in bosses]})
    fish = rows("""SELECT p.id,p.name,COUNT(*) AS score FROM log.log l JOIN player.player p ON p.id=l.who
                   WHERE """ + BOT_IS + """ AND l.time >= NOW() - INTERVAL 7 DAY
                     AND (l.what LIKE '%%ryb%%' OR l.what LIKE '%%fish%%')
                   GROUP BY p.id,p.name ORDER BY score DESC,p.name LIMIT 10""")
    quick_rankings.append({"title": "Balıklar", "subtitle": "yakalanan · son 7 gün", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} adet"} for row in fish]})
    ranking_ids = {item["id"] for ranking in quick_rankings for item in ranking["items"]}
    if ranking_ids:
        placeholders = ",".join(["%s"] * len(ranking_ids))
        jobs_by_id = {row["id"]: row["job"] for row in rows("SELECT id,job FROM player.player WHERE id IN (" + placeholders + ")", list(ranking_ids))}
        for quick_ranking in quick_rankings:
            for item in quick_ranking["items"]:
                item["job"] = jobs_by_id.get(item["id"], 0)
    return render_template("dashboard.html", totals=totals, bots=bots.get("count", 0), system=system, map_rows=map_rows, top=top, global_top_id=global_top_id, quick_rankings=quick_rankings, world_summary=world_summary, panel_version=PANEL_VERSION, latest_changelog=changelog_entries()[:1])
@app.route("/players")
@login_required
def players():
    query = request.args.get("q", "").strip()
    sql = "SELECT id, name, level, job, map_index, gold, playtime, last_play FROM player.player"
    args = []
    if query:
        sql += " WHERE name LIKE %s OR id=%s"
        args = [f"%{query}%", query if query.isdigit() else -1]
    sql += " ORDER BY level DESC, exp DESC LIMIT 250"
    roster, live = rows(sql, args), live_statuses()
    for character in roster:
        state = live.get(character["id"])
        character["map_live"] = bool(state)
        if state:
            character["map_index"] = state["map_index"]
    return render_template("players.html", players=roster, query=query)


@app.route("/guilds")
@login_required
def guilds():
    query = request.args.get("q", "").strip()
    filters, args = "", []
    if query:
        filters = "WHERE g.name LIKE %s OR leader.name LIKE %s"
        args = [f"%{query}%", f"%{query}%"]
    roster = rows(f"""SELECT g.id,g.name,g.level,g.exp,g.sp,g.win,g.draw,g.loss,g.ladder_point,g.gold,
                     leader.id AS leader_id,leader.name AS leader_name,leader.level AS leader_level,
                     COUNT(gm.pid) AS member_count
                     FROM player.guild g
                     LEFT JOIN player.player leader ON leader.id=g.master
                     LEFT JOIN player.guild_member gm ON gm.guild_id=g.id
                     {filters}
                     GROUP BY g.id,g.name,g.level,g.exp,g.sp,g.win,g.draw,g.loss,g.ladder_point,g.gold,leader.id,leader.name,leader.level
                     ORDER BY g.level DESC,member_count DESC,g.name ASC LIMIT 250""", args)
    return render_template("guilds.html", guilds=roster, query=query)


@app.route("/guild/<int:guild_id>")
@login_required
def guild(guild_id):
    details = one("""SELECT g.id,g.name,g.level,g.exp,g.sp,g.win,g.draw,g.loss,g.ladder_point,g.gold,
                     leader.id AS leader_id,leader.name AS leader_name,leader.level AS leader_level,
                     COUNT(gm.pid) AS member_count
                     FROM player.guild g
                     LEFT JOIN player.player leader ON leader.id=g.master
                     LEFT JOIN player.guild_member gm ON gm.guild_id=g.id
                     WHERE g.id=%s
                     GROUP BY g.id,g.name,g.level,g.exp,g.sp,g.win,g.draw,g.loss,g.ladder_point,g.gold,leader.id,leader.name,leader.level""", (guild_id,))
    if not details:
        abort(404)
    members = rows("""SELECT gm.pid,gm.grade,gm.is_general,gm.offer,p.name,p.level,p.job,p.map_index,p.playtime
                    FROM player.guild_member gm LEFT JOIN player.player p ON p.id=gm.pid
                    WHERE gm.guild_id=%s
                    ORDER BY (gm.pid=%s) DESC,gm.grade ASC,p.level DESC,p.name ASC""", (guild_id, details["leader_id"] or 0))
    return render_template("guild.html", guild=details, members=members)


@app.route("/player/<int:pid>")
@login_required
def player(pid):
    character = one("SELECT p.id,p.account_id,p.name,p.level,p.job,p.exp,p.gold,p.hp,p.mp,p.x,p.y,p.horse_level,p.alignment,p.st,p.ht,p.dx,p.iq,p.stat_point,p.skill_point,p.skill_group,p.skill_level,p.map_index,p.playtime," + EMPIRE_EXPR + " AS empire FROM player.player p LEFT JOIN account.account a ON a.id=p.account_id LEFT JOIN player.player_index pi ON pi.id=p.account_id WHERE p.id=%s", (pid,))
    if not character:
        abort(404)
    live = live_statuses().get(pid)
    if live:
        character.update(live)
        character["personality"] = live_label("personality", live.get("personality"))
        character["ambition"] = live_label("ambition", live.get("ambition"))
        character["goal"] = live_label("goal", live.get("goal"))
        character["action"] = live.get("status") or live_label("action", live.get("action"))
    else:
        character.update({"personality": "Bot çevrimdışı", "ambition": "—", "goal": "—", "action": "—"})
    character["job_name"] = class_profile(character.get("job"))["name"]
    character["class_profile"] = class_profile(character.get("job"))
    character["experience"] = experience_progress(character.get("level"), character.get("exp"))
    character["honor"] = honor_rank(character.get("alignment"))
    character["honor"]["css"] = {"Şövalye Ruhlu": "knightly", "Asil": "noble", "İyi": "good", "Dostane": "friendly", "Nötr": "neutral", "Saldırgan": "aggressive", "Sahtekar": "dishonest", "Kötü Niyetli": "malicious", "Acımasız": "cruel"}[character["honor"]["title"]]
    character["max_hp"] = max(int(character.get("max_hp") or 0), int(character.get("hp") or 0), 1)
    # The live Playerbots feed exposes exact max HP.  The original server
    # schema does not persist max MP, so an offline character is shown as a
    # current-value bar until it is next observed live.
    character["max_mp"] = max(int(character.get("max_mp") or 0), int(character.get("mp") or 0), 1)
    character["hp_percent"] = min(100, round(int(character.get("hp") or 0) * 100 / character["max_hp"], 1))
    character["mp_percent"] = min(100, round(int(character.get("mp") or 0) * 100 / character["max_mp"], 1))
    character["skills"] = parse_skills(character.pop("skill_level", b""), character.get("job"), character.get("skill_group"))
    items = rows("""
      SELECT i.id, i.vnum, i.count, i.window, i.pos, i.socket0,i.socket1,i.socket2,
      i.attrtype0,i.attrvalue0,i.attrtype1,i.attrvalue1,i.attrtype2,i.attrvalue2,i.attrtype3,i.attrvalue3,i.attrtype4,i.attrvalue4,i.attrtype5,i.attrvalue5,i.attrtype6,i.attrvalue6,
      p.applytype0,p.applyvalue0,p.applytype1,p.applyvalue1,p.applytype2,p.applyvalue2,p.size AS item_size,COALESCE(p.locale_name, CONCAT('VNUM ', i.vnum)) AS item_name
      FROM player.item i LEFT JOIN player.item_proto p ON p.vnum=i.vnum WHERE i.owner_id=%s
      ORDER BY i.window, i.pos LIMIT 250
    """, (pid,))
    safebox = rows("""
      SELECT i.id,i.vnum,i.count,i.window,i.pos,i.socket0,i.socket1,i.socket2,
      i.attrtype0,i.attrvalue0,i.attrtype1,i.attrvalue1,i.attrtype2,i.attrvalue2,i.attrtype3,i.attrvalue3,i.attrtype4,i.attrvalue4,i.attrtype5,i.attrvalue5,i.attrtype6,i.attrvalue6,
      p.applytype0,p.applyvalue0,p.applytype1,p.applyvalue1,p.applytype2,p.applyvalue2,p.size AS item_size,COALESCE(p.locale_name,CONCAT('VNUM ',i.vnum)) AS item_name
      FROM player.item i LEFT JOIN player.item_proto p ON p.vnum=i.vnum WHERE i.owner_id=%s AND i.window='SAFEBOX' ORDER BY i.pos LIMIT 180
    """, (character["account_id"] if "account_id" in character else one("SELECT account_id FROM player.player WHERE id=%s", (pid,)).get("account_id"),))
    equipment, inventory = {}, []
    # EWearPositions from Server/common/length.h. The database stores these
    # offsets directly in EQUIPMENT (rather than their client offset +90).
    equipment_slots = {
        0: "body", 1: "head", 2: "foots", 3: "wrist", 4: "weapon",
        5: "neck", 6: "ear", 7: "unique1", 8: "unique2", 9: "arrow",
        10: "shield", 23: "belt",
    }
    for item in [*items, *safebox]:
        item["item_name"] = game_text(item["item_name"])
        item["item_size"] = max(1, min(3, int(item.get("item_size") or 1)))
        item["base_stats"] = item_base_stats(item["vnum"])
        item["bonuses"] = [apply_text(item.get(f"applytype{i}"), item.get(f"applyvalue{i}")) for i in range(3) if item.get(f"applytype{i}") and item.get(f"applyvalue{i}")]
        item["bonuses"] += [apply_text(item.get(f"attrtype{i}"), item.get(f"attrvalue{i}")) for i in range(7) if item.get(f"attrtype{i}") and item.get(f"attrvalue{i}")]
        if item["window"] == "EQUIPMENT" and item["pos"] in equipment_slots:
            equipment[equipment_slots[item["pos"]]] = item
        elif item["window"] == "INVENTORY":
            inventory.append(item)
    socket_vnums = sorted({int(item.get(f"socket{i}") or 0) for item in [*items, *safebox] for i in range(3) if int(item.get(f"socket{i}") or 0) > 0})
    stone_defs = {}
    if socket_vnums:
        marks = ",".join(["%s"] * len(socket_vnums))
        for stone in rows("SELECT vnum,COALESCE(locale_name,CONCAT('VNUM ',vnum)) AS item_name,applytype0,applyvalue0,applytype1,applyvalue1,applytype2,applyvalue2 FROM player.item_proto WHERE vnum IN (" + marks + ")", socket_vnums):
            stone_defs[int(stone["vnum"])] = {"name": game_text(stone["item_name"]), "bonuses": [apply_text(stone.get(f"applytype{i}"), stone.get(f"applyvalue{i}")) for i in range(3) if stone.get(f"applytype{i}") and stone.get(f"applyvalue{i}")]}
    for item in [*items, *safebox]:
        item["stones"] = [stone_defs[vnum] for vnum in (int(item.get(f"socket{i}") or 0) for i in range(3)) if vnum in stone_defs]
    logs = rows("SELECT time,type,how,hint,what FROM log.log WHERE who=%s ORDER BY time DESC LIMIT 60", (pid,))
    for log in logs:
        for field in ("type", "how", "hint", "what"):
            log[field] = game_text(log.get(field))
    # Client uiinventory.py: page I begins at slot 0 and page II at slot 45.
    return render_template("player.html", character=character, equipment=equipment, inventory=inventory, safebox=safebox, has_inventory_page_two=any(int(item["pos"] or 0) >= 45 for item in inventory), has_safebox=bool(safebox), logs=logs)


@app.route("/economy")
@login_required
def economy():
    query = request.args.get("q", "").strip().lower()
    latest = one("SELECT MAX(captured_at) AS captured_at FROM player.web_seban_item_snapshot").get("captured_at")
    items = []
    if latest:
        items = rows("""
          SELECT s.vnum, s.amount, COALESCE(p.locale_name, CONCAT('VNUM ', s.vnum)) AS item_name
          FROM player.web_seban_item_snapshot s LEFT JOIN player.item_proto p ON p.vnum=s.vnum
          WHERE s.captured_at=%s ORDER BY s.amount DESC
        """, (latest,))
        for item in items:
            item["item_name"] = game_text(item["item_name"])
        if query:
            items = [item for item in items if query in item["item_name"].lower() or query == str(item["vnum"])]
    trend = rows("""
      SELECT DATE_FORMAT(captured_at, '%%m-%%d %%H:%%i') AS captured_at, value FROM player.web_seban_metric_snapshot
      WHERE metric='total_yang' AND captured_at >= NOW() - INTERVAL 7 DAY ORDER BY captured_at
    """)
    return render_template("economy.html", latest=latest, items=items[:500], query=query, trend=trend)


@app.route("/economy/item/<int:vnum>")
@login_required
def economy_item(vnum):
    item = one("SELECT vnum,COALESCE(locale_name,CONCAT('VNUM ',vnum)) AS item_name FROM player.item_proto WHERE vnum=%s", (vnum,)) or {"vnum": vnum, "item_name": f"VNUM {vnum}"}
    item["item_name"] = game_text(item["item_name"])
    history = rows("""SELECT DATE_FORMAT(captured_at, '%%m-%%d %%H:%%i') AS captured_at,amount
      FROM player.web_seban_item_snapshot WHERE vnum=%s AND captured_at >= NOW() - INTERVAL 14 DAY ORDER BY captured_at""", (vnum,))
    return render_template("economy_item.html", item=item, history=history)


@app.route("/items")
@login_required
def items_database():
    query = request.args.get("q", "").strip()
    item_type = request.args.get("type", "").strip()
    where, params = [], []
    if query:
        where.append("(p.vnum=%s OR p.locale_name LIKE %s OR p.name LIKE %s)")
        params += [int(query) if query.isdigit() else -1, f"%{query}%", f"%{query}%"]
    if item_type.isdigit():
        where.append("p.type=%s")
        params.append(int(item_type))
    predicate = " WHERE " + " AND ".join(where) if where else ""
    total = one("SELECT COUNT(*) AS count FROM player.item_proto p" + predicate, params).get("count", 0)
    records = rows("SELECT p.vnum,p.name,p.locale_name,p.type,p.subtype,p.size,p.gold,p.shop_buy_price FROM player.item_proto p" + predicate + " ORDER BY p.vnum", params)
    for item in records:
        item["name"] = game_text(item.get("locale_name") or item.get("name"))
    types = rows("SELECT type,COUNT(*) AS count,MIN(vnum) AS icon_vnum FROM player.item_proto GROUP BY type ORDER BY type")
    for category in types:
        index = int(category["type"])
        category["label"] = ITEM_TYPE_NAMES[index] if 0 <= index < len(ITEM_TYPE_NAMES) else f"ITEM_TYPE_{index}"
    return render_template("items.html", items=records, types=types, selected_type=item_type, query=query, total=total)


@app.route("/gm-commands")
@login_required
def gm_commands():
    return render_template("gm_commands.html", commands=GM_COMMANDS)


@app.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():
    authorities = ("PLAYER", "LOW_WIZARD", "GOD", "HIGH_WIZARD", "IMPLEMENTOR")
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()[:120]
        empire = max(1, min(3, int(request.form.get("empire", 1) or 1)))
        authority = request.form.get("authority", "PLAYER")
        gm_name = request.form.get("gm_name", "").strip()
        deletion_code = request.form.get("deletion_code", "").strip()
        try:
            gm_job = int(request.form.get("gm_job", 0) or 0)
        except ValueError:
            gm_job = -1
        gm_gender = request.form.get("gm_gender", "classic")
        # account.login is varchar(16) on mt2009 and varchar(30) on r40250; a
        # longer one is "Data too long" from the database, not a form error.
        login_max = 16 if ENGINE_MT2009 else 30
        if not (3 <= len(login) <= login_max and login.replace("_", "").isalnum() and len(password) >= 6 and authority in authorities):
            flash(f"Giriş adı 3–{login_max} karakter olmalı (harf, rakam, _), şifre ise en az 6 karakter.", "error")
        elif not (deletion_code.isdigit() and len(deletion_code) == 7):
            flash("Karakter silme kodu tam olarak 7 rakam olmalı.", "error")
        elif authority != "PLAYER" and not re.fullmatch(GM_NAME_PATTERN, gm_name):
            flash("GM karakter adı 2–24 karakter olmalı. Bir ön ek de kullanılabilir, örn. [GM]Seban veya [GA]Seban.", "error")
        elif authority != "PLAYER" and gm_job not in dict(GM_JOB_OPTIONS):
            flash("Geçerli bir GM karakter sınıfı seçin.", "error")
        elif authority != "PLAYER" and gm_gender not in dict(GM_GENDER_OPTIONS):
            flash("Geçerli bir GM karakter cinsiyeti seçin.", "error")
        else:
            account_id = None
            player_id = None
            try:
                with db() as con:
                    with con.cursor() as cur:
                        if authority != "PLAYER":
                            cur.execute("SELECT id FROM player.player WHERE name=%s LIMIT 1", (gm_name,))
                            if cur.fetchone():
                                raise ValueError("Bu karakter adı zaten mevcut.")
                        con.begin()
                        # The mt2009 account table has no empire column (the kingdom
                        # lives in player_index, written below for a GM character and
                        # by the game itself for a player's first character); naming
                        # it refused every account on the 2.x line ("Unknown column
                        # 'empire' in 'INSERT INTO'", NieBijOddam, 11 September).
                        if ENGINE_MT2009:
                            cur.execute("INSERT INTO account.account (login,password,social_id,email,status) VALUES (%s,PASSWORD(%s),%s,%s,'OK')", (login, password, deletion_code, email))
                        else:
                            cur.execute("INSERT INTO account.account (login,password,social_id,email,status,empire) VALUES (%s,PASSWORD(%s),%s,%s,'OK',%s)", (login, password, deletion_code, email, empire if authority != "PLAYER" else 0))
                        if authority != "PLAYER":
                            account_id = cur.lastrowid
                            x, y, map_index = GM_EMPIRE_STARTS[empire]
                            st, ht, dx, iq, hp, mp = GM_JOB_STARTS[gm_job]
                            character_race = GM_RACE_BY_CLASS_GENDER[(gm_job, gm_gender)]
                            cur.execute("""INSERT INTO player.player
                              (account_id,name,job,dir,x,y,map_index,exit_x,exit_y,exit_map_index,hp,mp,stamina,random_hp,random_sp,level,st,ht,dx,iq,stat_point,skill_point,sub_skill_point,part_main,part_base,part_hair,skill_group,horse_hp,horse_stamina,horse_level,horse_hp_droptime,horse_riding,horse_skill_point""" + ("" if ENGINE_MT2009 else ",bank_value") + """)
                              VALUES (%s,%s,%s,0,%s,%s,%s,%s,%s,%s,%s,%s,1000,0,0,1,%s,%s,%s,%s,0,0,0,0,0,0,0,0,0,0,0,0,0""" + ("" if ENGINE_MT2009 else ",0") + """)""",
                              (account_id, gm_name, character_race, x, y, map_index, x, y, map_index, hp, mp, st, ht, dx, iq))
                            player_id = cur.lastrowid
                            # Metin reads character slots from player_index.  A player row
                            # without this entry exists in SQL but is invisible at login.
                            cur.execute("""INSERT INTO player.player_index (id,pid1,pid2,pid3,pid4,empire)
                              VALUES (%s,%s,0,0,0,%s)
                              ON DUPLICATE KEY UPDATE pid1=VALUES(pid1),pid2=0,pid3=0,pid4=0,empire=VALUES(empire)""",
                              (account_id, player_id, empire))
                            cur.execute("INSERT INTO common.gmlist (mAccount,mName,mContactIP,mServerIP,mAuthority) VALUES (%s,%s,'','ALL',%s)", (login, gm_name, authority))
                        con.commit()
                if authority != "PLAYER":
                    flash(f"“{gm_name}” GM hesabı ve karakteri oluşturuldu. Karakter hemen kullanılabilir; GM yetkileri oyun servisleri yeniden başlatıldıktan sonra aktif olur.")
                else:
                    flash("Hesap oluşturuldu.")
                return redirect(url_for("accounts"))
            except (pymysql.MySQLError, ValueError) as exc:
                try: con.rollback()
                except Exception: pass
                # The original Metin tables use MyISAM, so a failed multi-table
                # creation is not rolled back by MariaDB.  Remove only records
                # made by this request so an empty account is never left behind.
                if account_id:
                    try:
                        with db() as cleanup_con:
                            with cleanup_con.cursor() as cleanup:
                                cleanup.execute("DELETE FROM common.gmlist WHERE mAccount=%s AND mName=%s", (login, gm_name))
                                if player_id:
                                    cleanup.execute("DELETE FROM player.player WHERE id=%s AND account_id=%s", (player_id, account_id))
                                cleanup.execute("DELETE FROM player.player_index WHERE id=%s", (account_id,))
                                cleanup.execute("DELETE FROM account.account WHERE id=%s AND login=%s", (account_id, login))
                    except pymysql.MySQLError:
                        pass
                flash(f"Hesap oluşturulamadı: {exc.args[1] if isinstance(exc, pymysql.MySQLError) and len(exc.args)>1 else exc}", "error")
    account_query = request.args.get("q", "").strip()[:60]
    display = request.args.get("display", "100")
    if display not in ("100", "1000", "all"):
        display = "100"
    where, params = [], []
    if account_query:
        where.append("(a.login LIKE %s OR EXISTS (SELECT 1 FROM player.player p WHERE p.account_id=a.id AND p.name LIKE %s))")
        params.extend([f"%{account_query}%", f"%{account_query}%"])
    query_sql = "SELECT a.id,a.login,a.email," + ("0 AS empire" if ENGINE_MT2009 else "a.empire") + ",a.create_time,a.last_play FROM account.account a"
    if where:
        query_sql += " WHERE " + " AND ".join(where)
    query_sql += " ORDER BY a.id DESC"
    if display != "all":
        query_sql += " LIMIT %s"
        params.append(int(display))
    recent = rows(query_sql, params)
    return render_template("accounts.html", accounts=recent, authorities=authorities, jobs=GM_JOB_OPTIONS, genders=GM_GENDER_OPTIONS, account_query=account_query, display=display)


@app.route("/maps")
@login_required
def maps():
    raw = rows("""
      SELECT DATE_FORMAT(captured_at, '%%m-%%d %%H:%%i') AS label, map_index, character_count
      FROM player.web_seban_map_snapshot
      WHERE captured_at >= NOW() - INTERVAL 24 HOUR ORDER BY captured_at ASC
    """)
    labels, series = [], {index: {} for index, _name in TRACKED_MAP_OPTIONS}
    for row in raw:
        index = int(row["map_index"] or 0)
        if index not in series:
            continue
        if row["label"] not in labels:
            labels.append(row["label"])
        series[index][row["label"]] = int(row["character_count"] or 0)
    chart = {"labels": labels, "series": [
        {"id": index, "name": name, "data": [values.get(label, 0) for label in labels]}
        for index, name in TRACKED_MAP_OPTIONS for values in (series[index],)
    ]}
    current = {int(row["map_index"]): row["character_count"] for row in live_map_counts()}
    latest = [{"map_index": index, "character_count": current.get(index, 0)} for index, _name in TRACKED_MAP_OPTIONS]
    return render_template("maps.html", chart=chart, latest=latest)


@app.route("/changelog")
@login_required
def changelog():
    return render_template("changelog.html", entries=changelog_entries(), panel_version=PANEL_VERSION)


@app.route("/api/live-bots")
@login_required
def api_live_bots():
    global_top = one("SELECT id FROM player.player WHERE " + BOT_IS_BARE + " ORDER BY level DESC,exp DESC LIMIT 1")
    return {"ok": True, "updated_at": int(datetime.now().timestamp() * 1000), "maps": MAP_NAMES, "bounds": MAP_BOUNDS, "global_top_id": global_top.get("id"), "bots": live_bots()}


@app.route("/api/news-feed")
@login_required
def api_news_feed():
    return {"ok": True, "events": news_feed_events()}


@app.route("/system")
@login_required
def system():
    samples = rows("""
      SELECT DATE_FORMAT(captured_at, '%%H:%%i') AS label, cpu_percent, ram_percent, ram_used_mb, ram_total_mb,
             disk_percent, disk_used_mb, disk_total_mb
      FROM player.web_seban_system_snapshot WHERE captured_at >= NOW() - INTERVAL 24 HOUR ORDER BY captured_at
    """)
    current = samples[-1] if samples else {}
    return render_template("system.html", samples=samples, current=current)


@app.route("/api/system-current")
@login_required
def api_system_current():
    return {"ok": True, "system": one("SELECT * FROM player.web_seban_system_snapshot ORDER BY captured_at DESC LIMIT 1")}


@app.route("/rankings")
@login_required
def rankings():
    kinds = {
        "level": "Seviye", "armor": "Zırh", "weapon": "Silah", "weapon30": "30 Lv Silah",
        # No "hunting": levelup.quest ships in quest/_unused on this engine
        # line, no kill hook fires, and the counter stayed zero for every
        # bot - the ranking was a hundred rows of "completed to Lv 0".
        "gold": "Yang", "items": "Eşyalar", "horse": "At", "biologist": "Biyolog",
        "shops": "Açık Tezgahlar", "skills": "Yetenekler", "plus9": "+9 Eşya", "playtime": "Oyun Süresi", "bosses": "Bosslar",
    }
    kind = request.args.get("type", "level")
    if kind not in kinds:
        kind = "level"
    weapon30_sort = request.args.get("sort", "avg") if kind == "weapon30" else "avg"
    if weapon30_sort not in ("avg", "skill", "upgrade"):
        weapon30_sort = "avg"
    ranking = bot_ranking(kind, weapon30_sort)
    ids = [row["id"] for row in ranking]
    if ids:
        # Which kingdom each of them belongs to. player_index.empire, because
        # that is the column the core reads when it decides where a bot lives;
        # the account's own copy was left at Chunjo for the whole cohort.
        marks = ",".join(["%s"] * len(ids))
        empire_rows = rows(
            "SELECT p.id, " + EMPIRE_EXPR + " AS empire"
            " FROM player.player p"
            " LEFT JOIN player.player_index pi ON pi.id=p.account_id"
            " LEFT JOIN account.account a ON a.id=p.account_id"
            " WHERE p.id IN (" + marks + ")", ids)
        empires = {row["id"]: row["empire"] for row in empire_rows}
        for row in ranking:
            row["empire"] = empires.get(row["id"], 0)
        progress_rows = rows("SELECT id,level,exp,job FROM player.player WHERE id IN (" + ",".join(["%s"] * len(ids)) + ")", ids)
        progress = {row["id"]: experience_progress(row["level"], row["exp"]) for row in progress_rows}
        jobs = {row["id"]: row["job"] for row in progress_rows}
        for row in ranking:
            row["job"] = jobs.get(row["id"], 0)
            row["experience"] = progress.get(row["id"], {"percent": 0})
    for row in ranking:
        if kind == "weapon30":
            row["detail"] = "Ortalama hasar: %s%% · Yetenek hasarı: %s%% · %s" % (
                int(row.get("avg_damage") or 0), int(row.get("skill_damage") or 0), game_text(row.get("item_name")))
        else:
            row["detail"] = game_text(row.get("detail"))
    return render_template("rankings.html", kinds=kinds, kind=kind, ranking=ranking, weapon30_sort=weapon30_sort)


@app.route("/season")
def season():
    """Weekly season from the three indexed event types only."""
    if time.time() - _season_cache["at"] < 600:
        return render_template("season.html", weekly=_season_cache["weekly"], records=_season_cache["records"])
    weekly = rows("""SELECT p.id,p.name,p.level,
        SUM(l.how='STONE_KILL') AS metins,
        SUM(l.how='BOSS_KILL') AS bosses,
        SUM(l.how='REFINE SUCCESS' AND (l.hint LIKE '%%+7' OR l.hint LIKE '%%+8' OR l.hint LIKE '%%+9')) AS refine7
        FROM log.log l JOIN player.player p ON p.id=l.who
        WHERE l.time>=NOW()-INTERVAL 7 DAY AND """ + BOT_IS + """
          AND l.how IN ('STONE_KILL','BOSS_KILL','REFINE SUCCESS')
        GROUP BY p.id ORDER BY (SUM(l.how='STONE_KILL')*150+SUM(l.how='BOSS_KILL')*500+SUM(l.how='REFINE SUCCESS' AND (l.hint LIKE '%%+7' OR l.hint LIKE '%%+8' OR l.hint LIKE '%%+9'))*200) DESC,p.level DESC LIMIT 30""")
    for row in weekly:
        row["points"] = int(row.get("metins") or 0)*150 + int(row.get("bosses") or 0)*500 + int(row.get("refine7") or 0)*200
    records = one("""SELECT
        SUM(l.how='STONE_KILL') AS metins,
        SUM(l.how='BOSS_KILL') AS bosses,
        SUM(l.how='REFINE SUCCESS' AND (l.hint LIKE '%%+7' OR l.hint LIKE '%%+8' OR l.hint LIKE '%%+9')) AS refine7,
        (SELECT MAX(level) FROM player.player) AS level
        FROM log.log l
        WHERE l.time>=NOW()-INTERVAL 7 DAY
          AND l.how IN ('STONE_KILL','BOSS_KILL','REFINE SUCCESS')""")
    _season_cache.update(at=time.time(), weekly=weekly, records=records)
    return render_template("season.html", weekly=weekly, records=records)


@app.route("/manage")
@login_required
def manage():
    map_counts = live_map_counts()
    current_settings = settings()
    updater = update_status()
    updater["protected"] = current_settings.get("auth_enabled") == "1" and bool(session.get("seban_admin"))
    return render_template("manage.html", rates=read_rates(), ai_weights=read_ai_weights(), ai_weight_keys=AI_WEIGHT_KEYS, restart=restart_progress(), settings=current_settings, map_counts=map_counts, bot_count=len(live_bots()), map_respawn_options=MAP_RESPAWN_OPTIONS, map_stone_respawn_ids=MAP_STONE_RESPAWN_IDS, map_respawn_status=read_map_regen_status(), server_settings=server_settings_status(), updater=updater, playerbots_release=playerbots_release_status(), update_csrf=update_csrf_token())


@app.post("/manage/update")
@login_required
def manage_update():
    current = settings()
    if current.get("auth_enabled") != "1" or not session.get("seban_admin"):
        flash("Panelden güncelleme yapabilmek için şifre korumasının açık olması gerekir.", "error")
        return redirect(url_for("manage"))
    supplied = request.form.get("update_csrf", "")
    expected = session.get("seban_update_csrf", "")
    if not expected or not hmac.compare_digest(supplied, expected):
        abort(403)
    try:
        queue_tieru_update()
    except (OSError, RuntimeError) as exc:
        flash(str(exc), "error")
    else:
        flash("Güncelleme talebi alındı. Sunucu izole updater tarafından yeniden derlenecek; ilerleme aşağıda görünür.")
    return redirect(url_for("manage"))


@app.post("/manage/settings")
@login_required
def manage_settings():
    values, error = validate_display_settings(request.form)
    if error:
        flash(error, "error")
        return redirect(url_for("manage"))
    current = settings()
    enable_auth = request.form.get("auth_enabled") == "1"
    password = request.form.get("panel_password", "")
    if enable_auth:
        if password and len(password) < 8:
            flash("Yeni şifre en az 8 karakter olmalı.", "error")
            return redirect(url_for("manage"))
        password_hash = generate_password_hash(password) if password else current.get("auth_password_hash", "")
        if not password_hash:
            flash("Korumayı etkinleştirmek için panel şifresi belirleyin.", "error")
            return redirect(url_for("manage"))
    else:
        password_hash = ""
        session.clear()
    values.update({"auth_enabled": "1" if enable_auth else "0", "auth_password_hash": password_hash, "setup_complete": "1"})
    write_settings(values)
    flash("Panel ayarları kaydedildi.")
    return redirect(url_for("manage"))


@app.post("/manage/restart-config")
@login_required
def manage_restart_config():
    action = request.form.get("submit_action", "apply")
    values, changes = {}, {}
    try:
        if action not in ("apply", "restart"):
            raise ValueError("Geçersiz işlem.")
        if action == "apply":
            values = {name: int(request.form.get(name, "")) for name in RATE_NAMES}
            if any(not 1 <= value <= 10000 for value in values.values()):
                raise ValueError("Çarpanlar 1–10.000% aralığında olmalı.")
            for index, name in MAP_RESPAWN_OPTIONS:
                for prefix in ("", "stone_"):
                    if prefix and index not in MAP_STONE_RESPAWN_IDS:
                        continue
                    key = f"{prefix}{index}"
                    # Older browser tabs do not contain the Metin fields.
                    if f"map_{key}" not in request.form:
                        continue
                    raw = request.form[f"map_{key}"].strip()
                    if not raw:
                        changes[key] = "reset"
                    else:
                        seconds = int(raw)
                        if not 1 <= seconds <= 3600:
                            raise ValueError(f"{name}: respawn 1–3600 saniye aralığında olmalı.")
                        changes[key] = seconds
        queue_server_settings(action, values, changes)
    except ValueError as exc:
        flash(str(exc) if "invalid literal" not in str(exc) else "Tam sayı değerleri girin.", "error")
    except RuntimeError as exc:
        flash(str(exc), "error")
    except FileExistsError:
        flash("Önceki talep hâlâ devam ediyor. Yeniden başlatmanın bitmesini bekleyin.", "error")
    except OSError:
        flash("Talep oyun kuyruğuna kaydedilemedi.", "error")
    else:
        flash("Küme kuyruğa kaydedildi: bir yeniden başlatma oranları ve respawn'ı uygulayacak." if action == "apply"
              else "Formdaki değişiklikler kaydedilmeden yeniden başlatma talep edildi.")
    return redirect(url_for("manage"))


@app.post("/manage/restart-clear-stale")
@login_required
def manage_restart_clear_stale():
    support = server_settings_status()
    if not support["can_clear"]:
        flash("Talep silinemiyor: yardımcı hâlâ işliyor olabilir ya da talep yeterince eski değil.", "error")
        return redirect(url_for("manage"))
    try:
        (RATES_SPOOL / "server-settings.request").unlink()
        (RATES_SPOOL / "server-settings.status").write_text(
            "state=failed\npercent=0\nmessage=Aktif oyun yardımcısı olmadan bekleyen talep silindi.\ntime=%s\n" % int(time.time()), encoding="utf-8")
    except OSError:
        flash("Bekleyen talep kuyruktan silinemedi.", "error")
    else:
        flash("Bekleyen talep silindi. Bir sonraki değişikliği talep etmeden önce oyun entegrasyonunu kurun.")
    return redirect(url_for("manage"))


@app.post("/manage/map-respawns")
@login_required
def manage_map_respawns():
    known_maps = {str(index) for index, _name in MAP_RESPAWN_OPTIONS}
    map_index = request.form.get("map_index", "")
    action = request.form.get("action", "")
    if map_index not in known_maps or action not in ("set", "reset"):
        flash("Geçersiz harita veya işlem.", "error")
        return redirect(url_for("manage"))
    seconds = None
    if action == "set":
        try:
            seconds = int(request.form.get("seconds", ""))
        except ValueError:
            seconds = 0
        if not 1 <= seconds <= 3600:
            flash("Respawn süresi 1–3600 saniye aralığında olmalı.", "error")
            return redirect(url_for("manage"))
    try:
        queue_map_regen_change(map_index, action, seconds)
    except OSError:
        flash("Harita değişikliği oyun kuyruğuna kaydedilemedi.", "error")
        return redirect(url_for("manage"))
    flash("Respawn değişikliği talep edildi. Oyun onu uygulayacak ve çekirdekleri yeniden başlatacak.")
    return redirect(url_for("manage"))


@app.post("/manage/behavior")
@login_required
def manage_behavior():
    # Keep live-only switches even if this request came from an older browser
    # tab that does not render them yet.
    values = read_ai_weights()
    for key, _, _ in AI_WEIGHT_KEYS:
        try:
            value = int(request.form.get(key, AI_WEIGHT_NEUTRAL))
        except (TypeError, ValueError):
            value = AI_WEIGHT_NEUTRAL
        values[key] = max(AI_WEIGHT_MIN, min(AI_WEIGHT_MAX, value))
    values["CHAT"] = 1 if "1" in request.form.getlist("CHAT") else 0
    # Preserve the existing switch for a form opened before this field existed.
    values["BOOKS"] = 1 if "BOOKS" not in request.form else (1 if "1" in request.form.getlist("BOOKS") else 0)
    try:
        values["SCRAP"] = max(0, min(100, int(request.form.get("SCRAP", values.get("SCRAP", 0)))))
    except (TypeError, ValueError):
        values["SCRAP"] = 0
    try:
        values["REST"] = max(0, min(100, int(request.form.get("REST", values.get("REST", 100)))))
    except (TypeError, ValueError):
        values["REST"] = 100
    for key in ("CHEST", "CHEST_STONE"):
        if key not in request.form:
            continue
        try:
            values[key] = max(0, min(1000, int(request.form[key])))
        except (TypeError, ValueError):
            # A malformed chest control must not turn an existing server value
            # into a guessed default.
            continue
    try:
        write_ai_weights(values)
    except OSError:
        flash("Playerbots ağırlıkları kaydedilemedi.", "error")
    else:
        flash("Bot davranışı kaydedildi — yeni plan 5 saniye içinde, yeniden başlatmadan devreye girer.")
    return redirect(url_for("manage"))


@app.post("/manage/restart")
@login_required
def manage_restart():
    if request.form.get("confirmation", "").strip().upper() != "RESTART":
        flash("Yeniden başlatmayı onaylamak için RESTART yazın.", "error")
        return redirect(url_for("manage"))
    queue_rate_restart(read_rates())
    flash("Yeniden başlatma talep edildi. İlerleme çubuğu sonraki aşamaları gösterecek.")
    return redirect(url_for("manage"))


@app.route("/api/manage-status")
@login_required
def api_manage_status():
    status = read_rate_status()
    updater = update_status()
    updater["protected"] = settings().get("auth_enabled") == "1" and bool(session.get("seban_admin"))
    return {"ok": True, "restart": restart_progress(), "server_settings": server_settings_status(), "updater": updater, "rates": read_rates(), "bots": len(live_bots()), "maps": live_map_counts()}


@app.route("/api/heat-events")
@login_required
def api_heat_events():
    event_type = request.args.get("type", "deaths").strip().lower()
    event_types = {"deaths": "DEAD_BY_NPC", "metins": "STONE_KILL", "bosses": "BOSS_KILL"}
    how = event_types.get(event_type)
    if not how:
        abort(400)
    raw = rows("""SELECT l.x,l.y,l.time,p.name FROM log.log l LEFT JOIN player.player p ON p.id=l.who
        WHERE l.type='CHARACTER' AND l.how=%s AND l.time >= NOW() - INTERVAL 24 HOUR ORDER BY l.time DESC LIMIT 4000""", (how,))
    events = []
    for event in raw:
        for index, bound in MAP_BOUNDS.items():
            if bound[0] <= event["x"] < bound[0] + bound[2] and bound[1] <= event["y"] < bound[1] + bound[3]:
                events.append({"map_index": index, "x": event["x"], "y": event["y"], "time": event["time"].isoformat(), "name": event.get("name")})
                break
    return {"ok": True, "type": event_type, "events": events, "bounds": MAP_BOUNDS}


from item_grants import install as install_item_grants
install_item_grants(app, db, login_required, game_text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7789)
