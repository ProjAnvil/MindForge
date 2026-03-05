### Django 应用

#### Django 模型

```python
# apps/users/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    """自定义用户管理器。"""

    def create_user(self, email: str, name: str, password: str = None, **extra_fields):
        """创建并保存普通用户。"""
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, name: str, password: str = None, **extra_fields):
        """创建并保存超级用户。"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """自定义用户模型。"""

    email = models.EmailField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        return self.name

    def get_short_name(self) -> str:
        return self.name.split()[0] if self.name else self.email
```

#### Django REST Framework Serializers

```python
# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """用户模型的 serializer。"""

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """创建用户的 serializer。"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'password_confirm']

    def validate(self, attrs):
        """验证密码确认。"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def create(self, validated_data):
        """创建带哈希密码的用户。"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """更新用户的 serializer。"""

    class Meta:
        model = User
        fields = ['name', 'email', 'is_active']
```

#### Django 视图

```python
# apps/users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from apps.users.models import User
from apps.users.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer
)
import logging


logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """用户操作的 ViewSet。"""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """根据操作获取权限。"""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """根据操作获取 serializer 类。"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """创建新用户。"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        logger.info(f"User created: {user.id}")

        headers = self.get_success_headers(serializer.data)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        """更新用户。"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        logger.info(f"User updated: {user.id}")

        return Response(UserSerializer(user).data)

    def destroy(self, request, *args, **kwargs):
        """删除用户。"""
        instance = self.get_object()
        user_id = instance.id
        instance.delete()

        logger.info(f"User deleted: {user_id}")

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活用户。"""
        user = self.get_object()
        user.is_active = True
        user.save()

        logger.info(f"User activated: {user.id}")

        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """停用用户。"""
        user = self.get_object()
        user.is_active = False
        user.save()

        logger.info(f"User deactivated: {user.id}")

        return Response(UserSerializer(user).data)
```
