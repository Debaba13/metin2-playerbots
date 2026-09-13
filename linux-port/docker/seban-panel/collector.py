import os
import time
from datetime import datetime
from pathlib import Path

import pymysql

INTERVAL = int(os.environ.get("SEBAN_COLLECTOR_INTERVAL", "300"))
STATUS_GLOB = os.environ.get("PLAYERBOTS_STATUS_GLOB", "/opt/metin2/var/channel1/*/playerbot_status.tsv")


def connect():
    return pymysql.connect(host=os.environ.get("DB_HOST", "mariadb"), port=int(os.environ.get("DB_PORT", "3306")), user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"], charset="utf8mb4", autocommit=True)


def host_metrics(previous=None):
    try:
        with open("/host/proc/stat") as f:
            parts = f.readline().split()[1:]
        total = sum(map(int, parts)); idle = int(parts[3]) + int(parts[4])
        with open("/host/proc/meminfo") as f:
            mem = {line.split(":")[0]: int(line.split()[1]) for line in f if ":" in line}
        total_mb = mem["MemTotal"] // 1024; used_mb = (mem["MemTotal"] - mem.get("MemAvailable", mem.get("MemFree", 0))) // 1024
        disk = os.statvfs("/hostfs")
        disk_total_mb = (disk.f_blocks * disk.f_frsize) // (1024 * 1024)
        disk_used_mb = ((disk.f_blocks - disk.f_bavail) * disk.f_frsize) // (1024 * 1024)
        if previous:
            cpu = round(100 * (1 - (idle - previous[1]) / max(1, total - previous[0])), 1)
        else:
            with open("/host/proc/loadavg") as f:
                load_1m = float(f.read().split()[0])
            with open("/host/proc/cpuinfo") as f:
                cpu_count = max(1, sum(1 for line in f if line.startswith("processor")))
            cpu = round(min(100, 100 * load_1m / cpu_count), 1)
        return (total, idle), cpu, used_mb, total_mb, disk_used_mb, disk_total_mb
    except (OSError, KeyError, ValueError):
        return previous, 0, 0, 0, 0, 0


def init(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_admin_queue (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      player_name VARCHAR(24) NOT NULL, cmd VARCHAR(32) NOT NULL,
      arg1 VARCHAR(255) NOT NULL DEFAULT '', arg2 VARCHAR(255) NOT NULL DEFAULT '',
      status VARCHAR(24) NOT NULL DEFAULT 'pending',
      created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      KEY pending (status, created), KEY player_status (player_name, status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_settings (
      name VARCHAR(64) NOT NULL PRIMARY KEY, value VARCHAR(255) NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB""")
    cur.execute("""INSERT IGNORE INTO player.web_seban_settings (name,value) VALUES
      ('panel_name','Metin2 Singleplayer'),('stuck_minutes','5'),('theme','ocean'),('monitor_mode','vps'),
      ('setup_complete','1'),('auth_enabled','0'),('auth_password_hash','')""")
    # One-time branding migration for deployments created before the public-ready build.
    cur.execute("UPDATE player.web_seban_settings SET value='Metin2 Singleplayer' WHERE name='panel_name' AND value='Mt2009'")
    # Single-player suite: no setup wizard, no passphrase - one player at their
    # own machine (Tieru, 13 September). Skip the wizard for installs seeded
    # before this; an operator can still turn auth on from the panel.
    cur.execute("UPDATE player.web_seban_settings SET value='1' WHERE name='setup_complete' AND value='0'")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_item_snapshot (
      captured_at DATETIME NOT NULL, vnum INT UNSIGNED NOT NULL, amount BIGINT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,vnum), KEY(vnum,captured_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_map_snapshot (
      captured_at DATETIME NOT NULL, map_index INT UNSIGNED NOT NULL, character_count INT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,map_index), KEY(map_index,captured_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_system_snapshot (
      captured_at DATETIME NOT NULL PRIMARY KEY, cpu_percent DECIMAL(5,1) NOT NULL,
      ram_percent DECIMAL(5,1) NOT NULL, ram_used_mb INT UNSIGNED NOT NULL, ram_total_mb INT UNSIGNED NOT NULL,
      disk_percent DECIMAL(5,1) NOT NULL DEFAULT 0, disk_used_mb INT UNSIGNED NOT NULL DEFAULT 0,
      disk_total_mb INT UNSIGNED NOT NULL DEFAULT 0) ENGINE=InnoDB""")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_percent DECIMAL(5,1) NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_used_mb INT UNSIGNED NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_total_mb INT UNSIGNED NOT NULL DEFAULT 0")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_metric_snapshot (
      captured_at DATETIME NOT NULL, metric VARCHAR(64) NOT NULL, value BIGINT NOT NULL,
      PRIMARY KEY(captured_at,metric), KEY(metric,captured_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_bot_position_snapshot (
      captured_at DATETIME NOT NULL, pid INT UNSIGNED NOT NULL, map_index INT UNSIGNED NOT NULL,
      x INT NOT NULL, y INT NOT NULL, PRIMARY KEY(captured_at,pid), KEY(pid,captured_at)) ENGINE=InnoDB""")


def live_positions():
    result = {}
    for path in Path("/").glob(STATUS_GLOB.lstrip("/")):
        try:
            if time.time() - path.stat().st_mtime > 25:
                continue
            for line in path.read_text(encoding="cp1250", errors="replace").splitlines()[1:]:
                values = line.split("\t", 13)
                if len(values) == 14:
                    result[int(values[0])] = (int(values[8]), int(values[9]), int(values[10]))
        except (OSError, ValueError):
            continue
    return result


def live_map_counts():
    counts = {}
    for index, _, _ in live_positions().values():
        counts[index] = counts.get(index, 0) + 1
    return counts


def collect(con, previous):
    now = datetime.now().replace(second=0, microsecond=0)
    previous, cpu, used, total, disk_used, disk_total = host_metrics(previous)
    ram = round(100 * used / total, 1) if total else 0
    disk_percent = round(100 * disk_used / disk_total, 1) if disk_total else 0
    with con.cursor() as cur:
        init(cur)
        cur.execute("""INSERT INTO player.web_seban_system_snapshot
          (captured_at,cpu_percent,ram_percent,ram_used_mb,ram_total_mb,disk_percent,disk_used_mb,disk_total_mb)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
          ON DUPLICATE KEY UPDATE cpu_percent=VALUES(cpu_percent), ram_percent=VALUES(ram_percent),
            ram_used_mb=VALUES(ram_used_mb), ram_total_mb=VALUES(ram_total_mb), disk_percent=VALUES(disk_percent),
            disk_used_mb=VALUES(disk_used_mb), disk_total_mb=VALUES(disk_total_mb)""",
            (now, cpu, ram, used, total, disk_percent, disk_used, disk_total))
        for map_index, count in live_map_counts().items():
            cur.execute("INSERT IGNORE INTO player.web_seban_map_snapshot VALUES (%s,%s,%s)", (now, map_index, count))
        for pid, (map_index, x, y) in live_positions().items():
            cur.execute("INSERT IGNORE INTO player.web_seban_bot_position_snapshot VALUES (%s,%s,%s,%s,%s)", (now, pid, map_index, x, y))
        cur.execute("""INSERT IGNORE INTO player.web_seban_item_snapshot (captured_at,vnum,amount)
          SELECT %s, vnum, SUM(count) FROM player.item GROUP BY vnum""", (now,))
        cur.execute("SELECT COALESCE(SUM(gold),0) FROM player.player WHERE name NOT IN ('[SA]Admin','Test')")
        yang = cur.fetchone()[0]
        cur.execute("INSERT IGNORE INTO player.web_seban_metric_snapshot VALUES (%s,'total_yang',%s)", (now, yang))
    return previous


def main():
    previous = None
    while True:
        try:
            with connect() as con:
                previous = collect(con, previous)
                print("[seban-collector] snapshot complete", flush=True)
        except Exception as exc:
            print(f"[seban-collector] {exc}", flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
