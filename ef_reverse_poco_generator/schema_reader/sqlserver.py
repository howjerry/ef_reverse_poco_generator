# schema_reader/sqlserver.py
from .base import SchemaReader

class SQLServerSchemaReader(SchemaReader):
    def read_tables(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                t.name AS table_name,
                CAST(p.value AS NVARCHAR(MAX)) AS table_description
            FROM 
                sys.tables t
            LEFT JOIN 
                sys.extended_properties p ON p.major_id = t.object_id AND p.minor_id = 0 AND p.name = 'MS_Description'
        """)
        tables = {row.table_name: {'description': row.table_description or ''} for row in cursor.fetchall()}
        cursor.close()
        return tables

    def read_columns(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                t.name AS table_name,
                c.name AS column_name,
                tp.name AS data_type,
                c.is_nullable,
                c.is_identity,
                CAST(ep.value AS NVARCHAR(MAX)) AS column_description
            FROM 
                sys.tables t
            INNER JOIN 
                sys.columns c ON t.object_id = c.object_id
            INNER JOIN 
                sys.types tp ON c.user_type_id = tp.user_type_id
            LEFT JOIN 
                sys.extended_properties ep ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
        """)
        columns = {}
        for row in cursor.fetchall():
            if row.table_name not in columns:
                columns[row.table_name] = []
            columns[row.table_name].append({
                'name': row.column_name,
                'type': row.data_type,
                'nullable': row.is_nullable,
                'identity': row.is_identity,
                'description': row.column_description or ''
            })
        cursor.close()
        return columns

    def read_primary_keys(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                t.name AS table_name,
                c.name AS column_name,
                ic.key_ordinal
            FROM 
                sys.tables t
            INNER JOIN 
                sys.indexes i ON t.object_id = i.object_id
            INNER JOIN 
                sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN 
                sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE 
                i.is_primary_key = 1
            ORDER BY
                t.name, ic.key_ordinal
        """)
        primary_keys = {}
        for row in cursor.fetchall():
            if row.table_name not in primary_keys:
                primary_keys[row.table_name] = []
            primary_keys[row.table_name].append(row.column_name)
        cursor.close()
        return primary_keys 

    def read_foreign_keys(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                t.name AS table_name,
                c.name AS column_name,
                rt.name AS referenced_table_name,
                rc.name AS referenced_column_name,
                fk.name AS constraint_name
            FROM 
                sys.foreign_keys fk
            INNER JOIN 
                sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN 
                sys.tables t ON fk.parent_object_id = t.object_id
            INNER JOIN 
                sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
            INNER JOIN 
                sys.tables rt ON fk.referenced_object_id = rt.object_id
            INNER JOIN 
                sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
        """)
        foreign_keys = {}
        for row in cursor.fetchall():
            if row.table_name not in foreign_keys:
                foreign_keys[row.table_name] = []
            foreign_keys[row.table_name].append({
                'column': row.column_name,
                'referenced_table': row.referenced_table_name,
                'referenced_column': row.referenced_column_name,
                'description': f"Foreign key constraint {row.constraint_name} referencing {row.referenced_table_name}.{row.referenced_column_name}"
            })
        cursor.close()
        return foreign_keys

    def read_procedures(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                p.name AS procedure_name,
                m.definition AS procedure_definition,
                CAST(ep.value AS NVARCHAR(MAX)) AS procedure_description
            FROM 
                sys.procedures p
            INNER JOIN 
                sys.sql_modules m ON p.object_id = m.object_id
            LEFT JOIN 
                sys.extended_properties ep ON p.object_id = ep.major_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
        """)
        procedures = {}
        for row in cursor.fetchall():
            procedure_name = row.procedure_name
            procedures[procedure_name] = {
                'definition': row.procedure_definition,
                'description': row.procedure_description or '',
                'parameters': self.read_procedure_parameters(procedure_name)
            }
        cursor.close()
        return procedures

    def read_procedure_parameters(self, procedure_name):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                p.name AS parameter_name,
                t.name AS parameter_type,
                p.is_output AS is_output
            FROM 
                sys.parameters p
            INNER JOIN 
                sys.procedures sp ON p.object_id = sp.object_id
            INNER JOIN 
                sys.types t ON p.user_type_id = t.user_type_id
            WHERE 
                sp.name = ?
            ORDER BY 
                p.parameter_id
        """, (procedure_name,))
        
        parameters = []
        for row in cursor.fetchall():
            parameters.append({
                'name': row.parameter_name,
                'type': row.parameter_type,
                'mode': 'OUT' if row.is_output else 'IN'
            })
        
        cursor.close()
        return parameters