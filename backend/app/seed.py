"""Create the local login accounts in PostgreSQL.

Run from the backend directory after migration 0005:

    NEXUS_DATABASE_URL=postgresql+asyncpg://nexus:nexus@127.0.0.1:5433/nexusai \\
        .venv/bin/python -m app.seed

The passwords below are for this local database only.
"""

import asyncio
from dataclasses import dataclass

from app.repositories.users import create_user, get_by_email


@dataclass(frozen=True)
class SeedAccount:
    email: str
    display_name: str
    role: str
    password: str


SEED_ACCOUNTS: tuple[SeedAccount, ...] = (
    SeedAccount("admin@nexusai.local", "Nexus Admin", "super_admin", "NexusAdmin-local"),
    SeedAccount("amina@nexusai.local", "Amina Rahman", "member", "Amina-local"),
    SeedAccount("luis@nexusai.local", "Luis Ortega", "member", "Luis-local"),
)


async def seed() -> None:
    for account in SEED_ACCOUNTS:
        existing = await get_by_email(account.email)
        if existing is not None:
            print(f"exists {account.email} role={existing.role}")
            continue
        created = await create_user(
            account.email,
            account.display_name,
            account.password,
            account.role,
        )
        print(f"created {created.email} role={created.role}")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
