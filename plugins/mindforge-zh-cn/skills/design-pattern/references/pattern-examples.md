# 设计模式 - 代码示例和实现

## 创建型模式示例

### 单例模式（Singleton）

```java
public class DatabaseConnection {
    private static volatile DatabaseConnection instance;
    private DatabaseConnection() {}
    
    public static DatabaseConnection getInstance() {
        if (instance == null) {
            synchronized (DatabaseConnection.class) {
                if (instance == null) {
                    instance = new DatabaseConnection();
                }
            }
        }
        return instance;
    }
}
```

### 工厂方法模式（Factory Method）

```typescript
interface Product {
    operation(): string;
}

abstract class Creator {
    abstract factoryMethod(): Product;
    
    someOperation(): string {
        const product = this.factoryMethod();
        return product.operation();
    }
}
```

### 建造者模式（Builder）

```python
class User:
    def __init__(self):
        self.name = None
        self.email = None
        self.age = None
        
class UserBuilder:
    def __init__(self):
        self.user = User()
    
    def with_name(self, name):
        self.user.name = name
        return self
    
    def with_email(self, email):
        self.user.email = email
        return self
    
    def build(self):
        return self.user
```

## 结构型模式示例

### 适配器模式（Adapter）

```go
type LegacyPrinter interface {
    PrintOld(text string)
}

type ModernPrinter interface {
    Print(text string)
}

type PrinterAdapter struct {
    legacy LegacyPrinter
}

func (a *PrinterAdapter) Print(text string) {
    a.legacy.PrintOld(text)
}
```

### 装饰器模式（Decorator）

```typescript
interface Component {
    operation(): string;
}

class ConcreteComponent implements Component {
    operation(): string {
        return "ConcreteComponent";
    }
}

class Decorator implements Component {
    protected component: Component;
    
    constructor(component: Component) {
        this.component = component;
    }
    
    operation(): string {
        return this.component.operation();
    }
}

class ConcreteDecorator extends Decorator {
    operation(): string {
        return `ConcreteDecorator(${super.operation()})`;
    }
}
```

## 行为型模式示例

### 策略模式（Strategy）

```java
interface PaymentStrategy {
    void pay(int amount);
}

class CreditCardStrategy implements PaymentStrategy {
    public void pay(int amount) {
        System.out.println("使用信用卡支付 " + amount);
    }
}

class PayPalStrategy implements PaymentStrategy {
    public void pay(int amount) {
        System.out.println("使用 PayPal 支付 " + amount);
    }
}

class ShoppingCart {
    private PaymentStrategy paymentStrategy;
    
    public void setPaymentStrategy(PaymentStrategy strategy) {
        this.paymentStrategy = strategy;
    }
    
    public void checkout(int amount) {
        paymentStrategy.pay(amount);
    }
}
```

### 观察者模式（Observer）

```python
class Subject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def notify(self, event):
        for observer in self._observers:
            observer.update(event)

class Observer:
    def update(self, event):
        pass
```

## 架构模式示例

### 仓储模式（Repository）

```typescript
interface UserRepository {
    findById(id: string): Promise<User>;
    save(user: User): Promise<void>;
    delete(id: string): Promise<void>;
}

class UserRepositoryImpl implements UserRepository {
    async findById(id: string): Promise<User> {
        // 数据库访问逻辑
    }
    
    async save(user: User): Promise<void> {
        // 保存逻辑
    }
}
```

## 现代模式示例

### 依赖注入（Dependency Injection）

```java
public class UserService {
    private final UserRepository repository;
    
    // 构造函数注入
    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

### 空对象模式（Null Object）

```python
class User:
    def get_name(self):
        pass

class RealUser(User):
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name

class NullUser(User):
    def get_name(self):
        return "访客"
```

## 实际示例

### 示例 1: 重构为策略模式

**之前：**
```java
class PaymentProcessor {
    public void processPayment(String type, int amount) {
        if (type.equals("credit")) {
            // 信用卡逻辑
        } else if (type.equals("paypal")) {
            // PayPal 逻辑
        } else if (type.equals("crypto")) {
            // 加密货币逻辑
        }
    }
}
```

**之后：**
```java
interface PaymentStrategy {
    void pay(int amount);
}

class PaymentProcessor {
    private PaymentStrategy strategy;
    
    public void setStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void processPayment(int amount) {
        strategy.pay(amount);
    }
}
```

### 示例 2: 实现仓储模式

```typescript
// 领域实体
class User {
    constructor(
        public id: string,
        public name: string,
        public email: string
    ) {}
}

// 仓储接口
interface UserRepository {
    findById(id: string): Promise<User | null>;
    findAll(): Promise<User[]>;
    save(user: User): Promise<void>;
    delete(id: string): Promise<void>;
}

// PostgreSQL 实现
class PostgresUserRepository implements UserRepository {
    async findById(id: string): Promise<User | null> {
        const result = await db.query('SELECT * FROM users WHERE id = $1', [id]);
        return result.rows[0] ? new User(result.rows[0].id, result.rows[0].name, result.rows[0].email) : null;
    }
    
    async save(user: User): Promise<void> {
        await db.query(
            'INSERT INTO users (id, name, email) VALUES ($1, $2, $3) ON CONFLICT (id) DO UPDATE SET name = $2, email = $3',
            [user.id, user.name, user.email]
        );
    }
}
```


## 重构示例

### 示例 1: 重构为策略模式

**之前：**
```java
class PaymentProcessor {
    public void processPayment(String type, int amount) {
        if (type.equals("credit")) {
            // 信用卡逻辑
        } else if (type.equals("paypal")) {
            // PayPal 逻辑
        } else if (type.equals("crypto")) {
            // 加密货币逻辑
        }
    }
}
```

**之后：**
```java
interface PaymentStrategy {
    void pay(int amount);
}

class PaymentProcessor {
    private PaymentStrategy strategy;
    
    public void setStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void processPayment(int amount) {
        strategy.pay(amount);
    }
}
```

### 示例 2: 实现仓储模式

```typescript
// 领域实体
class User {
    constructor(
        public id: string,
        public name: string,
        public email: string
    ) {}
}

// 仓储接口
interface UserRepository {
    findById(id: string): Promise<User | null>;
    findAll(): Promise<User[]>;
    save(user: User): Promise<void>;
    delete(id: string): Promise<void>;
}

// PostgreSQL 实现
class PostgresUserRepository implements UserRepository {
    async findById(id: string): Promise<User | null> {
        const result = await db.query('SELECT * FROM users WHERE id = $1', [id]);
        return result.rows[0] ? new User(result.rows[0].id, result.rows[0].name, result.rows[0].email) : null;
    }
    
    async save(user: User): Promise<void> {
        await db.query(
            'INSERT INTO users (id, name, email) VALUES ($1, $2, $3) ON CONFLICT (id) DO UPDATE SET name = $2, email = $3',
            [user.id, user.name, user.email]
        );
    }
}
```