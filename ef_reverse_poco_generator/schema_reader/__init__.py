# schema_reader/__init__.py
import logging
from .mysql import MySQLSchemaReader
from .postgresql import PostgreSQLSchemaReader
from .sqlserver import SQLServerSchemaReader
from .sqlite import SQLiteSchemaReader

logger = logging.getLogger(__name__)

def read_schema(db, naming_convention='original'):
    db_type = type(db).__name__
    logger.info(f"Reading schema for database type: {db_type}")
    
    if db_type in ['MySQLConnection', 'CMySQLConnection']:
        return MySQLSchemaReader(db, naming_convention).read_schema()
    elif db_type == 'connection' and hasattr(db, 'info'):  # PostgreSQL
        return PostgreSQLSchemaReader(db, naming_convention).read_schema()
    elif db_type == 'Connection' and hasattr(db, 'getinfo'):  # SQL Server
        return SQLServerSchemaReader(db, naming_convention).read_schema()
    elif db_type == 'Connection' and hasattr(db, 'cursor'):  # SQLite
        return SQLiteSchemaReader(db, naming_convention).read_schema()
    else:
        raise ValueError(f"Unsupported database type: {db_type}")