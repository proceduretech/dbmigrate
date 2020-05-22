import datetime
import re


class MigrationFile(object):
    revision_regex = re.compile(r"^-- revision:\s*?'([^']+)'$", re.M)
    down_revision_regex = re.compile(r"^-- down_revision:\s*?(?:'([^']*)'$)", re.M)
    upgrade_queries_regex = re.compile(".*?-- upgrade(.*)-- downgrade.*", re.DOTALL)
    downgrade_queries_regex = re.compile(".*?-- upgrade.*-- downgrade(.*)", re.DOTALL)

    revision_line = "-- revision: '{0}'\n"
    down_revision_line = "-- down_revision: '{0}'\n\n"
    upgrade_line = "-- upgrade\n\n"
    downgrade_line = "-- downgrade\n"

    @staticmethod
    def read_revision_number(migration_file_content, down=False):
        if not down:
            revision = MigrationFile.revision_regex.findall(migration_file_content)[0]
        else:
            revision = MigrationFile.down_revision_regex.findall(migration_file_content)[0]
        return revision

    @staticmethod
    def generate_migration_filename(name):
        name = re.sub(r"\s+", "_", name)
        name = name.lower()
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + name

    @staticmethod
    def write_migration_template_to_file(file_path, revision, down_revision):
        with open(file_path, 'w') as f:
            f.write(MigrationFile.revision_line.format(revision))
            f.write(MigrationFile.down_revision_line.format(down_revision))
            f.write(MigrationFile.upgrade_line)
            f.write(MigrationFile.downgrade_line)
            print("Created new migration file: %s" % f.name)

    @staticmethod
    def parse_file_and_read_migration_commands(migration_file, migration_direction):
        with open(migration_file, "r") as f:
            sql_commands = f.read()

        if migration_direction == 'upgrade':
            m = MigrationFile.upgrade_queries_regex.match(sql_commands)
        else:
            m = MigrationFile.downgrade_queries_regex.match(sql_commands)

        if not m:
            print("Migration file: {0} doesn't contain any valid migration".format(migration_file))
            return None

        sql_commands = m.group(1)
        return sql_commands
