### FastAPI 应用

#### Pydantic Schemas

```python
# app/schemas/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """用户基础 schema，包含公共字段。"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True


class UserCreate(UserBase):
    """创建用户的 schema。"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """更新用户的 schema。"""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """数据库中用户的 schema。"""
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """用户响应的 schema。"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

#### SQLAlchemy 模型

```python
# app/models/user.py
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """用户数据库模型。"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
```

#### Repository 模式

```python
# app/repositories/user.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """用户数据访问的 repository。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
        """创建新用户。"""
        user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password,
            is_active=user_data.is_active,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """通过 ID 获取用户。"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户。"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User, user_data: UserUpdate) -> User:
        """更新用户。"""
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """删除用户。"""
        await self.session.delete(user)
        await self.session.commit()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """分页列出用户。"""
        query = select(User)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否存在。"""
        result = await self.session.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None
```

#### Service 层

```python
# app/services/user.py
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash
import logging


logger = logging.getLogger(__name__)


class UserService:
    """用户业务逻辑的 service。"""

    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建新用户。"""
        # 检查邮箱是否已存在
        if await self.repository.exists_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # 哈希密码
        hashed_password = get_password_hash(user_data.password)

        # 创建用户
        user = await self.repository.create(user_data, hashed_password)

        logger.info(f"User created: {user.id}")

        return UserResponse.model_validate(user)

    async def get_user(self, user_id: int) -> UserResponse:
        """通过 ID 获取用户。"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """更新用户。"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # 如果正在更新邮箱，检查邮箱唯一性
        if user_data.email and user_data.email != user.email:
            if await self.repository.exists_by_email(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )

        updated_user = await self.repository.update(user, user_data)

        logger.info(f"User updated: {user_id}")

        return UserResponse.model_validate(updated_user)

    async def delete_user(self, user_id: int) -> None:
        """删除用户。"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await self.repository.delete(user)

        logger.info(f"User deleted: {user_id}")

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None
    ) -> List[UserResponse]:
        """分页列出用户。"""
        users = await self.repository.list(skip, limit, is_active)
        return [UserResponse.model_validate(user) for user in users]
```

#### FastAPI Router

```python
# app/api/v1/endpoints/users.py
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.services.user import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse


router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新用户",
    description="使用邮箱、姓名和密码创建新用户。"
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    创建新用户。

    - **email**: 有效的邮箱地址
    - **name**: 用户全名（2-100 个字符）
    - **password**: 密码（至少 8 个字符）
    """
    service = UserService(db)
    return await service.create_user(user_data)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="通过 ID 获取用户"
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """通过 ID 获取用户。"""
    service = UserService(db)
    return await service.get_user(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="更新用户"
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """更新用户。"""
    service = UserService(db)
    return await service.update_user(user_id, user_data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除用户"
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
) -> None:
    """删除用户。"""
    service = UserService(db)
    await service.delete_user(user_id)


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="列出用户"
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
) -> List[UserResponse]:
    """分页列出用户。"""
    service = UserService(db)
    return await service.list_users(skip, limit, is_active)
```

#### 主应用程序

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, Base
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期事件。"""
    # 启动
    logger.info("Starting up application...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    yield

    # 关闭
    logger.info("Shutting down application...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 包含路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```
