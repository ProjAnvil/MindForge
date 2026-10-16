### 4. 分片策略

#### 基于哈希的分片
```python
# 简单的模分片
def get_shard(user_id, num_shards=8):
    return user_id % num_shards

# 示例: user_id = 12345, num_shards = 8
shard_id = 12345 % 8 = 1
table_name = f"users_{shard_id}"  # users_1

优点:
✅ 均匀分布
✅ 实现简单

缺点:
❌ 难以重新分片（添加/删除分片）
❌ 无法跨所有数据进行范围查询
❌ 分片数量更改时必须重新分配数据
```

#### 基于范围的分片
```python
# 按 ID 范围分片
def get_shard(user_id):
    if user_id < 1000000:
        return 0
    elif user_id < 2000000:
        return 1
    elif user_id < 3000000:
        return 2
    # ...

优点:
✅ 易于添加新分片（下一个范围）
✅ 分片内的范围查询

缺点:
❌ 分布不均（热分片）
❌ 新数据获得更多流量（最后一个分片是热点）
```

#### 一致性哈希
```python
# 用于分布式缓存（Redis、Memcached）
import hashlib

def consistent_hash(key, num_shards=8, num_virtual_nodes=150):
    # 使用虚拟节点创建环
    ring = []
    for shard_id in range(num_shards):
        for v in range(num_virtual_nodes):
            hash_value = int(hashlib.md5(f"{shard_id}:{v}".encode()).hexdigest(), 16)
            ring.append((hash_value, shard_id))
    ring.sort()

    # 为键找到分片
    key_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)
    for hash_value, shard_id in ring:
        if key_hash <= hash_value:
            return shard_id
    return ring[0][1]

优点:
✅ 添加/删除分片时数据移动最少
✅ 使用虚拟节点均匀分布

缺点:
❌ 实现更复杂
❌ 无范围查询
```

#### 地理分片
```python
def get_shard(user_id, region):
    return {
        'us-east': 0,
        'us-west': 1,
        'eu-west': 2,
        'ap-southeast': 3,
    }.get(region)

优点:
✅ 数据本地性（低延迟）
✅ 符合数据驻留法律
✅ 故障隔离

缺点:
❌ 按地区分布不均
❌ 跨地区查询成本高
```

#### 分片的挑战
```
1. 跨分片查询
   问题: 查询需要来自多个分片的数据
   解决方案:
   - 反规范化数据以共同定位相关数据
   - 使用应用层 join（scatter-gather）
   - 为常见 join 物化视图
   - 使用搜索引擎（Elasticsearch）进行跨分片搜索

2. 分布式事务
   问题: 事务跨多个分片
   解决方案:
   - 避免分布式事务（重新设计为单分片）
   - 使用最终一致性
   - 实现 SAGA 模式
   - 仅在必要时使用 2PC（慢，阻塞）

3. 自增 ID
   问题: 每个分片独立生成 ID（冲突）
   解决方案:
   - UUID（全局唯一，但非顺序）
   - Snowflake ID（Twitter 的解决方案: 时间戳 + 机器 ID + 序列）
   - 带偏移的数据库序列（分片 0: 0,8,16...，分片 1: 1,9,17...）

4. JOIN
   问题: 跨分片 JOIN 成本高
   解决方案:
   - 反规范化数据
   - 使用应用层 join
   - 设计 schema 以避免跨分片 join
   - 将相关数据保持在同一分片（共同定位）
```
