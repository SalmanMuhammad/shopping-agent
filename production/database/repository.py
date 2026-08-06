import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path
from production.database.connection import get_db_connection
from production.logger import logger


class ProductRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def search_products(
        self,
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_organic: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "SELECT id, name, category, price, description, is_organic FROM products WHERE 1=1"
            params: List[Any] = []

            if query:
                sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
                like = f"%{query}%"
                params.extend([like, like, like])

            if min_price is not None:
                sql += " AND price >= ?"
                params.append(min_price)

            if max_price is not None:
                sql += " AND price <= ?"
                params.append(max_price)

            if is_organic is not None:
                sql += " AND is_organic = ?"
                params.append(1 if is_organic else 0)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "category": row["category"],
                    "price": row["price"],
                    "description": row["description"],
                    "is_organic": bool(row["is_organic"]),
                }
                for row in rows
            ]

    def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, category, price, description, is_organic FROM products WHERE id = ?",
                (product_id,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "category": row["category"],
                    "price": row["price"],
                    "description": row["description"],
                    "is_organic": bool(row["is_organic"]),
                }
            return None


class ReviewRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def get_product_rating(self, product_id: int) -> Dict[str, Any]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?",
                (product_id,),
            )
            row = cursor.fetchone()
            avg = round(row[0], 2) if row and row[0] is not None else 0.0
            count = row[1] if row else 0
            return {
                "product_id": product_id,
                "average_rating": avg,
                "review_count": count,
            }

    def get_ratings_for_products(self, product_ids: List[int]) -> List[Dict[str, Any]]:
        if not product_ids:
            return []
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(product_ids))
            cursor.execute(
                f"""
                SELECT product_id, AVG(rating), COUNT(*)
                FROM reviews
                WHERE product_id IN ({placeholders})
                GROUP BY product_id
                """,
                product_ids,
            )
            rows = cursor.fetchall()
            ratings_map = {
                r["product_id"]: {
                    "average_rating": round(r[1], 2),
                    "review_count": r[2],
                }
                for r in rows
            }
            return [
                {
                    "product_id": pid,
                    "average_rating": ratings_map.get(pid, {}).get("average_rating", 0.0),
                    "review_count": ratings_map.get(pid, {}).get("review_count", 0),
                }
                for pid in product_ids
            ]


class PreferenceRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def get_user_preferences(self, category: Optional[str] = None) -> Dict[str, Any]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT prefer_organic, min_price, max_price FROM category_preferences WHERE category = ?",
                    (category,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "prefer_organic": bool(row["prefer_organic"]) if row["prefer_organic"] is not None else None,
                        "min_price": row["min_price"],
                        "max_price": row["max_price"],
                    }

            cursor.execute(
                "SELECT prefer_organic, min_price, max_price FROM user_preferences WHERE id = 1"
            )
            row = cursor.fetchone()
            if row:
                return {
                    "prefer_organic": bool(row["prefer_organic"]) if row["prefer_organic"] is not None else None,
                    "min_price": row["min_price"],
                    "max_price": row["max_price"],
                }
            return {"prefer_organic": None, "min_price": None, "max_price": None}

    def get_all_category_preferences(self) -> Dict[str, Any]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT prefer_organic, min_price, max_price FROM user_preferences WHERE id = 1"
            )
            global_row = cursor.fetchone()
            if global_row:
                global_prefs = {
                    "prefer_organic": (
                        bool(global_row["prefer_organic"])
                        if global_row["prefer_organic"] is not None
                        else None
                    ),
                    "min_price": global_row["min_price"],
                    "max_price": global_row["max_price"],
                }
            else:
                global_prefs = {"prefer_organic": None, "min_price": None, "max_price": None}

            cursor.execute(
                "SELECT category, prefer_organic, min_price, max_price FROM category_preferences"
            )
            rows = cursor.fetchall()
            categories = {}
            for row in rows:
                categories[row["category"]] = {
                    "prefer_organic": (
                        bool(row["prefer_organic"])
                        if row["prefer_organic"] is not None
                        else None
                    ),
                    "min_price": row["min_price"],
                    "max_price": row["max_price"],
                }

            return {"global": global_prefs, "categories": categories}

    def set_user_preference(
        self,
        category: Optional[str] = None,
        prefer_organic: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> str:
        with get_db_connection(self.db_path) as conn:
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
                return f"Preferences for '{category}' updated successfully."
            else:
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
                return "Global preferences updated successfully."


class OrderRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def create_order(self, product_id: int, product_name: str, price: float) -> int:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO orders (product_id, product_name, price) VALUES (?, ?, ?)",
                (product_id, product_name, price),
            )
            return cursor.lastrowid

    def get_orders(
        self,
        limit: Optional[int] = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = "SELECT id, product_name, price, ordered_at FROM orders WHERE 1=1"
            params: List[Any] = []

            if start_date:
                sql += " AND ordered_at >= ?"
                params.append(start_date)

            if end_date:
                sql += " AND ordered_at <= ?"
                params.append(end_date)

            sql += " ORDER BY ordered_at DESC"

            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [
                {
                    "order_id": row["id"],
                    "product_name": row["product_name"],
                    "price": row["price"],
                    "ordered_at": row["ordered_at"],
                }
                for row in rows
            ]
