#!/usr/bin/env python3
"""
Diagnostic script to check database state.
Run: docker compose exec -w /app backend python scripts/check_db.py
"""
import asyncio
import sys
sys.path.insert(0, "/app")
from sqlalchemy import text
from app.db.session import engine
from app.db.base import Base
from app.models import *  # noqa: F403 - import all models to register them with Base.metadata


async def check_db():
    print("=" * 60)
    print("DATABASE DIAGNOSTIC REPORT")
    print("=" * 60)

    # 1. Check connection
    print("\n[1] Checking database connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"  Connection OK: {result.scalar()}")
    except Exception as e:
        print(f"  Connection FAILED: {e}")
        return

    # 2. Check existing tables
    print("\n[2] Checking existing tables...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            )
            tables = [row[0] for row in result.fetchall()]
            if tables:
                print(f"  Found {len(tables)} tables:")
                for t in tables:
                    row_count = await conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
                    count = row_count.scalar()
                    print(f"    - {t}: {count} rows")
            else:
                print("  No tables found!")
    except Exception as e:
        print(f"  Table check FAILED: {e}")

    # 3. Check model registration
    print("\n[3] Checking SQLAlchemy model registration...")
    mapped_tables = list(Base.metadata.tables.keys())
    if mapped_tables:
        print(f"  {len(mapped_tables)} models registered in Base.metadata:")
        for t in sorted(mapped_tables):
            print(f"    - {t}")
    else:
        print("  WARNING: No tables in Base.metadata!")

    # 4. Try to create tables
    print("\n[4] Attempting to create tables...")
    if not mapped_tables:
        print("  SKIPPED: No models to create.")
    else:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"  Tables created successfully: {len(mapped_tables)} tables")
        except Exception as e:
            print(f"  Create FAILED: {e}")

    # 5. Verify tables after creation
    print("\n[5] Final table verification...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"  Tables in database: {len(tables)}")
            for t in sorted(mapped_tables):
                status = "PRESENT" if t in tables else "MISSING"
                print(f"    - {t}: {status}")
    except Exception as e:
        print(f"  Verification FAILED: {e}")

    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_db())
