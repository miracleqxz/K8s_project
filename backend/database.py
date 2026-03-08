import os
import pymysql
import pymysql.cursors
from datetime import datetime, timezone


class Database:
    def __init__(self):
        self._config = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", 3306)),
            "user": os.environ.get("DB_USER", "tasks"),
            "password": os.environ.get("DB_PASSWORD", "tasks"),
            "database": os.environ.get("DB_NAME", "tasks"),
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
        }

    def _connect(self) -> pymysql.Connection:
        return pymysql.connect(**self._config)


    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _row_to_dict(row: dict | None) -> dict | None:
        if row is None:
            return None
        row["done"] = bool(row["done"])
        row["created_at"] = row["created_at"].isoformat()
        row["updated_at"] = row["updated_at"].isoformat()
        return row

    def get_all(self) -> list[dict]:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
                return [self._row_to_dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_by_id(self, task_id: int) -> dict | None:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
                return self._row_to_dict(cur.fetchone())
        finally:
            conn.close()

    def create(self, title: str, description: str = "") -> dict:
        now = self._now()
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tasks (title, description, created_at, updated_at) VALUES (%s, %s, %s, %s)",
                    (title, description, now, now),
                )
            conn.commit()
            return self.get_by_id(cur.lastrowid)
        finally:
            conn.close()

    def update(self, task_id: int, fields: dict) -> dict | None:
        if not fields:
            return self.get_by_id(task_id)
        existing = self.get_by_id(task_id)
        if not existing:
            return None
        sets, vals = [], []
        for key, val in fields.items():
            sets.append(f"{key} = %s")
            vals.append(val)
        sets.append("updated_at = %s")
        vals.append(self._now())
        vals.append(task_id)
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE tasks SET {', '.join(sets)} WHERE id = %s", vals
                )
            conn.commit()
            return self.get_by_id(task_id)
        finally:
            conn.close()

    def delete(self, task_id: int) -> bool:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()