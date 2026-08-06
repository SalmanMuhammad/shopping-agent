import sqlite3
from contextlib import contextmanager
from typing import Generator
from pathlib import Path
from production.config import settings
from production.logger import logger


@contextmanager
def get_db_connection(db_path: Path = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for managing SQLite database connections.
    Ensures commit on success, rollback on error, and automatic closure.
    """
    target_path = db_path or settings.DB_PATH
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row  # Enables column access by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error occurring during transaction: {e}")
        raise e
    finally:
        conn.close()
