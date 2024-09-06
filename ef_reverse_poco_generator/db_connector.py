# db_connector.py
import mysql.connector
import psycopg2
import pyodbc
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def connect(conn_params):
    try:
        db_type = conn_params.pop('db_type')
        logger.info(f"Attempting to connect to {db_type} database")
        logger.debug(f"Connection parameters: {conn_params}")
        
        if db_type == "mysql":
            connection = mysql.connector.connect(**conn_params)
        elif db_type == "postgresql":
            connection = psycopg2.connect(**conn_params)
        elif db_type == "sqlserver":
            connection = pyodbc.connect(**conn_params)
        elif db_type == "sqlite":
            connection = sqlite3.connect(conn_params['database'])
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        logger.info("Database connection successful")
        return connection
    except mysql.connector.Error as e:
        logger.error(f"MySQL Error: {e}")
        if e.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Access denied. Check your username and password.")
        elif e.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logger.error("Database does not exist.")
        else:
            logger.error(f"Error code: {e.errno}")
            logger.error(f"SQL State: {e.sqlstate}")
        raise ConnectionError(f"Failed to connect to the database: {str(e)}")
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise ConnectionError(f"Failed to connect to the database: {str(e)}")