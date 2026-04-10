"""
graph/neo4j_client.py
──────────────────────
Neo4j driver initialisation and context manager helpers.
All graph operations go through this module.
"""

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any, AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_driver() -> AsyncDriver:
    """Return a cached async Neo4j driver instance."""
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        max_connection_pool_size=50,
    )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a Neo4j session.

    Usage:
        async with get_session() as session:
            result = await session.run("MATCH (n) RETURN n LIMIT 5")
    """
    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        yield session


async def run_query(
    cypher: str,
    params: dict[str, Any] | None = None,
) -> list[dict]:
    """
    Execute a read/write Cypher query and return all records as dicts.
    """
    async with get_session() as session:
        result = await session.run(cypher, params or {})
        records = await result.data()
        return records


async def close_driver() -> None:
    """Gracefully close the driver – call on app shutdown."""
    driver = get_driver()
    await driver.close()


# ── Schema / Index initialisation ────────────────────────────

SCHEMA_QUERIES = [
    # Uniqueness constraints
    "CREATE CONSTRAINT business_gstin IF NOT EXISTS FOR (b:Business) REQUIRE b.gstin IS UNIQUE",
    "CREATE CONSTRAINT invoice_id IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    # Indexes for fast lookups
    "CREATE INDEX invoice_number IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_number)",
    "CREATE INDEX invoice_date IF NOT EXISTS FOR (i:Invoice) ON (i.invoice_date)",
]


async def init_graph_schema() -> None:
    """
    Idempotent schema setup – run once on app startup.
    Creates constraints and indexes if they don't already exist.
    """
    for query in SCHEMA_QUERIES:
        await run_query(query)
    print("[Neo4j] Graph schema initialised.")