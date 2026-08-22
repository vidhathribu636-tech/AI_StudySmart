"""
database/database.py
--------------------
SQLite database setup for AI Study Buddy.
"""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "study_buddy.db")


@contextmanager
def get_connection():
    """Context-manager connection — auto-commits and closes on exit."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not already exist."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    UNIQUE,
            created_at TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER REFERENCES users(id),
            topic        TEXT    NOT NULL,
            score        INTEGER NOT NULL DEFAULT 0,
            max_score    INTEGER NOT NULL DEFAULT 0,
            attempted_at TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS quiz_scores (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id     INTEGER REFERENCES quiz_attempts(id),
            question       TEXT    NOT NULL,
            user_answer    TEXT,
            correct_answer TEXT,
            is_correct     INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS topic_performance (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER REFERENCES users(id),
            topic        TEXT    NOT NULL,
            total_score  INTEGER NOT NULL DEFAULT 0,
            total_max    INTEGER NOT NULL DEFAULT 0,
            attempts     INTEGER NOT NULL DEFAULT 0,
            last_studied TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS saved_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT    NOT NULL,
            summary    TEXT    NOT NULL,
            created_at TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS saved_decks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            topic      TEXT    NOT NULL,
            cards_json TEXT    NOT NULL,
            created_at TEXT    DEFAULT (datetime('now'))
        );
        """)
