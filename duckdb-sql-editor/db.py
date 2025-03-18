import os
from pathlib import Path
import duckdb
from typing import Optional, Tuple

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

# Global instance
db = DatabaseManager()
