# test_neo4j.py — run from backend folder with venv activated
import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.core.config import get_settings
from neo4j import AsyncGraphDatabase

async def test():
    s = get_settings()
    print("URI:     ", repr(s.neo4j_uri))
    print("USER:    ", repr(s.neo4j_username))
    print("DATABASE:", repr(s.neo4j_database))
    print()

    driver = AsyncGraphDatabase.driver(
        s.neo4j_uri,
        auth=(s.neo4j_username, s.neo4j_password),
    )
    try:
        # 1. basic ping
        await driver.verify_connectivity()
        print("✓ Driver connected")

        # 2. query test
        async with driver.session(database=s.neo4j_database) as session:
            result = await session.run("RETURN 1 AS ok")
            data = await result.data()
            print("✓ Query OK:", data)

        # 3. write test
        async with driver.session(database=s.neo4j_database) as session:
            await session.run(
                "MERGE (t:TestNode {id: 'ping'}) SET t.ts = timestamp() RETURN t"
            )
            print("✓ Write OK: TestNode created/updated")

        # 4. read it back
        async with driver.session(database=s.neo4j_database) as session:
            result = await session.run("MATCH (t:TestNode {id: 'ping'}) RETURN t.ts AS ts")
            data = await result.data()
            print("✓ Read  OK:", data)

        # 5. clean up
        async with driver.session(database=s.neo4j_database) as session:
            await session.run("MATCH (t:TestNode {id: 'ping'}) DELETE t")
            print("✓ Cleanup OK")

        print("\n✅ Neo4j fully working!")

    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")

    finally:
        await driver.close()

asyncio.run(test())