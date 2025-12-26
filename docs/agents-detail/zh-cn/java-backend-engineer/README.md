# Java 后端工程师 Agent - 详细指南

本文档包含使用 Spring Boot 和 Mumble SDK 进行 Java 后端开发的综合示例、模板和最佳实践。

## 目录

1. [项目结构](#项目结构)
2. [RESTful API 开发](#restful-api-开发)
3. [分布式调度](#分布式调度)
4. [分布式锁模式](#分布式锁模式)
5. [数据访问层](#数据访问层)
6. [事务管理](#事务管理)
7. [异常处理](#异常处理)
8. [测试策略](#测试策略)
9. [最佳实践](#最佳实践)

## 项目结构

```
project/
├── src/main/java/
│   └── com/example/
│       ├── Application.java          # Spring Boot 入口点
│       ├── config/                   # 配置类
│       │   ├── SecurityConfig.java
│       │   └── RedisConfig.java
│       ├── controller/               # REST 控制器
│       │   └── UserController.java
│       ├── service/                  # 业务逻辑
│       │   ├── UserService.java
│       │   └── impl/
│       │       └── UserServiceImpl.java
│       ├── repository/               # 数据访问层
│       │   └── UserDAO.java
│       ├── model/                    # 数据模型
│       │   ├── domain/
│       │   │   └── UserDO.java
│       │   ├── request/
│       │   │   └── UserRequest.java
│       │   └── response/
│       │       └── UserResponse.java
│       ├── schedule/                 # 定时任务
│       │   └── UserSyncSchedule.java
│       └── exception/                # 自定义异常
│           ├── BusinessException.java
│           └── GlobalExceptionHandler.java
├── src/main/resources/
│   ├── application.yml              # 应用配置
│   ├── mapper/                      # MyBatis 映射文件
│   │   └── UserMapper.xml
│   └── logback-spring.xml           # 日志配置
└── src/test/java/                   # 测试
    └── com/example/
        ├── service/
        │   └── UserServiceTest.java
        └── controller/
            └── UserControllerTest.java
```

## RESTful API 开发

### 使用 Mumble SDK 的标准控制器

```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Slf4j
public class UserController extends MumbleAbstractBaseController<UserRequest, UserResponse> {

    private final UserService userService;

    @PostMapping("/query")
    public DeferredResult<BaseMessage> queryUsers(@RequestBody UserRequest request) {
        return super.doAsyncService(request);
    }

    @Override
    public UserResponse execute(UserRequest request) {
        return userService.queryUsers(request);
    }

    @Override
    public BizErrors validate(UserRequest request) {
        BizErrors errors = new BizErrors();
        // Mumble 自动验证注解
        return errors;
    }
}
```

### 服务层

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

        // 业务逻辑
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

### 请求/响应模型

```java
@Data
@Builder
public class UserRequest implements Serializable {
    private String username;
    private String email;

    @NotNull
    private PageInfo pageInfo;

    // 验证注解
    @NotBlank(message = "用户名必填")
    @Size(min = 3, max = 50, message = "用户名长度必须在 3 到 50 个字符之间")
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

## 分布式调度

### Mumble 定时任务

```java
@Component
@MumbleScheduled("User Data Sync Task")
@Slf4j
public class UserSyncSchedule {

    private final UserService userService;

    @MumbleCron(
        lock = "USER_SYNC_LOCK",
        cron = "0 0 2 * * ?",  // 每天凌晨 2 点
        desc = "从外部系统同步用户数据",
        retry = 3,
        timeoutInMs = 300000
    )
    public void syncUserData() {
        log.info("Starting user data synchronization...");
        try {
            userService.syncUserData();
            log.info("User data sync completed successfully");
        } catch (Exception e) {
            log.error("User data sync failed", e);
            throw e;  // 触发重试机制
        }
    }
}
```

## 分布式锁模式

### Redis 分布式锁

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
            // 尝试获取锁,超时时间 5 秒,锁过期时间 30 秒
            locked = redisLock.trySourceLock(lockKey, 5000, 30000);

            if (!locked) {
                throw new BusinessException("订单创建中");
            }

            // 业务逻辑
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

## 数据访问层

### MyBatis DAO 模式

```java
@Repository
public class UserDAO extends AbstractSimpleDAO {

    /**
     * 分页查询用户。
     * Mapper ID 以 "Page" 结尾会触发自动分页。
     */
    public List<UserDO> queryUserPage(UserRequest request) {
        return this.getSession().selectList("UserMapper.queryUserPage", request);
    }

    /**
     * 根据 ID 获取用户。
     */
    public UserDO getUserById(Long userId) {
        return this.getSession().selectOne("UserMapper.getUserById", userId);
    }

    /**
     * 插入用户。
     */
    public void insertUser(UserDO user) {
        this.getSession().insert("UserMapper.insertUser", user);
    }

    /**
     * 更新用户。
     */
    public void updateUser(UserDO user) {
        this.getSession().update("UserMapper.updateUser", user);
    }

    /**
     * 删除用户。
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

## 事务管理

### 事务传播策略

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class PaymentService {

    private final OrderDAO orderDAO;
    private final PaymentDAO paymentDAO;
    private final InventoryService inventoryService;

    /**
     * REQUIRED: 使用现有事务或创建新事务(默认)
     */
    @Transactional(propagation = Propagation.REQUIRED)
    public void processPayment(PaymentRequest request) {
        // 业务逻辑
    }

    /**
     * REQUIRES_NEW: 总是创建新事务,挂起现有事务(如果存在)
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordAuditLog(AuditLog log) {
        // 始终在自己的事务中执行
    }

    /**
     * NESTED: 在嵌套事务中执行(如果存在)
     */
    @Transactional(propagation = Propagation.NESTED)
    public void updatePartialData(Long userId) {
        // 可以独立回滚
    }

    /**
     * NOT_SUPPORTED: 无事务执行,挂起现有事务(如果存在)
     */
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void sendNotification(Notification notification) {
        // 非事务操作
    }

    /**
     * NEVER: 无事务执行,如果存在事务则抛出异常
     */
    @Transactional(propagation = Propagation.NEVER)
    public void logAccess(AccessLog log) {
        // 不能在事务中调用
    }

    /**
     * MANDATORY: 必须在现有事务中执行
     */
    @Transactional(propagation = Propagation.MANDATORY)
    public void validateTransaction() {
        // 需要活动的事务
    }
}
```

### 事务回滚策略

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class TransactionalService {

    /**
     * 对特定异常回滚
     */
    @Transactional(rollbackFor = {BusinessException.class, SystemException.class})
    public void executeWithSpecificRollback() {
        // 仅对指定的异常回滚
    }

    /**
     * 对特定异常不回滚
     */
    @Transactional(noRollbackFor = {ValidationException.class})
    public void executeWithNoRollback() {
        // ValidationException 不会回滚
    }

    /**
     * 只读事务
     */
    @Transactional(readOnly = true)
    public List<UserDO> queryUsers() {
        // 针对读操作优化
        return userDAO.selectAll();
    }

    /**
     * 设置事务超时
     */
    @Transactional(timeout = 30)  // 30 秒
    public void longRunningOperation() {
        // 30 秒后超时
    }

    /**
     * 指定隔离级别
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    public void readCommittedOperation() {
        // 防止脏读
    }
}
```

## 异常处理

### 自定义异常

```java
/**
 * 业务异常,用于预期的业务错误
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
 * 系统异常,用于意外的系统错误
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
 * 验证异常
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

### 全局异常处理器

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    /**
     * 处理业务异常
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
     * 处理验证异常
     */
    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(ValidationException ex) {
        log.warn("Validation exception: {}", ex.getErrors());

        ErrorResponse error = ErrorResponse.builder()
            .errorCode("VALIDATION_ERROR")
            .errorMessage("验证失败")
            .details(ex.getErrors())
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.badRequest().body(error);
    }

    /**
     * 处理系统异常
     */
    @ExceptionHandler(SystemException.class)
    public ResponseEntity<ErrorResponse> handleSystemException(SystemException ex) {
        log.error("System exception: {}", ex.getErrorMessage(), ex);

        ErrorResponse error = ErrorResponse.builder()
            .errorCode(ex.getErrorCode())
            .errorMessage("发生内部系统错误")
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }

    /**
     * 处理所有其他异常
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleException(Exception ex) {
        log.error("Unexpected exception: {}", ex.getMessage(), ex);

        ErrorResponse error = ErrorResponse.builder()
            .errorCode("INTERNAL_SERVER_ERROR")
            .errorMessage("发生意外错误")
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
```

## 测试策略

### 使用 JUnit 5 和 Mockito 的单元测试

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserDAO userDAO;

    @InjectMocks
    private UserService userService;

    @Test
    @DisplayName("当用户存在时应返回用户")
    void getUserById_WhenUserExists_ReturnsUser() {
        // Arrange(准备)
        Long userId = 1L;
        UserDO expectedUser = UserDO.builder()
            .id(userId)
            .username("testuser")
            .email("test@example.com")
            .build();
        when(userDAO.getUserById(userId)).thenReturn(expectedUser);

        // Act(执行)
        UserDO result = userService.getUserById(userId);

        // Assert(断言)
        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo(userId);
        assertThat(result.getUsername()).isEqualTo("testuser");
        verify(userDAO, times(1)).getUserById(userId);
    }

    @Test
    @DisplayName("当用户不存在时应抛出异常")
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
    @DisplayName("应成功创建用户")
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

### 使用 Spring Boot Test 的集成测试

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
    @DisplayName("应成功查询用户")
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
    @DisplayName("对于无效请求应返回验证错误")
    void createUser_WithInvalidData_ReturnsValidationError() throws Exception {
        // Arrange
        UserRequest request = UserRequest.builder()
            .username("")  // 无效:空用户名
            .build();

        // Act & Assert
        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
}
```

## 最佳实践

### 代码质量

✅ **应该做:**
- 使用 Lombok 注解减少样板代码
- 严格遵循 Java 命名约定
- 编写具有清晰名称的自文档化代码
- 为所有公共 API 添加 JavaDoc
- 使用 Optional 避免 NPE
- 保持方法简短和专注
- 应用 SOLID 原则

❌ **不应该做:**
- 创建职责过多的上帝类
- 使用模糊的名称如 `data1`、`temp`
- 重复代码(DRY 原则)
- 忽略 null 检查
- 编写超过 50 行的方法
- 跳过文档

### 性能优化

✅ **应该做:**
- 对大数据集使用分页
- 实现缓存(Redis、MyBatis L2)
- 对批量数据使用批量操作
- 使用适当的索引优化 SQL 查询
- 监控慢查询
- 使用连接池
- 对长时间任务启用异步处理

❌ **不应该做:**
- 将整个数据库加载到内存
- N+1 查询问题
- 忽略数据库索引
- 长时间任务的同步处理
- 忽略连接池配置

### 安全最佳实践

✅ **应该做:**
- 验证所有输入(JSR-303)
- 使用参数化查询
- 清理用户输入
- 加密敏感数据
- 实现认证/授权
- 在生产环境中使用 HTTPS
- 记录安全事件

❌ **不应该做:**
- SQL 的字符串拼接
- 信任客户端验证
- 在日志中暴露敏感数据
- 硬编码凭据
- 忽略 XSS/CSRF 防护
- 以明文存储密码

### 依赖管理

✅ **应该做:**
- 首先检查现有依赖
- 重用项目库
- 保持依赖最新
- 记录依赖决策
- 使用稳定版本

❌ **不应该做:**
- 在不检查的情况下添加依赖
- 重复功能
- 在生产环境使用 beta 版本
- 忽略安全漏洞
- 过度设计解决方案

记住:**优先考虑代码质量、可维护性和企业级可靠性。**
