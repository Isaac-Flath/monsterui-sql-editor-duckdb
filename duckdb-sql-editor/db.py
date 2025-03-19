import os
from pathlib import Path
import duckdb
from typing import Optional, Tuple, List, Dict, Any
import shutil
from functools import wraps

DB_PATH = os.getenv("DUCKDB_PATH", "../duckdb-demo.duckdb")

def with_db_connection(default_value=None):
    """Decorator to handle database connections and error handling
    Args:
        default_value: Value to return if operation fails (default: None)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.connect(DB_PATH)
            try:
                result = func(self, *args, **kwargs)
                return result
            except Exception as e:
                print(f"Error in {func.__name__}: {e}")
                return default_value
        return wrapper
    return decorator

class DatabaseManager:
    def __init__(self):
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._db_path: Optional[Path] = None
    
    def connect(self, db_path: str) -> None:
        path = Path(db_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Database not found: {path}")
            
        if self._connection:
            self._connection.close()
            
        self._connection = duckdb.connect(str(path))
        self._db_path = path
    
    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        if not self._connection:
            raise RuntimeError("No active database connection")
        return self._connection
    
    @with_db_connection(default_value=[])
    def get_table_names(self) -> List[str]:
        """Get a list of table names from the database"""
        tables = self.connection.execute("SHOW TABLES").fetchall()
        return [table[0] for table in tables]

    @with_db_connection(default_value=[])
    def get_table_schema(self, table_name: str) -> List[Tuple]:
        """Get the schema for a specific table"""
        print(f"Fetching schema for table: {table_name}")
        schema = self.connection.execute(f"DESCRIBE {table_name}").fetchall()
        print(f"Schema for {table_name}: {len(schema)} columns")
        return schema

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query and return the results"""
        def get_results(connection):
            """Helper to execute query and get results with column names"""
            result = connection.execute(query).fetchall()
            columns = []
            if connection.description is not None:
                columns = [col[0] for col in connection.description]
            return {"columns": columns, "data": result}

        self.connect(DB_PATH)
        try:
            print(f"Executing query: {query[:100]}...")
            return get_results(self.connection)

        except (duckdb.ConnectionException, duckdb.IOException) as conn_error:
            print(f"Connection error: {conn_error}")
            print("Attempting to reset connection...")
            
            if self.reset_connection():
                try:
                    self.connect(DB_PATH)
                    print("Retrying query after connection reset...")
                    return get_results(self.connection)
                except duckdb.Error as retry_error:
                    print(f"Retry failed: {retry_error}")
                    return {"error": f"Query failed after connection reset: {retry_error}", "columns": [], "data": []}
            return {"error": f"Database connection error: {conn_error}", "columns": [], "data": []}

        except duckdb.Error as query_error:
            print(f"Query error: {query_error}")
            return {"error": str(query_error), "columns": [], "data": []}

        except Exception as unexpected_error:
            print(f"Unexpected error: {unexpected_error}")
            return {"error": f"An unexpected error occurred: {unexpected_error}", "columns": [], "data": []}

    def change_database(self, new_db_path: str) -> Tuple[bool, Optional[str]]:
        try:
            self.connect(new_db_path)
            self.connection.execute("SELECT 1").fetchall()  # Test connection
            return True, None
        except Exception as e:
            return False, str(e)

    def reset_connection(self) -> bool:
        """Reset the database connection if it becomes unresponsive"""
        print("Resetting database connection...")
        try:
            if self._connection is not None:
                try:
                    self._connection.close()
                except Exception as e:
                    print(f"Error closing existing connection: {e}")
                finally:
                    self._connection = None
            
            if self._db_path is None:
                print("No database path available for reset")
                return False
                
            print(f"Creating new database connection to {self._db_path}")
            self._connection = duckdb.connect(str(self._db_path), read_only=True)
            
            self._connection.execute("SELECT 1").fetchall()
            print("Connection reset successful")
            return True
        except Exception as e:
            print(f"Failed to reset connection: {e}")
            self._connection = None
            return False

    def close(self) -> None:
        """Close the database connection"""
        if self._connection is not None:
            print("Closing database connection")
            try:
                self._connection.close()
                self._connection = None
            except Exception as e:
                print(f"Error closing database connection: {e}")

    def cleanup_temp_directory(self) -> None:
        """Clean up the temporary database directory"""
        try:
            temp_dir = Path("./temp_db")
            if temp_dir.exists():
                print("Cleaning up temporary database directory")
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")

def cleanup_resources():
    """Close database connection and clean up resources"""
    db.close()
    db.cleanup_temp_directory()

# Global instance
db = DatabaseManager()
