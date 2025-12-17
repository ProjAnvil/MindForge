---
name: tech-documentation
description: Technical documentation writing skill covering API docs, architecture documentation, deployment guides, and various technical writing best practices.
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Tech Documentation Skill

技术文档编写技能库，提供全面的技术文档写作方法论和模板。

## 概述

这是一个专注于技术文档编写的综合性技能模块，涵盖各类技术文档的编写规范、模板和最佳实践，帮助团队产出高质量、易理解、易维护的技术文档。

## 核心能力

### 1. API文档
- **OpenAPI/Swagger规范**
- **RESTful API文档**
- **GraphQL文档**
- **gRPC接口文档**
- **API变更日志**
- **认证授权说明**

### 2. 架构文档
- **架构设计文档** (Architecture Design Document)
- **架构决策记录** (Architecture Decision Records, ADR)
- **系统架构图** (C4模型、UML)
- **技术选型报告**
- **架构演进路线图**

### 3. 详细设计文档
- **模块设计文档**
- **数据库设计文档**
- **接口设计文档**
- **算法设计说明**
- **时序图/流程图**

### 4. 部署运维文档
- **部署手册**
- **运维手册**
- **故障处理手册**
- **监控告警配置**
- **性能优化指南**
- **备份恢复流程**

### 5. 用户手册
- **产品使用手册**
- **快速开始指南**
- **常见问题FAQ**
- **故障排查指南**
- **最佳实践**

### 6. 开发者文档
- **贡献指南** (CONTRIBUTING.md)
- **代码规范**
- **开发环境搭建**
- **测试指南**
- **发布流程**

### 7. 项目管理文档
- **项目计划**
- **需求文档**
- **测试计划**
- **发布说明** (Release Notes)
- **变更日志** (CHANGELOG)

### 8. 知识库文档
- **技术博客**
- **案例分析**
- **问题总结**
- **学习笔记**

## 文档编写原则

### 1. 5C原则
- **Clear (清晰)**: 语言简洁，逻辑清晰
- **Concise (简洁)**: 避免冗余，直击要点
- **Complete (完整)**: 信息全面，覆盖所需
- **Correct (正确)**: 内容准确，经过验证
- **Consistent (一致)**: 风格统一，术语规范

### 2. 读者导向
- 了解目标读者（开发者、运维、产品、用户）
- 使用读者熟悉的语言和概念
- 提供不同层次的信息（概览→详细）
- 包含实际示例和最佳实践

### 3. 结构化
- 清晰的层次结构
- 统一的格式和风格
- 目录和导航
- 交叉引用

### 4. 可维护性
- 版本控制
- 变更记录
- 定期审查和更新
- 反馈机制

## 文档模板

### API文档模板

````markdown
# API文档

## 概述
简要描述API的用途和功能

## 基础信息
- **Base URL**: `https://api.example.com/v1`
- **认证方式**: Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### 获取Token
```http
POST /auth/token
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## 接口列表

### 用户管理

#### 创建用户

**请求**:
```http
POST /users
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user"
}
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 用户邮箱，需唯一 |
| name | string | 是 | 用户姓名 |
| role | string | 否 | 用户角色，默认user |

**响应**: `201 Created`
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2024-12-16T10:00:00Z"
}
```

**错误响应**:
- `400 Bad Request` - 参数错误
- `401 Unauthorized` - 未认证
- `409 Conflict` - 邮箱已存在

```json
{
  "error": {
    "code": "EMAIL_EXISTS",
    "message": "Email already registered",
    "field": "email"
  }
}
```

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| EMAIL_EXISTS | 409 | 邮箱已注册 |
| INVALID_TOKEN | 401 | Token无效 |
| RATE_LIMIT_EXCEEDED | 429 | 请求过于频繁 |

## 限流规则
- 每用户 100 请求/分钟
- 超限返回 429 状态码

## 变更日志

### v1.1.0 (2024-12-16)
- 新增用户角色管理接口
- 优化Token过期机制

### v1.0.0 (2024-12-01)
- 初始版本发布
````

### 架构设计文档模板

````markdown
# 架构设计文档

## 文档信息
- **项目名称**: [项目名]
- **文档版本**: 1.0
- **编写日期**: 2024-12-16
- **作者**: [姓名]
- **审阅者**: [姓名]

## 1. 概述

### 1.1 背景
[项目背景和目标]

### 1.2 目标读者
- 开发团队
- 架构师
- 运维团队

### 1.3 术语表
| 术语 | 说明 |
|------|------|
| API | Application Programming Interface |
| QPS | Queries Per Second |

## 2. 需求分析

### 2.1 功能性需求
1. [需求1]
2. [需求2]

### 2.2 非功能性需求
- **性能**: API响应时间 < 200ms
- **可用性**: 99.9% SLA
- **扩展性**: 支持水平扩展

### 2.3 约束条件
- 预算: $10,000/月
- 时间: 3个月开发周期
- 团队: 5人开发团队

## 3. 架构设计

### 3.1 架构风格
选择微服务架构，原因：
- 独立部署需求
- 不同模块有不同的扩展需求
- 多团队并行开发

### 3.2 系统架构图

```
┌─────────┐
│  Client │
└────┬────┘
     │
     ↓
┌─────────────┐
│ API Gateway │
└──────┬──────┘
       │
   ┌───┴───┬─────────┐
   ↓       ↓         ↓
┌─────┐ ┌─────┐  ┌─────┐
│Svc A│ │Svc B│  │Svc C│
└──┬──┘ └──┬──┘  └──┬──┘
   ↓       ↓         ↓
┌─────┐ ┌─────┐  ┌─────┐
│ DB  │ │Cache│  │ MQ  │
└─────┘ └─────┘  └─────┘
```

### 3.3 组件说明

#### API Gateway
- **技术**: Kong
- **职责**: 
  - 请求路由
  - 认证授权
  - 限流
- **部署**: 2个实例

## 4. 技术选型

| 组件 | 技术 | 理由 |
|------|------|------|
| 后端框架 | Spring Boot | 团队熟悉，生态完善 |
| 数据库 | PostgreSQL | 需要ACID，复杂查询 |
| 缓存 | Redis | 高性能，持久化选项 |

## 5. 数据设计

### 5.1 数据模型
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 数据流
```
Write: Client → Service → DB → Cache (async)
Read:  Client → Service → Cache → DB (if miss)
```

## 6. 接口设计

### 6.1 内部接口
- gRPC用于服务间通信
- Protocol Buffers定义接口

### 6.2 外部接口
- RESTful API
- OpenAPI 3.0规范

## 7. 安全设计

### 7.1 认证授权
- OAuth 2.0 + JWT
- RBAC权限模型

### 7.2 数据安全
- TLS 1.3传输加密
- AES-256存储加密

## 8. 部署架构

### 8.1 环境规划
- Dev: 单节点
- Test: 小规模集群
- Prod: 多AZ部署

### 8.2 容器化
- Docker容器
- Kubernetes编排

## 9. 监控运维

### 9.1 监控指标
- 系统指标: CPU, Memory, Disk
- 应用指标: QPS, 响应时间, 错误率
- 业务指标: 订单量, 活跃用户

### 9.2 日志
- ELK Stack
- 日志保留30天

## 10. 风险评估

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 性能瓶颈 | 中 | 高 | 压测验证，缓存优化 |
| 安全漏洞 | 低 | 高 | 安全审计，渗透测试 |

## 11. 架构演进

### Phase 1: MVP (2个月)
- 核心功能
- 单region部署

### Phase 2: 优化 (1个月)
- 性能优化
- 监控完善

### Phase 3: 扩展
- 多region
- 高级功能

## 附录

### A. 参考文档
- [技术选型报告](./tech-selection.md)
- [API文档](./api-docs.md)

### B. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| 1.0 | 2024-12-16 | 初始版本 | John |
````

### 部署文档模板

````markdown
# 部署文档

## 概述
本文档描述 [系统名] 的部署流程和配置说明。

## 环境要求

### 硬件要求
- CPU: 4核及以上
- 内存: 8GB及以上
- 磁盘: 100GB SSD

### 软件要求
- 操作系统: Ubuntu 20.04 LTS
- Docker: 20.10+
- Kubernetes: 1.25+
- Helm: 3.10+

## 部署步骤

### 1. 准备工作

#### 1.1 创建命名空间
```bash
kubectl create namespace myapp-prod
```

#### 1.2 配置镜像仓库密钥
```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=password \
  -n myapp-prod
```

### 2. 数据库部署

#### 2.1 部署MySQL
```bash
helm install mysql bitnami/mysql \
  --set auth.rootPassword=secretpassword \
  --set primary.persistence.size=50Gi \
  -n myapp-prod
```

#### 2.2 初始化数据库
```bash
kubectl exec -it mysql-0 -n myapp-prod -- \
  mysql -uroot -psecretpassword < schema.sql
```

### 3. Redis部署

```bash
helm install redis bitnami/redis \
  --set auth.password=redispassword \
  --set replica.replicaCount=2 \
  -n myapp-prod
```

### 4. 应用部署

#### 4.1 部署配置
创建 `values.yaml`:
```yaml
image:
  repository: registry.example.com/myapp
  tag: v1.0.0
  pullPolicy: IfNotPresent

replicaCount: 3

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

env:
  - name: SPRING_PROFILES_ACTIVE
    value: prod
  - name: DB_HOST
    value: mysql.myapp-prod
  - name: REDIS_HOST
    value: redis-master.myapp-prod
```

#### 4.2 执行部署
```bash
helm install myapp ./helm-chart \
  -f values.yaml \
  -n myapp-prod
```

### 5. 配置Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  namespace: myapp-prod
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: myapp-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

```bash
kubectl apply -f ingress.yaml
```

## 配置说明

### 环境变量
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SPRING_PROFILES_ACTIVE | Spring Profile | prod |
| DB_HOST | 数据库地址 | localhost |
| REDIS_HOST | Redis地址 | localhost |

### 配置文件
应用配置文件位于 `/app/config/application.yml`

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://${DB_HOST}:3306/myapp
    username: ${DB_USER}
    password: ${DB_PASSWORD}
```

## 验证部署

### 检查Pod状态
```bash
kubectl get pods -n myapp-prod
```

预期输出:
```
NAME                     READY   STATUS    RESTARTS   AGE
myapp-6d4f7b5c9-abc12    1/1     Running   0          2m
myapp-6d4f7b5c9-def34    1/1     Running   0          2m
myapp-6d4f7b5c9-ghi56    1/1     Running   0          2m
```

### 健康检查
```bash
curl https://api.example.com/actuator/health
```

预期响应:
```json
{
  "status": "UP"
}
```

### 查看日志
```bash
kubectl logs -f deployment/myapp -n myapp-prod
```

## 升级部署

### 滚动更新
```bash
helm upgrade myapp ./helm-chart \
  --set image.tag=v1.0.1 \
  -n myapp-prod
```

### 回滚
```bash
# 查看历史
helm history myapp -n myapp-prod

# 回滚到上一版本
helm rollback myapp -n myapp-prod

# 回滚到指定版本
helm rollback myapp 3 -n myapp-prod
```

## 监控配置

### Prometheus
```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: myapp
  namespace: myapp-prod
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
  - port: metrics
    interval: 30s
```

### Grafana Dashboard
导入Dashboard ID: 12345

## 故障排查

### Pod无法启动
1. 查看Pod状态: `kubectl describe pod <pod-name> -n myapp-prod`
2. 查看日志: `kubectl logs <pod-name> -n myapp-prod`
3. 常见原因:
   - 镜像拉取失败
   - 配置错误
   - 资源不足

### 数据库连接失败
1. 检查数据库Pod状态
2. 验证网络连接: `kubectl exec -it myapp-xxx -- nc -zv mysql 3306`
3. 检查密码配置

### 服务无法访问
1. 检查Service: `kubectl get svc -n myapp-prod`
2. 检查Ingress: `kubectl get ingress -n myapp-prod`
3. 检查DNS解析
4. 检查证书状态

## 维护操作

### 备份数据库
```bash
kubectl exec mysql-0 -n myapp-prod -- \
  mysqldump -uroot -p$MYSQL_ROOT_PASSWORD myapp > backup.sql
```

### 扩缩容
```bash
kubectl scale deployment myapp --replicas=5 -n myapp-prod
```

### 重启应用
```bash
kubectl rollout restart deployment/myapp -n myapp-prod
```

## 安全检查清单

- [ ] 使用非root用户运行容器
- [ ] 配置资源限制
- [ ] 启用网络策略
- [ ] 敏感信息使用Secret
- [ ] 定期更新镜像
- [ ] 配置RBAC权限
- [ ] 启用Pod安全策略

## 附录

### A. 常用命令
```bash
# 查看所有资源
kubectl get all -n myapp-prod

# 进入容器
kubectl exec -it <pod-name> -n myapp-prod -- /bin/bash

# 端口转发
kubectl port-forward svc/myapp 8080:80 -n myapp-prod

# 查看事件
kubectl get events -n myapp-prod --sort-by='.lastTimestamp'
```

### B. 联系方式
- 技术支持: support@example.com
- 紧急联系: +86-xxx-xxxx-xxxx

### C. 变更记录
| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| 1.0 | 2024-12-16 | 初始版本 | DevOps Team |
````

## 使用场景

### 新项目启动
```
为新项目创建完整的文档体系：
- README.md
- API文档
- 架构设计文档
- 部署文档
- 贡献指南
```

### API设计评审
```
编写API设计文档，包括：
- 接口定义
- 数据模型
- 错误处理
- 安全认证
```

### 系统交付
```
准备系统交付文档包：
- 系统架构文档
- 部署运维手册
- 用户使用手册
- 故障处理手册
```

### 知识沉淀
```
技术方案总结：
- 问题分析
- 解决方案
- 技术决策
- 经验教训
```

## 集成示例

### 在Agent中使用
```json
{
  "agent": "tech-writer",
  "skills": [
    "tech-documentation",
    "system-architecture",
    "api-design"
  ]
}
```

### 在对话中引用
```
@tech-documentation 请为这个API创建完整的文档
```

## 文档质量检查清单

### 内容质量
- [ ] 信息准确完整
- [ ] 逻辑清晰连贯
- [ ] 示例真实可用
- [ ] 术语统一规范

### 可读性
- [ ] 语言简洁明了
- [ ] 结构层次分明
- [ ] 格式统一美观
- [ ] 配图清晰易懂

### 可维护性
- [ ] 版本信息明确
- [ ] 变更记录完整
- [ ] 联系方式准确
- [ ] 定期审查更新

### 可访问性
- [ ] 目录导航清晰
- [ ] 搜索功能完善
- [ ] 链接有效准确
- [ ] 支持多种格式

## 工具推荐

### 文档编写
- **Markdown编辑器**: Typora, VS Code
- **API文档**: Swagger Editor, Postman
- **图表工具**: Draw.io, PlantUML, Mermaid
- **截图工具**: Snipaste, Xnip

### 文档托管
- **静态站点**: GitBook, Docusaurus, VuePress
- **团队协作**: Confluence, Notion
- **版本控制**: Git, GitHub/GitLab

### 文档生成
- **API文档**: Swagger/OpenAPI, ApiDoc
- **代码文档**: JavaDoc, JSDoc, Sphinx
- **README生成**: readme-md-generator

## 学习资源

### 推荐书籍
- 《技术写作手册》
- 《Docs for Developers》
- 《The Documentation Compendium》

### 在线资源
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Microsoft Writing Style Guide](https://docs.microsoft.com/style-guide/)
- [Write the Docs](https://www.writethedocs.org/)

---

**版本**: 1.0.0  
**最后更新**: 2024-12  
**维护者**: AI Toolkit Team
