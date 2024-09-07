# schema_reader/mysql.py
from .base import SchemaReader

class MySQLSchemaReader(SchemaReader):
    def __init__(self, db, naming_convention='original'):
        super().__init__(db)
        self.naming_convention = naming_convention
    
    def format_name(self, name):
        if self.naming_convention == 'camelcase':
            return ''.join(word.capitalize() for word in name.split('_'))
        return name
        
    def read_tables(self):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                TABLE_NAME, 
                TABLE_COMMENT
            FROM 
                INFORMATION_SCHEMA.TABLES
            WHERE 
                TABLE_SCHEMA = DATABASE()
        """)
        tables = {self.format_name(row['TABLE_NAME']): {'description': row['TABLE_COMMENT']} for row in cursor.fetchall()}
        cursor.close()
        return tables

    def read_columns(self):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                TABLE_NAME, 
                COLUMN_NAME, 
                DATA_TYPE, 
                IS_NULLABLE, 
                COLUMN_KEY,
                COLUMN_COMMENT
            FROM 
                INFORMATION_SCHEMA.COLUMNS
            WHERE 
                TABLE_SCHEMA = DATABASE()
        """)
        columns = {}
        for row in cursor.fetchall():
            if row['TABLE_NAME'] not in columns:
                columns[row['TABLE_NAME']] = []
            columns[row['TABLE_NAME']].append({
                'name': row['COLUMN_NAME'],
                'type': row['DATA_TYPE'],
                'nullable': row['IS_NULLABLE'] == 'YES',
                'primary_key': row['COLUMN_KEY'] == 'PRI',
                'description': row['COLUMN_COMMENT']
            })
        cursor.close()
        return columns

    def read_primary_keys(self):
        # Primary keys are already identified in read_columns for MySQL
        return {}

    def read_foreign_keys(self):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                TABLE_NAME, 
                COLUMN_NAME, 
                REFERENCED_TABLE_NAME, 
                REFERENCED_COLUMN_NAME,
                CONSTRAINT_NAME
            FROM 
                INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE 
                REFERENCED_TABLE_SCHEMA = DATABASE() 
                AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        foreign_keys = {}
        for row in cursor.fetchall():
            if row['TABLE_NAME'] not in foreign_keys:
                foreign_keys[row['TABLE_NAME']] = []
            foreign_keys[row['TABLE_NAME']].append({
                'column': row['COLUMN_NAME'],
                'referenced_table': row['REFERENCED_TABLE_NAME'],
                'referenced_column': row['REFERENCED_COLUMN_NAME'],
                'description': f"Foreign key constraint {row['CONSTRAINT_NAME']} referencing {row['REFERENCED_TABLE_NAME']}.{row['REFERENCED_COLUMN_NAME']}"
            })
        cursor.close()
        return foreign_keys

    def read_procedures(self):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                ROUTINE_NAME, 
                ROUTINE_DEFINITION,
                ROUTINE_COMMENT
            FROM 
                INFORMATION_SCHEMA.ROUTINES
            WHERE 
                ROUTINE_SCHEMA = DATABASE() 
                AND ROUTINE_TYPE = 'PROCEDURE'
        """)
        procedures = {row['ROUTINE_NAME']: {
            'definition': row['ROUTINE_DEFINITION'],
            'description': row['ROUTINE_COMMENT']
        } for row in cursor.fetchall()}
        cursor.close()
        return procedures