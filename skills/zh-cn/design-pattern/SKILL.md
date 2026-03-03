---
name: design-pattern
description: 精通软件设计模式，包括 GoF 模式、架构模式和现代设计原则。应用适当的模式提高代码的可维护性、可扩展性和可伸缩性。
---

# 设计模式精通

## 指令

你是软件设计模式方面的专家，具有深厚的知识：
- 四人帮（GoF）设计模式
- 架构模式（MVC、MVVM、Clean Architecture、Hexagonal Architecture）
- 现代模式（依赖注入、仓储模式、CQRS、事件溯源）
- 反模式和代码坏味道
- SOLID 原则和设计最佳实践

## 此技能的功能

该技能提供有关软件设计模式的全面知识和实践指导。它帮助你：
- 识别特定问题的适当模式
- 在各种编程语言中正确实现模式
- 识别代码坏味道和反模式
- 应用 SOLID 原则
- 平衡灵活性与简单性
- 重构代码以提高可维护性

## 何时使用此技能

在以下情况下使用此技能：
- 设计新的软件组件或系统
- 审查代码设计质量
- 重构现有代码
- 解决复杂的设计问题
- 解释设计决策
- 教授软件工程概念
- 识别代码坏味道并提出改进建议

## 核心能力

### 1. 创建型模式

**单例模式（Singleton）**
- 确保类只有一个实例
- 提供全局访问点
- 用于配置管理器、连接池、日志记录

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

**工厂方法模式（Factory Method）**
- 定义创建对象的接口
- 让子类决定实例化哪个类
- 当确切类型直到运行时才知道时使用

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

**建造者模式（Builder）**
- 逐步构建复杂对象
- 将构造与表示分离
- 用于具有许多可选参数的对象

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

**原型模式（Prototype）**
- 克隆现有对象而不耦合到它们的类
- 当对象创建成本高时使用

**抽象工厂模式（Abstract Factory）**
- 提供创建相关对象族的接口
- 当系统应独立于对象创建方式时使用

### 2. 结构型模式

**适配器模式（Adapter）**
- 将类的接口转换为另一个接口
- 允许不兼容的接口一起工作

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

**装饰器模式（Decorator）**
- 动态地为对象附加额外的职责
- 提供灵活的子类化替代方案

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

**外观模式（Facade）**
- 为一组接口提供统一接口
- 简化复杂子系统

**代理模式（Proxy）**
- 为另一个对象提供占位符
- 控制访问、延迟初始化、日志记录

**组合模式（Composite）**
- 将对象组合成树形结构
- 统一对待单个对象和组合

**桥接模式（Bridge）**
- 将抽象与实现解耦
- 两者可以独立变化

**享元模式（Flyweight）**
- 在多个对象之间共享公共状态
- 减少内存占用

### 3. 行为型模式

**策略模式（Strategy）**
- 定义算法族
- 使它们可互换
- 当需要算法的不同变体时使用

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

**观察者模式（Observer）**
- 定义一对多依赖关系
- 当一个对象改变时，通知依赖者
- 用于事件处理系统

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

**命令模式（Command）**
- 将请求封装为对象
- 使用不同的请求参数化客户端
- 支持撤销/重做操作

**状态模式（State）**
- 允许对象在内部状态改变时改变行为
- 对象似乎改变了它的类

**模板方法模式（Template Method）**
- 在基类中定义算法骨架
- 让子类覆盖特定步骤

**迭代器模式（Iterator）**
- 顺序访问聚合元素
- 不暴露底层表示

**中介者模式（Mediator）**
- 定义封装对象交互方式的对象
- 减少组件之间的耦合

**备忘录模式（Memento）**
- 捕获和外部化对象的内部状态
- 允许以后恢复对象

**责任链模式（Chain of Responsibility）**
- 沿处理程序链传递请求
- 每个处理程序决定处理或传递

**访问者模式（Visitor）**
- 将算法与对象结构分离
- 在不修改对象的情况下添加新操作

### 4. 架构模式

**模型-视图-控制器（MVC）**
- 分离关注点：数据（Model）、展示（View）、逻辑（Controller）
- 用于 Web 应用、桌面应用

**模型-视图-视图模型（MVVM）**
- 将 UI 与业务逻辑分离
- 使用 View 和 ViewModel 之间的数据绑定
- 在 WPF、Angular、Vue.js 中流行

**整洁架构（Clean Architecture）**
- 依赖规则：依赖指向内部
- 实体 → 用例 → 接口适配器 → 框架
- 独立于框架、UI、数据库

**六边形架构（Ports and Adapters）**
- 应用核心与外部关注点隔离
- 端口定义接口，适配器实现它们
- 易于测试、交换实现

**仓储模式（Repository）**
- 在领域和数据映射层之间调解
- 为访问领域对象提供类似集合的接口

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

**CQRS（命令查询职责分离）**
- 分离读写操作
- 更新和查询使用不同的模型
- 提高可扩展性和性能

**事件溯源（Event Sourcing）**
- 将状态存储为事件序列
- 通过重放事件重建当前状态
- 提供审计跟踪、时间旅行

### 5. 现代模式

**依赖注入（Dependency Injection）**
- 控制反转原则
- 从外部提供依赖项
- 提高可测试性、灵活性

```java
public class UserService {
    private final UserRepository repository;
    
    // 构造函数注入
    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

**服务定位器（Service Locator）**
- 用于获取服务的中央注册表
- 依赖注入的替代方案

**空对象模式（Null Object）**
- 提供默认对象而不是 null
- 消除 null 检查

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

**对象池模式（Object Pool）**
- 重用创建成本高的对象
- 管理可重用对象池

**断路器模式（Circuit Breaker）**
- 防止级联故障
- 当服务不可用时快速失败

## SOLID 原则

**单一职责原则（SRP）**
- 一个类应该只有一个改变的理由
- 每个类做好一件事

**开闭原则（OCP）**
- 对扩展开放，对修改关闭
- 使用抽象和多态

**里氏替换原则（LSP）**
- 子类型必须可替换其基类型
- 派生类不得破坏基类契约

**接口隔离原则（ISP）**
- 客户端不应依赖他们不使用的接口
- 创建特定接口而不是通用接口

**依赖倒置原则（DIP）**
- 依赖于抽象，而不是具体实现
- 高层模块不应依赖于低层模块

## 需要避免的反模式

**上帝对象（God Object）**
- 类知道太多或做太多
- 违反 SRP

**意大利面代码（Spaghetti Code）**
- 纠缠的控制流
- 难以理解和维护

**熔岩流（Lava Flow）**
- 永远不会删除的死代码
- 害怕破坏某些东西

**金锤子（Golden Hammer）**
- 过度使用一种模式
- "当你有锤子时，一切看起来都像钉子"

**过早优化（Premature Optimization）**
- 在识别瓶颈之前进行优化
- 使代码不必要地复杂

**货物崇拜编程（Cargo Cult Programming）**
- 在不理解原因的情况下使用模式
- 在没有理解的情况下复制代码

## 模式选择指南

**何时使用创建型模式：**
- 对象创建复杂
- 需要控制实例创建
- 想要将创建与使用解耦

**何时使用结构型模式：**
- 需要组合对象
- 想要适配接口
- 需要简化复杂系统

**何时使用行为型模式：**
- 需要定义对象之间的通信
- 想要封装算法
- 需要对象行为的灵活性

## 示例

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

## 最佳实践

- **首先理解问题** - 不要在不适合的地方强制使用模式。模式是解决反复出现问题的方案。
- **保持简单** - 从简单开始，根据需要添加模式。不要过度工程化。
- **清晰命名** - 适当时在类/方法名称中使用模式名称。使代码自文档化。
- **深思熟虑地组合模式** - 模式经常一起工作（工厂 + 单例、策略 + 模板方法等）
- **考虑权衡** - 模式增加复杂性。平衡灵活性与简单性。
- **测试驱动开发** - 先写测试。模式自然地从重构中出现。
- **重构到模式** - 不要预先设计模式。让它们随着代码的发展而出现。

## 代码审查清单

审查代码中模式使用时：

- [ ] 该模式是否适合问题？
- [ ] 实现是否正确？
- [ ] 它是否提高了代码质量？
- [ ] 它是否过度工程化？
- [ ] 是否遵循 SOLID 原则？
- [ ] 代码是否可测试？
- [ ] 文档是否完善？
- [ ] 是否有更简单的替代方案？

## 模式参考快速指南

| 问题 | 模式 | 何时使用 |
|------|------|----------|
| 需要单一实例 | 单例 | 全局状态、资源管理 |
| 复杂对象创建 | 建造者 | 许多可选参数 |
| 相关对象族 | 抽象工厂 | 需要一致的对象族 |
| 克隆现有对象 | 原型 | 对象创建成本高 |
| 接口不匹配 | 适配器 | 集成遗留代码 |
| 添加职责 | 装饰器 | 需要灵活的扩展 |
| 简化复杂系统 | 外观 | 需要简化接口 |
| 控制访问 | 代理 | 延迟加载、访问控制 |
| 可互换算法 | 策略 | 多个算法变体 |
| 通知依赖者 | 观察者 | 事件处理、发布-订阅 |
| 封装请求 | 命令 | 撤销/重做、排队操作 |
| 状态依赖行为 | 状态 | 复杂状态转换 |

## 备注

设计模式是软件设计中常见问题的经过验证的解决方案。使用它们来：
- 编写可维护、可扩展的代码
- 清晰地传达设计意图
- 利用软件社区的集体智慧
- 避免重新发明轮子

记住：**模式是工具，不是规则。** 使用判断力在特定上下文中适当地应用它们。最好的代码通常是有效解决问题的最简单的代码。
