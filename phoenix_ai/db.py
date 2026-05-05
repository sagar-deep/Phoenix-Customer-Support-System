# ============================================================
# db.py  –  MySQL Connection Helper
# ============================================================

import mysql.connector

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",       # ← change if needed
    "password": "root123",           # ← change if needed
    "database": "phoenix_ai",
}


def get_conn():
    """Return a fresh MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)
