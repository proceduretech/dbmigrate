import datetime
import subprocess

import click
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
    def init_migration(cls, db_creds):
        MigrationDirectory.create_if_not_exists()

        CREATE_MIGRATIONS_TABLE_QUERY = """CREATE TABLE IF NOT EXISTS migrations (
        version character varying not null,
        applied_at timestamp with time zone not null,
        rollbacked boolean);"""

        for db_cred in db_creds:
            database_uri = "postgres://%(db_user)s:%(db_password)s@%(db_host)s:%(db_port)s/%(db_name)s" % db_cred
            schema = db_cred.get('db_schema')

            click.confirm("Running init_migration on database: %s, and schema: %s" % (database_uri, schema), abort=True)

            conn = cls.new_connection(database_uri, schema)
            try:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(CREATE_MIGRATIONS_TABLE_QUERY)
            finally:
                conn.close()

    @classmethod
    def fetch_last_applied_migration(cls, database_uri, schema):
        FETCH_LAST_MIGRATION_QUERY = "SELECT version FROM migrations WHERE rollbacked is not %s ORDER BY applied_at " \
                                     "DESC LIMIT 1;"

        conn = cls.new_connection(database_uri, schema)
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(FETCH_LAST_MIGRATION_QUERY, (True,))
                    last_version = cursor.fetchone()
        finally:
            conn.close()
        return last_version[0] if last_version else None

    @classmethod
    def run_migrations(cls, migration_direction, db_creds):
        for db_cred in db_creds:
            database_uri = "postgres://%(db_user)s:%(db_password)s@%(db_host)s:%(db_port)s/%(db_name)s" % db_cred
            schema = db_cred.get('db_schema')

            if migration_direction == 'upgrade':
                cls.upgrade(database_uri, schema)

            elif migration_direction == 'downgrade':
                cls.downgrade(database_uri, schema)

            else:
                raise Exception("Invalid migration direction")

    @classmethod
    def upgrade(cls, database_uri, schema):
        last_version = cls.fetch_last_applied_migration(database_uri, schema)

        graph = MigrationDirectory.prepare_migration_graph_to_apply(last_version)
        if not graph:
            print("Nothing to migrate")
            return

        print("Running migration on database: %s, and schema: %s" % (database_uri, schema))

        conn = cls.new_connection(database_uri, schema)

        try:
            for revision in graph:
                with conn:
                    # Apply Migrations
                    with conn.cursor() as cursor:
                        revision_file = MigrationDirectory.get_migration_file_path(revision)
                        sql_commands = MigrationFile.parse_file_and_read_migration_commands(revision_file,
                                                                                            'upgrade')
                        if not sql_commands:
                            continue

                        print("Running upgrade: {0} -> {1}".format(last_version, revision))
                        cursor.execute(sql_commands)
                        cursor.execute("INSERT INTO migrations (version, applied_at) VALUES (%s, %s)",
                                       (revision, datetime.datetime.now()))
                        last_version = revision

        finally:
            conn.close()

    @classmethod
    def downgrade(cls, database_uri, schema):
        last_version = cls.fetch_last_applied_migration(database_uri, schema)
        if not last_version:
            print("Nothing to rollback")
            return

        print("Rollbacking last applied migration version: %s, on database: %s, and "
              "schema: %s" % (last_version, database_uri, schema))

        revision_file = MigrationDirectory.get_migration_file_path(last_version)
        sql_commands = MigrationFile.parse_file_and_read_migration_commands(revision_file,
                                                                            'downgrade')
        if not sql_commands:
            print("Can't find SQL commands to rollback this migration")
            return

        conn = cls.new_connection(database_uri, schema)
        try:
            with conn:
                with conn.cursor() as cursor:
                    print("Running downgrade: {0}".format(last_version))
                    cursor.execute(sql_commands)
                    cursor.execute("UPDATE migrations SET rollbacked = %s WHERE version = %s", (True, last_version))
        finally:
            conn.close()

    @staticmethod
    def dump(database_uri, db_schema):
        schema_file_path = MigrationDirectory.get_schema_file_path('schema')

        process = subprocess.Popen(
            ["pg_dump", "--format=plain", "--encoding=UTF8", "--schema-only", "--no-privileges",
             "--no-owner", "-n", db_schema, "-f", schema_file_path, database_uri],
            stdout=subprocess.PIPE, universal_newlines=True)

        output = process.communicate()[0]
        if int(process.returncode) != 0:
            print('Command failed. Return code : {}'.format(process.returncode))
            exit(1)
        return output
