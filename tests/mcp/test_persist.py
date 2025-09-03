import shutil
import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import BaseModel, ValidationError

from getgather.config import settings
from getgather.mcp.auth import AuthUser
from getgather.mcp.persist import ModelWithAuth, PersistentStore, PersistentStoreWithAuth


# Test models
class TestUser(BaseModel):
    id: str
    name: str
    email: str


class TestUserWithAuth(ModelWithAuth):
    id: str
    name: str
    email: str
    user_login: str


class TestPersistentStore(PersistentStore[TestUser]):
    _row_model = TestUser
    _file_name = "test_users.json"
    _key_field = "id"

    def get_indexes_count(self) -> int:
        """Helper method to get index count for testing."""
        return len(self._indexes)

    def has_key_in_index(self, key: str) -> bool:
        """Helper method to check if key exists in index for testing."""
        return key in self._indexes


class TestPersistentStoreWithAuth(PersistentStoreWithAuth[TestUserWithAuth]):
    _row_model = TestUserWithAuth
    _file_name = "test_users_auth.json"
    _key_field = "id"

    def get_indexes_count(self) -> int:
        """Helper method to get index count for testing."""
        return len(self._indexes)

    def has_key_in_index(self, key: tuple[str, str] | str) -> bool:
        """Helper method to check if key exists in index for testing."""
        return key in self._indexes


def clear_singleton_instances():
    """Helper function to clear singleton instances for testing."""
    # Access the class-level _instances dict directly using getattr to avoid protected access warnings
    instances_dict = getattr(PersistentStore, "_instances", None)
    if instances_dict is not None:
        instances_dict.clear()

    auth_instances_dict = getattr(PersistentStoreWithAuth, "_instances", None)
    if auth_instances_dict is not None:
        auth_instances_dict.clear()


@pytest.fixture
def store(temp_project_dir: Path) -> TestPersistentStore:
    """Create a fresh PersistentStore for each test with isolated storage."""
    # Clear singleton instances to ensure fresh store
    clear_singleton_instances()

    return TestPersistentStore()


@pytest.fixture
def store_with_auth(temp_project_dir: Path) -> TestPersistentStoreWithAuth:
    """Create a fresh PersistentStore for each test with isolated storage."""
    # Clear singleton instances to ensure fresh store
    clear_singleton_instances()

    return TestPersistentStoreWithAuth()


@pytest.fixture
def mock_auth_user() -> AuthUser:
    """Mock authenticated user for testing."""
    return AuthUser(sub="test@github", login="testuser@github", email="test@example.com")


class TestPersistentStoreBasic:
    """Test basic PersistentStore functionality."""

    def test_file_path_property(self, store: TestPersistentStore):
        """Test that file_path property returns correct path."""
        expected_path = settings.persistent_store_dir / "test_users.json"
        assert store.file_path == expected_path

    def test_key_extraction(self, store: TestPersistentStore):
        """Test key extraction from model."""
        user = TestUser(id="123", name="John Doe", email="john@example.com")
        assert store.row_index_key(user) == "123"

    def test_index_key(self, store: TestPersistentStore):
        """Test index key generation."""
        assert store.index_key("test-key") == "test-key"

    def test_add_user(self, store: TestPersistentStore):
        """Test adding a new user."""
        user = TestUser(id="123", name="John Doe", email="john@example.com")

        result = store.add(user)

        assert result == user
        assert len(store.rows) == 1
        assert store.rows[0] == user
        assert store.has_key_in_index("123")
        assert store.get_indexes_count() == 1

    def test_add_duplicate_user_raises_error(self, store: TestPersistentStore):
        """Test that adding a duplicate user raises ValueError."""
        user1 = TestUser(id="123", name="John Doe", email="john@example.com")
        user2 = TestUser(id="123", name="Jane Doe", email="jane@example.com")

        store.add(user1)

        with pytest.raises(ValueError, match="Row with key 123 already exists"):
            store.add(user2)

    def test_get_existing_user(self, store: TestPersistentStore):
        """Test getting an existing user."""
        user = TestUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        result = store.get("123")

        assert result == user

    def test_get_nonexistent_user(self, store: TestPersistentStore):
        """Test getting a nonexistent user returns None."""
        result = store.get("nonexistent")

        assert result is None

    def test_update_existing_user(self, store: TestPersistentStore):
        """Test updating an existing user."""
        user = TestUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        updated_user = TestUser(id="123", name="John Smith", email="johnsmith@example.com")
        result = store.update(updated_user)

        assert result == updated_user
        assert store.rows[0] == updated_user
        assert store.has_key_in_index("123")

    def test_update_nonexistent_user_raises_error(self, store: TestPersistentStore):
        """Test that updating a nonexistent user raises ValueError."""
        user = TestUser(id="nonexistent", name="John Doe", email="john@example.com")

        with pytest.raises(ValueError, match="Row with key nonexistent not found"):
            store.update(user)

    def test_reset(self, store: TestPersistentStore):
        """Test resetting the store."""
        user = TestUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        store.reset()

        assert len(store.rows) == 0
        assert store.get_indexes_count() == 0

    def test_persistence_across_instances(self, temp_project_dir: Path):
        """Test that data persists across different store instances."""
        # Clear singleton instances
        clear_singleton_instances()

        # Create first store and add user
        store1 = TestPersistentStore()
        user = TestUser(id="123", name="John Doe", email="john@example.com")
        store1.add(user)

        # Clear singleton instances to simulate new instance
        clear_singleton_instances()

        # Create second store and verify user exists
        store2 = TestPersistentStore()
        result = store2.get("123")

        assert result == user

    def test_load_from_empty_file(self, store: TestPersistentStore):
        """Test loading when file doesn't exist."""
        # Should not raise error
        store.load()

        assert len(store.rows) == 0
        assert store.get_indexes_count() == 0

    def test_concurrent_access(self, store: TestPersistentStore):
        """Test concurrent access to store."""
        users = [
            TestUser(id=f"user{i}", name=f"User {i}", email=f"user{i}@example.com")
            for i in range(10)
        ]

        def add_user(user: TestUser):
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


class TestPersistentStoreWithAuthBasic:
    """Test basic PersistentStoreWithAuth functionality."""

    def test_index_key_with_auth(
        self, store_with_auth: TestPersistentStoreWithAuth, mock_auth_user: AuthUser
    ):
        """Test index key generation includes user login."""
        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_auth_user):
            result = store_with_auth.index_key("test-key")

            assert result == ("testuser@github", "test-key")

    def test_key_with_auth(
        self, store_with_auth: TestPersistentStoreWithAuth, mock_auth_user: AuthUser
    ):
        """Test key extraction includes user login."""
        user = TestUserWithAuth(
            id="123", name="John Doe", email="john@example.com", user_login="testuser@github"
        )

        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_auth_user):
            result = store_with_auth.row_index_key(user)

            assert result == ("testuser@github", "123")

    def test_add_user_with_auth(
        self, store_with_auth: TestPersistentStoreWithAuth, mock_auth_user: AuthUser
    ):
        """Test adding a user with authentication."""
        user = TestUserWithAuth(
            id="123", name="John Doe", email="john@example.com", user_login="testuser@github"
        )

        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_auth_user):
            result = store_with_auth.add(user)

            assert result == user
            assert len(store_with_auth.rows) == 1
            assert store_with_auth.rows[0] == user
            assert store_with_auth.has_key_in_index(("testuser@github", "123"))

    def test_get_user_with_auth(
        self, store_with_auth: TestPersistentStoreWithAuth, mock_auth_user: AuthUser
    ):
        """Test getting a user with authentication."""
        user = TestUserWithAuth(
            id="123", name="John Doe", email="john@example.com", user_login="testuser@github"
        )

        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_auth_user):
            store_with_auth.add(user)
            result = store_with_auth.get("123")

            assert result == user

    def test_user_isolation_with_auth(self, store_with_auth: TestPersistentStoreWithAuth):
        """Test that users are isolated by authentication."""
        user1 = TestUserWithAuth(
            id="123", name="John Doe", email="john@example.com", user_login="user1@github"
        )
        user2 = TestUserWithAuth(
            id="123", name="Jane Doe", email="jane@example.com", user_login="user2@github"
        )

        # Add user1 as user1@github
        mock_user1 = AuthUser(sub="user1@github", login="user1@github", email="user1@example.com")
        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_user1):
            store_with_auth.add(user1)

        # Add user2 as user2@github (same ID but different auth user)
        mock_user2 = AuthUser(sub="user2@github", login="user2@github", email="user2@example.com")
        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_user2):
            store_with_auth.add(user2)

        # Both should exist but be isolated
        assert len(store_with_auth.rows) == 2

        # Verify isolation: user1 can only see their own data
        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_user1):
            result = store_with_auth.get("123")
            assert result == user1

        # user2 can only see their own data
        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_user2):
            result = store_with_auth.get("123")
            assert result == user2

    def test_update_user_with_auth(
        self, store_with_auth: TestPersistentStoreWithAuth, mock_auth_user: AuthUser
    ):
        """Test updating a user with authentication."""
        user = TestUserWithAuth(
            id="123", name="John Doe", email="john@example.com", user_login="testuser@github"
        )

        with patch("getgather.mcp.persist.get_auth_user", return_value=mock_auth_user):
            store_with_auth.add(user)

            updated_user = TestUserWithAuth(
                id="123",
                name="John Smith",
                email="johnsmith@example.com",
                user_login="testuser@github",
            )
            result = store_with_auth.update(updated_user)

            assert result == updated_user
            assert store_with_auth.get("123") == updated_user


class TestSingletonBehavior:
    """Test singleton behavior of persistent stores."""

    def test_singleton_behavior(self, temp_project_dir: Path):
        """Test that stores behave as singletons."""
        # Clear singleton instances
        clear_singleton_instances()

        store1 = TestPersistentStore()
        store2 = TestPersistentStore()

        # Should be the same instance
        assert store1 is store2

    def test_singleton_behavior_with_auth(self, temp_project_dir: Path):
        """Test that auth stores behave as singletons."""
        # Clear singleton instances
        clear_singleton_instances()

        store1 = TestPersistentStoreWithAuth()
        store2 = TestPersistentStoreWithAuth()

        # Should be the same instance
        assert store1 is store2

    def test_different_store_types_are_separate_singletons(self, temp_project_dir: Path):
        """Test that different store types maintain separate singleton instances."""
        # Clear singleton instances
        clear_singleton_instances()

        regular_store = TestPersistentStore()
        auth_store = TestPersistentStoreWithAuth()

        # Should be different instances
        assert regular_store is not auth_store
        assert type(regular_store) != type(auth_store)


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_key_field_validation(self):
        """Test validation fails for invalid key field."""

        class InvalidTestStore(PersistentStore[TestUser]):
            _row_model = TestUser
            _file_name = "test.json"
            _key_field = "nonexistent_field"  # Invalid field

        with pytest.raises(ValidationError):
            InvalidTestStore()

    def test_auth_store_requires_user_login_field(self):
        """Test that auth store validation fails without user_login field."""

        class InvalidAuthStore(
            PersistentStoreWithAuth[TestUser]  # type: ignore
        ):  # TestUser doesn't have user_login
            _row_model = TestUser
            _file_name = "test.json"
            _key_field = "id"

        with pytest.raises(ValidationError):
            InvalidAuthStore()

    def test_file_path_creation(self, store: TestPersistentStore):
        """Test that directory is created if it doesn't exist."""
        # Ensure directory doesn't exist initially
        if store.file_path.parent.exists():
            shutil.rmtree(store.file_path.parent)

        user = TestUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        # Directory should be created
        assert store.file_path.parent.exists()
        assert store.file_path.exists()


class TestThreadSafety:
    """Test thread safety of persistent stores."""

    def test_concurrent_adds_different_keys(self, store: TestPersistentStore):
        """Test concurrent adds with different keys."""

        def add_users(start_idx: int, count: int):
            for i in range(start_idx, start_idx + count):
                user = TestUser(id=f"user{i}", name=f"User {i}", email=f"user{i}@example.com")
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

    def test_concurrent_updates(self, store: TestPersistentStore):
        """Test concurrent updates to the same user."""
        # First add a user
        user = TestUser(id="123", name="John Doe", email="john@example.com")
        store.add(user)

        def update_user(name_suffix: str):
            updated_user = TestUser(
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
