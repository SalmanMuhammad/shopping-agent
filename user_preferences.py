import os
import sqlite3
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")


def get_user_preferences(category: Optional[str] = None) -> dict:
    """Return preferences for a specific category or global."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if category:
        cursor.execute(
            "SELECT prefer_organic, min_price, max_price FROM category_preferences WHERE category = ?",
            (category,),
        )
        row = cursor.fetchone()
        if row:
            conn.close()
            return {
                "prefer_organic": bool(row[0]) if row[0] is not None else None,
                "min_price": row[1],
                "max_price": row[2],
            }
    # Fallback to global
    cursor.execute(
        "SELECT prefer_organic, min_price, max_price FROM user_preferences WHERE id = 1"
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "prefer_organic": bool(row[0]) if row[0] is not None else None,
            "min_price": row[1],
            "max_price": row[2],
        }
    return {"prefer_organic": None, "min_price": None, "max_price": None}


def get_all_category_preferences() -> dict:
    """Return all preferences: global + per‑category."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Global (old user_preferences table)
    cursor.execute(
        "SELECT prefer_organic, min_price, max_price FROM user_preferences WHERE id = 1"
    )
    global_row = cursor.fetchone()
    if global_row:
        global_prefs = {
            "prefer_organic": (
                bool(global_row[0]) if global_row[0] is not None else None
            ),
            "min_price": global_row[1],
            "max_price": global_row[2],
        }
    else:
        global_prefs = {"prefer_organic": None, "min_price": None, "max_price": None}

    # All categories
    cursor.execute(
        "SELECT category, prefer_organic, min_price, max_price FROM category_preferences"
    )
    rows = cursor.fetchall()
    conn.close()

    categories = {}
    for row in rows:
        categories[row[0]] = {
            "prefer_organic": bool(row[1]) if row[1] is not None else None,
            "min_price": row[2],
            "max_price": row[3],
        }

    return {"global": global_prefs, "categories": categories}


def set_user_preference(
    category: Optional[str] = None,
    prefer_organic: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> str:
    """Update preferences. category=None means global."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if category:
        cursor.execute(
            "INSERT OR IGNORE INTO category_preferences (category) VALUES (?)",
            (category,),
        )
        updates = []
        params = []
        if prefer_organic is not None:
            updates.append("prefer_organic = ?")
            params.append(1 if prefer_organic else 0)
        if min_price is not None:
            updates.append("min_price = ?")
            params.append(min_price)
        if max_price is not None:
            updates.append("max_price = ?")
            params.append(max_price)
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            sql = f"UPDATE category_preferences SET {', '.join(updates)} WHERE category = ?"
            params.append(category)
            cursor.execute(sql, params)
        conn.commit()
        conn.close()
        return f"Preferences for '{category}' updated successfully."
    else:
        # Global
        cursor.execute("INSERT OR IGNORE INTO user_preferences (id) VALUES (1)")
        updates = []
        params = []
        if prefer_organic is not None:
            updates.append("prefer_organic = ?")
            params.append(1 if prefer_organic else 0)
        if min_price is not None:
            updates.append("min_price = ?")
            params.append(min_price)
        if max_price is not None:
            updates.append("max_price = ?")
            params.append(max_price)
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            sql = f"UPDATE user_preferences SET {', '.join(updates)} WHERE id = 1"
            cursor.execute(sql, params)
            conn.commit()
        conn.close()
        return "Global preferences updated successfully."
