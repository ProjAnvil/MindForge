# Python Test Engineer Agent - Detailed Guide

This document contains comprehensive examples, templates, and best practices for Python testing.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Pytest Configuration](#pytest-configuration)
3. [Test Templates](#test-templates)
4. [Advanced Patterns](#advanced-patterns)
5. [Best Practices](#best-practices)
6. [Testing Strategies](#testing-strategies)

## Project Structure

```
project/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── main.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── user_service.py
│       └── models/
│           ├── __init__.py
│           └── user.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_services.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_api.py
│   └── e2e/
│       ├── __init__.py
│       └── test_workflows.py
├── pytest.ini                   # Pytest configuration
├── pyproject.toml              # Project dependencies
└── .coveragerc                 # Coverage configuration
```

## Pytest Configuration

### pytest.ini

```ini
[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow-running tests
    asyncio: Async tests
asyncio_mode = auto
```

### pyproject.toml

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow-running tests",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
```

## Test Templates

### Standard Test File Structure

```python
"""
Tests for UserService.

Coverage includes:
- User creation and retrieval
- Validation logic
- Error handling
- Edge cases
"""

import pytest
from unittest.mock import Mock, patch
from myapp.services.user_service import UserService
from myapp.models.user import User
from myapp.exceptions import NotFoundError, ValidationError


class TestUserService:
    """Test suite for UserService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock user repository."""
        return Mock()

    @pytest.fixture
    def user_service(self, mock_repository):
        """Create UserService with mocked dependencies."""
        return UserService(repository=mock_repository)

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True
        )

    # ========== Happy Path Tests ==========

    def test_create_user_with_valid_data_returns_user(
        self,
        user_service,
        mock_repository,
        sample_user
    ):
        """Test creating a user with valid data."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
        mock_repository.create.return_value = sample_user

        # Act
        result = user_service.create_user(**user_data)

        # Assert
        assert result is not None
        assert result.email == user_data["email"]
        assert result.username == user_data["username"]
        mock_repository.create.assert_called_once()

    def test_get_user_by_id_when_user_exists_returns_user(
        self,
        user_service,
        mock_repository,
        sample_user
    ):
        """Test retrieving an existing user by ID."""
        # Arrange
        user_id = 1
        mock_repository.get_by_id.return_value = sample_user

        # Act
        result = user_service.get_user_by_id(user_id)

        # Assert
        assert result is not None
        assert result.id == user_id
        mock_repository.get_by_id.assert_called_once_with(user_id)

    # ========== Edge Case Tests ==========

    def test_list_users_with_empty_database_returns_empty_list(
        self,
        user_service,
        mock_repository
    ):
        """Test listing users when database is empty."""
        # Arrange
        mock_repository.list_all.return_value = []

        # Act
        result = user_service.list_users()

        # Assert
        assert result == []
        mock_repository.list_all.assert_called_once()

    def test_create_user_with_duplicate_email_raises_validation_error(
        self,
        user_service,
        mock_repository
    ):
        """Test creating a user with duplicate email fails."""
        # Arrange
        user_data = {
            "email": "existing@example.com",
            "username": "newuser",
            "password": "SecurePass123!"
        }
        mock_repository.create.side_effect = ValidationError(
            "Email already exists"
        )

        # Act & Assert
        with pytest.raises(ValidationError, match="Email already exists"):
            user_service.create_user(**user_data)

    # ========== Exception Tests ==========

    def test_get_user_by_id_when_not_found_raises_not_found_error(
        self,
        user_service,
        mock_repository
    ):
        """Test retrieving non-existent user raises NotFoundError."""
        # Arrange
        user_id = 999
        mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError, match="User not found"):
            user_service.get_user_by_id(user_id)

    def test_create_user_with_invalid_email_raises_validation_error(
        self,
        user_service
    ):
        """Test creating user with invalid email raises ValidationError."""
        # Arrange
        user_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "SecurePass123!"
        }

        # Act & Assert
        with pytest.raises(ValidationError):
            user_service.create_user(**user_data)
```

## Advanced Patterns

### Parametrized Tests

```python
import pytest

class TestUserValidation:
    """Test user input validation."""

    @pytest.mark.parametrize("email,expected_valid", [
        ("user@example.com", True),
        ("user.name@example.com", True),
        ("user+tag@example.co.uk", True),
        ("invalid-email", False),
        ("@example.com", False),
        ("user@", False),
        ("", False),
        (None, False),
    ])
    def test_validate_email_with_various_inputs(
        self,
        email,
        expected_valid
    ):
        """Test email validation with various inputs."""
        result = validate_email(email)
        assert result.is_valid == expected_valid

    @pytest.mark.parametrize("password,is_strong", [
        ("SecurePass123!", True),
        ("MyP@ssw0rd", True),
        ("weak", False),
        ("onlylowercase", False),
        ("ONLYUPPERCASE", False),
        ("NoDigits!", False),
        ("NoSpecial123", False),
        ("", False),
    ])
    def test_password_strength_validation(self, password, is_strong):
        """Test password strength validation."""
        result = validate_password_strength(password)
        assert result.is_strong == is_strong


@pytest.mark.parametrize("limit,offset,expected_count", [
    (10, 0, 10),
    (20, 0, 20),
    (10, 10, 10),
    (100, 0, 50),  # Only 50 users exist
])
def test_list_users_with_pagination(limit, offset, expected_count):
    """Test user listing with various pagination parameters."""
    users = user_service.list_users(limit=limit, offset=offset)
    assert len(users) == expected_count
```

### Fixture Scopes

```python
# conftest.py

import pytest
import asyncio
from httpx import AsyncClient
from myapp.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database():
    """Create test database session."""
    db = create_test_database()
    yield db
    db.cleanup()


@pytest.fixture(scope="function")
def clean_database(test_database):
    """Clean database before each test."""
    test_database.truncate_all()
    yield test_database


@pytest.fixture(scope="module")
def async_client():
    """Create async HTTP client for API testing."""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture(scope="function")
def authenticated_user(async_client):
    """Create and authenticate a test user."""
    user_data = {"email": "test@example.com", "password": "testpass"}
    response = async_client.post("/auth/register", json=user_data)
    token = response.json()["access_token"]
    return {"user": user_data, "token": token}
```

### Async Testing

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAsyncUserAPI:
    """Test async user API endpoints."""

    async def test_create_user_returns_201(
        self,
        async_client: AsyncClient
    ):
        """Test creating a user via API."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }

        # Act
        response = await async_client.post("/api/users", json=user_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "password" not in data

    async def test_get_user_returns_200(
        self,
        async_client: AsyncClient,
        authenticated_user
    ):
        """Test getting current authenticated user."""
        # Arrange
        headers = {
            "Authorization": f"Bearer {authenticated_user['token']}"
        }

        # Act
        response = await async_client.get(
            "/api/users/me",
            headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == authenticated_user["user"]["email"]

    @pytest.mark.asyncio
    async def test_concurrent_requests_handle_correctly(
        self,
        async_client: AsyncClient
    ):
        """Test handling multiple concurrent requests."""
        # Arrange
        tasks = [
            async_client.get("/api/users/1")
            for _ in range(10)
        ]

        # Act
        responses = await asyncio.gather(*tasks)

        # Assert
        assert all(r.status_code == 200 for r in responses)
```

### Mocking External Dependencies

```python
from unittest.mock import patch, Mock
import pytest


class TestExternalAPI:
    """Test integration with external APIs."""

    @patch("myapp.services.user_service.requests.get")
    def test_fetch_user_from_external_api_success(
        self,
        mock_get,
        user_service
    ):
        """Test fetching user from external API."""
        # Arrange
        user_id = 123
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": user_id,
            "name": "External User",
            "email": "external@example.com"
        }
        mock_get.return_value = mock_response

        # Act
        result = user_service.fetch_from_external_api(user_id)

        # Assert
        assert result["id"] == user_id
        assert result["email"] == "external@example.com"
        mock_get.assert_called_once_with(
            f"https://api.example.com/users/{user_id}"
        )

    @patch("myapp.services.user_service.requests.get")
    def test_fetch_user_from_external_api_handles_404(
        self,
        mock_get,
        user_service
    ):
        """Test handling 404 from external API."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(NotFoundError):
            user_service.fetch_from_external_api(999)

    @patch.object(UserService, "send_email")
    def test_create_user_sends_welcome_email(
        self,
        mock_send_email,
        user_service
    ):
        """Test that creating a user sends welcome email."""
        # Arrange
        user_data = {"email": "new@example.com", "username": "newuser"}
        mock_send_email.return_value = True

        # Act
        user = user_service.create_user(**user_data)

        # Assert
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert call_args[1]["to_email"] == user_data["email"]
        assert "welcome" in call_args[1]["subject"].lower()
```

### Property-Based Testing with Hypothesis

```python
from hypothesis import given, strategies as st
import pytest


class TestUserProperties:
    """Property-based tests for User model."""

    @given(st.emails(), st.text(min_size=3, max_size=50))
    def test_user_creation_preserves_email_and_username(
        self,
        email,
        username
    ):
        """Test that user creation preserves input values."""
        user = User(email=email, username=username)
        assert user.email == email
        assert user.username == username

    @given(st.lists(st.integers(min_value=1, max_value=100), min_size=0))
    def test_user_ids_are_always_positive(self, user_ids):
        """Test that all user IDs are positive."""
        users = [User(id=id, email=f"user{id}@test.com") for id in user_ids]
        assert all(user.id > 0 for user in users)

    @given(st.emails())
    def test_email_normalization(self, email):
        """Test that email normalization is consistent."""
        user = User(email=email)
        normalized = user.normalize_email()
        assert normalized == normalized.lower()
        assert normalized.strip() == normalized


# Strategy for generating valid user data
user_strategy = st.builds(
    User,
    id=st.integers(min_value=1, max_value=10000),
    email=st.emails(),
    username=st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_characters='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
    )),
    is_active=st.booleans()
)

@given(user_strategy)
def test_user_serialization_roundtrip(user):
    """Test that user serialization and deserialization are consistent."""
    serialized = user.to_dict()
    deserialized = User.from_dict(serialized)
    assert deserialized == user
```

### Testing with Test Containers

```python
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def postgres_container():
    """Create a PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="function")
def db_session(postgres_container):
    """Create a database session for testing."""
    engine = create_engine(postgres_container)
    TestingSessionLocal = sessionmaker(bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


class TestDatabaseIntegration:
    """Integration tests with real database."""

    def test_create_user_persists_to_database(self, db_session):
        """Test that user creation persists to database."""
        # Arrange
        user = User(email="test@example.com", username="testuser")

        # Act
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Assert
        assert user.id is not None
        retrieved = db_session.query(User).filter_by(id=user.id).first()
        assert retrieved is not None
        assert retrieved.email == "test@example.com"

    def test_user_query_returns_correct_results(self, db_session):
        """Test querying users returns correct results."""
        # Arrange
        users = [
            User(email=f"user{i}@example.com", username=f"user{i}")
            for i in range(5)
        ]
        db_session.add_all(users)
        db_session.commit()

        # Act
        result = db_session.query(User).all()

        # Assert
        assert len(result) == 5
```

## Best Practices

### Test Organization

✅ **DO:**
- Organize tests by type (unit, integration, e2e)
- Use descriptive test names following `test_<what>_<condition>_<expected>`
- Keep tests independent and isolated
- Use fixtures for common setup
- Group related tests in classes
- Use markers to categorize tests

❌ **DON'T:**
- Create interdependent tests
- Use vague test names
- Put all tests in one file
- Duplicate setup code
- Test implementation details

### Test Coverage

✅ **DO:**
- Aim for 80%+ code coverage
- Test critical paths thoroughly
- Test error conditions
- Use coverage reports to identify gaps
- Test edge cases and boundary conditions

❌ **DON'T:**
- Chase 100% coverage at the cost of quality
- Test trivial code (getters, setters)
- Write meaningless tests
- Skip error handling tests

### Mocking Guidelines

✅ **Mock:**
- External APIs
- Database operations (for unit tests)
- File system operations
- Time-dependent code
- Expensive operations

❌ **Don't Mock:**
- Value objects/dataclasses
- Simple functions
- The class under test
- Python standard library (unless external interaction)

### Async Testing Best Practices

```python
# Always use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# Use pytest.mark.asyncio for entire classes
@pytest.mark.asyncio
class TestAsyncClass:
    async def test_method_one(self):
        pass

    async def test_method_two(self):
        pass

# Configure asyncio_mode in pytest.ini
# [pytest]
# asyncio_mode = auto
```

### Performance Testing

```python
import pytest
import time


@pytest.mark.slow
@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks."""

    def test_user_creation_performance(self, benchmark):
        """Benchmark user creation performance."""
        def create_users():
            return [User(email=f"user{i}@test.com") for i in range(1000)]

        result = benchmark(create_users)
        assert len(result) == 1000

    @pytest.mark.parametrize("count", [10, 100, 1000])
    def test_query_scalability(self, db_session, count, benchmark):
        """Test query performance with different dataset sizes."""
        # Setup
        users = [User(email=f"user{i}@test.com") for i in range(count)]
        db_session.add_all(users)
        db_session.commit()

        # Benchmark
        result = benchmark(db_session.query(User).all)
        assert len(result) == count
```

## Testing Strategies

### Test Pyramid

```
        /\
       /E2E\      - Few (10%)
      /------\
     /  Integration  \  - Some (30%)
    /--------------\
   /     Unit Tests  \ - Many (60%)
  /------------------\
```

### When to Use Each Test Type

**Unit Tests:**
- Business logic
- Validation functions
- Utility functions
- Independent components

**Integration Tests:**
- API endpoints
- Database interactions
- External service integrations
- Component interactions

**E2E Tests:**
- Critical user workflows
- Authentication flows
- Payment processes
- Multi-step operations

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_user_service.py

# Run specific test class
pytest tests/unit/test_user_service.py::TestUserService

# Run specific test method
pytest tests/unit/test_user_service.py::TestUserService::test_create_user

# Run only marked tests
pytest -m unit
pytest -m "not slow"

# Run with coverage
pytest --cov=src --cov-report=html

# Run parallel tests (requires pytest-xdist)
pytest -n auto

# Run failed tests only
pytest --lf

# Stop on first failure
pytest -x

# Verbose output
pytest -vv

# Show print statements
pytest -s
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[test]"

      - name: Run unit tests
        run: pytest -m unit --cov=src

      - name: Run integration tests
        run: pytest -m integration
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

Remember: **Good tests are maintainable, readable, and provide confidence in your code.**
