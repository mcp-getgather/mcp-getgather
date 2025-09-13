import shutil
import threading
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from getgather.config import settings
from getgather.mcp.persist import PersistentStore


# Test models
class ExampleUser(BaseModel):
    id: str
    name: str
    email: str


class ExamplePersistentStore(PersistentStore[ExampleUser]):
    _row_model = ExampleUser
    _file_name = "test_users.json"
    _key_field = "id"

    def get_indexes_count(self) -> int:
        """Helper method to get index count for testing."""
        return len(self._indexes)

    def has_key_in_index(self, key: str) -> bool:
        """Helper method to check if key exists in index for testing."""
        return key in self._indexes


def clear_singleton_instances():
    """Helper function to clear singleton instances for testing."""
    # Access the class-level _instances dict directly using getattr to avoid protected access warnings
    instances_dict = getattr(PersistentStore, "_instances", None)
    if instances_dict is not None:
        instances_dict.clear()


@pytest.fixture
def store(temp_project_dir: Path) -> ExamplePersistentStore:
    """Create a fresh PersistentStore for each test with isolated storage."""
    # Clear singleton instances to ensure fresh store
    clear_singleton_instances()

    return ExamplePersistentStore()


class TestPersistentStoreBasic:
    """Test basic PersistentStore functionality."""

    def test_file_path_property(self, store: ExamplePersistentStore):
        """Test that file_path property returns correct path."""
        expected_path = settings.persistent_store_dir / "test_users.json"
        assert store.file_path == expected_path

    def test_key_extraction(self, store: ExamplePersistentStore):
        """Test key extraction from model."""
        user = ExampleUser(id="123", name="John Doe", email="john@example.com")
        assert store.row_key_for_retrieval(user) == "123"

    def test_index_key(self, store: ExamplePersistentStore):
        """Test index key generation."""
        assert store.key_for_retrieval("test-key") == "test-key"

    def test_add_user(self, store: ExamplePersistentStore):
        """Test adding a new user."""
        user = ExampleUser(id="123", name="John Doe", email="john@example.com")

        result = store.add(user)

        assert result == user
        assert len(store.rows) == 1
        assert store.rows[0] == user
        assert store.has_key_in_index("123")
        assert store.get_indexes_count() == 1

    def test_add_duplicate_user_raises_error(self, store: ExamplePersistentStore):
        """Test that adding a duplicate user raises ValueError."""
        user1 = ExampleUser(id="123", name="John Doe", email="john@example.com")
        user2 = ExampleUser(id="123", name="Jane Doe", email="jane@example.com")

        store.add(user1)

        with pytest.raises(ValueError, match="Row with key 123 already exists"):
            store.add(user2)

    def test_get_existing_user(self, store: ExamplePersistentStore):
        """Test getting an existing user."""
        user = ExampleUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        result = store.get("123")

        assert result == user

    def test_get_nonexistent_user(self, store: ExamplePersistentStore):
        """Test getting a nonexistent user returns None."""
        result = store.get("nonexistent")

        assert result is None

    def test_update_existing_user(self, store: ExamplePersistentStore):
        """Test updating an existing user."""
        user = ExampleUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        updated_user = ExampleUser(id="123", name="John Smith", email="johnsmith@example.com")
        result = store.update(updated_user)

        assert result == updated_user
        assert store.rows[0] == updated_user
        assert store.has_key_in_index("123")

    def test_update_nonexistent_user_raises_error(self, store: ExamplePersistentStore):
        """Test that updating a nonexistent user raises ValueError."""
        user = ExampleUser(id="nonexistent", name="John Doe", email="john@example.com")

        with pytest.raises(ValueError, match="Row with key nonexistent not found"):
            store.update(user)

    def test_reset(self, store: ExamplePersistentStore):
        """Test resetting the store."""
        user = ExampleUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        store.reset()

        assert len(store.rows) == 0
        assert store.get_indexes_count() == 0

    def test_persistence_across_instances(self, temp_project_dir: Path):
        """Test that data persists across different store instances."""
        # Clear singleton instances
        clear_singleton_instances()

        # Create first store and add user
        store1 = ExamplePersistentStore()
        user = ExampleUser(id="123", name="John Doe", email="john@example.com")
        store1.add(user)

        # Clear singleton instances to simulate new instance
        clear_singleton_instances()

        # Create second store and verify user exists
        store2 = ExamplePersistentStore()
        result = store2.get("123")

        assert result == user

    def test_load_from_empty_file(self, store: ExamplePersistentStore):
        """Test loading when file doesn't exist."""
        # Should not raise error
        store.load()

        assert len(store.rows) == 0
        assert store.get_indexes_count() == 0

    def test_concurrent_access(self, store: ExamplePersistentStore):
        """Test concurrent access to store."""
        users = [
            ExampleUser(id=f"user{i}", name=f"User {i}", email=f"user{i}@example.com")
            for i in range(10)
        ]

        def add_user(user: ExampleUser):
            store.add(user)

        threads: list[threading.Thread] = [
            threading.Thread(target=add_user, args=(user,)) for user in users
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(store.rows) == 10
        for i in range(10):
            assert store.get(f"user{i}") is not None


class TestSingletonBehavior:
    """Test singleton behavior of persistent stores."""

    def test_singleton_behavior(self, temp_project_dir: Path):
        """Test that stores behave as singletons."""
        # Clear singleton instances
        clear_singleton_instances()

        store1 = ExamplePersistentStore()
        store2 = ExamplePersistentStore()

        # Should be the same instance
        assert store1 is store2

    def test_different_store_types_are_separate_singletons(self, temp_project_dir: Path):
        """Test that different store types maintain separate singleton instances."""
        # Clear singleton instances
        clear_singleton_instances()

        class AnotherExamplePersistentStore(PersistentStore[ExampleUser]):
            _row_model = ExampleUser
            _file_name = "test_users_another.json"
            _key_field = "id"

        store = ExamplePersistentStore()
        auth_store = AnotherExamplePersistentStore()

        # Should be different instances
        assert store is not auth_store
        assert type(store) != type(auth_store)


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_key_field_validation(self):
        """Test validation fails for invalid key field."""

        class InvalidTestStore(PersistentStore[ExampleUser]):
            _row_model = ExampleUser
            _file_name = "test.json"
            _key_field = "nonexistent_field"  # Invalid field

        with pytest.raises(ValidationError):
            InvalidTestStore()

    def test_file_path_creation(self, store: ExamplePersistentStore):
        """Test that directory is created if it doesn't exist."""
        # Ensure directory doesn't exist initially
        if store.file_path.parent.exists():
            shutil.rmtree(store.file_path.parent)

        user = ExampleUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        # Directory should be created
        assert store.file_path.parent.exists()
        assert store.file_path.exists()


class TestThreadSafety:
    """Test thread safety of persistent stores."""

    def test_concurrent_adds_different_keys(self, store: ExamplePersistentStore):
        """Test concurrent adds with different keys."""

        def add_users(start_idx: int, count: int):
            for i in range(start_idx, start_idx + count):
                user = ExampleUser(id=f"user{i}", name=f"User {i}", email=f"user{i}@example.com")
                store.add(user)

        threads: list[threading.Thread] = []
        for i in range(5):
            thread = threading.Thread(target=add_users, args=(i * 10, 10))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should have all 50 users
        assert len(store.rows) == 50
        for i in range(50):
            assert store.get(f"user{i}") is not None

    def test_concurrent_updates(self, store: ExamplePersistentStore):
        """Test concurrent updates to the same user."""
        # First add a user
        user = ExampleUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        def update_user(name_suffix: str):
            updated_user = ExampleUser(
                id="123", name=f"John Doe {name_suffix}", email="john@example.com"
            )
            store.update(updated_user)

        threads: list[threading.Thread] = []
        for i in range(10):
            thread = threading.Thread(target=update_user, args=(str(i),))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should still have exactly one user with ID "123"
        result = store.get("123")
        assert result is not None
        assert result.id == "123"
        assert len(store.rows) == 1
