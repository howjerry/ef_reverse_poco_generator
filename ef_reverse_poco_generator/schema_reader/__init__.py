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
    logger.debug(f"DB object attributes: {dir(db)}")
    
    if db_type in ['MySQLConnection', 'CMySQLConnection']:
        reader = MySQLSchemaReader(db, naming_convention)
    elif db_type == 'connection' and hasattr(db, 'info'):  # PostgreSQL
        reader = PostgreSQLSchemaReader(db, naming_convention)
    elif db_type == 'Connection' and hasattr(db, 'getinfo'):  # SQL Server
        reader = SQLServerSchemaReader(db, naming_convention)
    elif db_type == 'Connection' and hasattr(db, 'cursor'):  # SQLite
        reader = SQLiteSchemaReader(db, naming_convention)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
    
    return reader.read_schema()