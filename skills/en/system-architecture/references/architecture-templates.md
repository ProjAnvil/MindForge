## Response Patterns by Request Type

### 1. New System Architecture Design

**Output Format:**

```markdown
# [System Name] Architecture Design

## 1. Executive Summary
- **Purpose**: [What does this system do?]
- **Key Metrics**: 
  - Users: [number]
  - QPS: [number]
  - Data Volume: [size]
- **Architecture Style**: [Microservices/Monolithic/Event-Driven]

## 2. Requirements Summary

### Functional Requirements
1. [Requirement 1]
2. [Requirement 2]

### Non-Functional Requirements
- **Performance**: [target]
- **Availability**: [target]
- **Scalability**: [target]

## 3. Architecture Overview

### High-Level Architecture Diagram
```
[Client] → [CDN] → [Load Balancer]
                        ↓
           [API Gateway]
                ↓
    ┌──────────┼──────────┐
    ↓          ↓          ↓
[Service A][Service B][Service C]
    ↓          ↓          ↓
  [DB-A]    [DB-B]    [DB-C]
              ↓
          [Cache]
              ↓
        [Message Queue]
```

### Component Description

#### API Gateway
- **Technology**: Kong / Spring Cloud Gateway
- **Responsibilities**:
  - Request routing
  - Authentication/Authorization
  - Rate limiting
  - Request/Response transformation

#### Service A: [Name]
- **Technology**: Spring Boot 3.x
- **Responsibilities**: [What it does]
- **API Endpoints**:
  - `POST /api/v1/resource`
  - `GET /api/v1/resource/{id}`
- **Database**: MySQL 8.0
- **Cache**: Redis

## 4. Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Frontend | React | Rich ecosystem, team expertise |
| API Gateway | Kong | High performance, plugin ecosystem |
| Backend | Spring Boot | Enterprise-grade, team expertise |
| Database | MySQL | ACID compliance, mature tooling |
| Cache | Redis | High performance, persistence option |
| Message Queue | Kafka | High throughput, log retention |
| Container | Docker | Standard containerization |
| Orchestration | Kubernetes | Industry standard, cloud-agnostic |
| Monitoring | Prometheus + Grafana | Open source, powerful querying |

## 5. Data Architecture

### Database Schema
```sql
-- Key tables
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Data Flow
```
Write: Client → Service → Primary DB → Async Replication → Replica
Read:  Client → Service → Cache → (if miss) → Replica DB
```

### Caching Strategy
- **Cache Aside**: Application manages cache
- **TTL**: 30 minutes for user data
- **Eviction**: LRU when memory full

## 6. Scalability Strategy

### Horizontal Scaling
- **Stateless Services**: Scale to 10+ instances
- **Load Balancing**: Round-robin with health checks
- **Auto-scaling**: CPU > 70% → add instance

### Database Scaling
- **Read Replicas**: 3 replicas for read traffic
- **Sharding**: User ID-based sharding when > 100M users
- **Connection Pooling**: HikariCP with max 50 connections

## 7. High Availability Design

### Redundancy
- **Multi-AZ Deployment**: Deploy across 3 availability zones
- **No Single Point of Failure**: All components have replicas

### Fault Tolerance
- **Circuit Breaker**: Sentinel with 50% error threshold
- **Retry Policy**: 3 retries with exponential backoff
- **Fallback**: Return cached data or default response

### Disaster Recovery
- **RTO**: 1 hour (Recovery Time Objective)
- **RPO**: 15 minutes (Recovery Point Objective)
- **Backup**: Daily full + hourly incremental
- **DR Site**: Standby site in different region

## 8. Security Architecture

### Authentication & Authorization
- **Protocol**: OAuth 2.0 + JWT
- **Token Expiry**: 1 hour (access), 30 days (refresh)
- **RBAC**: Role-based access control

### Data Security
- **Encryption in Transit**: TLS 1.3
- **Encryption at Rest**: AES-256
- **Sensitive Data**: PII encrypted, PCI DSS compliant

### Network Security
- **Firewall**: WAF at edge
- **DDoS Protection**: CloudFlare
- **VPC**: Private subnets for backend

## 9. Observability

### Logging
- **Centralized**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Structure**: JSON format with correlation ID
- **Retention**: 30 days

### Monitoring
- **Metrics**: Prometheus + Grafana
- **Key Metrics**: CPU, Memory, QPS, Error Rate, Latency (P50, P95, P99)
- **Alerts**: PagerDuty for critical alerts

### Tracing
- **Tool**: SkyWalking / Jaeger
- **Sampling**: 1% for normal traffic, 100% for errors

## 10. Deployment Architecture

### Environment Strategy
- **Dev**: Single instance, H2 database
- **Test**: Mimic prod, synthetic data
- **Staging**: Prod-like, real data subset
- **Production**: Multi-region, full redundancy

### CI/CD Pipeline
```
Code Push → Unit Tests → Build → Integration Tests
  → Container Build → Security Scan → Deploy to Staging
  → Smoke Tests → Approval → Blue-Green Deploy to Prod
  → Monitor → (Rollback if needed)
```

## 11. Cost Estimation

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| Compute (K8s) | $5,000 | 20 nodes, auto-scaling |
| Database | $2,000 | RDS with replicas |
| Cache | $500 | Redis cluster |
| CDN | $1,000 | CloudFlare |
| Monitoring | $300 | Datadog |
| **Total** | **$8,800** | |

## 12. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Database bottleneck | Medium | High | Implement read replicas, caching |
| Service outage | Low | High | Multi-AZ deployment, circuit breakers |
| DDoS attack | Medium | High | CDN with DDoS protection |
| Data breach | Low | Critical | Encryption, regular security audits |

## 13. Implementation Roadmap

### Phase 1: MVP (2 months)
- Core services development
- Basic authentication
- Single-region deployment

### Phase 2: Optimization (1 month)
- Caching implementation
- Performance tuning
- Load testing

### Phase 3: Production Ready (1 month)
- Multi-region deployment
- Comprehensive monitoring
- Security hardening
- Disaster recovery setup

## 14. Architecture Decision Records

### ADR-001: Use Microservices Architecture
- **Date**: 2024-12-16
- **Decision**: Adopt microservices over monolith
- **Rationale**: Need independent deployment, scaling, and team autonomy
- **Consequences**: Increased operational complexity, need service mesh

### ADR-002: Choose MySQL over MongoDB
- **Date**: 2024-12-16
- **Decision**: Use MySQL for primary data store
- **Rationale**: Strong consistency requirements, team expertise, mature ecosystem
- **Consequences**: Need sharding strategy for scale, ORM complexity

## 15. Next Steps

1. **Proof of Concept**: Build and test critical path
2. **Architecture Review**: Present to stakeholders
3. **Detailed Design**: Component-level specifications
4. **Team Onboarding**: Training on new technologies
5. **Infrastructure Setup**: Provision environments
```

### 2. Architecture Review

**Output Format:**

```markdown
# Architecture Review: [System Name]

## Review Summary
- **Reviewer**: [Name]
- **Date**: [Date]
- **Overall Rating**: [Excellent/Good/Needs Improvement/Poor]

## Evaluation Criteria

### 1. Functionality ✅/⚠️/❌
**Score**: [X/10]

**Strengths**:
- [Positive point 1]
- [Positive point 2]

**Issues**:
- ⚠️ **[Issue Title]**: [Description]
  - **Impact**: [Critical/Major/Minor]
  - **Recommendation**: [How to fix]

### 2. Performance ✅/⚠️/❌
**Score**: [X/10]

**Analysis**:
- Expected QPS: [number]
- Current capacity: [number]
- Bottlenecks identified: [list]

**Recommendations**:
1. [Recommendation 1]
2. [Recommendation 2]

### 3. Scalability ✅/⚠️/❌
**Score**: [X/10]

### 4. Availability ✅/⚠️/❌
**Score**: [X/10]

### 5. Security ✅/⚠️/❌
**Score**: [X/10]

### 6. Maintainability ✅/⚠️/❌
**Score**: [X/10]

## Critical Issues

### Issue #1: [Title]
- **Severity**: Critical
- **Component**: [Service/Database/Network]
- **Description**: [Detailed description]
- **Impact**: [What happens if not fixed]
- **Recommendation**: [Solution]
- **Effort**: [High/Medium/Low]
- **Priority**: Must fix before production

## Improvement Suggestions

1. **[Suggestion Title]**
   - Current: [What is now]
   - Proposed: [What should be]
   - Benefit: [Why it's better]
   - Effort: [How much work]

## Approved with Conditions

The architecture is **approved** contingent on addressing:
1. [Critical issue 1]
2. [Critical issue 2]

Optional improvements for future phases:
- [Nice-to-have 1]
- [Nice-to-have 2]
```
