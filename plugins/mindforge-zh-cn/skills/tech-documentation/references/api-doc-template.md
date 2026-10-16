### API文档模板

````markdown
# API文档

## 概述
简要描述API的用途和功能

## 基础信息
- **Base URL**: `https://api.example.com/v1`
- **认证方式**: Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### 获取Token
```http
POST /auth/token
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## 接口列表

### 用户管理

#### 创建用户

**请求**:
```http
POST /users
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user"
}
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 用户邮箱，需唯一 |
| name | string | 是 | 用户姓名 |
| role | string | 否 | 用户角色，默认user |

**响应**: `201 Created`
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2024-12-16T10:00:00Z"
}
```

**错误响应**:
- `400 Bad Request` - 参数错误
- `401 Unauthorized` - 未认证
- `409 Conflict` - 邮箱已存在

```json
{
  "error": {
    "code": "EMAIL_EXISTS",
    "message": "Email already registered",
    "field": "email"
  }
}
```

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| EMAIL_EXISTS | 409 | 邮箱已注册 |
| INVALID_TOKEN | 401 | Token无效 |
| RATE_LIMIT_EXCEEDED | 429 | 请求过于频繁 |

## 限流规则
- 每用户 100 请求/分钟
- 超限返回 429 状态码

## 变更日志

### v1.1.0 (2024-12-16)
- 新增用户角色管理接口
- 优化Token过期机制

### v1.0.0 (2024-12-01)
- 初始版本发布
````
