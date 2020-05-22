#!/usr/bin/env python
import os
import sys

import psycopg2

from dbmigrate.database import Database
from dbmigrate.migration_directory import MigrationDirectory

"""
Script to create migration file template, run the migrations, from the file generated.

The script also tracks which migration has been run till now, and everytime runs only the remaining chain of the 
migration graph. If there is nothing to migrate, the script does nothing

The migration file should be in following format:

FileStart>>
-- revision: 'revision'        # current revision
-- down_revision: 'revision'   # revision after which this file was created. Keep empty string ('') for 1st migration

-- upgrade      # Denoting all sql commands after this line are upgrade commands
SQL Commands;   # CREATE TABLE, or ALTER TABLE, or DROP TABLE
SQL Commands;
SQL Commands;

-- downgrade    # Denoting all sql commands after this line are downgrade commands
SQL Commands;   # DROP TABLE, or ALTER TABLe, or CREATE TABLE
SQL Commands;
SQL Commands;
<<FileEnd

NOTE: This script can't take care of conflicting migrations yet. So please make sure you always take a pull from 
develop branch, before generating migration. Or even better would be to generate migration only on develop branch.

"""


def read_all_tenant_db_creds():
    tenant_db_creds = []

    conn = psycopg2.connect(dsn=os.environ.get("DATABASE_URL"))
    try:
        with conn:
            with conn.cursor() as cursor:
                # TODO: Provide a way to inject tenant_database credentials from other sources
                cursor.execute(
                    "SELECT db_user, db_password, db_host, db_port, db_name, db_schema FROM tenant_db_config WHERE "
                    "user_type='admin';")
                all_tenant_db_creds = cursor.fetchall()
                for db_creds in all_tenant_db_creds:
                    tenant_db_creds.append(
                        dict(db_user=db_creds[0], db_password=db_creds[1], db_host=db_creds[2], db_port=db_creds[3],
                             db_name=db_creds[4], db_schema=db_creds[5]))
    finally:
        conn.close()

    return tenant_db_creds


def dump_schema(database_uri):
    dump_schema_command = "pg_dump --format=plain --encoding=UTF8 --schema-only --no-privileges --no-owner"


if __name__ == '__main__':
    command = sys.argv[1]

    if command == "touch":
        if len(sys.argv) < 3:
            print("Please pass a short name for migration file to generate")
            exit(1)
        migration_description = sys.argv[2:]
        migration_description = "_".join(migration_description)
        MigrationDirectory.create_blank_migration_file(migration_description)

    elif command == "init":
        Database.init_migration(tenant_db_creds=read_all_tenant_db_creds())

    elif command in ("upgrade", "downgrade"):
        Database.run_migrations(command, tenant_db_creds=read_all_tenant_db_creds())

    else:
        print("Invalid command passed")
        exit(1)
