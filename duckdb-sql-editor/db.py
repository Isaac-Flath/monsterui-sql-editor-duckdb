import os
from pathlib import Path
import duckdb
from typing import Optional, Tuple
import shutil

DB_PATH = os.getenv("DUCKDB_PATH", "../duckdb-demo.duckdb")

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
            
        self._connection = duckdb.connect(str(path), read_only=True)
        self._db_path = path
    
    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        if not self._connection:
            raise RuntimeError("No active database connection")
        return self._connection
    
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
                
            # Create a new connection
            print(f"Creating new database connection to {self._db_path}")
            self._connection = duckdb.connect(str(self._db_path), read_only=True)
            
            # Test the connection
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
