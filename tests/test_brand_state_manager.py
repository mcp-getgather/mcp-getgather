import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, patch

import pytest

from getgather.brand_state import BrandState, BrandStateManager
from getgather.connectors.spec_loader import BrandIdEnum


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary file for testing database operations."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
        temp_path = temp_file.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_db_manager(temp_db_path: str) -> Generator[AsyncMock, None, None]:
    """Mock db_manager to use temporary file."""
    mock_data: dict[str, Any] = {}

    async def mock_get(key: str) -> Any:
        return mock_data.get(key)

    async def mock_set(key: str, value: Any) -> None:
        mock_data[key] = value

    mock_manager = AsyncMock()
    mock_manager.get = mock_get
    mock_manager.set = mock_set

    with patch("getgather.brand_state.db_manager", mock_manager):
        yield mock_manager


@pytest.fixture
def brand_state_manager(mock_db_manager: AsyncMock) -> BrandStateManager:
    """Create a BrandStateManager instance with mocked db_manager."""
    return BrandStateManager()


@pytest.fixture
def sample_brand_state() -> BrandState:
    """Create a sample BrandState for testing."""
    return BrandState(brand_id="amazon", browser_profile_id="test-profile-123", is_connected=False)


@pytest.mark.asyncio
async def test_add_brand_state(
    brand_state_manager: BrandStateManager, sample_brand_state: BrandState
) -> None:
    """Test adding a new brand state."""
    await brand_state_manager.add(sample_brand_state)

    # Verify by retrieving the added state
    result = await brand_state_manager.get_by_brand_id(BrandIdEnum("amazon"))
    assert result is not None
    assert result.brand_id == "amazon"


@pytest.mark.asyncio
async def test_get_by_brand_id_exists(
    brand_state_manager: BrandStateManager, sample_brand_state: BrandState
) -> None:
    """Test getting brand state by ID when it exists."""
    await brand_state_manager.add(sample_brand_state)

    result = await brand_state_manager.get_by_brand_id(BrandIdEnum("amazon"))
    assert result is not None
    assert result.brand_id == "amazon"
    assert result.browser_profile_id == "test-profile-123"


@pytest.mark.asyncio
async def test_get_by_brand_id_not_exists(brand_state_manager: BrandStateManager) -> None:
    """Test getting brand state by ID when it doesn't exist."""
    result = await brand_state_manager.get_by_brand_id(BrandIdEnum("amazon"))
    assert result is None


@pytest.mark.asyncio
async def test_update_is_connected_success(
    brand_state_manager: BrandStateManager, sample_brand_state: BrandState
) -> None:
    """Test updating is_connected status successfully."""
    await brand_state_manager.add(sample_brand_state)

    await brand_state_manager.update_is_connected(BrandIdEnum("amazon"), True)

    updated_state = await brand_state_manager.get_by_brand_id(BrandIdEnum("amazon"))
    assert updated_state is not None
    assert updated_state.is_connected is True


@pytest.mark.asyncio
async def test_update_is_connected_not_found(brand_state_manager: BrandStateManager) -> None:
    """Test updating is_connected status when brand state doesn't exist."""
    with pytest.raises(ValueError, match="Brand state amazon not found"):
        await brand_state_manager.update_is_connected(BrandIdEnum("amazon"), True)


@pytest.mark.asyncio
async def test_is_brand_connected_true(
    brand_state_manager: BrandStateManager, sample_brand_state: BrandState
) -> None:
    """Test checking if brand is connected when it is."""
    sample_brand_state.is_connected = True
    await brand_state_manager.add(sample_brand_state)

    result = await brand_state_manager.is_brand_connected(BrandIdEnum("amazon"))
    assert result is True


@pytest.mark.asyncio
async def test_is_brand_connected_false(
    brand_state_manager: BrandStateManager, sample_brand_state: BrandState
) -> None:
    """Test checking if brand is connected when it's not."""
    await brand_state_manager.add(sample_brand_state)

    result = await brand_state_manager.is_brand_connected(BrandIdEnum("amazon"))
    assert result is False


@pytest.mark.asyncio
async def test_is_brand_connected_not_exists(brand_state_manager: BrandStateManager) -> None:
    """Test checking if brand is connected when brand state doesn't exist."""
    result = await brand_state_manager.is_brand_connected(BrandIdEnum("amazon"))
    assert result is False


@pytest.mark.asyncio
async def test_get_browser_profile_id_exists(
    brand_state_manager: BrandStateManager, sample_brand_state: BrandState
) -> None:
    """Test getting browser profile ID when brand state exists."""
    await brand_state_manager.add(sample_brand_state)

    result = await brand_state_manager.get_browser_profile_id(BrandIdEnum("amazon"))
    assert result == "test-profile-123"


@pytest.mark.asyncio
async def test_get_browser_profile_id_not_exists(brand_state_manager: BrandStateManager) -> None:
    """Test getting browser profile ID when brand state doesn't exist."""
    result = await brand_state_manager.get_browser_profile_id(BrandIdEnum("amazon"))
    assert result is None


@pytest.mark.asyncio
async def test_multiple_brand_states(brand_state_manager: BrandStateManager) -> None:
    """Test managing multiple brand states."""
    amazon_state = BrandState(
        brand_id="amazon", browser_profile_id="amazon-profile", is_connected=True
    )
    shopee_state = BrandState(
        brand_id="shopee", browser_profile_id="shopee-profile", is_connected=False
    )

    await brand_state_manager.add(amazon_state)
    await brand_state_manager.add(shopee_state)

    # Check both states exist
    amazon_result = await brand_state_manager.get_by_brand_id(BrandIdEnum("amazon"))
    shopee_result = await brand_state_manager.get_by_brand_id(BrandIdEnum("shopee"))

    assert amazon_result is not None
    assert amazon_result.is_connected is True
    assert shopee_result is not None
    assert shopee_result.is_connected is False

    # Update one state
    await brand_state_manager.update_is_connected(BrandIdEnum("shopee"), True)

    # Verify only the updated state changed
    amazon_after = await brand_state_manager.get_by_brand_id(BrandIdEnum("amazon"))
    shopee_after = await brand_state_manager.get_by_brand_id(BrandIdEnum("shopee"))

    assert amazon_after is not None
    assert amazon_after.is_connected is True  # unchanged
    assert shopee_after is not None
    assert shopee_after.is_connected is True  # changed
