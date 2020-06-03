#!/usr/bin/env python
import json
import os

import click

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


def read_all_db_creds():
    all_db_creds = []

    if os.environ.get("DATABASE_URI"):
        all_db_creds.append(
            dict(database_uri=os.environ.get("DATABASE_URI"), db_schema=os.environ.get("SCHEMA", 'public')))

    elif os.environ.get("DB_USER"):
        all_db_creds.append(dict(db_user=os.environ.get("DB_USER"), db_password=os.environ.get("DB_PASSWORD"),
                                 db_host=os.environ.get("DB_HOST"), db_port=os.environ.get("DB_PORT", 5432),
                                 db_name=os.environ.get("DB_NAME"), db_schema=os.environ.get("SCHEMA", 'public')))

    else:
        # Supports migrations on multiple databases
        with open("db_creds.json", 'r') as db_creds:
            database_creds = json.load(db_creds)
            for db_creds in database_creds:
                all_db_creds.append(dict(db_user=db_creds['db_user'], db_password=db_creds['db_password'],
                                         db_host=db_creds['db_host'], db_port=db_creds.get('db_port', 5432),
                                         db_name=db_creds['db_name'], db_schema=db_creds.get('db_schema', 'public')))

    return all_db_creds


@click.group()
@click.pass_context
def main(ctx):
    pass


@main.command()
@click.option('--name', default=None,
              help="Give short name (space, or underscore separated) for the migration file to be generated, "
                   "while using 'touch' command")
def touch(name):
    """Creates a blank migration file"""
    if not name:
        click.echo("Please pass a short name for migration file to be generated")
        exit(1)
    migration_description = "_".join(name)
    MigrationDirectory.create_blank_migration_file(migration_description)


@main.command()
def init():
    """Initializes migration table on database"""
    Database.init_migration(db_creds=read_all_db_creds())


@main.command()
def upgrade():
    """Apply remaining un-applied forward migrations"""
    Database.run_migrations('upgrade', db_creds=read_all_db_creds())


@main.command()
def downgrade():
    """Rollbacks the last applied migrations"""
    Database.run_migrations('downgrade', db_creds=read_all_db_creds())


@main.command()
def dump():
    """Takes table structure dump for the given database and schema to schema.sql file"""
    db_creds = read_all_db_creds()[0]
    db_schema = db_creds['db_schema']
    if 'database_uri' in db_creds:
        database_uri = db_creds['database_uri']
    else:
        database_uri = "postgres://%(db_user)s:%(db_password)s@%(db_host)s:%(db_port)s/%(db_name)s" % db_creds
    Database.dump(database_uri, db_schema)
