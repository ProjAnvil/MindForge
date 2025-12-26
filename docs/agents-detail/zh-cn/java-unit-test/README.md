# Java 单元测试代理 - 详细指南

本文档包含 Java 单元测试代理的综合示例、模板和最佳实践。

## 代码生成模板

### 标准测试类结构

```java
package com.example.service;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;

/**
 * {@link ClassName} 的单元测试。
 *
 * <p>测试覆盖包括：
 * <ul>
 *   <li>正常操作场景</li>
 *   <li>边界情况和边界条件</li>
 *   <li>异常处理</li>
 *   <li>空值安全</li>
 * </ul>
 */
@RunWith(MockitoJUnitRunner.class)
public class ClassNameTest {

    @Mock
    private DependencyOne dependencyOne;

    @Mock
    private DependencyTwo dependencyTwo;

    @InjectMocks
    private ClassName classUnderTest;

    private TestDataType testData;

    @Before
    public void setUp() {
        // 初始化通用测试数据
        testData = new TestDataType(/* constructor args */);
    }

    // ========== 正常路径测试 ==========

    @Test
    public void givenValidInput_whenMethodName_thenExpectedBehavior() {
        // Given
        when(dependencyOne.method(any())).thenReturn(expectedValue);

        // When
        ResultType result = classUnderTest.methodName(testData);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getProperty()).isEqualTo(expectedValue);
        verify(dependencyOne).method(testData);
    }

    // ========== 边界情况测试 ==========

    @Test
    public void givenEmptyInput_whenMethodName_thenReturnsEmptyResult() {
        // 测试实现
    }

    // ========== 异常测试 ==========

    @Test(expected = IllegalArgumentException.class)
    public void givenNullInput_whenMethodName_thenThrowsIllegalArgumentException() {
        // When
        classUnderTest.methodName(null);

        // Then - 期望异常
    }
}
```

## Mockito 最佳实践

### 何时使用 Mock
✅ **应该 Mock：**
- 外部依赖（数据库、API、文件系统）
- 难以设置的复杂对象
- 具有非确定性行为的对象（时间、随机数）
- 昂贵的操作

❌ **不应该 Mock：**
- 值对象（不可变数据持有者）
- 简单的 POJO
- 被测试的类本身
- Java 标准库类（除非外部交互）

### Mock 设置模式

```java
// 简单返回值
when(mock.method(arg)).thenReturn(value);

// 多次调用
when(mock.method(arg))
    .thenReturn(value1)
    .thenReturn(value2);

// 参数匹配器
when(mock.method(any(Type.class))).thenReturn(value);
when(mock.method(anyString())).thenReturn(value);
when(mock.method(eq(specificValue))).thenReturn(value);

// 抛出异常
when(mock.method(arg)).thenThrow(new RuntimeException("message"));

// Void 方法
doNothing().when(mock).voidMethod(arg);
doThrow(new RuntimeException()).when(mock).voidMethod(arg);
```

### 验证模式

```java
// 基本验证
verify(mock).method(arg);

// 调用次数
verify(mock, times(2)).method(arg);
verify(mock, atLeastOnce()).method(arg);
verify(mock, never()).method(arg);

// 参数捕获器
ArgumentCaptor<Type> captor = ArgumentCaptor.forClass(Type.class);
verify(mock).method(captor.capture());
Type capturedArg = captor.getValue();
assertThat(capturedArg).isEqualTo(expected);
```

## AssertJ 断言模式

```java
// 基本断言
assertThat(actual).isEqualTo(expected);
assertThat(actual).isNotNull();
assertThat(actual).isInstanceOf(Type.class);

// 字符串断言
assertThat(string)
    .isNotEmpty()
    .startsWith("prefix")
    .contains("substring")
    .endsWith("suffix");

// 数值断言
assertThat(number)
    .isPositive()
    .isGreaterThan(5)
    .isBetween(1, 10);

// 集合断言
assertThat(list)
    .isNotEmpty()
    .hasSize(3)
    .contains(element)
    .containsExactly(e1, e2, e3)
    .extracting(Type::getProperty)
    .containsOnly(value1, value2);

// 异常断言
assertThatThrownBy(() -> methodCall())
    .isInstanceOf(ExceptionType.class)
    .hasMessageContaining("expected message");

// Optional 断言
assertThat(optional)
    .isPresent()
    .hasValue(expectedValue);

assertThat(optional).isEmpty();
```

## 测试场景检查清单

对于每个公共方法，考虑：

### 输入验证
- [ ] 有效输入（正常路径）
- [ ] 空输入
- [ ] 空字符串/集合
- [ ] 无效格式
- [ ] 超出范围的值

### 业务逻辑
- [ ] 正确的计算/转换
- [ ] 状态变化
- [ ] 返回值
- [ ] 副作用

### 依赖项
- [ ] 依赖方法被正确调用
- [ ] 传递正确的参数
- [ ] 正确的调用次数
- [ ] 来自依赖项的错误处理

### 边界情况
- [ ] 边界值（0、1、最大值）
- [ ] 空集合
- [ ] 单元素集合
- [ ] 大数据集（性能）
- [ ] 并发访问（如果适用）

### 异常处理
- [ ] 抛出预期的异常
- [ ] 异常消息正确
- [ ] 异常后发生清理
- [ ] 没有静默失败

## 附加指南

1. **保持测试专注**：每个测试一个断言概念
2. **使用有意义的测试数据**：避免魔法数字/字符串
3. **避免测试相互依赖**：测试应该以任何顺序运行
4. **保持测试可读性**：清晰的变量名、结构化的代码
5. **不要测试实现细节**：测试行为，而不是内部实现
6. **维护测试代码质量**：应用与生产代码相同的标准

记住：**质量优于数量**。拥有更少但编写良好的测试比拥有许多脆弱的测试更好。
