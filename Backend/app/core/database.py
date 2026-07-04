"""
HRMS Database Configuration
Async SQLAlchemy engine, session factory, and dependency injection.
Production-grade connection pooling with health checks.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class DatabaseManager:
    """Manages async database engine and session lifecycle."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._settings = None

    def _get_settings(self):
        """Lazy-load settings to avoid import-time crashes."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    async def connect(self) -> None:
        """Initialize the async engine and session factory."""
        settings = self._get_settings()
        connect_args: dict[str, Any] = {}
        if settings.is_testing:
            connect_args["server_settings"] = {"search_path": "hrms_test, public"}

        pool_kwargs: dict[str, Any] = {}
        if settings.ENVIRONMENT.value == "testing":
            pool_kwargs["poolclass"] = NullPool
        else:
            pool_kwargs.update(
                {
                    "pool_size": settings.DB_POOL_SIZE,
                    "max_overflow": settings.DB_MAX_OVERFLOW,
                    "pool_timeout": settings.DB_POOL_TIMEOUT,
                    "pool_recycle": settings.DB_POOL_RECYCLE,
                    "pool_pre_ping": True,
                }
            )

        self._engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            connect_args=connect_args,
            **pool_kwargs,
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info(
            "Database engine created: pool_size=%d, max_overflow=%d",
            settings.DB_POOL_SIZE,
            settings.DB_MAX_OVERFLOW,
        )

    async def disconnect(self) -> None:
        """Dispose of the engine and release all connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine disposed")

    async def health_check(self) -> bool:
        """Verify database connectivity."""
        if not self._engine:
            return False
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            logger.exception("Database health check failed")
            return False

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self._session_factory

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield an async session with automatic commit/rollback."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call connect() first.")
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async for session in db_manager.get_session():
        yield session
