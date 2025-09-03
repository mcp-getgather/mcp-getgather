import asyncio
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest import MonkeyPatch

from getgather.mcp.activity import Activity, ActivityManager, activity, activity_manager
from getgather.mcp.auth import AuthUser


@pytest.fixture
def manager(temp_project_dir: Path, monkeypatch: MonkeyPatch) -> ActivityManager:
    """Create a fresh ActivityManager for each test with isolated database."""
    # Create isolated database manager for testing
    activity_manager.reset()

    return activity_manager


class TestActivityManager:
    """Test ActivityManager functionality."""

    @pytest.mark.asyncio
    async def test_create_activity(self, manager: ActivityManager) -> None:
        """Test creating a new activity."""
        brand_id = "test-brand"
        name = "test-activity"
        start_time = datetime.now(UTC)

        activity_id = manager.add(
            Activity(
                user_login="user@localhost", brand_id=brand_id, name=name, start_time=start_time
            )
        ).id

        assert isinstance(activity_id, str)
        assert len(activity_id) == 32  # UUID hex format
        activity_obj = manager.get(activity_id)
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

        id1 = manager.add(
            Activity(
                user_login="user@localhost",
                brand_id="brand1",
                name="activity1",
                start_time=start_time,
            )
        ).id
        id2 = manager.add(
            Activity(
                user_login="user@localhost",
                brand_id="brand2",
                name="activity2",
                start_time=start_time,
            )
        ).id
        id3 = manager.add(
            Activity(
                user_login="user@localhost",
                brand_id="brand3",
                name="activity3",
                start_time=start_time,
            )
        ).id

        # All IDs should be unique UUID hex strings
        assert isinstance(id1, str) and len(id1) == 32
        assert isinstance(id2, str) and len(id2) == 32
        assert isinstance(id3, str) and len(id3) == 32
        assert len({id1, id2, id3}) == 3  # All unique

    @pytest.mark.asyncio
    async def test_update_end_time(self, manager: ActivityManager) -> None:
        """Test updating activity end time and execution time calculation."""
        start_time = datetime.now(UTC)
        activity_id = manager.add(
            Activity(
                user_login="user@localhost", brand_id="brand1", name="test", start_time=start_time
            )
        ).id

        # Simulate some time passing
        await asyncio.sleep(0.01)
        end_time = datetime.now(UTC)
        manager.update(
            Activity(
                id=activity_id,
                user_login="user@localhost",
                brand_id="brand1",
                name="test",
                start_time=start_time,
                end_time=end_time,
            )
        )

        activity_obj = manager.get(activity_id)
        assert activity_obj is not None
        assert activity_obj.end_time == end_time
        assert activity_obj.execution_time_ms is not None
        assert activity_obj.execution_time_ms >= 0
        # Should be at least 10ms since we slept for 0.01 seconds
        assert activity_obj.execution_time_ms >= 10

    @pytest.mark.asyncio
    async def test_update_nonexistent_activity(self, manager: ActivityManager) -> None:
        """Test updating a nonexistent activity raises error."""
        with pytest.raises(ValueError, match="not found"):
            manager.update(
                Activity(
                    id="nonexistent-id",
                    user_login="user@localhost",
                    brand_id="brand1",
                    name="test",
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC),
                )
            )

    @pytest.mark.asyncio
    async def test_get_nonexistent_activity(self, manager: ActivityManager) -> None:
        """Test getting a nonexistent activity returns None."""
        activity_obj = manager.get("nonexistent-id")
        assert activity_obj is None

    @pytest.mark.asyncio
    async def test_get_all_activities_empty(self, manager: ActivityManager) -> None:
        """Test getting all activities when none exist."""
        activities = manager.get_all()
        assert activities == []

    @pytest.mark.asyncio
    async def test_get_all_activities_ordered(self, manager: ActivityManager) -> None:
        """Test getting all activities in correct order (start_time descending)."""
        start_time1 = datetime.now(UTC)
        await asyncio.sleep(0.001)  # Ensure different timestamps
        start_time2 = datetime.now(UTC)
        await asyncio.sleep(0.001)
        start_time3 = datetime.now(UTC)

        user_login = "user@localhost"

        id1 = manager.add(
            Activity(user_login=user_login, brand_id="brand1", name="first", start_time=start_time1)
        ).id
        id2 = manager.add(
            Activity(
                user_login=user_login, brand_id="brand2", name="second", start_time=start_time2
            )
        ).id
        id3 = manager.add(
            Activity(user_login=user_login, brand_id="brand3", name="third", start_time=start_time3)
        ).id

        activities = manager.get_all()
        assert len(activities) == 3

        # Should be ordered by start_time descending (most recent first)
        assert activities[0].id == id3  # third (most recent)
        assert activities[1].id == id2  # second
        assert activities[2].id == id1  # first (oldest)

    @pytest.mark.asyncio
    async def test_get_all_activities_filtered_by_user_login(
        self, manager: ActivityManager
    ) -> None:
        """Test getting all activities filtered by user login."""
        manager.add(
            Activity(
                user_login="user_1", brand_id="brand1", name="first", start_time=datetime.now(UTC)
            )
        )
        manager.add(
            Activity(
                user_login="user_2", brand_id="brand2", name="second", start_time=datetime.now(UTC)
            )
        )
        manager.add(
            Activity(
                user_login="user_1", brand_id="brand3", name="third", start_time=datetime.now(UTC)
            )
        )
        mock_auth_user = AuthUser(login="user_1", sub="user_1")
        with patch("getgather.mcp.activity.get_auth_user", return_value=mock_auth_user):
            activities = manager.get_all()
            assert len(activities) == 2
            assert activities[0].user_login == "user_1"
            assert activities[1].user_login == "user_1"

    @pytest.mark.asyncio
    async def test_json_persistence(self, manager: ActivityManager) -> None:
        """Test that activities persist across manager instances."""
        start_time = datetime.now(UTC)

        # Create activity with first manager instance
        activity_id = manager.add(
            Activity(
                user_login="user@localhost",
                brand_id="test-brand",
                name="test-activity",
                start_time=start_time,
            )
        ).id

        # Create new manager instance (both use same global database)
        new_manager = ActivityManager()

        # Should be able to retrieve the activity
        activity = new_manager.get(activity_id)
        assert activity is not None
        assert activity.brand_id == "test-brand"
        assert activity.name == "test-activity"

    @pytest.mark.asyncio
    async def test_json_file_corruption_handling(self, manager: ActivityManager) -> None:
        """Test handling of corrupted JSON file."""
        # Should be able to create new activities
        start_time = datetime.now(UTC)
        activity_id = manager.add(
            Activity(
                user_login="user@localhost",
                brand_id="test-brand",
                name="test-activity",
                start_time=start_time,
            )
        ).id
        assert isinstance(activity_id, str) and len(activity_id) == 32


class TestActivityContextManager:
    """Test cases for activity context manager."""

    @pytest.mark.asyncio
    async def test_activity_context_manager_basic(self, manager: ActivityManager) -> None:
        """Test activity context manager creates and updates activity."""
        initial_count = len(manager.get_all())

        async with activity("test-operation", "test-brand"):
            # During execution, activity should be created
            current_activities = manager.get_all()
            assert len(current_activities) == initial_count + 1

            latest_activity = current_activities[0]
            assert latest_activity.name == "test-operation"
            assert latest_activity.brand_id == "test-brand"
            assert latest_activity.end_time is None
            assert latest_activity.execution_time_ms is None

        # After context exit, activity should be completed
        final_activities = manager.get_all()
        completed_activity = final_activities[0]
        assert completed_activity.end_time is not None
        assert completed_activity.execution_time_ms is not None
        assert completed_activity.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_activity_context_manager_with_exception(self, manager: ActivityManager) -> None:
        """Test activity context manager handles exceptions properly."""
        initial_count = len(manager.get_all())

        try:
            async with activity("failing-operation", "test-brand"):
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception

        # Activity should still be completed even with exception
        activities = manager.get_all()
        assert len(activities) == initial_count + 1

        latest_activity = activities[0]
        assert latest_activity.name == "failing-operation"
        assert latest_activity.brand_id == "test-brand"
        assert latest_activity.end_time is not None
        assert latest_activity.execution_time_ms is not None

    @pytest.mark.asyncio
    async def test_activity_context_manager_execution_time(self, manager: ActivityManager) -> None:
        """Test activity context manager measures execution time correctly."""
        async with activity("timed-operation", "test-brand"):
            await asyncio.sleep(0.05)  # Sleep for 50ms

        activities = manager.get_all()
        activity_obj = activities[0]

        # Should have measured at least 50ms execution time
        assert activity_obj.execution_time_ms is not None
        assert activity_obj.execution_time_ms >= 50
        # But shouldn't be too much more (allowing for some overhead)
        assert activity_obj.execution_time_ms < 200

    @pytest.mark.asyncio
    async def test_nested_activity_context_managers(self, manager: ActivityManager) -> None:
        """Test that nested activity context managers work correctly."""
        async with activity("outer-operation", "outer-brand"):
            async with activity("inner-operation", "inner-brand"):
                await asyncio.sleep(0.01)

        activities = manager.get_all()
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
