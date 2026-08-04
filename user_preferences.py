import os
import sqlite3
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")

def get_user_preferences() -> dict:
    """Return the current user preferences as a dict."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT prefer_organic, max_price FROM user_preferences WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "prefer_organic": bool(row[0]) if row[0] is not None else None,
            "max_price": row[1]
        }
    return {"prefer_organic": None, "max_price": None}

def set_user_preference(prefer_organic: Optional[bool] = None, max_price: Optional[float] = None) -> str:
    """Update preferences. Only provided fields are changed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ensure the row exists
    cursor.execute("INSERT OR IGNORE INTO user_preferences (id) VALUES (1)")
    updates = []
    params = []
    if prefer_organic is not None:
        updates.append("prefer_organic = ?")
        params.append(1 if prefer_organic else 0)
    if max_price is not None:
        updates.append("max_price = ?")
        params.append(max_price)
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE user_preferences SET {', '.join(updates)} WHERE id = 1"
        cursor.execute(sql, params)
        conn.commit()
    conn.close()
    return "Preferences updated successfully."