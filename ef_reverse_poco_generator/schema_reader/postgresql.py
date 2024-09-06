# schema_reader/postgresql.py
from .base import SchemaReader

class PostgreSQLSchemaReader(SchemaReader):
    def read_tables(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                table_name,
                obj_description(('"' || table_schema || '"."' || table_name || '"')::regclass, 'pg_class') as table_description
            FROM 
                information_schema.tables
            WHERE 
                table_schema = 'public'
        """)
        tables = {row[0]: {'description': row[1] or ''} for row in cursor.fetchall()}
        cursor.close()
        return tables

    def read_columns(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default,
                col_description(('"' || table_schema || '"."' || table_name || '"')::regclass, ordinal_position) as column_description
            FROM 
                information_schema.columns
            WHERE 
                table_schema = 'public'
        """)
        columns = {}
        for row in cursor.fetchall():
            if row[0] not in columns:
                columns[row[0]] = []
            columns[row[0]].append({
                'name': row[1],
                'type': row[2],
                'nullable': row[3] == 'YES',
                'default': row[4],
                'description': row[5] or ''
            })
        cursor.close()
        return columns

    def read_primary_keys(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name
            FROM 
                information_schema.table_constraints tc
            JOIN 
                information_schema.key_column_usage kcu
            ON 
                tc.constraint_name = kcu.constraint_name
            WHERE 
                tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
        """)
        primary_keys = {}
        for row in cursor.fetchall():
            if row[0] not in primary_keys:
                primary_keys[row[0]] = []
            primary_keys[row[0]].append(row[1])
        cursor.close()
        return primary_keys

    def read_foreign_keys(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM 
                information_schema.table_constraints AS tc 
            JOIN 
                information_schema.key_column_usage AS kcu
            ON 
                tc.constraint_name = kcu.constraint_name
            JOIN 
                information_schema.constraint_column_usage AS ccu
            ON 
                ccu.constraint_name = tc.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
        """)
        foreign_keys = {}
        for row in cursor.fetchall():
            if row[0] not in foreign_keys:
                foreign_keys[row[0]] = []
            foreign_keys[row[0]].append({
                'column': row[1],
                'referenced_table': row[2],
                'referenced_column': row[3],
                'description': f"Foreign key constraint {row[4]} referencing {row[2]}.{row[3]}"
            })
        cursor.close()
        return foreign_keys

    def read_procedures(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                proname,
                prosrc,
                description
            FROM 
                pg_proc
            LEFT JOIN 
                pg_description ON pg_proc.oid = pg_description.objoid
            WHERE 
                pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        """)
        procedures = {row[0]: {
            'definition': row[1],
            'description': row[2] or ''
        } for row in cursor.fetchall()}
        cursor.close()
        return procedures