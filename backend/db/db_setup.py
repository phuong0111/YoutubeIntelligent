import sqlite3
import os
import json
import threading
from typing import Dict, Any, Optional

class DatabaseManager:
    """
    Handles all database operations for the YouTube analysis server.
    Thread-safe implementation using thread-local storage.
    """
    def __init__(self, db_path: str = "db/youtube_analysis.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.local = threading.local()
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Initialize the database connection and create tables if they don't exist."""
        try:
            # Create the database directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            
            # Connect to the database in the main thread for initialization
            conn = sqlite3.connect(self.db_path)
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Create cursor
            cursor = conn.cursor()
            
            # Load and execute schema
            with open('db/schema.sql', 'r') as f:
                schema = f.read()
                conn.executescript(schema)
            
            conn.commit()
            conn.close()
            print(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def close(self) -> None:
        """Close the database connection for the current thread."""
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None
            self.local.cursor = None
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get the database connection for the current thread.
        Creates a new connection if one doesn't exist.
        
        Returns:
            SQLite connection object
        """
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.execute("PRAGMA foreign_keys = ON")
            self.local.cursor = self.local.conn.cursor()
        return self.local.conn
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            SQLite cursor object
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def execute_many(self, query: str, params_list: list) -> None:
        """
        Execute a SQL query with multiple parameter sets.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """
        Execute a query and fetch one result.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Single result row as tuple, or None if no result
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def fetchall(self, query: str, params: tuple = ()) -> list:
        """
        Execute a query and fetch all results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows as tuples
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert data into a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
            
        Returns:
            ID of the inserted row
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.execute(query, tuple(data.values()))
        self.local.conn.commit()
        return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: tuple) -> int:
        """
        Update data in a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values to update
            where_clause: WHERE clause for the update
            where_params: Parameters for the WHERE clause
            
        Returns:
            Number of rows affected
        """
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = tuple(data.values()) + where_params
        cursor = self.execute(query, params)
        self.local.conn.commit()
        return cursor.rowcount
    
    def delete(self, table: str, where_clause: str, where_params: tuple) -> int:
        """
        Delete data from a table.
        
        Args:
            table: Table name
            where_clause: WHERE clause for the delete
            where_params: Parameters for the WHERE clause
            
        Returns:
            Number of rows affected
        """
        query = f"DELETE FROM {table} WHERE {where_clause}"
        cursor = self.execute(query, where_params)
        self.local.conn.commit()
        return cursor.rowcount

    def create_task(self, task_type: str, entity_id: Optional[int] = None, 
                  entity_type: Optional[str] = None) -> int:
        """
        Create a new task entry.
        
        Args:
            task_type: Type of task ('scrape', 'download', 'transcribe', 'analyze')
            entity_id: ID of the related entity
            entity_type: Type of the related entity
            
        Returns:
            ID of the created task
        """
        data = {
            "task_type": task_type,
            "status": "pending"
        }
        
        if entity_id is not None:
            data["entity_id"] = entity_id
        
        if entity_type is not None:
            data["entity_type"] = entity_type
        
        return self.insert("tasks", data)
    
    def update_task_status(self, task_id: int, status: str, 
                         error_message: Optional[str] = None) -> None:
        """
        Update a task's status.
        
        Args:
            task_id: ID of the task to update
            status: New status ('pending', 'in_progress', 'completed', 'failed')
            error_message: Error message if the task failed
        """
        data = {
            "status": status,
            "updated_at": "CURRENT_TIMESTAMP"
        }
        
        if error_message is not None:
            data["error_message"] = error_message
        
        self.update("tasks", data, "id = ?", (task_id,))

# Create database schema file from SQL string
def create_schema_file(schema_content: str, file_path: str = "schema.sql") -> None:
    """
    Create the database schema file from the provided SQL content.
    
    Args:
        schema_content: SQL schema content
        file_path: Path to save the schema file
    """
    try:
        with open(file_path, 'w') as f:
            f.write(schema_content)
        print(f"Schema file created at {file_path}")
    except Exception as e:
        print(f"Error creating schema file: {e}")