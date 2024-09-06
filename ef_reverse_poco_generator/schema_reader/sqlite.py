# schema_reader/sqlite.py
from .base import SchemaReader

class SQLiteSchemaReader(SchemaReader):
    def read_tables(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0]: {'description': ''} for row in cursor.fetchall()}  # SQLite doesn't support table comments natively
        cursor.close()
        return tables

    def read_columns(self):
        cursor = self.db.cursor()
        columns = {}
        for table_name in self.read_tables().keys():
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns[table_name] = []
            for column in cursor.fetchall():
                columns[table_name].append({
                    'name': column[1],
                    'type': column[2],
                    'nullable': not column[3],
                    'primary_key': column[5] == 1,
                    'description': ''  # SQLite doesn't support column comments natively
                })
        cursor.close()
        return columns

    def read_primary_keys(self):
        # Primary keys are already identified in read_columns for SQLite
        return {}

    def read_foreign_keys(self):
        cursor = self.db.cursor()
        foreign_keys = {}
        for table_name in self.read_tables().keys():
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys[table_name] = []
            for fk in cursor.fetchall():
                foreign_keys[table_name].append({
                    'column': fk[3],
                    'referenced_table': fk[2],
                    'referenced_column': fk[4],
                    'description': f"Foreign key constraint referencing {fk[2]}.{fk[4]}"
                })
        cursor.close()
        return foreign_keys

    def read_procedures(self):
        # SQLite doesn't support stored procedures
        return {}