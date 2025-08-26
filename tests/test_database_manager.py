import tempfile
import threading
import time
from pathlib import Path
from typing import Generator

import pytest

from getgather.db import DatabaseManager, db_manager


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

    def test_set_and_get_string(self, db_manager: DatabaseManager) -> None:
        """Test setting and getting string values."""
        db_manager.set("test_key", "test_value")
        value = db_manager.get("test_key")
        assert value == "test_value"

    def test_set_and_get_dict(self, db_manager: DatabaseManager) -> None:
        """Test setting and getting dictionary values."""
        test_dict = {"name": "test", "value": 123}
        db_manager.set("test_dict", test_dict)
        value = db_manager.get("test_dict")
        assert value == test_dict

    def test_set_and_get_list(self, db_manager: DatabaseManager) -> None:
        """Test setting and getting list values."""
        test_list = [1, 2, 3, "test"]
        db_manager.set("test_list", test_list)
        value = db_manager.get("test_list")
        assert value == test_list

    def test_get_nonexistent_key(self, db_manager: DatabaseManager) -> None:
        """Test getting a nonexistent key returns None."""
        value = db_manager.get("nonexistent")
        assert value is None

    def test_json_persistence(self, db_manager: DatabaseManager) -> None:
        """Test that data persists across manager instances."""
        db_manager.set("persistent_key", "persistent_value")

        # Create new manager instance with same file
        new_manager = DatabaseManager(json_file_path=db_manager.json_file_path)

        # Should be able to retrieve the data
        value = new_manager.get("persistent_key")
        assert value == "persistent_value"

    def test_json_file_corruption_handling(self, temp_json_file: Path) -> None:
        """Test handling of corrupted JSON file."""
        # Write invalid JSON to file
        with open(temp_json_file, "w") as f:
            f.write("invalid json content")

        db_manager = DatabaseManager(json_file_path=temp_json_file)

        # Should handle corruption gracefully and start fresh
        value = db_manager.get("nonexistent")
        assert value is None

        # Should be able to set new data
        db_manager.set("new_key", "new_value")
        value = db_manager.get("new_key")
        assert value == "new_value"

    def test_empty_file_handling(self, temp_json_file: Path) -> None:
        """Test handling of empty JSON file."""
        # Create empty file
        with open(temp_json_file, "w") as f:
            f.write("")

        db_manager = DatabaseManager(json_file_path=temp_json_file)

        # Should handle empty file gracefully
        value = db_manager.get("nonexistent")
        assert value is None

        # Should be able to set new data
        db_manager.set("new_key", "new_value")
        value = db_manager.get("new_key")
        assert value == "new_value"

    def test_in_memory_caching_single_load(self, db_manager: DatabaseManager) -> None:
        """Test that data is cached in memory after first load."""
        # Set initial data
        db_manager.set("cache_test", "initial_value")

        # Verify data attribute is populated
        assert db_manager.data is not None
        assert db_manager.data.get("cache_test") == "initial_value"

        # Get data - should use cached version
        value = db_manager.get("cache_test")
        assert value == "initial_value"

    def test_in_memory_caching_persistence(self, db_manager: DatabaseManager) -> None:
        """Test that cache is updated when data changes."""
        # Set initial data
        db_manager.set("cache_key", "value1")
        assert db_manager.data is not None
        assert db_manager.data.get("cache_key") == "value1"

        # Update data
        db_manager.set("cache_key", "value2")
        assert db_manager.data.get("cache_key") == "value2"

        # Verify get returns updated value
        value = db_manager.get("cache_key")
        assert value == "value2"

    def test_in_memory_caching_lazy_load(self, db_manager: DatabaseManager) -> None:
        """Test that data is only loaded when needed."""
        # Initially data should be None
        assert db_manager.data is None

        # First get should trigger load
        value = db_manager.get("nonexistent")
        assert db_manager.data is not None
        assert value is None

    def test_in_memory_caching_with_external_file_changes(
        self, db_manager: DatabaseManager
    ) -> None:
        """Test that cache doesn't interfere with external file changes."""
        # Set data through manager
        db_manager.set("external_test", "manager_value")

        # Manually modify the file (simulating external change)
        import json

        with open(db_manager.json_file_path, "w") as f:
            json.dump({"external_test": "external_value", "new_key": "new_value"}, f)

        # Create new manager instance - should read fresh data
        new_manager = DatabaseManager(json_file_path=db_manager.json_file_path)
        value = new_manager.get("external_test")
        assert value == "external_value"

        new_value = new_manager.get("new_key")
        assert new_value == "new_value"

    def test_thread_safety_concurrent_reads(self, db_manager: DatabaseManager) -> None:
        """Test that concurrent reads are thread-safe."""
        # Set initial data
        db_manager.set("thread_test", "initial_value")

        results: list[str] = []
        errors: list[Exception] = []

        def read_worker():
            try:
                for _ in range(100):
                    value = db_manager.get("thread_test")
                    results.append(value)
            except Exception as e:
                errors.append(e)

        # Start multiple reader threads
        threads = [threading.Thread(target=read_worker) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All reads should succeed and return correct value
        assert len(errors) == 0
        assert all(result == "initial_value" for result in results)
        assert len(results) == 500  # 5 threads * 100 reads each

    def test_thread_safety_concurrent_writes(self, db_manager: DatabaseManager) -> None:
        """Test that concurrent writes are thread-safe."""
        write_count = 20
        thread_count = 5
        results: list[tuple[str, str]] = []
        errors: list[Exception] = []

        def write_worker(thread_id: int):
            try:
                for i in range(write_count):
                    key = f"thread_{thread_id}_item_{i}"
                    value = f"value_{thread_id}_{i}"
                    db_manager.set(key, value)
                    results.append((key, value))
            except Exception as e:
                errors.append(e)

        # Start multiple writer threads
        threads = [threading.Thread(target=write_worker, args=(i,)) for i in range(thread_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All writes should succeed
        assert len(errors) == 0
        assert len(results) == thread_count * write_count

        # Verify all written data is accessible
        for key, expected_value in results:
            actual_value = db_manager.get(key)
            assert actual_value == expected_value

    def test_thread_safety_mixed_operations(self, db_manager: DatabaseManager) -> None:
        """Test thread safety with mixed read/write operations."""
        # Set initial data
        for i in range(10):
            db_manager.set(f"initial_{i}", f"value_{i}")

        read_results: list[str] = []
        write_results: list[tuple[str, str]] = []
        errors: list[Exception] = []

        def reader_worker():
            try:
                for _ in range(50):
                    key = f"initial_{_ % 10}"
                    value = db_manager.get(key)
                    read_results.append(value)
                    time.sleep(0.001)  # Small delay to increase contention
            except Exception as e:
                errors.append(e)

        def writer_worker(thread_id: int):
            try:
                for i in range(25):
                    key = f"writer_{thread_id}_{i}"
                    value = f"written_{thread_id}_{i}"
                    db_manager.set(key, value)
                    write_results.append((key, value))
                    time.sleep(0.001)  # Small delay to increase contention
            except Exception as e:
                errors.append(e)

        # Start mixed reader and writer threads
        reader_threads = [threading.Thread(target=reader_worker) for _ in range(3)]
        writer_threads = [threading.Thread(target=writer_worker, args=(i,)) for i in range(2)]

        all_threads = reader_threads + writer_threads
        for thread in all_threads:
            thread.start()
        for thread in all_threads:
            thread.join()

        # All operations should succeed
        assert len(errors) == 0
        assert len(read_results) == 150  # 3 threads * 50 reads each
        assert len(write_results) == 50  # 2 threads * 25 writes each

        # Verify written data is accessible
        for key, expected_value in write_results:
            actual_value = db_manager.get(key)
            assert actual_value == expected_value
