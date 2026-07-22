import aiosqlite
from config import DATABASE_URL

class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    async def setup(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    owner_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Groups table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    chat_id INTEGER,
                    group_title TEXT,
                    is_selected INTEGER DEFAULT 1,
                    UNIQUE(owner_id, chat_id)
                )
            """)
            # Stats table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    owner_id INTEGER PRIMARY KEY,
                    total_sent INTEGER DEFAULT 0,
                    total_success INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0
                )
            """)
            await db.commit()

    async def add_user(self, owner_id, username, full_name):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (owner_id, username, full_name) VALUES (?, ?, ?)",
                (owner_id, username, full_name)
            )
            await db.execute(
                "INSERT OR IGNORE INTO stats (owner_id) VALUES (?)",
                (owner_id,)
            )
            await db.commit()

    async def add_group(self, owner_id, chat_id, title):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO groups (owner_id, chat_id, group_title) VALUES (?, ?, ?)",
                (owner_id, chat_id, title)
            )
            await db.commit()

    async def remove_group(self, owner_id, chat_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM groups WHERE owner_id = ? AND chat_id = ?",
                (owner_id, chat_id)
            )
            await db.commit()

    async def get_groups(self, owner_id, search=None):
        async with aiosqlite.connect(self.db_path) as db:
            if search:
                cursor = await db.execute(
                    "SELECT chat_id, group_title, is_selected FROM groups WHERE owner_id = ? AND group_title LIKE ?",
                    (owner_id, f"%{search}%")
                )
            else:
                cursor = await db.execute(
                    "SELECT chat_id, group_title, is_selected FROM groups WHERE owner_id = ?",
                    (owner_id,)
                )
            return await cursor.fetchall()

    async def toggle_group_selection(self, owner_id, chat_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE groups SET is_selected = 1 - is_selected WHERE owner_id = ? AND chat_id = ?",
                (owner_id, chat_id)
            )
            await db.commit()

    async def bulk_selection(self, owner_id, select_all=True):
        val = 1 if select_all else 0
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE groups SET is_selected = ? WHERE owner_id = ?",
                (val, owner_id)
            )
            await db.commit()

    async def get_selected_groups(self, owner_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT chat_id FROM groups WHERE owner_id = ? AND is_selected = 1",
                (owner_id,)
            )
            return [row[0] for row in await cursor.fetchall()]

    async def update_stats(self, owner_id, success: bool):
        async with aiosqlite.connect(self.db_path) as db:
            if success:
                await db.execute(
                    "UPDATE stats SET total_sent = total_sent + 1, total_success = total_success + 1 WHERE owner_id = ?",
                    (owner_id,)
                )
            else:
                await db.execute(
                    "UPDATE stats SET total_sent = total_sent + 1, total_failed = total_failed + 1 WHERE owner_id = ?",
                    (owner_id,)
                )
            await db.commit()

    async def get_user_stats(self, owner_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT total_sent, total_success, total_failed FROM stats WHERE owner_id = ?", (owner_id,))
            return await cursor.fetchone()

db = Database(DATABASE_URL)