from getgather.config import settings
import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def ensure_db_directory_exists():
    """Ensure the directory for the database file exists."""
    db_dir = os.path.dirname(settings.database_path)
    Path(db_dir).mkdir(parents=True, exist_ok=True)


def run_migrations() -> None:
    """Run migrations in 'online' mode."""
    ensure_db_directory_exists()

    configuration = config.get_section(config.config_ini_section)

    if configuration is not None:
        configuration["sqlalchemy.url"] = f"sqlite:///{settings.database_path}"

    connectable = engine_from_config(
        configuration or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations()
