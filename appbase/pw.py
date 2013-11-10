import psycopg2
import psycopg2.pool

from peewee import PostgresqlDatabase, ImproperlyConfigured

import settings


class PostgresqlPoolDatabase(PostgresqlDatabase):
    pool = psycopg2.pool.ThreadedConnectionPool(5, 20, database=settings.DB_NAME)

    def init_pool(self, database, **kwargs):
        self.pool = psycopg2.pool.SimpleConnectionPool(
            5, 10, database=settings.DB_NAME)

    def _connect(self, database, **kwargs):
        if not psycopg2:
            raise ImproperlyConfigured('psycopg2 must be installed.')
        conn = self.pool.getconn()
        #if self.register_unicode:
        #    pg_extensions.register_type(pg_extensions.UNICODE, conn)
        #    pg_extensions.register_type(pg_extensions.UNICODEARRAY, conn)
        return conn

    def execute_sql(self, sql, params=None, require_commit=True):
        print((sql, params))
        cursor = self.get_cursor()
        try:
            cursor.execute(sql, params or ())
        except Exception as exc:
            print('Error executing query %s (%s)' % (sql, params))
            return self.sql_error_handler(exc, sql, params, require_commit)
        if require_commit and self.get_autocommit():
            self.commit()
        return cursor

    def complete(self):
        pass

    def _close(self, conn):
        conn.cursor.close()
        self.pool.putconn(conn)
