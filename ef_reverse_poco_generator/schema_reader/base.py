# schema_reader/base.py
from abc import ABC, abstractmethod

class SchemaReader(ABC):
    def __init__(self, db, naming_convention='original'):
        self.db = db
        self.naming_convention = naming_convention

    @abstractmethod
    def read_tables(self):
        pass

    @abstractmethod
    def read_columns(self):
        pass

    @abstractmethod
    def read_primary_keys(self):
        pass

    @abstractmethod
    def read_foreign_keys(self):
        pass

    @abstractmethod
    def read_procedures(self):
        pass

    def read_schema(self):
        schema = {'tables': {}, 'procedures': {}}
        
        tables = self.read_tables()
        for table_name, table_info in tables.items():
            schema['tables'][table_name] = {
                'columns': [],
                'foreign_keys': [],
                'description': table_info.get('description', '')
            }

        columns = self.read_columns()
        for table_name, table_columns in columns.items():
            schema['tables'][table_name]['columns'] = table_columns

        primary_keys = self.read_primary_keys()
        for table_name, pk_columns in primary_keys.items():
            schema['tables'][table_name]['primary_key'] = pk_columns

        foreign_keys = self.read_foreign_keys()
        for table_name, fks in foreign_keys.items():
            schema['tables'][table_name]['foreign_keys'] = fks

        schema['procedures'] = self.read_procedures()

        return schema