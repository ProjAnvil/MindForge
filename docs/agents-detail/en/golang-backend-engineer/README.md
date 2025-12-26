# Golang Backend Engineer Agent - Detailed Guide

This document contains comprehensive examples, templates, and best practices for Go backend development.

## Clean Architecture Template

```
project/
├── cmd/
│   └── api/
│       └── main.go           # Application entry point
├── internal/
│   ├── domain/               # Business logic and entities
│   │   ├── entity.go
│   │   └── repository.go     # Repository interfaces
│   ├── usecase/              # Business rules / Application logic
│   │   └── user_usecase.go
│   ├── repository/           # Data access implementations
│   │   └── user_repository.go
│   ├── delivery/             # Delivery mechanisms (HTTP, gRPC, etc.)
│   │   └── http/
│   │       ├── handler.go
│   │       └── middleware.go
│   └── infrastructure/       # External concerns
│       ├── database/
│       └── config/
├── pkg/                      # Public libraries
├── api/                      # API definitions (OpenAPI, protobuf)
├── configs/                  # Configuration files
├── migrations/               # Database migrations
├── scripts/                  # Build and deployment scripts
└── go.mod
```

## Fiber Handler Example

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

func (h *UserHandler) GetUser(c *fiber.Ctx) error {
    id, err := c.ParamsInt("id")
    if err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
            "error": "Invalid user ID",
        })
    }

    user, err := h.userUseCase.GetByID(c.Context(), id)
    if err != nil {
        return c.Status(fiber.StatusNotFound).JSON(fiber.Map{
            "error": "User not found",
        })
    }

    return c.JSON(user)
}
```

## GORM Repository Example

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

func (r *userRepository) Update(ctx context.Context, user *entity.User) error {
    return r.db.WithContext(ctx).Save(user).Error
}

func (r *userRepository) Delete(ctx context.Context, id int) error {
    return r.db.WithContext(ctx).Delete(&entity.User{}, id).Error
}

func (r *userRepository) List(ctx context.Context, limit, offset int) ([]*entity.User, error) {
    var users []*entity.User
    err := r.db.WithContext(ctx).
        Limit(limit).
        Offset(offset).
        Find(&users).Error
    return users, err
}
```

## Cobra CLI Example

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
        // Start server logic
    },
}

func init() {
    serveCmd.Flags().Int("port", 8080, "Port to run the server on")
    rootCmd.AddCommand(serveCmd)
}

func Execute() {
    if err := rootCmd.Execute(); err != nil {
        fmt.Println(err)
        os.Exit(1)
    }
}
```

## Dependency Injection with Wire

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

## Testing Example

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

func (m *MockUserRepository) Create(ctx context.Context, user *entity.User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func TestUserUseCase_Register(t *testing.T) {
    // Arrange
    mockRepo := new(MockUserRepository)
    useCase := usecase.NewUserUseCase(mockRepo)
    req := &dto.RegisterRequest{
        Email:    "test@example.com",
        Password: "password123",
    }

    mockRepo.On("Create", mock.Anything, mock.Anything).Return(nil)

    // Act
    user, err := useCase.Register(context.Background(), req)

    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, user)
    assert.Equal(t, req.Email, user.Email)
    mockRepo.AssertExpectations(t)
}
```

## Best Practices

### Error Handling
- Always wrap errors with context: `fmt.Errorf("failed to create user: %w", err)`
- Use custom error types for domain-specific errors
- Never ignore errors

### Concurrency
- Use goroutines for concurrent operations
- Always use channels or sync.WaitGroup to manage goroutines
- Use context for cancellation and timeouts
- Avoid shared mutable state

### Database Operations
- Always use context with timeout for database operations
- Use transactions for multi-step operations
- Implement proper indexing for performance
- Use prepared statements to prevent SQL injection

### API Design
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Implement proper status codes
- Validate input data
- Use middleware for cross-cutting concerns (logging, auth)
- Implement rate limiting

### Configuration Management
- Use environment variables for configuration
- Never commit secrets to version control
- Use struct-based configuration with Viper
- Implement configuration validation

## Performance Optimization

- Use connection pooling for database
- Implement caching where appropriate (Redis)
- Use pagination for list endpoints
- Optimize database queries (avoid N+1 queries)
- Use pprof for profiling
- Implement proper logging (structured logging with Zap)
