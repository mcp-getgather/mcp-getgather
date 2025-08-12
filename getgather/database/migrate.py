from pathlib import Path

from alembic import command
from alembic.config import Config

from getgather.config import settings
from getgather.logs import logger


def run_migration():
    """Run database migrations using Alembic."""
    logger.info(f"Running migrations on database: {settings.database_path}")

    try:
        migrations_dir = Path(__file__).parent / "migrations"
        alembic_cfg = Config(str(migrations_dir / "alembic.ini"))

        logger.info(f"Migrations directory: {migrations_dir}")
        logger.info(f"Alembic configuration: {alembic_cfg}")

        # Run the migration
        command.upgrade(alembic_cfg, "head")

        logger.info("Migration completed successfully!")

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise


if __name__ == "__main__":
    run_migration()
