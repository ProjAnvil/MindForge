### 6. 数据迁移策略

#### 模式迁移（大表零停机 DDL）

先判断变更是否真的阻塞——简单的加列**不要**动用双写：

- **PostgreSQL 11+ / MySQL 8.0.12+**：带常量默认值的 `ADD COLUMN` 是秒级元数据操作——不重建表，不需要双写
- **仍然阻塞的场景**：修改列类型、加 volatile 默认值（`now()`、`random()`）、旧版本上加无默认值的 `NOT NULL`、热表上的 DROP/RENAME
- **MySQL < 8.0.12 或会锁表的 DDL**：使用 pt-online-schema-change 或 gh-ost
- 始终设置 `lock_timeout`（PG）/ `--max-load`（gh-ost），让被阻塞的 DDL 快速失败而不是堆积连接
- 大表建索引：`CREATE INDEX CONCURRENTLY`（PG）/ `ALGORITHM=INPLACE, LOCK=NONE`（MySQL）

**迁移 Runbook——大表 DDL 必须遵循的结构：**

1. **前置检查**——数据库版本、表大小、主从延迟；确认 DDL 是即时操作，否则选择在线工具
2. **备份验证**——备份存在且近期做过恢复演练（没验证过的备份不算备份）
3. **护栏**——设置 lock_timeout / statement_timeout；对连接堆积和主从延迟设告警
4. **灰度发布**——预发 → 最小生产副本 → 主库
5. **回滚**——提前写好精确的反向 DDL；明确的中止判据

#### 在线迁移（零停机时间）
```
阶段 1: 准备
- 设计目标 schema
- 编写迁移脚本
- 设置双写逻辑
- 在 staging 环境测试

阶段 2: 回填历史数据
- 将现有数据从旧 DB 复制到新 DB
- 验证数据完整性
- 监控延迟

阶段 3: 双写
应用程序同时写入旧 DB 和新 DB:

def create_user(data):
    # 写入旧 DB
    old_user = old_db.users.create(data)

    # 写入新 DB
    try:
        new_user = new_db.users.create(transform(data))
    except Exception as e:
        log_error(e)
        # 继续 - 如果新 DB 写入失败不要失败

    return old_user

阶段 4: 同步与验证
- 持续同步从旧到新的更改
- 定期比较数据
- 修复不一致

阶段 5: 切换
- 将读取切换到新 DB（逐步推出）
- 监控错误率和性能
- 停止写入旧 DB
- 最终同步
- 准备好回滚计划

阶段 6: 清理
- 删除双写逻辑
- 停用旧 DB（在保留期后）
```

#### CDC（变更数据捕获）
```
工具: Debezium、Maxwell、Canal、AWS DMS

工作原理:
1. CDC 工具读取数据库事务日志（MySQL 中的 binlog）
2. 将更改流式传输到 Kafka 或其他消息队列
3. 消费者将更改应用到目标数据库

优点:
✅ 低延迟（近实时）
✅ 应用程序无需代码更改
✅ 可以从任何时间点重放

缺点:
❌ 需要访问事务日志
❌ 额外的基础设施（Kafka 等）
❌ Schema 更改需要仔细处理
```

### 7. 备份与恢复

#### 备份策略（3-2-1 规则）
```
3 个数据副本:
  - 生产数据库
  - 本地备份
  - 远程备份

2 种不同的介质:
  - 磁盘
  - 磁带或云存储

1 个异地副本:
  - 不同的数据中心或云区域
```

#### 备份计划
```
全量备份:
  - 频率: 每周（周日凌晨 2 点）
  - 保留: 4 周
  - 方法: mysqldump 或 xtrabackup

增量备份:
  - 频率: 每 6 小时
  - 保留: 7 天
  - 方法: 二进制日志备份

事务日志备份:
  - 频率: 每 15 分钟
  - 保留: 7 天
  - 支持时间点恢复
```

#### 时间点恢复 (PITR)
```bash
# 恢复全量备份
mysql < full_backup_sunday.sql

# 应用增量备份
mysql < incremental_monday.sql
mysql < incremental_tuesday.sql

# 应用事务日志到特定时间
mysqlbinlog --stop-datetime="2025-01-15 14:30:00" \
  binlog.000001 binlog.000002 | mysql

# 结果: 数据库恢复到 2025-01-15 14:30:00
```

#### 灾难恢复
```
RTO（恢复时间目标）:
  可以停机多长时间？
  - 4 小时 RTO = 需要热备或快速恢复

RPO（恢复点目标）:
  可接受多少数据丢失？
  - 1 小时 RPO = 需要每小时备份或复制

按 RTO/RPO 的策略:
1. RTO: 分钟，RPO: 秒
   → 多区域主-主架构，同步复制

2. RTO: 1 小时，RPO: 5 分钟
   → 主-备架构，异步复制 + 自动故障转移

3. RTO: 4 小时，RPO: 1 小时
   → 定期备份 + 手动恢复流程

4. RTO: 24 小时，RPO: 24 小时
   → 每日备份
```
