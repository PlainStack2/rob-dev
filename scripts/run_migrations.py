from __future__ import annotations

import asyncio
from pathlib import Path

from rob.config.settings import configure_logging, load_settings
from rob.database.connection import Database

MIGRATIONS_DIR = Path("rob/database/migrations")

async def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    database = Database(settings.database_url)
    await database.connect()

    try:
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        if not migration_files:
            raise RuntimeError("No migration files found.")
        
        async with database.transaction() as connection:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )

            rows = await connection.fetch(
                "SELECT version FROM schema_migrations;"
            )
            applied_versions = {row["version"] for row in rows}

            for migration_file in migration_files:
                version = migration_file.stem

                if version in applied_versions:
                    print(f"Skipping {version}; already applied.")
                    continue

                sql = migration_file.read_text(encoding="utf-8")

                print(f"Applying {version}...")
                await connection.execute(sql)
                await connection.execute(
                    """
                    INSERT INTO schema_migrations (version)
                    VALUES ($1);
                    """,
                    version,
                )

        print("Migrations complete.")
    finally:
        await database.close()

if __name__ == "__main__":
    asyncio.run(main())