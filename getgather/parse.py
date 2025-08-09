import base64
import json
from pathlib import Path
from typing import Any

from patchright.async_api import async_playwright
from pydantic import BaseModel

from getgather.connectors.spec_loader import BrandIdEnum, load_brand_spec
from getgather.connectors.spec_models import Schema
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
) -> BundleOutput:
    """
    Use headless Playwright to parse HTML content into a tabular format stored as
    JSON file.
    Assuming schema.row_selector is a valid CSS selector to identify the individual rows,
    and schema.columns is a list of CSS selectors to identify the individual
    columns within a row.
    """
    logger.info(
        f"Parsing HTML content: {html_content[:200] if html_content else 'None'}",
        extra={"schema": schema},
    )
    if not (bundle_dir is None) ^ (html_content is None):
        raise ValueError("Exactly one of bundle_dir or html_content must be provided")

    data: list[dict[str, str | list[str]]] = []
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
                    values: list[str] = []
                    for element in await elements.all():
                        if column.attribute is not None:
                            attr_value = await element.get_attribute(column.attribute)
                            if attr_value is not None:
                                values.append(attr_value)
                        else:
                            text = await element.inner_text()
                            if text:
                                values.append(text)
                    row[column.name] = values
                else:
                    element = elements.first
                    if column.attribute is not None:
                        attr_value = await element.get_attribute(column.attribute)
                        row[column.name] = attr_value if attr_value is not None else ""
                    else:
                        row[column.name] = await element.inner_text()

            data.append(row)

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
