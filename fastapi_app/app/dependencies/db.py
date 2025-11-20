from typing import AsyncGenerator 
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import AsyncSessionLocal


# 의존성 주입 (Dependency Injection)

# MySQL 의존성 주입
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()