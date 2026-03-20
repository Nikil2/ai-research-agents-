#!/usr/bin/env python3
"""Initialize database with 5-table schema."""
from database.db import init_db

if __name__ == "__main__":
    init_db()
    print("✅ Schema migration complete!")
