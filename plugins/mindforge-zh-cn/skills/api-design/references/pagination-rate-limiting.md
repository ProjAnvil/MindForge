### 7. 分页模式

#### 基于偏移的分页（简单）
```
GET /api/v1/posts?page=2&size=20

优点: 简单，适用于 SQL LIMIT/OFFSET
缺点: 大偏移量性能下降，并发写入时不一致

SQL: SELECT * FROM posts ORDER BY id LIMIT 20 OFFSET 20;
```

#### 基于游标的分页（推荐用于实时 feed）
```
GET /api/v1/posts?cursor=post_123&limit=20

优点: 一致，高效，适用于实时数据
缺点: 无法跳转到任意页面

响应:
{
  "data": [...],
  "cursor": {
    "next": "post_143",
    "previous": "post_103"
  },
  "has_more": true
}

SQL: SELECT * FROM posts WHERE id > 'post_123' ORDER BY id LIMIT 20;
```

#### Keyset 分页（最佳性能）
```
GET /api/v1/posts?after_id=123&after_created_at=2025-01-01T00:00:00Z&limit=20

优点: 出色的性能，一致
缺点: 需要索引列，更复杂

SQL:
SELECT * FROM posts
WHERE (created_at, id) > ('2025-01-01', 123)
ORDER BY created_at, id
LIMIT 20;
```

### 8. 速率限制策略

#### 令牌桶算法
```
桶容量: 100 tokens
补充速率: 10 tokens/秒
请求成本: 每个请求 1 token

Headers:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1735689600

超限时:
HTTP 429 Too Many Requests
Retry-After: 60
```

#### 实现
```python
from redis import Redis
import time

redis = Redis()

def check_rate_limit(user_id, limit=100, window=60):
    key = f"rate_limit:{user_id}"
    current = time.time()

    # 移除旧条目
    redis.zremrangebyscore(key, 0, current - window)

    # 统计当前请求数
    count = redis.zcard(key)

    if count >= limit:
        return False, 0

    # 添加当前请求
    redis.zadd(key, {str(current): current})
    redis.expire(key, window)

    remaining = limit - count - 1
    return True, remaining
```
