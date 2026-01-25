#!/usr/bin/env python3
"""
Script to set up the test database.

This script creates a separate test database (shark_fin_test) for running tests.
Tests will use PostgreSQL instead of SQLite to match the production environment
and support PostgreSQL-specific features like JSONB.

Usage:
    python scripts/setup_test_db.py
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError


def create_test_database():
    """Create the test database if it doesn't exist."""
    # Connect to the default postgres database to create our test database
    # Use 'postgres' as hostname when running inside Docker
    admin_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sharkfin:sharkfin@postgres:5432/postgres"
    )

    # Extract connection info to create test database URL
    # Default test database will be shark_fin_test
    test_db_name = "shark_fin_test"

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        with admin_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": test_db_name}
            )
            exists = result.fetchone() is not None

            if exists:
                print(f"Test database '{test_db_name}' already exists.")
            else:
                # Create the test database
                conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))
                print(f"Created test database '{test_db_name}'.")

    except ProgrammingError as e:
        print(f"Error creating test database: {e}")
        sys.exit(1)
    finally:
        admin_engine.dispose()

    print("\nTest database setup complete!")
    print(f"Test database URL: postgresql://sharkfin:sharkfin@localhost:5433/{test_db_name}")


if __name__ == "__main__":
    create_test_database()
