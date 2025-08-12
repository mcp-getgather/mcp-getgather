import base64
import json
from pathlib import Path
from typing import Any

from patchright.async_api import Page, async_playwright
from pydantic import BaseModel

from getgather.connectors.spec_loader import BrandIdEnum, load_brand_spec
from getgather.connectors.spec_models import Schema
from getgather.logs import logger

TIMEOUT = 30000


class BundleOutput(BaseModel):
    """A bundle output."""

    name: str
    parsed: bool
    parse_schema: Schema | None
    content: Any


async def parse(
    brand_id: BrandIdEnum,
    *,
    bundle: str | None = None,
    bundle_dir: Path | None = None,
    b64_content: str | None = None,
) -> list[BundleOutput] | None:
    """Parse content for a brand.

    Args:
        brand_id: The brand ID to use for parsing
        bundle: Required when using b64_content, ignored when using bundle_dir
        bundle_dir: Directory containing the bundle files. Either this or b64_content must be provided
        b64_content: Base64 encoded content. Either this or bundle_dir must be provided

    Returns:
        Parsed data when using b64_content, None when using bundle_dir
    """
    logger.info(
        f"Parsing bundle: {bundle} with b64_content: {b64_content[:200] if b64_content else 'None'}",
        extra={"brand_id": brand_id},
    )
    parsed_bundles: list[BundleOutput] = []

    if not (bundle_dir is None) ^ (b64_content is None):
        raise ValueError(
            f"Either bundle_dir or b64_content must be provided, but not both. \nbundle_dir:{bundle_dir} \nb64_content:{b64_content[:200] if b64_content else 'None'}"
        )

    spec = await load_brand_spec(brand_id)
    if not spec.parse:
        raise ValueError(f"No parse steps defined for {brand_id}!")

    if b64_content:
        # When using b64_content, we must have a bundle
        if not bundle:
            raise ValueError("Bundle name is required when using b64_content")

        # Find the bundle configuration
        bundle_config = next((p for p in spec.parse if p.bundle == bundle), None)
        if not bundle_config:
            raise ValueError(f"No parse configuration found for bundle '{bundle}' in {brand_id}")
        b64_bytes = b64_content.encode("ascii")

        content = base64.b64decode(b64_bytes).decode("utf-8")
        parsed_bundle = await _parse_by_format(schema=bundle_config, content=content)
        if parsed_bundle:
            parsed_bundles.append(parsed_bundle)
    else:
        # When using bundle_dir, parse all matching files
        assert bundle_dir is not None
        for schema in spec.parse:
            bundle_path = bundle_dir / schema.bundle
            if not bundle_path.exists():
                continue

            parsed_bundle = await _parse_by_format(schema=schema, bundle_dir=bundle_dir)
            if parsed_bundle:
                parsed_bundles.append(parsed_bundle)
    return parsed_bundles


async def _parse_by_format(
    *,
    schema: Schema,
    bundle_dir: Path | None = None,
    content: str | None = None,
) -> BundleOutput | None:
    match schema.format.lower():
        case "html":
            return await parse_html(schema=schema, bundle_dir=bundle_dir, html_content=content)
        case _:
            raise ValueError(f"Format '{schema.format}' is not supported for parsing")


async def parse_html(
    schema: Schema,
    *,
    bundle_dir: Path | None = None,
    html_content: str | None = None,
    page: Page | None = None,
    dump_html_path: Path | None = None,
) -> BundleOutput:
    """
    Use headless Playwright to parse HTML content into a tabular format stored as
    JSON file.
    Assuming schema.row_selector is a valid CSS selector to identify the individual rows,
    and schema.columns is a list of CSS selectors to identify the individual
    columns within a row.
    """
    logger.info(
        (
            f"Parsing HTML with provided page: {page is not None} "
            f"and inline content set: {html_content is not None}"
        ),
        extra={"schema": schema},
    )

    # Exactly one of bundle_dir, html_content, page must be provided
    provided = [bundle_dir is not None, html_content is not None, page is not None]
    if sum(1 for p in provided if p) != 1:
        raise ValueError("Exactly one of bundle_dir, html_content, or page must be provided")

    data: list[dict[str, str | list[str]]] = []

    async def _extract_from_page(active_page: Page) -> None:
        lc_rows = active_page.locator(schema.row_selector)
        logger.info(f"Found {await lc_rows.count()} rows")
        for lc in await lc_rows.all():
            logger.info(f"Processing row {lc} of {await lc_rows.count()} rows")
            row: dict[str, str | list[str]] = {}
            try:
                for column in schema.columns:
                    try:
                        elements = lc.locator(column.selector)
                        count = await elements.count()
                        if count == 0:
                            row[column.name] = [] if column.multiple else ""
                            continue
                        if column.multiple:
                            values: list[str] = []
                            for element in await elements.all():
                                try:
                                    if column.attribute is not None:
                                        attr_value = await element.get_attribute(column.attribute)
                                        if attr_value is not None:
                                            values.append(attr_value)
                                    else:
                                        text = await element.inner_text()
                                        if text:
                                            values.append(text)
                                except Exception as e:
                                    logger.warning(
                                        f"Error extracting multi element for column '{column.name}': {e}"
                                    )
                                    continue
                            row[column.name] = values
                        else:
                            element = elements.first
                            try:
                                if column.attribute is not None:
                                    attr_value = await element.get_attribute(column.attribute)
                                    row[column.name] = attr_value if attr_value is not None else ""
                                else:
                                    row[column.name] = await element.inner_text()
                            except Exception as e:
                                logger.warning(
                                    f"Error extracting element for column '{column.name}': {e}"
                                )
                                row[column.name] = "" if not column.multiple else []
                    except Exception as e:
                        logger.warning(
                            f"Error locating selector for column '{getattr(column, 'name', '?')}': {e}"
                        )
                        row[getattr(column, "name", "unknown")] = (
                            "" if not getattr(column, "multiple", False) else []
                        )
                data.append(row)
            except Exception as e:
                logger.warning(f"Failed processing a row: {e}")
                continue

    # Use provided page directly
    if page is not None:
        # Optional HTML dump for debugging
        if dump_html_path is not None:
            try:
                dump_html_path.parent.mkdir(parents=True, exist_ok=True)
                html_dump = await page.content()
                dump_html_path.write_text(html_dump, encoding="utf-8")
                logger.info(f"Wrote HTML dump to {dump_html_path}")
            except Exception as e:
                logger.warning(f"Failed to write HTML dump: {e}")
        await _extract_from_page(page)
    else:
        # Create a temporary Playwright context for parsing standalone content
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            context = await browser.new_context()
            context.set_default_timeout(TIMEOUT)
            context.set_default_navigation_timeout(TIMEOUT)
            new_page = await context.new_page()

            if html_content is not None:
                await new_page.set_content(html_content)
            else:
                assert bundle_dir is not None
                input_path = bundle_dir / schema.bundle
                logger.info(f"Parsing {input_path} ...")
                await new_page.goto(Path(input_path).absolute().as_uri())

            # Optional dump when using temporary page
            if dump_html_path is not None:
                try:
                    dump_html_path.parent.mkdir(parents=True, exist_ok=True)
                    html_dump = await new_page.content()
                    dump_html_path.write_text(html_dump, encoding="utf-8")
                    logger.info(f"Wrote HTML dump to {dump_html_path}")
                except Exception as e:
                    logger.warning(f"Failed to write HTML dump: {e}")

            await _extract_from_page(new_page)

            await browser.close()

    if bundle_dir:
        output_path = bundle_dir / schema.output
        with open(output_path, "w") as f:
            json.dump(data, f)
        logger.info(f"{len(data)} rows written to {output_path}")
        return BundleOutput(
            name=schema.bundle,
            parsed=True,
            parse_schema=schema,
            content=data,
        )
    else:
        # Return the data directly if no bundle_dir provided
        logger.info(
            f"Returning data directly: {data[:200] if data else 'None'}", extra={"schema": schema}
        )
        return BundleOutput(
            name=schema.bundle,
            parsed=True,
            parse_schema=schema,
            content=data,
        )
