import aiosqlite

from .config import DB_PATH


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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS blocked_users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                blocked_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, blocked_id)
            );
        """)
        await db.commit()


async def migrate_db():
    """Миграция существующей БД: добавление колонок для медиа и снятие NOT NULL с text."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("PRAGMA table_info(messages);")
        columns = {row[1]: row for row in await cur.fetchall()}
        
        # Добавляем новые колонки если их нет
        if "media_type" not in columns:
            await db.execute("ALTER TABLE messages ADD COLUMN media_type TEXT;")
        if "media_file_id" not in columns:
            await db.execute("ALTER TABLE messages ADD COLUMN media_file_id TEXT;")
        
        # Проверяем, есть ли NOT NULL на text (notnull = 1)
        # columns[name] = (cid, name, type, notnull, default, pk)
        if "text" in columns and columns["text"][3] == 1:
            # Пересоздаём таблицу без NOT NULL на text
            await db.execute("PRAGMA foreign_keys = OFF;")
            await db.execute("""
                CREATE TABLE messages_new (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    link_id           INTEGER NOT NULL REFERENCES links(id) ON DELETE CASCADE,
                    sender_user_id    INTEGER REFERENCES users(id),
                    text              TEXT,
                    media_type        TEXT,
                    media_file_id     TEXT,
                    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reply_to_id       INTEGER
                );
            """)
            await db.execute("""
                INSERT INTO messages_new (id, link_id, sender_user_id, text, created_at, reply_to_id)
                SELECT id, link_id, sender_user_id, text, created_at, reply_to_id FROM messages;
            """)
            await db.execute("DROP TABLE messages;")
            await db.execute("ALTER TABLE messages_new RENAME TO messages;")
            await db.execute("PRAGMA foreign_keys = ON;")
        
        await db.commit()
