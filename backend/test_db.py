import asyncio
import os

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.mark.asyncio
async def test_connection():
    database_url = os.getenv("DATABASE_URL") or "postgresql+asyncpg://postgres:postgres@localhost:5432/inventory"
    print(f"Testing connection to: {database_url}")
    
    engine = create_async_engine(database_url)
    
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1"))
            print("Connection successful!")
            print(f"Result: {result.scalar()}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())
