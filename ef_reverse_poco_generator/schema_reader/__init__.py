# schema_reader/__init__.py
import logging
from .mysql import MySQLSchemaReader
from .postgresql import PostgreSQLSchemaReader
from .sqlserver import SQLServerSchemaReader
from .sqlite import SQLiteSchemaReader

logger = logging.getLogger(__name__)

def read_schema(db):
    db_type = type(db).__name__
    logger.info(f"Reading schema for database type: {db_type}")
    
    if db_type in ['MySQLConnection', 'CMySQLConnection']:
        return MySQLSchemaReader(db).read_schema()
    elif db_type == 'connection' and hasattr(db, 'info'):  # PostgreSQL
        return PostgreSQLSchemaReader(db).read_schema()
    elif db_type == 'Connection' and hasattr(db, 'getinfo'):  # SQL Server
        return SQLServerSchemaReader(db).read_schema()
    elif db_type == 'Connection' and hasattr(db, 'cursor'):  # SQLite
        return SQLiteSchemaReader(db).read_schema()
    else:
        raise ValueError(f"Unsupported database type: {db_type}")