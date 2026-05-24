"""Database schema migrations for Zero2Print PrintManager."""
import sqlite3
import os
from pathlib import Path


def get_db_path():
    """Get the database path."""
    return os.path.join("data", "database.sqlite")


def migration_add_filament_fields(conn):
    """Add filament questionnaire fields to print_jobs table."""
    cursor = conn.cursor()
    
    fields = [
        ("filament_use_case", "VARCHAR"),
        ("filament_temperature", "VARCHAR"),
        ("filament_finish", "VARCHAR"),
    ]
    
    for column, sql_type in fields:
        try:
            cursor.execute(f"ALTER TABLE print_jobs ADD COLUMN {column} {sql_type}")
            print(f"✓ Added column '{column}' to print_jobs")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  Column '{column}' already exists")
            else:
                raise
    
    conn.commit()


def run_migrations():
    """Run all pending migrations."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    print("Running database migrations...")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Migration 1: Add filament questionnaire fields
        migration_add_filament_fields(conn)
        
        conn.close()
        print("✓ All migrations completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


if __name__ == "__main__":
    run_migrations()
