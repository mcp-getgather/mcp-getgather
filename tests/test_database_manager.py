import tempfile
from pathlib import Path
from typing import Generator

import pytest

from getgather.database import DatabaseManager, db_manager


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    @pytest.fixture
    def temp_json_file(self) -> Generator[Path, None, None]:
        """Create a temporary JSON file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        # Clean up
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def db_manager(self, temp_json_file: Path) -> DatabaseManager:
        """Create a fresh DatabaseManager for each test."""
        return DatabaseManager(json_file_path=temp_json_file)

    @pytest.mark.asyncio
    async def test_set_and_get_string(self, db_manager: DatabaseManager) -> None:
        """Test setting and getting string values."""
        await db_manager.set("test_key", "test_value")
        value = await db_manager.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_set_and_get_dict(self, db_manager: DatabaseManager) -> None:
        """Test setting and getting dictionary values."""
        test_dict = {"name": "test", "value": 123}
        await db_manager.set("test_dict", test_dict)
        value = await db_manager.get("test_dict")
        assert value == test_dict

    @pytest.mark.asyncio
    async def test_set_and_get_list(self, db_manager: DatabaseManager) -> None:
        """Test setting and getting list values."""
        test_list = [1, 2, 3, "test"]
        await db_manager.set("test_list", test_list)
        value = await db_manager.get("test_list")
        assert value == test_list

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, db_manager: DatabaseManager) -> None:
        """Test getting a nonexistent key returns None."""
        value = await db_manager.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_exists(self, db_manager: DatabaseManager) -> None:
        """Test checking if keys exist."""
        assert not await db_manager.exists("test_key")

        await db_manager.set("test_key", "value")
        assert await db_manager.exists("test_key")

    @pytest.mark.asyncio
    async def test_delete(self, db_manager: DatabaseManager) -> None:
        """Test deleting keys."""
        await db_manager.set("test_key", "value")
        assert await db_manager.exists("test_key")

        result = await db_manager.delete("test_key")
        assert result is True
        assert not await db_manager.exists("test_key")

        # Deleting non-existent key should return False
        result = await db_manager.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_keys(self, db_manager: DatabaseManager) -> None:
        """Test getting all keys."""
        keys = await db_manager.keys()
        assert keys == []

        await db_manager.set("key1", "value1")
        await db_manager.set("key2", "value2")

        keys = await db_manager.keys()
        assert set(keys) == {"key1", "key2"}

    @pytest.mark.asyncio
    async def test_clear(self, db_manager: DatabaseManager) -> None:
        """Test clearing all data."""
        await db_manager.set("key1", "value1")
        await db_manager.set("key2", "value2")

        keys = await db_manager.keys()
        assert len(keys) == 2

        await db_manager.clear()

        keys = await db_manager.keys()
        assert keys == []

    @pytest.mark.asyncio
    async def test_json_persistence(self, db_manager: DatabaseManager) -> None:
        """Test that data persists across manager instances."""
        await db_manager.set("persistent_key", "persistent_value")

        # Create new manager instance with same file
        new_manager = DatabaseManager(json_file_path=db_manager.json_file_path)

        # Should be able to retrieve the data
        value = await new_manager.get("persistent_key")
        assert value == "persistent_value"

    @pytest.mark.asyncio
    async def test_json_file_corruption_handling(self, temp_json_file: Path) -> None:
        """Test handling of corrupted JSON file."""
        # Write invalid JSON to file
        with open(temp_json_file, "w") as f:
            f.write("invalid json content")

        db_manager = DatabaseManager(json_file_path=temp_json_file)

        # Should handle corruption gracefully and start fresh
        keys = await db_manager.keys()
        assert keys == []

        # Should be able to set new data
        await db_manager.set("new_key", "new_value")
        value = await db_manager.get("new_key")
        assert value == "new_value"

    @pytest.mark.asyncio
    async def test_empty_file_handling(self, temp_json_file: Path) -> None:
        """Test handling of empty JSON file."""
        # Create empty file
        with open(temp_json_file, "w") as f:
            f.write("")

        db_manager = DatabaseManager(json_file_path=temp_json_file)

        # Should handle empty file gracefully
        keys = await db_manager.keys()
        assert keys == []

        # Should be able to set new data
        await db_manager.set("new_key", "new_value")
        value = await db_manager.get("new_key")
        assert value == "new_value"


class TestGlobalDatabaseManager:
    """Test cases for the global db_manager instance."""

    @pytest.mark.asyncio
    async def test_global_instance_exists(self) -> None:
        """Test that global db_manager instance exists and works."""
        # The global instance should be available
        assert db_manager is not None
        assert isinstance(db_manager, DatabaseManager)

        # Should be able to use it for basic operations
        await db_manager.set("test_global", "global_value")
        value = await db_manager.get("test_global")
        assert value == "global_value"

        # Clean up
        await db_manager.delete("test_global")
