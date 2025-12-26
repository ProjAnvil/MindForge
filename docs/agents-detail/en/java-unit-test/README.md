# Java Unit Test Agent - Detailed Guide

This document contains comprehensive examples, templates, and best practices for the Java Unit Test Agent.

## Code Generation Template

### Standard Test Class Structure

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
 * Unit tests for {@link ClassName}.
 *
 * <p>Test coverage includes:
 * <ul>
 *   <li>Normal operation scenarios</li>
 *   <li>Edge cases and boundary conditions</li>
 *   <li>Exception handling</li>
 *   <li>Null safety</li>
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
        // Initialize common test data
        testData = new TestDataType(/* constructor args */);
    }

    // ========== Happy Path Tests ==========

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

    // ========== Edge Case Tests ==========

    @Test
    public void givenEmptyInput_whenMethodName_thenReturnsEmptyResult() {
        // Test implementation
    }

    // ========== Exception Tests ==========

    @Test(expected = IllegalArgumentException.class)
    public void givenNullInput_whenMethodName_thenThrowsIllegalArgumentException() {
        // When
        classUnderTest.methodName(null);

        // Then - exception expected
    }
}
```

## Mockito Best Practices

### When to Mock
✅ **DO Mock:**
- External dependencies (databases, APIs, file systems)
- Complex objects that are hard to set up
- Objects with non-deterministic behavior (time, random)
- Expensive operations

❌ **DON'T Mock:**
- Value objects (immutable data holders)
- Simple POJOs
- The class under test itself
- Java standard library classes (unless external interaction)

### Mock Setup Patterns

```java
// Simple return value
when(mock.method(arg)).thenReturn(value);

// Multiple calls
when(mock.method(arg))
    .thenReturn(value1)
    .thenReturn(value2);

// Argument matchers
when(mock.method(any(Type.class))).thenReturn(value);
when(mock.method(anyString())).thenReturn(value);
when(mock.method(eq(specificValue))).thenReturn(value);

// Throw exception
when(mock.method(arg)).thenThrow(new RuntimeException("message"));

// Void methods
doNothing().when(mock).voidMethod(arg);
doThrow(new RuntimeException()).when(mock).voidMethod(arg);
```

### Verification Patterns

```java
// Basic verification
verify(mock).method(arg);

// Number of invocations
verify(mock, times(2)).method(arg);
verify(mock, atLeastOnce()).method(arg);
verify(mock, never()).method(arg);

// Argument captor
ArgumentCaptor<Type> captor = ArgumentCaptor.forClass(Type.class);
verify(mock).method(captor.capture());
Type capturedArg = captor.getValue();
assertThat(capturedArg).isEqualTo(expected);
```

## AssertJ Assertion Patterns

```java
// Basic assertions
assertThat(actual).isEqualTo(expected);
assertThat(actual).isNotNull();
assertThat(actual).isInstanceOf(Type.class);

// String assertions
assertThat(string)
    .isNotEmpty()
    .startsWith("prefix")
    .contains("substring")
    .endsWith("suffix");

// Numeric assertions
assertThat(number)
    .isPositive()
    .isGreaterThan(5)
    .isBetween(1, 10);

// Collection assertions
assertThat(list)
    .isNotEmpty()
    .hasSize(3)
    .contains(element)
    .containsExactly(e1, e2, e3)
    .extracting(Type::getProperty)
    .containsOnly(value1, value2);

// Exception assertions
assertThatThrownBy(() -> methodCall())
    .isInstanceOf(ExceptionType.class)
    .hasMessageContaining("expected message");

// Optional assertions
assertThat(optional)
    .isPresent()
    .hasValue(expectedValue);

assertThat(optional).isEmpty();
```

## Test Scenarios Checklist

For each public method, consider:

### Input Validation
- [ ] Valid inputs (happy path)
- [ ] Null inputs
- [ ] Empty strings/collections
- [ ] Invalid formats
- [ ] Out of range values

### Business Logic
- [ ] Correct calculation/transformation
- [ ] State changes
- [ ] Return values
- [ ] Side effects

### Dependencies
- [ ] Dependency methods are called correctly
- [ ] Correct parameters passed
- [ ] Correct number of invocations
- [ ] Error handling from dependencies

### Edge Cases
- [ ] Boundary values (0, 1, max)
- [ ] Empty collections
- [ ] Single element collections
- [ ] Large datasets (performance)
- [ ] Concurrent access (if applicable)

### Exception Handling
- [ ] Expected exceptions are thrown
- [ ] Exception messages are correct
- [ ] Cleanup happens after exceptions
- [ ] No silent failures

## Additional Guidelines

1. **Keep tests focused**: One assertion concept per test
2. **Use meaningful test data**: Avoid magic numbers/strings
3. **Avoid test interdependence**: Tests should run in any order
4. **Keep tests readable**: Clear variable names, structured code
5. **Don't test implementation details**: Test behavior, not internals
6. **Maintain test code quality**: Apply same standards as production code

Remember: **Quality over quantity**. Better to have fewer, well-written tests than many fragile tests.
