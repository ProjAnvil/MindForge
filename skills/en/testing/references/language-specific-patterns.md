## Language-Specific Test Templates

### Java (JUnit 5 + Mockito + AssertJ)

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.*;
import static org.assertj.core.api.Assertions.*;

class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private UserService userService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    @DisplayName("Should successfully create user with valid data")
    void givenValidUser_whenCreate_thenSuccess() {
        // Arrange
        User user = new User("test@example.com", "Test User");
        when(userRepository.existsByEmail(user.getEmail())).thenReturn(false);
        when(userRepository.save(any(User.class))).thenReturn(user);

        // Act
        User createdUser = userService.create(user);

        // Assert
        assertThat(createdUser)
            .isNotNull()
            .extracting(User::getEmail, User::getName)
            .containsExactly("test@example.com", "Test User");

        verify(userRepository).existsByEmail(user.getEmail());
        verify(userRepository).save(user);
        verify(emailService).sendWelcomeEmail(user.getEmail());
    }

    @Test
    @DisplayName("Should throw exception when email already exists")
    void givenExistingEmail_whenCreate_thenThrowException() {
        // Arrange
        User user = new User("existing@example.com", "Test User");
        when(userRepository.existsByEmail(user.getEmail())).thenReturn(true);

        // Act & Assert
        assertThatThrownBy(() -> userService.create(user))
            .isInstanceOf(EmailAlreadyExistsException.class)
            .hasMessage("Email already registered: existing@example.com");

        verify(userRepository).existsByEmail(user.getEmail());
        verify(userRepository, never()).save(any());
    }
}
```

### Go (testing + testify)

```go
package user_test

import (
    "context"
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"
)

// Mock repository
type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) Create(ctx context.Context, user *User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func (m *MockUserRepository) ExistsByEmail(ctx context.Context, email string) (bool, error) {
    args := m.Called(ctx, email)
    return args.Bool(0), args.Error(1)
}

// Test suite
func TestUserService_Create(t *testing.T) {
    t.Run("should successfully create user with valid data", func(t *testing.T) {
        // Arrange
        mockRepo := new(MockUserRepository)
        service := NewUserService(mockRepo)

        user := &User{
            Email: "test@example.com",
            Name:  "Test User",
        }

        mockRepo.On("ExistsByEmail", mock.Anything, user.Email).Return(false, nil)
        mockRepo.On("Create", mock.Anything, user).Return(nil)

        // Act
        err := service.Create(context.Background(), user)

        // Assert
        require.NoError(t, err)
        assert.NotEmpty(t, user.ID)
        mockRepo.AssertExpectations(t)
    })

    t.Run("should return error when email already exists", func(t *testing.T) {
        // Arrange
        mockRepo := new(MockUserRepository)
        service := NewUserService(mockRepo)

        user := &User{
            Email: "existing@example.com",
            Name:  "Test User",
        }

        mockRepo.On("ExistsByEmail", mock.Anything, user.Email).Return(true, nil)

        // Act
        err := service.Create(context.Background(), user)

        // Assert
        require.Error(t, err)
        assert.Contains(t, err.Error(), "email already exists")
        mockRepo.AssertExpectations(t)
        mockRepo.AssertNotCalled(t, "Create", mock.Anything, mock.Anything)
    })
}

// Table-driven test example
func TestValidateEmail(t *testing.T) {
    tests := []struct {
        name    string
        email   string
        wantErr bool
    }{
        {"valid email", "test@example.com", false},
        {"empty email", "", true},
        {"no @ symbol", "testexample.com", true},
        {"no domain", "test@", true},
        {"no local part", "@example.com", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateEmail(tt.email)
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }
        })
    }
}
```

### Python (pytest)

```python
import pytest
from unittest.mock import Mock, patch, call
from user_service import UserService
from exceptions import EmailAlreadyExistsError

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def user_service(mock_repository):
    return UserService(mock_repository)

class TestUserService:

    def test_create_valid_user_success(self, user_service, mock_repository):
        # Arrange
        user_data = {
            'email': 'test@example.com',
            'name': 'Test User'
        }
        mock_repository.exists_by_email.return_value = False
        mock_repository.save.return_value = user_data

        # Act
        result = user_service.create(user_data)

        # Assert
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'Test User'
        mock_repository.exists_by_email.assert_called_once_with('test@example.com')
        mock_repository.save.assert_called_once()

    def test_create_existing_email_raises_exception(self, user_service, mock_repository):
        # Arrange
        user_data = {
            'email': 'existing@example.com',
            'name': 'Test User'
        }
        mock_repository.exists_by_email.return_value = True

        # Act & Assert
        with pytest.raises(EmailAlreadyExistsError) as exc_info:
            user_service.create(user_data)

        assert 'already registered' in str(exc_info.value)
        mock_repository.exists_by_email.assert_called_once()
        mock_repository.save.assert_not_called()

# Parametrized test
@pytest.mark.parametrize("email,expected", [
    ("test@example.com", True),
    ("", False),
    ("no-at-symbol", False),
    ("@example.com", False),
    ("test@", False),
])
def test_validate_email(email, expected):
    result = validate_email(email)
    assert result == expected
```

### JavaScript (Jest)

```javascript
import { UserService } from './UserService';
import { EmailAlreadyExistsError } from './errors';

describe('UserService', () => {
  let userService;
  let mockRepository;
  let mockEmailService;

  beforeEach(() => {
    mockRepository = {
      existsByEmail: jest.fn(),
      save: jest.fn(),
    };
    mockEmailService = {
      sendWelcomeEmail: jest.fn(),
    };
    userService = new UserService(mockRepository, mockEmailService);
  });

  describe('create', () => {
    it('should successfully create user with valid data', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        name: 'Test User',
      };
      mockRepository.existsByEmail.mockResolvedValue(false);
      mockRepository.save.mockResolvedValue({ id: '1', ...userData });

      // Act
      const result = await userService.create(userData);

      // Assert
      expect(result).toMatchObject({
        email: 'test@example.com',
        name: 'Test User',
      });
      expect(mockRepository.existsByEmail).toHaveBeenCalledWith('test@example.com');
      expect(mockRepository.save).toHaveBeenCalledTimes(1);
      expect(mockEmailService.sendWelcomeEmail).toHaveBeenCalledWith('test@example.com');
    });

    it('should throw error when email already exists', async () => {
      // Arrange
      const userData = {
        email: 'existing@example.com',
        name: 'Test User',
      };
      mockRepository.existsByEmail.mockResolvedValue(true);

      // Act & Assert
      await expect(userService.create(userData))
        .rejects
        .toThrow(EmailAlreadyExistsError);

      expect(mockRepository.existsByEmail).toHaveBeenCalled();
      expect(mockRepository.save).not.toHaveBeenCalled();
    });
  });
});

// Test table pattern
describe('validateEmail', () => {
  test.each([
    ['test@example.com', true],
    ['', false],
    ['no-at-symbol', false],
    ['@example.com', false],
    ['test@', false],
  ])('validateEmail(%s) should return %s', (email, expected) => {
    expect(validateEmail(email)).toBe(expected);
  });
});
```
