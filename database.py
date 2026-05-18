import sqlite3
from datetime import datetime

DB_NAME = "bot.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT UNIQUE NOT NULL,
        title TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        original_url TEXT,
        converted_url TEXT,
        platform TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_admin(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (user_id,))
    conn.commit()
    conn.close()


def remove_admin(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def is_admin(user_id: int, owner_id: int) -> bool:
    if user_id == owner_id:
        return True

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def add_channel(chat_id: str, title: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR IGNORE INTO channels(chat_id, title, created_at)
    VALUES(?, ?, ?)
    """, (chat_id, title, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def remove_channel(chat_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM channels WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()


def get_channels():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT chat_id, title FROM channels")
    rows = cur.fetchall()
    conn.close()
    return rows


def save_analytics(user_id: int, original_url: str, converted_url: str, platform: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO analytics(user_id, original_url, converted_url, platform, created_at)
    VALUES(?, ?, ?, ?, ?)
    """, (
        user_id,
        original_url,
        converted_url,
        platform,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()


def analytics_count():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM analytics")
    total = cur.fetchone()[0]

    cur.execute("SELECT platform, COUNT(*) FROM analytics GROUP BY platform")
    by_platform = cur.fetchall()

    conn.close()
    return total, by_platform


def set_setting(key: str, value: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO settings(key, value) VALUES(?, ?)
    ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_setting(key: str, default: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default
