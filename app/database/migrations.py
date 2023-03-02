import os
import re
import sqlite3
import logging

from app.config import Config

logger = logging.getLogger(__name__)


MIGRATIONS_FOLDER = os.path.join(os.path.dirname(__file__), 'migrations')


def apply_migrations() -> None:
    with Config.database.get_connection() as conn:
        cursor = conn.cursor()
        __create_migrations_table(cursor)

        for migration_file in sorted(os.listdir(MIGRATIONS_FOLDER)):
            migration_match = re.match(r'^(\d+).*\.sql$', migration_file)
            if not migration_match:
                logger.warning('Skipping invalid migration file: %s', migration_file)
                continue

            migration_version = int(migration_match.group(1))
            if __migration_already_applied(cursor, migration_version):
                logger.info('Skipping already-applied migration file: %s', migration_file)
                continue

            migration_path = os.path.join(MIGRATIONS_FOLDER, migration_file)
            __apply_migration(cursor, migration_version, migration_path)


def __create_migrations_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL UNIQUE
        );
    ''')


def __migration_already_applied(cursor: sqlite3.Cursor, version: int) -> bool:
    cursor.execute(
        'SELECT COUNT(*) FROM migrations WHERE version = ?',
        (version,)
    )
    return cursor.fetchone()[0] > 0


def __apply_migration(cursor: sqlite3.Cursor, migration_version: int, migration_path: str) -> None:
    with open(migration_path, encoding='utf-8') as f:
        migration_sql = f.read()
        cursor.executescript(migration_sql)
        cursor.execute(
            'INSERT INTO migrations (version) VALUES (?)',
            (migration_version,)
        )
        logger.info('Applied migration file: %s', migration_path)
