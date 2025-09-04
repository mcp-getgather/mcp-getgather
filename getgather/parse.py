import asyncio
import base64
import json
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from patchright.async_api import Locator, Page, async_playwright
from pydantic import BaseModel
from rich import print

from getgather.connectors.spec_loader import BrandIdEnum, load_brand_spec, load_custom_functions
from getgather.connectors.spec_models import Column, Schema
from getgather.logs import logger

TIMEOUT = 10000


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


async def _extract_data_with_evaluator(
    brand_id: BrandIdEnum,
    schema: Schema,
    page: Page,
) -> list[dict[str, Any]]:
    """
    Extract data from a page using JavaScript evaluation.

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
        if not getattr(col, "name", None) or not getattr(col, "selector", None):
            raise ValueError(f"Invalid column definition: {col}")

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
            if (!rows.length) {
                return [];
            }
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


async def _extract_data_with_python_parser(
    brand_id: BrandIdEnum,
    schema: Schema,
    html_content: str,
    page: Page | None = None,
) -> list[dict[str, str | list[str]]]:
    """
    This method parses HTML using python parser.

    Args:
        brand_id: Brand identifier for custom parsing functions
        schema: Schema definition with CSS selectors
        html_content: Raw HTML content to parse
        page: Optional Playwright page (not used, kept for API compatibility)

    Returns:
        List of dictionaries containing extracted data
    """
    soup = BeautifulSoup(html_content, "lxml")
    data: list[dict[str, str | list[str]]] = []

    rows = soup.select(schema.row_selector)
    logger.info(f"Found {len(rows)} rows using python_parser")

    for row in rows:
        row_data: dict[str, str | list[str]] = {}

        for column in schema.columns:
            elements = row.select(column.selector)

            if not elements:
                row_data[column.name] = [] if column.multiple else ""
                continue

            if column.multiple:
                values: list[str] = []
                for elem in elements:
                    if column.attribute:
                        value = elem.get(column.attribute, "")
                    else:
                        value = elem.get_text(strip=True)

                    if value:
                        values.append(str(value))
                row_data[column.name] = values
            else:
                elem = elements[0]
                if column.attribute:
                    value = elem.get(column.attribute, "")
                else:
                    value = elem.get_text(strip=True)
                row_data[column.name] = value if value else ""

        data.append(row_data)

    return data


async def _extract_data_from_page(
    brand_id: BrandIdEnum,
    schema: Schema,
    page: Page,
) -> list[dict[str, str | list[str]]]:
    """
    Extract data from a live Playwright page using the schema's extraction method.

    Custom functions force locator method regardless of schema setting.

    Args:
        brand_id: Brand identifier for custom parsing functions
        schema: Schema definition with CSS selectors and extraction_method
        page: Live Playwright page object

    Returns:
        List of dictionaries containing extracted data
    """
    has_custom_functions = any(col.function is not None for col in schema.columns)
    extraction_method = getattr(schema, "extraction_method", "locator")

    if has_custom_functions:
        extraction_method = "locator"  # Force locator method for custom functions

    if extraction_method == "evaluator":
        try:
            return await _extract_data_with_evaluator(brand_id, schema, page)
        except Exception as e:
            print(f"[PARSE] Evaluate extraction failed: {e}, falling back to locator method")
            return await _extract_data_with_locators(brand_id, schema, page)
    elif extraction_method == "python_parser":
        try:
            html_content = await page.content()
            return await _extract_data_with_python_parser(brand_id, schema, html_content, page)
        except Exception as e:
            print(f"[PARSE] Python parser extraction failed: {e}, falling back to locator method")
            return await _extract_data_with_locators(brand_id, schema, page)
    else:
        # Default to locator method
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
    Parse HTML content into a tabular format.

    This function supports two modes:
    1. Headless browser mode: Creates a new Playwright browser instance to parse
       HTML from files or content strings, optionally saving results to JSON
    2. Live page mode: Uses an existing live browser page for parsing without
       creating a new browser instance (more efficient for real-time data extraction)

    Supports three extraction methods (configured in schema):
    1. "locator" (default): Uses Playwright locators with auto-wait
    2. "evaluator": Extract data from a page using JavaScript evaluation.
    3. "python_parser": Parses HTML using Python's BeautifulSoup

    Args:
        brand_id: Brand identifier for custom parsing functions
        schema: Schema definition with CSS selectors and extraction_method configuration
        bundle_dir: Directory containing HTML files to parse (headless mode)
        html_content: HTML content string to parse (headless mode)
        page: Live Playwright page object to parse from (live mode)

    Returns:
        BundleOutput containing parsed data and metadata

    Note: When using headless mode, exactly one of bundle_dir or html_content must be provided.
          When using live mode, only the page parameter is needed.
          Custom functions force locator method regardless of extraction_method setting.
    """
    logger.info(
        f"Parsing HTML content: {html_content[:200] if html_content else 'None'} with page: {page is not None}",
        extra={"schema": schema},
    )

    data: list[dict[str, str | list[str]]] = []

    # Decide extraction path based on available inputs
    if page is not None:
        # Live page mode: use the page directly
        data = await _extract_data_from_page(brand_id, schema, page)

    elif html_content:
        # Check if we can extract directly from HTML
        has_custom_functions = any(col.function is not None for col in schema.columns)
        extraction_method = getattr(schema, "extraction_method", "locator")

        if has_custom_functions or extraction_method != "python_parser":
            # Need a browser for extraction
            async with async_playwright() as pw:
                browser = await pw.chromium.launch()
                context = await browser.new_context()
                context.set_default_timeout(TIMEOUT)
                context.set_default_navigation_timeout(TIMEOUT)
                page = await context.new_page()
                await page.set_content(html_content)
                data = await _extract_data_from_page(brand_id, schema, page)
                await browser.close()
        else:
            # Can extract directly from HTML using python_parser
            data = await _extract_data_with_python_parser(brand_id, schema, html_content, None)

    else:
        # Headless browser mode with bundle_dir
        if bundle_dir is None:
            raise ValueError("Either page, html_content, or bundle_dir must be provided")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            context = await browser.new_context()
            context.set_default_timeout(TIMEOUT)
            context.set_default_navigation_timeout(TIMEOUT)
            page = await context.new_page()

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
