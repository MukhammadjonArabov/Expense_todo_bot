import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from dotenv import load_dotenv
import os

# .env fayldan o'qish
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy metadata import qilinadi
from app.database import Base  # <-- sening loyhangda Base shu joyda
# agar joyi boshqacha bo‘lsa, to‘g‘ri yo‘lni yoz

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    """Offline rejimda migratsiya."""
    context.configure(
        url=DATABASE_URL.replace("asyncpg", "psycopg2"),  # sync uchun
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Asinxron online migratsiya."""
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
