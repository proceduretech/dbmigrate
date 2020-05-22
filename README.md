This package is to manage database migrations using plain SQL files on multiple databases or schema. Currently supports only Postgres.

It includes following operations:

    - Command to generate blank migration file, with given name
    - Command to initialize the migration on one or more fresh databases
    - Command to apply the unapplied migrations on one or more databases.

This package takes care of generating a migration file in a specific template, which is understood by the package,
to apply the migration. It's suggested to not generate a migration file manually, or tweak the migration file
template that is generated.
