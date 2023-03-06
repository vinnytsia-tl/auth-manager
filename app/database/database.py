import sqlite3
import threading
import logging


logger = logging.getLogger(__name__)


class Database():
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.thread_local = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        connection = getattr(self.thread_local, 'connection', None)

        if connection is None:
            connection = sqlite3.connect(self.db_path)
            connection.execute('PRAGMA foreign_keys = ON;')
            connection.set_trace_callback(lambda sql: logger.debug('Executing SQL query: %s', sql))
            self.thread_local.connection = connection
            logger.debug('Opened new database connection')

        return connection

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.get_connection().execute(sql, params)

    def cleanup(self) -> None:
        with self.get_connection() as connection:
            connection.execute('DELETE FROM sessions;')
            logger.info('Cleaned up sessions table')
