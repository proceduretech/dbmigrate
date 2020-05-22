import datetime

import psycopg2

from dbmigrate.migration_directory import MigrationDirectory
from dbmigrate.migration_file import MigrationFile


class Database(object):
    @staticmethod
    def new_connection(database_uri, schema):
        if schema:
            conn = psycopg2.connect(dsn=database_uri, options="-c search_path={0}".format(schema))
        else:
            conn = psycopg2.connect(dsn=database_uri)
        return conn

    @classmethod
    def init_migration(cls, tenant_db_creds):
        CREATE_MIGRATIONS_TABLE_QUERY = """CREATE TABLE IF NOT EXISTS migrations (
        version character varying not null,
        applied_at timestamp with time zone not null);"""

        for tenant_db_cred in tenant_db_creds:
            database_uri = "postgres://%(db_user)s:%(db_password)s@%(db_host)s:%(db_port)s/%(db_name)s" % tenant_db_cred
            schema = tenant_db_cred.get('db_schema')

            print("Running init_migration on database: %s, and schema: %s" % (database_uri, schema))

            conn = cls.new_connection(database_uri, schema)
            try:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(CREATE_MIGRATIONS_TABLE_QUERY)
            finally:
                conn.close()

    @classmethod
    def fetch_last_applied_migration(cls, database_uri, schema):
        FETCH_LAST_MIGRATION_QUERY = "SELECT version FROM migrations ORDER BY applied_at DESC LIMIT 1;"

        conn = cls.new_connection(database_uri, schema)
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(FETCH_LAST_MIGRATION_QUERY)
                    last_version = cursor.fetchone()
        finally:
            conn.close()
        return last_version[0] if last_version else None

    @classmethod
    def run_migrations(cls, migration_direction, tenant_db_creds):
        for tenant_db_cred in tenant_db_creds:
            database_uri = "postgres://%(db_user)s:%(db_password)s@%(db_host)s:%(db_port)s/%(db_name)s" % tenant_db_cred
            schema = tenant_db_cred.get('db_schema')

            last_version = cls.fetch_last_applied_migration(database_uri, schema)
            graph = MigrationDirectory.prepare_migration_graph_to_apply(last_version)
            if not graph:
                print("Nothing to migrate")
                continue

            print("Running migration on database: %s, and schema: %s" % (database_uri, schema))

            conn = cls.new_connection(database_uri, schema)

            try:
                for revision in graph:
                    with conn:
                        # Apply Migrations
                        with conn.cursor() as cursor:
                            revision_file = MigrationDirectory.get_migration_file_path(revision)
                            sql_commands = MigrationFile.parse_file_and_read_migration_commands(revision_file,
                                                                                                migration_direction)
                            if not sql_commands:
                                continue

                            print("Running upgrade: {0} -> {1}".format(last_version, revision))
                            cursor.execute(sql_commands)
                            cursor.execute("INSERT INTO migrations (version, applied_at) VALUES (%s, %s)",
                                           (revision, datetime.datetime.now()))
                            last_version = revision

            finally:
                conn.close()
