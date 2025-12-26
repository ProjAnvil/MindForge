# Python 测试工程师 Agent - 详细指南

本文档包含 Python 测试的综合示例、模板和最佳实践。

## 目录

1. [项目结构](#项目结构)
2. [Pytest 配置](#pytest-配置)
3. [测试模板](#测试模板)
4. [高级模式](#高级模式)
5. [最佳实践](#最佳实践)
6. [测试策略](#测试策略)

## 项目结构

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
│   ├── conftest.py              # 共享 fixtures
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
├── pytest.ini                   # Pytest 配置
├── pyproject.toml              # 项目依赖
└── .coveragerc                 # 覆盖率配置
```

## Pytest 配置

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
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    slow: 慢速测试
    asyncio: 异步测试
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
    "unit: 单元测试",
    "integration: 集成测试",
    "slow: 慢速测试",
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

## 测试模板

### 标准测试文件结构

```python
"""
UserService 的测试。

覆盖范围包括:
- 用户创建和检索
- 验证逻辑
- 错误处理
- 边界情况
"""

import pytest
from unittest.mock import Mock, patch
from myapp.services.user_service import UserService
from myapp.models.user import User
from myapp.exceptions import NotFoundError, ValidationError


class TestUserService:
    """UserService 的测试套件。"""

    @pytest.fixture
    def mock_repository(self):
        """创建 mock 用户仓库。"""
        return Mock()

    @pytest.fixture
    def user_service(self, mock_repository):
        """创建带有 mock 依赖的 UserService。"""
        return UserService(repository=mock_repository)

    @pytest.fixture
    def sample_user(self):
        """创建用于测试的示例用户。"""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True
        )

    # ========== 正常路径测试 ==========

    def test_create_user_with_valid_data_returns_user(
        self,
        user_service,
        mock_repository,
        sample_user
    ):
        """测试使用有效数据创建用户。"""
        # Arrange（准备）
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
        mock_repository.create.return_value = sample_user

        # Act（执行）
        result = user_service.create_user(**user_data)

        # Assert（断言）
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
        """测试通过 ID 检索现有用户。"""
        # Arrange
        user_id = 1
        mock_repository.get_by_id.return_value = sample_user

        # Act
        result = user_service.get_user_by_id(user_id)

        # Assert
        assert result is not None
        assert result.id == user_id
        mock_repository.get_by_id.assert_called_once_with(user_id)

    # ========== 边界情况测试 ==========

    def test_list_users_with_empty_database_returns_empty_list(
        self,
        user_service,
        mock_repository
    ):
        """测试数据库为空时列出用户。"""
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
        """测试使用重复邮箱创建用户失败。"""
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

    # ========== 异常测试 ==========

    def test_get_user_by_id_when_not_found_raises_not_found_error(
        self,
        user_service,
        mock_repository
    ):
        """测试检索不存在的用户抛出 NotFoundError。"""
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
        """测试使用无效邮箱创建用户抛出 ValidationError。"""
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

## 高级模式

### 参数化测试

```python
import pytest

class TestUserValidation:
    """测试用户输入验证。"""

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
        """测试使用各种输入验证邮箱。"""
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
        """测试密码强度验证。"""
        result = validate_password_strength(password)
        assert result.is_strong == is_strong


@pytest.mark.parametrize("limit,offset,expected_count", [
    (10, 0, 10),
    (20, 0, 20),
    (10, 10, 10),
    (100, 0, 50),  # 只存在 50 个用户
])
def test_list_users_with_pagination(limit, offset, expected_count):
    """测试使用各种分页参数列出用户。"""
    users = user_service.list_users(limit=limit, offset=offset)
    assert len(users) == expected_count
```

### Fixture 作用域

```python
# conftest.py

import pytest
import asyncio
from httpx import AsyncClient
from myapp.main import app


@pytest.fixture(scope="session")
def event_loop():
    """为异步测试创建事件循环。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database():
    """创建测试数据库会话。"""
    db = create_test_database()
    yield db
    db.cleanup()


@pytest.fixture(scope="function")
def clean_database(test_database):
    """每次测试前清理数据库。"""
    test_database.truncate_all()
    yield test_database


@pytest.fixture(scope="module")
def async_client():
    """创建用于 API 测试的异步 HTTP 客户端。"""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture(scope="function")
def authenticated_user(async_client):
    """创建并认证测试用户。"""
    user_data = {"email": "test@example.com", "password": "testpass"}
    response = async_client.post("/auth/register", json=user_data)
    token = response.json()["access_token"]
    return {"user": user_data, "token": token}
```

### 异步测试

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAsyncUserAPI:
    """测试异步用户 API 端点。"""

    async def test_create_user_returns_201(
        self,
        async_client: AsyncClient
    ):
        """测试通过 API 创建用户。"""
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
        """测试获取当前认证用户。"""
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
        """测试处理多个并发请求。"""
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

### Mock 外部依赖

```python
from unittest.mock import patch, Mock
import pytest


class TestExternalAPI:
    """测试与外部 API 的集成。"""

    @patch("myapp.services.user_service.requests.get")
    def test_fetch_user_from_external_api_success(
        self,
        mock_get,
        user_service
    ):
        """测试从外部 API 获取用户。"""
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
        """测试处理外部 API 的 404 响应。"""
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
        """测试创建用户发送欢迎邮件。"""
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

### 使用 Hypothesis 进行基于属性的测试

```python
from hypothesis import given, strategies as st
import pytest


class TestUserProperties:
    """User 模型的基于属性的测试。"""

    @given(st.emails(), st.text(min_size=3, max_size=50))
    def test_user_creation_preserves_email_and_username(
        self,
        email,
        username
    ):
        """测试用户创建保留输入值。"""
        user = User(email=email, username=username)
        assert user.email == email
        assert user.username == username

    @given(st.lists(st.integers(min_value=1, max_value=100), min_size=0))
    def test_user_ids_are_always_positive(self, user_ids):
        """测试所有用户 ID 都是正数。"""
        users = [User(id=id, email=f"user{id}@test.com") for id in user_ids]
        assert all(user.id > 0 for user in users)

    @given(st.emails())
    def test_email_normalization(self, email):
        """测试邮箱规范化是一致的。"""
        user = User(email=email)
        normalized = user.normalize_email()
        assert normalized == normalized.lower()
        assert normalized.strip() == normalized


# 生成有效用户数据的策略
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
    """测试用户序列化和反序列化是一致的。"""
    serialized = user.to_dict()
    deserialized = User.from_dict(serialized)
    assert deserialized == user
```

### 使用 Test Containers 测试

```python
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def postgres_container():
    """为集成测试创建 PostgreSQL 容器。"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="function")
def db_session(postgres_container):
    """创建用于测试的数据库会话。"""
    engine = create_engine(postgres_container)
    TestingSessionLocal = sessionmaker(bind=engine)

    # 创建表
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


class TestDatabaseIntegration:
    """与真实数据库的集成测试。"""

    def test_create_user_persists_to_database(self, db_session):
        """测试用户创建持久化到数据库。"""
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
        """测试查询用户返回正确结果。"""
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

## 最佳实践

### 测试组织

✅ **应该做:**
- 按类型组织测试（单元、集成、e2e）
- 使用描述性测试名称，遵循 `test_<what>_<condition>_<expected>`
- 保持测试独立和隔离
- 使用 fixtures 进行通用设置
- 在类中组织相关测试
- 使用标记来分类测试

❌ **不应该做:**
- 创建相互依赖的测试
- 使用模糊的测试名称
- 将所有测试放在一个文件中
- 重复设置代码
- 测试实现细节

### 测试覆盖率

✅ **应该做:**
- 以 80%+ 的代码覆盖率为目标
- 彻底测试关键路径
- 测试错误条件
- 使用覆盖率报告识别差距
- 测试边界情况和边界条件

❌ **不应该做:**
- 以牺牲质量为代价追求 100% 覆盖率
- 测试琐碎代码（getters、setters）
- 编写无意义的测试
- 跳过错误处理测试

### Mock 指南

✅ **应该 Mock:**
- 外部 API
- 数据库操作（用于单元测试）
- 文件系统操作
- 时间相关代码
- 昂贵操作

❌ **不应该 Mock:**
- 值对象/dataclasses
- 简单函数
- 被测试的类本身
- Python 标准库（除非有外部交互）

### 异步测试最佳实践

```python
# 始终使用 pytest-asyncio 进行异步测试
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# 对整个类使用 pytest.mark.asyncio
@pytest.mark.asyncio
class TestAsyncClass:
    async def test_method_one(self):
        pass

    async def test_method_two(self):
        pass

# 在 pytest.ini 中配置 asyncio_mode
# [pytest]
# asyncio_mode = auto
```

### 性能测试

```python
import pytest
import time


@pytest.mark.slow
@pytest.mark.benchmark
class TestPerformance:
    """性能基准测试。"""

    def test_user_creation_performance(self, benchmark):
        """基准测试用户创建性能。"""
        def create_users():
            return [User(email=f"user{i}@test.com") for i in range(1000)]

        result = benchmark(create_users)
        assert len(result) == 1000

    @pytest.mark.parametrize("count", [10, 100, 1000])
    def test_query_scalability(self, db_session, count, benchmark):
        """测试不同数据集大小的查询性能。"""
        # 设置
        users = [User(email=f"user{i}@test.com") for i in range(count)]
        db_session.add_all(users)
        db_session.commit()

        # 基准测试
        result = benchmark(db_session.query(User).all)
        assert len(result) == count
```

## 测试策略

### 测试金字塔

```
        /\
       /E2E\      - 少量 (10%)
      /------\
     /  集成测试  \  - 适量 (30%)
    /--------------\
   /     单元测试  \ - 大量 (60%)
  /------------------\
```

### 何时使用每种测试类型

**单元测试:**
- 业务逻辑
- 验证函数
- 工具函数
- 独立组件

**集成测试:**
- API 端点
- 数据库交互
- 外部服务集成
- 组件交互

**E2E 测试:**
- 关键用户工作流
- 认证流程
- 支付流程
- 多步骤操作

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_user_service.py

# 运行特定测试类
pytest tests/unit/test_user_service.py::TestUserService

# 运行特定测试方法
pytest tests/unit/test_user_service.py::TestUserService::test_create_user

# 仅运行带标记的测试
pytest -m unit
pytest -m "not slow"

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html

# 并行运行测试（需要 pytest-xdist）
pytest -n auto

# 仅运行失败的测试
pytest --lf

# 首次失败时停止
pytest -x

# 详细输出
pytest -vv

# 显示 print 语句
pytest -s
```

### 持续集成

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

      - name: 设置 Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: 安装依赖
        run: |
          pip install -e ".[test]"

      - name: 运行单元测试
        run: pytest -m unit --cov=src

      - name: 运行集成测试
        run: pytest -m integration
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

      - name: 上传覆盖率
        uses: codecov/codecov-action@v3
```

记住：**好的测试应该是可维护的、可读的，并为您的代码提供信心。**
