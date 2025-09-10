import tempfile
from pathlib import Path
from typing import Literal
from unittest.mock import patch

import pytest

from getgather.connectors.spec_loader import brand_id_list, list_brand_specs, load_brand_spec
from getgather.connectors.spec_models import BrandSpec


@pytest.mark.asyncio
async def test_load_brand_spec():
    """Test the load_connector_config function with a mocked yaml file."""
    # Create a temporary directory for the mocked yaml file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "acme_spec.yml"

        # Create the mocked yaml file
        with open(temp_path, "w") as f:
            f.write("""
            name: test_spec
            signin:
                steps:
                    - name: test_step
            extract:
                steps:
                    - name: test_step
            parse:
                - bundle: test_bundle
                  format: html
                  output: test_output
                  row_selector: test_row
                  columns:
                    - name: test_column
                      selector: test_selector
            """)

        # Patch Path.resolve to return our temporary file path
        with patch("getgather.connectors.spec_loader._get_brand_spec_path", return_value=temp_path):
            # Test the load_connector_config function
            spec = await load_brand_spec("acme_spec")
            assert spec is not None
            assert isinstance(spec, BrandSpec)
            assert spec.name == "test_spec"
            assert spec.signin is not None
            assert spec.signin.steps is not None
            assert len(spec.signin.steps) == 1
            assert spec.signin.steps[0].name == "test_step"
            assert spec.extract is not None
            assert spec.extract.steps is not None
            assert len(spec.extract.steps) == 1
            assert spec.extract.steps[0].name == "test_step"
            assert spec.parse is not None
            assert len(spec.parse) == 1
            assert spec.parse[0].bundle == "test_bundle"
            assert spec.parse[0].format == "html"
            assert spec.parse[0].output == "test_output"
            assert spec.parse[0].row_selector == "test_row"
            assert spec.parse[0].columns is not None
            assert len(spec.parse[0].columns) == 1
            assert spec.parse[0].columns[0].name == "test_column"
            assert spec.parse[0].columns[0].selector == "test_selector"


@pytest.mark.parametrize("include", ["all", "test", "prod"])
@pytest.mark.asyncio
async def test_list_brand_specs(include: Literal["all", "test", "prod"]):
    """Test the list_brand_specs function."""
    specs = await list_brand_specs(include=include)
    assert len(specs) > 0
    assert isinstance(specs[0], BrandSpec)


def test_list_brand_ids():
    """Test the list_brand_ids function."""
    spec_ids = brand_id_list()
    assert len(spec_ids) > 0
    assert isinstance(spec_ids[0], str)
