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
                text              TEXT NOT NULL,
                created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
                reply_to_id       INTEGER
            );
        """)
        await db.commit()
