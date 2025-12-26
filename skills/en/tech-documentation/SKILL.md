---
name: tech-documentation
description: Technical documentation writing skill covering API docs, architecture documentation, deployment guides, and various technical writing best practices. Use this skill when creating technical documentation, writing API documentation, creating architecture design documents, or need templates for deployment and operations manuals.
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Tech Documentation Skill

Technical documentation writing expertise, providing comprehensive methodology and templates for producing high-quality technical documentation.

## Overview

This is a comprehensive skill module focused on technical documentation writing, covering standards, templates, and best practices for various types of technical documentation to help teams produce high-quality, easy-to-understand, and maintainable documentation.

## Core Capabilities

### 1. API Documentation
- **OpenAPI/Swagger Specifications**
- **RESTful API Documentation**
- **GraphQL Documentation**
- **gRPC Interface Documentation**
- **API Change Logs**
- **Authentication and Authorization Documentation**

### 2. Architecture Documentation
- **Architecture Design Documents (ADD)**
- **Architecture Decision Records (ADR)**
- **System Architecture Diagrams** (C4 Model, UML)
- **Technology Selection Reports**
- **Architecture Evolution Roadmaps**

### 3. Detailed Design Documents
- **Module Design Documents**
- **Database Design Documents**
- **Interface Design Documents**
- **Algorithm Design Specifications**
- **Sequence Diagrams/Flowcharts**

### 4. Deployment and Operations Documentation
- **Deployment Manuals**
- **Operations Manuals**
- **Incident Response Manuals**
- **Monitoring and Alerting Configuration**
- **Performance Optimization Guides**
- **Backup and Recovery Procedures**

### 5. User Manuals
- **Product User Manuals**
- **Quick Start Guides**
- **Frequently Asked Questions (FAQ)**
- **Troubleshooting Guides**
- **Best Practices**

### 6. Developer Documentation
- **Contributing Guidelines** (CONTRIBUTING.md)
- **Coding Standards**
- **Development Environment Setup**
- **Testing Guides**
- **Release Processes**

### 7. Project Management Documentation
- **Project Plans**
- **Requirements Documents**
- **Test Plans**
- **Release Notes**
- **Change Logs** (CHANGELOG)

### 8. Knowledge Base Documentation
- **Technical Blog Posts**
- **Case Studies**
- **Problem Summaries**
- **Learning Notes**

## Documentation Principles

### 1. The 5C Principles
- **Clear**: Concise language, clear logic
- **Concise**: Avoid redundancy, get to the point
- **Complete**: Comprehensive information covering all needs
- **Correct**: Accurate content, verified and tested
- **Consistent**: Unified style, standardized terminology

### 2. Audience-Oriented
- Understand target audience (developers, operations, product, users)
- Use language and concepts familiar to the audience
- Provide information at different levels (overview → detailed)
- Include practical examples and best practices

### 3. Structured Organization
- Clear hierarchical structure
- Unified format and style
- Table of contents and navigation
- Cross-references

### 4. Maintainability
- Version control
- Change records
- Regular review and updates
- Feedback mechanisms

## Documentation Templates

### API Documentation Template

````markdown
# API Documentation

## Overview
Briefly describe the purpose and functionality of the API

## Basic Information
- **Base URL**: `https://api.example.com/v1`
- **Authentication**: Bearer Token
- **Data Format**: JSON
- **Character Encoding**: UTF-8

## Authentication

### Get Token
```http
POST /auth/token
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## API Endpoints

### User Management

#### Create User

**Request**:
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

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | User email, must be unique |
| name | string | Yes | User name |
| role | string | No | User role, defaults to 'user' |

**Response**: `201 Created`
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2024-12-16T10:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Not authenticated
- `409 Conflict` - Email already exists

```json
{
  "error": {
    "code": "EMAIL_EXISTS",
    "message": "Email already registered",
    "field": "email"
  }
}
```

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| EMAIL_EXISTS | 409 | Email already registered |
| INVALID_TOKEN | 401 | Invalid token |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |

## Rate Limiting
- 100 requests/minute per user
- Returns 429 status code when exceeded

## Changelog

### v1.1.0 (2024-12-16)
- Added user role management endpoints
- Improved token expiration mechanism

### v1.0.0 (2024-12-01)
- Initial release
````

### Architecture Design Document Template

````markdown
# Architecture Design Document

## Document Information
- **Project Name**: [Project Name]
- **Document Version**: 1.0
- **Date**: 2024-12-16
- **Author**: [Name]
- **Reviewer**: [Name]

## 1. Overview

### 1.1 Background
[Project background and objectives]

### 1.2 Target Audience
- Development team
- Architects
- Operations team

### 1.3 Glossary
| Term | Description |
|------|-------------|
| API | Application Programming Interface |
| QPS | Queries Per Second |

## 2. Requirements Analysis

### 2.1 Functional Requirements
1. [Requirement 1]
2. [Requirement 2]

### 2.2 Non-Functional Requirements
- **Performance**: API response time < 200ms
- **Availability**: 99.9% SLA
- **Scalability**: Support horizontal scaling

### 2.3 Constraints
- Budget: $10,000/month
- Timeline: 3-month development cycle
- Team: 5-person development team

## 3. Architecture Design

### 3.1 Architecture Style
Selected microservices architecture for the following reasons:
- Independent deployment requirements
- Different modules have different scaling needs
- Multiple teams developing in parallel

### 3.2 System Architecture Diagram

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

### 3.3 Component Description

#### API Gateway
- **Technology**: Kong
- **Responsibilities**:
  - Request routing
  - Authentication and authorization
  - Rate limiting
- **Deployment**: 2 instances

## 4. Technology Selection

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend Framework | Spring Boot | Team familiarity, mature ecosystem |
| Database | PostgreSQL | ACID required, complex queries |
| Cache | Redis | High performance, persistence options |

## 5. Data Design

### 5.1 Data Model
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Data Flow
```
Write: Client → Service → DB → Cache (async)
Read:  Client → Service → Cache → DB (if miss)
```

## 6. Interface Design

### 6.1 Internal Interfaces
- gRPC for inter-service communication
- Protocol Buffers for interface definitions

### 6.2 External Interfaces
- RESTful API
- OpenAPI 3.0 specification

## 7. Security Design

### 7.1 Authentication and Authorization
- OAuth 2.0 + JWT
- RBAC permission model

### 7.2 Data Security
- TLS 1.3 for transport encryption
- AES-256 for storage encryption

## 8. Deployment Architecture

### 8.1 Environment Planning
- Dev: Single node
- Test: Small-scale cluster
- Prod: Multi-AZ deployment

### 8.2 Containerization
- Docker containers
- Kubernetes orchestration

## 9. Monitoring and Operations

### 9.1 Monitoring Metrics
- System metrics: CPU, Memory, Disk
- Application metrics: QPS, Response Time, Error Rate
- Business metrics: Order volume, Active users

### 9.2 Logging
- ELK Stack
- 30-day log retention

## 10. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance bottleneck | Medium | High | Load testing, cache optimization |
| Security vulnerability | Low | High | Security audit, penetration testing |

## 11. Architecture Evolution

### Phase 1: MVP (2 months)
- Core functionality
- Single-region deployment

### Phase 2: Optimization (1 month)
- Performance optimization
- Monitoring enhancement

### Phase 3: Expansion
- Multi-region
- Advanced features

## Appendix

### A. Reference Documents
- [Technology Selection Report](./tech-selection.md)
- [API Documentation](./api-docs.md)

### B. Change Record

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-12-16 | Initial version | John |
````

### Deployment Documentation Template

````markdown
# Deployment Documentation

## Overview
This document describes the deployment process and configuration for [System Name].

## Prerequisites

### Hardware Requirements
- CPU: 4 cores or more
- Memory: 8GB or more
- Disk: 100GB SSD

### Software Requirements
- Operating System: Ubuntu 20.04 LTS
- Docker: 20.10+
- Kubernetes: 1.25+
- Helm: 3.10+

## Deployment Steps

### 1. Preparation

#### 1.1 Create Namespace
```bash
kubectl create namespace myapp-prod
```

#### 1.2 Configure Image Registry Secret
```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=password \
  -n myapp-prod
```

### 2. Database Deployment

#### 2.1 Deploy MySQL
```bash
helm install mysql bitnami/mysql \
  --set auth.rootPassword=secretpassword \
  --set primary.persistence.size=50Gi \
  -n myapp-prod
```

#### 2.2 Initialize Database
```bash
kubectl exec -it mysql-0 -n myapp-prod -- \
  mysql -uroot -psecretpassword < schema.sql
```

### 3. Redis Deployment

```bash
helm install redis bitnami/redis \
  --set auth.password=redispassword \
  --set replica.replicaCount=2 \
  -n myapp-prod
```

### 4. Application Deployment

#### 4.1 Deployment Configuration
Create `values.yaml`:
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

#### 4.2 Execute Deployment
```bash
helm install myapp ./helm-chart \
  -f values.yaml \
  -n myapp-prod
```

### 5. Configure Ingress

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

## Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| SPRING_PROFILES_ACTIVE | Spring Profile | prod |
| DB_HOST | Database address | localhost |
| REDIS_HOST | Redis address | localhost |

### Configuration Files
Application configuration located at `/app/config/application.yml`

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://${DB_HOST}:3306/myapp
    username: ${DB_USER}
    password: ${DB_PASSWORD}
```

## Verify Deployment

### Check Pod Status
```bash
kubectl get pods -n myapp-prod
```

Expected output:
```
NAME                     READY   STATUS    RESTARTS   AGE
myapp-6d4f7b5c9-abc12    1/1     Running   0          2m
myapp-6d4f7b5c9-def34    1/1     Running   0          2m
myapp-6d4f7b5c9-ghi56    1/1     Running   0          2m
```

### Health Check
```bash
curl https://api.example.com/actuator/health
```

Expected response:
```json
{
  "status": "UP"
}
```

### View Logs
```bash
kubectl logs -f deployment/myapp -n myapp-prod
```

## Upgrade Deployment

### Rolling Update
```bash
helm upgrade myapp ./helm-chart \
  --set image.tag=v1.0.1 \
  -n myapp-prod
```

### Rollback
```bash
# View history
helm history myapp -n myapp-prod

# Rollback to previous version
helm rollback myapp -n myapp-prod

# Rollback to specific version
helm rollback myapp 3 -n myapp-prod
```

## Monitoring Configuration

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
Import Dashboard ID: 12345

## Troubleshooting

### Pod Fails to Start
1. Check pod status: `kubectl describe pod <pod-name> -n myapp-prod`
2. View logs: `kubectl logs <pod-name> -n myapp-prod`
3. Common causes:
   - Image pull failure
   - Configuration errors
   - Insufficient resources

### Database Connection Failure
1. Check database pod status
2. Verify network connectivity: `kubectl exec -it myapp-xxx -- nc -zv mysql 3306`
3. Verify password configuration

### Service Inaccessible
1. Check service: `kubectl get svc -n myapp-prod`
2. Check ingress: `kubectl get ingress -n myapp-prod`
3. Check DNS resolution
4. Check certificate status

## Maintenance Operations

### Backup Database
```bash
kubectl exec mysql-0 -n myapp-prod -- \
  mysqldump -uroot -p$MYSQL_ROOT_PASSWORD myapp > backup.sql
```

### Scaling
```bash
kubectl scale deployment myapp --replicas=5 -n myapp-prod
```

### Restart Application
```bash
kubectl rollout restart deployment/myapp -n myapp-prod
```

## Security Checklist

- [ ] Run container as non-root user
- [ ] Configure resource limits
- [ ] Enable network policies
- [ ] Use secrets for sensitive data
- [ ] Regularly update images
- [ ] Configure RBAC permissions
- [ ] Enable Pod security policies

## Appendix

### A. Common Commands
```bash
# View all resources
kubectl get all -n myapp-prod

# Exec into container
kubectl exec -it <pod-name> -n myapp-prod -- /bin/bash

# Port forwarding
kubectl port-forward svc/myapp 8080:80 -n myapp-prod

# View events
kubectl get events -n myapp-prod --sort-by='.lastTimestamp'
```

### B. Contact Information
- Technical Support: support@example.com
- Emergency Contact: +1-xxx-xxx-xxxx

### C. Change Record
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-12-16 | Initial version | DevOps Team |
````

## Use Cases

### New Project Launch
```
Create complete documentation system for new project:
- README.md
- API documentation
- Architecture design document
- Deployment documentation
- Contributing guidelines
```

### API Design Review
```
Write API design documentation, including:
- Interface definitions
- Data models
- Error handling
- Security authentication
```

### System Delivery
```
Prepare system delivery documentation package:
- System architecture documentation
- Deployment and operations manual
- User manual
- Incident response manual
```

### Knowledge Management
```
Technical solution summary:
- Problem analysis
- Solutions
- Technical decisions
- Lessons learned
```

## Integration Examples

### Using in Agent
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

### Referencing in Conversation
```
@tech-documentation Please create complete documentation for this API
```

## Documentation Quality Checklist

### Content Quality
- [ ] Information is accurate and complete
- [ ] Logic is clear and coherent
- [ ] Examples are realistic and usable
- [ ] Terminology is consistent and standardized

### Readability
- [ ] Language is concise and clear
- [ ] Structure is well-organized
- [ ] Formatting is unified and attractive
- [ ] Diagrams are clear and easy to understand

### Maintainability
- [ ] Version information is clear
- [ ] Change records are complete
- [ ] Contact information is accurate
- [ ] Regular review and updates

### Accessibility
- [ ] Table of contents navigation is clear
- [ ] Search functionality is complete
- [ ] Links are valid and accurate
- [ ] Multiple formats are supported

## Recommended Tools

### Documentation Writing
- **Markdown Editors**: Typora, VS Code
- **API Documentation**: Swagger Editor, Postman
- **Diagram Tools**: Draw.io, PlantUML, Mermaid
- **Screenshot Tools**: Snipaste, Xnip

### Documentation Hosting
- **Static Sites**: GitBook, Docusaurus, VuePress
- **Team Collaboration**: Confluence, Notion
- **Version Control**: Git, GitHub/GitLab

### Documentation Generation
- **API Documentation**: Swagger/OpenAPI, ApiDoc
- **Code Documentation**: JavaDoc, JSDoc, Sphinx
- **README Generation**: readme-md-generator

## Learning Resources

### Recommended Books
- "Technical Writing: A Practical Guide"
- "Docs for Developers"
- "The Documentation Compendium"

### Online Resources
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Microsoft Writing Style Guide](https://docs.microsoft.com/style-guide/)
- [Write the Docs](https://www.writethedocs.org/)

---

**Version**: 1.0.0
**Last Updated**: December 2024
**Maintainer**: MindForge Team
