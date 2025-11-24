"""
Database connection module for SQLite
Provides connection management and initialization
"""
import sqlite3
from pathlib import Path
from typing import Optional

from incident_iq.config import get_database_dir, get_database_name


def _get_default_db_path() -> Path:
    """
    Get default database path from configuration.
    Configuration loaded from pyproject.toml [tool.incident-iq] section
    """
    # Get database directory and name from config
    db_dir_name = get_database_dir()
    db_name = get_database_name()
    
    # Database directory is relative to package root (src/incident_iq)
    db_dir = Path(__file__).parent.parent / db_dir_name
    db_dir.mkdir(parents=True, exist_ok=True)
    
    return db_dir / db_name


# Database path - resolved relative to package structure and configuration
DB_PATH = _get_default_db_path()


def get_connection() -> sqlite3.Connection:
    """
    Get a SQLite database connection
    
    Creates the database file if it doesn't exist.
    Enables foreign keys and sets row factory for dict-like access.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Create connection using string path for sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # Enable foreign keys
    conn.execute('PRAGMA foreign_keys = ON')
    
    return conn


def init_db(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    """
    Initialize the database with all migration tables and seed data
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        sqlite3.Connection: Database connection object
    """
    global DB_PATH
    
    if db_path:
        DB_PATH = Path(db_path) if isinstance(db_path, str) else db_path
    
    conn = get_connection()
    
    # Step 1: Run migrations
    migration_dir = Path(__file__).parent.parent / 'migration'
    migration_files = sorted([f for f in migration_dir.glob('*.py') if f.name != '__init__.py'])
    
    print("\n" + "="*60)
    print("Running Migrations...")
    print("="*60)
    
    for migration_file in migration_files:
        try:
            # Read and execute the migration file
            migration_code = migration_file.read_text()
            migration_module = {}
            exec(migration_code, migration_module)
            
            # Call the run() function if it exists
            if 'run' in migration_module:
                migration_module['run'](conn)
                print(f"✓ Migration {migration_file.name} completed")
            else:
                print(f"⚠ Migration {migration_file.name} skipped (no run function)")
                
        except Exception as e:
            print(f"✗ Migration {migration_file.name} failed: {e}")
            conn.close()
            raise
    
    # Step 2: Run seeders
    seeder_dir = Path(__file__).parent.parent / 'seeders'
    seeder_files = sorted([f for f in seeder_dir.glob('*.py') if f.name != '__init__.py' and not f.name.endswith('.bak')])
    
    print("\n" + "="*60)
    print("Running Seeders...")
    print("="*60)
    
    for seeder_file in seeder_files:
        try:
            # Read and execute the seeder file
            seeder_code = seeder_file.read_text()
            seeder_module = {}
            exec(seeder_code, seeder_module)
            
            # Call the run() function if it exists
            if 'run' in seeder_module:
                seeder_module['run'](conn)
                print(f"✓ Seeder {seeder_file.name} completed")
            else:
                print(f"⚠ Seeder {seeder_file.name} skipped (no run function)")
                
        except Exception as e:
            print(f"✗ Seeder {seeder_file.name} failed: {e}")
            # Don't raise - continue with other seeders
            continue
    
    return conn


def close_connection(conn: sqlite3.Connection) -> None:
    """
    Close database connection
    
    Args:
        conn: Connection to close
    """
    if conn:
        conn.close()


def get_db_path() -> str:
    """Get the current database path as string"""
    return str(DB_PATH)


def set_db_path(path: str | Path) -> None:
    """Set a custom database path"""
    global DB_PATH
    DB_PATH = Path(path) if isinstance(path, str) else path
