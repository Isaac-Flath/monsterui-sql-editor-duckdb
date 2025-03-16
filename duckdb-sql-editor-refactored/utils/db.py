#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database utilities for DuckDB SQL Editor
"""

import os
import duckdb
import atexit
from pathlib import Path

# Global connection object
_db_connection = None

def get_connection():
    """Get a connection to the DuckDB database using a singleton pattern"""
    global _db_connection
    
    try:
        if _db_connection is None:
            db_path = Path(os.getenv("DUCKDB_PATH", "../duckdb-demo.duckdb")).resolve()
            if not db_path.exists():
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            # Connect to the database (read-only mode)
            print(f"Opening new database connection to {db_path} (singleton)")
            _db_connection = duckdb.connect(str(db_path), read_only=True)
        
        return _db_connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def reset_with_new_db(new_db_path):
    """Reset the connection with a new database file path"""
    global _db_connection
    
    try:
        # Close existing connection if it exists
        if _db_connection is not None:
            _db_connection.close()
            _db_connection = None
        
        # Update environment variable
        os.environ["DUCKDB_PATH"] = str(new_db_path)
        
        # Create a new connection
        return get_connection()
    except Exception as e:
        print(f"Error resetting database connection: {e}")
        raise

def reset_connection():
    """Reset the database connection"""
    global _db_connection
    
    try:
        if _db_connection is not None:
            _db_connection.close()
            _db_connection = None
        return get_connection()
    except Exception as e:
        print(f"Error resetting connection: {e}")
        raise

def get_table_names():
    """Get a list of all tables in the database"""
    try:
        conn = get_connection()
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [row[0] for row in result]
    except Exception as e:
        print(f"Error getting table names: {e}")
        return []

def get_table_schema(table_name):
    """Get the schema for a specific table"""
    try:
        conn = get_connection()
        result = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return [{"name": row[1], "type": row[2], "notnull": row[3], "pk": row[5]} for row in result]
    except Exception as e:
        print(f"Error getting schema for table {table_name}: {e}")
        return []

def execute_query(query):
    """Execute a SQL query and return the results"""
    try:
        conn = get_connection()
        result = conn.execute(query)
        
        # Get column names
        columns = [col[0] for col in result.description]
        
        # Fetch all rows
        data = result.fetchall()
        
        # Convert rows to list of dicts
        rows = []
        for row in data:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            rows.append(row_dict)
        
        return {"error": None, "columns": columns, "data": rows}
    except Exception as e:
        print(f"Error executing query: {e}")
        
        # Try to reset connection and retry once
        try:
            reset_connection()
            conn = get_connection()
            result = conn.execute(query)
            
            # Get column names
            columns = [col[0] for col in result.description]
            
            # Fetch all rows
            data = result.fetchall()
            
            # Convert rows to list of dicts
            rows = []
            for row in data:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                rows.append(row_dict)
            
            return {"error": None, "columns": columns, "data": rows}
        except Exception as retry_error:
            print(f"Retry failed: {retry_error}")
            return {"error": f"Query failed: {e}", "columns": [], "data": []}

def cleanup_resources():
    """Clean up database resources on application exit"""
    global _db_connection
    
    if _db_connection is not None:
        print("Closing database connection")
        _db_connection.close()
        _db_connection = None

# Register cleanup function to run on exit
atexit.register(cleanup_resources) 