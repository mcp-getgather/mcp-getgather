import os
import sqlite3
from pathlib import Path

from getgather.config import settings


def ensure_db_directory_exists():
    """Ensure the directory for the database file exists."""
    db_dir = os.path.dirname(settings.database_path)
    Path(db_dir).mkdir(parents=True, exist_ok=True)


def run_migration():
    """Run database migrations."""
    print(f"Running migrations on database: {settings.database_path}")

    # Ensure the database directory exists
    ensure_db_directory_exists()

    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(settings.database_path)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # Read and execute schema file
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r") as f:
            schema_sql = f.read()

        # Execute the entire schema as a script
        cursor = conn.cursor()
        cursor.executescript(schema_sql)

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
