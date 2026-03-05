### Standard File Templates

#### Domain Entity

```go
package user

import (
    "time"
    "gorm.io/gorm"
)

// User represents a user in the system
type User struct {
    ID        string         `gorm:"type:uuid;primary_key;default:gen_random_uuid()" json:"id"`
    Email     string         `gorm:"type:varchar(255);uniqueIndex;not null" json:"email"`
    Name      string         `gorm:"type:varchar(100);not null" json:"name"`
    Password  string         `gorm:"type:varchar(255);not null" json:"-"`
    Role      string         `gorm:"type:varchar(50);default:'user'" json:"role"`
    Active    bool           `gorm:"default:true" json:"active"`
    CreatedAt time.Time      `gorm:"autoCreateTime" json:"created_at"`
    UpdatedAt time.Time      `gorm:"autoUpdateTime" json:"updated_at"`
    DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
}

// TableName specifies the table name
func (User) TableName() string {
    return "users"
}

// BeforeCreate hook
func (u *User) BeforeCreate(tx *gorm.DB) error {
    // Hash password, validate data, etc.
    return nil
}
```

#### Repository Interface (Domain Layer)

```go
package user

import "context"

// Repository defines user data access methods
type Repository interface {
    Create(ctx context.Context, user *User) error
    GetByID(ctx context.Context, id string) (*User, error)
    GetByEmail(ctx context.Context, email string) (*User, error)
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id string) error
    List(ctx context.Context, offset, limit int) ([]*User, error)
    ExistsByEmail(ctx context.Context, email string) (bool, error)
}

// Domain errors
var (
    ErrNotFound     = errors.New("user not found")
    ErrEmailExists  = errors.New("email already exists")
    ErrInvalidInput = errors.New("invalid input")
)
```

#### Repository Implementation (Adapter Layer)

```go
package repository

import (
    "context"
    "myapp/internal/domain/user"
    "gorm.io/gorm"
)

type userRepository struct {
    db *gorm.DB
}

// NewUserRepository creates a new user repository
func NewUserRepository(db *gorm.DB) user.Repository {
    return &userRepository{db: db}
}

func (r *userRepository) Create(ctx context.Context, u *user.User) error {
    return r.db.WithContext(ctx).Create(u).Error
}

func (r *userRepository) GetByID(ctx context.Context, id string) (*user.User, error) {
    var u user.User
    err := r.db.WithContext(ctx).Where("id = ?", id).First(&u).Error
    if err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, user.ErrNotFound
        }
        return nil, err
    }
    return &u, nil
}

func (r *userRepository) GetByEmail(ctx context.Context, email string) (*user.User, error) {
    var u user.User
    err := r.db.WithContext(ctx).Where("email = ?", email).First(&u).Error
    if err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, user.ErrNotFound
        }
        return nil, err
    }
    return &u, nil
}

func (r *userRepository) Update(ctx context.Context, u *user.User) error {
    return r.db.WithContext(ctx).Save(u).Error
}

func (r *userRepository) Delete(ctx context.Context, id string) error {
    return r.db.WithContext(ctx).Delete(&user.User{}, "id = ?", id).Error
}

func (r *userRepository) List(ctx context.Context, offset, limit int) ([]*user.User, error) {
    var users []*user.User
    err := r.db.WithContext(ctx).
        Offset(offset).
        Limit(limit).
        Order("created_at DESC").
        Find(&users).Error
    return users, err
}

func (r *userRepository) ExistsByEmail(ctx context.Context, email string) (bool, error) {
    var count int64
    err := r.db.WithContext(ctx).
        Model(&user.User{}).
        Where("email = ?", email).
        Count(&count).Error
    return count > 0, err
}
```

#### Service Interface (Domain Layer)

```go
package user

import "context"

// Service defines user business logic methods
type Service interface {
    Create(ctx context.Context, user *User) (*User, error)
    GetByID(ctx context.Context, id string) (*User, error)
    Update(ctx context.Context, id string, updates map[string]interface{}) (*User, error)
    Delete(ctx context.Context, id string) error
    List(ctx context.Context, page, pageSize int) ([]*User, int64, error)
}
```

#### Service Implementation (Use Case Layer)

```go
package usecase

import (
    "context"
    "myapp/internal/domain/user"
    "myapp/pkg/logger"
    "github.com/pkg/errors"
    "golang.org/x/crypto/bcrypt"
)

type userService struct {
    repo   user.Repository
    logger logger.Logger
}

// NewUserService creates a new user service
func NewUserService(repo user.Repository, logger logger.Logger) user.Service {
    return &userService{
        repo:   repo,
        logger: logger,
    }
}

func (s *userService) Create(ctx context.Context, u *user.User) (*user.User, error) {
    // Validate
    if err := s.validate(u); err != nil {
        return nil, errors.Wrap(err, "validation failed")
    }
    
    // Check if email exists
    exists, err := s.repo.ExistsByEmail(ctx, u.Email)
    if err != nil {
        return nil, errors.Wrap(err, "failed to check email existence")
    }
    if exists {
        return nil, user.ErrEmailExists
    }
    
    // Hash password
    hashedPassword, err := bcrypt.GenerateFromPassword([]byte(u.Password), bcrypt.DefaultCost)
    if err != nil {
        return nil, errors.Wrap(err, "failed to hash password")
    }
    u.Password = string(hashedPassword)
    
    // Create user
    if err := s.repo.Create(ctx, u); err != nil {
        return nil, errors.Wrap(err, "failed to create user")
    }
    
    s.logger.Info("User created", "user_id", u.ID, "email", u.Email)
    return u, nil
}

func (s *userService) GetByID(ctx context.Context, id string) (*user.User, error) {
    u, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, errors.Wrap(err, "failed to get user")
    }
    return u, nil
}

func (s *userService) validate(u *user.User) error {
    if u.Email == "" {
        return errors.New("email is required")
    }
    if u.Name == "" {
        return errors.New("name is required")
    }
    if u.Password == "" {
        return errors.New("password is required")
    }
    return nil
}
```

#### Fiber HTTP Handler (Adapter Layer)

```go
package handler

import (
    "myapp/internal/domain/user"
    "myapp/internal/dto/request"
    "myapp/internal/dto/response"
    "myapp/pkg/errors"
    "github.com/gofiber/fiber/v2"
)

type UserHandler struct {
    userService user.Service
}

func NewUserHandler(userService user.Service) *UserHandler {
    return &UserHandler{userService: userService}
}

// CreateUser creates a new user
// @Summary Create user
// @Description Create a new user account
// @Tags users
// @Accept json
// @Produce json
// @Param user body request.CreateUserRequest true "User data"
// @Success 201 {object} response.UserResponse
// @Failure 400 {object} response.ErrorResponse
// @Failure 409 {object} response.ErrorResponse
// @Router /api/v1/users [post]
func (h *UserHandler) CreateUser(c *fiber.Ctx) error {
    var req request.CreateUserRequest
    
    // Parse and validate request
    if err := c.BodyParser(&req); err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(response.ErrorResponse{
            Code:    "INVALID_REQUEST",
            Message: "Invalid request body",
        })
    }
    
    if err := req.Validate(); err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(response.ErrorResponse{
            Code:    "VALIDATION_ERROR",
            Message: err.Error(),
        })
    }
    
    // Call service
    createdUser, err := h.userService.Create(c.Context(), &user.User{
        Email:    req.Email,
        Name:     req.Name,
        Password: req.Password,
    })
    
    if err != nil {
        // Handle specific errors
        if errors.Is(err, user.ErrEmailExists) {
            return c.Status(fiber.StatusConflict).JSON(response.ErrorResponse{
                Code:    "EMAIL_EXISTS",
                Message: "Email already registered",
            })
        }
        return c.Status(fiber.StatusInternalServerError).JSON(response.ErrorResponse{
            Code:    "INTERNAL_ERROR",
            Message: "Failed to create user",
        })
    }
    
    // Return response
    return c.Status(fiber.StatusCreated).JSON(response.UserResponse{
        ID:        createdUser.ID,
        Email:     createdUser.Email,
        Name:      createdUser.Name,
        Role:      createdUser.Role,
        Active:    createdUser.Active,
        CreatedAt: createdUser.CreatedAt,
    })
}

// RegisterRoutes registers all user routes
func (h *UserHandler) RegisterRoutes(router fiber.Router) {
    users := router.Group("/users")
    
    users.Post("/", h.CreateUser)
    users.Get("/:id", h.GetUser)
    users.Put("/:id", h.UpdateUser)
    users.Delete("/:id", h.DeleteUser)
    users.Get("/", h.ListUsers)
}
```

#### DTO (Data Transfer Objects)

```go
package request

import "github.com/go-playground/validator/v10"

type CreateUserRequest struct {
    Email    string `json:"email" validate:"required,email"`
    Name     string `json:"name" validate:"required,min=2,max=100"`
    Password string `json:"password" validate:"required,min=8"`
}

func (r *CreateUserRequest) Validate() error {
    validate := validator.New()
    return validate.Struct(r)
}

package response

import "time"

type UserResponse struct {
    ID        string    `json:"id"`
    Email     string    `json:"email"`
    Name      string    `json:"name"`
    Role      string    `json:"role"`
    Active    bool      `json:"active"`
    CreatedAt time.Time `json:"created_at"`
}

type ErrorResponse struct {
    Code    string `json:"code"`
    Message string `json:"message"`
    Details any    `json:"details,omitempty"`
}
```

#### Cobra CLI Command

```go
package cmd

import (
    "fmt"
    "github.com/spf13/cobra"
    "github.com/spf13/viper"
)

var (
    cfgFile string
    verbose bool
)

// rootCmd represents the base command
var rootCmd = &cobra.Command{
    Use:   "myapp",
    Short: "MyApp CLI tool",
    Long:  `A powerful CLI tool built with Cobra.`,
}

func Execute() error {
    return rootCmd.Execute()
}

func init() {
    cobra.OnInitialize(initConfig)
    
    rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.myapp.yaml)")
    rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "verbose output")
    
    viper.BindPFlag("verbose", rootCmd.PersistentFlags().Lookup("verbose"))
}

func initConfig() {
    if cfgFile != "" {
        viper.SetConfigFile(cfgFile)
    } else {
        home, _ := os.UserHomeDir()
        viper.AddConfigPath(home)
        viper.SetConfigType("yaml")
        viper.SetConfigName(".myapp")
    }
    
    viper.AutomaticEnv()
    viper.ReadInConfig()
}

// userCmd represents the user command
var userCmd = &cobra.Command{
    Use:   "user",
    Short: "Manage users",
}

var createUserCmd = &cobra.Command{
    Use:   "create",
    Short: "Create a new user",
    RunE: func(cmd *cobra.Command, args []string) error {
        email, _ := cmd.Flags().GetString("email")
        name, _ := cmd.Flags().GetString("name")
        
        fmt.Printf("Creating user: %s (%s)\n", name, email)
        // Implement user creation logic
        
        return nil
    },
}

func init() {
    rootCmd.AddCommand(userCmd)
    userCmd.AddCommand(createUserCmd)
    
    createUserCmd.Flags().StringP("email", "e", "", "User email (required)")
    createUserCmd.Flags().StringP("name", "n", "", "User name (required)")
    createUserCmd.MarkFlagRequired("email")
    createUserCmd.MarkFlagRequired("name")
}
```

