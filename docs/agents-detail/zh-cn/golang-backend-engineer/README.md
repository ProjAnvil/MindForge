# Golang 后端工程师 Agent - 详细指南

本文档包含 Go 后端开发的综合示例、模板和最佳实践。

## 整洁架构模板

```
project/
├── cmd/
│   └── api/
│       └── main.go           # 应用入口点
├── internal/
│   ├── domain/               # 业务逻辑和实体
│   │   ├── entity.go
│   │   └── repository.go     # Repository 接口
│   ├── usecase/              # 业务规则/应用逻辑
│   │   └── user_usecase.go
│   ├── repository/           # 数据访问实现
│   │   └── user_repository.go
│   ├── delivery/             # 交付机制（HTTP、gRPC 等）
│   │   └── http/
│   │       ├── handler.go
│   │       └── middleware.go
│   └── infrastructure/       # 外部关注点
│       ├── database/
│       └── config/
├── pkg/                      # 公共库
├── api/                      # API 定义（OpenAPI、protobuf）
├── configs/                  # 配置文件
├── migrations/               # 数据库迁移
├── scripts/                  # 构建和部署脚本
└── go.mod
```

## Fiber Handler 示例

```go
package delivery

import (
    "github.com/gofiber/fiber/v2"
)

type UserHandler struct {
    userUseCase usecase.UserUseCase
}

func NewUserHandler(userUseCase usecase.UserUseCase) *UserHandler {
    return &UserHandler{userUseCase: userUseCase}
}

func (h *UserHandler) Register(c *fiber.Ctx) error {
    var req dto.RegisterRequest
    if err := c.BodyParser(&req); err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
            "error": "Invalid request body",
        })
    }

    user, err := h.userUseCase.Register(c.Context(), &req)
    if err != nil {
        return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
            "error": err.Error(),
        })
    }

    return c.Status(fiber.StatusCreated).JSON(user)
}
```

## GORM Repository 示例

```go
package repository

import (
    "context"
    "gorm.io/gorm"
)

type userRepository struct {
    db *gorm.DB
}

func NewUserRepository(db *gorm.DB) repository.UserRepository {
    return &userRepository{db: db}
}

func (r *userRepository) Create(ctx context.Context, user *entity.User) error {
    return r.db.WithContext(ctx).Create(user).Error
}

func (r *userRepository) GetByID(ctx context.Context, id int) (*entity.User, error) {
    var user entity.User
    err := r.db.WithContext(ctx).First(&user, id).Error
    if err != nil {
        return nil, err
    }
    return &user, nil
}
```

## Cobra CLI 示例

```go
package cmd

import (
    "fmt"
    "github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
    Use:   "myapp",
    Short: "My application does amazing things",
    Long:  `A longer description of what my application does.`,
}

var serveCmd = &cobra.Command{
    Use:   "serve",
    Short: "Start the HTTP server",
    Run: func(cmd *cobra.Command, args []string) {
        port, _ := cmd.Flags().GetInt("port")
        fmt.Printf("Starting server on port %d\n", port)
    },
}

func init() {
    serveCmd.Flags().Int("port", 8080, "Port to run the server on")
    rootCmd.AddCommand(serveCmd)
}
```

## Wire 依赖注入示例

```go
//+build wireinject

package main

import (
    "github.com/google/wire"
    "myapp/internal/delivery"
    "myapp/internal/repository"
    "myapp/internal/usecase"
)

func InitializeApp(db *gorm.DB) (*fiber.App, error) {
    wire.Build(
        repository.NewUserRepository,
        usecase.NewUserUseCase,
        delivery.NewUserHandler,
        NewApp,
    )
    return &fiber.App{}, nil
}
```

## 测试示例

```go
package usecase_test

import (
    "context"
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

type MockUserRepository struct {
    mock.Mock
}

func TestUserUseCase_Register(t *testing.T) {
    // Arrange
    mockRepo := new(MockUserRepository)
    useCase := usecase.NewUserUseCase(mockRepo)

    // Act
    user, err := useCase.Register(context.Background(), req)

    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, user)
}
```

## 最佳实践

### 错误处理
- 始终使用上下文包装错误：`fmt.Errorf("failed to create user: %w", err)`
- 对特定于领域的错误使用自定义错误类型
- 永远不要忽略错误

### 并发
- 对并发操作使用 goroutines
- 始终使用 channels 或 sync.WaitGroup 管理 goroutines
- 使用 context 进行取消和超时
- 避免共享可变状态

### 数据库操作
- 始终使用带超时的 context 进行数据库操作
- 对多步骤操作使用事务
- 实现适当的索引以提高性能
- 使用准备好的语句防止 SQL 注入

### API 设计
- 使用正确的 HTTP 方法（GET、POST、PUT、DELETE）
- 实现正确的状态码
- 验证输入数据
- 使用中间件处理横切关注点（日志、身份验证）
- 实现速率限制

## 性能优化

- 对数据库使用连接池
- 在适当的地方实现缓存（Redis）
- 对列表端点使用分页
- 优化数据库查询（避免 N+1 查询）
- 使用 pprof 进行性能分析
- 实现适当的日志记录（使用 Zap 进行结构化日志记录）
