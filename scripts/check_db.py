from __future__ import annotations

import asyncio

from rob.config.settings import configure_logging, load_settings
from rob.database.connection import Database


async def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    database = Database(settings.database_url)

    await database.connect()

    try:
        healthy = await database.health_check()

        if healthy:
            print("Database check passed.")
        else:
            raise RuntimeError("Database check failed.")
    finally:
        await database.close()

if __name__ == "__main__":
    asyncio.run(main())