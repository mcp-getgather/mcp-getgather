from __future__ import annotations

import asyncio
from enum import StrEnum
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import aiofiles
import yaml

from getgather.config import settings
from getgather.yaml_utils import RegexLoader

if TYPE_CHECKING:
    from getgather.connectors.spec_models import BrandSpec


def _get_brand_spec_path(brand: str) -> Path:
    possible_paths = [
        settings.brand_spec_dir / f"{brand}.yml",
        settings.test_brand_spec_dir / f"{brand}.yml",
        settings.brand_spec_dir / brand / "specs.yml",
        settings.test_brand_spec_dir / brand / "specs.yml",
    ]
    path = next((p for p in possible_paths if p.exists()), None)
    if not path:
        raise FileNotFoundError(f"Connector config file not found for brand: {brand}")
    return path


async def load_brand_spec(brand: str) -> BrandSpec:
    """Load a connector config from a Yaml file asynchronously.

    Args:
        link_id_or_brand (str): The link_id or brand to load.

    Returns:
        BrandSpec: The BrandSpec object, loaded from the Yaml file.
    """
    from getgather.connectors.spec_models import BrandSpec, BrandSpecYML

    # Use aiofiles to read the file asynchronously
    async with aiofiles.open(_get_brand_spec_path(brand), "r") as f:
        content = await f.read()
        yaml_data = yaml.load(content, Loader=RegexLoader)
        spec = BrandSpecYML.model_validate({"id": brand, **yaml_data})
        return BrandSpec.from_yml(
            spec, fields_map=spec.auth.fields_map, pages_map=spec.auth.pages_map
        )


def is_valid_brand(brand: str) -> bool:
    return brand in brand_id_set(include_test_specs=True)


@cache
def brand_id_set(*, include: Literal["all", "test", "prod"] = "prod") -> set[str]:
    """
    List all connector strings in the connectors directory.

    These are the Yaml file names in the getgather/connectors/brand_specs directory
    or subdirectories like getgather/connectors/brand_specs/adidas/specs.yml.
    """
    yml_files: list[Path] = []
    if include == "all" or include == "prod":
        brand_spec_dir = settings.brand_spec_dir
        if brand_spec_dir.exists():
            # Get YAML files directly in the brand_spec_dir
            yml_files.extend(brand_spec_dir.glob("*.y*ml"))
            # Get YAML files in subdirectories
            for subdir in brand_spec_dir.iterdir():
                if subdir.is_dir():
                    specs_file = subdir / "specs.yml"
                    if specs_file.exists():
                        yml_files.append(specs_file)
    if include == "all" or include == "test":
        test_brand_spec_dir = settings.test_brand_spec_dir
        # test specs are not available in the production container image
        if test_brand_spec_dir.exists():
            # Get YAML files directly in the test_brand_spec_dir
            yml_files.extend(test_brand_spec_dir.glob("*.y*ml"))
            # Get YAML files in subdirectories
            for subdir in test_brand_spec_dir.iterdir():
                if subdir.is_dir():
                    specs_file = subdir / "specs.yml"
                    if specs_file.exists():
                        yml_files.append(specs_file)

    # For files directly in the directory, use the file stem as the brand ID
    # For files in subdirectories, use the directory name as the brand ID
    brand_ids: set[str] = set()
    for yml_file in yml_files:
        if yml_file.name == "specs.yml":
            brand_ids.add(yml_file.parent.name)
        else:
            brand_ids.add(yml_file.stem)

    return brand_ids


@cache
def brand_id_list(*, include: Literal["all", "test", "prod"] = "prod") -> list[str]:
    return sorted(brand_id_set(include=include))


async def list_brand_specs(*, include: Literal["all", "test", "prod"] = "prod") -> list[BrandSpec]:
    """List all connector configs in the getgather/connectors/brand_specs directory."""
    yaml_file_names = brand_id_list(include=include)
    tasks = [load_brand_spec(yaml_file_name) for yaml_file_name in yaml_file_names]
    configs = await asyncio.gather(*tasks)
    # Sort configs by connector id
    configs.sort(key=lambda x: x.id)
    return configs


if TYPE_CHECKING:
    # this is only for Pylance/static type-checking
    class BrandIdEnum(StrEnum):
        """stub: members injected at runtime"""

        pass

else:
    # runtime: build the real StrEnum using direct brand spec loading
    brand_ids = {id: id for id in brand_id_list(include="all")}
    BrandIdEnum = StrEnum("BrandIdEnum", brand_ids)
