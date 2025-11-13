from unittest.mock import AsyncMock, MagicMock

import pytest
from patchright.async_api import Locator

from getgather.distill import locate


@pytest.mark.asyncio
async def test_locate_handles_nth_element_error():
    """Test locate() gracefully handles 'Can't query n-th element' errors."""

    # Mock locator that has 2 elements but second one fails on nth()
    mock_locator = MagicMock(spec=Locator)
    mock_locator.count = AsyncMock(return_value=2)

    # First element: nth() works, is_visible() returns False
    mock_el1 = MagicMock(spec=Locator)
    mock_el1.is_visible = AsyncMock(return_value=False)

    # Second element: nth() works, is_visible() throws "Can't query n-th element"
    mock_el2 = MagicMock(spec=Locator)
    mock_el2.is_visible = AsyncMock(side_effect=Exception("Can't query n-th element"))

    # Configure nth() to return different mocks
    mock_locator.nth = MagicMock(side_effect=[mock_el1, mock_el2])

    # Test that locate() doesn't crash and returns None
    result = await locate(mock_locator)

    assert result is None
    assert mock_locator.nth.call_count == 2
    mock_el1.is_visible.assert_called_once()
    mock_el2.is_visible.assert_called_once()


@pytest.mark.asyncio
async def test_locate_returns_first_visible_element():
    """Test locate() returns first visible element when available."""

    mock_locator = MagicMock(spec=Locator)
    mock_locator.count = AsyncMock(return_value=3)

    # First element: not visible
    mock_el1 = MagicMock(spec=Locator)
    mock_el1.is_visible = AsyncMock(return_value=False)

    # Second element: visible - should be returned
    mock_el2 = MagicMock(spec=Locator)
    mock_el2.is_visible = AsyncMock(return_value=True)

    # Third element: shouldn't be checked since we found visible one
    mock_el3 = MagicMock(spec=Locator)
    mock_el3.is_visible = AsyncMock(return_value=False)

    mock_locator.nth = MagicMock(side_effect=[mock_el1, mock_el2, mock_el3])

    result = await locate(mock_locator)

    assert result is mock_el2
    assert mock_locator.nth.call_count == 2  # Only checks first 2 elements


@pytest.mark.asyncio
async def test_locate_returns_none_when_no_elements():
    """Test locate() returns None when no elements match."""

    mock_locator = MagicMock(spec=Locator)
    mock_locator.count = AsyncMock(return_value=0)

    result = await locate(mock_locator)

    assert result is None
    mock_locator.nth.assert_not_called()
