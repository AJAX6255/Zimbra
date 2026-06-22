import sqlite3
from datetime import datetime
from typing import List
import pandas as pd
from zimbra.config import DATABASE_PATH
from zimbra.models import PostRecord

def init_db(db_path: str = DATABASE_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            source TEXT,
            platform_entity TEXT,
            post_id TEXT PRIMARY KEY,
            author TEXT,
            created_utc TEXT,
            text TEXT,
            thread_id TEXT,
            thread_title TEXT,
            likes REAL,
            replies REAL,
            reposts REAL,
            views REAL,
            followers_est REAL,
            author_role_hint TEXT,
            url TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            symbol TEXT,
            timestamp TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (symbol, timestamp)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economic_indicators (
            indicator_name TEXT,
            year INTEGER,
            month INTEGER,
            value REAL,
            PRIMARY KEY (indicator_name, year, month)
        )
        """
    )
    conn.commit()
    conn.close()

def save_posts(posts: List[PostRecord], db_path: str = DATABASE_PATH):
    if not posts:
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR REPLACE INTO posts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                p.source, p.platform_entity, p.post_id, p.author, 
                p.created_utc.isoformat() if isinstance(p.created_utc, datetime) else str(p.created_utc), 
                p.text, p.thread_id, p.thread_title, p.likes, p.replies, p.reposts, 
                p.views, p.followers_est, p.author_role_hint, p.url
            )
            for p in posts
        ],
    )
    conn.commit()
    conn.close()

def load_posts(db_path: str = DATABASE_PATH) -> pd.DataFrame:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM posts", conn)
    conn.close()
    if not df.empty:
        df["created_utc"] = pd.to_datetime(df["created_utc"], utc=True)
    return df

def save_prices(prices: List[dict], db_path: str = DATABASE_PATH):
    if not prices:
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR REPLACE INTO prices VALUES (?,?,?,?,?,?,?)",
        [
            (
                p.get("symbol"),
                p.get("timestamp"),
                p.get("open"),
                p.get("high"),
                p.get("low"),
                p.get("close"),
                p.get("volume"),
            )
            for p in prices
        ],
    )
    conn.commit()
    conn.close()

def load_prices(symbol: str, db_path: str = DATABASE_PATH) -> pd.DataFrame:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM prices WHERE symbol = ?", conn, params=[symbol])
    conn.close()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.sort_values("timestamp", inplace=True)
    return df

def save_economic_indicators(indicators: List[dict], db_path: str = DATABASE_PATH):
    if not indicators:
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR REPLACE INTO economic_indicators VALUES (?,?,?,?)",
        [
            (
                ind.get("indicator_name"),
                ind.get("year"),
                ind.get("month"),
                ind.get("value"),
            )
            for ind in indicators
        ],
    )
    conn.commit()
    conn.close()

def load_economic_indicators(indicator_name: str, db_path: str = DATABASE_PATH) -> pd.DataFrame:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM economic_indicators WHERE indicator_name = ?", conn, params=[indicator_name])
    conn.close()
    if not df.empty:
        df.sort_values(["year", "month"], inplace=True)
    return df
