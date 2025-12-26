# Java Backend Engineer Agent - Detailed Guide

This document contains comprehensive examples, templates, and best practices for Java backend development with Spring Boot.

## Table of Contents

1. [Project Structure](#project-structure)
2. [RESTful API Development](#restful-api-development)
3. [Distributed Scheduling](#distributed-scheduling)
4. [Distributed Lock Pattern](#distributed-lock-pattern)
5. [Data Access Layer](#data-access-layer)
6. [Transaction Management](#transaction-management)
7. [Exception Handling](#exception-handling)
8. [Testing Strategies](#testing-strategies)
9. [Best Practices](#best-practices)

## Project Structure

```
project/
├── src/main/java/
│   └── com/example/
│       ├── Application.java          # Spring Boot entry point
│       ├── config/                   # Configuration classes
│       │   ├── SecurityConfig.java
│       │   └── RedisConfig.java
│       ├── controller/               # REST controllers
│       │   └── UserController.java
│       ├── service/                  # Business logic
│       │   ├── UserService.java
│       │   └── impl/
│       │       └── UserServiceImpl.java
│       ├── repository/               # Data access layer
│       │   └── UserDAO.java
│       ├── model/                    # Data models
│       │   ├── domain/
│       │   │   └── UserDO.java
│       │   ├── request/
│       │   │   └── UserRequest.java
│       │   └── response/
│       │       └── UserResponse.java
│       ├── schedule/                 # Scheduled tasks
│       │   └── UserSyncSchedule.java
│       └── exception/                # Custom exceptions
│           ├── BusinessException.java
│           └── GlobalExceptionHandler.java
├── src/main/resources/
│   ├── application.yml              # Application configuration
│   ├── mapper/                      # MyBatis mappers
│   │   └── UserMapper.xml
│   └── logback-spring.xml           # Logging configuration
└── src/test/java/                   # Tests
    └── com/example/
        ├── service/
        │   └── UserServiceTest.java
        └── controller/
            └── UserControllerTest.java
```

## RESTful API Development

### Standard Controller

```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Slf4j
public class UserController {

    private final UserService userService;

    @PostMapping("/query")
    public ResponseEntity<UserResponse> queryUsers(@RequestBody UserRequest request) {
        UserResponse response = userService.queryUsers(request);
        return ResponseEntity.ok(response);
    }

    @PostMapping
    public ResponseEntity<UserResponse> createUser(@RequestBody UserRequest request) {
        userService.createUser(request);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserDO> getUserById(@PathVariable Long id) {
        UserDO user = userService.getUserById(id);
        return ResponseEntity.ok(user);
    }
}
```

### Service Layer

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserDAO userDAO;

    @Transactional(readOnly = true)
    public UserResponse queryUsers(UserRequest request) {
        log.info("Querying users with request: {}", request);

        List<UserDO> users = userDAO.queryUserPage(request);

        return UserResponse.builder()
            .users(users)
            .pageInfo(request.getPageInfo())
            .build();
    }

    @Transactional
    public void createUser(UserRequest request) {
        log.info("Creating user: {}", request);

        // Business logic
        UserDO user = buildUserDO(request);
        userDAO.insertUser(user);
    }

    private UserDO buildUserDO(UserRequest request) {
        return UserDO.builder()
            .username(request.getUsername())
            .email(request.getEmail())
            .build();
    }
}
```

### Request/Response Models

```java
@Data
@Builder
public class UserRequest implements Serializable {
    private String username;
    private String email;

    @NotNull
    private PageInfo pageInfo;

    // Validation annotations
    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    public String getUsername() {
        return username;
    }
}

@Data
@Builder
public class UserResponse implements Serializable {
    private List<UserDO> users;
    private PageInfo pageInfo;
    private Integer totalCount;
}
```

## Distributed Scheduling

### Scheduled Task with Spring

```java
@Component
@Slf4j
public class UserSyncSchedule {

    private final UserService userService;

    @Scheduled(cron = "0 0 2 * * ?")  // Daily at 2 AM
    public void syncUserData() {
        log.info("Starting user data synchronization...");
        try {
            userService.syncUserData();
            log.info("User data sync completed successfully");
        } catch (Exception e) {
            log.error("User data sync failed", e);
            throw e;
        }
    }
}
```

## Distributed Lock Pattern

### Redis Distributed Lock

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderService {

    private final DistributedRedisLock redisLock;
    private final OrderDAO orderDAO;

    public OrderResult createOrder(OrderRequest request) {
        String lockKey = "ORDER_CREATE_" + request.getUserId();
        boolean locked = false;

        try {
            // Try to acquire lock with 5s timeout, 30s expiration
            locked = redisLock.trySourceLock(lockKey, 5000, 30000);

            if (!locked) {
                throw new BusinessException("Order creation in progress");
            }

            // Business logic
            OrderDO order = buildOrder(request);
            orderDAO.insertOrder(order);

            return OrderResult.success(order.getOrderId());

        } finally {
            if (locked) {
                redisLock.unlock(lockKey);
            }
        }
    }
}
```

## Data Access Layer

### MyBatis DAO Pattern

```java
@Repository
public class UserDAO extends AbstractSimpleDAO {

    /**
     * Query users with pagination.
     * Mapper ID ending with "Page" triggers auto-pagination.
     */
    public List<UserDO> queryUserPage(UserRequest request) {
        return this.getSession().selectList("UserMapper.queryUserPage", request);
    }

    /**
     * Get user by ID.
     */
    public UserDO getUserById(Long userId) {
        return this.getSession().selectOne("UserMapper.getUserById", userId);
    }

    /**
     * Insert user.
     */
    public void insertUser(UserDO user) {
        this.getSession().insert("UserMapper.insertUser", user);
    }

    /**
     * Update user.
     */
    public void updateUser(UserDO user) {
        this.getSession().update("UserMapper.updateUser", user);
    }

    /**
     * Delete user.
     */
    public void deleteUser(Long userId) {
        this.getSession().delete("UserMapper.deleteUser", userId);
    }
}
```

### MyBatis Mapper XML

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
    "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<mapper namespace="UserMapper">

    <resultMap id="UserDOResult" type="com.example.model.domain.UserDO">
        <id column="id" property="id"/>
        <result column="username" property="username"/>
        <result column="email" property="email"/>
        <result column="created_time" property="createdTime"/>
        <result column="updated_time" property="updatedTime"/>
    </resultMap>

    <select id="queryUserPage" resultMap="UserDOResult">
        SELECT
            id, username, email, created_time, updated_time
        FROM
            t_user
        <where>
            <if test="username != null and username != ''">
                AND username LIKE CONCAT('%', #{username}, '%')
            </if>
            <if test="email != null and email != ''">
                AND email = #{email}
            </if>
        </where>
        ORDER BY created_time DESC
    </select>

    <select id="getUserById" resultMap="UserDOResult">
        SELECT
            id, username, email, created_time, updated_time
        FROM
            t_user
        WHERE
            id = #{userId}
    </select>

    <insert id="insertUser" parameterType="com.example.model.domain.UserDO"
        useGeneratedKeys="true" keyProperty="id">
        INSERT INTO t_user (
            username, email, created_time, updated_time
        ) VALUES (
            #{username}, #{email}, NOW(), NOW()
        )
    </insert>

    <update id="updateUser" parameterType="com.example.model.domain.UserDO">
        UPDATE t_user
        <set>
            <if test="username != null">username = #{username},</if>
            <if test="email != null">email = #{email},</if>
            updated_time = NOW()
        </set>
        WHERE id = #{id}
    </update>

    <delete id="deleteUser">
        DELETE FROM t_user WHERE id = #{userId}
    </delete>

</mapper>
```

## Transaction Management

### Transaction Propagation Strategies

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class PaymentService {

    private final OrderDAO orderDAO;
    private final PaymentDAO paymentDAO;
    private final InventoryService inventoryService;

    /**
     * REQUIRED: Use existing transaction or create new one (default)
     */
    @Transactional(propagation = Propagation.REQUIRED)
    public void processPayment(PaymentRequest request) {
        // Business logic
    }

    /**
     * REQUIRES_NEW: Always create new transaction, suspend existing if any
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordAuditLog(AuditLog log) {
        // Always executes in its own transaction
    }

    /**
     * NESTED: Execute within nested transaction if one exists
     */
    @Transactional(propagation = Propagation.NESTED)
    public void updatePartialData(Long userId) {
        // Can rollback independently
    }

    /**
     * NOT_SUPPORTED: Execute without transaction, suspend existing if any
     */
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void sendNotification(Notification notification) {
        // Non-transactional operation
    }

    /**
     * NEVER: Execute without transaction, throw exception if one exists
     */
    @Transactional(propagation = Propagation.NEVER)
    public void logAccess(AccessLog log) {
        // Must not be called within a transaction
    }

    /**
     * MANDATORY: Must be called within existing transaction
     */
    @Transactional(propagation = Propagation.MANDATORY)
    public void validateTransaction() {
        // Requires an active transaction
    }
}
```

### Transaction Rollback Strategies

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class TransactionalService {

    /**
     * Rollback on specific exceptions
     */
    @Transactional(rollbackFor = {BusinessException.class, SystemException.class})
    public void executeWithSpecificRollback() {
        // Only rolls back for specified exceptions
    }

    /**
     * No rollback on specific exceptions
     */
    @Transactional(noRollbackFor = {ValidationException.class})
    public void executeWithNoRollback() {
        // Won't rollback for ValidationException
    }

    /**
     * Read-only transaction
     */
    @Transactional(readOnly = true)
    public List<UserDO> queryUsers() {
        // Optimized for read operations
        return userDAO.selectAll();
    }

    /**
     * Set transaction timeout
     */
    @Transactional(timeout = 30)  // 30 seconds
    public void longRunningOperation() {
        // Will timeout after 30 seconds
    }

    /**
     * Specify isolation level
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    public void readCommittedOperation() {
        // Prevents dirty reads
    }
}
```

## Exception Handling

### Custom Exceptions

```java
/**
 * Business exception for expected business errors
 */
@Getter
public class BusinessException extends RuntimeException {
    private final String errorCode;
    private final String errorMessage;

    public BusinessException(String errorCode, String errorMessage) {
        super(errorMessage);
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    public BusinessException(String errorMessage) {
        this("BUSINESS_ERROR", errorMessage);
    }
}

/**
 * System exception for unexpected system errors
 */
@Getter
public class SystemException extends RuntimeException {
    private final String errorCode;
    private final String errorMessage;

    public SystemException(String errorCode, String errorMessage) {
        super(errorMessage);
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    public SystemException(String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.errorCode = "SYSTEM_ERROR";
        this.errorMessage = errorMessage;
    }
}

/**
 * Validation exception
 */
@Getter
public class ValidationException extends RuntimeException {
    private final Map<String, String> errors;

    public ValidationException(Map<String, String> errors) {
        super("Validation failed");
        this.errors = errors;
    }
}
```

### Global Exception Handler

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    /**
     * Handle business exceptions
     */
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusinessException(BusinessException ex) {
        log.warn("Business exception: {}", ex.getErrorMessage());

        ErrorResponse error = ErrorResponse.builder()
            .errorCode(ex.getErrorCode())
            .errorMessage(ex.getErrorMessage())
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.badRequest().body(error);
    }

    /**
     * Handle validation exceptions
     */
    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(ValidationException ex) {
        log.warn("Validation exception: {}", ex.getErrors());

        ErrorResponse error = ErrorResponse.builder()
            .errorCode("VALIDATION_ERROR")
            .errorMessage("Validation failed")
            .details(ex.getErrors())
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.badRequest().body(error);
    }

    /**
     * Handle system exceptions
     */
    @ExceptionHandler(SystemException.class)
    public ResponseEntity<ErrorResponse> handleSystemException(SystemException ex) {
        log.error("System exception: {}", ex.getErrorMessage(), ex);

        ErrorResponse error = ErrorResponse.builder()
            .errorCode(ex.getErrorCode())
            .errorMessage("An internal system error occurred")
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }

    /**
     * Handle all other exceptions
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleException(Exception ex) {
        log.error("Unexpected exception: {}", ex.getMessage(), ex);

        ErrorResponse error = ErrorResponse.builder()
            .errorCode("INTERNAL_SERVER_ERROR")
            .errorMessage("An unexpected error occurred")
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
```

## Testing Strategies

### Unit Tests with JUnit 5 and Mockito

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserDAO userDAO;

    @InjectMocks
    private UserService userService;

    @Test
    @DisplayName("Should return user when user exists")
    void getUserById_WhenUserExists_ReturnsUser() {
        // Arrange
        Long userId = 1L;
        UserDO expectedUser = UserDO.builder()
            .id(userId)
            .username("testuser")
            .email("test@example.com")
            .build();
        when(userDAO.getUserById(userId)).thenReturn(expectedUser);

        // Act
        UserDO result = userService.getUserById(userId);

        // Assert
        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo(userId);
        assertThat(result.getUsername()).isEqualTo("testuser");
        verify(userDAO, times(1)).getUserById(userId);
    }

    @Test
    @DisplayName("Should throw exception when user not found")
    void getUserById_WhenUserNotFound_ThrowsException() {
        // Arrange
        Long userId = 999L;
        when(userDAO.getUserById(userId)).thenReturn(null);

        // Act & Assert
        assertThatThrownBy(() -> userService.getUserById(userId))
            .isInstanceOf(BusinessException.class)
            .hasMessageContaining("User not found");
    }

    @Test
    @DisplayName("Should create user successfully")
    void createUser_WithValidData_CreatesUser() {
        // Arrange
        UserRequest request = UserRequest.builder()
            .username("newuser")
            .email("new@example.com")
            .build();

        // Act
        userService.createUser(request);

        // Assert
        verify(userDAO, times(1)).insertUser(any(UserDO.class));
    }
}
```

### Integration Tests with Spring Boot Test

```java
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class UserControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserDAO userDAO;

    @Test
    @DisplayName("Should query users successfully")
    void queryUsers_WithValidRequest_ReturnsUsers() throws Exception {
        // Arrange
        UserRequest request = UserRequest.builder()
            .username("test")
            .pageInfo(PageInfo.builder().pageNum(1).pageSize(10).build())
            .build();

        // Act & Assert
        mockMvc.perform(post("/api/v1/users/query")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.users").isArray())
                .andExpect(jsonPath("$.totalCount").isNumber());
    }

    @Test
    @DisplayName("Should return validation error for invalid request")
    void createUser_WithInvalidData_ReturnsValidationError() throws Exception {
        // Arrange
        UserRequest request = UserRequest.builder()
            .username("")  // Invalid: empty username
            .build();

        // Act & Assert
        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
}
```

## Best Practices

### Code Quality

✅ **DO:**
- Use Lombok annotations to reduce boilerplate
- Follow Java naming conventions strictly
- Write self-documenting code with clear names
- Add JavaDoc for all public APIs
- Use Optional to avoid NPE
- Keep methods short and focused
- Apply SOLID principles

❌ **DON'T:**
- Create god classes with too many responsibilities
- Use vague names like `data1`, `temp`
- Repeat code (DRY principle)
- Ignore null checks
- Write methods longer than 50 lines
- Skip documentation

### Performance Optimization

✅ **DO:**
- Use pagination for large datasets
- Implement caching (Redis, MyBatis L2)
- Use batch operations for bulk data
- Optimize SQL queries with proper indexes
- Monitor slow queries
- Use connection pooling
- Enable async processing for long tasks

❌ **DON'T:**
- Load entire database into memory
- N+1 query problems
- Ignore database indexes
- Synchronous processing for long tasks
- Ignore connection pool configuration

### Security Best Practices

✅ **DO:**
- Validate all inputs (JSR-303)
- Use parameterized queries
- Sanitize user input
- Encrypt sensitive data
- Implement authentication/authorization
- Use HTTPS in production
- Log security events

❌ **DON'T:**
- String concatenation for SQL
- Trust client-side validation
- Expose sensitive data in logs
- Hardcode credentials
- Ignore XSS/CSRF protection
- Store passwords in plain text

### Dependency Management

✅ **DO:**
- Check existing dependencies first
- Reuse project libraries
- Keep dependencies up to date
- Document dependency decisions
- Use stable versions

❌ **DON'T:**
- Add dependencies without checking
- Duplicate functionality
- Use beta versions in production
- Ignore security vulnerabilities
- Over-engineer solutions

Remember: **Prioritize code quality, maintainability, and enterprise-grade reliability.**
