"""
HRMS Health Check Script
Verifies all services are running and accessible.
"""

from __future__ import annotations

import asyncio
import sys

import httpx


async def check_service(name: str, url: str, timeout: float = 5.0) -> bool:
    """Check if a service is reachable."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            ok = resp.status_code < 500
            status = "✅" if ok else "⚠️"
            print(f"  {status} {name}: {resp.status_code}")
            return ok
    except httpx.ConnectError:
        print(f"  ❌ {name}: Connection refused")
        return False
    except httpx.TimeoutException:
        print(f"  ⏱️  {name}: Timeout")
        return False
    except Exception as exc:
        print(f"  ❌ {name}: {exc}")
        return False


async def check_redis(name: str, url: str) -> bool:
    """Check Redis connectivity."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(url)
        ok = await r.ping()
        await r.aclose()
        print(f"  {'✅' if ok else '❌'} {name}: {'Connected' if ok else 'Ping failed'}")
        return ok
    except Exception as exc:
        print(f"  ❌ {name}: {exc}")
        return False


async def check_postgres(name: str, url: str) -> bool:
    """Check PostgreSQL connectivity."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        print(f"  ✅ {name}: Connected")
        return True
    except Exception as exc:
        print(f"  ❌ {name}: {exc}")
        return False


async def main() -> None:
    print("═" * 50)
    print("  HRMS Service Health Check")
    print("═" * 50)
    print()

    results = []

    # Backend
    results.append(await check_service("Backend API", "http://localhost:8000/health"))

    # PostgreSQL
    results.append(await check_postgres("PostgreSQL", "postgresql+asyncpg://hrms:hrms@localhost:5432/hrms_db"))

    # Redis
    results.append(await check_redis("Redis", "redis://localhost:6379/0"))

    # Ollama
    results.append(await check_service("Ollama", "http://localhost:11434/api/tags"))

    # Whisper
    results.append(await check_service("Whisper", "http://localhost:9000/"))

    # ClamAV
    results.append(await check_service("ClamAV", "http://localhost:3310/"))

    # ngrok (optional — only if running)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:4040/api/tunnels")
            if resp.status_code == 200:
                import json
                tunnels = resp.json().get("tunnels", [])
                if tunnels:
                    url = tunnels[0].get("public_url", "unknown")
                    print(f"  ✅ ngrok: Tunnel active → {url}")
                    results.append(True)
                else:
                    print("  ⚠️  ngrok: No active tunnels")
                    results.append(False)
            else:
                print("  ⏭️  ngrok: Not running (optional)")
    except (httpx.ConnectError, httpx.TimeoutException):
        print("  ⏭️  ngrok: Not running (optional)")

    print()
    passed = sum(results)
    total = len(results)
    print(f"  Result: {passed}/{total} services healthy")

    if passed == total:
        print("  ✅ All services are running!")
    else:
        print("  ⚠️  Some services are not reachable.")
        print("  Run: docker compose up -d")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
