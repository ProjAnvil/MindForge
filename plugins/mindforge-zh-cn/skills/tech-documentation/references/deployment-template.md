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
