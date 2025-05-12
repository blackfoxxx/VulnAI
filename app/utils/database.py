import sqlite3
from contextlib import contextmanager

DATABASE_PATH = "data/database.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def initialize_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Create table for tool outputs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                parameters TEXT NOT NULL,
                output TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()

# Initialize the database when the module is imported
initialize_database()
