import aiosqlite

DB_PATH = "/app/db/anonbot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id   INTEGER UNIQUE NOT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                code       TEXT UNIQUE NOT NULL,
                owner_id   INTEGER NOT NULL
                  REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                link_id           INTEGER NOT NULL
                  REFERENCES links(id) ON DELETE CASCADE,
                sender_user_id    INTEGER
                  REFERENCES users(id),
                text              TEXT,
                media_type        TEXT,
                media_file_id     TEXT,
                created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
                reply_to_id       INTEGER
            );
        """)
        await db.commit()


async def migrate_db():
    """Миграция существующей БД: добавление колонок для медиа."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("PRAGMA table_info(messages);")
        columns = {row[1] for row in await cur.fetchall()}
        
        if "media_type" not in columns:
            await db.execute("ALTER TABLE messages ADD COLUMN media_type TEXT;")
        if "media_file_id" not in columns:
            await db.execute("ALTER TABLE messages ADD COLUMN media_file_id TEXT;")
        
        await db.commit()
