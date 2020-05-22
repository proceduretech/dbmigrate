This package is to manage database migrations using plain SQL files on multiple databases or schema. Currently supports only Postgres.

It provides `dbmigrate` cli tool to perform following operations:

    - generate blank migration file, with given name
    - initialize the migration on one or more fresh databases
    - apply the unapplied migrations on one or more databases
    - rollback the last applied migrations on one or more databases

Usage:

    - pip install dbmigrate-treebo
    - dbmigrate

This package takes care of generating a migration file in a specific template, which is understood by the package,
to apply the migration. It's suggested to not generate a migration file manually, or tweak the migration file
template that is generated.