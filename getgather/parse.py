import asyncio
import base64
import json
import sys
from pathlib import Path
from typing import Any, Literal

from patchright.async_api import Locator, Page, async_playwright
from pydantic import BaseModel
from rich import print

from getgather.connectors.spec_loader import BrandIdEnum, load_brand_spec, load_custom_functions
from getgather.connectors.spec_models import Column, Schema
from getgather.logs import logger

TIMEOUT = 1000


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
        parsed_bundle = await _parse_by_format(
            brand_id=brand_id, schema=bundle_config, content=content
        )
        if parsed_bundle:
            parsed_bundles.append(parsed_bundle)
    else:
        # When using bundle_dir, parse all matching files
        assert bundle_dir is not None
        for schema in spec.parse:
            bundle_path = bundle_dir / schema.bundle
            if not bundle_path.exists():
                continue

            parsed_bundle = await _parse_by_format(
                brand_id=brand_id, schema=schema, bundle_dir=bundle_dir
            )
            if parsed_bundle:
                parsed_bundles.append(parsed_bundle)
    return parsed_bundles


async def _parse_by_format(
    *,
    brand_id: BrandIdEnum,
    schema: Schema,
    bundle_dir: Path | None = None,
    content: str | None = None,
) -> BundleOutput | None:
    match schema.format.lower():
        case "html":
            return await parse_html(
                brand_id=brand_id, schema=schema, bundle_dir=bundle_dir, html_content=content
            )
        case _:
            raise ValueError(f"Format '{schema.format}' is not supported for parsing")


async def _get_value(brand_id: BrandIdEnum, column: Column, element: Locator) -> str | None:
    """Extract value from an element based on column configuration."""
    if column.attribute is not None:
        return await element.get_attribute(column.attribute)
    elif column.function is not None:
        functions = load_custom_functions(brand_id)
        return await functions.extract_url(element)
    else:
        return await element.inner_text()


async def _extract_data_with_locators(
    brand_id: BrandIdEnum,
    schema: Schema,
    page: Page,
) -> list[dict[str, str | list[str]]]:
    """
    Extract data from a page using Playwright locators.

    This is the original extraction method that uses individual DOM queries.
    Best for: Authentication flows, interactive elements, complex waiting conditions.

    Args:
        brand_id: Brand identifier for custom parsing functions
        schema: Schema definition with CSS selectors
        page: Live Playwright page object

    Returns:
        List of dictionaries containing extracted data
    """
    data: list[dict[str, str | list[str]]] = []
    lc_rows = page.locator(schema.row_selector)

    for lc in await lc_rows.all():
        row: dict[str, str | list[str]] = {}

        for column in schema.columns:
            elements = lc.locator(column.selector)
            count = await elements.count()

            if count == 0:
                row[column.name] = [] if column.multiple else ""
                continue

            if column.multiple:
                values = await asyncio.gather(*[
                    _get_value(brand_id, column, element) for element in await elements.all()
                ])
                row[column.name] = [v for v in values if v is not None]
            else:
                value = await _get_value(brand_id, column, elements.first)
                row[column.name] = value if value is not None else ""

        data.append(row)
    return data


async def _extract_data_with_evaluate(
    brand_id: BrandIdEnum,
    schema: Schema,
    page: Page,
) -> list[dict[str, Any]]:
    """
    Extract data from a page using JavaScript evaluation.

    This method executes all extraction logic in the browser context in a single call.
    Best for: Bulk data extraction, search results, product listings, read-only operations.

    Args:
        brand_id: Brand identifier (not used in evaluate method but kept for consistency)
        schema: Schema definition with CSS selectors
        page: Live Playwright page object

    Returns:
        List of dictionaries containing extracted data
    """
    # Prepare column data for JavaScript
    columns_for_js: list[dict[str, Any]] = []
    for col in schema.columns:
        col_data: dict[str, Any] = {
            "name": col.name,
            "selector": col.selector,
            "attribute": col.attribute,
            "multiple": col.multiple if hasattr(col, "multiple") else False,
        }
        columns_for_js.append(col_data)

    # Execute all extraction in a single browser call
    data: list[dict[str, Any]] = await page.evaluate(
        """
        ({rowSelector, columns}) => {
            const rows = document.querySelectorAll(rowSelector);
            const results = [];

            for (const row of rows) {
                const rowData = {};

                for (const col of columns) {
                    if (col.multiple) {
                        const elements = row.querySelectorAll(col.selector);
                        const values = [];
                        for (const el of elements) {
                            if (col.attribute) {
                                values.push(el.getAttribute(col.attribute) || "");
                            } else {
                                values.push(el.innerText || "");
                            }
                        }
                        rowData[col.name] = values;
                    } else {
                        const el = row.querySelector(col.selector);
                        if (el) {
                            if (col.attribute) {
                                rowData[col.name] = el.getAttribute(col.attribute) || "";
                            } else {
                                rowData[col.name] = el.innerText || "";
                            }
                        } else {
                            rowData[col.name] = "";
                        }
                    }
                }

                results.push(rowData);
            }

            return results;
        }
    """,
        {"rowSelector": schema.row_selector, "columns": columns_for_js},
    )
    return data


async def _extract_data_from_page(
    brand_id: BrandIdEnum,
    schema: Schema,
    page: Page,
    *,
    force_method: Literal["locator", "evaluate", None] = None,
) -> list[dict[str, str | list[str]]]:
    """
    Router function that chooses the appropriate extraction method.

    Decides between locator-based and evaluate-based extraction based on:
    1. force_method parameter (if specified)
    2. schema.use_evaluate_extraction flag
    3. Presence of custom functions (forces locator method)

    Args:
        brand_id: Brand identifier for custom parsing functions
        schema: Schema definition with CSS selectors
        page: Live Playwright page object
        force_method: Force a specific extraction method

    Returns:
        List of dictionaries containing extracted data
    """
    # Check if we need to use locator method due to custom functions
    has_custom_functions = any(col.function is not None for col in schema.columns)

    # Determine which method to use (default to locator)
    use_evaluate = False
    
    if not has_custom_functions:
        if force_method == "evaluate":
            use_evaluate = True
        elif force_method != "locator":
            # Use schema configuration
            use_evaluate = getattr(schema, "use_evaluate_extraction", False)

    # Execute the appropriate extraction method
    if use_evaluate:
        try:
            return await _extract_data_with_evaluate(brand_id, schema, page)
        except Exception as e:
            print(f"[PARSE] Evaluate extraction failed: {e}, falling back to locator method")
            return await _extract_data_with_locators(brand_id, schema, page)
    else:
        return await _extract_data_with_locators(brand_id, schema, page)


async def parse_html(
    brand_id: BrandIdEnum,
    schema: Schema,
    *,
    bundle_dir: Path | None = None,
    html_content: str | None = None,
    page: Page | None = None,
) -> BundleOutput:
    """
    Parse HTML content using CSS selectors into a tabular format.

    This function supports two modes:
    1. Headless browser mode: Creates a new Playwright browser instance to parse
       HTML from files or content strings, optionally saving results to JSON
    2. Live page mode: Uses an existing live browser page for parsing without
       creating a new browser instance (more efficient for real-time data extraction)

    Args:
        brand_id: Brand identifier for custom parsing functions
        schema: Schema definition with CSS selectors for data extraction
        bundle_dir: Directory containing HTML files to parse (headless mode)
        html_content: HTML content string to parse (headless mode)
        page: Live Playwright page object to parse from (live mode)

    Returns:
        BundleOutput containing parsed data and metadata

    Note: When using headless mode, exactly one of bundle_dir or html_content must be provided.
          When using live mode, only the page parameter is needed.
    """
    logger.info(
        f"Parsing HTML content: {html_content[:200] if html_content else 'None'} with page: {page is not None}",
        extra={"schema": schema},
    )

    # If page is provided, use it directly (live page parsing)
    if page is not None:
        data = await _extract_data_from_page(brand_id, schema, page)
    else:
        # Original headless browser logic
        if not (bundle_dir is None) ^ (html_content is None):
            raise ValueError("Exactly one of bundle_dir or html_content must be provided")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            context = await browser.new_context()
            context.set_default_timeout(TIMEOUT)
            context.set_default_navigation_timeout(TIMEOUT)
            page = await context.new_page()

            if html_content:
                await page.set_content(html_content)
            else:
                assert bundle_dir is not None
                input_path = bundle_dir / schema.bundle
                logger.info(f"Parsing {input_path} ...")
                await page.goto(Path(input_path).absolute().as_uri())

            data = await _extract_data_from_page(brand_id, schema, page)
            await browser.close()

    if bundle_dir:
        output_path = bundle_dir / schema.output
        with open(output_path, "w") as f:
            json.dump(data, f)
        logger.info(f"{len(data)} rows written to {output_path}")
        result = BundleOutput(
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
        result = BundleOutput(
            name=schema.bundle,
            parsed=True,
            parse_schema=schema,
            content=data,
        )

    return result


# test with:
# python getgather/parse.py [brand] data/bundles/[profile_id]/[brand]
if __name__ == "__main__":
    brand_id = BrandIdEnum(sys.argv[1])
    bundle_dir = Path(sys.argv[2])
    parsed_bundles = asyncio.run(parse(brand_id, bundle_dir=bundle_dir))
    print(parsed_bundles)
