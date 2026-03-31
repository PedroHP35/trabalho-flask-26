import sqlite3

DB_PATH = "data.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Cria as tabelas 'data' e 'users' se ainda não existirem."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT    NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


def insert_value(value: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute("INSERT INTO data (value) VALUES (?)", (value,))
        return cursor.lastrowid

def get_all_values() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM data ORDER BY id DESC").fetchall()
    return [{"id": row["id"], "data": row["value"]} for row in rows]

# ── Operações da tabela 'users' ───────────────────────────────────────────────

def create_user(username: str, password_hash: str) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                (username, password_hash)
            )
        return True
    except sqlite3.IntegrityError:

        return False

def get_user_by_username(username: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None
