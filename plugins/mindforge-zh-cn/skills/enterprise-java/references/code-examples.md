# 企业级 Java 技能 - 代码示例和模板

## 标准类模板

```java
package com.example.{module}.{layer};

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.{Annotation};
import org.springframework.transaction.annotation.Transactional;

/**
 * {类的目的和职责}
 *
 * <p>主要特性:
 * <ul>
 *   <li>特性 1</li>
 *   <li>特性 2</li>
 * </ul>
 *
 * @author Enterprise Java Developer
 * @since {Version}
 */
@Slf4j
@RequiredArgsConstructor
@{Annotation}
public class {ClassName} {

    private final Dependency dependency;

    /**
     * {方法目的}
     *
     * @param param 参数描述
     * @return 返回值描述
     * @throws BusinessException 当业务规则被违反时
     */
    @Transactional(rollbackFor = Exception.class)
    public Result methodName(Param param) {
        log.info("Method started, param: {}", param);

        try {
            // 1. Validate input
            validateParam(param);

            // 2. Execute business logic
            Result result = executeBusinessLogic(param);

            // 3. Return result
            log.info("Method completed successfully");
            return result;

        } catch (BusinessException e) {
            log.error("Business error: {}", e.getMessage(), e);
            throw e;
        } catch (Exception e) {
            log.error("System error occurred", e);
            throw new SystemException("Unexpected error", e);
        }
    }

    private void validateParam(Param param) {
        if (param == null) {
            throw new IllegalArgumentException("Param cannot be null");
        }
        // Additional validations...
    }

    private Result executeBusinessLogic(Param param) {
        // Implementation...
        return new Result();
    }
}
```

## 分层架构模式

```
controller/    - HTTP 端点、请求/响应处理
├── dto/       - 数据传输对象
└── vo/        - 视图对象

service/       - 业务逻辑、编排
├── impl/      - 服务实现

repository/    - 数据访问层
├── entity/    - JPA 实体
└── mapper/    - MyBatis 映射器

domain/        - 领域模型（DDD）
├── model/     - 领域对象
├── service/   - 领域服务
└── event/     - 领域事件

config/        - 配置类
exception/     - 自定义异常
util/          - 工具类
constant/      - 常量和枚举
```

## 性能优化示例

### 选项 1：Join Fetch（推荐）

```java
// 之前
public List<User> getUsersWithOrders() {
    List<User> users = userRepository.findAll();
    users.forEach(user -> user.getOrders().size()); // N 次查询
    return users;
}

// 之后
public List<User> getUsersWithOrders() {
    return userRepository.findAllWithOrders(); // 1 次查询
}

// Repository
@Query("SELECT u FROM User u LEFT JOIN FETCH u.orders")
List<User> findAllWithOrders();
```

### 选项 2：Redis 缓存

```java
@Cacheable(value = "users", key = "#userId")
public User getUser(Long userId) {
    return userRepository.findById(userId)
        .orElseThrow(() -> new UserNotFoundException(userId));
}
```

## 最佳实践代码示例

### 异常处理

```java
// ❌ 差
try {
    service.process();
} catch (Exception e) {
    e.printStackTrace();
}

// ✅ 好
try {
    service.process();
} catch (BusinessException e) {
    log.warn("Business validation failed: {}", e.getMessage());
    throw e;
} catch (Exception e) {
    log.error("Unexpected error in process", e);
    throw new SystemException("Processing failed", e);
}
```

### 空值安全

```java
// ❌ 差
public String getUserName(User user) {
    return user.getName();
}

// ✅ 好
public String getUserName(User user) {
    return Optional.ofNullable(user)
        .map(User::getName)
        .orElse("Unknown");
}
```

### 资源管理

```java
// ❌ 差
InputStream is = new FileInputStream(file);
// 忘记关闭

// ✅ 好
try (InputStream is = new FileInputStream(file)) {
    // 使用流
} // 自动关闭
```

### 配置

```java
// ❌ 差
private static final String API_URL = "http://api.example.com";

// ✅ 好
@Value("${api.url}")
private String apiUrl;
```

### 日志

```java
// ❌ 差
System.out.println("User: " + user);
log.debug("Processing order: " + order.getId());

// ✅ 好
log.info("User operation started, userId: {}", user.getId());
log.debug("Processing order, orderId: {}", order.getId());
```

## 常见陷阱示例

### 事务边界

```java
// ❌ 错误：循环中的事务
public void updateUsers(List<User> users) {
    for (User user : users) {
        updateUser(user); // 每次调用都打开/关闭事务
    }
}

// ✅ 正确：单个事务
@Transactional
public void updateUsers(List<User> users) {
    for (User user : users) {
        userRepository.save(user);
    }
}
```

### 懒加载问题

```java
// ❌ LazyInitializationException
@Transactional
public User getUser(Long id) {
    return userRepository.findById(id).orElse(null);
}
// 之后：user.getOrders() 失败 - 没有会话

// ✅ 获取所需数据
@Transactional
public User getUserWithOrders(Long id) {
    return userRepository.findByIdWithOrders(id).orElse(null);
}
```

### 缓存一致性

```java
// ❌ 更新后缓存过期
@Cacheable("users")
public User getUser(Long id) { ... }

public void updateUser(User user) {
    userRepository.save(user);
    // 缓存仍有旧数据！
}

// ✅ 使缓存失效
@CacheEvict(value = "users", key = "#user.id")
public void updateUser(User user) {
    userRepository.save(user);
}
```

## 生产问题诊断示例

### 问题诊断（OutOfMemoryError）

```java
// 有问题的代码
public List<Order> exportAllOrders() {
    return orderRepository.findAll(); // 加载 100 万+ 记录
}

// 立即修复（生产环境）：增加堆大小
// -Xmx4g -Xms4g

// 正确修复（代码）：使用分页和流式处理
public void exportAllOrders(OutputStream output) {
    int pageSize = 1000;
    int page = 0;

    Page<Order> orderPage;
    do {
        orderPage = orderRepository.findAll(
            PageRequest.of(page++, pageSize)
        );

        writeToStream(orderPage.getContent(), output);

    } while (orderPage.hasNext());
}
```

### 内存监控

```java
@Scheduled(fixedRate = 60000)
public void checkMemoryUsage() {
    MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
    long used = memoryBean.getHeapMemoryUsage().getUsed();
    long max = memoryBean.getHeapMemoryUsage().getMax();

    if (used > max * 0.8) {
        log.warn("High memory usage: {}%", (used * 100 / max));
    }
}
```
