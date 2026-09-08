"""Durable mass item grants. Items are created only by the in-game quest."""
import json
import secrets
import time

from flask import abort, flash, redirect, render_template, request, session, url_for

MAX_ITEM_COUNT, MAX_PENDING = 65535, 10
JOBS = (("", "Każda klasa"), ("0", "Wojownik"), ("1", "Ninja"), ("2", "Sura"), ("3", "Szaman"))
TERMINAL = {"done": "Nadano", "has_item": "Już posiada", "full": "Brak miejsca w ekwipunku",
    "failed": "Gra nie mogła utworzyć przedmiotu", "bad_args": "Nieprawidłowy VNUM lub ilość",
    "no_skill": "Warunek nie jest już spełniony", "gone": "Postać nie istnieje",
    "cancelled": "Anulowano", "review": "Wymaga sprawdzenia", "unknown_cmd": "Quest wymaga aktualizacji"}
LABELS = {"waiting": "Czeka na wysłanie", "queued": "Przekazano aktywnej postaci", **TERMINAL}


def init(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_grants (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, batch CHAR(32) NOT NULL,
      player_id INT UNSIGNED NOT NULL, player_name VARCHAR(24) NOT NULL, vnum INT UNSIGNED NOT NULL,
      quantity INT UNSIGNED NOT NULL DEFAULT 1, criteria VARCHAR(1000) NOT NULL DEFAULT '{}',
      only_missing TINYINT(1) NOT NULL DEFAULT 1, status VARCHAR(24) NOT NULL DEFAULT 'waiting',
      queue_id INT NULL, created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, next_try DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY batch_player(batch,player_id), KEY pending(status,next_try), KEY recipient(player_id,vnum,status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    cur.execute("SHOW COLUMNS FROM player.web_seban_grants")
    columns = {row["Field"] for row in cur.fetchall()}
    for name, sql in (
        ("quantity", "ADD COLUMN quantity INT UNSIGNED NOT NULL DEFAULT 1 AFTER vnum"),
        ("criteria", "ADD COLUMN criteria VARCHAR(1000) NOT NULL DEFAULT '{}' AFTER quantity"),
        ("only_missing", "ADD COLUMN only_missing TINYINT(1) NOT NULL DEFAULT 1 AFTER criteria"),
    ):
        if name not in columns:
            cur.execute("ALTER TABLE player.web_seban_grants " + sql)


def number(raw, label, maximum, empty=True):
    raw = (raw or "").strip()
    if empty and not raw:
        return None
    try: value = int(raw)
    except ValueError: abort(400, f"{label}: wpisz liczbę całkowitą.")
    if not 0 <= value <= maximum: abort(400, f"{label}: dozwolony zakres to 0–{maximum}.")
    return value


def criteria_from(values):
    job = values.get("job", "")
    if job not in dict(JOBS): abort(400, "Nieprawidłowa klasa postaci.")
    criteria = {
        "min_level": number(values.get("min_level"), "Minimalny poziom", 120),
        "max_level": number(values.get("max_level"), "Maksymalny poziom", 120),
        "min_horse": number(values.get("min_horse"), "Minimalny poziom konia", 30),
        "min_playtime": number(values.get("min_playtime"), "Minimalny czas gry", 100000),
        "min_riding": number(values.get("min_riding"), "Minimalne jeździectwo", 30),
        "job": int(job) if job else None,
    }
    if criteria["min_level"] is not None and criteria["max_level"] is not None and criteria["min_level"] > criteria["max_level"]:
        abort(400, "Minimalny poziom nie może być wyższy od maksymalnego.")
    return {key: value for key, value in criteria.items() if value is not None}


def criteria_text(criteria):
    labels = []
    for key, text in (("min_level", "Lv ≥ {}"), ("max_level", "Lv ≤ {}"), ("min_horse", "Koń ≥ {}"),
                      ("min_playtime", "Czas ≥ {} h"), ("min_riding", "Jeździectwo ≥ {}")):
        if key in criteria: labels.append(text.format(criteria[key]))
    if "job" in criteria: labels.append(dict(JOBS)[str(criteria["job"])])
    return " · ".join(labels) or "Bez warunków"


def where_for(criteria, alias="p"):
    conditions, params = [], []
    for key, sql, multiplier in (
        ("min_level", f"{alias}.level >= %s", 1), ("max_level", f"{alias}.level <= %s", 1),
        ("min_horse", f"{alias}.horse_level >= %s", 1), ("min_playtime", f"{alias}.playtime >= %s", 60),
        ("job", f"MOD({alias}.job,4) = %s", 1), ("min_riding", f"ORD(SUBSTRING({alias}.skill_level,782,1)) >= %s", 1),
    ):
        if key in criteria:
            conditions.append(sql); params.append(criteria[key] * multiplier)
    return conditions, params


def has_item_sql(vnum, alias="p"):
    return f"""EXISTS(SELECT 1 FROM player.item i WHERE i.vnum=%s AND i.count>0 AND
      ((i.owner_id={alias}.id AND i.window IN ('INVENTORY','EQUIPMENT')) OR
       (i.owner_id={alias}.account_id AND i.window IN ('SAFEBOX','MALL'))))""", [vnum]


def candidates(cur, vnum, criteria, only_missing, player_id=None):
    conditions, params = where_for(criteria)
    if only_missing:
        sql, item_params = has_item_sql(vnum); conditions.append("NOT " + sql); params += item_params
    if player_id is not None: conditions.append("p.id=%s"); params.append(player_id)
    query = """SELECT p.id,p.name,p.level,p.horse_level,p.playtime,MOD(p.job,4) AS job,
      ORD(SUBSTRING(p.skill_level,782,1)) AS riding FROM player.player p"""
    if conditions: query += " WHERE " + " AND ".join(conditions)
    cur.execute(query + " ORDER BY p.id", params)
    return cur.fetchall()


def grant_criteria(grant):
    try:
        value = json.loads(grant["criteria"] or "{}")
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        return None


def install(app, db, login_required, game_text):
    @app.route("/manage/items", methods=["GET", "POST"])
    @login_required
    def manage_items():
        token = session.setdefault("grant_csrf", secrets.token_hex(32))
        try: vnum = int(request.values.get("vnum", "50051"))
        except (TypeError, ValueError): abort(400, "Nieprawidłowy VNUM.")
        if not 1 <= vnum <= 2147483647: abort(400, "Nieprawidłowy VNUM.")
        quantity = number(request.values.get("quantity", "1"), "Ilość", MAX_ITEM_COUNT, False)
        criteria = criteria_from(request.values)
        only_missing = (request.values.getlist("only_missing") or ["1"])[-1] == "1"
        with db() as con, con.cursor() as cur:
            init(cur)
            if request.method == "POST" and not secrets.compare_digest(request.form.get("csrf", ""), token):
                abort(400, "Odśwież formularz i spróbuj ponownie.")
            if request.method == "POST" and request.form.get("action") == "cancel":
                cur.execute("UPDATE player.web_seban_grants SET status='cancelled',updated=NOW() WHERE status='waiting' AND batch=%s", (request.form.get("batch", ""),))
                flash(f"Anulowano oczekujące nadania: {cur.rowcount}.")
                return redirect(url_for("manage_items", vnum=vnum))
            cur.execute("SELECT vnum,locale_name,type,size FROM player.item_proto WHERE vnum=%s", (vnum,))
            item = cur.fetchone()
            if not item: abort(404, "Nie ma przedmiotu o tym VNUM.")
            if not 1 <= int(item["size"] or 0) <= 3 or int(item["type"] or 0) in (0, 10, 30):
                abort(400, "Ten przedmiot nie jest obsługiwany przez zwykły ekwipunek.")
            recipients = candidates(cur, vnum, criteria, only_missing)
            fingerprint = json.dumps((vnum, quantity, criteria, only_missing), sort_keys=True)
            if request.method == "POST":
                preview = session.get("grant_preview")
                if not preview or preview.get("fingerprint") != fingerprint or time.time() - preview["time"] > 900:
                    abort(400, "Najpierw odśwież podgląd odbiorców.")
                cur.execute("SELECT GET_LOCK('seban_item_grants',10) AS acquired")
                if cur.fetchone()["acquired"] != 1: abort(409, "Inne nadanie jest właśnie zapisywane.")
                try:
                    con.begin()
                    recipients = candidates(cur, vnum, criteria, only_missing)
                    criteria_json = json.dumps(criteria, separators=(",", ":"))
                    for row in recipients:
                        cur.execute("""INSERT INTO player.web_seban_grants
                          (batch,player_id,player_name,vnum,quantity,criteria,only_missing)
                          VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                          (preview["batch"], row["id"], row["name"], vnum, quantity, criteria_json, only_missing))
                    con.commit()
                except Exception:
                    con.rollback(); raise
                finally:
                    cur.execute("SELECT RELEASE_LOCK('seban_item_grants')")
                session.pop("grant_preview", None)
                flash(f"Zlecono {quantity}× VNUM {vnum} dla {len(recipients)} postaci.")
                return redirect(url_for("manage_items", vnum=vnum))
            session["grant_preview"] = {"fingerprint": fingerprint, "batch": secrets.token_hex(16), "time": time.time()}
            cur.execute("SELECT * FROM player.web_seban_grants ORDER BY id DESC LIMIT 1000")
            history = cur.fetchall()
            for grant in history:
                grant["criteria_text"] = criteria_text(grant_criteria(grant) or {})
            item["name"] = game_text(item["locale_name"])
            return render_template("item_grants.html", item=item, vnum=vnum, quantity=quantity, criteria=criteria,
                recipients=recipients, only_missing=only_missing, history=history, labels=LABELS, csrf=token, jobs=JOBS,
                criteria_text=criteria_text)


def tick(con):
    with con.cursor() as cur:
        cur.execute("SELECT GET_LOCK('seban_item_grants',0) AS acquired")
        if cur.fetchone()["acquired"] != 1: return
        try:
            con.begin()
            cur.execute("""SELECT g.*,q.status AS queue_status,TIMESTAMPDIFF(SECOND,q.created,NOW()) AS age
              FROM player.web_seban_grants g LEFT JOIN player.web_admin_queue q ON q.id=g.queue_id
              WHERE g.status='queued' FOR UPDATE""")
            for grant in cur.fetchall():
                status = grant["queue_status"]
                if status == "pending" and (grant["age"] or 0) > 60:
                    cur.execute("UPDATE player.web_admin_queue SET status='cancelled' WHERE id=%s AND status='pending'", (grant["queue_id"],))
                    if cur.rowcount: status = "player_offline"
                if status == "pending": continue
                if status and status.startswith("w"):
                    if (grant["age"] or 0) < 120: continue
                    status = "review"
                if status == "player_offline":
                    cur.execute("UPDATE player.web_seban_grants SET status='waiting',queue_id=NULL,next_try=NOW()+INTERVAL 2 MINUTE,updated=NOW() WHERE id=%s", (grant["id"],))
                else:
                    cur.execute("UPDATE player.web_seban_grants SET status=%s,updated=NOW() WHERE id=%s", (status if status in TERMINAL else "review", grant["id"]))
            cur.execute("SELECT COUNT(*) AS n FROM player.web_admin_queue WHERE status='pending'")
            capacity = max(0, MAX_PENDING - cur.fetchone()["n"])
            cur.execute("SELECT * FROM player.web_seban_grants WHERE status='waiting' AND next_try<=NOW() ORDER BY next_try,id LIMIT %s FOR UPDATE", (capacity,))
            for grant in cur.fetchall():
                criteria = grant_criteria(grant)
                player = candidates(cur, grant["vnum"], criteria, bool(grant["only_missing"]), grant["player_id"]) if criteria is not None else []
                if not player:
                    cur.execute("SELECT id FROM player.player WHERE id=%s", (grant["player_id"],))
                    status = "gone" if not cur.fetchone() else ("has_item" if grant["only_missing"] else "no_skill")
                    cur.execute("UPDATE player.web_seban_grants SET status=%s,updated=NOW() WHERE id=%s", (status, grant["id"]))
                    continue
                command = "BULK_MISSING" if grant["only_missing"] else "BULK_ITEM"
                cur.execute("INSERT INTO player.web_admin_queue(player_name,cmd,arg1,arg2) VALUES(%s,%s,%s,%s)",
                    (player[0]["name"], command, str(grant["vnum"]), str(grant["quantity"])))
                cur.execute("UPDATE player.web_seban_grants SET status='queued',queue_id=%s,updated=NOW() WHERE id=%s", (cur.lastrowid, grant["id"]))
            con.commit()
        except Exception:
            con.rollback(); raise
        finally:
            cur.execute("SELECT RELEASE_LOCK('seban_item_grants')")


if __name__ == "__main__":
    from app import db
    while True:
        try:
            with db() as con:
                with con.cursor() as cur: init(cur)
                tick(con)
        except Exception as exc:
            print(f"[item-grants] {type(exc).__name__}: {exc}", flush=True)
        time.sleep(3)
