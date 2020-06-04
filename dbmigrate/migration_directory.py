import os

from dbmigrate.migration_file import MigrationFile

migrations_directory = 'db_migrations/versions/'
schema_file_directory = 'db_migrations/'


class MigrationDirectory(object):
    @staticmethod
    def create_if_not_exists():
        if not os.path.exists(migrations_directory):
            os.makedirs(migrations_directory)

    @staticmethod
    def read_migrations_graph():
        upward_graph = dict()

        for f in os.listdir(migrations_directory):
            with open(os.path.join(migrations_directory, f), 'r') as file:
                file_content = file.read()
                revision = MigrationFile.read_revision_number(file_content)
                down_revision = MigrationFile.read_revision_number(file_content, down=True)
                if down_revision in upward_graph:
                    existing_up_revision = upward_graph[down_revision]
                    print("Found conflicting revision: %s and %s, branching from the same "
                          "revision: %s" % (existing_up_revision, revision, down_revision))
                    raise RuntimeError()
                upward_graph[down_revision] = revision

        graph = []
        next_node = ''
        while True:
            next_node = upward_graph.get(next_node)
            if next_node is None:
                break
            graph.append(next_node)
        return graph

    @classmethod
    def prepare_migration_graph_to_apply(cls, last_version):
        graph = cls.read_migrations_graph()
        if last_version is None:
            start_version_index = 0
        else:
            last_version_index = graph.index(last_version)
            if last_version_index == -1:
                print("Can't find the revision: {0}".format(last_version))
                return
            if last_version_index == len(graph) - 1:
                return
            start_version_index = last_version_index + 1
        return graph[start_version_index:]

    @staticmethod
    def get_migration_file_path(migration_file_name):
        file_path = os.path.join(migrations_directory, '{0}.sql'.format(migration_file_name))
        return file_path

    @staticmethod
    def get_schema_file_path(schema_file_name):
        file_path = os.path.join(schema_file_directory, '{0}.sql'.format(schema_file_name))
        return file_path

    @classmethod
    def create_blank_migration_file(cls, description):
        graph = cls.read_migrations_graph()
        revision = MigrationFile.generate_migration_filename(description)
        down_revision = graph[-1] if len(graph) > 0 else ''

        file_path = cls.get_migration_file_path(revision)
        MigrationFile.write_migration_template_to_file(file_path, revision, down_revision)
