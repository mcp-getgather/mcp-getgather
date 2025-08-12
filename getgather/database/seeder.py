from getgather.database.connection import execute_query, fetch_all
from getgather.logs import logger
from getgather.mcp.auto_import import auto_import
from getgather.mcp.registry import BrandMCPBase


def seed_brand_states() -> None:
    """Seed the brand_states table with initial data for all available brands."""
    logger.info("Starting to seed brand_states table...")

    auto_import("getgather.mcp.brand")
    brands = [
        (brand_id, BrandMCPBase.registry[brand_id].name)
        for brand_id in BrandMCPBase.registry.keys()
    ]
    if not brands:
        logger.warning("No brands found to seed")
        return

    logger.info(f"Found {len(brands)} brands to seed: {', '.join([brand[0] for brand in brands])}")

    # Check if table already has data
    existing_brands = fetch_all("SELECT brand_id FROM brand_states")
    existing_brand_ids = {row["brand_id"] for row in existing_brands}

    # Filter out brands that already exist
    brands_to_seed = [brand for brand in brands if brand not in existing_brand_ids]

    if not brands_to_seed:
        logger.info("All brands already seeded, nothing to do")
        return

    logger.info(f"Seeding {len(brands_to_seed)} new brands...")

    # Prepare insert query
    insert_query = """
        INSERT INTO brand_states (brand_id, name)
        VALUES (?, ?)
    """

    # Seed each brand
    for brand_id, name in brands_to_seed:
        try:
            execute_query(insert_query, (brand_id, name))
            logger.info(f"Seeded brand: {brand_id}")
        except Exception as e:
            logger.error(f"Failed to seed brand {brand_id}: {e}")

    logger.info(f"Brand states seeding completed. Seeded {len(brands_to_seed)} brands.")
