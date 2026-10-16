### 5. 查询优化流程

#### 步骤 1: 识别慢查询
```sql
-- 启用慢查询日志（MySQL）
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- 记录 > 1 秒的查询
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- 查找慢查询（PostgreSQL）
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### 步骤 2: 使用 EXPLAIN 分析
```sql
EXPLAIN SELECT u.username, COUNT(o.order_id) as order_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.status = 1
GROUP BY u.user_id
ORDER BY order_count DESC
LIMIT 10;

要查找的关键点:
1. type:
   - ALL = 全表扫描（不好）
   - index = 索引扫描（可以）
   - range = 范围扫描（好）
   - ref = 非唯一索引查找（好）
   - eq_ref = 唯一索引查找（极好）
   - const = 常量查找（极好）

2. rows:
   - 高数字 = 扫描许多行（优化）

3. Extra:
   - "Using filesort" = 昂贵的排序操作（为 ORDER BY 添加索引）
   - "Using temporary" = 创建临时表（优化 GROUP BY）
   - "Using where" = 读取行后应用过滤（可以）
   - "Using index" = 覆盖索引（极好）
   - "Using index condition" = 索引下推（好）
```

#### 步骤 3: 优化
```sql
-- 之前: 全表扫描
EXPLAIN SELECT * FROM orders WHERE status = 1 ORDER BY created_at DESC LIMIT 10;
-- type: ALL, rows: 1,000,000

-- 之后: 添加索引
CREATE INDEX idx_status_created ON orders(status, created_at DESC);
-- type: ref, rows: 10

-- 之前: 文件排序
EXPLAIN SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at DESC;
-- Extra: Using filesort

-- 之后: 在索引中包含 ORDER BY 列
CREATE INDEX idx_user_created ON orders(user_id, created_at DESC);
-- Extra: Using index

-- 之前: 相关子查询（为每行执行）
SELECT u.username,
       (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id) as order_count
FROM users u;

-- 之后: 使用 JOIN
SELECT u.username, COUNT(o.order_id) as order_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id;
```
