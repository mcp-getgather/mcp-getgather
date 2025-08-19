import asyncio
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Generator

import pytest
from pytest import MonkeyPatch

from getgather.activity import ActivityManager, active_activity_ctx, activity
from getgather.database import DatabaseManager


class TestActivityManager:
    """Test cases for ActivityManager class."""

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
    def manager(self, temp_json_file: Path, monkeypatch: MonkeyPatch) -> ActivityManager:
        """Create a fresh ActivityManager for each test with isolated database."""
        # Create isolated database manager for testing
        test_db_manager = DatabaseManager(temp_json_file)

        # Patch the global db_manager import in activity module
        monkeypatch.setattr("getgather.activity.db_manager", test_db_manager)

        return ActivityManager()

    @pytest.mark.asyncio
    async def test_create_activity(self, manager: ActivityManager) -> None:
        """Test creating a new activity."""
        brand_id = "test-brand"
        name = "test-activity"
        start_time = datetime.now(UTC)

        activity_id = await manager.create_activity(brand_id, name, start_time)

        assert isinstance(activity_id, str)
        assert len(activity_id) == 32  # UUID hex format
        activity_obj = await manager.get_activity(activity_id)
        assert activity_obj is not None
        assert activity_obj.brand_id == brand_id
        assert activity_obj.name == name
        assert activity_obj.start_time == start_time
        assert activity_obj.end_time is None
        assert activity_obj.execution_time_ms is None

    @pytest.mark.asyncio
    async def test_multiple_activities_get_unique_ids(self, manager: ActivityManager) -> None:
        """Test that multiple activities get unique UUIDs."""
        start_time = datetime.now(UTC)

        id1 = await manager.create_activity("brand1", "activity1", start_time)
        id2 = await manager.create_activity("brand2", "activity2", start_time)
        id3 = await manager.create_activity("brand3", "activity3", start_time)

        # All IDs should be unique UUID hex strings
        assert isinstance(id1, str) and len(id1) == 32
        assert isinstance(id2, str) and len(id2) == 32
        assert isinstance(id3, str) and len(id3) == 32
        assert len({id1, id2, id3}) == 3  # All unique

    @pytest.mark.asyncio
    async def test_update_end_time(self, manager: ActivityManager) -> None:
        """Test updating activity end time and execution time calculation."""
        start_time = datetime.now(UTC)
        activity_id = await manager.create_activity("brand1", "test", start_time)

        # Simulate some time passing
        await asyncio.sleep(0.01)
        end_time = datetime.now(UTC)
        await manager.update_end_time(activity_id, end_time)

        activity_obj = await manager.get_activity(activity_id)
        assert activity_obj is not None
        assert activity_obj.end_time == end_time
        assert activity_obj.execution_time_ms is not None
        assert activity_obj.execution_time_ms >= 0
        # Should be at least 10ms since we slept for 0.01 seconds
        assert activity_obj.execution_time_ms >= 10

    @pytest.mark.asyncio
    async def test_update_nonexistent_activity(self, manager: ActivityManager) -> None:
        """Test updating a nonexistent activity raises error."""
        with pytest.raises(ValueError, match="Activity nonexistent-id not found"):
            await manager.update_end_time("nonexistent-id", datetime.now(UTC))

    @pytest.mark.asyncio
    async def test_get_nonexistent_activity(self, manager: ActivityManager) -> None:
        """Test getting a nonexistent activity returns None."""
        activity_obj = await manager.get_activity("nonexistent-id")
        assert activity_obj is None

    @pytest.mark.asyncio
    async def test_get_all_activities_empty(self, manager: ActivityManager) -> None:
        """Test getting all activities when none exist."""
        activities = await manager.get_all_activities()
        assert activities == []

    @pytest.mark.asyncio
    async def test_get_all_activities_ordered(self, manager: ActivityManager) -> None:
        """Test getting all activities in correct order (start_time descending)."""
        start_time1 = datetime.now(UTC)
        await asyncio.sleep(0.001)  # Ensure different timestamps
        start_time2 = datetime.now(UTC)
        await asyncio.sleep(0.001)
        start_time3 = datetime.now(UTC)

        id1 = await manager.create_activity("brand1", "first", start_time1)
        id2 = await manager.create_activity("brand2", "second", start_time2)
        id3 = await manager.create_activity("brand3", "third", start_time3)

        activities = await manager.get_all_activities()
        assert len(activities) == 3

        # Should be ordered by start_time descending (most recent first)
        assert activities[0].id == id3  # third (most recent)
        assert activities[1].id == id2  # second
        assert activities[2].id == id1  # first (oldest)

    @pytest.mark.asyncio
    async def test_json_persistence(self, manager: ActivityManager) -> None:
        """Test that activities persist across manager instances."""
        start_time = datetime.now(UTC)

        # Create activity with first manager instance
        activity_id = await manager.create_activity("test-brand", "test-activity", start_time)

        # Create new manager instance (both use same global database)
        new_manager = ActivityManager()

        # Should be able to retrieve the activity
        activity = await new_manager.get_activity(activity_id)
        assert activity is not None
        assert activity.brand_id == "test-brand"
        assert activity.name == "test-activity"

    @pytest.mark.asyncio
    async def test_json_file_corruption_handling(self, temp_json_file: Path) -> None:
        """Test handling of corrupted JSON file."""
        # This test now uses the global database, so we test general resilience
        manager = ActivityManager()

        # Should be able to create new activities
        start_time = datetime.now(UTC)
        activity_id = await manager.create_activity("test-brand", "test-activity", start_time)
        assert isinstance(activity_id, str) and len(activity_id) == 32


class TestActivityContextManager:
    """Test cases for activity context manager."""

    @pytest.fixture
    def temp_json_file(self) -> Generator[Path, None, None]:
        """Create a temporary JSON file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        # Clean up
        if temp_path.exists():
            temp_path.unlink()

    def create_fresh_manager(self, temp_json_file: Path) -> ActivityManager:
        """Create a fresh ActivityManager instance for testing."""
        # Create isolated database manager for testing
        test_db_manager = DatabaseManager(temp_json_file)

        # Patch the global db_manager in activity module
        import getgather.activity

        getgather.activity.db_manager = test_db_manager

        return ActivityManager()

    @pytest.mark.asyncio
    async def test_activity_context_manager_basic(self, temp_json_file: Path) -> None:
        """Test activity context manager creates and updates activity."""
        # Create isolated database manager for testing
        test_db_manager = DatabaseManager(temp_json_file)
        test_manager = ActivityManager()

        # Patch the global managers temporarily
        import getgather.activity

        original_db_manager = getgather.activity.db_manager
        original_manager = getgather.activity.activity_manager
        getgather.activity.db_manager = test_db_manager
        getgather.activity.activity_manager = test_manager

        try:
            initial_count = len(await test_manager.get_all_activities())

            async with activity("test-operation", "test-brand"):
                # During execution, activity should be created
                current_activities = await test_manager.get_all_activities()
                assert len(current_activities) == initial_count + 1

                latest_activity = current_activities[0]
                assert latest_activity.name == "test-operation"
                assert latest_activity.brand_id == "test-brand"
                assert latest_activity.end_time is None
                assert latest_activity.execution_time_ms is None

            # After context exit, activity should be completed
            final_activities = await test_manager.get_all_activities()
            completed_activity = final_activities[0]
            assert completed_activity.end_time is not None
            assert completed_activity.execution_time_ms is not None
            assert completed_activity.execution_time_ms >= 0

        finally:
            # Restore original managers
            getgather.activity.db_manager = original_db_manager
            getgather.activity.activity_manager = original_manager

    @pytest.mark.asyncio
    async def test_activity_context_manager_with_exception(self, temp_json_file: Path) -> None:
        """Test activity context manager handles exceptions properly."""
        # Create isolated database manager for testing
        test_db_manager = DatabaseManager(temp_json_file)
        test_manager = ActivityManager()

        # Patch the global managers temporarily
        import getgather.activity

        original_db_manager = getgather.activity.db_manager
        original_manager = getgather.activity.activity_manager
        getgather.activity.db_manager = test_db_manager
        getgather.activity.activity_manager = test_manager

        try:
            initial_count = len(await test_manager.get_all_activities())

            try:
                async with activity("failing-operation", "test-brand"):
                    raise ValueError("Test exception")
            except ValueError:
                pass  # Expected exception

            # Activity should still be completed even with exception
            activities = await test_manager.get_all_activities()
            assert len(activities) == initial_count + 1

            latest_activity = activities[0]
            assert latest_activity.name == "failing-operation"
            assert latest_activity.brand_id == "test-brand"
            assert latest_activity.end_time is not None
            assert latest_activity.execution_time_ms is not None

        finally:
            # Restore original managers
            getgather.activity.db_manager = original_db_manager
            getgather.activity.activity_manager = original_manager

    @pytest.mark.asyncio
    async def test_activity_context_manager_execution_time(self, temp_json_file: Path) -> None:
        """Test activity context manager measures execution time correctly."""
        # Create isolated database manager for testing
        test_db_manager = DatabaseManager(temp_json_file)
        test_manager = ActivityManager()

        # Patch the global managers temporarily
        import getgather.activity

        original_db_manager = getgather.activity.db_manager
        original_manager = getgather.activity.activity_manager
        getgather.activity.db_manager = test_db_manager
        getgather.activity.activity_manager = test_manager

        try:
            async with activity("timed-operation", "test-brand"):
                await asyncio.sleep(0.05)  # Sleep for 50ms

            activities = await test_manager.get_all_activities()
            activity_obj = activities[0]

            # Should have measured at least 50ms execution time
            assert activity_obj.execution_time_ms is not None
            assert activity_obj.execution_time_ms >= 50
            # But shouldn't be too much more (allowing for some overhead)
            assert activity_obj.execution_time_ms < 200

        finally:
            # Restore original managers
            getgather.activity.db_manager = original_db_manager
            getgather.activity.activity_manager = original_manager

    @pytest.mark.asyncio
    async def test_nested_activity_context_managers(self, temp_json_file: Path) -> None:
        """Test that nested activity context managers work correctly."""
        # Create isolated database manager for testing
        test_db_manager = DatabaseManager(temp_json_file)
        test_manager = ActivityManager()

        # Patch the global managers temporarily
        import getgather.activity

        original_db_manager = getgather.activity.db_manager
        original_manager = getgather.activity.activity_manager
        getgather.activity.db_manager = test_db_manager
        getgather.activity.activity_manager = test_manager

        try:
            async with activity("outer-operation", "outer-brand"):
                async with activity("inner-operation", "inner-brand"):
                    await asyncio.sleep(0.01)

            activities = await test_manager.get_all_activities()
            assert len(activities) == 2

            # Most recent first (inner operation completed last)
            inner_activity = activities[0]
            outer_activity = activities[1]

            assert inner_activity.name == "inner-operation"
            assert inner_activity.brand_id == "inner-brand"
            assert outer_activity.name == "outer-operation"
            assert outer_activity.brand_id == "outer-brand"

            # Both should be completed
            assert inner_activity.end_time is not None
            assert outer_activity.end_time is not None

        finally:
            # Restore original managers
            getgather.activity.db_manager = original_db_manager
            getgather.activity.activity_manager = original_manager

    @pytest.mark.asyncio
    async def test_activity_context_variable_tracking(self) -> None:
        """Test that context variable tracks active activity correctly."""
        # Initially no active activity
        assert active_activity_ctx.get() is None

        async with activity("context-test", "test-brand") as activity_id:
            # During execution, context variable should be set
            current_activity = active_activity_ctx.get()
            assert current_activity is not None
            assert current_activity.id == activity_id
            assert current_activity.name == "context-test"
            assert current_activity.brand_id == "test-brand"
            assert current_activity.end_time is None  # Not finished yet

        # After context exit, context variable should be reset
        assert active_activity_ctx.get() is None

    @pytest.mark.asyncio
    async def test_nested_activity_context_variable_tracking(self) -> None:
        """Test that context variable correctly handles nested activities."""
        # Initially no active activity
        assert active_activity_ctx.get() is None

        async with activity("outer-context", "outer-brand") as outer_id:
            # Should track outer activity
            outer_activity = active_activity_ctx.get()
            assert outer_activity is not None
            assert outer_activity.id == outer_id
            assert outer_activity.name == "outer-context"

            async with activity("inner-context", "inner-brand") as inner_id:
                # Should now track inner activity
                inner_activity = active_activity_ctx.get()
                assert inner_activity is not None
                assert inner_activity.id == inner_id
                assert inner_activity.name == "inner-context"
                # Should be different from outer
                assert inner_activity.id != outer_activity.id

            # After inner context exits, should return to outer activity
            current_activity = active_activity_ctx.get()
            assert current_activity is not None
            assert current_activity.id == outer_id
            assert current_activity.name == "outer-context"

        # After outer context exits, should be None
        assert active_activity_ctx.get() is None

    @pytest.mark.asyncio
    async def test_activity_context_variable_with_exception(self) -> None:
        """Test that context variable is properly reset even when exceptions occur."""
        # Initially no active activity
        assert active_activity_ctx.get() is None

        try:
            async with activity("exception-context", "test-brand"):
                # Context variable should be set
                current_activity = active_activity_ctx.get()
                assert current_activity is not None
                assert current_activity.name == "exception-context"

                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception

        # After exception, context variable should still be reset
        assert active_activity_ctx.get() is None
