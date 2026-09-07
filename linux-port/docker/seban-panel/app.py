import json
import os
import socket
import time
import re
from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timedelta
from functools import wraps

import pymysql
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SEBAN_SESSION_SECRET", "change-this-before-public-use")


def playerbots_version():
    """The suite's VERSION, staged next to this file by the launcher and by
    prepare-context.sh the way the classic panel gets its copy; the
    environment overrides it, and neither means "unknown"."""
    env = os.environ.get("PLAYERBOTS_VERSION", "").strip()
    if env:
        return env
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION"), encoding="utf-8") as fh:
            value = fh.read().strip()
            return value or "unknown"
    except OSError:
        return "unknown"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

MAP_NAMES = {
    1: "Shinsoo M1", 3: "Shinsoo M2", 21: "Chunjo M1", 23: "Chunjo M2",
    24: "Chunjo M3", 25: "Łatwy Loch Małp", 41: "Jinno M1", 43: "Jinno M2",
    63: "Pustynia Yongbi", 64: "Dolina Orków",
}
MAP_BOUNDS = {
    21: (0, 102400, 102400, 128000), 23: (102400, 204800, 102400, 102400),
    24: (179200, 0, 51200, 51200), 25: (844800, 435200, 76800, 76800),
    63: (204800, 486400, 153600, 153600), 64: (256000, 665600, 153600, 153600),
}
STATUS_GLOBS = (os.environ.get("PLAYERBOTS_STATUS_GLOB", "/opt/metin2/var/channel1/*/playerbot_status.tsv"),)
RATES_SPOOL = Path("/opt/m2spool")
GAME_HOST = os.environ.get("PLAYERBOTS_GAME_HOST", "metin2-game")
GAME_LOGIN_PORT = int(os.environ.get("PLAYERBOTS_LOGIN_PORT", "11000"))
GAME_WORLD_PORT = int(os.environ.get("PLAYERBOTS_WORLD_PORT", "13000"))
RATE_NAMES = ("exp", "drop", "yang")
AI_WEIGHTS_FILE = RATES_SPOOL / "playerbot_weights.tsv"
AI_WEIGHT_KEYS = (
    ("RESTOCK", "Mikstury", "🧪"), ("REFINE", "Kowal", "🔨"),
    ("SKILL", "Księgi umiejętności", "📖"), ("HORSE", "Koń", "🐎"),
    ("BIOLOG", "Biolog", "🧬"), ("METIN", "Metiny", "🗿"),
    ("PARTY", "Grupy", "👥"), ("HUNTING", "Misje polowania", "🏹"),
    ("LEVEL", "Bicie potworów", "⚔️"), ("FISHING", "Wędkowanie", "🎣"),
    ("TRADE", "Stragany", "🏪"),
)
AI_WEIGHT_MIN, AI_WEIGHT_MAX, AI_WEIGHT_NEUTRAL = 25, 250, 100
# These two values share the live weight file with goal weights, but the game
# treats them as switches rather than 25–250% weights (Tieru 1.29.8/1.29.9).
AI_LIVE_DEFAULTS = {"CHAT": 1, "SCRAP": 0}
BIOLOGIST_COMPLETE_STATE = 557528158
BIOLOGIST_MISSIONS = ("make_herb_lv4", "make_herb_lv7", "make_herb_lv10", "make_herb_lv15", "make_herb_lv20", "make_herb_lv25")
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
BOT_PERSONALITIES = {0: "Wytrwały poszukiwacz", 1: "Pogromca Metinów", 2: "Towarzysz drużyny", 3: "Mistrz ekwipunku", 4: "Rozważny zbieracz", 5: "Wędrowiec"}
BOT_AMBITIONS = {0: "Poziom", 1: "Ekwipunek", 2: "Metiny", 3: "Koń", 4: "Biolog", 5: "Umiejętności"}
BOT_GOALS = {0: "Zdobywanie poziomu", 1: "Przetrwanie", 2: "Wybór profesji", 3: "Zdobycie ekwipunku", 4: "Uzupełnienie zapasów", 5: "Ulepszanie EQ", 6: "Rozwój umiejętności", 7: "Polowanie na Metiny", 8: "Silne cele w PT", 9: "Misja Biologa", 10: "Misja Polowania", 11: "Rozwój konia"}
BOT_ACTIONS = {0: "Planuje następny ruch", 1: "Podróżuje", 2: "Walczy", 3: "Podnosi łup", 4: "Regeneruje się", 5: "Wybiera profesję", 6: "Handluje", 7: "Ulepsza EQ", 8: "Czyta KU", 9: "Wkłada KD", 10: "Organizuje PT", 11: "Robi Biologa", 12: "Odwiedza Stajennego"}
ITEM_TYPE_NAMES = (
    "ITEM_NONE", "ITEM_WEAPON", "ITEM_ARMOR", "ITEM_USE", "ITEM_AUTOUSE", "ITEM_MATERIAL", "ITEM_SPECIAL", "ITEM_TOOL", "ITEM_LOTTERY", "ITEM_ELK",
    "ITEM_METIN", "ITEM_CONTAINER", "ITEM_FISH", "ITEM_ROD", "ITEM_RESOURCE", "ITEM_CAMPFIRE", "ITEM_UNIQUE", "ITEM_SKILLBOOK", "ITEM_QUEST", "ITEM_POLYMORPH",
    "ITEM_TREASURE_BOX", "ITEM_TREASURE_KEY", "ITEM_SKILLFORGET", "ITEM_GIFTBOX", "ITEM_PICK", "ITEM_HAIR", "ITEM_TOTEM", "ITEM_BLEND", "ITEM_COSTUME", "ITEM_DS",
    "ITEM_SPECIAL_DS", "ITEM_EXTRACT", "ITEM_SECONDARY_COIN", "ITEM_RING", "ITEM_BELT", "ITEM_PET", "ITEM_MEDIUM", "ITEM_GACHA", "ITEM_SOUL", "ITEM_PASSIVE",
)
APPLY_LABELS = {
    1: ("Maks. PŻ", ""), 2: ("Maks. PM", ""), 3: ("Witalność", ""), 4: ("Inteligencja", ""), 5: ("Siła", ""), 6: ("Zręczność", ""), 7: ("Szybkość ataku", "%"), 8: ("Szybkość ruchu", "%"), 9: ("Szybkość zaklęcia", "%"), 10: ("Regeneracja PŻ", "%"), 11: ("Regeneracja PM", "%"), 12: ("Odporność na truciznę", "%"), 13: ("Szansa na omdlenie", "%"), 14: ("Szansa na spowolnienie", "%"), 15: ("Szansa na cios krytyczny", "%"), 16: ("Szansa na przeszywający", "%"), 17: ("Wartość ataku", ""), 18: ("Silny przeciw ludziom", "%"), 19: ("Silny przeciw zwierzętom", "%"), 20: ("Silny przeciw orkom", "%"), 21: ("Silny przeciw mistykom", "%"), 22: ("Silny przeciw nieumarłym", "%"), 23: ("Silny przeciw diabłom", "%"), 24: ("Kradzież PŻ", "%"), 25: ("Kradzież PM", "%"), 26: ("Spalenie PM", "%"), 27: ("Odzyskanie PM po obrażeniach", "%"), 28: ("Szansa na blok", "%"), 29: ("Szansa na unik strzał", "%"), 30: ("Odporność na miecze", "%"), 31: ("Odporność na broń dwuręczną", "%"), 32: ("Odporność na sztylety", "%"), 33: ("Odporność na dzwony", "%"), 34: ("Odporność na wachlarze", "%"), 35: ("Odporność na strzały", "%"), 36: ("Odporność na ogień", "%"), 37: ("Odporność na błyskawice", "%"), 38: ("Odporność na magię", "%"), 39: ("Odporność na wiatr", "%"), 40: ("Odbicie obrażeń fizycznych", "%"), 41: ("Odbicie klątwy", "%"), 42: ("Skrócenie trucia", "%"), 43: ("Odzyskanie PM po zabiciu", "%"), 44: ("Bonus doświadczenia", "%"), 45: ("Bonus Yang", "%"), 46: ("Bonus dropu przedmiotów", "%"), 47: ("Bonus mikstur", "%"), 48: ("Odzyskanie PŻ po zabiciu", "%"), 49: ("Odporność na omdlenie", ""), 50: ("Odporność na spowolnienie", ""), 51: ("Odporność na przewrócenie", ""), 52: ("Bonus umiejętności", "%"), 53: ("Zasięg łuku", "%"), 54: ("Wartość ataku", ""), 55: ("Wartość obrony", ""), 56: ("Magiczna wartość ataku", ""), 57: ("Magiczna wartość obrony", ""), 58: ("Szansa na klątwę", "%"), 59: ("Maks. wytrzymałość", ""), 60: ("Silny przeciw wojownikom", "%"), 61: ("Silny przeciw ninja", "%"), 62: ("Silny przeciw surom", "%"), 63: ("Silny przeciw szamanom", "%"), 64: ("Silny przeciw potworom", "%"), 70: ("Maks. PŻ", "%"), 71: ("Średnie obrażenia", "%"), 72: ("Obrażenia umiejętności", "%"), 73: ("Odporność na umiejętności", "%"), 74: ("Odporność na średnie obrażenia", "%"), 75: ("Bonus doświadczenia", "%"), 76: ("Bonus dropu", "%"), 77: ("Kradzież PŻ", "%"), 78: ("Odporność na wojowników", "%"), 79: ("Odporność na ninja", "%"), 80: ("Odporność na sury", "%"), 81: ("Odporność na szamanów", "%"), 82: ("Energia", "%"), 83: ("Wartość obrony", ""), 84: ("Bonus atrybutów kostiumu", "%"), 85: ("Magiczny atak", "%"), 86: ("Atak fizyczny i magiczny", "%"), 87: ("Odporność na lód", "%"), 88: ("Odporność na ziemię", "%"), 89: ("Odporność na mrok", "%"), 90: ("Odporność na cios krytyczny", "%"), 91: ("Odporność na przeszywający", "%")}
# W tej kompilacji serwera Playerbots pola 71/72 są odwrotne względem
# standardowego enumu klienta.  Ten override dotyczy tooltipów przedmiotów.
APPLY_LABELS.update({71: ("Obrażenia umiejętności", "%"), 72: ("Średnie obrażenia", "%")})
JOB_NAMES = ("Wojownik", "Ninja", "Sura", "Szaman")
SKILLS = {
    (0, 1): ((1, "Aura Miecza"), (2, "Berserk"), (3, "Wir Miecza"), (4, "Szybki Atak"), (5, "Trzystronne Cięcie"), (6, "Szarża")),
    (0, 2): ((16, "Duchowe Uderzenie"), (17, "Tapnięcie"), (18, "Uderzenie Miecza"), (19, "Silne Ciało"), (20, "Walnięcie"), (21, "Uderzenie Ducha")),
    (1, 1): ((31, "Zasadzka"), (32, "Szybki Atak"), (33, "Wirujący Sztylet"), (34, "Ukrycie"), (35, "Trująca Chmura")),
    (1, 2): ((46, "Powtarzalny Strzał"), (47, "Deszcz Strzał"), (48, "Ognista Strzała"), (49, "Bezszeletny Krok"), (50, "Trująca Strzała")),
    (2, 1): ((61, "Uderzenie Palcem"), (62, "Wirujący Miecz"), (63, "Zaklęte Ostrze"), (64, "Strach"), (65, "Zaklęta Zbroja"), (66, "Rozproszenie Magii")),
    (2, 2): ((76, "Mroczne Uderzenie"), (77, "Mroczna Sfera"), (78, "Mroczny Duch"), (79, "Mroczna Ochrona"), (80, "Płomienne Uderzenie"), (81, "Mroczny Kamień")),
    (3, 1): ((91, "Latający Talizman"), (92, "Smoczy Skowyt"), (93, "Smocza Pomoc"), (94, "Błogosławieństwo"), (95, "Odbicie"), (96, "Pomoc Smoka")),
    (3, 2): ((106, "Rzut Błyskawicą"), (107, "Przywołanie Błyskawicy"), (108, "Szpon Błyskawicy"), (109, "Leczenie"), (110, "Szybkość"), (111, "Atak+")),
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
    GM_COMMANDS = "Brak pliku z komendami."


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


def map_name(index):
    """Name only maps which this Playerbots world actually runs."""
    index = int(index or 0)
    return MAP_NAMES.get(index, f"Poza aktywnym światem (mapa #{index})")


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
        return None, "Nazwa panelu nie może być pusta."
    if theme not in ("ocean", "ember", "forest") or monitor_mode not in ("vps", "docker"):
        return None, "Nieprawidłowe ustawienia wyglądu lub monitoringu."
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
        (12000, "Rycerski", "knightly"), (8000, "Szlachetny", "noble"),
        (4000, "Dobry", "good"), (1000, "Przyjazny", "friendly"),
        (0, "Neutralny", "neutral"), (-3999, "Agresywny", "aggressive"),
        (-7999, "Nieuczciwy", "dishonest"), (-11999, "Złośliwy", "malicious"),
        (-20000, "Okrutny", "cruel"),
    )
    for threshold, title, css in bands:
        if points >= threshold:
            return {"points": points, "title": title, "css": css}
    return {"points": points, "title": "Okrutny", "css": "cruel"}


def live_label(field, value):
    labels = {"personality": BOT_PERSONALITIES, "ambition": BOT_AMBITIONS, "goal": BOT_GOALS, "action": BOT_ACTIONS}.get(field, {})
    value = int(value or 0)
    return labels.get(value, f"#{value}")


def is_stationary_activity(status):
    text = str(status or "").casefold()
    return any(marker in text for marker in ("łowi", "lowi", "ryb", "fishing", "czekam na branie"))


def apply_text(apply_type, value):
    name, suffix = APPLY_LABELS.get(int(apply_type or 0), (f"Bonus #{apply_type}", ""))
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
        stats.append(f"Wymagany poziom: {level}")
    value = lambda index: int(proto.get(f"value{index}") or 0)
    if item_type == 1:  # ITEM_WEAPON: magic 1/2, physical 3/4.
        attack_min, attack_max = value(3), value(4)
        magic_min, magic_max = value(1), value(2)
        if attack_min or attack_max:
            stats.append(f"Wartość ataku: {attack_min}–{attack_max}" if attack_min != attack_max else f"Wartość ataku: {attack_max}")
        if magic_min or magic_max:
            stats.append(f"Wartość magicznego ataku: {magic_min}–{magic_max}" if magic_min != magic_max else f"Wartość magicznego ataku: {magic_max}")
    elif item_type == 2:  # ITEM_ARMOR, including body armour and shields.
        defense = value(1)
        if defense:
            stats.append(f"Wartość obrony: {defense}")
    return stats


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
            result.append({"vnum": vnum, "name": name, "level": level, "master_type": master, "rank": rank, "icon_suffix": "_p" if rank == "P" else "_m" if rank.startswith("M") else ""})
    return result


SKILL_NAMES = {vnum: name for skill_set in SKILLS.values() for vnum, name in skill_set}


def news_feed_events():
    """Curate rare achievements from the native game log with stable IDs."""
    raw = rows("""SELECT l.time,l.how,l.hint,l.what,l.who,p.name
      FROM log.log l JOIN player.player p ON p.id=l.who
      WHERE l.time >= NOW() - INTERVAL 12 HOUR
        AND l.how IN ('REFINE SUCCESS','SKILLUP','GET')
      ORDER BY l.time DESC LIMIT 900""")
    events, seen = [], set()
    for row in raw:
        how, hint, name = str(row.get("how") or ""), game_text(row.get("hint")), game_text(row.get("name"))
        key = f"{how}:{row.get('who')}:{row.get('what')}:{row.get('time')}"
        if key in seen or not name:
            continue
        message = None
        if how == "REFINE SUCCESS":
            match = re.search(r"\+([789])(?:\s|$)", hint)
            if match:
                message = f"{name} ulepszył {hint.strip()}"
        elif how == "SKILLUP":
            match = re.search(r"SkillUp:\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)", hint)
            if match:
                vnum, master, level = map(int, match.groups())
                rank = skill_rank(master, level)
                if (rank.startswith("M") and rank != "M1") or rank.startswith("G") or rank == "P":
                    message = f"{name} rozwinął {SKILL_NAMES.get(vnum, f'umiejętność #{vnum}')} na {rank}"
        elif how == "GET" and "małż" in hint.casefold():
            message = f"{name} znalazł Małż podczas połowu"
        if message:
            seen.add(key)
            events.append({"key": key, "time": row["time"].strftime("%H:%M") if hasattr(row.get("time"), "strftime") else str(row.get("time"))[11:16], "message": message})
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
            stuck = bool(old and old["map_index"] == state["map_index"] and (old["x"] - state["x"]) ** 2 + (old["y"] - state["y"]) ** 2 < 40000 and not is_stationary_activity(state.get("status")))
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
                    if key == "CHAT":
                        values[key] = 0 if raw_value.lower() in ("0", "off", "no") else 1
                    elif key == "SCRAP":
                        values[key] = max(0, min(100, int(raw_value)))
                    else:
                        values[key] = max(AI_WEIGHT_MIN, min(AI_WEIGHT_MAX, int(raw_value)))
                except ValueError:
                    pass
    except OSError:
        pass
    return values


def write_ai_weights(values):
    """Atomically replace the file so the core never catches a partial save."""
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    content = [
        "# Metin2 Playerbots — wagi celów ustawione przez Seban Panel.",
        "# 25 = rzadko · 100 = domyślnie · 250 = często.",
        "# Rdzeń odczytuje plik co pięć sekund; restart nie jest wymagany.", "",
    ]
    content.extend(f"{key}\t{values[key]}" for key, _, _ in AI_WEIGHT_KEYS)
    content.append(f"CHAT\t{1 if values.get('CHAT', 1) else 0}")
    content.append(f"SCRAP\t{max(0, min(100, int(values.get('SCRAP', 0))))}")
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
    status = read_rate_status()
    auth, world = port_open(GAME_LOGIN_PORT), port_open(GAME_WORLD_PORT)
    state = status.get("state", "unknown")
    if state == "running":
        if not auth:
            return {"percent": 25, "stage": "Zatrzymywanie procesów gry", "state": state}
        if not world:
            return {"percent": 65, "stage": "Serwer logowania działa — uruchamianie świata", "state": state}
        return {"percent": 85, "stage": "Sprawdzanie kanału i usług", "state": state}
    if state == "ok" and auth and world:
        return {"percent": 100, "stage": "Serwer działa", "state": state}
    if state == "failed":
        return {"percent": 100, "stage": status.get("message", "Restart nie powiódł się"), "state": state}
    return {"percent": 100 if auth and world else 40, "stage": "Serwer działa" if auth and world else "Oczekiwanie na usługi", "state": state}


def queue_rate_restart(values):
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


def bot_ranking(kind, sort_by="avg"):
    base = "p.name LIKE 'bot%%'"
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
            "avg": "skill_damage DESC, avg_damage DESC, p.level DESC",
            "skill": "avg_damage DESC, skill_damage DESC, p.level DESC",
            "upgrade": "MOD(i.vnum,10) DESC, skill_damage DESC, avg_damage DESC, p.level DESC",
        }.get(sort_by, "skill_damage DESC, avg_damage DESC, p.level DESC")
        result = rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)) AS item_name,
            IF(GREATEST(CASE WHEN i.attrtype0=71 THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1=71 THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2=71 THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3=71 THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4=71 THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5=71 THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6=71 THEN i.attrvalue6 ELSE -999 END)=-999,0,GREATEST(CASE WHEN i.attrtype0=71 THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1=71 THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2=71 THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3=71 THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4=71 THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5=71 THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6=71 THEN i.attrvalue6 ELSE -999 END)) AS avg_damage,
            IF(GREATEST(CASE WHEN i.attrtype0=72 THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1=72 THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2=72 THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3=72 THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4=72 THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5=72 THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6=72 THEN i.attrvalue6 ELSE -999 END)=-999,0,GREATEST(CASE WHEN i.attrtype0=72 THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1=72 THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2=72 THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3=72 THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4=72 THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5=72 THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6=72 THEN i.attrvalue6 ELSE -999 END)) AS skill_damage
            FROM player.item i JOIN player.player p ON p.id=i.owner_id LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum
            WHERE {base} AND ((i.vnum BETWEEN 290 AND 299) OR (i.vnum BETWEEN 1170 AND 1179) OR (i.vnum BETWEEN 2150 AND 2159) OR (i.vnum BETWEEN 3210 AND 3219) OR (i.vnum BETWEEN 5110 AND 5119) OR (i.vnum BETWEEN 7160 AND 7169))
            ORDER BY {weapon30_order} LIMIT 100""")
        # The database's custom Playerbots build stores type 71 as skill
        # damage and type 72 as average damage.  The query above remains
        # legible; normalize the public field names here before sorting/UI.
        for row in result:
            row["avg_damage"], row["skill_damage"] = row["skill_damage"], row["avg_damage"]
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
    if kind == "items":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(i.id) AS score,CONCAT(COUNT(i.id),' przedmiotów') AS detail
            FROM player.player p LEFT JOIN player.item i ON i.owner_id=p.id AND i.window='INVENTORY'
            WHERE {base} GROUP BY p.id ORDER BY score DESC,p.level DESC LIMIT 100""")
    if kind == "horse":
        return rows(f"SELECT p.id,p.name,p.level,p.gold,p.horse_level AS score,CONCAT('Koń Lv ',p.horse_level) AS detail FROM player.player p WHERE {base} ORDER BY p.horse_level DESC,p.level DESC LIMIT 100")
    if kind == "biologist":
        marks = ",".join(["%s"] * len(BIOLOGIST_MISSIONS))
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(DISTINCT q.szName) AS score,CONCAT(COUNT(DISTINCT q.szName),' / {len(BIOLOGIST_MISSIONS)} misji') AS detail
            FROM player.player p LEFT JOIN player.quest q ON q.dwPID=p.id AND q.szName IN ({marks}) AND q.szState='__status' AND q.lValue=%s
            WHERE {base} GROUP BY p.id ORDER BY score DESC,p.level DESC LIMIT 100""", (*BIOLOGIST_MISSIONS, BIOLOGIST_COMPLETE_STATE))
    if kind == "hunting":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,MAX(CASE WHEN q.szState='complete' THEN q.lValue ELSE 0 END) AS score,
            CONCAT('Ukończone do Lv ',MAX(CASE WHEN q.szState='complete' THEN q.lValue ELSE 0 END)) AS detail
            FROM player.player p LEFT JOIN player.quest q ON q.dwPID=p.id AND q.szName='levelup'
            WHERE {base} GROUP BY p.id ORDER BY score DESC,p.level DESC LIMIT 100""")
    if kind == "shops":
        keeper_ids = [pid for pid, state in live_statuses().items() if int(state.get("action") or 0) == 13]
        if not keeper_ids:
            return []
        placeholders = ",".join(["%s"] * len(keeper_ids))
        return rows(f"SELECT p.id,p.name,p.level,p.gold,'Stragan otwarty' AS detail FROM player.player p WHERE p.id IN ({placeholders}) ORDER BY p.level DESC LIMIT 100", keeper_ids)
    if kind == "skills":
        roster = rows(f"SELECT p.id,p.name,p.level,p.gold,p.job,p.skill_group,p.skill_level FROM player.player p WHERE {base} AND p.skill_group>0 ORDER BY p.level DESC LIMIT 400")
        for bot in roster:
            best = max(parse_skills(bot.get("skill_level"), bot.get("job"), bot.get("skill_group")), key=lambda skill: (3 if skill["rank"] == "P" else 2 if skill["rank"].startswith("G") else 1 if skill["rank"].startswith("M") else 0, skill["level"]), default=None)
            bot["score"] = (3 if best and best["rank"] == "P" else 2 if best and best["rank"].startswith("G") else 1 if best and best["rank"].startswith("M") else 0, best["level"] if best else 0)
            bot["detail"] = f"{best['name']} · {best['rank']}" if best else "Brak rozwiniętych umiejętności"
        return sorted(roster, key=lambda bot: (bot["score"], bot["level"]), reverse=True)[:100]
    if kind == "plus9":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)) AS detail
            FROM player.item i JOIN player.player p ON p.id=i.owner_id LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum
            WHERE {base} AND i.vnum<12000 AND MOD(i.vnum,10)=9 ORDER BY i.vnum DESC,p.level DESC LIMIT 100""")
    return rows(f"SELECT p.id,p.name,p.level,p.gold,p.level AS score,'Poziom' AS detail FROM player.player p WHERE {base} ORDER BY p.level DESC,p.exp DESC LIMIT 100")


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
    return {"tieru_url": tieru_url, "panel_brand": current_settings.get("panel_name", "Metin2 Singleplayer"), "settings": current_settings, "map_name": map_name, "item_icon": item_icon}


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
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Nieprawidłowe hasło.", "error")
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
            error = "Hasło panelu musi mieć co najmniej 8 znaków."
        if error:
            flash(error, "error")
        else:
            values.update({"setup_complete": "1", "auth_enabled": "1" if enable_auth else "0", "auth_password_hash": generate_password_hash(password) if enable_auth else ""})
            write_settings(values)
            if enable_auth:
                session["seban_admin"] = True
            flash("Konfiguracja została zapisana.")
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
    top = rows("SELECT id, name, level, exp, map_index, playtime FROM player.player WHERE name LIKE 'bot%%' ORDER BY level DESC, exp DESC LIMIT 10")
    global_top_id = top[0]["id"] if top else None
    live = live_statuses()
    live_roster = live_bots()
    try:
        bot_guilds = one("""SELECT COUNT(*) AS count FROM player.guild g
                           JOIN player.player p ON p.id=g.master WHERE p.name LIKE 'bot%%'""").get("count", 0)
    except pymysql.MySQLError:
        bot_guilds = 0
    restart_status = read_rate_status()
    restart_time = restart_status.get("time")
    try:
        restart_label = datetime.fromtimestamp(int(restart_time)).strftime("%d.%m.%Y, %H:%M:%S")
    except (TypeError, ValueError, OSError):
        restart_label = "Brak danych"
    world_summary = {
        "bots": len(live_roster),
        "average_level": round(sum(int(bot.get("level") or 0) for bot in live_roster) / len(live_roster), 1) if live_roster else 0,
        "party_bots": sum(1 for bot in live_roster if bot.get("in_party")),
        "max_level": max((int(bot.get("level") or 0) for bot in live_roster), default=0),
        "horse_average": round(sum(int(bot.get("horse_level") or 0) for bot in live_roster) / len(live_roster), 1) if live_roster else 0,
        "horse_max": max((int(bot.get("horse_level") or 0) for bot in live_roster), default=0),
        "guilds": bot_guilds,
        "last_restart": restart_label,
        "version": playerbots_version(),
        "rates": read_rates(),
    }
    for bot in top:
        if bot["id"] in live:
            bot["map_index"] = live[bot["id"]]["map_index"]
    quick_rankings = []
    quick_rankings.append({"title": "Poziom", "subtitle": "najwyższe poziomy", "items": [{"id": row["id"], "name": row["name"], "value": f"Lv {row['level']}"} for row in top]})
    playtime = bot_ranking("playtime")[:10]
    quick_rankings.append({"title": "Czas gry", "subtitle": "najdłużej online", "items": [{"id": row["id"], "name": row["name"], "value": row["detail"]} for row in playtime]})
    gold = bot_ranking("gold")[:10]
    quick_rankings.append({"title": "Yang", "subtitle": "najwięcej przy postaci", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row.get('gold') or 0):,}".replace(",", " ")} for row in gold]})
    weapon30 = bot_ranking("weapon30")[:10]
    quick_rankings.append({"title": "Broń 30 Lv", "subtitle": "średnie / umiejętności", "items": [{"id": row["id"], "name": row["name"], "value": f"Śr. {int(row.get('avg_damage') or 0)}% · Um. {int(row.get('skill_damage') or 0)}%"} for row in weapon30]})
    metins = rows("""SELECT p.id,p.name,COUNT(*) AS score FROM log.log l JOIN player.player p ON p.id=l.who
                     WHERE p.name LIKE 'bot%%' AND l.how='STONE_KILL' AND l.time >= NOW() - INTERVAL 7 DAY
                     GROUP BY p.id,p.name ORDER BY score DESC,p.name LIMIT 10""")
    quick_rankings.append({"title": "Metiny", "subtitle": "rozbite · ostatnie 7 dni", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} szt."} for row in metins]})
    fish = rows("""SELECT p.id,p.name,COUNT(*) AS score FROM log.log l JOIN player.player p ON p.id=l.who
                   WHERE p.name LIKE 'bot%%' AND l.time >= NOW() - INTERVAL 7 DAY
                     AND (l.what LIKE '%%ryb%%' OR l.what LIKE '%%fish%%')
                   GROUP BY p.id,p.name ORDER BY score DESC,p.name LIMIT 10""")
    quick_rankings.append({"title": "Ryby", "subtitle": "wyłowione · ostatnie 7 dni", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} szt."} for row in fish]})
    return render_template("dashboard.html", totals=totals, bots=bots.get("count", 0), system=system, map_rows=map_rows, top=top, global_top_id=global_top_id, quick_rankings=quick_rankings, world_summary=world_summary)


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


@app.route("/player/<int:pid>")
@login_required
def player(pid):
    character = one("SELECT id,account_id,name,level,job,exp,gold,hp,mp,x,y,horse_level,alignment,st,ht,dx,iq,stat_point,skill_point,skill_group,skill_level,map_index,playtime FROM player.player WHERE id=%s", (pid,))
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
        character.update({"personality": "Bot offline", "ambition": "—", "goal": "—", "action": "—"})
    character["job_name"] = JOB_NAMES[int(character.get("job") or 0) % 4]
    character["experience"] = experience_progress(character.get("level"), character.get("exp"))
    character["honor"] = honor_rank(character.get("alignment"))
    character["honor"]["css"] = {"Rycerski": "knightly", "Szlachetny": "noble", "Dobry": "good", "Przyjazny": "friendly", "Neutralny": "neutral", "Agresywny": "aggressive", "Nieuczciwy": "dishonest", "Złośliwy": "malicious", "Okrutny": "cruel"}[character["honor"]["title"]]
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
    types = rows("SELECT type,COUNT(*) AS count FROM player.item_proto GROUP BY type ORDER BY type")
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
        if not (3 <= len(login) <= 30 and login.replace("_", "").isalnum() and len(password) >= 6 and authority in authorities):
            flash("Login ma mieć 3–30 znaków (litery, cyfry, _), a hasło minimum 6 znaków.", "error")
        elif not (deletion_code.isdigit() and len(deletion_code) == 7):
            flash("Kod usunięcia postaci ma zawierać dokładnie 7 cyfr.", "error")
        elif authority != "PLAYER" and not gm_name:
            flash("Dla konta GM wpisz docelowy nick postaci.", "error")
        else:
            try:
                with db() as con:
                    with con.cursor() as cur:
                        cur.execute("INSERT INTO account.account (login,password,social_id,email,status,empire) VALUES (%s,PASSWORD(%s),%s,%s,'OK',%s)", (login, password, deletion_code, email, empire if authority != "PLAYER" else 0))
                        if authority != "PLAYER":
                            cur.execute("INSERT INTO common.gmlist (mAccount,mName,mContactIP,mServerIP,mAuthority) VALUES (%s,%s,'','ALL',%s)", (login, gm_name, authority))
                flash("Konto utworzone. Uprawnienia GM staną się aktywne po restarcie usług gry.")
                return redirect(url_for("accounts"))
            except pymysql.MySQLError as exc:
                flash(f"Nie utworzono konta: {exc.args[1] if len(exc.args)>1 else exc}", "error")
    account_query = request.args.get("q", "").strip()[:60]
    display = request.args.get("display", "100")
    if display not in ("100", "1000", "all"):
        display = "100"
    where, params = [], []
    if account_query:
        where.append("(a.login LIKE %s OR EXISTS (SELECT 1 FROM player.player p WHERE p.account_id=a.id AND p.name LIKE %s))")
        params.extend([f"%{account_query}%", f"%{account_query}%"])
    query_sql = "SELECT a.id,a.login,a.email,a.empire,a.create_time,a.last_play FROM account.account a"
    if where:
        query_sql += " WHERE " + " AND ".join(where)
    query_sql += " ORDER BY a.id DESC"
    if display != "all":
        query_sql += " LIMIT %s"
        params.append(int(display))
    recent = rows(query_sql, params)
    return render_template("accounts.html", accounts=recent, authorities=authorities, account_query=account_query, display=display)


@app.route("/maps")
@login_required
def maps():
    raw = rows("""
      SELECT DATE_FORMAT(captured_at, '%%m-%%d %%H:%%i') AS label, map_index, character_count
      FROM player.web_seban_map_snapshot
      WHERE captured_at >= NOW() - INTERVAL 24 HOUR ORDER BY captured_at ASC
    """)
    labels, series = [], {}
    for row in raw:
        if row["label"] not in labels:
            labels.append(row["label"])
        series.setdefault(map_name := MAP_NAMES.get(int(row["map_index"] or 0), f"Mapa #{row['map_index']}"), {})[row["label"]] = row["character_count"]
    chart = {"labels": labels, "series": [{"name": key, "data": [values.get(label, 0) for label in labels]} for key, values in sorted(series.items())]}
    latest = live_map_counts()
    return render_template("maps.html", chart=chart, latest=latest)


@app.route("/api/live-bots")
@login_required
def api_live_bots():
    global_top = one("SELECT id FROM player.player WHERE name LIKE 'bot%%' ORDER BY level DESC,exp DESC LIMIT 1")
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
        "level": "Poziom", "armor": "Zbroja", "weapon": "Broń", "weapon30": "Broń 30 Lv",
        "gold": "Yang", "items": "Przedmioty", "horse": "Koń", "hunting": "Polowanie", "biologist": "Biolog",
        "shops": "Otwarte stragany", "skills": "Umiejętności", "plus9": "Przedmiot +9", "playtime": "Czas gry",
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
        progress_rows = rows("SELECT id,level,exp FROM player.player WHERE id IN (" + ",".join(["%s"] * len(ids)) + ")", ids)
        progress = {row["id"]: experience_progress(row["level"], row["exp"]) for row in progress_rows}
        for row in ranking:
            row["experience"] = progress.get(row["id"], {"percent": 0})
    for row in ranking:
        if kind == "weapon30":
            row["detail"] = "Średnie obrażenia: %s%% · Obrażenia umiejętności: %s%% · %s" % (
                int(row.get("avg_damage") or 0), int(row.get("skill_damage") or 0), game_text(row.get("item_name")))
        else:
            row["detail"] = game_text(row.get("detail"))
    return render_template("rankings.html", kinds=kinds, kind=kind, ranking=ranking, weapon30_sort=weapon30_sort)


@app.route("/season")
def season():
    """Public weekly season, calculated from existing server logs."""
    weekly = rows("""SELECT p.id,p.name,p.level,
        SUM(l.how='STONE_KILL') AS metins,
        SUM(l.how LIKE '%%BOSS%%') AS bosses,
        SUM(l.how='REFINE_SUCCESS' AND CAST(l.hint AS UNSIGNED)>=7) AS refine7
        FROM log.log l JOIN player.player p ON p.id=l.who
        WHERE l.time>=NOW()-INTERVAL 7 DAY AND p.name LIKE 'bot%%'
        GROUP BY p.id ORDER BY (SUM(l.how='STONE_KILL')*150+SUM(l.how LIKE '%%BOSS%%')*500+SUM(l.how='REFINE_SUCCESS' AND CAST(l.hint AS UNSIGNED)>=7)*200) DESC,p.level DESC LIMIT 30""")
    for row in weekly:
        row["points"] = int(row.get("metins") or 0)*150 + int(row.get("bosses") or 0)*500 + int(row.get("refine7") or 0)*200
    records = one("""SELECT
        (SELECT COUNT(*) FROM log.log WHERE how='STONE_KILL') AS metins,
        (SELECT COUNT(*) FROM log.log WHERE how LIKE '%%BOSS%%') AS bosses,
        (SELECT COUNT(*) FROM log.log WHERE how='REFINE_SUCCESS' AND CAST(hint AS UNSIGNED)>=7) AS refine7,
        (SELECT MAX(level) FROM player.player) AS level
    """)
    return render_template("season.html", weekly=weekly, records=records)


@app.route("/manage")
@login_required
def manage():
    map_counts = live_map_counts()
    return render_template("manage.html", rates=read_rates(), ai_weights=read_ai_weights(), ai_weight_keys=AI_WEIGHT_KEYS, restart=restart_progress(), settings=settings(), map_counts=map_counts, bot_count=len(live_bots()))


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
            flash("Nowe hasło musi mieć co najmniej 8 znaków.", "error")
            return redirect(url_for("manage"))
        password_hash = generate_password_hash(password) if password else current.get("auth_password_hash", "")
        if not password_hash:
            flash("Aby włączyć ochronę, ustaw hasło panelu.", "error")
            return redirect(url_for("manage"))
    else:
        password_hash = ""
        session.clear()
    values.update({"auth_enabled": "1" if enable_auth else "0", "auth_password_hash": password_hash, "setup_complete": "1"})
    write_settings(values)
    flash("Ustawienia panelu zapisane.")
    return redirect(url_for("manage"))


@app.post("/manage/rates")
@login_required
def manage_rates():
    try:
        values = {name: int(request.form.get(name, "")) for name in RATE_NAMES}
    except ValueError:
        flash("Wpisz całkowite wartości procentowe.", "error")
        return redirect(url_for("manage"))
    if any(value < 1 or value > 10000 for value in values.values()):
        flash("Każdy mnożnik musi mieścić się od 1% do 10 000%.", "error")
        return redirect(url_for("manage"))
    with db() as con:
        with con.cursor() as cur:
            for name, value in values.items():
                cur.execute("INSERT INTO player.web_admin_rates (name,value) VALUES (%s,%s) ON DUPLICATE KEY UPDATE value=VALUES(value)", (name, value))
    queue_rate_restart(values)
    flash("Mnożniki zapisane. Serwer otrzymał polecenie bezpiecznego restartu.")
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
    try:
        values["SCRAP"] = max(0, min(100, int(request.form.get("SCRAP", values.get("SCRAP", 0)))))
    except (TypeError, ValueError):
        values["SCRAP"] = 0
    try:
        write_ai_weights(values)
    except OSError:
        flash("Nie udało się zapisać wag Playerbots.", "error")
    else:
        flash("Zachowanie botów zapisane — nowy plan działania wejdzie w życie do 5 sekund, bez restartu.")
    return redirect(url_for("manage"))


@app.post("/manage/restart")
@login_required
def manage_restart():
    if request.form.get("confirmation", "").strip().upper() != "RESTART":
        flash("Aby potwierdzić restart, wpisz RESTART.", "error")
        return redirect(url_for("manage"))
    queue_rate_restart(read_rates())
    flash("Restart został zlecony. Pasek postępu pokaże kolejne etapy.")
    return redirect(url_for("manage"))


@app.route("/api/manage-status")
@login_required
def api_manage_status():
    status = read_rate_status()
    return {"ok": True, "restart": restart_progress(), "last_restart_time": status.get("time"), "rates": read_rates(), "bots": len(live_bots()), "maps": live_map_counts()}


@app.route("/api/heat-events")
@login_required
def api_heat_events():
    event_type = request.args.get("type", "deaths")
    how = "STONE_KILL" if event_type == "metins" else "DEAD_BY_NPC"
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
